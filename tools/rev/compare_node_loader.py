"""Verify native node-library lifetime, RMS result and SEM contracts.

Only hashes, firmware addresses and ABI facts are emitted. ROM instructions
remain local. These static checks do not replace created-worker device tests.
"""
import argparse
import datetime
import json
from pathlib import Path

from compare_node_info import Module, compare
from extract_doff_section import Doff, sha256
from paths import ROM, SHARED


def require_equal(first, second, a, b, size):
    result = compare(first, second, a, b, size)
    if not result["bytes_equal"]:
        raise ValueError("native range differs at %08X" % a)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n95-rom", type=Path, default=Path(ROM))
    p.add_argument("--e90-rom", type=Path, required=True)
    p.add_argument("--n95-base", type=Path,
                   default=SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
    p.add_argument("--e90-base", type=Path, required=True)
    a = p.parse_args()
    nb = Module(a.n95_rom / "bridgeapi.dll")
    eb = Module(a.e90_rom / "bridgeapi.dll")
    np = Module(a.n95_rom / "ehwaomap.pdd")
    ep = Module(a.e90_rom / "ehwaomap.pdd")
    nbase, ebase = Doff(a.n95_base), Doff(a.e90_base)
    bridge = {
        "missing_create_library_fallback_3_to_2": require_equal(nb, eb, 0x80A5E188, 0x803FABF8, 42),
        "generic_library_skips_execute_delete_lists": require_equal(nb, eb, 0x80A5E742, 0x803FB1B2, 32),
    }
    # Obtain each vtable from its own constructor literal. The code delta
    # does not also apply to vtable storage addresses.
    nv, ev = np.word(0x8019FDEC), ep.word(0x803E442C)
    if (nv, ev) != (0x801B3DE8, 0x803F8424):
        raise ValueError("unexpected node vtable literals")
    slots = {"allocate": (8, 0x801A0264, 0x803E48A4),
             "create": (12, 0x801A1038, 0x803E5678),
             "run": (32, 0x801A1404, 0x803E5A44),
             "free": (88, 0x801A2118, 0x803E6758),
             "delete": (92, 0x801A25C4, 0x803E6C04)}
    for offset, naddr, eaddr in slots.values():
        if np.word(nv + offset) != naddr or ep.word(ev + offset) != eaddr:
            raise ValueError("node vtable function differs")
    ranges = {
        "phase_split_from_library_lists": (0x801A07C8, 0x803E4E08, 48),
        "run_unloads_create_only_if_split_dynamic": (0x801A1474, 0x803E5AB4, 44),
        "created_delete_retains_create_and_loads_delete_if_split": (0x801A263C, 0x803E6C7C, 132),
        "free_unloads_loaded_phase_libraries": (0x801A2118, 0x803E6758, 176),
        "completion_negative_rms_status_maps_to_minus2": (0x801A27A4, 0x803E6DE4, 12),
        "create_success_checks_status_and_environment": (0x801A27E4, 0x803E6E24, 16),
        "create_success_sets_created_state1": (0x801A283C, 0x803E6E7C, 16),
    }
    pdd = {name: require_equal(np, ep, *params) for name, params in ranges.items()}
    common = {}
    nstart, nc = nbase.text("EXTERNAL_common_code")
    estart, ec = ebase.text("EXTERNAL_common_code")
    for name, first, end in (("node_create_return_ac0_to_reply", 0x24B225, 0x24B238),
                             ("reply_copies_status_to_first_long", 0x24E684, 0x24E6D9)):
        x, y = nc[first - nstart:end - nstart], ec[first - estart:end - estart]
        if len(x) != end - first or x != y:
            raise ValueError("RMS result relay differs")
        common[name] = {"start": "%06X" % first, "end_exclusive": "%06X" % end,
                        "bytes": len(x), "bytes_equal": True, "sha256": sha256(x)}
    expected_relay = bytes.fromhex("9200eb1c08ed30bfed1c0890b13d026c24e684")
    if nc[0x24B225 - nstart:0x24B238 - nstart] != expected_relay:
        raise ValueError("create no longer relays the node's AC0 return")

    ns, ncode = nbase.text(".bios")
    es, ecode = ebase.text(".bios")
    if ns != 0x25A20C or es != ns:
        raise ValueError("unexpected native BIOS code base")
    normalized = bytearray(ecode)
    data_refs = {
        0x25D496: (b"\xa5\x31", "_SWI_D_lock"),
        0x25D4A0: (b"\xa5\x31", "_SWI_D_curmask"),
        0x25D4AB: (b"\xe6\x31\x02", "_SWI_D_curmask"),
        0x25D1B7: (b"\xa4\x31", "TRC_R_mask"),
        0x25D1C7: (b"\xa4\x31", "_SWI_D_lock"),
        0x25D1D3: (b"\xaa\x31", "_SWI_D_curmask"),
        0x25D208: (b"\xe6\x31\x02", "_SWI_D_curmask"),
    }
    references = []
    for address, (opcode, symbol) in data_refs.items():
        offset = address - ns
        for module, code in ((nbase, ncode), (ebase, ecode)):
            if code[offset:offset + len(opcode)] != opcode:
                raise ValueError("SEM data-reference opcode changed")
            value = int.from_bytes(code[offset + len(opcode):offset + len(opcode) + 3], "big")
            if value * 2 != module.symbols[symbol][0]:
                raise ValueError("SEM instruction no longer addresses " + symbol)
        start = offset + len(opcode)
        normalized[start:start + 3] = ncode[start:start + 3]
        references.append({"instruction": "%06X" % address, "symbol": symbol,
                           "n95_word_address": "%06X" % (nbase.symbols[symbol][0] // 2),
                           "e90_word_address": "%06X" % (ebase.symbols[symbol][0] // 2)})
    sem = {}
    for name, start, end in (("SEM_create", 0x25BF18, 0x25BF7C),
                             ("SEM_delete", 0x25C4AC, 0x25C4BC),
                             ("SEM_pend", 0x25D473, 0x25D4C1),
                             ("SEM_post", 0x25D1B7, 0x25D216),
                             ("pend_sets_blocked_mode2", 0x25AC1C, 0x25AC21)):
        x, y = ncode[start - ns:end - ns], ecode[start - es:end - es]
        if x != normalized[start - es:end - es]:
            raise ValueError("SEM contract differs beyond verified data symbols: " + name)
        sem[name] = {"start": "%06X" % start, "bytes": len(x), "bytes_equal": x == y,
                     "equal_except_verified_data_addresses": True,
                     "n95_sha256": sha256(x), "e90_sha256": sha256(y)}
    symbols = {}
    for name in ("_SEM_create", "_SEM_delete", "_SEM_pend", "_SEM_post", "_SEM_ATTRS"):
        if nbase.symbols[name] != ebase.symbols[name]:
            raise ValueError("SEM export differs: " + name)
        symbols[name] = "%06X" % nbase.symbols[name][0]
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static native loader/result/SEM contract; own worker residency needs device evidence",
        "module_sha256": {"n95_bridge": sha256(nb.data), "e90_bridge": sha256(eb.data),
                          "n95_pdd": sha256(np.data), "e90_pdd": sha256(ep.data),
                          "n95_base": sha256(nbase.data), "e90_base": sha256(ebase.data)},
        "bridge": bridge, "pdd": pdd, "rms": common, "sem": sem,
        "sem_data_references": references, "sem_symbols_byte_addresses": symbols,
        "vtable": {"n95": "%08X" % nv, "e90": "%08X" % ev,
                   "slots": {name: {"offset": offset, "n95": "%08X" % x, "e90": "%08X" % y}
                             for name, (offset, x, y) in slots.items()}},
        "node_offsets": {"state": 40, "load_type": 184, "phase_split": 208,
                         "library_heads": [196, 200, 204], "loaded_flags": [212, 216, 220]},
        "interpretation": [
            "Library type2 is selected if create type3 lookup returns -6; no separate phase lists.",
            "Dynamic create code remains loaded while node is CREATED, including with split phases.",
            "Created-state delete does not unload create; final node free unloads loaded libraries.",
            "Split phase loading can create a different data/code instance; static retention alone does not prove identity.",
            "Negative node create/delete RMS return becomes host -2; arbitrary positive returns can map to host success.",
            "SEM_create: count T0, optional attrs XAR0; SEM_pend: handle XAR0, timeout T0, result T0.",
            "SEM_pend timeout is in BIOS ticks, not automatically milliseconds; positive blocking sets task mode2.",
        ],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
