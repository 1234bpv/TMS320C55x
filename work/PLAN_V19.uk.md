# V19: фактичний пошук WSOLA і короткий вихід

Повний обсяг завдання і критерії завершення — `work/PLAN.md`.
Вихідний checkpoint `b7f0d7d`: v18, обидва апарати, equal-size STRM.

1. Перенести точну семантику `WsolaBestOffset` із
   `PS1Emulator/src/symbian/snd_symbian.cpp`: 220 відліків, 441 зсув,
   лівий канал зі stride2 і arithmetic >>6, coarse step4, refinement +-4,
   strict `>` і порядок обходу. ARM-еталон зберігає stereo/shift inner loop;
   DSP отримує окремо упаковані scaled signed16 і використовує contiguous MAC.
2. Додати лише перевірений незалежний output stream size: input896 C55 words
   (1792 Б), output24 words (48 Б). Native allocation лишається4096 Б.
   Протокол19 явно повертає обидві довжини, offset, score, число кандидатів,
   case, checksum усього входу, sequence, stop і timer. Equal-size echo
   підтримується. DCD і official RUN не змінювати.
3. Dataset: точний seed/layout існуючого PS1 benchmark, silence, positive
   maximum, negative scores, left/right refinement, last offset і tie-order.
   Незалежний Python-еталон перевіряє ARM/DSP offset/score/checksum/count.
   Жодного gain PS1 без інтеграції і вимірювання самого застосунку.
4. Міряти ARM оригінальний пошук батчем16 повторів на тих самих stereo
   даних; результат кожного повтору має споживача. Окремо packing,
   issue-to-observed-completion та packing+completion за ARM FastCounter.
   Чергувати порядок ARM/DSP baseline між пакетами. DSP raw ticks залишити
   діагностичними, configured164 не використовувати для перерахунку в час.
5. До апаратів: ARM/DSP/SIS builds, DOFF/imports, MAC ASM, новий immutable
   artifact archive і fixtures. Спершу N95 один старий echo packet, один
   asymmetric no-compute, один WSOLA. Відмова зупиняє серію до читання журналу.
6. Fresh stock-clock preparation/backups; на кожному телефоні три paired
   runs no-compute/WSOLA, по32 packets, з чергуванням порядку runs.
   N95 MPU reservation100 до/після кожного пакета; окремі результати E90.
   Перевірити FINAL/EXIT0, one create/no RUN, explicit stop, join/delete/free/close.
7. Original DSP/logs повернути GET-equal, PS/INFO та host hash перевірити.
   Опублікувати small byte-exact journals/JSON, оцінку окупності одного
   WSOLA hop (~4.99ms) і обмеження. Від'ємний результат прийнятний.
8. Узгодити docs, audit F05-F08 і private checkpoint. Error lifecycle,
   timer/idle і довга робота/audio coexistence лишаються окремими питаннями;
   не вважати їх перевіреними цими позитивними kernel runs.

## Перевірка виконання

- [x] Точна семантика і fixtures; короткий wire contract.
- [x] ARM/DSP/SIS і archive перевірено перед доставкою.
- [x] N95: мінімальні перевірки, три pairs, правильність і cleanup.
- [x] E90: встановлення, ті самі перевірки і cleanup.
- [x] Originals відновлено; доказові journals/results опубліковано.
- [x] Окупність, межі висновків, F-audit і private checkpoint узгоджено.

V19 runs/fixtures/cleanup/recovery виконано на обох. ARMv5 timing залишено
historical; final comparison уточнено ARMv6 v20. Докази: WSOLA.md і
docs/evidence/2026-10-01/{n95,e90}-wsola-v19-results.json. Private checkpoint
перевіряється разом з v20; full PLAN audit у FINAL_AUDIT.md.

Private source/evidence checkpoint e8f38c1 verified LOCAL=REMOTE,
PRIVATE і clean. Completion metadata проходить окремий final gate.
