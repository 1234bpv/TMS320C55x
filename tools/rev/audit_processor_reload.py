"""Verify the stock PROC_Load stop/load/start path from saved firmware only."""
import hashlib
import json
from pathlib import Path

from compare_node_info import Module, arm_bl_target
from paths import ROM

ROOT = Path(__file__).resolve().parents[2]


def audit(module, dispatch_delta, processor_delta):
    def relocated(address):
        return address + (dispatch_delta if address < 0x8019F000 else processor_delta)
    # Native dispatch entry 3 is called by the base-image loader after the
    # image has been read into the shared chunk. No running-state shortcut.
    checks = {
        0x8019A1A4: 0xE5950038,
        0x8019A1C4: 0xE3500000,
        0x8019A1CC: 0x03A0A001,
        0x8019A1E4: 0x15901064,
        0x8019A1EC: 0x112FFF31,
        0x8019A268: 0xE5970000,
        0x8019A26C: 0xE5901060,
        0x8019A274: 0xE12FFF31,
        # Stop method: board vtable slot68, then processor state1 on success.
        0x8019F1E0: 0xE590002C,
        0x8019F1E8: 0xE5911044,
        0x8019F1EC: 0xE12FFF31,
        0x8019F1F4: 0xA3A01001,
        0x8019F1FC: 0xA5841008,
        # Start method requires state3, invokes board slot64, records state4.
        0x8019F190: 0xE5900008,
        0x8019F194: 0xE3500003,
        0x8019F1BC: 0xE5912040,
        0x8019F1C4: 0xE12FFF32,
        0x8019F1CC: 0xA3A01004,
        0x8019F1D0: 0xA5841008,
        0x8019F20C: 0xE5900008,
    }
    for address, expected in checks.items():
        if module.word(relocated(address)) != expected:
            raise ValueError(f"processor ABI changed at {relocated(address):08X}")
    for address, target in ((0x8019A1C0, 0x8019F20C),
                            (0x8019A1D0, 0x8019F1D8),
                            (0x8019A20C, 0x8019F0FC)):
        actual = arm_bl_target(relocated(address), module.word(relocated(address)))
        if actual != relocated(target):
            raise ValueError("processor call graph differs")
    return {
        "module_sha256": hashlib.sha256(module.data).hexdigest().upper(),
        "checked_instructions": len(checks),
        "checked_calls": 3,
        "base_load_dispatch": f"{relocated(0x8019A1A4):08X}",
        "unconditional_stop_call": f"{relocated(0x8019A1D0):08X}",
        "processor_state_offset": 8,
        "running_state": 4,
        "stop_board_slot": 68,
        "start_board_slot": 64,
        "stop_state": 1,
    }


def build_report():
    return {
        "scope": "saved firmware only; no phone access",
        "n95": audit(Module(Path(ROM) / "ehwaomap.pdd"), 0, 0),
        "e90": audit(Module(ROOT / "work/evidence/e90/rom/ehwaomap.pdd"), 0x244650, 0x244640),
        "conclusion": "PROC_Load stops and reloads an already running processor; host35 must attach without calling ordinal26",
        "limit": "This call graph alone does not establish which runtime audio queue owns an active DSP task, or prove clean D0.",
    }
def main():
    print(json.dumps(build_report(), indent=2))


if __name__ == "__main__":
    main()
