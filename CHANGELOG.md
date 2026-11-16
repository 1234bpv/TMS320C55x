# Changelog

## 1.0.0 — 2026-11-16

First public release. It publishes the research as it stood at the
checkpoint of 2026-10-04, with the following additions for readers outside
the project:

- English documentation. Every report in `docs/` and every working note in
  `work/` has an English version; the Ukrainian originals stay beside them as
  `NAME.uk.md`. `work/CODEX_TASK_2026-10-01.md` keeps its Ukrainian original
  under its own name because its hash is recorded in the acceptance evidence;
  its translation is `CODEX_TASK_2026-10-01.en.md`.
- A new [README](README.md) with the results and their limits, a developer
  guide [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md), a document index
  [docs/INDEX.md](docs/INDEX.md) and [docs/REFERENCES.md](docs/REFERENCES.md).
- Licence: GPL-2.0-or-later ([LICENSE](LICENSE)).
- The two TI manuals that were stored in the repository root are removed from
  the tree and replaced by their document numbers and links.
- The previous README, a running log of the research, is kept as
  [docs/archive/README-2026-10-04.uk.md](docs/archive/README-2026-10-04.uk.md).
- A private local path was removed from `work/GEMINI_REVIEW_2026-10-03`.

No source code, build script, verifier or evidence file was changed. The
offline checks give the same result as before the release work.

### Contents of the research at this release

- August 2026: a custom node on the C55x and a fixed-point benchmark against
  the ARM1136.
- September 2026: the stream worker without RUN, packet sizes from 512 to 4096
  bytes, parallel ARM and DSP work, the WSOLA kernel on the DSP.
- October 2026: three clean full node lifecycles on both phones, the 16 KiB
  shared ring, CPU accounting, and the paired measurements of the MDEC, SPU mix
  and current WSOLA jobs that keep these emulator workloads on the ARM.
