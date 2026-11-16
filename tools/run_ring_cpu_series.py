"""Three N95-only aggregate CPU64 series, stopped by any clock/run/epoch failure."""
import json
import sys

import e90_task_session
from run_ring_series import require_stock_clocks
from summarize_ring import ROOT, boot


def main():
    directory=ROOT / "work/evidence/n95/d0-20261003-clean34"
    epoch="62209 boot 0 by n"
    def action(name,tag,batch=None):
        sys.argv=["e90_task_session.py","--device","n95","--session",str(directory),
                  "--host-version","49","--action",name,"--tag",tag,"--keep-awake","--expected-boot",epoch]
        if batch is not None:
            sys.argv += ["--command",f"dmm-ring-window batch={batch} frames=120"]
        e90_task_session.main()
        report=json.loads((directory / (tag+".json")).read_text())
        assert report["complete"] and boot(report)==boot(report,"info_after")==epoch
        if name=="clocks":
            require_stock_clocks(report,directory,"n95")
    for series in (1,2,3):
        prefix=f"window64-stock01-s{series}"
        action("clocks",prefix+"-clock-before")
        for batch in (1,2,8,15):
            action("run",prefix+f"-b{batch}",batch)
        action("clocks",prefix+"-clock-after")
    print("N95 CPU64: three series/12 runs complete, stock snapshots and daemon epoch stable")


if __name__=="__main__":
    main()
