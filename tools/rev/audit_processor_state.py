"""Audit native LDD processor-state query from saved firmware, without I/O."""
import hashlib
import json
from pathlib import Path

from compare_node_info import Module, arm_bl_target
from audit_dmm_ownership import exports
from paths import ROM

ROOT = Path(__file__).resolve().parents[2]


def audit(directory, ldd_delta, pdd_delta, manager_delta):
    ldd = Module(directory / "ehwa.ldd")
    pdd = Module(directory / "ehwaomap.pdd")
    kernel = Module(directory / "ekern.exe")
    # LDD control2: own PDD object+12 -> local stack -> caller's four bytes.
    ldd_checks = {0x803F9908: 0xEA00000F, 0x803F994C: 0xE5940028,
                  0x803F9950: 0xE590000C, 0x803F9954: 0xEA000018,
                  0x803F99BC: 0xE3A03000, 0x803F99C0: 0xE58D3000,
                  0x803F99C4: 0xE58D0004, 0x803F99C8: 0xE5940064,
                  0x803F99CC: 0xE3A03004, 0x803F99D0: 0xE28D2004,
                  0x803F99D4: 0xE1A01005}
    pdd_checks = {0x803DE234: 0xE5940038, 0x803DE23C: 0xE3500004,
                  0x803DE240: 0x908FF100, 0x803DE248: 0xEA000003,
                  0x803DE24C: 0xEA000002, 0x803DE250: 0xEA000003,
                  0x803DE254: 0xEA000002, 0x803DE258: 0xEA000003,
                  0x803DE25C: 0xE3A00003, 0x803DE264: 0xE3A00002,
                  0x803DE26C: 0xE3A00001, 0x803DE270: 0xE584000C}
    for module, delta, checks in ((ldd, ldd_delta, ldd_checks), (pdd, pdd_delta, pdd_checks)):
        for address, word in checks.items():
            if module.word(address + delta) != word:
                raise ValueError(f"native query ABI changed at {address + delta:08X}")
    call = 0x803F99D8 + ldd_delta
    stub = arm_bl_target(call, ldd.word(call))
    if ldd.word(stub) != 0xE51FF004 or ldd.word(stub + 4) != exports(kernel)[297]:
        raise ValueError("query does not call kernel ordinal298 ThreadRawWrite")
    getter = arm_bl_target(0x803DE238 + pdd_delta, pdd.word(0x803DE238 + pdd_delta))
    if getter != 0x803E384C + manager_delta or pdd.read(getter, 8) != bytes.fromhex("080090e51eff2fe1"):
        raise ValueError("processor initializer does not read manager state")
    return {"module_sha256": {name: hashlib.sha256(m.data).hexdigest().upper()
                              for name, m in (("ldd", ldd), ("pdd", pdd), ("kernel", kernel))},
            "checked_instructions": len(ldd_checks) + len(pdd_checks) + 2,
            "ioctl": 2, "argument1": "pointer to caller-owned aligned Uint32",
            "argument2": "unused/null", "output_bytes": 4,
            "ldd_handler": f"{0x803F994C + ldd_delta:08X}",
            "copy_call": f"{call:08X}", "copy_kernel_ordinal": 298,
            "initializer": f"{0x803DE1F0 + pdd_delta:08X}",
            "manager_to_channel_state": {"0": 3, "1": 3, "2": 2, "3": 2, "4": 1},
            "limit": "channel state is cached native state, initialized at open; it is not a global queue enumeration or DSP fault diagnosis"}


def build_report():
    return {"scope": "saved firmware only; no device I/O",
            "n95": audit(Path(ROM), -0x244640, -0x244650, -0x244640),
            "e90": audit(ROOT / "work/evidence/e90/rom", 0, 0, 0),
            "rejected_hypothesis": "bridgeapi ordinal35 subcommand0 is processor control04000007, not a state getter; do not invoke it for observation",
            "native_query": "channel.Ctl(2, &state, NULL); accept state1 after open; never PROC_Load",
            "limit": "this replaces the running-base observation only; unique queue routing and native allocation lifetime are separate contracts"}


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
