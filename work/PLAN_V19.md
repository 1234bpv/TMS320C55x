# V19: actual WSOLA search and the short output

The full scope of the task and the completion criteria are in `work/PLAN.md`.
Starting checkpoint `b7f0d7d`: v18, both devices, equal-size STRM.

1. Port the exact semantics of `WsolaBestOffset` from
   `PS1Emulator/src/symbian/snd_symbian.cpp`: 220 samples, 441 offsets, the
   left channel with stride2 and arithmetic >>6, coarse step4, refinement
   +-4, strict `>`, and the traversal order. The ARM reference keeps the
   stereo/shift inner loop; the DSP receives separately packed scaled signed16
   and uses a contiguous MAC.
2. Add only the verified, independent output stream size: input 896 C55 words
   (1792 B), output 24 words (48 B). The native allocation stays at 4096 B.
   Protocol19 explicitly returns both lengths, offset, score, the number of
   candidates, case, the checksum of the entire input, sequence, stop, and
   timer. Equal-size echo is supported. Do not change DCD or the official RUN.
3. Dataset: the exact seed/layout of the existing PS1 benchmark, silence,
   positive maximum, negative scores, left/right refinement, last offset, and
   tie-order. An independent Python reference checks the ARM/DSP
   offset/score/checksum/count. No PS1 gain without integration and
   measurement of the application itself.
4. Measure the ARM original search in a batch of 16 repetitions on the same
   stereo data; the result of each repetition has a consumer. Measure
   separately packing, issue-to-observed-completion, and packing+completion
   with the ARM FastCounter. Alternate the ARM/DSP baseline order between
   packets. Keep the DSP raw ticks diagnostic; do not use configured164 to
   convert them to time.
5. Before the devices: ARM/DSP/SIS builds, DOFF/imports, MAC ASM, a new
   immutable artifact archive, and fixtures. First, on N95: one old echo
   packet, one asymmetric no-compute, one WSOLA. A failure stops the series
   before the journal is read.
6. Fresh stock-clock preparation/backups; on each phone, three paired
   no-compute/WSOLA runs of 32 packets each, alternating the order of the runs.
   On N95, MPU reservation100 before/after each packet; E90 results separately.
   Check FINAL/EXIT0, one create/no RUN, explicit stop, join/delete/free/close.
7. Restore the original DSP/logs to GET-equal, and check PS/INFO and the host
   hash. Publish small byte-exact journals/JSON, the payback estimate for one
   WSOLA hop (~4.99ms), and the limitations. A negative result is acceptable.
8. Reconcile the docs, audit F05-F08, and the private checkpoint. The error
   lifecycle, timer/idle, and long-running work/audio coexistence remain
   separate questions; do not regard them as verified by these positive kernel
   runs.

## Completion check

- [x] Exact semantics and fixtures; short wire contract.
- [x] ARM/DSP/SIS and the archive were verified before delivery.
- [x] N95: minimal checks, three pairs, correctness, and cleanup.
- [x] E90: installation, the same checks, and cleanup.
- [x] Originals restored; evidentiary journals/results published.
- [x] Payback, limits of conclusions, F-audit, and the private checkpoint are reconciled.

V19 runs/fixtures/cleanup/recovery were completed on both phones. The ARMv5
timing is kept as historical; the final comparison was refined by ARMv6 in v20.
Evidence: WSOLA.md and docs/evidence/2026-10-01/{n95,e90}-wsola-v19-results.json.
The private checkpoint is verified together with v20; the full PLAN audit is in
FINAL_AUDIT.md.

The private source/evidence checkpoint e8f38c1 was verified: LOCAL=REMOTE,
PRIVATE, and clean. The completion metadata passes a separate final gate.
