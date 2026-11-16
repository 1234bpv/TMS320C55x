"""N95-only WSOLA68/host53, exact retained DSP63; bounded first-failure stop."""
import argparse
import json
import sys

import e90_task_session
from run_ring_series import require_stock_clocks
from summarize_ring import ROOT,boot
from device_work_lock import device_lock


def locked_main():
    parser=argparse.ArgumentParser(description=__doc__); group=parser.add_mutually_exclusive_group()
    for flag in ("prepare","pilot","restore","resume-third"): group.add_argument("--"+flag,action="store_true")
    parser.add_argument("--recovery",action="store_true",help="use separate final restoration02 tags after third-series recovery")
    args=parser.parse_args(); directory=ROOT / "work/evidence/n95/d0-20261003-clean34"; epoch="62209 boot 0 by n"
    def action(name,tag,frames=120):
        sys.argv=["e90_task_session.py","--device","n95","--session",str(directory),"--host-version","53",
                  "--artifact-proof","docs/evidence/2026-10-04/n95-wsola68-artifacts.json","--action",name,"--tag",tag,"--keep-awake","--expected-boot",epoch]
        if name=="run": sys.argv += ["--command",f"dmm-ring-wsola-current frames={frames}"]
        if name=="deploy-dsp": sys.argv += ["--artifact","out/dsp/c55stream-dmm-ring-wsola.dll55l"]
        e90_task_session.main(); report=json.loads((directory/(tag+".json")).read_text())
        assert report["complete"] and boot(report)==boot(report,"info_after")==epoch
        if name=="clocks": require_stock_clocks(report,directory,"n95")
    if args.prepare:
        action("clocks","wsola68-pilot-clock-before01"); action("deploy-host","wsola68-host-deploy01"); action("deploy-dsp","wsola68-dsp-deploy01")
    elif args.pilot:
        action("run","wsola68-pilot-f8-01",8); action("clocks","wsola68-pilot-clock-after01")
    elif args.restore:
        suffix="02" if args.recovery else "01"
        action("restore","wsola68-final-restore"+suffix); action("restore-host","wsola68-final-host-restore"+suffix); action("verify","wsola68-final-verify"+suffix)
    elif args.resume_third:
        # This recovery is specific to the verified pre-START host mismatch,
        # not an unchanged retry after a hardware failure.
        failure=json.loads((directory/"wsola68-stock01-s3-run.json").read_text())
        transport=(directory/"wsola68-stock01-s3-run-transport.txt").read_text()
        assert not failure["complete"] and failure["error"]=="RuntimeError: installed host differs from the built v53 artifact"
        assert not any(s in transport for s in ("> START ","> PUT ","> KILL ")) and "exit" not in failure
        assert (directory/"wsola68-stock01-s3-run-host-readback.exe").read_bytes()==(directory/"original-3.bin").read_bytes()
        assert json.loads((directory/"wsola68-final-verify01.json").read_text())["complete"]
        for s in (1,2): assert json.loads((directory/f"wsola68-stock01-s{s}-run.json").read_text())["complete"]
        action("clocks","wsola68-recovery-clock-before02"); action("deploy-host","wsola68-host-deploy02"); action("deploy-dsp","wsola68-dsp-deploy02")
        prefix="wsola68-stock02-s3"; action("clocks",prefix+"-clock-before"); action("run",prefix+"-run"); action("clocks",prefix+"-clock-after")
    else:
        assert json.loads((directory/"wsola68-pilot-f8-01.json").read_text())["complete"]
        require_stock_clocks(json.loads((directory/"wsola68-pilot-clock-after01.json").read_text()),directory,"n95")
        for series in (1,2,3):
            prefix=f"wsola68-stock01-s{series}"; action("clocks",prefix+"-clock-before"); action("run",prefix+"-run"); action("clocks",prefix+"-clock-after")
    print(f"WSOLA68 requested actions complete; restored={args.restore}")


def main():
    with device_lock(ROOT / "out/n95-work.lock"): locked_main()


if __name__=="__main__": main()
