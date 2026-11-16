"""Disassemble a ROM module in Thumb with every import call named.

Pieces:
  * ROM export tables give {code address -> ordinal} for the callee modules.
  * The SDK's .dso import libraries give {ordinal -> mangled C++ name}
    (a .dso symbol's st_value is (ordinal-1)*4).
  * The caller's import stubs are 8-byte ARM thunks `ldr pc,[pc,#-4]; .word t`,
    so a Thumb `blx <stub>` resolves to a named API.

Result: bridgeapi's methods read as ordinary Symbian code instead of raw calls.
"""
import glob, os, re, struct, subprocess, sys

from paths import ROM, SDKLIB, TC
OD = TC + "arm-none-symbianelf-objdump.exe"
RE_ = TC + "arm-none-symbianelf-readelf.exe"
HDR = 120
STUB = 0xE51FF004
HERE = os.path.dirname(os.path.abspath(__file__))


def rom_hdr(mod):
    b = open(ROM + mod, 'rb').read()
    return b, struct.unpack_from('<I', b, 0x14)[0]


def rom_exports(mod):
    """{code addr (thumb bit stripped) -> ordinal}"""
    try:
        b, ca = rom_hdr(mod)
    except OSError:
        return {}
    cnt = struct.unpack_from('<I', b, 0x3C)[0]
    dirv = struct.unpack_from('<I', b, 0x40)[0]
    off = dirv - ca + HDR
    out = {}
    for i in range(cnt):
        if off + 4 * i + 4 > len(b):
            break
        a = struct.unpack_from('<I', b, off + 4 * i)[0]
        out.setdefault(a & ~1, i + 1)
    return out


def dso_names(dllbase):
    """{ordinal -> mangled name} from the SDK import library"""
    cands = glob.glob(SDKLIB + dllbase + '.dso') + \
            glob.glob(SDKLIB + dllbase + '{*}.dso')
    if not cands:
        return {}
    out = {}
    txt = subprocess.run([RE_, '-s', cands[0]], capture_output=True,
                         text=True).stdout
    for line in txt.splitlines():
        m = re.match(r'\s*\d+:\s+([0-9a-f]{8})\s+\d+\s+FUNC\s+\S+\s+\S+\s+\S+\s+(\S+)',
                     line)
        if m:
            val = int(m.group(1), 16)
            name = m.group(2).split('@@')[0]
            out[val // 4 + 1] = name
    return out


def module_map():
    """[(name, lo, hi)] for every ROM module, to attribute a target address"""
    mods = []
    for p in glob.glob(ROM + '*'):
        try:
            b = open(p, 'rb').read()
            if len(b) < 128:
                continue
            if struct.unpack_from('<I', b, 0)[0] not in (0x10000079, 0x1000007A):
                continue
            ca = struct.unpack_from('<I', b, 0x14)[0]
            cs = struct.unpack_from('<I', b, 0x1C)[0]
            if ca < 0x80000000 or not (0 < cs < 4000000):
                continue
            mods.append((os.path.basename(p), ca, ca + cs))
        except OSError:
            pass
    return mods


def stub_table(mod, mods):
    """{stub addr -> 'module::name'}"""
    b, ca = rom_hdr(mod)
    code = b[HDR:]
    cache = {}
    out = {}
    for off in range(0, len(code) - 8, 4):
        if struct.unpack_from('<I', code, off)[0] != STUB:
            continue
        tgt = struct.unpack_from('<I', code, off + 4)[0]
        owner = next((m for m in mods if m[1] <= tgt < m[2]), None)
        label = '??? 0x%08X' % tgt
        if owner:
            name, lo, _ = owner
            base = os.path.splitext(name)[0]
            if base not in cache:
                cache[base] = (rom_exports(name), dso_names(base))
            exps, names = cache[base]
            o = exps.get(tgt & ~1)
            if o:
                label = '%s::ord%d %s' % (base, o, names.get(o, ''))
            else:
                label = '%s+0x%X' % (base, tgt - lo)
        out[ca + off] = label
    return out


def main():
    mod, addr = sys.argv[1], int(sys.argv[2], 16)
    length = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    mods = module_map()
    stubs = stub_table(mod, mods)
    selfexp = rom_exports(mod)
    b, ca = rom_hdr(mod)
    tmp = os.path.join(HERE, '_an.bin')
    open(tmp, 'wb').write(b[HDR:])
    start = addr & ~1
    txt = subprocess.run(
        [OD, '-D', '-b', 'binary', '-m', 'arm', '-Mforce-thumb',
         '--adjust-vma=0x%X' % ca, '--start-address=0x%X' % start,
         '--stop-address=0x%X' % (start + length), tmp],
        capture_output=True, text=True).stdout
    for line in txt.splitlines():
        note = ''
        # The address column also matches, so take the LAST hex word on the
        # line - that is the branch target objdump printed.
        hits = re.findall(r'\b(?:0x)?(80[0-9a-f]{6})\b', line)
        m = len(hits) > 1 and ('bl' in line or 'b.n' in line or 'b.w' in line)
        if m:
            t = int(hits[-1], 16)
            for cand in (t, t & ~3, t & ~1):
                if cand in stubs:
                    note = '   ; ' + stubs[cand]
                    break
            else:
                if (t & ~1) in selfexp:
                    note = '   ; SELF ord%d' % selfexp[t & ~1]
        print(line + note)


main()
