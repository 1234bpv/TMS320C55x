"""Publish distinct N95 CPU-window64 cohort; old short CPU deltas stay raw."""
import json
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT, boot, digest, load, publish_text, stats

DEST=ROOT / "docs/evidence/2026-10-04"
SESSION=ROOT / "work/evidence/n95/d0-20261003-clean34"


def main():
    proof=load(DEST / "n95-window64-artifacts.json")
    hashes={f["path"]:f["sha256"] for f in proof["files"]}
    runs,clocks=[],[]
    for series,batch,tag,frames in [(0,15,"window64-pilot-b15-f8-01",8)]+[
            (s,b,f"window64-stock01-s{s}-b{b}",120) for s in (1,2,3) for b in (1,2,8,15)]:
        report=load(SESSION / (tag+".json")); source=SESSION / (tag+".log")
        text=source.read_text(encoding="ascii")
        assert report["complete"] and report["exit"]==["EXIT 0 Kill"]
        assert boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
        assert digest(source)==report["journal_sha256"]
        assert report["host_sha256"]==hashes["out/arm/c55stream.exe"]
        assert report["dsp_sha256"]==hashes["out/dsp/c55stream-dmm-ring-window.dll55l"]
        command=f"dmm-ring-window batch={batch} frames={frames}"
        validate_journal(text,command,49)
        hz=int(re.search(r"fast_counter_hz=(\d+)",text)[1]); assert hz==32768
        timing=re.search(r"RING CPU WINDOW frames=(\d+) batch=(\d+) outer_ticks=(\d+) loop_ticks=(\d+) final_yield_ticks=(\d+) cpu_us=(\d+)",text)
        _,_,outer,loop,yield_,cpu=map(int,timing.groups())
        lifecycle=re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text)
        setup,teardown=map(int,lifecycle.groups())
        rows=re.findall(r"RING FRAME frame=(\d+) slot=(\d+) batch=(\d+) packet_start=(\d+) wall_us=(\d+) cpu_us=-1 bad_words=0 dsp_ticks=(\d+)",text)
        wall=[int(r[4]) for r in rows]; dsp=[int(r[5]) for r in rows]
        target=DEST/("n95-"+tag+".txt")
        runs.append({"series":series,"pilot":series==0,"batch":batch,"frames":frames,"packets":frames*batch,
                     "command":command,"outer_ticks":outer,"loop_ticks":loop,"final_yield_ticks":yield_,"CPU_us":cpu,
                     "outer_wall_us":outer*1000000/hz,"loop_wall_us":loop*1000000/hz,"final_yield_us":yield_*1000000/hz,
                     "CPU_percent_including_final_yield":100*cpu/(outer*1000000/hz),
                     "exchange_wall_us":wall,"raw_DSP_ticks":dsp,"setup_us":setup,"teardown_us":teardown,
                     "published_journal":target.relative_to(ROOT).as_posix(),"published_sha256":publish_text(source,target)})
    for series in (1,2,3):
        for position in ("before","after"):
            report=load(SESSION/f"window64-stock01-s{series}-clock-{position}.json")
            assert report["complete"] and boot(report)==boot(report,"info_after")=="62209 boot 0 by n"
            combined,probes="",[]
            for probe in report["probes"]:
                source=SESSION/probe["path"]; assert digest(source)==probe["sha256"]
                combined+=source.read_text(encoding="ascii")
                target=DEST/("n95-"+source.stem+".txt")
                probes.append({"published_path":target.relative_to(ROOT).as_posix(),"published_sha256":publish_text(source,target)})
            assert report["stock_verified"] and stock_clock_matches(combined,"n95")
            clocks.append({"series":series,"position":position,"stock_verified":True,"probes":probes})
    aggregate={}
    for batch in (1,2,8,15):
        selected=[r for r in runs if not r["pilot"] and r["batch"]==batch]
        wall=[v for r in selected for v in r["exchange_wall_us"]]
        cpu=sum(r["CPU_us"] for r in selected); outer=sum(r["outer_wall_us"] for r in selected)
        payload=sum(r["packets"]*960 for r in selected)
        aggregate[str(batch)]={"runs":len(selected),"packets":batch*360,"exchange_wall_us":stats(wall),
            "CPU_us_per_window":stats([r["CPU_us"] for r in selected]),"outer_wall_us_per_window":stats([r["outer_wall_us"] for r in selected]),
            "weighted_CPU_percent_including_final_yield":100*cpu/outer,
            "useful_bidirectional_MB_s_exchange_intervals":payload/sum(wall),
            "useful_bidirectional_MB_s_full_window_including_pack_checks_yield":payload/outer,
            "raw_DSP_ticks":stats([v for r in selected for v in r["raw_DSP_ticks"]])}
    source=SESSION/"window64-final-verify01.json"; restored=load(source)
    assert restored["complete"] and len(restored["files"])==5 and all(f["equal_original"] for f in restored["files"])
    assert restored["c55stream_processes"]==restored["ocprobe_processes"]==["OK ps 0"]
    target=DEST/"n95-window64-final-verify01.json"
    result={"scope":"distinct N95 candidate64/host49/protocol38; calibrated aggregate CPU ring window",
            "status":"measurement_complete","plan_status":"in_progress","series":3,"runs_excluding_pilot":12,"packets_excluding_pilot":9360,
            "host_sha256":hashes["out/arm/c55stream.exe"],"DSP_sha256":hashes["out/dsp/c55stream-dmm-ring-window.dll55l"],
            "runs":runs,"clocks":clocks,"aggregate":aggregate,
            "calibration_source":"docs/evidence/2026-10-04/n95-cpu-counter-results.json",
            "CPU_qualified_scope":"Aggregate thread CPU over outer window including pack/cache/notifications/full input-output checks and final settling yield; no journaling or scalar ARM baseline inside. Not pure DSP wait CPU or production application load.",
            "CPU_window_checks_passed":all(r["CPU_us"]*32768<=(r["outer_ticks"]+2)*1000000 for r in runs),
            "restoration":{"utc":restored["utc"],"files":restored["files"],"published_path":target.relative_to(ROOT).as_posix(),"published_sha256":publish_text(source,target)},
            "limits":["Candidate64 DSP binary differs from archived52/61; protocol38 correctness/lifecycle retained, performance samples are a separate cohort",
                      "No DCR read in this mode; prior62/63 readings are not current64 configuration proof",
                      "Stock frequency brackets are snapshots, not continuous DVFS trace; no performance reservation",
                      "Final User::After(1) is included and measured; CPU/outer wall fraction must not be relabeled as fraction of the loop alone",
                      "Raw DSP ticks unconverted; W=0 and synthetic transform remain separate from application speedup",
                      "Full independent endpoint-publication contract remains open; E90 deferred by user"]}
    path=DEST/"n95-ring-cpu64-results.json"
    path.write_bytes((json.dumps(result,indent=2)+"\n").encode())
    print(json.dumps({"path":str(path),"aggregate":aggregate},indent=2))


if __name__=="__main__":
    main()
