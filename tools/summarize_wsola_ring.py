"""Publish actual N95 WSOLA-ring measurements separately from synthetic rings."""
import json
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT, boot, digest, load, publish_text, stats

DEST = ROOT / "docs/evidence/2026-10-04"
SESSION = ROOT / "work/evidence/n95/d0-20261003-clean34"


def main():
    proof = load(DEST / "n95-wsola63-artifacts.json")
    hashes = {item["path"]: item["sha256"] for item in proof["files"]}
    runs, clocks, all_records = [], [], []
    for series, tag, frames in [(0, "wsola63-pilot-f8-01", 8)] + [
            (s, f"wsola63-stock01-s{s}-run", 120) for s in (1,2,3)]:
        report = load(SESSION / (tag + ".json"))
        source = SESSION / (tag + ".log")
        text = source.read_text(encoding="ascii")
        command = f"dmm-ring-wsola frames={frames}"
        assert report["complete"] and report["exit"] == ["EXIT 0 Kill"]
        assert boot(report) == boot(report, "info_after") == "62209 boot 0 by n"
        assert digest(source) == report["journal_sha256"]
        assert report["host_sha256"] == hashes["out/arm/c55stream.exe"]
        assert report["dsp_sha256"] == hashes["out/dsp/c55stream-dmm-ring-wsola.dll55l"]
        validate_journal(text, command, 48)
        hz = int(re.search(r"fast_counter_hz=(\d+)", text)[1])
        lifecycle = re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0", text)
        setup, teardown = map(int, lifecycle.groups())
        results = re.findall(r"RING WSOLA RESULT frame=(\d+) case=(\d+) slot=(\d+) offset=(\d+) expected_offset=(\d+) score=(-?\d+) expected_score=(-?\d+) scored=(\d+) expected_scored=(\d+) errors=0 checked_words=1280", text)
        timings = re.findall(r"RING WSOLA TIMING frame=(\d+) arm_iterations=16 arm_ticks=(\d+) arm_first=([01]) pack_ticks=(\d+) transfer_ticks=(\d+) end_to_end_ticks=(\d+) cpu_us=(\d+) raw_dsp_ticks=(\d+) counts_per_ms=(\d+)", text)
        dcr = re.findall(r"DCR READ frame=(\d+) protocol=40 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01])", text)
        records = []
        for result, timing, reading in zip(results, timings, dcr):
            r, t = list(map(int,result)), list(map(int,timing))
            assert r[0] == t[0] == int(reading[0])
            assert reading[1:] == ("0000","0000","0","0")
            records.append({"frame": r[0], "case": r[1], "slot": r[2], "offset": r[3],
                            "score": r[5], "scored": r[7], "arm_iterations": 16,
                            "arm_ticks": t[1], "arm_first": t[2], "pack_ticks": t[3],
                            "transfer_ticks": t[4], "end_to_end_ticks": t[5],
                            "raw_thread_cpu_us": t[6], "raw_DSP_ticks": t[7], "raw_CLK_countspms": t[8],
                            "A_arm_us": t[1]*1000000/hz/16,
                            "H_plus_D_us_including_pack_result_load": t[5]*1000000/hz,
                            "DCR_before": reading[1], "DCR_after": reading[2],
                            "S_us_instrumented": setup+teardown})
        published = DEST / ("n95-" + tag + ".txt")
        runs.append({"series": series, "pilot": series == 0, "command": command,
                     "jobs": frames, "fast_counter_hz": hz, "setup_us": setup,
                     "teardown_us": teardown, "records": records,
                     "published_journal": published.relative_to(ROOT).as_posix(),
                     "published_sha256": publish_text(source, published)})
        if series:
            all_records.extend(records)
    for series in (1,2,3):
        for position in ("before", "after"):
            tag = f"wsola63-stock01-s{series}-clock-{position}"
            report = load(SESSION / (tag + ".json"))
            assert report["complete"] and boot(report) == boot(report, "info_after") == "62209 boot 0 by n"
            combined, probes = "", []
            for probe in report["probes"]:
                source = SESSION / probe["path"]
                assert digest(source) == probe["sha256"]
                combined += source.read_text(encoding="ascii")
                published = DEST / ("n95-" + source.stem + ".txt")
                probes.append({"published_path": published.relative_to(ROOT).as_posix(),
                               "published_sha256": publish_text(source, published)})
            assert stock_clock_matches(combined, "n95") and report["stock_verified"]
            clocks.append({"series": series, "position": position, "stock_verified": True, "probes": probes})
    def aggregate(records):
        return {"samples": len(records), "A_arm_us": stats([r["A_arm_us"] for r in records]),
                "H_plus_D_us": stats([r["H_plus_D_us_including_pack_result_load"] for r in records]),
                "blocking_winners_without_setup": sum(r["H_plus_D_us_including_pack_result_load"] < r["A_arm_us"] for r in records),
                "W_strict_threshold_us_scenarios": {
                    str(n): stats([r["H_plus_D_us_including_pack_result_load"] + r["S_us_instrumented"]/n - r["A_arm_us"] for r in records])
                    for n in (16,64,256,1000)},
                "setup_condition_S_over_N_less_than_A_samples": {
                    str(n): sum(r["S_us_instrumented"]/n < r["A_arm_us"] for r in records)
                    for n in (16,64,256,1000)},
                "blocking_gain_with_setup_samples": {
                    str(n): sum(r["H_plus_D_us_including_pack_result_load"] + r["S_us_instrumented"]/n < r["A_arm_us"] for r in records)
                    for n in (16,64,256,1000)}}
    restoration_source = SESSION / "wsola63-final-verify01.json"
    restored = load(restoration_source)
    assert restored["complete"] and len(restored["files"]) == 5
    assert all(item["equal_original"] for item in restored["files"])
    assert restored["c55stream_processes"] == restored["ocprobe_processes"] == ["OK ps 0"]
    target = DEST / "n95-wsola63-final-verify01.json"
    result = {"scope": "actual WSOLA coarse/refine search through native16KiB ring; distinct N95 candidate63/host48/protocol40",
              "status": "measurement_complete", "plan_status": "in_progress", "jobs": 360, "pilot_jobs_separate": 8,
              "host_sha256": hashes["out/arm/c55stream.exe"], "DSP_sha256": hashes["out/dsp/c55stream-dmm-ring-wsola.dll55l"],
              "runs": runs, "clocks": clocks, "aggregate": aggregate(all_records),
              "cases": {str(case): aggregate([r for r in all_records if r["case"] == case]) for case in range(8)},
              "S_us_instrumented": stats([run["setup_us"]+run["teardown_us"] for run in runs if not run["pilot"]]),
              "capacity": {"ring_total_bytes": 16384, "input_slots_per_job": 4, "output_slots_per_job": 1,
                           "audio_words": 880, "checked_words_per_job": 1280, "scratch_node_words": 880},
              "WPE_disabled_all_720_series_readings": True, "useful_ARM_W_measured": False,
              "CPU_usage_qualified": False,
              "CPU_samples_exceeding_transfer_wall": sum(r["raw_thread_cpu_us"] > r["transfer_ticks"]*1000000/32768 for r in all_records),
              "decision": "Keep current WSOLA implementation. No consistent blocking speedup: most paired ring H+D samples exceed the scalar ARM baseline even before setup amortization. Parallel gain is conditional on sufficient independent useful ARM W, which this host does not execute. No SMLAD baseline or emulator integration measured.",
              "restoration": {"utc": restored["utc"], "files": restored["files"],
                              "published_path": target.relative_to(ROOT).as_posix(),
                              "published_sha256": publish_text(restoration_source, target)},
              "limits": ["ARM baseline averages sixteen warm scalar calls; alternates before/after each packet; no performance reservation or continuous DVFS trace",
                         "Stock clock brackets are snapshots, not a guarantee of constant ARM frequency inside each timing interval",
                         "CLK_countspms=164 is not used to convert raw DSP ticks; native v17 calibration showed inconsistent wall-time scale",
                         "Per-frame GetCpuTime deltas often exceed transfer wall time; retain raw values and do not infer offload CPU percentage",
                         "Current DCR samples qualify this new experiment only; full endpoint-publication contract remains separate",
                         "Setup includes logging; correctness/reference checking outside measured intervals is instrumentation",
                         "W threshold scenarios require the independent strict setup condition S/N<A; thresholds alone do not prove possible gain",
                         "MDEC/SPU ring kernels and emulator integration remain unmeasured; E90 deferred by user"]}
    path = DEST / "n95-wsola63-results.json"
    path.write_bytes((json.dumps(result, indent=2)+"\n").encode("utf-8"))
    print(json.dumps({"path":str(path), "A_p50_us":result["aggregate"]["A_arm_us"]["p50"],
                      "H_plus_D_p50_us":result["aggregate"]["H_plus_D_us"]["p50"],
                      "S_p50_us":result["S_us_instrumented"]["p50"]}))


if __name__ == "__main__":
    main()
