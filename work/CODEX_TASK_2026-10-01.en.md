# Brief for the Codex executor, 2026-10-01

A brief from the orchestrator of the PS1Emulator project, given with the
person's consent. You work independently in this folder
(`H:\VsCodeProjects\SymbianProjects\TMS320C55x test`). First read `README.md`,
`work/STATE.md` (the last sections are the current state), `work/PLAN.md`,
`work/features.json`, `docs/STREAM_RESEARCH.md`, `docs/APPLICATION_CANDIDATES.md`
and the guide `..\PS1Emulator\docs\dsp-integration-guide.md`. Methodology and
rules are as in the user's global rules and in the files of this folder: the
state lives in files; every command has a time limit; three attempts per
problem; the report is concrete (file, line, exact error text, measured number).

## Goal

Bring the work with the C55x DSP to the state where the PS1 emulator can decide
whether to move even one task to the DSP. The emulator is now stuck on the v20
channel: latency 0,5–1 ms, about 9 MB/s, buffers of 4096 B. Through it, the
measured candidates of the emulator do not pay off (data from
`..\PS1Emulator\plans\reports\perf-dsp-analysis-2026-10-01.md`):

- MDEC in FMV: an exchange of about 190 us per macroblock versus 50 us of ARM work;
- SPU mixing: 3,7% of the scene time;
- WSOLA offset search: DSP 385 us per hop; the current ARM 999 us per hop, while
  the ARM core with `smlad` is estimated at 135–200 us (a calculation, not a
  measurement).

Stages (in this order, each with its own check):

- **D0. Safe completion.** Audit of errors, timeout and cancel in the native
  loader and in the streaming host (guide, section 5; the current defect is
  delete, status, FINAL, EXIT = −2 after RUN). Done when the full cycle
  create → RUN → packets → delete completes cleanly (EXIT/FINAL = 0) in three
  consecutive runs, and the device remains in a suitable state afterwards.
- **D1. Copy-free channel.** Check the shared buffer mapping (DMM / zero-copy,
  packet ring of 16 KiB) and measure the exchange latency and the throughput over
  repeats (not a single point). A negative result is also a result, if it is
  proven.
- **D2. Decision for the emulator.** From the measured numbers, compute each
  candidate above by the formula of the guide, `max(H + D, W) + S/N < A + W`, and
  record the verdict in `docs/PS1_CANDIDATES_2026-10-01.md`: what pays off, at
  which packet sizes, and what is missing. Do not implement this in the emulator —
  that is the zone of another executor.

## Devices: we divide them so as not to interfere

Update from the user, 2026-10-02: for testing, both N95 and E90 are now
available. The restriction below that concerns only E90 is historical; the ban
on INFO/GET/START for N95 is cancelled by this permission. Before experiments,
check the identity and the active processes, and keep the files that will be
replaced.

- Only the Nokia E90, 192.168.3.21:2323, is yours.
- **Do not touch the Nokia N95 (192.168.3.22) at all** — neither INFO, nor GET,
  nor START: the emulator is currently being tested on it. The unfinished N95
  items from `work/STATE.md` (the idle-first journal, the return of
  `ocprobe.log`, the cleanup of research files) remain deferred; record them in
  the report.
- The E90 is running overclocked (see `..\CLAUDE.md`): record the numbers together
  with the clock read from the registers, not from the intention.
- Before any write to the E90, save the original files, and after the experiment
  return them with a GET/SHA-256 check. Do not perform irreversible actions
  (flash, system files outside your research files).

## When a person is needed

If the E90 needs a reboot, a confirmation by the SIS installer on the screen, or
another physical action, append a request to `work/HELP_NEEDED.md` (date, what to
do, why, what has already been tried) and continue the work that does not need
the device. Do not keep retrying the same hardware failure more than three times.

## At the end

Update `work/STATE.md` and `work/features.json`, commit the changes in this
repository (without AI markers in the message) and push to private main, if that
is already this repository's practice. As the final message, give a short report:
what has been achieved for D0–D2, the numbers, what remains, and what is needed
from a person.
