"""Independent recalculation from published N95 SPU67 journals; no phone."""
import json
import re

from spu_session_support import validate_spu
from stage_spu_mix import fixtures,emit_array
from prepare_stream import stock_clock_matches
from summarize_ring import stats
from verify_ring_publication import ROOT,checked


def main():
    dest=ROOT / "docs/evidence/2026-10-04"
    result=json.loads((dest/"n95-spu67-results.json").read_text()); proof=json.loads((dest/"n95-spu67-artifacts.json").read_text())
    files={r["path"]:r["sha256"] for r in proof["files"]}
    assert result["host_sha256"]==files["out/arm/c55stream.exe"] and result["DSP_sha256"]==files["out/dsp/c55stream-dmm-ring-spu.dll55l"]
    for path in ("src/spu/mix_arm.s","src/spu/fixtures.h","src/spu/snapshot.json","src/dsp/spu_mix_ring.inc"):
        checked(path,files[path])
    fixture_rows=fixtures(); header=(ROOT / "src/spu/fixtures.h").read_text()
    for name,shape,key in (("spu_samples",[8,24,64],"samples"),("spu_volumes",[8,24,2],"volumes"),("spu_initial",[8,128],"initial"),("spu_expected",[8,3,128],"expected")):
        assert emit_array(name,shape,[r[key] for r in fixture_rows]) in header
    assert proof["imports_exist_in_saved_n95_baseimage"] and len(proof["imports"])==15 and "__mpyli" not in proof["imports"]
    assert proof["ARM_instruction_counts"]==dict(smlawb=2,smlawt=2)
    audit=proof["read_only_DCR_instruction_audit"]
    assert audit["DSP_sha256"]==result["DSP_sha256"] and audit["helper_code_hex"]=="A45102004804"
    assert audit["helper_io_writes"]==audit["helper_relocations"]==0 and audit["calls_per_exchange"]==2
    assert {(r["series"],r["voices"]) for r in result["runs"]}=={(s,v) for s in (0,1,2,3) for v in (1,8,24)}
    selected={str(v):[] for v in (1,8,24)}; words=0
    for run in result["runs"]:
        text=checked(run["published_journal"],run["published_sha256"]); parsed=validate_spu(text,run["command"],52)
        assert [list(map(int,r)) for r in parsed["timings"]]==run["timing_rows"]
        assert all(r[1:]==("0000","0000","0","0") for r in parsed["dcr"])
        assert parsed["checked_words"]==run["checked_words_per_job"] and parsed["jobs"]==run["jobs"]==(8 if run["pilot"] else 120)
        assert list(map(int,re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text).groups()))==[run["setup_us"],run["teardown_us"]]
        if run["pilot"]: continue
        words+=run["jobs"]*run["checked_words_per_job"]
        for t in run["timing_rows"]:
            selected[str(run["voices"])].append(dict(case=(t[0]-1)%8,A_us=t[1]*1000000/32768/256,H_ready_us=t[5]*1000000/32768,
                                                   H_checked_us=t[6]*1000000/32768,notification_us=t[4]*1000000/32768,raw_DSP_ticks=t[7],S_us=run["setup_us"]+run["teardown_us"]))
    for v,rows in selected.items():
        aggregate=result["aggregate"][v]; assert aggregate["jobs"]==len(rows)==360
        for key in ("A_us","H_ready_us","H_checked_us","notification_us","raw_DSP_ticks"):
            assert aggregate[key]==stats([r[key] for r in rows])
        assert aggregate["blocking_winners_without_setup"]==sum(r["H_ready_us"]<r["A_us"] for r in rows)==0
        for c in range(8):
            subset=[r for r in rows if r["case"]==c]; case=result["cases"][v][str(c)]
            assert case["jobs"]==len(subset)==45
            for key in ("A_us","H_ready_us","H_checked_us","notification_us","raw_DSP_ticks"):
                assert case[key]==stats([r[key] for r in subset])
            assert case["blocking_winners_without_setup"]==0
        for n in (16,64,256,1000,1000000):
            scenario=aggregate["strict_scenarios"][str(n)]
            assert scenario["W_threshold_us"]==stats([r["H_ready_us"]+r["S_us"]/n-r["A_us"] for r in rows])
            assert scenario["setup_condition_passed"]==sum(r["S_us"]/n<r["A_us"] for r in rows)
            assert scenario["blocking_gain_with_setup"]==sum(r["H_ready_us"]+r["S_us"]/n<r["A_us"] for r in rows)==0
    assert result["jobs"]==1080 and result["pilot_jobs_separate"]==24 and result["stereo_sum_uint32_words_checked"]==138240
    assert words==result["ring_uint16_words_checked"]==2672640
    assert result["instrumented_S_us"]==stats([r["setup_us"]+r["teardown_us"] for r in result["runs"] if not r["pilot"]])
    assert len(result["clocks"])==8
    for clock in result["clocks"]:
        assert clock["stock_verified"] and stock_clock_matches(''.join(checked(p["published_path"],p["published_sha256"]) for p in clock["probes"]),"n95")
    restoration=result["restoration"]; restored=json.loads(checked(restoration["published_path"],restoration["published_sha256"]))
    assert restored["complete"] and restored["files"]==restoration["files"]
    assert len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
    assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
    assert not result["CPU_usage_measured"] and not result["useful_ARM_W_measured"]
    print("Verified SPU67:24 pilot +1080 jobs,138240 exact32-bit stereo sums,2672640 ring words,8 stock clock snapshots and5 originals restored; no blocking winners.")


if __name__=="__main__": main()
