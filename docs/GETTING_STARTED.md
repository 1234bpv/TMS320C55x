# Getting started with the C55x DSP on OMAP2420 Symbian phones

This guide is for a developer who wants to run their own code on the
TMS320C55x DSP of a Nokia N95 8GB or Nokia E90, either to repeat the
measurements of this project or to use the DSP in an application. It collects
what the research established and points to the report where each fact is
proven. Where this guide and a dated report disagree, the dated report holds
the evidence; please report the difference.

Everything here was verified on two phones and two firmware versions only.
Nothing is known about other firmware, and the host program refuses to run on
it.

## 1. What the project gives you

- A build chain for C55x **dynamic nodes** (`.dll55l`, TI DOFF format) that
  runs natively on Windows, and for the ARM host program (`c55stream.exe`).
- The **ARM-side contract of the Symbian DSP bridge**: the 39 ordinals of
  `bridgeapi.dll`, the kernel channel `Hwa` (`ehwa.ldd` + `ehwaomap.pdd`) and
  its control codes, the stream packet layout and the shared memory mapping
  calls. See [findings.md](findings.md) §16–§19 and
  [STREAM_RESEARCH.md](STREAM_RESEARCH.md).
- **Working node sources**: a create-phase benchmark node
  (`src/dsp/bench_node.c`) and a stream node with many variants
  (`src/dsp/stream_node.c`), including a worker task, a ring exchange and
  exact ports of three emulator kernels.
- **Measured costs** of every step, with the journals they come from, and an
  offline verifier for the published evidence.

## 2. Decide first whether the DSP is worth it

The C55x wins only on 16-bit fixed-point multiply-accumulate over a stream of
data. Measured on the N95 ([DSP_GUIDE.md](DSP_GUIDE.md) §1):

| Workload | C55x | ARM1136 | Verdict |
|---|---|---|---|
| Q15 multiply-accumulate | 54–93 MMAC/s | 32 MMAC/s | DSP 1.7–2.9 times faster |
| 32-bit integer arithmetic | 1.5 (4.1 by hand) MMAC/s | 23 MMAC/s | ARM 5.6 times faster |
| branchy logic | 9.0 Melem/s | 9.6 Melem/s | parity, not worth it |
| emulated fp32 | 0.066 (0.15 by hand) MMAC/s | 4.9 MMAC/s | ARM 33 times faster |
| 32/32 division | 0.41 Mdiv/s | 10.9 Mdiv/s | ARM 27 times faster |

Plan with the sustained 50 MMAC/s, not the peak. The dual MAC needs a shared
operand (FIR with two outputs, correlation, matrix-vector); the compiler never
emits it, so it is reachable only from assembler (§10 of the guide). The DSP
runs at CORE/3, 220.16 MHz at the nominal CORE clock, as read from the PRCM
registers ([ANSWER_DSP_CLOCK.md](ANSWER_DSP_CLOCK.md)); but the DVFS governor
can halve CORE while the ARM idles, which cost about 19% of DSP time in one
measurement (guide §15.7). The header of the table in §1 of the guide still
says "~60 MHz"; §10 of the same guide corrects that.

Then compare the size of your job with the fixed costs:

| Cost | Measured value | Source |
|---|---|---|
| create an empty node phase | about 9 ms | [CHARACTERIZATION.md](CHARACTERIZATION.md) |
| set up and tear down the ring channel | 0.84–0.87 s (p50, includes journaling) | [CLAUDE_PS1_HANDOFF](CLAUDE_PS1_HANDOFF_2026-10-04.md) |
| one ring exchange, synthetic packets (batch 1 / 2) | N95 1037 / 732 µs, E90 640 / 793 µs (p50) | [DMM_RING](DMM_RING_2026-10-03.md) |
| smallest emulator job through the ring (1 SPU voice) | 1617.432 µs (p50) | [N95_SPU_RING](N95_SPU_RING_2026-10-04.md) |
| 1792-byte exchange with a stream worker | 518 µs N95, 640 µs E90 (median) | [PACKET_SIZES.md](PACKET_SIZES.md) |

No break-even job size was measured. The emulator kernels, which the ARM
finishes in 4 to 340 µs, lost every one of 2520 paired measurements ([README](../README.md#emulator-workloads-stay-on-the-arm)).
The DSP pays off only for long fixed-point jobs, or when the ARM has useful
independent work to do while the DSP computes; the second case is not measured
here and the model for it is in [CLAUDE_PS1_HANDOFF](CLAUDE_PS1_HANDOFF_2026-10-04.md).

## 3. Supported phones and firmware

| Phone | Firmware | Notes |
|---|---|---|
| Nokia N95 8GB (RM-320) | V 35.0.001, MachineUid `20002D84` | main research device |
| Nokia E90 (RA-6) | 400.34.93 | verified, with the open issues listed in the README |

Before touching the bridge, the host checks the MachineUid, all 39 live exports
of `bridgeapi.dll` and the start of the internal DCD parser against the values
recorded for these firmware versions. Any difference stops it. Porting to
another OMAP2420 phone (SymbianOverclock lists the N82, the original N95, the
N93 and the N93i) means repeating that verification
against its ROM with the tools in `tools/rev/`.

## 4. What you need on the PC

The build was used on Windows 10/11. Paths are discovered relative to the
project by `tools/env.cmd`, which expects the project to sit next to the SDK and
toolchain folders:

```
<root>/S60_3rd_FP1/        Symbian S60 3rd Edition FP1 SDK
<root>/toolchain/          perl, CSL_Arm_Toolchain (GCCE 3.4.3), gcce/arm-2012.03 (GCCE 4.6.3),
                           ti/dspbridge/dsp/doffbuild (dllcreate.exe, DLLdump.exe)
<root>/TMS320C55x test/    this repository
```

- **S60 3rd Edition FP1 SDK** with the CSL GCCE 3.4.3 compiler it ships.
- **GCCE 4.6.3** (Sourcery CodeBench Lite 2012.03) for the static library with
  the MDEC kernel, built by `tools/build_mdec_kernel.cmd` to match the
  emulator's compiler.
- **Perl older than 5.22** (5.20.3 was used). The SDK's `E32Plat.pm` uses `defined(%hash)`, which is
  fatal from Perl 5.22.
- **TI C5500 Code Generation Tools 4.4.1** (`cl55`, `lnk55`, `dis55`, `ofd55`).
  They produce TI-COFF, which is what the bridge's loader expects. The path is
  found through `DSP_CGT`, `PATH` or the default install folder on any drive.
- **TI dspbridge `doffbuild`** (`dllcreate.exe`, `DLLdump.exe`), Windows PE
  binaries from the `bridge-tools.tar` archive of
  [kpykc/userspace-dspbridge](https://github.com/kpykc/userspace-dspbridge). The
  path can be overridden with `DSP_DOFFBUILD`.
- **Python 3.12** and **PowerShell 7** for the runners and verifiers.

Two build traps are handled by the scripts but are worth knowing. A space in the
project path breaks `abld`/`makmake`, so `tools\build.cmd` builds through a
junction `<SDK drive>:\symbuild\c55x`. `ABLD.BAT` returns 0 even when `make`
fails, so the script deletes the target first and treats a missing file as an
error. The old `cl55` also fails on paths with spaces, Cyrillic or 8.3 short
names. Three DOFF traps are described in [findings.md](findings.md) §15.5:
`dllcreate -e` localizes the node's own phase symbols, `.s55` files must go
through `cl55` rather than `asm55` to get the large memory model, and DOFF
metasections such as `.dcd_register` must be `type = COPY` in the linker
command file.

## 5. What you need on the phone

- A phone that installs self-signed packages with the capabilities
  `PowerMgmt WriteDeviceData ReadDeviceData ReadUserData WriteUserData ProtServ
  MultimediaDD` (see `group/c55stream.mmp`). In practice that means a hacked
  phone (an install-server patch). **MultimediaDD** is the one the bridge driver
  checks: without it the `Hwa` channel does not open.
- A way to copy files, start processes and fetch journals. The project used
  SymbianDeployDaemon over Wi-Fi (TCP port 2323) or Bluetooth; the runners in
  `tools/` speak its protocol. That daemon is a separate project and is not
  published at the time of writing, so device runs cannot be reproduced from
  this repository alone.
- Some diagnostic modes and the clock guard use the kernel patcher of `ocprobe`
  from [SymbianOverclock](https://github.com/1234bpv/SymbianOverclock).

## 6. Building

From the project root in PowerShell 7. Every command runs under an explicit
time limit through `tools/run_bounded.ps1`; a build that does not finish is a
failure, not a pause.

```powershell
pwsh -NoProfile -File tools/check_state.ps1
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/arm-build.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_dsp_node.cmd' -TimeoutSec 120 -Log out/dsp-build.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_stream_node.cmd' -TimeoutSec 120 -Log out/stream-dsp-build.log
pwsh -NoProfile -File tools/check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

| Script | Output |
|---|---|
| `tools\build.cmd` | `out/arm/dsptest.exe`, `out/arm/c55stream.exe` |
| `tools\build_dsp_node.cmd` | `out/dsp/bench.dll55l`, the August benchmark node |
| `tools\build_stream_node.cmd [variant]` | `out/dsp/c55stream*.dll55l`, the stream node or one of its variants |
| `tools\build_mdec_kernel.cmd` | the C55x and ARM MDEC kernels and `c55xmdec463research.lib` |
| `tools\build_stream_sis.ps1 -Revision N` | a SIS package with the host, for phones where `sys\bin` cannot be written directly |

Each stream-node variant also overwrites the main DLL in `out/dsp`, so build the
plain node again afterwards. The variants are listed in [BUILD.md](BUILD.md).

The DSP chain is `cl55 -c` → `lnk55 -r` → `dllcreate`. After every build, check
the node with `DLLdump` and compare every `UNDEFINED EXTERNAL SYMBOL` with the
symbol table of the phone's base image in [base_syms.txt](base_syms.txt): a
dynamic node is not linked with `rts55.lib`, its imports are resolved against
the firmware's `baseimage.dof`, and a missing symbol means the node will not
load.

## 7. Safety rules

These rules were paid for with reboots. Breaking them does not return an error;
it restarts the phone at once. The project never writes the firmware image,
and in its experience a restart returned the phone to its normal state; files
that the tools copied or replaced stay on the phone until they are restored.

- **Never call `User::LoadLogicalDevice("ehwa.ldd")`.** The driver is already
  loaded.
- **Never call `bridgeapi` ordinal 26 (`PROC_Load`) on a node**, ours or Nokia's.
  Load nodes as phase libraries; the project calls the DCD parser directly
  instead ([findings.md](findings.md) §18–§19). If ordinal 26 is unavoidable,
  hold the file open exclusively, and it returns `-14` instead of rebooting.
- **Do not call task commands `fn 18` and above.** `fn 0..17` were checked.
- Pass the kernel a **`TBuf8`, not a `TPtr8`**: the driver reads a fixed-size raw
  record from the pointer. Raw allocation records are 32 bytes on both firmware
  versions; the SDK's `TBuf8<20>` gives only 28.
- Asynchronous operations (`fn 5..8`) must wait for their status, and the
  `TRequestStatus` must be **static**, or the driver writes into a dead stack
  frame.
- **`fn=6` deletes the node.** Call it on every path, including errors.
- **Integer overflow kills the node phase** on the C55x, and the ARM sees only a
  bare `-2`. Estimate the maximum of every accumulator before writing the loop.
  When you see `-2`, suspect your arithmetic before the platform.
- Keep the node's `.bss` under **4381 words**, the length of the `DYN_SARAM`
  segment of the base image. Above it, node creation fails with `-2` and no
  diagnostics.
- Do not abandon a wait while a phase is still running. Accumulated failures
  and abandoned waits jam the DSP: `fn=4` returning `-2` with `taskHandle=0`
  means only a reboot will help.
- The DSP belongs to the phone's audio stack. Our nodes run beside it through
  the bridge; taking the DSP away from it (the "path B" of the research plan)
  is expected to kill sound until the next reboot. This was planned as a risk,
  not observed.
- When the ownership of a pending transfer or a failed delete is uncertain,
  leave the process alone. The host then enters a quarantine state and keeps
  the process and its resources instead of killing it, because a kill would
  leave the ownership of that memory unknown.

The host and runners add guards of their own: an explicit IP and device name,
a check of the phone model, a fresh preparation record no older than 10
minutes, backup and byte-exact restore of every replaced phone file, and a time
limit on every command. A timeout is never counted as a success.

## 8. Three ways to run code on the DSP

| Model | How it works | Status | Read |
|---|---|---|---|
| **Work in the create phase** | The computation runs inside the node's `create` phase; the ARM times `DoControl(5)`. Parameters are fixed at build time with `-D`. | Works; the August benchmark ran this way on the N95. No data path. | [WRITEUP.md](WRITEUP.md), [findings.md](findings.md) §20 |
| **Stream worker without RUN** | `create` starts a DSP/BIOS task (`TSK_create`) that reads and writes STRM channels while the node stays in CREATED. A stop packet ends it; delete joins the task. Uses a generic type 2 library registration. | Works on both phones: series of packets, Q15 and WSOLA kernels, clean teardown. | [STREAM_RESEARCH.md](STREAM_RESEARCH.md), [PACKET_SIZES.md](PACKET_SIZES.md), [WSOLA.md](WSOLA.md) |
| **Full lifecycle with a shared ring** | create → RUN → packets → delete, with the payload in a 16 KiB ring mapped to both processors through the bridge's DMM calls (reserve 27, map 31, unmap 34, unreserve 28) and notifications through the native transport. | 3 consecutive clean cycles on each phone; ring series of 9360 packets on the N95. The DSP-to-SDRAM completion contract is not proven. | [LIFECYCLE_DMM](LIFECYCLE_DMM_2026-10-01.md), [DMM_ABI](DMM_ABI_2026-10-03.md), [DMM_RING](DMM_RING_2026-10-03.md), [N95_ACCEPTANCE](N95_ACCEPTANCE_2026-10-04.md) |

The bridge's message queue (ordinals 15–18, control codes `0x0C000001/2`) is not
used by any ROM module and crashed the kernel with the arguments tried. Later
experiments showed a DSP message reaching the shared message window, but its
delivery to an ARM caller was not established as a general contract, and two
nodes with the same message source can collide in the native routing ([WORKER_MESSAGES](WORKER_MESSAGES_2026-10-02.md),
[MESSAGE_ROUTING](MESSAGE_ROUTING_2026-10-03.md)). Do not build on it.

## 9. Writing a node

A dynamic node consists of a C file with the phases, a DCD registration in
assembler and a linker command file:

```
src/dsp/node.h              minimal node interface (create/execute/delete, RMS types)
src/dsp/bench_node.c        create-phase benchmark node
src/dsp/stream_node.c       stream node: worker task, ring exchange, kernel jobs
src/dsp/bench_dcd.s55       DCD registration: UUID, node properties, phase libraries
src/dsp/stream_*_dcd.s55    registrations of the stream node variants
src/dsp/*.lcf               linker command files (metasections as COPY)
src/dsp/bios_task.h         DSP/BIOS task ABI verified against the base image
src/dsp/c55math.h           hand-written 32-bit and fp32 arithmetic, as a header
```

Things to keep in mind, all explained in [DSP_GUIDE.md](DSP_GUIDE.md):

- `char`, `short` and `int` are 16 bits, `long` is 32, `float` and `double` are
  both 32. A loop counter that can pass 32767 must be `long`. A "byte array" is
  an array of 16-bit words, and one stream MAU is a 16-bit word: 256 MAU are 512
  ARM bytes.
- Data shared with the ARM must be laid out in 32-bit fields, written as explicit
  low and high 16-bit words. An ARM pointer is not a DSP pointer, so a structure
  with native pointers is not a wire format.
- `long × long`, division and floating point are calls into the base image
  (`__mpyli`, `__divli`, `__mpyd`, ...). Keep them out of hot loops; use
  `c55math.h` for 32-bit multiplies, and leave division to the compiler.
- Firmware nodes keep their context in `env->moreEnv` at an offset of 12 C55x
  words, allocated with `MEM_valloc` in create. The stream node does the same and
  checks the offset at compile time.
- Each node needs its own UUID in the DCD. For a dynamic node the phase
  libraries must be declared explicitly, because the ROM normally synthesizes
  them in ordinal 26, which we bypass ([findings.md](findings.md) §19).
- The DCD fields for static data size, global data size and program memory do
  not fix a `.bss` overflow. Only a smaller `.bss` does.

## 10. The ARM side

The host loads `bridgeapi.dll` with `RLibrary::Load` and calls its ordinals by
number. The sequence that creates a task on the C55x was predicted from the
disassembly and confirmed on the N95 ([findings.md](findings.md) §18):

```
ord36(objC)                                       construct class C (20-byte object)
ord11(objA)                                       construct class A (8 bytes)
ord32(objC, 0, 0, NULL)                    -> 0   open processor 0 (C55x); [C+0] is the channel handle
ord9(objA, objC)                           -> 0   bind A to the processor
ord26(objC, "Z:\resource\plugins\baseimage.dof", 0) -> 0   load the BASE image (never a node)
ord6(objA, uuid16)                         -> 0   find the node in the DCD (-6 = not found)
ord4(objA, &ref)                           -> 0
DoControl(channel, fn=4, TBuf8<20>{0,0,ref,0,0}, &out) -> 0   out = task handle
DoControl(channel, fn=5, handle, &status)  then wait for status: node CREATED
...
DoControl(channel, fn=6, handle, &status)  delete, on every path
ord10(objA); ord33(objC)                          shut down in CBal::Shutdown order
```

The channel handle is taken from `[objC+0]` into a subclass of
`RBusLogicalChannel` with `SetHandle`, and must not be closed by you: it
belongs to object C. Stream transfers use control codes `0x0800000E` (ARM to
DSP) and `0x08000010` (DSP to ARM) with a 28-byte packet copied by the driver
with `ThreadRawRead`; the layout is in [STREAM_RESEARCH.md](STREAM_RESEARCH.md).
`src/c55stream.cpp` is the reference implementation of all of this.

## 11. The shared ring format

The ring is 16 KiB **in total**, not per direction: a 1024-byte control area,
then 15 input and 15 output slots of 512 bytes. Each slot carries 480 bytes of
payload, so one exchange moves at most 7200 bytes in each direction. Ownership
covers the whole ring. The exact per-job layouts used for WSOLA, MDEC and the
SPU mix, with their slot counts, are in
[CLAUDE_PS1_HANDOFF](CLAUDE_PS1_HANDOFF_2026-10-04.md); the ring itself and its
measurements in [DMM_RING](DMM_RING_2026-10-03.md).

## 12. Measuring honestly

The project's numbers rest on a few rules ([DSP_GUIDE.md](DSP_GUIDE.md) §8,
[MEASUREMENT_PLAN.md](MEASUREMENT_PLAN.md)):

- A point is valid only when the status is 0. A time without a status check may
  be a timeout.
- Measure the difference of two runs with different repetition counts, so that
  fixed overheads cancel.
- Discard an abnormally fast run; it did not do the same work.
- Build both binaries from the same tree for every series.
- Do not trust the frequency the system reports. Read the clock registers or
  measure the work; record the clock state of every series.
- Keep the ARM busy while the DSP works (the `armbusy` mode of `dsptest`), or
  the DVFS governor lowers CORE and with it the DSP clock: in one measurement
  this removed a 41% spread and 18.9% of the DSP time (guide §15.7).
- Repeat every point. The spread between repeated runs depends on the setup
  (from 0% with `armbusy` to 41% without it), so take the tolerance from
  repeats of the same configuration.
- `CLK_countspms` = 164 and the 19.2 MHz timer do not give DSP time: over 800 ms
  the DSP counted only about 501 ms. Time everything on the ARM.

## 13. Checking the published evidence

The raw journals and summaries are in `docs/evidence/<date>/`. The verifiers
recompute the published results from those journals and check their hashes;
none of them talks to a phone.

```
python -B tools/test_e90_task_session.py
python -B tools/test_mdec_session.py
python -B tools/test_spu_session.py
python -B tools/test_wsola_current_session.py
python -B tools/verify_n95_acceptance.py
```

In a checkout without the phone ROM, one of the 27 tests in
`test_e90_task_session.py`
(`test_kernel_containers_audit_proves_e90_and_n95_root_and_factory`) fails with
`FileNotFoundError` for `work/evidence/e90/rom/ekern.exe`: it audits the ROM
itself, which is not distributed. The other 43 tests and the verifier need no
ROM.

If the sibling `PS1Emulator` tree exists next to this repository,
`verify_n95_acceptance.py` also compares the quoted source excerpts with it, and
fails if that tree has changed since the measurements. Run it in a checkout
without the sibling tree to check only the published evidence.

## 14. Where to go next

- [DSP_GUIDE.md](DSP_GUIDE.md): the complete rules for writing C55x code on this
  platform, including the clock and ioctl map.
- [findings.md](findings.md): the reverse-engineering record, each fact marked
  as measured on a device, derived from ROM code, or a hypothesis.
- [INDEX.md](INDEX.md): every document, with what question it answers.
- [REFERENCES.md](REFERENCES.md): the TI manuals and other primary sources.
