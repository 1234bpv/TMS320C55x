import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("xr", os.path.join(os.path.dirname(os.path.abspath(__file__)), "xref.py"))
from paths import ROM
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
    ORD.setdefault(a, []).append(i+1)
mod = sys.argv[1]
b = open(ROM+mod,'rb').read()
ca = struct.unpack_from('<I', b, 20)[0]
code = b[HDR:]
n = len(code)
hits=[]
for off in range(0, n-3, 4):
    v = struct.unpack_from('<I', code, off)[0]
    t = v & ~1
    if t in ORD: hits.append((ca+off,'lit',t))
for off in range(0, n-3, 2):
    h1,h2 = struct.unpack_from('<HH', code, off)
    if (h1 & 0xF800)!=0xF000: continue
    if (h2 & 0xF800) not in (0xF800,0xE800): continue
    hi = h1 & 0x7FF
    if hi & 0x400: hi -= 0x800
    t = (ca+off+4+(hi<<12)+((h2&0x7FF)<<1)) & 0xFFFFFFFF
    if (h2 & 0xF800)==0xE800: t &= ~3
    if t in ORD: hits.append((ca+off,'thbl',t))
for va,k,t in sorted(set(hits)):
    print('%08x %-5s -> %08x  ord %s' % (va,k,t,ORD[t]))
