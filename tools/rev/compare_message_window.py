"""Compare the DSP-to-ARM window consumer in the two recovered ROMs.

Only static module bytes are read. Output contains hashes and contracts,
not ROM contents. Runtime routing, endianness and IRQ delivery remain open.
"""
import argparse
import datetime
import json
from pathlib import Path

from compare_node_info import Module, arm_bl_target, compare, sha256
from paths import ROM


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n95-rom", type=Path, default=Path(ROM))
    parser.add_argument("--e90-rom", type=Path, required=True)
    args = parser.parse_args()
    n95 = Module(args.n95_rom / "ehwaomap.pdd")
    e90 = Module(args.e90_rom / "ehwaomap.pdd")

    # The E90 import area differs in size; derive this reader from its unique
    # instruction sequence, then confirm all four consumer calls target it.
    reader = n95.read(0x801B3028, 24)
    code = e90.read(e90.base, e90.size)
    offset = code.find(reader)
    if offset < 0 or code.find(reader, offset + 1) >= 0:
        raise ValueError("reader is absent or not unique in E90")
    ereader = e90.base + offset
    ranges = {
        "word_reader": compare(n95, e90, 0x801B3028, ereader, 24),
        "window_consumer": compare(n95, e90, 0x8019B0A8, 0x803DF6E8, 744),
        "mailbox_dfc": compare(n95, e90, 0x8019BA84, 0x803E00C4, 88),
        "configuration_copy": compare(n95, e90, 0x8019EE68, 0x803E34A8, 8),
        "window_pointer_setup": compare(n95, e90, 0x8019C214, 0x803E0854, 64),
        "reader_owner_setup": compare(n95, e90, 0x8019BC8C, 0x803E02CC, 12),
        "embedded_interface_getter": compare(n95, e90, 0x801AA98C, 0x803EEFCC, 8),
    }
    if not all(entry["bytes_equal"] for name, entry in ranges.items()
               if name != "window_consumer"):
        raise ValueError("expected common instruction range differs")
    differences = []
    for offset in range(0, 744, 4):
        first, second = 0x8019B0A8 + offset, 0x803DF6E8 + offset
        a, b = n95.word(first), e90.word(second)
        if a == b:
            continue
        if ((a ^ b) & 0xFF000000 or (a & 0x0F000000) != 0x0B000000):
            raise ValueError("consumer difference is not a matching ARM BL")
        # Preserve the condition check above; the shared decoder accepts AL.
        at = arm_bl_target(first, (a & 0x0FFFFFFF) | 0xE0000000)
        bt = arm_bl_target(second, (b & 0x0FFFFFFF) | 0xE0000000)
        if bt - at != ereader - 0x801B3028:
            raise ValueError("unexpected consumer instruction/call difference")
        differences.append({"offset": offset, "n95_target": "%08X" % at,
                            "e90_target": "%08X" % bt})
    if [entry["offset"] for entry in differences] != [96, 112, 128, 144, 220, 284, 476, 520, 616]:
        raise ValueError("unexpected set of relocated consumer calls")
    for offset in (96, 112, 128, 144):
        first, second = 0x8019B0A8 + offset, 0x803DF6E8 + offset
        if (arm_bl_target(first, n95.word(first)) != 0x801B3028 or
                arm_bl_target(second, e90.word(second)) != ereader):
            raise ValueError("consumer field read does not target this reader")
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static ROM comparison; no kernel calls or phone writes",
        "pdd_sha256": {"n95": sha256(n95.data), "e90": sha256(e90.data)},
        "ranges": ranges, "consumer_relocated_calls": differences,
        "record": {"arm_bytes": 16, "c55_words": 8,
                   "cmd_offset": 0, "arg1_offset": 4, "arg2_offset": 8,
                   "source_offset": 12},
        "consumer": {"window_context_offset": 224,
                     "record_array_context_offset": 240,
                     "queue_source_offset": 16,
                     "pending_receive_offset": 40,
                     "ack_command": "40000000"},
        "reader": {"condition": "reader object byte+64 nonzero -> ror16",
                   "owner": "context+24 = (context+48 object)+164 via 801AA98C",
                   "processor_exit_flag_is_separate": "processor+64 <- configuration+588; not this reader object",
                   "runtime_value": "not observed"},
        "open": ["actual message record and word order", "source routing",
                 "IRQ/DFC execution", "runtime shared-window mapping"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
