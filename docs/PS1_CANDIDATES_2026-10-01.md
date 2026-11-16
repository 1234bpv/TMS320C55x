# Decisions for PS1Emulator based on C55x results

## Current update 2026-10-04: N95

[Claude PS1 handoff](CLAUDE_PS1_HANDOFF_2026-10-04.md) closes current
work with a report upon user request: decisions, exact jobs, sources,
verifications and open gates. Do not start new hardware experiments automatically.

D0 is already complete on both phones; native ring 16KiB TOTAL works.
N95 native61 has 3 series/9360 correct packets with stock brackets.
After separate calibration candidate64/host49 aggregate CPU
measurement was performed: batch 1/2/8/15 exchange p50=915/1190/3021/5126us,
thread CPU 45.37/45.87/48.09/45.68% in full correctness window with final
settling yield. Full-window useful bidirectional bandwidth 0.712/0.960/
1.357/1.500MB/s. This is a synthetic transform; these T are not MDEC/SPU kernels.
[CPU window and limits](N95_RING_CPU_2026-10-04.md).

WSOLA63/host48 — actual coarse/refine kernel via ring, pilot 8 + 360
paired jobs, exact offsets/scores. A p50=1155.853us, pack-to-result H+D
p50=1983.643us, only 16/360 H+D<A before setup. **For current blocking
WSOLA keep ARM.** Instrumented S p50=828063us includes logging,
not pure create/minimum production startup. Strict scenarios N16/64/256/1000
use S of the corresponding series and separately check S/N<A and
W>H+D+S/N−A. Useful W was not executed; asynchronous gain is not measured.
SMLAD135–200us remains an estimate.
[WSOLA results](N95_WSOLA_RING_2026-10-04.md),
[paired calculations](evidence/2026-10-04/n95-wsola63-results.json).

Current shell already has packed SMLAD. WSOLA68/host53 with exact snapshot
and retained exactDSP63 completed 8 pilots + 360 paired jobs: current A
p50=337.601us, scalar 1003.265us, H+D ready 1098.633us; current winners 0/360
before setup, paired scalar/current p50ratio 3.017x. **Current blocking WSOLA
keep ARM.** Estimate 135–200us is not confirmed by this probe; measured A
includes packing. S p50=865080us logging; N10000 setup 360/360, required
W p50847.608us, blocking gain 0. Useful W/full audio unmeasured.
[Current WSOLA68/interruption](N95_WSOLA_CURRENT_2026-10-04.md).

MDEC66/host51 — actual six-IDCT + RGB24, int32 coefficients, exact outputs:
1080 jobs/2520 macros; batches 1/2/4 A GCCE463 p50=78.201/110.626/295.639us,
H+D pack→RGB24 reconstructed in ARM memory p50=2655.029/4272.461/7690.430us.
Oracle checks outside both time limits; blocking winners 0/1080 before setup.
**For measured blocking MDEC job keep ARM.** S p50=840178us
includes lifecycle journaling; W=0; not gameplay/full RLE-DMA-IRQ integration
and not proof of impossibility of resident/asynchronous DSP.
[MDEC accuracy/measurements](N95_MDEC_RING_2026-10-04.md).
SPU: prior scene budget 3.7% is not the time of ring kernel;
actual mix job/state traffic/A/W and full identity of audio/state are needed.
Therefore **keep SPU on ARM until measured profitability of a concrete job**;
async/resident DSP options are open, impossibility is not proven.
[SPU boundary audit](N95_SPU_BOUNDARY_2026-10-04.md): plain 24 voices with
samples/volumes/sums32 accommodates only up to 66 samples/job; optional ARM work_item
8396B is already larger than 7200B input payload. 512KiB SPU RAM, history/ADSR/
noise/reverb/IRQ require a separate coherency boundary. Current ARM baseline
has smlawb/smlawt. After the audit SPU67/host52 was performed: 24 pilots and 1080
plain-mix jobs 1/8/24 voices×64 samples with exact 128 stereo sums32/job.
A current ARM p50=3.576/27.180/40.531us versus H+D ready 1617.432/3295.898/
3540.039us; oracle checks outside. Blocking winners 0/1080 before setup.
**Keep measured plain-mix job on ARM.** S p50=863494us includes logging,
W0, CPU unmeasured; full SPU/state/PCM and async/resident profit are open.
[SPU67 measured contract](N95_SPU_RING_2026-10-04.md).

Independent endpoint-publication contract remains open; stock
brackets are not continuous DVFS trace. D1/D2 overall in_progress.
Current source dependency audit established immediate consumers and mutation
boundaries for all three kernels. For the same ARM thread the model
`H+max(D,W)+S/N<A+W` additionally requires `H+S/N<A`.
Measured serial intervals outside notification pass this necessary
condition at S=0 in MDEC 1/1080, SPU 0/1080, currentWSOLA 359/360 jobs;
these are not overlap winners. W in unchanged blocking calls is 0 by structure,
general independent guest-work budget is not measured.
[Dependencies and paired bounds](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md).
Emulator unchanged. N95 originals 5 after 68 restored/GET-SHA equal, PS0;
E90 postponed by the user, no new commands were sent.
[N95 requirement/evidence checkpoint](N95_ACCEPTANCE_2026-10-04.md)
separates delivered measured-job verdict from open memory contract
and future emulator integration; master verifier checks all main
N95 cohorts and fresh read-only original-files/PS0 state.

## Historical calculation 2026-10-01

Date: 2026-10-01. **Do not start application integration now:** D0 with official
RUN is not yet accepted, DMM/shared ring 16KiB are not measured. Below is given
calculation for prior, already measured copying channel v18/v20.
This is an intermediate D2 result; it needs to be supplemented after hardware D1.
Emulator was not modified in this work; N95 was not queried.

Continuation of E90: two RUNs gave 8 correct 512-B packets each, but
delete−2/−33; third MSG diagnostic also delete−2. D0 remains 0/3.
The user permitted new attempts with a separate hypothesis; native reference
control is being prepared. Median 396us from 16 packets of these failed-lifecycle
probes does not substitute for accepted D1 measurement and does not change formula below.
[Evidence](evidence/2026-10-01/e90-d0-resume-checkpoint.json).

## Data and comparison limits

[WSOLA](WSOLA.md) contains three paired series v20 of 32 control/search packets each
on each device. [v18 packets](PACKET_SIZES.md) contain three series
of 32 packets per size. All these measurements were made under stock guard m86/div3.
In the current session E90 is also actually stock: `CM_CLKSEL1_PLL=00056400`,
`CM_CLKSEL2_PLL=2`, `CM_CLKSEL_MPU=2`, `CM_CLKSEL1_CORE=04360626`,
`CM_CLKSEL_DSP=00000343`; ARM330.24MHz, bus110.08MHz, DSP220.16MHz.
This was read from registers, frequencies were not changed. The specified in assignment
overclocking m105 is not confirmed now.

E90 symmetric echo 512/1568/1792/2048/2304/4096 B: pooled medians
396/610/640/701/762/1129us, 96 packets per size. For 4096 B medians
of three separate series 1129/1129/1129us, p95=1220us, max=2502us.
Maximums 1792/2048 B 7812/7690us remain in the sample. This is full echo
with driver/scheduling, not isolated DMA or zero-copy measurement.

The estimate 9MB/s from [emulator report](<../../PS1Emulator/plans/reports/perf-dsp-analysis-2026-10-01.md>)
is used only in scenarios. It should not be declared directly measured
throughput of DMM. DSP 385us from assignment is also not a measurement of kernel
time: 385.28us is median **pairwise savings of ARM−DSP path on N95**.
Measured full WSOLA path is 640.87/732.42us N95/E90.
Difference of search/control medians 122.07us is not an independent measurement of pure D.

## Formula and overlap

Let `T=H+D`, `q=S/N`. Checked is
`max(T,W)+q < A+W`. For non-negative times this is equivalent to simultaneous
conditions **`q < A` and `W > T+q−A`**. For `W=0` needed is `T+q < A`.
For `W>=T` sufficient is `q<A`, but in practice H partially occupies ARM,
and processors compete for the bus. Ideal formula is a lower bound.

Therefore `H>A` alone does not prove impossibility of asynchronous gain:
one still needs to establish how much independent W is available until consuming
the result. W is not measured in the emulator for these jobs; average frame time
cannot be automatically declared such independent work.

S must include all startup and teardown of the session. Available 8.102/8.5595ms
N95/E90 is create only, therefore N given below are optimistic.
Calculations are reproduced by [assess_ps1_candidates.py](../tools/assess_ps1_candidates.py),
exact input hashes and numbers — [JSON](evidence/2026-10-01/ps1-candidates-calculation.json).

Application A for MDEC/SPU are taken from N95 reports, not new E90 A/B.
SPU scene has ARM330.24/bus165.12MHz; E90 channel has bus110.08MHz.
These are different devices and buses; budgets require verification on target device.

## MDEC

Current exact format is 384 int32=1536 B per macroblock, RGB15/RGB24
512/768 B output. With 32-B header in each direction this is 1568/544 or 800 B
per one block. 768 B of coefficients from external report assume int16;
such range and byte-for-byte identity are not yet proven. `rl2blk` already
performs IDCT; after it DSP receives only YUV→RGB, with smaller A.

For the scenario `B=9MB/s`, `L=500us`, A=50us/macroblock, `D=0`:

| Buffer in each direction | Blocks | RGB24 in/out, B | H per block, us | A per block, us |
|---|---:|---:|---:|---:|
| 4096 B | 2 | 3104/1568 | 509.56 | 50 |
| 16384 B, not yet verified | 10 | 15392/7712 | 306.71 | 50 |

This is a **copying scenario**, not a new measurement. Estimate 190us/block from report
already exceeds 50us; keeping int32 raises data budget. Growth
of packet only amortizes L. Even with infinite batch, zero L/D/S
and 9MB/s the traffic itself RGB15/RGB24 costs 227.56/256us per block.
For blocking gain under zero other overhead needed are over
40.96/46.08MB/s respectively.

Under ideal overlap two-block RGB24 batch requires
`W>919.11us+D+S/N`, where D is time of entire batch. For ten blocks threshold
`W>2567.11us+D+S/N`. This might be mathematically possible, but there are
no measured D, W, asymmetric H or verification of guest DMA/IRQ visibility.
16384 B in each direction are also not identical to a ring of total size
16KiB: simultaneous input/output of such batch occupy 23104 B without metadata.

**Verdict:** blocking MDEC via current copying is not profitable
under the given model. Async batch or DMM remain conditional candidates;
real IDCT/YUV kernel, unchanged output and H/D/W measurements in FMV are needed.

## SPU

GT profile 609 calls: entire `doSamples` 965–974ms, that is 1584.56–1599.34us
per call on average and about 3.7% of the scene. **Separate mixing** is estimated
by sampling 1:16 at 225.4–230.3ms, that is 370.11–378.16us per call
and about 0.87–0.89% of the scene. These intervals
are nested; they cannot be added. 3.7% is not a share of mix kernel itself.

Stereo PCM up to 3656 B, with header 3688 B; intermediate int32 SSumLR up to 7312 B,
with header 7344 B, larger than buffer 4096. This is maximum capacity 914 samples,
not average output. [Primary SPU report](<../../PS1Emulator/plans/runs/2026-09-28_gemini/n95-spustage-result.md>)
has 446816 samples/609 calls: 733.69 samples and 2934.75 B PCM per call.
At 9MB/s the **average** PCM output itself costs 326.08us; maximum packet
406.22us, int32 maximum 812.44us. One cannot compare maximum bytes
with average A and thereby prove a loss. For mix-only average output
leaves only 44–52us for input/L/D/setup; under scenario L500us blocking
gain is already absent. Actual asymmetric H for this job is not measured.
SPU RAM 512KiB must be kept resident and dirty ranges transferred;
their volume is unknown.

For full SPU the blocking condition `H+D+S/N<1585..1599us` can have
a non-zero budget; 3.7% in itself does not refute it. For overlap
needed are `S/N<A` and `W>H+D+S/N−A`. Not a single complete C55x SPU kernel or
same-input A/B exists. Voice state, capture, CD mixing, IRQ and save/load
make transferring only PCM an insufficient contract.

**Verdict:** mix-only via copying is not recommended. Full SPU
with resident state has no proven profitability or proven impossibility;
until DMM and profile of heavier sound scene do not port it.

## WSOLA

Measured input 1792/output 48 B: scalar ARM 999.45us versus full DSP
640.87/732.42us N95/E90. Pairwise savings 385.28/265.12us give
create-only 22/33 hops. If instead of pairwise statistics one takes the difference
of overall medians 358.58/267.03us, formula gives 23/33 hops; these are different estimates.
Against current scalar ARM synthetic sequential gain is confirmed.

ARM SMLAD 135–200us is a **calculation, not a measurement**. If it is confirmed,
blocking DSP path 640–732us loses. With `N=1000` and create only in S
ideal formula gives following thresholds of independent W:

| Device | A=135us: W greater, us | A=200us: W greater, us |
|---|---:|---:|
| N95, old data without new access | 513.97 | 448.97 |
| E90 | 605.98 | 540.98 |

If `W>=T`, minimal create-only N for A 135/200 are 61/41 N95
and 64/43 E90. This is a conditional async candidate even against fast ARM;
proof of such W and small ARM submission/completion time does not exist.
The next hop depends on prior offset, therefore filling the ring independently
with many future searches of a single audio stream is impossible.

**Verdict:** preserve proven DSP/scalar result, but before choosing
integration obtain physical ARM SMLAD A/B. DMM can change H; needed are
new asymmetric search/control runs, p95/p99/max, PCM and underrun.
With Preserve pitch disabled gain equals zero.

## What is needed for final D2

First accept three clean D0 RUNs, then D1 mapping/cache/ownership/ring
and repeat exchange numbers. Recalculate tables according to actual H+D and full
S, measure W up to the point of consuming the result. Before this none of the three
candidates has proof of speedup for the entire game or safe cancel.
Presence of incomplete D1 is not a negative result about zero-copy.

ROM STRMCOPY control RUN4 on E90 gave 8 exact echoes 512 B with median 488us,
range 457–579us, but delete−33/pending/state3. This is separate diagnostics of failed
lifecycle; these numbers do not substitute for D1 H/D/B and do not change provisional
verdict above. D0 own0/3, DMM/ring 16KiB are still not verified physically.

RUN5 own RMS_EXIT diagnostic confirmed get1/waits1 and the first idle of both
streams 0/pending0; all 8 checked packets have median 396us/range 366–457us.
However delete−33/pending/state3, clean FINAL/EXIT are absent. This narrows D0
to the last diagnostic reclaim/idle, execute return and native outbound
EXITACK/consumer/delete callback; it does not add measured DMM H/D/B.
Therefore reported D2 numbers and conditional conclusions are unchanged.

After recovery RUN5 new created-worker MSG probe stopped before MSG/RUN
at no-input create-only delete−33/pending/state1. This does not add packet
measurement, DMM result or clean D0; experimental RUN remains 5.
ARM reader initial ror16 flag1 and source binding are clarified statically.
Physical outbound MSG and wrapper/EXITACK still require verification.
