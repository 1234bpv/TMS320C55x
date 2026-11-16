"""Compile ARM SPU layout and calculate transport budgets; no phone access."""
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHARED=ROOT.parent
SPU=SHARED / "PS1Emulator/pcsx_rearmed/plugins/dfsound"
OUTPUT=ROOT / "out/spu-boundary"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    OUTPUT.mkdir(exist_ok=True)
    source=(SPU / "spu.c").read_text(encoding="utf-8")
    worker=source.split("static struct spu_worker {")[1].split("} *worker;")[0]
    worker="static struct spu_worker {"+worker+"} *worker;\n"
    keys=["sizeof_int","sizeof_pointer","MAXCHAN","NSSIZE","ADSR_bytes","SPUCHAN_bytes","sample_buf_bytes",
          "SPUInfo_bytes","work_item_bytes","work_channel_bytes","worker_bytes","work_channels_offset","work_sums_offset"]
    values=["sizeof(int)","sizeof(void*)","MAXCHAN","NSSIZE","sizeof(ADSRInfoEx)","sizeof(SPUCHAN)","sizeof(sample_buf)",
            "sizeof(SPUInfo)","sizeof(struct work_item)","sizeof(worker->i[0].ch[0])","sizeof(*worker)",
            "offsetof(struct work_item,ch)","offsetof(struct work_item,SSumLR)"]
    code='#define CALLBACK\n#include <stddef.h>\n#include "externals.h"\n'+worker
    code+='const unsigned int spu_layout[]={'+','.join(values)+'};\n'
    cfile=OUTPUT / "layout.c"; cfile.write_bytes(code.encode("utf-8"))
    obj=OUTPUT / "layout.o"; binary=OUTPUT / "layout.bin"
    compiler=SHARED / "toolchain/gcce/arm-2012.03/bin/arm-none-symbianelf-gcc.exe"
    includes=["-I"+str(SPU),"-I"+str(SHARED / "PS1Emulator/src/compat"),"-I"+str(SHARED / "S60_3rd_FP1/Epoc32/include/libc")]
    subprocess.run([str(compiler),"-O2","-march=armv6","-mtune=arm1136j-s",*includes,"-c",str(cfile),"-o",str(obj)],check=True,timeout=30)
    objcopy=compiler.with_name("arm-none-symbianelf-objcopy.exe")
    subprocess.run([str(objcopy),"-O","binary","-j",".rodata",str(obj),str(binary)],check=True,timeout=15)
    raw=binary.read_bytes(); assert len(raw)==4*len(keys)
    layout=dict(zip(keys,struct.unpack("<"+"I"*len(keys),raw)))
    thread_obj=OUTPUT / "layout-thread.o"; thread_binary=OUTPUT / "layout-thread.bin"
    subprocess.run([str(compiler),"-O2","-march=armv6","-mtune=arm1136j-s","-DWANT_THREAD_CODE=1",*includes,"-c",str(cfile),"-o",str(thread_obj)],check=True,timeout=30)
    subprocess.run([str(objcopy),"-O","binary","-j",".rodata",str(thread_obj),str(thread_binary)],check=True,timeout=15)
    thread_layout=dict(zip(keys,struct.unpack("<"+"I"*len(keys),thread_binary.read_bytes())))
    assert layout["SPUInfo_bytes"]==3840 and thread_layout["SPUInfo_bytes"]==5440
    assert layout["sizeof_int"]==layout["sizeof_pointer"]==4 and layout["MAXCHAN"]==24
    assert layout["NSSIZE"]==914 and layout["work_sums_offset"]==layout["work_channels_offset"]+24*layout["work_channel_bytes"]
    budgets=[]
    for count in (32,64,66,68,128,256,914):
        # Conservative explicit32-bit post-ADSR input; two32-bit volumes/voice;
        # initial/final stereo int32 accumulator. No pointer/struct byte copying.
        input_bytes=24*count*4+24*2*4+count*2*4
        output_bytes=count*2*4
        budgets.append(dict(samples=count,voices=24,input_bytes=input_bytes,output_bytes=output_bytes,
                            input_slots=(input_bytes+479)//480,output_slots=(output_bytes+479)//480,
                            fits_7200_payload_each_direction=input_bytes<=7200 and output_bytes<=7200))
    profile=SHARED / "PS1Emulator/plans/runs/2026-09-28_gemini/n95-spustage-result.md"
    # Values are attributed to this prior report, not new hardware measurements.
    historical=dict(source=profile.relative_to(SHARED).as_posix(),sha256=digest(profile),frames=600,
                    control_pass_ms=[25996,26055],control_doSamples_ms=[968,965],
                    stage_mix_plain_ms_reported=227.9,stage_decode_adpcm_ms_reported=644.4,
                    stage_adsr_ms_reported=18.8,stage_voice_calls=7212,stage_voice_samples=5292000)
    historical["doSamples_mean_us_per_frame"]=(968+965)*1000/2/600
    historical["mix_plain_reported_mean_us_per_frame"]=227.9*1000/600
    historical["mix_plain_reported_mean_us_per_voice_call"]=227.9*1000/7212
    historical["mean_samples_per_voice_call"]=5292000/7212
    historical["doSamples_fraction_of_control_pass_percent"]=100*(968+965)/(25996+26055)
    report=dict(scope="offline current SPU boundary/layout budget; GCCE463 ARM ABI; no emulator writes or phone commands",
                layout=layout,optional_thread_layout=thread_layout,post_ADSR_plain_mix_budgets=budgets,SPU_RAM_bytes=512*1024,
                compiled_layout_evidence=dict(compiler=str(compiler),architecture_flags=["-O2","-march=armv6","-mtune=arm1136j-s"],
                                              generated_source_sha256=digest(cfile),object_sha256=digest(obj),thread_object_sha256=digest(thread_obj),
                                              constant_keys=keys,constants_hex=raw.hex().upper(),thread_constants_hex=thread_binary.read_bytes().hex().upper()),
                SPU_RAM_copy_payload_handoffs_minimum=(512*1024+7199)//7200,
                historical_budget=historical,
                source_files=[dict(path=p.relative_to(SHARED).as_posix(),sha256=digest(p)) for p in
                              (SPU / "spu.c",SPU / "externals.h",SPU / "arm_utils.S",SPU / "adsr.c",SPU / "dma.c",SPU / "registers.c",SPU / "reverb.c",SHARED / "PS1Emulator/src/compat/stdint.h")],
                next_probe="Plain24-voice mix with32-bit samples and accumulator,64 samples/job fits15input+2output slots; baseline must preserve current HAVE_ARMV5 smlawb/smlawt semantics. This only covers mix_plain; decode/ADSR/noise/fmod/reverb/IRQ/state stay on ARM.",
                full_offload_requirements=["SPU RAM mirror/delta coherency for register/DMA writes and readbacks",
                                           "Decode history, ADSR, pitch/fmod, noise generator, reverb state and RAM write ownership",
                                           "Guest-cycle ordering, decode-buffer voice1/3 writes and IRQ equivalence",
                                           "PCM plus mutated-state equivalence, not just integer mix output",
                                           "Actual useful independent ARM W and continuous workload-specific A/H/D"],
                limits=["Native ARM layouts are audited only; raw struct/bitfield/pointer serialization to C55 is invalid.",
                        "Historical stage estimates use sampling1:16 and old source/build/330MHz ARM165MHz bus; current N95 ring stock bus differs. Do not call these current paired A.",
                        "Plain mixing measurement would not quantify the66% ADPCM decode component or full SPU gain.",
                        "E90 deferred; no hardware SPU kernel measurement in this audit."])
    path=ROOT / "docs/evidence/2026-10-04/n95-spu-boundary-audit.json"
    path.write_bytes((json.dumps(report,indent=2)+"\n").encode())
    print(json.dumps(dict(layout=layout,budgets=budgets,historical=historical),indent=2))


if __name__=="__main__":
    main()
