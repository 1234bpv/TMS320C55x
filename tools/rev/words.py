"""ROM word inspection and aligned literal xrefs (static evidence only)."""
import argparse
import struct
from pathlib import Path
from paths import ROM

p = argparse.ArgumentParser()
p.add_argument('module')
p.add_argument('address', type=lambda s: int(s, 16))
p.add_argument('--count', type=int, default=16)
p.add_argument('--xref', action='store_true')
args = p.parse_args()
b = (Path(ROM) / args.module).read_bytes()
base, size = struct.unpack_from('<II', b, 20)[0], struct.unpack_from('<I', b, 28)[0]
print(f'{args.module}: code={base:08x} code_size={size} file_size={len(b)}')
if args.xref:
    for off in range(120, len(b)-3, 4):
        word = struct.unpack_from('<I', b, off)[0]
        if word == args.address:
            print(f'literal @{base+off-120:08x} file_offset={off:x}')
else:
    start = args.address - base + 120
    if start < 120 or start + args.count*4 > len(b):
        raise SystemExit('requested address is outside file-backed module')
    for off in range(start, start + args.count*4, 4):
        print(f'{base+off-120:08x}: {struct.unpack_from("<I",b,off)[0]:08x}')
