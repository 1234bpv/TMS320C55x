"""Verify DMM page-list and cache helper ABI from saved N95/E90 firmware.

No device I/O. The archived public kernel export reference supplies names;
the actual firmware export tables and call instructions establish ordinals.
"""
import hashlib
import json
from pathlib import Path
import re
import struct

from compare_node_info import Module, arm_bl_target
from paths import ROM

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = "https://raw.githubusercontent.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/master/kernel/eka/eabi/ekernu.def"


def exports(module):
    count, address = struct.unpack_from("<II", module.data, 60)
    return struct.unpack(f"<{count}I", module.read(address, count * 4))


def audit_physical_pools(directory, delta):
    pdd = Module(directory / "ehwaomap.pdd")
    kernel = Module(directory / "ekern.exe")
    table = exports(kernel)
    checks = {
        0x801AAF88: 0xE58400F4,  # owner+244 retains its pool record
        0x801AAFD4: 0xE5970000,
        0x801AAFD8: 0xE5810008,  # pool record first physical allocation size
        0x801AAFDC: 0xE5972004,
        0x801AAFE0: 0xE59410F4,
        0x801AAFF8: 0xE4901008,  # first allocation physical address
        0x801AAFFC: 0xE5902000,  # first allocation bytes
        0x801AB004: 0xE1A0300A,
        0x801AB01C: 0xE5810020,  # first hardware chunk pointer
        0x801AB028: 0xE5810004,  # first hardware chunk linear address
        0x801AB050: 0xE5970008,
        0x801AB054: 0xE5810018,
        0x801AB05C: 0xE1A00500,  # second pool bytes = config value << 10
        0x801AB060: 0xE5810014,
        0x801AB06C: 0xE281100C,
        0x801AB08C: 0xE5B0100C,
        0x801AB090: 0xE5902008,
        0x801AB0AC: 0xE5810024,
        0x801AB0B8: 0xE5810010,
        0x801AB174: 0xE5910000,
        0x801AB180: 0xE5911008,
        0x801AB1C0: 0xE591000C,
        0x801AB1CC: 0xE5911014,
    }
    for address, value in checks.items():
        if pdd.word(address + delta) != value:
            raise ValueError("physical pool record ABI changed")
    calls = []
    for address, ordinal in ((0x801AAFE4, 242), (0x801AB008, 60),
                             (0x801AB070, 242), (0x801AB098, 60),
                             (0x801AB184, 241), (0x801AB1D0, 241)):
        address += delta
        stub = arm_bl_target(address, pdd.word(address))
        if pdd.word(stub) != 0xE51FF004 or pdd.word(stub + 4) != table[ordinal - 1]:
            raise ValueError("physical pool kernel import does not match")
        calls.append({"address": f"{address:08X}", "kernel_ordinal": ordinal})
    if pdd.word(0x801AB4D0 + delta) != 0x1044:
        raise ValueError("hardware chunk mapping attributes changed")
    return {"pdd_sha256": hashlib.sha256(pdd.data).hexdigest().upper(),
            "checked_instructions": len(checks), "calls": calls,
            "owner_record_offset": 244, "hardware_chunk_attributes_raw": "00001044",
            "record_offsets": {"physical1": 0, "linear1": 4, "bytes1": 8,
                               "physical2": 12, "linear2": 16, "bytes2": 20,
                               "hardware_chunk1": 32, "hardware_chunk2": 36},
            "limit": "these owner-scoped physical pools are not yet linked to the candidate ARM native buffer; this is not ring pinning/lifetime proof"}


def audit_mapping_flags(directory, delta):
    pdd = Module(directory / "ehwaomap.pdd")
    checks = {0x801AACA4: 0xE31B0001, 0x801AACA8: 0x0A00002E,
              0x801AAC4C: 0xE791418C, 0x801AAC50: 0xE1540003,
              0x801AAC60: 0xE5900004, 0x801AACC4: 0xE1A0300A,
              0x801AAD00: 0xE0853004, 0x801AAD10: 0xE59D1008,
              0x801AAD14: 0xE0890004, 0x801AAD44: 0xE1A01009,
              0x801AAD78: 0xE1A0100A}
    for address, word in checks.items():
        if pdd.word(address + delta) != word:
            raise ValueError("native page-list flag dispatch changed")
    for address in (0x801AACD0, 0x801AAD04):
        if arm_bl_target(address + delta, pdd.word(address + delta)) != 0x801AAC34 + delta:
            raise ValueError("page-list physical lookup call changed")
    return {"checked_instructions": len(checks), "checked_lookup_calls": 2,
            "bit0_set": "use copied page list: match ARM linearPage, load physicalPage at +4",
            "bit0_clear": "pass supplied ARM address directly to MMU as physical address; page list ignored",
            "virtual_arm_buffer_flags": 17,
            "limit": "Nokia native bit0 behavior differs from the archived TI userspace flag names; do not transplant their semantics."}


def audit(directory, util_base, map_entry):
    util = Module(directory / "ebridgeutil.ldd")
    kernel = Module(directory / "ekern.exe")
    bridge = Module(directory / "bridgeapi.dll")
    if util.base != util_base:
        raise ValueError("unexpected utility code base")
    checks = {
        0x21C: 0xE92D43FE,
        0x220: 0xE3510001,
        0x234: 0xE3510002,
        0x238: 0x1A000005,
        0x23C: 0xE5971000,  # fn2 length is dereferenced from a2
        0x240: 0xE5950000,  # fn2 address is dereferenced from a1
        0x248: 0xE5971000,
        0x24C: 0xE5950000,
        0x254: 0xE1A00008,
        0x25C: 0xE3A04000,
        0x260: 0xE3A02008,  # fn1 input = two 32-bit words
        0x270: 0xE59D0004,
        0x274: 0xE59D1008,
        0x278: 0xE1A05620,
        0x27C: 0xE1A05605,
        0x2A8: 0xE7815184,  # record[2*i] = linear page base
        0x2B0: 0xE2855A01,  # advance 4096 bytes
        0x2B8: 0xE5810004,  # record[2*i+1] = physical page base
        0x2C0: 0xE2466A01,
    }
    for offset, word in checks.items():
        if util.word(util_base + offset) != word:
            raise ValueError(f"utility ABI differs at {util_base + offset:08X}")
    kernel_exports = exports(kernel)
    calls = {}
    for label, call_offset, stub_offset, ordinal in (
        ("cache_first", 0x244, 0x3A0, 378),
        ("cache_second", 0x250, 0x398, 376),
        ("page_translate", 0x2A0, 0x368, 245),
        ("page_input_copy", 0x26C, 0x420, 719),
        ("page_output_pointer_copy", 0x294, 0x420, 719),
    ):
        call, stub = util_base + call_offset, util_base + stub_offset
        if arm_bl_target(call, util.word(call)) != stub or util.word(stub) != 0xE51FF004:
            raise ValueError("unexpected utility import call")
        target = util.word(stub + 4)
        if target != kernel_exports[ordinal - 1]:
            raise ValueError("utility call does not match the expected kernel ordinal")
        calls[label] = {"ordinal": ordinal, "target": f"{target:08X}"}
    instructions = struct.unpack("<45I", util.read(util_base + 0x21C, 180))
    if sum(word >> 24 == 0xEB for word in instructions) != len(calls):
        raise ValueError("unclassified utility call")
    # The mapping wrapper builds six payload words and allocates 8 bytes/page.
    thumb_checks = {0: 0xB5FF, 2: 0xB08F, 4: 0x2218,
                    0x26: 0x0B30, 0x28: 0x0300, 0x2E: 0x0B07, 0x30: 0x00F8,
                    0x86: 0x9608, 0x8C: 0x900A, 0x8E: 0x9109,
                    0x94: 0xC191, 0x9A: 0x9B18, 0x9E: 0x1D89}
    for offset, word in thumb_checks.items():
        if struct.unpack("<H", bridge.read(map_entry + offset, 2))[0] != word:
            raise ValueError("map wrapper ABI differs")
    return {"module_sha256": {name: hashlib.sha256(module.data).hexdigest().upper()
                              for name, module in (("utility", util), ("kernel", kernel), ("bridge", bridge))},
            "checked_util_instructions": len(checks), "checked_map_halfwords": len(thumb_checks),
            "calls": calls, "utility_dispatch_sha256": hashlib.sha256(util.read(util_base + 0x21C, 180)).hexdigest().upper(),
            "map_wrapper_sha256": hashlib.sha256(bridge.read(map_entry, 182)).hexdigest().upper()}


def main():
    reference = ROOT / "out/symbian-ekern-exports-reference.def"
    names = {int(ordinal): name for name, ordinal in re.findall(
        r"^\s*(\S+)\s+@\s+(\d+)\s+NONAME", reference.read_text(encoding="ascii"), re.M)}
    required = {245: "_ZN4Epoc16LinearToPhysicalEm",
                376: "_ZN5Cache23SyncMemoryBeforeDmaReadEmj",
                378: "_ZN5Cache24SyncMemoryBeforeDmaWriteEmj", 719: "kumemget32",
                60: "_ZN12DPlatChunkHw3NewERPS_mij",
                241: "_ZN4Epoc15FreePhysicalRamEmi", 242: "_ZN4Epoc16AllocPhysicalRamEiRmi"}
    if any(names.get(ordinal) != name for ordinal, name in required.items()):
        raise ValueError("public kernel export names changed")
    n95 = audit(Path(ROM), 0x801B5888, 0x80A5D9EC)
    e90 = audit(ROOT / "work/evidence/e90/rom", 0x803FEF88, 0x803FA45C)
    if any(n95[key] != e90[key] for key in ("utility_dispatch_sha256", "map_wrapper_sha256")):
        raise ValueError("firmware helper implementations differ")
    print(json.dumps({
        "scope": "offline saved firmware ABI audit; candidate54 hardware results are separately recorded in d1-ring-results.json",
        "reference": {"url": REFERENCE, "sha256": hashlib.sha256(reference.read_bytes()).hexdigest().upper(),
                      "matched_ordinals": required},
        "n95": n95, "e90": e90,
        "physical_pools": {"n95": audit_physical_pools(Path(ROM), 0),
                           "e90": audit_physical_pools(ROOT / "work/evidence/e90/rom", 0x244640)},
        "mapping_flags": {"n95": audit_mapping_flags(Path(ROM), 0),
                          "e90": audit_mapping_flags(ROOT / "work/evidence/e90/rom", 0x244640)},
        "page_list_record": ["32-bit ARM linear page base", "32-bit physical page base"],
        "page_bytes": 4096, "page_record_bytes": 8,
        "map_signature": "TInt map(processor*, armAddress, byteCount, reservedDspAddress, mappedDspAddressOut*, flags)",
        "cache_control": "BridgeUtil DoControl(2, &linearAddress, &byteCount)",
        "cache_order": ["SyncMemoryBeforeDmaWrite: clean", "SyncMemoryBeforeDmaRead: invalidate/prepare"],
        "ownership_inference": "helper cleans before invalidating; ARM dirty data in a DSP-owned line must be prevented, including adjacent control fields",
        "pinning": "fn1 translates pages but contains no pin/unpin call; another lifetime mechanism must be established",
        "unverified_by_this_static_audit": ["native allocation chunk attributes and immutable page lifetime",
                       "DSP cache and publish ordering", "runtime correctness and timing; see separate hardware evidence"],
    }, indent=2))


if __name__ == "__main__":
    main()
