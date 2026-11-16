"""Archive exact current ARM SMLAD and retained DSP63 before N95-only cohort68."""
import datetime
import json
import re
import subprocess
from pathlib import Path

from stage_wsola_current import main as stage
from summarize_ring import ROOT,digest,load


def main():
    stage(); proof=ROOT/"docs/evidence/2026-10-04/n95-wsola68-artifacts.json"; assert not proof.exists()
    host=ROOT/"out/arm/c55stream.exe"; dsp=ROOT/"out/dsp/c55stream-dmm-ring-wsola.dll55l"
    assert b"C55STREAM v53 " in host.read_bytes() and b"RING WSOLA CURRENT PASS" in host.read_bytes()
    prior=load(ROOT/"docs/evidence/2026-10-04/n95-wsola63-artifacts.json")
    assert digest(dsp)==next(f["sha256"] for f in prior["files"] if f["path"]==dsp.relative_to(ROOT).as_posix())
    obj=ROOT/"out/wsola-current/kernel.o"; obj.parent.mkdir(exist_ok=True)
    obj.write_bytes((ROOT.parent/"S60_3rd_FP1/Epoc32/BUILD/symbuild/c55x/group/C55STREAM/GCCE/urel/kernel.o").read_bytes())
    binary=ROOT.parent/"toolchain/CSL_Arm_Toolchain/bin/arm-none-symbianelf-objdump.exe"
    dis=subprocess.run([str(binary),"-d",str(obj)],capture_output=True,text=True,check=True,timeout=15).stdout
    count=len(re.findall(r"\bsmlad\b",dis)); assert count==5 and "WsolaBestOffsetCurrent" in dis
    dispath=obj.with_name("kernel-disassembly.txt"); dispath.write_bytes(dis.encode())
    log="out/n95-wsola68-host53-build01.log"; assert "EXIT_CODE=0\n" in (ROOT/log).read_text(encoding="utf-8")
    files=[host,dsp,obj,dispath,ROOT/"src/c55stream.cpp",ROOT/"src/wsola_reference.cpp",ROOT/"src/wsola_reference.h",
           ROOT/"group/c55stream.mmp",ROOT/"tools/build.cmd",ROOT/"tools/e90_task_session.py",ROOT/"tools/stage_wsola_current.py",
           ROOT/"tools/wsola_current_session_support.py",ROOT/"tools/run_wsola_current_series.py",ROOT/"tools/record_wsola_current_artifacts.py"]
    files.extend(sorted((ROOT/"src/wsola_current").glob("*")))
    archive=ROOT/"work/evidence/artifacts/c55stream-wsola-current-v68"
    for p in files:
        target=archive/p.relative_to(ROOT); target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): assert target.read_bytes()==p.read_bytes(),"archive drift"
        else: target.write_bytes(p.read_bytes())
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_revision=68,host_version=53,DSP_kernel_candidate_revision=63,protocol=40,device="n95",hardware_verified=False,
                scope="current SMLAD ARM search versus scalar ARM and exact retained DSP63, paired identical inputs; no emulator changes",
                current_ARM_SMLAD_instruction_sites=count,DSP_reused_exact63=True,builds=[log],
                files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in files],
                limits=["Current ARM snapshot packing and search both inside A; compiler CSL343/O2/ARMv6 matches stage1 shell.","Warm isolated baselines not complete live audio/gameplay; useful W unmeasured.","DCR instruction proof remains exact63; external-memory publication contract open."])
    proof.write_bytes((json.dumps(report,indent=2)+"\n").encode()); print(proof)


if __name__=="__main__": main()
