"""Snapshot actual ARM mixer and produce an independent bit-exact wire oracle."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def signed(value,bits=32):
    value&=(1<<bits)-1
    return value-(1<<bits) if value&(1<<(bits-1)) else value


def reference(samples,volumes,sums,voices):
    out=sums[:]
    for v in range(voices):
        packed=((volumes[v][0]&0xffffffff)|((volumes[v][1]<<16)&0xffffffff))<<1
        packed&=0xffffffff
        gains=[signed(packed,16),signed(packed>>16,16)]
        for i,value in enumerate(samples[v]):
            x=signed(value<<1)
            for channel,gain in enumerate(gains):
                out[i*2+channel]=signed(out[i*2+channel]+((x*gain)>>16))
    return out


def fixtures():
    rows=[]; state=0x91827364
    for case in range(8):
        samples=[]; volumes=[]
        for v in range(24):
            row=[]
            for i in range(64):
                state=(state*1664525+1013904223)&0xffffffff
                value=signed(state,16)
                if case==0: value=0
                elif case==1: value=(32767,-32768)[i%2]
                elif case==2: value=(i-32)*(v+1)
                elif case==6: value=signed(state)
                elif case==7: value=(-2147483648,2147483647,0x40000001,-65537)[i%4]
                row.append(value)
            samples.append(row)
            lv,rv=(v*683)%16384,(16383-v*517)%16384
            if case==1: lv,rv=16383,8191
            if case==3: lv,rv=-1234,2345 # Preserve upstream OR/sign spill too.
            if case==4: lv,rv=0,0
            if case==7: lv,rv=0x76543210,signed(0xfedcba98)
            volumes.append([lv,rv])
        sums=[(i-64)*777 for i in range(128)]
        if case==0: sums=[0]*128
        if case==5: sums=[2147483640 if i%2 else -2147483640 for i in range(128)]
        if case==7: sums=[signed(i*0x13579bdf) for i in range(128)]
        rows.append(dict(samples=samples,volumes=volumes,initial=sums,
                         expected=[reference(samples,volumes,sums,n) for n in (1,8,24)]))
    return rows


def emit_array(name,dimensions,values):
    flat=[]
    def flatten(value):
        if isinstance(value,list):
            for item in value: flatten(item)
        else: flat.append(value)
    flatten(values)
    lines=["static const spu_s32 "+name+''.join(f"[{n}]" for n in dimensions)+"={"]
    # Flat initializer with omitted nested braces is valid C and C++.
    for i in range(0,len(flat),12): lines.append(','.join("(-2147483647L-1L)" if v==-2147483648 else str(v)+"L" for v in flat[i:i+12])+",")
    return '\n'.join(lines+["};\n"])


def write_exact(path,data):
    if path.exists(): assert path.read_bytes()==data,"snapshot drift: "+str(path)
    else: path.write_bytes(data)


def main():
    directory=ROOT / "src/spu"; directory.mkdir(exist_ok=True)
    source=ROOT.parent / "PS1Emulator/pcsx_rearmed/plugins/dfsound/arm_utils.S"
    raw=source.read_bytes(); text=raw.decode("utf-8").replace('\r\n','\n')
    body=text.split('#elif defined(HAVE_ARMV5)')[1].split('FUNCTION(mix_chan_rvb)')[0].strip()
    assert body.count('load_varadr r0, ChanBuf')==1 and body.count('smlawb')==2 and body.count('smlawt')==2
    original=body+'\n'
    body=body.replace('FUNCTION(mix_chan):','spu_mix_chan_arm:').replace('load_varadr r0, ChanBuf','ldr         r0, [sp, #24]')
    assembly=text.split('#include')[0]+'.syntax unified\n.arm\n.text\n.align 2\n.global spu_mix_chan_arm\n.type spu_mix_chan_arm,%function\n'+body+'\n.size spu_mix_chan_arm,.-spu_mix_chan_arm\n.section .note.GNU-stack,"",%progbits\n'
    write_exact(directory/'mix_arm.s',assembly.encode())
    rows=fixtures()
    header='// Generated bit-exact ARM SMLAW oracle; cases6/7 exceed legal PCM range.\n#ifndef SPU_MIX_FIXTURES_H\n#define SPU_MIX_FIXTURES_H\n#include "mix.h"\n'
    for field,dims in (("samples",[8,24,64]),("volumes",[8,24,2]),("initial",[8,128]),("expected",[8,3,128])):
        header+=emit_array('spu_'+field,dims,[r[field] for r in rows])
    header+='#endif\n'; write_exact(directory/'fixtures.h',header.encode())
    report=dict(source_sha256=hashlib.sha256(raw).hexdigest().upper(),source=str(source.relative_to(ROOT.parent)),
                original_ARMV5_body_LF_sha256=hashlib.sha256(original.encode()).hexdigest().upper(),
                snapshot_sha256=hashlib.sha256(assembly.encode()).hexdigest().upper(),
                fixtures_sha256=hashlib.sha256(header.encode()).hexdigest().upper(),
                adaptations=["symbol renamed to spu_mix_chan_arm", "one global ChanBuf literal-address load replaced by fifth-argument stack load at24B after the same six-register push", "bare ARM assembler directives replace upstream macros/includes; ARMv5 instructions retained under ARMv6 host target"],
                scope="plain mix only; exact current ARM packed-volume/SMLAW/wrap32 arithmetic; not full SPU or final PCM",
                license="upstream GPL2-or-later or LGPL2.1-or-later; original notice preserved; GPL selected for this research snapshot")
    write_exact(directory/'snapshot.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
