# D0 and D1: E90 lifecycle and DMM

The evening continuation of 02.10 supersedes the checkpoint below: the E90
reboot has been performed, and the finite MSG was verified on E90/N95. The
created worker finished cleanly on both, but the ARM receive returned -33 and
the record is empty. Both are at host20/PS0, and all 5 originals were restored
with GET equality; no physical action is needed now. D0 own 0/3, and the
experimental RUN5 is unchanged. The evidence and the next runtime audit are in
[WORKER_MESSAGES](WORKER_MESSAGES_2026-10-02.md).

The current checkpoint of 02.10: after RUN5 the journal and PS0 were obtained,
and the original DLL/log/clocklog were restored exactly. Host26 direct deploy
verified. The created-worker MSG control stopped at the create-only preflight:
create 0/7598 us, delete -33/pending/state 1. The trigger, MSG606, and RUN did
not start; experimental RUN5 is unchanged, D0 own 0/3. Live GET 2092 B, hash
B9B4E282…, PS1/startTick 65704 unchanged at 15:21. HELP at 15:16 requests a
reboot/daemon. The DSP and log are now research26; clocklog original exact,
host26/hash research. D1 hardware pending, D2 provisional.

Static refinement of the ARM reader: the C55 board 803F0208 passes the common
base+8 into the context constructor 803E011C. The getter 803EEFCC adds 164, so
the reader is at board+172, and its byte 64 is at board+236. Init 803F0308 sets
r8=1, and 803F03C0 writes this byte. The IVA board has a different layout and
does not define the C55 flag. This is evidence of the initial store, not a live
runtime observation. The RMS create result 803E6E34–803E6E40 stores env at
node+44 and passes the same value through the queue setter 803F3A98→queue+16,
without a multiply or word swap. The native wrapper 24E6F0 and the MSG functions
have separate reproducible hashes in the
[native audit](evidence/2026-10-01/e90-d0-d1-native-audit.json).

The new diagnostic [artifact33](evidence/2026-10-01/d0-worker-message-v33-artifacts.json)
separates the outbound MSG from the execute return: the host pre-arms
receive/output in CREATED, one final input starts the finite worker, which
performs NODE_putMsg606/A1B2C3D4/env and snapshot 7/protocol 26, then
reclaim/idle/return; delete checks the terminated worker before releasing it.
The wrapper/EXITACK and the official RUN are absent, so a success would not
close D0. The first run mistakenly reused the create-only preflight of an active
worker, whose stop without input had not been proven by the earlier packet
tests. The script now skips only this preflight; cleanup without input remains
unresolved. After the reboot by the user, GET/PS0/restore is needed, followed by
one finite trigger diagnostic, not an unchanged repetition of the no-input
delete. The lower sections keep the earlier checkpoints.

After the continuation of 2026-10-01, **D0 is 0/3**. Host21 GET was confirmed.
Two different DSP candidates each ran RUN and produced 8 correct packets each,
but delete returned -2 and -33. Both host processes kept ownership through
QUARANTINE; there was no KILL. After reboots confirmed by the user, the journals
were retrieved up to START/PUT, and the original DLL/log/clocklog were restored
exactly. [Continuation evidence](evidence/2026-10-01/e90-d0-resume-checkpoint.json).
D1 remains static; this is not proof that zero-copy is impossible. The N95 was
not polled in this session.

Host22 with EFileShareAny was installed and GET 35120 B AFF498B8… was confirmed.
The third RUN passed 3 MSG snapshots: get(0)=0, put(0)=1, and the shared record
was correct, but message-get -2/state 3/delete -2. The live journal D29CDA12…
GET succeeded. After the reboot by the user, the DLL/log/clocklog were restored
exactly. The user lifted the limit of 3, on the condition of a new hypothesis
for each RUN. The ROM reference test on host23 stopped before RUN: DCD select
-6. Host24 was installed and GET confirmed: 12356F00…. A separate
properties/library2 parse had select -6 before RUN. The combined registry packet
passed select; RUN4 with native STRMCOPY code/data/relocations passed 8 exact
echoes of 512 B each, but delete -33/pending/state 3. The live GET of the
journal A33A433C… succeeded. The reboot by the user on 02.10 was confirmed;
after it, Python connect 3 s/8 s and .NET 8 s timed out before INFO. GET/PS0/
restore are still pending.

## Completion audit

Reproduction without the device: `python tools/rev/audit_e90_task.py`. Addresses,
lengths of the checked regions, and hashes are in the
[native audit](evidence/2026-10-01/e90-d0-d1-native-audit.json). Source: the
saved E90 ehwaomap.pdd, ehwa.ldd, and bridgeapi.dll. Raw ROMs and disassembly
remain local.

| E90 component | Established contract | Consequence for the host |
|---|---|---|
| PDD803E5AB4, RUN | Unload of create only under phase_split1/dynamic1 | The generic library2 keeps code/data between phases |
| PDD803E6DE8, RMS callback | A negative DSP status is reported as -2 | -2 does not confirm that the task has completed |
| PDD803E70B8, delete completion | The error skips success/env clear but moves to internal state 4 | State 4 itself does not prove a safe unload |
| LDD803F87FC, destructor | State 4 allows the PDD free; PDD803E6758 unloads the libraries | Close after a failed delete may free live code |
| LDD803F8AF4, cancel adapter | Task 15/17 passes the index as a value; the adapter returns 0 | A separate completed transfer status is required |
| PDD803E69B4, running delete | State 9, queue RMS_EXIT 80000000 from nodeEnv | Submit 0 does not prove the DSP receipt |
| PDD803DF7EC–803DF864, EXITACK | Waits for RMS_EOK 8000, checks the node, and dispatches the delete itself | An early return may race with hostCtl6; the cause of the specific failure is not proven |

Host21/22 does not perform delete/free/close for a pending create/RUN/transfer
after a cancel attempt. After a failed delete/free, or with a pending message,
it keeps the ownership of the resources and writes QUARANTINE. The supervisor
has a deadline of 30 s and tries a GET of the journal; the phone process does
not receive a KILL. Host21 held an exclusive RFile: a live GET returned -14.
Host22 uses EFileShareAny; a GET of the live QUARANTINE was confirmed by the
third RUN. This is retention until a manual reboot, **not a proven safe
cancel**. A synchronous control inside the kernel may block the phone; a local
timeout does not correct this.

DSP run-stop21: after stop/reclaim, an early return with 8000. Candidate22,
after the same packets, waits for RMS_EXIT before the return. A new input after
stop is not issued. There is no manual duplication of the ACK. The context is
explicitly zeroed; execute checks the context and buffers before access. State 3
does not prove a successful ACK: the native fault path also sets this state.

| Candidate / host | Before delete | Packets | Delete / status | FINAL / EXIT0 |
|---|---:|---:|---|---|
| run-stop21 /21 | state 3 | 8/8 correct | -2/-2 | none |
| run-stop22 /21 | state 2 | 8/8 correct | -33/pending | none |
| generic message-diag /22 | state 3 | 3/3 snapshots | -2/-2 | none |
| ROM STRMCOPY combined /24 | state 2 | 8/8 exact echoes | -33/pending, after state 3 | none |

Packet wall: 16 diagnostic observations, median 396 us, 366–488 us. This is not
an accepted D1 latency/bandwidth and not an application speedup. The first
reboot before these runs took place between the GET verification and the clock
connection; no new RUN occurred before it. The transport logs show four RUNs:
two own packet tests, the MSG diagnostic, and the ROM control. The separate
select -6 preflights are not RUNs. The ROM packet wall median is 488 us, range
457–579 us; this is a separate diagnostic sample, not an accepted D1 latency or
speedup.

In the third snapshot, fromDSP is empty 1/count 1; the raw record is
0000/0600/000F/0001/0000/77E0/0000/77E0, and ror16 gives
cmd600/arg1F0001/arg2/source77E0. This is DSP→shared window movement, not
evidence of an ARM IRQ/DFC, the actual reader endian flag, or EXITACK delivery.
State 3 after the execute return also does not establish a specific cause of
the fault.

## Build and the next diagnostic

Artifacts: [run-stop21](evidence/2026-10-01/d0-run-stop-v21-artifacts.json),
[run-stop22](evidence/2026-10-01/d0-run-stop-v22-artifacts.json),
[host22](evidence/2026-10-01/d0-livejournal-v22-artifacts.json),
[generic message diagnostic](evidence/2026-10-01/d0-message-diag-v24-artifacts.json).
The DOFF/import/ASM checks are static; they do not establish hardware success.
The last variant passes 3 STRM snapshots: before NODE_getMsg(0), after get,
after NODE_putMsg(0), including the message windows and the record source. This
third RUN was performed, and it does not count toward D0.

The subsequent hypothesis: ROM STRMCOPY with the same generic library2 is
expected to distinguish custom execute/return from the host/native lifecycle.
The ROM DLL has only properties0; an additional research copy changes the
registration :0→:2 and the checksum, while all instruction/data/relocation bytes
are unchanged. [Derivation proof](evidence/2026-10-01/e90-d0-native-library2-derivation.json),
[host24 proof](evidence/2026-10-01/d0-native-copy-host-v24-artifacts.json).
The host23 select -6 was a preflight, not a fourth RUN; the journals after it
were restored exactly without a reboot. Host24 parsed the ROM properties, then
the E library2. The separate parse did not resolve select; the combined
properties0/library2 did:
[combined proof](evidence/2026-10-01/e90-d0-native-library2-combined-derivation.json),
[same host24, control artifact](evidence/2026-10-01/d0-native-copy-host-v24-combined-artifacts.json).
All non-registration packets, including the DSP code/data/relocations, are
byte-for-byte unchanged; the metadata packet was enlarged, and the table
offsets/checksums were corrected. RUN4 ruled out its own execute as the only
explanation of the lifecycle failure; the specific cause in the host/setup/native
path has not yet been established. The control does not count as three clean
own-DSP cycles. A repetition without a new change is not planned. The next
diagnostic must separate the RMS_EXIT receipt, idle/reclaim, and native
return/EXITACK via STRM snapshots.

Historical command of an already executed probe; it must not be repeated:

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'python tools/e90_task_session.py --session work/evidence/e90/d0-20261001 --action d0-message-diagnostic --host-version 22 --artifact-proof docs/evidence/2026-10-01/d0-message-diag-v24-artifacts.json --tag message-diag01' -TimeoutSec 120 -Log out/d0-message-diag01.log
```

Fresh clocks, inspect, and clean create/delete were confirmed in the same socket
session. After the failure, the live journal was retrieved and the RUN stopped:
the limit of 3 had been exhausted before the user's later permission. The old
hypothesis must not be repeated. The original DLL/log/clocklog may be PUT only
after a confirmed completion or a reboot. After the cause is established, the
full D0 requires:

1. Three consecutive separate create/RUN 0 cycles, each with 8 ordered packets
   and a check of 240 payload words, stop, delete/free/native 0, FINAL 0, EXIT 0,
   a responsive INFO, and an unchanged daemon startTick.
2. Exact restore of the original DLL/log/clocklog, checked by GET/SHA256.
3. After the research: install the restore SIS from the exact original host20
   EXE, and check the EXE and the sys/hash by GET. The restore package number
   must exceed the last installed package 28; restore 29 is already prepared.
   The payload is not rebuilt.

The tool has a fixed E90 IP. The generic run_stream.py remains for the
historical v7–v20; its timeout also does not send a KILL. The separate variants
and the immutable local archives are kept; the normal PC DSP is rebuilt after
the diagnostic variant (bounded build EXIT 0).

## D1: static preparation

Update of 2026-10-03: the [reproducible native page-list/cache audit](DMM_ABI_2026-10-03.md)
compared N95/E90, confirmed the pairs `{linearPage, physicalPage}`, the exact
map signature, and the cache helper clean→invalidate. Pinning/lifetime, DSP
units, coherence, and all D1 hardware criteria remain unverified.

| bridgeapi.dll action | Ordinal | Control | E90 entry |
|---|---:|---|---|
| Reserve DSP range | 27 | 0400000F | 803FA420 |
| Map ARM buffer | 31 | 04000012 | 803FA45C |
| Unmap | 34 | 04000013 | 803FA512 |
| Unreserve | 28 | 04000010 | 803FA532 |

The map payload is 24 B: ARM virtual address, byte count, reserved DSP address,
flags, physical page-table pointer, page count. The wrapper works with 4096-B
pages. The native DSP-address units, MMU flags, and pinning/cache ABI are not
yet proven. No reserve/map/16 KiB transfer was called in this session.

The [TI reference audit](evidence/2026-10-01/e90-d0-dmm-ti-reference.json)
records archived primary samples, not the Nokia runtime: map flags virtual 0/
physical 1, big-endian 2, mixed 4, element 8/16/32/64 bits — 8/10/20/40 hex.
The sample for DSPTYPE_55 divides the returned byte address and byte length by
2, flushes the ARM input before the work, and invalidates the output after
completion. The units and flag bits still have to be confirmed on E90; the
sample cannot be carried over as a proven firmware ABI. Its notify also depends
on the NODE message path, which is not currently accepted in D0.

Probe after D0: confirm the allocation/alignment/cache ABI, reserve/map one
region, and check sentinels at the 16-bit/32-bit/4 KiB boundaries in both
directions; then unmap/unreserve/free without pending ownership. The Ring16KiB
is a shared region. Producer/consumer indices, slot ownership, sequence/length,
ordering/cache, wraparound, and notify are required. Wire format: explicit
16-bit fields; on C55, char/int/short are 16 bits, long is 32 bits, and pointer
is 23 bits.

Measurement: three series of several sizes, all repetitions byte-equal, ARM
FastCounter Hz and p50/p95/p99/max, with submit CPU/wall/bytes/s reported
separately. Do not use CLK_countspms164. A negative DMM result requires an exact
native error, proven by the ABI and a clean teardown; it is not a blocker for D0.

## Originals and physical dependency

The [initial checkpoint](evidence/2026-10-01/e90-d0-session-checkpoint.json) at
19:02 UTC established all 5 original files, host20/hash, and PS0. The
continuation above confirmed host21 and fresh clock probes: m86/div3, ARM
330.24 MHz/bus 110.08 MHz/DSP 220.16 MHz, without PRCM writes.

After the second reboot at 19:58 UTC, PS0/startTick 60875; the DLL/log/clocklog
were restored exactly. The original host20/hash has not yet been restored;
host22 is GET-proven after the new daemon startTick 91233. The new SIS 20416 B
0F8577C6… is GET-equal; runtime22 is not the restore package revision22 that
contains host20.

After the third research reboot, startTick 61475; the 3 originals were restored
exactly. Host23 is GET-proven at 36492 B, 31836A0F…; the native-copy preflight
gave FINAL/EXIT -6 before allocate/create/RUN. The prepared package 28 for
host24 was delivered; the final host20 restore must be package 29 or above the
current SIS.

The physical step is in [HELP_NEEDED](../work/HELP_NEEDED.md). The N95
idle-first journal, the return of ocprobe.log, and the research cleanup have
been deferred to another executor. The interim D2 is in
[PS1_CANDIDATES](PS1_CANDIDATES_2026-10-01.md).

## Continuation of 2026-10-02: recovery and RMS_EXIT diagnostic

After the reboot by the user at 13:21, `native-recovery03` received the
unchanged RUN4 journal A33A433C…; c55stream/ocprobe PS0, INFO/startTick 81256.
`native-restore01` returned the three initial E: files with GET/SHA equality.
Host24/hash remain research-only until the final original restore.

The new [artifact31](evidence/2026-10-01/d0-run-exit-diag-v31-artifacts.json):
host25, DSP 5144 B 29069D52…, 18 resolved imports, DOFF/ASM verified; SIS31
delivered, GET exact 8D0E3BE8…. `exit-stages` performs 8 normal protocol 21
packets, then the diagnostic protocol 25. Stage 4 is before waiting for
RMS_EXIT. The host ARM output comes before control 6; the DSP records stage 5
immediately after NODE_getMsg, and stage 6 after STRM_idle(input/output); both
structures are in 512 B with offsets 0/96 C55 words. The snapshot contains the
message, the raw shared headers/records of both directions, pending ownership,
and idle/status. The raw fields may change concurrently; an atomic snapshot is
not claimed.

After stage 6, the extra output reissue/reclaim/idle is still to be performed.
Stage 6 by itself does not prove its completion or the wrapper EXITACK. The
diagnostic RUN does not count toward D0, even with a clean delete. The host
keeps a persistent descriptor/status and QUARANTINE on a pending output or a
failed delete, without KILL/free/close. Before a new RUN, SIS31 must be
installed by the user. The original host20 restore SIS32 is ready, SHA
6E6C81E0….

At 13:38, through HELP, the user allowed a direct deploy of our EXE/hash without
SIS. `host25-deploy01` kept the current host24/hash; PUT→GET confirmed host25
CB74DE96… and the SHA1-loader hash (its SHA-256 EDDE22CA…). `exit-diag01` ran
RUN5 after a clean inspect/create/delete preflight and a read-only clock guard
of 330.24/110.08/220.16 MHz. All 8 packets of 512 B were correct, 240 payload
words each, median 396 us, range 366–457 us, total 3169 us. This is a
failed-lifecycle diagnostic, not a D1 exchange benchmark.

Stage 4 input/output pending 0, message 0. Stage 5 **get 1/waits 1**,
cmd 80000000/arg1=env 77E0/arg2=0; stage 6 has **idle input/output 0**, pending
0, and status 00008000. Thus, in this RUN, delivery of RMS_EXIT and the first
cleanup of the streams were physically proven. After the diagnostic reissue,
the last reclaim/idle and the actual execute return have not yet been observed.
Delete submit 0, 5000 ms deadline -33/status pending; state 2→3, QUARANTINE
without free/close. The live GET journal SHA 778039EB…; the local 30 s runner
did not perform a phone KILL. The native EXITACK construction, delivery,
consumer, and the delete callback remain unknown; state 3 does not show at which
of these boundaries the failure occurred. A reboot by the user at 13:43 was
requested in HELP; GET/PS0/restore are still needed after it.
