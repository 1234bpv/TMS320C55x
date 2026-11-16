"""Publish N95 SPU67 exact plain-mix results; no whole-SPU/game claim."""
import json
import re

from spu_session_support import validate_spu
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT,boot,digest,load,publish_text,stats

DEST=ROOT / "docs/evidence/2026-10-04"
SESSION=ROOT / "work/evidence/n95/d0-20261003-clean34"


def aggregate(rows,scenarios=True):
    result=dict(jobs=len(rows))
    for key in ("A_us","H_ready_us","H_checked_us","notification_us","raw_DSP_ticks"):
        result[key]=stats([r[key] for r in rows])
    result["blocking_winners_without_setup"]=sum(r["H_ready_us"]<r["A_us"] for r in rows)
    if scenarios:
        result["strict_scenarios"]={str(n):dict(
            W_threshold_us=stats([r["H_ready_us"]+r["S_us"]/n-r["A_us"] for r in rows]),
            setup_condition_passed=sum(r["S_us"]/n<r["A_us"] for r in rows),
            blocking_gain_with_setup=sum(r["H_ready_us"]+r["S_us"]/n<r["A_us"] for r in rows)) for n in (16,64,256,1000,1000000)}
    return result


def main():
    proof=load(DEST / "n95-spu67-artifacts.json"); hashes={f["path"]:f["sha256"] for f in proof["files"]}
    runs,clocks,samples=[],[],[]
    tags=[(0,v,f"spu67-pilot-v{v}-f8-01",8) for v in (1,8,24)]+[(s,v,f"spu67-stock01-s{s}-v{v}",120) for s in (1,2,3) for v in (1,8,24)]
    for series,voices,tag,frames in tags:
        report=load(SESSION/(tag+".json")); source=SESSION/(tag+".log"); text=source.read_text(encoding="ascii")
        command=f"dmm-ring-spu voices={voices} frames={frames}"
        assert report["complete"] and report["exit"]==["EXIT 0 Kill"] and boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
        assert digest(source)==report["journal_sha256"] and report["host_sha256"]==hashes["out/arm/c55stream.exe"] and report["dsp_sha256"]==hashes["out/dsp/c55stream-dmm-ring-spu.dll55l"]
        parsed=validate_spu(text,command,52); rows=[list(map(int,r)) for r in parsed["timings"]]
        setup,teardown=map(int,re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text).groups())
        assert all(r[1:]==("0000","0000","0","0") for r in parsed["dcr"])
        target=DEST/("n95-"+tag+".txt")
        runs.append(dict(series=series,pilot=series==0,voices=voices,jobs=frames,command=command,input_slots=parsed["input_slots"],output_slots=2,
                         checked_words_per_job=parsed["checked_words"],setup_us=setup,teardown_us=teardown,timing_rows=rows,
                         published_journal=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)))
        if series:
            for t in rows:
                samples.append(dict(voices=voices,case=(t[0]-1)%8,A_us=t[1]*1000000/32768/256,H_ready_us=t[5]*1000000/32768,
                                    H_checked_us=t[6]*1000000/32768,notification_us=t[4]*1000000/32768,raw_DSP_ticks=t[7],S_us=setup+teardown))
    for series in (0,1,2,3):
        for position in ("before","after"):
            tag=f"spu67-pilot-clock-{position}01" if series==0 else f"spu67-stock01-s{series}-clock-{position}"
            report=load(SESSION/(tag+".json")); probes=[]; combined=""
            assert report["complete"] and boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
            for p in report["probes"]:
                source=SESSION/p["path"]; assert digest(source)==p["sha256"]; combined+=source.read_text(encoding="ascii")
                target=DEST/("n95-"+source.stem+".txt")
                probes.append(dict(published_path=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)))
            assert report["stock_verified"] and stock_clock_matches(combined,"n95")
            clocks.append(dict(series=series,position=position,stock_verified=True,probes=probes))
    source=SESSION/"spu67-final-verify01.json"; restored=load(source)
    assert restored["complete"] and len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
    assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
    target=DEST/"n95-spu67-final-verify01.json"
    result=dict(scope="N95 SPU67/host52/protocol42; current ARMV5 plain mixer,64 samples/voice,1/8/24 voices",status="measurement_complete",plan_status="in_progress",
                host_version=52,host_sha256=hashes["out/arm/c55stream.exe"],DSP_sha256=hashes["out/dsp/c55stream-dmm-ring-spu.dll55l"],
                jobs=1080,pilot_jobs_separate=24,stereo_sum_uint32_words_checked=1080*128,
                ring_uint16_words_checked=sum(r["jobs"]*r["checked_words_per_job"] for r in runs if not r["pilot"]),
                runs=runs,clocks=clocks,aggregate={str(v):aggregate([r for r in samples if r["voices"]==v]) for v in (1,8,24)},
                cases={str(v):{str(c):aggregate([r for r in samples if r["voices"]==v and r["case"]==c],False) for c in range(8)} for v in (1,8,24)},
                instrumented_S_us=stats([r["setup_us"]+r["teardown_us"] for r in runs if not r["pilot"]]),
                WPE_disabled_all_2160_series_readings=True,useful_ARM_W_measured=False,CPU_usage_measured=False,
                restoration=dict(files=restored["files"],published_path=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)),
                decision="Keep this measured stateless plain-mix job on ARM; full resident SPU and independent W remain unmeasured.",
                limits=["Eight synthetic fixtures: signed16/zero/fractional volumes, negative gains and wrap32; two also stress full signed32 inputs beyond legal PCM range. Not gameplay PCM or full mutable SPU state.",
                        "Actual upstream ARM SMLAW instructions retained; one global source load becomes fifth pointer argument; wrapper/voice loop/volatile sink inside A.",
                        "A averages256 successive additions to warm sums; reset, single-job and modular256-job oracles outside A. Live emulator cache/state differs.",
                        "H+D includes all input packing, cache/notifications, DSP calculation and reconstruction of128 stereo sums into ARM memory; all result/input/header/padding checks outside.",
                        "Stock clocks are snapshots, not continuous DVFS qualification. No frequency/performance reservation or DCR/PRCM writes.",
                        "CPU unmeasured(-1); DSP raw ticks/countspms unconverted. Read-only DCR may perturb ordering; external-memory publication contract remains open.",
                        "S includes lifecycle journaling; not minimum production startup. Scenario W thresholds require S/N<A and do not prove useful independent work.",
                        "Decode/ADSR/fmod/noise/reverb, SPU RAM/DMA/register/IRQ/state equivalence and final PCM all outside this isolated job. E90 deferred; no E90 commands."])
    assert len(samples)==1080
    (DEST/"n95-spu67-results.json").write_bytes((json.dumps(result,indent=2)+"\n").encode())
    print(json.dumps(dict(aggregate=result["aggregate"],instrumented_S_us=result["instrumented_S_us"]),indent=2))


if __name__=="__main__": main()
