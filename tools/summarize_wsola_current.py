"""Publish paired current SMLAD/scalar/DSP63 measurements and pre-START interruption."""
import json
import re

from wsola_current_session_support import validate_current
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT,boot,digest,load,publish_text,stats

DEST=ROOT/"docs/evidence/2026-10-04"; SESSION=ROOT/"work/evidence/n95/d0-20261003-clean34"


def aggregate(rows):
    result=dict(jobs=len(rows))
    for key in ("A_current_us","A_scalar_us","H_ready_us","notification_us","raw_DSP_ticks","scalar_over_current"):
        result[key]=stats([r[key] for r in rows])
    result["blocking_winners_current_without_setup"]=sum(r["H_ready_us"]<r["A_current_us"] for r in rows)
    result["blocking_winners_scalar_without_setup"]=sum(r["H_ready_us"]<r["A_scalar_us"] for r in rows)
    result["strict_scenarios"]={str(n):dict(W_threshold_us=stats([r["H_ready_us"]+r["S_us"]/n-r["A_current_us"] for r in rows]),
                                             setup_condition_passed=sum(r["S_us"]/n<r["A_current_us"] for r in rows),
                                             blocking_gain_with_setup=sum(r["H_ready_us"]+r["S_us"]/n<r["A_current_us"] for r in rows)) for n in (16,64,256,1000,10000)}
    return result


def main():
    proof=load(DEST/"n95-wsola68-artifacts.json"); hashes={f["path"]:f["sha256"] for f in proof["files"]}
    runs,clocks,samples=[],[],[]
    tags=[(0,"wsola68-pilot-f8-01",8)]+[(s,f"wsola68-stock{'02' if s==3 else '01'}-s{s}-run",120) for s in (1,2,3)]
    for series,tag,frames in tags:
        report=load(SESSION/(tag+".json")); source=SESSION/(tag+".log"); text=source.read_text(encoding="ascii"); command=f"dmm-ring-wsola-current frames={frames}"
        assert report["complete"] and report["exit"]==["EXIT 0 Kill"] and boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
        assert digest(source)==report["journal_sha256"] and report["host_sha256"]==hashes["out/arm/c55stream.exe"] and report["dsp_sha256"]==hashes["out/dsp/c55stream-dmm-ring-wsola.dll55l"]
        parsed=validate_current(text,command,53); timings=[list(map(int,r)) for r in parsed["timings"]]; results=[list(map(int,r)) for r in parsed["results"]]
        setup,teardown=map(int,re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text).groups())
        assert all(r[1:]==("0000","0000","0","0") for r in parsed["dcr"])
        target=DEST/("n95-"+tag+".txt")
        runs.append(dict(series=series,pilot=series==0,jobs=frames,command=command,setup_us=setup,teardown_us=teardown,timing_rows=timings,result_rows=results,
                         published_journal=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)))
        if series:
            for t in timings:
                a=t[2]*1000000/32768/64; scalar=t[1]*1000000/32768/16
                samples.append(dict(case=(t[0]-1)%8,A_current_us=a,A_scalar_us=scalar,H_ready_us=t[6]*1000000/32768,notification_us=t[5]*1000000/32768,raw_DSP_ticks=t[8],S_us=setup+teardown,scalar_over_current=scalar/a))
    clock_tags=[(s,p,f"wsola68-pilot-clock-{p}01" if s==0 else f"wsola68-stock{'02' if s==3 else '01'}-s{s}-clock-{p}") for s in (0,1,2,3) for p in ("before","after")]
    for series,position,tag in clock_tags:
        report=load(SESSION/(tag+".json")); combined=""; probes=[]
        assert report["complete"] and boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
        for p in report["probes"]:
            source=SESSION/p["path"]; assert digest(source)==p["sha256"]; combined+=source.read_text(encoding="ascii")
            target=DEST/("n95-"+source.stem+".txt"); probes.append(dict(published_path=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target)))
        assert report["stock_verified"] and stock_clock_matches(combined,"n95")
        clocks.append(dict(series=series,position=position,stock_verified=True,probes=probes))
    def publish_file(name):
        source=SESSION/name; target=DEST/("n95-"+name)
        return dict(published_path=target.relative_to(ROOT).as_posix(),published_sha256=publish_text(source,target))
    failure=load(SESSION/"wsola68-stock01-s3-run.json"); transport=(SESSION/"wsola68-stock01-s3-run-transport.txt").read_text()
    assert not failure["complete"] and failure["error"]=="RuntimeError: installed host differs from the built v53 artifact" and "exit" not in failure
    assert not any(s in transport for s in ("> START ","> PUT ","> KILL "))
    restorations=[]
    for suffix in ("01","02"):
        restored=load(SESSION/f"wsola68-final-verify{suffix}.json")
        assert restored["complete"] and len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
        assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
        restorations.append(dict(files=restored["files"],**publish_file(f"wsola68-final-verify{suffix}.json")))
    result=dict(scope="N95 WSOLA68/host53/current SMLAD ARM, scalar ARM and exact DSP63/protocol40",status="measurement_complete",plan_status="in_progress",
                host_version=53,host_sha256=hashes["out/arm/c55stream.exe"],DSP_sha256=hashes["out/dsp/c55stream-dmm-ring-wsola.dll55l"],
                jobs=360,pilot_jobs_separate=8,ring_uint16_words_checked=360*1280,runs=runs,clocks=clocks,aggregate=aggregate(samples),
                cases={str(c):aggregate([r for r in samples if r["case"]==c]) for c in range(8)},instrumented_S_us=stats([r["setup_us"]+r["teardown_us"] for r in runs if not r["pilot"]]),
                useful_ARM_W_measured=False,CPU_usage_measured=False,WPE_disabled_all_720_series_readings=True,restorations=restorations,
                interruption=dict(reason="orchestrator started restoration while series still live; host mismatch stopped third attempt before START; completed series1/2 retained, third run after redeployment with new stock brackets",report=publish_file("wsola68-stock01-s3-run.json"),transport=publish_file("wsola68-stock01-s3-run-transport.txt"),before_START=True,excluded_from_samples=True),
                decision="Use current SMLAD ARM WSOLA for this measured blocking search; full audio/independent W remains unmeasured.",
                limits=["Exact current shell source snapshot; packing, two search banks, SMLAD/traversal/ties/assertion retained; CSL343/O2/ARMv6/ARM1136 matches stage1.","A current averages64 calls, scalar16; volatile sink/loop inside, dataset/oracle/journal outside. Warm isolated arrays differ from live cache/audio state.","H+D includes pack/cache/notifications/DSP and offset/score/scored reconstruction in ARM memory; checks and journal outside.","Eight synthetic fixtures with15 LCG seeds for random case across each120-job run; not captured PCM/underrun/full-game measurements.","Stock brackets are snapshots, not continuous DVFS trace. S includes lifecycle journaling; CPU-1 and useful W0, raw DSP ticks unconverted.","Pre-START third-attempt failure retained; same exact binaries redeployed, no hardware failure or new hypothesis RUN concealed. OS device work lock now prevents competing session/runner actions.","Independent endpoint publication remains open; read-only DCR may affect ordering. E90 deferred; no E90 commands."])
    (DEST/"n95-wsola68-results.json").write_bytes((json.dumps(result,indent=2)+"\n").encode())
    print(json.dumps(dict(aggregate=result["aggregate"],S=result["instrumented_S_us"]),indent=2))


if __name__=="__main__": main()
