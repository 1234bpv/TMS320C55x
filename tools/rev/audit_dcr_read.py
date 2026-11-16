"""Verify the downloadable diagnostic's DCR helper bytes, not just its source."""
import json
import argparse
import re
import struct
import subprocess
from pathlib import Path

from extract_doff_section import checksum, coff, sha256

ROOT = Path(__file__).resolve().parents[2]


def build_report(variant="dmm-ring-dcr"):
    assert variant in ("dmm-ring-dcr", "dmm-ring-wsola", "dmm-ring-mdec", "dmm-ring-spu")
    wsola = variant == "dmm-ring-wsola"
    mdec = variant == "dmm-ring-mdec"
    spu = variant == "dmm-ring-spu"
    path = ROOT / f"out/dsp/c55stream-{variant}.dll55l"
    data = path.read_bytes()
    strings_size, _, _, _, symbols, _, sections, *_ = struct.unpack_from("<4I8HI", data)
    strings = data[56:56 + strings_size]
    start = 56 + strings_size
    matches = []
    for i in range(sections):
        entry = struct.unpack_from("<4I2H2I", data, start + i*28)
        name = strings[entry[0]:strings.index(0, entry[0])].decode("ascii")
        if name == ".text":
            matches.append((i+1, entry))
    assert len(matches) == 1, "missing or duplicate downloadable text section"
    section, (_, address, _, size, _, _, pos, packets) = matches[0]
    pieces = []
    relocations_at = []
    relocation_kinds = {}
    offset = 0
    for _ in range(packets):
        relocations, count, _ = struct.unpack_from("<3I", data, pos)
        end = pos + 12 + ((count + 3) & ~3)
        packet_end = end + relocations*12
        assert 0 < count <= size and packet_end <= len(data)
        assert checksum(data[pos:packet_end]) == 0xffffffff
        for i in range(relocations):
            relative, symbol, kind = struct.unpack_from("<3I", data, end+i*12)
            assert relative < count and symbol < symbols and kind in ((0x50000,0x7c0000) if mdec else (0x50000,))
            relocation_kinds[f"{kind:08X}"] = relocation_kinds.get(f"{kind:08X}",0)+1
            relocations_at.append(offset + relative)
        pieces.append(data[pos+12:pos+12+count])
        pos = packet_end
        offset += count
    text = b"".join(pieces)
    assert len(text) == size
    definitions = []
    for i in range(symbols):
        name, value, target_section, storage = struct.unpack_from("<IIhh", data, start+sections*28+i*12)
        if name == 0xffffffff:
            assert storage == 3 and target_section > 0, "unexpected anonymous symbol"
            continue
        if strings[name:strings.index(0, name)] == b"_ring_read_dcr":
            definitions.append((value, target_section, storage))
    assert len(definitions) == 1 and definitions[0][1:] == (section, 2)
    helper_offset = definitions[0][0] - address
    assert 0 <= helper_offset <= len(text)-6
    assert not any(helper_offset-4 <= location < helper_offset+6 for location in relocations_at)
    code = text[helper_offset:helper_offset+6]
    obj = ROOT / "out/dcr62-read-helper.obj"
    obj.write_bytes(coff(address, code))
    disassembler = Path("C:/Program Files (x86)/Texas Instruments/C5500 Code Generation Tools 4.4.1/bin/dis55.exe")
    result = subprocess.run([str(disassembler), "-qq", str(obj)], capture_output=True,
                            text=True, timeout=15, check=True)
    instructions = re.findall(r"^\s*[0-9a-fA-F]+:\s+[0-9a-fA-F]+\s+(.+)$", result.stdout, re.M)
    assert len(instructions) == 2, result.stdout
    assert re.fullmatch(r"MOV\s+port\(#(?:512|0x200|00200h)\),\s*T0", instructions[0], re.I), instructions
    assert instructions[1].strip().upper() == "RET", instructions
    assembly = (ROOT / f"out/dsp/stream_node-{variant}.asm").read_text(encoding="ascii")
    calls = [match.start() for match in re.finditer(r"^\s*CALL #_ring_read_dcr", assembly, re.M)]
    exchange = assembly.index("CALL #_ring_spu_exchange" if spu else "CALL #_ring_mdec_exchange" if mdec else "CALL #_ring_wsola_exchange" if wsola else "CALL #_ring_exchange")
    assert len(calls) == (4 if wsola or mdec or spu else 2)
    before = max(pos for pos in calls if pos < exchange)
    after = min(pos for pos in calls if pos > exchange)
    assert "MOV T0, *AR3(#14)" in assembly[before:exchange]
    assert "MOV T0, *AR3(#15)" in assembly[after:]
    return {"scope": f"distinct N95 candidate{67 if spu else 65 if mdec else 63 if wsola else 62}/protocol{42 if spu else 41 if mdec else 40 if wsola else 39}; no phone I/O",
            "DSP_sha256": sha256(data), "helper_section": ".text (linker merged .text:dcr_read)",
            "helper_symbol_value": f"{definitions[0][0]:06X}", "helper_section_byte_offset": helper_offset,
            "helper_code_hex": code.hex().upper(), "helper_code_sha256": sha256(code),
            "helper_relocations": 0, "instructions": instructions,
            "text_relocation_kinds": relocation_kinds,
            "helper_io_reads": 1, "helper_io_writes": 0,
            "calls_per_exchange": 2, "call_order": f"DCR read -> {'ring_spu_exchange' if spu else 'ring_mdec_exchange' if mdec else 'ring_wsola_exchange' if wsola else 'ring_exchange'} -> DCR read",
            "notification_fields": {"marker_word": 13, "before_word": 14, "after_word": 15},
            "reference": "docs/evidence/2026-10-03/dsp-native-notification-audit.json",
            "limits": ["DCR reads may affect timing/ordering; diagnostic is separate from candidate61",
                       "helper instruction audit is not a complete external-memory publication contract"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("dmm-ring-dcr", "dmm-ring-wsola"), default="dmm-ring-dcr")
    args = parser.parse_args()
    report = build_report(args.variant)
    path = ROOT / f"docs/evidence/2026-10-04/n95-{'wsola63' if args.variant == 'dmm-ring-wsola' else 'dcr62'}-instruction-audit.json"
    path.write_bytes((json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(path)
