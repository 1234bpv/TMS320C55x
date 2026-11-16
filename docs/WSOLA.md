# WSOLA on a persistent C55x worker: N95/E90

Date: 2026-10-01. The current comparison series is **host/protocol20**.
The plans were written before the edits: `work/PLAN_V19.md`, `work/PLAN_V20.md`.

## Algorithm and wire contract

Ported from `PS1Emulator/src/symbian/snd_symbian.cpp:WsolaBestOffset`, which
calls `CSymSnd::WsolaFeed`. The ARM keeps the window choice, the stereo
overlap-add and the audio queue. The search takes the left channel after the
arithmetic `>>6`: template 220, search 660, offsets 0..440. The coarse pass
evaluates 111 offsets with a step of 4; the refinement adds 3 or 6 offsets
near the coarse maximum. On ties the candidate already chosen is kept. The
signed 32-bit sum is bounded by 220×512×512, so there is no overflow.

The ARM reference has the original stereo stride 2/shift inner loops. The DSP
receives packed scaled signed 16-bit values and uses a contiguous dot product
from CGT4.4.1 `RPT/MACM`. All 22 native imports exist in both base images. A
separate Python reference computes the table of all 441 scores, then
reproduces the ordered coarse/refine. Fixtures: PS1 benchmark LCG/layout,
silence, positive maximum, negative scores, left/right refinement, last coarse
offset, and a tie with offset 4. The first vector: offset 172/score 4364902.
Each 32-packet run has 4 cycles; the LCG seed changes between the cycles.
[Vectors](evidence/2026-10-01/wsola-v19-vectors.json).

The input is 1792 B = 32-byte header + 880 signed 16-bit values. The output is
48 B = 32-byte header + offset/count, two lengths, operation/case, and a 32-bit
weighted checksum of the whole input. The native properties independently set
896 input / 24 output C55 words; both ARM allocations remain 4096 B. The DCD is
unchanged; ARM pointers/structs are not passed to the DSP. The following are
checked: magic/sequence/length/repetitions/protocol, score/frame/stop/priority
15, offset/count/case/checksum. The DSP checks the range −512..511. Control
reps0 has the same wire/checksum path without a search.

A single create starts its own TSK in generic library2; the node remains
CREATED1, and there is no official RUN. Last packet stop → output reclaim →
idle/reclaim → SEM post/native TSK exit → join TERMINATED3/cookie/status/
pending gate → task/SEM/streams/context delete → DELETED5/free native/close/
FINAL/EXIT0. This is the verified completion of correct packets.

## ARM compilation and method

V19 checked the arithmetic/wire/cleanup, but it had an SDK ARMv5 baseline. The
ARMv6 pure-function build differed: 260→244 B. V19 is kept as a historical
harness comparison; its ARM time was not used for the current PS1 conclusion.
V20: CSL GCCE3.4.3, SDK UREL `-O2 -fno-unit-at-a-time`,
`-march=armv6 -mtune=arm1136j-s -fomit-frame-pointer`, as the current stage1.
The body of the search matches the ARMv6 pure-function build byte for byte.
[Codegen](evidence/2026-10-01/wsola-v20-arm-codegen.json).
The SDK reused a cached object after the MMP option edit; it was rebuilt before
delivery. `build.cmd` now cleans both research objects.

On each v20: 9 runs / 195 correct packets — one echo 512, one short control,
one search, and 3 paired runs control/search of 32 packets each. Search 97 /
control 97 / echo 1; the statistics below have 96 samples per mode. Run order
`[0,1]`, `[1,0]`, `[0,1]`; the ARM/DSP baseline order alternates between
packets. ARM baseline — mean batch 16 on the same stereo data, each return has
a volatile sink. This is a warm-cache scalar baseline, without application
overhead.

The ARM FastCounter (32768 Hz) measures the packing and the end-to-end time:
from deinterleave/shift to both transfer completions. It includes the DSP
input range/checksum, the driver, scheduling and the search. Generation,
reference, validation and logging lie outside the interval. The raw DSP
ticks/configured 164 remain diagnostic, not wall time.

| Microseconds, pooled 96 | N95 | E90 |
|---|---:|---:|
| ARMv6 search, median batch 16 mean |999.45|999.45|
| Packing+control round trip, median |518.80|610.35|
| Packing+DSP search+round trip, median |640.87|732.42|
| DSP path p95 / maximum |640.87 /671.39|762.94 /762.94|
| Median same-packet `ARM − DSP path` |385.28|265.12|

DSP path medians over three runs: N95 640.87/610.35/640.87, E90 732.42 for
all. Each search packet was shorter than its measured ARM batch mean. The LCG
case 0 separately, 12 samples: ARM median 1024.25 on both, DSP 640.87/732.42.
All outliers are kept; control maxima 885.01/1190.19. The V18 E90 equal-size
outlier 7.812 ms remains a separate result.

The N95 MPU reservation is 100%, each packet before/after 100, release 0. A
fresh stock guard m86/div3/firmware profile on both. In v19/v20, the results
were correct, one create/no RUN/no KILL, FINAL/EXIT0; the daemon startTick was
unchanged across the series. The original DSP/clock logs and host 20 are
GET-equal, PS0: [final state](evidence/2026-10-01/worker-stream-v20-checkpoint-device-status.json).
The later N95 reboot after v18, with an unknown cause, remains a separate fact.

## Payback and limits

The create median is 8.102 ms on N95 and 8.5595 ms on E90. At the median
paired saving, **the create alone** pays back after 22/33 hops (~110/165 ms of
sound). The model does not include the base/processor load, the native
allocation or other session preparation. One TSK is needed for the whole
session. Hop 220/44100≈4.989 ms; the median DSP path takes ≈13%/15% of the
interval. The mean time and the maximum of the sample do not guarantee the
deadline.

Teardown on invalid input/timeout requires a native loader audit: a failed join
may leave a live task, and unloading after a callback error is not considered
safe. KILL is not a verified recovery. The shared ring/DMM ownership, long-run
operation, audio coexistence, underrun, and application FPS/PCM gain are not
established.

Integration plan: resident service/active-object completion, a queued search
job next to `WsolaFeed`, buffer ownership until completion, ARM
overlap-add/ring. After the safe cancellation/error audit — the same PCM, the
final output, underrun/tail latency and long-run operation with real audio;
fallback after completed DSP ownership. The current result provides the
kernel/channel and substantiates this plan.

## Reproduction and evidence

After the verified builds/archive, SIS20 on E90 and a fresh `prepare_stream.py`:

```powershell
python tools/run_stream.py --device n95 --ip 192.168.3.22 --host-version 20 --mode worker-wsola --reps 1 --frames 1 --preparation work/evidence/n95/NEW-preparation.json --tag NEW-one
python tools/run_wsola_series.py --device n95 --ip 192.168.3.22 --host-version 20 --preparation work/evidence/n95/NEW-preparation.json --tag-prefix NEW-pairs
python tools/recover_stream.py --device n95 --ip 192.168.3.22 --preparation work/evidence/n95/NEW-preparation.json --restore-dsp --tag NEW-recovery
```

Always use new names; after a failure, stop the series. `summarize_wsola.py`
checks the historical tags offline and does not overwrite the reports.
[N95](evidence/2026-10-01/n95-wsola-v20-results.json),
[E90](evidence/2026-10-01/e90-wsola-v20-results.json),
[artifact6](evidence/2026-10-01/worker-stream-v6-artifacts.json).
Firmware/EXE/DLL/ASM/SIS/keys/screenshots remain local.
