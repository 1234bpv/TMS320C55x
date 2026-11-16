# MSG delivery and completion of a finite worker — 2026-10-02

A later continuation: the host29 read-copy diagnostic and the static pointer
audit are described in [ARM_MESSAGE_RUNTIME](ARM_MESSAGE_RUNTIME_2026-10-02.md).
There were no new MSG/RUN; the E90 was again fully restored to host20/PS0.
This document remains the report on the four earlier finite MSG diagnostics.

After the reboot of the E90 confirmed by the user, the old journal was
fetched before any writes: 2092 B, SHA-256
B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92.
PS0, new daemon startTick61087; the three initial files were returned
GET-equal. The user allowed tests on the N95 as well; its initial five files
were saved before the host was replaced.

## Result

A single final STRM input releases the BIOS worker into the CREATED state.
The worker calls NODE_putMsg606/A1B2C3D4/env, returns the STRM snapshot,
idle/reclaim, and finishes. The ARM checks the snapshot and calls the
created delete/join. There is no official RUN and no wrapper EXITACK in
these experiments.

| Phone / host | ARM receive | DSP put / STRM output | ARM MSG | delete/free/close |
|---|---|---|---|---|
| E90 / 26 | Before input | 1 / correct snapshot | −33, pending | Successful |
| E90 / 27 | After output | 1 / correct snapshot | −33, buffer empty | Successful |
| E90 / 27 | Before input, raw logging added | 1 / correct snapshot | −33, buffer empty | Successful |
| N95 / 28 | Before input | 1 / correct snapshot | −33, buffer empty | Successful |

FINAL/EXIT in all four cases were −33 via MSG receive; these are **not
successful D0 cycles**. However, delete=0/status 0, state DELETED 5, free
task/native buffers 0 and close are confirmed. The pending receive was
released before close; there is no QUARANTINE. The no-input cleanup, which
hung earlier, was not repeated and not fixed.

Stage 7 confirms cmd606/arg1A1B2C3D4/arg2env77E0 and the raw source77E0.
DSP queue count 0, fromDSP header 0/0/1 during the snapshot, and empty_after 1.
The snapshot is not atomic. The change in empty is consistent with the work
of the ARM consumer, but on its own does not prove IRQ/DFC, the actual ARM
word order, or the chosen queue. The failure repeats on both phones; the
exact cause has not yet been established.

## Clock rates and restoration

E90: the stock profile was read: ARM 330.24 / bus 110.08 / DSP 220.16 MHz.
N95: the existing overclock m111, PLL0006F400/sel2=2/MPU2/core04360844/DSP23C3;
by the registers ARM 426.24 / bus 213.12 / DSP 284.16 MHz. The old ocprobe
text "firmware math CORE660480" uses the stock reference and is not the actual
N95 clock in this session. The first N95 preparation with the stock guard
refused before DSP START; the next one explicitly checked the exact existing
m111 profile. There are no PRCM writes. This is a snapshot of the clock rates
before the test, not a check of DVFS on each packet, and not a performance
benchmark.

After the tests on **both** phones, DLL/log/ocprobe.log/EXE/hash were
returned; all five GET/SHA-256 values match the originals. On both, the
initial host20 is installed; the local diagnostic build is host28/protocol26.
The final c55stream/ocprobe PS0, startTick E9061087/N9522918156 are unchanged.
There are no new RUN/KILL/reboot in these tests; the total historical count
of experimental RUN remains 5, D0 own 0/3. D1 was not run, and D2 remains at
its previous status.

Evidence: [checkpoint](evidence/2026-10-02/worker-message-checkpoint.json),
[E90 before input](evidence/2026-10-02/e90-laptop-worker-prearmed27-worker-message.txt),
[E90 after output](evidence/2026-10-02/e90-laptop-worker-queued01-worker-message-queued.txt),
[N95](evidence/2026-10-02/n95-worker-msg02-worker-message.txt).
Reproducible publication: tools/summarize_worker_messages.py;
source/import/DOFF hashes — artifacts35/37 in evidence/2026-10-01.

## Next check

Before a new MSG/RUN, an audit of a bounded read-only ARM snapshot is
needed: the actual shared-window address and DWORD, reader byte64, queue
source16, pending receive40 and the consumer count. This will separate
mapping/word order, the choice of queue, and completion. The PDD addresses
and offsets known from the static code do not yet give a safe runtime
pointer: first trace its origin and the read bounds. Do not patch the reader,
and do not force IRQ/DFC on an assumption. Three E90 variants have already
been checked; the same receive must not be repeated without a new proven
hypothesis. No physical actions are needed now.
