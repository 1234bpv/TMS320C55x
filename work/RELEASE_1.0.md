# Release 1.0: plan and state

Goal (from the user, 2026-11-16): prepare all documentation that makes work
with the DSP easier for other developers, translate all documentation into
English while keeping the Ukrainian copies, and publish the project.

Decisions of the user, 2026-11-16: licence GPL-2.0-or-later for the whole
project; the two TI PDF manuals are removed from the tree and replaced by
references (git history still contains them; rewriting history is the user's
decision); English is the primary language, Ukrainian originals kept as
`NAME.uk.md`. Run executors one at a time to save limits.

Branch: `release-1.0`.

## Acceptance

1. Every `docs/*.uk.md`, `work/*.uk.md`, `work/research/*.uk.txt` has an
   English `NAME.md`/`NAME.txt` that passes `out/translation/check_translation.py`
   (copy of the checker: the scratchpad of the session; spec in
   `out/translation/TRANSLATION_SPEC.md`) or has every mismatch explained.
   `work/CODEX_TASK_2026-10-01.md` stays byte-identical (hash in evidence);
   its translation is `.en.md`.
2. New: README.md, LICENSE, CHANGELOG.md, docs/GETTING_STARTED.md,
   docs/INDEX.md, docs/REFERENCES.md; old README archived in docs/archive/.
3. No source, script, verifier or evidence file changed. Offline tests
   (44 unit tests) pass, and `tools/verify_n95_acceptance.py` passes in a clean
   clone without the sibling PS1Emulator tree (baseline on main: PASS).
4. Final review by `final-reviewer`, then merge to main, push, make the
   repository public (after asking about the history containing the PDFs),
   tag v1.0.0.

## State, 2026-11-16 (evening)

- Item 2 done. Item 1 done: all 48 English documents exist; the checker passes
  for all of them except explained cases: label glued to a value in the source
  (`N95640.87`, `N95 50847.608` in WSOLA and N95_WSOLA_CURRENT), code spans that
  contained Cyrillic and were translated (BUILD, ANSWER_DSP_CLOCK), two anchors
  in findings remapped to the English headings of STREAM_RESEARCH
  (`out/translation/fix_anchors.py`), and the Ukrainian labels that the R1 prompt
  itself requires. One dropped address (`803DF864`) in PLAN_D0_D2 was restored
  by hand.
- Executors: Haiku translated 26 files before its weekly limit (resets
  2026-11-18 15:00 Europe/Helsinki); Gemini 3.8 Flash through agy translated the
  rest in 9 sequential batches (`out/translation/run_agy.sh`, run without
  `--agent`, because the generated `~/.gemini/config/agents/ag-*.md` list both
  `view_file` and `read_file` and agy 1.4.1 fails with
  `tool name conflict: multiple tools resolved with name "read_file"`). Codex:
  the wrapper default `gpt-6.1-sol` is rejected for a ChatGPT account; with
  `MODEL=gpt-6-luna` a read-only probe works, but two write runs ended with
  exit 0, no output and no file.
- Two links in PS1_CANDIDATES point into the sibling PS1Emulator tree (as in
  the original); they do not resolve in a standalone checkout.
- Next: commit on the branch, item 3 in a clean clone, item 4.

## Decisions after the final review, 2026-11-17

- Publish as a new repository with a single commit (user). The old history
  contains both TI PDFs, a private profile path in earlier versions of
  `work/GEMINI_REVIEW_2026-10-03.md`, and `docs/bridgeapi_fns.txt`; it stays
  private.
- `docs/bridgeapi_fns.txt` (disassembly listing of Nokia `bridgeapi.dll`, used
  by no tool) removed from the tree; local copy in ignored
  `work/vendor/rom-derived/`.
- `src/wsola_current` is the author's own code: PS1Emulator history shows
  `WsolaBestOffset` added in `096c646` (2026-09-21) and its SMLAD version in
  `dc749fe` (2026-10-01), all 13 commits of `snd_symbian.cpp` by the author;
  no such code in pcsx_rearmed. Licence of this repository applies.

## Noticed in the sources (not changed)

- `docs/CLAUDE_PS1_HANDOFF_2026-10-04` gives the N95 stock bus as 110.08 MHz;
  `docs/MESSAGE_ROUTING_2026-10-03` measured BUS 165120 kHz on the N95, which
  matches SymbianOverclock. The handoff figure looks wrong.
- `docs/DSP_GUIDE` §1 still says the C55x runs at about 60 MHz; §10 of the same
  guide corrects this to 220.16 MHz.
