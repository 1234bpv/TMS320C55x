# Response to `TASK_DSP_CLOCK`: C55x frequency and why the benchmark is lower than expected

Source: the `../SymbianOverclock` project, which has kernel access to PRCM.
Full analysis and all intermediate steps — `../SymbianOverclock/docs/findings.md`
§23–§25. Device — the same Nokia N95 8GB (RM-320), 2026-08-11.

Here is only what pertains to this project. **Measured facts are explicitly
separated from assumptions**; where "hypothesis" stands, there is no proof.

---

## 1. Short answer

**The hypothesis "C55x is clocked at half the nominal rate" is false.** DSP is
already at nominal 220.16 MHz, and was at it the entire time.

**DSP overclocking is still available, but via a different lever — the DPLL
multiplier.** With `mult 111` C55x runs at 284.16 MHz, and your benchmark sees
this: **1 136 260 → 882 995 us, that is −22%.** No changes in your code are
needed for this.

**There is no hidden "performance mode" that would hold DSP down.** The
hypothesis regarding `ivapolicyserver` and a ×3–4 reserve (`CHARACTERIZATION.md`
§8) is not confirmed — justification is in §5.

---

## 2. What was measured on hardware

Reading registers of the DSP domain (RM-320, device idling):

```
CM_FCLKEN_DSP @c6008800 = 00000401
CM_ICLKEN_DSP @c6008810 = 00000002
CM_IDLEST_DSP @c6008820 = 00000000
CM_CLKSEL_DSP @c6008840 = 000023c3
fields: DSP[3:0]=3  [4:0]=3  IF[6:5]=2  bit7=1  IVA[12:8]=3  bit13=1
```

12 snapshots in 3 seconds — **a single value**, no changes whatsoever.
`CORE/3 = 660480/3 = 220160 kHz`.

## 3. Where the "110 000" in `_BRIDGEINIT_DSP_FREQ` came from

The chain closes without a single assumption:

1. `power.dll::ord60(1)` @`0x800B1620` computes `CORE / CM_CLKSEL_DSP[3:0]` —
   the mask in code is precisely `0xF` (`ands r1, r0, #15`), not `0x1F`;
2. `CORE = DPLL × CM_CLKSEL2_PLL[1:0]`;
3. and `CM_CLKSEL2_PLL[1:0]` **itself toggles between 1 and 2** under the DVFS
   governor. This was documented long ago in the neighboring project
   (`findings` §12, §18) and encoded in its `Prepare()`, which precisely for
   that reason captures a series under load and takes the maximum, rather than
   trusting an instantaneous reading.

Hence `sel2=2 → 660480/3 = 220160`, `sel2=1 → 330240/3 = 110080`. Exactly
your two groups, with the same ratio. **The DSP divider did not change a
single time throughout this.**

Confirmation from the other side: in the entire 60-MB ROM image the literal
`0xC6008840` appears **twice**, both times in `power.dll`. The addresses of
both stock setters of this register (`0x800AC59C` in power.dll, `0x801AE900`
in ehwaomap.pdd) **do not appear a single time** in the image — neither as a
`BL` target nor in export tables. That is, firmware never changes this
divider; it is configured at boot.

### Corrections to your documents

- `DSP_GUIDE.md` §14.3 is **correct**. Your own control ("the value changed
  twofold, but throughput did not") pointed from the very beginning to the fact
  that this was not the operating frequency of the DSP.
- `DSP_GUIDE.md` §15.4 ("C55x almost always at 110 MHz") is **refuted**; it
  should be marked as false.
- MAC/cycle numbers were calculated at 220 MHz. This assumption **was
  confirmed**, no recalculation is needed.

## 4. C55x frequency limit: between 284 and 330 MHz

The divider can be changed at runtime — this was done and works (a call to the
stock `power.dll` setter via a kernel primitive, plus mandatory latching of
`PRCM_CLKCFG_CTRL`). But it is an integer divider, so from the stock 3 the
only step up in frequency is immediately 2, that is +50%.

And **silicon does not hold 330 MHz**:

| what was done | result |
|---|---|
| divider 2, DSP idling, 120 s with sampling | clean |
| divider 2, DSP idling, 240 s of deep idle | clean |
| divider 2, inside the window of `dsptest baseonly...` | **device died at `child: started`** |
| divider 2, left in the system, device "idling" | delayed reboot |

The last row is for the same reason: sooner or later the DSP domain brings up
something stock (audio, notifications), and the same repeats. Generalization:

> **The DSP domain at 330 MHz is alive while nothing executes on C55x, and
> falls over as soon as the DSP is brought up.**

Therefore:

| C55x frequency | source | state |
|---|---|---|
| 220.16 MHz | stock | — |
| **284.16 MHz** | `mult 111` | **works daily, including audio** |
| 330.24 MHz | divider 2 | crashes device under any DSP work |

**Practical conclusion for you: the divider is unsuitable for overclocking
(too coarse), while the DPLL multiplier provides +29% safely and is already
verified.**

Moving the divider in the other direction (4, 6, 8 → 165 / 110 / 82 MHz) is
safe by construction and can be useful for power saving when the DSP is not
needed.

---

## 5. Why the benchmark is lower than expected

### 5.1. The measurement that verifies this

The same node, the same `dsptest`, the same binaries (`sweep.ps1 -SkipBuild`,
node from 2026-08-10 22:28 — not rebuilt between series), 3 runs per point,
summary — minimum of the series:

| CORE | DSP frequency | time, us | spread |
|---|---|---|---|
| `mult 86` (stock) | 220.16 MHz | **1 136 260** | 5% |
| `mult 111` | 284.16 MHz | **882 995** | 15% |

Speedup is **28.7%**. Pure clock scaling predicts
`284.16/220.16 − 1 = 29.1%`. Match within a quarter of a percent.

> Caveat: absolute numbers are comparable only within these two series —
> repeat count in the node and workload here are those embedded into existing
> `bench.dll55l`, not the default ones in `sweep.ps1`.

### 5.2. What follows from this

**1. Benchmark time is almost entirely determined by execution on the DSP.** If
a significant fraction were fixed overheads (node creation, message exchange,
the ARM side), the gain would be noticeably smaller than clock scaling. Your
differential method (20000 vs 10000) works correctly.

**2. There is no hidden performance mode.** The machine responds exactly to the
frequency that was set. A policy that "nobody asked for" would not scale
linearly with CORE. Plus separately: nobody holds anything back through
`CM_CLKSEL_DSP` (§3). If `ivapolicyserver` does anything, it is not via this
divider — voltage or a ceiling remain, and there is no evidence in their favor
so far.

**3. Hence the deficit is not in frequency, but in cycles per operation.**
~67 M op/s at 220 MHz is ~0.3 operations per cycle, and the value is constant.

### 5.3. Where the weak point is in §8 of `CHARACTERIZATION.md`

The conclusion "actual clock is around 60 MHz" relies on all workloads giving
the same number of operations per second. But a **uniform stall gives exactly
the same signature as a fourfold lower clock**: if each instruction fetch
costs extra cycles, this equally slows down Q15, fp32, and division. Your
measurement does not distinguish these two cases.

The control kernel `dsp_reg_mac` does not distinguish this either. It
eliminates access to **data**, but code is fetched from the same place as
before. That is, it verified "data is not the bottleneck", not "memory is not
the bottleneck".

And the clock is now known directly from the register. **The "low clock"
version on the hardware side is closed**: 60 MHz in `CM_CLKSEL_DSP` does not
exist and cannot be there.

### 5.4. The hypothesis I consider most likely (not proven)

**Node instruction fetching.** This is the only mechanism that uniformly slows
down any code while remaining unnoticed by your control kernel. Where the
loader places the node's `.text` is determined by the segment mask in the DCD
record (`bench_dcd.s55`, fields 30/31 `0ff3f3f00H` / `0ff3f3f02H`), not
`.lcf`. If code ends up outside the internal DSP memory, every fetch costs
wait states.

How to test without relying on guesswork: create two kernels with **identical**
arithmetic, but different sizes of the working loop — a tight `RPT` loop (one
instruction executed many times, fetch is amortized) versus unrolled linear
code of the same length in operations. If the former is significantly faster
than the latter, the bottleneck is code fetching.

### 5.5. Second hypothesis, cheap and safe to test

**DSP frequency is a hostage to the ARM governor.** `DSP = CORE/3`, while CORE
varies twofold (§3). During the DSP benchmark, ARM is **blocked waiting** for
the result, which from the governor's perspective looks like idle — the most
natural consequence: OPP drops, CORE drops twofold, DSP along with it.

This also explains that particular feature of your data that you attributed to
audio stack preemption: estimates **monotonously decrease** with increasing
workload volume (88.1 → 68.2 → 55.6 MMAC/s). The longer DSP computes alone,
the greater fraction of time the governor maintains low OPP, the lower the
asymptotic speed. Audio preemption does not predict such monotonicity, but
this mechanism does.

**Verification:** keep ARM busy with a separate thread in a loop for the
duration of DSP work. If part of the gap comes from the governor, numbers must
go up. Done entirely on your side, the device risks nothing.

---

## 6. What can be taken from this right now

1. **+29% DSP clock frequency for free** — run `patcher hold 111` from
   `../SymbianOverclock` before your series. Measured −22% in time.
2. **Do not look for hidden throttle** — it does not exist; one must look for
   cycles per operation.
3. **Do not attempt to increase DSP divider** — 330 MHz crashes the device as
   soon as anything is launched on C55x.
4. **Check the governor** (§5.5) — the cheapest among open experiments.
5. **Check code fetching** (§5.4) — the most probable cause of the deficit.
