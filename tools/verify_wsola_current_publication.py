"""Recalculate published current ARM WSOLA results, including interruption boundary."""
import json
import re

from wsola_current_session_support import validate_current
from prepare_stream import stock_clock_matches
from summarize_ring import stats
from verify_ring_publication import ROOT,checked


def main():
    dest=ROOT/"docs/evidence/2026-10-04"; result=json.loads((dest/"n95-wsola68-results.json").read_text()); proof=json.loads((dest/"n95-wsola68-artifacts.json").read_text())
    files={r["path"]:r["sha256"] for r in proof["files"]}; assert result["host_sha256"]==files["out/arm/c55stream.exe"] and result["DSP_sha256"]==files["out/dsp/c55stream-dmm-ring-wsola.dll55l"]
    prior=json.loads((dest/"n95-wsola63-results.json").read_text()); assert result["DSP_sha256"]==prior["DSP_sha256"] and proof["DSP_reused_exact63"]
    assert proof["current_ARM_SMLAD_instruction_sites"]==5
    for p in ("src/wsola_current/kernel.inc","src/wsola_current/kernel.cpp","src/wsola_current/snapshot.json","src/wsola_current/ring_host.inc"):
        checked(p,files[p])
    assert [r["jobs"] for r in result["runs"]]==[8,120,120,120]; rows=[]
    for run in result["runs"]:
        text=checked(run["published_journal"],run["published_sha256"]); parsed=validate_current(text,run["command"],53)
        assert [list(map(int,r)) for r in parsed["timings"]]==run["timing_rows"] and [list(map(int,r)) for r in parsed["results"]]==run["result_rows"]
        assert all(r[1:]==("0000","0000","0","0") for r in parsed["dcr"])
        assert list(map(int,re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text).groups()))==[run["setup_us"],run["teardown_us"]]
        if run["pilot"]: continue
        for t in run["timing_rows"]:
            scalar=t[1]*1000000/32768/16; current=t[2]*1000000/32768/64
            rows.append(dict(case=(t[0]-1)%8,A_current_us=current,A_scalar_us=scalar,H_ready_us=t[6]*1000000/32768,notification_us=t[5]*1000000/32768,raw_DSP_ticks=t[8],scalar_over_current=scalar/current,S_us=run["setup_us"]+run["teardown_us"]))
    def verify(selected,aggregate):
        assert aggregate["jobs"]==len(selected)
        for key in ("A_current_us","A_scalar_us","H_ready_us","notification_us","raw_DSP_ticks","scalar_over_current"):
            assert aggregate[key]==stats([r[key] for r in selected])
        assert aggregate["blocking_winners_current_without_setup"]==sum(r["H_ready_us"]<r["A_current_us"] for r in selected)==0
        assert aggregate["blocking_winners_scalar_without_setup"]==sum(r["H_ready_us"]<r["A_scalar_us"] for r in selected)
        for n in (16,64,256,1000,10000):
            s=aggregate["strict_scenarios"][str(n)]
            assert s["W_threshold_us"]==stats([r["H_ready_us"]+r["S_us"]/n-r["A_current_us"] for r in selected])
            assert s["setup_condition_passed"]==sum(r["S_us"]/n<r["A_current_us"] for r in selected)
            assert s["blocking_gain_with_setup"]==sum(r["H_ready_us"]+r["S_us"]/n<r["A_current_us"] for r in selected)==0
    verify(rows,result["aggregate"])
    for c in range(8): verify([r for r in rows if r["case"]==c],result["cases"][str(c)])
    assert len(rows)==result["jobs"]==360 and result["ring_uint16_words_checked"]==460800
    assert result["instrumented_S_us"]==stats([r["setup_us"]+r["teardown_us"] for r in result["runs"] if not r["pilot"]])
    assert len(result["clocks"])==8
    for clock in result["clocks"]:
        assert clock["stock_verified"] and stock_clock_matches(''.join(checked(p["published_path"],p["published_sha256"]) for p in clock["probes"]),"n95")
    assert len(result["restorations"])==2
    for restoration in result["restorations"]:
        restored=json.loads(checked(restoration["published_path"],restoration["published_sha256"]))
        assert restored["complete"] and restored["files"]==restoration["files"] and len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
        assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
    interruption=result["interruption"]; failure=json.loads(checked(interruption["report"]["published_path"],interruption["report"]["published_sha256"]))
    transport=checked(interruption["transport"]["published_path"],interruption["transport"]["published_sha256"])
    assert not failure["complete"] and "exit" not in failure and failure["error"]=="RuntimeError: installed host differs from the built v53 artifact"
    assert not any(s in transport for s in ("> START ","> PUT ","> KILL ")) and interruption["before_START"] and interruption["excluded_from_samples"]
    assert not result["useful_ARM_W_measured"] and not result["CPU_usage_measured"]
    recovery=json.loads((dest/"n95-wsola68-recovery-artifacts.json").read_text())
    for f in recovery["files"]: checked(f["path"],f["sha256"])
    print("Verified WSOLA68:8 pilots +360 current-SMLAD/scalar/DSP63 jobs with independent Python oracle,460800 ring words,8 stock brackets, pre-START interruption and originals5 restored twice.")


if __name__=="__main__": main()
