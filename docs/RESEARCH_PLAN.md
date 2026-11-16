# Initial research plan: access to the TMS320C55x on the N95 8GB

This is the historical plan, 2026-08-09. The current assignment and criteria
are in `work/PLAN.md`, the execution is in `work/FINAL_AUDIT.md`, and the
current measurements are in `docs/WSOLA.md`. The nominal frequencies and the
initial intentions below do not replace the new hardware results.

Date: 2026-08-09. The state of the facts is in `findings.md`. The methodology
and safety rules are inherited from `../SymbianOverclock/CLAUDE.md` (nothing
to flash, everything at runtime, do not repeat after two failures, measure
the work and not the label).

## Goal

Enable execution of our own code on the TMS320C55x inside the OMAP2420 and
**measure its speed against the ARM1136**, making this reproducible many
times. The result is a foothold for using the DSP in other projects (codecs,
DSP computations).

The minimal success (MVP): any **observable** own instruction executed on the
DSP, with the result returned to the ARM. Full success: a matched C55x vs
ARM11 benchmark with independently confirmed numbers, and the phone fully
working after the test.

## The main uncertainty that drives the plan

The DSP is **already occupied** by the firmware (the audio stack:
`ebridge`/`mailboxipc`/`activeadsp`, `findings.md` §3). Therefore we first
analyse how Symbian controls it, and only then choose between two paths:

- **Path A — coexistence through the Symbian bridge.** Through
  `ebridge`/mailbox, hand the DSP our own node/task (as Nokia's DSP Gateway
  on Maemo did). The smallest hardware risk; the blocker is whether the
  bridge accepts arbitrary code at all.
- **Path B — controlled takeover of the DSP.** Kernel MMIO (through
  `memoryaccess.ldd` or the exec-code primitive of the kernel, §5 of the
  findings): gate the DSP domain in the PRCM, release and restore the reset,
  configure the DSP MMU, load the C55x image into the DSP memory
  (`dspmemmapper`), set the boot vector, start it, collect the result through
  mailbox/shared memory, then return the DSP to the audio stack. Full control,
  higher risk.

The choice of A vs B is **a gate after Phase 1**, not now.

---

## Phase 0 — Knowledge base and tools (in parallel, without the phone)

Goal: have a complete map of the hardware and a working toolchain for the C55x.

0.1. **Get the OMAP2420 Multimedia Processor TRM** (not the C55x manuals, but
     the SoC). From it: the exact maps of the PRCM (CM_FCLKEN/ICLKEN/CLKSEL
     for the DSP domain, RM_RSTCTRL/RSTST reset), the CONTROL module (DSP/IVA
     boot config, `CONTROL_*`), the **DSP MMU** (TLB/CAM/RAM registers), the
     **MAILBOX** (the full map from the base `0x48094000`), and the DSP memory
     map in the L3 space (DARAM/SARAM, where it is mapped).
0.2. **Extract the relevant sections of the local PDFs** (SPRU312 +
     programming): the C55x boot sequence, the reset-vector format, IDLE
     domains, EMIF/DARAM, and the instruction set for the benchmark's
     fixed-point kernels. (`pdftotext -layout` already works; drafts are in
     `out/`.)
0.3. **Toolchain for C55x.** Evaluate the options and choose one: TI Code
     Composer Studio / `cl55` (asm+compiler, generates COFF), or open paths.
     Goal: build a minimal `.obj`/raw binary with a known entry, and be able to
     extract the raw code section (an analogue of stripping the header).
0.4. **Check the inherited infrastructure on a live phone:** the deploy daemon
     starts, `deploy_net.ps1 put/run/get` works, and the kernel read+exec
     primitives of SymbianOverclock reproduce. Without this, Phases 3+ are
     blocked.
0.5. **Project skeleton:** `src/` (ARM probe host), `group/` (mmp/bld.inf as
     in the neighbors), `tools/build.cmd` (a clone from SymbianDeployDaemon),
     `out/` (not committed). The target host will be called `dsptest.exe`.

Output of Phase 0: `findings.md` supplemented with register maps; the
toolchain builds a test C55x image; the hardware channel is confirmed live.

## Phase 1 — Reverse engineering of the Symbian DSP stack from ROM (without the phone)

Goal: understand **how the firmware controls the DSP**, and whether there is
an easy path.

1.1. Disassemble (objdump, extract the `TRomImageHeader`; if needed
     `syminflate.js`): `ebridgeutil.ldd`, `mailboxipc.dll`,
     `mrmailboxutils.dll`, `dspmemmapper.dll`, `activeadsp.dll`,
     `einfoadspplugin.dll`, `idspluginhandler.dll`. Artifacts are in `out/asm/`.
1.2. **`ebridgeutil.ldd`:** the registered driver name, the set of channel
     commands (`DoControl`/`DoRequest`), whether it exposes **code loading /
     node creation** on the DSP, or only controlled audio operations. Resolve
     the imports against the real `ekern.exe` from a dump (the SymbianOverclock
     method, §10).
1.3. **`mailboxipc.dll`:** the mailbox message format (the ARM↔DSP protocol)
     and which commands the DSP firmware understands. It gives a model for
     Path A and for code injection.
1.4. **`dspmemmapper.dll`:** how the DSP memory is mapped into the ARM (the
     physical addresses of DARAM/SARAM, sizes, cache attributes) — needed in
     order to place code/data for the DSP.
1.5. **`activeadsp.dll` (+ plugins):** is there a user-side client API
     (`RActiveADSP`?) that opens the channel; can it be used to slip in our
     own code.
1.6. **`memoryaccess.ldd`:** disassemble it fully. Does it give user-side
     Read/Write by physical address, and of what width (§4 of the findings).
     This may shortcut the whole Path B to simple MMIO — and close an open
     question of the neighboring project.
1.7. **Boot DSP:** find which module loads the DSP firmware at boot and how
     (where the DSP image lies in ROM, how the reset is released). It gives
     either a mechanism for repetition (Path B), or a pause point (Path A).

Output of Phase 1: in `findings.md` — the model of DSP control, the decision
**A vs B** with evidence, and the list of concrete commands/addresses for the
MVP.

## DECISION GATE — REVISED: Path A (see `findings.md` §11–§12)

Step 2 first inclined toward Path B. But a scan of Z: found on the phone a
**complete set of sample nodes of TI dspbridge** (`ping/scale/dmmcopy/strmcopy`
DOFF C55x) + Nokia's audio **DSP/BIOS base** (`baseimage.dof`) + a **dynamic**
PING (`pingdyn.dll55l`). This removes the main doubt about Path A (the DCD is
not closed — dynamic registration works) and gives a ready target. **Path A
was chosen** (the node via `bridgeapi.dll`): lower risk (no DSP reset is
needed, the audio stays intact), a sanctioned mechanism, and there is a node
template.

**Milestone 1 «Hello, DSP» — WITHOUT the toolchain:** trigger the existing
**PING node** (UUID `12A3C3C1-D015-11D4-9F69-00C04F3A59AE`) through
`bridgeapi.dll` (attach → node-allocate → create → run → ping-msg). cl55 is
NOT needed → it can be run autonomously (reverse engineering of the node-load
API of `bridgeapi.dll`).

**Milestone 2 «Benchmark»:** an own C55x node with Q15 kernels (template —
ping) — here **TI `cl55`** is needed (C5500 CGT, free, proprietary; there is
no open C55x assembler) + the node description/DCD. Installing cl55 is a user
step.

> **ARM-side status (2026-08-10, findings §16–§17):** the bridge has been
> reverse-engineered. The whole dspbridge lives in the kernel behind the LDD
> `Hwa` (`ehwa.ldd` + `ehwaomap.pdd`), and the MultimediaDD capability is
> required. The 39 ordinals of `bridgeapi.dll` are sorted into three classes
> (A/B/C), and all 39 addresses were checked against the live phone. The full
> kernel surface was obtained: 24 device commands `0x0400_00NN`, 18 task
> commands `0x0800_00NN`, and the family `0x0C00_00NN`. A reference sequence
> was found in `CBal` (§17.5); our loader mirrors it. Separately, the ARM-side
> build, which had never worked because of a space in the path, was fixed.
>
> **Blocker:** the phone reboots (§16.8, §17.6, §17.7). One cause is probably
> ours and has already been removed (`User::LoadLogicalDevice`); the other lies
> outside our code (a neighboring project left `dvfs_interface` and
> `RomPatcherPlus.Driver` in the system; at 423 MHz the phone was in a mode with
> a known auto-reboot). Until this is clarified, runs on the phone measure
> noise.

> **DSP-side status of Milestone 2: closed** (findings §13–§15). cl55 is
> installed, the COFF→DOFF chain works natively on Windows, the node has its
> own UUID and DCD entry, and the DOFF form matches Nokia's production node.
> Both milestones now run into the same thing: the ARM loader on top of
> `bridgeapi.dll` (reverse engineering of the 39 ordinals under the §14.1
> contract) — and a phone for the run. Phase 3.3 is incidentally closed: the
> DSP-side time instrument is `CLK_gethtime` / `CLK_countspms` from the base
> image (§15.4).

Path B (controlled DSP takeover, full register map §8) is kept as a fallback,
in case the DCD registration of our own node on a retail phone turns out to be
closed after all.

## Phase 2 — «Hello, DSP»: the first own instruction (on the phone)

Goal — make-or-break: to run our own code on the DSP **observably**.

- **Path A:** send a minimal own operation through the open channel; prove
  that exactly our code ran (e.g., the DSP writes a recognizable pattern into
  shared memory, which the ARM reads through `dspmemmapper`).
- **Path B:** a minimal C55x blob «write 0x5A5A to a known DARAM cell and
  stop»; the ARM gates the domain, releases the reset, waits, reads the cell,
  and returns the DSP. (A mirror of the SymbianOverclock technique, where the
  blob `mov r0,#0x5A; bx lr` proved that the SRAM is executable.)
- Mandatory: timeouts on every step (a lesson from the neighbor: a hang blocks
  the whole delivery channel), restoration of the DSP state at the end, and
  everything risky behind an explicit argument of the probe.

Output: a confirmed and documented fact that «our code runs on the DSP».

## Phase 3 — C55x vs ARM11 benchmark (on the phone)

3.1. Choose matched kernels: (a) **DSP-profile** — FIR / dot-product / block
     FFT in Q15 fixed-point (C55x dual-MAC versus ARM1136); (b) **neutral
     integer** — to see the limit outside the DSP's strong side. Do not use
     floating point (the C55x has no hardware for it).
3.2. ARM side: reuse the measurement framework of SymbianOverclock (counters,
     Mitr/s, sustained load).
3.3. DSP side: instrument the loops (the DSP clock-cycle counter), the same
     workload, the same data, and account for the transfer cost through
     mailbox/shared memory separately from pure computation.
3.4. Normalize by frequency (DSP ~220 MHz vs ARM 330 MHz) and give both
     absolute and per-clock figures.

## Phase 4 — Measurements, cross-checking, documentation

- Each number is taken with **two independent instruments** and reproduced at
  least 2 times (the discipline of evidence). Explicitly separate «pure DSP
  computation» and «computation + IPC».
- Record in `findings.md`; a short summary report, as in the neighbor
  (`WRITEUP.md`).
- Make sure that after the test the phone's audio/DSP works (a reboot as
  insurance, but the goal is a correct recovery without a reboot).

---

## Risks and safeguards

| Risk | Safeguard |
|---|---|
| DSP takeover breaks sound until a reboot | Path A first; in Path B, save/restore the state of the DSP domain; the test only behind an explicit argument |
| A hang blocks the delivery channel | Timeouts on every request and on the load/create of the driver; a static `TRequestStatus`; do not close the channel after a timeout (lesson SymbianOverclock §7) |
| No Kernel DevKit | Only third-party drivers or the kernel exec primitive; we do not build our own LDD |
| Compressed DSP modules in ROM | `syminflate.js` already solves the Symbian deflate |
| Byte order / MMIO width | Mailbox/PRCM registers — strictly 32-bit access (lesson §10 of the neighbor) |
| Passing a guess off as a fact | Every address/field is checked against the ROM code or the TRM; hypotheses are marked |

## Next 3 steps (right after this plan)

1. Obtain the OMAP2420 Multimedia Processor TRM and extract the PRCM/CONTROL/
   DSP-MMU/mailbox maps (Phase 0.1).
2. Disassemble `memoryaccess.ldd` and `ebridgeutil.ldd` — they decide the A/B
   gate (Phase 1.2, 1.6).
3. Bring up the project skeleton and check the deploy channel on the phone
   (Phase 0.4–0.5).
