"""Archive MDEC65/host50 with N95 baseimage/import, fixture and build proof."""
import datetime
import argparse
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools/rev"))
from extract_doff_section import Doff,sha256
from audit_dcr_read import build_report
from paths import SHARED
from mdec_reference import render


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort",type=int,choices=(65,66),default=65)
    args=parser.parse_args(); cohort=args.cohort; version=50 if cohort==65 else 51
    proof=ROOT / f"docs/evidence/2026-10-04/n95-mdec{cohort}-artifacts.json"
    assert not proof.exists()
    render()
    host=ROOT / "out/arm/c55stream.exe"
    dsp=ROOT / "out/dsp/c55stream-dmm-ring-mdec.dll55l"
    assert f"C55STREAM v{version} ".encode() in host.read_bytes() and b"RING MDEC PASS" in host.read_bytes()
    result=subprocess.run([str(SHARED / "toolchain/ti/dspbridge/dsp/doffbuild/bin/DLLdump.exe"),str(dsp)],capture_output=True,text=True,check=True,timeout=30)
    assert "Verification PASSED" in result.stdout
    base=Doff(SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
    data=dsp.read_bytes(); strings_size,_,_,_,symbols,_,sections,*_=struct.unpack_from("<4I8HI",data)
    strings=data[56:56+strings_size]; start=56+strings_size+sections*28
    imports=[]
    for i in range(symbols):
        name,_,section,storage=struct.unpack_from("<IIhh",data,start+i*12)
        if section==0 and storage==2:
            imports.append(strings[name:strings.index(0,name)].decode("ascii"))
    assert len(imports)==16 and "__mpyli" in imports and not set(imports)-base.symbols.keys(),imports
    assembly=(ROOT / "out/dsp/kernel_c55-mdec.asm").read_text()
    assert "CALL #__mpyli" in assembly and "_mdec_kernel_process:" in assembly
    host463=ROOT / "out/mdec-kernel/kernel_arm463.o"
    assert struct.unpack_from("<I",host463.read_bytes(),0x24)[0]==0x04000000
    for compiler in ("CSL_Arm_Toolchain", "gcce/arm-2012.03"):
        nm=SHARED / f"toolchain/{compiler}/bin/arm-none-symbianelf-nm.exe"
        obj=host463 if "gcce" in compiler else ROOT / "out/mdec-kernel/kernel_arm343.o"
        assert not subprocess.run([str(nm),"-u",str(obj)],capture_output=True,text=True,check=True,timeout=15).stdout.strip()
    logs=["out/n95-mdec65-dsp-build01.log","out/n95-mdec65-host50-build02.log" if cohort==65 else "out/n95-mdec66-host51-build01.log"]
    for name in logs:
        assert "EXIT_CODE=0\n" in (ROOT/name).read_text(encoding="utf-8")
    files=[host,dsp,ROOT / "out/dsp/stream_node-dmm-ring-mdec.asm",ROOT / "out/dsp/kernel_c55-mdec.asm",host463,
           ROOT / "out/mdec-kernel/kernel_arm343.o",ROOT / "out/mdec-kernel/mdec_probe463.lib",
           ROOT / "src/c55stream.cpp",ROOT / "src/dsp/stream_node.c",ROOT / "src/dsp/dcr_read.s55",
           ROOT / "group/c55stream.mmp",ROOT / "tools/build.cmd",ROOT / "tools/build_stream_node.cmd",ROOT / "tools/build_mdec_kernel.cmd",
           ROOT / "tools/install_mdec_library.ps1",ROOT / "tools/stage_mdec_kernel.py",ROOT / "tools/mdec_reference.py",
           ROOT / "tools/e90_task_session.py",ROOT / "tools/mdec_session_support.py",ROOT / "tools/rev/audit_dcr_read.py"]
    files.extend(sorted((ROOT / "src/mdec").glob("*")))
    archive=ROOT / f"work/evidence/artifacts/c55stream-dmm-ring-mdec-v{cohort}"
    instruction_audit=build_report("dmm-ring-mdec")
    archive.mkdir(exist_ok=True)
    for path in files:
        # Preserve directory structure: two wrappers/headers must remain distinct.
        target=archive / path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        # A failed preflight may leave a partial archive. Resume only exact bytes.
        if target.exists():
            assert target.read_bytes()==path.read_bytes(),"immutable archive drift: "+str(target)
        else:
            target.write_bytes(path.read_bytes())
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_revision=cohort,DSP_kernel_candidate_revision=65,host_version=version,protocol=41,
                device="n95",hardware_verified=False,scope="six IDCT + RGB24 macroblocks; no emulator writes/RLE/DMA/IRQ integration",
                imports=imports,imports_exist_in_saved_n95_baseimage=True,multiply_helper=base.symbols["__mpyli"],
                files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha256(p.read_bytes())) for p in files],
                builds=logs,read_only_DCR_instruction_audit=instruction_audit,
                limits=["Both ARM snapshots and DSP must pass bounded fixtures on the physical N95 before accepting results.",
                        "GCCE463 matches optimization/architecture flags; isolated wrapper/cache/state differs from live emulator.",
                        "DCR is read-only; external-memory publication contract remains unresolved."])
    proof.write_bytes((json.dumps(report,indent=2)+"\n").encode())
    print(proof)


if __name__=="__main__":
    main()
