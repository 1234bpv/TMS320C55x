# TMS320C55x vs. ARM1136 benchmark on Nokia N95 8GB — report

Goal: execute custom code on **TMS320C55x** inside **OMAP2420** under
Symbian and measure its performance against **ARM1136**.

This is a status report as of 2026-08-10. Facts are in `findings.md` (each with a source:
confirmed on device, deduced from ROM code, or marked as a hypothesis).

---

## 0. RESULT

Q15 dot-product, `n = 1024`, the same source code on both sides, measurements in
a single device boot:

| | MMAC/s | MAC/cycle |
|---|---|---|
| **ARM1136** @324 MHz (measured) | 32.3 | 0.099 |
| **TMS320C55x** @220 MHz (nominal) | 55.6 – 88.1 | 0.253 – 0.400 |

> **C55x is faster by approximately 1.7–2.7 times in absolute performance
> and by 2.6–4.0 times per cycle.**

The range, rather than a single number, is intentional: estimates monotonically decrease with
increasing workload (88 → 68 → 56 MMAC/s), because the longer the DSP computes, the
more it is preempted by the audio stack that owns it. Details and caveats —
`findings.md` §20.

## 1. Summary in one paragraph

The ARM side of the benchmark is ready and measured on device. The C55x node builds from
custom code into a loadable DOFF and structurally does not differ from
Nokia production nodes. The bridge to the DSP is completely reversed — from 39 C++ ordinals
to four families of kernel commands — and on the live device **our
custom node has been registered and a task created for it on the C55x**. The last
link has not been closed: node execution and message passing. Because of this, the final
"DSP vs ARM" number does not exist yet.

## 2. What works on device

```
ord32 Open(proc=0 DSP, flag=0, NULL) -> 0     channel handle 0x00030002
ord9  bind(A, C)                     -> 0
ord26 Load(Z:\resource\plugins\baseimage.dof) -> 0
ord6(A, UUID of node from base)      -> 0
ord4(A, &ref)                        -> 0     ref = 0x007003B0
DoControl(channel, fn=4, TBuf8<20>, &out) -> 0  taskHandle = 0x00008000
ord10/ord33 close                             device alive
```

Each step was a prediction from the disassembler that came true. In particular,
`ord4(A, NULL)` returned exactly `-6 KErrArgument`, just as it was supposed to from the code.

**ARM baseline** (Q15, identical data from deterministic LCG):

| kernel | time | MMAC/s | MAC/cycle |
|---|---|---|---|
| DOT (8192×2000) | 508 ms | 32.2 | 0.098 |
| FIR (4096×32×200) | 990 ms | 26.5 | 0.080 |
| BLK (8192×2000) | 648 ms | 25.3 | 0.077 |

## 3. Main technical findings

**The entire dspbridge lives in the kernel.** `bridgeapi.dll` is only a C++ facade; the DOFF loader,
DSP MMU, RMS protocol, and mailbox are in `ehwaomap.pdd` (110 KB) behind the LDD **`Hwa`**
(not `D32HWA` — that is an internal string). The **MultimediaDD** capability is required.

**39 ordinals = three classes**, derived from the structure of aliased pairs `C1/C2`+`D1/D2`
and confirmed twice independently (from constructors and from the `CBal` layout):
A (1–14, UUID/DCD, 8 B), B (15–24, task/node, 16 B), C (25–39,
processor/channel, 20 B).

**Complete kernel surface:** `fn 0..10` (channel; `fn 4` = task creation),
24 device commands `0x0400_00NN`, 18 live task commands `0x0800_00NN`,
family `0x0C00_00NN`.

**DCD and DOFF format decoded** from nodes in ROM: 31 fields of node record,
two registration sections, DOFF header with checksum rule
checksum = ~(sum of 8 previous words) — verified on four files.

## 4. Our node on the DSP

`ord26` (`PROC_Load`) panics the kernel on any non-executable DOFF — both on
our node and on the stock `pingdyn.dll55l`. Bypassed by **direct call
to the parser** `0x80A5F0D4`: it populates the user-side DCD, while the fatal image
loading is performed separately, later in `ord26`.

Next, it turned out that `ord6` does not see a **dynamic** node without entries
for phase libraries (DCD types 3/4/5). In ROM, nobody declares them — there they are synthesized
by `ord26` itself. We declared them explicitly in our own `.dcd_register`, and the node
was found.

```
parse(loader, "E:/bench.dll55l") -> 0
ord7(A, our UUID, args)           -> 0
ord4(A, &ref)                     -> 0
DoControl(fn=4, {0,0,ref,0,0})    -> 0   taskHandle 0x8000
```

That this is indeed our node is evident from the structure behind `ref`: it contains
`BENCH_DSP_create/execute/delete`. Task commands return addresses in DSP space
(`0x300000xx`), meaning memory for the node has been allocated.

The missing link was a separate asynchronous step `fn=5` (node creation) — I
had called it earlier and saw `0`, but did not wait for the status, so I considered it useless.
With proper waiting:

```
DoControl(5) node-create -> 0, status 0   *** NODE CREATED ON THE C55x ***
node fn 7 -> 0, status 0                  (before creation: -18)
node fn 8 -> 0, status 0                  (before creation: -2)
```

That is, the kernel loaded our `bench.dll55l` onto the DSP, the dynamic loader resolved
external symbols against the base image, and RMS invoked our phase
**`BENCH_DSP_create()` on the C55x**.

**Four independent proofs that this is indeed our node:** successful `node-create`;
the names `BENCH_DSP_create/execute/delete` in the node structure; allocated
addresses in DSP space for it (`0x300000xx`); and the fact that operations on the node changed
their result from error to success right after its creation.

**Data path.** The message queue turned out to be a dead end: ordinals 15–18
(`0x0C000001/2`) are not used by any module in ROM, and invoking them panics the kernel.
Therefore, the measurement was designed differently — **the work runs inside the `create` phase, while
time is measured on the ARM**; fixed overhead is cancelled out by the difference of two runs
with different iteration counts. The numbers are in Section 0.

## 5. Incidentally fixed

- **The ARM side never built:** a space in the path broke `abld`→`makmake`
  (passed without quotes). Fixed by a junction without spaces, which is now
  created outside the project tree and removed after the build.
- **The benchmark was mismatched:** the ARM computed in 64 bits versus 32 on the DSP.
  Fixed; equivalence is proven by unchanged checksums.
- **`build.cmd` deployed a stale binary:** `ABLD.BAT` returns 0 even when
  `make` fails. Now the target is deleted before building.
- **Two of the three ARM kernels measure memory rather than the core** (DOT and BLK stream-
  read 16 KB each — larger than L1D). Therefore, ARM and DSP numbers must be captured in
  the same run; between reboots they vary by one and a half times at the same
  core frequency.

## 6. Methodological lessons (bought with mistakes)

- **The unit of observation is the complete device boot, not a run.** Three times I
  declared a suspect innocent based on too short a window.
- **Do not construct causality on the timing of human messages.** The model
  of "deferred reboot" was invented in exactly this way and turned out to be false.
- **A function's length cannot be inferred from the distance to the next ordinal** —
  that is how `TLex` from an adjacent unexported function ended up in the description of `ord4`.
- **A control must be chosen by a proven property.** The first control on
  the PING node UUID proved nothing: PING was not registered. The correct one
  turned out to be the UUID that the base itself registers.
- **A sign of a real run** — lines "OK <bytes>" from PUT and a fresh `cmdline`
  in the first line of the log. Without them, a crash pertains to the state of the device *before* the command.

## 7. Safety

Nothing in flash; everything is runtime; reboot restores the device to its previous state. Audio was not
reclaimed — Path A was chosen. Reboots occurred only on one specific
call (`ord26` on a node), and a safe alternative was found for it: keep
the file open exclusively, in which case `-14` is returned instead of a crash.
