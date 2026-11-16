"""Recompute published CPU calibration from committed journals only."""
import json

from counter_probe_session import validate
from summarize_ring import stats
from verify_ring_publication import ROOT, checked


def main():
    result=json.loads((ROOT / "docs/evidence/2026-10-04/n95-cpu-counter-results.json").read_text())
    records=[]
    for run in result["runs"]:
        rows=validate(checked(run["published_path"],run["published_sha256"]))
        assert len(rows)==len(run["records"])==36
        for row,record in zip(rows,run["records"]):
            assert [record[key] for key in ("index","repeat","sleep","boundary_yield","requested_us","inner_ticks","outer_ticks","nticks","utc_us")] == list(map(int,row[:9]))
            assert record["CPU_before_us"]==int(row[9]+row[10],16)
            assert record["CPU_after_us"]==int(row[11]+row[12],16)
            assert record["CPU_delta_us"]==record["CPU_after_us"]-record["CPU_before_us"]
            assert record["outer_wall_us"]==record["outer_ticks"]*1000000/32768
            assert record["series"]==run["series"]
        records.extend(run["records"])
    assert len(records)==108
    for name,group in result["groups"].items():
        import re
        duration,sleep,yield_=map(int,re.fullmatch(r"duration(\d+)-sleep([01])-yield([01])",name).groups())
        selected=[r for r in records if (r["requested_us"],r["sleep"],r["boundary_yield"])==(duration,sleep,yield_)]
        assert group["samples"]==len(selected)==9
        assert group["CPU_delta_us"]==stats([r["CPU_delta_us"] for r in selected])
        assert group["outer_wall_us"]==stats([r["outer_wall_us"] for r in selected])
        assert group["CPU_over_wall_percent"]==stats([100*r["CPU_delta_us"]/r["outer_wall_us"] for r in selected])
        assert group["zero_CPU_delta_samples"]==sum(r["CPU_delta_us"]==0 for r in selected)
        assert group["CPU_exceeds_outer_wall_samples"]==sum(r["CPU_delta_us"]>r["outer_wall_us"] for r in selected)
    assert result["groups"]["duration1000-sleep0-yield0"]["zero_CPU_delta_samples"]==8
    assert result["groups"]["duration10000-sleep0-yield0"]["zero_CPU_delta_samples"]==8
    assert result["groups"]["duration10000-sleep1-yield0"]["CPU_exceeds_outer_wall_samples"]==2
    assert all(r["CPU_delta_us"]<=r["outer_wall_us"] for r in records if r["boundary_yield"])
    for item in result["deployment_removal"]:
        report=json.loads(checked(item["published_path"],item["published_sha256"]))
        assert report["complete"]
        if report["action"]=="deploy":
            assert report["absent_before"]==[["OK ls 0"]]*3
        else:
            assert report["action"]=="remove" and report["absent_after"]
    proof=json.loads((ROOT / "docs/evidence/2026-10-04/n95-counterprobe-artifacts.json").read_text())
    assert proof["executable_sha256"]==result["executable_sha256"]
    print("Verified 108 standalone N95 counter samples, group arithmetic and exact owned-file cleanup; short CPU deltas unqualified, boundary-yield follow-up supported.")


if __name__=="__main__":
    main()
