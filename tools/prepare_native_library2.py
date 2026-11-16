"""Derive a research-only generic registration from the saved E90 ROM DLL.

Changes only :0 to :2 in .dcd_register and that packet's checksum.
The original ROM properties are parsed separately. DSP code/data/relocations
remain byte-for-byte identical. Never writes to a phone or to ROM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from extract_doff_section import checksum
from paths import SHARED


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combined", action="store_true", help="keep properties0 and add library2 in one registration packet")
    args = parser.parse_args()
    source = ROOT / "work/evidence/e90/strmcopydyn-e90.dll55l"
    target = ROOT / ("out/dsp/strmcopy-e90-library2-combined.dll55l" if args.combined else "out/dsp/strmcopy-e90-library2.dll55l")
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest().upper() != "9929856254DF6912BB6CC70C30551A950647F1462CC4AB335E56220ED7F0E53A":
        raise RuntimeError("unexpected E90 ROM reference")
    strings, _, _, _, _, _, sections, _, _, _, _, _, _ = struct.unpack_from("<4I8HI", data)
    table = 56 + strings
    names = data[56:table]
    selected = []
    for i in range(sections):
        name, _, _, _, _, _, pos, packets = struct.unpack_from("<4I2H2I", data, table + i * 28)
        if names[name:names.index(0, name)] == b".dcd_register":
            selected.append((pos, packets))
    if len(selected) != 1 or selected[0][1] != 1:
        raise RuntimeError("registration must occupy one packet")
    pos, _ = selected[0]
    relocations, count, _ = struct.unpack_from("<3I", data, pos)
    end = pos + 12 + ((count + 3) & ~3)
    if relocations or checksum(data[pos:end]) != 0xFFFFFFFF:
        raise RuntimeError("invalid registration packet")
    old = "7EEB2C7E_785A_11D4_A650_00C04F0C04F3:0,".encode("utf-16-be")
    new = "7EEB2C7E_785A_11D4_A650_00C04F0C04F3:2,".encode("utf-16-be")
    payload = data[pos + 12:pos + 12 + count]
    if payload.count(old) != 1:
        raise RuntimeError("unique type0 registration missing")
    altered = bytearray(data)
    if args.combined:
        replacement = old + new + b"\0\0"
        replacement += b"\0" * (-len(replacement) % 4)
        packet = struct.pack("<3I", 0, len(old + new) + 2, 0) + replacement
        altered[pos:end] = packet
        growth = len(packet) - (end - pos)
        # DOFF packet offsets are absolute. The only section after registration
        # is the unchanged properties packet. No downloadable section changes.
        for i in range(sections):
            record = table + i * 28
            section_pos = struct.unpack_from("<I", data, record + 20)[0]
            if section_pos == pos:
                struct.pack_into("<I", altered, record + 12, len(old + new) + 2)
            elif section_pos >= end:
                struct.pack_into("<I", altered, record + 20, section_pos + growth)
        struct.pack_into("<I", altered, 40, (0xFFFFFFFF - checksum(altered[table:table + sections * 28])) & 0xFFFFFFFF)
        struct.pack_into("<I", altered, 52, 0)
        struct.pack_into("<I", altered, 52, (0xFFFFFFFF - checksum(altered[36:56])) & 0xFFFFFFFF)
        end += growth
    else:
        altered[pos + 12:pos + 12 + count] = payload.replace(old, new)
    struct.pack_into("<I", altered, pos + 8, 0)
    struct.pack_into("<I", altered, pos + 8, (0xFFFFFFFF - checksum(altered[pos:end])) & 0xFFFFFFFF)
    if checksum(altered[pos:end]) != 0xFFFFFFFF:
        raise RuntimeError("packet checksum failed")
    if not args.combined and (altered[:pos] != data[:pos] or altered[end:] != data[end:]):
        raise RuntimeError("changes outside registration packet")
    unchanged = []
    for i in range(sections):
        record = table + i * 28
        section_name_offset, _, _, _, _, _, section_pos, _ = struct.unpack_from("<4I2H2I", data, record)
        if section_pos == pos:
            continue
        section_name = names[section_name_offset:names.index(0, section_name_offset)].decode("ascii")
        section_end = min([entry_pos for j in range(sections)
                           if (entry_pos := struct.unpack_from("<I", data, table + j * 28 + 20)[0]) > section_pos] + [len(data)])
        new_pos = struct.unpack_from("<I", altered, record + 20)[0]
        raw = data[section_pos:section_end]
        if altered[new_pos:new_pos + len(raw)] != raw:
            raise RuntimeError("section packet or relocations changed: " + section_name)
        unchanged.append({"section": section_name, "packet_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest().upper()})
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(altered)
    dump = subprocess.run([str(SHARED / "toolchain/ti/dspbridge/dsp/doffbuild/bin/DLLdump.exe"), str(target)],
                          capture_output=True, text=True, timeout=30, check=True)
    if "Verification PASSED" not in dump.stdout:
        raise RuntimeError("derived DLL verification failed")
    result = {"scope": "Research-file DCD metadata only; no phone writes or code changes",
              "source_sha256": hashlib.sha256(data).hexdigest().upper(),
              "derived_path": target.relative_to(ROOT).as_posix(),
              "derived_sha256": hashlib.sha256(altered).hexdigest().upper(),
              "bytes": len(altered), "DLLdump_verification": True,
              "changed_section": ".dcd_register", "changed_offsets": None if args.combined else [i for i, (a, b) in enumerate(zip(data, altered)) if a != b],
              "registration_from": ":0,", "registration_to": ":2,",
              "code_data_relocations_identical": True,
              "requires": "Parse original Z ROM properties first, then this E research library2 registration; no successful reference RUN yet"}
    if args.combined:
        result.update({"registration_to": ":0, and :2, in one packet", "unchanged_section_packets": unchanged,
                       "metadata_changes": "Registration packet grew; section size/absolute offsets and table/verification checksums updated",
                       "requires": "Combined properties0/library2 tests select preflight; failure attribution is still open"})
    report = "e90-d0-native-library2-combined-derivation.json" if args.combined else "e90-d0-native-library2-derivation.json"
    (ROOT / "docs/evidence/2026-10-01" / report).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
