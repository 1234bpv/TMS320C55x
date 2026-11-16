"""Publish two separate N95 MDEC cohorts;66 excludes oracle cost from H+D."""
import json
import re

from mdec_session_support import validate_mdec
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT,boot,digest,load,publish_text,stats

DEST=ROOT / "docs/evidence/2026-10-04"
SESSION=ROOT / "work/evidence/n95/d0-20261003-clean34"


def aggregate(samples,ready):
    result={"jobs":len(samples)}
    for key in ("A343_us","A463_us","H_checked_us","H_ready_us","notification_us","raw_DSP_ticks"):
        if key in samples[0]:
            result[key]=stats([r[key] for r in samples])
    if ready:
        result["blocking_winners_without_setup"]=sum(r["H_ready_us"]<r["A463_us"] for r in samples)
        result["H_ready_per_macroblock_us"]=stats([r["H_ready_us"]/r["macros"] for r in samples])
        result["A463_per_macroblock_us"]=stats([r["A463_us"]/r["macros"] for r in samples])
        result["strict_scenarios"]={str(n):dict(
            W_threshold_us=stats([r["H_ready_us"]+r["S_us"]/n-r["A463_us"] for r in samples]),
            setup_condition_passed=sum(r["S_us"]/n<r["A463_us"] for r in samples),
            blocking_gain_with_setup=sum(r["H_ready_us"]+r["S_us"]/n<r["A463_us"] for r in samples)) for n in (16,64,256,1000)}
    return result


def publish(cohort):
    version=50 if cohort==65 else 51
    proof=load(DEST / f"n95-mdec{cohort}-artifacts.json")
    hashes={f["path"]:f["sha256"] for f in proof["files"]}
    runs,clocks,samples=[],[],[]
    tags=[(0,b,f"mdec{cohort}-pilot-b{b}-f8-01",8) for b in (1,2,4)]+[
        (s,b,f"mdec{cohort}-stock01-s{s}-b{b}",120) for s in (1,2,3) for b in (1,2,4)]
    for series,batch,tag,frames in tags:
        report=load(SESSION/(tag+".json")); source=SESSION/(tag+".log")
        text=source.read_text(encoding="ascii"); command=f"dmm-ring-mdec batch={batch} frames={frames}"
        assert report["complete"] and report["exit"]==["EXIT 0 Kill"]
        assert boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
        assert digest(source)==report["journal_sha256"]
        assert report["host_sha256"]==hashes["out/arm/c55stream.exe"]
        assert report["dsp_sha256"]==hashes["out/dsp/c55stream-dmm-ring-mdec.dll55l"]
        parsed=validate_mdec(text,command,version)
        life=re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text)
        setup,teardown=map(int,life.groups())
        assert all(r[1:]==("0000","0000","0","0") for r in parsed["dcr"])
        rows=[list(map(int,r)) for r in parsed["timings"]]
        ready=[list(map(int,r)) for r in parsed["ready"]]
        target=DEST/("n95-"+tag+".txt")
        runs.append(dict(series=series,pilot=series==0,macroblocks_per_job=batch,jobs=frames,command=command,
                         input_slots=parsed["input_slots"],output_slots=parsed["output_slots"],checked_words_per_job=parsed["checked_words"],
                         setup_us=setup,teardown_us=teardown,timing_rows=rows,ready_rows=ready,
                         published_journal=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)))
        if not series:
            continue
        for i,t in enumerate(rows):
            r=dict(macros=batch,case=(t[0]-1)%8,A343_us=t[1]*1000000/32768/16,A463_us=t[2]*1000000/32768/16,
                   H_checked_us=t[6]*1000000/32768,raw_DSP_ticks=t[7],S_us=setup+teardown)
            if ready:
                r.update(H_ready_us=ready[i][2]*1000000/32768,notification_us=ready[i][1]*1000000/32768)
            samples.append(r)
    for series in (0,1,2,3):
        for position in ("before","after"):
            tag=f"mdec{cohort}-pilot-clock-{position}01" if series==0 else f"mdec{cohort}-stock01-s{series}-clock-{position}"
            report=load(SESSION/(tag+".json"))
            assert report["complete"] and boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
            probes=[]; combined=""
            for probe in report["probes"]:
                source=SESSION/probe["path"]; assert digest(source)==probe["sha256"]
                combined+=source.read_text(encoding="ascii")
                target=DEST/("n95-"+source.stem+".txt")
                probes.append(dict(published_path=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)))
            assert report["stock_verified"] and stock_clock_matches(combined,"n95")
            clocks.append(dict(series=series,position=position,stock_verified=True,probes=probes))
    source=SESSION/f"mdec{cohort}-final-verify01.json"; restored=load(source)
    assert restored["complete"] and len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
    assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
    target=DEST/f"n95-mdec{cohort}-final-verify01.json"
    result=dict(scope=f"N95 MDEC{cohort}/host{version}/protocol41; DSP kernel65",status="measurement_complete",plan_status="in_progress",
                host_version=version,host_sha256=hashes["out/arm/c55stream.exe"],DSP_sha256=hashes["out/dsp/c55stream-dmm-ring-mdec.dll55l"],
                jobs=1080,macroblocks=2520,pilot_jobs_separate=24,pilot_macroblocks_separate=56,
                RGB24_uint32_words_checked=2520*192,ring_uint16_words_checked=sum(r["jobs"]*r["checked_words_per_job"] for r in runs if not r["pilot"]),
                runs=runs,clocks=clocks,aggregate={str(b):aggregate([r for r in samples if r["macros"]==b],cohort==66) for b in (1,2,4)},
                cases={str(b):{str(c):aggregate([r for r in samples if r["macros"]==b and r["case"]==c],False) for c in range(8)} for b in (1,2,4)},
                instrumented_S_us=stats([r["setup_us"]+r["teardown_us"] for r in runs if not r["pilot"]]),
                WPE_disabled_all_2160_series_readings=True,useful_ARM_W_measured=False,CPU_usage_measured=False,
                restoration=dict(files=restored["files"],published_path=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)),
                decision="Keep MDEC on ARM for this measured blocking six-IDCT + RGB24 job; independent ARM W and resident/asynchronous alternative remain unmeasured." if cohort==66 else "Correctness cohort; H includes full oracle checks, so use corrected66 intervals for blocking comparison.",
                limits=["Eight bounded synthetic coefficient fixtures, not captured gameplay or exhaustive legal PS1 inputs.",
                        "RLE/dequantization, DMA/IRQ and live emulator state are outside this job; emulator unchanged.",
                        "A averages16 warm batch calls; reset and oracle checks outside A; wrapper/loop/sink inside A. GCCE463 optimization/architecture match current core, isolated cache/state differs.",
                        "66 H+D includes input packing, cache/notifications and RGB24 reconstruction into ARM memory; oracle checks outside.65 full checks inside H, kept separate.",
                        "Stock clock brackets are snapshots, not continuous DVFS guarantee; no frequency/performance reservation writes.",
                        "CPU unmeasured(-1); raw DSP ticks/countspms unconverted. DCR reads may perturb ordering; external-memory publication contract still open.",
                        "Instrumented setup+teardown includes lifecycle journaling; not minimum production startup. Parallel W thresholds additionally require S/N<A.",
                        "E90 deferred by user; no E90 phone commands."])
    assert len(samples)==1080 and sum(r["macros"] for r in samples)==2520
    path=DEST/f"n95-mdec{cohort}-results.json"; path.write_bytes((json.dumps(result,indent=2)+"\n").encode())
    print(json.dumps(dict(cohort=cohort,aggregate=result["aggregate"]),indent=2))


if __name__=="__main__":
    for cohort in (65,66):
        publish(cohort)
