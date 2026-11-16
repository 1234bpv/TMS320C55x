"""Extract named XIP files from a bounded live-ROM window.

TRomEntry layout is from S60_3rd_FP1/Epoc32/include/e32rom.h:
size/address/attributes/nameLength/UTF-16 name. No guessed file addresses.
Usage: extract_xip.py window.bin 80000000 output-dir module [...]
"""
import hashlib
import struct
import sys
from pathlib import Path

source, base, destination, *names = sys.argv[1:]
base = int(base, 16)
data = Path(source).read_bytes()
output = Path(destination)
output.mkdir(parents=True, exist_ok=True)
for name in names:
    needle = name.encode('utf-16-le')
    matches = []
    position = 0
    while True:
        position = data.find(needle, position)
        if position < 0:
            break
        if position >= 10:
            size, address, attributes, length = struct.unpack_from('<IIBB', data, position - 10)
            start = address - base
            if length == len(name) and attributes & 0x80 and 0 <= start <= len(data) - size and size >= 120:
                image = data[start:start + size]
                uid, = struct.unpack_from('<I', image)
                code, = struct.unpack_from('<I', image, 20)
                if uid in (0x10000079, 0x1000007a) and address + 120 == code:
                    matches.append((address, image))
        position += 2
    if len(matches) != 1:
        raise SystemExit(f'{name}: expected one validated entry, found {len(matches)}')
    address, image = matches[0]
    (output / name).write_bytes(image)
    print(f'{name}: header={address:08x} bytes={len(image)} sha256={hashlib.sha256(image).hexdigest()}')
