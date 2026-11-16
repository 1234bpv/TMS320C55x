"""Reproduce E90-only D0 lifecycle and D1 ordinal audit from saved ROM.

No device access. Publishes addresses and hashes, never ROM instructions.
"""
import datetime
import json
from pathlib import Path

from compare_node_info import Module
from extract_doff_section import sha256
from extract_doff_section import Doff

ROOT = Path(__file__).resolve().parents[2]


def main():
    rom = ROOT / "work/evidence/e90/rom"
    pdd = Module(rom / "ehwaomap.pdd")
    ldd = Module(rom / "ehwa.ldd")
    bridge = Module(rom / "bridgeapi.dll")
    ranges = {
        "run_split_dynamic_unloads_create": (pdd, 0x803E5AB4, 44),
        "negative_rms_maps_to_minus2": (pdd, 0x803E6DE8, 8),
        "delete_completion_including_failure": (pdd, 0x803E70B8, 232),
        "free_unloads_loaded_libraries": (pdd, 0x803E6758, 176),
        "ldd_destructor_frees_pdd_only_if_internal_state4": (ldd, 0x803F87FC, 44),
        "cancel_adapter_keeps_index_value": (ldd, 0x803F8AF4, 44),
        "running_delete_sends_rms_exit": (pdd, 0x803E69B4, 276),
        "exitack_checks_eok_and_dispatches_delete": (pdd, 0x803DF7EC, 128),
        "delete_dispatch_loads_callback": (pdd, 0x803E6860, 340),
        "reserve_ordinal27": (bridge, 0x803FA420, 60),
        "map_ordinal31": (bridge, 0x803FA45C, 182),
        "unmap_ordinal34": (bridge, 0x803FA512, 32),
        "unreserve_ordinal28": (bridge, 0x803FA532, 30),
        "mmu_mapping_flag_masks": (pdd, 0x803EF01C, 96),
        "c55_common_board_base_adjustment": (pdd, 0x803F03D0, 8),
        "common_embedded_reader_getter": (pdd, 0x803EEFCC, 8),
        "c55_reader_initial_flag_one": (pdd, 0x803F0304, 8),
        "c55_reader_flag_store": (pdd, 0x803F03BC, 12),
        "create_env_binds_queue_source": (pdd, 0x803E6E34, 16),
        "queue_source_setter": (pdd, 0x803F3A98, 8),
    }
    expected = ((pdd, 0x803E6DE8, 0xE35A0000),
                (pdd, 0x803E6DEC, 0xB3E05001),
                (pdd, 0x803E70DC, 0xE3550000),
                (pdd, 0x803E7198, 0xE5848028),
                (ldd, 0x803F880C, 0xE3500004),
                (ldd, 0x803F8B00, 0xE1A01002),
                (pdd, 0x803E6A14, 0xE3A00102),
                (pdd, 0x803DF7EC, 0xE3500101),
                (pdd, 0x803DF7F8, 0xE3500902),
                (pdd, 0x803DF850, 0xE3500902),
                (pdd, 0x803DF864, 0xEB001BFD),
                (pdd, 0x803EF01C, 0xE3100002),
                (pdd, 0x803EF02C, 0xE2001004),
                (pdd, 0x803EF050, 0xE3100010),
                (pdd, 0x803F0308, 0xE3A08001),
                (pdd, 0x803F03C0, 0xE5C480EC),
                (pdd, 0x803F03D0, 0xE2841008),
                (pdd, 0x803EEFCC, 0xE28000A4),
                (pdd, 0x803E6E34, 0xE584602C),
                (pdd, 0x803F3A98, 0xE5801010))
    for module, address, value in expected:
        if module.word(address) != value:
            raise ValueError("audited instruction changed at %08X" % address)
    for slot, address in ((56, 0x803E6048), (64, 0x803E62F0),
                          (88, 0x803E6758), (92, 0x803E6C04)):
        if pdd.word(0x803F8424 + slot) != address:
            raise ValueError("vtable changed")
    base = Doff(ROOT / "work/evidence/e90/baseimage.dof")
    code_base, code = base.text("EXTERNAL_common_code")
    dsp_ranges = {"execute_wrapper": (0x24E6F0, 100),
                  "NODE_putMsg": (0x24DD5C, 186),
                  "MSG_notify": (0x24E758, 98),
                  "MSG_fromDSP": (0x24C928, 360)}
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static saved E90 ROM; no new DSP RUN or DMM evidence",
        "rom_sha256": {name: sha256(m.data) for name, m in
                       (("pdd", pdd), ("ldd", ldd), ("bridge", bridge))},
        "ranges": {name: {"address": "%08X" % start, "bytes": count,
                          "sha256": sha256(m.read(start, count))}
                   for name, (m, start, count) in ranges.items()},
        "baseimage_sha256": sha256(base.data),
        "dsp_ranges": {name: {"address": "%06X" % start, "bytes": count,
                              "sha256": sha256(code[start-code_base:start-code_base+count])}
                       for name, (start, count) in dsp_ranges.items()},
        "d0": [
            "RUN unloads create only when phase_split=1 and dynamic load_type=1; generic library2 skips this.",
            "Negative RMS callback return maps to host -2; it does not prove absence of a live task.",
            "Delete completion failure skips success notification/env clear but still reaches internal PDD state4.",
            "LDD destructor tests internal state4 before PDD destruction; a failed callback is not a safe unload barrier.",
            "Task15/17 cancellation forwards argument as index value, not a pointer to an index.",
            "Cancel adapter returns zero; transfer status must independently complete before freeing its descriptor/buffer.",
            "Official execute return invokes native EXITACK; its message delivery remains a hardware gate.",
            "RUNNING control6 sets internal state9 and queues RMS_EXIT 80000000 with nodeEnv; queue submission alone is not delivery.",
            "EXITACK consumer expects RMS_EOK 00008000, checks node membership/magic, then dispatches delete automatically even after an error-status notification.",
            "An execute return before host control6 can race automatic deletion with manual deletion; this is a hypothesis for the failed run, not proven causation.",
            "State3 alone does not prove successful execute/ACK; native processor-fault paths can also set it.",
            "C55 board setup passes its common base+8. The common reader getter+164 addresses board+172; byte+64 therefore equals board+236, explicitly initialized to1. The IVA board layout is different; runtime reader value is not observed.",
            "Native wrapper constructs EXITACK cmd40000000/arg1=execute AC0 return/arg2=0 and NODE_putMsg timeoutFFFF. NODE_putMsg copies cmd/args and env as source; MSG_fromDSP copies native longs, publishes empty0, then interrupts GPP. Hardware completion remains unproven.",
            "Successful RMS create stores its returned env in node+44 and the same value through queue setter to queue+16, without multiplication or a word swap. Actual runtime routing still requires message delivery evidence.",
        ],
        "d1": {
            "ordinals": {"reserve": 27, "map": 31, "unmap": 34, "unreserve": 28},
            "reserve_ioctl": "0400000F", "map_ioctl": "04000012",
            "unmap_ioctl": "04000013", "unreserve_ioctl": "04000010",
            "map_record_payload_bytes": 24, "page_bytes": 4096,
            "map_record": ["ARM virtual address", "byte count", "reserved DSP address",
                           "flags", "linear-to-physical page table pointer", "page count"],
            "native_low_level_flag_masks": {"bit1": "endian boolean", "bit2": "mixed element boolean",
                                             "bits3_to6": "element8/16/32/64 selection, skipped if mixed"},
            "flag_limit": "Masks match TI reference. Full wrapper/default normalization and actual byte/word interpretation still unverified on E90.",
            "unverified": ["DSP returned address units", "pinned lifetime", "MMU element/endian flags",
                           "cache maintenance ownership", "notification and ring wrap", "latency/bandwidth"],
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
