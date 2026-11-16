"""Trace CMM ring backing to bridgecfg's retained hardware chunk in saved ROM."""
import hashlib
import json
import struct
from pathlib import Path

from compare_node_info import Module, arm_bl_target
from audit_dmm_ownership import exports
from paths import ROM, SHARED

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = "https://raw.githubusercontent.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/master/kernel/eka/include/memmodel/epoc/platform.h"


def audit(directory, rom_path, cfg_delta, early_delta, late_delta):
    cfg = Module(directory / "bridgecfg.dll")
    pdd = Module(directory / "ehwaomap.pdd")
    kernel = Module(directory / "ekern.exe")
    raw = rom_path.read_bytes()
    offset = cfg.base - 0x80000000
    # The stored XIP file ends before two import veneers. Read those from the
    # saved ROM only after verifying the complete stored code matches it.
    if raw[offset:offset + len(cfg.data) - 120] != cfg.data[120:]:
        raise ValueError("bridgecfg GET code does not match saved ROM")
    def raw_word(address):
        return struct.unpack_from("<I", raw, address - 0x80000000)[0]
    cfg_checks = {
        0x803DD2A0: 0x03A01002,  # first ASIC selector2
        0x803DD2C4: 0xE591C054,  # ASIC virtual method+84
        0x803DD2C8: 0xE1A0100D,
        0x803DD2CC: 0xE28D2018,  # returned physical address
        0x803DD2C0: 0xE28D300C,  # returned bytes
        0x803DD2DC: 0xE59F7348,
        0x803DD2E0: 0xE59D1018,
        0x803DD2E4: 0xE59D200C,
        0x803DD2E8: 0xE28D0010,  # retained first chunk
        0x803DD2EC: 0xE1A03007,
        0x803DD350: 0xE5862104,  # config+260 = chunk1
        0x803DD358: 0xE5861108,  # config+264 = chunk2
        0x803DD35C: 0xE5922024,  # chunk1 linear+36
        0x803DD360: 0xE586210C,  # config+268 = shared ARM base
        0x803DD364: 0xE5911024,
        0x803DD368: 0xE5861110,
        0x803DD62C: 0x00001044,
        0x803DD5F8: 0x15901000,  # cleanup virtual destructors for chunks
        0x803DD600: 0x15912008,
        0x803DD608: 0x112FFF32,
        0x803DD610: 0x15940000,
        0x803DD618: 0x15902008,
        0x803DD620: 0x112FFF32,
    }
    for address, instruction in cfg_checks.items():
        if cfg.word(address + cfg_delta) != instruction:
            raise ValueError(f"bridgecfg backing path changed at {address+cfg_delta:08X}")
    calls = []
    for address, ordinal in ((0x803DD290, 236), (0x803DD2F0, 60), (0x803DD340, 60)):
        address += cfg_delta
        stub = arm_bl_target(address, cfg.word(address))
        if raw_word(stub) != 0xE51FF004 or raw_word(stub+4) != exports(kernel)[ordinal-1]:
            raise ValueError("bridgecfg kernel import changed")
        calls.append({"address": f"{address:08X}", "ordinal": ordinal})
    early = {0x803E02D4: 0xE5840018, 0x803E0568: 0xE5940018,
             0x803E056C: 0xE5900000, 0x803E0570: 0xE080900B,
             0x803E05A8: 0xE5940018, 0x803E05AC: 0xE5907000,
             0x803E0654: 0xE5940028, 0x803E065C: 0xE1A0200C}
    late = {0x803EEFCC: 0xE28000A4, 0x803F0298: 0xE595110C,
            0x803F029C: 0xE58410AC}
    factory = {0x803DDA10: 0xE5940044, 0x803DDA18: 0xE5902104,
               0x803DDA1C: 0xE5903108, 0x803DDA20: 0xE1A00007}
    for delta, checks in ((early_delta, early), (late_delta, late), (cfg_delta, factory)):
        for address, instruction in checks.items():
            if pdd.word(address+delta) != instruction:
                raise ValueError(f"PDD backing chain changed at {address+delta:08X}")
    if arm_bl_target(0x803E02D0+early_delta, pdd.word(0x803E02D0+early_delta)) != 0x803EEFCC+late_delta:
        raise ValueError("context does not retain the embedded board reader")
    if arm_bl_target(0x803E0660+early_delta, pdd.word(0x803E0660+early_delta)) != 0x803E3098+late_delta:
        raise ValueError("context does not register CMM region")
    address = 0x803DDA24 + cfg_delta
    stub = arm_bl_target(address, pdd.word(address))
    if pdd.word(stub) != 0xE51FF004 or pdd.word(stub+4) != 0x803DD5F0 + cfg_delta:
        raise ValueError("factory does not call bridgecfg hardware chunk cleanup")
    return {"module_sha256": {name: hashlib.sha256(module.data).hexdigest().upper()
                              for name,module in (("bridgecfg",cfg),("pdd",pdd),("kernel",kernel))},
            "saved_rom_sha256": hashlib.sha256(raw).hexdigest().upper(),
            "checked_instructions": len(cfg_checks)+len(early)+len(late)+len(factory), "kernel_calls": calls,
            "backing_chain": "ASIC selector2 physical/bytes -> DPlatChunkHw::New attrs1044 -> config+260 chunk / +268 linear -> board+172 reader[0] -> context+24 -> CMM region registration",
            "attributes_raw": "00001044", "attributes_public_reference": REFERENCE,
            "attributes_interpretation": "user read/write, no execute; buffered uncached L1, uncached L2 under the public TMappingAttributes contract",
            "lifetime": "config retains hardware chunk; PDD factory cleanup calls bridgecfg cleanup with both chunk pointers; native CMM alloc/free changes suballocation lists, not backing pages. Keep the processor channel, node and allocation until delete/free/unmap/unreserve succeed.",
            "limits": ["public attribute decoding is corroboration, not a runtime page-table dump",
                       "ASIC selector implementation and boot reservation are not decoded here; no claim of explicit pin/unpin calls",
                       "current D1 page identity and successful mapping bracket the retained allocation; global DSP reset/reload is prohibited"]}


def build_report():
    return {"scope": "saved firmware, no device I/O",
            "n95": audit(Path(ROM), SHARED / "eka2l1/data/roms/rm-320/SYM.ROM", -0x244650, -0x244640, -0x244640),
            "e90": audit(ROOT / "work/evidence/e90/rom", ROOT / "work/evidence/e90/romdump-before-restore.bin", 0, 0, 0)}


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
