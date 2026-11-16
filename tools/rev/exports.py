"""Dump the export table of a ROM (XIP) module.

TRomImageHeader is 120 bytes; the fields we need are iCodeAddress (+0x14),
iCodeSize (+0x1C), iExportDirCount (+0x3C) and iExportDir (+0x40). The export
directory is an array of 32-bit code addresses, ordinal 1 first.
"""
import struct, sys

from paths import ROM
HDR = 120


def dump(mod):
    b = open(ROM + mod, 'rb').read()
    ca = struct.unpack_from('<I', b, 0x14)[0]
    cnt = struct.unpack_from('<I', b, 0x3C)[0]
    dirv = struct.unpack_from('<I', b, 0x40)[0]
    print('#### %s code=0x%08X exports=%d dir=0x%08X' % (mod, ca, cnt, dirv))
    off = dirv - ca + HDR
    out = []
    for i in range(cnt):
        a = struct.unpack_from('<I', b, off + 4 * i)[0]
        out.append((i + 1, a))
    # group aliased addresses
    seen = {}
    for o, a in out:
        seen.setdefault(a, []).append(o)
    for o, a in out:
        tag = '  <alias of %s>' % seen[a] if len(seen[a]) > 1 else ''
        print('  ord %2d -> 0x%08X%s' % (o, a, tag))
    return out


for m in sys.argv[1:]:
    dump(m)
    print()
