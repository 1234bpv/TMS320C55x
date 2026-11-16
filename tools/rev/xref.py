"""Find XIP callers of a target address range across the ROM's sys/bin.

In an XIP ROM there are no import stubs for inter-DLL calls: the ROM builder
patches the call sites to the final address. So a client of bridgeapi.dll shows
up as either a direct BL/BLX to an export, or a 32-bit literal holding the
export address (with the Thumb bit) that is later used with BLX rN.

Both encodings are decoded here. ARM and Thumb code coexist in these modules,
so every 4-byte and 2-byte alignment is tried; false positives are filtered by
requiring the target to be one of the known export addresses.
"""
import os, struct, sys, glob

from paths import ROM
HDR = 120


def load(path):
    b = open(path, 'rb').read()
    if len(b) < 128:
        return None
    uid1 = struct.unpack_from('<I', b, 0)[0]
    if uid1 not in (0x10000079, 0x1000007A):
        return None
    ca = struct.unpack_from('<I', b, 20)[0]
    cs = struct.unpack_from('<I', b, 28)[0]
    if ca < 0x80000000 or not (0 < cs < 4000000):
        return None
    return ca, b[HDR:]


def scan(code, base, targets):
    """yield (offset_va, target, kind)"""
    n = len(code)
    # 32-bit literals
    for off in range(0, n - 3, 4):
        v = struct.unpack_from('<I', code, off)[0]
        t = v & ~1
        if t in targets:
            yield base + off, t, 'lit'
    # ARM BL / BLX(imm)
    for off in range(0, n - 3, 4):
        w = struct.unpack_from('<I', code, off)[0]
        cond, op = w >> 28, (w >> 25) & 7
        if op != 5:
            continue
        imm = w & 0xFFFFFF
        if imm & 0x800000:
            imm -= 0x1000000
        tgt = (base + off + 8 + imm * 4) & 0xFFFFFFFF
        if cond == 0xF:                      # BLX(imm): H bit adds 2
            tgt = (tgt + ((w >> 23) & 2)) & ~1
        if (w >> 24) & 1 or cond == 0xF:     # link bit
            if tgt in targets:
                yield base + off, tgt, 'armbl'
    # Thumb BL / BLX pairs
    for off in range(0, n - 3, 2):
        h1, h2 = struct.unpack_from('<HH', code, off)
        if (h1 & 0xF800) != 0xF000:
            continue
        if (h2 & 0xF800) not in (0xF800, 0xE800):
            continue
        hi = h1 & 0x7FF
        if hi & 0x400:
            hi -= 0x800
        tgt = (base + off + 4 + (hi << 12) + ((h2 & 0x7FF) << 1)) & 0xFFFFFFFF
        if (h2 & 0xF800) == 0xE800:
            tgt &= ~3
        if tgt in targets:
            yield base + off, tgt, 'thbl'


def main():
    tgt_lo, tgt_hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
    self_name = sys.argv[3] if len(sys.argv) > 3 else None
    targets = set(range(tgt_lo, tgt_hi, 2))
    for path in sorted(glob.glob(ROM + '*')):
        name = os.path.basename(path)
        if self_name and name.lower() == self_name.lower():
            continue
        r = load(path)
        if not r:
            continue
        ca, code = r
        hits = sorted(set(scan(code, ca, targets)))
        if hits:
            print('#### %s (code 0x%08X)  %d hits' % (name, ca, len(hits)))
            for va, t, kind in hits:
                print('   %08x %-6s -> %08x' % (va, kind, t))


main()
