# Continuation for agy: native ring, 2026-10-04

## Current steering: N95 now, E90 tomorrow

The user resumed the target and instructed to finalize on N95; E90 is deferred
until tomorrow. **Do not execute new E90 phone commands**, including restore,
while this deferral is in effect. Old Open4All requests below are no longer
relevant.

N95 host46/candidate61: 3 new full series, 12 runs / 9360 packets,
all 6 stock clock brackets PASS, startup tuple 62209 unchanged. 5 originals
returned and GET/SHA-equal. New batch 15 p50=5249us / 2.713MB/s,
slower than the distinct old 54 cohort; the reason is not yet proven.
Evidence — docs/evidence/2026-10-04/d1-n95-native-ring-results.json.
Distinct N95 host47/candidate62/protocol39 DCR pilot already PASS: 8 exchanges,
120 packets, 16 reads port 0x200 all 0000/WPE0, two stock clock brackets.
5 originals after pilot restored+verified, PS0. Helper bytes A45102004804
have no writes/relocations. Published n95-dcr62-results.json and
docs/N95_DCR_2026-10-04.md. Runtime 62 does not qualify past 54/61.
Source/out now host47/DCR62; old ring 61 DSP and archive 61 unchanged.
Next is the OMAP2420 endpoint publication contract and distinct WSOLA ring/A
measurement; do not run default 46 runner against newly built 47.

E90: stock clock 02 passed after user toggle, but before new DSP deployment
a user-confirmed automatic reboot occurred. Subsequent UI session KEY down/SHOT/GET
completed fully; subsequent connect failed before any command.
The user confirmed physical reboot; daemon log later showed reset tick.
The reason is not established; there are no new DSP RUNs. Evidence and source audit —
docs/E90_DAEMON_REBOOT_2026-10-04.md and e90-daemon-reboot-audit.json.
`startTick` is daemon launch tick, not a unique phone boot ID. Last
INFO/GET-only recovery had startTick 93682; automatic reboot cannot
be deduced solely from startup tuple change. REBOOT/RESTART/KILL commands were not sent.

E90 standard patcher copy 105 / free 100 / getter 103 versus RDomain copy 102 /
free 104 / getter 105 under the same RomPatcherPlus.Driver: offline 5-variant
contract is proven, actual loaded module identity not read.
Distinct ringclock.exe built (SHA 95CEE1F7…4560), **never installed
or run**: 4 deploy attempts stopped before PUT, last LS−46.
E90 known host 46 / original DSP; EXE/hash/journals restore pending.
Saved originals — work/evidence/e90/d0-20261003-clean34/original-*.bin.
Later clean up only own E:\codex-oct04-patches03/04/05.bmp.
Do not confuse N95 and E90 restoration: E90 final-verify 01 was before redeploy 46.

22 tests PASS; publication verifier 45 runs / 32040 packets across separate
cohorts. D0 complete, D1/D2 in_progress. Prior text below is history.

Working folder `D:\VsCodeProjects\SymbianProjects\TMS320C55x test`.
Assignment D0–D2 remains active; do not mark the entire plan complete.
Current code host 46, DSP candidate 52 / protocol 38; on phones **original 20**.

## Completed results

- D0: 3 ordinary RUN / 8 correct packets each on N95/E90, clean teardown.
- N95 candidate 54 / host 41: 3 full D1 series, 12 runs / 9360 packets, stock clocks.
- E90 native candidate 61 / host 46: 3 full D1 series, 12 runs / 9360 packets,
  boot 60136 unchanged. Native ioctl 2 own-channel cached state 1, retained
  own-node state 1 / nonzero RMS MEM_valloc env, 4 pages GET via BridgeUtil 1
  before/after exchanges, exact identities. No RomPatcher snapshot in
  native ring mode; distinct clock probes did patcher own-buffer self-test.
- Full verification of 256 input and 256 output words/packet, sequence wrap,
  32-bit carry, delete/free task/unmap/unreserve/free ring/notifications/close.
- Native CMM backing: 38 instructions and 3 kernel imports/phone trace
  ASIC selector 2 → retained bridgecfg DPlatChunkHw(attrs 1044) → reader
  → context → CMM register. Cleanup factory passes both chunks.
  Public attributes: user RW, buffered uncached L1, uncached L2.
  ASIC reservation/PTE dump not done; do not claim explicit pin/unpin.
- Both returned 5 initial originals GET/SHA256-equal, c55stream/ocprobe PS0.
  E90 final boot 60136; N95 remained original 20, fresh GET-only verify.
- 19 tests pass. Source-independent publication check: 33 long runs,
  22680 packets in separate cohorts. Current full cohorts — 9360 each.

## Important corrected accounting error

`run_ring_series.py` previously checked only complete=true clock action.
All 6 native 61 brackets on E90 have **ocprobe self-test−20**, HAL CPU 330MHz,
without PRCM DSP/bus read. Stock for these brackets is **not confirmed**.
Summary and independent verifier retain explicit failed clock status.
Runner now checks stock_clock_matches and stops before next RUN;
negative regression test proves that completed action does not mean clock pass.

Async request to user: enable Open4All on E90, without reboot, and notify.
Latest "Keep working" does not confirm execution of this physical step.
After response, first only clocks action / new tag, GET logs and parse.
If self-test fails again, analyze own-buffer driver contract;
do not present failure as proof of stock and do not start new DSP RUN.
Successful new clock bracket does not confirm frequencies of past native 61 series.
If 3 stock-qualified series are needed, create new evidence cohort with
the same immutable host 46 / candidate 61 / DSP after clock validation:
`run_ring_series.py --device e90 --host-version 46 --revision 61
--tag-prefix native61-stock02 --keep-awake`. Do not overwrite old 61 tags.

## Other open part of D1

`dsp-ring-publish-audit.json`: archived deployed compiler assembly proves
volatile output/control stores → return → timer → notification fields
→ STRM_issue. Generic C55x manuals describe W/W+, write-pending and bypass;
this is not an independent OMAP2420 interconnect visibility/fence contract.
Independent firmware/hardware audit of external writes before native
notification visibility is required. Do not call volatile readback full barrier.

Offline continuation 04.10: `dsp-native-notification-audit.json` and
`tools/rev/audit_dsp_notification.py` verify 29 instruction sites/phone,
DSM cinit table, BIOS 5.10 / user-init and mailbox paths. TI BIOS 5.41
`gbl.h55` from primary installer confirmed DCR I/O port 200, WPE mask 80.
Installer was only read/unpacked selected records, not executed.
Downloaded immutable package remained `out/bios_setuplinux_5_41_13_42.bin`;
audit reproduces with it and saved baseimages. SHAs are in JSON.
Actual WPE is unknown; absence of symbol in 5.10 does not mean non-posted.
Reading mailbox 7F1041 before message 7F1022 is not proven as SDRAM drain.
A distinct future read-only DSP diagnostic port 200 may be prepared
after fresh clock validation; do not write DCR / do not count it for 61.
Dynamic channel/copy function pointer of historical runs not read by this audit.

D2 updated for separate N95/E90 synthetic T/S scenarios. MDEC/SPU/WSOLA
through this specific ring were not measured; application gain is not proven.
135–200us SMLAD is preliminary estimate, not a new hardware measurement.
Emulator was not edited. D1/D2 remain in_progress.

## Evidence and commands

`docs/evidence/2026-10-03/d1-native-ring-results.json` and 12 published journals;
`native-ring-backing-audit.json`, `native-processor-state-audit.json`,
`native-ring-owner-audit.json`, `dsp-ring-publish-audit.json`;
`d1-native-ring-v61-artifacts.json`, published final verify of both.
Generator `tools/summarize_native_ring.py`, verifier `tools/verify_ring_publication.py`.
E90 p50 batch 1/2/8/15=640/793/1831/3021us, useful bidirectional
MB/s=1.449/2.316/4.100/4.598; DSP clock unknown.

Python: `C:\Program Files\LibreOffice\program\python.exe -X utf8`;
launch via `tools/run_bounded.ps1`. LO Python does not invoke itself via
subprocess; orchestration imports main() with separate sys.argv.
Device runner: `tools/e90_task_session.py --device e90 --session
work/evidence/e90/d0-20261003-clean34 --action clocks --host-version46
--tag <new-unused-tag> --keep-awake` (in real CLI --host-version 46).
Saved originals: `work/evidence/{device}/d0-20261003-clean34/original-{0..4}.bin`.
IPs: E90 .21:2323; N95 .22:2323; strict device identity guards, no scans.

Do not touch third-party changes to `docs/APPLICATION_CANDIDATES.md`,
`work/CODEX_TASK_2026-10-01.md`, and Gemini scratch tools/files.
Commit/push private main allowed by user; stage only own changes.
Code/evidence: commit `233740c31dbf218d0ea7201f60ddd60fa9fa181f`, pushed
private main, independent ls-remote confirmed SHA. STATE contains record.
After next changes update checkpoint and verify push.
If Open4All step is not answered, do not repeat request without a new reason.
