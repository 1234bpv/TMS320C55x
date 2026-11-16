"""Recompute WSOLA evidence from versioned journals, without phone/work files."""
import json
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import stats
from verify_ring_publication import ROOT, checked


def main():
    result = json.loads((ROOT / "docs/evidence/2026-10-04/n95-wsola63-results.json").read_text())
    proof = json.loads((ROOT / "docs/evidence/2026-10-04/n95-wsola63-artifacts.json").read_text())
    hashes = {item["path"]: item["sha256"] for item in proof["files"]}
    assert result["host_sha256"] == hashes["out/arm/c55stream.exe"]
    assert result["DSP_sha256"] == hashes["out/dsp/c55stream-dmm-ring-wsola.dll55l"]
    assert [run["jobs"] for run in result["runs"]] == [8,120,120,120]
    records = []
    for run in result["runs"]:
        text = checked(run["published_journal"], run["published_sha256"])
        validate_journal(text, run["command"], 48)
        hz = int(re.search(r"fast_counter_hz=(\d+)", text)[1])
        assert hz == run["fast_counter_hz"] == 32768
        lifecycle = re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0", text)
        assert list(map(int, lifecycle.groups())) == [run["setup_us"],run["teardown_us"]]
        timing = re.findall(r"RING WSOLA TIMING frame=(\d+) arm_iterations=16 arm_ticks=(\d+) arm_first=([01]) pack_ticks=(\d+) transfer_ticks=(\d+) end_to_end_ticks=(\d+) cpu_us=(\d+) raw_dsp_ticks=(\d+) counts_per_ms=(\d+)", text)
        results = re.findall(r"RING WSOLA RESULT frame=(\d+) case=(\d+) slot=(\d+) offset=(\d+) expected_offset=(\d+) score=(-?\d+) expected_score=(-?\d+) scored=(\d+) expected_scored=(\d+) errors=0 checked_words=1280", text)
        dcr = re.findall(r"DCR READ frame=(\d+) protocol=40 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01])", text)
        assert len(timing) == len(results) == len(dcr) == len(run["records"]) == run["jobs"]
        for record, row, output, reading in zip(run["records"], timing, results, dcr):
            t, o = list(map(int,row)), list(map(int,output))
            assert o[3] == o[4] and o[5] == o[6] and o[7] == o[8]
            assert [record[key] for key in ("frame","case","slot","offset","score","scored")] == [o[i] for i in (0,1,2,3,5,7)]
            assert [record[key] for key in ("frame","arm_ticks","arm_first","pack_ticks","transfer_ticks","end_to_end_ticks","raw_thread_cpu_us","raw_DSP_ticks","raw_CLK_countspms")] == t
            assert record["A_arm_us"] == t[1]*1000000/hz/16
            assert record["H_plus_D_us_including_pack_result_load"] == t[5]*1000000/hz
            assert record["S_us_instrumented"] == run["setup_us"]+run["teardown_us"]
            assert reading == (str(record["frame"]),"0000","0000","0","0")
            assert record["DCR_before"] == record["DCR_after"] == "0000"
        if not run["pilot"]:
            records.extend(run["records"])
    def verify_aggregate(selected, aggregate):
        a = [r["A_arm_us"] for r in selected]
        h = [r["H_plus_D_us_including_pack_result_load"] for r in selected]
        assert aggregate["samples"] == len(selected)
        assert aggregate["A_arm_us"] == stats(a) and aggregate["H_plus_D_us"] == stats(h)
        assert aggregate["blocking_winners_without_setup"] == sum(hd < arm for hd,arm in zip(h,a))
        for n in (16,64,256,1000):
            assert aggregate["W_strict_threshold_us_scenarios"][str(n)] == stats([hd+r["S_us_instrumented"]/n-arm for r,hd,arm in zip(selected,h,a)])
            assert aggregate["setup_condition_S_over_N_less_than_A_samples"][str(n)] == sum(r["S_us_instrumented"]/n<arm for r,arm in zip(selected,a))
            assert aggregate["blocking_gain_with_setup_samples"][str(n)] == sum(hd+r["S_us_instrumented"]/n<arm for r,hd,arm in zip(selected,h,a))
    verify_aggregate(records,result["aggregate"])
    for case in range(8):
        verify_aggregate([r for r in records if r["case"]==case], result["cases"][str(case)])
    assert result["jobs"] == len(records) == 360
    assert result["CPU_samples_exceeding_transfer_wall"] == sum(r["raw_thread_cpu_us"] > r["transfer_ticks"]*1000000/32768 for r in records) == 320
    assert not result["CPU_usage_qualified"] and not result["useful_ARM_W_measured"]
    assert result["S_us_instrumented"] == stats([run["setup_us"]+run["teardown_us"] for run in result["runs"] if not run["pilot"]])
    assert len(result["clocks"]) == 6
    for clock in result["clocks"]:
        assert clock["stock_verified"] and stock_clock_matches("".join(checked(p["published_path"],p["published_sha256"]) for p in clock["probes"]),"n95")
    restoration = result["restoration"]
    restored = json.loads(checked(restoration["published_path"],restoration["published_sha256"]))
    assert restored["complete"] and restored["files"] == restoration["files"]
    assert len(restored["files"])==5 and all(item["equal_original"] for item in restored["files"])
    assert restored["c55stream_processes"] == restored["ocprobe_processes"] == ["OK ps 0"]
    audit = json.loads((ROOT / "docs/evidence/2026-10-04/n95-wsola63-instruction-audit.json").read_text())
    assert audit["DSP_sha256"] == result["DSP_sha256"] and audit["helper_code_hex"] == "A45102004804"
    assert audit["helper_io_writes"] == 0 and audit["call_order"] == "DCR read -> ring_wsola_exchange -> DCR read"
    print("Verified N95 WSOLA63: 8 pilot + 360 paired jobs, exact outputs, timing/scenario recomputation, six stock brackets and five-original restoration; CPU usage unqualified.")


if __name__ == "__main__":
    main()
