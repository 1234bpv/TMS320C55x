"""Recompute MDEC evidence using committed files only; no phone access."""
import json
import re

from mdec_session_support import validate_mdec
from mdec_reference import fixtures
from prepare_stream import stock_clock_matches
from summarize_ring import stats
from verify_ring_publication import ROOT,checked


def main():
    fixture_rows=fixtures()
    for f in fixture_rows:
        assert len(f["coefficients"])==len(f["idct"])==384 and len(f["rgb24"])==192
    dsp_hashes=[]
    for cohort,version in ((65,50),(66,51)):
        root=ROOT / "docs/evidence/2026-10-04"
        result=json.loads((root/f"n95-mdec{cohort}-results.json").read_text())
        proof=json.loads((root/f"n95-mdec{cohort}-artifacts.json").read_text())
        files={r["path"]:r["sha256"] for r in proof["files"]}
        assert result["host_sha256"]==files["out/arm/c55stream.exe"]
        assert result["DSP_sha256"]==files["out/dsp/c55stream-dmm-ring-mdec.dll55l"]
        dsp_hashes.append(result["DSP_sha256"])
        checked("src/mdec/fixtures.h",files["src/mdec/fixtures.h"])
        assert proof["imports_exist_in_saved_n95_baseimage"] and len(proof["imports"])==16 and "__mpyli" in proof["imports"]
        audit=proof["read_only_DCR_instruction_audit"]
        assert audit["DSP_sha256"]==result["DSP_sha256"] and audit["helper_code_hex"]=="A45102004804"
        assert audit["helper_io_writes"]==audit["helper_relocations"]==0 and audit["calls_per_exchange"]==2
        assert {(r["series"],r["macroblocks_per_job"]) for r in result["runs"]}=={(s,b) for s in (0,1,2,3) for b in (1,2,4)}
        selected={str(b):[] for b in (1,2,4)}; words=0
        for run in result["runs"]:
            text=checked(run["published_journal"],run["published_sha256"])
            parsed=validate_mdec(text,run["command"],version)
            assert [list(map(int,r)) for r in parsed["timings"]]==run["timing_rows"]
            assert [list(map(int,r)) for r in parsed["ready"]]==run["ready_rows"]
            assert all(r[1:]==("0000","0000","0","0") for r in parsed["dcr"])
            assert parsed["checked_words"]==run["checked_words_per_job"]
            assert parsed["jobs"]==run["jobs"]==(8 if run["pilot"] else 120)
            assert list(map(int,re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text).groups()))==[run["setup_us"],run["teardown_us"]]
            if run["pilot"]:
                continue
            words+=run["jobs"]*run["checked_words_per_job"]
            for i,t in enumerate(run["timing_rows"]):
                row=dict(case=(t[0]-1)%8,macros=run["macroblocks_per_job"],A343_us=t[1]*1000000/32768/16,
                         A463_us=t[2]*1000000/32768/16,H_checked_us=t[6]*1000000/32768,raw_DSP_ticks=t[7],
                         S_us=run["setup_us"]+run["teardown_us"])
                if cohort==66:
                    row.update(H_ready_us=run["ready_rows"][i][2]*1000000/32768,notification_us=run["ready_rows"][i][1]*1000000/32768)
                selected[str(run["macroblocks_per_job"])].append(row)
        for b,rows in selected.items():
            aggregate=result["aggregate"][b]; assert aggregate["jobs"]==len(rows)==360
            for key in ("A343_us","A463_us","H_checked_us","H_ready_us","notification_us","raw_DSP_ticks"):
                if key in rows[0]:
                    assert aggregate[key]==stats([r[key] for r in rows])
            for c in range(8):
                subset=[r for r in rows if r["case"]==c]; case=result["cases"][b][str(c)]
                assert case["jobs"]==len(subset)==45
                for key in ("A343_us","A463_us","H_checked_us","H_ready_us","notification_us","raw_DSP_ticks"):
                    if key in subset[0]:
                        assert case[key]==stats([r[key] for r in subset])
            if cohort==66:
                assert aggregate["blocking_winners_without_setup"]==sum(r["H_ready_us"]<r["A463_us"] for r in rows)
                assert aggregate["H_ready_per_macroblock_us"]==stats([r["H_ready_us"]/r["macros"] for r in rows])
                assert aggregate["A463_per_macroblock_us"]==stats([r["A463_us"]/r["macros"] for r in rows])
                for n in (16,64,256,1000):
                    scenario=aggregate["strict_scenarios"][str(n)]
                    assert scenario["W_threshold_us"]==stats([r["H_ready_us"]+r["S_us"]/n-r["A463_us"] for r in rows])
                    assert scenario["setup_condition_passed"]==sum(r["S_us"]/n<r["A463_us"] for r in rows)
                    assert scenario["blocking_gain_with_setup"]==sum(r["H_ready_us"]+r["S_us"]/n<r["A463_us"] for r in rows)
        assert result["jobs"]==1080 and result["macroblocks"]==2520
        assert words==result["ring_uint16_words_checked"]==3409920 and result["RGB24_uint32_words_checked"]==483840
        assert result["instrumented_S_us"]==stats([r["setup_us"]+r["teardown_us"] for r in result["runs"] if not r["pilot"]])
        assert len(result["clocks"])==8
        for clock in result["clocks"]:
            assert clock["stock_verified"] and stock_clock_matches("".join(checked(p["published_path"],p["published_sha256"]) for p in clock["probes"]),"n95")
        restoration=result["restoration"]; restored=json.loads(checked(restoration["published_path"],restoration["published_sha256"]))
        assert restored["complete"] and restored["files"]==restoration["files"]
        assert len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
        assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
        assert not result["CPU_usage_measured"] and not result["useful_ARM_W_measured"]
    assert dsp_hashes[0]==dsp_hashes[1],"66 must reuse exact65 DSP kernel"
    print("Verified N95 MDEC65/66 separately: each24 pilot +1080 jobs/2520 macroblocks, exact32-bit/RGB24 outputs, corrected66 timing/scenarios, stock snapshots and originals5 restoration.")


if __name__=="__main__":
    main()
