"""Snapshot the exact local MDEC pure kernel; emulator remains read-only."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def main():
    source=ROOT.parent / "PS1Emulator/pcsx_rearmed/libpcsxcore/mdec.c"
    raw=source.read_bytes()
    text=raw.decode("utf-8").replace("\r\n","\n")
    assert text.count("/* MDEC-KERNEL-BEGIN */")==text.count("/* MDEC-KERNEL-END */")==1
    license_=text.split('#include "arm_features.h"')[0]
    kernel=text.split("/* MDEC-KERNEL-BEGIN */")[1].split("/* MDEC-KERNEL-END */")[0].strip()+"\n"
    assert kernel.count("__attribute__((noinline))")==2 and kernel.count("(1 << 19)")==3
    directory=ROOT / "src/mdec"
    directory.mkdir(exist_ok=True)
    arm=(license_+"// Exact MDEC-KERNEL snapshot; see snapshot.json for upstream hash.\n"+kernel).encode()
    # C55x int is16 bits. Arithmetic/loop types become long32 in the wrapper.
    # Explicit long literals prevent a16-bit shift before conversion to u32.
    # GNU noinline attributes are replaced by corresponding TI pragmas.
    dsp=(license_+"// C55x adaptation: int->long in wrapper, explicit32-bit rounding literals.\n"
         +"#pragma FUNC_CANNOT_INLINE(idct_fill)\n#pragma FUNC_CANNOT_INLINE(idct_spread)\n"
         +kernel.replace("__attribute__((noinline)) ","").replace("(1 << 19)","(1UL << 19)")) .encode()
    for name,data in (("kernel_arm.inc",arm),("kernel_c55.inc",dsp)):
        target=directory/name
        if target.exists():
            assert target.read_bytes()==data,"refuse changed snapshot: "+name
        else:
            target.write_bytes(data)
    metadata={"source":"../PS1Emulator/pcsx_rearmed/libpcsxcore/mdec.c","source_sha256":sha(raw),
              "kernel_LF_sha256":sha(kernel.encode()),"ARM_snapshot_sha256":sha(arm),"C55_snapshot_sha256":sha(dsp),
              "scope":"six IDCT blocks + exact current RGB24 conversion; RLE/dequantization/DMA/IRQ/state remain outside",
              "C55_adaptations":["wrapper macro converts int to32-bit long; no16-bit coefficient narrowing",
                                 "three rounding literals1<<19 become1UL<<19 before evaluation",
                                 "GNU noinline attributes replaced by TI FUNC_CANNOT_INLINE pragmas",
                                 "RGB24 output is192 packed32-bit words; u8 pointer is only cast back to aligned u32 within conversion"],
              "ARM_baseline_limit":"snapshot can be built by CSL343; current emulator core usesGCCE463, which needs a matching baseline before claiming application A",
              "license":"GPL-2.0-or-later; original copyright/license notice preserved"}
    target=directory/"snapshot.json"
    if target.exists():
        assert json.loads(target.read_text())==metadata
    else:
        target.write_bytes((json.dumps(metadata,indent=2)+"\n").encode())
    print(json.dumps(metadata,indent=2))


if __name__=="__main__":
    main()
