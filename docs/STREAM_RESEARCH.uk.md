# Потоковий канал ARM–C55x: дослідження 2026-09-30

## Нове доручення D0–D2, 2026-10-01

Актуальний [E90 lifecycle/DMM audit](LIFECYCLE_DMM_2026-10-01.md):
failed delete не є захистом від unload; cancel rc0 вимагає окремого
завершення transfer status. Host21 утримує невизначену сесію до ручного
reboot, supervisor не надсилає KILL. Generic RUN-stop candidate зібрано,
але три чисті official RUN ще не перевірені; потрібен фізичний SIS install.
DMM ordinals уточнено: reserve27/map31/unmap34/unreserve28. Mapping,
ring16KiB та bandwidth не виміряні. N95 не опитувався. Проміжне
[рішення PS1](PS1_CANDIDATES_2026-10-01.md) використовує старі v18/v20
виміри й окремо позначені сценарії. Нижче збережено історію дослідження.

## Межа доказів

Нижче наведено статичний розбір штатного ROM RM-320 і нові апаратні результати. На N95 власний вузол передав 8 правильних пакетів за один create/RUN, але повне очищення завершилося помилкою. Паралельне прискорення ще не виміряне. Старі аварії повідомлень не доводять відсутності інших каналів. Приблизно 9 мс зі старої `CHARACTERIZATION.md` стосуються створення порожнього вузла, а не передавання порції довгоживучому вузлу.

## Встановлені контракти RM-320

Інструменти: `tools/rev/exports.py`, `fn.py`, `words.py`; ARM для `ehwa.ldd`/`ehwaomap.pdd`, Thumb для функцій `bal.dll`/`bridgeapi.dll` з непарними експортами. `fn.py` тепер використовує окремий тимчасовий файл для кожного процесу: попередні паралельні розбори зі спільним `_fn.bin` відкинуто.

| Операція | Джерело | Що встановлено |
|---|---|---|
| Створення задачі / вузла | `bal.dll:80A41DDC`, існуючий хост | `Ctl(4, raw32, &handle)`; SDK `TBuf8<20>` має лише 28 Б, потім `Ctl(5, handle, &status)` і завершення статусу |
| Запуск execute | `bal.dll:80A41976`, LDD `801B4294`, PDD `801A1404` | `0x08000007`; PDD virtual slot +32; окремий запуск після create |
| Завершення / видалення | `bal.dll:80A41F4C`, LDD `801B5118`, PDD `801A25C4/801A2374` | `Ctl(6, handle, &status)`; у running-гілці при PDD node+440=0 надсилає RMS_EXIT, ACK запускає delete; після успіху `Ctl(7)` звільняє host task |
| ARM → DSP | `bal.dll` ord6 `80A41863`, LDD `801B4988/801B4478`, PDD `801A1A90` | `0x0800000E`, 28-байтовий пакет; PDD slot +60 |
| DSP → ARM | `bal.dll` ord5 `80A418BF`, ті самі LDD-функції, PDD `801A1890` | `0x08000010`, той самий пакет; PDD slot +52 |
| Скасування потоків | `bal.dll:80A41AD9/80A41AEB` | task15/task17; аргумент індексу потоку треба зберегти |
| Буфери | `balbuffers.dll:80A42408`, bridgeapi ord30 `80A5D87F` | штатний клієнт просить округлений до 4 KiB буфер у режимі 2; існує й режим 0 через `User::Alloc` |

Пакет потокової операції копіюється LDD через `ThreadRawRead(..., 28)`. Перші три слова — представлення `TPtr8` (тип/довжина, максимальна довжина, адреса), далі адреса `TRequestStatus`, довжина даних, додатковий аргумент і індекс потоку. `bal.dll:80A41F2C` копіює ці сім слів. Вхідний PDD використовує довжину, а обидва напрямки використовують статус та індекс. Остаточне значення додаткового аргументу і поведінку завершення треба перевірити перед тестом.

Таблиця virtual methods DNode знайдена через RTTI `801B397C`, посилання `801B3DE4`, початок `801B3DE8`. Це незалежно пов'язує LDD з потрібними PDD-функціями; назва довільного файлу дизасемблера доказом операції не є.

`bridgeapi` ord3 задає 176-байтову структуру потоку **за значенням**, а не вказівником: індекс у r1, напрямок у r2, перше слово структури у r3, решта на стеку (`80A5E68E/80A5E064`). Внутрішні описи потоків: input +184, output +1592 від props; до восьми кожного, крок 176. Початковий опис не містить придатного розміру буфера; перед create його треба заповнити.

У ROM є динамічний `STRMCOPY_TI`: `system/apps/strmcopy/strmcopydyn.dll55l`, UUID `7EEB2C7E_785A_11D4_A650_00C04F0C04F3`, один вхід та один вихід. Це приклад вузла, не базовий образ процесора. Його `.dof55l` не слід передавати PROC-load замість `baseimage.dof`.

## Кандидати та порядок перевірки

1. Штатні host streams: власний TASK-вузол з одним входом/виходом, налаштовані props, один create/run, передавання багатьох пакетів через task14/task16. Найсильніший кандидат: його використовує production `bal.dll`.
2. Нативні буфери та DSP mapping: розібрати ord30 і `dspmemmapper` разом з cache maintenance `ebridgeutil`; підтвердити адресування DSP у 16-бітних словах і власника буфера. Сам факт виділення ARM-буфера не доводить доступу DSP.
3. Спільний кільцевий буфер: можливий після доказу mapping, когерентності й notify; не використовувати вгадану фізичну адресу.
4. DSP/BIOS worker через `TSK_create`/`SEM`: альтернативний спосіб довгоживучого виконання, але без зворотного каналу не дає потокового прототипу.
5. Повідомлення: старі небезпечні спроби зберегти як негативні результати конкретних аргументів. Повторювати лише після нового повного контракту.

Для зіставлення використано первинні вихідні тексти [TI Bridge node.c](https://android.googlesource.com/kernel/common/+/f761237eee55222fdb509c79e784a67ab3d72cbd/drivers/staging/tidspbridge/rmgr/node.c), [Linux v2.6.37 tidspbridge](https://github.com/torvalds/linux/tree/v2.6.37/drivers/staging/tidspbridge) та [оригінальний dsp-dummy](https://github.com/felipec/dsp-dummy). Їхня Linux ABI не переноситься на Symbian.

## Нові читання апаратів

- N95: INFO 320×240; live `bridgeapi.dll` прочитано через daemon, 20544 байти, code `80A5D458`. Read-only `ocprobe patcher dsp 1` завершився `EXIT 0 Kill`: поточний multiplier 111, DSP divider 3 (`CM_CLKSEL_DSP=000023C3`), отже DSP 284160 kHz за поточним DPLL. У старому ocprobe рядок «firmware math» використовує **stock** CORE й не є частотою цього прогону.
- E90: INFO 800×352; read-only clock probe завершився `EXIT 0 Kill`, profile RA-6 400.34.93, divider 3 (`00000343`), без повідомлення NOT STOCK. Пряме читання `Z:\sys\bin\bridgeapi.dll` демоном відхилено `-46`; так само STAT у `sys\bin`. Це межа дозволів демона, а не відсутність DSP.
- Обидва попередні `E:\ocprobe.log` збережено в `work/device-backups`; DSP-хост/вузол ще не замінювалися. Нові журнали — `work/evidence/{n95,e90}/clock-before.log`.

Це початкові читання сесії. Пізніші результати й зміни наведені нижче.

## TI STRM ABI та контекст фаз

Первинне джерело: локальна копія [TI userspace-dspbridge](https://github.com/kpykc/userspace-dspbridge),
коміт `342b027b642eed909e232b2bc1fa144fb0a94c8c`; `strm.h`, `rms_sh.h`,
`rmsdefs.h`, `node.h` і `source/samples/dsp/strmcopy{Create,Execute,Delete}.c`.
Firmware `STRMCOPY_TI` додатково звірено через `DLLdump` та `dis55`.

- `RMS_STATUS` / розміри STRM — 32-бітний `long`; на C55x `char`/`short`/`int`
  мають 16 біт, а MAU потоку — 16-бітне слово. 256 MAU = 512 ARM-байтів.
- `RMS_StrmDef`: п'ять 32-бітних слів size/nbufs/segid/align/timeout, потім
  ім'я з 16-бітних символів. `STRM_Attrs`: чотири 16-бітних поля
  nbufs/segid/align/timeout. `STRM_INPUT=0`, `STRM_OUTPUT=1`.
- `STRM_issue(stream, ptr, datasize, bufsize, arg)` передає власність буфера;
  reclaim дозволено лише після issue. `STRM_reclaim(..., NULL, ...)` для
  необов'язкового pbufsize прямо дозволено TI й використано firmware-вузлом.
- Штатний execute спершу issue input, потім `NODE_wait`, а reclaim output
  виконує лише після попереднього issue output. Конкретні таймаути й очищення
  треба перевіряти в стані живого вузла.
- Firmware зберігає контекст у `env->moreEnv` за зсувом **12 C55x-слів**;
  create виділяє його через `MEM_valloc`, execute/delete дістають його звідти.
  Новий прототип відтворює це та має compile-time перевірку зсуву. Попередній
  варіант з фазовими static/BSS-полями збережений в історії результатів.

## Апаратний журнал N95

Профіль: RM-320, `V 35.0.001 / 11-11-09`, MachineUid `20002D84`.
Усі 39 експортів та початок внутрішнього DCD parser звіряються до драйверних
викликів. Час ARM FastCounter має роздільність 1/32768 с (~30,5 мкс).

| Дослід | Результат | Доказ |
|---|---|---|
| Перший base load, початковий стан m111/div3 | Перезапуск, останній запис BEGIN base load | локальний `stream-create-first.log`, відповідь користувача |
| Base-only після перезапуску, stock m86/div3 | base load=0, close, FINAL=0 | [base stock](evidence/2026-09-30/n95-stream-base-stock.txt) |
| Вузол з 1 input / 1 output: create/delete | create=0, 5584 мкс; delete=0; FINAL=0 | [create stock](evidence/2026-09-30/n95-stream-create-stock.txt) |
| Перший execute, phase-local BSS | Перезапуск, останній запис BEGIN execute | [first execute](evidence/2026-09-30/n95-stream-echo-recovered.txt) |
| Execute-smoke: три DSP-інструкції return RMS_EOK, без STRM | RUN=0/status=0; delete timeout −33; телефон лишився доступним | [smoke](evidence/2026-09-30/n95-stream-execute-smoke.txt) |
| `env->moreEnv` + NODE_wait: create/delete | create=0, 7415 мкс; delete=0; free task=0; FINAL=0 | [context create](evidence/2026-09-30/n95-stream-context-create.txt) |
| Той самий вузол, перший пакет, reps=0 | RUN=0/status=0; put/get status −2; 18585 мкс; журнал обривається на BEGIN delete | [context first packet](evidence/2026-09-30/n95-stream-context-echo-recovered.txt) |

Вимір першого пакета вище **не є** затримкою успішного потокового обміну.
Пізніший успішний обмін наведений нижче. Одночасна корисна робота двох
процесорів і виграш у часі ще не доведені.
Зміни контексту й NODE_wait внесені разом; один прогін не встановлює, яка з
них усунула ранню відмову. Стоковий base load після попереднього перезапуску
не доводить, що причиною першої аварії був саме overclock.

Smoke DSP SHA-256: `9BB4672A3FC0AB8FC40D85ACC264B39C189CE7EE115B4F652E46A38E1C3F0287`.
Context DSP: `BFF843C2BA3FEA82A643A2654D8DAF5E7FBEFCC0134D5CFB8119CB70F0A157BE`.
Host context build: `224D206F609D427B04C01B02FA169B7D8CE790862C05B36C18A079C25A699E3E`.
Журнали збірок — `out/stream-{dsp,arm}-*-build.log`; повторна збірка змінює артефакти.

### Host connection і перші 8 пакетів

PDD `8019FF5C` створює host stream лише коли поле props **+24 = 0**.
Функція `8019FB58` для цього режиму створює внутрішній connection kind 2.
Початкове DCD значення 1 означає device connection й не створює потрібних
host stream objects. У v6 поле attr[6] виправлено на 0 для обох напрямків.
Окремий create/delete з цими props дав FINAL=0:
[create v6](evidence/2026-09-30/n95-stream-host-connect-create-v6.txt).

У [serial reps=0 v6](evidence/2026-09-30/n95-stream-host-echo-v6.txt) один
create (7446 мкс) і RUN обробили 8 пакетів по 256 C55x-слів. Усі put/get
статуси 0, errors=0; порядкові номери, довжини й усі 240 слів перетворення
збіглися з ARM-еталоном. CRC 64 KiB ARM-роботи щоразу `CD837CD0`.
Reps=0 не перевіряє ненульове Q15-обчислення.

Frames 1–7: wall 17486–18127 мкс; frame 8: 345275 мкс;
STREAM PASS total=468868 мкс. Цей wall включає послідовний CRC, тому він
**не є** виміром затримки передачі. State перед delete=3; delete/status=−2,
FINAL/EXIT=−2. Телефон після цієї спроби був доступний. DSP цього прогону:
SHA-256 `45F877E2A18B392DF8E9EBA2DCE2947B148FD6B9E9AEE408DB3012CA6FD79873`.

Наступний DSP-варіант переніс idle перед reclaim останнього output.
[Транспортний журнал](evidence/2026-09-30/n95-stream-final-idle-transport.txt)
обривається таймаутом PS після START. Журнал телефона ще не прочитано;
факт автоматичного перезапуску й точне місце відмови не встановлені.

### Штатний RMS lifecycle: статичний доказ і v7

Контроль каналу 6 проходить через LDD `801B5118` у PDD slot +92
(`801A25C4`). Для running state=2 при node+440=0 `801A2374` надсилає `{RMS_EXIT=80000000,
arg1=nodeEnv}`; PDD `8019B1AC` приймає RMS_EXITACK=40000000 і викликає
`801A2220`, який запускає фазу delete. Це вже наявний шлях контролю 6.
Поле node+440 копіюється з processor+64 (`801A0344`, getter `8019F28C`),
а processor+64 — з конфігурації +588 (`8019EE68`). При ненульовому полі
викликається інший шлях `801A3DF4`; значення й повний контракт цього
варіанта ще уточнюються. Сам факт control 6 не доводить доставку RMS_EXIT.

DSP/BIOS task wrapper `24E6F0` викликає execute з nodeEnv, потім формує
`{40000000, returned_status, 0}` і викликає NODE_putMsg з destination=NULL
та timeout=FOREVER. Отже, штатна обгортка вже надсилає EXITACK після
повернення execute. Ручне додавання ACK потребує окремого обґрунтування.

State=3 не можна зараховувати як успішне завершення: PDD `801A2D2C`
ставить його, зокрема, при відмові процесора (`8019DAD8`). V6 return після
in-band stop обходив очікування RMS_EXIT; причинний зв'язок із конкретною
аварією ще потребує апаратного підтвердження.

V7 повторно issue input після кожного frame, включно з останнім,
чекає RMS_EXIT у NODE_wait/getMsg, потім idle/reclaim outstanding buffers.
Host чекає контроль 6 і лише після успіху звільняє host task. Native free
не викликається, якщо transfer status лишився pending. У packet є версія
протоколу 7, host перевіряє її та останній marker. Додано окремі ARM CRC,
issue, wait і спостережений completion час; паралельний completion час
включає ARM-роботу й не є точним моментом закінчення DSP.

V7 ARM/DSP зібрані й частково перевірені на апаратах. E90 мінімальний
звичайний execute без host frames підтвердив RUN=0/status=0, але control 6
лишив deleteStatus pending і дав FINAL/EXIT=−33. N95 окремий RMS-only
execute має такий самий результат; подробиці нижче. Serial/parallel
залишаються до перевірки чистого завершення.

### Відновлений N95 та RMS-only ізоляція

Два повні сканування 192.168.3.1–254 на TCP 2323 спочатку знайшли лише E90.
Користувач повідомив, що N95 був в іншій підмережі. Після виправлення
N95 за `.22` відповів INFO 320×240. До нових запусків c55stream збережено
старий EXE/hash, DLL і [журнал idle-first](evidence/2026-09-30/n95-stream-idle-first-recovered.txt).
Цей журнал v6 має 7 правильних frames, останній запис — frame=7;
frame=8, delete і FINAL відсутні. Це окрема спроба, вона не замінює
попередній доказ 8 frames з delete −2. Прочитаний DLL — 3644 Б,
SHA-256 `EC11FC17EB22B8B9539BCFB8C109A7F4A362D11C438714A0383AD351764911BF`.

NODE_getMsg `24D790` повертає BOOL=1 після копіювання трьох long;
NODE_wait, NODE_getMsg, RMS_executeNode і task wrapper побайтово тотожні
у common-code N95/E90, хоча вся секція відрізняється у 116 байтах.
[Доказ порівняння](evidence/2026-09-30/n95-e90-dsp-rms-code-comparison.json)
отримано з 64 DOFF packets із 12-байтовими заголовками.

Варіант `build_stream_node.cmd rms` повторює PING-підхід TI: execute
лише чекає RMS_EXIT через NODE_getMsg; межа — 100×100 мс. Create/delete
все ще створюють і звільняють звичайні stream objects, але execute не
викликає issue/wait/idle/reclaim. Host v7, SHA-1 loader hash і DLL 2700 Б
прочитані назад та зіставлені побайтово до тесту.

- [Create/delete](evidence/2026-09-30/n95-stream-create-v7-rms-wait.txt):
  create=8361 мкс, delete/free task=0, EXIT/FINAL=0.
- [Execute](evidence/2026-09-30/n95-stream-execute-v7-rms-wait.txt):
  RUN=0/status=0, state=2; delete=−33/status=pending, FINAL/EXIT=−33.
  [Транспорт](evidence/2026-09-30/n95-stream-execute-v7-rms-wait-transport.txt)
  підтверджує доступність N95 після завершення host process.
- [Read-only clock](evidence/2026-09-30/n95-clock-before-v7-rms-wait.txt):
  stock m86, DSP divider 3, firmware math 220160 kHz;
  HAL ARM ECPUSpeed=206438 kHz у момент проби. Це не вимір overlap.
- [Оригінальний ocprobe.log](evidence/2026-09-30/n95-restored-original-ocprobe.json)
  1259 Б відновлено й перевірено побайтово. Після ізоляції на телефон
  повернуто звичайний v7 DLL 3668 Б із SHA-256
  `5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9`;
  його execute на N95 ще не запускався.

Невдача RMS-only не залежить від STRM-операцій у його execute. Вона ще
не визначає, чи загублено exit request, повернення execute або ACK;
наступний контракт має розрізнити ці випадки.

Повідомлення залишаються окремим кандидатом: LDD task20 `801B44F0`
читає 8-байтову пару `{status*, record*}`. PDD `801A1D58` читає **24 сирих
байти** record, у якому header/max займають 8 байтів і далі cmd/arg1/arg2.
Get-info task2 копіює 112 байтів; nodeEnv — data offset 64
(`801A11F0`). Ці контракти встановлені статично, не перевірені новим
апаратним messaging-тестом. SDK TBuf8<12> (20 Б) і TBuf8<104> (112 Б)
треба відрізняти від явного розміру kernel raw copy.

### V8: get-info на N95 і точний messaging ABI

[Get-info v8](evidence/2026-09-30/n95-stream-info-v8-raw-record.txt)
виконано **без RUN** на normal DSP v7: create=5859 мкс, task2 rc=0,
header/max `30000068/104`, nodeEnv `000077e0`; delete/free task=0,
EXIT/FINAL=0. [Транспорт](evidence/2026-09-30/n95-stream-info-v8-raw-record-transport.txt)
закінчується успішним INFO. Це перевірка record і nodeEnv, а не execute.
У цьому першому журналі поле payload+52 названо `timeout=3`;
статичний доказ установлює лише PDD node+112. Підпис виправлено на
`property112` у наступній збірці; одиниці часу для цього поля не доведені.

Статичний маршрут: PDD put `801AF3A0` записує queue+16 у destination
frame; setter `801AF45C` отримує повернений nodeEnv після create ACK
(`801A27F4..801A2800`). PDD shared-record writer `8019AF44..8019AFAC`
формує 16-байтовий `{cmd,arg1,arg2,destination}`. MSG-toDSP SWI `24D498`
ставить повідомлення в чергу destination і викликає MSG_notify `24E758`.
Нативні NODE_putMsg, MSG-toDSP SWI і MSG_notify, а також потрібні LDD
put/get/info/dispatcher фрагменти N95/E90 побайтово тотожні:
[адреси та SHA-256](evidence/2026-09-30/n95-e90-message-routing-contract.json).
Це доказ коду обох прошивок; get-info/messages на E90 v8 ще не запускалися.

PDD queued receive `801AF284` і pending receive `8019B048` пишуть
**24 Б**. Record v8 має явний padding; він не інтерпретується. Task20/21
отримують 8-Б пару `{TRequestStatus*,record*}`. Dispatcher має команди
0–21, окремих cancel22/23 немає; після таймауту новий receive не
надсилається поверх pending. Статуси та records живуть до закриття
каналу; таймаут і пізнє завершення не зараховуються як чистий успіх.

Новий messages variant ізолює execute від
STRM. Hello `{600,00080001,nodeEnv}` підтверджує вхід в execute;
host `{601,12345678,a5c55a5a}` має дати echo `{602,...}`; повідомлення
`{603,80000000,echo_count}` показує отримання RMS_EXIT перед return.
Штатний wrapper формує EXITACK сам. DSP receive обмежений 150×100 мс,
host зберігає першу помилку й дозволяє додаткові 15 с для pending delete;
runner має deadline не менше 60 с. Лише echo разом з receipt,
delete/free та EXIT/FINAL=0 відкриває наступну потокову пробу.

Після восьмигодинної паузи INFO на обох IP отримав connect timeout.
ПК залишився `192.168.3.11`, шлюз `.1` відповів; причина недоступності
телефонів не встановлена. Після успішного get-info новий RUN і доставка
messages DLL ще не виконувалися. Підготовчий `prepare_stream.py`
робить backup, read-only clock probe, відновлює ocprobe.log та перевіряє
EXE/hash/DLL читанням назад.

**Подальша доступність 10:59 UTC:** prepare на N95 пройшов:
[metadata/readback](evidence/2026-09-30/n95-messages-v8-preparation.json),
[clock](evidence/2026-09-30/n95-clock-before-messages-v8.txt).
Stock m86/div3, firmware math 220160 kHz, HAL ARM 206438 kHz;
original ocprobe.log 1259 Б повернуто з тим самим SHA-256 1ABC8073... .
Host 18668 Б 0900DFE3... і messages DLL 2924 Б 5A06007E... доставлені
й прочитані назад. [Create/info/delete](evidence/2026-09-30/n95-stream-info-v8-messages-create.txt)
з цим DLL: create=6347 мкс, header/max 30000068/104, nodeEnv=000077e0;
delete/free task=0, EXIT/FINAL=0, новий підпис property112=3.

**Message RUN:** START прийнятий о 11:00:20 UTC, PS кілька разів
показав живий процес. Наступний PS отримав response timeout;
новий connect/GET також timeout до команди. Телефонний журнал ще
не прочитано, тому hello/echo/RMS_EXIT receipt, FINAL/EXIT та точне
місце відмови невідомі. Перезапуск телефона не підтверджено.
Докази — [transport](evidence/2026-09-30/n95-stream-messages-v8-routing-transport.txt)
та [стан](evidence/2026-09-30/device-status-after-v8-message-run.json).
E90 свіжий INFO успішний, PS c55stream*=0; новий DSP RUN на ньому
не робився. Наступне — прочитати журнал і DLL N95 до нового START,
після quiescent PS повернути normal DLL із backup та перевірити GET.
Prepare перевірений на апараті; success messages ще не доведений.

## E90: окремий живий ROM

MachineUid **20002496**, RA-6 `400.34.93 / 21-04-2009`. Read-only ocprobe
прочитав вікно ROM `80000000..803FFFFF`; файли виділено за TRomEntry та
120-байтовим TRomImageHeader, а не вгадуванням адрес.

| Модуль | Code address | SHA-256 |
|---|---|---|
| bridgeapi.dll | `803F9EC8` | `003D47B0778D1E6687BDEEB456E4E02BFE64D8763E4178CFAECFDDDBA994C6FE2` |
| ehwa.ldd | `803F8648` | `07731D17142D8D45EF29229F00D7856135CE59D2F51935DB1DF96AD742E9A70D` |
| ehwaomap.pdd | `803DD788` | `D2818CC222051D3C1B2C61ACB17E14D72B964AB173EDC04A493C31A4CC6CFAB4` |

39 bridgeapi ординалів мають зсув `FF99CA70` від N95; live inspect підтвердив
усі 39 і FINAL=0: [E90 inspect](evidence/2026-09-30/e90-stream-inspect-recovered.txt).
DCD parse — `803FBB45`, lock/unlock — `803FBA11/803FBA07`.
Загальний зсув **не застосовується до PDD**: прологи функцій зіставлялися
окремо; RUN `803E5A44`, input `803E60D0`, output `803E5ED0`.
Три потрібні LDD-фрагменти тотожні побайтово, у відповідних PDD-функціях
відрізняються адреси BL. Це статичне зіставлення, а не результат DSP-тесту E90.

Його `baseimage.dof` (155708 Б) має SHA-256
`180F95602B078111F617F459620C4AECD203ECB730E91803AEF9E591E5D22F35`;
використовується власний `Z:\resource\plugins\baseimage.dof` цього апарата.
Перша відмова inspect сталася в daemon WAIT при живому процесі; recovered
журнал мав FINAL=0, користувач повідомив про виліт демона. DSP-драйвер тоді
не викликався. Runner тепер чекає завершення через PS й лише потім читає WAIT.

Після оновлення SIS і допомоги користувача
[inspect](evidence/2026-09-30/e90-stream-verify-v3.txt) підтвердив host v3.
[Base](evidence/2026-09-30/e90-stream-base-v3.txt) і
[create/delete](evidence/2026-09-30/e90-stream-context-create-v3.txt)
завершилися EXIT/FINAL=0; create=6774 мкс, free task=0. Це попередній
етап v3 до оновлення, без RUN і без виправлення host connection v6.

Після ручного встановлення користувачем SIS revision 7
[inspect](evidence/2026-09-30/e90-stream-v7-user-installed.txt) підтвердив
host v7, UID 20002496 і всі 39 exports. DSP DLL 3668 Б записано й
прочитано назад; байти тотожні локальному v7 з SHA-256
`E039E983AA042EF1397368151E671FEB8D29BA0828A576139223367CF6FEF5C1`.

| E90 v7 режим | Результат | Доказ |
|---|---|---|
| Base | load/close=0, EXIT/FINAL=0 | [base](evidence/2026-09-30/e90-stream-base-v7.txt) |
| Native buffers | два alloc/free по 4096 Б, EXIT/FINAL=0 | [buffers](evidence/2026-09-30/e90-stream-buffers-v7.txt) |
| Create/delete | create=8697 мкс, delete/free=0, EXIT/FINAL=0 | [create](evidence/2026-09-30/e90-stream-create-v7.txt) |
| Execute без host frames | RUN=0/status=0; delete pending/−33, EXIT/FINAL=−33 | [execute](evidence/2026-09-30/e90-stream-execute-v7-minimum.txt), [transport](evidence/2026-09-30/e90-stream-execute-v7-minimum-transport.txt) |

[Clock probe](evidence/2026-09-30/e90-clock-before-v7-min-execute.txt)
підтвердив stock m86/div3, firmware math DSP 220160 kHz; original
ocprobe.log після проби повернуто й зіставлено побайтово. Телефон відповів
одразу після −33. Пізніший connect мав timeout; під час підготовки
RMS-only на E90 не було жодної команди PUT/START. Наступний INFO знову
успішний, але uptime менший за попередній: між перевірками є ознака
перезапуску, причина не встановлена. Мінімальний журнал і normal v7 DLL
прочитані знову, байти не змінилися. [Поточний стан обох телефонів](evidence/2026-09-30/device-status-after-n95-subnet-recovery.json).

### Get-info E90: власний PDD getter і доставлений v8

`tools/rev/compare_node_info.py` звірив task2 raw copy (100 Б), node-info
adapter (56 Б) і constructor (44 Б): LDD-код побайтово тотожний. Adapter
викликає PDD vtable slot20. У N95 це table801B3DE8/getter801A11B8,
у E90 — table803F8424/getter803E57F8; записи vtable перевірені окремо.
92-Б getter різниться лише ARM BL у +20, який іде в різні import stubs.
Решта 88 Б однакова. Зокрема, node+44 записано у payload+64 через
N95 801A11F0/801A11F4 та E90 803E5830/803E5834. Це підтверджує формат
info без перенесення загального delta bridgeapi на PDD.
[JSON](evidence/2026-09-30/n95-e90-get-info-contract.json) містить усі hashes,
vtable, call targets і offsets. Значення property112 не отримало одиниць часу.

11:30 UTC на E90 передано `E:\c55stream-v8.sis` (11716 Б,
SHA-256804B1533...), readback рівний. До запису збережено EXE/hash/DLL/log;
versioned SIS path раніше був відсутній. Старий SIS і DSP DLL не замінено,
OPEN/SHOT/START у цьому кроці не було. [Доказ доставки](evidence/2026-09-30/e90-host-v8-sis-delivery.json).
Пізніше GET установленого EXE дав v7 hash87CEA30C...; встановлення v8
очікується. Наступний тест — inspect, stock clock guard та create/info/delete
без RUN. Це ще не апаратна перевірка v8 на E90.

N95 досі недоступний: recovery01/02 зупинилися на connect timeout до першої
daemon-команди; повне сканування TCP2323 знайшло лише E90. Журнал message
RUN і normal DSP restore лишаються pending. `recover_stream.py` зберігає
журнал/current DLL, читає свіжий PS і дозволяє restore лише після завершення
c55stream та при відомих before/after hashes. Compile/help пройшли;
позитивне апаратне виконання recovery ще не відбулося.

Пізніша перевірка E90 виявила помилку stock guard у prepare: він вимагав
restore-check100 для обох апаратів, хоча E90 штатно повертає1. Перша спроба
guard01 дала complete=false до DSP PUT і повернула original ocprobe.log.
Після розділення UID/profile/restore-code guard02 пройшов complete=true:
stock m86/div3, firmware math DSP220160 kHz, HAL ARM330000 kHz; normal
DLL E039E983... та ocprobe.log BE58F5EF... прочитані назад, байти рівні.
[Журнал](evidence/2026-09-30/e90-clock-before-info-v8.txt),
[preparation](evidence/2026-09-30/e90-info-v8-preparation.json).

E90 recovery фактично пройшов: збережено попередній minimum-execute journal,
INFO/PS0, current DLL уже був exact backup, PUT пропущено, GET рівний.
[Метадані](evidence/2026-09-30/e90-idempotent-dsp-recovery.json) і транспорт
підтверджують цей випадок. Це не результат v8 info/messages і не перевірка
повернення зміненого DLL N95. На N95 journal/normal restore досі pending.

## Native buffers, DMM, notify та worker

Статично встановлено: bridgeapi ord30 має форму
`Alloc(processor, TDes8*, sizeBytes, unused=0, unused=0, mode)`.
Mode 0 викликає `User::Alloc`, mode 1/2 вимагають позитивний розмір,
кратний 4096, та передають descriptor у `Ctl(0x0400000B, descriptor, size)`.
Production `balbuffers:80A42408` округлює розмір до 4 KiB та використовує mode 2;
ord29 звільняє відповідний descriptor і зануляє його.
[Окремий N95 buffers-тест](evidence/2026-09-30/n95-stream-native-buffers-v4.txt)
підтвердив два виділення по 4096 байтів і обидва free=0, FINAL=0. Саме ці
буфери використано в 8-packet v6 тесті. Це не ізольований доказ, що попередній
−2 був спричинений звичайним user buffer; виправлення connection має окреме
статичне обґрунтування.

`dspmemmapper.dll` має 11 експортів; внутрішні записи — 48 Б на mapping.
Ord9 (`80A44743`) приймає `{armAddress, byteSize, flags, slot}` та replace flag,
перевіряє slot і ненульовий розмір, зберігає DSP-address результат ord31.
Ord2 знімає mapping через ord34, ord6 після цього знімає reservation через
ord28 (reservation створює ord27). Ord3/4 читають збережені адреси. Повний контракт резервування, доступу
за DSP-адресою та cache ownership ще не перевірено на апараті.

`ebridgeutil` fn1 перетворює сторінки через LinearToPhysical; це читання
адрес **не є доказом pinning**. Fn2 виконує cache clean/flush. Ring buffer
потребує окремого доказу життєвого циклу сторінок, порядку публікації index,
когерентності й завершення. Notify стану вузла розібрано нижче; окремий
notify для довільного спільного ring buffer не встановлений.

Base image експортує `TSK_create`/`TSK_delete`, `SEM_*`, `CLK_*`, `STRM_*`,
`NODE_wait/getMsg/putMsg`. Worker, запущений один раз із create, є окремим
кандидатом, але він потребує ABI задачі, власного стеку та каналу повернення
результатів. Неприсутність `SIO_*` в експортній таблиці не доводить відсутність
цієї можливості всередині BIOS. Апаратний прототип worker/DMM/ring поки не запускали.

## Notify, одноразова підготовка та завершення карти каналів F04

### Notify стану вузла

**Статично встановлено, апаратно не викликався:** task5 `08000005`, LDD
`801B4418`, читає 8 байтів `{TRequestStatus*, flags}`. Вказівник зберігається
у LDD node +36, flags — +40; PDD virtual slot +96 перевіряє початковий стан.
Повторна реєстрація за наявності status pointer не дозволяється.

У `801B4384` LDD записує новий state у +20. Якщо state змінився від
попереднього значення **2** і notification зареєстрована, він ставить
completion=0 у +44 і ставить DFC +48 у чергу через `801B5598`.
DFC `801B40C8` завершує збережений request через `801B5698`.
Task6 `08000006` скасовує саме цю notification зі статусом −3.
Це **інша команда**, ніж lifecycle control 6 без префікса `08000000`.

PDD slot +96 (`801A2D50`) має окремі перевірки state=11, flags bit0 та
message queue. Значення flags й усі випадки початкового completion не
перевірені на телефоні. State notification не доводить наявність довільного
міжпроцесорного doorbell і не використовується для ring indices.

На DSP `NODE_wait` за TI `node.h` чекає готовності STRM або повідомлення;
stream mask і messagesReady — 16-бітні `Uns`, timeout — мілісекунди.
Очікування з timeout>0 потребує task context і має обмеження `SEM_pend`.
Для поточного вузла stream mask 1 означає готовий єдиний input. Цей шлях
додатково підтверджений повторною передачею 8 пакетів; API довільного
спільного буфера із цього не випливає.

### Що виконується один раз

| Стадія | Частота у прототипі | Доказ / межа |
|---|---|---|
| Перевірка firmware, processor open, DCD bind, base load | Один раз на процес | ARM-код та base/create апаратні журнали |
| DCD parse, select, stream props, allocate host task | Один раз перед create | ARM-код та журнали v6 |
| DSP create: контекст, STRM objects, DSP buffers, coefficients | Один раз на вузол | DSP-код; 8 пакетів мають один create |
| Native ARM buffers ord30 | Два виділення на процес | Окремий buffers-тест, обидва free=0 |
| RUN execute | Один раз на вузол | RUN=0 і 8 frames без повторного RUN |
| Host input/output requests, issue/reclaim, обчислення | Для кожної порції | Апаратно підтверджена передача; reps=0 ще не доводить Q15 workload |
| RMS_EXIT → ACK → delete → free host task | Один раз при завершенні | Статичний штатний шлях; після потокового RUN чисте завершення ще не доведене |

Create використовує status pointer: LDD `801B5014` передає його PDD через
slot +12 (`801A1038`), зворотний completion проходить DFC. Це дозволяє
ARM-коду виконати роботу **після повернення DoControl і до Wait**. Частина
підготовки/завантаження коду може виконуватися всередині DoControl; її
тривалість окремо ще не виміряна. Поточний хост одразу чекає create, тому
фізичний overlap ARM/create не заявляється. Таймер create включає submission
і очікування. Для довгоживучого каналу ця ціна сплачується один раз.

### Матриця доказів для кандидатів

| Кандидат | Контракт / джерело | Поточний доказ | Що лишається перевірити |
|---|---|---|---|
| Host STRM, TASK execute | LDD task14/16, 28 Б; PDD connection=0; TI strmcopy | 8×512 Б за один create/RUN | Штатний вихід, Q15, час компонентів, serial/parallel |
| Native allocation і DMM | Ord30/29; dspmemmapper ord9, bridge ord31/34/27/28 | Alloc/free mode2 на N95; mapping розібрано статично | Усі mapping flags, DSP-address доступ, pinning та cache ownership |
| Shared ring + notify | DMM і ebridgeutil fn1/2; node state notification task5 | Складові існують; спільного ring тесту немає | Публікація indices, бар'єри, когерентність, сигнал даних та wraparound |
| TSK/SEM worker із create | Native TSK/SEM ABI, generic library2, created-state lifetime | На N95/E90 finite task і parked task: block у create, wake/join/delete у delete; data/address збережені | STRM у created state, stop/cleanup, Q15 та корисний ARM overlap |
| Повідомлення | Task20/21 pair8 Б + raw record24 Б; TI RMS_DSPMSG | N95 DSP get0/put1, queue→shared window; created pending get скасовано −3 на N95/E90 | ARM delivery, echo, RMS_EXIT/ACK і bounded shutdown |

Порядок експериментів: завершити найсильніший уже робочий STRM-кандидат;
потім виміряти передачу й overlap; DMM/ring або власні повідомлення потрібні,
якщо виміряна вартість STRM не підходить конкретному застосунку. Worker сам
по собі не усуває потребу в каналі даних. Негативного висновку про ці
альтернативи немає: їхні апаратні контракти лишаються відкритими.

F04 завершено як **карта каналів і доказів** відповідно до PLAN. Це не
завершення потокового прототипу F05, E90 F06 або вимірів окупності F07.

## Нові апаратні докази: recovery, receive й MSG stages (13:15–15:54 UTC)

Попередні записи вище описують стан на час відповідного досліду.
N95 recovery і встановлення E90 v8/v14 вже виконано.

| Перевірка | Результат і межа доказу | Журнал у evidence/2026-09-30 |
|---|---|---|
| N95 v8 recovery | Старий journal прочитано; hello −33, останній запис BEGIN delete. Normal5B6BE15B… повернуто PUT/GET побайтово | n95-messages-v8-recovery.json/.txt |
| N95 v9/v10 receive-created | Create/get-info, get pending до RUN; delete/free0 → get −3; EXIT/FINAL0 | n95-receive-created-v9.txt, n95-receive-created-v10.txt |
| N95 messages-bare | DCD нуль streams, create/info/delete чисті. RUN без STRM у жодній фазі: hello/delete −33; телефон залишився доступним | n95-info-v9-bare-messages.txt, n95-messages-v9-bare.txt |
| N95 v11 markers | Три STRM output512 Б; execute entry, NODE_getMsg(0)=0, NODE_putMsg(0)=1; delete/FINAL/EXIT−33 | n95-message-stages-v11.txt |
| N95 v12 windows | DSP toGPP count0, fromDSP window count1 після put; ARM get ще не ставився; delete−33 | n95-message-windows-v12.txt |
| N95 v13 get після markers | Після put empty0/count1 у fromDSP window; власний ARM get pending/−33, delete/FINAL/EXIT−33 | n95-message-windows-v13.txt |
| N95/E90 v14 patcher | Write105 у власну RAM0, actual51/a7/3c/d2, EXIT/FINAL0; без DSP/PRCM/kernel patch | n95-patcher-own-ram-v14.txt, e90-patcher-own-ram-v14.txt |
| E90 v14 після reboot | EXE/hash рівні локальній збірці; inspect39 exports; свіжий stock guard; info та receive-created EXIT/FINAL0, без RUN | e90-v14-installed-after-reboot.json, e90-v14-postreboot-preparation.json, e90-info-v14-postreboot.txt, e90-receive-created-v14.txt |

N95 v9–v14 мав той самий daemon startTick7928381 і зростання uptime.
Після кожного bare/stages варіанта normal DSP5B6BE15B… відновлено GET-equal;
E90 normalE039E983… не замінювався варіантами. Це перевірка телефонного
файла, а не доказ успішного завершення попереднього DSP worker.

### Allocation і pending receive

Control4 LDD копіює **32 байти** (`801B4EE8`, E90 `803F9528`).
SDK `TBuf8<20>` займає28; v10 ввів explicit32 record з header30000014,
max20, п'ятьма payload DWORD та padding. Останній DWORD не передається
алокатору. Over-read виправлено, але він не встановлений як причина MSG
відмови. Compile-time assertions і успішна збірка перевіряють обидва розміри.

`tools/rev/compare_receive_cleanup.py` перевірив byte-equal ranges N95/E90:
node destructor, cancel saved get/put, free control7 і allocation copy.
[Статичний контракт](evidence/2026-09-30/n95-e90-allocation-receive-contract.json).
У state1 delete завершується, free викликає LDD destructor, який завершує
saved get status значенням KErrCancel−3. N95 v9/v10 і E90 v14 підтвердили
це апаратно. Для state2 timeout delete цей позитивний висновок не застосовується.

Runner тепер вимагає свіжий успішний preparation для receive та всіх RUN
режимів і звіряє current DSP перед START. E90 info v8 було помилково
запущено після відхиленого clock guard03: 8758 мкс — справжній результат
create/info, але **не вимір за підтверджених частот**. Новий v14 info6652 мкс
має власний успішний guard; ці одиночні числа не є оцінкою швидкодії між версіями.

### DSP messenger і ARM receive window

TI primary header `msg.h` із userspace-dspbridge342b… задає
WORKNEEDED=1, BUFFEREMPTY=2, ENABLE=4. Native SWI mailbox3 означає
work+bufferempty; це **не доказ OEM enable gate**. NODE_enableMsg відсутній
серед exports; виклик невідомої адреси не обґрунтований.

Readonly DSP snapshots v12/v13 показали:

- MSG_toGPP0012AC38: count0, notify2000, notifyHandle raw words0000/7AE6,
  maxMessages16. V12 помилково друкував handle через low-word-first Get32
  як7AE60000; v13 зберігає raw words. Цей формат v12 не є адресою.
- MSG_pfromDSPBuffer→0008FEF8: count0 до put і1 після put.
- MSG_ptoDSPBuffer→0008FF7C: empty1/count0.
- Native NODE_put24DD5C копіює три long у frame й source=nodeEnv;
  MSG_notify24E758 постить fromDSP SWI. MSG_fromDSPFxn24C928 переносить
  записи у shared window, ставить empty0 та викликає MSG_interruptGPP24EC70.

Комбінація queue0/window count1 — доказ руху DSP до shared window.
V13 ARM task21 pending після трьох markers не доводить, що ARM отримав
IRQ або знайшов правильну чергу. Native wrapper24E6F0 уже надсилає ACK;
ручне дублювання ACK без нового контракту не потрібне.

Відтворюваний `tools/rev/compare_message_window.py` звірив consumer744 Б
N95/E90: різняться лише дев’ять relocated BL. Reader24 Б, DFC88 Б,
configuration copy та window setup тотожні. E90 reader803F7664 знайдено
за унікальними інструкціями й чотирма фактичними BL; general relocation
для нього не підходить. [Контракт і hashes](evidence/2026-09-30/n95-e90-message-window-consumer.json).

ARM PDD consumer `8019B0A8` бере window у context+224, повідомлення з+240,
читає чотири32-bit поля через `801B3028` і зіставляє source з queue+16.
Reader робить ror16, якщо byte+64 його embedded memory-interface
ненульовий. Це інший об’єкт, ніж processor+64 із configuration+588. Збіг звичайного
повідомлення: pending user-record у queue+40 або список queued receive;
ACK40000000 проходить окремо. DFC `8019BA84` викликає consumer після
mailbox service. Static code не встановлює фактичного runtime flag,
IRQ/DFC виконання, record source або mapping. Наступна локалізація має
розрізнити ці умови, а не повторити v13 без нової інформації.

### E90 patcher і перезавантаження

E90 guard03 і окремий старий ocprobe level1 до reboot дали self-test−20;
original ocprobe.log повернуто. On-disk patcher C:/E: мав однаковий hash,
але стан завантаженого resident driver не вимірювався. V14 SIS передано
14:38 UTC, readback рівний; користувач повідомив про автоматичний reboot
та встановлення. У цій сесії E90 DSP RUN не викликався; причина reboot невідома.

15:52–15:54 UTC installed host22408 Б5F1C77CF… збігся з локальним v14.
Own-RAM patcher load/open/write0, readback51/a7/3c/d2. Новий clock probe
підтвердив m86/div3, HAL ARM330000, firmware DSP math220160 kHz; усі
logs restored. E90 restore-check1 — порівняння шести live Usbc instructions;
старий ocprobe підписує його загальним DoControl, що для E90 неточно.
Позитивні результати після reboot не встановлюють причину попереднього−20.

### V15: фактичний record і уточнення об’єкта reader (16:14 UTC)

[Журнал v15](evidence/2026-09-30/n95-message-records-v15.txt) містить snapshot
восьми слів першого shared record. Count1/empty0 до й після читання:
`0000/0600/000F/0001/0000/77E0/0000/77E0`. Native long-word-first дає
cmd600, arg1F0001, arg2/source77E0 — очікувані поля цієї проби.
ARM raw little-endian read дає cmd06000000/source77E00000; ror16 повертає
правильні значення. Вхід у execute та put1 знову підтверджені;
ARM get/delete/FINAL/EXIT−33. Normal5B6BE15B… повернуто exact GET,
телефон доступний/startTick сталий. Нового успішного MSG delivery немає.

Уточнення статичного висновку v14: consumer передає reader pointer із
context+24. Setup8019BC8C/getter801AA98C встановлює його як об’єкт із
context+48 плюс164. Reader byte+64 належить цій embedded memory-interface;
**не можна ототожнювати його з processor+64**, що бере configuration+588
і керує іншим exit path. Стару асоціацію виправлено в звіті й metadata.
Getter/setup byte-equal на E90, перевірені compare_message_window.py.
Значення runtime reader flag, window mapping та IRQ/DFC невідомі. Правильні
поля DSP record не доводять, що ARM прочитав їх із потрібним flag.

### Альтернатива TSK worker: native ABI та короткий probe

[TI C55x DSP/BIOS API guide, SPRU404Q](https://www.ti.com/lit/ug/spru404q/spru404q.pdf),
с.447,455–457, описує dynamic task із attributes, до восьми Arg,
автоматичний TSK_exit після повернення function та explicit TSK_delete.
Attributes враховують окремий C55 system stack. Вищий пріоритет може
запустити нову задачу одразу; при бар’єрі priority−1 вона очікує підвищення.
Guide2012 не є самостійним доказом ABI старого Nokia firmware.

Локальний base DOFF експортує TSK_create25A5B4, TSK_delete25B6FC,
TSK_ATTRS255814. Native code24B0FC–24B130 читає default attrs із C55
word12AC0A, копіює **14 C55 words** (RPT13), задає priority−1 і два
stack sizes, потім викликає TSK_create для wrapper24E6F0. Це підтверджує
фактичний attrs extent й відкладений старт у цьому ROM.

Новий `extract_doff_section.py` звіряє header/verification/table/packet
checksums і зберігає instruction bytes без перестановки. Common section
65266 Б повністю збіглася з незалежним попереднім витягом. Synthetic COFF
дозволив dis55 розібрати `.bios`; локальні ROM/COFF/assembler не публікуються.
`compare_bios_tasks.py` підтвердив TSK_stat/startup/argument setup byte-equal
на N95/E90; create/delete/exit відрізняються лише сімома перевіреними
посиланнями на ті самі BIOS data symbols.

Native startup25CF3B–25CF4D передає перші п'ять аргументів у **XAR0–4**.
Вісім Arg займають 16 C55words; це pointer ABI, а не ABI `long` через AC.
У large model контейнер pointer — 32 біти, адреса — 23 біти. TSK_Stat
має 22 C55words, mode за offset14; native exit ставить task mode3.
Header `bios_task.h` перевіряє sizeof/offsetof під cl55 4.4.1, а assembler
probe підтвердив entry в AC0, attrs/8 Arg на stack та callback XAR0/XAR1.

`CREATE_WORKER_ONCE` перевіряє priority поточного RMS task (<15), створює
finite task із priority15, stack1024/sysstack256 та вісьмома pointer Arg.
Callback робить лише volatile stores marker/cookie й повертається. Create
повертає успіх лише після перевірки marker, cookie00123456 та stat.mode3;
TSK_delete викликається ще всередині create. Callback не володіє STRM,
locks або зовнішніми buffers; код задачі не може лишитися активним після
повернення цієї фази. Це перевірка task ABI та очищення, а не persistence.

| Телефон / host | DLL | create, мкс | delete / free / FINAL / EXIT | Офіційний RUN |
|---|---|---:|---|---|
| N95 / v15 | 3172 Б, 0709550C… | 10131 | 0 / 0 / 0 / 0 | Немає |
| E90 / v14 | Той самий DLL | 9368 | 0 / 0 / 0 / 0 | Немає |

Create timing включає звичайне STRM/MEM setup і task probe; це не час
порожнього create або вартість обробки пакета. Fresh stock guard m86/div3
пройшов на обох, original clocklogs відновлено, daemon startTick не змінився.
Після PS0 повернуто exact normal DLL N955B6BE15B…/E90E039E983… і GET-equal.
Докази: [task contract](evidence/2026-09-30/n95-e90-bios-task-contract.json),
[artifact](evidence/2026-09-30/worker-once-artifacts.json),
[N95](evidence/2026-09-30/n95-worker-once.txt),
[E90](evidence/2026-09-30/e90-worker-once.txt),
[results](evidence/2026-09-30/worker-once-device-results.json).

Розглядається worker із create як наступний канал: host тримає вузол
у created state, worker обмінюється пакетами STRM, explicit stop frame
завершує worker перед control6/delete. Це гіпотеза архітектури, а не готовий
обхід RMS lifecycle. Attributes/Args/termination підтверджено коротким
probe, але час життя dynamic code/data між create/delete ще відкритий.
Звичайний вузол має phase library types3/4/5. Для наступних worker probes
додано generic library type2; її create/delete residency та parked task
вже підтверджено нижче. Один create і справжні serial/parallel/Q15 виміри
залишаються критеріями F05.

### Бібліотека типу 2 і задача після create

Перевірено 2026-09-30 22:19–22:45 UTC (2026-10-01 за місцевим часом).
`compare_node_loader.py` звіряє два ROM та обидва base DOFF. Native
bridge fallback80A5E188/803FABF8 при missing create library3/−6 повторює
lookup із library2. Caller80A5E742/803FB1B2 пропускає окремі execute/delete
lists після цього fallback. Обидва ranges byte-equal.

PDD встановлює phase_split за lists+196/+200/+204, offset208. **Код create
залишається завантаженим у CREATED**, навіть із split phases. RUN може
вивантажити create; created-state delete зберігає create та, для split,
завантажує delete окремо. Final free вивантажує loaded libraries. Це
native Symbian контракт; попередню Linux-аналогію негайного unload після
create не можна переносити на ці прошивки. Припущення про збереження
тотожного data instance із цього статичного факту не випливає.

V1 resident probe містить initialized downloadable `.data` із stamp
1BADB002. Create перевіряє його, записує C55DC0DE та зберігає program
address delete у MEM context. Delete перевіряє **обидві** умови й завжди
звільняє звичайні ресурси. Generic0/2 і split0/3/4/5 мають однакові raw
`.text` bytes; відрізняється реєстрація.

Контроль split на N95: create0/7415us, delete−2, останній запис BEGIN close;
зв'язок зник. Recovery забрав журнал2039Б81DC64C0… і повернув normal DLL
GET-equal. До recovery uptime став нижчим, daemon був запущений наново;
причину перезапуску не встановлено. Негативний joint check показує зміну
stamp **або** delete address; окремі причини не виміряні. Цей дослід не
створював TSK та не викликав RUN.

У початкових v1 positive probes delete міг повернути8000 при null context,
обійшовши перевірку. Цю прогалину закрито у **v2**: null env/context —
negative error. V1 positive журнали збережено як попередні результати;
доказом assertions є нові v2 прогони зі свіжою preparation.

Generic library2 v2 пройшла на **обох** телефонах: create/delete/free,
FINAL/EXIT0. У цих прогонах збережено data stamp і адресу delete. Native
RMS24B225–24B238 передає return AC0 у reply24E684; PDD signed comparison
801A27A8/803E6DE8 відображає negative RMS return у host−2. Тому випадковий
позитивний return0x1234 із legacy probe не спростовує наших negative
гейтів80008015. Split control реально повернув−2; generic —0.

Наступний `worker-parked` не потребує initialized globals. Create
створює SEM(count0) і task(priority15, stack1024/sysstack256). Callback
пише pointer cookie00123456/stageC551 й блокується на SEM_pend30000 BIOS
ticks. Create перевіряє stat.mode2. Delete повторно перевіряє blocked2,
будить callback через SEM_post, перевіряє terminated3/stageC552/pend1,
потім TSK_delete та SEM_delete. Лише після цього звільняються streams і
MEM context. Задача не захоплює STRM, locks або зовнішні buffers.

| Варіант | N95 host15 create, мкс | E90 host14 create, мкс | Delete/free/FINAL/EXIT |
|---|---:|---:|---|
| resident-check v2, library2, 3000БD229D53F… | 9399 | 6744 | 0/0/0/0 на обох |
| worker-parked v2, library2, 3592БED8C2862… | 7873 | 9277 | 0/0/0/0 на обох |

Час включає звичайне STRM/MEM setup і probe; він не є packet latency.
Це перевірки умов у конкретних hashed DSP artifacts і native RMS mapping;
ARM не логував task fields незалежно. SEM ABI підтверджено emitted ASM
і native code; N95/E90 відрізняються лише сімома verified symbolic data
references. SEM timeout вимірюється BIOS ticks, не автоматично мілісекундами.

Fresh stock guards і restore original ocprobe.log пройшли. Daemon startTick
не змінився протягом кожної generic/parked preparation→recovery. Немає
active c55stream; normalN955B6BE15B…/E90E039E983… повернуто GET-equal.
Докази: [native contract](evidence/2026-09-30/n95-e90-node-loader-sem-contract.json),
[generic results](evidence/2026-09-30/resident-generic-v2-device-results.json),
[parked artifact](evidence/2026-09-30/worker-parked-v2-artifacts.json),
[parked results](evidence/2026-09-30/worker-parked-v2-device-results.json),
[failed control](evidence/2026-09-30/resident-phase-device-result.json).

Цей parked probe доводить життя задачі після повернення create та її
завершення через created-state delete для generic node. Він ще не
перевіряв STRM, Q15 та useful ARM overlap; наступна серія наведена нижче.
Придатність обчислень поряд з audio tasks не встановлена. Офіційного
RUN із library2 не було.

## Потоковий worker у CREATED — v16, обидва телефони

Апаратна серія завершена 2026-09-30 23:35 UTC. Host v16 24464 Б
AB016003… на обох; DSP worker DLL4792 Б DE7DF926… із 22 imports,
перевіреними в обох base images. DOFF dump PASSED; emitted ASM підтверджує
pointer Arg, task entry AC0, NULL-env NODE_wait і SEM timeout argument.
[Артефакт v2](evidence/2026-09-30/worker-stream-v2-artifacts.json) містить
точні source/DCD/ASM/EXE hashes; v1 з іншим host збережено окремо.

### Native контракт і завершення

`compare_created_stream.py` звіряє byte-equal LDD submit, direction slots,
PDD input/output state gates й 320 Б native NODE_wait. PDD не відхиляє
CREATED1: виключає states9/13/4/10/11/0. LDD копіює transfer record28 Б;
status12/length16/arg20/index24, task14 input/task16 output.
NODE_wait(NULL,...) пропускає RMS message queue та пише messagesReady=0.
[Статичний контракт](evidence/2026-09-30/n95-e90-created-stream-contract.json)
не є самостійним доказом передавання — ним є журнали нижче.

Create налаштовує STRM/MEM і TSK priority15, stack2048/sysstack512;
перевіряє blocked2, input pending, pointer cookie00123456 та stageC561.
Node лишається CREATED; control8/RUN не викликається. Worker:

1. Очікує input через stream-only NODE_wait зі скінченним timeout.
2. Перевіряє 256 words, magic, sequence, length, reps та stop0/1.
3. Рахує Q15 dot240 repeated reps і повертає transformed payload,
   result, raw DSP ticks, reported counts/ms та protocol16/cookie/priority.
4. Reclaim output виконується перед новим input. На last stop input
   не ставиться повторно; STRM idle/reclaim повертає pending ownership.
5. Callback постить completion SEM і повертається через native TSK_exit.
   Delete чекає до 5000 **BIOS ticks**, вимагає terminated3, успішний
   status, stop і нуль pending; лише тоді видаляє task/SEM, streams/context.
   Невдалий join не звільняє context активної задачі.

**LDD reported DELETED=5 відрізняється від PDD internal deleted=4.**
Native getter LDD node+20 перекриває PDD state у відповіді. У першому N95
one test пакет і cleanup працювали, але host вимагав 4, тому FINAL/EXIT−20.
Host виправлено на expected5; DSP не змінювався, новий one test пройшов.
[Перший журнал](evidence/2026-09-30/n95-worker-stream-first-state-v16.txt)
збережено. Journal-only recovery без --restore-dsp не повернув DLL;
наступна preparation правильно відхилила цей стан до запису/нового тесту.
Окремий restore повернув exact normal, після чого виконано fresh preparation.
Ці негативні результати не приховано та не включено в успішні виміри.

### Апаратна correctness і стінний час

На **кожному** телефоні пройшли one reps0, 8 packets reps0, 8 packets
reps1000 і три пари serial/parallel reps10000. У кожному run один create;
кожен packet512 Б, output echo/result збігаються, sequence/stop правильні.
ARM CRC64 КіБ на кожен packet = cd837cd0. У parallel CRC виконується
між put та очікуванням get; у serial — після завершення DSP.
Put/get statuses, errors, delete/free/native/close/FINAL/EXIT=0 у всіх
18 успішних runs. Немає офіційного RUN або transport KILL.

| Телефон / пара | Serial, мкс | Parallel, мкс | Зміна стінного часу |
|---|---:|---:|---:|
| N95 / 1 | 406551 | 150968 | −62.866% |
| N95 / 2 | 399838 | 149868 | −62.518% |
| N95 / 3 | 249324 | 149593 | −40.001% |
| E90 / 1 | 266809 | 160305 | −39.918% |
| E90 / 2 | 263363 | 164517 | −37.532% |
| E90 / 3 | 257351 | 159542 | −38.006% |

Порядок: S1/P1, P2/S2, S3/P3. Таблиця охоплює цикл 8 пакетів із CRC,
передачею та очікуванням; виключає create, підготовку CRC-еталона,
logging і cleanup. **Це спостережувані зміни, не ізольований overlap gain.**
На N95 serial1 у frames4–8 одночасно подвоїлися ARM CRC (~18.4→36.8 мс),
DSP raw ticks (~239834→479669) та completion (~12.8→25.5 мс).
Це сумісне зі зміною частотного режиму, але PRCM не читався для кожного
пакета й причина не доведена. E90 значно рівніший, умови теж потребують
контролю. Критерій трьох N95 pairs в однакових умовах ще не закритий.

У multi reps0 observed completion512 Б становив N95 **335 мкс** і E90
**396 мкс**: issue/wait/echo/header checks, без CRC. Це не чистий DMA latency
і не вимір bandwidth. FastCounter32768 Гц дає крок близько30.5 мкс.
За reps1000 completion — N951525–1556 мкс, E901617–1647 мкс, з правильними
ненульовими Q15 results. Successful one create — N958087/E907507 мкс;
setup включає STRM/MEM/task, його не треба додавати до кожного пакета.

CLK_countspms=164 не узгоджується з raw ticks і ARM wall time. Native
CLK_gethtime25D5C4 повертає AC0 після читання timer ports7814/7815;
CLK_countspms25D649 читає double-word BIOS RAM01316A в AC0. Отже наявна
32-bit return ABI правильна, але масштаб таймера ще не відкалібровано.
З raw ticks у цьому звіті **не обчислюються DSP мілісекунди**.

У кожній preparation пройшов stock clock guard і повернення original log;
daemon startTick не змінився за серію. E90 SIS v16 встановлено через
спостережуваний installer; EXE GET збігся з ARM artifact. Recovery повернув
normal N955B6BE15B…/E90E039E983… та original logs readback-equal; PS0.
[N95 results](evidence/2026-09-30/n95-worker-stream-v16-results.json),
[E90 results](evidence/2026-09-30/e90-worker-stream-v16-results.json),
[final checkpoint](evidence/2026-09-30/worker-stream-v16-checkpoint-device-status.json).
Raw phone journals збережено побайтово з SHA-256; Git -text залишає CRLF.

Доведено робочий STRM/Q15 канал і корисну одночасну роботу ARM на обох
телефонах у короткій серії. Тривала робота, audio coexistence, tail latency,
більші пакети, error-path lifecycle та застосункова інтеграція не перевірені.

## V17: штатне резервування MPU та калібрування таймера

2026-10-01 UTC: код і план [PLAN_V17](../work/PLAN_V17.md), DSP4800 Б
41D14CD4…/22 imports, host28456 БC8B08E8C… на обох телефонах.
[Артефакт v3](evidence/2026-10-01/worker-stream-v3-artifacts.json) зберігає
точні hashes. Protocol17 замінив wire cookie на absolute DSP timestamp
offset14; pointer cookie лишається обов'язковим create/delete gate.
Q15 workload240×reps і 512-byte packet layout решти полів не змінені.

### N95: контроль штатного режиму

`check_n95_performance.py` звіряє dvfs_interface getter, request0,
SetPerformance і destructor. У native SetPerformance80148460 лише a2
порівнюється з50; >50 додає reservation, <=50 знімає. Resource66 фіксований,
довільної частоти цей API не приймає. Getter control1 ділить MPU clock
на3300000 і повертає integer percent. Destructor видаляє залишкову
reservation клієнта. Чотири live fingerprints перевіряються перед API;
ніяких PRCM writes або ROM-shadow patches у host немає.
[Native contract](evidence/2026-10-01/n95-stock-performance-contract.json).

V17 викликає request0/a2=100 до processor setup й release0 після close;
request storage persistent, очікування bounded5000 мс. В усіх N95 runs
reserve/release/status0, MPU100% до/після кожного packet. Після release
можливі50 або100 через штатну політику/інших клієнтів; це не вимога
негайно повернути конкретну частоту. E90 пропускає цю гілку: N95 API й
адреси там не використовуються. Всі DSP/bus clock domains цим не sampled.

| Телефон / пара v17 | Serial, мкс | Parallel, мкс | Зміна wall time |
|---|---:|---:|---:|
| N95 / 1 | 251154 | 148953 | −40.693% |
| N95 / 2 | 250148 | 151211 | −39.551% |
| N95 / 3 | 249994 | 150205 | −39.917% |
| E90 / 1 | 259791 | 155729 | −40.056% |
| E90 / 2 | 258508 | 157467 | −39.086% |
| E90 / 3 | 263087 | 159878 | −39.230% |

Порядок S1/P1,P2/S2,S3/P3, один create та8 packets у кожному run,
reps10000, useful ARM CRC64KiB/frame. Scope total_us той самий, що у v16:
без create/CRC baseline/logging/cleanup. N95 raw dot ticks239834–239854
майже тотожні, doubled intervals у цій серії відсутні. Це сильніший
доказ useful overlap, ніж змішані частотні умови v16. Відсотки стосуються
цього синтетичного навантаження; застосункового прискорення не виміряно.

### DSP-таймер: короткі інтервали та довга пауза

`worker-calibrate` обробляє8 correct echo packets без CRC, з паузами
100/200/400/800/100/200/400 мс. DSP t1 записується перед відповіддю;
host записує FastCounter до submit та після completion. Для двох stamps
delta часу лежить між begin2−done1 і done2−begin1; bounds розширено на
один counter tick похибки. Verifier незалежно перераховує усі bounds
із журналів. На кожному телефоні три такі runs з FINAL/EXIT0.

За коротких100–400 мс nominal19.2 МГц входить в усі measured bounds.
Їх intersection N95 **19185149–19213529 Гц**, E90
**19182339–19218353 Гц**. Це bounds цього досліду й short-interval model,
а не калібрування всіх умов. CLK_countspms лишається164.

В усіх шести800-ms intervals DSP delta відповідає лише **501.06–501.36 мс**
за19.2 МГц. ARM brackets — **828.19–875.89 мс**. Видиме середнє rate
на цих intervals N95~11.6 МГц, E90~11.0–11.6 МГц. Коректні packets та
cleanup пройшли; потрібний висновок — **таймер не можна вважати
безперервним wall clock під час довгого idle**. Нестача з'являється і на
E90, і на N95 із MPU100%, тому лише MPU DVFS її не пояснює.
Зупинка/gating DSP або самого timer після~500 мс — гіпотеза; runtime
PRCM/idle-policy contract ще не виміряний. Не відкидати ці intervals,
щоб отримати красиву спільну calibration rate.

На обох повторно пройшли one/multi reps0, Q15 reps1000, три pairs та
три calibrations — **24 успішні runs v17**. Completion512 Б reps0
N95335/E90396 мкс. Жодного RUN, KILL або reboot у серії. E90 SIS16776 Б
9C04181A… встановлено за observed installer, EXE GET-equal. Recovery
повернув original DSP і clocklogs exact, PS0; final INFO/GET збережено.
[N95 v17](evidence/2026-10-01/n95-worker-stream-v17-results.json),
[E90 v17](evidence/2026-10-01/e90-worker-stream-v17-results.json),
[final checkpoint](evidence/2026-10-01/worker-stream-v17-checkpoint-device-status.json).
Report зберігає raw ticks/bounds і не переводить їх за reported164.

## Наступний дослід

1. Виміряти packet1760/2048/2304/4096 Б, jitter і границі володіння буферами.
   Зіставити ці результати з форматами WSOLA/MDEC та media stages браузера.
2. Розібрати native timer/idle contract для~500-ms паузи та відрізнити
   timer stop від зміни clock domains. Для порівнянь wall time лишається
   ARM FastCounter; short rate не переносити на довгий idle.
3. Перевірити error/timeout lifecycle до прикладної інтеграції та audio
   coexistence для звукових кандидатів. Не запускати старі невдалі RUN.
4. Перевірити вимоги F05–F08 за реальними доказами. MSG маршрут лишається
   відкритим: v15 shared record правильний, runtime reader/routing/IRQ
   не встановлені; наявний робочий STRM не є доказом роботи MSG.
## V18: довжини та вартість packet echo — 2026-10-01

Static native contract на обох ROM: properties size+4 -> RMS size+0,
C55 words; ARM descriptor length — bytes. DCD не змінено. Host v18 і
worker protocol18 підтримують однакові input/output packet512–4096 Б;
це ліміт prototype allocation4096, не максимум native allocator.

На обох телефонах перевірено512/1568/1792/2048/2304/4096 Б,32 packets
за один create, по3 ordered runs на size. One512/1792/4096 і Q15×8 на4096
також пройшли. На кожному22 runs/587 correct packets, clean FINAL/EXIT0,
no official RUN/KILL/reboot. Оригінальний DSP повернуто GET-equal.

Режим worker-transfer не рахує ARM CRC/Q15 repetitions. ARM issue-to-
observed-completion для1792 Б: N95 median518/max549us, E90 median640/
max7812us. Max не вилучено; це не доводить аудіодедлайн hop≈4.99ms.
Actual WSOLA, короткий output та MDEC не виміряні. Таймерні висновки v17
не замінюються перерахунком counts/ms164.

Повна методика, таблиця та докази: [PACKET_SIZES.md](PACKET_SIZES.md).
Розміри — із32-byte header: WSOLA input1792, MDEC input1568/output544
або800. Не підміняти їх одним symmetric packet2048/2304.

## Поточне прикладне ядро і audit: v19/v20 —2026-10-01

WSOLA220/441 exact coarse/refine перенесено на resident STRM worker: input896/
output24 C55 words (1792/48 Б), independent properties, unchanged DCD.
V20 scalar ARMv6 baseline matches current PS1 compiler options і codegen.
На кожному9 runs/195 correct packets,97 searches; три paired runs по32.
ARM median999.45us, packing+DSP+completion median640.87/732.42us.
One create/no RUN, valid stop/join/DELETED5/free/native close/FINAL/EXIT0;
originals/clock logs returned GET-equal. Method/raw journals/results — WSOLA.md.

Native copy path coherence/ownership validated for these packets; shared
ring/DMM cache ownership не випливає з цього. Error/timeout/live-task unload
не перевірені й потребують native audit перед інтеграцією; audio/long-run
stability і application gain невідомі. Native164/long idle timer не conversion.
Scope/criteria audit: ../work/FINAL_AUDIT.md.
