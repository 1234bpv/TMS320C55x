# Characterization of C55x versus ARM1136 — measured data

Device: Nokia N95 8GB (RM-320), OMAP2420. ARM1136 @ ~325 MHz (measured with NOP loop),
C55x @ 220 MHz (nominal; DSP frequency was not measured — see §5).

Measurement channel: work is performed in the node `create` phase, time is taken on ARM
around `DoControl(5)`. A point is valid **only** with `node-create status == 0`.
Estimate is the **minimum of the series**: interference can only slow things down.

---

## 1. Q15 dot-product (W_DOT16) — duration ladder

Working set 1024×int16, entirely in DSP memory.

| repeats | min time, us | series | spread | ok |
|---|---|---|---|---|
| 0 (base) | 9 002 | 3 | 33 % | 3/3 |
| 5 000 | 64 056 | 8 | 25 % | 8/8 |
| 20 000 | 314 483 | 5 | 22 % | 5/5 |
| 40 000 | 751 037 | 5 | 10 % | 5/5 |
| 70 000 | 1 329 559 | 8 | 4 % | 8/8 |

### Long workloads: 1 minute versus 2 minutes

Measured after eliminating the accumulator defect (§2):

| repeats | time | MMAC/s | spread | ok |
|---|---|---|---|---|
| 200 000 | 4.073 s | 50.28 | 0 % | 2/2 |
| 400 000 | 8.148 s | 50.25 | 0 % | 2/2 |
| 3 000 000 | **61.146 s** | 50.24 | 1 % | 2/2 |
| 6 000 000 | **122.598 s** | 50.11 | 0 % | 2/2 |

**There is NO degradation on long workloads.** Between the one-minute and
two-minute runs performance drops by **0.25 %** — within the margin of error.
Scaling is perfectly linear: 122.598 / 61.146 = 2.0050 when doubling the volume.

**Stability is excellent:** spread 0–1 % across all points from 4 to 123 seconds.

Steady-state value for planning: **50.2 MMAC/s**.

### Speed on short chunks

Absolute (time minus base 9 002 us):

| repeats | MAC | MMAC/s |
|---|---|---|
| 5 000 | 5.12 M | **93.0** |
| 20 000 | 20.48 M | 67.0 |
| 40 000 | 40.96 M | 55.2 |
| 70 000 | 71.68 M | 54.3 |

Differential (slope between adjacent points — cancels out any fixed
component):

| segment | MMAC/s |
|---|---|
| 0 → 5 000 | 93.0 |
| 5 000 → 20 000 | 61.3 |
| 20 000 → 40 000 | 46.9 |
| 40 000 → 70 000 | 53.1 |

Short chunks show HIGHER numbers (61–93 MMAC/s), but they should not be trusted:
useful work there is 55–300 ms, while base 9 ms with its own spread of
±3 ms is subtracted, so the error reaches tens of percent. Long runs (§above)
give 50.2 MMAC/s with a spread of 0 % and perfect linearity — this exact number
is the operational one.

---

## 2. "Duration ceiling" that does not exist — it was a defect in our code

Initially there was a conclusion here about a non-deterministic ceiling of ~1 s,
beyond which node creation supposedly becomes unreliable. **This conclusion is
false**, and refuting it is perhaps the most valuable result of this stage.

What was observed (Q15, series of 2–5 runs):

| repeats (×1000) | 40 | 45 | 50 | 55 | 60 | 65 | 70 | 75 | 80 | 90 | 100 | 120 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| result | ok | **-2** | **-2** | ok | **-2** | **-2** | ok | ok | **-2** | ok | **-2** | ok |

The result is **deterministic by the number of repeats** (0/5 or 5/5), but time
does not correlate with it: 1.20 s fails, 1.33 s passes, 2.38 s passes. Thus
this is not a timeout. Control experiment: **branching workload passed 3/3 at
3.13 s** — meaning duration has nothing to do with it at all.

**Root cause.** `dsp_q15_dot(gBuf, gBuf, N)` is a sum of squares, that is, the
exact same **positive** number every time, and `acc += ...` steadily overflows
the 32-bit `long`. It was sufficient to bound the accumulated value (`& 0x3F`)
so that points 45 000 and 60 000, which previously failed 0/7, passed 2/2 —
**in the same time** (886 vs 889 ms, 1197 vs 1205 ms). After this, 122.6 s
was measured without a single failure.

The exact mechanism on the DSP side was not established (likely overflow of the
40-bit accumulator or a saturation trap). But the connection was proven by
experiment: remove overflow — failures disappear, execution time does not change.

**The fp32 failure had the same root**: the `(long)s` conversion overflowed
there. Two independent cases, one defect.

⚠️ **Main practical conclusion.** Integer overflow on C55x **does not wrap
silently like on ARM** — it crashes the node phase, while on ARM this looks
like a bare `-2` without diagnostics. And since it is deterministic with
respect to data, it is very easy to confuse it with a system limitation. I spent
most of this stage on this false hypothesis.

---

## 3. Workload matrix: C55x versus ARM1136

DSP: minimum of a series of 3, base subtracted. ARM: best-of-3, the same
source code (`src/dsptest.cpp` ↔ `src/dsp/bench_node.c`), the same data (LCG,
seed 12345).

| workload | C55x | ARM1136 | ratio | per cycle |
|---|---|---|---|---|
| Q15 dot (16-bit MAC) | 54.3–93.0 MMAC/s | 32.2 MMAC/s | **DSP ×1.7–2.9** | DSP ×2.5–4.3 |
| int32 (32×32 MAC) | 1.47 MMAC/s | 23.0 MMAC/s | **ARM ×15.7** | ARM ×10.6 |
| branches (state machine) | 8.99 Melem/s | 9.98 Melem/s | ARM ×1.11 | DSP ×1.33 |
| fp32 (emulation) | 0.066–0.085 MMAC/s | 4.90 MMAC/s | **ARM ×58–74** | ARM ×50 |

Raw DSP points:
- int32: reps=800 → 567 687 us, base 9 002 → 558 685 us for 819 200 MAC.
- branches: reps=500 → 64 941 us, base 7 995 → 56 946 us for 512 000 elements.
- fp32: base 9 948; reps=20 → 252 380 us (0.0845 MMAC/s);
  reps=40 → 564 666 us (0.0738). Differential 20→40: 20 480 MAC / 312 286 us
  = **0.0656 MMAC/s** — this is the steady-state value, 0.0845 is peak.

⚠️ The fp32 number deserves a separate caveat: 0.0656 MMAC/s at 220 MHz is
≈3 350 cycles per multiply-accumulate, that is ≈1 700 cycles per call to
`__mpyd`/`__addd`. This is an order of magnitude larger than expected for
software emulation (100–300 cycles). An explanation was not found; the number
is cited as measured, not as justified. That it is NOT explained by slow
memory is evident from Q15, which on the very same buffers yields 4 cycles per MAC.

### What follows from this

- **16-bit fixed-point is the only domain where the DSP wins.** That is where
  dual MAC operates.
- **32-bit integer arithmetic is a disaster.** `long × long` on C55x is a
  subroutine call to `__mpyli`, not an instruction; hence the ×15.7 loss. Code
  that "just uses int" on C55x will get 32-bit operations where the programmer
  intended 16-bit ones (on C55x `int` = 16 bits!), or vice versa — expensive
  calls where `long` was written.
- **Code with conditional branches runs roughly on par** (ARM ×1.11 in
  absolute terms, DSP ×1.33 per cycle). That is, porting application logic — a
  messenger, parser, state machine — to the DSP **makes no sense**: there is no
  gain, while all the complexity of node loading, DCD, and IPC remains.

---

## 4. ARM↔DSP communication cost

| operation | time |
|---|---|
| full cycle "create node with empty phase" | **9 002 us** |
| the same cycle, spread | 8.0–19.1 ms |

This is the lower bound of the cost of **launching work on the DSP**: DCD parsing
is already done, the task is created (`fn=4`), leaving `create` with zero workload.

**What could not be measured and why.** The stock dspbridge message queue
(ordinals 15–18 of `bridgeapi`, ioctl `0x0C000001/2`) on this firmware is dead
code: not a single module in ROM uses it, and calling it crashes the kernel.
Therefore the **cost of an individual ARM→DSP→ARM message was not measured**,
and there is no number for it in this document. Likewise, array transfer via
DMM was not measured.

Practical consequence: **a threshold task worth offloading to the DSP starts at
approximately 10 ms of its own work.** Anything shorter is swallowed by launch
cost. No upper bound was found: tested up to 122.6 s of continuous work in a phase.

---

## 5. Caveats regarding the numbers

- C55x frequency was **not measured**, nominal 220 MHz was taken. All "per
  cycle" columns for DSP depend proportionally on this assumption.
- ARM frequency was measured with a NOP loop: 321–325 MHz between boots.
- DSP is shared with the audio stack; our nodes have priority 05H, deliberately
  lower than audio (0aH–0eH). Therefore what was measured is performance of a
  **guest on a busy DSP**, not the peak capability of C55x.
- A suspiciously **fast** run should be discarded rather than accepted as a
  record: once 70 000 repeats yielded 728 ms against a stable 1.33 s in a
  series of eight. Minimum-of-series is correct only as long as all runs do the
  same work.

---

## 6. Who in the system actually uses the DSP

Cross-references by export addresses throughout `sys/bin` of ROM.

Only `bal.dll` (18 places) and `ivapolicyserver.exe` (16) call `bridgeapi.dll`
directly. Clients of `bal.dll` are exclusively **gateways for codecs and audio
effects**:

- codecs: `aacdecgwc`, `aacencgwc`, `eaacplusdecgwc`, `mp3decgwc`,
  `amrdecgwcti`, `amrencgwcti`, `amrwbdecgwcti`, `g711dec/encgwc`,
  `g729dec/encgwc`, `ilbcdec/encgwc`, `rawgwc`;
- effects: `revbgwc` (reverb), `mumdrceqgwc` (DRC/equalizer), `pos3dgwc`
  (3D positioning), `stwgwc`, `audvisgwc` (visualization);
- all of this through the shared `gwc.dll` (15 places).

**Players — RealPlayer, `mediaplayer.exe` — do not access the DSP.** They work
with the multimedia framework, which in turn picks up these gwc plugins. That
is, there is no publicly accessible compute path to C55x in the firmware: DSP
is accessible only as an accelerator for audio codecs and effects. Everything
this project does is bypassing this boundary.

## 7. Why not 2 MACs per cycle

Analyzed from the generated assembly (`cl55 -v5510 -o3`).

**The inner loop of `dsp_q15_dot` is a single MAC:**

```
        RPT CSR
        MACM *AR1+, *AR0+, AC0, AC0
```

That is, the theoretical ceiling of this specific code is **1 MAC/cycle**, not
2. We measure 50.2 MMAC/s, that is 4.4 cycles per MAC at nominal 220 MHz.

**Dual MAC on C55x has a rigid structural requirement.** Its form is —

```
MAC Xmem, coef(Cmem), AC0 :: MAC Ymem, coef(Cmem), AC1
```

both multipliers take a **shared** operand from the coefficient bus (CDP).
Hence the dot product of two **independent** vectors `sum(a[i]*b[i])` cannot
use dual-MAC in principle: each multiplication needs its own pair of operands.
Only structures with a shared operand provide a gain — FIR for two output
samples, correlation, matrix-vector.

Verified additionally:
- FIR for two outputs written in canonical dual-MAC form is transformed by the
  compiler into **two sequential** `MACM` (shared `*AR4`), rather than a pair
  via `::`;
- in `c55x.h` there are **no** dual MAC intrinsics — only single `_smac`,
  `_smpy`, `_smacr`.

**Conclusion: dual-MAC on this toolchain is available only from assembly.** From
C it cannot be obtained either directly or by hint.

### Memory is not the bottleneck — FALSE CONCLUSION, control is unusable

> **Refuted on 11.08.2026.** The control kernel does not do what is written here:
> `dsp_reg_mac` compiles not into a MAC, but into a chain of three ALU additions
> (the compiler folds multiplication by a constant), so a single `MACM` was
> being compared against three instructions. A proper cycle measurement gives
> **1.05 cycles per register instruction versus 1.97 per `MACM` from memory** —
> that is, memory costs exactly twofold. Analysis and numbers — `DSP_GUIDE.md`
> §15.8. The text below is retained as a description of the error.

The control kernel `dsp_reg_mac` executes the same 1024 MACs per iteration, but
holds operands in registers — there are no memory accesses in the loop at all.

| kernel | 20 000 repeats | speed |
|---|---|---|
| Q15 dot (two operands from memory) | 314 483 us | 67.0 M/s |
| MAC in registers (zero accesses) | 339 416 us | 62.0 M/s |

There is practically no difference (register version is even slightly slower
due to an extra increment). Hence 4.4 cycles per MAC are **not explained** by
the node's external memory. The hypothesis remains regarding actual DSP
frequency significantly lower than nominal 220 MHz — to verify it, the `W_CLKP`
workload was added (§8).

### How many operations per second the machine actually delivers

Let us calculate the approximate number of machine operations per element for
four completely different workloads:

| workload | speed | op/element | operations/s |
|---|---|---|---|
| Q15 (`RPT` + `MACM`) | 67 M/s | 1 | ~67 M |
| manual int32 (3 multiplications + shifts) | 4.09 M/s | ~15 | ~61 M |
| manual fp32 | 0.149 M/s | ~400 | ~60 M |
| manual division (32 iterations) | 0.233 M/s | ~192 | ~45 M |

**45–67 million operations per second, regardless of code type.** C55x for such
sequences is mostly single-cycle, hence actual operating frequency is **around
60 MHz, not nominal 220**.

> **Refuted on 11.08.2026.** Frequency was read directly from PRCM: 220.16 MHz,
> stably (`docs/ANSWER_DSP_CLOCK.md`). Equality of "operations/s" across
> different workloads does not distinguish a low clock from uniform stalling —
> both produce the same signature. Real breakdown: ~1 cycle per register
> instruction, ~2 cycles per `MACM` from memory, plus the DVFS governor taking
> another ~19% on measurements where ARM idles. See `DSP_GUIDE.md` §15.7–15.8.

**Hypothesis of the cause (not proven).** The DSP performance mode on this
platform is governed by `ivapolicyserver.exe` — and that is precisely what we
bypass by accessing `bridgeapi` directly. That is, DSP remains in a low power
mode simply because nobody requested a high one. If so, the stock path (or
direct setting of OPP) could yield another 3–4 times. **Not verified.**

An alternative explanation — uniform ~4-fold pipeline stalling by external
memory — is less consistent with data: the register kernel (without data
accesses) and the kernel with two operands from memory give the same speed.

## 9. Hand-written arithmetic versus compiler helper routines

Implementations — `src/dsp/c55math.h`; correctness verified by model
`tools/check_math.py` (mul32 and divu32 — exact on 200k/100k random pairs,
fmul/fadd — within 1 ULP).

| operation | C55x compiler | C55x manual | gain | ARM1136 |
|---|---|---|---|---|
| int32 32x32 multiplication | 1.47 MMAC/s | **4.09** | **×2.8** | 22.9 |
| fp32 multiplication+addition | 0.0656 MMAC/s | **0.149** | **×2.3** | 4.95 |
| division 32/32 | **0.407 M/s** | 0.233 | ×0.57 | 10.93 |

**Multiplication is worth writing by hand, division is not.** Subroutine `__divul`
from the base image beats our shift-subtract loop by 1.75 times (most likely
uses hardware `SUBC`).

Even after manual optimization ARM remains ahead: int32 by 5.6 times, fp32 by
33 times, division by 27 times. That is, manual arithmetic reduces the loss,
but does not reverse it — the conclusion "only 16-bit fixed-point on DSP"
remains valid.

### Two measurement pitfalls caught here

1. **A function call costs more than the arithmetic itself.** While `dsp_mul32`
   resided in a separate module, the manual version was THREE TIMES SLOWER than
   the compiler one: `cl55` without `-pm` does not do cross-module inlining.
   Moving it into a header yielded an eightfold speedup of the same function.
2. **An overflow mask ruined the benchmark.** Accumulation
   `s += (mul32(x,x) & 0x3F)` yielded "33 MMAC/s" — that is ~2 machine operations
   per 32x32 multiplication, which is impossible. The lower 6 bits of a product
   depend only on the lower bits of the factors, so the compiler legitimately
   discarded two of the three partial products. The correct form is
   `s ^= mul32(x,x)`: XOR preserves all 32 bits and does not overflow.

## 10. What remained unexplained

1. The exact mechanism by which integer overflow crashes the node phase on the DSP (§2).
2. Why fp32 costs ≈3 350 cycles per operation (§3).
3. Actual C55x frequency (nominal 220 MHz was taken).
