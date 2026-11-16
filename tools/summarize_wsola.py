"""Verify all v19/v20 WSOLA records and cleanup before publishing measurements."""
import argparse
import datetime
import json
import math
from pathlib import Path
import re
import statistics
import zlib

from prepare_stream import stock_clock_matches
from summarize_packet_sizes import sha, numbers, stats
from summarize_worker_stream import NORMAL
from wsola_vectors import vector

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", choices=("n95", "e90"), required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--version", type=int, choices=(19, 20), default=19)
    a = p.parse_args()
    a.out = a.out.resolve()
    folder = ROOT / "work/evidence" / a.device
    prefix = f"wsola-v{a.version}"
    revision = {19: 5, 20: 6}[a.version]
    target = a.out / f"{a.device}-{prefix}-results.json"
    if target.exists():
        p.error("new result required")
    publications = []
    def publish(path, suffix):
        dest = a.out / f"{a.device}-{prefix}-{suffix}"
        raw = path.read_bytes()
        if dest.exists() and dest.read_bytes() != raw:
            raise RuntimeError("publication differs: " + str(dest))
        publications.append((dest, raw))
        return dest.relative_to(ROOT).as_posix()
    def require(condition, message):
        if not condition:
            raise RuntimeError(message)

    artifact = json.loads((a.out / f"worker-stream-v{revision}-artifacts.json").read_text())
    require(artifact["host_version"] == artifact["protocol"] == a.version, "artifact version")
    prep_path = folder / f"{prefix}-prepare-01-preparation.json"
    recovery_path = folder / f"{prefix}-recovery-01.json"
    series_path = folder / f"{prefix}-pairs-series.json"
    prep, recovery, series = [json.loads(path.read_text()) for path in (prep_path, recovery_path, series_path)]
    require(all(prep.get(k) is True for k in ("complete", "stock_clock_guard", "clock_log_restored")), "preparation")
    require(prep["device"] == a.device and series["device"] == a.device, "device identity")
    clock_path = ROOT / prep["clock_log"]
    require(stock_clock_matches(clock_path.read_text(encoding="ascii"), a.device), "stock clocks")
    require(recovery["complete"] and recovery["dsp_restored"] and recovery["restored_dsp"]["equal"] and
            recovery["restored_dsp"]["sha256"] == NORMAL[a.device] and recovery["ps"] == ["OK ps 0"], "restoration")
    deployed = [r for r in prep["files"] if r["remote"] == "E:\\c55stream.dll55l" and r.get("equal")]
    require(len(deployed) == 1 and deployed[0]["sha256"] == artifact["sha256"] and
            sha((ROOT / deployed[0]["readback"]).read_bytes()) == artifact["sha256"], "DSP image")
    if a.device == "n95":
        host = next(r for r in prep["files"] if r["remote"] == "E:\\sys\\bin\\c55stream.exe" and r.get("equal"))
        require(host["sha256"] == artifact["host_sha256"], "N95 host")
    else:
        host = json.loads((a.out / f"e90-host-v{a.version}-installed.json").read_text())["host_readback"]
        require(host["expected_equal"] and host["sha256"] == artifact["host_sha256"], "E90 host")
    daemon_tick = re.search(r"startTick (\d+)", "\n".join(prep["info_after"]))[1]
    require(set(re.findall(r"startTick (\d+)", "\n".join(recovery["info_after"]))) == {daemon_tick}, "recovery reboot")
    fixtures = json.loads((a.out / "wsola-v19-vectors.json").read_text())
    require(fixtures["vectors"] == [vector(i) for i in range(1, 33)], "independent fixtures")
    require(series["complete"] and series["orders"] == [[0, 1], [1, 0], [0, 1]] and len(series["runs"]) == 6, "series")
    for index, row in enumerate(series["runs"]):
        round_no = index // 2 + 1
        require(row["exit_code"] == 0 and row["round"] == round_no and
                row["reps"] == series["orders"][round_no - 1][index % 2], "series status/order")
        require(row["tag"] == f"{prefix}-pairs-reps{row['reps']}-r{round_no}-01", "series tag")

    def envelope(tag):
        path = folder / (tag + ".log")
        raw = path.read_bytes(); text = raw.decode("ascii")
        transport_path = folder / (tag + "-transport.txt")
        transport = transport_path.read_text()
        profile = (folder / (tag + "-profile.log")).read_text()
        uid = {"n95": "20002d84", "e90": "20002496"}[a.device]
        require(text.startswith(f"C55STREAM v{a.version} ") and f"machine={uid} " in text.splitlines()[0], tag + " profile")
        require(profile.startswith(f"C55STREAM v{a.version} ") and profile.rstrip().endswith("FINAL status=0"), tag + " inspect")
        required = ("profile guard=0", "create=0 status=0 ", "delete=0 status=0",
                    "state phase=worker deleted rc=0", "  state=5 ", "free task=0",
                    "free native out=0", "free native in=0", "BEGIN close",
                    "WORKER CLEANUP PASS no_run=1 delete_free_native_close=0")
        require(all(s in text for s in required) and text.rstrip().endswith("FINAL status=0"), tag + " lifecycle")
        require(not any(s in text for s in ("BEGIN execute", "cancel input=", "cancel output=")), tag + " RUN/cancel")
        require(re.findall(r"^EXIT (.+)$", transport, re.M) == ["0 Kill", "0 Kill"] and
                not re.search(r"\bKILL ", transport), tag + " exits")
        require(set(re.findall(r"startTick (\d+)", transport)) == {daemon_tick}, tag + " daemon restart")
        require(sha((folder / (tag + "-prepared-dsp.dll55l")).read_bytes()) == artifact["sha256"], tag + " DSP")
        if a.device == "n95":
            require(re.search(r"PERF reserve=0 status=0 before=\d+ after=100", text) and
                    re.search(r"PERF release=0 status=0 after=\d+", text), tag + " MPU")
        hz = int(re.search(r"fast_counter_hz=(\d+)", text)[1])
        require(hz > 0, tag + " counter")
        result = {"tag": tag, "journal": publish(path, tag.removeprefix(prefix + "-") + ".txt"),
                  "journal_sha256": sha(raw), "transport": publish(transport_path, tag.removeprefix(prefix + "-") + "-transport.txt"),
                  "transport_sha256": sha(transport_path.read_bytes()), "fast_counter_hz": hz,
                  "create_us": int(re.search(r"create=0 status=0 wall_us=(\d+)", text)[1]),
                  "status": "FINAL0/EXIT0, CREATED1/DELETED5/free/close0, no RUN or cancel"}
        return text, result

    text, echo = envelope(prefix + "-echo-one-01")
    expected_crc = zlib.crc32(bytes((i * 13 + 7) & 255 for i in range(65536)))
    require("WORKER STREAM PASS frames=1 creates=1 runs=0 useful_arm_crc=1 mode=0 reps=0 " in text and
            f"SIZE frame=1 input_bytes=512 output_bytes=512 returned_words=256 protocol={a.version} checked_payload_words=240" in text and
            "result=0 expected=0" in text and "errors=0 stop=1" in text and f"crc={expected_crc:08x}" in text, "echo packet")

    def verify(tag, reps, count):
        text, result = envelope(tag)
        require(f"WORKER WSOLA PASS frames={count} creates=1 runs=0 reps={reps} input_bytes=1792 output_bytes=48 " in text,
                tag + " PASS")
        records = []; current = None
        for line in text.splitlines():
            if line.startswith("WSOLA frame="):
                if current is not None: records.append(current)
                match = re.fullmatch(r"WSOLA frame=(\d+) case=(\d+) reps=(\d+) put=0/0 get=0/0 errors=0 stop=([01])", line)
                require(match, tag + " transfer")
                current = dict(zip(("frame", "case", "reps", "stop"), map(int, match.groups())))
            elif current is not None and line.startswith("WSOLA "):
                kind = line.split()[1]
                require(kind in ("result", "reference", "timing", "size") and kind not in current, tag + " record kind")
                values = numbers(line)
                require(values["frame"] == current["frame"], tag + " record sequence")
                current[kind] = values
            elif current is not None and line.startswith("PERF frame="):
                current["perf"] = numbers(line)
        if current is not None: records.append(current)
        require(len(records) == count, tag + " record count")
        hz = result["fast_counter_hz"]
        for index, record in enumerate(records, 1):
            fixture = vector(index)
            require(record["frame"] == index and record["case"] == fixture["case"] and record["reps"] == reps and
                    record["stop"] == int(index == count), tag + " header")
            wire = record["result"]; ref = record["reference"]; size = record["size"]; timing = record["timing"]
            for key in ("offset", "score", "scored"):
                value = fixture[key] if reps else 0
                require(wire[key] == wire["expected_" + key] == value, tag + " DSP " + key)
                require(ref[key] == fixture[key], tag + " ARM " + key)
            require(wire["input_sum"] == wire["expected_sum"] == fixture["input_sum"] and
                    ref["arm_last"] == fixture["offset"], tag + " input/reference")
            require(all(size[k] == v for k, v in {"input_bytes": 1792, "output_bytes": 48,
                    "input_words": 896, "output_words": 24, "protocol": a.version, "operation": 1, "case": fixture["case"]}.items()), tag + " sizes")
            require(timing["arm_iterations"] == 16 and timing["arm_ticks"] > 0 and
                    timing["arm_first"] == index % 2 and timing["end_to_end_ticks"] >= timing["transfer_ticks"] + timing["pack_ticks"] and
                    timing["transfer_ticks"] * 1e6 / hz >= timing["issue_us"] and timing["counts_per_ms"] == 164, tag + " timing")
            if reps:
                require(timing["raw_dsp_ticks"] > 0, tag + " compute timer")
            if a.device == "n95":
                require(record["perf"] == {"frame": index, "before": 100, "after": 100}, tag + " per-packet MPU")
            record["fixture_sha256"] = fixture["packed_sha256"]
            record["arm_per_search_us"] = timing["arm_ticks"] * 1e6 / hz / 16
            record["pack_us"] = timing["pack_ticks"] * 1e6 / hz
            record["completion_us"] = timing["transfer_ticks"] * 1e6 / hz
            record["end_to_end_us"] = timing["end_to_end_ticks"] * 1e6 / hz
            record["saving_us"] = record["arm_per_search_us"] - record["end_to_end_us"]
        result.update(reps=reps, frames=count, records=records,
                      end_to_end=stats([r["end_to_end_us"] for r in records]))
        return result

    runs = [verify(prefix + "-short-one-01", 0, 1), verify(prefix + "-compute-one-01", 1, 1)]
    for row in series["runs"]:
        run = verify(row["tag"], row["reps"], 32); run["round"] = row["round"]; runs.append(run)
    aggregate = {}
    for reps in (0, 1):
        records = [r for run in runs if run.get("round") and run["reps"] == reps for r in run["records"]]
        aggregate[str(reps)] = {key: stats([r[key] for r in records]) for key in
                               ("arm_per_search_us", "pack_us", "completion_us", "end_to_end_us", "saving_us")}
        aggregate[str(reps)]["by_case"] = {str(case): {key: stats([r[key] for r in records if r["case"] == case]) for key in
                                                     ("arm_per_search_us", "end_to_end_us", "saving_us")} for case in range(8)}
    kernel = [r for run in runs if run.get("round") and run["reps"] == 1 for r in run["records"]]
    median_saving = statistics.median(r["saving_us"] for r in kernel)
    create_median = statistics.median(run["create_us"] for run in runs if run.get("round"))
    report = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "device": a.device,
              "host_version": a.version, "protocol": a.version, "artifact": f"docs/evidence/2026-10-01/worker-stream-v{revision}-artifacts.json",
              "host_sha256": artifact["host_sha256"], "dsp_sha256": artifact["sha256"],
              "preparation": publish(prep_path, "preparation.json"), "clock_journal": publish(clock_path, "clock.txt"),
              "recovery": publish(recovery_path, "recovery.json"), "series": publish(series_path, "series.json"),
              "echo": echo, "runs": runs, "successful_runs": len(runs) + 1,
              "correct_packets": 1 + sum(run["frames"] for run in runs), "wsola_packets": sum(run["frames"] for run in runs),
              "real_search_packets": sum(run["frames"] for run in runs if run["reps"] == 1),
              "aggregate": aggregate, "create_median_us": create_median,
              "break_even": {"median_same_packet_saving_us": median_saving,
                             "create_only_minimum_packets": math.floor(create_median / median_saving) + 1 if median_saving > 0 else None,
                             "hop_us": 220 * 1e6 / 44100,
                             "kernel_median_as_fraction_of_hop": aggregate["1"]["end_to_end_us"]["median_us"] / (220 * 1e6 / 44100)},
              "originals_restored": True,
              "limits": ["ARM batch16 mean compares the original algorithm compiled by this harness; compiler flags must be disclosed.",
                         "DSP cost includes stereo-left packing, input range/checksum, driver transfer, scheduling and compute; excludes generation, validation and logging.",
                         "No-op is the same1792/48 wire path with checksum and no search, not pure DMA.",
                         "ARM counter resolution is about30.5us. Raw DSP ticks/configured164 are diagnostic only.",
                         "Synthetic edge/tie datasets and benchmark LCG do not establish live audio deadlines or PS1 speedup.",
                         "No audio coexistence, long-session stability, invalid-input or timeout lifecycle result is inferred.",
                         "Creation-only break-even omits other session startup costs and assumes reuse of one resident node."]}
    a.out.mkdir(parents=True, exist_ok=True)
    for path, raw in publications:
        path.write_bytes(raw)
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(target), "runs": report["successful_runs"], "packets": report["correct_packets"],
                      "aggregate": aggregate, "break_even": report["break_even"]}, indent=2))


if __name__ == "__main__":
    main()
