# N95: залежності результатів і серійні витрати ARM

У виміряних блокувальних WSOLA68, MDEC66 та plain-SPU67 DSP не дає
виграшу проти відповідного ARM kernel. Цей аудит уточнює, що потрібно
довести для асинхронного варіанта. Він не змінює емулятор і не виконує
команд на телефонах; N95 залишається після verified originals5/PS0,
E90 відкладено користувачем.

[JSON з hashes, рядками джерел і всіма розрахунками](evidence/2026-10-04/n95-offload-dependency-audit.json)
отримано з current local PS1Emulator source та опублікованих журналів
cohorts66/67/68. [Аудит](../tools/audit_offload_dependencies.py) читає
сусідній проєкт; [незалежний verifier](../tools/verify_offload_dependencies.py)
перевіряє hashed journals, всі2520 full-job timings і strict нерівності.
Pilot jobs не входять у статистику. Джерельні excerpts зберігаються в JSON;
якщо сусідній проєкт доступний, verifier також перевіряє його повні hashes.

## Де потрібен результат

| Kernel | Поточний порядок у джерелі | Що потрібно для перекриття |
|---|---|---|
| WSOLA | `WsolaBestOffset` повертає offset; він одразу вибирає `win` для overlap-add та заміни `iWsTail`. Наступний hop використовує цей новий шаблон; compaction змінює search buffer. | Утримувати template/search до completion, відкласти mutation. Довести незалежність refill/guest work і виконання audio deadline. Майбутні пошуки одного потоку залежні. |
| MDEC | `rl2blk` перемежовує RLE/dequant та IDCT шести блоків; `yuv2rgb24` пише guest DMA RAM до повернення `psxDma1` і планування MDECOUTDMA. | Виділити стабільний coefficient job; довести input/output aliasing, guest RAM visibility, dynarec invalidation і порядок DMA busy/status/IRQ. Наступний RLE може бути pipeline work лише після цього доказу. |
| SPU plain mix | `ChanBuf` перевикористовується наступним голосом, `SSumLR` накопичується між голосами; потім MixCD/reverb/finish споживають суми й формують PCM. | Зберігати per-voice samples і володіння сумами. Врахувати FMOD, capture, noise, ADSR, register/DMA/SPU RAM ordering; resident full SPU потребує іншого контракту. |

Для незміненого блокувального виклику між поданням і негайним
споживанням результату немає запланованої незалежної роботи: `W=0` у
цій структурі. Це не вимір загального запасу guest CPU роботи й не доказ
неможливості іншого scheduler. Guest-cycle затримка MDEC event не є
незалежною роботою ARM у host wall time. Shell виконує guest Execute,
після нього audio pump; перенесення callback не доведене цим аудитом.

SPU має conditional worker source, але deployed emulator binary та
runtime thread configuration тут не перевірялися. Наявність worker у
джерелі сама по собі не доводить його активність чи безпечну DSP заміну.

## Необхідна умова для тієї самої ARM нитки

Початкова ідеальна модель `max(H+D,W)+q < A+W`, де `q=S/N`, еквівалентна
двом strict умовам: `q<A` та `W>H+D+q−A`.

Якщо submission/completion виконуються серійно з `W` на тій самій ARM
нитці, модель уточнюється до `H+max(D,W)+q < A+W`. Тепер необхідні
`H+q<A` та `W>H+D+q−A`: інша робота не приховує серійне пакування.

У журналах `result_ticks−notification_ticks` — elapsed інтервали
пакування/підготовки/відновлення результату поза notification exchange.
Позначимо їх `B`. Notification також включає ARM cache/submission/
completion work, тому повний `H` окремо не виміряно. За збереження цієї
виміряної stage envelope `B+q<A` є лише необхідною умовою. Це не мінімум
production CPU time: інтервали включають headers/padding/scratch і
можливі scheduling delays. Інший layout, zero-copy чи scheduler потребує
нового виміру.

| Job | A p50, us | Pack p50, us | B p50, us | Jobs із B<A, q=0 | Jobs із B+S/10000<A |
|---|---:|---:|---:|---:|---:|
| MDEC, 1 macroblock | 78.201 | 427.246 | 549.316 | 0/360 | 0/360 |
| MDEC, 2 macroblocks | 110.626 | 732.422 | 976.562 | 0/360 | 0/360 |
| MDEC, 4 macroblocks | 295.639 | 1403.809 | 1922.607 | 1/360 | 1/360 |
| SPU, 1 voice ×64 samples | 3.576 | 213.623 | 305.176 | 0/360 | 0/360 |
| SPU, 8 voices ×64 samples | 27.180 | 671.387 | 762.939 | 0/360 | 0/360 |
| SPU, 24 voices ×64 samples | 40.531 | 885.010 | 946.045 | 0/360 | 0/360 |
| Current WSOLA SMLAD | 337.601 | 91.553 | 91.553 | 359/360 | 359/360 |

Умови пораховано попарно для кожного job із його lifecycle S; різницю
медіан для них не використовували. Єдиний MDEC pass — series3/frame89,
batch4: ARM463615ticks/16, B34ticks, result136ticks. Він усе одно не є
блокувальним виграшем; це окремий повільний ARM sample, не стабільна
перевага чи підтверджене overlap.

WSOLA проходить необхідну серійну умову майже завжди; однак за N10000
потрібна незалежна `W` з paired threshold p50=847.608us у попередньому
[WSOLA68 розрахунку](N95_WSOLA_CURRENT_2026-10-04.md). Ні така корисна
робота, ні audio deadline/PCM equivalence тут не виміряні. За N≤1000
instrumented lifecycle S не проходить навіть необхідну умову для жодного
із2520 jobs. S включає journaling і не є мінімальним production startup.

Поточні kernels залишаються на ARM. Для D2 ще потрібен конкретний
незалежний W/state contract; для D1 — незалежний OMAP2420 external-memory
publication/notification proof. Ці критерії залишаються відкритими;
точність isolated synthetic jobs не доводить full-game speedup чи
тотожність повного PCM/стану.
