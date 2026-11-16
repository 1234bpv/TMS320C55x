"""Mark a DOFF file as "executable" so PROC_Load (bridgeapi ord26) accepts it.

Why this exists
---------------
ord26 loads a file onto the DSP as a *processor image*. On the device it
happily loads `baseimage.dof` and kills the kernel outright on every dynamic
node we tried - ours, the stock `pingdyn.dll55l`, and even a stub with no
downloadable sections at all. The one header difference between the file that
works and the files that crash (findings 18.10):

    baseimage.dof   flags 0x12e3   entry point 0x000273bb
    every node      flags 0x12e0   entry point 0

So the loader distinguishes an executable image from a relocatable one by the
low two flag bits, and feeding it a relocatable one is what kills the kernel.

This script flips those two bits and plants an entry point, then repairs the
header checksum. The rule is verified on four real files: the nine header
words sum to 0xFFFFFFFF, i.e. checksum = ~(sum of the eight preceding words).

Header layout (offsets, all little-endian 32-bit unless noted):
    +0x00 strtab_size          +0x14 {u16 no_scns, u16 target_scns}
    +0x04 entrypt              +0x18 {u16 doff_version, u16 target_id}
    +0x08 byte_order           +0x1c {u16 flags, u16 entry_secn}
    +0x0c scn_name_size        +0x20 checksum
    +0x10 {u16 no_syms, u16 max_str_len}

The entry point defaults to the base image's own entry: if anything ever does
jump there it lands in real, loaded base-image code rather than nowhere.

Only meaningful for a file with no allocated sections - otherwise the loader
would write those sections into DSP memory at their link addresses and stomp
on the base image.
"""
import struct
import sys

HDR_WORDS = 9
OFF_ENTRY = 0x04
OFF_FLAGS = 0x1C
OFF_CKSUM = 0x20

BASE_ENTRY = 0x000273BB          # entry point of baseimage.dof
EXEC_FLAGS = 0x12E3              # base image has 0x12e3, nodes have 0x12e0
EXEC_ENTRY_SECN = 0xFFFF         # base image marks the entry as absolute


def checksum(words):
    """checksum = ~(sum of the eight words before it)"""
    return (~sum(words[:8])) & 0xFFFFFFFF


def main():
    src, dst = sys.argv[1], sys.argv[2]
    d = bytearray(open(src, 'rb').read())
    words = list(struct.unpack_from('<9I', d, 0))

    if checksum(words) != words[8]:
        raise SystemExit('refusing to patch: source header checksum is already '
                         'wrong (%08x != %08x)' % (words[8], checksum(words)))

    struct.pack_into('<I', d, OFF_ENTRY, BASE_ENTRY)
    struct.pack_into('<I', d, OFF_FLAGS,
                     EXEC_FLAGS | (EXEC_ENTRY_SECN << 16))
    words = list(struct.unpack_from('<9I', d, 0))
    words[8] = checksum(words)
    struct.pack_into('<I', d, OFF_CKSUM, words[8])

    open(dst, 'wb').write(bytes(d))
    print('%s -> %s' % (src, dst))
    print('  entry point  0x%08x' % BASE_ENTRY)
    print('  flags/secn   0x%08x' % (EXEC_FLAGS | (EXEC_ENTRY_SECN << 16)))
    print('  checksum     0x%08x (header words now sum to 0xFFFFFFFF)'
          % words[8])


main()
