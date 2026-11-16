# Застосування C55x у сусідніх проєктах

Переглянуто актуальні вихідні тексти й профілі 2026-10-01. Потоковий STRM/Q15 worker
v17 пройшов на N95/E90, включно з корисним ARM CRC і чистим завершенням;
v18 додав перевірені більші пакети й вимір без CRC/Q15; v20 — actual WSOLA
з ARMv6 baseline та input1792/output48 Б. [WSOLA.md](WSOLA.md).
Нижче — оцінка кандидатів та план інтеграції; прискорення цих застосунків
ще не виміряно. Сусідні репозиторії не змінювалися.

## Що вже виміряно для каналу

8 пакетів по512 Б без повторного create; при reps0 observed completion
N95335 мкс/E90396 мкс, без ARM CRC усередині completion interval. Це issue/wait/echo,
не чистий DMA latency та не bandwidth. Reps1000 означає repeated dot240,
тобто240 тисяч MAC на packet; із передачею completion приблизно1.5–1.65 мс.
Цей синтетичний kernel не тотожний WSOLA/SPU/MDEC, і його час не слід
лінійно переносити на інший код/пам'ять/розмір порції.

У v17 N95 резервує штатний MPU режим, перевіряє100% на кожен packet;
три pairs мають S250–251/P149–151 мс. E90 S259–263/P156–160 мс.
DSP ticks у N95 однакові без doubled intervals. Скорочення wall time
близько40% стосується dot240×10000 плюс незалежний CRC, а не програм.
Три calibration runs на кожному дають~19.2 МГц за коротких пауз, але
timer на800 мс нараховує лише~501 мс цього масштабу; причина невідома.
Reported164 непридатний для conversion. Порівнювати ARM wall time.
[N95](evidence/2026-10-01/n95-worker-stream-v17-results.json),
[E90](evidence/2026-10-01/e90-worker-stream-v17-results.json).

V18 має32-byte header і перевірені512/1568/1792/2048/2304/4096-byte packets.
WSOLA1760 Б даних уміщаються в один1792-byte input; MDEC1536 Б — у1568.
На кожному телефоні три серії по32 пакети на розмір. Медіана full echo
1792 Б: N95518 мкс/E90640 мкс;1568 Б:518/610 мкс. Генерація input і
перевірка output не входять у цей interval; DSP echo і scheduling входять.
Це орієнтир `H_echo`, не вимір `H` справжнього прикладного ядра та не його
гарантована верхня межа. Умовну стару модель чотирьох512-byte packets
тепер замінюють ці прямі виміри розміру.

E90 мав1792-byte outlier7812 мкс і2048-byte7690 мкс; усі packets correct.
Причину не встановлено. Для WSOLA hop≈4.99 мс одна медіана недостатня:
потрібні queue/buffering, actual search і вимір underrun. Повна таблиця,
методика та byte-exact докази — [PACKET_SIZES.md](PACKET_SIZES.md).
WSOLA asymmetric output/search перевірено у v20. Довга/audio-сумісна робота
та MDEC asymmetric kernel лишаються наступними integration gates.

## Спільна умова окупності

Позначення: `A` — час цього самого ядра на ARM; `D` — DSP; `H` — підготовка, передавання в обох напрямках, завершення запиту та когерентність; `W` — незалежна корисна робота ARM; `S` — одноразове створення вузла; `N` — число порцій.

- Послідовний ARM: `A + W`.
- DSP з блокуванням: `H + D + W + S/N`; виграш можливий лише за `H + D + S/N < A`.
- Ідеально перекрите виконання: приблизно `max(H + D, W) + S/N`. Реальний результат треба міряти стінним часом: копіювання та кеш можуть конкурувати за шину.
- Потік має також укладатися в дедлайн порції, не лише покращувати середній час. Модель `H ≈ L + (I + O)/B` потребує окремих оцінок `L`/`B`; v18 echo не відділяє чисту transport bandwidth від driver/echo/scheduling.

Приблизно 9 мс старої порожньої create-фази входять у `S`, а не автоматично у `H`. Таблиця не підставляє вигадану швидкість каналу.

## PS1Emulator

Шляхи нижче відносні до `../PS1Emulator/`.

| Стадія | Конкретний код і дані | Придатність / межа |
|---|---|---|
| WSOLA correlation | `src/symbian/snd_symbian.cpp:WsolaBestOffset`, `CSymSnd::WsolaFeed` | Перевірений перший DSP-кандидат: exact signed16 coarse/refine search зі signed32 сумою. ARM залишає вибір вікна, overlap-add, чергу динаміка. Працює лише за ввімкненого WSOLA; application audio gain ще потрібний. |
| SPU voices / interpolation / mixing | `pcsx_rearmed/plugins/dfsound/spu.c:decode_block_data`, `do_samples_adpcm`, `do_channel_work`, `queue_channel_work`, `sync_worker_thread` | Регулярна fixed-point робота, але залежить від 24 каналів, SPU RAM, ADSR, noise/FMod, IRQ і регістрів. Потрібен постійний стан на DSP та передавання лише змін. |
| MDEC | `pcsx_rearmed/libpcsxcore/mdec.c:rl2blk`, `idct`, `yuv2rgb15`, `yuv2rgb24`, `psxDma1` | Другий кандидат для FMV: пакет макроблоків. Не є універсальним прискоренням 3D; у GT/Crash без FMV MDEC може не працювати. Потрібна тотожність округлення та часткового DMA. |
| GTE | `pcsx_rearmed/libpcsxcore/gte.c`, `gte_arm.S`, виклики динарека | Поганий перший кандидат: багато дрібних операцій зі швидким споживанням результатів MIPS, прапорами й широкими проміжними значеннями. Без перебудови планування ціна синхронізації переважає коротку математику. |
| GPU raster | `pcsx_rearmed/plugins/gpu_unai/gpulib_if.cpp` та scanline kernels | Велика мішень за профілем і залежністю від частоти ARM. Досліджувати пакет команд із резидентними даними або узгодженим mapping; короткі окремі спани не окупають обмін. Швидкість C55x на справжньому raster kernel ще не виміряна. |

### Перший інтеграційний експеримент: WSOLA

Поточні `KWsolaHop=220`, `KWsolaRange=441`, частота 44100 Гц. Алгоритм оцінює лише лівий канал, після арифметичного `>>6`; грубий крок 4 і уточнення поблизу найкращого зсуву. Для одного пошуку достатньо передати 220 значень шаблону та 660 значень пошукової області: **1760 байтів**, повернути зсув і score. Це 25080 або25740 MAC; точну кількість визначає край області. Синтезний hop — приблизно **4.99 мс**. Шаблон наступного hop залежить від результату попереднього: незалежно відправити кілька послідовних пошуків одного аудіопотоку не можна. Черга буферизує PCM та дозволяє ARM виконувати іншу роботу, поки один пошук очікує completion.

Важливо зберегти арифметичне зсування від'ємних значень, обмеження 32-бітної суми, порядок проходів і вибір першого максимуму (`>`). Тестувати також тишу, однакові scores, краї 0/440, мінімальні/максимальні семпли й зміну швидкості. Формат транспортного пакета має бути явно серіалізований, без передачі ARM `struct` на C55x, де `char`/`int` мають 16 біт.

Пошук/offset/score/count/input checksum і короткий output перевірено у v20.
ARMv6 median999 мкс, DSP end-to-end641/732 мкс; create-only модель окупається
після22/33 hops. Це synthetic vectors, не recorded audio scene. Далі safe
error/cancel audit, queued integration біля `WsolaFeed`, черговані application
ARM/DSP прогони з однаковим PCM, underrun/tail latency і кінцевий PCM.
Поза deadline або окупністю залишити ARM. Методика й limits — WSOLA.md.

### SPU: вже є форма для worker, але інший DSP

`spu.c` має умовний worker із чотирма `work_item`; `do_channel_work` відділений від завершення на ARM. Це добрий зразок межі задачі. `spu_c64x.c` і `spu_c64x_dspcode.c` — **C64x**, інші syscall/cache/типи; їхній бінарник і адреси для C55x непридатні. У поточній Symbian-оболонці звук створюється без цього worker, `iUseReverb=0`, `iUseInterpolation=0`; звичайна гаусова інтерполяція не є автоматично наявним великим навантаженням.

`NSSIZE=((44100/50+32)&~1)=914`; стерео PCM 16 біт — до 3656 Б на порцію; проміжний `SSumLR` із 32-бітними сумами — 7312 Б. SPU RAM — 512 KiB: повна копія за кожної порції неприйнятна, потрібні dirty ranges або узгоджений mapping. Синхронізація обов'язкова на DMA/регістрових зверненнях, IRQ, load/save state, CD mixing та зміні reverb.

Історичний фізичний профіль від 2026-09-23 (`plans/reports/second-opinion-omap2420-2026-09-22.md`, секція B2, журнали `plans/runs/2026-09-23_spucore_xa_n95/`) містить 4177 активних викликів і 1 769 816 семплів; центральний інтервал 1263 мс — у середньому **0.302 мс на активний виклик**. Це не новий A/B і не час окремого voice kernel, але показує, наскільки малим має бути `H`. `SPUasync=2177 мс` включає іншу/перекриту роботу; інтервали не додаються.

Новіший GT-профіль N95 від 2026-09-28: повний `doSamples` у контролі 965/968 мс
на 600 кадрів, у профільованій збірці 973/974 мс; 609 calls і 446816 output
frames. Стадії семпльовані 1/16: ADPCM 642–646 мс, mix 225–230 мс,
ADSR 17–20 мс. Сирі дані: `plans/runs/2026-09-28_gemini/n95-spustage/`;
методика: `spu-fusion-decision.md`. ADPCM-таймер охоплює вибраний шлях
генерації семплів; поточний `iUseInterpolation=0`, тому називати ці 642 мс
вартістю гаусової інтерполяції неправильно. Усі стадії вже входять у
`doSamples`. Повний мікшер — близько 3.7% цього приблизно 25.8-секундного прогону:
це стеля усунення його ARM-часу, ще без DSP/transfer costs. Один запит на
голос буде надто дрібним; потрібен блок усіх активних голосів із постійним
станом. Для важчої сцени або ввімкненої якісної інтерполяції пріоритет може
бути іншим; приріст на них не виміряно.

### MDEC: формат і порядок

Макроблок 16×16 складається з шести IDCT-блоків 8×8 (Cr, Cb, чотири Y). Масив із 384 32-бітних значень — **1536 Б**; вихід RGB15 — **512 Б**, RGB24 — **768 Б**. Нинішній `rl2blk` уже виконує `idct` для кожного підблока: передавання його готового результату виносить лише YUV→RGB. Для DSP IDCT+YUV потрібна нова межа після RLE/dequantization, перед IDCT; менший потік — RLE 16 біт плюс одноразова quantization table, з усім `rl2blk/idct` на DSP. Для варіанта з384 int32 і32-byte header у кожному напрямку це input1568/output544 або800 Б, сумарно2112/2368 Б. V18 вимірює симетричний echo1568/1568, а не цей асиметричний обмін; час kernel ще потрібний. Зменшувати коефіцієнти до16 біт без перевірки всіх діапазонів і округлення не можна.

Для кадру 320×240 потрібно 300 макроблоків: сам вихід 153600/230400 Б. Пакетувати кілька блоків і міряти FMV-сцену. Зберегти `mdec.block_buffer_pos`, неповний останній DMA, endian/saturation, прапор STP й відкладений DMA interrupt. GTE/GPU виграші з інших сцен не додаються до MDEC.

### Ділянки, чутливі до частоти ядра: що справді доводять заміри

Джерело: `docs/measurements/f1-core-vs-memory-2026-09-19.md`, завершена
серія A/D від 2026-09-20 й C від 2026-09-21. Той самий EXE, GT 7700→8300,
600 кадрів, window output, `nosnd` (SPU при цьому виконується); три
черговані A/D. Шина A/D 165.12 МГц; ARM 330.24/165.12 МГц. Середні:

| Профільний інтервал | ARM330, мс | ARM165, мс |
|---|---:|---:|
| total |25010|45550|
| emu |22047|40512|
| gpuRaster |10484|19700|

У C ARM 330.24/шина 82.56 МГц: `emu=26486`, `gpuRaster=11959` мс, один
прогін. Це підтверджує сильну чутливість raster path до ARM та окремий
вплив пам'яті. Модель ~84%/88% роботи за частотою ARM для emu/raster —
двоточкова оцінка, а не незалежна карта фізичних stalls чи прогноз DSP.
`gpuRaster` включає command/DMA API, setup і raster; він уже входить у
`emu`. Попередню тезу «растеризатор переважно обмежений шиною» ці виміри
не підтримують. Окремий огляд меж моделей: звіт
`plans/reports/second-opinion-omap2420-2026-09-22.md`, §3.

Для поточного вибору конкретного kernel корисніші CF-профілі від 23 вересня:
GT CF000/02b ~577/347 мс; Crash CF0c1 ~1908–1929 мс,
CF0a3 ~863–880 мс на 600 кадрів. Це інклюзивні семпльовані оцінки polygon
setup+spans із залишковим збуренням ~0.3 с у Crash. WipEout майже цілком
використовує наявні ARM ASM spans. Див. `work/state.md`, O2,
та `plans/runs/2026-09-23_cftime_sampled_*_n95/`.

Для GPU пропонована межа DSP-job — група команд у початковому порядку,
або кілька довгих спанів із усіма потрібними texels/CLUT/destination tiles.
Внутрішній pixel loop має 32-бітні texture gradients, clipping, 15-бітні
кольори, mask і blending; швидкість dot/MAC не характеризує цю роботу.
Потрібен captured-command/spans benchmark проти поточного ARM ASM/C++
із побайтовим збігом VRAM, включно з цілочисельним округленням. Потім —
резидентні VRAM tiles/dirty updates або verified shared mapping та бар'єри
на CPU/DMA читанні/записі VRAM, texture read-after-write, frame present,
save/load. Поточний `renderer_flush_queues` порожній, тож готового
асинхронного контракту в цьому renderer немає. Передавати 1 MiB VRAM
на кожен кадр через нинішні 4096-byte буфери недоцільно. C55x GPU-виграш
лишається гіпотезою з великим потенційним бюджетом і складною інтеграцією.

Гостьовий R3000A/динарек і GTE також чутливі до швидкості ARM. Динарек
генерує ARM instructions і працює з RAM, регістрами, interrupt/SMC state;
його виконання на C55x означало б новий backend/порт, а не готовий DSP-job.
GTE змінює CP2 registers/flags, а динарек одразу споживає результати й
обліковує `gteBusyCycle`. Винесення одного RTPS/RTPT/MAC виклику на канал
із сотнями мікросекунд completion не має обґрунтованої окупності. Перевірка
багатьох залежностей і пакетування вимагали б окремого редизайну.

`vout_symbian.cpp:blitCurrent` має box downscale, `FxaaPixel`, BGR555→565/8888
і RGB24 conversion. Регулярні image kernels можливі, але готовий кадр
великий, DSA/WS/GL present залишаються на ARM, а 1:1 conversion уже має
ручні ARM loops. Досліджувати DSP тут після mapping або для виміряної
дорогої фільтрації; час `blitPresent` не приписувати обчисленням конвертора.

За практичним порядком: WSOLA integration; MDEC на FMV або GPU batch
benchmark за ціллю сцени; SPU на важкому аудіопрофілі. WSOLA при типовому
вимкненому Preserve pitch не прискорить гру. Старе A/B повного WSOLA
23228→28616 мс (+23.2% на N95) містить crossfade, копіювання та зміну
робочого набору; kernel-дельта v20 не усуває автоматично всі ці 23.2%.
Після search-only можна окремо перевірити повний послідовний WSOLA на
DSP із резидентним tail/input state, якщо ARM copy/overlap-add домінують.

## ModernBrowser

Шляхи відносні до `../ModernBrowser/`.

| Стадія | Поточна реалізація | Рішення |
|---|---|---|
| JPEG/GIF/BMP decode | `stage0/nsrun/src/nsjpeg.c:nsjpeg_decode`, `symbian_icl.cpp:DecodeFrame/RunJob` | Уже використовує системний Image Conversion Library. Не писати другий JPEG-декодер лише заради DSP. Чи конкретний codec використовує DSP, з цього API не видно. |
| PNG | `stage0/nsrun/src/nspng.c:nspng_decode`, lodepng | Inflate і фільтри зі змінними гілками та 8-бітними даними; C55x потребує обережного упакування байтів. Спершу профіль decode/filter/copy окремо. Перший кандидат — рядковий filter або перетворення кольору, якщо вони домінують. |
| Масштабування / YUV→RGB / audio resampling | Майбутній власний media handler | Регулярні kernels придатні; спершу перевіряти штатний MMF/codec шлях. Наявність `<audio>/<video>` і вимір продуктивності власного медіаконвеєра тут не встановлені. |
| JS, DOM, CSS/layout, HTTP/TLS automata | QuickJS, NetSurf, `http_fetcher.c`, `symbian_socket.cpp`, `symbian_tls.c` | Залишити на ARM: вказівники, динамічна пам'ять, часті зв'язки зі станом UI/мережі. Окрему математику TLS можна відділити, див. нижче. |
| TLS ECDHE / public-key math | BearSSL, `macTLS/os9/ostls_tls13_handshake.c:tls13_generate_keypair/tls13_ecdh_shared` | Перспективний дослід: ціла scalar multiplication одним job, малий вхід/вихід. Є `ec_c25519_i15.c` і `i15_montmul.c`; окремого ARM/DSP часу ще немає. |

PNG наразі синхронно декодує повне джерело в `data_complete`, потім копіює RGBA рядками, конвертує формат і перевіряє opacity. Навіть зображення 320×240 дає **307200 Б** RGBA. Окремий ARM worker може прибрати затримку UI раніше, ніж стане доступним ефективний DSP mapping.

ICL уже має окремий `RThread` зі своїм scheduler, але `RunJob` **чекає** `thread.Logon` через `User::WaitForRequest`; це ізоляція decoder, а не перекриття роботи UI. Для справжньої фонової обробки потрібні job queue, completion у головному scheduler, lifetime джерела й bitmap, cancel при закритті сторінки; виклики NetSurf лишаються у його потоці. Аналогічно DSP completion має належати окремому active object. Не вводити вкладений scheduler у головному потоці: код socket/ICL уже документує stray-signal помилки.

### Виміряні вузькі місця браузера й нові кандидати

Актуальний `docs/state.md` завершується станом від 19 вересня; джерела
переглянуто 1 жовтня (main `c99c542`). Розвідка не переносить показники
інших браузерів/ПК на цей застосунок.

* CSS cascade `t-large`, N95: 4.259/4.264 с із ранньою відмовою для вузлів
  без атрибутів, 4.430/4.421 с без неї. Це парні виміри при штатному
  тактуванні. `libcss/src/select/css_select.c` працює з DOM callbacks,
  node data, arena/interning і computed styles. Найдорожча виміряна
  ділянка завантаження має слабку форму для C55x: серіалізація вузлів і
  часті completion не розв'язують її. Подальший ARM-напрям — reuse/shared
  computed styles та зменшення per-node роботи. Стару розбивку init/share/
  create на розігнаному апараті потрібно переміряти перед кількісними
  висновками; JS і layout не мають нового доказу DSP-придатності.
* E90 scroll benchmark 60 steps: ~31.2 мс/step; paint 151.5 мс і upload 64.4 мс
  на серію, present 866.7 мс (~14.4 мс/step). `draw_us` вже включає present,
  додавати їх не можна. DSP image kernel не прибере EGL/драйверний present.
  У N95 вже є GL tile ring; старе «4 мс на32×32 upload» не є чинним
  універсальним bandwidth: `state.md` розрізняє upload у щойно використану
  й давно не використану текстуру.
* HTTP gzip на N95: 38982→146904 Б за 53.0 мс і 116875→422279 Б за 171.8 мс.
  `http_fetcher.c:send_body` вимірює `macos9_gunzip_push` разом із
  `deliver_body` callback. Це верхня межа ізольованого inflate, а не його
  чистий час. Декодер — resumable Huffman/LZ77 state machine з 32 KiB byte
  history, не MAC-heavy kernel. Можливий резидентний chunk worker, але
  ARM delivery/parse залишаються; спершу потрібні окремі counters та
  end-to-end перевірка. На C55x байти слід явно пакувати через 16-бітний
  `char`, включно з window, checksum і chunk boundaries.
* PNG decode/filter/format conversion та `symbian_gfx.cpp:sgfx_bitmap`
  копіюють source image й формують alpha mask; масштабування нині робить
  `CFbsBitGc::DrawBitmap/DrawBitmapMasked`. Пакет DSP варто формувати як
  image operation або рядковий strip і кешувати результат під display
  size. Корисний результат — готовий RGB565 та потрібна alpha, менше
  повторних copies/repaints. Лише RGBA→RGB565 з повним input/output
  через copy stream може коштувати більше за ARM; first gate — окремий
  profile decode/unfilter/scale/copy та дані конкретної картинки.

Нова компактна математична мішень — X25519/ECDHE. Обидві точки інтеграції
в TLS 1.3 уже викликають `br_ec_get_default()`. Поточний ARM default обирає
m31 за відсутності `BR_LOMUL`; коментар про m15 у handshake не означає,
що саме m15 зараз виконується. Для C55x є окремий i15 варіант: 15-бітні
limbs у `uint16_t`, 32-бітні добутки/carries та Montgomery multiplication.
Private scalar і point для X25519 — по 32 октети; результат 32 октети.
Варто віддати **цілу** scalar multiplication, залишивши її внутрішні
field multiplies на DSP. Запит на кожне `br_i15_montymul` був би надто
дрібним. Перетворення serialized octets і контроль unsigned widths
обов'язкові; це не пряме компілювання ARM-коду з його 8-бітним `char`.

Це кандидат, а не виміряний виграш: зафіксовані 1.00/1.27 с live TLS handshake
на N95/E90 містять мережу, certificate processing і socket pump. Перший
дослід — ARM counters keypair/shared-secret/certificate verify, потім
DSP X25519 на публічних test vectors із exact result, коректною обробкою
invalid/all-zero результатів, constant-time code review та очищенням
секретних buffers. Виміряти повний job разом із session start; перше
коротке з'єднання не може ігнорувати startup. RSA/ECDSA перевірку можна
дослідити окремо, якщо її бюджет буде значним. Мережевий автомат,
перевірка сертифікатів і TLS policy залишаються у браузері.

## Послідовність інтеграції після апаратного гейта

1. Echo v18 до4096 Б та WSOLA asymmetric1792/48 v20, correct results/stop/cleanup підтверджені. Native allocation4096 Б;16384 Б не підтримується прототипом і не перевірено.
2. WSOLA scalar kernel пройшов exact ARM/Python comparison і три pairs на обох. Useful ARM overlap доведено окремим v17 dot+CRC. Application queue/error/cancel/audio/underrun/tail latency — наступний integration gate.
3. MDEC пакет макроблоків для FMV або captured GPU batch benchmark для 3D; SPU worker з dirty RAM за значного аудіобюджету. Вибір за профілем конкретної сцени.
4. Browser: окремі counters TLS math і image stages, asynchronous job queue; DSP X25519/image kernel лише за виміряної окупності. GPU present/CSS budgets оцінювати окремо.
5. Відмова/timeout DSP завжди повертає виконання на ARM після безпечного очищення; save/load/exit зупиняють worker. Відсутність каналу лишає інтеграцію експериментальною.
