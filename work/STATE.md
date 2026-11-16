# Research continuation state

## Handoff to Claude 04.10: completion of current work at the user's request

The current research stage is logically closed by the handoff; no new phone
commands or hardware experiments are to be started automatically. The
emulator was not edited. docs/CLAUDE_PS1_HANDOFF_2026-10-04.md: D0/D1/D2
evidence, paired timings, actual job/packet formats, source entry points,
strict async conditions, memory/lifecycle limits, version/DSP hashes, offline
verification. Decision on currentWSOLA/MDEC/plainSPU: keep on ARM (0/2520
blocking wins against current kernels before setup). The full initial plan is
not complete: the DSP endpoint and the ARM caller/context cache completion are
not accepted; the E90 original EXE/hash/journals restoration and frequency
qualification are postponed.

Final current work: the complete compiler listings of the deployed
DSP63/65/67 have been published, bound to the build/results hashes.
Independent verifier PASS: payload stores→4/5 completion words→RET→read-only
DCR→timing/notification→STRM_issue. This is compiler order, not a
linked-machine decode or an OMAP SDRAM fence proof. Master evidence verifier
PASS incl. compiler-order; no commands are sent to the phones. N95 last
read-only checkpoint 09:32:35 UTC, 5 originals equal/PS0; E90 no commands.
Before E90 is restored: GET current journal/PS before writes, then its own
originals restoration; do not start a DSP RUN from this handoff. Previous
checkpoint 8382b1dfda3f9de8ddcf36eeffc2a2cd1d105d06 pushed, exact match.

## Current as of 04.10: N95 now; E90 postponed by the user

Requirements acceptance checkpoint: the current N95 original assignment is
matched against the D0/D1/D2 evidence; the D2 measured-job verdict is
delivered; the full-game/audio implementation is not the current assignment.
The D1 publication gate and the E90 restoration/frequencies remain open; the
goal is active. Published complete N95 D0 inspect/create/3 RUN journals (24
packets total) and 2 stock probes; the portable verifier no longer needs the
ignored D0 archive. Fresh N95 verify 04.10 09:32:35 UTC: INFO/PS/GET only, 5
files equal_original, c55stream/ocprobe PS0, daemon launch tuple 62209, boot 0,
byn unchanged. Master tools/verify_n95_acceptance.py PASS:
D0/native61/CPU64/MDEC65-66/SPU67/WSOLA68/dependencies/ARM-cache; no new DSP
RUN/deploy, E90 no commands. docs/N95_ACCEPTANCE_2026-10-04.md +
machineaudit/finalstate publication. ARM-cache checkpoint
93e08daaeae026714d751c5323a372278f77ddae pushed, exact match.

The saved N95 ARM cache path audit is complete: utility 2→kernel 378 clean→376
invalidate; the exact module identity is checked against the previous DMM ABI.
46 kernel sites/10 branch targets; published 109 words/436 B, 7 ranges,
independent verifier decode 13 CP15 operations PASS. Clean MVA/SetWay both end
in DSB; invalidate MVA 52 B without explicit DSB, whole-cache clean-invalidate
with DSB. Runtime thresholds not dumped; both branches checked. This is exact
ARM-side barrier evidence, not a DSP endpoint acknowledgement proof. The old
reference SPRU376A 4.4.3.1 was checked against the local primary text:
accurate; generic pipeline pending/bypass, not an OMAP fence. No phone
commands/E90 access. docs/N95_ARM_CACHE_2026-10-04.md + audit/verifier/json.
Dependency checkpoint 0ad8097788edbbda9722f685de2b852e9c38b926 pushed, exact
match. Next: DSP endpoint contract and caller/context cache-completion
semantics; D1/D2 in_progress, E90 tomorrow.

The read-only dependency audit of currentWSOLA/MDEC/SPU is complete: immediate
result consumers and mutable buffers are traced; unchanged blocking calls W0
by structure; the useful async guest-work budget is not measured. Same-ARM
model H+max(D,W)+S/N<A+W requires H+S/N<A. The 2520 full-job timings were
re-checked against the published hashed journals; serial interval outside
notification<A at S0: MDEC 1/1080, SPU 0/1080, WSOLA 359/360. Passing is only
a necessary condition, not a gain; the elapsed lower bound is conditional on
the same stage envelope, not a production CPU minimum. 32768 strict model
boundary cases PASS. Phones and emulator untouched.
docs/N95_OFFLOAD_DEPENDENCIES_2026-10-04.md + audit/verifier/json. WSOLA68
checkpoint 257339aad577365c7a48a4557e0181021b0aa47d pushed, exact match. Next:
independent OMAP2420 endpoint publication; the concrete async W/state contract
is still open. D1/D2 in_progress; E90 tomorrow, no commands.

WSOLA68/host53/protocol40: exact current shell SMLAD snapshot (CSL343/O2/
ARMv6), retained exact DSP63,8 pilots + 360 paired jobs. A current
p50337.601us, scalar 1003.265 us, H+D ready 1098.633 us; current winners
0/360 before S, paired scalar/current p50 ratio 3.017x. S p50865080us
logging, W0, CPU unmeasured. 460800 ring words, 16,720 DCR reads 0000/WPE0,8
stock brackets; current: keep ARM. Own early concurrent restore after
accepted series 1/2 stopped; the third attempt stopped pre-START on host
mismatch; no PUT/START in failed transport. 5 originals verified 01. OS
per-phone session + whole-runner lock added/tested; specific recovery 02, same
binaries; third series stock 02 complete; 5 originals GET/SHA equal, PS0,
verify 02. Daemon tuple 62209 stable, no reboot. Source/out 53; typed DSP63
used, generic DSP67. docs/N95_WSOLA_CURRENT_2026-10-04.md + independent
verifier/44 tests PASS. At the WSOLA68 checkpoint: next endpoint publication
and dependency audit; read-only dependency audit completed above, useful W
still unmeasured. D1/D2 in_progress. SPU67 commit
2e675c9c20edeab93de34e0ba8fb038738a4b5f4 pushed, exact match; WSOLA68
checkpoint 257339aa pushed, exact match.

SPU67/host52/protocol42 completed 24 pilot + 1080 full jobs: 1/8/24 voices of
64 samples each, current actual SMLAW ARM assembler baseline, 128 exact
sums32/job. 138240 sums32 and 2672640 ring words 16 in the full series; all
pages/ownership/teardown PASS, 8 stock brackets, 2160 DCR reads 0000/WPE0. A
p50 = 3.576/27.180/40.531 us; H+D pack→ARM 128 sums ready = 1617.432/3295.898/
3540.039 us; oracle checks outside; blocking winners 0/1080 before S. S p50 =
863494 us includes lifecycle logging, W0, CPU unmeasured (-1). The plain mix
stays on ARM; this is not a full SPU/gamePCM/mutable-state verdict. N95 5
originals restored (GET/SHA-equal), PS0, daemon tuple 62209, boot 0, byn
stable; source/out 52/DSP67; the immutable archive is preserved. No commands
to E90. docs/N95_SPU_RING_2026-10-04.md + publication verifier/39 session tests
PASS. Next: independent endpoint-publication evidence and a useful ARM W/job
dependency audit, current WSOLA SMLAD baseline; E90 frequency/restoration
tomorrow. D1/D2 overall in_progress. The SPU67 checkpoint is published
separately.

SPU offline boundary audit after MDEC: GCCE463 ABI int/pointer 4B, NSSIZE914,
ADSR16, SPUCHAN56, sample_buf64, SPUInfo 3840 (no thread)/5440 (thread),
optional work_item 8396, worker 33840B. The full SPU RAM is 512 KiB; mix_plain
is not the whole doSamples. A plain 24-voice job with samples/volumes/sums32
holds 64 samples (6848 input/512 output bytes, 15/2 slots), max 66; 68 does
not fit. Next hardware probe: current HAVE_ARMV5 smlawb/smlawt baseline + exact
sum oracle, only mix_plain; decode/ADSR/fmod/reverb/IRQ stay on ARM. At the
time of the offline audit, SPU hardware measurement was NOT performed; the
SPU67 entry above added it. docs/N95_SPU_BOUNDARY_2026-10-04.md;
tools/audit_spu_boundary.py compiled layout + capacity calculations. MDEC
checkpoint 1e6ea1c2ca23b152ef489e96872a34839c6f1267 pushed, exact match.

MDEC65/host50 and 66/host51/protocol41 each completed 3×8 pilots and 3×3×120
full jobs, 1080 jobs/2520 macros, 483840 RGB24 uint32 words, 3409920 ring
uint16 words, exact. The source is the current local PS1 MDEC kernel snapshot;
32-bit C55 adaptation, Python oracle + ARM343/463, no emulator edits. 66
reused exact DSP65; H+D ends after the RGB24 copy into ARM memory; oracle
checks are outside A/H+D. Batch 1/2/4 p50 A463 = 78.201/110.626/295.639 us,
H+D = 2655.029/4272.461/7690.430 us; winners 0/1080 without setup. S p50 =
840178 us, includes lifecycle logging; W0, CPU unmeasured (-1), DSP raw ticks
unconverted. All 2160 full-series DCR reads/cohort 0000/WPE0; the current
publication proof is still open. N95 after EACH cohort: 5 originals restored,
GET/SHA, PS0; daemon 62209, boot 0, byn stable. Source/out 51/DSP65. No commands
to E90. docs/N95_MDEC_RING_2026-10-04.md + independent publication verifier/34
tests PASS. Next N95: actual SPU/state job boundary/budget and endpoint
publication; the asynchronous useful W is not measured. D1/D2 remain
in_progress. CPU64 checkpoint 70902bbe59fc22030f9cb0fef12aa8f4ad376060 pushed,
exact match; MDEC checkpoint published separately.

CPU-window64/host49/protocol38 completed pilot 120 packets and 3×4 full runs,
9360 correct packets, 6 stock brackets, pages/ownership/teardown clean. Batch
1/2/8/15 p50 exchange 915/1190/3021/5126 us. Weighted CPU 45.37/45.87/48.09/
45.68% over whole 120-job outer windows, including pack/cache/full checks/final
settling yield; no per-frame CPU reads, file I/O, or ARM baseline inside. Scope
is correctness harness, not pure wait/production CPU. Full-window useful
bidirectional 0.712/0.960/1.357/1.500 MB/s. The new DSP64 SHA 00FCD176… differs
from 52/61; old typed files/archive kept. No DCR/PRCM writes; current64 WPE not
measured. N95 5 originals after 64 restored, GET/SHA-equal, PS0. Source/out
host49. Evidence: docs/N95_RING_CPU_2026-10-04.md; verifier +27 tests PASS.
Actual WSOLA verdict added to docs/PS1_CANDIDATES_2026-10-01.md. Next N95:
independent endpoint publication proof and actual MDEC/SPU job budget/state
contracts; no emulator edits. E90 untouched until tomorrow. Counter checkpoint
c8d005fc99704e329b69ed12e5bdccb7fe18eaeb pushed private main, ls-remote exact;
CPU64 published separately.

No-DSP counterprobe v1 completed 3×36 calibration samples. Raw busy 1/10 ms
returns CPU 0 in 8/9 samples each; raw sleep 10 ms has 2/9 deltas > wall. All
54 samples with yields at boundaries have CPU ≤ outer wall; late slice
accounting reproduced without DSP. This is not an exact firmware-source match.
The counterprobe EXE/hash/log were initially absent, verified exact, and
removed after 3 EXIT0; originals c55stream/ocprobe were not changed. Evidence:
docs/N95_CPU_COUNTER_2026-10-04.md; verifier/tests 25 PASS. Short historical
N95 ring CPU percentages are likewise unqualified raw arithmetic. The aggregate
ring CPU window with settling boundaries was performed as the next step, 64,
above. WSOLA checkpoint d9e9a8de8bc019bdba93924030743e387474129a pushed private
main, ls-remote exact. Counter calibration checkpoint published separately.

WSOLA63/host48/protocol40 completed pilot 8 and 3×120 actual kernel jobs.
Offset/score/scored exact, native ownership/pages/teardown PASS, 6 stock clock
brackets. A p50 = 1155.853 us; H+D pack→result p50 = 1983.643 us; only 16/360
paired samples are faster before setup. Instrumented S p50 = 828063 us,
includes synchronous journal Write/Flush; not a pure create/minimum cost. W = 0,
parallel gain not measured. 720 DCR reads 0000/WPE0, exactly for 63. CPU usage
unqualified: 320/360 deltas are larger than the transfer wall; a separate
calibration is needed. Raw DSP ticks/countspms must not be converted to ms. N95
5 originals after 63 GET/SHA-equal, PS0; source/out 48/WSOLA63. Evidence:
docs/N95_WSOLA_RING_2026-10-04.md and tools/verify_wsola_publication.py.
Checkpoint 25a365686b814b9e8276d963efefce83e9a48db2 pushed private main;
WSOLA63 published separately. D1/D2 overall in_progress: the publication
contract, qualified CPU, and MDEC/SPU verdicts remain open; emulator unchanged.
The next No-DSP counter calibration was already performed above.

The goal is restored and active. N95 native61 completed 3 series/12 runs/9360
packets, 6 stock clocks PASS, 5 originals GET/SHA-equal restored. The new cohort
is slower than old54 (batch 15 p50 = 5249 vs 2716 us); do not mix samples or
state a cause without verification. Distinct DCR62/host47/protocol39 pilot
PASS: 120 packets/8 exchanges, all 16 reads 0000/WPE0, stock clocks
before/after. The 5 originals after the pilot were again restored and verified,
PS0. Source/out 47/DCR62, old ring61/archive unchanged. Evidence:
docs/N95_DCR_2026-10-04.md. The next step, WSOLA63, was already measured above.
Checkpoint c207070e16f2b25b635c53e299a33c5708d2e969 pushed private main,
independent ls-remote confirmed. The new DCR62 changes are published separately.

Do not query or restore E90 before returning to it tomorrow. Source audit and
exact timeline: docs/E90_DAEMON_REBOOT_2026-10-04.md. User-confirmed reboot
after the completed KEYdown/SHOT/GET; the next connect sent no commands. The
GET daemon log succeeded; the tick reset confirms a system restart; the fault
reason was not obtained. startTick/boot/by — daemon launch/classification, not
a unique phone boot ID. The known E90 host46/original DSP; originals restore
pending; the ringclock was built, but 4 deploy attempts did not reach PUT.
Driver API RDomain 102/104 vs standard 105/100 under a shared name was proven
offline; this is not the reboot cause.

The current short checkpoint 2026-10-04 —
[HANDOFF_NATIVE_RING](HANDOFF_NATIVE_RING_2026-10-04.md).
E90 native61 completed 3 full series/9360 packets; 5 originals returned to
both. Clock self-test −20 is not counted as stock; Open4All on E90 without
reboot is required. Below is the history; the current D1/D2 remain in_progress.

Below is the saved chronology. The current state is the last dated section;
the criteria and audit are in `work/PLAN.md` and `work/FINAL_AUDIT.md`.

## 2026-09-29: start

The full assignment and criteria were recorded in `work/PLAN.md` before the
code changes. The current statuses are in `work/features.json`.

Checked: `.git` absent; the source texts and hardware journals remain from
August; Claude's harness decisions are on record, along with two requests
without research results. Old D: paths are known in the scripts. The TI CGT
was found on G:, and the SDK and dllcreate on H:.

Done: the plan, the requirements list, and this state file were created.

Next action: restore the relative environment configuration and build both
sides; in parallel, read the independent local sources of the stream contract
and check the active GitHub account. After the contract is prepared, hardware
experiments, not a sweep of calls.

Not finished: F01 (scenario check), F02–F08. The user confirmed the private
GitHub repository on 2026-09-30. The active account in the current check is
1234bpv. Both addresses 192.168.3.22 and 192.168.3.21 answered on TCP:2323; the
phones' identity still has to be verified via INFO.

## 2026-09-30: environment restored

F01 and F02 completed: portable paths, bounded runner, JSON/tool checks,
successful ARM and DSP builds, relative reverse-engineering paths. Evidence:
`docs/BUILD.md`, `docs/SESSION_2026_09_30.md`, logs `out/*build-desktop.log`.

Both phones answered INFO with the corresponding screens; the DSP test has not
been run yet. Local Git was initialized; publication of the private repository
is next. After it: static analysis of the ROM channels/clients, backups of the
phone files, and a minimal justified test.

## 2026-09-30: GitHub and stream contract

F03 completed: private https://github.com/1234bpv/TMS320C55x, main
`e35a7315dc8d86add484d36f2bc1f698b9d4897e`; the remote HEAD was verified. F04
is in progress; results in `docs/STREAM_RESEARCH.md`. The stock BAL uses
task14/task16 for buffers; task7 starts execute, fn6 deletes. The DNode vtable
and the 176-byte stream props were found. The DSP STRM ABI, props, and cleanup
are being refined.

The current DSP dividers and the profiles of both phones have been read; the
old ocprobe.log is kept. N95 m=111/div=3, E90 stock/div=3. A direct GET of the
E90 library is not allowed (-46); a read from a separate process or an already
verified user-mode ROM dump is required. So far only ocprobe.log has changed on
the phones (via read-only runs); both are to be restored from backup after the
experiments.

F05–F08 are not completed. Next: a minimal ARM host and a streaming DSP node
after static argument checking; the E90 firmware profile; practical
PS1/browser candidates.

## 2026-09-30: current hardware check

Results and contracts: `docs/STREAM_RESEARCH.md`; practical candidates:
`docs/APPLICATION_CANDIDATES.md`. F04–F08 are in progress. The custom C55x node
has one input/output, context in `env->moreEnv`, execute started separately
from create. So far there is no successful streaming packet and no measurement
of parallel speedup.

N95: after the first restart, stock m86/div3 was checked. Base-only,
create/delete, free task succeeded; the context create takes 7415–7446 µs in
separate runs. The smoke execute confirmed RUN, but delete ended in a timeout.
The normal context execute also confirmed RUN; the first put/get got −2, the
last record — BEGIN delete. After this, the user restarted the phone. This is
not evidence of an automatic restart in this specific attempt.

Host v4 was built (`out/stream-arm-v4-build-fixed.log`) and installed via
E:\sys\bin. The separate buffers/create tests completed with EXIT/FINAL=0.
Ord30/29 mode2 allocates and frees two 4096-byte buffers; get-state copies 280
bytes, so an explicit array was used instead of the 276-byte SDK TBuf8<268>.
The firmware does not fill all stream fields for every connection type; they
cannot be treated as valid data without a type check.

E90: live ROM, UID 20002496, 39 bridgeapi exports verified. The user helped
install the SIS and reported a phone restart. After the daemon was restored,
inspect confirmed **C55STREAM v3**; base-only and the custom context
create/delete/free task succeeded, create=6774 µs. The streaming execute has
not yet been called on E90.

The link is controlled by `tools/strict_net.py` and `run_stream.py`: only an
explicit address and a verified screen, without searching for another phone.
WAIT is called only after PS=inactive, because the old daemon's WAIT could
re-Resume a live process and crash.

Next: clarify the PDD stream-connection fields and the cleanup after RUN, and
check the first packet against the newly proven contract; then correctness and
three paired serial/parallel runs. E90 has v3 for now, N95 has v4; mode names
must not be applied to an unconfirmed old host version.

**Phone restoration has not yet been performed.** The old ocprobe.log of both
phones and the 12288-byte E90 romdump.bin are kept in `work/device-backups`.
After the experiments, return them with a byte check. The new c55stream
EXE/hash/DLL/log on N95 and the E90 research SIS/DLL/log are to be removed, or
explicitly left at the user's decision. The old dsptest.exe, bench.dll and
benchmark logs were not replaced. The new DSP DLL on E90 was absent before the
write (STAT −1).

The latest code changes and reports are not yet committed or pushed to GitHub;
F08 requires synchronization after the check.

## 2026-09-30: current state after 8 packets

N95 host v6, connection=0: **8 correct packets per single create/RUN**, serial
reps=0. Data/sequence/lengths/CRC checked; non-zero Q15 and the parallel
speedup are not yet checked. Delete/status/FINAL/EXIT=−2, so the run is not
fully successful. Journal in
`docs/evidence/2026-09-30/n95-stream-host-echo-v6.txt`.

The next DSP idle-first test lost the connection. Its phone journal has not yet
been read; do not make a new write or START before this journal is obtained. A
request has been sent to the user to restore N95 and to report whether there
was a restart. Repeated INFO on N95 — connect timeout; E90 — reachable.

The static lifecycle was refined: control 6 via PDD slot +92 itself sends
RMS_EXIT, and the ACK starts delete. V7 fixes the early exit after the marker:
input is issued again, execute waits for RMS_EXIT, then idle/reclaim. Component
timers and a DSP protocol version 7 check were added. V7 ARM/DSP and SIS
revision 7 were built and verified locally; **they have not yet been run on
the device**.

N95 keeps host v6 and the DLL of the last failed idle-first attempt; E90 has the
installed host v3 and the old context DLL. The new local
`out/dsp/c55stream.dll55l` is v7; it must not be attributed to the v6 journal.

Next: GET the N95 log and remote DLL before any write; inspect/create v7,
execute without host frames from control 6; after a clean EXIT/FINAL=0 —
serial reps=0, Q15 correctness, and three paired serial/parallel runs. Only
after a stable N95 lifecycle should E90 be updated and tested. F04–F08 remain
in_progress. The phone restoration described above has not yet been performed.

The runner now saves the previous log and performs inspect v7 before the DSP
modes. On live E90 v3, the rejection of mode=create before any DSP driver calls
was verified: only inspect was run, EXIT/FINAL=0. Evidence is in docs/evidence.

The original E90 `ocprobe.log` (1249 B) and `romdump.bin` (12288 B) were
restored. Both GETs after PUT match the backup byte for byte; INFO succeeded.
Evidence: `docs/evidence/2026-09-30/e90-restored-originals.json`. The N95
ocprobe restore and the removal of the research files from both phones remain
unfinished; the SIS/DLL on E90 were left for the next hardware check.

The research checkpoint `aa802d0f5e49da9976d650c5abbfd4f2323d097f` was pushed
to private main; the local and remote HEAD were verified. This is
synchronization of the current state, not completion of F04–F08.

## 2026-09-30: F04 map completed, hardware check awaits N95

F04 complete: STREAM_RESEARCH now contains the exact static contract of node
state notification (task5/task6), one-off and packet steps, the overlap
boundary with create, and a matrix of all candidates with their sources and
unknown parts. Hardware checks of DMM/ring/own messages are not claimed; this
is not a negative conclusion about their feasibility. F05–F08 remain
in_progress.

The previous goal turn was progress: v7 built, runner guard verified, E90
originals restored, code/reports pushed to private main. In the current
continuation, a repeated N95 INFO/GET again gave a connect timeout. There are no
new STARTs on N95; the journal of the idle-first attempt has not been read. The
next hardware action remains the GET of this journal after the user restores
the phone.

## 2026-09-30: E90 v7 preparation and the limit of further execution

The previous goal turn was progress: the F04 map was completed and pushed to
private main; HEAD verified. In the third consecutive goal turn, N95 again gave
a connect timeout; the emergency idle-first journal is unavailable.

Independent preparation of E90: INFO succeeded, PS c55stream=0; before the
update, E:\c55stream.log, the DLL (3496 B) and the SIS (6336 B) were saved to
`work/evidence/e90/stream-before-v7.*`. SIS revision 7 (10192 B) was written to
E:\c55stream_sha1.sis and opened via OPEN. The snapshot install-v7-02.bmp showed
the prompt "Install C55Stream Research?".
Before the KEY lsk was sent, a new TCP connection had already timed out; this
command was **not sent**. The v7 installation is not confirmed. There is no new
DSP RUN on E90.

The restoration of the E90 ocprobe.log/romdump.bin from the previous turn
remains proven; these files were not changed during the SIS preparation. A
request was sent to the user to finish the installer and open the daemon on
E90, and also to restore N95.

Without restoring the phones, F05 cannot be checked or the N95 restore
performed; F06 awaits inspect of the installed v7, base/create and the stream;
F07 requires channel measurements; F08 needs hardware evidence and the final
restore. Local builds, the channel map, the runner guard, reports, and
publication are already verified. The next step after external restoration: N95
GET log/DLL before any new START; E90 inspect v7 before any DSP mode. The goal
is not complete.

## 2026-09-30: E90 reachable again and installed version check

After the user's report of E90 availability, it answered INFO: 800×352, AP
Huawei, script IDLE. Before the launch, PS had no active c55stream. The previous
journal was saved; a new inspect via `C:\sys\bin\c55stream.exe` ended with EXIT
0 Kill / FINAL 0 and showed **C55STREAM v3**, MachineUid 20002496. The runner
rejected the old version after inspect; the DSP was not called. Evidence:
`docs/evidence/2026-09-30/e90-stream-installed-v3-after-recovery*.txt`.

The snapshot `work/evidence/e90/install-v7-recovery-01.bmp` showed the list of
installed applications, not an active installer. There was no new OPEN, KEY,
EXE/DLL write, or DSP START in this continuation. After the snapshot, the E90
TCP link became unavailable again. N95 at 192.168.3.22 did not respond to any
attempt, so its emergency journal and DLL have not yet been read. Four
additional bounded checks of both known addresses ended in connect timeout;
`docs/evidence/2026-09-30/device-recovery-unavailable.txt`. This does not
establish a restart or the cause of failure of either phone.

Requests were sent to the user to check N95/IP and to open the E90 daemon,
finishing the installation of the already written SIS v7. After restoration:
save the daemon journal (`E:\ps1_daemon.log`) and the N95 c55stream.log/DLL
before a new START; complete the E90 update through the observable installer,
then inspect. For the UI, try one TCP connection; this is not yet a proven fix
for the transport instability. F05–F08 remain in_progress.

Later, E90 answered twice more; the daemon journals
`work/evidence/e90/daemon-after-recovery-02.log` and
`daemon-heartbeat-02.log` were collected. They contain new launch records, but
the user has not yet specified the exact kind of recovery. The existing SIS was
opened via OPEN; the first snapshot showed preparation of the installation. The
next SHOT on the same TCP connection got a timeout. KEY was not sent.

`tools/live_device.py` was added: one verified device, sequential commands from
stdin, INFO every 2 seconds between commands, a unique full journal, and a
duration limit of 30–600 s. Python compile and help succeeded. On E90,
successful heartbeat INFO, journal GET, and SHOT/GET/DEL were verified. The last
snapshot showed the main menu without the installer. After it, the next INFO
ended with ConnectionResetError; the client closed the connection and sent no
further requests. Evidence: `e90-installer-heartbeat-transport.txt` and
`e90-daemon-latest-sessions.txt` in docs/evidence/2026-09-30. This is **not a
proven fix** of the link. The further GET SIS / START inspect prepared after
this were not sent: the client had already finished. The last verified
installed version of E90 remains v3; no DSP RUN. N95 remains unavailable. The
gateway 192.168.3.1 answered ICMP (2 ms), so the current check did not show a
general LAN loss on the PC.

In the next window on E90, a new inspect (`stream-installed-after-restart-03`)
again ended with EXIT/FINAL 0 and confirmed v3. GET SIS returned 10192 B: the
bytes fully match the local revision 7, SHA-256
54A214227DFFF6CF0638A007F9980331D1F06888B654AFF28831FA4EAD174AB9. Evidence:
`docs/evidence/2026-09-30/e90-sis-v7-readback.json`. This is a check of the
delivered package, not of the installed EXE.

The new live client successfully performed INFO heartbeat, GET SIS, GET
daemon.log and FG. The next INFO got ConnectionResetError (10054). OPEN and the
prepared SHOT with step=2 were **not performed**: they were not in the protocol
of the already finished client. Transport — `docs/evidence/2026-09-30/e90-heartbeat-without-open-or-shot.txt`;
the control characters of the FG response are escaped there, and the original
is kept locally. Therefore, the full SHOT is not a necessary condition for the
disconnect; the reduced SHOT is not yet verified. Do not make new UI retries
without restoring and clarifying the state. Requests to the user about N95/IP
and the E90 installation/daemon remain unanswered. F05–F08 are not completed;
the DSP on E90 was not started in this continuation.

## 2026-09-30: N95 in the correct subnet; v7 on both; RMS-only −33

The earlier entries above are historical. The current INFO check succeeded on
N95 192.168.3.22 (320×240) and E90 192.168.3.21 (800×352); PS c55stream*=0. The
user clarified that N95 was on a different subnet. Before that, two full
authorized TCP 2323 scans of 254 addresses found only E90. After the correction,
N95 is reachable; the IP request is no longer needed.

**N95 recovery:** before new c55stream STARTs, the idle-first journal, the 3644
B DLL, the 15084 B host v6 EXE, and the SHA-1 hash were saved. The v6 journal
breaks off after frame=7 with errors=0; there is no frame 8/delete/FINAL. Do not
confuse this result with the earlier 8-frame v6 run with delete −2.

**E90 v7:** the SIS installed by the user was confirmed by inspect (all 39
exports, UID, EXIT/FINAL=0). The 3668 B normal v7 DSP (SHA-256 E039E983...) was
read back and compared byte-for-byte. Base, native buffers, and
create/delete/free task=0 (create 8697 µs). Minimum execute without host frames:
RUN=0/status=0, state=2; deleteStatus remained pending after 5000 ms,
delete/FINAL/EXIT=−33. Immediately after the test, E90 responded. Later connect
timeout; after recovery, INFO shows a lower uptime — an indication of a restart
between checks; the cause is unknown. The minimum log and DLL readback are
unchanged. RMS-only was not transferred to or started on E90: prepare had a
connect timeout before the first daemon command. Normal v7 E039E983... remains
on E90.

**Static evidence:** NODE_wait (24D020), NODE_getMsg (24D790), RMS_executeNode
(24DEDC), and the task wrapper (24E6F0) in N95/E90 have identical bytes; whole
common-code differs in 116 bytes. DOFF packet header=12 B, 64 packets.
NODE_getMsg returns 1 after copying three longs. The task wrapper calls execute
and itself sends EXITACK 40000000 via
NODE_putMsg(env,NULL,{cmd,return_status,0},FOREVER). Do not add a manual ACK
without new evidence. PDD control 6 under running/state 2 and node+440=0 sends
EXIT 80000000 with arg1=nodeEnv; with node+440!=0 it calls 801A3DF4. Field 440
comes from processor+64, which in turn comes from configuration +588; the
value/contract of the other backend are still being clarified.

**N95 RMS-only:** build_stream_node.cmd rms adds an execute that only waits for
NODE_getMsg/EXIT (100×100 ms), without issue/wait/idle/reclaim. Create/delete
remain standard, with stream objects. Host v7 15684 B (87CEA30C...) and the
loader hash/DLL 2700 B (8F65458F...) readback verified. Create/delete/free
task=0, create=8361 µs, EXIT/FINAL=0. Minimum execute RUN/status=0, state=2;
delete pending/−33, EXIT/FINAL=−33. N95 responded even several minutes after
this, uptime increases. This is a new isolation of RMS, not an echo pass. After
the test, the normal v7 DLL 3668 B (rebuild 5B6BE15B...) was written to N95 and
read back; its execute has not yet been started. The main out/dsp DLL was also
restored with the normal build; the RMS artifact was saved separately as
c55stream-rms.dll55l and stream_node-rms.asm.

**Clock/restoration:** read-only N95 stock m86/div3, firmware math DSP 220160
kHz; HAL MPU=206438 kHz at the time of the probe, not an overlap measurement.
E90 before its RUN stock m86/div3, MPU=330000 according to HAL. N95 original
ocprobe.log 1259 B was finally returned and checked byte-for-byte (SHA-256
1ABC8073...). E90 original ocprobe.log 1249 B was returned again after the probe;
original romdump.bin 12288 B was restored earlier. Research EXE/SIS/DLL/log
remain for continuation; old dsptest/bench untouched. F05–F08 in_progress, goal
active after network recovery; measurements of H/Q15/overlap and final cleanup
are not performed.

Evidence and full SHA-256 — docs/SESSION_2026_09_30.md and
docs/evidence/2026-09-30/n95-stream-execute-v7-rms-wait*.txt,
e90-stream-execute-v7-minimum*.txt, n95-restored-original-ocprobe.json,
n95-e90-dsp-rms-code-comparison.json,
device-status-after-n95-subnet-recovery.json.

**Next:** analyze native MSG-toDSP routing/dispatch for RMS_EXIT and the PDD
flag/backend to distinguish missing EXIT, execute return, and missing ACK. If
needed, prepare a bounded host get-info/message probe on the exact raw ABI task
2/task 20/task 21 (see STREAM_RESEARCH), with a new version guard. A new RUN
only after concrete static evidence or an altered contract; do not repeat
RMS-only −33 and do not run serial/parallel now.

## 2026-09-30: v8 get-info preparation and messaging diagnostic

MSG-toDSP SWI 24D498 copies three longs into the frame and puts it into the
destination queue from the fourth DWORD of the shared packet. PDD 801AF3A0 takes
destination from queue+16; after create ACK 801A27F4/801A2800 the driver sets
this field to the returned nodeEnv. NODE_getMsg reads this same queue. This is a
static route, not confirmation of actual EXIT delivery.

Task 2: LDD 801B4A98 writes 112 B, header/max=30000068/104; nodeEnv payload+64.
Task 20/21: 8-B status/record pair, raw record **24 B**,
header/max=3000000c/12, payload=cmd,arg1,arg2. Both queued receive 801AF284 and
pending receive 8019B048 write 24 B; do not read the last DWORD padding.
Dispatcher 801B4B64 has commands 0–21; there is no separate cancel 22/23.
Statuses and records in v8 are global; repeated get while pending is prohibited.
The destructor terminates pending status; this does not mean that the kernel or
DSP can be recovered after a crash.

v8 info performs create/get-info/delete without RUN. Only after its success — a
separate messages variant: DSP hello {600,00080001,env}, host echo
{601,12345678,a5c55a5a}, reply 602, receipt 603 before the standard EXITACK
wrapper. Execute messages does not call STRM; receive limit 150×100 ms. Host
waits for receipt during control 6, distinguishes echo PASS from clean
lifecycle, and preserves the first error even with late completion. Runner
messages requires v8 and deadline >=60 s; the old E90 v7 is available via
explicit --host-version 7 only for already existing modes.

ARM v8 build EXIT_CODE=0: out/stream-host-v8-message-build.log. At the time of
this entry, info/messages have not yet been run on hardware. N95 INFO
successful, PS=0, uptime increases. E90 was not updated to v8.

## 2026-09-30: N95 get-info v8 confirmed; messages awaiting network

02:36 UTC: first host v8 build 18660 B, SHA-256 374F8BE1..., hash and EXE saved
and read back. On the phone, normal v7 DLL 3668 B 5B6BE15B... was not changed.
Info (without RUN) gave create=5859 µs, header/max=30000068/104,
nodeEnv=000077e0; delete/free task=0, EXIT/FINAL=0. Transport ended with INFO,
PS showed finished process. Evidence —
docs/evidence/2026-09-30/n95-stream-info-v8-raw-record*.txt and
n95-host-v8-raw-info-deploy.json.

PDD field node+112 in the first journal was erroneously named timeout=3; time
units are not established. Local v8 build fixes only the label to property112:
18668 B, 0900DFE3...; it has not yet been delivered. Messages DLL 2924 B
5A06007E... and SIS revision 8 11716 B 804B1533... were built, neither
delivered. The main out/dsp DLL after the variant was restored with normal build
3668 B 70BD54CE... . On E90, installed v7 remains.

MSG_toDSP_SWI, MSG_notify, NODE_putMsg, LDD put/get/info/dispatcher are
byte-identical in ROM N95/E90. Shared record writer PDD formats 16-B
{cmd,arg1,arg2,destination}; destination — offset 12 ARM bytes / 6 C55 words.
JSON with SHA-256 — n95-e90-message-routing-contract.json. This is static
evidence for the next experiment, not a hardware echo PASS.

After an eight-hour pause (10:44 UTC) both IPs got connect timeout; PC
Wi-Fi=192.168.3.11, gateway .1 responded. INFO/PS via former escalation also
ended in timeout; there are no unfinished exec handles after the break. A new
DSP RUN after successful info was not started. Pending async request asks to
open N95 daemon and check Wi-Fi/IP. Reason of unavailability is unknown; do not
attribute it to DSP or get-info.

Next: fresh INFO/PS N95; tools/prepare_stream.py with a unique tag, current DSP
hash 5B6BE15B... and messages DLL; check clock guard and byte restoration of
ocprobe.log; run_stream messages --deadline60. After probe, save log/transport
and return normal DSP from backup, read back. In case of failure, do not start
serial/parallel. The prepare script was verified by compile/help, its real
execution has not yet occurred. F05–F08 in_progress, goal active; last
continuation — progress.

## 2026-09-30: prepare v8 passed; message RUN lost connection

10:59 UTC N95 became available. Prepare stream-v8-messages-prepare-01 performed
all backups, stock read-only clock guard (m86/div3, HAL 206438), ocprobe.log
restore 1259 B 1ABC8073..., and EXE/hash/DLL readback equal. On N95 now host
18668 B 0900DFE3... and messages DLL 2924 B 5A06007E...; normal 5B6BE15B...
saved in work/evidence/n95/stream-v8-messages-prepare-01-before.dll55l. The
original ocprobe.log was already restored **before RUN**.

Info with the new host/messages DLL (stream-info-v8-messages-create) is clean:
create 6347 µs, property112=3, nodeEnv 000077e0, delete/free 0, EXIT/FINAL 0.
Messages START accepted 11:00:20 UTC (daemon proc 5), PS alive until 11:00:23;
next PS timed out. PC runner session 41172 ended EXIT 1; state of phone
process/DSP unknown. Connect/GET log after this twice got timeout **before the
first daemon command**, recovered log was not created. Do not consider either
echo or lifecycle successful. Restart not confirmed. E90 INFO successful, PS
c55stream*=0; v8 SIS/new DSP were not transferred to E90.

Evidence docs/evidence/2026-09-30: n95-messages-v8-preparation.json,
n95-clock-before-messages-v8.txt, n95-stream-info-v8-messages-create*.txt,
n95-stream-messages-v8-routing-transport.txt,
device-status-after-v8-message-run.json. Pending async request clarifies the
failure type of N95 and asks to open the daemon.

**Next upon availability:** GET E:\c55stream.log and current DLL BEFORE any new
c55stream START/PUT, fresh INFO/PS. If c55stream is still alive, do not consider
it terminal and do not call WAIT. After recovery and PS=0, return normal from
the specified backup and verify GET. Do not use blind KILL 5 after daemon
restart: ids may change. A new RUN only after journal and a new contract;
repeating the same message probe is prohibited now. Cleanup normal DLL pending.
F05–F08 in_progress, goal active; this continuation has hardware progress.

## 2026-09-30 11:49 UTC: N95 recovery awaiting network; E90 v8 SIS/stock guard ready

The last user message about availability was checked again. PC 192.168.3.11;
full TCP 2323 scan 192.168.3.1–254 found only E90 `.21`. N95 `.22` connect
timeout; ARP neighbor Incomplete. N95 restart after message RUN not confirmed.
GET journal/current DLL did not take place, normal 5B6BE15B... restore pending;
on N95 messages 5A06007E... remains. There was no new DSP RUN. Async request
clarifies IP/daemon and restart fact.

`tools/recover_stream.py` added: journal/current DLL → INFO/PS → exact before-DSP
restore/readback only with finished c55stream and known hash. Does not call
START/WAIT/KILL. Compile/help passed. Recovery 01/02 (11:17/11:20 UTC) both
complete=false/connect timeout before the first command; no phone writes.
Positive hardware execution not yet verified. Later recovery was verified on
E90: journal/current DLL/PS0 obtained, DLL already exact backup, PUT skipped,
final GET equal/INFO successful. This is an idempotent path, not an executed N95
restore.

E90 INFO/PS0 successful, uptime increases/startTick 42746. 11:30 UTC
`E:\c55stream-v8.sis`, 11716 B 804B1533... transferred, GET equal. Before this,
EXE/hash/DLL/log were saved; versioned SIS path absent. DSP normal 3668 B
E039E983... remained. Later installed EXE GET still has v7 hash 87CEA30C...; v8
installation awaits user. There was no OPEN/SHOT/START. Package and checksums
are concrete, no need to re-deliver SIS.

11:45 UTC E90 guard 01 rejected regular restore-check 1, because the script
erroneously expected N95 value 100; there was no DSP PUT, original ocprobe.log
returned. Guard fixed for separate UID/profile/code. 11:48 UTC guard 02 passed:
stock m86/div3, HAL ARM 330000, firmware math DSP 220160 kHz; original
ocprobe.log 1249 B BE58F5EF... and normal DLL 3668 B E039E983... readback equal.
This clock ocprobe START is separate from SIS delivery; c55stream was not run.
Evidence — e90-info-v8-preparation.json/e90-clock-before-info-v8.txt; old
rejected guard 01 saved separately. EXE v8 installation not yet confirmed.

E90 get-info PDD getter 803E57F8/table 803F8424/slot 20 established from its
ROM. NodeEnv payload+64; getter 92 B differs from N95 only in relocated BL+20.
LDD get-info copy/adapter/constructor byte-equal. Reproducible
`tools/rev/compare_node_info.py` executed; JSON hashes —
docs/evidence/2026-09-30/n95-e90-get-info-contract.json.

**Next:**
1. If N95 responds, recover_stream with a new tag, preparation
   stream-v8-messages-prepare-01, and --restore-dsp; read journal first. With
   live c55stream, restore is prohibited. A new RUN only after log analysis.
2. If E90 SIS is installed, GET host/hash, inspect v8, stock read-only clock
   with saving/restoring original ocprobe.log, info without RUN.
3. Analyze RMS/message failure using new evidence; do not repeat the same RUN.
F05–F08 in_progress, goal active; current continuation has static/deployment progress.

## 2026-09-30 15:54 UTC: v14 verified; ARM message delivery open

Previous pending recovery/SIS items completed. Both phones responded: N95
`.22`/startTick 7928381; E90 `.21`/startTick 47653 after user-confirmed
automatic reboot. Installed v14 EXE 22408 B 5F1C77CF… verified on both; E90 SIS
13624 B 1BC4F000… installed by user. No active c55stream.

N95 v8 recovered log hello −33, break BEGIN delete; exact normal restore
5B6BE15B… PUT/GET completed. V9/v10 created pending receive→delete/free 0→−3,
EXIT/FINAL 0; explicit raw allocation 32 instead of SDK 28. Bare no-STRM also
hello/delete −33. V11–v13 STRM markers confirmed execute/get 0/put 1. V13 DSP
queue 0/from-window empty 0/count 1, ARM get after markers pending,
delete/FINAL/EXIT −33. Normal after each variant returned exact GET; clock logs
restored 1ABC8073… . File restore does not prove clean DSP exit.

E90 v8 info after failed guard was an ungated mistake: not stock timing
evidence. V14 ownRAM PASS 0/51a73cd2; fresh clock guard
m86/div3/HAL 330000/DSP math 220160; original clock log restored BE58F5EF… . Info
create 6652 µs clean; created receive get pending→delete/free 0→cancel −3,
EXIT/FINAL 0 without RUN. E90 normal E039E983… unchanged. Previous patcher
self-test −20 and reboot cause unknown.

Runner default 14; receive-created and RUN modes require successful preparation
≤10 min, saved/current DSP/hash, and uptime check. Failed guard is rejected
before START. Each mode saves prior journal and passes inspect.
README/BUILD/research/session updated; 26 new V13/V14/E90 small proofs added,
builds/artifacts metadata recorded. Private GitHub confirmed.

**Next:**
1. Readonly DSP actual shared record and static ARM reader/window/IRQ contract.
   Reader 801B3028 conditionally ror 16, consumer 8019B0A8 compares source with
   queue+16, DFC 8019BA84 invokes consumer. Runtime flag/source/DFC/mapping
   still unknown; do not call kernel internal pointers at random.
2. After new contract — fresh prep, one minimal message/lifecycle RUN,
   journal/recovery/exact normal GET on negative. Do not repeat V13 without new
   information. E90 new RUN after confirmed N95 lifecycle.
3. Hello/echo+delete/free/EXIT 0 before serial 0/Q15/three serialparallelruns.
4. Verify evidence, commit/push private checkpoint. F05–F08 in_progress; full
   objective not completed. Current turn — hardware progress.

16:10 UTC static message-window comparison completed: consumer N95/E90 744 B
differs only in nine relocated BL; reader E90803F7664 unique, DFC/config/window
setup byte-equal. Source/runtime/IRQ still unknown. Pycompile, check_state with
both artifacts, manifest paths, and diff-check passed; locally failed
preparation rejected before phone connection.

## V15 shared record, 16:14 UTC

N95 fresh preparation `stream-v15-records-prepare-01` complete=true: stock
m86/div3, original clocklog returned, host/DSP/hash GET-equal. Host v15
supplements STRM marker readonly first-record snapshot, protocol 15. Info create
10559 µs clean; actual RUN `stream-message-records-v15-01` preserved expected
record words 0000/0600/000F/0001/0000/77E0/0000/77E0, fromDSP empty 0/count 1
before and after copy. Ror 16 gives cmd 600/arg1 F0001/arg2/source 77E0. Raw ARM
source 77E00000 does not match env 77E0. Runtime flag unknown, therefore this is
not a proven cause of pending ARM get. Get/delete/FINAL/EXIT −33; process
completed, no KILL. Recovery 01 obtained log 4189 B BBFE109C… and returned
exact normal 5B6BE15B… GET-equal; INFO startTick 7928381 unchanged/PS0. E90 v14
did not participate in this RUN.

Further static object tracing corrected reader flag association: 8019BC8C →
context+24, 801AA98C → (context+48 object)+164. Byte+64 of this embedded
memory-interface is not identical to processor+64/configuration 588 from the
exit-path code. Script and metadata updated; getter/setup E90 byte-equal. Report
corrected, without altering historical facts of hardware runs.

V15 builds ARM/DSP stage/normal EXIT_CODE 0. Smallproofs
n95-message-records-v15.txt, n95-v15-records-preparation.json,
n95-v15-records-recovery.json, stream-v15-records-artifacts.json. Current
source/runner 15, E90 installed 14 requires explicit --host-version 14; N95
installed 15. No full messaging/lifecycle or parallel proof, F05–F08
in_progress. Private checkpoint 24d82ce earlier synchronized HEAD; commit of
this addition to be verified via git log and remote main.

TSK alternative: primary TI C55 DSP/BIOS API guide read, native 24B0FC–24B130
confirmed default attrs 14 C55 words/priority −1 and TSK_create. Arg ABI,
termination, and stream cleanup before TSK_delete not yet established; no
hardware worker test. This is the next independent static action if readonly
runtime reader/IRQ check requires additional contract.

Latest INFO/PS/GET confirmed availability of both phones and PS0; normal N955B6BE15B…/E90 E039E983… GET hashes exact. No running PC sessions. Evidence
stream-v15-checkpoint-device-status.json; native TSK creation site 56 B
byte-equal N95/E90 according to n95-e90-native-tsk-create-contract.json. Next
gate — runtime reader flag/IRQ or TSK Arg/termination ABI, not repeat of v15.

## Native BIOS worker-once — 2026-09-30

DOFF extraction checksum-verified, packet instruction bytes unchanged;
common raw exact-equal 65266 B. .bios dis55 now valid; previous exploratory
per-four-byte reversal/error-loading outputs were invalid and not used. Native
Arg 32 pointer/XAR ABI established (long declaration would be wrong). TSK attrs
14/stat 22 words, mode 14/terminated 3, eight pointer Args, entry AC0; cl55
assertions and emitted assembler agree. N95/E90 TSK ranges equal apart from
seven verified symbolic BIOS data addresses.

CREATE_WORKER_ONCE DLL 3172 B 0709550C… checks caller priority <15, finite
callback marker/cookie 00123456, stat.mode 3, TSK_delete before create return.
No callback STRM/locks/resources; no official node RUN, no resident worker.
N95 v15 info create 10131 µs/delete/free/FINAL/EXIT 0; E90 v14 info 9368 µs same
0. Fresh preparations/stock guards passed; original clocklogs returned. Both
PS0, uptime/startTick continuous; exact phone normal DLLs restored GET-equal
N955B6BE15B…/E90 E039E983…. KILL and phone reboot were not needed.

Small reproducible proofs: n95-e90-bios-task-contract.json,
worker-once-artifacts/device-results.json, both worker-once txt/prep/recovery.
Normal PC DLL rebuilt after variant. Hosts unchanged N95 v15/E90 v14. F05–F08
remain in_progress: task ABI is proved, persistent STRM/Q15 and ARM parallel
work are not. Next independent gate: native loader handling of shared library
type 2 vs existing phase 3/4/5 and code/BSS lifetime across create/delete; use
no live worker until residency is established.

## Generic library residency and worker-parked — 2026-10-01 local

Static verification completed for native bridge/PDD/base DOFF of both phones:
compare_node_loader.py, n95-e90-node-loader-sem-contract.json. Library 3
missing/−6 has fallback 2; after generic selection there are no separate lists
1/2. Native create code is not unloaded immediately: it is resident in
CREATED; RUN unload under phase_split 1/dynamic 1. Created delete leaves create
loaded; free unloads loaded libraries. Storage vtable is taken from firmware
constructor literal, not code delta. SEM count/timeout T0, handle/attrs XAR0;
SEM_pend blocked mode 2, timeout in BIOS ticks. RMS create return AC0 relay and
signed host mapping −2 confirmed; positive 1234 not error gate.

Recovery N95 phase-control proc 42 retrieved journal 2039 B 81DC64C0…: create
0/7415 µs, delete −2, BEGIN close without FINAL. Joint check data/address
failed; what exactly changed is not separated. Connection lost during close;
later uptime lower, daemon new. Restart reason unknown. Normal 5B6BE15B…
restored GET-equal; no new RUN before recovery.

Resident v1 generic DLL 2980 B 475EFB3B… and phase DLL 3136 B 488C980B… have
the same raw text CF27629B… and initialized data stamp 1BADB002. Generic create
verifies init, changes stamp C55DC0DE; delete verifies stamp and the saved
delete address. N95 v15 create 9307 µs, E90 v14 9735 µs; both
delete/free/FINAL/EXIT 0, without RUN. Exact normals restored.

Worker-parked DLL 3604 B A5B0AE7B… library 0/2, 16 imports in both bases. Create
SEM 0/TSK priority 15 stack 1024/sys 256; callback stores cookie 00123456, stage
C551, and SEM_pend 30000 ticks. Create gate stat.mode 2. Delete re-checks
blocked 2, SEM_post -> callback stage C552/pend 1/terminated 3, TSK_delete ->
SEM_delete -> ordinary STRM/MEM cleanup. N95 v15 create 9063 µs, E90 v14 7293 µs;
both delete/free/FINAL/EXIT 0. In callback there was no STRM. This is evidence
of task lifetime after create and join in delete via conditional returns hashed
artifact; ARM did not log task fields independently.

In four new positive runs fresh stock guards passed, original clocklogs
returned; daemon startTick stable from prep to recovery. Both PS0 and exact
normal DLLs GET-equal N955B6BE15B…/E90 E039E983… . Hosts remained N95 v15/E90
v14, SIS not changed. Journals, prep/recovery, and small reports moved to
docs/evidence/2026-09-30; UTC timestamps before local midnight. Tested v1 DLLs
archived in ignored evidence. Normal PC build after variant EXIT 0; source adds
null env/context guards.

Next: ARM STRM transfer gate in CREATED, separate host mode without RUN, DSP
stream worker with explicit stop/finite wait/join and buffers ownership. One
packet clean exit -> multi-packet/Q15 -> three same-condition serial/parallel
runs -> E90 port/new SIS -> measured application choice. Parked priority 15 only
stores/wait/return; audio coexistence for MAC not proven. MSG runtime
reader/IRQ direction remains open. F05–F08 in_progress; full goal and useful
parallelism not completed.

### V2 audit — null-context assertions, 2026-09-30 22:42 UTC

During source review it was found that v1 delete returned 8000 on null moreEnv
before diagnostic checks. V1 positive results are not full proof of these
checks; limitation added to both v1 result JSONs. Source fixed:
CREATE_RESIDENT_CHECK and CREATE_WORKER_PARKED return 80008015 for null context,
env also checked. In worker-stream this rule will be mandatory.

V2 generic DLL 3000 B D229D53F…/7 imports: N95 create 9399 µs, E90 create 6744
µs. V2 parked DLL 3592 B ED8C2862…/16 imports: N95 create 7873 µs, E90 create
9277 µs. All four fresh prep/run/recovery 02 complete; create/delete/free/FINAL/
EXIT 0. Negative gates now mandatory for success. No official RUN/worker STRM.
Normal and original clocklogs returned GET-equal; PS0, startTick without changes
in each new prep→recovery. Hosts N95 v15/E90 v14 unchanged.

Authoritative v2 proofs: resident-generic-v2-artifacts/device-results.json,
worker-parked-v2-artifacts/device-results.json, both device v2 txt/prep/
recovery. V1 kept as history; negative split control remains in effect.
Worker-parked/resident-check/normal builds EXIT 0; normal main PC DLL rebuilt
after variant. Static comparison, pycompile, environment/manifest, and
source/evidence consistency to be checked before commit/push.

Next action remains STRM worker in CREATED with stop/join/cleanup, then nonzero
Q15 and same-condition serial/parallel. F05–F08 open.

22:45 UTC final readback: both phones online, PS0; host N95 v15 hash 45140071…,
E90 v14 hash 5F1C77CF…, original normal DSPs and ocprobe.log hashes match
expected exactly. worker-created-checkpoint-device-status.json preserves
INFO/PS/hash evidence. Final check_state with both artifact flags passed 4/8,
UTF8 feature titles/statuses unchanged, all evidence paths/JSON valid, git
diff-check passed. Source and small proofs ready for private checkpoint; raw
ROM/DLL/EXE/COFF/SIS and local backups remain ignored.

## Streaming worker in CREATED — plan for the next step

2026-10-01: both phones responded INFO/PS; no research processes. Native PDD
transfer excludes states 0/4/9/10/11/13, but allows CREATED=1; LDD copies
28-byte transfer and selects slots 52/60 without additional state gate.
Verification identical on N95/E90. Native NODE_wait allows NULL env: this is
waiting only for STRM, without altering RMS message queue. These static facts do
not yet prove hardware exchange with the new task.

1. Preserve reproducible static verification compare_created_stream.py.
2. Add generic library 2 worker: bounded stream wait, explicit last-packet stop,
   output reclaim, completion semaphore, and join before free context/code.
   Official execute of this variant must reject RUN.
3. Host v16: worker-one, worker-serial, worker-parallel without RUN; native mode
   2 buffers, sequence/length/echo/Q15 checks, and CREATED check before delete.
4. Clean one packet on N95 -> many packets reps 0 -> nonzero Q15 -> at least
   three same-condition serial/parallel pairs with useful ARM CRC.
5. New SIS E90 and the same checks; measure transport latency and application
   break-even. After each variant exact normal restore.
6. Record results and private checkpoint. F05–F08 remain in_progress; parked
   callback does not count as stream/parallel proof.

23:11 UTC N95 worker-one v16/DE7DF926…: create 0/10070 µs, 1 packet put/get 0,
errors 0, protocol 16/cookie valid, no RUN, state 1. Delete/free task/native
buffers 0, close returned. FINAL −20 only due to host expectation deleted 4:
wire task 3 actual 5. Native LDD 801B440C–4410 overrides PDD record with LDD
node+20; PDD internal 4 and reported LDD 5 — different enums. Recovery 01
initially only saved the journal/current DLL (restore_requested=false).
Preparation 02 correctly refused the still-installed diagnostic. Explicit
restore 01 then returned normal 5B6BE15B… exact; PS0/startTick continuous. First
run not counted as FINAL 0. Host expectation being fixed to 5; DSP build
unchanged. Repeat allowed by concrete established contract.

## Completed worker-stream series v16 — 2026-10-01

23:35 UTC checkpoint: both host v16 AB016003…; DSP worker DE7DF926…, library 2,
one create and 8×512 B in CREATED without official RUN. One/multi reps 0, Q15
reps 1000, and three pairs reps 10000 passed on EACH phone: sequence/length/
echo/dot/CRC/stop correct, delete/free/native/close/FINAL/EXIT 0. In this series
there is no reboot or KILL; task finished before cleanup. E90 v16 SIS installed
via observable daemon installer; GET EXE exact 24464 B. Negative first N95 run
and journal-only recovery preserved.

N95 pairs S/P µs: 406551/150968,399838/149868,249324/149593.
E90: 266809/160305,263363/164517,257351/159542. CRC 64 KiB executed by ARM
simultaneously with Q15 on DSP. Part of N95 serial intervals doubled; PRCM on
each packet not read. Percentages — provisional, not pure overlap gain. Raw CLK
ticks from reported 164 are not converted to DSP ms. Reps 0 observed completion
512 B N95335us/E90396us — not pure DMA latency/bandwidth.

Authoritative proofs: docs/evidence/2026-09-30/{n95,e90}-worker-stream-v16-
results.json, worker-stream-v2-artifacts.json, created-stream-contract.json,
worker-stream-v16-checkpoint-device-status.json, byte-exact phone journals.
Original DSP N955B6BE15B…/E90 E039E983… and original clocklogs GET-equal; PS0,
no active worker. Main normal DLL on PC rebuilt after variant.

Next steps according to unchanged work/PLAN.md:
1. Native N95 dvfs_interface reservation/release and per-packet conditions,
   minimum three same-condition serial/parallel pairs.
2. Cross-packet DSP timestamp calibration against ARM FastCounter; explicit
   error, without trusting counts/ms 164.
3. Required WSOLA/MDEC packet 1760/2048/2304 B and payback assessment.
4. Audit F05–F08 and remote checkpoint. F01–F04 complete, F05–F08 in_progress;
   full goal not yet reached.

## V17 completed on both phones — 2026-10-01 UTC

Checkpoint 1430722 with v16 pushed to private GitHub; subsequent v17 built and
verified according to PLAN_V17.md. DSP 4800 B 41D14CD4…/host 28456 B C8B08E8C…;
E90 SIS 16776 B 9C04181A… installed via observed installer, GET exact. MPU
reservation on N95 without PRCM/ROM patches: four native fingerprints, request
0/a2=100, per-packet 100%, release 0/status 0. On E90 branch not executed.

24 v17 runs successful: on each one, multi 0, Q15, three calibration, and three
pairs. In all, correct echo/dot/CRC/stop, CREATED 1→reported DELETED 5, join/task/
SEM/streams/context/native free/close/FINAL/EXIT 0. No RUN/KILL/reboot. N95 S/P
µs 251154/148953,250148/151211,249994/150205; raw dot ticks almost
identical. E90 259791/155729,258508/157467,263087/159878. Reduction ~40%
only for this synthetic dot+CRC load; application gain absent.

Short timer bounds N95 [19185149,19213529] Hz/E90 [19182339,19218353] Hz. In all
six 800 ms intervals DSP raw delta ~501 ms according to 19.2 MHz, ARM 828–876 ms.
Unknown whether idle DSP/timer gating or other reason; MPU DVFS alone does not
explain this. Do not use reported 164. Measure wall time with ARM counter.

Normal DSPs/original logs returned GET-equal, both PS0/INFO; hosts v17 exact.
Main PC normal DLL rebuilt. Authoritative docs/evidence/2026-10-01:
n95/e90-worker-stream-v17-results.json (raw journals/bounds), v3-artifacts,
n95-stock-performance-contract, worker-stream-v17-checkpoint-device-status.
Source/docs/small proofs ready for private checkpoint; raw firmware,
SIS/EXE/DLL/ASM/keys/screenshots/backups remain ignored.

Next work: larger 1760/2048/2304/4096-byte packets for evaluation of
WSOLA/MDEC/media transfer cost, timer/idle contract, and error lifecycle. Full
work/PLAN.md unchanged, F05–F08 in_progress; goal active, no blocker.

## V18: packets up to 4096 B on both phones — 2026-10-01

Plan recorded in PLAN_V18.md before edits. Native size-bearing instructions on
both ROMs show properties attr+4 -> RMS stream size+0 without scaling; stream
size — C55 words, transfer descriptor length — ARM bytes. DCD not changed.
Native buffers 4096 B each, worker protocol 18 accepts 256–2048 words for both
directions; entire payload echo is verified. Q15 remained 240 values.
Worker-transfer reps 0 excludes ARM CRC and repeated dot from measurement.

Host 29760 B 571C5A62…/DSP 4852 B DD8D50DC…; DOFF/22 imports/ASM verified,
immutable archive revision 4 preserved. E90 SIS v18 installed via observable
installer; GET EXE and runtime profile match.

On EACH: one 512/1792/4096, Q15 reps 1000×8 at 4096 B, and three ordered series
of 32 packets each for 512/1568/1792/2048/2304/4096 B. Total 22 runs/587
packets on each, FINAL/EXIT 0, no RUN/KILL/reboot, normal DSP GET-equal after
recovery. N95 MPU percent 100 on each packet. Medians completion N95:
335/518/518/549/610/885 µs; E90: 396/610/640/701/762/1129 µs. E90 outliers
1792=7812 µs/2048=7690 µs; not excluded. This is equal-size echo, not pure
DMA/bandwidth or application gain. WSOLA 1760 B payload requires 1792 B packet;
MDEC input 1536 requires 1568. Short output and actual kernel not yet measured.

Authoritative: docs/PACKET_SIZES.md, {n95,e90}-packet-sizes-v18-results.json,
n95-e90-stream-size-contract.json, worker-stream-v4-artifacts.json, raw
journals/preparations/recoveries in docs/evidence/2026-10-01. Helper
summarize_packet_sizes.py verifies each packet/result/CRC/MPU, raw hashes,
process statuses, and cleanup before publication. Normal main DLL on PC rebuilt
after worker variant. Source/docs/proofs being prepared for private push.

At 10:17 UTC later E90 GET once again confirmed original DSP/log and v18 host,
PS0, the same daemon startTick 75535. N95 twice had connect timeout after the
already completed series and exact recovery. Request to wake it sent; no new DSP
experiment after recovery. Current availability of N95 unknown.

After user response, N95 is available: original DSP/log and host v18 GET-equal,
PS0. Uptime 194682/startTick 93219 against test uptime 28049534/startTick
17620669 shows a new boot after the series; cause being clarified with the user.
No new DSP experiments in this boot. Authoritative live readbacks:
{n95,e90}-packet-sizes-v18-device-status.json and
worker-stream-v18-checkpoint-device-status.json in the same evidence dir.

Further according to full PLAN: actual WSOLA/ARM reference and asymmetrical
output, static audit error/delete lifecycle before negative hardware tests;
timer/idle and audio/long stability. Audit F05–F08 separately, without adding
unstated requirement of full integration into neighboring projects. Full goal
active.

V18 source/proofs/docs published in private main as 4d39a89, LOCAL=REMOTE
verified. Environment/artifacts/manifest gate 4/8; byte-exact staged audit 46
journals; report checks 22 runs/587 packets per device. PLAN_V18 completed,
while full PLAN and statuses F05–F08 remain open for next audit.

## V19/V20: exact WSOLA and final audit — 2026-10-01

V19 on both: 9 runs/195 correct packets, actual search/1792 input/48 output,
originals restored. ARMv5 baseline discovered that differs from current PS1
ARMv6 body; evidence preserved, comparison clarified by separate PLAN_V20.

V20 source/ARM/DSP/SIS built, artifact 6, ARMv6 codegen 244 B exact. SDK stale
object after MMP option edit eliminated before delivery; build.cmd clears both
research objects. Host 34196 B CBB91873…/DSP 5384 B 87EDE15C…; SIS 20 EAC61C9D…
installed on E90 observed UI, EXE GET exact.

On EACH v20: echo/control/search one and three paired 32-packet runs, 9 runs/195
packets (97 actual searches/97 controls/1 echo). ARMv6 median 999.45 µs; DSP
path with packing N95640.87us/E90732.42us, max671.39/762.94us. Paired
median saving 385.28/265.12 µs; create-only model 22/33 hops.
Algorithm/offset/score/count/checksum/stop and lifecycle correct, FINAL/EXIT 0,
no RUN/KILL, no daemon restart in v19/v20. N95 MPU 100% on each packet; fresh
m86/div3 guards.

Original DSP/clock logs of both GET-equal, PS0, host 20 GET-equal; normal main
PC DSP rebuilt. Authoritative docs/WSOLA.md, docs/evidence/2026-10-01:
n95/e90-wsola-v20-results.json, worker-stream-v6-artifacts.json, wsola-v20-
arm-codegen.json, worker-stream-v20-checkpoint-device-status.json.

Full PLAN audited in FINAL_AUDIT.md: F05/F06/F07 criteria of research prototype
and assessment fulfilled; F08 awaits final gates/private push. Limits timer/idle,
unsafe negative teardown, real audio/long sessions/application integration
explicit; no application speedup or production stability claimed.

## Full research PLAN completed — 2026-10-01

Source/evidence checkpoint e8f38c1 pushed and verified LOCAL=REMOTE, PRIVATE,
clean. Gates artifacts/environment/JSON/evidence paths/raw hashes and staged
audit passed. F01–F08 complete according to FINAL_AUDIT.md; prototype and
application assessment completed. Completion metadata concludes publication.
Limits error/unload, timer idle, long/audio, and application integration remain
explicit future integration gates; no new hardware runs needed.

## New assignment D0–D2: E90 checkpoint — 2026-10-01

This is a separate continuation after completed F01–F08, according to
PLAN_D0_D2.md. Initial HEAD b75853f; initial edits of APPLICATION_CANDIDATES.md
and added CODEX_TASK_2026-10-01.md preserved outside this commit. Only E90
192.168.3.21:2323; N95 received no commands. Its idle-first journal,
ocprobe.log restore, and cleanup of research files postponed to another
implementer.

D0 in_progress, **0/3 accepted RUN**. E90 native audit confirmed: failed delete
−2 still reaches internal state 4; destructor may free/unload code. Task 15/17
cancel index — value 0, adapter rc 0 does not guarantee completion. Host 21
retains pending/failed ownership via QUARANTINE without close/free; runner
deadline preserves journal without KILL. This is not proven safe cancel; manual
recovery required on failure.

Built ARM 35120 B 8FD9FAE1…/generic run-stop DSP 3900 B 7B07E8D0…; DOFF, 14 E90
imports, ASM, and four offline runner tests passed. DSP stop reclaim returns
0x8000 native wrapper without repeated input issue; delivery of EXITACK not
verified. SIS 21 A3592773… delivered as E:\c55stream-d0-v21.sis, GET-equal.
Installation requires human; HELP_NEEDED.md contains concrete step. Restore SIS
22 9C2D310E… prepared with exact original host 20 EXE; not yet delivered.

D1 pending: native reserve 27/map 31/unmap 34/unreserve 28 and map record 24 B
clarified statically. Address units, pinning/cache/endian/notify not yet known.
Mapping/ring 16 KiB and latency/bandwidth not performed; no negative conclusion
about zero-copy. Order of hardware probe — LIFECYCLE_DMM.

D2 in_progress: docs/PS1_CANDIDATES_2026-10-01.md ready as interim verdict for
old copy channel. Formula equivalent to S/N<A and W>H+D+S/N−A: H>A itself does
not exclude async. MDEC actual input 1536 B, RGB15/24 outputs 512/768; under 9
MB/s scenario even traffic floor 227.56/256 µs against A 50 µs. MIX-only SPU
sampled A 370–378 µs against mean PCM floor 326 µs: this is only 44–52 µs for
input/L/D/setup; maximum 914 samples cannot be compared with mean A. Under L 500
µs scenario blocking loses. Full SPU A 1585–1599 µs does not yet have measured
DSP kernel. WSOLA: 385 µs is paired saving N95, DSP path 641/732 µs N95/E90;
SMLAD 135–200 µs estimate only. For E90 at N 1000/create-only, independent
W>606/541 µs is required. W itself and ARM submission CPU time not measured.
Application gain not claimed; final D2 depends on D1.

Clock probes READ ONLY: CM_CLKSEL1_PLL 00056400, CLKSEL2_PLL 2, CLKSEL_MPU 2,
CLKSEL1_CORE 04360626, CLKSEL_DSP 343. In fact stock ARM 330.24/bus 110.08/DSP
220.16 MHz, no PRCM writes. Original ocprobe.log returned GET-equal. At 19:02
UTC GET of all 5 initial files exact: DSP E039E983…, stream log CFE4DF8B…, clock
log BE58F5EF…, host 20 CBB91873…, sys/hash B3AB7C72…. PS c55stream/ocprobe 0,
startTick 75535 unchanged; no new c55stream START/RUN.

Authoritative docs/evidence/2026-10-01: e90-d0-d1-native-audit.json,
d0-run-stop-v21-artifacts.json, e90-d0-session-checkpoint.json,
ps1-candidates-calculation.json; docs/LIFECYCLE_DMM_2026-10-01.md. Normal PC DSP
rebuilt after variant. Private/main GitHub live verified. Next: physical
install 21, inspect/clock/create, three clean RUNs, then D1.

Later installer observation attempt at 19:10:31 UTC got
`TimeoutError: timed out` in connect 3 s before any daemon command. At 19:02
remains last confirmed state; current availability of E90 unknown. HELP
supplemented with request to restore Wi-Fi daemon.

At 19:12:52 UTC second connect repeated TimeoutError before INFO. Hardware work
stopped until daemon returns; availability not termed confirmed.

Final offline gates passed: source/artifact/proof SHA256, all new evidence paths
and statuses D0–D2, repeated native audit and numeric D2 recalculation; Python
compile, environment/manifest 8/8, and four runner tests. Historical F01–F08 do
not substitute criteria of new assignment.

After publication 08ad9f9 response of human appeared in HELP_NEEDED via
orchestrator: SIS 21 installed, E90 daemon not yet available. Third connect
(verify 03) also got TimeoutError before INFO; limit 3 exhausted. Install 21 is
message of human, not GET-confirmation of new EXE. Only E90 Wi-Fi daemon needs
to be returned; repeated SIS install not needed. All five originals exact at
19:02 — historical checkpoint before this installation; current host/hash not
checked. DSP RUN was not executed in this session.

## Continuation of D0: three experimental RUNs, 0/3 accepted

Host 21 GET-proven 8FD9FAE1…; stock read-only clock 330.24/110.08/220.16 MHz.
Candidate 21: 8 correct packets, state 3, delete/status −2, QUARANTINE. After
human reboot GET journal CE5B1947… before new START/PUT; originals
DLL/log/clocklog returned exact. Candidate 22 (await RMS_EXIT after stop/output
reclaim): 8 correct packets, state 2, delete −33/pending. Host 21 GET of live
journal gave −14; after human reboot GET F35CDF7F…, originals again exact
restored. Before the first RUN there was a separate reboot between read-only
verify and failed connect clocks; do not attribute it to RUN.

Host 22 adds EFileShareAny. Package 23 SIS 0F8577C6… GET-equal, human install,
GET exact EXE 35120 B AFF498B8…/PS0/startTick 91233. Third RUN — generic
run-message-diag 3836 B B1CB8409…: 3 correct STRM snapshots,
NODE_getMsg(0)=0/putMsg(0)=1, fromDSP count 1, record cmd 600/arg1
F0001/arg2/source 77E0 after ror 16. After return message-get
−2/state 3/delete −2/QUARANTINE. Live journal D29CDA12… GET succeeded; host
sharing realistically verified. KILL 0, no new RUNs: limit 3 exhausted. Native
cause not yet proven; valid shared record does not prove IRQ/DFC, actual ARM
reader flag, or EXITACK delivery.

D0 remains 0/3; D1 hardware not open. Offline DMM reference audit clarified
candidate flags, C55 sample address/length /2 and flush/invalidate; this is
primary sample, not verified Nokia mapping. D2 provisional report preserved:
385 µs WSOLA saving, not DSP kernel; SPU mean PCM 2934.75 B not to be confused
with maximum 3656 B. Emulator and N95 were not touched.

Current dependency: human E90 reboot/daemon after third QUARANTINE, GET
journal/PS0 before write, exact DLL/log/clock restore; then restore SIS revision
25 with exact original host 20 EXE, installer, and GET EXE/sys/hash. Old restore
package 22 remained historical; after installing package 23 higher 25 is needed.
HELP_NEEDED has concrete steps. Do not call host restoration complete yet.
Evidence — e90-d0-resume-checkpoint.json; all 3 variants archived local, raw
logs/JSON published without binaries.

DOFF/import/ASM gates passed, five offline runner tests passed; normal PC DSP
rebuilt EXIT 0 after diagnostic. Native audit and numeric D2 reproduced;
initial user edits APPLICATION_CANDIDATES and task file left outside commit.
F01–F08 historical completion does not close D0–D2.

## Human decision and ROM reference preflight — continuation

HELP_NEEDED at 23:22 local conveyed human decision: general limit 3 RUN lifted;
only new documented hypothesis, maximum diagnostics, no KILL/unload of live
session. Previous entry about final stop due to limit is henceforth historical.
D0→D1→D2 continue.

Human reboot 23:27, GET final-recovery 01 journal D29CDA12… before PUT, PS0/startTick
61475; final-restore 01 original DLL/log/clocklog exact. Native E90
Z:\system\apps\strmcopy\strmcopydyn.dll55l GET 4396 B 99298562…; all DSP phases
executed by ROM code. Hypothesis control: custom execute/return versus
host/native lifecycle; 8 exact echo packets. Host 23 package 26 D383BF30…
installed, GET 36492 B 31836A0F…. Native-reference 01 ended select −6/FINAL
−6/EXIT −6 before allocate/create/RUN, without QUARANTINE. Thus at this moment
still THREE experimental RUNs. Reason for preflight: ROM .dcd_register only
properties:0, libraries 3/2 not registered. I did not check this before host 23
SIS; redundant installation. Native-preflight-restore 01 returned all 3 research
originals exact without reboot.

Research copy strmcopy-e90-library2.dll55l 4396 B 308090D3… changes only
registration:0→:2 and packet checksum (two byte positions 3807/3883). DSP
code/data/relocations exact unchanged, DLLdump PASSED; ROM/firmware not written.
Host 24 parse original ROM properties, then E research library 2. Hypothesis and
safe fail-stop unchanged; control does not close D0 own-node criterion. Host 24
package 28 CEB641F9… delivered GET-equal; install/GET still awaited in HELP.
Restore exact original host 20 ready as package 29 A2620208… for end of
research; EXE/hash now deliberately research, do not call full restore.

D1 statically added native MMU mask 803EF01C..803EF07C: endian bit 1, mixed bit
2, element bits 3..6; grammar matches TI header. Full path, address units/default
flags/cache/pinning not yet proven. Native() in old host requested fixed 4096 —
this is not proof of kernel maximum 4096; possibility of requested 16 KiB to be
checked separately after D0.

Current evidence checkpoint — e90-d0-resume-checkpoint.json and
native-library2-derivation.json; latest build/source proof native-copy-host-v24.
D0 0/3, D1 pending, D2 provisional. N95 received no commands.

## RUN4 native control and recovery 2026-10-02

Host 24 runtime/package 28 installed; native-reference 02 GET exact EXE
12356F00E0163EF0B0823A0E017D38A2796DCE83F2AB1FA85554DCFFF32A09D8. Separate ROM
properties 0 and research library 2 parse both 0, but select −6 before
allocate/create/RUN. Native-preflight-restore 02 returned originals 3 exact,
without reboot. Native-reference 01/02 do NOT add RUN to counter.

Combined reference 4476 B
C75723582115997EF143D23565587E3FA90AB24FB710F1BAB8AD4C69CBDDF8F8 adds 0+2 in
one registration packet, fixes section size/offsets and checksums; all
non-registration packets/code/data/relocations exact. DLLdump PASSED; derivation
and artifact 30 published. Native-reference 03 select/create/RUN 0,8 exact
echoes 512 B, checked 256 words each; wall_us 579/488/488/488/457/457/488/488.
Create 9674 µs. Delete −33/pending, state 2 before/3 after, QUARANTINE; live GET
journal A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1. This
is RUN4, KILL/unload 0, PRCM writes 0. Read-only frequencies again stock ARM
330.24/bus 110.08/DSP 220.16 MHz. D0 own 0/3, native control not counted.
Failure remained with unchanged ROM execute: localization to host/setup/native
path, but message delivery/cleanup/EXITACK cause not yet proven.

Human/user confirmed reboot after RUN4 and daemon startup 02.10 at 04:07 local.
Previous Codex process stopped due to usage limit, not device failure. In this
continuation attempt GET journal/PS0/restore NOT performed: three bounded
connect attempts to .21:2323 — Python 3 s, Python 8 s, .NET 8 s — timeout before
INFO. No new PUT/START/RUN. PC route 192.168.3.11/24 goes via Wi-Fi. HELP 01:12
UTC asks for daemon INFO/END, closing third-party TCP clients, normal restart of
daemon if needed; new reboot not requested. Original DSP/log after RUN4 not yet
restored; clock log was exact before RUN4. EXE/hash deliberately research 24, full
restore of original 20 also not yet done.

Next D0 hypothesis: own STRM snapshots before waiting for RMS_EXIT, after
NODE_getMsg, after idle/reclaim before return. Host must retrieve snapshots
during pending delete to separate EXIT receipt/cleanup/EXITACK, preserving
fail-stop. Do not repeat old RUN without change. First transport recovery, GET
old journal/PS0 and exact originals 3; then new diagnostic. If it establishes
and fixes cause, 3 consecutive own create/RUN/8 packets/delete/free/native/
FINAL/EXIT 0 with unchanged daemon startTick. D1 hardware does not start before
this. D2 prior-copy-channel provisional; emulator was not changed. N95 received
no commands; its idle-first/ocprobe restore/research cleanup remain postponed to
another implementer.

## 2026-10-02 13:35 — RUN4 recovery completed, host25 diagnostic prepared

After human reboot 13:21 `native-recovery03` (bounded 45 s) GET-ted journal
before PUT/START. SHA exact, as in live RUN4:
`A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1`. PS
c55stream/ocprobe 0, INFO screen 800x352/startTick 81256. DSP research reference
C7572358… confirmed by GET. `native-restore01` returned saved original DLL 3668
B E039E983…, log 21528 B CFE4DF8B…, ocprobe.log 1249 B BE58F5EF…; each
PUT→GET exact. Host 24/hash remain experimental.

Built host 25 EXE 39504 B
`CB74DE96012E3C9D4D7DDE6F783C6A746F75713B83DBF136DF03001C7035CA0A`, own DSP
`run-exit-diag` 5144 B
`29069D525B9209CA808F0D9315AA23BACCF222B44B6D6ABEFFC0B37B8EBB2833`. Builds
ARM/DSP/SIS bounded EXIT_CODE 0; DOFF/ASM and 18 baseimage imports verified;
immutable artifact revision 31. New mode `exit-stages`: 8 protocol 21 full
payload packets; snapshot stage 4 before NODE_getMsg; combined stage 5 after get
and stage 6 after input/output idle, protocol 25, 512 B offsets 0/96 C55 words.
Raw MSG headers/records read-only; snapshots not atomic. Host output request
ordered before control 6, persistent descriptor/status held until completion or
QUARANTINE. Extra output after idle affects cleanup; only clean delete proves
final reclaim/idle/EXITACK, diagnostic not included in 3 regular D0 cycles.

`exit-diag-sis01` delivered `E:\c55stream-exit-diag-v25.sis`, package 31, 22416 B
SHA 8D0E3BE8…; GET-equal, PS0, unchanged startTick 81256. HELP 13:35 asks human
to install this SIS, notify, and leave daemon. Restore SIS 32 ready with exact
saved original host 20 EXE, SHA 6E6C81E0…; not yet delivered or installed.
Awaiting installation of host 25, did no new RUN: experimental 4, own D0 0/3, D1
hardware pending, D2 provisional. No new PRCM writes/phone KILL/N95 commands.
Published 88 raw proofs; checkpoint hash/native audit/calculation PASS.

## 2026-10-02 13:43 — RUN5: RMS_EXIT and first idle proven, delete pending

Human via orchestrator at 13:38 authorized replacement of our EXE/hash without
installer: E90 hack active. `host25-deploy01` backed up host 24 EXE/hash GET
before PUT, saved originals 20/hash verified; host 25/hash GET exact (EXE
CB74DE96…, hash 20 B SHA-256 EDDE22CA…). SIS 31 was not installed; physical
installer no longer needed.

`exit-diag01`: fresh read-only clock m86/div3, ARM 330.24/bus 110.08/DSP 220.16
MHz, restore clocklog exact; inspect/create preflight FINAL/EXIT 0, unchanged
daemon startTick 81256. One new own diagnostic RUN5: create 8941 µs, RUN 0, all
8 packets 512 B/240 checked payload words correct, timings
457/396/396/366/366/396/396/396 µs, median 396/range 366–457, total 3169 µs.
These numbers diagnostic, not D1 and not application speedup.

Stage 4 before exit: pending input/output 0. Stage 5 NODE_getMsg result 1, waits
1, cmd 80000000/arg1=env 77E0/arg2=0/status 00008000. Stage 6 after
STRM_idle(input/output): both rc 0, pending 0/status 00008000. RMS_EXIT receipt
and first cleanup in this RUN physically proven. Stage 6 precedes extra output
reissue/reclaim/idle: actual last idle, execute return/EXITACK, and native
delete callback not yet proven. Delete submit 0/pending, after 5000 ms
−33/pending; state 2→3, QUARANTINE. Local runner 30 s timeout without
KILL/free/close. Live journal GET successful:
`778039EBA2B21B3A07F65FB7EDF89040F2BBB386CF1C11B84157B76023F1691E`.

HELP 13:43 asks human reboot E90/daemon; only after confirmation GET
journal/PS0, then originals 3 exact restore. DSP/log now research 25, clocklog
exact restored before RUN5; host 25/hash research and hold ownership. Do not do
new unchanged RUN. D0 own 0/3, experimental 5; D1 pending, D2 provisional
unchanged. ARM outbound MSG reader flag actual value, IRQ/DFC/EXITACK, and native
callback still open. N95 without commands; its idle-first/clocklog/research
cleanup postponed to another implementer. Published 97 raw proofs; original host
20 direct restore permitted, but do only after PS0 and originals 3 restore, not
under live owner.

13:54 `exit-recovery01` read-only GET journal/DSP + INFO/PS: journal SHA
778039EB… unchanged, DSP 29069D52… unchanged, c55stream PS1/ocprobe 0, startTick
81256 unchanged. Phone/daemon respond, but reboot did not take place and
QUARANTINE owner still alive. Restore/new RUN currently prohibited by ownership
guard. Human request 13:43 active; no additional PUT/START/KILL. Evidence of this
read-only check also published.

## 2026-10-02 — recovery RUN5 and new outbound MSG hypothesis

Human reboot after RUN5 confirmed. `exit-recovery02` GET journal SHA
778039EBA2B21B3A07F65FB7EDF89040F2BBB386CF1C11B84157B76023F1691E, PS
c55stream/ocprobe 0, INFO screen 800x352/startTick 65704. `exit-restore01`
returned original DLL/log/ocprobe.log PUT→GET exact. EXE/hash research 25; full
host 20 restore not yet done. No new RUN.

Static wrapper 24E6F0 after execute return itself does NODE_putMsg cmd
40000000/arg1=return/arg2=0/timeout FFFF. MSG_fromDSP 24C928 copies native long
fields into window, sets empty 0 and interruptGPP. C55 board 803F0208 uses common
base +8; getter +164 therefore points to embedded interface +172. Init 803F03C0
explicitly writes byte 236=1, that is reader byte 64=1. IVA +164 without this
store — another board. This clarifies static initial state, does not measure
runtime value.

New check `worker-message`, host 26/protocol 26/artifact 33: finite priority 15
worker is created in create and waits for one STRM input; host prearms MSG
receive and STRM output in CREATED before trigger. Worker sends NODE_putMsg
606/A1B2C3D4/env, read-only MSG/window snapshot 7, reclaim/idle, and returns.
Created delete joins terminated worker before free. There is no official RUN or
wrapper EXITACK: this separates outbound ARM MSG reader from execute return
without a new RUN. Previous RUN3 armed receive only after execute return; its −2
did not prove delivery. Success of this diagnostic does not count toward D0.
Pending/failure preserves ownership; no KILL/unload of live owner. Build
ARM/DSP/SIS EXIT 0, DOFF/ASM and 25 base imports checked. Host direct replacement
permitted. After one diagnostic save journal/PS, restore 3 if PS0. D0 own 0/3,
experimental RUN5; D1 hardware only after D0; N95 without commands.

### Created-worker preflight result, 15:16–15:21 local

Host 26 GET exact 40920 B
2EAC917E90CF78F18A6EA1DBD9EE117FF9CB2398C6269414E559B4140758D787, DSP 5616 B
71B4D893956BEBD2575D0CF6A50706D75FC71AFD69F0D74B8EFBCD78ED0BC265.
`worker-msg01` completed inspect 0 and create 0/7598 µs; active worker waited
for input. Create-only preflight moved to delete without native buffers and
trigger: delete −33/pending, state 1 remained 1, QUARANTINE. Did not reach
official RUN or outbound NODE_putMsg 606. This is new problem of no-input
stop/join/idle, not negative MSG result. Runtime setter flag 1 and source
binding proven only statically, physical delivery of MSG not added.

Live journal GET 2092 B
B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92.
`worker-recovery01` read-only at 15:21: same journal/DSP SHA, INFO screen
800x352/startTick 65704 unchanged, c55stream PS1/ocprobe 0. Live QUARANTINE
owner blocks restore and next launch. HELP 15:16 asks reboot/daemon; KILL 0, no
additional PUT. Initial E: files were exact after RUN5, now DSP/log research 26;
clocklog original exact. Host 26/hash research remain; full original 20 restore
not done.

Comparison of archived e90-worker-stream-one-v17/prepare showed: old successful
streaming worker always received final input, create-only preflight was not done
for it. Thus reuse of new create-only preflight was redundant. Session script
now skips it only for worker-message: immediately prearmed MSG/output→single
final input, reclaim/idle→terminated worker→created delete. This is not a fix
and not proof of stop without input. Do not start anything before human reboot
and GET/PS0/originals 3 restore. If subsequently MSG passes, ARM reader is
separated from wrapper return; if not, raw snapshot/pending receive localize
channel. D0 own 0/3, experimental RUN5 unchanged; D1 pending; D2 provisional.
Orchestrator separately reported its single LS E:\PS1\cfg\ on E90, without
write/START; its fact is not included in our experiment/RUN counts.

## 2026-10-02 21:16 local — familiarization after transfer, both phones available

The user permitted both N95 and E90 for testing; the previous prohibition of
polling N95 in CODEX_TASK_2026-10-01.md is no longer in effect. The goal remains
asynchronous DSP work in parallel with useful ARM work.

Read-only INFO/PS verified at explicit addresses without fallback:
N95 .22:2323, screen 320x240, startTick 22918156, c55stream/ocprobe PS0;
E90 .21:2323, screen 800x352, startTick 65704, c55stream PS1/ocprobe PS0.
E90 GET E:\c55stream.log: 2092 B, SHA-256
B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92, exactly
matches created-worker preflight 15:16; delete −33/pending, state 1,
QUARANTINE. Local copy: out/reorientation-e90-journal-20261002-211633.log.
Thus the previous owner is still alive; before PUT/START/restore, human reboot
of E90/daemon, repeated GET/PS0, and originals 3 exact restore are required.
There were no new phone PUT/START/RUN/KILL, experimental RUN5 and D0 own 0/3.

On the current PC python/python3/py not found in PATH; bounded calls to
strict_net.py completed before connecting. INFO/PS/GET performed via .NET TCP
with connect/read deadlines 3/5 s. Before restoring Python runners, it is
necessary to find or restore Python and check toolchain/SDK paths. Git HEAD
bac5ffa, uncommitted edits and new evidence from the previous session
preserved; in this familiarization commit/push were not performed.

## 2026-10-02 evening — finite MSG diagnostic of E90 and N95, full restoration

According to user report, E90 was rebooted. laptop-recovery01: GET old journal
2092 B/B9B4E282… exact, DSP 71B4D893… exact, PS0, new startTick 61087.
laptop-restore01 originals 3 PUT→GET exact. Found Python 3.12 via
C:\Program Files\LibreOffice\program\python.exe; check_state verified SDK/toolchain
on D: and TI CGT 4.4.1 on C:.

E90 laptop-worker-msg01/host26: finite final input, prearmed MSG/output, DSP
put 1, stage 7 cmd 606/A1B2C3D4/env 77E0, STRM completions 0/0. ARM receive
−33/pending; created delete 0/DELETED 5, task/native free 0, close passed,
FINAL/EXIT −33 due to receive. No QUARANTINE/reboot. Host 27 added raw record
and after-delete status, and receive after output. laptop-worker-queued01 and
laptop-worker-prearmed27: same DSP put 1/snapshot; ARM receive −33, cmd/args 0,
status pending before delete, clean delete/free/close. Do not repeat these three
E90 variants without new evidence.

Host 28 allows same finite diagnostic on confirmed N95 profile. Before
replacement, snapshot 5 in work/evidence/n95/d0-20261002. All 25 candidate
imports exist in saved N95 baseimage. First preparation worker-msg01 rejected by
stock guard before DSP START: N95 has existing m111. Read-only exact profile
guard for finite MSG confirmed PLL 0006F400/sel2=2/MPU 2/core 04360844/DSP 23C3:
according to registers ARM 426.24/bus 213.12/DSP 284.16 MHz. No PRCM writes;
this is not a performance benchmark and not per-packet DVFS proof. worker-msg02
gave same receive −33/empty record, DSP put 1/snapshot, and clean created
delete/free/close. Thus problem reproduces on both; concrete ARM
mapping/reader/source/IRQ cause not yet proven. Snapshot header empty_after 1 is
not sufficient proof of DFC.

On both, **all 5 originals** returned, including EXE/hash, PUT→GET exact.
laptop-final-verify01/E90 and final-verify01/N95: host 20, c55stream/ocprobe PS0,
startTick 61087/22918156 unchanged. New official RUN 0, KILL 0, reboot 0 in
finite series; historical experimental RUN5, D0 own 0/3, D1 hardware pending, D2
provisional. No-input worker cleanup not fixed.

Local host 28/protocol 26/artifact 37, ARM builds 27/28, and SIS/import/DOFF
checks successful; 8 offline session/clock guards tests pass. Evidence
published by tools/summarize_worker_messages.py, single current checkpoint —
docs/evidence/2026-10-02/worker-message-checkpoint.json;
e90-d0-resume-checkpoint.json also updated with these results. Report —
docs/WORKER_MESSAGES_2026-10-02.md. Physical actions not needed now. Next: trace
runtime pointer of ARM window/reader/queue and prepare bounded read-only
snapshot with verified bounds. Only after new proven hypothesis — next MSG/RUN.
Emulator was not changed.

## 2026-10-02 — resumption of host29 diagnostic, ARM pointer audit, and exact restore

After user request to continue, uncommitted host 29 edits and session
work/evidence/e90/d0-20261002-pointer found, which were newer than STATE.
Previous turn already installed host 29 and performed patcher-read-check: three
copies of 24 B from own RAM, ROM 803F7664, and BSS C8010B20 to own buffer,
FINAL/EXIT 0, DSP open 0/kernel code writes 0/PRCM writes 0. Not repeated.
resume-reader01 repeatedly retrieved journal SHA
56167F767D4B30FF225DA24BFB0F6666FD25F16B9FB22B1398D4DBB911195D76, PS0/startTick
61087; original DSP E039E983… unchanged.

New offline tools/rev/audit_arm_message_runtime.py checked 28 instructions, 2 BL
targets, BSS header, and reader code. Board+264→context 364 B, context+48=board+8,
context+24=reader=board+172, reader byte 64=board byte 236 initialized 1. Reader
DWORD0 is shared base; fromDSP header context+224, records context+240=header+8,
queue source 16, pending 40. BSS C8010B20 — flags, not MSG root; runtime swap
byte not read. Live board/context root, its lifetime, and mapping bounds still
need to be proven via audited native object lookup. No new MSG/RUN on
assumptions.

Read-copy validator reinforced: exact words/source/size/order/destination,
firmware/profile, no DSP open, and FINAL 0; handles native CRLF. 9 offline
session tests passed. Source/EXE host 29 hashes exact artifact 38; successful
bounded ARM build in previous turn, no new source change of ARM. check_state
-RequireArtifacts -RequireStreamArtifacts successful.

resume-restore01 + resume-hostrestore01 returned all 5 originals of E90.
resume-finalverify01: each GET/SHA exact, host 20, c55stream/ocprobe PS0,
startTick 61087 unchanged. N95 in this continuation without commands; its last
proof remains restored host 20/PS0. New MSG/RUN/KILL 0, D0 own 0/3, historical
experimental RUN5, D1 pending, D2 provisional. Physical action not needed.
Publication of 16 raw proofs: tools/summarize_arm_message_runtime.py; current
checkpoint docs/evidence/2026-10-02/arm-message-runtime-checkpoint.json, report
docs/ARM_MESSAGE_RUNTIME_2026-10-02.md. Next — live root provenance, not repeat
of failed receive. Pre-existing docs/APPLICATION_CANDIDATES.md edits remain
separately in working tree.

## 2026-10-02 — handoff to agy

The user asked to save summary for agy. Complete handoff:
work/HANDOFF_AGY_2026-10-02.md. It contains current D0–D2 criteria,
proofs/restore, permitted and verified push 5fc3071+26d6354, new offline
container-root/factory/manager analysis after commit 26d6354, and next actions.
No new phone commands after restore. Runtime container root C80019D4 derived
only from saved kernel export 251; bounds/type/lifetime still require audit.
D0 own 0/3, D1 pending, D2 provisional unchanged.

## 2026-10-02 (agy continuation) — offline audit of kernel containers root, PDD factory, and manager

Step 1 of the handoff next actions completed: offline audit of the kernel
root containers, array bounds, object types, PDD factory vtable, and the
pointer chain to the board and context fully completed.

1. Kernel containers root (export 251 `Kern::Containers`):
   E90 export `80037778` loads literal `80038084` = **`C80019D4`**;
   N95 export `8008CE40` loads literal `8008DC1C` = **`C80019F0`**.
2. Array bounds and object types:
   System call `TFindHandleBase::NextObject` (`ekern.exe` `8002B930`)
   checks `8002B934: cmp r0, #17` (exactly 17 containers, types 0..16),
   when exceeded raises panic `movcs r0, #25` (`EBadObjectType`).
   The array contains 17 words (68 bytes, for E90 `C80019D4`–`C8001A18`), which
   is confirmed by check `8003FCD0: cmp r4, #17` with literal `C8001A18`.
   According to `euser.dll` `TFind*::Next` opcodes, confirmed: type 10 — `DPhysicalDevice`
   (PDD slot `C80019FC` on E90, `C8001A18` on N95), type 9 — `DLogicalDevice`
   (LDD slot `C80019F8` on E90).
3. Structure `DObjectCon` (kernel export 12 `80038290` / `8008D638`):
   `+16` — `iCount`, `+20` — array `iObjects`, `+24` — mutex `iMutex`.
4. Identification of factory `ehwaomap` (PDD export 1 `803DD8A4` on E90, `80199254` on N95):
   allocates 120 B, constructor sets vtable **`803F8380`** on E90
   and **`801B3D44`** on N95. Among objects of PDD container, factory is found
   by rule `*(TUint32*)obj == 0x803F8380` (on E90).
5. Processor 0 manager (DSP):
   stored in `factory + 48` (allocation of 68 B), constructor `803E32E8`
   sets magic word `434F5250` ('PROC'), `manager + 56 = factory`,
   `manager + 60 = 0` (DSP).
6. Board interface (`board`):
   manager setup `803E3348` allocates 336 B (constructor `803EFFCC`),
   adds 8 and writes `board + 8` into `manager + 44`.
   Base address of the board: `board = *(TUint32*)(manager + 44) - 8`.
7. Full chain to shared memory:
   `board + 264` → context (364 B), `context + 48 = board + 8`,
   `context + 24 = board + 172` (reader), `reader byte64 = board byte236` (1),
   `reader DWORD0` = ARM base address of DSP shared memory,
   `context + 224` → header `fromDSP`, `context + 240` → `records = header + 8`.
8. Added reproducible tool `tools/rev/audit_kernel_containers.py`,
   publication script `tools/summarize_kernel_containers.py`,
   evidence `docs/evidence/2026-10-02/kernel-containers-audit.json`,
   report `docs/KERNEL_CONTAINERS_ROOT_2026-10-02.md`.
9. Regenerated disassembler `out/e90-ldd-disasm.txt` with actual base `803F8648`.
10. Unit tests in `tools/test_e90_task_session.py` expanded with check
    of container root and factory (10 tests pass); `check_state.ps1` successful.
11. At the time of this offline audit, phone operations had not yet been executed.
    Later state given in checkpoint below.

## 2026-10-03: continuation after Gemini, native source collision

This checkpoint supersedes earlier assertions about current phones/counters.
Gemini performed live pointer snapshot and several failed RUNs, but D0 remained
0/3. Review: work/GEMINI_REVIEW_2026-10-03.md.

E90 available, PS0/startTick 33897. Last Gemini create 32 journal obtained: ends
BEGIN select node, before create/teardown. Original DLL/log/clocklog returned
GET-equal; EXE/hash restore blocked by ERR open −46 in C:\sys\bin. Open4All
required. Recovery/restore: d0-20261003-cycle2/codex-*.json.

N95: one new official diagnostic RUN transferred 8 correct packets 512 B, 2987
µs; delete −33/pending, not accepted D0. Snapshot before delete revealed two
queues source 77E0: old node C81CF8D0 and new C81BBDE0. After delete fromDSP
record — EXITACK 40000000/EOK 8000/source 77E0. Old node env cleared, new
remained pending; routing selects first match. For causal check N95 reboot
needed, requested from user. After GET journal authorized KILL, then 5 originals
SHA-equal restored, PS0/startTick 132858:
d0-20261003-codex-routing/finalverify01.json. Clocks confirmed stock m86, ARM
330240/BUS 165120/DSP 220160 kHz.

Host 33 removed unconfirmed NULL-status/two-delete code of Gemini, added
read-only routing diagnostics. Host 34 has pre-RUN unique-source gate: duplicate
source→refusal before RUN and cleanup only of its own CREATED node. 13 offline
tests pass. New host 34 not yet tested on hardware. DSP bit-exact candidate
41/42; existing delay hypothesis not proven. Document:
docs/MESSAGE_ROUTING_2026-10-03.md; JSON checkpoint and native audit in
docs/evidence/2026-10-03. D0 0/3; D1 pending; D2 provisional. Old historical
RUN5 is not full counter after Gemini.

## 2026-10-03: after preparing phones, host35 without PROC_Load

Previous Open4All/reboot requests fulfilled: E90 five originals restored
codex-verify02, N95 new startTick 64375. Both available, originals backup in
work/evidence/{e90,n95}/d0-20261003-clean34.

Host 34 candidate 46 d0-sequence: inspect/create clean on both, first RUN guard
refused before execute — source 77E0 matching 2. Cleanup of CREATED node, task,
and two native buffers completed 0; FINAL/EXIT −11, no quarantine. Both devices
have old standard queues 77E0/7700 even after reboot.

Established: host 34 each time PROC_Load-ed shared base. Offline ROM audit on
N95/E90 confirms unconditional stop before load/start, manager state 4 is
running. Host 35 candidate 47 removes PROC_Load, checks running base via
validated manager, and connects to it, preserving unique guard. 14 tests pass,
bounded ARM/SIS build 0, DOFF/import/artifact checks pass.

Host 35 installed and tested on both: attach gate 0, create/delete/free 0, RUN
guard −11 before execute due to conflict remaining after host 34 reload. No new
official RUN during four guarded refusals. D0 remained 0/3; D1 pending; D2
provisional. On both, originals 3 DLL/log/clocklog restored GET-equal, host
35/hash deliberately installed; originals EXE/hash preserved. attach-verify01:
PS c55stream/ocprobe 0, E90 startTick 33897/N9564375.

Async requested from user new reboot of both and daemon/Open4All: host 35 cannot
fix already inconsistent old queues. Next check changed startTick and run
d0-sequence35/candidate47 with tag attach-sequence02 in the same session of each
device, without new snapshot of host 35 as original. Exact commands and all
limitations — docs/BASE_ATTACH_2026-10-03.md; reproducible checkpoint —
tools/summarize_base_attach.py.

## 2026-10-03: static preparation of D1 while awaiting reboot

Repeated INFO check: E90 startTick 33897/N9564375, no new boot yet. Previous
goal turn yielded progress (host 35/commits/evidence); hardware dependency in
this continuation is the same. No new DSP RUN or mapping.

Retrieved E90 Z:\sys\bin\ebridgeutil.ldd read-only GET 1260 B. New
tools/rev/audit_dmm_ownership.py compares actual kernel export targets, 19
ARM+13 Thumb checks, and all 5 utility BL on N95/E90; identical dispatch and map
wrapper confirmed by hashes. Pages are pairs of 32-bit linear/physical, map
signature has output pointer as fifth argument and flags as sixth. Fn 2
DoControl(2,&address,&bytes) clean 378→invalidate/prepare 376; fn 1 only copy
719 and translate 245, without pin/unpin API. Source names compared with
official Symbian kernel exports; reference SHA preserved.

D1 probe ownership/ring layout 16 KiB TOTAL clarified in docs/DMM_ABI_2026-10-03.md.
This is static preparation, not opening of hardware D1. Pinning/native chunk,
DSP units/cache/order, correctness/wrap/teardown, and measurements not yet
proven. Previous statement "ebridgeutil mem-pin" in findings corrected. D0 as
before 0/3; next hardware action — fresh boot of host 35 candidate 47.

## 2026-10-03: physical pools audit and awaiting external step

Last goal turn was progress: DMM ABI audit a7e51ab pushed. Again INFO/PS
confirmed E90 startTick 33897 and N9564375, c55stream 0; reboot for host 35
still not confirmed. This is the third consecutive goal turn with the same
physical dependency (the first — after preparing host 35).

Static preparation supplemented with physical pool record on N95/E90: owner
+244, Epoc::AllocPhysicalRam 242, DPlatChunkHw::New 60, paired
Epoc::FreePhysicalRam 241. Audit of 23 instructions + 6 actual import calls on
each firmware, attrs raw 1044. Important evidence limit: these pools not yet
connected to candidate native ARM buffer; ring pinning/lifetime not claimed.
Host/DSP binaries not changed.

Next necessary decision depends on fresh hardware D0 evidence. Do not execute
new RUN in old conflicting state. D1 hardware prohibited before D0, D2 without
measured D1 does not complete. Valid request reboot/daemon/Open4All in
HELP_NEEDED.md; after it exact host 35 candidate 47, new startTick, PS0, and
d0-sequence attach-sequence02. Plan not completed: D0 0/3, D1 hardware pending,
D2 provisional.

Final verify 02 on both phones successful: three original DLL/log byte-equal,
installed host 35 matches built artifact, PS c55stream and ocprobe empty.
StartTick remained E90 33897 / N95 64375. Automatic continuation stops with
status blocked until new physical boot; this is not completion of plan. After
user report of reboot, continue from INFO check and D0 described above.

## 2026-10-03: D0 completed after new reboot of both phones

The user rebooted both and permitted independent installation. E90 startTick
60327 / N95 62209, PS0; host 35 exact built GET, originals 3 GET-equal.
attach-sequence02 candidate 47 completed complete=True: inspect/create and 3
consecutive ordinary RUNs on each, 8 correct 512-B packets/protocol 21/240
payload words; delete/free task/free native out/in/close/FINAL 0, EXIT 0.
StartTick unchanged in all steps. 6 official RUNs added, minimum historical
count 16; D0 accepted 3/3 on each. Copy-channel total/packet timings saved
separately; these are not D1 measurements and not application speedup.

attach-restore03 on both returned original DLL/log/clocklog GET-equal. Host
35/hash remain installed; original EXE/hash backup preserved. Evidence
docs/evidence/2026-10-03/d0-attach-success.json reproduced by
tools/summarize_d0_attach_success.py. D1 hardware gate now open: next — native
allocation/lifetime provenance and minimal reserve/map probe, then 16 KiB TOTAL
ring, ownership/wrap/cache/teardown/measurements.

## 2026-10-03: D1 partial hardware checkpoint, host42 prepared

D0 complete 3/3 on both preserved, commit 4edbb56 pushed. D1 host 41/candidate
54 protocol 38: native ordinal 30 allocation 16384 in CMM region 131072 B;
utility 1 confirmed 4 linear/physical pages. DSP mapped 00300000 BYTE → 00180000
WORD; flags 17. Flags 16 map returned 0, but DSP read zeros: this is a rejected
hypothesis, clean teardown/FINAL −20; native PDD bit 0=page-list translation
proven by static audit and correct data flags 17.

Ring TOTAL 16384: control 1024 + 15 input/15 output slots of 512 B each, payload
480 B/slot. Additional notifications allocations 2×4096 B separately.
Whole-region ownership, utility 2 clean→invalidate before handoff and after
completion, ARM does not access during DSP ownership. Release only after
delete/free task, then unmap/unreserve/free ring/notifications/close. Native
chunk attrs/DSP cache-order contract still partially inferred.

N95: three full series batches 1/2/8/15, 120 exchanges/run each, 9360 correct
packets. All input/output words, slot/sequence wrap/32bit carry verified;
delete/unmap/unreserve/free/FINAL/EXIT 0, unchanged boot 62209. Stock clocks
before/after 3 series ARM 330.24/bus 165.12/DSP 220.16 MHz. Exchange batch 15
p50 2716 µs, aggregate useful bidirectional bandwidth 4.996 MB/s. Measurement
includes synthetic transform/verify/cache/notifications; not application H+D.
RThread CPU measured; ARM useful parallel W was not executed. Full S includes
logging (~1 s setup), DSP ticks not converted. ring-final-restore01/host-restore01/
verify01 returned **all 5 originals** GET/SHA-equal; PS c55stream/ocprobe 0. N95
does not require physical actions.

E90: s1-b1/b2 complete, 360 correct packets, clean teardown, boot 60327. s1-b8
transport lost. After daemon returned: boot 33873/boot 1 by t, PS0; ring-recovery03
GET before any PUT saved journal C1EEA683…, last line ROUTING queue 1/node
c816a6b8. No ring allocation/map, own task create/RUN/FINAL. Reason for boot
change unknown; do not call this DSP batch 8 failure and do not repeat unchanged
candidate. ring-final-restore01 returned original DLL/log/clocklog,
completeTrue. ring-final-host-restore01 stopped **before PUT**: ERR open −46 on
GET C:\sys\bin\c55stream.exe. After reboot Open4All required; request async
sent. E90 EXE/hash currently host 41 research, originals saved.

Next hypothesis: initial non-atomic snapshot read 448 B of foreign native nodes,
whose lifetime candidate task handle does not hold. Host 42 candidate 55 removed
foreign-node dereference; own retained node and unique queue gate preserved.
This is not proof of reboot reason; list/queue reads remain non-atomic. ARM/SIS
builds 0, DOFF dump/imports 15 verified; candidate 55 **not installed/not run**.
Current out/arm — host 42, out/dsp — ring 52. Proof
docs/evidence/2026-10-03/d1-ring-v55-artifacts.json, SIS
out/sis/c55stream-d1-v42-r55_sha1.sis. Artifact 54 archive in
work/evidence/artifacts/c55stream-dmm-ring-v54; do not substitute with new build.

After Open4All E90: exact restore-host with NEW tag, verify all 5 originals; then
deploy-host42 + deploy-dsp ring with artifact-proof 55, finite inspect/provenance
gate, and 8-frame correctness up to 120 frames. If failure again — GET journal,
stop, without KILL/unchanged replay. Upon success three full series
`tools/run_ring_series.py --device e90 --host-version42 --revision55`
(CLI uses separate tokens: `--host-version 42 --revision 55`). Runner
stop-first-failure, boot unchanged in series. Do not mix 54/55 samples. Before
restore obtain all journals; finish 5-original GET/SHA verify.

Evidence: docs/DMM_RING_2026-10-03.md, d1-ring-results.json with samples/SHA,
tools/summarize_ring.py, native mapping flags audit. D2 conditional recalculated
by tools/assess_ring_candidates.py: correct 7200 B payload/direction, MDEC max 3
blocks without repacking, SPU int32 requires tiling; application-specific T/A/W
unknown. Emulator and user docs/APPLICATION_CANDIDATES.md not changed by this
continuation. D1/D2 in_progress, full plan NOT completed. check_state 8/8
pertains to old F01–F08; now also prints current D0–D2 statuses. Old goal
blockage after D0 reboot overcome; new physical dependency Open4All — first new
turn, not basis to repeatedly mark blocked.

## 2026-10-03: last state — E90 candidate56 interrupted s2-b2

The user enabled E90/Open4All. ring-final-host-restore02 and verify 01 proved all
5 originals before deploy 42. Candidate 55: provenance 0, short 8×batch 8
correct, s1-b1/b2 clean 360 packets, but s1-b8 transport lost. The user
returned daemon; ring55-recovery02 GET before PUT, boot 33372, PS0, journal
E4ED8570… ends DMM POOLS before broad board read. No map/create/own RUN.
Foreign-node-read hypothesis did not resolve the problem; neither kernel reboot
mechanism nor DSP failure proven. ring55-final-restore01/host-restore01/verify01
returned all 5 originals.

Offline saved E90 patcher.ldd SHA 423E4FF1… decompressed elf2e32 dump audited 22
words: control 105 destination=*a1, source=TDesC8::Ptr, length=low 28
descriptor; raw memcpy 725 under ThreadEnterCS 401/LeaveCS 402. ROM destination
has separate 32-B copy branch; user destination fixed 256 B limit does not have.
Contract does not use fault-safe user-copy/pinning; this is motive for user-mode
destination pre-touch, not proof root cause. Evidence
e90-patcher-copy-audit.json, tools/rev/audit_patcher_copy.py.

Host 43/candidate 56: ReadKernel Mem::FillZ destination before Ctl 105, broad
336-B board read removed; foreign nodes not read. ARM/SIS 0, DOFF/imports 15
verified. Deploy/provenance/short batch 8 frames 8 clean. Long series 1 batches
1/2/8/15 and clock-after — completeTrue, 120 frames each, 3120 packets; series 2
clock-before and b1 — another 120 packets. All 512 input+output words/packet
checked, wrap/carry, clean teardown, boot 33372. On **ring-r56-s2-b2** daemon PS
ceased responding, run_error TimeoutError and journal_error saved separately.
GET of journal not yet received. Recovery 01 connect timeout 8 s; async physical
E90 recovery/daemon/Open4All requested. Do NOT do new RUN/PUT before GET journal
and PS; do not repeat unchanged 56. Reason unknown: pre-touch allowed one
series, but did not prove stability.

Latest E90 files: research 43 EXE/hash, DSP ring 52/candidate 56, and research
journals installed. Saved originals unchanged
d0-20261003-clean34/originals.json. After daemon: recover-journal --host-version
43 with new tag; preserve and analyze; restore → restore-host → verify all 5
originals with new tags. If PS1/unknown native ownership — without PUT/KILL,
clean reboot needed. N95 remains restored original 20/5 SHA equal/PS0, do not
run repeatedly.

Current out/arm host 43, out/dsp ring 52, proof d1-ring-v56-artifacts.json, SIS
out/sis/c55stream-d1-v43-r56_sha1.sis. Runner default 43/revision 56, **do not
run from beginning** after failure. Candidate 54 N95 and E9054/55/56 samples
not mixed. tools/summarize_ring.py publishes all accepted journals/timing arrays,
boot/clocks/restoration/status, and features; assess_ring_candidates
recalculates conditional D2. Statuses: D0 complete, D1/D2 in_progress. Tests
15/15, ARM/SIS and static ABI audits passed; not full D0–D2 completion.

## 2026-10-03: final checkpoint — all journals received, originals 5 on both

ring56-recovery02 GET before PUT: boot 33773, PS0, journal 25662456… ends
ROUTING queue 0/c819ba98, BEFORE native ring allocation/map/own create/RUN. All
three interrupted commands 54/55/56 stopped in initial/native-memory
diagnostics, and not in DSP packet loop. Exact exception cause unknown. ring56
restore/hostrestore complete; verify 01 had connect timeout without new host
START. After user reboot boot 101039 verify 02 confirmed 5 originals.

Documentation of daemon describes autolock/Wi-Fi parking and WAKE. Candidate 57
host 43 + controller --keep-awake passed short batch 8 frames 8. Then user
clarified: **E90 reboots itself**, daemon auto-starts, hack/Open4All does not
start automatically. Therefore long 57 series **were not executed**; WAKE-only
hypothesis insufficient. Originals 5 returned and verified
ring57-final-verify01. Do not call these events only sleep/transport.

Host 44/candidate 58 added read-only boot-info, bypass Research: only HAL::Get
ESystemStartupReason/ESystemException and UserHal FaultReason/ExceptionId/
ExceptionInfo. DSP open/RUN and patcher not used. ARM/SIS 0; boot58-info01
FINAL/EXIT 0, boot 101039 unchanged. Getter rc 0, startup 0, exception 156,
fault −1604135081(A062D757), code 0/data 480/extra 5BC. These are raw fields
after manual reboot, not proof of previous kernel panic cause.
boot58-final-restore01/host-restore01/verify01 returned **all 5 originals**
GET/SHA-equal on E90, PS c55stream/ocprobe 0; N95 original 5 remain verified.
Neither active owner, nor QUARANTINE, nor needed physical action currently
exists.

Current source/out ARM 44, DSP ring 52/protocol 38. Artifacts 58 contain
read-only host 44; no new DSP RUN with 44 occurred. Ring runner defaults host
43/revision 57, but **do not run it unchanged**: long E90 runs must await
concrete safe native-reader contract/fault investigation. After automatic reboot
fault probe must be obtained before manual reboot; current cold boot does not
allow attributing raw exception 156 to our attempts.

Results: N95 candidate 54 three series 9360 correct packets; E9054/55/56
separate cohorts 360/360/3240 packets, the last has one full series, not three.
Native flags 17, byte→word units, four CMM pages, and release order proven in
hardware; native chunk attrs/DSP cache/publish and raw reader lifetime not
closed fully. D2 — conditional formula/scenarios, application T/A/W not
measured, emulator unchanged. D0 complete on both, D1/D2 in_progress. All
accepted journals/clocks/samples/SHA and restoration reports published in
docs/evidence/2026-10-03, generators summarize_ring/assess_ring_candidates. Next
independent work: native IPC processor-state/queue API and fault contract,
replacement of dangerous non-atomic foreign snapshots; not a new permutation of
RUN. User APPLICATION_CANDIDATES.md, CODEX_TASK, and Gemini scratch not changed/not
included in commit. Goal not declared complete or newly blocked. Final checks:
16 unit tests, verify_ring_publication 21 journals/13320 packets, clocks/failure
boundaries/restorations; check_state prints current D0 complete/D1 in_progress/D2
in_progress. Canonical LF hashes publication separate from SHA of original
daemon files so that Git EOL conversion does not spoil checksum check. Do not
repeat hardware to verify commit.

## 2026-10-04: native E90 ring61, three full series of data

D0 complete for both. E90 host 46/candidate 61 completed 12 long runs, 9360
packets, boot 60136 unchanged. N95 candidate 54 already had the same data
criterion. Native ring mode uses ioctl 2 cached own-state, BridgeUtil 1 own pages
before/after, retained own-node env/state, and live DSP base, without raw
RomPatcher snapshots/global queue enumeration. Reason of previous pre-RUN
reboots unknown; this is success of new path, not root-cause diagnosis.

All 6 E90 native 61 clock brackets: **self-test −20**, only HAL CPU 330 MHz.
Mistake of old runner complete=true acceptance corrected; failed clock probe now
stops series before next RUN. Journals preserved truthfully, DSP/bus clock
unconfirmed. Async Open4All E90 without reboot request still open. After
response only clocks/new tag and GET/parse, before any new RUN.

Native backing 38 instructions/phone traced to retained bridgecfg hardware chunk
(attrs 1044), global CMM suballocation lifetime. Compiled DSP order verified, but
independent OMAP2420 external-write/notification visibility contract open. D1/D2
in_progress; application gain not claimed. D2 recalculation separately for
N95/E90 synthetic scenarios; emulator unchanged.

19 tests, source-independent 33 runs/22680 packets verification, and check_state
-RequireArtifacts -RequireStreamArtifacts successful. To both originals 5
returned GET/SHA-equal, c55stream/ocprobe PS0. Detailed continuation point —
HANDOFF_NATIVE_RING_2026-10-04.md; proof — native-ring-results. Code and
evidence published commit `233740c31dbf218d0ea7201f60ddd60fa9fa181f`. Push
private main successful; independent ls-remote confirmed same SHA. Third-party
APPLICATION_CANDIDATES and Gemini scratch files not included in it.

## 2026-10-04: DCR and native mailbox audit

Offline audit of 29 instruction sites/phone + DSM cinit table confirmed native
BIOS 5.10, user-init BCLR ST3_MPNMC/RET, STRM_issue callback, and copy/zero-copy
SHM notification paths. Primary TI BIOS 5.41 gbl.h55 identifies DCR I/O port
200/WPE mask 80. Read-only extraction of selected InstallJammer records without
launching installer; hashes and references published in
dsp-native-notification-audit.json. N95 BIOS_init is by 4 bytes later than E90,
export resolved separately; global relocation delta not assumed.

Actual value of WPE not measured, mailbox status polling not proven as SDRAM
drain. DSP compiler publication audit preserved partial and bound to new
firmware audit. Future distinct diagnostic can only read port 200 after fresh
clock gate; kernel register writes not needed. No new phone I/O/DSP RUN in this
offline continuation. Both phones remained on verified originals; pending
Open4All question still unanswered. D1/D2 in_progress. HANDOFF updated; native
audit, publication verification (33 runs/22680 packets), and check_state with
both artifact flags passed. Audit published by separate commit/push, without
third-party user files.
