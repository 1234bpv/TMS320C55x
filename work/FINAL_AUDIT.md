# Audit of the full research task

Date 2026-10-01. The criteria are taken from `work/PLAN.md`, recorded before
implementation. Research result: a portable private project, a confirmed
persistent STRM worker on two phones, a useful ARM/DSP parallel workload, an
exact WSOLA kernel with an ARMv6 baseline, an assessment of the application and
an integration plan.

| Requirement | Evidence of completion | Limit of the conclusion |
|---|---|---|
| F01: plan and scaffolding | PLAN/features/STATE, bounded runners, check_state, unchanged historical evidence tags | Check_state does not run a phone experiment. |
| F02: portable build | BUILD.md, env/build helpers; current ARM/DSP/SIS20 builds; artifact6, ARMv6 codegen proof | Raw binaries/ASM are local; source/import hashes and build results are published. |
| F03: private GitHub | 1234bpv/TMS320C55x, PRIVATE; earlier checkpoints verified LOCAL=REMOTE; the final push and the check after this audit | Firmware, vendor files, keys, EXE/DLL/SIS/backups/screenshots are not published. |
| F04: channel map | STREAM_RESEARCH.md, native ROM comparisons, STRM/DMM/notify/RMS/TSK/SEM contracts and ranked candidates | MSG route/shared ring remain separate unverified channels; the working STRM does not prove them. |
| F05: persistent stream/parallel N95 | v17: three serial/parallel pairs with a DSP dot and an independent ARM CRC; v18: many packets/create; v20: exact WSOLA/length/stop and clean completion | Start/transfer/combined compute time was measured with the ARM counter; the DSP raw timer has an idle limitation. |
| F06: real E90 | separate firmware guards, ROM profiles, stock-clock preparations, v17/v18/v20 hardware journals, SIS20/EXE readback and final recovery | N95 addresses are not transferred to the E90 PDD without verification. |
| F07: PS1/Browser assessment | APPLICATION_CANDIDATES.md: concrete files, formats/sizes/rates/dependencies, SPU historical profile; WSOLA.md: ARMv6 comparison, 22/33-hop create-only break-even, integration plan | This is an assessment and a verified research kernel. Changes or gains in the neighboring applications themselves are not claimed. |
| F08: reconciliation and final state | README/WSOLA/PACKET_SIZES/STREAM_RESEARCH, historical corrections, features/evidence path audit, JSON/raw hash/status checks, PS0/originals GET-equal; private checkpoint | Source/evidence checkpoint e8f38c1: gates/push/LOCAL=REMOTE/PRIVATE verified. |

## Data ownership and prototype limits

ARM native allocations in mode 2 remain live until transfer completion and a
successful delete; statuses/transfer records have persistent storage. The DSP
owns issued buffers until reclaim, primes them again only after output reclaim,
and the last stop returns the buffers and completes the TSK before unload.
Lengths in ARM bytes/C55 words are set explicitly and checked with hundreds of
varied packets. Coherence of the **native copy path** confirms the correctness of
all data; manual mapping/cache barriers for the shared ring do not follow from
this.

Bounded host waits, stream waits and joins are specified in the source/artifacts;
BIOS ticks are not called milliseconds. All counted hardware runs have FINAL0,
EXIT0, no cancellation/KILL, explicit stop, delete/free/close. Invalid input,
timeout/live-task unload and a safe ARM fallback were not checked; a native loader
audit is needed before application integration. The current positive
implementation is a research prototype with a defined, checked completion path.

## Agreed refutations and what is unknown

- The old ~9 ms of the empty create phase is not the cost of each packet: the
  resident stream v18/v20 was measured separately; the WSOLA create median
  8.10/8.56 ms is amortized.
- Nominal DSP 220 MHz is not substituted as a per-packet measurement. The stock
  guard checks PRCM m86/div3/profile; the N95 MPU 100% is reserved/checked.
- CLK_countspms164 does not convert raw ticks into wall time. Short ARM-bracket
  calibrations are close to 19.2 MHz; a long 800 ms idle systematically
  undercounts. The cause is unknown. The comparisons used the ARM FastCounter.
- Native copy/TSK success does not prove shared ring pinning/cache ownership or
  audio coexistence. Priority 15 and short runs are not a production audio test.
- ARMv5 v19 does not replace the current PS1 scalar ARMv6 baseline. The V20
  body/flags were checked, and a stale SDK object was eliminated before delivery;
  the v19 evidence is kept.
- The early RUN/MSG/phase-library failures and the late N95 reboot after v18 are
  kept. For the late reboot the cause is unknown; in v19/v20 the daemon startTick
  did not change.
- v17 ~40% concerns the combined synthetic dot+CRC; the v20 saving concerns the
  WSOLA kernel vectors. The application FPS/PCM/underrun gain is not established.

## What belongs to the next integration

Safe error/cancel ownership/unload, long-running work, real audio coexistence,
recorded-PCM output/underrun/tail latency; MDEC/SPU state batching and the
Browser job queue/profile. PLAN required research/prototype/assessment and an
integration plan. Full implementation of all these future application stages is
not a criterion for completing the current brief. They explicitly remain
unverified.

## Summary of verification

F01–F08 are completed within the research criteria. Source/evidence checkpoint
e8f38c1c052046560c216fb4cf7aa8aec8d02d16 was pushed; LOCAL=REMOTE/PRIVATE/clean
verified. 129 reviewed files, 76 byte-exact text artifacts, 36 v19/v20 runs, 780
correct packets; current source/host/DSP SHA matches; originals/PS0 verified.
Completion metadata does not change the source, binaries or hardware results.
