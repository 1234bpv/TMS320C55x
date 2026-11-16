# V20: aligning the ARM baseline with PS1Emulator

During the v19 audit, a concrete difference was found: the SDK baseline
ARMv5/O2 has 260 B of search code; with ARMv6/arm1136j-s/fomit-frame-pointer
it is 244 B, and the opcodes do not match. The v19 journals/results are kept;
they prove arithmetic/wire/cleanup, but their ARM time does not carry over to
the current PS1 build. Evidence: `docs/evidence/2026-10-01/wsola-v19-arm-codegen.json`.

1. Add to the MMP the same architecture/tune/frame-pointer parameters as in
   the PS1 `configs/stage1/group/stage1.mmp`; the SDK O2/no-unit-at-a-time
   settings remain. Host/protocol/SIS20, immutable archive6, new journals
   without overwriting v19.
2. Verify the ARM body against the ARMv6 pure-function build, ARM/DSP/SIS/imports/MAC.
3. Fresh preparation, one echo/no-op/WSOLA, and three 32-packet pairs on N95,
   then host20 SIS and the same checks on E90. Algorithm/format/data sets as in v19.
4. Restore the originals to GET-equal, check clocks/PS/host/uptime. Offline,
   check each packet and status, and publish the evidentiary results.
5. Compute the payback from the ARMv6 baseline. Keep V19 as the historical
   harness comparison, and v20 as the current scalar comparison. There is no
   application gain or guaranteed audio deadline without corresponding
   application checks.
6. Audit the full PLAN F05-F08, reconcile the docs and the private checkpoint.

- [x] Builds and the ARMv6 body verified.
- [x] N95 series/cleanup/recovery.
- [x] E90 series/cleanup/recovery.
- [x] Verified results/limits, F-audit, and the private checkpoint.

Codegen/source/artifacts, 9 runs/195 packets per phone, originals/PS0, and
offline byte/status checks passed. The final documentation/private gate is in
progress; the authoritative sources are WSOLA.md and the v20
results/checkpoint-device-status.

Private source/evidence checkpoint e8f38c1 verified LOCAL=REMOTE,
PRIVATE, and clean. The completion metadata passes a separate final gate.
