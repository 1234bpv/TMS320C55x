"""Verify dependency publication arithmetic from hashed, validated wire journals."""
import hashlib
import itertools
import json
import math
import re

from mdec_session_support import validate_mdec
from spu_session_support import validate_spu
from wsola_current_session_support import validate_current
from verify_ring_publication import ROOT,checked


def distribution(values):
    ordered=sorted(values)
    return dict(count=len(values),min=min(values),mean=sum(values)/len(values),
                p50=ordered[math.ceil(.5*len(values))-1],p95=ordered[math.ceil(.95*len(values))-1],
                p99=ordered[math.ceil(.99*len(values))-1],max=max(values))


def main():
    report=json.loads((ROOT/"docs/evidence/2026-10-04/n95-offload-dependency-audit.json").read_text())
    assert report["status"]=="audit_complete" and report["plan_status"]=="in_progress"
    for source in report["sources"]:
        path=ROOT.parent/source["path"]
        # Excerpts remain portable; when the original tree exists, verify its full identity too.
        lines=None
        if path.exists():
            raw=path.read_bytes()
            assert hashlib.sha256(raw).hexdigest().upper()==source["sha256"],path
            lines=raw.decode("utf-8").splitlines()
        for excerpt in source["excerpts"]:
            assert hashlib.sha256(excerpt["text"].encode()).hexdigest().upper()==excerpt["sha256"]
            assert excerpt["line"]>0
            if lines is not None: assert lines[excerpt["line"]-1]==excerpt["text"]
    assert [m["cohort"] for m in report["measurements"]]==[66,67,68]
    total=0
    for measurement in report["measurements"]:
        result=json.loads(checked(measurement["published_result"],measurement["result_sha256"]))
        cohort=measurement["cohort"]; selected={}
        for run in result["runs"]:
            text=checked(run["published_journal"],run["published_sha256"])
            validator,version={66:(validate_mdec,51),67:(validate_spu,52),68:(validate_current,53)}[cohort]
            parsed=validator(text,run["command"],version)
            timings=[tuple(map(int,t)) for t in parsed["timings"]]
            assert [list(t) for t in timings]==run["timing_rows"]
            if cohort==66:
                ready=[tuple(map(int,t)) for t in parsed["ready"]]
                assert [list(t) for t in ready]==run["ready_rows"]
            lifecycle=tuple(map(int,re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0",text).groups()))
            assert lifecycle==(run["setup_us"],run["teardown_us"])
            if run["pilot"]: continue
            key=str(run["macroblocks_per_job"]) if cohort==66 else str(run["voices"]) if cohort==67 else "current_SMLAD"
            rows=selected.setdefault(key,[])
            for i,t in enumerate(timings):
                if cohort==66: a=t[2]/16; p=t[4]; notification=ready[i][1]; end=ready[i][2]
                elif cohort==67: a=t[1]/256; p=t[3]; notification=t[4]; end=t[5]
                else: a=t[2]/64; p=t[4]; notification=t[5]; end=t[6]
                assert a>0 and 0<p<=end-notification
                # Match operation order of the published conversion, not rounded display values.
                scale=1000000/32768
                rows.append((a*scale,end*scale,p*scale,(end-notification)*scale,sum(lifecycle)))
        assert set(selected)==set(measurement["groups"])
        for key,rows in selected.items():
            group=measurement["groups"][key]; assert group["jobs"]==len(rows)==360
            total+=len(rows)
            for column,label in enumerate(("A_us","T_ready_us","pack_us","serial_outside_notification_us")):
                assert group[label]==distribution([r[column] for r in rows]),(cohort,key,label)
            assert group["pack_less_than_A_jobs"]==sum(r[2]<r[0] for r in rows)
            assert group["serial_lower_bound_less_than_A_jobs"]==sum(r[3]<r[0] for r in rows)
            assert group["paired_W_threshold_with_zero_setup_us"]==distribution([r[1]-r[0] for r in rows])
            assert group["single_ARM_necessary_condition"]=={str(n):sum(r[3]+r[4]/n<r[0] for r in rows) for n in (16,64,256,1000,10000,1000000)}
    # Exhaustive small domains include equality boundaries and zero work/setup.
    for h,d,w,q,a in itertools.product(range(8),repeat=5):
        assert (max(h+d,w)+q<a+w)==(q<a and w>h+d+q-a)
        assert (h+max(d,w)+q<a+w)==(h+q<a and w>h+d+q-a)
    assert total==2520
    print("Verified dependency source excerpts,2520 non-pilot journal timings,paired serial bounds/setup scenarios and32768 strict model boundary cases; no phone access.")


if __name__=="__main__": main()
