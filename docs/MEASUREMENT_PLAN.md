# C55x characterization plan and work status

Date: 2026-08-10. Project goal (execute custom code on C55x and measure against
ARM1136) **achieved** — result in `WRITEUP.md` section 0 and `findings.md` §20.
This file describes **next stage**: broader characterization of DSP for practical
use in applications, and preserves all context needed to
continue work from scratch.

---

## 1. What was requested at this stage

1. **Degradation on long tasks** — 1 min versus 2 min; whether performance drops and
   how stably code executes.
2. **fp32 / int32 in software emulation** — C55x has neither FPU nor fast
   32×32; the cost must be known.
3. **Code with conditional branches** — workload close to applications
   (messengers, etc.), versus the same code on ARM.
4. **Communication cost** — time to transmit task and receive result,
   exchange rate ARM↔DSP.
5. **Summary guide** — extraction of meaningful results for writing
   reliable code for DSP in other projects, with numbers.

---

## 2. Main constraint: how to measure at all

State of August experiments (findings §20.1); this is not a final conclusion
about channel availability:

- old message calls (ordinals 15–18 `bridgeapi`, ioctl
  `0x0C000001/2`) caused crashes with arguments of that time. Conclusion
  "dead code" refuted as excessive: driver lifecycle uses
  MSG, exact task20/21 ABI is analyzed. In September STRM already transmitted many
  packets; DSP NODE_getMsg(0)/NODE_putMsg(0) returned 0/1. Delivery from
  shared message window to ARM and RUN completion do not work yet;
- value returned from `create` phase **does not reach** ARM (verified:
  returned `0x1234`, status is still `0`).

**Working channel:** work runs **inside `create` phase**, and time
is measured on ARM around `DoControl(5)` (node creation is synchronous). Fixed
overhead is cancelled out by **difference of two runs** with different number of repetitions.

Consequences that determine the entire measurement design:
- parameters are passed into the node only **at build stage** (`-D`), because arguments
  in `create` do not exist;
- **one measurement = one run** (node is created once per run);
- interference can only slow down, so for each point **minimum of the
  series** (best-of-N) is taken, same as on ARM side.

---

## 3. fp32/int32: subroutines ARE in the base image

> Initially I wrote the opposite ("there is no floating point in base, must link
> `rts55.lib`"). This was **wrong** — I searched for names `_addf/_mpyf`, whereas
> on C55x `double` equals 32 bits, and TI names these subroutines with suffix
> `d`. Corrected after repeated check of `docs/base_syms.txt`.

Base image (`baseimage.dof`, 1678 symbols — full list preserved in
`docs/base_syms.txt`) **exports**:

- **floating point (32-bit, because on C55x `float` == `double` == 32 bits):**
  `_addd` `_subd` `_mpyd` `_divd` `_negd` `_cmpd`
  + conversions `_fixdi` `_fixdli` `_fixdul` `_fltid` `_fltlid` `_fltuld`;
- **long/integer arithmetic:**
  `_mpyli` `_mpylli` `_divi` `_divli` `_divlli` `_divu` `_divul` `_divull`
  `_remi` `_remli` `_remlli`.

That is, `rts55.lib` **does not need** to be linked — the node can remain thin, and
subroutines will be resolved by loader against base, like `_NODE_getMsg` and `_CLK_gethtime`.

⚠️ **Rule mandatory before every run** (lesson §15.3 about `BCACHE_*`,
which almost made node unloadable): look in `DLLdump` at list of
`UNDEFINED EXTERNAL SYMBOL` and verify that **every** one of them is present in
`docs/base_syms.txt`. Currently there are five — `_NODE_getMsg`, `_NODE_putMsg`,
`_CLK_gethtime`, `_CLK_countspms`, `_c_int00`; new workloads will add
arithmetic ones. Any symbol absent in base = node will not load.

This is in itself a meaningful result for the guide: **set of what DSP code
can use "for free" is defined by symbol table of base image
of specific firmware** — and it must be verified, not assumed.

---

## 3a. CRITICAL: DSP wedges, and this cannot be cured without reboot

Caught during the first matrix run. Sequence of events:

1. fp32 and branch with `reps=1000` turned out much slower than Q15, and
   ARM side stopped waiting earlier than `create` completed
   (`status: -2147483647` = `KRequestPending`);
2. **after these two runs node creation stably started returning `-2`** —
   permanently, for any build;
3. roll-back of the node to binary that previously worked **did not help**. Thus reason
   is not in node code, but in DSP state.

**Two conclusions, both go into the guide:**

- **Phase that does not return in time hangs DSP until reboot.** No
  diagnostics is provided: subsequent `create` simply return `-2`, while all
  preceding steps (DCD parsing, `ord7`, `fn=4`) report success.
- **`fn=6` is NODE DELETION, not "launch"** (correction of previous
  error in §19: `bal` @`0x80A41F4C` calls specifically it to terminate task in
  error handling path). That is, in working runs the node was indeed deleted. But
  when `create` does not return, there is nothing to delete — and precisely such "hung"
  node remains on DSP permanently.

### Clarification after full measurement cycle (10.08.2026)

Model above was **incomplete**. Observed in working runs:

- `create` that returned **`-2` does NOT wedge device**: after failure at 1.4 s
  next run with `reps=0` completed normally (verified twice).
- Wedging is caused by **accumulation** of failures: after series of ~6 consecutive `-2` (fp32) next
  creation began failing already on `DoControl(4)` — that is, not even task
  is created, `taskHandle=0`. This is another, deeper symptom than `-2` from `fn=5`.
- Wedging is also caused by **abandoned wait**: if ARM stops waiting while phase is still
  executing, the node remains hung permanently.

That is, signs of degradation, in increasing severity:
`fn=5 -> -2` (harmless) → `fn=4 -> -2` (wedged, reboot only).

### C55x type trap that cost half a day

`int` on C55x is **16-bit**. The loop `for (int i = 0; i < 100000; i++)` does not
ever terminate: `i` reaches 32767, overflows and spins forever.
This looked like "DSP hangs on long tasks" — in reality the node was properly
executing infinite loop, while ARM was counting its wait ceiling.
Repetition counters — **only `long`**.

**Rules that follow from this:**

1. Bound work in phase so that it is guaranteed to fit in seconds;
   select number of repetitions **based on measured workload speed**, not
   at random (int32 ≈ 1.2 MMAC/s, that is ~50 times slower than Q15 — and
   `reps` suitable for Q15 is catastrophic for it).
2. Wait ceiling on ARM must be **knowingly greater** than longest
   workload. `User::After(10000)` gives not 10 ms, but ~15.6 ms — granularity
   of nanokernel tick; 300 iterations gave exactly 4.7 s and looked like a "result".
3. Measurement point is valid **only** if `node-create status == 0`. Time without
   status check can measure own timeout (which is exactly what happened).
4. Node deletion — DoControl(channel, fn=6, taskHandle, &status) + wait
   (form with `bal`). Call **always**, including in error paths.

## 4. Workload matrix

Each is a separate `-D` during node build, and **mirrored implementation on ARM** in
`src/dsptest.cpp` for fair comparison (the same source code where
possible).

| Code | Workload | What it shows |
|---|---|---|
| `W_DOT16` | Q15 dot-product, `n=1024` (already exists) | Reference point, dual-MAC |
| `W_INT32` | `acc += (long)a[i]*(long)b[i]` 32×32 | Cost of long arithmetic |
| `W_FP32` | `facc += fa[i]*fb[i]` | Cost of software float emulation |
| `W_BRANCH` | Finite state machine/byte parser with data-dependent branches | Code "like in application" |
| `W_NONE` | Nothing (buffer initialization only) | Baseline overhead |

For duration: same `W_DOT16` with `BENCH_CREATE_REPS`, chosen for
≈10 s / 60 s / 120 s, 3–4 runs per point.

---

## 5. Run procedure (verified)

```
tools\build_dsp_node.cmd <REPS>     # first argument -> -DBENCH_CREATE_REPS
tools\build.cmd run <ip> baseonlydcdopnobench
```

Flags of `dsptest.exe`: `baseonly` + `dcdop` enable branch where
DCD parsing, node creation and measurement occur; `nobench` disables ARM benchmark.
Flags are recognized by **substring**, so they merge into a single token.

Sign that run actually occurred: lines OK <bytes> from PUT **and** fresh
`cmdline` in the first log line. `UPTIME:` on the first line distinguishes kernel reboot
from shell restart.

For series without rebuild — run the same binary multiple times:
```
deploy_net.ps1 -Ip <ip> -Cycle -Run "E:\sys\bin\dsptest.exe baseonlydcdopnobench" `
               -GetFile "E:\dsptest.log" -OutFile out\repN.log
```

---

## 6. Run safety (bought with reboots)

- **`ord26` on node crashes device** — both on ours and on stock `pingdyn`.
  Bypassed by direct call to parser `0x80A5F0D5` (see §19.1). If `ord26` 
  is really needed — keep file open exclusively, then `-14` instead of reboot.
- **Do not call task command `fn 18`** — crashes device. `fn 0..17` verified.
- **Do not probe task family blindly**; DCD family (`0x0400001E`+op) is safe.
- **Never do `User::LoadLogicalDevice("ehwa.ldd")`**.
- Pass **`TBuf8`, not `TPtr8`** to kernel — it performs raw reading
  of fixed size from pointer.
- Asynchronous operations (`fn 5`, `fn 6`, `fn 7`, `fn 8`) **mandatorily** with
  status waiting; `TRequestStatus` — **static**, otherwise driver writes into
  destroyed stack frame.

---

## 7. What has already been measured (not to remeasure)

ARM1136 @324 MHz, in one boot, best-of-3:

| Kernel | Time | MMAC/s | MAC/cycle | Working set |
|---|---|---|---|---|
| DOT | 52124 us | 31.43 | 0.097 | 32 KB |
| DOT-S | 50750 us | 32.28 | 0.099 | 4 KB |
| FIR | 99945 us | 26.22 | 0.080 | 8 KB |
| BLK | 65826 us | 24.88 | 0.076 | 16 KB |

C55x, `create` channel, minimums from series of 4:

| Repetitions × 1024 MAC | Minimum time |
|---|---|
| 0 | 7 934 us |
| 10000 | 124 176 us |
| 20000 | 308 197 us |

Derived estimates: 88.1 / 68.2 / 55.6 MMAC/s (decrease with growing volume —
preemption by audio stack). Summary: **C55x faster ~1.7–2.7 times absolutely,
~2.6–4.0 times per cycle**; DSP frequency not measured, nominal 220 MHz taken.

Raw logs of series — `out/base*.log`, `out/rep*.log`, `out/w20_*.log`.

---

## 8. Order of work

1. Add `rts55.lib` to node link; check list of undefined symbols.
2. Implement `W_INT32`, `W_FP32`, `W_BRANCH` on DSP and mirrors on ARM.
3. Run matrix (each point is a series, take minimum).
4. Duration: `W_DOT16` at ≈10 s / 60 s / 120 s, assess degradation and spread.
5. Communication: base `create` (7.9 ms) = cost of launching work on DSP;
   separately measure `DoControl(fn=3)` time (reading 268 B from kernel) as lower bound
   of call cost. In August prototype message cost is not
   measured; its further verification depends on ARM delivery and standard
   completion. Current plan and evidence — work/PLAN.md and STREAM_RESEARCH.md.
6. Write `docs/DSP_GUIDE.md` — guide with numbers and rules.
