"""Check raw allocation and pending-message destruction in N95/E90 ROMs.

No phone calls. The output contains hashes and record offsets only.
"""
import argparse
import datetime
import json
from pathlib import Path

from compare_node_info import Module, compare, sha256
from paths import ROM


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n95-rom", type=Path, default=Path(ROM))
    parser.add_argument("--e90-rom", type=Path, required=True)
    args = parser.parse_args()
    n95 = Module(args.n95_rom / "ehwa.ldd")
    e90 = Module(args.e90_rom / "ehwa.ldd")
    ranges = {
        "ldd_node_destructor": (0x801B4150, 0x803F8790, 156),
        "cancel_saved_put_get": (0x801B418C, 0x803F87CC, 48),
        "control7_free_task": (0x801B4DE4, 0x803F9424, 132),
        "allocate_copy_arguments": (0x801B4EE8, 0x803F9528, 12),
        "allocate_payload_forwarding": (0x801B4F70, 0x803F95B0, 20),
    }
    compared = {name: compare(n95, e90, *addresses)
                for name, addresses in ranges.items()}
    if not all(item["bytes_equal"] for item in compared.values()):
        raise ValueError("documented cleanup/allocation instruction ranges differ")
    for module, address in ((n95, 0x801B4EE8), (e90, 0x803F9528)):
        if module.word(address) != 0xE3A03020:  # ARM mov r3, #32
            raise ValueError("control4 no longer copies 32 bytes")
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static ROM contract; no E90 receive test or DSP RUN",
        "ldd_sha256": {"n95": sha256(n95.data), "e90": sha256(e90.data)},
        "ranges": compared,
        "allocation_record": {
            "control": 4, "raw_bytes": 32, "header": "30000014", "maximum": 20,
            "reference_raw_offset": 16, "padding_raw_offset": 28,
            "sdk_TBuf8_20_bytes": 28,
            "sdk_size_evidence": "src/c55stream.cpp compile-time assertion in successful v10 build",
            "padding_use": "last copied word is not forwarded by this allocator",
            "failure_causality": "over-read fixed; message failure cause not established",
        },
        "pending_receive": {
            "task": 21, "ldd_saved_status_offset": 84,
            "destructor_completion": -3,
            "control7_precondition": "PDD node has completed deletion and entered state4",
            "hardware_scope": "N95 receive-created v9/v10: pending before delete, cancelled by free; no RUN",
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
