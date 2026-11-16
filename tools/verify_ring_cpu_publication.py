"""Verify CPU-window64 journals/timing/math with no phone or ignored files."""
import json
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import stats
from verify_ring_publication import ROOT, checked


def main():
    result=json.loads((ROOT / "docs/evidence/2026-10-04/n95-ring-cpu64-results.json").read_text())
    proof=json.loads((ROOT / "docs/evidence/2026-10-04/n95-window64-artifacts.json").read_text())
    hashes={f["path"]:f["sha256"] for f in proof["files"]}
    assert result["host_sha256"]==hashes["out/arm/c55stream.exe"]
    assert result["DSP_sha256"]==hashes["out/dsp/c55stream-dmm-ring-window.dll55l"]
    assert len(result["runs"])==13 and sum(r["packets"] for r in result["runs"] if not r["pilot"])==9360
    for run in result["runs"]:
        text=checked(run["published_journal"],run["published_sha256"])
        validate_journal(text,run["command"],49)
        window=re.search(r"RING CPU WINDOW frames=(\d+) batch=(\d+) outer_ticks=(\d+) loop_ticks=(\d+) final_yield_ticks=(\d+) cpu_us=(\d+)",text)
        assert list(map(int,window.groups()))==[run[k] for k in ("frames","batch","outer_ticks","loop_ticks","final_yield_ticks","CPU_us")]
        rows=re.findall(r"RING FRAME frame=(\d+) slot=(\d+) batch=(\d+) packet_start=(\d+) wall_us=(\d+) cpu_us=-1 bad_words=0 dsp_ticks=(\d+)",text)
        assert [int(r[4]) for r in rows]==run["exchange_wall_us"]
        assert [int(r[5]) for r in rows]==run["raw_DSP_ticks"]
        for ticks,wall in (("outer_ticks","outer_wall_us"),("loop_ticks","loop_wall_us"),("final_yield_ticks","final_yield_us")):
            assert run[wall]==run[ticks]*1000000/32768
        assert run["CPU_percent_including_final_yield"]==100*run["CPU_us"]/run["outer_wall_us"]
        assert run["CPU_us"]*32768<=(run["outer_ticks"]+2)*1000000
        lifecycle=re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text)
        assert list(map(int,lifecycle.groups()))==[run["setup_us"],run["teardown_us"]]
    assert {(r["series"],r["batch"]) for r in result["runs"] if not r["pilot"]}=={(s,b) for s in (1,2,3) for b in (1,2,8,15)}
    for batch,aggregate in result["aggregate"].items():
        selected=[r for r in result["runs"] if not r["pilot"] and r["batch"]==int(batch)]
        cpu=sum(r["CPU_us"] for r in selected); outer=sum(r["outer_wall_us"] for r in selected)
        payload=sum(r["packets"]*960 for r in selected)
        wall=[v for r in selected for v in r["exchange_wall_us"]]
        assert aggregate["exchange_wall_us"]==stats(wall)
        assert aggregate["CPU_us_per_window"]==stats([r["CPU_us"] for r in selected])
        assert aggregate["outer_wall_us_per_window"]==stats([r["outer_wall_us"] for r in selected])
        assert aggregate["raw_DSP_ticks"]==stats([v for r in selected for v in r["raw_DSP_ticks"]])
        assert aggregate["weighted_CPU_percent_including_final_yield"]==100*cpu/outer
        assert aggregate["useful_bidirectional_MB_s_exchange_intervals"]==payload/sum(wall)
        assert aggregate["useful_bidirectional_MB_s_full_window_including_pack_checks_yield"]==payload/outer
    assert len(result["clocks"])==6 and result["CPU_window_checks_passed"]
    for clock in result["clocks"]:
        assert clock["stock_verified"] and stock_clock_matches("".join(checked(p["published_path"],p["published_sha256"]) for p in clock["probes"]),"n95")
    restoration=result["restoration"]
    saved=json.loads(checked(restoration["published_path"],restoration["published_sha256"]))
    assert saved["complete"] and saved["files"]==restoration["files"]
    assert len(saved["files"])==5 and all(f["equal_original"] for f in saved["files"])
    assert saved["c55stream_processes"]==saved["ocprobe_processes"]==["OK ps 0"]
    print("Verified separate N95 CPU64: pilot120 + 9360 packets/12 runs, settled aggregate CPU scope, six stock snapshots and five-original restoration.")


if __name__=="__main__":
    main()
