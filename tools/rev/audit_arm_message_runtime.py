"""Prove E90 ARM message pointer provenance from saved ROM, without device I/O.

The BSS read in host29 proves the copy primitive. It is not a message-context
root. No guessed pointers, kernel heap scans, ROM code or device calls are
published here; only checked addresses, range hashes and field contracts.
"""
import argparse
import datetime
import json
import struct
from pathlib import Path

from compare_node_info import Module, arm_bl_target, sha256

ROOT = Path(__file__).resolve().parents[2]


def audit(rom):
    pdd = Module(rom / "ehwaomap.pdd")
    expected = {
        0x803DF228: 0xE5801030,  # context+48 = common board argument
        0x803F03BC: 0xE3A00F5B,  # allocate 364-byte context
        0x803F03C0: 0xE5C480EC,  # board+236 = byte1
        0x803F03D0: 0xE2841008,  # common board = board+8
        0x803F03DC: 0xE5840108,  # board+264 = returned context
        0x803E02CC: 0xE5940030,  # load context+48
        0x803E02D4: 0xE5840018,  # context+24 = reader
        0x803EEFCC: 0xE28000A4,  # reader = common board+164
        0x803E080C: 0xE5940018,  # reader pointer
        0x803E0814: 0xE5900000,  # first reader word = shared-memory base
        0x803E081C: 0xE2903010,  # shared base+16
        0x803E0854: 0xE283CFA6,  # shared base+16+664
        0x803E0858: 0xE58430DC,  # context+220 = shared base+16
        0x803E085C: 0xE0832002,  # fromDSP = shared base+16+layout offset
        0x803E086C: 0xE2823008,  # record = fromDSP+8
        0x803E0870: 0xE58420E0,  # context+224 = fromDSP header
        0x803E0878: 0xE58430F0,  # context+240 = records
        0x803DF6F8: 0xE59010E0,  # consumer header
        0x803DF71C: 0x059460F0,  # consumer record array
        0x803DF7DC: 0xE5952010,  # queue+16 source
        0x803DF86C: 0xE5952028,  # queue+40 pending receive
        0x803DF8B8: 0xE5850028,  # clear pending receive after completion
        0x803DF9B0: 0xE1C100B0,  # empty=1
        0x803DF9B8: 0xE1C100B2,  # second header halfword=1
        0x803F3A98: 0xE5801010,  # queue source setter
        0x803F2038: 0xC8010B20,  # static BSS scalar, not a pointer to board
        0x803F1D18: 0xE5911000,
        0x803F1D1C: 0xE3510000,  # BSS word tested against zero
    }
    for address, word in expected.items():
        if pdd.word(address) != word:
            raise ValueError("audited instruction changed at %08X" % address)
    for address, target in ((0x803F03D4, 0x803E011C), (0x803E02D0, 0x803EEFCC)):
        if arm_bl_target(address, pdd.word(address)) != target:
            raise ValueError("pointer constructor/getter call changed")
    if struct.unpack_from("<I", pdd.data, 96)[0] != 0xC8010B20 or struct.unpack_from("<I", pdd.data, 36)[0] != 24:
        raise ValueError("BSS root/size changed")
    reader = [0xE5D00040, 0xE5911000, 0xE3500000, 0x01A00001, 0x11A00861, 0xE12FFF1E]
    if pdd.read(0x803F7664, 24) != struct.pack("<6I", *reader):
        raise ValueError("word reader changed")
    ranges = {
        "context_constructor_base": (0x803DF228, 64),
        "board_allocation_and_reader_flag": (0x803F03BC, 36),
        "context_reader_owner": (0x803E02CC, 12),
        "embedded_reader_getter": (0x803EEFCC, 8),
        "shared_window_pointer_setup": (0x803E080C, 136),
        "consumer": (0x803DF6E8, 744),
        "word_reader": (0x803F7664, 24),
        "bss_scalar_test": (0x803F1D14, 16),
    }
    return {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static saved E90 ROM; no device I/O or memory mutation",
        "pdd_sha256": sha256(pdd.data),
        "checked_instructions": len(expected),
        "ranges": {name: {"address": "%08X" % address, "bytes": count,
                          "sha256": sha256(pdd.read(address, count))}
                   for name, (address, count) in ranges.items()},
        "pointer_chain": {
            "context_bytes": 364,
            "board_context_offset": 264,
            "context_common_board_offset": 48,
            "common_board_adjustment": 8,
            "context_reader_offset": 24,
            "reader_common_board_adjustment": 164,
            "reader_board_offset": 172,
            "reader_swap_byte": 64,
            "swap_byte_board_offset": 236,
            "swap_byte_initial_value": 1,
            "reader_word0": "shared-memory ARM base, not the fromDSP header",
            "context_fromDSP_header_offset": 224,
            "context_record_array_offset": 240,
            "record_array_header_adjustment": 8,
            "queue_source_offset": 16,
            "queue_pending_receive_offset": 40,
        },
        "copy_check_bss": {
            "address": "C8010B20", "bytes": 24,
            "meaning": "six module BSS words; word0 is used as a zero/nonzero flag",
            "message_context_root": False,
            "runtime_reader_swap_byte_observed": False,
        },
        "runtime_gate": {
            "ready": False,
            "missing": "verified live board/context root and mapped allocation bounds",
            "required": ["pin or otherwise prove live object ownership",
                         "verify board/context identity before following fields",
                         "verify mapped shared-memory span before header/record reads",
                         "bounded queue traversal; treat snapshots as non-atomic"],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--e90-rom", type=Path, default=ROOT / "work/evidence/e90/rom")
    args = parser.parse_args()
    print(json.dumps(audit(args.e90_rom), indent=2))


if __name__ == "__main__":
    main()
