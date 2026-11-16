# V18: packet sizes and transfer cost for media

The full scope and completion criteria remain in `work/PLAN.md`.
Starting checkpoint: `156dea7`, worker v17 on N95/E90, 512-byte packets,
correct Q15/CRC, and a clean completion. F05–F08 are still open.

1. Establish from the native code where the STRM sizes come from, in what
   units the ARM passes them, what connection/transfer/allocation checks
   apply, and what the buffer limits are. Do not change the DCD fields
   without a proven link to these sizes.
2. Add explicit packet lengths with bounds checks to the host and the worker.
   The header takes 32 bytes: WSOLA needs 1760 bytes of data, that is 1792
   bytes in total; MDEC input of 1536 bytes needs 1568 with the header.
   Separate the useful data from the full transfer length. Earlier experiments
   with the official RUN stay at 512 B.
3. Verify the whole received payload, Q15 on the first 240 values, sequence,
   length, stop, and the final cleanup. To measure the channel, use the mode
   without ARM CRC and without repeated Q15, with the ARM FastCounter for each
   packet. Do not call the completion time pure DMA latency or bandwidth.
4. Before the device: successful ARM/DSP/SIS builds, checks of DOFF/imports/ASM,
   and saving the new artifacts without overwriting the v16/v17 evidence.
5. Fresh preparation with exact backups/readback. First, on N95, one 512 B
   packet; after a clean FINAL0, one packet of the nearest required size, then
   short series of larger packets and Q15. A failure stops the hardware series
   before the journal is read and the new contract is checked.
6. Install host v18 on the E90, check the EXE and the runtime profile, and
   repeat the confirmed checks. Record the conditions and results for each
   phone separately.
7. After the series, restore the original DSP/clock logs and verify SHA-256 and
   PS/INFO. Publish byte-exact journals and verifiable JSON with all statuses,
   sizes, measured times, and the limits of the conclusions.
8. Update the WSOLA/MDEC assessment using the measured sizes. The open
   questions that remain separate are timer/idle, long-running work, audio
   coexistence, and the error lifecycle; do not credit them on the basis of
   short positive tests. Reconcile the documentation and keep the checkpoint
   in private GitHub.

## Completion check

- [x] The native size/allocation/transfer contract is established on both ROMs.
- [x] Host/worker support the required lengths; the artifacts are verified.
- [x] N95: correctness, transfer, Q15, stop/cleanup, and recovery.
- [x] E90: installation, the same checks, and recovery.
- [x] The data are suitable for assessing WSOLA/MDEC; the limits of the conclusion are recorded.
- [x] Source/evidence/docs are synchronized with private GitHub.

Evidence: `docs/PACKET_SIZES.md`, `docs/evidence/2026-10-01/`:
`n95-e90-stream-size-contract.json`, `worker-stream-v4-artifacts.json`,
`{n95,e90}-packet-sizes-v18-results.json`, the corresponding recovery and raw
journals. On each phone: 22 runs/587 correct packets, 96 measurements per size.
The original DSP on both phones was restored with GET-equal results. A later
live check of the E90 also confirmed the original clocklog and host v18. After
two timeouts, the user restored access to the N95; its final GET also matched,
PS0. The reduced uptime indicates a new boot after the series; a clarification
about the cause was sent to the user. This is not a failure of any of the
completed v18 runs. The later status JSON files for both phones and the shared
checkpoint are saved in the same directory.

Checkpoint `4d39a89` was pushed to main. GitHub visibility is PRIVATE, the local
HEAD and the remote main matched, and the tree is clean. Before the commit, 79
files were reviewed; 46 raw journals in staged blobs matched byte for byte;
binaries, vendor firmware, keys, screenshots, and backups were not added.
Completion of this stage does not complete F05–F08 or the full goal.
