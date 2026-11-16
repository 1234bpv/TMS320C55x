"""Verify the known N95 stock performance reservation contract without calls.

Raw ROM bytes remain local. E90 has no corresponding driver in this profile.
"""
import datetime
import json
from pathlib import Path

from compare_node_info import Module, arm_bl_target, sha256
from paths import ROM


def fingerprint(data):
    value = 2166136261
    for offset in range(0, len(data), 4):
        value = ((value ^ int.from_bytes(data[offset:offset+4], "little")) * 16777619) & 0xffffffff
    return value


def main():
    module = Module(Path(ROM) / "dvfs_interface.ldd")
    ranges = ((0x80148410, 6, 0x75736a35, "stock percent getter"),
              (0x80148460, 56, 0x8c9deac3, "reserve/release and request completion"),
              (0x80148638, 24, 0x4c360a14, "request0 argument dispatch"),
              (0x80148334, 28, 0x4584a74d, "channel destructor and client removal"))
    proof = []
    for address, words, expected, purpose in ranges:
        data = module.read(address, words * 4)
        if fingerprint(data) != expected:
            raise ValueError("unexpected native performance range")
        proof.append({"address": "%08X" % address, "words": words,
                      "fnv32_words": "%08X" % expected, "sha256": sha256(data),
                      "purpose": purpose})
    instructions = {0x80148464: 0xe3520032, 0x8014849c: 0xe3a00042,
                    0x801484f4: 0xe3a00042, 0x8014852c: 0xe3a02000,
                    0x8014863c: 0xe3510000, 0x80148644: 0xe59d6018,
                    0x80148660: 0xe1a02006, 0x8014835c: 0xe3a00042,
                    0x801485f4: 3300000}
    if any(module.word(address) != word for address, word in instructions.items()):
        raise ValueError("native operation contract changed")
    for address, target in ((0x8014866c, 0x80148460), (0x80148534, 0x80148840),
                            (0x801484a0, 0x80148948), (0x801484f8, 0x80148940),
                            (0x80148360, 0x80148938)):
        if arm_bl_target(address, module.word(address)) != target:
            raise ValueError("unexpected native call target")
    print(json.dumps({
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": "n95", "machine_uid": "20002D84",
        "scope": "Static ROM contract; no reservation or phone call performed",
        "driver_sha256": sha256(module.data), "ranges": proof,
        "request": {"number": 0, "decision_argument": "a2", "reserve_value": 100,
                    "release_value": 0, "threshold": 50, "resource": 66,
                    "status_completed_by": "native call80148840 with result0; native method returns wait result"},
        "getter": {"control": 1, "clock_domain": "MPU", "divisor": 3300000,
                   "unit": "integer percent of nominal MPU frequency"},
        "lifecycle": "client count increments/decrements; destructor removes remaining client reservation",
        "limits": ["No arbitrary frequency or PRCM write is exposed by this API.",
                   "MPU percent alone does not measure every DSP/bus clock.",
                   "E90 must not use these N95 addresses or this channel."],
    }, indent=2))


if __name__ == "__main__":
    main()
