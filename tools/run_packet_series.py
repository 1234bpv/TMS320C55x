"""Run three ordered packet-size series, stopping on the first failed run."""
import argparse
import datetime
import json
from pathlib import Path
import re
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SIZES = (512, 1568, 1792, 2048, 2304, 4096)
ORDERS = (SIZES, tuple(reversed(SIZES)), SIZES[2:] + SIZES[:2])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ip', required=True)
    p.add_argument('--device', choices=('n95', 'e90'), required=True)
    p.add_argument('--preparation', type=Path, required=True)
    p.add_argument('--tag-prefix', required=True)
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', a.tag_prefix):
        p.error('invalid tag prefix')
    folder = ROOT / 'work/evidence' / a.device
    report_path = folder / (a.tag_prefix + '-series.json')
    transcript = folder / (a.tag_prefix + '-series.txt')
    if report_path.exists() or transcript.exists():
        p.error('series evidence already exists')
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'device': a.device, 'ip': a.ip, 'frames_per_run': 32,
              'orders': ORDERS, 'runs': [], 'complete': False}
    def save():
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    save()
    with transcript.open('x', encoding='utf-8') as out:
        for number, order in enumerate(ORDERS, 1):
            for size in order:
                tag = f'{a.tag_prefix}-{size}-r{number}-01'
                command = [sys.executable, str(ROOT / 'tools/run_stream.py'),
                           '--ip', a.ip, '--device', a.device, '--mode', 'worker-transfer',
                           '--host-version', '18', '--reps', '0', '--packet-bytes', str(size),
                           '--frames', '32', '--preparation', str(a.preparation.resolve()),
                           '--tag', tag]
                if a.device == 'e90':
                    command.extend(['--exe', 'C:\\sys\\bin\\c55stream.exe'])
                out.write('COMMAND ' + json.dumps(command) + '\n'); out.flush()
                result = subprocess.run(command, stdout=out, stderr=subprocess.STDOUT, cwd=ROOT)
                report['runs'].append({'tag': tag, 'packet_bytes': size,
                                       'round': number, 'command': command,
                                       'exit_code': result.returncode})
                save()
                if result.returncode:
                    raise RuntimeError('series stopped at ' + tag)
                log = (folder / (tag + '.log')).read_text(encoding='ascii')
                times = [int(x) for x in re.findall(r'completion_observed_us=(\d+)', log)]
                if len(times) != 32:
                    raise RuntimeError('missing completion records at ' + tag)
                print(f'VERIFIED {tag} median_us={statistics.median(times)} max_us={max(times)}', flush=True)
    report['complete'] = True; save()
    print('SERIES COMPLETE ' + str(report_path), flush=True)


if __name__ == '__main__':
    main()
