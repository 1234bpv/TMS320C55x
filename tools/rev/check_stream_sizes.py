"""Check size-bearing native instructions; publish no extracted ROM code."""
import argparse
import datetime
import json
from pathlib import Path

from compare_node_info import Module, compare, sha256
from paths import ROM


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--n95-rom', type=Path, default=Path(ROM))
    p.add_argument('--e90-rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('report already exists')
    n = Module(a.n95_rom / 'ehwaomap.pdd')
    e = Module(a.e90_rom / 'ehwaomap.pdd')
    nb = Module(a.n95_rom / 'bridgeapi.dll')
    eb = Module(a.e90_rom / 'bridgeapi.dll')
    ranges = {}
    for name, first, second, size in (
        ('attributes_to_rms_stream_definition', 0x8019FE38, 0x803E4478, 52),
        ('input_properties_offset184', 0x8019FFA4, 0x803E45E4, 16),
        ('output_properties_offset1592', 0x801A00D4, 0x803E4714, 20),
        ('input_descriptor_length_to_request', 0x801A1B6C, 0x803E61AC, 16),
        ('output_descriptor_length_to_request', 0x801A1954, 0x803E5F94, 16),
    ):
        ranges[name] = compare(n, e, first, second, size)
        if not ranges[name]['bytes_equal']:
            raise RuntimeError('size-bearing native range differs: ' + name)
    # attr+4 -> RMS size+0; the remaining fields are reordered, not scaled.
    for offset, opcode in ((8, 0xE5910004), (12, 0xE5820000),
                           (16, 0xE5910008), (20, 0xE5820004)):
        if n.word(0x8019FE38 + offset) != opcode:
            raise RuntimeError('unexpected native RMS field mapping')
    delta = (0x803FAEF3 - 0x80A5E483) & 0xffffffff
    ranges['allocation_modes_positive_page_multiple'] = compare(
        nb, eb, 0x80A5D8B8, (0x80A5D8B8 + delta) & 0xffffffff, 20)
    if not ranges['allocation_modes_positive_page_multiple']['bytes_equal']:
        raise RuntimeError('native allocation size checks differ')
    if int.from_bytes(nb.read(0x80A5D8C8, 2), 'little') != 0x0520:
        raise RuntimeError('native allocation no longer checks low 12 bits')
    report = {
        'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Static size-bearing instructions on both ROMs; hardware sizes must be tested separately',
        'module_sha256': {'n95_pdd': sha256(n.data), 'e90_pdd': sha256(e.data),
                          'n95_bridge': sha256(nb.data), 'e90_bridge': sha256(eb.data)},
        'ranges': ranges,
        'properties_offsets': {'input': 184, 'output': 1592},
        'attributes_size_offset': 4, 'rms_stream_size_offset': 0,
        'rms_stream_size_units': 'C55 16-bit words; existing 256-word/512-byte hardware proof',
        'transfer_descriptor_length_units': 'ARM bytes, forwarded without a fixed 512-byte constant in these ranges',
        'native_allocation': {'modes': [1, 2], 'positive_bytes': True,
                              'bytes_multiple': 4096, 'prototype_capacity_bytes': 4096},
        'prototype_packet_limits': {'min_bytes': 512, 'max_bytes': 4096, 'even_bytes': True},
        'dcd_changed': False,
        'limits': ['These ranges do not establish the maximum driver or DSP allocator capacity.',
                   'Prototype bounds preserve at least 240 Q15 input values plus a 32-byte header.',
                   'Neither a hardware transfer nor negative lifecycle safety is inferred.'],
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('VERIFIED ' + str(a.out))


if __name__ == '__main__':
    main()
