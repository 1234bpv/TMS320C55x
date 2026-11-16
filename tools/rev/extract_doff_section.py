"""Extract linked C55 instruction bytes from a local executable DOFF.

This handles DOFF0 with little-endian records, big-endian C55 code and no
relocations in the selected text section. Packet instruction bytes are kept
unchanged. Raw code and a synthetic COFF for dis55 remain local artifacts.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def checksum(data, extra=0):
    if len(data) % 4:
        raise ValueError("checksum record is not aligned to four bytes")
    return (sum(struct.unpack("<%dI" % (len(data) // 4), data)) + extra) & 0xFFFFFFFF


class Doff:
    def __init__(self, path):
        self.data = path.read_bytes()
        d = self.data
        if len(d) < 56 or checksum(d[:36]) != 0xFFFFFFFF:
            raise ValueError("invalid DOFF header checksum")
        (strings_size, _, reshuffle, names_size, symbols, _, sections, targets,
         version, target, flags, _, _) = struct.unpack_from("<4I8HI", d)
        if (reshuffle != 0x00010203 or version != 0 or target != 0x9C or
                flags & 0x300 != 0x200 or flags & 3 != 3):
            raise ValueError("only linked executable C55 DOFF0 in this byte order is supported")
        if not 0 < names_size <= strings_size or not sections or targets > sections:
            raise ValueError("invalid DOFF table sizes")
        section_start = 56 + strings_size
        symbol_start = section_start + sections * 28
        symbol_end = symbol_start + symbols * 12
        if strings_size % 4 or symbol_end > len(d):
            raise ValueError("truncated DOFF tables")
        self.strings = d[56:section_start]
        verify = struct.unpack_from("<5I", d, 36)
        tables = (d[section_start:symbol_start], self.strings, d[symbol_start:symbol_end])
        if checksum(d[36:56]) != 0xFFFFFFFF or any(
                checksum(table, cs) != 0xFFFFFFFF for table, cs in zip(tables, verify[1:4])):
            raise ValueError("invalid DOFF verification/table checksum")
        self.sections = {}
        for i in range(sections):
            entry = struct.unpack_from("<4I2H2I", d, section_start + i * 28)
            name = self.string(entry[0])
            if name in self.sections:
                raise ValueError("duplicate section name: " + name)
            self.sections[name] = entry
        self.symbols = {}
        for i in range(symbols):
            name, value, section, storage = struct.unpack_from("<IIhh", d, symbol_start + i * 12)
            if storage == 2:
                self.symbols[self.string(name)] = (value, section)

    def string(self, offset):
        if not 0 <= offset < len(self.strings):
            raise ValueError("string-table offset out of bounds")
        end = self.strings.find(b"\0", offset)
        if end < 0:
            raise ValueError("unterminated DOFF string")
        return self.strings[offset:end].decode("ascii")

    def text(self, name):
        _, address, load, size, page, flags, pos, packets = self.sections[name]
        if flags & 15 or not flags & 0x20 or page or load != address or not packets:
            raise ValueError("selected section is not linked downloadable C55 text")
        pieces = []
        for _ in range(packets):
            if pos + 12 > len(self.data):
                raise ValueError("truncated image packet")
            relocations, count, _ = struct.unpack_from("<3I", self.data, pos)
            end = pos + 12 + ((count + 3) & ~3)
            if relocations or not count or end > len(self.data):
                raise ValueError("relocated, empty or truncated packet is unsupported")
            if checksum(self.data[pos:end]) != 0xFFFFFFFF:
                raise ValueError("invalid image packet checksum")
            pieces.append(self.data[pos + 12:pos + 12 + count])
            pos = end
        code = b"".join(pieces)
        if len(code) != size:
            raise ValueError("C55 text size differs from packet payload size")
        return address, code


def coff(address, code):
    header = struct.pack("<HHIIIHHH", 0xC2, 1, 0, 0, 0, 28, 0x12E0, 0x9C)
    optional = struct.pack("<HH6I", 0x108, 0, len(code), 0, 0, address, address, 0)
    section = struct.pack("<8s9I2H", b".text", address, address, len(code), 98,
                          0, 0, 0, 0, 0x20, 8, 0)
    return header + optional + section + code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--section", required=True)
    p.add_argument("--out-base", required=True, type=Path)
    p.add_argument("--reference", type=Path, help="require exact equality with an independent raw extraction")
    a = p.parse_args()
    module = Doff(a.input)
    address, code = module.text(a.section)
    if a.reference and code != a.reference.read_bytes():
        raise ValueError("code does not match the independent reference")
    a.out_base.parent.mkdir(parents=True, exist_ok=True)
    a.out_base.with_suffix(".bin").write_bytes(code)
    a.out_base.with_suffix(".obj").write_bytes(coff(address, code))
    print(json.dumps({"input_sha256": sha256(module.data), "section": a.section,
                      "address": "%06X" % address, "bytes": len(code),
                      "code_sha256": sha256(code), "packet_bytes": "unchanged",
                      "checksums": "header, verification, tables and all selected packets verified",
                      "independent_reference_equal": True if a.reference else None}, indent=2))


if __name__ == "__main__":
    main()
