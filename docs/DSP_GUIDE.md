# Guide: How to Write Reliable Code for TMS320C55x in an OMAP2420 Smartphone

Summary of practically significant results from the "custom code on C55x in Nokia N95" project.
Written for anyone intending to use the DSP in **their own** application —
standalone or in parallel with ARM.

All numbers are measured on a live device (Nokia N95 8GB, Symbian 9.2, S60 3rd FP1).
Full tables and methodology are in `CHARACTERIZATION.md`; technical reversing is in `findings.md`.

---

## 1. The most important: when DSP is worth the effort at all

The first decision is not "how", but "is it worth it". The answer is given by the measured ratios:

| what you compute | C55x (actually ~60 MHz, §10) | ARM1136 @325 MHz | verdict |
|---|---|---|---|
| 16-bit fixed-point (Q15 MAC) | 54–93 MMAC/s | 32 MMAC/s | **DSP ×1.7–2.9 — take DSP** |
| 32-bit integer arithmetic | 1.5 (manual 4.1) MMAC/s | 23 MMAC/s | **ARM ×5.6 — do not take DSP** |
| logic with conditional branches | 9.0 Melem/s | 9.6 Melem/s | parity — **not worth the effort** |
| fp32 (emulation) | 0.066 (manual 0.15) MMAC/s | 4.9 MMAC/s | **ARM ×33 — categorically no** |
| 32/32 division | 0.41 Mdiv/s | 10.9 Mdiv/s | **ARM ×27 — categorically no** |

("manual" — with the `c55math.h` library, §11.)

**Rule.** C55x wins exactly where its dual MAC works: 16-bit
multiply-accumulates over a stream of data. Everything else it either loses or matches
at parity — while the entry price (node loading, DCD, IPC, risk of wedging the DSP)
remains full.

That is, offloading application logic to the DSP — message parsing, state machines,
UI computations — **makes no sense**. Offloading filters, convolutions, codecs,
correlation over int16 — does.

### Threshold task

| quantity | value |
|---|---|
| cost of launching work on DSP (empty phase) | **≈9 ms** |
| steady-state throughput (Q15) | **50.2 MMAC/s** |
| maximum verified duration of a single chunk | **122.6 s** (no limit found) |

A task shorter than ~10 ms is eaten up by overhead. There is no upper limit: two minutes
of continuous work in a phase pass with 0 % spread.

---

## 2. C55x language and type traps

This is the most expensive section: every point cost either a ruined measurement or a reboot.

### `int` is 16-bit

```c
for (int i = 0; i < 100000; i++)   /* NEVER TERMINATES */
```
`i` reaches 32767, wraps around to −32768, and the loop spins forever. From the
outside, this looks like "DSP wedged on a long task", even though the DSP is dutifully
executing an infinite loop. **Counters and anything that can exceed 32767 must be `long` only.**

Full type model:

| type | bit width |
|---|---|
| `char`, `short`, `int` | 16 bits |
| `long` | 32 bits |
| `float`, `double` | **both 32 bits** |
| accumulators | 40 bits |

`char` being 16 bits wide means that an "array of bytes" on C55x is an array of 16-bit
words. Data formats shared with ARM must be described **only** with 32-bit
fields (`long`), otherwise structures will misalign.

### 32-bit multiplication is a subroutine call

`long × long` compiles into a call to `__mpyli`, not an instruction. The same
principle applies to `__divi`, `__remi`, `__divli`. **Division and 32-bit multiplication in
a hot loop are prohibited.**

If 32-bit multiplication is indeed unavoidable, a manual implementation via three 16x16
multiplications yields **×2.8** (§11). Leave division to the compiler, however — its subroutine
wins by a factor of 1.75.

### Floating point is also subroutines

`__addd`, `__subd`, `__mpyd`, `__divd`, `__cmpd`, conversions `__fltid`,
`__fixdli`. The suffix is `d`, not `f` — because `double` here is 32-bit. (I searched for
`_addf`/`_mpyf` for a long time, could not find them, and mistakenly recorded that floating point was absent in the base image.)

### Integer overflow crashes the node — this is the main rule of reliability

On ARM, signed integer overflow quietly wraps around, and code continues
running with an incorrect number. **On C55x, it kills the node phase.** On ARM, this
is visible as a bare `-2` without any diagnostics.

Two independent cases in this project:

1. `acc += dot(gBuf, gBuf, N)` in a loop — a sum of squares, i.e. the same positive
   number every time; `acc` overflows the 32-bit `long` faster with more
   repetitions. It is enough to mask the accumulated value (`& 0x3F`) for points that failed
   0/7 to pass 2/2 **in the same amount of time**.
2. `(long)s` for an fp32 sum of ~3.6e11 — conversion via `__fixdli` exceeds
   32 bits. The node crashed **every time** when `reps > 0`, regardless of duration.

The most insidious aspect is that the crash is **data-deterministic**: some parameter
values work stably, while others stably crash. This is extraordinarily easy
to confuse with a platform system limit — which is exactly what I did, spending most
of the phase on a false hypothesis about a "duration ceiling".

**Rules:**
- normalize input (for fp32 — to [−1,1));
- estimate the maximum of each accumulator **before** writing the loop;
- when diagnosing `-2`, **the primary suspect must be your arithmetic**, not
  the platform. Verification: the same workload with a clamped accumulator.

---

## 3. Node memory discipline

**Keep `.bss` minimal.** When arrays for three different workloads were kept
in the code simultaneously, `.bss` grew from 1024 to ~5120 words — and the baseline run, which
previously completed stably in 8 ms, stopped creating. There is no diagnostic:
simply `-2`.

Declare buffers conditionally, for a specific mode:

```c
static short gBuf[N];
#if WORKLOAD == W_FP32
static double gF[N];        /* only where really needed */
#endif
```

The DCD fields `static data size` / `global data size` / `program memory`
(`0200H`/`080H`/`0c00H` in our nodes) **are not the lever** to fix this:
increasing them did not help. Reducing `.bss` specifically did.

---

## 4. Long tasks: no degradation

| duration | MMAC/s | spread | ok |
|---|---|---|---|
| 4.07 s | 50.28 | 0 % | 2/2 |
| 8.15 s | 50.25 | 0 % | 2/2 |
| 61.15 s | 50.24 | 1 % | 2/2 |
| 122.60 s | 50.11 | 0 % | 2/2 |

Between a one-minute and a two-minute task, performance drops by **0.25 %** — within
the margin of error. Scaling is perfectly linear, spread is zero. **Long computations on
C55x are entirely viable**, and there is no need to split them into chunks.

Short chunks show higher numbers (61–93 MMAC/s), but this is an artifact: the
9 ms baseline with a spread of ±3 ms is subtracted there from a useful 55–300 ms. **Plan
around 50 MMAC/s.**

### Caution with conclusions about "system limits"

Originally, this section featured an "undetermined ceiling of ~1 s", beyond which node
creation was supposedly unreliable. That was false: the reason was **our own arithmetic**
(§2, accumulator overflow), not the platform. Misleading symptoms:
the result was deterministic (0/5 or 5/5), failure arrived at approximately the
expected completion of work, and `-2` carried no diagnostics.

The test that exposes this: **run the same duration with a different workload.**
The branching kernel passed 3/3 at 3.13 s where Q15 crashed at 1.20 s — and the ceiling
hypothesis collapsed immediately.

---

## 5. Safety rules: what crashes the device

Bought with reboots. Violating these rules does not return an error — it
reboots the phone **immediately**.

- **Never `User::LoadLogicalDevice("ehwa.ldd")`.**
- **Ordinal 26 of `bridgeapi` on a node crashes the device** — on both custom and
  stock nodes. Workaround: call DCD parsing directly. If `ord26` is truly needed —
  keep the file open exclusively, which gives `-14` instead of a reboot.
- **Do not call task command `fn 18`.** `fn 0..17` are verified.
- Pass **`TBuf8`, not `TPtr8`** to the kernel: it does a raw read
  of fixed size from the pointer.
- Asynchronous operations (`fn 5..8`) — **must** have a status wait, and
  `TRequestStatus` must be **static**: otherwise the driver will write into a destroyed
  stack frame.
- **`fn=6` is node deletion**, not "start". Always call it, including in
  error paths.

### Signs that the DSP is wedged

In increasing order of severity:

| symptom | what it means |
|---|---|
| `fn=5` → `-2` | phase did not finish in time; **harmless**, the next run will pass |
| `fn=4` → `-2`, `taskHandle=0` | **wedged**, recoverable only by reboot |

What wedges is not the failure itself, but the **accumulation** of failures and **abandoned waiting** —
when ARM stops waiting while the phase is still executing. Therefore, the wait ceiling on
ARM must be comfortably greater than the longest workload, but not absurdly
large (§8).

---

## 6. What DSP code can use "for free"

A dynamic node does not link against `rts55.lib` — undefined symbols are resolved by
the loader against the **base image of the specific firmware**. That is, the set of
available features is defined not by TI documentation, but by the symbol table of your device.

**Mandatory check before every run:** take the list of
`UNDEFINED EXTERNAL SYMBOL` entries from `DLLdump` and cross-check **every one** against the
base symbol table. A symbol not in the base = the node will not load.

```powershell
DLLdump.exe bench.dll55l          # -> bench.dd
# every UNDEFINED EXTERNAL SYMBOL must be in docs/base_syms.txt
```

In our base (1382 symbols), available symbols include: `_NODE_getMsg`, `_NODE_putMsg`,
`_CLK_gethtime`, `_CLK_countspms`, all 32-bit arithmetic (`__mpyli`, `__divli`,
`__remi`, …), and all fp32 emulation (`__addd`, `__mpyd`, `__divd`, `__fltid`,
`__fixdli`, …).

---

## 7. ARM↔DSP communication: what works and what does not

| mechanism | state on this firmware |
|---|---|
| node creation + phase (`fn=4`, `fn=5`) | **works**, ≈9 ms overhead |
| message queue (ordinals 15–18, ioctl `0x0C000001/2`) | **dead code** — not used by any ROM module, calling it crashes the kernel |
| return value from phase to ARM | **does not arrive** (returned `0x1234` — ARM saw `0`) |

A consequence that determines the architecture of any application on this platform:
**the standard data path is unavailable**, and the cost of an individual
ARM→DSP→ARM message cannot be measured — a number for it does not exist in this
project and is not fabricated.

The working channel that remains: **execute work in the `create` phase and measure time
on ARM**. Parameters are passed only at build time (`-D`), since
the phase takes no arguments.

---

## 8. How to measure honestly

A methodology without which the numbers are worth nothing:

1. **A data point is valid only when `status == 0`.** Time without status checking
   measures a timeout or crash. I twice obtained a "result" of exactly 4.707 s — that was my
   own wait ceiling, not DSP work.
2. **`User::After(10000)` is not 10 ms, but ~15.6 ms** (nanokernel tick
   granularity). 300 iterations yield exactly 4.7 s and look convincing.
3. **Differential measurement.** Phase time includes fixed overhead; take the difference
   between two runs with different repetition counts.
4. **Minimum of a series**, because interference can only slow things down. But:
5. **An abnormally FAST run must be discarded**, not accepted as a record. Once,
   70 000 repetitions yielded 728 ms against a stable 1.33 s in a series of eight.
   Minimum-of-series is correct only as long as all runs do the same work.
6. **Both binaries from the current tree.** The series script initially updated only
   the DSP node, and runs quietly executed with the old ARM host; that is where
   the bogus 4.7 s came from.
7. **Wait ceiling ~25 s**, not 200: a run keeps the deployment harness busy
   for its entire duration, so an oversized ceiling turns each failure into several minutes
   of downtime.

---

## 9. Gaps — honestly

- **fp32 is measured (0.0656 MMAC/s), but unexplained.** This is ≈3 350 cycles per
  multiply-accumulate — an order of magnitude more than expected from software
  emulation. Slow memory does not explain this: Q15 on the same buffers yields
  4 cycles per MAC. The number is presented as measured, without a hypothesis.
- **C55x clock frequency is unmeasured** — nominal 220 MHz is assumed. All "per cycle"
  estimates for DSP depend proportionally on this assumption.
- **ARM↔DSP message cost** is not measured due to the dead queue (§7).
- **The mechanism by which integer overflow crashes the phase** is not established
  (likely a 40-bit accumulator or saturation trap). Only the cause-and-effect
  relationship is proven: eliminate overflow — failures disappear, execution time
  remains unchanged.
- **Some ROM modules in the `bridgeapi` client list are false positives.** Modules with
  a single hit (e.g. `adobereader.exe`, `phone.exe`) almost certainly
  contain simply a coincidental 32-bit constant; reliable clients are those with
  5-18 call sites (§14).

---

## 10. What to expect from hardware: 2 MAC/cycle and real frequency

### Dual MAC requires a shared operand

The advertised "2 multiply-accumulates per cycle" are real, but have a structural
condition. The instruction form:

```
MAC Xmem, coef(Cmem), AC0 :: MAC Ymem, coef(Cmem), AC1
```

both multipliers take a **shared** operand from the coefficient data bus (CDP). Therefore,
a dot product of two **independent** vectors `sum(a[i]*b[i])` cannot
use dual-MAC in principle. A speedup is provided only by structures with a shared
operand: **FIR for two output samples, correlation, matrix-vector**.

When designing an algorithm for C55x, look specifically for this form — otherwise half
of the multipliers will remain idle.

### The compiler does not generate dual-MAC

`cl55` 4.4.1 for a typical dot product produces a single
`RPT CSR` + `MACM`. Even a dual-output FIR written in the canonical
dual-MAC form is translated into **two consecutive** `MACM` instructions, not into a pair via
`::`. There are no dual-MAC intrinsics in `c55x.h`.

**Conclusion: dual-MAC is available only from assembly.**

### Frequency is nominal (220 MHz), and the deficit is in cycles per operation

> **Corrected 11.08.2026.** In earlier revisions, this section claimed that the
> DSP runs at ~60 MHz (and §15.4 — that it runs at 110 MHz). **Both claims are false.**
> `CM_CLKSEL_DSP` was read directly from PRCM via kernel access: `0x000023C3`, divider
> field `[3:0] = 3`, stable → CORE/3 = 220.16 MHz, and so all the time.
> Analysis is in `docs/ANSWER_DSP_CLOCK.md`. Below is the original measurement, which remains
> correct, and its proper interpretation.

Count the machine operations per second for different workloads — they converge:

| workload | op./element | operations/s |
|---|---|---|
| Q15 (`RPT`+`MACM`) | 1 | ~67 M |
| int32 manual | ~15 | ~61 M |
| fp32 manual | ~400 | ~60 M |
| division manual | ~192 | ~45 M |

**45–67 million operations per second regardless of code type.** At the measured
220.16 MHz, this means **~0.3 machine operations per cycle** — that is, each operation
costs on average 3–4 cycles instead of one.

Why "therefore frequency is ~60 MHz" was the wrong conclusion: **a uniform bottleneck
produces exactly the same signature as a clock four times lower.** If every instruction
fetch costs extra cycles, this slows down Q15, fp32, and division equally —
the equality of "operations/s" across workloads does not distinguish between these two cases. The control
kernel `dsp_reg_mac` (operands in registers) does not distinguish them either: it eliminates
accesses to **data**, but code is still fetched from the same place as before.
That is, "data is not the bottleneck" was proven, not "memory is not the bottleneck".

The most likely (but **not proven**) reason is instruction fetching of the node from
external memory. Where the loader places `.text` is determined by the segment mask in
the DCD entry (`bench_dcd.s55`, fields 30/31), not `.lcf`. A test that does not
rely on guesswork: two kernels with identical arithmetic, but a tight `RPT` loop
(fetch is amortized) versus unrolled linear code of the same length. If
the former is significantly faster, the bottleneck is indeed code fetching.

**The hypothesis "it's `ivapolicyserver.exe`'s fault" was tested and REJECTED.** Previously,
an assumption was made here that the DSP performance mode is managed by this server, while
we access `bridgeapi` directly, bypassing it. Reversing the server did not
confirm this (details in §14a):

- the server protocol consists of exactly four opcodes (128–131), and the sole parameter is **accelerator
  type** (0–5: mp4dec, postproc, mp4enc, preproc, jpegenc, jpegdec);
  there is no performance level whatsoever in the messages;
- the complete list of server imports is `euser`, `bridgeapi` (open/
  load/map), and `RBusLogicalChannel`. **Not a single** call to HAL,
  power management, or DVFS.

That is, `ivapolicyserver` is an arbiter of "who currently owns IVA" plus the loader of
`Z:\System\Data\Iva_base.dof`, not a frequency regulator.

**Where the lever actually is.** DSP power and clock management resides in
the kernel `ehwaomap.pdd`: named objects `KIVAHighPerfSem`,
`DRBJKDSPSemHP`, `DRBJKIVAPwrDomainSem`, `KDSPPwrDomainSem`, strings "Enable to
put DSP/IVA in standby mode" are there, and this is the **only ROM module (besides `smart2go.exe`)**
that contains the PRCM base `0x48008000` at all — it maps it to the kernel VA
`0x00FCE000`. Thus mode switching is not a user-space call, but an ioctl of the
`Hwa` channel or direct PRCM intervention from the kernel. This remains unresolved.

Memory **is not** the bottleneck: the kernel with operands in registers (zero data
accesses) runs at the same speed as the kernel with two operands from
memory.

---

## 11. The `c55math.h` library — manual arithmetic

A ready-to-port header: `src/dsp/c55math.h`. All functions are `static`, so they are
included directly at the call site and inlined.

| function | what it does | vs compiler |
|---|---|---|
| `dsp_mul32(a,b)` | 32x32 -> lower 32 bits, three 16x16 multiplications | **×2.8 faster** than `__mpyli` |
| `dsp_fmul(a,b)` | float32 multiplication (bit representations) | **×2.3 faster** than `__mpyd` |
| `dsp_fadd(a,b)` | float32 addition | included in that same ×2.3 |
| `dsp_divu32(n,d)` | 32/32 division by shift-and-subtract | **×1.75 SLOWER** than `__divul` |
| `dsp_reg_mac(x,y,n)` | MAC without memory accesses | diagnostic |

**Correctness verified** with the `tools/check_math.py` model, which replicates each
function with explicit 16/32-bit masking and checks against reference arithmetic:
`mul32` and `divu32` are exact on 200 000 and 100 000 random pairs, `fmul`/`fadd` — within
1 ULP.

**fp32 limitations, deliberate:** no denormalized numbers (treated as zero),
no NaN/Inf (overflow saturates to the maximum finite value),
truncation rounding. For filters and convolutions this is acceptable; for general
mathematics — not.

**Leave division to the compiler.** This is the only case where the subroutine from
the base image wins — most likely due to hardware `SUBC`.

⚠️ **Must be included via header, not as a separate module.** `cl55` without `-pm` does
not perform inter-module inlining, and a function call costs more than the arithmetic
itself: the same `dsp_mul32` in a separate `.c` was **three times slower** than
the compiler subroutine, but in the header became 2.8 times faster. An eightfold
difference — from code placement alone.

---

## 12. Quick checklist

- [ ] Task is 16-bit fixed-point over a stream? If no — leave it on ARM.
- [ ] Chunk of work is larger than ~10 ms (smaller will not amortize overhead)?
- [ ] All counters `long`, not `int`?
- [ ] **Maximum of each accumulator estimated — overflow impossible?**
- [ ] Node `.bss` minimal, buffers declared conditionally?
- [ ] Every `UNDEFINED EXTERNAL SYMBOL` exists in the firmware base?
- [ ] Node is deleted (`fn=6`) on all paths, including error paths?
- [ ] `TRequestStatus` static, status wait present everywhere?
- [ ] Throughput planned around ~50 MMAC/s, not peak 93?
- [ ] Algorithm has a SHARED operand (dual-output FIR, correlation)? Without this,
      dual-MAC is unreachable, and ceiling is two times lower (§10).
- [ ] 32-bit multiplications - via `c55math.h`, division - via compiler (§11)?

---

## 13. Context: how the system itself uses the DSP

Cross-referencing across all of `sys/bin` in ROM shows that `bridgeapi.dll` is directly
called only by `bal.dll` and `ivapolicyserver.exe`, and clients of `bal.dll` are
**exclusively codec and audio effect gateways** (`*gwc.dll`): AAC, eAAC+, MP3, AMR,
AMR-WB, G.711, G.729, iLBC, as well as reverb, DRC/equalizer, 3D positioning, and
visualization. All — via a shared `gwc.dll`.

**Players do not access the DSP.** Neither RealPlayer nor `mediaplayer.exe` has
its own path to C55x: they work with the multimedia framework, which in turn
picks a gwc plugin.

Practical conclusion for your project: **a standard, supported way to compute
custom code on this DSP does not exist.** The platform provides it only as
an audio accelerator. Everything described in this guide is a workaround that works, but
carries no compatibility guarantees with other firmware versions.

---

---

## 14. Attempt to switch DSP to a higher performance mode

Section 10 once assumed that the DSP is kept in a low-power mode because
we bypass `ivapolicyserver.exe`. The hypothesis has been tested. **It is false.**

### 14.1. What `ivapolicyserver.exe` actually does

Reversing (`tools/rev/annotate.py`, `xref.py`):

- This is a Symbian server `!IvaPolicyServer` based on `CMmfIpcServer`, version `TVersion(1,0,1)`.
  The client `ivapolicyclient.dll` has five exports: `Connect` (ord 3, itself
  starts the server via `RProcess` + global semaphore), opcode 131 (ord 4),
  opcode 129 + `Close` (ord 1), `TVersion` (ord 5), and a trivial setter (ord 2).
- The server's entire protocol consists of **four opcodes 128–131**. The only substantive
  parameter (opcode 128) is **accelerator type**: `0` mp4dec, `1` postproc,
  `2` mp4enc, `3` preproc, `4` jpegenc, `5` jpegdec, `6` "without object".
  There is no performance level, clock rate, or OPP anywhere in the protocol.
- Clients are exactly six IVA plugins (`ivamp4dechwdevice.dll`,
  `ivapostprochwdevice.dll`, `ivaicljpeg*plugin.dll`, …) plus `ivadofloader.dll`.
- The full list of server imports: `euser`, `drtaeabi`, `bridgeapi`
  (ordinals 4, 6, 9, 10, 11, 13, 25–28, 31–34, 36, 38 — open, load,
  map) and `RBusLogicalChannel`. **Not a single HAL, power, or DVFS import.**

That is, it is an arbiter of "who currently owns IVA" and a loader of
`Z:\System\Data\Iva_base.dof` — a separate base image for
video/images, parallel to our `baseimage.dof`. It is not a frequency
regulator, and connecting to it cannot speed anything up.

### 14.2. Where the lever actually is

In the kernel `ehwaomap.pdd`:

| finding | address | what it is |
|---|---|---|
| `KIVAHighPerfSem` | `0x801AF544` (ADR) | name of semaphore "IVA high performance" |
| `DRBJKDSPSemHP` | `0x801AB9CC` | the same for the DSP domain |
| `DRBJKIVAPwrDomainSem`, `KDSPPwrDomainSem` | | power domain semaphores |
| "Enable to put DSP/IVA in standby mode" | | standby management |
| `0x48008000` (PRCM base) | mapped to kernel VA `0x00FCE000` | **only** ROM module, besides `smart2go.exe`, that contains this constant at all |

Both "HP" semaphores are created in the constructors of the power domain objects.
Thus mode switching is a **kernel operation**, accessible at most through
an ioctl of the `Hwa` channel, not through any user-space server. Exactly which ioctl —
has not been found: the code dispatcher in the PDD has not been localized.

### 14.3. New instrument: reading frequency from the base image

`ehwaomap.pdd` contains the string `_BRIDGEINIT_DSP_FREQ`, and this symbol is present in
`docs/base_syms.txt`. This is a standard TI Bridge step: having loaded the base image,
the driver finds the symbol and **writes the DSP clock frequency there** (by TI convention —
in kilohertz), so that DSP/BIOS can configure timers.

Thus the frequency does not need to be inferred from indirect estimates, but can be **read**. Workload
`W_FREQ` (11) in `bench_node.c` declares `extern unsigned long
BRIDGEINIT_DSP_FREQ;` — the loader binds the reference, the node is created normally
(verified: 9.0 ms baseline, just like an empty phase).

**Result (6 runs, "value into time" channel, repeat cost 19.6 µs from
the control measurement):**

| run | clean time | value |
|---|---|---|
| 1 | 1 069 824 µs | ~218 000 |
| 2 | 501 526 | ~102 000 |
| 3 | 508 515 | ~104 000 |
| 4 | 1 187 897 | ~242 000 |
| 5 | 502 594 | ~103 000 |
| 6 | 562 317 | ~115 000 |

Two groups with a ratio of ≈2.1: **~110 000 and ~220 000 kHz**, meaning the driver
reports to the DSP either 110 MHz or 220 MHz — from run to run, within a single
system boot.

**However, the measured throughput does not change.** Control from the same
day: fixed 60 000 repetitions of Q15 — 1.186–1.266 s, 7 % spread, meaning 19.6 µs
per repetition, exactly as across the whole characterization. If 110/220 were the true operating
frequency, the time would jump twofold. It does not jump.

**Conclusion.** The value of `_BRIDGEINIT_DSP_FREQ` is what the driver *configures*,
not what the DSP *delivers*. Changing this value twofold yields no gain
whatsoever. Therefore the thesis that "DSP sits in a low OPP, with a hidden ×3–4 reserve"
**is not confirmed**: the simplest available frequency switch has already changed
twice on its own and changed nothing.

### 14.4. Caveat to §10 and to `CLK_gethtime`

Indirectly, it turned out that **the frequency of the `CLK_gethtime` counter is not constant.**
A self-normalized version of the instrument (number of repetitions scaled to the rate measured
via `CLK_gethtime`) should have yielded a constant time for a constant value —
instead it showed a 72 % spread while computational speed during the same days was
stable within 7 %. Recalculation gives a counter rate of 9.8–17.6 MHz instead of
the 26.8 MHz measured on one occasion.

Thus the earlier conclusion that "`CLK_gethtime` is clocked by the 26 MHz system crystal"
**must be considered unconfirmed**, and the counter itself — unsuitable as a reference
instrument. All performance numbers in this document were obtained with the ARM-side
timer and are unaffected by this.

---

## 15. The ioctl dispatcher and where the DSP clock actually comes from

### 15.1. Complete ioctl map of the `Hwa` channel

The dispatcher was found: `ehwa.ldd` @`0x801B52A0`, signature
`(this, aFunction, a1, a2)`.

```
cmp  r1, #10 ; addls pc, pc, r1, lsl #2      <- direct commands 0..10
...
add  r3, r1, #0xFC000000 ; cmp r3, #0x04000000
   -> 0x04000000 <= fn < 0x08000000 : vtable+0x1C of object [this+40]   (DCD)
cmp  r1, #0x08000000
   -> fn >= 0x08000000 : jump to 0x801B4AFC                          (nodes)
   otherwise -5 KErrNotSupported
```

At `0x801B4AFC`: `add r0, r7, #0xF8000000; cmp r0, #21; addls pc, pc, r0, lsl #2`
— **a 22-entry table** (`0x08000000` + 0..21), while everything `>= 0x0C000000` goes to
vtable+0x54 (node messages).

Direct commands 0..10 (`0x801B52A0`):

| fn | what it does |
|---|---|
| 0 | returns 32-bit value from `[channel+88]` |
| 1 | vtable+0x08 of object `[channel+40]` |
| 2 | returns 32-bit value `[[channel+40]+12]` |
| 3 | vtable+0x0C of the same object |
| 4 | create task |
| 5 | create node (asynchronous) |
| 6 | delete node |
| 7 | `0x801B4DE4` |
| 8 | returns 32-bit value (via `0x801B5258`) |
| 9 | `0x801B505C` |
| 10 | nothing, returns 0 |

**There is no power or frequency management command in this list.** Neither among
direct commands 0..10, nor among the 22 node commands, nor in the DCD family.

### 15.2. Code that could change frequency is dead in the firmware

In `ehwaomap.pdd`, PRCM handling was found (base `0x48008000` is mapped to kernel
VA `0x00FCE000`):

| address | register | what it does |
|---|---|---|
| `0x801AE714` | `CM_FCLKEN_DSP`/`CM_ICLKEN_DSP` (+0x800/+0x810) | enable/disable clocks, table of 17 resources |
| `0x801AE8B4` | `CM_IDLEST_DSP` (+0x820) | query status |
| **`0x801AE900`** | **`CM_CLKSEL_DSP` (+0x840)** | **write divider fields**: field 1 = bits 5–6 (`CLKSEL_DSP_IF`), field 3 = bits 8–12 (`CLKSEL_IVA`) |
| `0x801AE9B8` | `RM_RSTCTRL_DSP` (+0x850) | reset |

Calls exist only to `0x801AE714` and `0x801AE8B4`. **There is not a single reference to `0x801AE900` in the entire ROM** — neither `BL` nor through a pointer table (verified
by searching for the address across all modules). That is, the driver knows how to change the DSP frequency
divider, but **never** does so. This conclusively explains why no
user-space action could affect performance.

### 15.3. What the driver actually writes into `_BRIDGEINIT_DSP_FREQ`

`ehwaomap.pdd` @`0x801A7220`:

```
lookup("_BRIDGEINIT_DSP_FREQ") -> address in DSP space, <<1 into bytes
rate_hz = power.dll::ord60(1)          ; 1 = DSP clock ID
rate_khz = rate_hz / 1000
write 4 bytes to the address in DSP memory
```

`power.dll::ord60(1)` (@`0x800B1620`) computes the frequency **from the real divider
field in the PRCM register**, rather than taking it from a constant. That is, it is the true frequency, not
a declaration.

### 15.4. Where the "110 000" came from: it is CORE, not the DSP divider

> **Corrected 11.08.2026.** In the previous revision, this subsection concluded
> "DSP is clocked at CORE/6 = 110 MHz". **It is false** — refuted by direct
> reading of PRCM from the kernel (`docs/ANSWER_DSP_CLOCK.md`).

Measured on the device, DSP domain idle, 12 snapshots over 3 seconds — **one and the
same value**:

```
CM_FCLKEN_DSP @c6008800 = 00000401
CM_ICLKEN_DSP @c6008810 = 00000002
CM_IDLEST_DSP @c6008820 = 00000000
CM_CLKSEL_DSP @c6008840 = 000023c3      ; divider field [3:0] = 3
```

That is, **the DSP divider is always 3, and C55x is at the nominal 220.16 MHz all the time**.

The bimodality of the readout (§14.3) originates elsewhere in the same chain:

1. `power.dll::ord60(1)` computes `CORE / CM_CLKSEL_DSP[3:0]` — the mask in code is specifically
   `0xF` (`ands r1, r0, #15`), so the active field is `[3:0]`, not `[4:0]`;
2. `CORE = DPLL × CM_CLKSEL2_PLL[1:0]`;
3. and `CM_CLKSEL2_PLL[1:0]` **itself fluctuates between 1 and 2** under the DVFS governor.

Hence `sel2=2 → 660480/3 = 220160`, `sel2=1 → 330240/3 = 110080` — exactly our two
groups, with the same ratio, **without any change to the DSP divider**.

Independent confirmation: in the 60 MB ROM image, literal `0xC6008840` occurs
twice (both times in `power.dll`), and addresses of both setters of this register
(`0x800AC59C`, `0x801AE900`) — not once. The firmware never changes this divider;
it is configured at boot.

The caveat in §14.3 ("the value changed twofold, but throughput did not")
turned out to be correct and in itself indicated that this was not the operating frequency of the DSP.

### 15.5. Where the switch actually is — and why it is out of reach

`power.dll` is the kernel Resource Manager, and among its **named resources**
(strings in the module) is exactly what was sought:

```
SiliconPower  SdramActive  MPUActive  DSPIpiClk  LcdActive
HighPerf      DSPDomainOn  GFXDomainOn  PreventRetention  AllowArmIdleOnly
```

plus classes `DHighPerfResource`, `MHighPerformanceResource`,
`MDSPDomainOnResource`, `DOmap24xxPowerController`. It is specifically to this `HighPerf`
that the semaphore `KIVAHighPerfSem` in the PDD refers.

However, this is a **kernel** interface: no ioctl of the `Hwa` channel (§15.1) and no
user-space server (§14.1) leads to it. It cannot be called from an application.

### 15.6. How to raise DSP frequency: DPLL multiplier only

> **Corrected 11.08.2026.** Previously, it was recommended here to try the DSP divider
> first. Both variants have been verified on hardware, and **the recommendation has flipped to
> the opposite**.

| C55x frequency | origin | status |
|---|---|---|
| 220.16 MHz | stock (divider 3) | — |
| **284.16 MHz** | `mult 111` | **works daily, including audio** |
| 330.24 MHz | divider 2 | **crashes the device** on any DSP work |

**The divider is unusable because it is too coarse.** It is an integer, so from the stock 3,
the only step up is straight to 2, i.e. +50%, and silicon does not tolerate 330 MHz. Writing
the divider at runtime succeeds (stock setter in `power.dll` + locking
`PRCM_CLKCFG_CTRL`), and while nothing is executing on C55x, the domain stays alive as long
as desired. But as soon as the DSP is brought up — by our `dsptest` or by stock audio — the device
crashes. Downward (4/6/8 → 165/110/82 MHz), the divider is safe by design and can
be useful for power saving.

**The DPLL multiplier has been verified and gives +29% safely.** `patcher hold 111` from
SymbianOverclock: DPLL 426.24 → CORE 852.5 → DSP = CORE/3 = 284.16 MHz.
**Nothing needs to be changed in our code.**

Measured with the same node and the same binaries, 3 runs per point,
summary is the minimum of the series:

| CORE | DSP frequency | time, µs | spread |
|---|---|---|---|
| `mult 86` (stock) | 220.16 MHz | **1 136 260** | 5% |
| `mult 111` | 284.16 MHz | **882 995** | 15% |

Speedup of **28.7%** versus the purely clock-based expectation of **29.1%** — a match within
a quarter of a percent. From this follow two things, more important than the +29% itself:

1. **Benchmark time is almost entirely determined by execution on the DSP.** If a significant
   share consisted of fixed overhead (node creation, ARM side), the speedup would
   be noticeably smaller than the clock ratio. The differential method of §8 works correctly.
2. **There is no hidden "performance mode".** The machine responds exactly to
   the frequency that was set; a policy that nobody requested would not scale
   linearly with CORE.

### 15.7. DVFS governor: confirmed by measurement

**Hypothesis.** `DSP = CORE/3`, and CORE fluctuates twofold under the governor (§15.4). During
the DSP benchmark, the main ARM thread waits in `User::After` for the `create`
status — to the governor, this **looks like idle**, even though the C55x is computing
at this time. If OPP drops, the DSP falls together with CORE.

**Instrument.** In `dsptest.cpp`, a monitor thread (`ArmMonThread`) was added that measures
the ARM frequency using the same `SpinNop` that measures CPU at startup. MPU is also
clocked from CORE, so the dip is directly visible. Two command line modes:

- `armwatch` — short bursts with 200 ms pauses (~8% load): **observe**
  the frequency while barely altering conditions;
- `armbusy` — spin continuously: **cancel** idle.

The monitor starts before `ct0` and stops after `ct1`, thus covering exactly the
window in which C55x is working. Flags are passed via `tools\sweep.ps1 -Extra`.

**What was measured** (Q15 dot, 20 000 repetitions, 3 runs, summary — minimum):

| mode | ARM frequency in window | create time | spread |
|---|---|---|---|
| idle (as before) | — | 320 159 µs | 41% |
| `armwatch` | **296 → 163 MHz** | 314 697 µs | 1% |
| `armbusy` | 295, then 17 measurements 325–328 MHz | **259 613 µs** | 0% |

The drop is directly visible: in observation mode, the second measurement already yields **163 MHz**,
that is, exactly half of the nominal 330. Under continuous load, ARM
holds at 328 MHz, and DSP time drops by **18.9%**, while the spread disappears completely.

**Conclusion: the governor is a real contributor, worth ~19% of the time.** It also
explains the monotonic decline of estimates with increasing work volume (88.1 → 68.2 →
55.6 MMAC/s), which §4 attributed to preemption by the audio stack: the longer DSP computes
in isolation, the larger fraction of the window the governor keeps in low OPP.

**Practical rule: run any measurement on DSP with `armbusy`.** This not only
accelerates — it eliminates spread (41% → 0%), that is, it makes the measurement point valid.

### 15.8. What a cycle actually costs: the proper control

The previous control (§8 of `CHARACTERIZATION.md`, "memory is not the bottleneck")
**is invalid**, as seen from the generated assembly. `dsp_reg_mac` does not
compile into a MAC at all: with constant `y` and `x++`, the compiler folds
`(long)x * (long)y` into a chain of additions, and unrolls the outer loop of repetitions
twofold:

```
$C$L16:
    ADD AC0, AC2        ; repeat 1 accumulator
    ADD AC0, AC1        ; repeat 2 accumulator
    ADD #5, AC0
```

That is, **one `MACM` from memory** was being compared against **three ALU instructions in
registers**. Identical execution time meant not "memory is free", but mutual
masking of two different effects.

The proper way is to count **cycles**, not operations, and take them from assembly:

- `dsp_q15_dot`: `RPT CSR` + one `MACM *AR1+, *AR0+, AC0, AC0` → exactly
  1024 instructions per repeat;
- `dsp_reg_mac`: 3 slots × 1024 for **two** repeats → exactly 1536 per repeat.

Measurement by slope (several points across repetitions, all under `armbusy`, minimum of 3
runs):

| kernel | points (repeats) | slope | cycles per instruction at 220.16 MHz |
|---|---|---|---|
| `dsp_reg_mac` (registers) | 10k / 40k / 60k | 7.36 µs/repeat | **1.05** |
| `dsp_q15_dot` (memory) | 20k / 40k / 60k | 9.15 µs/repeat | **1.97** |

**Two conclusions.**

1. **C55x indeed delivers one instruction per cycle at 220 MHz.** The register kernel yields
   1.05 cycles per instruction — that is, neither hidden throttling nor an underclocked
   frequency exists. This conclusively settles the "real frequency ~60 MHz" version.
2. **`MACM` with two operands from memory costs exactly double — ~2 cycles.** Here
   is where the remainder of the deficit lies.

**Instruction fetch has nothing to do with it** (the hypothesis of §10 is refuted twice): the inner
loop of `dsp_q15_dot` is `RPT`, the instruction is fetched once and repeated
in hardware, there is nothing to fetch; while the register kernel in `RPTBLOCAL` reaches 1 cycle per
instruction, so there is no fetch penalty there either.

**Same address has nothing to do with it.** `dsp_q15_dot(gBuf, gBuf, N)` reads the same
array with two pointers. Tested with the `W_DOT2` (12) workload — the same
code, but with two different arrays:

| kernel | 40 000 repeats |
|---|---|
| `W_DOT16`, one array | 435 577 µs |
| `W_DOT2`, two arrays | 436 584 µs |

There is no difference. **However, this experiment does not prove that memory is not the cause:** `gBuf` and
`gBuf2` lie side-by-side in the same `.bss`, that is, in the same block. It rules out
a conflict of identical **address**, not a **block** conflict. What exactly causes these 2 cycles —
in §15.9.

### 15.9. Where node data resides: segment table from the base image

Where the loader places node sections is determined not by `.lcf`, but by the dynamic
segment table **in the base image itself** plus fields 30/31 of the DCD entry.

The table resides in `baseimage.dof`, section `.dspbridge_mem` (symbols
`DYNM_0`..`DYNM_3`): count word, followed by four entries
`{segid, base, length, flags}`. Decoded:

| segid | name | base | length |
|---|---|---|---|
| 0 | `DYN_DARAM` | `0x007f00` | **256 words** |
| 1 | `DYN_SARAM` | `0x008008` | 4381 words |
| 2 | `DYN_EXTERNAL` | `0x0b0000` | 458 752 words |
| 3 | `DYN_SRAM` | `0x068000` | 98 304 words |

The names match the driver trace strings (`DYN_DARAM`, `DYN_SARAM`,
`DYN_EXTERNAL`, `DYN_SRAM` in `ehwaomap.pdd`), and the order matches segid.

**The low byte of field 30 (data) and field 31 (code) is segid.** All Nokia nodes and
all TI samples set `0` for data, and `2` (Nokia) or `1` (TI) for code.

**This explains the project's long-standing crash.** When `.bss` grew to ~5120 words (all three
arrays declared simultaneously), node creation began returning `-2` without diagnostics,
and the cause could not be found back then — "the real limit is somewhere in the node's memory
allocation". Now it has a number: **4381 words**, the length of `DYN_SARAM`. 5120 does not fit
even there. The discipline of "keeping `.bss` minimal" was correct, but now it
has a number.

**Attempt to place data in DARAM.** DARAM is dual-ported (two accesses per cycle),
SARAM is single-ported — that is exactly the factor of two we measure. `BENCH_CREATE_N` is made
a build parameter (`tools\build_dsp_node.cmd` arg 4), data segid is arg 5.
At `N=200`, section `.bss` comes out to 0x194 bytes = **202 words**, meaning it
fits into the 256-word DARAM heap.

Result — **no effect**:

| configuration | repeats | time | cycles per MACM |
|---|---|---|---|
| `N=1024`, segid 0 | 40 000 / 60 000 (slope) | 9.149 µs/repeat | 1.97 |
| `N=200`, segid 0 | 200 000 | 439 544 µs | — |

The two points with different `N` are solved together: `1024c + O = 2014` and
`200c + O = 484` yield **c = 1.86 cycles per MACM, O = 113 overhead cycles per
repeat**. That is, the access cost is the same, `N` does not affect it.

**All four segments measured.** The build is the same (`W_DOT16`, `N=200`, 40 000
repeats, `armbusy`, minimum of 3 runs), the difference is exactly one DCD byte:

| segid | segment | time |
|---|---|---|
| 0 | `DYN_DARAM` (request) | 121 673 µs |
| 1 | `DYN_SARAM` | 129 669 µs |
| 2 | `DYN_EXTERNAL` | **502 685 µs** |
| 3 | `DYN_SRAM` | **69 671 µs** |

The field **works**: external memory slows down fourfold, SRAM speeds up almost
twofold. But "speeds up" here is deceptive, and here is why.

**SRAM gain is fixed, not per cycle.** The second pair of points on production
`N=1024`: segid 0 → 435 577 µs, segid 3 → 376 647 µs. We solve both pairs
together, subtracting by `N` (this eliminates both node loading and call
overhead):

| segment | cycles per `MACM` |
|---|---|
| segid 0 | 2.10 |
| segid 3 | 2.05 |
| segid 2 | ~11 |

That is, **between DARAM/SARAM/SRAM access costs are identical**, and the entire difference in time
comes down to a constant ~50 ms for node creation (identical at `N=200` and `N=1024`,
which proves: this is not computation). The practical consequence for benchmark numbers is
**zero**, because the differential method cancels this constant anyway. The only thing of real
significance: **avoid external memory**, it costs ~11 cycles per access
versus 2.

**Why DARAM is unreachable.** The `DYN_DARAM` heap is 256 words, and from that same data
segment the node stacks are also allocated: DCD fields 16/17 give `0x200` + `0x100` =
**768 words**. That is, they alone are already three times larger than the entire heap, and `.bss` cannot
be placed there, no matter how much you reduce `N`. This is consistent with measurement: segid 0 and segid 1
are indistinguishable (121 673 versus 129 669 at 15% spread; on the `W_DOT2` pair,
`N=100` — 65 643 versus 64 666), meaning the DARAM request silently falls back to SARAM.

**What remained untested.** The only way to actually get into DARAM is to reduce
fields 16/17 so that the stacks plus `.bss` fit into 256 words (e.g. `0x60`/
`0x30` = 144 words of stack with `W_DOT2` at `N=32` = 66 words). If after this
segid 0 becomes noticeably faster than segid 1 — the dual-ported nature of DARAM yields those same 2
cycles → 1, that is, ×2 on all memory-bound kernels. The risk is real, not in hardware, but
in time: a stack that is too small crashes the phase, while a failed node creation hits the ARM
wait ceiling (~150 s per run) and blocks the deployment daemon.
