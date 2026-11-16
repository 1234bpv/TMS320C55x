# N95 WSOLA68: current ARM SMLAD versus DSP63

**Keep the current blocking WSOLA search on ARM.** The actual shell already
contains packed SMLAD; the old63 run compared DSP against scalar ARM. The
new68 run performed 8 pilots and 3×120 paired jobs with the current ARM,
scalar ARM and the exact retained DSP63 on identical inputs. Current
blocking winners 0/360 before setup.

| Search time, us | min | p50 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|
|A current SMLAD|329.494|337.601|387.192|679.970|727.654|
|A scalar|995.636|1003.265|1081.467|1443.863|2262.115|
|H+D ready result|1007.080|1098.633|2075.195|8514.404|9155.273|

Median paired scalar/current ratio 3.017×, not the ratio of pooled medians.
Against scalar DSP, there are 20/360 winners before setup; the current
emulator comparison does not change this. The historical SMLAD estimate of
135–200 us is not confirmed by this probe: the actual current kernel includes
packing, two search banks and traversal. Historical cohorts 20/63 are kept
separately.

A snapshot of the actual `snd_symbian.cpp` keeps the packing, two
accumulators, the coarse/refine order, strict `>` ties and the assertion;
only the exported entry/static was changed. CSL343/O2/ARMv6/ARM1136/
fomit-frame-pointer matches the stage1 audio shell; the GCCE463 core
compiler does not substitute for it. Disassembly shows 5 SMLAD sites;
[source/block hashes](../src/wsola_current/snapshot.json).

The A current measurement averages 64 calls, scalar 16, with the loop and
volatile sink inside and the dataset/oracle outside. ARM order alternates
before/after DSP. H+D, from packing to offset/score/scored in ARM memory,
includes cache, notifications and DSP. Full input/output/header/padding
checks and the journal are outside the timing; rows are buffered until the
end of the loop, and CPU is not read (`-1`). An isolated warm cache/state is
not equal to live audio/gameplay.

An independent Python signed16/LCG/shift oracle re-checks the outputs of all
368 jobs, the boundary/tie order, and score/scored. Full series: 460800 ring
words of 16 bits; pilots separately. 8 fixtures, 15 LCG seeds, random
case/120-job run; captured PCM, final sound and underrun/full audio state
were not checked. Ring 16 KiB TOTAL, 4 input / 1 output slots, 480 B payload,
stable pages/ownership, clean lifecycle/EXIT/FINAL0. DCR 720 readings
0000/WPE0, helper exact 63; the reads may affect ordering. The independent
endpoint publication remains open. The 8 stock brackets are snapshots, not a
continuous DVFS trace; frequencies and performance reservation were not
changed.

Instrumented S p50 = 865080 us (min 860992 / max 1207945), includes
journaling. Strict conditions together: `S/N<A`, `W>H+D+S/N−A`. For
N 16/64/256/1000: setup 0/360; N 10000: setup 360/360, blocking gain 0/360.
N 10000 required W p50 847.608 / p95 1835.024 / max 8927.023 us: these are
theoretical thresholds, not useful work. H occupies the ARM and competes for
the bus; the next hop depends on the previous offset.

The first runner completed series 1/2. The runner's own early concurrent
restore changed the EXE; the third attempt stopped before START on an
installed-host mismatch. The failed transport has INFO/WAKE/PS/GET and no
PUT/START/KILL; the samples do not contain it. Originals 5 verified 01:
GET/SHA-equal, PS 0. An OS nonblocking per-phone lock was added for the entire
runner/session; nested same-process actions are allowed, while competing
actions are refused before the connection. The test really checks the locked
byte, the competing handle and the release. The specific recovery 02
redeployed the exact binaries; the third series, with new stock brackets, is
complete; the modified orchestration is archived separately, and the initial
immutable preflight remains. Originals 5 verified 02: GET/SHA-equal, PS 0;
daemon tuple 62209, boot 0, byn stable; no physical reboot was recorded.

E90 untouched. Source/out host 53, typed DSP used 63; the generic
`out/dsp/c55stream.dll55l` remains SPU67 and must not be used as WSOLA. The
phone has its original files. [Artifacts](evidence/2026-10-04/n95-wsola68-artifacts.json),
[recovery artifacts](evidence/2026-10-04/n95-wsola68-recovery-artifacts.json),
[results/interruption/restorations](evidence/2026-10-04/n95-wsola68-results.json).
`python tools/verify_wsola_current_publication.py`; 44 session tests PASS.
D1/D2 in_progress: publication, useful W/full audio and the deferred E90 remain open.
