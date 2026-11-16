# TMS320C55x on the Nokia N95 8GB and E90

This repository is a research project. It runs custom code on the
**TMS320C55x DSP** inside the **TI OMAP2420** of two Symbian phones, the
**Nokia N95 8GB (RM-320)** and the **Nokia E90 (RA-6)**, and measures that code
against the phone's **ARM1136** core. It contains the source of an ARM host
program and of several DSP nodes, the reverse-engineered contract of the
Symbian DSP bridge, the build chain for both processors, and the published
measurements with the journals they were computed from.

The work went through three stages. In August 2026 it got a custom node running
on the C55x and benchmarked fixed-point kernels. In September and October 2026
it built a streaming data channel between the ARM and the DSP: first through
the bridge's stream API, then through a 16 KiB shared ring in mapped memory.
Finally it measured real workloads from a PlayStation emulator (MDEC, SPU mix,
WSOLA audio stretching) over that channel, to decide whether they should move
to the DSP.

Nothing here modifies the phone's firmware image. The tools copy their own
programs to the phone and temporarily replace DSP files, keep backups, and
restore the replaced files byte for byte; this was verified on the N95 after
every series. On the E90 the restoration after the last session is not
finished (see [What is open](#what-is-open)).

> **Research code, not a library.** The host program refuses to run on any
> firmware except the two exact versions it was verified on, and some bridge
> calls reboot the phone instantly. Read
> [the safety rules](docs/GETTING_STARTED.md#7-safety-rules) before running
> anything on a device.

## Results

### The DSP is fast only for 16-bit multiply-accumulate

The August benchmark ran the same Q15 dot product, `n = 1024`, on both
processors in the same boot of the phone, with the phone's audio stack alive
beside it:

| | MMAC/s | MAC per cycle |
|---|---|---|
| ARM1136 at 324 MHz (measured) | 32.3 | 0.099 |
| TMS320C55x at nominal 220 MHz | 55.6 – 88.1 | 0.253 – 0.400 |

The C55x is about 1.7–2.7 times faster in absolute terms on this kernel. The
estimates fall as the amount of work grows (88 → 68 → 56 MMAC/s), and for
planning the sustained rate of long jobs is 50.2 MMAC/s, about 1.55 times the
ARM. The MAC-per-cycle figure assumes the nominal DSP clock. The advantage holds
only for 16-bit fixed-point multiply-accumulate over a data stream. For 32-bit
integer arithmetic the ARM is about 5.6 times faster, for emulated 32-bit
floating point about 33 times, and for 32-bit division about 27 times, even
against hand-written C55x routines; branchy control code runs at parity.

The DSP clock divider was later read from the PRCM registers: the DSP runs at
CORE/3, 220.16 MHz at the nominal CORE clock. CORE itself is moved by the
phone's DVFS governor, and while the ARM sleeps waiting for the DSP the
governor can halve it; keeping the ARM busy during a measurement shortened the
DSP time by 18.9% and removed the spread. Measure DSP work with the ARM kept
busy (the `armbusy` mode). Details:
[DSP_GUIDE](docs/DSP_GUIDE.md), [CHARACTERIZATION](docs/CHARACTERIZATION.md),
[ANSWER_DSP_CLOCK](docs/ANSWER_DSP_CLOCK.md).

### A working streaming channel between the ARM and the DSP

The bridge's message queue does not work on this firmware, so the project found
other channels and verified each on both phones:

- **A worker task fed through bridge streams.** A DSP/BIOS task started in the
  node's create phase processes packets from STRM channels without the official
  RUN. Exchanging 1792 bytes took a median of 518 µs on the N95 and 640 µs on
  the E90 ([PACKET_SIZES](docs/PACKET_SIZES.md)). The worst cases in the same
  sample were 549 µs and 7812 µs, so the median does not guarantee an audio
  deadline.
- **Real parallel work.** With the ARM computing a 64 KiB CRC while the DSP ran
  a Q15 kernel, the combined workload took 250–251 ms in series and 149–151 ms
  in parallel on the N95, and 259–263 ms against 156–160 ms on the E90, about
  40% less time for this workload ([STREAM_RESEARCH](docs/STREAM_RESEARCH.md)).
  This is a property of the test load, not a measured speed-up of an
  application.
- **Full node lifecycle.** Three consecutive clean create → RUN → packets →
  delete cycles were completed on each phone.
- **A 16 KiB shared ring.** Payload travels through a ring in memory mapped to
  both processors, with page ownership and clean teardown verified; on the N95
  this ran 3 series, 12 runs and 9360 correct packets
  ([DMM_RING](docs/DMM_RING_2026-10-03.md)). Notifications still use the
  bridge's own transport.

### Emulator workloads stay on the ARM

Each emulator job was measured as a whole, from packing the input to having the
result back in ARM memory, and paired with the current ARM implementation of the
same job on the same phone (N95, stock clocks; p50 values in microseconds; the DSP path includes packing,
cache maintenance, transport and the DSP work):

| Job | ARM | DSP path | DSP faster |
|---|---:|---:|---:|
| WSOLA search, current SMLAD code | 337.601 | 1098.633 | 0 of 360 |
| MDEC, 1 / 2 / 4 macroblocks | 78.201 / 110.626 / 295.639 | 2655.029 / 4272.461 / 7690.430 | 0 of 1080 |
| SPU mix, 1 / 8 / 24 voices × 64 samples | 3.576 / 27.180 / 40.531 | 1617.432 / 3295.898 / 3540.039 | 0 of 1080 |

The DSP path did not win a single one of the 2520 pairs, even before counting
the node setup and teardown of about 0.84–0.87 s (instrumented, including
journaling, so not a production minimum). The reports do not split the DSP path
into fixed and per-job parts; note that for MDEC it grows with the job size,
by about 1.6–1.7 ms per macroblock. The verdict covers these blocking jobs only;
asynchronous or resident DSP work that overlaps useful ARM work was not
measured. Full report: [CLAUDE_PS1_HANDOFF](docs/CLAUDE_PS1_HANDOFF_2026-10-04.md),
acceptance matrix: [N95_ACCEPTANCE](docs/N95_ACCEPTANCE_2026-10-04.md).

## What is open

The [acceptance matrix](docs/N95_ACCEPTANCE_2026-10-04.md) lists the limits in
full. The main ones:

- No independent proof that DSP writes reach SDRAM before the mailbox
  notification arrives. Packets were correct in every run, but that is evidence
  of behaviour, not of the hardware contract.
- No universal safe cancel. If ownership of a pending transfer or a failed
  delete is uncertain, the host leaves the process in quarantine rather than
  killing it.
- The E90 is less stable than the N95. It restarted by itself several times
  during ring diagnostics ([DMM_RING](docs/DMM_RING_2026-10-03.md)), and the
  last session ended with a reboot after interface commands to the daemon,
  cause unknown ([E90_DAEMON_REBOOT](docs/E90_DAEMON_REBOOT_2026-10-04.md)).
  After that, the original host EXE, its hash and the journals on the E90 were
  not yet restored, and its clock frequencies during the last ring series are
  not confirmed.
- Long-running operation, coexistence with active audio, and error and timeout
  paths of the lifecycle were not tested as such.

## For developers

Start with **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**. It explains
when the DSP is worth using, what you need on the PC and on the phone, how to
build a node and a host, the three execution models that work, the safety rules
and how to verify the published evidence. The practical rules for writing C55x
code are in [docs/DSP_GUIDE.md](docs/DSP_GUIDE.md), and every document is listed
in [docs/INDEX.md](docs/INDEX.md).

The published evidence can be checked without a phone:

```
python -B tools/verify_n95_acceptance.py
```

Run it in a checkout that has no `PS1Emulator` folder next to it. If that
folder exists, the verifier also compares quoted emulator sources with it and
fails when the emulator has changed since the measurements.

## Repository layout

```
src/              ARM host programs (c55stream.cpp, dsptest.cpp) and shared headers
src/dsp/          C55x nodes: kernels, DCD registration, linker command files
src/mdec/, spu/,  exact snapshots of the emulator kernels used in the measurements
src/wsola_current/
group/            Symbian build files (bld.inf, *.mmp)
tools/            build scripts, device runners, journal summarizers, verifiers
tools/rev/        static analysis of the phone ROM (needs a local ROM dump)
docs/             reports, guides and findings; docs/evidence holds the raw data
work/             working notes of the research: plans, state, hand-offs
```

Every translated document has the Ukrainian original beside it as
`NAME.uk.md`; the release documents (this README, CHANGELOG, GETTING_STARTED,
INDEX, REFERENCES) were written in English. The research was conducted in
Ukrainian; where a translation and its original differ, the Ukrainian text is
the original record.

## Licence

Copyright (c) 2026 Pavlo Biletskyi. Licensed under GPL-2.0-or-later, see
[LICENSE](LICENSE). The host and the nodes include kernels
from PCSX-ReARMed (`src/mdec`, `src/spu`, with their original notices and
`COPYING`), so the built programs are covered by the GPL in any case.

TI manuals used during the work are not redistributed here; see
[docs/REFERENCES.md](docs/REFERENCES.md) for their numbers and links.
Symbol names, addresses and short strings from the phone ROM are quoted in
`docs/` for interoperability analysis. ROM images and disassembly listings of
Nokia code are not included; the tools in `tools/rev/` regenerate what they
need from a local ROM dump.

## Related projects

The phones are reached through SymbianDeployDaemon, a daemon on the phone
that accepts file and process commands over Wi-Fi or Bluetooth; it is a
separate project of the same author and is not published yet. The clock probe
`ocprobe` comes from
[SymbianOverclock](https://github.com/1234bpv/SymbianOverclock). The emulator
whose workloads were measured is
[PS1Emulator](https://github.com/1234bpv/PS1Emulator).
