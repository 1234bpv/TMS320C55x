# Аудит повного дослідницького завдання

Дата2026-10-01. Критерії взято з `work/PLAN.md`, записаного до реалізації.
Дослідницький результат: переносний приватний проєкт, підтверджений
постійний STRM worker на двох телефонах, корисний ARM/DSP parallel workload,
точний WSOLA kernel з ARMv6 baseline, оцінка застосування і план інтеграції.

| Вимога | Доказ виконання | Межа висновку |
|---|---|---|
| F01: план і обв'язка | PLAN/features/STATE, bounded runners, check_state, незмінні historical evidence tags | Check_state не запускає phone experiment. |
| F02: переносна збірка | BUILD.md, env/build helpers; поточні ARM/DSP/SIS20 builds; artifact6, ARMv6 codegen proof | Raw binaries/ASM локальні; source/import hashes і build results публікуються. |
| F03: приватний GitHub | 1234bpv/TMS320C55x, PRIVATE; попередні checkpoints verified LOCAL=REMOTE; фінальний push і звірка після цього audit | Не публікуються firmware, vendor, keys, EXE/DLL/SIS/backups/screenshots. |
| F04: карта каналів | STREAM_RESEARCH.md, native ROM comparisons, STRM/DMM/notify/RMS/TSK/SEM contracts і ранжовані кандидати | MSG route/shared ring лишаються окремими неперевіреними каналами; робочий STRM не доводить їх. |
| F05: persistent stream/parallel N95 | v17 три serial/parallel pairs з DSP dot та незалежним ARM CRC; v18 багато packets/create; v20 exact WSOLA/length/stop і чисте завершення | Час start/transfer/combined compute виміряно ARM counter; DSP raw timer має idle limitation. |
| F06: справжній E90 | окремі firmware guards, ROM profiles, stock-clock preparations, v17/v18/v20 hardware journals, SIS20/EXE readback і final recovery | Адреси N95 не переносяться на PDD E90 без звірки. |
| F07: PS1/Browser assessment | APPLICATION_CANDIDATES.md: конкретні файли, formats/sizes/rates/dependencies, SPU historical profile; WSOLA.md: ARMv6 comparison,22/33-hop create-only break-even, integration plan | Це оцінка й перевірений research kernel. Зміни/виграш самих сусідніх застосунків не заявлені. |
| F08: узгодження і фінальний стан | README/WSOLA/PACKET_SIZES/STREAM_RESEARCH, historical corrections, features/evidence path audit, JSON/raw hash/status checks, PS0/originals GET-equal; private checkpoint | Source/evidence checkpoint e8f38c1: gates/push/LOCAL=REMOTE/PRIVATE перевірені. |

## Володіння даними й межі прототипу

ARM native allocations mode2 лишаються live до transfer completion і
успішного delete; statuses/transfer records мають persistent storage.
DSP owns issued buffers до reclaim, повторно primes лише після output
reclaim, last stop повертає buffers і завершує TSK до unload. Довжини в
ARM bytes/C55 words задано явно й перевірено сотнями varied packets.
Когерентність **native copy path** підтверджує правильність усіх даних;
manual mapping/cache barriers для shared ring з цього не виводяться.

Bounded host waits/stream waits/join вказані у source/artifacts; BIOS ticks
не називаються milliseconds. Усі зараховані hardware runs мають FINAL0,
EXIT0, no cancellation/KILL, explicit stop, delete/free/close. Invalid input,
timeout/live-task unload і безпечний ARM fallback не перевірені; native
loader audit потрібний перед application integration. Поточна позитивна
реалізація є research prototype із визначеним перевіреним шляхом завершення.

## Узгоджені спростування і невідоме

- Старі~9 мс порожньої create-фази не є вартістю кожного packet: resident
  stream v18/v20 виміряно окремо; WSOLA create median8.10/8.56 мс амортизується.
- Номінальні DSP220 МГц не підставляються як per-packet вимір. Stock guard
  перевіряє PRCM m86/div3/profile; N95 MPU100% резервується/перевіряється.
- CLK_countspms164 не перетворює raw ticks у wall time. Короткі ARM-bracket
  калібрування близькі до19.2MHz; довгий800ms idle систематично недораховує.
  Причина невідома. У порівняннях використано ARM FastCounter.
- Native copy/TSK success не доводить shared ring pinning/cache ownership
  або audio coexistence. Priority15 і короткі runs не є production audio test.
- ARMv5 v19 не замінює current PS1 scalar ARMv6 baseline. V20 body/flags
  звірено, stale SDK object усунуто до доставки; v19 evidence збережено.
- Ранні RUN/MSG/phase-library аварії та late N95 reboot після v18 збережено.
  Для late reboot причина невідома; у v19/v20 daemon startTick не змінився.
- v17~40% стосується combined synthetic dot+CRC; v20 saving стосується
  WSOLA kernel vectors. Application FPS/PCM/underrun gain не встановлено.

## Що належить наступній інтеграції

Safe error/cancel ownership/unload, довга робота, real audio coexistence,
recorded-PCM output/underrun/tail latency; MDEC/SPU state batching і Browser
job queue/profile. PLAN вимагав дослідження/прототип/оцінку й план інтеграції.
Повна реалізація всіх цих майбутніх застосункових стадій не є критерієм
завершення поточного доручення. Вони явно залишаються неперевіреними.

## Підсумок перевірки

F01–F08 виконані в межах research criteria. Source/evidence checkpoint
e8f38c1c052046560c216fb4cf7aa8aec8d02d16 відправлено; LOCAL=REMOTE/PRIVATE/clean verified.
129 reviewed files,76 byte-exact text artifacts,36 v19/v20 runs/780 correct
packets, current source/host/DSP SHA matches, originals/PS0 verified.
Completion metadata не змінює source/бінарники або hardware results.
