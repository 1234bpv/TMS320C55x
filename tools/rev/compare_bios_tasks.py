"""Check native C55 DSP/BIOS task contracts in N95/E90 executable DOFFs.

Output is hashes, ABI offsets and symbolic relocation checks. No ROM bytes
are published and no phone is called. Dynamic module lifetime is not proved.
"""
import argparse
import datetime
import json
from pathlib import Path

from extract_doff_section import Doff, sha256
from paths import SHARED


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n95-base", type=Path,
                   default=SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
    p.add_argument("--e90-base", type=Path, required=True)
    a = p.parse_args()
    n95, e90 = Doff(a.n95_base), Doff(a.e90_base)
    base, ncode = n95.text(".bios")
    ebase, ecode = e90.text(".bios")
    if base != 0x25A20C or ebase != base:
        raise ValueError("unexpected BIOS code address")
    ranges = {
        "TSK_create": (0x25A5B4, 0x25A818),
        "TSK_delete": (0x25B6FC, 0x25B7E0),
        "TSK_stat": (0x25B7E0, 0x25B8BE),
        "TSK_exit": (0x25B4F4, 0x25B5FA),
        "task_startup": (0x25CF30, 0x25CF6F),
        "stack_argument_setup": (0x25D373, 0x25D3D0),
    }
    # Each different immediate must address the same exported data symbol.
    # Do not normalize opcodes, branches or task-object field offsets.
    data_refs = {
        0x25A780: (b"\xa5\x31", "__HOOK_NUMHOOKS"),
        0x25A7D7: (b"\xa4\x31", "__HOOK_knlId"),
        0x25B6FE: (b"\xa9\x31", "TRC_R_mask"),
        0x25B70F: (b"\xed\x31\x8f", "_LOG_D_system"),
        0x25B795: (b"\xa5\x31", "__HOOK_NUMHOOKS"),
        0x25B5BF: (b"\xa9\x31", "TRC_R_mask"),
        0x25B5D6: (b"\xed\x31\x8f", "_LOG_D_system"),
    }
    normalized = bytearray(ecode)
    references = []
    for address, (opcode, symbol) in data_refs.items():
        offset = address - base
        for module, code in ((n95, ncode), (e90, ecode)):
            if code[offset:offset + len(opcode)] != opcode:
                raise ValueError("unexpected data-reference instruction")
            value = int.from_bytes(code[offset + len(opcode):offset + len(opcode) + 3], "big")
            if value * 2 != module.symbols[symbol][0]:
                raise ValueError("instruction no longer addresses " + symbol)
        start = offset + len(opcode)
        normalized[start:start + 3] = ncode[start:start + 3]
        references.append({"instruction": "%06X" % address, "symbol": symbol,
                           "n95_word_address": "%06X" % (n95.symbols[symbol][0] // 2),
                           "e90_word_address": "%06X" % (e90.symbols[symbol][0] // 2)})
    compared = {}
    for name, (start, end) in ranges.items():
        first, second = ncode[start - base:end - base], ecode[start - base:end - base]
        if first != normalized[start - base:end - base]:
            raise ValueError("native task contract differs beyond symbolic data addresses: " + name)
        compared[name] = {"start": "%06X" % start, "end_exclusive": "%06X" % end,
                          "bytes": end - start, "bytes_equal": first == second,
                          "equal_except_verified_data_addresses": True,
                          "n95_sha256": sha256(first), "e90_sha256": sha256(second)}
    symbols = {}
    for name in ("_TSK_create", "_TSK_delete", "_TSK_stat", "_TSK_ATTRS", "_KNL_curtask"):
        if n95.symbols[name] != e90.symbols[name]:
            raise ValueError("task export differs: " + name)
        symbols[name] = "%06X" % n95.symbols[name][0]
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static task ABI only; no own worker hardware or resident-code lifetime proof",
        "primary_reference": "https://www.ti.com/lit/ug/spru404q/spru404q.pdf",
        "base_sha256": {"n95": sha256(n95.data), "e90": sha256(e90.data)},
        "ranges": compared, "verified_data_references": references,
        "symbols_byte_addresses": symbols,
        "abi": {"attrs_c55_words": 14, "stat_c55_words": 22,
                "attr_offsets": {"priority": 0, "stack": 2, "stacksize": 4,
                                 "sysstacksize": 5, "stackseg": 6, "environ": 8,
                                 "name": 10, "exitflag": 12, "initstackflag": 13},
                "stat_offsets": {"mode": 14, "sp": 16, "ssp": 18,
                                 "used": 20, "sysused": 21},
                "arg": "eight 32-bit pointer arguments; first five loaded into XAR0..4",
                "large_data_pointer_bits": 23, "task_entry_register": "AC0",
                "terminated_mode": 3, "native_exit_after_entry_return": "25CF69..25CF6B -> TSK_exit"},
        "probe_scope": "finite callback owns no resources; join/delete before create returns",
        "open": ["persistent worker code/data lifetime across node loader phases",
                 "STRM use in a created node", "hardware task creation/termination/cleanup"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
