"""Archive recovery's OS lock/session changes separately from immutable preflight68."""
import json
from summarize_ring import ROOT,digest


def main():
    archive=ROOT/"work/evidence/artifacts/c55stream-wsola-current-v68-recovery02"
    paths=["tools/device_work_lock.py","tools/e90_task_session.py","tools/run_wsola_current_series.py","tools/test_wsola_current_session.py","tools/record_wsola_recovery.py"]
    for name in paths:
        p=ROOT/name; target=archive/name; target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): assert target.read_bytes()==p.read_bytes(),"recovery archive drift"
        else: target.write_bytes(p.read_bytes())
    result=dict(scope="WSOLA68 recovery02 host orchestration only; exact host53/DSP63 unchanged",original_preflight="docs/evidence/2026-10-04/n95-wsola68-artifacts.json",
                change="OS nonblocking per-device lock held across entire runner, nested session actions reuse same process owner; competing actions fail before connecting",
                files=[dict(path=name,sha256=digest(ROOT/name)) for name in paths])
    dest=ROOT/"docs/evidence/2026-10-04/n95-wsola68-recovery-artifacts.json"; assert not dest.exists()
    dest.write_bytes((json.dumps(result,indent=2)+"\n").encode()); print(dest)


if __name__=="__main__": main()
