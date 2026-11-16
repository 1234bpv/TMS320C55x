"""Verify native ring and RMS environment ownership paths from saved ROM."""
import hashlib
import json
from pathlib import Path

from compare_node_info import Module, arm_bl_target
from extract_doff_section import Doff
from paths import ROM, SHARED

ROOT = Path(__file__).resolve().parents[2]


def audit(directory, base_path, delta):
    pdd = Module(directory / "ehwaomap.pdd")
    base = Doff(base_path)
    start, code = base.text("EXTERNAL_common_code")
    # RMS allocates the environment from the live BIOS heap, not a counter
    # reset by each client. This relies on MEM_valloc's normal allocator
    # contract and on preserving the loaded base; no global queue count.
    ranges = {"environment_allocation": (0x24B010, 0x34),
              "environment_return_in_reply": (0x24B225, 0x13)}
    if code[0x24B025-start:0x24B029-start] != bytes.fromhex("6c25c368"):
        raise ValueError("RMS create does not invoke native MEM_valloc")
    if base.symbols["_MEM_valloc"][0] != 0x25C368:
        raise ValueError("MEM_valloc export differs")
    if code[0x24B230-start:0x24B238-start] != bytes.fromhex("90b13d026c24e684"):
        raise ValueError("RMS reply no longer returns allocated environment")
    checks = {0x803E3894: 0xE5900020,  # manager's CMM pointer
              0x803E2EC0: 0xE595002C,  # region free list
              0x803E2F98: 0xE5950030,  # region allocated list
              0x803E2FA4: 0xE596000C,  # return allocation linear address
              0x803E2FA8: 0xE58A0000,
              0x803E6E34: 0xE584602C,  # returned env -> own node
              0x803E6E38: 0xE59400A4,  # own retained message queue
              0x803E6E3C: 0xE1A01006}
    for address, word in checks.items():
        if pdd.word(address + delta) != word:
            raise ValueError(f"native ownership ABI changed at {address + delta:08X}")
    setter = 0x803F3A98 if delta == 0 else 0x801AF45C
    if (pdd.word(setter) != 0xE5801010
            or arm_bl_target(0x803E6E40 + delta, pdd.word(0x803E6E40 + delta)) != setter):
        raise ValueError("created env is not bound to native queue source")
    return {"pdd_sha256": hashlib.sha256(pdd.data).hexdigest().upper(),
            "baseimage_sha256": hashlib.sha256(base.data).hexdigest().upper(),
            "checked_arm_instructions": len(checks),
            "dsp_ranges": {name: {"address": f"{address:06X}", "bytes": count,
                                  "sha256": hashlib.sha256(code[address-start:address-start+count]).hexdigest().upper()}
                           for name, (address, count) in ranges.items()},
            "env_allocator": "RMS create calls native MEM_valloc(0,18 C55 words,0,0) for task-node environment; AC1 reply carries its pointer",
            "native_queue_binding": "successful RMS create stores env in retained own node+44 and own queue source+16",
            "cmm_allocator": "native manager+32 CMM suballocates region; allocation moves from free list+44 to allocated list+48 and returns linear address",
            "limits": ["uniqueness relies on the native allocator contract and unchanged live base; this is not enumeration of all global queues",
                       "region backing chunk mapping attributes and lifetime are not established by this audit",
                       "runtime page identities before/after exchange are brackets, not continuous pin instrumentation"]}


def build_report():
    n = audit(Path(ROM), SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof", -0x244640)
    e = audit(ROOT / "work/evidence/e90/rom", ROOT / "work/evidence/e90/baseimage.dof", 0)
    if n["dsp_ranges"] != e["dsp_ranges"]:
        raise ValueError("RMS environment paths differ between devices")
    return {"scope": "saved firmware only; no device I/O", "n95": n, "e90": e}


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
