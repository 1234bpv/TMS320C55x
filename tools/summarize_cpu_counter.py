"""Publish standalone N95 counter calibration and expose short-window limits."""
import json

from counter_probe_session import DIRECTORY, EPOCH, PROOF, ROOT, validate
from summarize_ring import boot, digest, publish_text, stats

DEST = ROOT / "docs/evidence/2026-10-04"


def main():
    proof = json.loads(PROOF.read_text())
    runs, records = [], []
    for series in (1,2,3):
        tag = f"counterprobe-series{series:02}"
        report = json.loads((DIRECTORY / (tag+".json")).read_text())
        source = DIRECTORY / (tag+".log")
        assert report["complete"] and report["exit"] == ["EXIT 0 Kill"]
        assert boot(report)==boot(report,"info_after")==EPOCH
        assert digest(source)==report["journal_sha256"]
        assert report["files"][0]["sha256"]==proof["executable_sha256"]
        parsed = []
        for row in validate(source.read_text(encoding="ascii")):
            v = list(map(int,row[:9]))
            before,after = int(row[9]+row[10],16),int(row[11]+row[12],16)
            parsed.append({"series":series,"index":v[0],"repeat":v[1],"sleep":v[2],"boundary_yield":v[3],
                           "requested_us":v[4],"inner_ticks":v[5],"outer_ticks":v[6],"nticks":v[7],"utc_us":v[8],
                           "CPU_before_us":before,"CPU_after_us":after,"CPU_delta_us":after-before,
                           "outer_wall_us":v[6]*1000000/32768})
        target = DEST / ("n95-"+tag+".txt")
        runs.append({"series":series,"published_path":target.relative_to(ROOT).as_posix(),
                     "published_sha256":publish_text(source,target),"records":parsed})
        records.extend(parsed)
    groups = {}
    for duration in (1000,10000,200000):
        for sleep in (0,1):
            for yield_ in (0,1):
                subset = [r for r in records if (r["requested_us"],r["sleep"],r["boundary_yield"])==(duration,sleep,yield_)]
                groups[f"duration{duration}-sleep{sleep}-yield{yield_}"] = {
                    "samples":len(subset),"CPU_delta_us":stats([r["CPU_delta_us"] for r in subset]),
                    "outer_wall_us":stats([r["outer_wall_us"] for r in subset]),
                    "CPU_over_wall_percent":stats([100*r["CPU_delta_us"]/r["outer_wall_us"] for r in subset]),
                    "zero_CPU_delta_samples":sum(r["CPU_delta_us"]==0 for r in subset),
                    "CPU_exceeds_outer_wall_samples":sum(r["CPU_delta_us"]>r["outer_wall_us"] for r in subset)}
    boundary_reports = []
    for tag in ("counterprobe-deploy01","counterprobe-remove01"):
        source = DIRECTORY / (tag+".json")
        report = json.loads(source.read_text())
        assert report["complete"] and boot(report)==boot(report,"info_after")==EPOCH
        if "deploy" in tag:
            assert report["absent_before"]==[["OK ls 0"]]*3
        else:
            assert report["absent_after"]
        target=DEST/("n95-"+tag+".json")
        boundary_reports.append({"published_path":target.relative_to(ROOT).as_posix(),"published_sha256":publish_text(source,target)})
    result = {"scope":"N95 V35.0.001 standalone user-mode counter calibration; three series/108 samples",
              "status":"measurement_complete","executable_sha256":proof["executable_sha256"],"runs":runs,"groups":groups,
              "deployment_removal":boundary_reports,
              "decision":"Do not qualify per-frame GetCpuTime deltas as CPU usage. Explicit boundary yielding supports an aggregate-window follow-up; it changes wall time and must be disclosed. Do not silently correct old CPU samples.",
              "limits":["No DSP/patcher/performance reservation used; no extrapolation of actual offload CPU percentage from this calibration",
                        "Observed delayed slice accounting; exact installed-kernel implementation has not been matched to published reference source",
                        "Future CPU wall windows must include GetCpuTime calls and any final yield; logging/ARM baseline should remain outside the window",
                        "Historical N95 ring CPU percentages were arithmetic of unqualified short deltas; retain raw values without treating them as qualified load",
                        "Only N95 was tested; E90 remains deferred by user"]}
    path=DEST/"n95-cpu-counter-results.json"
    path.write_bytes((json.dumps(result,indent=2)+"\n").encode())
    print(json.dumps({"path":str(path),"groups":groups},indent=2))


if __name__ == "__main__":
    main()
