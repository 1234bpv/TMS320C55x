"""Check the native CREATED-state stream submission contract on both ROMs.

Only addresses, hashes and decoded contract facts are published. Native code
and vendor base images remain local. This does not prove a hardware transfer.
"""
import argparse
import datetime
import json
from pathlib import Path

from compare_node_info import Module, compare
from extract_doff_section import Doff, sha256
from paths import ROM, SHARED


def equal(first, second, a, b, size):
    result = compare(first, second, a, b, size)
    if not result["bytes_equal"]:
        raise ValueError("native stream range differs at %08X" % a)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n95-rom", type=Path, default=Path(ROM))
    p.add_argument("--e90-rom", type=Path, required=True)
    p.add_argument("--n95-base", type=Path,
                   default=SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
    p.add_argument("--e90-base", type=Path, required=True)
    a = p.parse_args()
    nl, el = Module(a.n95_rom / "ehwa.ldd"), Module(a.e90_rom / "ehwa.ldd")
    np, ep = Module(a.n95_rom / "ehwaomap.pdd"), Module(a.e90_rom / "ehwaomap.pdd")
    ldd = {
        "copy_28_bytes_then_submit_without_node_state_check": equal(
            nl, el, 0x801B4988, 0x803F8FC8, 132),
        "direction_selects_pdd_slot52_or60": equal(
            nl, el, 0x801B4478, 0x803F8AB8, 60),
        "state_record_overrides_pdd_with_ldd_node_offset20": equal(
            nl, el, 0x801B43EC, 0x803F8A2C, 44),
    }
    pdd = {
        "input_node_state_gate": equal(np, ep, 0x801A1AA4, 0x803E60E4, 56),
        "output_node_state_gate": equal(np, ep, 0x801A18A0, 0x803E5EE0, 56),
    }
    excluded = [9, 13, 4, 10, 11, 0]
    for module, first in ((np, 0x801A1AAC), (ep, 0x803E60EC),
                          (np, 0x801A18A8), (ep, 0x803E5EE8)):
        expected = [0xE3500000 | excluded[0]] + [0x13500000 | x for x in excluded[1:]]
        if [module.word(first + 4 * i) for i in range(6)] != expected:
            raise ValueError("unexpected native excluded-state comparisons")
    for module, table, output, input_ in ((np, 0x801B3DE8, 0x801A1890, 0x801A1A90),
                                          (ep, 0x803F8424, 0x803E5ED0, 0x803E60D0)):
        if module.word(table + 52) != output or module.word(table + 60) != input_:
            raise ValueError("unexpected stream virtual slots")
    nb, eb = Doff(a.n95_base), Doff(a.e90_base)
    ns, nc = nb.text("EXTERNAL_common_code")
    es, ec = eb.text("EXTERNAL_common_code")
    start, end = 0x24D020, 0x24D160
    code, other = nc[start-ns:end-ns], ec[start-es:end-es]
    if code != other or len(code) != end - start:
        raise ValueError("native NODE_wait differs")
    # Native null-env branches skip the message queue and write messagesReady=0.
    for address, expected in ((0x24D091, "040020"), (0x24D143, "6600"),
                               (0x24D154, "e66100")):
        value = bytes.fromhex(expected)
        if nc[address-ns:address-ns+len(value)] != value:
            raise ValueError("NODE_wait null-env handling differs")
    print(json.dumps({
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static native contract; physical STRM transfer still required",
        "rom_sha256": {"n95_ldd": sha256(nl.data), "e90_ldd": sha256(el.data),
                       "n95_pdd": sha256(np.data), "e90_pdd": sha256(ep.data),
                       "n95_base": sha256(nb.data), "e90_base": sha256(eb.data)},
        "ldd": ldd, "pdd": pdd,
        "node_state_offset": 40, "created_state": 1, "excluded_states": excluded,
        "reported_state": {"source": "LDD node+20 overrides PDD record",
                           "created": 1, "deleted": 5,
                           "deleted_value_evidence": "n95 worker-one v16 first packet journal"},
        "transfer": {"bytes": 28, "status_offset": 12, "length_offset": 16,
                     "argument_offset": 20, "index_offset": 24,
                     "input_task": 14, "output_task": 16},
        "node_wait": {"start": "%06X" % start, "bytes": len(code),
                      "bytes_equal": True, "sha256": sha256(code),
                      "null_env": "stream-only wait; no RMS message queue accessed"},
        "limits": ["Native channel allocation, buffer mapping and completion remain runtime gates.",
                   "No DSP RUN, task creation or hardware packet is performed by this script."],
    }, indent=2))


if __name__ == "__main__":
    main()
