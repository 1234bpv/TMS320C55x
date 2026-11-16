"""Compare the recovered N95/E90 get-info paths without running a device.

Only the documented firmware addresses below are examined. ROM contents stay
local; output contains hashes, instruction differences and record offsets.
"""
import argparse
import datetime
import hashlib
import json
import struct
from pathlib import Path

from paths import ROM


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


class Module:
    def __init__(self, path):
        self.data = path.read_bytes()
        if len(self.data) < 120:
            raise ValueError("truncated extracted XIP header: " + str(path))
        self.base = struct.unpack_from("<I", self.data, 20)[0]
        declared_size = struct.unpack_from("<I", self.data, 28)[0]
        self.size = min(declared_size, len(self.data) - 120)
        uid = struct.unpack_from("<I", self.data)[0]
        if uid not in (0x10000079, 0x1000007A) or self.base < 0x80000000 or self.size <= 0:
            raise ValueError("invalid extracted XIP module: " + str(path))

    def read(self, address, size):
        offset = address - self.base
        if offset < 0 or offset + size > self.size:
            raise ValueError("address outside module code")
        return self.data[120 + offset:120 + offset + size]

    def word(self, address):
        return struct.unpack("<I", self.read(address, 4))[0]


def arm_bl_target(address, word):
    if word >> 24 != 0xEB:
        raise ValueError("expected an unconditional ARM BL")
    immediate = word & 0xFFFFFF
    if immediate & 0x800000:
        immediate -= 0x1000000
    return (address + 8 + immediate * 4) & 0xFFFFFFFF


def compare(n95, e90, first, second, size):
    a, b = n95.read(first, size), e90.read(second, size)
    return {
        "n95_start": "%08X" % first, "e90_start": "%08X" % second,
        "bytes": size, "bytes_equal": a == b,
        "n95_sha256": sha256(a), "e90_sha256": sha256(b),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n95-rom", type=Path, default=Path(ROM))
    parser.add_argument("--e90-rom", type=Path, required=True)
    args = parser.parse_args()
    nldd = Module(args.n95_rom / "ehwa.ldd")
    eldd = Module(args.e90_rom / "ehwa.ldd")
    npdd = Module(args.n95_rom / "ehwaomap.pdd")
    epdd = Module(args.e90_rom / "ehwaomap.pdd")

    ldd = {
        "task2_raw_copy": compare(nldd, eldd, 0x801B4A98, 0x803F90D8, 100),
        "node_info_adapter": compare(nldd, eldd, 0x801B43B4, 0x803F89F4, 56),
        "record_constructor": compare(nldd, eldd, 0x801B56DC, 0x803F9D1C, 44),
    }
    if not all(item["bytes_equal"] for item in ldd.values()):
        raise ValueError("documented LDD get-info paths differ")

    first, second, size = 0x801A11B8, 0x803E57F8, 92
    a, b = npdd.read(first, size), epdd.read(second, size)
    differences = [offset for offset in range(0, size, 4)
                   if a[offset:offset + 4] != b[offset:offset + 4]]
    if differences != [20]:
        raise ValueError("PDD getter differs beyond the documented relocated call")
    targets = [arm_bl_target(address + 20, module.word(address + 20))
               for module, address in ((npdd, first), (epdd, second))]
    if targets != [0x801B2EC8, 0x803F7504]:
        raise ValueError("unexpected PDD getter call targets")
    if any(module.word(target) != 0xE51FF004
           for module, target in zip((npdd, epdd), targets)):
        raise ValueError("getter call targets are not the documented import stubs")
    tables = [(npdd, 0x801B3DE8, first), (epdd, 0x803F8424, second)]
    if any(module.word(table + 20) != getter for module, table, getter in tables):
        raise ValueError("DNode vtable slot20 does not identify the getter")
    getter = compare(npdd, epdd, first, second, size)
    getter.update({
        "different_arm_word_offsets": differences,
        "equal_except_relocated_bl": True,
        "call_targets": ["%08X" % target for target in targets],
        "import_stub_targets": ["%08X" % module.word(target + 4)
                                for module, target in zip((npdd, epdd), targets)],
        "vtable_starts": ["%08X" % table for _, table, _ in tables],
        "vtable_byte_slot": 20,
    })
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Static firmware comparison; no DSP RUN or hardware get-info",
        "rom_sha256": {"n95_ldd": sha256(nldd.data), "e90_ldd": sha256(eldd.data),
                       "n95_pdd": sha256(npdd.data), "e90_pdd": sha256(epdd.data)},
        "ldd": ldd, "pdd_node_info_getter": getter,
        "record": {
            "bytes_including_header": 112, "header": "30000068", "maximum": 104,
            "payload_offsets": {"property112": 52, "inputs": 56, "outputs": 60,
                                "node_env": 64},
            "node_env_load_store_n95": "801A11F0-801A11F4",
            "node_env_load_store_e90": "803E5830-803E5834",
            "property112_units": "unknown",
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
