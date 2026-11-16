"""N95-only SPU67 fixed bounded cohort; stop on first failure, never contact E90."""
import argparse
import json
import sys

import e90_task_session
from run_ring_series import require_stock_clocks
from summarize_ring import ROOT,boot


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument("--prepare",action="store_true"); group.add_argument("--pilot",action="store_true"); group.add_argument("--restore",action="store_true")
    args=parser.parse_args(); directory=ROOT / "work/evidence/n95/d0-20261003-clean34"; epoch="62209 boot 0 by n"
    def action(name,tag,voices=None,frames=120):
        sys.argv=["e90_task_session.py","--device","n95","--session",str(directory),"--host-version","52",
                  "--artifact-proof","docs/evidence/2026-10-04/n95-spu67-artifacts.json","--action",name,"--tag",tag,"--keep-awake","--expected-boot",epoch]
        if voices is not None: sys.argv += ["--command",f"dmm-ring-spu voices={voices} frames={frames}"]
        if name=="deploy-dsp": sys.argv += ["--artifact","out/dsp/c55stream-dmm-ring-spu.dll55l"]
        e90_task_session.main()
        report=json.loads((directory / (tag+".json")).read_text())
        assert report["complete"] and boot(report)==boot(report,"info_after")==epoch
        if name=="clocks": require_stock_clocks(report,directory,"n95")
    if args.prepare:
        action("clocks","spu67-pilot-clock-before01"); action("deploy-host","spu67-host-deploy01"); action("deploy-dsp","spu67-dsp-deploy01")
    elif args.pilot:
        for voices in (1,8,24): action("run",f"spu67-pilot-v{voices}-f8-01",voices,8)
        action("clocks","spu67-pilot-clock-after01")
    elif args.restore:
        action("restore","spu67-final-restore01"); action("restore-host","spu67-final-host-restore01"); action("verify","spu67-final-verify01")
    else:
        for voices in (1,8,24):
            assert json.loads((directory / f"spu67-pilot-v{voices}-f8-01.json").read_text())["complete"]
        require_stock_clocks(json.loads((directory / "spu67-pilot-clock-after01.json").read_text()),directory,"n95")
        for series in (1,2,3):
            prefix=f"spu67-stock01-s{series}"; action("clocks",prefix+"-clock-before")
            for voices in (1,8,24): action("run",prefix+f"-v{voices}",voices)
            action("clocks",prefix+"-clock-after")
    print(f"SPU67 requested actions complete; restored={args.restore}")


if __name__=="__main__": main()
