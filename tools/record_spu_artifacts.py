"""Preflight SPU67/host52, saved N95 imports, exact ARM instructions and archive."""
import datetime
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "tools/rev"))
from extract_doff_section import Doff,sha256
from audit_dcr_read import build_report
from paths import SHARED
from stage_spu_mix import main as stage


def main():
    proof=ROOT / "docs/evidence/2026-10-04/n95-spu67-artifacts.json"
    assert not proof.exists(); stage()
    host=ROOT / "out/arm/c55stream.exe"; dsp=ROOT / "out/dsp/c55stream-dmm-ring-spu.dll55l"
    assert b"C55STREAM v52 " in host.read_bytes() and b"RING SPU PASS" in host.read_bytes()
    result=subprocess.run([str(SHARED / "toolchain/ti/dspbridge/dsp/doffbuild/bin/DLLdump.exe"),str(dsp)],capture_output=True,text=True,check=True,timeout=30)
    assert "Verification PASSED" in result.stdout
    base=Doff(SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
    data=dsp.read_bytes(); strings_size,_,_,_,symbols,_,sections,*_=struct.unpack_from("<4I8HI",data)
    strings=data[56:56+strings_size]; start=56+strings_size+sections*28; imports=[]
    for i in range(symbols):
        name,_,section,storage=struct.unpack_from("<IIhh",data,start+i*12)
        if section==0 and storage==2: imports.append(strings[name:strings.index(0,name)].decode("ascii"))
    assert len(imports)==15 and "__mpyli" not in imports and not set(imports)-base.symbols.keys(),imports
    asm=(ROOT / "out/dsp/stream_node-dmm-ring-spu.asm").read_text()
    product=asm.split("_spu_smlaw_product:")[1].split('\t.sect')[0]
    assert "MPY T0, AC0, AC0" in product and "MAC AC1, T0, AC0" in product and "CALL #__mpyli" not in asm
    objects=[]
    for name in ("mix_arm.o","mix_job_arm.o"):
        source=SHARED / f"S60_3rd_FP1/Epoc32/BUILD/symbuild/c55x/group/C55STREAM/GCCE/urel/{name}"
        target=ROOT / "out/spu-kernel" / name; target.parent.mkdir(exist_ok=True); target.write_bytes(source.read_bytes()); objects.append(target)
    objdump=SHARED / "toolchain/CSL_Arm_Toolchain/bin/arm-none-symbianelf-objdump.exe"
    dis=subprocess.run([str(objdump),"-d",str(objects[0])],capture_output=True,text=True,check=True,timeout=15).stdout
    assert len(re.findall(r"\bsmlawb\b",dis))==2 and len(re.findall(r"\bsmlawt\b",dis))==2 and "[sp, #24]" in dis
    dispath=ROOT / "out/spu-kernel/mix_arm-disassembly.txt"; dispath.write_bytes(dis.encode())
    logs=["out/n95-spu67-dsp-build01.log","out/n95-spu67-host52-build03.log"]
    assert all("EXIT_CODE=0\n" in (ROOT/name).read_text(encoding="utf-8") for name in logs)
    files=[host,dsp,ROOT / "out/dsp/stream_node-dmm-ring-spu.asm",*objects,dispath,
           ROOT / "src/c55stream.cpp",ROOT / "src/dsp/stream_node.c",ROOT / "src/dsp/spu_mix_ring.inc",ROOT / "src/dsp/dcr_read.s55",
           ROOT / "group/c55stream.mmp",ROOT / "tools/build.cmd",ROOT / "tools/build_stream_node.cmd",
           ROOT / "tools/stage_spu_mix.py",ROOT / "tools/e90_task_session.py",ROOT / "tools/spu_session_support.py",
           ROOT / "tools/run_spu_ring_series.py",ROOT / "tools/rev/audit_dcr_read.py",ROOT / "tools/record_spu_artifacts.py"]
    files.extend(sorted((ROOT / "src/spu").glob("*")))
    archive=ROOT / "work/evidence/artifacts/c55stream-dmm-ring-spu-v67"
    audit=build_report("dmm-ring-spu")
    for path in files:
        target=archive / path.relative_to(ROOT); target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): assert target.read_bytes()==path.read_bytes(),"immutable archive drift: "+str(target)
        else: target.write_bytes(path.read_bytes())
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate_revision=67,host_version=52,protocol=42,
                device="n95",hardware_verified=False,scope="post-ADSR plain mix only, 64 samples/voice, 1/8/24 voices; no full SPU or emulator integration",
                imports=imports,imports_exist_in_saved_n95_baseimage=True,
                ARM_instruction_counts=dict(smlawb=2,smlawt=2),ARM_adapter="global ChanBuf source replaced by fifth pointer argument at sp+24",
                DSP_product="signed32 x signed16 high-product via native MPY/MAC; no 40-bit long-long narrowing",
                files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha256(p.read_bytes())) for p in files],
                builds=logs,read_only_DCR_instruction_audit=audit,
                limits=["ARM and DSP must pass all eight fixtures on N95 before full series.","ARM timer averages 256 repeated additions on warm sums; validates one job and modular 256-job sums outside timing.","DCR reads are diagnostic only; external-memory publication contract remains open."])
    proof.write_bytes((json.dumps(report,indent=2)+"\n").encode()); print(proof)


if __name__=="__main__": main()
