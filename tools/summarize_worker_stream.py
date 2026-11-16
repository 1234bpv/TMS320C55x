"""Publish small verified worker-stream journals and provisional timing data.

Does not infer all clock domains from an MPU percent. Every accepted run must
have successful completion, correct packets and full native cleanup.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from prepare_stream import stock_clock_matches
from recover_stream import sha256

NORMAL = {"n95": "5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9",
          "e90": "E039E983AA042EF1397368151E671FEB8D29BA0828A576139223367CF6FEF5C1"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", choices=("n95", "e90"), required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--version", type=int, choices=(16,17), default=17)
    a = p.parse_args()
    folder = ROOT / "work/evidence" / a.device
    a.out = a.out.resolve()
    a.out.mkdir(parents=True, exist_ok=True)
    prefix = f"stream-worker-v{a.version}-"
    target = a.out / f"{a.device}-worker-stream-v{a.version}-results.json"
    if target.exists():
        p.error("result already exists")

    def publish(path, name):
        destination = a.out / (a.device + "-worker-stream-" + name)
        data = path.read_bytes()
        if destination.exists():
            if destination.read_bytes() != data:
                raise RuntimeError("published evidence differs")
        else:
            destination.write_bytes(data)
        return destination.relative_to(ROOT).as_posix()

    def run(tag, frames, reps, mode, name):
        path = folder / (tag + ".log")
        raw = path.read_bytes()
        text = raw.decode("ascii", errors="replace")
        transport = (folder / (tag + "-transport.txt")).read_text(encoding="utf-8")
        expected = f"WORKER STREAM PASS frames={frames} creates=1 runs=0 useful_arm_crc={frames} mode={mode} reps={reps} total_us="
        for marker in (f"C55STREAM v{a.version} ", expected, "WORKER CLEANUP PASS no_run=1 delete_free_native_close=0", "FINAL status=0"):
            if marker not in text:
                raise RuntimeError("missing run gate: " + marker)
        if "BEGIN execute" in text or "\nKILL " in transport or " KILL " in transport:
            raise RuntimeError("RUN or forced termination in worker run")
        if re.findall(r"^EXIT (.+)$", transport, re.M) != ["0 Kill", "0 Kill"]:
            raise RuntimeError("inspect/experiment must both EXIT0")
        patterns = re.findall(r"frame=(\d+) put=(\d+)/(\d+) get=(\d+)/(\d+) wall_us=(\d+) crc=([0-9a-f]+)\s+"
                              r"issue_us=(\d+) arm_crc_us=(\d+) wait_us=(\d+) completion_observed_us=(\d+)\s+"
                              r"(?:PERF frame=\d+ before=\d+ after=\d+\s+)?"
                              r"result=(-?\d+) expected=(-?\d+) ticks=(\d+) counts_per_ms=(\d+) errors=(\d+) stop=(\d+)", text)
        if len(patterns) != frames:
            raise RuntimeError("wrong number of frame records")
        data = []
        for index, fields in enumerate(patterns, 1):
            values = list(fields)
            if tuple(values[1:5]) != ("0", "0", "0", "0") or values[6] != "cd837cd0" or values[11] != values[12] or values[15] != "0":
                raise RuntimeError("packet status/data/CRC check failed")
            if int(values[0]) != index or int(values[16]) != int(index == frames):
                raise RuntimeError("sequence/stop mismatch")
            keys = ("sequence", "put_submit", "put_done", "get_submit", "get_done", "wall_us", "crc",
                    "issue_us", "arm_crc_us", "wait_us", "completion_observed_us", "result", "expected",
                    "raw_dsp_ticks", "reported_counts_per_ms", "errors", "stop")
            data.append({key: (value if key == "crc" else int(value)) for key, value in zip(keys, values)})
        if a.version==17:
            stamps=re.findall(r"^  dsp_stamp=(\d+)\r?$",text,re.M)
            if len(stamps)!=frames:
                raise RuntimeError("absolute DSP timestamps missing")
            for item,stamp in zip(data,stamps):
                item["dsp_stamp"]=int(stamp)
            percentages=re.findall(r"^PERF frame=(\d+) before=(\d+) after=(\d+)\r?$",text,re.M)
            if a.device=="n95":
                if percentages!=[(str(i),"100","100") for i in range(1,frames+1)]:
                    raise RuntimeError("N95 per-packet MPU conditions changed")
                if "PERF reserve=0 status=0" not in text or "PERF release=0 status=0" not in text:
                    raise RuntimeError("stock performance reservation/release failed")
                for item in data:
                    item["mpu_percent_before"]=item["mpu_percent_after"]=100
            elif "PERF reserve=" in text:
                raise RuntimeError("N95 performance API must not be used on E90")
        total = int(re.search(re.escape(expected) + r"(\d+)", text).group(1))
        if total != sum(x["wall_us"] for x in data):
            raise RuntimeError("frame total differs")
        if not re.search(r"state phase=worker deleted.*?state=5", text, re.S):
            raise RuntimeError("reported deleted state must be 5")
        start_ticks = set(re.findall(r"tick \d+ startTick (\d+) boot", transport))
        if len(start_ticks) != 1:
            raise RuntimeError("daemon changed during run")
        return {"journal": publish(path, name + ".txt"), "journal_sha256": sha256(raw),
                "transport_sha256": sha256((folder / (tag + "-transport.txt")).read_bytes()),
                "daemon_start_tick": int(next(iter(start_ticks))), "frames": frames,
                "reps": reps, "parallel": bool(mode), "total_us": total, "frame_results": data,
                "official_run": False, "exit": 0, "cleanup": "delete/free task/native buffers/close/FINAL0"}

    prep_names = (["stream-worker-v16-one-prepare-03", "stream-worker-v16-multi-prepare-01"]
                  if a.device == "n95" else ["stream-worker-v16-one-prepare-01"])
    if a.version==17:
        prep_names=[prefix+"one-prepare-01"]
    preparations = []
    for name in prep_names:
        path = folder / (name + "-preparation.json")
        proof = json.loads(path.read_text(encoding="utf-8"))
        if not all(proof.get(k) is True for k in ("complete", "stock_clock_guard", "clock_log_restored")):
            raise RuntimeError("preparation failed")
        if not stock_clock_matches((ROOT / proof["clock_log"]).read_text(encoding="ascii"), a.device):
            raise RuntimeError("stock clock evidence differs")
        preparations.append(publish(path, name.replace(prefix, "") + ".json"))
    recover_names = (["stream-worker-v16-one-recovery-02", "stream-worker-v16-multi-recovery-01"]
                     if a.device == "n95" else ["stream-worker-v16-recovery-01"])
    if a.version==17:
        recover_names=[prefix+"recovery-01"]
    recoveries = []
    for name in recover_names:
        path = folder / (name + ".json")
        proof = json.loads(path.read_text(encoding="utf-8"))
        if not proof.get("complete") or not proof.get("dsp_restored") or proof["restored_dsp"]["sha256"] != NORMAL[a.device] or proof["ps"] != ["OK ps 0"]:
            raise RuntimeError("normal DSP restoration or PS0 missing")
        recoveries.append(publish(path, name.replace(prefix, "") + ".json"))
    one = run(prefix+"one-" + ("02" if a.device=="n95" and a.version==16 else "01"),1,0,0,f"one-v{a.version}")
    zero = run(prefix+"multi-zero-01",8,0,0,f"multi-zero-v{a.version}")
    q15 = run(prefix+"q15-01",8,1000,0,f"q15-v{a.version}")
    pairs = []
    for number in range(1, 4):
        serial = run(f"{prefix}pair{number}-serial-01",8,10000,0,f"pair{number}-serial-v{a.version}")
        parallel = run(f"{prefix}pair{number}-parallel-01",8,10000,1,f"pair{number}-parallel-v{a.version}")
        pairs.append({"number": number, "serial": serial, "parallel": parallel,
                      "observed_wall_change_percent": round(100 * (parallel["total_us"] / serial["total_us"] - 1), 3)})
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "device": a.device,
        "artifact": f"worker-stream-v{3 if a.version==17 else 2}-artifacts.json", "preparations": preparations,
        "recoveries": recoveries, "one": one, "multi_zero": zero, "q15": q15, "pairs": pairs,
        "median_serial_total_us": statistics.median(x["serial"]["total_us"] for x in pairs),
        "median_parallel_total_us": statistics.median(x["parallel"]["total_us"] for x in pairs),
        "scope": "Working persistent STRM/Q15 task and useful ARM CRC overlap; timing is provisional",
        "limits": ["Stock clock guard ran before the series; PRCM was not sampled for every packet.",
                   "N95 serial runs contain doubled ARM/DSP timings, consistent with a frequency transition; its cause is not measured.",
                   "Observed wall changes combine overlap and any changed operating conditions; they are not isolated overlap speedups.",
                   "Reported CLK_countspms=164 conflicts with high-resolution ticks versus ARM wall time; no DSP milliseconds are derived.",
                   "512-byte packets only; useful workload is 240-element repeated Q15 dot plus 64KiB CRC per frame.",
                   "Audio coexistence, tail latency, larger packets and application integration are not verified."],
    }
    if a.version==17:
        calibrations=[]
        for number in range(1,4):
            tag=prefix+f"calibrate-{number:02d}"
            path=folder/(tag+".log")
            raw=path.read_bytes();text=raw.decode("ascii")
            transport_path=folder/(tag+"-transport.txt")
            transport=transport_path.read_text(encoding="utf-8")
            markers=("C55STREAM v17 ","WORKER CALIBRATION PASS frames=8 creates=1 runs=0 intervals=7 no_crc=1",
                     "WORKER CLEANUP PASS no_run=1 delete_free_native_close=0","FINAL status=0")
            if any(marker not in text for marker in markers) or "BEGIN execute" in text or re.search(r"^> KILL",transport,re.M):
                raise RuntimeError("calibration run gate failed")
            if re.findall(r"^EXIT (.+)$",transport,re.M)!=["0 Kill","0 Kill"]:
                raise RuntimeError("calibration inspect/experiment must EXIT0")
            if a.device=="n95" and ("PERF reserve=0 status=0" not in text or "PERF release=0 status=0" not in text):
                raise RuntimeError("calibration reservation/release failed")
            if a.device=="e90" and "PERF reserve=" in text:
                raise RuntimeError("N95 performance API must not be used on E90")
            hz=int(re.search(r"fast_counter_hz=(\d+)",text).group(1))
            values=lambda line:{k:int(v) for k,v in re.findall(r"\b([a-z_]+)=(-?\d+)",line)}
            frame_lines=[line for line in text.splitlines() if line.startswith("CAL frame=")]
            conditions=[values(line) for line in text.splitlines() if line.startswith("CAL conditions ")]
            intervals=[values(line) for line in text.splitlines() if line.startswith("CAL interval=")]
            frames=[values(line) for line in frame_lines]
            if len(frames)!=8 or len(conditions)!=8 or len(intervals)!=7:
                raise RuntimeError("calibration record count differs")
            for index,(frame,line,condition) in enumerate(zip(frames,frame_lines,conditions),1):
                if frame["frame"]!=index or condition["frame"]!=index or frame["errors"] or "put=0/0 get=0/0" not in line:
                    raise RuntimeError("calibration correctness/status failed")
                if a.device=="n95" and (condition["perf_before"]!=100 or condition["perf_after"]!=100):
                    raise RuntimeError("calibration MPU changed")
                frame.update(condition)
            for index,item in enumerate(intervals,1):
                first,last=frames[index-1:index+1]
                low=((last["begin"]-first["done"])&0xffffffff)-1
                high=((last["done"]-first["begin"])&0xffffffff)+1
                dsp=(last["dsp_stamp"]-first["dsp_stamp"])&0xffffffff
                if (item["interval"]!=index or item["dsp_delta"]!=dsp or item["arm_min_ticks"]!=low or
                    item["arm_max_ticks"]!=high or low<=0 or item["hz_min"]!=dsp*hz//high or item["hz_max"]!=dsp*hz//low):
                    raise RuntimeError("timestamp bracket/rate calculation differs")
                item["nominal_19_2mhz_inside_bounds"]=item["hz_min"]<=19200000<=item["hz_max"]
                item["requested_delay_ms"]=last["delay_ms"]
            calibrations.append({"journal":publish(path,f"calibrate-{number:02d}-v17.txt"),"journal_sha256":sha256(raw),
                                 "transport_sha256":sha256(transport_path.read_bytes()),"fast_counter_hz":hz,
                                 "frames":frames,"intervals":intervals,"exit":0})
        result["calibrations"]=calibrations
        short=[item for cal in calibrations for item in cal["intervals"] if item["requested_delay_ms"]<=400]
        long=[item for cal in calibrations for item in cal["intervals"] if item["requested_delay_ms"]==800]
        result["timer_short_interval_intersection_hz"]=[max(item["hz_min"] for item in short),min(item["hz_max"] for item in short)]
        result["timer_800ms_bounds_hz"]=[[item["hz_min"],item["hz_max"]] for item in long]
        result["mpu_stock_reservation"]=a.device=="n95"
        result["scope"]="Correct persistent STRM/Q15 and useful ARM overlap; N95 stock MPU reservation, cross-packet timer bounds"
        result["limits"]=["Only N95 MPU percent is monitored per packet; not every DSP/bus clock domain.",
                          "Short-interval rate and 800ms idle rate may differ; timer is not assumed continuously wall-clock calibrated.",
                          "No DSP milliseconds are derived from reported counts/ms164.",
                          "512-byte packets, repeated dot240 and ARM CRC64KiB; no application speedup inferred.",
                          "Larger packets, long stability and audio coexistence remain unverified."]
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(target), "pairs": [(x["serial"]["total_us"], x["parallel"]["total_us"], x["observed_wall_change_percent"]) for x in pairs]}, indent=2))


if __name__ == "__main__":
    main()
