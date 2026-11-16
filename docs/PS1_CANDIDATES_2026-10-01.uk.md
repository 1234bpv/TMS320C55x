# Рішення для PS1Emulator за результатами C55x

## Актуальне доповнення 2026-10-04: N95

[Передача Claude для PS1](CLAUDE_PS1_HANDOFF_2026-10-04.md) закриває поточні
роботи звітом за запитом користувача: рішення, точні jobs, джерела,
перевірки й відкриті gates. Нових hardware experiments автоматично не починати.

D0 уже complete на обох телефонах; native ring16KiB TOTAL працює.
N95 native61 має3 серії/9360 correct packets із stock brackets.
Після окремої калібровки виконано candidate64/host49 aggregate CPU
measurement: batch1/2/8/15 exchange p50=915/1190/3021/5126us,
thread CPU45.37/45.87/48.09/45.68% у full correctness window із final
settling yield. Full-window useful bidirectional bandwidth0.712/0.960/
1.357/1.500MB/s. Це synthetic transform; ці T не є MDEC/SPU kernels.
[CPU window і межі](N95_RING_CPU_2026-10-04.md).

WSOLA63/host48 — actual coarse/refine kernel через ring, pilot8 +360
paired jobs, exact offsets/scores. A p50=1155.853us, pack-to-result H+D
p50=1983.643us, лише16/360 H+D<A до setup. **Для поточного блокувального
WSOLA залишити ARM.** Instrumented S p50=828063us includes logging,
не pure create/minimum production startup. Strict сценарії N16/64/256/1000
використовують S відповідної серії й окремо перевіряють S/N<A та
W>H+D+S/N−A. Useful W не виконувався; asynchronous gain не виміряний.
SMLAD135–200us залишається оцінкою.
[WSOLA результати](N95_WSOLA_RING_2026-10-04.md),
[paired calculations](evidence/2026-10-04/n95-wsola63-results.json).

Current shell уже має packed SMLAD. WSOLA68/host53 із exact snapshot
і retained exactDSP63 завершив8 pilots +360 paired jobs: current A
p50=337.601us, scalar1003.265us, H+D ready1098.633us; current winners0/360
до setup, paired scalar/current p50ratio3.017x. **Current blocking WSOLA
залишити ARM.** Оцінка135–200us не підтверджена цією probe; measured A
включає packing. S p50=865080us logging; N10000 setup360/360, required
W p50847.608us, blocking gain0. Useful W/full audio unmeasured.
[Current WSOLA68/interruption](N95_WSOLA_CURRENT_2026-10-04.md).

MDEC66/host51 — actual six-IDCT + RGB24, int32 coefficients, exact outputs:
1080 jobs/2520 macros; batches1/2/4 A GCCE463 p50=78.201/110.626/295.639us,
H+D pack→RGB24 reconstructed in ARM memory p50=2655.029/4272.461/7690.430us.
Oracle checks поза обома часовими межами; blocking winners0/1080 до setup.
**Для виміряного блокувального MDEC job залишити ARM.** S p50=840178us
includes lifecycle journaling; W=0; не gameplay/full RLE-DMA-IRQ integration
і не доказ неможливості resident/asynchronous DSP.
[MDEC точність/виміри](N95_MDEC_RING_2026-10-04.md).
SPU: попередній scene budget3.7% не є часом ring kernel;
потрібні actual mix job/state traffic/A/W і повна тотожність audio/state.
Тому **SPU залишити ARM до виміряної окупності конкретного job**;
async/resident DSP варіанти відкриті, неможливість не доведена.
[SPU boundary audit](N95_SPU_BOUNDARY_2026-10-04.md): plain24 voices із
samples/volumes/sums32 вміщує лише до66 samples/job; optional ARM work_item
8396B вже більший за7200B input payload. 512KiB SPU RAM, history/ADSR/
noise/reverb/IRQ потребують окремої coherency межі. Current ARM baseline
має smlawb/smlawt. Після аудиту виконано SPU67/host52:24 pilots і1080
plain-mix jobs1/8/24 voices×64 samples із exact128 stereo sums32/job.
A current ARM p50=3.576/27.180/40.531us проти H+D ready1617.432/3295.898/
3540.039us; oracle checks outside. Blocking winners0/1080 до setup.
**Виміряний plain-mix job залишити ARM.** S p50=863494us includes logging,
W0, CPU unmeasured; full SPU/state/PCM та async/resident profit відкриті.
[SPU67 measured contract](N95_SPU_RING_2026-10-04.md).

Independent endpoint-publication contract лишається відкритим; stock
brackets не є continuous DVFS trace. D1/D2 загалом in_progress.
Current source dependency audit встановив immediate consumers і mutation
межі для всіх трьох kernels. Для тієї самої ARM нитки модель
`H+max(D,W)+S/N<A+W` додатково вимагає `H+S/N<A`.
Measured serial intervals outside notification проходять цю необхідну
умову при S=0 у MDEC1/1080, SPU0/1080, currentWSOLA359/360 jobs;
це не overlap winners. W у незмінених blocking calls0 за структурою,
загальний незалежний guest-work budget не виміряний.
[Залежності й paired bounds](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md).
Емулятор unchanged. N95 originals5 після68 restored/GET-SHA equal, PS0;
E90 відкладено користувачем, нових команд не надсилали.
[N95 requirement/evidence checkpoint](N95_ACCEPTANCE_2026-10-04.md)
відокремлює delivered measured-job verdict від відкритого memory contract
і майбутньої emulator integration; master verifier перевіряє всі основні
N95 cohorts та свіжий read-only original-files/PS0 стан.

## Історичний розрахунок 2026-10-01

Дата: 2026-10-01. **Прикладну інтеграцію зараз не починати:** D0 з офіційним
RUN ще не прийнято, DMM/спільне кільце16KiB не виміряні. Нижче наведено
розрахунок для попереднього, вже виміряного каналу копіювання v18/v20.
Це проміжний результат D2; його треба доповнити після апаратного D1.
Емулятор у цій роботі не змінювався; N95 не опитувався.

Продовження E90: два RUN дали по8 правильних512-Б packets, але
delete−2/−33; третій MSG diagnostic також delete−2. D0 лишається0/3.
Людина дозволила нові спроби з окремою гіпотезою; native reference
control готується. Median396us із16 packets цих failed-lifecycle
проб не підміняє прийнятий D1 замір і не змінює формулу нижче.
[Докази](evidence/2026-10-01/e90-d0-resume-checkpoint.json).

## Дані та межі порівняння

[WSOLA](WSOLA.md) містить три парні серії v20 по32 control/search пакети
на кожному апараті. [Пакети v18](PACKET_SIZES.md) містять три серії
по32 пакети на розмір. Усі ці виміри зроблені за штатного guard m86/div3.
У поточній сесії E90 також фактично штатний: `CM_CLKSEL1_PLL=00056400`,
`CM_CLKSEL2_PLL=2`, `CM_CLKSEL_MPU=2`, `CM_CLKSEL1_CORE=04360626`,
`CM_CLKSEL_DSP=00000343`; ARM330.24MHz, bus110.08MHz, DSP220.16MHz.
Це прочитано з регістрів, частоти не змінювалися. Вказаний у дорученні
розгін m105 зараз не підтверджено.

E90 symmetric echo512/1568/1792/2048/2304/4096 Б: pooled медіани
396/610/640/701/762/1129us, по96 пакетів на розмір. Для4096 Б медіани
трьох окремих серій1129/1129/1129us, p95=1220us, max=2502us.
Максимуми1792/2048 Б7812/7690us залишаються у вибірці. Це повний echo
із драйвером/плануванням, а не ізольований DMA або вимір zero-copy.

Оцінку9MB/s з [звіту емулятора](<../../PS1Emulator/plans/reports/perf-dsp-analysis-2026-10-01.md>)
використано тільки в сценаріях. Її не слід оголошувати прямо виміряною
пропускною здатністю DMM. DSP385us із доручення також не є виміром часу
ядра:385.28us — медіанна **попарна економія ARM−DSP path на N95**.
Виміряний повний WSOLA path становить640.87/732.42us N95/E90.
Різниця медіан search/control122.07us не є незалежним виміром чистого D.

## Формула та перекриття

Позначимо `T=H+D`, `q=S/N`. Перевіряється
`max(T,W)+q < A+W`. Для невід'ємних часів це рівносильно одночасним
умовам **`q < A` і `W > T+q−A`**. За `W=0` потрібне `T+q < A`.
За `W>=T` достатньо `q<A`, але на практиці H частково займає ARM,
а процесори конкурують за шину. Ідеальна формула є нижньою оцінкою.

Тому саме лише `H>A` не доводить неможливості асинхронного виграшу:
потрібно ще встановити, скільки незалежної W доступно до споживання
результату. W не виміряна в емуляторі для цих job; середній час кадру
не можна автоматично оголосити такою незалежною роботою.

S має містити весь запуск і прибирання сесії. Наявні8.102/8.5595ms
N95/E90 — лише create, тому наведені нижче N є оптимістичними.
Розрахунки відтворює [assess_ps1_candidates.py](../tools/assess_ps1_candidates.py),
точні вхідні hashes і числа — [JSON](evidence/2026-10-01/ps1-candidates-calculation.json).

Прикладні A для MDEC/SPU взято з N95-звітів, а не нового E90 A/B.
SPU scene має ARM330.24/bus165.12MHz; E90 channel має bus110.08MHz.
Це різні апарати й шини; бюджети потребують перевірки на цільовому апараті.

## MDEC

Поточний точний формат —384 int32=1536 Б на макроблок, RGB15/RGB24
512/768 Б виходу. Із32-Б заголовком у кожному напрямку це1568/544 або800 Б
на один блок. 768 Б коефіцієнтів із зовнішнього звіту передбачають int16;
такий діапазон і побайтова тотожність ще не доведені. `rl2blk` уже
виконує IDCT; після нього DSP отримує тільки YUV→RGB, із меншим A.

Для сценарію `B=9MB/s`, `L=500us`, `A=50us/макроблок`, `D=0`:

| Буфер у кожному напрямку | Блоків | Вхід/вихід RGB24, Б | H на блок, us | A на блок, us |
|---|---:|---:|---:|---:|
| 4096 Б | 2 | 3104/1568 | 509.56 | 50 |
| 16384 Б, ще не перевірено | 10 | 15392/7712 | 306.71 | 50 |

Це **сценарій копіювання**, не новий вимір. Оцінка190us/блок зі звіту
вже перевищує50us; збереження int32 піднімає бюджет даних. Зростання
пакета лише амортизує L. Навіть за нескінченного batch, нульових L/D/S
та9MB/s сам трафік RGB15/RGB24 коштує227.56/256us на блок.
Для блокувального виграшу за нульових інших витрат потрібні понад
40.96/46.08MB/s відповідно.

За ідеального overlap двоблоковий RGB24 batch потребує
`W>919.11us+D+S/N`, де D — час всього batch. Для десяти блоків поріг
`W>2567.11us+D+S/N`. Це може бути математично можливо, але немає
виміряних D, W, асиметричного H чи перевірки гостьової DMA/IRQ видимості.
16384 Б у кожному напрямку також не тотожні кільцю загальним обсягом
16KiB: одночасні input/output такого batch займають23104 Б без metadata.

**Вердикт:** блокувальний MDEC через поточне копіювання не окупається
за наведеної моделі. Async batch або DMM залишаються умовними кандидатами;
потрібні справжній IDCT/YUV kernel, незмінний вихід і виміри H/D/W у FMV.

## SPU

GT-профіль609 calls: весь `doSamples`965–974ms, тобто1584.56–1599.34us
на виклик у середньому та близько3.7% сцени. **Окреме mixing** оцінено
за семплюванням1:16 у225.4–230.3ms, тобто370.11–378.16us на виклик
і близько0.87–0.89% сцени. Ці інтервали
вкладені; їх не можна додавати. 3.7% не є часткою самого mix kernel.

Stereo PCM до3656 Б, з header3688 Б; проміжний int32 SSumLR до7312 Б,
з header7344 Б, більше буфера4096. Це максимальна місткість914 samples,
а не середній вихід. [Первинний SPU-звіт](<../../PS1Emulator/plans/runs/2026-09-28_gemini/n95-spustage-result.md>)
має446816 samples/609 calls:733.69 samples і2934.75 Б PCM на виклик.
За9MB/s сам **середній** PCM output коштує326.08us; maximum packet
406.22us, int32 maximum812.44us. Не можна порівнювати maximum bytes
із середнім A й цим доводити програш. Для mix-only середній output
залишає лише44–52us на вхід/L/D/setup; за сценаріюL500us блокувальний
виграш уже відсутній. Фактичний asymmetric H для цього job не виміряний.
SPU RAM512KiB треба тримати резидентно й передавати dirty ranges;
їхній обсяг невідомий.

Для повного SPU блокувальна умова `H+D+S/N<1585..1599us` може мати
ненульовий бюджет;3.7% саме по собі її не спростовує. За overlap
потрібні `S/N<A` і `W>H+D+S/N−A`. Жодного повного C55x SPU kernel чи
same-input A/B немає. Стан голосів, capture, CD mixing, IRQ та save/load
роблять передачу лише PCM недостатнім контрактом.

**Вердикт:** mix-only через копіювання не рекомендований. Повний SPU
із резидентним станом не має доведеної окупності або доведеної неможливості;
до DMM і профілю важчої звукової сцени його не переносити.

## WSOLA

Виміряний input1792/output48 Б: scalar ARM999.45us проти повного DSP
640.87/732.42us N95/E90. Попарна економія385.28/265.12us дає
create-only22/33 hops. Якщо замість попарної статистики брати різницю
загальних медіан358.58/267.03us, формула дає23/33 hops; це різні оцінки.
До поточного scalar ARM синтетичний послідовний виграш підтверджений.

ARM SMLAD135–200us — **розрахунок, не замір**. Якщо він підтвердиться,
блокувальний DSP path640–732us програє. При `N=1000` і лише create у S
ідеальна формула дає такі пороги незалежної W:

| Апарат | A=135us: W більше, us | A=200us: W більше, us |
|---|---:|---:|
| N95, старі дані без нового доступу | 513.97 | 448.97 |
| E90 | 605.98 | 540.98 |

Якщо `W>=T`, мінімальні create-only N для A135/200 становлять61/41 N95
та64/43 E90. Це умовний async-кандидат навіть проти швидкого ARM;
доказу такого W та малого ARM submission/completion часу немає.
Наступний hop залежить від попереднього offset, тому незалежно заповнити
кільце багатьма майбутніми пошуками одного аудіопотоку не можна.

**Вердикт:** зберегти доведений DSP/scalar результат, але перед вибором
інтеграції отримати фізичний ARM SMLAD A/B. DMM може змінити H; потрібні
нові asymmetric search/control runs, p95/p99/max, PCM та underrun.
За вимкненого Preserve pitch виграш дорівнює нулю.

## Що потрібно для остаточного D2

Спершу прийняти три чисті D0 RUN, потім D1 mapping/cache/ownership/ring
і повторні числа обміну. Перерахувати таблиці за фактичним H+D та повним
S, виміряти W до точки споживання результату. До цього жоден із трьох
кандидатів не має доказу прискорення всієї гри чи безпечного cancel.
Наявність незавершеного D1 не є негативним результатом про zero-copy.

ROM STRMCOPY control RUN4 на E90 дав8 exact echoes512 Б із median488us,
range457–579us, але delete−33/pending/state3. Це окрема діагностика failed
lifecycle; ці числа не підмінюють D1 H/D/B і не змінюють provisional
вердикт вище. D0 own0/3, DMM/ring16KiB досі не перевірено фізично.

RUN5 own RMS_EXIT diagnostic підтвердив get1/waits1 і перший idle обох
потоків0/pending0; усі8 checked packets мають median396us/range366–457us.
Однак delete−33/pending/state3, clean FINAL/EXIT відсутні. Це звужує D0
до останнього diagnostic reclaim/idle, execute return та native outbound
EXITACK/consumer/delete callback; воно не додає виміряного DMM H/D/B.
Тому наведені D2 числа й умовні висновки не змінено.

Після recovery RUN5 новий created-worker MSG probe зупинився до MSG/RUN
на no-input create-only delete−33/pending/state1. Це не додає packet
measurement, DMM результату або clean D0; experimental RUN лишається5.
ARM reader initial ror16 flag1 і source binding уточнено статично.
Фізичний outbound MSG і wrapper/EXITACK ще потребують перевірки.
