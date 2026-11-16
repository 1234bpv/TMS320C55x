# N95 WSOLA68: поточний ARM SMLAD проти DSP63

**Current blocking WSOLA search залишити ARM.** Actual shell уже містить
packed SMLAD; старий63 порівнював DSP зі scalar ARM. Новий68 виконав
8 pilots і3×120 paired jobs з current ARM, scalar ARM і exact retained
DSP63 на однакових inputs. Current blocking winners0/360 до setup.

| Час пошуку, us | min | p50 | p95 | p99 | max |
|---|---:|---:|---:|---:|---:|
|A current SMLAD|329.494|337.601|387.192|679.970|727.654|
|A scalar|995.636|1003.265|1081.467|1443.863|2262.115|
|H+D ready result|1007.080|1098.633|2075.195|8514.404|9155.273|

Median paired scalar/current ratio3.017×, не ratio of pooled medians.
Проти scalar DSP має20/360 winners до setup; current emulator comparison
це не змінює. Історична SMLAD135–200us оцінка не підтверджена цією probe:
actual current kernel включає packing, два search banks й traversal.
Historical cohorts20/63 збережені окремо.

Snapshot actual `snd_symbian.cpp` зберігає packing, two accumulators,
coarse/refine order, strict `>` ties, assertion; змінено лише exported
entry/static. CSL343/O2/ARMv6/ARM1136/fomit-frame-pointer matches stage1
audio shell; GCCE463 core compiler його не підміняє. Disassembly5 SMLAD
sites; [source/block hashes](../src/wsola_current/snapshot.json).

A current averages64 calls, scalar16, loop/volatile sink inside,
dataset/oracle outside. ARM order alternates before/after DSP. H+D від
packing до offset/score/scored у ARM memory включає cache/notifications/
DSP. Full input/output/header/padding checks і журнал поза timing;
rows buffered до кінця loop, CPU не читається (`-1`). Isolated warm
cache/state не дорівнює live audio/gameplay.

Independent Python signed16/LCG/shift oracle повторно перевіряє outputs
усіх368 jobs, boundary/tie order, score/scored. Full series460800 ring
words16; pilots окремо. 8 fixtures,15 LCG seeds random case/120-job run;
captured PCM, final sound, underrun/full audio state не перевірено.
Ring16KiB TOTAL,4 input/1 output slots480B payload, stable pages/ownership,
clean lifecycle/EXIT/FINAL0. DCR720 readings0000/WPE0, helper exact63;
reads можуть впливати на ordering. Independent endpoint publication
відкритий. 8 stock brackets — snapshots, не continuous DVFS trace;
частоти/performance reservation не змінювали.

Instrumented S p50=865080us (min860992/max1207945), includes journaling.
Strict conditions разом: `S/N<A`, `W>H+D+S/N−A`. Для N16/64/256/1000
setup0/360; N10000 setup360/360, blocking gain0/360. N10000 required W
p50847.608/p951835.024/max8927.023us: theoretical thresholds, не useful
work. H займає ARM і конкурує за bus; next hop залежить від previous offset.

Перший runner завершив series1/2. Own early concurrent restore змінив
EXE; третій attempt зупинився до START на installed-host mismatch.
Failed transport має INFO/WAKE/PS/GET, жодного PUT/START/KILL; samples
його не містять. Originals5 verified01 GET/SHA-equalPS0.
Додано OS nonblocking per-phone lock для entire runner/session; nested
same-process actions дозволено, competing actions відмовляються до
connection. Test реально перевіряє locked byte/competing handle/release.
Specific recovery02 redeployed exact binaries, третя series із новими
stock brackets complete; modified orchestration archived separately,
initial immutable preflight залишився. Originals5 verified02 GET/SHA-equal
PS0, daemon tuple62209boot0byn stable; physical reboot не зафіксовано.

E90 untouched. Source/out host53, typed DSP використаний63; generic
`out/dsp/c55stream.dll55l` лишається SPU67, не використовувати як WSOLA.
Телефон має originals. [Artifacts](evidence/2026-10-04/n95-wsola68-artifacts.json),
[recovery artifacts](evidence/2026-10-04/n95-wsola68-recovery-artifacts.json),
[results/interruption/restorations](evidence/2026-10-04/n95-wsola68-results.json).
`python tools/verify_wsola_current_publication.py`;44 session tests PASS.
D1/D2 in_progress: publication, useful W/full audio та deferred E90 відкриті.
