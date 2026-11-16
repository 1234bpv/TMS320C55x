"""Validate every v18 packet/cleanup record before publishing size measurements."""
import argparse
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import zlib

from prepare_stream import stock_clock_matches
from run_packet_series import SIZES, ORDERS
from summarize_worker_stream import NORMAL

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def numbers(line):
    return {k: int(v) for k, v in re.findall(r'(\w+)=(-?\d+)', line)}


def stats(values):
    ordered = sorted(values)
    return {'samples': len(values), 'min_us': min(values),
            'median_us': statistics.median(values),
            'p95_us': ordered[math.ceil(len(values) * .95) - 1],
            'p99_us': ordered[math.ceil(len(values) * .99) - 1],
            'max_us': max(values)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device', choices=('n95', 'e90'), required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    folder = ROOT / 'work/evidence' / a.device
    a.out = a.out.resolve()
    target = a.out / f'{a.device}-packet-sizes-v18-results.json'
    if target.exists():
        p.error('result already exists')
    publications = []
    def publish(path, suffix):
        dest = a.out / f'{a.device}-packet-sizes-v18-{suffix}'
        raw = path.read_bytes()
        if dest.exists() and dest.read_bytes() != raw:
            raise RuntimeError('published evidence differs: ' + str(dest))
        publications.append((dest, raw))
        return dest.relative_to(ROOT).as_posix()

    prep_path = folder / 'stream-worker-v18-prepare-01-preparation.json'
    recovery_path = folder / 'stream-worker-v18-recovery-01.json'
    prep = json.loads(prep_path.read_text(encoding='utf-8'))
    recovery = json.loads(recovery_path.read_text(encoding='utf-8'))
    artifact = json.loads((a.out / 'worker-stream-v4-artifacts.json').read_text(encoding='utf-8'))
    if artifact['host_version'] != 18 or artifact['protocol'] != 18:
        raise RuntimeError('wrong artifact version')
    if not all(prep.get(k) is True for k in ('complete', 'stock_clock_guard', 'clock_log_restored')):
        raise RuntimeError('preparation incomplete')
    clock_path = ROOT / prep['clock_log']
    if not stock_clock_matches(clock_path.read_text(encoding='ascii'), a.device):
        raise RuntimeError('stock clock conditions missing')
    if not recovery['complete'] or not recovery['dsp_restored'] or not recovery['restored_dsp']['equal']:
        raise RuntimeError('recovery incomplete')
    if recovery['restored_dsp']['sha256'] != NORMAL[a.device] or recovery['ps'] != ['OK ps 0']:
        raise RuntimeError('normal DSP not restored or worker still present')
    deployed = [x for x in prep['files'] if x.get('remote') == 'E:\\c55stream.dll55l' and x.get('equal')]
    if len(deployed) != 1 or deployed[0]['sha256'] != artifact['sha256']:
        raise RuntimeError('preparation does not reference this DSP build')
    if sha((ROOT / deployed[0]['readback']).read_bytes()) != artifact['sha256']:
        raise RuntimeError('preparation DSP readback differs')
    daemon_tick = re.search(r'startTick (\d+)', '\n'.join(prep['info_after'])).group(1)
    series_path = folder / 'stream-worker-v18-transfer-series.json'
    series = json.loads(series_path.read_text(encoding='utf-8'))
    expected_tags = [f'stream-worker-v18-transfer-{size}-r{round_}-01'
                     for round_, order in enumerate(ORDERS, 1) for size in order]
    if (not series['complete'] or [x['tag'] for x in series['runs']] != expected_tags or
            any(x['exit_code'] for x in series['runs'])):
        raise RuntimeError('size series incomplete or reordered')
    expected_crc = f'{zlib.crc32(bytes((i*13+7)&255 for i in range(65536))):08x}'

    def read_run(tag, size, count, reps, crc_enabled):
        path = folder / (tag + '.log')
        raw = path.read_bytes(); text = raw.decode('ascii')
        transport_path = folder / (tag + '-transport.txt')
        transport = transport_path.read_text(encoding='utf-8')
        profile = (folder / (tag + '-profile.log')).read_text(encoding='ascii')
        uid = {'n95': '20002d84', 'e90': '20002496'}[a.device]
        if not text.startswith('C55STREAM v18 ') or f'machine={uid} ' not in text.splitlines()[0]:
            raise RuntimeError('version/device mismatch: ' + tag)
        if not profile.startswith('C55STREAM v18 ') or not profile.rstrip().endswith('FINAL status=0'):
            raise RuntimeError('inspect failed: ' + tag)
        prefix = (f'WORKER STREAM PASS frames={count} creates=1 runs=0 useful_arm_crc={count if crc_enabled else 0} '
                  f'mode=0 reps={reps} total_us=')
        pass_line = next((x for x in text.splitlines() if x.startswith(prefix)), None)
        if pass_line is None or f'packet_bytes={size} no_crc={int(not crc_enabled)}' not in pass_line:
            raise RuntimeError('incorrect PASS marker: ' + tag)
        required = ('create=0 status=0 ', 'delete=0 status=0',
                    'state phase=worker deleted rc=0', '  state=5 ',
                    'free task=0', 'free native out=0', 'free native in=0',
                    'WORKER CLEANUP PASS no_run=1 delete_free_native_close=0')
        if any(x not in text for x in required) or not text.rstrip().endswith('FINAL status=0'):
            raise RuntimeError('cleanup incomplete: ' + tag)
        if 'BEGIN execute' in text or 'cancel input=' in text or 'cancel output=' in text:
            raise RuntimeError('unexpected lifecycle/transfer cancellation: ' + tag)
        if re.findall(r'^EXIT (.+)$', transport, re.M) != ['0 Kill', '0 Kill'] or re.search(r'\bKILL ', transport):
            raise RuntimeError('process did not exit cleanly: ' + tag)
        if set(re.findall(r'startTick (\d+)', transport)) != {daemon_tick}:
            raise RuntimeError('daemon restarted: ' + tag)
        if sha((folder / (tag + '-prepared-dsp.dll55l')).read_bytes()) != artifact['sha256']:
            raise RuntimeError('per-run DSP readback differs: ' + tag)
        if a.device == 'n95':
            if not re.search(r'PERF reserve=0 status=0 before=\d+ after=100', text) or not re.search(r'PERF release=0 status=0 after=\d+', text):
                raise RuntimeError('MPU reservation/release failed: ' + tag)
        records = []; current = None
        for line in text.splitlines():
            if line.startswith('frame='):
                if current is not None: records.append(current)
                match = re.fullmatch(r'frame=(\d+) put=0/0 get=0/0 wall_us=(\d+) crc=([0-9a-f]{8})', line)
                if not match: raise RuntimeError('transfer failed: ' + tag)
                current = {'sequence': int(match[1]), 'wall_us': int(match[2]), 'crc': match[3]}
            elif current is not None and line.startswith(('  issue_us=', 'SIZE ', '  result=', '  dsp_stamp=')):
                current.update(numbers(line))
            elif current is not None and line.startswith('PERF frame='):
                current['perf'] = numbers(line)
        if current is not None: records.append(current)
        if len(records) != count: raise RuntimeError('wrong packet count: ' + tag)
        for index, rec in enumerate(records, 1):
            dot = sum((((i*17+index*11)&255)-128) * (((i-16)&15)-7) for i in range(16, 256)) if reps else 0
            expected = {'sequence': index, 'frame': index, 'input_bytes': size, 'output_bytes': size,
                        'returned_words': size//2, 'protocol': 18, 'checked_payload_words': size//2-16,
                        'result': dot, 'expected': dot, 'errors': 0, 'stop': int(index == count),
                        'counts_per_ms': 164, 'crc': expected_crc if crc_enabled else '00000000'}
            if any(rec.get(k) != v for k, v in expected.items()):
                raise RuntimeError('packet data or bounds differ: ' + tag + ' frame ' + str(index))
            if rec['completion_observed_us'] < rec['issue_us'] or rec['wall_us'] < rec['completion_observed_us']:
                raise RuntimeError('completion time inconsistent: ' + tag)
            if not crc_enabled and rec['arm_crc_us'] != 0:
                raise RuntimeError('ARM CRC included in transport measurement: ' + tag)
            if 'dsp_stamp' not in rec: raise RuntimeError('DSP timestamp missing: ' + tag)
            if a.device == 'n95' and rec.get('perf') != {'frame': index, 'before': 100, 'after': 100}:
                raise RuntimeError('MPU condition differs: ' + tag)
        total = numbers(pass_line)['total_us']
        if total != sum(rec['wall_us'] for rec in records):
            raise RuntimeError('packet total differs: ' + tag)
        times = [rec['completion_observed_us'] for rec in records]
        return {'tag': tag, 'journal': publish(path, tag.removeprefix('stream-worker-v18-') + '.txt'),
                'journal_sha256': sha(raw), 'transport_sha256': sha(transport_path.read_bytes()),
                'packet_bytes': size, 'payload_bytes': size-32, 'frames': count, 'reps': reps,
                'useful_arm_crc': crc_enabled, 'total_us': total,
                'completion_observed_us': times, 'completion_statistics': stats(times),
                'raw_dsp_ticks': [rec['ticks'] for rec in records],
                'dot_results': [rec['result'] for rec in records],
                'create_wall_us': int(re.search(r'^create=0 status=0 wall_us=(\d+)\r?$', text, re.M)[1]),
                'delete_submit_us': int(re.search(r'^delete submitted=0 status=-?\d+ submit_us=(\d+)\r?$', text, re.M)[1]),
                'all_packet_checks_passed': True, 'exit': 0, 'cleanup': 'delete/task/native/close/FINAL0'}

    one = [read_run(f'stream-worker-v18-one-{size}-01', size, 1, 0, True) for size in (512, 1792, 4096)]
    q15 = read_run('stream-worker-v18-q15-4096-01', 4096, 8, 1000, True)
    transfers = [read_run(x['tag'], x['packet_bytes'], 32, 0, False) for x in series['runs']]
    summaries = []
    for size in SIZES:
        selected = [x for x in transfers if x['packet_bytes'] == size]
        times = [t for run in selected for t in run['completion_observed_us']]
        summaries.append({'packet_bytes': size, 'payload_bytes': size-32,
                          'round_medians_us': [x['completion_statistics']['median_us'] for x in selected],
                          **stats(times)})
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'device': a.device, 'host_version': 18, 'protocol': 18,
              'artifact': 'worker-stream-v4-artifacts.json',
              'static_contract': 'n95-e90-stream-size-contract.json',
              'preparation': publish(prep_path, 'preparation.json'),
              'clock_journal': publish(clock_path, 'clock.txt'), 'clock_journal_sha256': sha(clock_path.read_bytes()),
              'recovery': publish(recovery_path, 'recovery.json'),
              'series': publish(series_path, 'series.json'),
              'daemon_start_tick': int(daemon_tick), 'fast_counter_hz': 32768,
              'stock_clock_guard': True, 'mpu_percent_per_packet': 100 if a.device == 'n95' else None,
              'successful_runs': len(one)+len(transfers)+1,
              'correct_packets': sum(x['frames'] for x in one+transfers+[q15]),
              'one': one, 'q15': q15, 'transfers': transfers, 'size_summary': summaries,
              'measurement': 'ARM issue-to-observed-completion, equal-size input/output, full echo, Q15 reps0, no ARM CRC',
              'limits': ['Includes driver issue/wait/scheduling, stream transport and DSP echo; not pure DMA latency or bandwidth.',
                         'Input generation, payload validation, per-packet logging and one-time create are outside the completion interval.',
                         'Empirical percentiles describe 96 samples per size, not guaranteed deadline bounds.',
                         'Input/output have equal lengths; actual short WSOLA output and asymmetric MDEC are not measured.',
                         'No application kernel speedup, long stability, audio coexistence or negative lifecycle safety is inferred.']}
    a.out.mkdir(parents=True, exist_ok=True)
    for dest, raw in publications:
        if not dest.exists(): dest.write_bytes(raw)
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('VERIFIED ' + str(target))
    for summary in summaries: print(summary)


if __name__ == '__main__':
    main()
