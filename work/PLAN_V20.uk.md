# V20: узгодження ARM baseline з PS1Emulator

Під час аудиту v19 виявлено конкретну різницю: SDK baseline ARMv5/O2 має
260 Б коду пошуку; з ARMv6/arm1136j-s/fomit-frame-pointer —244 Б, opcodes
не збігаються. v19 journals/results збережено; вони доводять arithmetic/
wire/cleanup, але їхній ARM час не переноситься на поточну збірку PS1.
Доказ: `docs/evidence/2026-10-01/wsola-v19-arm-codegen.json`.

1. Додати до MMP ті самі architecture/tune/frame-pointer параметри, що у
   PS1 `configs/stage1/group/stage1.mmp`; SDK O2/no-unit-at-a-time лишаються.
   Host/protocol/SIS20, immutable archive6, нові journals без перезапису v19.
2. Звірити ARM body з ARMv6 pure-function build, ARM/DSP/SIS/imports/MAC.
3. Fresh preparation, one echo/no-op/WSOLA і три32-packet pairs на N95,
   потім host20 SIS та ті самі перевірки E90. Алгоритм/формат/набори v19.
4. Відновити originals GET-equal, перевірити clocks/PS/host/uptime.
   Offline перевірити кожен packet і status, опублікувати доказові результати.
5. Рахувати окупність з ARMv6 baseline. V19 залишити historical harness
   comparison, v20 — поточний scalar comparison. Немає application gain
   або гарантованої audio deadline без відповідних перевірок застосунку.
6. Audit повного PLAN F05-F08, узгодити docs і private checkpoint.

- [x] Builds і ARMv6 body перевірено.
- [x] N95 series/cleanup/recovery.
- [x] E90 series/cleanup/recovery.
- [x] Verified results/limits, F-audit і private checkpoint.

Codegen/source/artifacts,9 runs/195 packets per phone, originals/PS0
і offline byte/status checks пройшли. Final documentation/private gate
виконується; authoritative WSOLA.md та v20 results/checkpoint-device-status.

Private source/evidence checkpoint e8f38c1 verified LOCAL=REMOTE,
PRIVATE і clean. Completion metadata проходить окремий final gate.
