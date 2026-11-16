"""Audit saved DSP notification paths; do not infer an interconnect fence."""
import hashlib
import json
import struct
from pathlib import Path

from extract_doff_section import Doff, checksum
from paths import SHARED

ROOT = Path(__file__).resolve().parents[2]
TI_URL = ("https://software-dl.ti.com/dsps/dsps_public_sw/sdo_sb/targetcontent/"
          "bios/dspbios/5_41_13_42/exports/bios_setuplinux_5_41_13_42.bin")


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def initialized_data(module, name):
    entry = module.sections[name]
    pos, packets = entry[-2:]
    parts = []
    for _ in range(packets):
        relocations, count, _ = struct.unpack_from("<3I", module.data, pos)
        end = pos + 12 + ((count + 3) & ~3)
        if relocations or not count or end > len(module.data):
            raise ValueError("unsupported initialized data packet")
        if checksum(module.data[pos:end]) != 0xFFFFFFFF:
            raise ValueError("invalid initialized data checksum")
        parts.append(module.data[pos + 12:pos + 12 + count])
        pos = end
    raw = b"".join(parts)
    if len(raw) != entry[3]:
        raise ValueError("initialized section size differs")
    return raw


def cinit_records(raw):
    pos, records = 0, {}
    while pos + 2 <= len(raw):
        words = int.from_bytes(raw[pos:pos + 2], "big")
        if not words:
            if pos + 2 != len(raw):
                raise ValueError("unexpected cinit data after terminator")
            return records
        end = pos + 6 + 2 * words
        if end > len(raw):
            raise ValueError("truncated cinit record")
        address = int.from_bytes(raw[pos + 2:pos + 5], "big")
        space = raw[pos + 5]
        if (address, space) in records:
            raise ValueError("duplicate initializer destination")
        records[address, space] = raw[pos + 6:end]
        pos = end
    raise ValueError("missing cinit terminator")


def audit(path):
    module = Doff(path)
    sections = {name: module.text(name) for name in
                ("EXTERNAL_common_code", ".sysinit")}
    checks = {
        0x02725A: "6c25d65f",       # BIOS version getter
        0x02725E: "7c510044",       # require native BIOS 5.10
        0x027262: "0414fd",         # mismatch spins at this check
        0x0272A2: "6c24ece0",       # native configured user-init call
        0x24ECE0: "46664804",       # BCLR ST3_MPNMC; RET
        0x24BFA3: "140ea4",         # stream function table destination +14 words
        0x24BFA9: "4c0d806514",     # copy 14 words from matched device table
        0x24E581: "ed6d080014",     # issue callback at stream+20 C55 words
        0x24E589: "9200",           # indirect CALL AC0
        0x247DC5: "f06d00010008",   # native channel type 1 branch
        0x247DD9: "6c246958",       # DMA path
        0x247DE3: "f06d00020008",   # native channel type 2 branch
        0x247DF7: "6c24b350",       # zero-copy path
        0x247E3B: "6c24daa4",       # copy path mailbox notification
        0x24B456: "eb6d080008",     # zero-copy buffer address -> shared descriptor
        0x24B4C9: "6c24dac4",       # zero-copy mailbox notification
        0x026768: "ed310812ace0",   # copy routine from native configured pointer
        0x026776: "9200",           # copy callback call
        0x0267BA: "6c24daa4",       # copy completion mailbox notification
        0x24DAA4: "ec31be7f1041",   # mailbox status address
        0x24DAAA: "ed6108180100",   # status read, mask bit 0
        0x24DAB0: "0410f7",         # poll while status bit set
        0x24DAB7: "ec31be7f1022",   # mailbox message address
        0x24DABD: "eb6108",         # mailbox write
        0x24DAC8: "ec31be7f1041",
        0x24DACE: "ed6108180100",
        0x24DAD4: "0410f7",
        0x24DADA: "ec31be7f1022",
        0x24DAE0: "eb6108",
    }
    observed = []
    bios_delta = module.symbols["_BIOS_init"][0] - 0x027248
    for reference_address, expected in checks.items():
        # N95's BIOS initializer is four bytes later; service/STRM sites
        # match E90. Resolve this function from its export, not a global delta.
        address = reference_address + (bios_delta if reference_address in
                                       (0x02725A, 0x02725E, 0x027262, 0x0272A2) else 0)
        start, code = next((start, code) for start, code in sections.values()
                           if start <= address < start + len(code))
        raw = code[address - start:address - start + len(bytes.fromhex(expected))]
        if raw != bytes.fromhex(expected):
            raise ValueError(f"native DSP instruction changed at {address:06X}")
        observed.append({"byte_address": f"{address:06X}", "bytes": raw.hex().upper()})
    cinit = initialized_data(module, ".cinit")
    table_address = module.symbols["_DSM_FXNS"][0] // 2
    table = cinit_records(cinit)[table_address, 0]
    expected_table = bytes.fromhex(
        "00247a900025c49400247acc00247dac00247f0400248148002481ec")
    if table != expected_table or module.symbols["GBL_A_VERSION"][0] != 0x5100:
        raise ValueError("native BIOS version or DSM function table changed")
    return {"baseimage_sha256": digest(module.data),
            "native_BIOS_version": "5.10 (0x5100)",
            "checked_instructions": observed,
            "DSM_function_table_cinit_word_address": f"{table_address:06X}",
            "DSM_function_table": [f"{int.from_bytes(table[p:p+4], 'big'):06X}"
                                   for p in range(0, len(table), 4)],
            "cinit_sha256": digest(cinit),
            "GBL_DCRPOSTEDWRITE_symbol_present": "GBL_DCRPOSTEDWRITE" in module.symbols}


def reference():
    # Read only selected InstallJammer records. No installer is executed.
    import zlib
    archive = (ROOT / "out/bios_setuplinux_5_41_13_42.bin").read_bytes()
    trailer = archive[-256:]
    if not trailer.startswith(b"CRAP02"):
        raise ValueError("unsupported TI reference archive")
    start = int(trailer[6:].split(b"\0")[0])
    wanted = {"main2.tcl", "870E4A8B-DFAD-1C94-CA7F-FF57BBA99F6B"}
    selected = {}
    for pos in range(start, len(archive) - 256, 256):
        entry = archive[pos:pos + 256]
        if entry[:6] != b"FILEZL":
            continue
        name = entry[6:134].split(b"\0")[0].decode("ascii")
        if name not in wanted:
            continue
        size = int(entry[134:146].split(b"\0")[0])
        count = int(entry[146:158].split(b"\0")[0])
        offset = int(entry[172:184].split(b"\0")[0])
        if size > 2_000_000 or offset + count > start:
            raise ValueError("reference archive record outside payload")
        data = zlib.decompress(archive[offset:offset + count], -15)
        if len(data) != size:
            raise ValueError("reference decompression size differs")
        selected[name] = data
    guid = "870E4A8B-DFAD-1C94-CA7F-FF57BBA99F6B"
    manifest = selected["main2.tcl"].decode("utf-8")
    if f"File ::{guid} -name gbl.h55 " not in manifest:
        raise ValueError("reference identifier is not gbl.h55")
    header = selected[guid].decode("ascii")
    if "or #0x80, port(#0x200)" not in header:
        raise ValueError("reference DCR/WPE configuration changed")
    return {"author": "Texas Instruments", "download_url": TI_URL,
            "archive_sha256": digest(archive),
            "selected_file": "packages/ti/bios/include/gbl.h55",
            "selected_file_sha256": digest(selected[guid]),
            "section": "GBL configuration, lines 295-306, OMAP2420 conditional",
            "instruction": "or #0x80, port(#0x200)",
            "meaning": "OMAP2420 DCR is I/O port 0x200, WPE bit mask 0x80",
            "limit": "TI BIOS 5.41 reference, not the phones' BIOS 5.10 configuration"}


def build_report():
    n95 = audit(SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
    e90 = audit(ROOT / "work/evidence/e90/baseimage.dof")
    for key in ("DSM_function_table",):
        if n95[key] != e90[key]:
            raise ValueError("audited native notification paths differ between phones")
    if [item["bytes"] for item in n95["checked_instructions"]] != [
            item["bytes"] for item in e90["checked_instructions"]]:
        raise ValueError("audited native notification instructions differ between phones")
    return {"scope": "saved firmware and read-only extraction of a primary TI reference; no phone I/O",
            "status": "partial", "n95": n95, "e90": e90,
            "DCR_reference": reference(),
            "posted_mode_reference": {
                "url": "https://software-dl.ti.com/targetcontent/legacy_files/targetcontent/bios/bios_5_31/sabios-h16/docs/packages/ti/bios/doc/spru404m.pdf",
                "section": "GBL Module, 2-118, PDF page 146",
                "meaning": "DCR.WPE selects posted/non-posted D-port writes on OMAP2320/2420. The documented configuration default is posted; it is not a measurement of these phones."},
            "verified": [
                "STRM_create copies 14 words of matched device callbacks; STRM_issue calls stream+20 words. The initialized DSM table puts 0x247DAC at this position.",
                "DSM callback branches on native channel type: DMA=1, zero-copy=2, other types follow the copy path. Both copy and zero-copy mailbox routines poll DSP-word address 0x7F1041 before writing 0x7F1022.",
                "Native early user-init clears ST3_MPNMC and returns; this function does not set DCR.WPE."],
            "not_proven": [
                "The actual DCR.WPE value during candidate54/61 runs is unknown. Absence of the BIOS 5.41 configuration symbol in native BIOS 5.10 is not proof that posting is disabled.",
                "Polling mailbox status is not independently established as a drain of earlier SDRAM D-port writes.",
                "The configured copy-function pointer and dynamic device/channel selection of each historical run are not re-read by this static audit.",
                "No OMAP2420 interconnect-wide publication fence is established; compiler order and correct packets remain separate evidence."],
            "next_probe": "After fresh clock validation, use a distinct read-only DSP diagnostic to report port(0x200) before/after exchange. Do not write DCR, replace native firmware, or retrospectively assign its result to candidate61."}


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
