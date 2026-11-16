# D0–D2: execution of the 2026-10-01 brief

Update 04.10: at the user's request, the current work is completed by the report
docs/CLAUDE_PS1_HANDOFF_2026-10-04.md. New hardware experiments must not be started
automatically. D0 with 3 clean cycles is accepted; the N95 repeated mapping/kernel
measurements are complete; the D2 measured blocking verdict is delivered (keep on
ARM). DSP publication/ARM caller completion and the deferred E90 recovery/frequencies
are not accepted. Below is the history, not a current command to start the next RUN.

Current continuation, 02.10 21:45: the E90 reboot/recovery is done; a finite MSG
was checked on the E90 and on the N95 that the user allowed. On both, clean created
delete/free/close, but ARM receive −33 and an empty record. Both were fully restored
and GET-equal, host20/PS0. The three E90 variants are not to be repeated; next, a
static audit of the bounded runtime ARM window/reader/queue snapshot. There are no
new official RUNs; D0 0/3, D1 pending; no physical actions are required. Evidence:
docs/WORKER_MESSAGES_2026-10-02.md.

Next step, 02.10, after the created-worker preflight: human reboot/daemon, GET
journal/PS0 → exact restore of 3 originals; host26 is already GET-exact.
`d0-worker-message` skips the create-only preflight of the active worker and
immediately runs a finite final-trigger diagnostic with a prearmed receive in
CREATED. The no-input stop/join/idle has not been proven; do not repeat it. A MSG
success is not a D0 cycle; next are the wrapper/EXITACK root cause and 3 clean own
RUNs. D1 has a 16 KiB TOTAL ring and only after D0; D2 is recalculated after the
measured D1.

Initial HEAD: b75853f. Before the work, the user had changed
docs/APPLICATION_CANDIDATES.md and added work/CODEX_TASK_2026-10-01.md; these
changes are kept separately. Only E90 192.168.3.21:2323 was available. N95 is not
polled. Initial INFO: screen 800x352, startTick 75535, c55stream/ocprobe PS0;
out/d0-e90-initial-connect.log.

1. D0: a reproducible audit of the native loader/cancel/destructor; a separate
   generic library2 RUN + stop/reclaim. The new host21 holds the unsafe session
   when the teardown is unconfirmed; the runner does not KILL on timeout. Save
   DLL/log/ocprobe.log/EXE/hash/SIS before replacement; check the frequencies from
   the registers without PRCM writes. A create/delete probe before the RUN; then
   three consecutive correct RUNs with EXIT/FINAL0 and an unchanged daemon
   startTick.
2. D1 only after D0: analysis of the native reserve/map/unmap/cache ABI; one
   minimal mapping probe to the shared 16 KiB ring. Repeated exchange
   latency/bandwidth, a full check of data/ownership/wrap/teardown. If D0 requires
   a person, only static preparation of D1 is permitted.
3. D2: a verdict for MDEC/SPU/WSOLA by max(H+D,W)+S/N < A+W; distinguish the old
   stock measurements, the current E90 frequencies, estimates and unknowns. SMLAD
   135–200 us is an estimate, not a physical measurement. Do not edit the emulator.
4. Return the originals with GET/SHA256, check the new evidence/STATE/features/
   README, commit/push to private main. Keep the unfulfilled hardware criteria
   open; record physical actions in HELP_NEEDED.md.

All external commands are run through run_bounded.ps1; a maximum of 3 attempts per
problem; no repeated RUN after a hardware failure/reboot.

## D0 correction after the first RUN

Run-stop21 passed 8 correct packets, but returned execute to hostCtl6; state 3,
delete −2, QUARANTINE; after this a person confirmed a reboot. GET of the journal
before START: resume-recovery02.log CE5B1947…; the original DLL/log/clocklog were
returned GET-equal (resume-restore01). A GET-only before this RUN also had a
separate reboot; this is not a second RUN in our transport logs.

On EXITACK, the E90 PDD 803DF864 itself calls the delete dispatch 803E6860. Candidate 22
(host and protocol remain 21): after the stop/output reclaim, it waits for RMS_EXIT
from hostCtl6 and does not issue the next input. This corresponds to the native
Running→Terminating→EXITACK→delete sequence. The probe is a new bounded series; on
the first failure, stop at once and do not start the next RUN.

The third RUN was performed as a generic message diagnostic: 3 snapshots, put 1,
and a valid DSP shared record; then state 3/message-get −2/delete −2. Host22, with
EFileShareAny GET, confirmed the live journal. The limit of 3 is exhausted; further
hardware work is only recovery/originals restore; D0 0/3; D1 is not opened.

A person at 23:22 (local time) lifted the general limit of 3, on the condition of a
new hypothesis for each RUN. Next: ROM STRMCOPY with the same generic library2.
Host23 had select −6 before RUN; host24 parsed ROM properties0 + research library2
copy (only registration/checksum changed). SIS28 was installed, host24 GET exact.
Separate parses again had select −6 before RUN; combined properties0/library2 in
one packet resolved the select. All code/data/relocations unchanged. Native control
RUN4 gave 8 exact echoes, but delete −33/pending/state 3. A repeated native RUN
without change is not planned. The next own diagnostic has STRM snapshots
before/after RMS_EXIT and cleanup before return, to distinguish host message
delivery, DSP teardown and native EXITACK. D0 own 0/3.

The human reboot of 02.10 was confirmed, but the GET recovery had not yet started
because of three connect timeouts (3 s/8 s Python and 8 s .NET). Before any
PUT/START, restore the daemon transport, GET journal/PS0 and exact originals
restore. The general reboot limit was lifted by a person; unchanged retries are
forbidden.

On 02.10 at 13:22, after a new human reboot, the transport was restored.
`native-recovery03`: GET journal RUN4 exact A33A433C… before any PUT/START; PS
c55stream/ocprobe 0; INFO/startTick 81256. `native-restore01` returned DLL/log/
clocklog GET/SHA exact. Host24 is still installed.

The next controlled diagnostic is host25/package31, own `run-exit-diag`: 8 checked
packets; stage 4 before waiting for RMS_EXIT; stage 5 after NODE_getMsg and stage 6
after both idles in the shared 512-B output. The host arms the output before
control6; the status/descriptor live until completion or QUARANTINE. Stage 6 proves
only the first cleanup: the diagnostic output is still reissued/reclaimed/idle, so
the full completion is determined by delete/free/close/FINAL, and this RUN is not
counted among the 3 ordinary D0 cycles. SIS delivered, GET exact; installation by a
person is needed through the ordinary installer. The restore package 32 contains
the exact saved host20; it has not been rebuilt. D1 remains after D0.
