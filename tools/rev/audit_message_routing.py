"""Check the native first-match routing and callback phase ABI, offline."""
import hashlib
import json
from pathlib import Path
import struct

from compare_node_info import Module, arm_bl_target

ROOT = Path(__file__).resolve().parents[2]


def main():
    pdd = Module(ROOT / "work/evidence/e90/rom/ehwaomap.pdd")
    expected = {
        0x803DF7BC: 0xE5940020,  # context+32 owns incoming pool
        0x803DF7C0: 0xE5900008,  # pool+8 owns queue list
        0x803DF7CC: 0x1590500C,  # list item+12 is queue
        0x803DF7D8: 0xE59D1010,  # decoded record source
        0x803DF7DC: 0xE5952010,  # queue+16 source
        0x803DF7E0: 0xE1510002,
        0x803DF7E4: 0x1A000055,  # mismatch alone advances list
        0x803DF7EC: 0xE3500101,  # EXITACK 40000000
        0x803DF81C: 0xE5959024,  # matched queue+36 owns native node
        0x803DF850: 0xE3500902,  # RMS_EOK 8000
        0x803DF868: 0xEA000047,  # matched ACK skips remaining queues
        0x803E6DE4: 0xE5940068,  # callback switch reads node phase+104
        0x803E6E00: 0x908FF100,
        0x803E6E14: 0xEA00003E,  # phase3 case, not phase4
        0x803E6F24: 0xE3A00003,
        0x803E6F28: 0xE5840028,  # phase3 sets PDD state3
        0x803E6E20: 0xEA0000A4,  # phase6 delete completion
        0x803E7198: 0xE5848028,  # delete completion sets PDD state4
    }
    for address, word in expected.items():
        if pdd.word(address) != word:
            raise ValueError(f"native instruction changed at {address:08X}")
    if arm_bl_target(0x803DF864, pdd.word(0x803DF864)) != 0x803E6860:
        raise ValueError("EXITACK no longer dispatches native delete")
    # ARM add pc,pc,r0,lsl#2 at 6E00 starts its indexed table at 6E08.
    if 0x803E6E08 + 3 * 4 != 0x803E6E14:
        raise ValueError("phase table indexing")
    dump = (ROOT / "work/evidence/e90/romdump-before-restore.bin").read_bytes()
    helper = struct.pack("<6I", 0xE1A02000, 0xE5921000, 0xE3A00000,
                         0xE1510002, 0x11A00001, 0xE12FFF1E)
    if dump[0x3DCB78:0x3DCB90] != helper:
        raise ValueError("list First() sentinel contract changed")
    print(json.dumps({
        "scope": "saved E90 ROM only; no device access",
        "pdd_sha256": hashlib.sha256(pdd.data).hexdigest().upper(),
        "checked_pdd_instructions": len(expected),
        "list_first_sha256": hashlib.sha256(helper).hexdigest().upper(),
        "incoming_pool_context_offset": 32,
        "pool_queue_list_offset": 8,
        "list_sentinel": "head address; head[0] == head means empty",
        "list_item_queue_offset": 12,
        "queue_source_offset": 16,
        "queue_node_offset": 36,
        "consumer": "first matching source wins; EXITACK automatically calls native delete",
        "duplicate_source_risk": "an older matching queue can take a newer node's ACK",
        "phase3_sets_pdd_state3": True,
        "phase6_is_delete_completion": True,
        "limit": "PS0 does not establish that native queues are gone; runtime causality needs a clean-device test",
    }, indent=2))


if __name__ == "__main__":
    main()
