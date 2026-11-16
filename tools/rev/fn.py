"""Disassemble one function of a ROM module in Thumb, and annotate call targets.

Usage: python fn.py <module> <hex-addr> [bytes] [thumb|arm]

Call targets are resolved against a table of known bridgeapi ordinals so a
client's call sequence reads directly as "ord N".
"""
import struct, subprocess, sys, os, re, tempfile

from paths import ROM, OD
HDR = 120

BRIDGEAPI = [
    0x80A5E483, 0x80A5E539, 0x80A5E68F, 0x80A5E6BB, 0x80A5E561, 0x80A5E585,
    0x80A5E677, 0x80A5E4DF, 0x80A5E43F, 0x80A5E409, 0x80A5E401, 0x80A5E401,
    0x80A5E433, 0x80A5E433, 0x80A5DC71, 0x80A5DC37, 0x80A5DCDB, 0x80A5DCA1,
    0x80A5DD0B, 0x80A5DD1B, 0x80A5DC2D, 0x80A5DC2D, 0x80A5DC35, 0x80A5DC35,
    0x80A5DAE1, 0x80A5D533, 0x80A5D9B1, 0x80A5DAC3, 0x80A5D901, 0x80A5D87F,
    0x80A5D9ED, 0x80A5D751, 0x80A5D4FD, 0x80A5DAA3, 0x80A5D955, 0x80A5D4C9,
    0x80A5D4C9, 0x80A5D4D9, 0x80A5D4D9,
]
ORD = {}
for i, a in enumerate(BRIDGEAPI):
    ORD.setdefault(a & ~1, []).append(i + 1)


def main():
    mod, addr = sys.argv[1], int(sys.argv[2], 16)
    length = int(sys.argv[3]) if len(sys.argv) > 3 else 220
    mode = sys.argv[4] if len(sys.argv) > 4 else 'thumb'
    if mode not in ('thumb', 'arm'):
        raise SystemExit('mode must be thumb or arm')
    b = open(ROM + mod, 'rb').read()
    ca = struct.unpack_from('<I', b, 0x14)[0]
    code = b[HDR:]
    start = addr & ~1
    with tempfile.TemporaryDirectory(prefix='c55x_disasm_') as directory:
        binary = os.path.join(directory, 'module.bin')
        with open(binary, 'wb') as output:
            output.write(code)
        result = subprocess.run(
            [OD, '-D', '-b', 'binary', '-m', 'arm'] +
            (['-Mforce-thumb'] if mode == 'thumb' else []) + [
             '--adjust-vma=0x%X' % ca,
             '--start-address=0x%X' % start,
             '--stop-address=0x%X' % (start + length), binary],
            capture_output=True, text=True, timeout=30, check=True)
        out = result.stdout
    for line in out.splitlines():
        m = re.search(r'\b(80[0-9a-f]{6})\b\s*$', line)
        note = ''
        if m:
            t = int(m.group(1), 16) & ~1
            if t in ORD:
                note = '   <<< bridgeapi ord %s' % ORD[t]
        # literal loads: objdump prints "(0x....)" for pc-relative
        print(line + note)


main()
