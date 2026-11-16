# ARM MSG: memory reads and the origin of pointers

This continuation recovered the result of an unfinished earlier run:
host29 was already installed on the E90, and `patcher-read-check` finished
successfully. The saved journal was re-fetched before any writes: SHA-256
56167F767D4B30FF225DA24BFB0F6666FD25F16B9FB22B1398D4DBB911195D76,
PS c55stream/ocprobe0, daemon startTick61087 unchanged.
This diagnostic was not run again.

## What was proven

Control105 copies 24 bytes from an address into a TPtrC8 buffer of our
process. Three sources were checked: our own RAM, the ROM code of
reader803F7664, and the 24-byte BSS of the PDD at C8010B20. The first two
gave exactly the six expected ARM instructions. The third gave
DWORD0/1/1/0/0/1. FINAL/EXIT0; the DSP processor was not opened, and kernel
code and PRCM were not changed.

This proves a read primitive for the kernel RAM. **C8010B20 is not the
address of the MSG context or the reader.** The static code uses the first
word as a zero/nonzero flag. Reading these six words does not measure
reader byte64, the address of the shared window, or message routing.

## The verified static chain

`tools/rev/audit_arm_message_runtime.py` checks 28 instructions, two BL
targets, the ROM header BSS address/size and the full reader body. It
publishes the addresses, fields and SHA-256 hashes of the ranges; the ROM
stays local.

| Field | Origin |
|---|---|
| board+264 | Pointer to the context after the 364 B allocation and the constructor |
| context+48 | Common board, passed as board+8 |
| context+24 | Reader: common board+164, i.e. board+172 |
| reader byte64 | board byte236, written as 1 in setup |
| reader DWORD0 | ARM base of the shared memory; this is not yet the fromDSP header |
| context+224 | fromDSP header, computed from the shared base+16 and the layout offset |
| context+240 | Records: fromDSP header+8 |
| queue+16 | Source binding, without conversion in the setter |
| queue+40 | Pending receive; the consumer clears it after completion |

These are static contracts, not values of live objects. For the next
snapshot, one must first prove the live board/context root through an
audited native object lookup, the bounds of the allocation/mapping, and the
lifetime. A check of the numeric range of a kernel pointer alone is not
sufficient. The snapshot will be non-atomic; traversal of the queues must
have an explicit count limit.

## Restoration and checks

All five originals were restored on the E90: DLL/log/ocprobe.log/EXE/hash.
Each PUT was verified by a GET, and the final verify showed all five SHA
equal, host20 and PS0. The N95 was not polled in this continuation; its last
proven state remains restored host20/PS0 from the previous checkpoint.
There are no new MSG/RUN/KILL; D0 own 0/3, historical experimental RUN 5,
D1 pending, D2 provisional. No reboot or other physical action is needed.

The validator now checks the exact ROM words, source addresses, size, order
and the shared destination of the three copies, the firmware
identity/profile, FINAL0, and the absence of a DSP open. Nine offline tests
pass, including the rejection of damaged or incomplete read-copy proofs. The
current ARM host29 was not rebuilt: its source/EXE exact hashes and the
successful bounded build are kept in artifact38.

Evidence: [current checkpoint](evidence/2026-10-02/arm-message-runtime-checkpoint.json),
[static audit](evidence/2026-10-02/e90-arm-message-pointer-audit.json),
[read-copy journal](evidence/2026-10-02/e90-pointer-readcheck01.txt),
[restoration](evidence/2026-10-02/e90-pointer-resume-finalverify01.json).
Reproducible publication: `tools/summarize_arm_message_runtime.py`; it
requires the saved session/ROM files and does not contact the phones.
