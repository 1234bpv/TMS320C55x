"""N95-only MDEC65 series. First failure stops; E90 is never contacted."""
import argparse
import json
import sys

import e90_task_session
from run_ring_series import require_stock_clocks
from summarize_ring import ROOT,boot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-rest",action="store_true")
    parser.add_argument("--restore",action="store_true")
    parser.add_argument("--prepare",action="store_true")
    parser.add_argument("--cohort",type=int,choices=(65,66),default=65)
    args=parser.parse_args()
    directory=ROOT / "work/evidence/n95/d0-20261003-clean34"
    epoch="62209 boot 0 by n"
    cohort=args.cohort; version=50 if cohort==65 else 51
    def action(name,tag,batch=None,frames=120):
        sys.argv=["e90_task_session.py","--device","n95","--session",str(directory),"--host-version",str(version),
                  "--artifact-proof",f"docs/evidence/2026-10-04/n95-mdec{cohort}-artifacts.json",
                  "--action",name,"--tag",tag,"--keep-awake","--expected-boot",epoch]
        if batch is not None:
            sys.argv += ["--command",f"dmm-ring-mdec batch={batch} frames={frames}"]
        if name=="deploy-dsp":
            sys.argv += ["--artifact","out/dsp/c55stream-dmm-ring-mdec.dll55l"]
        e90_task_session.main()
        report=json.loads((directory / (tag+".json")).read_text())
        assert report["complete"] and boot(report)==boot(report,"info_after")==epoch
        if name=="clocks":
            require_stock_clocks(report,directory,"n95")
    if args.prepare:
        action("clocks",f"mdec{cohort}-pilot-clock-before01")
        action("deploy-host",f"mdec{cohort}-host-deploy01")
        action("deploy-dsp",f"mdec{cohort}-dsp-deploy01")
    elif args.restore:
        action("restore",f"mdec{cohort}-final-restore01")
        action("restore-host",f"mdec{cohort}-final-host-restore01")
        action("verify",f"mdec{cohort}-final-verify01")
    elif args.pilot_rest:
        for batch in ((2,4) if cohort==65 else (1,2,4)):
            action("run",f"mdec{cohort}-pilot-b{batch}-f8-01",batch,8)
        action("clocks",f"mdec{cohort}-pilot-clock-after01")
    else:
        # Full runs require all short jobs and the final stock clock gate.
        for batch in (1,2,4):
            assert json.loads((directory / f"mdec{cohort}-pilot-b{batch}-f8-01.json").read_text())["complete"]
        require_stock_clocks(json.loads((directory / f"mdec{cohort}-pilot-clock-after01.json").read_text()),directory,"n95")
        for series in (1,2,3):
            prefix=f"mdec{cohort}-stock01-s{series}"
            action("clocks",prefix+"-clock-before")
            for batch in (1,2,4):
                action("run",prefix+f"-b{batch}",batch)
            action("clocks",prefix+"-clock-after")
    print(f"MDEC{cohort} requested actions complete; restored={args.restore}")


if __name__=="__main__":
    main()
