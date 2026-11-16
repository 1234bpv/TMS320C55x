# Збірка на поточному ПК та після перенесення

Оновлення02.10 після повернення SSD: корінь знову D:\VsCodeProjects\SymbianProjects;
SDK/toolchain знайдені поруч, TI CGT4.4.1 — на C:. ARM host28 збирається,
локальні artifacts37 перевірені; на телефонах після тестів повернений host20.
Python3.12 доступний через `C:\Program Files\LibreOffice\program\python.exe`.
Звичайні `python/python3/py` у PATH відсутні. Обв'язку запускати через
run_bounded із повним шляхом цього Python. Для scripts із subprocess
sys.executable враховувати, що LibreOffice повертає каталог python-core;
check_d0_checkpoint.py уже обробляє його або приймає --python.
Апаратні результати й відновлення — [WORKER_MESSAGES](WORKER_MESSAGES_2026-10-02.md).

Для доручення D0–D2: host25 збирає build.cmd, DSP candidates —
build_stream_node.cmd run-stop / run-message-diag / run-exit-diag; пакет —
build_stream_sis.ps1 -Revision31 -OutputName c55stream-exit-diag-v25.
Перевірка DOFF/imports/ASM і immutable archive — record_d0_artifacts.py.
Чотири experimental RUN дали failed teardown, D0 0/3. Людина дозволила
нові спроби з окремою гіпотезою; наступна — own-node RMS_EXIT/idle snapshots
під час pending delete. ROM STRMCOPY control уже виконано. Деталі й порядок
відновлення — [LIFECYCLE_DMM](LIFECYCLE_DMM_2026-10-01.md).

Пакет повернення початкового EXE без перезбирання host:

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'pwsh -NoProfile -File tools/build_stream_sis.ps1 -Revision 29 -BinaryPath work/evidence/e90/d0-20261001/original-3.bin -OutputName c55stream-restore-v20-r29' -TimeoutSec 60 -Log out/d0-restore-v20-r29-sis.log
```

Revision29 перевищує підготовлений package28; payload лишається exact
original host20. Старі restore22/25 збережено як історичні artifacts.
Установник створює sys/hash; після відновлення перевірити обидва файли.

`tools/env.cmd` визначає сусідні SDK, toolchain і демон від каталогу проєкту. Perl має бути 5.20. TI CGT шукається через `DSP_CGT`, PATH і встановлення `Texas Instruments/C5500 Code Generation Tools 4.4.1` на наявних дисках; `DSP_DOFFBUILD` можна перевизначити.

Запуск із кореня проєкту у PowerShell 7:

```powershell
pwsh -NoProfile -File tools/check_state.ps1
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/arm-build-desktop.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_dsp_node.cmd 0 1' -TimeoutSec 120 -Log out/dsp-build-desktop.log
pwsh -NoProfile -File tools/check_state.ps1 -RequireArtifacts
```

ARM-артефакт копіюється в `out/arm/dsptest.exe`, DSP-вузол — у `out/dsp/bench.dll55l`. Перед ARM-збіркою попередній цільовий EXE видаляється, тому відсутність нового файла є помилкою. Відсутність `dllcreate` також дає помилку, а не удаваний успіх часткової DSP-збірки.

Для старого SDK проєкт збирається через junction `<диск SDK>:/symbuild/c55x`. Сценарій `build_alias.ps1` перевіряє місце, тип посилання та його ціль перед видаленням. Справжній каталог або посилання на інший проєкт не видаляється.

`tools/sweep.ps1` вимагає явної `-Ip`; legacy `dsptest` підтримує лише N95
і відхиляє `-Device e90`. Серія записує вузол і ARM-хост на телефон; перед
нею зберегти замінювані файли. Використовується `strict_net.py` з перевіркою
INFO, без LAN fallback. EXEC має власну межу `RunTimeoutSec`, socket — ще
5 секунд; ненульовий process exit припиняє серію після отримання журналу.

## Потоковий прототип c55stream

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/stream-arm-build.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_stream_node.cmd' -TimeoutSec 120 -Log out/stream-dsp-build.log
pwsh -NoProfile -File tools/check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

Артефакти: `out/arm/c55stream.exe`, `out/dsp/c55stream.dll55l`;
`stream.x55` та `stream_node.asm` лишаються в ignored `out/dsp`.
Поточний host — **v18**, runner за замовчуванням очікує v18.
V17 встановлено на обох телефонах; E90 використовує EXE у C:\sys\bin.
Host перевіряє
MachineUid, усі 39 live exports та початок parser до DSP driver calls.
Інша прошивка відхиляється. Історичний host можна явно вибрати через
`--host-version`; новий режим потребує своєї мінімальної версії.

### Окремі DSP-варіанти

| Аргумент build_stream_node.cmd | Призначення | Окремий DLL |
|---|---|---|
| Без аргументу | Звичайний потік, один create, багато порцій | c55stream.dll55l |
| smoke | Execute одразу повертає 8000, без STRM | c55stream-smoke.dll55l |
| rms | Execute чекає RMS_EXIT, без STRM у execute | c55stream-rms.dll55l |
| messages | Hello/echo/RMS_EXIT, звичайні create/delete | c55stream-messages.dll55l |
| messages-bare | Ті самі повідомлення, нуль STRM у DCD/create/delete | c55stream-messages-bare.dll55l |
| message-stages | Три STRM-маркери й readonly shared record навколо NODE get/put | c55stream-message-stages.dll55l |
| worker-once | Коротка TSK-задача, stat/Arg перевірка та TSK_delete всередині create | c55stream-worker-once.dll55l |
| resident-check | Бібліотека типу 2, перевірка data stamp та адреси delete між create/delete | c55stream-resident-check.dll55l |
| resident-phase | Історичний контроль із типами 3/4/5; delete −2, обрив close на N95 | c55stream-resident-phase.dll55l |
| worker-parked | Тип 2, TSK чекає SEM після create; delete будить, перевіряє й видаляє task/SEM | c55stream-worker-parked.dll55l |
| worker-stream | Тип 2, TSK обробляє STRM у CREATED; explicit stop, join і cleanup | c55stream-worker-stream.dll55l |

**Кожен варіант також перезаписує основний DLL у out/dsp.** Після нього
зібрати звичайний вузол. Зберігається окремий assembler кожного варіанта.
Bare не усунув message timeout. V11–v13 markers підтвердили execute,
get=0, put=1 і DSP → shared window, але ARM get та delete дали −33.
Ці невдалі RUN не повторювати без нового доказу або зміненого контракту.

`worker-once` перевіряється режимом `info` на наявних host v15/N95 та
v14/E90, із явно переданою свіжою `--preparation` для цього DLL.
У цьому варіанті **не викликати execute/serial/parallel**: задача вже
завершена й видалена до повернення create. Постійний worker — окремий
варіант `worker-stream`, описаний нижче.
На обох телефонах create/delete/free/EXIT0 пройшли; докази —
[worker-once-device-results.json](evidence/2026-09-30/worker-once-device-results.json).

`resident-check` і `worker-parked` також використовують **лише `info`**
зі свіжою підготовкою. Тип 2 підтримується native fallback 3→2; generic
список не створює окремих execute/delete libraries. На обох телефонах
resident data/address checks та parked-task checks пройшли із
delete/free/EXIT/FINAL0. `worker-parked` має finite SEM timeout **30000
BIOS ticks**, не 30000 мс; priority15 виконує тільки stores/wait/return.
Він не обробляє STRM. Після тесту повернути exact backup через recovery.
`resident-phase` уже дав негативний результат; повтор без нового
контракту не потрібен. Історичні v1 hashes прив'язані до збережених
артефактів. **V2** додатково повертає negative error при null env/context,
щоб обов'язкові assertions не можна було обійти. На обох телефонах v2
пройшла повторні fresh-preparation прогони; саме вони є доказом.

Статична звірка native loader, RMS return і SEM ABI:

```powershell
python tools/rev/compare_node_loader.py --e90-rom work/evidence/e90/rom --e90-base work/evidence/e90/baseimage.dof
```

Vtable береться з окремого constructor literal кожної прошивки; різницю
адрес code не застосовано до storage vtable. JSON містить hashes, offsets
і перевірені symbolic BIOS data references; ROM bytes не публікуються.

### Підготовка й умови запуску

`prepare_stream.py` зберігає попередні телефонні файли, звіряє очікуваний
SHA-256 поточного DSP, виконує read-only stock clock probe, повертає
оригінальний `ocprobe.log` і перевіряє EXE/hash/DLL читанням назад.
На N95 `--host` оновлює EXE та SHA-1 file; на E90 host встановлюється SIS.
Prepare не запускає c55stream або DSP RUN. Clock probe сам тимчасово
використовує patcher для читання регістрів, без запису PRCM.

Режими `receive-created`, `message-stages`, `messages`, `execute`,
`serial`, `parallel`, `worker-one`, `worker-serial`, `worker-parallel`
**вимагають `--preparation`**. Runner до підключення
перевіряє успіх, апарат/IP, stock guard, restore журналу, час не старше
10 хвилин і збережений DSP/hash. Після підключення він перевіряє uptime
та поточні байти DSP. Помилка підготовки зупиняє запуск до START.
Перезапуск телефона потребує свіжої підготовки.

Приклад чистої перевірки на N95 без RUN; DSP — exact normal backup
цього телефона, а очікуваний hash треба брати з актуального GET:

```powershell
python tools/prepare_stream.py --ip 192.168.3.22 --device n95 --tag prepare_unique --host out/arm/c55stream.exe --dsp work/evidence/n95/stream-v8-messages-prepare-01-before.dll55l --expect-dsp-sha256 5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
python tools/run_stream.py --ip 192.168.3.22 --device n95 --mode info --preparation work/evidence/n95/prepare_unique-preparation.json --tag info_unique
if ($LASTEXITCODE -ne 0) { throw 'Info failed' }
python tools/run_stream.py --ip 192.168.3.22 --device n95 --mode receive-created --preparation work/evidence/n95/prepare_unique-preparation.json --tag receive_unique
```

`info` — create/get-info/delete. `receive-created` додатково ставить get
у pending **до RUN**, потім перевіряє delete/free та cancellation −3.
N95 v9/v10 і E90 v14 пройшли цей режим; він не доводить отримання
повідомлення від виконуваного DSP. Raw allocation тепер має явні 32 байти
за LDD обох прошивок; SDK `TBuf8<20>` має 28 байтів.

Для нового обґрунтованого RUN підготувати відповідний окремий DLL й передати
успішний preparation JSON у runner. `messages` потребує `--deadline 60`
або більше. `serial/parallel --reps 0` і серію вимірів починати після
чистого hello/echo та delete/free, EXIT/FINAL=0. Такий результат ще відсутній.

Runner зберігає попередній журнал до START і запускає inspect перед
режимом. Кожен tag унікальний; докази не перезаписуються. PS спостерігає
процес, WAIT викликається після його завершення. Deadline 5–120 секунд,
reps 0–20000. Pending, timeout, ненульовий EXIT/FINAL не зараховуються як
успіх навіть за наявності STREAM PASS. Журнали — `work/evidence/<device>`.

### Потоковий worker без RUN (v18)

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_stream_node.cmd worker-stream' -TimeoutSec 120 -Log out/worker_dsp_unique.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/worker_arm_unique.log
pwsh -NoProfile -File tools/build_stream_sis.ps1 -Revision 18
```

DLL має generic registration library2. Використовувати лише `worker-one`,
`worker-serial`, `worker-parallel`, `worker-calibrate`, `worker-transfer`;
**штатний execute/RUN заборонено**. Worker-one обробляє 1 пакет, інші режими
за замовчуванням — 8. V18 frame modes приймають `--packet-bytes` (парні
512–4096 Б, включно з32-Б header) і `--frames` (1–4096, one лише1).
Calibrate лишається8×512 Б. Reps 0 перевіряє STRM/echo,
reps 1000–10000 — правильний Q15 dot із корисним ARM CRC 64 КіБ на порцію.
Priority15/stack2048/sysstack512; придатність поряд із audio ще не виміряно.
Join очікує SEM до 5000 BIOS ticks, не автоматично 5000 мс. Task видаляється
тільки після terminated3 та повернення pending buffers.

Починаючи з v17 host на N95 перевіряє чотири live fingerprints dvfs_interface, штатно
резервує MPU режим request0/a2=100 та звільняє його a2=0 до FINAL.
Frame до/після мусить показати100%; усі DSP/bus clocks цим не вимірюються.
Немає PRCM writes або ROM patches. E90 цю N95 гілку пропускає.
Protocol18, як і17, на offset14 повертає абсолютний DSP timestamp замість wire
cookie; pointer cookie лишається обов'язковим DSP create/delete gate.
`worker-calibrate` передає8 echo packets без CRC із паузами100/200/400/800 мс,
записує ARM FastCounter brackets та bounds timer Hz. На800 мс count
відстає від wall time на обох телефонах; не трактувати19.2 МГц як
безперервний wall clock. Countspms164 не є придатним calibration factor.

Приклад N95 після перевірки актуальної адреси й exact normal hash:

```powershell
python tools/prepare_stream.py --ip 192.168.3.22 --device n95 --tag worker_prepare_unique --host out/arm/c55stream.exe --dsp out/dsp/c55stream-worker-stream.dll55l --expect-dsp-sha256 5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
python tools/run_stream.py --ip 192.168.3.22 --device n95 --host-version 18 --mode worker-one --reps 0 --preparation work/evidence/n95/worker_prepare_unique-preparation.json --tag worker_one_unique
if ($LASTEXITCODE -ne 0) { throw 'Worker failed; recover journal before another test' }
python tools/recover_stream.py --ip 192.168.3.22 --device n95 --preparation work/evidence/n95/worker_prepare_unique-preparation.json --tag worker_recovery_unique --restore-dsp
```

На E90 встановити v18 SIS, не передавати `--host` у prepare; використовувати
його normal hash E039E983… і `--exe 'C:\sys\bin\c55stream.exe'` у runner.
Повні hashes/proofs є у device results. Tag завжди новий; preparation
чинна 10 хвилин. Після variant відновити звичайний main DLL на ПК.
Архівація DOFF/ASM/imports: `record_worker_stream.py` з новими revision/report;
для v18 host-version/protocol18. `worker-transfer` вимагає reps0 і не рахує
ARM CRC. Приклад після успішного one, до recovery:

```powershell
python tools/run_stream.py --ip 192.168.3.22 --device n95 --host-version 18 --mode worker-transfer --packet-bytes 1792 --frames 32 --preparation work/evidence/n95/worker_prepare_unique-preparation.json --tag worker_transfer_unique
```

Повна v18 серія: `run_packet_series.py` з явними IP/device/preparation/tag-prefix.
Перевірка та публікація саме збереженої v18 серії:
`summarize_packet_sizes.py --device n95 --out docs/evidence/2026-10-01`.
Вона очікує історичні tags v18; для іншої серії спершу узгодити tags і нову
назву результату. Старі v16/v17 журнали перевіряє
`summarize_worker_stream.py --version 17` (або historical16).
Опубліковані результати
зберігають raw journals і не обчислюють DSP мілісекунди з CLK_countspms=164.

### Відновлення після діагностичного варіанта

`recover_stream.py` спершу отримує журнал і current DLL, перевіряє INFO/PS.
**Без `--restore-dsp` це лише читання журналу**: complete=true не означає
повернення DSP. З цим прапором повертається exact backup із preparation;
обов'язково перевірити dsp_restored=true та final hash. Live c55stream
або невідомий hash DLL забороняє restore. START/WAIT/KILL не викликаються.
На N95 фактично перевірено заміну messages/stages DLL назад на normal,
PUT і final GET рівні. E90 idempotent path також перевірено.

```powershell
python tools/recover_stream.py --ip 192.168.3.22 --device n95 --preparation work/evidence/n95/prepare_unique-preparation.json --tag recovery_unique --restore-dsp
```

### E90: поточний v18 та попередні встановлення

V18 встановлено через observed installer1.00(18), host29760 Б
SHA-256571C5A6221C7E7815558A2C3AE5F6665D8D7DE0B82D676488869C7BAA260F14F.
GET і runtime збігаються; 22 runs/587 correct packets пройшли на кожному.
Докази: `e90-host-v18-delivery.json` (момент OPEN),
`e90-host-v18-installed.json`, `e90-packet-sizes-v18-results.json` та
`e90-packet-sizes-v18-device-status.json` у `docs/evidence/2026-10-01`.

V17 SIS16776 Б SHA-2569C04181AE3A79FF4B54C73F3E2446A671CF65D1274436F461DFD18C51F8F8460
встановлено через фактичний installer. EXE28456 Б на обох телефонах
C8B08E8C0442F1E58CB07C40B5299E4FE6FD5DE873B3F3536014A72C1B284163;
GET та runtime inspect збігаються. One/multi/Q15/3 calibration/3 pairs
пройшли на обох. Delivery snapshot installed=false описує момент OPEN;
final checkpoint доводить встановлений EXE. Збережено попередні результати:

V16 встановлено через демон із SIS 14604 Б, SHA-256
6422DAE688C1C071843F5B26DB0707EE0CC6E2DC9EE57FAADBE6F9AC2C93BC5D.
Установлений C:\sys\bin\c55stream.exe 24464 Б на E90 і E:\sys\bin на N95:
AB016003DD44751FDDE19B57C37B9FD79E0D3A1BC40C0462EE4E9ADFAFFC43AB.
One/multi/Q15/3 pairs пройшли; raw delivery snapshot з installed=false
описує момент OPEN до встановлення, а final checkpoint доводить новий EXE.
Нижче збережено історичний результат v14.

Запис у E90 sys/bin демоном не дозволений у перевіреній конфігурації;
використати SIS. Пакет revision14 доставлено як `E:\c55stream-v14.sis`
і встановлено користувачем. GET установленого EXE22408 Б збігся з локальним
SHA-256 `5F1C77CF7914312818F63D77AA950DED5B1208F454E986CF55C68EAD9E47274A`.
Пакет не встановлює DSP DLL. Наступна збірка пакета на ПК:

```powershell
pwsh -NoProfile -File tools/build_stream_sis.ps1 -Revision 18
python tools/run_stream.py --ip 192.168.3.21 --device e90 --exe 'C:\sys\bin\c55stream.exe' --host-version 18 --mode inspect --tag e90_inspect_unique
```

`patcher-check` v14 пише чотири байти **лише у власну RAM** через відомий
control105 і читає їх через volatile pointer. Kernel patch, PRCM і DSP
RUN відсутні. На обох телефонах отримано `PATCHER OWN RAM PASS` та
EXIT/FINAL=0. Він придатний для уточнення відмови primitive перед clock guard:

```powershell
python tools/run_stream.py --ip 192.168.3.21 --device e90 --exe 'C:\sys\bin\c55stream.exe' --host-version 18 --mode patcher-check --tag e90_patcher_unique
```

E90 до перезавантаження двічі не пройшов patcher self-test із −20.
Після перезавантаження v14 own-RAM test та свіжий stock guard пройшли:
m86/div3, HAL ARM330000, firmware math DSP220160 kHz. Конкретна причина
попередньої відмови не доведена. Після guard original ocprobe.log1249 Б
повернуто побайтово. Нормальний DSP E90 має окремий hash E039E983…;
N95 backup не можна використовувати як його original restore.

Stock guard звіряє UID/profile і результат restore окремо: N95 100,
E90 1. У старому ocprobe загальний напис DoControl неточний: на E90 це
порівняння шести live Usbc words, а на N95 — штатний DVFS відсоток.
На E90 v14 create/info/delete та receive-created завершилися чисто,
без DSP RUN. До нових RUN потрібен уточнений message/lifecycle контракт.

### Керування установником через одне з'єднання

`live_device.py` приймає JSON-операції зі stdin і виконує весь I/O
послідовно. Між командами кожні 2 секунди йде INFO. З'єднання перевіряє
апарат за екраном, не перепідключається й не шукає інший IP; журнал
створюється лише за відсутності файла. Межа тривалості 30–600 секунд,
очікування однієї daemon-команди — 30 секунд. На E90 heartbeat і файлові
операції перевірені, але подальший обрив з'єднання лишився.

Запустити в інтерактивному терміналі, указавши нове ім'я журналу:

```powershell
python -u tools/live_device.py --ip 192.168.3.21 --device e90 --log work/evidence/e90/installer_unique.txt --duration 300
```

Далі вводити по одному JSON-об'єкту на рядок, наприклад:

```json
{"cmd":"FG"}
{"get":["E:\\ps1_daemon.log","work/evidence/e90/daemon_unique.log"]}
{"close":true}
```

GET не перезаписує локальний файл. OPEN/KEY виконувати за фактичним станом
установника; не надсилати клавіші за старим знімком. Цей клієнт не замінює
version guard, збереження попереднього журналу та перевірки `run_stream.py`.

Інструменти `tools/rev` використовують спільні відносні шляхи. Змінна `C55_ROM_DIR` задає каталог `sys/bin` іншого розпакованого ROM. Приклад статичної перевірки:

```powershell
python tools/rev/exports.py bridgeapi.dll
python tools/rev/compare_node_info.py --e90-rom work/evidence/e90/rom
```

Друга команда звіряє LDD get-info та його PDD vtable/getter у двох
прошивках. Вона не підставляє загальну різницю адрес N95 для PDD E90;
відмінний BL та адреси його import stubs перелічено окремо. ROM залишається
локально; JSON містить hashes і контракт 112-Б record.

Перевірки 2026-09-30: ARM і DSP збірки завершилися з кодом 0; перевірка середовища й JSON пройшла; експортний список `bridgeapi.dll` містить очікувані 39 ординалів. Команди й контрольні суми наведені у `docs/SESSION_2026_09_30.md`.

## WSOLA / ARMv6 — поточна збірка20

MMP research host має -march=armv6 -mtune=arm1136j-s -fomit-frame-pointer;
SDK UREL -O2 -fno-unit-at-a-time. Додано wsola_reference.cpp і DSP
wsola_dsp.c (contiguous RPT/MACM dot), input1792/output48 Б.
build.cmd clears c55stream.o і wsola_reference.o: SDK не invalidates їх
лише за MMP compiler-option change. Перед доставкою verified244-byte ARM
body, DOFF/imports/ASM і source/host hashes: artifact6/codegen evidence.

Builds: tools/build.cmd, tools/build_stream_node.cmd worker-stream,
tools/build_stream_sis.ps1 -Revision20. Dedicated worker archive незмінний;
після серій tools/build_stream_node.cmd перебудовує main normal DLL.
run_stream.py default host20; для historical evidence вказувати версію явно.
WSOLA series helper має --host-version19/20. Screenshots installers можуть
тривати понад8s; daemon native command OPEN, timeout30s, observed KEY/SHOT.
OPENSIS не підтримується. Відтворення/limits — WSOLA.md.

Combined reference для host24 (вже виконаний контроль, не команда повтору):
`python tools/prepare_native_library2.py --combined` створює local DOFF4476 Б
із properties0/library2 в одному packet. Non-registration packets і
relocations exact; DLLdump passed. Proof —
`e90-d0-native-library2-combined-derivation.json`, artifact30 —
`d0-native-copy-host-v24-combined-artifacts.json`. Host/SIS ті самі v24/package28.
RUN4 передав8 exact echoes, але delete−33/pending; це failed lifecycle.
`e90_task_session.py` тепер має connect timeout8s тільки у E90 session;
за трьох post-reboot connect failures наступний retry чекає зміни transport.

Поточний E90 diagnostic — host26/protocol26, `worker-message`, package33.
ARM/DSP build EXIT0,25 imports/DOFF/ASM checked; immutable artifact33.
Finite CREATED worker sends one MSG606 and read-only snapshot, no RUN.
Default checkpoint checker використовує цей artifact; старі proofs історичні.
Пряма заміна нашого C:\sys\bin\c55stream.exe та C:\sys\hash\c55stream.exe
дозволена людиною: `e90_task_session.py --action deploy-host --host-version 26`
з matching `--artifact-proof` зберігає GET backups до PUT і звіряє GET після.
`restore-host` повертає exact saved host20 і exact saved hash; тільки за PS0
та original DSP. Installer більше не потрібний. Новий worker-msg01 мав
failed create-only preflight delete−33/pending до MSG/RUN; повторювати його
не можна. Далі лише після reboot/GET/PS0/restore з пропущеним no-input preflight.
