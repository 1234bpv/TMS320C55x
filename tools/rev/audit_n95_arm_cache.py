"""Trace saved N95 utility2 to its kernel cache operations, without device I/O."""
import hashlib
import json
import struct
from pathlib import Path

from audit_dmm_ownership import exports
from compare_node_info import Module,arm_bl_target
from paths import ROM

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/"docs/evidence/2026-10-04/n95-arm-cache-path-audit.json"


def branch(address,word):
    assert (word>>25)&7==5
    displacement=word&0xffffff
    if displacement&0x800000: displacement-=0x1000000
    return (address+8+4*displacement)&0xffffffff


def main():
    prior=json.loads((ROOT/"docs/evidence/2026-10-03/dmm-ownership-native-audit.json").read_text())
    utility=Module(Path(ROM)/"ebridgeutil.ldd"); kernel=Module(Path(ROM)/"ekern.exe")
    for name,module in (("utility",utility),("kernel",kernel)):
        assert hashlib.sha256(module.data).hexdigest().upper()==prior["n95"]["module_sha256"][name]
    table=exports(kernel)
    assert table[377]==0x8007343c and table[375]==0x8007344c
    for call,stub,ordinal in ((0x801b5acc,0x801b5c28,378),(0x801b5ad8,0x801b5c20,376)):
        assert arm_bl_target(call,utility.word(call))==stub
        assert utility.word(stub)==0xe51ff004 and utility.word(stub+4)==table[ordinal-1]
    expected={
        0x8007343c:0xe1a02001,0x80073440:0xe1a01000,0x80073444:0xe3a00006,
        0x80073448:0xeaffffc3,0x8007344c:0xe1a02001,0x80073450:0xe1a01000,
        0x80073454:0xe3a00006,0x80073458:0xeaffffa1,
        0x80073364:0xe1b01002,0x80073368:0x13130002,0x8007336c:0x012fff1e,
        0x80073380:0xe1520001,0x80073384:0x2affe8b8,0x80073388:0x3affe8c5,
        0x800732e8:0xe1b04002,0x800732f4:0x08bd81f0,0x800732f8:0xe3150002,
        0x80073300:0x0a000009,0x80073310:0xe1500004,0x80073314:0x2a000001,
        0x80073318:0xebffe8f6,0x8007331c:0xea000002,0x80073328:0xebffe8c2,
        0x8007332c:0xe3150001,0x80073330:0x08bd81f0,
        0x8006d690:0x2e070f3a,0x8006d698:0x8afffffb,0x8006d69c:0xee071f9a,
        0x8006d6a0:0xe12fff1e,0x8006d6bc:0xee070f5a,0x8006d6c4:0xee070f5a,
        0x8006d6cc:0xee070f5a,0x8006d6d4:0xee070f5a,0x8006d6ec:0x1afffff2,
        0x8006d6f0:0xee073f9a,0x8006d6f4:0xe12fff1e,
        0x8006d65c:0x2e070f36,0x8006d664:0x8afffffb,0x8006d668:0xe12fff1e,
        0x8006d710:0xee070f5e,0x8006d718:0xee070f5e,0x8006d720:0xee070f5e,
        0x8006d728:0xee070f5e,0x8006d740:0x1afffff2,0x8006d744:0xee073f9a,
        0x8006d748:0xe12fff1e}
    for address,word in expected.items(): assert kernel.word(address)==word,hex(address)
    branches={0x80073448:0x8007335c,0x80073458:0x800732e4,
              0x80073384:0x8006d66c,0x80073388:0x8006d6a4,
              0x80073318:0x8006d6f8,0x80073328:0x8006d638,
              0x8006d698:0x8006d68c,0x8006d6ec:0x8006d6bc,
              0x8006d664:0x8006d658,0x8006d740:0x8006d710}
    for address,target in branches.items(): assert branch(address,kernel.word(address))==target
    ranges=[]
    for label,start,size in (("exports378_376",0x8007343c,32),("clean_dispatch",0x8007335c,48),
                             ("invalidate_dispatch",0x800732e4,80),("invalidate_MVA",0x8006d638,52),
                             ("clean_MVA",0x8006d66c,56),("clean_SetWay",0x8006d6a4,84),
                             ("clean_invalidate_SetWay",0x8006d6f8,84)):
        raw=kernel.read(start,size)
        ranges.append(dict(label=label,address=f"{start:08X}",bytes=size,sha256=hashlib.sha256(raw).hexdigest().upper(),
                           instructions=[dict(address=f"{start+i*4:08X}",word=f"{w:08X}") for i,w in enumerate(struct.unpack(f"<{size//4}I",raw))]))
    report=dict(scope="saved N95 firmware exact instructions; no phone commands, E90 access or changes to deployed binaries",
                status="ARM_path_verified_DSP_endpoint_unresolved",module_sha256=prior["n95"]["module_sha256"],
                utility_order=[378,376],exports={"378":"8007343C","376":"8007344C"},
                asserted_instruction_sites=len(expected),ranges=ranges,
                branches=[dict(address=f"{a:08X}",target=f"{t:08X}") for a,t in branches.items()],
                cp15_operations=dict(clean_MVA=["8006D690"],clean_SetWay=["8006D6BC","8006D6C4","8006D6CC","8006D6D4"],
                                     invalidate_MVA=["8006D65C"],clean_invalidate_SetWay=["8006D710","8006D718","8006D720","8006D728"],
                                     DSB=["8006D69C","8006D6F0","8006D744"]),
                interpretation=["Both two-argument exported wrappers pass internal mask6: mask0x2 selects data-cache work, mask0x1 is zero so instruction-cache work is skipped.",
                                "Ordinal378 dispatches to MVA clean or Set/Way clean according to the configured threshold; both branches end in CP15 c7,c10,4 (DSB).",
                                "Ordinal376 dispatches to MVA invalidate or whole-cache Set/Way clean-invalidate according to the configured threshold. The whole-cache branch includes DSB; the short MVA invalidate branch has no explicit DSB in its52bytes.",
                                "Whole-region utility2 always calls378 before376; an ARM dirty line created during DSP ownership could therefore overwrite DSP results during the clean phase.",
                                "ARM-side DSB is not evidence that an earlier DSP master write has reached SDRAM before its mailbox interrupt."],
                reference=dict(author="Arm",url="https://documentation-service.arm.com/static/5e8e4306fd977155116aade2",
                               document="ARM1136JF-S/J-S TRM DDI0211I r1p3",sections=["Table3-77,3-99/3-100 cache line operations","CP15 c7 Flush operations,3-105..3-107 DSB"],
                               scope="Instruction semantics only; not proof of the phone's core revision or OMAP interconnect acknowledgement rules"),
                limits=["Runtime cache metadata/threshold and page-table attributes not dumped; both compiled threshold branches checked.",
                        "No claim that a short invalidate without a subsequent explicit DSB proves all cache-operation completion ordering; caller/context semantics remain separate.",
                        "Independent DSP endpoint-memory publication contract remains open; successful isolated jobs and measured WPE0 do not establish a general fence."])
    DEST.write_bytes((json.dumps(report,indent=2)+"\n").encode()); print(DEST); print("Verified46 kernel instruction sites,10 branch destinations, utility import order and7 code ranges.")


if __name__=="__main__": main()
