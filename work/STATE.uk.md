# Стан продовження дослідження

## Передача Claude04.10 — завершення поточних робіт за запитом користувача

Поточний дослідницький етап логічно закрито handoff, нових phone commands
і hardware experiments не запускати автоматично. Емулятор не редагували.
docs/CLAUDE_PS1_HANDOFF_2026-10-04.md: D0/D1/D2 evidence, paired timings,
actual job/packet formats, source entry points, strict async conditions,
memory/lifecycle limits, version/DSP hashes, offline verification.
Рішення currentWSOLA/MDEC/plainSPU: залишити ARM (0/2520 blocking wins
проти current kernels до setup). Повний початковий план не complete:
DSP endpoint і ARM caller/context cache completion не прийняті; E90
original EXE/hash/journals restoration і frequency qualification відкладені.

Final current work: повні compiler listings deployed DSP63/65/67 опубліковано
з build/results hash binding. Independent verifier PASS: payload stores→
4/5completion words→RET→read-onlyDCR→timing/notification→STRM_issue.
Це compiler order, не linked-machine decode чи OMAP SDRAM fence proof.
Master evidence verifier PASS incl compiler-order; телефонам команд немає.
N95 останній read-only checkpoint09:32:35UTC originals5equal/PS0;
E90 no commands. До відновлення E90 — GET current journal/PS before writes,
then own originals restoration; не починати DSP RUN із цього handoff.
Previous checkpoint8382b1dfda3f9de8ddcf36eeffc2a2cd1d105d06 pushed exact.

## Актуально04.10: N95 зараз; E90 відкладено користувачем

Requirements acceptance checkpoint: current N95 original assignment
зіставлено з D0/D1/D2 evidence; D2 measured-job verdict delivered,
full-game/audio implementation не є поточним дорученням. D1 publication
gate та E90 restoration/frequencies залишаються відкритими, ціль active.
Published complete N95 D0 inspect/create/3RUN journals(24packets total)
і2stock probes; portable verifier більше не потребує ignored D0 archive.
Fresh N95 verify04.10 09:32:35UTC: INFO/PS/GETonly, files5equal_original,
c55stream/ocprobePS0,daemon launch tuple62209boot0byn unchanged.
Master tools/verify_n95_acceptance.py PASS: D0/native61/CPU64/MDEC65-66/
SPU67/WSOLA68/dependencies/ARM-cache; no new DSP RUN/deploy, E90 no commands.
docs/N95_ACCEPTANCE_2026-10-04.md + machineaudit/finalstate publication.
ARM-cache checkpoint93e08daaeae026714d751c5323a372278f77ddae pushed exact.

Saved N95 ARM cache path audit завершено: utility2→kernel378clean→376
invalidate, exact module identity зіставлена з попереднім DMM ABI.
46 kernel sites/10 branch targets; published109 words/436B,7ranges,
independent verifier decode13 CP15 operations PASS. Clean MVA/SetWay
обидва закінчуються DSB; invalidate MVA52B без explicit DSB, whole-cache
clean-invalidate з DSB. Runtime thresholds не dumped, обидвіbrancheschecked.
Це exact ARM-side barrier evidence, не DSP endpoint acknowledgement proof.
SPRU376A4.4.3.1 старе посилання перевірено за localprimarytext: accurate,
generic pipeline pending/bypass, не OMAPfence. No phone commands/E90access.
docs/N95_ARM_CACHE_2026-10-04.md + audit/verifier/json.
Dependency checkpoint0ad8097788edbbda9722f685de2b852e9c38b926 pushed exact.
Next: DSP endpoint contract and caller/context cache-completion semantics;
D1/D2in_progress, E90 tomorrow.

Read-only dependency audit currentWSOLA/MDEC/SPU завершено: immediate
result consumers/mutable buffers простежено; незмінені blocking calls
W0 за структурою, useful async guest-work budget не виміряний.
Same-ARM model H+max(D,W)+S/N<A+W потребує H+S/N<A.
2520 full-job timings повторно checked з published hashed journals;
serial interval outside notification<A при S0: MDEC1/1080, SPU0/1080,
WSOLA359/360. Passing є лише necessary, не виграш; elapsed lower bound
умовний для тієї самої stage envelope, не production CPU minimum.
32768 strict model boundary cases PASS. Phones/emulator untouched.
docs/N95_OFFLOAD_DEPENDENCIES_2026-10-04.md + audit/verifier/json.
WSOLA68 checkpoint257339aad577365c7a48a4557e0181021b0aa47d pushed exact.
Next: independent OMAP2420 endpoint publication; concrete async W/state
contract still open. D1/D2in_progress; E90 tomorrow, no commands.

WSOLA68/host53/protocol40: exact current shell SMLAD snapshot(CSL343/O2/
ARMv6), retained exactDSP63,8pilots+360paired jobs. A current p50337.601us,
scalar1003.265us,H+D ready1098.633us; current winners0/360 до S, paired
scalar/current p50ratio3.017x. S p50865080us logging,W0,CPUunmeasured.
460800ringwords16,720DCRreads0000/WPE0,8stock brackets; current keepARM.
Own early concurrent restore after acceptedseries1/2 stoppedthirdattempt
pre-START host-mismatch; noPUT/START infailedtransport. Originals5verified01.
OS perphone session+whole-runner lockadded/tested; specificrecovery02
samebinaries thirdseriesstock02complete; originals5GET/SHAequalPS0verify02.
Daemon tuple62209stable,no reboot. Source/out53; typedDSP63used,genericDSP67.
docs/N95_WSOLA_CURRENT_2026-10-04.md + independentverifier/44testsPASS.
At WSOLA68 checkpoint: next endpoint publication and dependency audit;
read-only dependency audit completed above, useful W still unmeasured.
D1/D2in_progress. SPU67commit2e675c9c20edeab93de34e0ba8fb038738a4b5f4
pushed exact; WSOLA68 checkpoint257339aa pushed exact.

SPU67/host52/protocol42 завершив24 pilot +1080 full jobs:1/8/24 voices
по64 samples, current actual SMLAW ARM assembler baseline,128 exact sums32/job.
138240 sums32 і2672640 ring words16 у full series; all pages/ownership/
teardown PASS,8 stock brackets,2160 DCR reads0000/WPE0.
A p50=3.576/27.180/40.531us; H+D pack→ARM128sums ready=1617.432/
3295.898/3540.039us; oracle checks outside; blocking winners0/1080 до S.
S p50=863494us includes lifecycle logging, W0, CPU unmeasured(-1).
Plain mix залишити ARM; це не fullSPU/gamePCM/mutable-state verdict.
Н95 originals5 restored GET/SHA-equal, PS0, daemon tuple62209boot0byn stable;
source/out52/DSP67, immutable archive збережено. E90 жодної команди.
docs/N95_SPU_RING_2026-10-04.md + publication verifier/39 sessiontests PASS.
Next: independent endpoint-publication evidence та useful ARM W/job dependency
audit, current WSOLA SMLAD baseline; E90 frequency/restoration завтра.
D1/D2 загалом in_progress. SPU67 checkpoint публікується окремо.

SPU offline boundary audit після MDEC: GCCE463 ABI int/pointer4B,
NSSIZE914, ADSR16, SPUCHAN56, sample_buf64, SPUInfo3840(no thread)/5440
(thread), optional work_item8396, worker33840B. Повна SPU RAM512KiB;
mix_plain не є весь doSamples. Plain24-voice job із samples/volumes/sums32
вміщує64 samples (6848input/512output bytes,15/2 slots), max66;68 не fits.
Next hardware probe: current HAVE_ARMV5 smlawb/smlawt baseline + exact
sum oracle, only mix_plain; decode/ADSR/fmod/reverb/IRQ залишити ARM.
На момент offline audit SPU hardware вимір НЕ виконано;67 вище його додав.
docs/N95_SPU_BOUNDARY_2026-10-04.md;
tools/audit_spu_boundary.py compiled layout + capacity calculations.
MDEC checkpoint1e6ea1c2ca23b152ef489e96872a34839c6f1267 pushed exact.

MDEC65/host50 та66/host51/protocol41 завершили кожен3×8 pilots і3×3×120
full jobs,1080 jobs/2520 macros,483840 RGB24 uint32 words,3409920 ring
uint16 words exact. Джерело — current local PS1 MDEC kernel snapshot;
32-bit C55 adaptation, Python oracle + ARM343/463, no emulator edits.
66 reused exact DSP65; H+D закінчується після RGB24 copy в ARM memory,
oracle checks поза A/H+D. Batch1/2/4 p50 A463=78.201/110.626/295.639us,
H+D=2655.029/4272.461/7690.430us; winners0/1080 без setup. S p50=840178us
includes lifecycle logging; W0, CPU unmeasured(-1), DSP raw ticks unconverted.
Усі2160 full-series DCR reads/cohort0000/WPE0; current publication proof
все ще відкритий. N95 після КОЖНОГО cohort originals5 restoredGET/SHA,
PS0; daemon62209boot0byn stable. Source/out51/DSP65. E90 жодної команди.
docs/N95_MDEC_RING_2026-10-04.md + independent publication verifier/34 tests
PASS. Next N95: actual SPU/state job boundary/budget та endpoint publication;
асинхронна useful W не виміряна. D1/D2 залишаються in_progress.
CPU64 checkpoint70902bbe59fc22030f9cb0fef12aa8f4ad376060 pushed exact;
MDEC checkpoint публікується окремо.

CPU-window64/host49/protocol38 завершив pilot120 packets і3×4 fullruns,
9360 correct packets,6 stock brackets, pages/ownership/teardown clean.
Batch1/2/8/15 p50 exchange915/1190/3021/5126us. Weighted CPU45.37/45.87/
48.09/45.68% over whole120-job outer windows includes pack/cache/full
checks/final settling yield; no per-frame CPU reads/file I/O/ARM baseline
inside. Scope is correctness harness, not pure wait/production CPU.
Full-window useful bidirectional0.712/0.960/1.357/1.500MB/s.
Нове DSP64 SHA00FCD176… відрізняється від52/61; старі typed files/archive
збережені. НіякихDCR/PRCM writes; current64 WPE не виміряний.
N95 originals5 після64 restored GET/SHA-equal, PS0. Source/out host49.
Докази docs/N95_RING_CPU_2026-10-04.md; verifier +27 tests PASS.
Actual WSOLA verdict додано до docs/PS1_CANDIDATES_2026-10-01.md.
Next N95: independent endpoint publication proof та actual MDEC/SPU
job budget/state contracts; no emulator edits. E90 до завтра не торкатися.
Counter checkpoint c8d005fc99704e329b69ed12e5bdccb7fe18eaeb pushed private
main, ls-remote exact; CPU64 публікується окремо.

No-DSP counterprobe v1 завершив3×36 calibration samples. Raw busy1/10ms
повертає CPU0 у8/9 samples кожен; raw sleep10ms має2/9 deltas>wall.
Усі54 samples із yields на boundaries маютьCPU≤outer wall; late slice
accounting відтворено безDSP. Це не exact firmware-source match.
Counterprobe EXE/hash/log спочатку absent, exact verified і прибрані
після3 EXIT0; originals c55stream/ocprobe не змінювалися.
Докази docs/N95_CPU_COUNTER_2026-10-04.md; verifier/tests25 PASS.
Короткі historical N95 ring CPU percentages теж unqualified raw arithmetic.
Aggregate ring CPU window із settling boundaries виконано наступним64 вище.
WSOLA checkpoint d9e9a8de8bc019bdba93924030743e387474129a pushed private main,
ls-remote exact. Counter calibration checkpoint публікується окремо.

WSOLA63/host48/protocol40 завершив pilot8 і3×120 actual kernel jobs.
Offset/score/scored exact, native ownership/pages/teardown PASS,6 stock
clock brackets. A p50=1155.853us; H+D pack→result p50=1983.643us;
лише16/360 paired samples швидші до setup. Інструментований S p50=828063us,
includes synchronous journal Write/Flush; не pure create/minimum cost.
W=0, parallel gain не виміряний. 720 DCR reads0000/WPE0 саме63.
CPU usage unqualified:320/360 deltas більші за transfer wall; потрібна
окрема калібровка. Raw DSP ticks/countspms не перетворювати в ms.
N95 originals5 після63 GET/SHA-equal, PS0; source/out48/WSOLA63.
Докази docs/N95_WSOLA_RING_2026-10-04.md і tools/verify_wsola_publication.py.
Checkpoint25a365686b814b9e8276d963efefce83e9a48db2 pushed private main;
WSOLA63 публікується окремо. D1/D2 загалом in_progress: publication
contract/qualified CPU та MDEC/SPU verdicts відкриті; емулятор unchanged.
No-DSP counter calibration наступним уже виконано вище.

Ціль відновлена й активна. N95 native61 завершив3 серії/12 runs/9360
packets,6 stock clocks PASS, originals5 GET/SHA-equal restored.
Новий cohort повільніший за old54 (batch15 p50=5249 проти2716us);
не змішувати samples і не заявляти причину без перевірки.
Distinct DCR62/host47/protocol39 pilot PASS:120 packets/8 exchanges,
усі16 reads0000/WPE0, stock clocks до/після. Originals5 після pilot
знову restored+verified, PS0. Source/out47/DCR62, old ring61/archive unchanged.
Докази — docs/N95_DCR_2026-10-04.md. WSOLA наступним63 уже виміряно вище.
Checkpoint c207070e16f2b25b635c53e299a33c5708d2e969 pushed private main,
independent ls-remote confirmed. Нові DCR62 зміни публікуються окремо.

E90 не опитувати й не відновлювати до завтрашнього повернення до нього.
Source audit й exact timeline — docs/E90_DAEMON_REBOOT_2026-10-04.md.
User-confirmed reboot після завершеної KEYdown/SHOT/GET; наступний
connect не надіслав жодної команди. GET daemon log успішний, tick reset
підтверджує system restart; fault reason не отримано. startTick/boot/by —
daemon launch/classification, не unique phone boot ID.
Відомий E90 host46/original DSP, originals restore pending; ringclock
зібрана, але4 deploy attempts не дійшли до PUT. Driver API RDomain102/104
проти standard105/100 під shared name доведено offline, це не reboot cause.

Актуальний короткий checkpoint 2026-10-04 —
[HANDOFF_NATIVE_RING](HANDOFF_NATIVE_RING_2026-10-04.md).
E90 native61 пройшов3 повні серії/9360 packets, originals5 повернуто обом.
Clock self-test−20 не зарахований як stock; потрібен Open4All E90 без reboot.
Нижче — історія; поточні D1/D2 залишаються in_progress.

Нижче збережена хронологія. Поточний стан — останній датований розділ;
критерії й audit — `work/PLAN.md` та `work/FINAL_AUDIT.md`.

## 2026-09-29: початок

Повне доручення й критерії записані у `work/PLAN.md` перед змінами коду. Поточні статуси — `work/features.json`.

Перевірено: `.git` немає; вихідні тексти та апаратні журнали залишаються серпневими; від Claude наявні рішення про обв'язку та два запити без результатів дослідження. Відомі старі шляхи D: у скриптах. TI CGT знайдений на G:, SDK і dllcreate — на H:.

Виконано: створені план, перелік вимог і цей файл стану.

Наступна дія: відновити відносне налаштування середовища, зібрати обидва боки; паралельно читати незалежні локальні джерела контракту потоків і перевірити активний GitHub-обліковий запис. Після підготовки контракту — апаратні експерименти, а не перебір викликів.

Незавершено: F01 (перевірка сценарію), F02–F08. Користувач підтвердив приватний GitHub-репозиторій 2026-09-30. Активний акаунт у поточній перевірці — 1234bpv. Обидві адреси 192.168.3.22 і 192.168.3.21 відповіли на TCP:2323; ідентичність телефонів ще треба перевірити через INFO.

## 2026-09-30: середовище відновлено

F01 і F02 завершено: переносні шляхи, bounded runner, перевірка JSON/інструментів, успішні збірки ARM і DSP, відносні шляхи реверсу. Докази: `docs/BUILD.md`, `docs/SESSION_2026_09_30.md`, журнали `out/*build-desktop.log`.

Обидва телефони відповіли на INFO з відповідними екранами; тест DSP ще не запускався. Локальний Git ініціалізовано, публікація приватного репозиторію наступна. Після неї — статичний розбір каналів/клієнтів ROM, резервні копії телефонних файлів і мінімальний обґрунтований тест.

## 2026-09-30: GitHub і контракт потоків

F03 завершено: приватний https://github.com/1234bpv/TMS320C55x, main `e35a7315dc8d86add484d36f2bc1f698b9d4897e`; віддалений HEAD звірено. F04 триває, результати — `docs/STREAM_RESEARCH.md`. Штатний BAL використовує task14/task16 для буферів; task7 запускає execute, fn6 видаляє. Знайдено vtable DNode й 176-байтові stream props. Уточнюються DSP STRM ABI, props та очищення.

Прочитані поточні DSP dividers і профілі обох телефонів; старі ocprobe.log збережено. N95 m=111/div=3, E90 stock/div=3. Пряма GET бібліотеки E90 не дозволена (-46); потрібне читання з окремого процесу або вже перевіреного user-mode ROM dump. На телефонах поки змінено лише ocprobe.log через read-only запуск; повернути обидва з backup після дослідів.

F05–F08 не завершено. Наступне: мінімальний ARM-хост і потоковий DSP-вузол після статичної перевірки аргументів; E90 firmware profile; практичні кандидати PS1/браузера.

## 2026-09-30: поточна апаратна перевірка

Результати й контракти: `docs/STREAM_RESEARCH.md`; практичні кандидати: `docs/APPLICATION_CANDIDATES.md`. F04–F08 тривають. Власний C55x-вузол має один input/output, контекст у `env->moreEnv`, запуск execute окремо від create. Жодного успішного потокового пакета чи виміру паралельного прискорення поки немає.

N95: після першого перезапуску перевірено stock m86/div3. Base-only, create/delete, free task успішні; контекстний create займає 7415–7446 мкс в окремих прогонах. Smoke execute підтвердив RUN, але delete завершився таймаутом. Нормальний контекстний execute теж підтвердив RUN; перший put/get отримав −2, останній запис — BEGIN delete. Після цього користувач перезапустив телефон. Це не доказ автоматичного перезапуску саме в цій спробі.

Host v4 зібраний (`out/stream-arm-v4-build-fixed.log`), встановлений через E:\sys\bin. Окремі buffers/create тести завершені з EXIT/FINAL=0. Ord30/29 mode2 виділяє й звільняє два 4096-байтові буфери; get-state копіює 280 байтів, тому використано явний масив, а не 276-байтовий SDK TBuf8<268>. Firmware не заповнює всі stream-поля для кожного виду з'єднання; їх не можна трактувати як валідні дані без перевірки типу.

E90: live ROM, UID 20002496, 39 bridgeapi exports звірено. Користувач допоміг установити SIS і повідомив про перезавантаження телефона. Після відновлення демона inspect підтвердив **C55STREAM v3**; base-only і власний контекстний create/delete/free task успішні, create=6774 мкс. Потоковий execute на E90 ще не викликався.

Зв'язок контролюється `tools/strict_net.py` і `run_stream.py`: лише явна адреса та перевірений екран, без пошуку іншого телефона. WAIT викликається лише після PS=неактивний, бо старий daemon WAIT міг повторно Resume живий процес і впасти.

Наступне: уточнити PDD stream-connection поля й очищення після RUN, перевірити перший пакет на новому доведеному контракті; далі correctness та три парні serial/parallel прогони. E90 поки має v3, N95 — v4; назви режимів не можна застосовувати до непідтвердженої старої версії хоста.

**Відновлення телефонів ще не виконано.** Старі ocprobe.log обох телефонів і 12288-байтовий E90 romdump.bin збережені у `work/device-backups`. Після експериментів повернути їх із перевіркою байтів. Нові c55stream EXE/hash/DLL/log на N95 та E90 research SIS/DLL/log прибрати або явно залишити за рішенням користувача. Старі dsptest.exe, bench.dll і benchmark logs не замінювалися. Новий DSP DLL на E90 до запису був відсутній (STAT −1).

Останні зміни коду й звіти ще не закомічені та не відправлені на GitHub; F08 потребує синхронізації після перевірки.

## 2026-09-30: поточний стан після 8 пакетів

N95 host v6, connection=0: **8 правильних пакетів за один create/RUN**,
serial reps=0. Дані/послідовність/довжини/CRC перевірені; ненульовий Q15 і
паралельне прискорення ще не перевірені. Delete/status/FINAL/EXIT=−2,
тому прогін не є повністю успішним. Журнал у
`docs/evidence/2026-09-30/n95-stream-host-echo-v6.txt`.

Наступний DSP idle-first тест втратив зв'язок. Його телефонний журнал ще
не прочитано; не робити новий запис або START до отримання цього журналу.
Користувачу надіслано запит відновити N95 і повідомити, чи був перезапуск.
Повторне INFO N95 — connect timeout; E90 — доступний.

Статичний lifecycle уточнено: control 6 через PDD slot +92 сам надсилає
RMS_EXIT, ACK запускає delete. V7 виправляє ранній вихід після marker:
input повторно issue, execute чекає RMS_EXIT, потім idle/reclaim. Додані
компонентні таймери й перевірка DSP protocol version 7. V7 ARM/DSP і SIS
revision 7 зібрані та перевірені локально; **на апараті ще не запускалися**.

На N95 лишається host v6 та DLL останньої невдалої idle-first спроби;
на E90 — встановлений host v3 і старий context DLL. Новий локальний
`out/dsp/c55stream.dll55l` є v7, його не можна приписувати v6 журналу.

Наступне: GET N95 log і remote DLL до запису; inspect/create v7,
execute без host frames з control 6; після чистого EXIT/FINAL=0 — serial
reps=0, Q15 correctness і три парні serial/parallel прогони. Лише після
стабільного N95 lifecycle оновити й тестувати E90. F04–F08 лишаються
in_progress. Restore телефонів, описаний вище, ще не виконано.

Runner тепер зберігає попередній log і виконує inspect v7 перед DSP-режимами.
На живому E90 v3 перевірено відхилення mode=create до DSP driver calls:
запускався лише inspect, EXIT/FINAL=0. Доказ у docs/evidence.

Повернено оригінальні E90 `ocprobe.log` (1249 Б) і `romdump.bin` (12288 Б).
Обидва GET після PUT побайтово збігаються з backup; INFO успішне.
Доказ: `docs/evidence/2026-09-30/e90-restored-originals.json`.
N95 ocprobe restore та видалення research-файлів обох телефонів лишаються
незавершеними; SIS/DLL на E90 залишені для наступної апаратної перевірки.

Дослідницький checkpoint `aa802d0f5e49da9976d650c5abbfd4f2323d097f`
відправлено до private main; локальний і віддалений HEAD звірено.
Це синхронізація поточного стану, не завершення F04–F08.

## 2026-09-30: карта F04 завершена, апаратна перевірка очікує N95

F04 complete: у STREAM_RESEARCH додані точний статичний контракт node state
notification (task5/task6), одноразові й пакетні кроки, межа overlap із
create та матриця всіх кандидатів із джерелами/невідомими частинами.
Апаратні перевірки DMM/ring/власних messages не заявляються; це не негативний
висновок про їхню можливість. F05–F08 лишаються in_progress.

Попередній goal turn був progress: v7 зібрана, runner guard перевірений,
E90 originals повернені, код/звіти відправлені до private main. У поточному
продовженні повторне N95 INFO/GET знову дало connect timeout. Нових START
на N95 немає; журнал idle-first спроби не прочитано. Наступна апаратна
дія лишається GET цього журналу після відновлення телефона користувачем.

## 2026-09-30: підготовка E90 v7 та межа подальшого виконання

Попередній goal turn був progress: F04 карта завершена й відправлена до
private main, HEAD звірено. У третьому послідовному goal turn N95 знову
дав connect timeout; аварійний журнал idle-first недоступний.

Незалежна підготовка E90: INFO успішне, PS c55stream=0; перед оновленням
збережені E:\c55stream.log, DLL (3496 Б) і SIS (6336 Б) у
`work/evidence/e90/stream-before-v7.*`. SIS revision 7 (10192 Б) записаний
у E:\c55stream_sha1.sis і відкритий через OPEN. Знімок install-v7-02.bmp
показав запит «Установить C55Stream Research?». До надсилання KEY lsk
нове TCP-з'єднання вже отримало timeout; ця команда **не надсилалася**.
Встановлення v7 не підтверджено. Нового DSP RUN на E90 немає.

Відновлення ocprobe.log/romdump.bin E90 з попереднього turn залишається
доведеним; ці файли в підготовці SIS не змінювалися. Користувачу надіслано
запит завершити установник і відкрити демон на E90, а також відновити N95.

Без відновлення телефонів F05 не можна перевірити або виконати N95 restore;
F06 чекає inspect встановленого v7, base/create і потоку; F07 потребує
вимірів каналу; F08 — апаратних доказів та остаточного restore. Локальні
збірки, карта каналів, runner guard, звіти та публікація вже перевірені.
Наступний крок після зовнішнього відновлення: N95 GET log/DLL перед будь-яким
новим START; E90 inspect v7 перед будь-яким DSP-режимом. Goal не завершений.

## 2026-09-30: повторна доступність E90 та перевірка встановленої версії

Після повідомлення користувача про доступність E90 відповів на INFO:
800×352, AP Huawei, script IDLE. PS перед запуском не мав активного
c55stream. Попередній журнал збережений, новий inspect через
`C:\sys\bin\c55stream.exe` завершився EXIT 0 Kill / FINAL 0 та показав
**C55STREAM v3**, MachineUid 20002496. Runner відхилив стару версію після
inspect; DSP не викликався. Докази —
`docs/evidence/2026-09-30/e90-stream-installed-v3-after-recovery*.txt`.

Знімок `work/evidence/e90/install-v7-recovery-01.bmp` показав список
встановлених застосунків, а не активний установник. Нового OPEN, KEY,
запису EXE/DLL або DSP START у цьому продовженні немає. Після знімка
TCP-зв'язок E90 знову став недоступним. N95 за 192.168.3.22 не відповів
на жодну спробу, тому його аварійний журнал і DLL ще не прочитані.
Чотири додаткові обмежені перевірки обох відомих адрес завершилися connect
timeout; `docs/evidence/2026-09-30/device-recovery-unavailable.txt`.
Це не встановлює перезапуск або причину відмови будь-якого телефона.

Користувачу надіслано запити перевірити N95/IP та відкрити демон E90,
завершивши установку вже записаного SIS v7. Після відновлення: зберегти
журнал демона (`E:\ps1_daemon.log`) і N95 c55stream.log/DLL до нового START;
E90 оновлення завершити через спостережуваний установник, потім inspect.
Для UI спробувати одне TCP-з'єднання; це ще не доведене виправлення
нестабільності транспорту. F05–F08 лишаються in_progress.

Пізніше E90 двічі знову відповів; забрано журнали демона
`work/evidence/e90/daemon-after-recovery-02.log` та
`daemon-heartbeat-02.log`. У них є нові записи запуску, однак точний вид
відновлення користувач ще не уточнив. Наявний SIS відкрито через OPEN,
перший знімок показав підготовку встановлення. Наступний SHOT у тому
самому TCP-з'єднанні отримав timeout. KEY не надсилався.

Додано `tools/live_device.py`: один перевірений апарат, послідовні команди
зі stdin, INFO кожні 2 секунди між командами, унікальний повний журнал,
межа тривалості 30–600 с. Python compile/help успішні. На E90 перевірені
успішні heartbeat INFO, GET журналу, SHOT/GET/DEL. Останній знімок показав
головне меню без установника. Після нього наступний INFO завершився
ConnectionResetError; клієнт закрив з'єднання, нових запитів не надсилав.
Докази — `e90-installer-heartbeat-transport.txt` та
`e90-daemon-latest-sessions.txt` у docs/evidence/2026-09-30.
Це **не доведене виправлення** зв'язку. Подальші GET SIS / START inspect,
підготовлені після цього, не надіслані: клієнт уже завершився.
Остання перевірена встановлена версія E90 лишається v3; DSP RUN немає.
N95 лишається недоступним. Шлюз 192.168.3.1 відповів на ICMP (2 мс),
тому поточна перевірка не показала загальної втрати LAN на ПК.

У наступному вікні E90 новий inspect (`stream-installed-after-restart-03`)
знову завершився EXIT/FINAL 0 та підтвердив v3. GET SIS повернув 10192 Б:
байти повністю збігаються з локальним revision 7, SHA-256
54A214227DFFF6CF0638A007F9980331D1F06888B654AFF28831FA4EAD174AB9.
Доказ — `docs/evidence/2026-09-30/e90-sis-v7-readback.json`.
Це перевірка доставленого пакета, а не встановленого EXE.

Новий live-клієнт успішно виконав INFO heartbeat, GET SIS, GET daemon.log
та FG. Наступний INFO отримав ConnectionResetError (10054). OPEN і
підготовлений SHOT зі step=2 **не виконувалися**: їх не було у протоколі
вже завершеного клієнта. Транспорт —
`docs/evidence/2026-09-30/e90-heartbeat-without-open-or-shot.txt`;
керувальні символи відповіді FG там екрановані, оригінал збережений локально.
Отже, повний SHOT не є необхідною умовою обриву; зменшений SHOT ще не
перевірений. Нових UI-повторів без відновлення й уточнення стану не робити.
Запити користувачу щодо N95/IP та встановлення/демона E90 лишаються без
відповіді. F05–F08 не завершені; у цьому продовженні DSP на E90 не запускався.

## 2026-09-30: N95 у правильній підмережі; v7 на обох; RMS-only −33

Попередні записи вище історичні. Поточна перевірка INFO успішна на N95
192.168.3.22 (320×240) та E90 192.168.3.21 (800×352), PS c55stream*=0.
Користувач уточнив, що N95 був в іншій підмережі. Перед цим два повні
авторизовані TCP 2323 сканування 254 адрес знайшли лише E90.
Після виправлення N95 доступний; запит IP більше не потрібний.

**N95 recovery:** до нових c55stream START збережені журнал idle-first,
DLL 3644 Б, host v6 EXE 15084 Б і SHA-1 hash. Journal v6 обривається після
frame=7 з errors=0; frame8/delete/FINAL немає. Не змішувати цей результат
із ранішим 8-frame v6 прогоном із delete −2.

**E90 v7:** установлений користувачем SIS підтверджено inspect (усі 39
exports, UID, EXIT/FINAL=0). DSP normal v7 3668 Б (SHA-256 E039E983...)
прочитаний назад та зіставлений побайтово. Base, native buffers і
create/delete/free task=0 (create 8697 мкс). Minimum execute без host
frames: RUN=0/status=0, state=2; deleteStatus лишився pending за 5000 мс,
delete/FINAL/EXIT=−33. Одразу після тесту E90 відповів. Пізніше connect
timeout, після відновлення INFO має менший uptime — ознака перезапуску
між перевірками; причина невідома. Minimum log і DLL readback незмінні.
RMS-only на E90 не передавався й не запускався: prepare мав connect timeout до
першої daemon-команди. На E90 лишається normal v7 E039E983... .

**Статичний доказ:** NODE_wait (24D020), NODE_getMsg (24D790),
RMS_executeNode (24DEDC) і task wrapper (24E6F0) у N95/E90 мають однакові
байти; whole common-code різниться у 116 байтах. DOFF packet header=12 Б,
64 packets. NODE_getMsg повертає 1 після копіювання трьох long.
Task wrapper викликає execute і сам надсилає EXITACK 40000000 через
NODE_putMsg(env,NULL,{cmd,return_status,0},FOREVER). Ручний ACK не додавати
без нового доказу. PDD control6 при running/state2 і node+440=0 надсилає
EXIT 80000000 з arg1=nodeEnv; при node+440!=0 викликає 801A3DF4.
Поле440 походить із processor+64, а воно — з конфігурації +588;
значення/контракт іншого backend ще уточнюються.

**N95 RMS-only:** build_stream_node.cmd rms додає execute, що лише чекає
NODE_getMsg/EXIT (100×100 мс), без issue/wait/idle/reclaim. Create/delete
лишаються звичайними, зі stream objects. Host v7 15684 Б (87CEA30C...)
і loader hash/DLL 2700 Б (8F65458F...) readback verified. Create/delete/
free task=0, create=8361 мкс, EXIT/FINAL=0. Minimum execute RUN/status=0,
state=2; delete pending/−33, EXIT/FINAL=−33. N95 відповідав і через кілька
хвилин після цього, uptime зростає. Це нова ізоляція RMS, а не echo pass.
Після тесту normal v7 DLL 3668 Б (повторна збірка 5B6BE15B...) записаний
на N95 і прочитаний назад; його execute ще не запускався. Основний
out/dsp DLL також відновлений normal збіркою, RMS artifact збережений
окремо як c55stream-rms.dll55l і stream_node-rms.asm.

**Clock/restoration:** read-only N95 stock m86/div3, firmware math DSP
220160 kHz; HAL MPU=206438 kHz у момент проби, не вимір overlap. E90 перед
його RUN stock m86/div3, MPU=330000 за HAL. N95 original ocprobe.log 1259 Б
нарешті повернуто й перевірено побайтово (SHA-256 1ABC8073...). E90
original ocprobe.log 1249 Б знову повернуто після probe; original romdump.bin 12288 Б
відновлений раніше. Research EXE/SIS/DLL/log залишаються для продовження;
старі dsptest/bench untouched. F05–F08 in_progress, goal active після
відновлення мережі; виміри H/Q15/overlap та остаточний cleanup не виконані.

Докази й повні SHA-256 — docs/SESSION_2026_09_30.md та
docs/evidence/2026-09-30/n95-stream-execute-v7-rms-wait*.txt,
e90-stream-execute-v7-minimum*.txt, n95-restored-original-ocprobe.json,
n95-e90-dsp-rms-code-comparison.json, device-status-after-n95-subnet-recovery.json.

**Наступне:** розібрати native MSG-toDSP routing/dispatch для RMS_EXIT і
PDD flag/backend, щоб розрізнити missing EXIT, execute return та missing
ACK. За потреби підготувати bounded host get-info/message probe на точному
raw ABI task2/task20/task21 (див. STREAM_RESEARCH), із новим version guard.
Новий RUN лише після конкретного статичного доказу або зміненого контракту;
не повторювати RMS-only −33 та не запускати serial/parallel зараз.

## 2026-09-30: підготовка v8 get-info та messaging diagnostic

MSG-toDSP SWI 24D498 копіює три long у frame та ставить його в чергу
destination з четвертого DWORD shared packet. PDD 801AF3A0 бере destination
з queue+16; після create ACK 801A27F4/801A2800 driver установлює це поле
в повернений nodeEnv. NODE_getMsg читає цю саму чергу. Це статичний маршрут,
не підтвердження фактичної доставки EXIT.

Task2: LDD 801B4A98 пише 112 Б, header/max=30000068/104; nodeEnv payload+64.
Task20/21: 8-Б пара status/record, raw record **24 Б**, header/max=3000000c/12,
payload=cmd,arg1,arg2. І queued receive 801AF284, і pending receive 8019B048
пишуть 24 Б; останній DWORD padding не читати. Dispatcher 801B4B64 має
команди 0–21; окремого cancel22/23 немає. Статуси й records у v8 глобальні,
повторний get при pending заборонений. Destructor завершує pending status;
це не означає, що kernel або DSP можна відновити після аварії.

v8 info виконує create/get-info/delete без RUN. Лише після його успіху —
окремий messages variant: DSP hello {600,00080001,env}, host echo
{601,12345678,a5c55a5a}, reply602, receipt603 перед штатним EXITACK wrapper.
Execute messages не викликає STRM; межа receive 150×100 мс. Host чекає
receipt під час control6, відрізняє echo PASS від чистого lifecycle та
зберігає першу помилку навіть за пізнього завершення. Runner messages
потребує v8 і deadline >=60 с; старий E90 v7 доступний через явний
--host-version 7 тільки для вже наявних режимів.

Збірка ARM v8 EXIT_CODE=0: out/stream-host-v8-message-build.log.
На момент цього запису info/messages на апараті ще не запускалися.
N95 INFO успішний, PS=0, uptime зростає. E90 не оновлювався до v8.

## 2026-09-30: N95 get-info v8 підтверджено; messages очікує мережу

02:36 UTC: перша host v8 збірка 18660 Б, SHA-256 374F8BE1..., hash і EXE
збережені й прочитані назад. На телефоні normal v7 DLL 3668 Б 5B6BE15B...
не змінювався. Info (без RUN) дав create=5859 мкс, header/max=30000068/104,
nodeEnv=000077e0; delete/free task=0, EXIT/FINAL=0. Транспорт закінчився
INFO, PS показав завершений процес. Докази —
docs/evidence/2026-09-30/n95-stream-info-v8-raw-record*.txt та
n95-host-v8-raw-info-deploy.json.

Поле PDD node+112 у першому журналі помилково названо timeout=3; одиниці
часу не встановлені. Локальна v8 збірка виправляє лише підпис на
property112: 18668 Б, 0900DFE3...; вона ще не доставлена. Messages DLL
2924 Б 5A06007E... і SIS revision8 11716 Б 804B1533... зібрані, жоден не
доставлений. Основний out/dsp DLL після variant відновлено normal збіркою
3668 Б 70BD54CE... . На E90 лишається встановлена v7.

MSG_toDSP_SWI, MSG_notify, NODE_putMsg, LDD put/get/info/dispatcher
побайтово тотожні у ROM N95/E90. Shared record writer PDD формує 16-Б
{cmd,arg1,arg2,destination}; destination — offset12 ARM bytes / 6 C55 words.
JSON зі SHA-256 — n95-e90-message-routing-contract.json. Це статичний
доказ для наступного досліду, не апаратний echo PASS.

Після восьмигодинної паузи (10:44 UTC) обидва IP отримали connect timeout;
PC Wi-Fi=192.168.3.11, шлюз .1 відповів. INFO/PS через колишню escalation
також завершився timeout; незавершених exec handles після перерви немає.
Новий DSP RUN після успішного info не запускався. Pending async request
просить відкрити демон N95 та перевірити Wi-Fi/IP. Причина недоступності
невідома; не приписувати її DSP або get-info.

Наступне: свіжий INFO/PS N95; tools/prepare_stream.py з унікальним tag,
current DSP hash 5B6BE15B... і messages DLL; перевірити clock guard та
байтове відновлення ocprobe.log; run_stream messages --deadline60.
Після проби зберегти log/transport та повернути normal DSP із backup,
прочитати назад. При відмові не починати serial/parallel. Скрипт prepare
перевірений compile/help, його реальне виконання ще не було.
F05–F08 in_progress, goal active; останнє продовження — progress.

## 2026-09-30: prepare v8 пройшов; message RUN втратив зв'язок

10:59 UTC N95 став доступним. Prepare stream-v8-messages-prepare-01
виконав усі backups, stock read-only clock guard (m86/div3, HAL206438),
ocprobe.log restore1259 Б 1ABC8073... та EXE/hash/DLL readback рівні.
На N95 тепер host18668 Б 0900DFE3... і messages DLL2924 Б 5A06007E...;
normal5B6BE15B... збережений у
work/evidence/n95/stream-v8-messages-prepare-01-before.dll55l.
Оригінальний ocprobe.log вже відновлений **до RUN**.

Info з новим host/messages DLL (stream-info-v8-messages-create) чистий:
create6347 мкс, property112=3, nodeEnv000077e0, delete/free0, EXIT/FINAL0.
Messages START accepted11:00:20 UTC (daemon proc5), PS живий до11:00:23;
наступний PS timed out. PC runner session41172 завершилася EXIT1;
стан phone process/DSP невідомий. Connect/GET log після цього двічі
отримав timeout **до першої daemon-команди**, recovered log не створений.
Не вважати ні echo, ні lifecycle успішними. Перезапуск не підтверджено.
E90 INFO успішний, PS c55stream*=0; v8SIS/новийDSP на E90 не передавалися.

Докази docs/evidence/2026-09-30: n95-messages-v8-preparation.json,
n95-clock-before-messages-v8.txt, n95-stream-info-v8-messages-create*.txt,
n95-stream-messages-v8-routing-transport.txt, device-status-after-v8-message-run.json.
Pending async request уточнює тип відмови N95 й просить відкрити демон.

**Наступне при доступності:** GET E:\c55stream.log та current DLL ДО
будь-якого нового c55stream START/PUT, свіжий INFO/PS. Якщо c55stream
ще живий, не вважати його terminal і не викликати WAIT. Після recovery
та PS=0 повернути normal із вказаного backup і перевірити GET. Не
використовувати сліпий KILL5 після daemon restart: ids можуть змінитися.
Новий RUN лише після журналу й нового контракту; повтор тієї самої
message-проби заборонений зараз. Cleanup normal DLL pending.
F05–F08 in_progress, goal active; це продовження має апаратний progress.

## 2026-09-30 11:49 UTC: N95 recovery очікує мережу; E90 v8 SIS/stock guard готові

Останнє повідомлення користувача про доступність перевірено заново.
PC192.168.3.11; повний TCP2323 scan192.168.3.1–254 знайшов лише E90`.21`.
N95`.22` connect timeout; ARP neighbor Incomplete. Перезапуск N95 після
message RUN не підтверджено. GET журналу/current DLL не відбувся,
normal5B6BE15B... restore pending; на N95 лишається messages5A06007E... .
Нового DSP RUN не було. Async запит уточнює IP/демон і факт перезапуску.

`tools/recover_stream.py` додано: journal/current DLL → INFO/PS → exact
before-DSP restore/readback тільки при завершеному c55stream і відомому hash.
START/WAIT/KILL не викликає. Compile/help пройшли. Recovery01/02
(11:17/11:20 UTC) обидва complete=false/connect timeout до першої команди;
жодних телефонних writes. Позитивне hardware виконання ще не перевірено.
Пізніше recovery перевірений на E90: journal/current DLL/PS0 отримані,
DLL already exact backup, PUT пропущено, final GET рівний/INFO успішний.
Це idempotent path, не виконаний N95 restore.

E90 INFO/PS0 успішні, uptime зростає/startTick42746. 11:30 UTC передано
`E:\c55stream-v8.sis`,11716 Б804B1533..., GET рівний. До цього збережено
EXE/hash/DLL/log; versioned SIS path absent. DSP normal3668 БE039E983...
лишився. Пізніший installed EXE GET ще має v7 hash87CEA30C...; v8 установка
очікує користувача. OPEN/SHOT/START не було. Пакет і контрольні суми конкретні,
повторно доставляти SIS не потрібно.

11:45 UTC E90 guard01 відхилив штатний restore-check1, бо script помилково
очікував N95 значення100; DSP PUT не було, original ocprobe.log повернуто.
Guard виправлено на окремі UID/profile/code. 11:48 UTC guard02 пройшов:
stock m86/div3, HAL ARM330000, firmware math DSP220160 kHz; original
ocprobe.log1249 БBE58F5EF... і normal DLL3668 БE039E983... readback рівні.
Цей clock ocprobe START окремий від SIS доставки; c55stream не запускався.
Докази — e90-info-v8-preparation.json/e90-clock-before-info-v8.txt;
old rejected guard01 збережено окремо. EXEv8 встановлення ще не підтверджено.

E90 get-info PDD getter803E57F8/table803F8424/slot20 установлені з його
ROM. NodeEnv payload+64; getter92 Б різниться з N95 лише relocated BL+20.
LDD get-info copy/adapter/constructor byte-equal. Відтворюваний
`tools/rev/compare_node_info.py` виконано; JSON hashes —
docs/evidence/2026-09-30/n95-e90-get-info-contract.json.

**Наступне:**
1. Якщо N95 відповідає, recover_stream з новим tag, preparation
   stream-v8-messages-prepare-01 та --restore-dsp; спочатку читати journal.
   При live c55stream restore заборонений. Новий RUN тільки після розбору log.
2. Якщо E90 SIS установлено, GET host/hash, inspect v8, stock read-only clock
   зі збереженням/відновленням original ocprobe.log, info без RUN.
3. Розібрати RMS/message відмову за новими доказами; не повторювати той самий RUN.
F05–F08 in_progress, goal active; поточне продовження має static/deployment progress.

## 2026-09-30 15:54 UTC: v14 verified; ARM message delivery відкритий

Попередні pending recovery/SIS пункти виконано. Обидва телефони відповіли:
N95`.22`/startTick7928381; E90`.21`/startTick47653 після user-confirmed
автоматичного reboot. Installed v14 EXE22408 Б5F1C77CF… verified на обох;
E90 SIS13624 Б1BC4F000… установлено користувачем. Немає активного c55stream.

N95 v8 recovered log hello−33, обрив BEGIN delete; exact normal restore
5B6BE15B… PUT/GET completed. V9/v10 created pending receive→delete/free0→−3,
EXIT/FINAL0; explicit raw allocation32 замість SDK28. Bare no-STRM також
hello/delete−33. V11–v13 STRM markers підтвердили execute/get0/put1.
V13 DSP queue0/from-window empty0/count1, ARM get після markers pending,
delete/FINAL/EXIT−33. Normal після кожного variant повернуто exact GET;
clock logs restored1ABC8073… . Файловий restore не доводить clean DSP exit.

E90 v8 info після failed guard був ungated mistake: не stock timing доказ.
V14 ownRAM PASS0/51a73cd2; fresh clock guardm86/div3/HAL330000/DSPmath220160;
original clock log restoredBE58F5EF… . Info create6652 мкс clean; created
receive get pending→delete/free0→cancel−3, EXIT/FINAL0 без RUN. E90 normal
E039E983… unchanged. Попередній patcher self-test−20 та reboot cause невідомі.

Runner default14; receive-created та RUN режими потребують successful
preparation≤10 хв, saved/current DSP/hash та uptime check. Failed guard
відхиляється до START. Кожен mode зберігає prior journal та проходить inspect.
README/BUILD/research/session оновлено; 26 нових V13/V14/E90 small proofs
додано, builds/artifacts metadata зафіксовано. Private GitHub підтверджений.

**Наступне:**
1. Readonly DSP actual shared record і статичний ARM reader/window/IRQ
   contract. Reader801B3028 conditionallyror16, consumer8019B0A8 порівнює
   source із queue+16, DFC8019BA84 invokes consumer. Runtime flag/source/
   DFC/mapping ще невідомі; не викликати kernel internal pointers навмання.
2. Після нового контракту — fresh prep, один minimal message/lifecycleRUN,
   journal/recovery/exactnormalGET при negative. V13 без нової інформації
   не повторювати. E90 newRUN після підтвердженого N95 lifecycle.
3. Hello/echo+delete/free/EXIT0 перед serial0/Q15/три serialparallelruns.
4. Звірити докази, commit/push приватний checkpoint. F05–F08 in_progress;
   full objective не завершено. Поточний turn — hardware progress.

16:10 UTC static message-window comparison виконано: consumer N95/E90
744 Б різниться лише дев’ятьма relocated BL; reader E90803F7664 unique,
DFC/config/window setup byte-equal. Source/runtime/IRQ ще невідомі.
Pycompile, check_state з обома artifacts, manifest paths і diff-check
пройшли; локально failed preparation відхилено до phone connection.

## V15 shared record, 16:14 UTC

N95 свіжа preparation `stream-v15-records-prepare-01` complete=true:
stockm86/div3, original clocklog returned, host/DSP/hash GET-equal.
Hostv15 доповнює STRM marker readonly first-record snapshot, protocol15.
Info create10559 мкс clean; actual RUN `stream-message-records-v15-01`
зберіг expected record words0000/0600/000F/0001/0000/77E0/0000/77E0,
fromDSP empty0/count1 до й після copy. Ror16 дає cmd600/arg1F0001/
arg2/source77E0. Raw ARMsource77E00000 не збігається з env77E0.
Runtime flag невідомий, тому це не доведена причина pending ARM get.
Get/delete/FINAL/EXIT−33; процес завершився, KILL не було. Recovery01
отримав log4189 БBBFE109C… і повернув exactnormal5B6BE15B… GET-equal;
INFO startTick7928381 незмінний/PS0. E90 v14 у цьому RUN не брав участі.

Подальший static object tracing виправив асоціацію reader flag:
8019BC8C → context+24, 801AA98C → (context+48 object)+164. Byte+64
цієї embedded memory-interface не тотожний processor+64/configuration588
із exit-path коду. Script і metadata оновлено; getter/setup E90byte-equal.
Виправлено звіт, без зміни історичних фактів апаратних прогонів.

V15 builds ARM/DSPstage/normal EXIT_CODE0. Smallproofs n95-message-records-v15.txt,
n95-v15-records-preparation.json, n95-v15-records-recovery.json,
stream-v15-records-artifacts.json. Current source/runner15, E90installed14
треба явно --host-version14; N95installed15. Повного messaging/lifecycle
або parallel proof немає, F05–F08 in_progress. Private checkpoint24d82ce
раніше synchronizedHEAD; коміт цього додатка звіряти через git log та remote main.

Альтернатива TSK: primary TI C55 DSP/BIOS API guide прочитано, native
24B0FC–24B130 підтвердив default attrs14 C55words/priority−1 і TSK_create.
Arg ABI, termination і stream cleanup перед TSK_delete ще не встановлені;
апаратного worker тесту немає. Це наступна незалежна статична дія, якщо
readonly runtime reader/IRQ перевірка потребує додаткового контракту.

Останні INFO/PS/GET підтвердили доступність обох телефонів і PS0; normal
N955B6BE15B…/E90E039E983… GET hashes точні. Немає running PC sessions.
Докази stream-v15-checkpoint-device-status.json; nativeTSK creation site56Б
byte-equal N95/E90 за n95-e90-native-tsk-create-contract.json. Наступний
gate — runtime reader flag/IRQ або TSK Arg/termination ABI, не повтор v15.


## Native BIOS worker-once — 2026-09-30

DOFF extraction checksum-verified, packet instruction bytes unchanged;
common raw exact-equal65266B. .bios dis55 now valid; previous exploratory
per-four-byte reversal/error-loading outputs were invalid and not used.
Native Arg32 pointer/XAR ABI established (long declaration would be wrong).
TSKattrs14/stat22words, mode14/terminated3, eight pointer Args, entryAC0;
cl55 assertions and emitted assembler agree. N95/E90 TSK ranges equal apart
from seven verified symbolic BIOS data addresses.

CREATE_WORKER_ONCE DLL3172B0709550C… checks caller priority<15, finite
callback marker/cookie00123456, stat.mode3, TSK_delete before create return.
No callback STRM/locks/resources; no official node RUN, no resident worker.
N95v15 info create10131us/delete/free/FINAL/EXIT0; E90v14 info9368us same0.
Fresh preparations/stock guards passed; original clocklogs returned. Both
PS0, uptime/startTick continuous; exact phone normal DLLs restored GET-equal
N955B6BE15B…/E90E039E983…. KILL and phone reboot were not needed.

Small reproducible proofs: n95-e90-bios-task-contract.json,
worker-once-artifacts/device-results.json, both worker-once txt/prep/recovery.
Normal PC DLL rebuilt after variant. Hosts unchanged N95v15/E90v14.
F05–F08 remain in_progress: task ABI is proved, persistent STRM/Q15 and ARM
parallel work are not. Next independent gate: native loader handling of
shared library type2 vs existing phase3/4/5 and code/BSS lifetime across
create/delete; use no live worker until residency is established.


## Generic library residency та worker-parked — 2026-10-01 local

Статичну звірку завершено для native bridge/PDD/base DOFF обох телефонів:
compare_node_loader.py, n95-e90-node-loader-sem-contract.json. Library3
missing/−6 має fallback2; після generic selection немає окремих lists1/2.
Native create code не unload одразу: він resident у CREATED; RUN unload
при phase_split1/dynamic1. Created delete лишає create loaded; free
unload loaded libraries. Storage vtable береться з firmware constructor
literal, а не code delta. SEM count/timeout T0, handle/attrs XAR0;
SEM_pend blocked mode2, timeout у BIOS ticks. RMS create return AC0
relay і signed host mapping−2 підтверджені; positive1234 не error gate.

Recovery N95 phase-control proc42 забрав журнал2039Б81DC64C0…:
create0/7415us, delete−2, BEGIN close без FINAL. Joint check data/address
failed; що саме змінилося, не розділено. Зв'язок зник під час close;
пізніший uptime нижчий, daemon новий. Причина restart невідома.
Normal5B6BE15B… restored GET-equal; нового RUN до recovery не було.

Resident v1 generic DLL2980Б475EFB3B… і phase DLL3136Б488C980B…
мають однаковий raw text CF27629B… та initialized data stamp1BADB002.
Generic create перевіряє init, змінює stampC55DC0DE; delete перевіряє
stamp та збережену адресу delete. N95v15 create9307us, E90v14 9735us;
обидва delete/free/FINAL/EXIT0, без RUN. Відновлено exact normals.

Worker-parked DLL3604БA5B0AE7B… library0/2, 16 imports у обох bases.
Create SEM0/TSKpriority15 stack1024/sys256; callback stores cookie00123456,
stageC551 та SEM_pend30000ticks. Create gate stat.mode2. Delete повторно
перевіряє blocked2, SEM_post -> callback stageC552/pend1/terminated3,
TSK_delete -> SEM_delete -> ordinary STRM/MEM cleanup. N95v15 create9063us,
E90v14 7293us; обидва delete/free/FINAL/EXIT0. У callback STRM не було.
Це доказ task lifetime після create і join у delete через conditional
returns hashed artifact; ARM не логував task fields незалежно.

У чотирьох нових positive runs fresh stock guards пройшли, original
clocklogs повернуто; daemon startTick сталий від prep до recovery.
Both PS0 та exact normal DLLs GET-equal N955B6BE15B…/E90E039E983… .
Hosts залишились N95v15/E90v14, SIS не змінювався. Журнали, prep/recovery
та small reports перенесено в docs/evidence/2026-09-30; UTC timestamps
перед місцевою північчю. Tested v1 DLLs archived в ignored evidence.
Normal PC build після variant EXIT0; source додає null env/context guards.

Наступне: ARM STRM transfer gate у CREATED, окремий host mode без RUN,
DSP stream worker з explicit stop/finite wait/join та buffers ownership.
Один packet clean exit -> multi-packet/Q15 -> три same-condition
serial/parallel runs -> E90 port/new SIS -> measured application choice.
Parked priority15 лише stores/wait/return; audio coexistence для MAC
не доведена. MSG runtime reader/IRQ напрям лишається відкритим.
F05–F08 in_progress; full goal і корисний паралелізм не завершено.


### V2 audit — null-context assertions, 2026-09-30 22:42 UTC

Під час source review виявлено, що v1 delete повертав8000 при null
moreEnv до diagnostic checks. V1 positive results не є повним доказом
цих checks; limitation додано до обох v1 result JSON. Source виправлено:
CREATE_RESIDENT_CHECK та CREATE_WORKER_PARKED повертають80008015 для null
context, env також checked. У worker-stream це правило буде обов'язковим.

V2 generic DLL3000БD229D53F…/7 imports: N95create9399us, E90create6744us.
V2 parked DLL3592БED8C2862…/16 imports: N95create7873us, E90create9277us.
Всі чотири fresh prep/run/recovery02 complete; create/delete/free/FINAL/
EXIT0. Negative gates тепер обов'язкові для успіху. No official RUN/worker
STRM. Normal та original clocklogs returned GET-equal; PS0, startTick
без змін у кожній новій prep→recovery. Hosts N95v15/E90v14 unchanged.

Authoritative v2 proofs: resident-generic-v2-artifacts/device-results.json,
worker-parked-v2-artifacts/device-results.json, both device v2 txt/prep/
recovery. V1 kept as history; negative split control лишається чинним.
Worker-parked/resident-check/normal builds EXIT0; normal main PC DLL
rebuilt після variant. Static comparison, pycompile, environment/manifest
та source/evidence consistency перевіряти перед commit/push.

Наступна дія залишається STRM worker у CREATED із stop/join/cleanup,
потім nonzero Q15 та same-condition serial/parallel. F05–F08 відкриті.


22:45 UTC final readback: both phones online, PS0; host N95v15 hash45140071…,
E90v14 hash5F1C77CF…, original normal DSPs and ocprobe.log hashes match
expected exactly. worker-created-checkpoint-device-status.json preserves
INFO/PS/hash evidence. Final check_state with both artifact flags passed
4/8, UTF8 feature titles/statuses unchanged, all evidence paths/JSON valid,
git diff-check passed. Source and small proofs ready for private checkpoint;
raw ROM/DLL/EXE/COFF/SIS and local backups remain ignored.

## Потоковий worker у CREATED — план наступного кроку

2026-10-01: обидва телефони відповіли INFO/PS; дослідницьких процесів немає.
Native PDD transfer виключає states 0/4/9/10/11/13, але допускає CREATED=1;
LDD копіює 28-byte transfer та вибирає slots52/60 без додаткового state gate.
Перевірка однакова на N95/E90. Native NODE_wait допускає NULL env: це
очікування лише STRM, без зміни RMS message queue. Ці статичні факти ще
не доводять апаратний обмін із новою задачею.

1. Зберегти відтворювану статичну звірку compare_created_stream.py.
2. Додати generic library2 worker: bounded stream wait, explicit last-packet
   stop, output reclaim, completion semaphore та join до free context/code.
   Офіційний execute цього варіанта має відхиляти RUN.
3. Hostv16: worker-one, worker-serial, worker-parallel без RUN; native mode2
   buffers, sequence/length/echo/Q15 checks та перевірка CREATED до delete.
4. Чистий один packet на N95 -> багато packets reps0 -> nonzero Q15 ->
   щонайменше три same-condition serial/parallel pairs з корисним ARM CRC.
5. Новий SIS E90 та ті самі перевірки; виміряти transport latency та
   application break-even. Після кожного варіанта exact normal restore.
6. Зафіксувати результати й приватний checkpoint. F05–F08 залишаються
   in_progress; parked callback не зараховується як stream/parallel proof.

23:11 UTC N95 worker-one v16/DE7DF926…: create0/10070us, 1 packet
put/get0, errors0, protocol16/cookie valid, no RUN, state1. Delete/free
task/native buffers0, close returned. FINAL−20 лише через host expectation
deleted4: wire task3 actual5. Native LDD801B440C–4410 overrides PDD record
with LDD node+20; PDD internal4 та reported LDD5 — різні enum.
Recovery01 initially only saved the journal/current DLL (restore_requested=false).
Preparation02 correctly refused the still-installed diagnostic. Explicit
restore01 then returned normal5B6BE15B… exact; PS0/startTickcontinuous.
Перший прогін не зараховано як FINAL0. Виправляється host expectation на5;
DSP build без змін. Повтор дозволено конкретним встановленим контрактом.

## Завершена серія worker-stream v16 — 2026-10-01

23:35 UTC checkpoint: обидва host v16 AB016003…; DSP worker DE7DF926…,
library2, один create і 8×512 Б у CREATED без official RUN. One/multi reps0,
Q15 reps1000 та три pairs reps10000 пройшли на КОЖНОМУ телефоні:
sequence/length/echo/dot/CRC/stop правильні, delete/free/native/close/
FINAL/EXIT0. У цій серії немає reboot або KILL; task завершено до cleanup.
E90 v16 SIS встановлено через спостережуваний daemon installer; GET EXE
exact24464 Б. Негативний перший N95 run і journal-only recovery збережено.

N95 pairs S/P us:406551/150968,399838/149868,249324/149593.
E90:266809/160305,263363/164517,257351/159542. CRC64KiB виконується ARM
одночасно з Q15 на DSP. Частина N95 serial intervals подвоїлася; PRCM
на кожному packet не читався. Відсотки — provisional, не pure overlap gain.
Raw CLK ticks з reported164 не перетворюються у DSP ms. Reps0 observed
completion512 Б N95335us/E90396us — не pure DMA latency/bandwidth.

Authoritative proofs: docs/evidence/2026-09-30/{n95,e90}-worker-stream-v16-
results.json, worker-stream-v2-artifacts.json, created-stream-contract.json,
worker-stream-v16-checkpoint-device-status.json, byte-exact phone journals.
Original DSP N955B6BE15B…/E90E039E983… і original clocklogs GET-equal;
PS0, no active worker. Main normal DLL на ПК rebuilt після variant.

Наступні кроки за незмінним work/PLAN.md:
1. Native N95 dvfs_interface reservation/release і per-packet умови,
   мінімум три same-condition serial/parallel pairs.
2. Cross-packet DSP timestamp calibration проти ARM FastCounter;
   явна похибка, без довіри до counts/ms164.
3. Потрібні WSOLA/MDEC packet1760/2048/2304 Б та оцінка окупності.
4. Audit F05–F08 і віддалений checkpoint. F01–F04 complete,
   F05–F08 in_progress; повна мета ще не досягнута.

## V17 завершено на обох телефонах — 2026-10-01 UTC

Checkpoint1430722 із v16 відправлено у private GitHub; подальший v17
зібрано й перевірено за PLAN_V17.md. DSP4800 Б41D14CD4…/host28456 БC8B08E8C…;
E90 SIS16776 Б9C04181A… встановлено через observed installer, GET exact.
MPU reservation на N95 без PRCM/ROM patches: чотири native fingerprints,
request0/a2=100, per-packet100%, release0/status0. На E90 гілка не виконується.

24 v17 runs успішні: на кожному one, multi0, Q15, три calibration та
три pairs. У всіх correct echo/dot/CRC/stop, CREATED1→reported DELETED5,
join/task/SEM/streams/context/native free/close/FINAL/EXIT0. No RUN/KILL/reboot.
N95 S/P us251154/148953,250148/151211,249994/150205; raw dot ticks майже
тотожні. E90 259791/155729,258508/157467,263087/159878. Скорочення~40%
лише для цього синтетичного dot+CRC навантаження; application gain відсутній.

Short timer bounds N95[19185149,19213529]Hz/E90[19182339,19218353]Hz.
У всіх шести800ms intervals DSP raw delta~501ms за19.2MHz, ARM828–876ms.
Невідомо, чи idle DSP/timer gating або інша причина; лише MPU DVFS цього
не пояснює. Reported164 не використовувати. Wall time міряти ARM counter.

Normal DSPs/original logs returned GET-equal, both PS0/INFO; hosts v17 exact.
Main PC normal DLL rebuilt. Authoritative docs/evidence/2026-10-01:
n95/e90-worker-stream-v17-results.json (raw journals/bounds), v3-artifacts,
n95-stock-performance-contract, worker-stream-v17-checkpoint-device-status.
Source/docs/small proofs готові для private checkpoint; raw firmware,
SIS/EXE/DLL/ASM/keys/screenshots/backups лишаються ignored.

Наступна робота: larger1760/2048/2304/4096-byte packets для оцінки WSOLA/
MDEC/media transfer cost, timer/idle contract і error lifecycle. Повний
work/PLAN.md незмінний, F05–F08 in_progress; мета активна, блокера немає.

## V18: пакети до4096 Б на обох телефонах — 2026-10-01

План записано у PLAN_V18.md до правок. Native size-bearing instructions
на обох ROM показують properties attr+4 -> RMS stream size+0 без scaling;
stream size — C55 words, transfer descriptor length — ARM bytes. DCD не
змінювався. Native buffers по4096 Б, worker протокол18 приймає256–2048
words для обох напрямків; весь payload echo перевіряється. Q15 лишився240
значень. Worker-transfer reps0 виключає ARM CRC і повторний dot із виміру.

Host29760 Б571C5A62…/DSP4852 БDD8D50DC…; DOFF/22 imports/ASM перевірено,
immutable archive revision4 збережено. E90 SIS v18 встановлено через
спостережуваний installer; GET EXE і runtime profile збігаються.

На КОЖНОМУ:one512/1792/4096, Q15 reps1000×8 на4096 Б та три ordered
series по32 packets для512/1568/1792/2048/2304/4096 Б. Разом22 runs/587
packets на кожному, FINAL/EXIT0, no RUN/KILL/reboot, normal DSP GET-equal
після recovery. N95 MPU percent100 на кожен packet.
Медіани completion N95:335/518/518/549/610/885us;
E90:396/610/640/701/762/1129us. E90 outliers1792=7812us/2048=7690us;
не вилучені. Це equal-size echo, не pure DMA/bandwidth або application gain.
WSOLA1760 Б payload потребує1792 Б packet; MDEC input1536 потребує1568.
Короткий output і actual kernel ще не виміряні.

Authoritative: docs/PACKET_SIZES.md, {n95,e90}-packet-sizes-v18-results.json,
n95-e90-stream-size-contract.json, worker-stream-v4-artifacts.json,
raw journals/preparations/recoveries у docs/evidence/2026-10-01.
Helper summarize_packet_sizes.py перевіряє кожен packet/result/CRC/MPU,
raw hashes, process statuses і cleanup до публікації. Normal main DLL на
ПК rebuilt після worker variant. Source/docs/proofs готуються до private push.

О 10:17 UTC пізніший E90 GET ще раз підтвердив original DSP/log та v18 host,
PS0, той самий daemon startTick75535. N95 двічі мав connect timeout після
вже завершеної серії та exact recovery. Запит розбудити його надіслано;
нового DSP досліду після recovery не було. Поточна доступність N95 невідома.

Після відповіді користувача N95 доступний: original DSP/log і host v18
GET-equal, PS0. Uptime194682/startTick93219 проти тестового uptime28049534/
startTick17620669 показує нове завантаження після серії; причина уточнюється
у користувача. Нових DSP experiments у цьому завантаженні немає.
Authoritative live readbacks: {n95,e90}-packet-sizes-v18-device-status.json
і worker-stream-v18-checkpoint-device-status.json у тому самому evidence dir.

Далі за повним PLAN: actual WSOLA/ARM reference та asymmetrical output,
static audit error/delete lifecycle перед negative hardware tests;
timer/idle і audio/long stability. Audit F05–F08 окремо, без додавання
непоставленої вимоги повної інтеграції у сусідні проєкти. Повна мета активна.

V18 source/proofs/docs опубліковано в private main як4d39a89, LOCAL=REMOTE
перевірено. Environment/artifacts/manifest gate4/8; byte-exact staged audit46
journals; report checks22 runs/587 packets per device. PLAN_V18 виконано,
а повний PLAN і статуси F05–F08 лишаються відкритими для наступного аудиту.

## V19/V20: exact WSOLA та завершальний audit —2026-10-01

V19 на обох:9 runs/195 correct packets, actual search/1792 input/48 output,
оригінали відновлено. Виявлено ARMv5 baseline, що відрізняється від current
PS1 ARMv6 body; evidence збережено, порівняння уточнено окремим PLAN_V20.

V20 source/ARM/DSP/SIS built, artifact6, ARMv6 codegen244 Б exact. SDK stale
object після MMP option edit усунуто до доставки; build.cmd clears обидва
research objects. Host34196 Б CBB91873… /DSP5384 Б87EDE15C…; SIS20 EAC61C9D…
на E90 встановлено observed UI, EXE GET exact.

На КОЖНОМУ v20:echo/control/search one і три paired32-packet runs,9 runs/195
packets (97 actual searches/97 controls/1 echo). ARMv6 median999.45us; DSP
path з packing N95640.87us/E90732.42us, max671.39/762.94us. Paired median
saving385.28/265.12us; create-only модель22/33 hops. Algorithm/offset/score/
count/checksum/stop і lifecycle правильні, FINAL/EXIT0, no RUN/KILL, no
daemon restart у v19/v20. N95 MPU100% на кожен packet; fresh m86/div3 guards.

Original DSP/clock logs обох GET-equal, PS0, host20 GET-equal; normal main
PC DSP rebuilt. Authoritative docs/WSOLA.md, docs/evidence/2026-10-01:
n95/e90-wsola-v20-results.json, worker-stream-v6-artifacts.json, wsola-v20-
arm-codegen.json, worker-stream-v20-checkpoint-device-status.json.

Повний PLAN audited у FINAL_AUDIT.md: F05/F06/F07 критерії research prototype
і assessment виконано; F08 очікує final gates/private push. Limits timer/idle,
unsafe negative teardown, real audio/long sessions/application integration
явні; не заявлено application speedup або production stability.

## Повний research PLAN виконано —2026-10-01

Source/evidence checkpoint e8f38c1 pushed і verified LOCAL=REMOTE,
PRIVATE, clean. Gates artifacts/environment/JSON/evidence paths/raw hashes
і staged audit пройшли. F01–F08 complete за FINAL_AUDIT.md; prototype
і application assessment виконано. Completion metadata завершує publication.
Limits error/unload, timer idle, long/audio та application integration
залишаються явними майбутніми integration gates; нових hardware runs не потрібно.

## Нове доручення D0–D2: E90 checkpoint —2026-10-01

Це окреме продовження після завершеного F01–F08, за PLAN_D0_D2.md.
Початковий HEAD b75853f; початкові правки APPLICATION_CANDIDATES.md і
доданий CODEX_TASK_2026-10-01.md збережено поза цим commit. Лише E90
192.168.3.21:2323; N95 не отримував жодної команди. Його idle-first journal,
ocprobe.log restore та прибирання research-файлів відкладені іншому виконавцю.

D0 in_progress, **0/3 accepted RUN**. E90 native audit підтвердив:
failed delete−2 все одно доходить до internal state4; destructor може
free/unload code. Task15/17 cancel index — значення0, adapter rc0 не
гарантує completion. Host21 утримує pending/failed ownership через
QUARANTINE без close/free; runner deadline зберігає journal без KILL.
Це не доведений безпечний cancel; потрібне ручне відновлення при відмові.

Зібрано ARM35120 Б8FD9FAE1…/generic run-stop DSP3900 Б7B07E8D0…;
DOFF,14 E90 imports, ASM і чотири offline runner tests passed.
DSP stop reclaim повертає0x8000 native wrapper без повторного input issue;
доставка EXITACK не перевірена. SIS21 A3592773… доставлено як
E:\c55stream-d0-v21.sis, GET-equal. Встановлення потребує людини;
HELP_NEEDED.md містить конкретний крок. Restore SIS22 9C2D310E…
підготовлено з exact original host20 EXE; ще не доставлено.

D1 pending: native reserve27/map31/unmap34/unreserve28 і map record24 Б
уточнено статично. Address units, pinning/cache/endian/notify ще невідомі.
Mapping/ring16KiB та latency/bandwidth не виконувалися; негативного
висновку про zero-copy немає. Порядок апаратного probe — LIFECYCLE_DMM.

D2 in_progress: docs/PS1_CANDIDATES_2026-10-01.md готовий як проміжний
вердикт для старого copy channel. Формула еквівалентна S/N<A та
W>H+D+S/N−A: H>A саме по собі не виключає async. MDEC actual input
1536 Б, RGB15/24 outputs512/768; за сценарію9MB/s навіть traffic floor
227.56/256us проти A50us. MIX-only SPU sampled A370–378us проти mean
PCM floor326us: це лише44–52us для входу/L/D/setup; maximum914 samples
не можна порівнювати з mean A. За сценаріюL500us blocking програє.
Повний SPU A1585–1599us ще не має виміряного DSP kernel.
WSOLA:385us є paired saving N95, DSP path641/732us N95/E90;
SMLAD135–200us лише оцінка. Для E90 при N1000/create-only потрібна
незалежна W>606/541us. Сам W й ARM submission CPU time не виміряні.
Application gain не заявлено; остаточний D2 залежить від D1.

Clock probes READ ONLY: CM_CLKSEL1_PLL00056400, CLKSEL2_PLL2,
CLKSEL_MPU2, CLKSEL1_CORE04360626, CLKSEL_DSP343. Фактично stock
ARM330.24/bus110.08/DSP220.16MHz, PRCM writes немає. Original ocprobe.log
повернуто GET-equal. О19:02 UTC GET усіх5 початкових файлів exact:
DSP E039E983…, stream log CFE4DF8B…, clock log BE58F5EF…,
host20 CBB91873…, sys/hash B3AB7C72…. PS c55stream/ocprobe0,
startTick75535 незмінний; нового c55stream START/RUN не було.

Authoritative docs/evidence/2026-10-01: e90-d0-d1-native-audit.json,
d0-run-stop-v21-artifacts.json, e90-d0-session-checkpoint.json,
ps1-candidates-calculation.json; docs/LIFECYCLE_DMM_2026-10-01.md.
Normal PC DSP rebuilt після variant. Private/main GitHub live verified.
Далі: фізичне install21, inspect/clock/create, три clean RUN, потім D1.

Пізніша спроба installer observation о19:10:31 UTC отримала
`TimeoutError: timed out` у connect3s до будь-якої daemon-команди.
О19:02 залишається останнім підтвердженим станом; поточна доступність
E90 невідома. HELP доповнено запитом відновити Wi-Fi-демон.

О19:12:52 UTC другий connect повторив TimeoutError до INFO. Hardware
робота зупинена до повернення демона; доступність не названа підтвердженою.

Завершальні offline gates passed: source/artifact/proof SHA256, всі нові
evidence paths і статуси D0–D2, повторний native audit і numeric D2
recalculation; Python compile, environment/manifest8/8 і чотири runner
tests. Історичні F01–F08 не підмінюють критерії нового доручення.

Після publication08ad9f9 у HELP_NEEDED з'явилася відповідь людини через
оркестратора: SIS21 встановлено, E90 демон ще недоступний. Третій
connect (verify03) також отримав TimeoutError до INFO; ліміт3 вичерпано.
Install21 є повідомленням людини, не GET-підтвердженням нового EXE.
Потрібно повернути лише E90 Wi-Fi-демон; повторний SIS install не потрібен.
Усі п'ять originals exact о19:02 — історичний checkpoint до цієї установки;
поточний host/hash не перевірені. DSP RUN у цій сесії не виконувався.

## Продовження D0: три experimental RUN, 0/3 accepted

Host21 GET-proven8FD9FAE1…; stock read-only clock330.24/110.08/220.16MHz.
Candidate21:8 correct packets, state3, delete/status−2, QUARANTINE.
Після human reboot GET journal CE5B1947… до нового START/PUT; originals
DLL/log/clocklog повернуто exact. Candidate22 (await RMS_EXIT після
stop/output reclaim):8 correct packets, state2, delete−33/pending.
Host21 GET живого журналу дав−14; після human reboot GET F35CDF7F…,
originals знову exact restored. До першого RUN було окреме reboot
між read-only verify і невдалим connect clocks; не приписувати його RUN.

Host22 додає EFileShareAny. Package23 SIS0F8577C6… GET-equal, human
install, GET exact EXE35120 БAFF498B8…/PS0/startTick91233.
Третій RUN — generic run-message-diag3836 БB1CB8409…:3 правильні
STRM snapshots, NODE_getMsg(0)=0/putMsg(0)=1, fromDSP count1,
record cmd600/arg1F0001/arg2/source77E0 після ror16. Після return
message-get−2/state3/delete−2/QUARANTINE. Живий journal D29CDA12…
GET succeeded; host sharing реально перевірено. KILL0, нових RUN немає:
ліміт3 вичерпано. Native cause ще не доведена; valid shared record
не доводить IRQ/DFC, actual ARM reader flag або EXITACK delivery.

D0 лишається0/3; D1 hardware не відкрито. Offline DMM reference audit
уточнив candidate flags, C55 sample address/length /2 і flush/invalidate;
це primary sample, не verified Nokia mapping. D2 provisional report
збережено:385us WSOLA saving, не DSP kernel; SPU mean PCM2934.75 Б
не плутати з maximum3656 Б. Емулятор і N95 не чіпалися.

Поточна залежність: human E90 reboot/daemon після третьої QUARANTINE,
GET journal/PS0 до запису, exact DLL/log/clock restore; далі restore SIS
revision25 із exact original host20 EXE, installer і GET EXE/sys/hash.
Старий restore package22 лишився історичним; після install package23
потрібен вищий25. HELP_NEEDED має конкретні кроки. Відновлення host
поки не називати завершеним. Докази — e90-d0-resume-checkpoint.json;
всі3 variants archived local, raw logs/JSON published without binaries.

DOFF/import/ASM gates passed, п'ять offline runner tests passed; normal
PC DSP rebuilt EXIT0 після diagnostic. Native audit і numeric D2
відтворено; початкові user edits APPLICATION_CANDIDATES і task file
лишено поза commit. F01–F08 historical completion не закриває D0–D2.

## Рішення людини і ROM reference preflight — продовження

HELP_NEEDED о23:22 local передав рішення людини: загальний ліміт3 RUN
знято; лише нова задокументована гіпотеза, максимальна діагностика,
ніякого KILL/unload живої сесії. Попередній запис про остаточну зупинку
через ліміт відтепер історичний. D0→D1→D2 продовжуються.

Human reboot23:27, GET final-recovery01 journal D29CDA12… до PUT,
PS0/startTick61475; final-restore01 original DLL/log/clocklog exact.
Native E90 Z:\system\apps\strmcopy\strmcopydyn.dll55l GET4396 Б
99298562…; всі DSP фази виконує ROM code. Гіпотеза control:
custom execute/return versus host/native lifecycle;8 exact echo packets.
Host23 package26 D383BF30… встановлено, GET36492 Б31836A0F….
Native-reference01 завершився select−6/FINAL−6/EXIT−6 до allocate/create/
RUN, без QUARANTINE. Отже на цей момент усе ще ТРИ experimental RUN.
Причина preflight: ROM .dcd_register лише properties:0, libraries3/2
не зареєстровані. Я не перевірив це до host23 SIS; зайва установка.
Native-preflight-restore01 повернув усі3 research originals exact без reboot.

Research copy strmcopy-e90-library2.dll55l4396 Б308090D3… змінює тільки
registration:0→:2 і packet checksum (дві byte positions3807/3883).
DSP code/data/relocations exact unchanged, DLLdump PASSED;
ROM/firmware не записуються. Host24 parse original ROM properties,
потім E research library2. Гіпотеза та safe fail-stop незмінні;
control не закриває D0 own-node criterion. Host24 package28
CEB641F9… доставлено GET-equal; install/GET ще очікуються в HELP.
Restore exact original host20 готовий як package29 A2620208… для кінця
дослідження; EXE/hash зараз навмисно research, не називати full restore.

D1 статично додано native MMU mask803EF01C..803EF07C: endian bit1,
mixed bit2, element bits3..6; grammar збігається з TI header. Full path,
address units/default flags/cache/pinning ще не доведені. Native() у
старому host просив fixed4096 — це не доказ kernel maximum4096;
можливість requested16KiB окремо перевірити після D0.

Поточний доказовий checkpoint — e90-d0-resume-checkpoint.json і
native-library2-derivation.json; latest build/source proof native-copy-host-v24.
D0 0/3, D1 pending, D2 provisional. N95 не отримував команд.

## RUN4 native control і відновлення 2026-10-02

Host24 runtime/package28 installed; native-reference02 GET exact EXE
12356F00E0163EF0B0823A0E017D38A2796DCE83F2AB1FA85554DCFFF32A09D8.
Separate ROM properties0 та research library2 parse обидва0, але select−6
до allocate/create/RUN. Native-preflight-restore02 повернув originals3
exact, без reboot. Native-reference01/02 НЕ додають RUN до лічильника.

Combined reference4476 БC75723582115997EF143D23565587E3FA90AB24FB710F1BAB8AD4C69CBDDF8F8
додає0+2 в одному registration packet, виправляє section size/offsets і
checksums; усі non-registration packets/code/data/relocations exact.
DLLdump PASSED; derivation і artifact30 published. Native-reference03
select/create/RUN0,8 exact echoes512 Б, checked256 words each;
wall_us579/488/488/488/457/457/488/488. Create9674us. Delete−33/pending,
state2 до/3 після, QUARANTINE; live GET journal A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1.
Це RUN4, KILL/unload0, PRCM writes0. Частоти read-only знову stock
ARM330.24/bus110.08/DSP220.16MHz. D0 own0/3, native control не зараховано.
Failure лишився з незмінним ROM execute: локалізація до host/setup/native
path, але message delivery/cleanup/EXITACK причина ще не доведена.

Human/user підтвердили reboot після RUN4 і запуск демона02.10 о04:07 local.
Попередній процес Codex зупинився через usage limit, не device failure.
У цій спробі продовження GET journal/PS0/restore НЕ виконано: три bounded
connect attempts до .21:2323 — Python3s, Python8s, .NET8s — timeout до INFO.
Жодного нового PUT/START/RUN. Маршрут ПК192.168.3.11/24 йде через Wi-Fi.
HELP01:12UTC просить daemon INFO/END, закриття сторонніх TCP клієнтів,
звичайний restart демона за потреби; новий reboot не запитується.
Original DSP/log після RUN4 ще не відновлені; clock log був exact до RUN4.
EXE/hash навмисно research24, full restore original20 також ще не зроблено.

Наступна D0 гіпотеза: own STRM snapshots до очікування RMS_EXIT, після
NODE_getMsg, після idle/reclaim до return. Host має забрати snapshots під
час pending delete, щоб відокремити EXIT receipt/cleanup/EXITACK, зберігаючи
fail-stop. Не повторювати old RUN без зміни. Спершу transport recovery,
GET old journal/PS0 і exact originals3; потім новий diagnostic. Якщо він
встановить і виправить причину,3 consecutive own create/RUN/8 packets/
delete/free/native/FINAL/EXIT0 з unchanged daemon startTick. D1 до цього
hardware не запускається. D2 prior-copy-channel provisional; emulator
не змінювався. N95 не отримав команд; його idle-first/ocprobe restore/
прибирання research лишаються відкладеними іншому виконавцю.

## 2026-10-02 13:35 — RUN4 recovery завершено, host25 diagnostic підготовлено

Після human reboot13:21 `native-recovery03` (bounded45s) GET-нув журнал
перед PUT/START. SHA точний, як у live RUN4:
`A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1`.
PS c55stream/ocprobe0, INFO screen800x352/startTick81256. DSP research
reference C7572358… підтверджено GET. `native-restore01` повернув saved
original DLL3668Б E039E983…, log21528Б CFE4DF8B…, ocprobe.log1249Б
BE58F5EF…; кожен PUT→GET exact. Host24/hash лишаються дослідними.

Зібрано host25 EXE39504Б
`CB74DE96012E3C9D4D7DDE6F783C6A746F75713B83DBF136DF03001C7035CA0A`,
own DSP `run-exit-diag`5144Б
`29069D525B9209CA808F0D9315AA23BACCF222B44B6D6ABEFFC0B37B8EBB2833`.
Builds ARM/DSP/SIS bounded EXIT_CODE0; DOFF/ASM та18 baseimage imports
перевірено; immutable artifact revision31. Новий mode `exit-stages`:
8 protocol21 full payload packets; snapshot stage4 before NODE_getMsg;
combined stage5 after get і stage6 after input/output idle, protocol25,
512Б offsets0/96 C55 words. Raw MSG headers/records read-only; snapshots
не atomic. Host output request замовляється до control6, persistent
descriptor/status утримуються до completion чи QUARANTINE. Extra output
після idle впливає на cleanup; лише clean delete доводить final reclaim/
idle/EXITACK, diagnostic не входить у3 звичайні D0 цикли.

`exit-diag-sis01` доставив `E:\c55stream-exit-diag-v25.sis`, package31,
22416Б SHA8D0E3BE8…; GET-equal, PS0, unchanged startTick81256.
HELP13:35 просить людину встановити цей SIS, повідомити та лишити демон.
Restore SIS32 готовий із точним saved original host20 EXE, SHA6E6C81E0…;
ще не доставлявся й не встановлювався. Чекаючи встановлення host25,
нового RUN не робив: experimental4, own D0 0/3, D1 hardware pending,
D2 provisional. Нових PRCM writes/phone KILL/N95 команд немає.
Опубліковано88 raw proofs; checkpoint hash/native audit/calculation PASS.

## 2026-10-02 13:43 — RUN5: RMS_EXIT і перший idle доведено, delete pending

Людина через оркестратора о13:38 дозволила заміну нашого EXE/hash без
установника: hack E90 активний. `host25-deploy01` backup-нув host24
EXE/hash GET до PUT, saved originals20/hash перевірені; host25/hash
GET exact (EXE CB74DE96…, hash20Б SHA-256 EDDE22CA…). SIS31 не
встановлювався; фізичний installer більше не потрібний.

`exit-diag01`: fresh read-only clock m86/div3, ARM330.24/bus110.08/
DSP220.16MHz, restore clocklog exact; inspect/create preflight FINAL/EXIT0,
unchanged daemon startTick81256. Один новий own diagnostic RUN5:
create8941us, RUN0, усі8 packets512Б/240 checked payload words correct,
timings457/396/396/366/366/396/396/396us, median396/range366–457,
total3169us. Ці числа діагностичні, не D1 і не application speedup.

Stage4 before exit: pending input/output0. Stage5 NODE_getMsg result1,
waits1, cmd80000000/arg1=env77E0/arg2=0/status00008000. Stage6 після
STRM_idle(input/output): обидва rc0, pending0/status00008000.
RMS_EXIT receipt та перший cleanup у цьому RUN фізично доведені.
Stage6 передує extra output reissue/reclaim/idle: фактичний останній idle,
execute return/EXITACK і native delete callback ще не доведено.
Delete submit0/pending, через5000ms−33/pending; state2→3, QUARANTINE.
Local runner30s timeout без KILL/free/close. Live journal GET успішний:
`778039EBA2B21B3A07F65FB7EDF89040F2BBB386CF1C11B84157B76023F1691E`.

HELP13:43 просить human reboot E90/daemon; тільки після підтвердження
GET journal/PS0, then originals3 exact restore. DSP/log зараз research25,
clocklog exact restored до RUN5; host25/hash research і тримають ownership.
Нового unchanged RUN не робити. D0 own0/3, experimental5; D1 pending,
D2 provisional unchanged. ARM outbound MSG reader flag actual value,
IRQ/DFC/EXITACK і native callback ще відкриті. N95 без команд; його
idle-first/clocklog/research cleanup відкладено іншому виконавцю.
Опубліковано97 raw proofs; original host20 direct restore дозволено,
але робити лише після PS0 та originals3 restore, не під live owner.

13:54 `exit-recovery01` read-only GET journal/DSP + INFO/PS: SHA journal
778039EB… unchanged, DSP29069D52… unchanged, c55streamPS1/ocprobe0,
startTick81256 unchanged. Телефон/демон відповідають, але reboot не
відбулося й QUARANTINE owner ще живий. Restore/новий RUN зараз заборонені
ownership guard. Human request13:43 активний; додаткових PUT/START/KILL
не було. Докази цієї read-only перевірки теж опубліковані.

## 2026-10-02 — recovery RUN5 і нова outbound MSG гіпотеза

Human reboot після RUN5 підтверджено. `exit-recovery02` GET journal
SHA778039EBA2B21B3A07F65FB7EDF89040F2BBB386CF1C11B84157B76023F1691E,
PS c55stream/ocprobe0, INFO screen800x352/startTick65704.
`exit-restore01` повернув original DLL/log/ocprobe.log PUT→GET exact.
EXE/hash дослідні25; full host20 restore ще не робився. Нового RUN немає.

Static wrapper24E6F0 після execute return сам робить NODE_putMsg
cmd40000000/arg1=return/arg2=0/timeoutFFFF. MSG_fromDSP24C928 копіює
native long fields у window, ставить empty0 і interruptGPP. C55 board
803F0208 використовує common base +8; getter +164 тому вказує на
embedded interface +172. Init803F03C0 явно записує byte236=1,
тобто reader byte64=1. IVA +164 без цього store — інший board.
Це уточнює статичний початковий стан, не вимірює runtime value.

Нова перевірка `worker-message`, host26/protocol26/artifact33:
finite priority15 worker створюється в create і чекає один STRM input;
host prearms MSG receive і STRM output у CREATED до trigger. Worker
надсилає NODE_putMsg606/A1B2C3D4/env, read-only MSG/window snapshot7,
reclaim/idle і повертається. Created delete joins terminated worker
перед free. Офіційного RUN і wrapper EXITACK немає: це відокремлює
outbound ARM MSG reader від execute return без нового RUN. Попередній
RUN3 arm receive лише після execute return; його−2 не доводив delivery.
Успіх цього diagnostic не зараховується до D0. Pending/failure зберігає
ownership; KILL/unload живого owner немає. Build ARM/DSP/SIS EXIT0,
DOFF/ASM і25 base imports checked. Host direct replacement дозволений.
Після одного diagnostic зберегти journal/PS, restore3 якщо PS0.
D0 own0/3, experimental RUN5; D1 hardware лише після D0; N95 без команд.

### Created-worker preflight результат, 15:16–15:21 local

Host26 GET exact40920Б2EAC917E90CF78F18A6EA1DBD9EE117FF9CB2398C6269414E559B4140758D787,
DSP5616Б71B4D893956BEBD2575D0CF6A50706D75FC71AFD69F0D74B8EFBCD78ED0BC265.
`worker-msg01` завершив inspect0 і create0/7598us; active worker чекав
input. Create-only preflight перейшов до delete без native buffers і
trigger: delete−33/pending, state1 залишився1, QUARANTINE. До офіційного
RUN або outbound NODE_putMsg606 не дійшло. Це нова проблема no-input
stop/join/idle, не негативний результат MSG. Runtime setter flag1 і
source binding доведені лише статично, фізичної доставки MSG не додано.

Live journal GET2092БB9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92.
`worker-recovery01` read-only о15:21: той самий journal/DSP SHA, INFO
screen800x352/startTick65704 unchanged, c55streamPS1/ocprobe0. Живий
QUARANTINE owner блокує restore та наступний запуск. HELP15:16 просить
reboot/daemon; KILL0, додаткових PUT немає. Початкові E:-файли були
exact після RUN5, зараз DSP/log research26; clocklog original exact.
Host26/hash research лишаються; full original20 restore не зроблено.

Порівняння archived e90-worker-stream-one-v17/prepare показало: старий
успішний streaming worker завжди одержував final input, create-only
preflight для нього не робився. Отже повторне використання нового
create-only preflight було зайвим. Session script тепер пропускає його
лише для worker-message: одразу prearmed MSG/output→single final input,
reclaim/idle→terminated worker→created delete. Це не виправлення й не
доказ stop без input. Нічого не запускати до human reboot і GET/PS0/
originals3 restore. Якщо далі MSG проходить, відокремлено ARM reader
від wrapper return; якщо ні, raw snapshot/pending receive локалізують
канал. D0 own0/3, experimental RUN5 unchanged; D1 pending; D2 provisional.
Оркестратор окремо повідомив про свій один LS E:\PS1\cfg\ на E90,
без write/START; його факт не входить у наші experiment/RUN counts.

## 2026-10-02 21:16 local — ознайомлення після перенесення, доступні обидва телефони

Користувач дозволив для тестування і N95, і E90; попередня заборона
опитування N95 в CODEX_TASK_2026-10-01.md більше не діє. Мета лишається
асинхронна робота DSP паралельно з корисною роботою ARM.

Read-only INFO/PS перевірено за явними адресами без fallback:
N95 .22:2323, screen320x240, startTick22918156, c55stream/ocprobe PS0;
E90 .21:2323, screen800x352, startTick65704, c55stream PS1/ocprobe PS0.
E90 GET E:\c55stream.log:2092Б, SHA-256
B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92,
точно збігається з created-worker preflight15:16; delete−33/pending,
state1, QUARANTINE. Локальна копія:
out/reorientation-e90-journal-20261002-211633.log.
Отже попередній owner досі живий; перед PUT/START/restore потрібні
human reboot E90/daemon, повторні GET/PS0 та originals3 exact restore.
Нових phone PUT/START/RUN/KILL не було, experimental RUN5 і D0 own0/3.

На поточному ПК python/python3/py не знайдені в PATH; bounded виклики
strict_net.py завершились до підключення. INFO/PS/GET виконано через
.NET TCP з connect/read deadlines3/5с. Перед відновленням Python runners
потрібно знайти або відновити Python і перевірити шляхи toolchain/SDK.
Git HEAD bac5ffa, збережені незакомічені правки та нові докази попередньої
сесії; у цьому ознайомленні commit/push не виконувались.

## 2026-10-02 вечір — finite MSG діагностика E90 і N95, повне відновлення

За повідомленням користувача E90 перезавантажено. laptop-recovery01:
GET old journal2092Б/B9B4E282… exact, DSP71B4D893… exact, PS0,
новий startTick61087. laptop-restore01 originals3 PUT→GET exact.
Знайдено Python3.12 через C:\Program Files\LibreOffice\program\python.exe;
check_state перевірив SDK/toolchain наD: і TI CGT4.4.1 наC:.

E90 laptop-worker-msg01/host26: finite final input, prearmed MSG/output,
DSP put1, stage7 cmd606/A1B2C3D4/env77E0, STRM completions0/0.
ARM receive−33/pending; created delete0/DELETED5, task/native free0,
close пройшли, FINAL/EXIT−33 через receive. Немає QUARANTINE/reboot.
Host27 додав raw record і after-delete status та receive після output.
laptop-worker-queued01 і laptop-worker-prearmed27: той самий DSP put1/
snapshot; ARM receive−33, cmd/args0, statuspending до delete, clean
delete/free/close. Ці три E90 варіанти без нових доказів не повторювати.

Host28 дозволяє той самий finite diagnostic на підтвердженому N95
профілі. Перед заміною snapshot5 у work/evidence/n95/d0-20261002.
Усі25 candidate imports є у saved N95 baseimage. Перша підготовка
worker-msg01 відхилена stock guard до DSP START: N95 має наявнийm111.
Read-only exact profile guard для finite MSG підтвердив PLL0006F400/
sel2=2/MPU2/core04360844/DSP23C3: за регістрами ARM426.24/bus213.12/
DSP284.16MHz. PRCM writes немає; це не performance benchmark і не
per-packet DVFS proof. worker-msg02 дав той самий receive−33/empty record,
DSP put1/snapshot і clean created delete/free/close. Отже проблема
відтворюється на обох; конкретна ARM mapping/reader/source/IRQ причина
ще не доведена. Snapshot headerempty_after1 не є достатнім доказом DFC.

На обох повернуті **всі5 originals**, включно з EXE/hash, PUT→GET exact.
laptop-final-verify01/E90 і final-verify01/N95: host20, c55stream/ocprobe
PS0, startTick61087/22918156 unchanged. Нових official RUN0, KILL0,
reboot0 у finite серії; historical experimentalRUN5, D0 own0/3,
D1 hardware pending, D2 provisional. No-input worker cleanup не виправлено.

Local host28/protocol26/artifact37, ARM builds27/28 і SIS/import/DOFF
перевірки успішні; 8 offline session/clock guards tests проходять.
Докази публікує tools/summarize_worker_messages.py, єдиний поточний
checkpoint — docs/evidence/2026-10-02/worker-message-checkpoint.json;
e90-d0-resume-checkpoint.json також оновлюється з цими результатами.
Звіт — docs/WORKER_MESSAGES_2026-10-02.md. Фізичних дій зараз не потрібно.
Наступне: простежити runtime pointer ARM window/reader/queue та підготувати
bounded read-only snapshot із перевіреними межами. Лише після нової
доведеної гіпотези — наступний MSG/RUN. Емулятор не змінювався.

## 2026-10-02 — відновлення host29 diagnostic, ARM pointer audit та exact restore

Після прохання користувача продовжити знайдено незакомічені host29 правки
та session work/evidence/e90/d0-20261002-pointer, які були новішими за STATE.
Попередній хід уже встановив host29 і виконав patcher-read-check:
три копії24Б з власної RAM, ROM803F7664 і BSSC8010B20 до власного буфера,
FINAL/EXIT0, DSP open0/kernel code writes0/PRCM writes0. Не повторювали.
resume-reader01 повторно отримав journal SHA56167F767D4B30FF225DA24BFB0F6666FD25F16B9FB22B1398D4DBB911195D76,
PS0/startTick61087; original DSP E039E983… unchanged.

Новий offline tools/rev/audit_arm_message_runtime.py перевірив28 instructions,
2 BL targets, BSS header і reader code. Board+264→context364Б,
context+48=board+8, context+24=reader=board+172,
reader byte64=board byte236 initialized1. Reader DWORD0 є shared base;
fromDSP header context+224, records context+240=header+8, queue source16,
pending40. BSS C8010B20 — flags, не MSG root; runtime swap byte не прочитано.
Живий board/context root, його lifetime і mapping bounds ще треба довести
через audited native object lookup. Нового MSG/RUN на припущеннях не було.

Read-copy validator посилено: точні words/source/size/order/destination,
firmware/profile, no DSP open і FINAL0; обробляє native CRLF. 9 offline
session tests пройшли. Source/EXE host29 hashes exact artifact38;
успішна bounded ARM build у попередньому ході, нової source зміни ARM немає.
check_state -RequireArtifacts -RequireStreamArtifacts успішний.

resume-restore01 + resume-hostrestore01 повернули всі5 originals E90.
resume-finalverify01: кожний GET/SHA exact, host20, c55stream/ocprobe PS0,
startTick61087 unchanged. N95 у цьому продовженні без команд; його останній
proof лишається restored host20/PS0. Нових MSG/RUN/KILL0, D0 own0/3,
historical experimentalRUN5, D1 pending, D2 provisional. Фізичної дії не потрібно.
Публікація16 raw proofs: tools/summarize_arm_message_runtime.py;
поточний checkpoint docs/evidence/2026-10-02/arm-message-runtime-checkpoint.json,
звіт docs/ARM_MESSAGE_RUNTIME_2026-10-02.md. Наступне — live root provenance,
не повторення failed receive. Pre-existing docs/APPLICATION_CANDIDATES.md
правки лишаються окремо у working tree.

## 2026-10-02 — передача agy

Користувач попросив зберегти підсумок для agy. Повний handoff:
work/HANDOFF_AGY_2026-10-02.md. Він містить поточні D0–D2 criteria,
proofs/restore, дозволений і перевірений push5fc3071+26d6354, новий offline
container-root/factory/manager розбір після commit26d6354 і наступні дії.
Нових телефонних команд після restore не було. Runtime container root
C80019D4 виведено лише зі saved kernel export251; bounds/type/lifetime
ще потребують аудиту. D0 own0/3, D1 pending, D2 provisional unchanged.

## 2026-10-02 (продовження agy) — офлайн-аудит кореня контейнерів ядра, фабрики PDD та менеджера

Виконано крок 1 з наступних дій handoff: повністю завершено офлайн-аудит
кореневих контейнерів ядра, меж масиву, типів об'єктів, vtable фабрики PDD
та ланцюга покажчиків до плати й контексту.

1. Корінь контейнерів ядра (експорт 251 `Kern::Containers`):
   E90 експорт `80037778` завантажує літерал `80038084` = **`C80019D4`**;
   N95 експорт `8008CE40` завантажує літерал `8008DC1C` = **`C80019F0`**.
2. Межі масиву й типи об'єктів:
   Системний виклик `TFindHandleBase::NextObject` (`ekern.exe` `8002B930`)
   перевіряє `8002B934: cmp r0, #17` (рівно 17 контейнерів, типи 0..16),
   при перевищенні викликає паніку `movcs r0, #25` (`EBadObjectType`).
   Масив містить 17 слів (68 байтів, для E90 `C80019D4`–`C8001A18`), що
   підтверджується перевіркою `8003FCD0: cmp r4, #17` з літералом `C8001A18`.
   За опкодами `euser.dll` `TFind*::Next` підтверджено: тип 10 — `DPhysicalDevice`
   (слот PDD `C80019FC` на E90, `C8001A18` на N95), тип 9 — `DLogicalDevice`
   (слот LDD `C80019F8` на E90).
3. Структура `DObjectCon` (експорт 12 ядра `80038290` / `8008D638`):
   `+16` — `iCount`, `+20` — масив `iObjects`, `+24` — м'ютекс `iMutex`.
4. Ідентифікація фабрики `ehwaomap` (PDD експорт 1 `803DD8A4` на E90, `80199254` на N95):
   виділяє 120 Б, конструктор встановлює vtable **`803F8380`** на E90
   та **`801B3D44`** на N95. Серед об'єктів PDD-контейнера фабрика шукається
   за правилом `*(TUint32*)obj == 0x803F8380` (на E90).
5. Менеджер процесора 0 (DSP):
   зберігається у `factory + 48` (виділення 68 Б), конструктор `803E32E8`
   встановлює магічне слово `434F5250` ('PROC'), `manager + 56 = factory`,
   `manager + 60 = 0` (DSP).
6. Інтерфейс плати (`board`):
   setup менеджера `803E3348` виділяє 336 Б (конструктор `803EFFCC`),
   додає 8 і записує `board + 8` у `manager + 44`.
   Базова адреса плати: `board = *(TUint32*)(manager + 44) - 8`.
7. Повний ланцюг до спільної пам'яті:
   `board + 264` → контекст (364 Б), `context + 48 = board + 8`,
   `context + 24 = board + 172` (читач), `reader byte64 = board byte236` (1),
   `reader DWORD0` = ARM базова адреса спільної пам'яті DSP,
   `context + 224` → заголовок `fromDSP`, `context + 240` → `records = header + 8`.
8. Додано відтворюваний інструмент `tools/rev/audit_kernel_containers.py`,
   скрипт публікації `tools/summarize_kernel_containers.py`,
   доказ `docs/evidence/2026-10-02/kernel-containers-audit.json`,
   звіт `docs/KERNEL_CONTAINERS_ROOT_2026-10-02.md`.
9. Регенеровано дизасемблер `out/e90-ldd-disasm.txt` з реальною базою `803F8648`.
10. Модульні тести в `tools/test_e90_task_session.py` розширено перевіркою
    кореня контейнерів і фабрики (10 тестів проходять); `check_state.ps1` успішний.
11. На момент цього офлайн-аудиту телефонні операції ще не виконувались.
    Пізніший стан наведено в checkpoint нижче.

## 2026-10-03: продовження після Gemini, колізія native source

Цей checkpoint замінює попередні твердження про актуальні телефони/лічильники.
Gemini виконав live pointer snapshot і кілька невдалих RUN, але D0 лишився0/3.
Огляд: work/GEMINI_REVIEW_2026-10-03.md.

E90 доступний, PS0/startTick33897. Останній Gemini create32 journal отримано:
закінчується BEGIN select node, до create/teardown. Original DLL/log/clocklog
повернуто GET-equal; EXE/hash restore заблокований ERR open−46 у C:\sys\bin.
Потрібен Open4All. Recovery/restore: d0-20261003-cycle2/codex-*.json.

N95: один новий official diagnostic RUN передав8 correct packets512Б,
2987us; delete−33/pending, не прийнятий D0. Snapshot до delete виявив
дві черги source77E0: старий node C81CF8D0 і новий C81BBDE0.
Після delete fromDSP record — EXITACK40000000/EOK8000/source77E0.
Старий node env очищено, новий лишився pending; routing обирає перший
збіг. Для причинної перевірки потрібен N95 reboot, запитаний користувачу.
Після GET journal авторизований KILL, потім5 originals SHA-equal restored,
PS0/startTick132858: d0-20261003-codex-routing/finalverify01.json.
Clocks підтвердили stockm86, ARM330240/BUS165120/DSP220160kHz.

Host33 прибрав непідтверджений NULL-status/two-delete код Gemini, додав
read-only routing diagnostics. Host34 має pre-RUN unique-source gate:
дубльовані source→відмова до RUN і cleanup лише свого CREATED node.
13 offline tests проходять. Новий host34 ще не перевірений на апараті.
DSP bit-exact candidate41/42; існуюча delay гіпотеза не доведена.
Документ: docs/MESSAGE_ROUTING_2026-10-03.md; JSON checkpoint і native audit
у docs/evidence/2026-10-03. D0 0/3; D1 pending; D2 provisional.
Старий historical RUN5 не є повним лічильником після Gemini.

## 2026-10-03: після підготовки телефонів, host35 без PROC_Load

Попередні Open4All/reboot запити виконано: E90 five originals restored
codex-verify02, N95 новий startTick64375. Обидва доступні, originals backup
у work/evidence/{e90,n95}/d0-20261003-clean34.

Host34 candidate46 d0-sequence: inspect/create clean на обох, перший
RUN guard відмовив до execute — source77E0 matching2. Cleanup CREATED node,
task і два native buffers завершився0; FINAL/EXIT−11, quarantine немає.
Обидва апарати мають старі штатні queues77E0/7700 навіть після reboot.

Встановлено: host34 щоразу PROC_Load-ив спільну базу. Offline ROM audit
на N95/E90 підтверджує безумовний stop перед load/start, manager state4
є running. Host35 candidate47 прибирає PROC_Load, перевіряє running base
через validated manager і підключається до неї, зберігаючи unique guard.
14 tests pass, bounded ARM/SIS build0, DOFF/import/artifact checks pass.

Host35 встановлено й перевірено на обох: attach gate0, create/delete/free0,
RUN guard−11 до execute через конфлікт, що залишився після host34 reload.
Жодного нового official RUN за чотири guarded refusals. D0 лишився0/3;
D1 pending; D2 provisional. На обох originals3 DLL/log/clocklog restored
GET-equal, host35/hash навмисно встановлені; originals EXE/hash збережені.
attach-verify01: PS c55stream/ocprobe0, E90 startTick33897/N9564375.

Користувачу async запитано новий reboot обох і daemon/Open4All: host35
не може виправити вже неузгоджені старі queues. Далі перевірити changed
startTick й запустити d0-sequence35/candidate47 з tag attach-sequence02
в тій самій сесії кожного апарата, без нового snapshot host35 як original.
Точні команди й усі обмеження — docs/BASE_ATTACH_2026-10-03.md;
відтворюваний checkpoint — tools/summarize_base_attach.py.

## 2026-10-03: статична підготовка D1 під час очікування reboot

Повторна INFO перевірка: E90 startTick33897/N9564375, нового boot ще немає.
Попередній goal turn дав progress (host35/commits/evidence); hardware
залежність у цьому продовженні та сама. Нових DSP RUN або mapping немає.

Отримано E90 Z:\sys\bin\ebridgeutil.ldd read-only GET1260Б. Новий
tools/rev/audit_dmm_ownership.py звіряє actual kernel export targets,
19 ARM+13 Thumb checks і всі5 utility BL на N95/E90; однакові dispatch
і map wrapper підтверджені hashes. Сторінки — пари32-bit linear/physical,
map signature має output pointer п'ятим аргументом і flags шостим.
Fn2 DoControl(2,&address,&bytes) clean378→invalidate/prepare376;
fn1 лише copy719 і translate245, без pin/unpin API. Source names звірено
з official Symbian kernel exports; reference SHA збережено.

D1 probe ownership/ring layout16KiB TOTAL уточнено у docs/DMM_ABI_2026-10-03.md.
Це static preparation, не відкриття hardware D1. Pinning/native chunk,
DSP units/cache/order, correctness/wrap/teardown і виміри ще не доведені.
Попереднє твердження «ebridgeutil mem-pin» у findings виправлено.
D0 як і раніше0/3; наступна hardware дія — свіжий boot host35 candidate47.

## 2026-10-03: physical pools audit та очікування зовнішнього кроку

Останній goal turn був progress: DMM ABI audit a7e51ab pushed. Знову
INFO/PS підтвердили E90 startTick33897 і N9564375, c55stream0; reboot
для host35 досі не підтверджений. Це третій послідовний goal turn з
тією самою фізичною залежністю (перший — після підготовки host35).

Статичну підготовку доповнено physical pool record на N95/E90:
owner+244, Epoc::AllocPhysicalRam242, DPlatChunkHw::New60, парні
Epoc::FreePhysicalRam241. Audit23 instructions +6 actual import calls
на кожній прошивці, attrs raw1044. Важлива межа доказу: ці pools ще
не зв'язані з candidate native ARM buffer; ring pinning/lifetime не
заявляється. Host/DSP binaries не змінювались.

Наступне необхідне рішення залежить від свіжого hardware D0 evidence.
Нового RUN у старому конфліктному state не виконувати. D1 hardware
заборонено до D0, D2 без measured D1 не завершується. Чинний запит
reboot/daemon/Open4All у HELP_NEEDED.md; після нього exact host35
candidate47, новий startTick, PS0 і d0-sequence attach-sequence02.
План не завершено: D0 0/3, D1 hardware pending, D2 provisional.

Фінальний verify02 на обох телефонах успішний: три original DLL/log
byte-equal, installed host35 відповідає built artifact, PS c55stream
і ocprobe порожні. StartTick залишився E90 33897 / N95 64375.
Автоматичне продовження зупиняється зі статусом blocked до нового
фізичного boot; це не завершення плану. Після повідомлення користувача
про перезавантаження продовжити з перевірки INFO та D0, описаної вище.

## 2026-10-03: D0 завершено після нового reboot обох телефонів

Користувач перезавантажив обидва та дозволив самостійне встановлення.
E90 startTick60327 / N95 62209, PS0; host35 exact built GET, originals3
GET-equal. attach-sequence02 candidate47 завершився complete=True:
inspect/create та3 consecutive ordinary RUN на кожному,8 correct512-Б
packets/protocol21/240 payload words; delete/free task/free native
out/in/close/FINAL0, EXIT0. StartTick незмінний у всіх steps.
Офіційних RUN додалось6, minimum historical count16; D0 accepted3/3
на кожному. Copy-channel total/packet timings збережено окремо;
це не D1 measurements і не application speedup.

attach-restore03 на обох повернув original DLL/log/clocklog GET-equal.
Host35/hash залишаються встановленими; original EXE/hash backup збережені.
Доказ docs/evidence/2026-10-03/d0-attach-success.json відтворюється
tools/summarize_d0_attach_success.py. D1 hardware gate тепер відкрито:
наступне — native allocation/lifetime provenance і minimal reserve/map
probe, потім16KiB TOTAL ring, ownership/wrap/cache/teardown/measurements.

## 2026-10-03: D1 partial hardware checkpoint, host42 підготовлений

D0 complete3/3 на обох збережено, commit4edbb56 pushed. D1 host41/
candidate54 protocol38: native ordinal30 allocation16384 у CMM region
131072 B; utility1 підтвердив4 linear/physical pages. DSP mapped00300000
BYTE →00180000 WORD; flags17. Flags16 map повертав0, але DSP читав нулі:
це відкинута гіпотеза, clean teardown/FINAL−20; native PDD bit0=page-list
translation доведено статичним аудитом і правильними даними flags17.

Кільце TOTAL16384: control1024 +15 input/15 output slots по512 B,
payload480 B/slot. Додаткові notifications allocations2×4096 B окремо.
Whole-region ownership, utility2 clean→invalidate до handoff і після
completion, ARM не звертається під час DSP ownership. Release тільки
після delete/free task, потім unmap/unreserve/free ring/notifications/close.
Native chunk attrs/DSP cache-order contract ще частково inferred.

N95: три повні серії batches1/2/8/15, по120 exchanges/run,9360 correct
packets. Усі input/output words, slot/sequence wrap/32bit carry перевірені;
delete/unmap/unreserve/free/FINAL/EXIT0, незмінний boot62209. Stock clocks
до/після3 серій ARM330.24/bus165.12/DSP220.16MHz. Exchange batch15 p50
2716us, aggregate useful двобічний bandwidth4.996MB/s. Вимір включає
synthetic transform/verify/cache/notifications; не application H+D.
RThread CPU виміряний; ARM useful parallel W не виконувався. Повний S
включає журналювання (~1s setup), DSP ticks не конвертовані.
ring-final-restore01/host-restore01/verify01 повернули **всі5 originals**
GET/SHA-equal; PS c55stream/ocprobe0. N95 не потребує фізичних дій.

E90: s1-b1/b2 complete,360 correct packets, clean teardown, boot60327.
s1-b8 transport lost. Після повернення daemon: boot33873/boot1 by t, PS0;
ring-recovery03 GET до будь-якого PUT зберіг журнал C1EEA683…,
останній рядок ROUTING queue1/node c816a6b8. Немає ring allocation/map,
own task create/RUN/FINAL. Причина boot change невідома; не називати
це DSP batch8 failure і не повторювати unchanged candidate.
ring-final-restore01 повернув original DLL/log/clocklog, completeTrue.
ring-final-host-restore01 зупинився **до PUT**: ERR open−46 на GET
C:\sys\bin\c55stream.exe. Після reboot потрібен Open4All; запит async
надіслано. E90 EXE/hash наразі host41 research, originals saved.

Наступна гіпотеза: initial non-atomic snapshot читав448 B сторонніх
native nodes, lifetime яких task handle кандидата не утримує. Host42
candidate55 прибрав foreign-node dereference; own retained node і unique
queue gate збережені. Це не доказ причини reboot; list/queue reads і далі
non-atomic. ARM/SIS builds0, DOFF dump/imports15 verified; candidate55
**не встановлений/не запускався**. Current out/arm —host42, out/dsp —ring52.
Proof docs/evidence/2026-10-03/d1-ring-v55-artifacts.json, SIS
out/sis/c55stream-d1-v42-r55_sha1.sis. Artifact54 archive у
work/evidence/artifacts/c55stream-dmm-ring-v54; не підміняти новою збіркою.

Після Open4All E90: exact restore-host з НОВИМ tag, verify всі5 originals;
потім deploy-host42 + deploy-dsp ring з artifact-proof55, finite inspect/
provenance gate і8-frame correctness до120 frames. Якщо знову failure —
GET журнал, stop, без KILL/unchanged replay. За успіху три повні серії
`tools/run_ring_series.py --device e90 --host-version42 --revision55`
(CLI використовує окремі tokens: `--host-version 42 --revision 55`).
Runner stop-first-failure, boot незмінний у серії. Не змішувати54/55 samples.
Перед restore отримати всі журнали; завершити5-original GET/SHA verify.

Докази: docs/DMM_RING_2026-10-03.md, d1-ring-results.json з samples/SHA,
tools/summarize_ring.py, native mapping flags audit. D2 conditional
перераховано tools/assess_ring_candidates.py: правильні7200 B payload/
direction, MDEC max3 blocks без repacking, SPU int32 потребує tiling;
application-specific T/A/W невідомі. Емулятор і користувацький
docs/APPLICATION_CANDIDATES.md не змінювалися цим продовженням.
D1/D2 in_progress, повний план НЕ завершений. check_state8/8 стосується
старих F01–F08; тепер також друкує актуальні D0–D2 statuses.
Стара goal blockage після D0 reboot подолана; нова фізична залежність
Open4All — перший новий turn, не підстава повторно маркувати blocked.

## 2026-10-03: останній стан — E90 candidate56 interrupted s2-b2

Користувач увімкнув E90/Open4All. ring-final-host-restore02 і verify01
довели всі5 originals перед deploy42. Candidate55: provenance0,
short8×batch8 correct, s1-b1/b2 clean360 packets, але s1-b8 transport lost.
Користувач повернув daemon; ring55-recovery02 GET до PUT, boot33372,
PS0, journal E4ED8570… закінчується DMM POOLS перед broad board read.
Немає map/create/own RUN. Foreign-node-read hypothesis не вирішила
проблему; ні kernel reboot mechanism, ні DSP failure не доведені.
ring55-final-restore01/host-restore01/verify01 повернули всі5 originals.

Offline saved E90 patcher.ldd SHA423E4FF1… decompressed elf2e32 dump
аудитовано22 words: control105 destination=*a1, source=TDesC8::Ptr,
length=low28 descriptor; raw memcpy725 під ThreadEnterCS401/LeaveCS402.
ROM destination має окрему32-B copy branch; user destination fixed256B
limit не має. Контракт не використовує fault-safe user-copy/pinning;
це мотив для user-mode destination pre-touch, не proof root cause.
Доказ e90-patcher-copy-audit.json, tools/rev/audit_patcher_copy.py.

Host43/candidate56: ReadKernel Mem::FillZ destination до Ctl105, broad
336-B board read прибрано; foreign nodes не читаються. ARM/SIS0,
DOFF/imports15 verified. Deploy/provenance/short batch8 frames8 clean.
Довга серія1 batches1/2/8/15 і clock-after — completeTrue,120 frames
кожен,3120 packets; серія2 clock-before і b1 —ще120 packets. Усі512
input+output words/packet checked, wrap/carry, clean teardown, boot33372.
На **ring-r56-s2-b2** daemon PS перестав відповідати, run_error TimeoutError
і journal_error збережені окремо. GET журналу ще не отриманий. Recovery01
connect timeout8s; async physical E90 recovery/daemon/Open4All запитано.
НЕ робити новий RUN/PUT до GET journal та PS; не повторювати unchanged56.
Причина невідома: pre-touch дозволив одну серію, але не довів стабільності.

Latest E90 files: research43 EXE/hash, DSP ring52/candidate56 і research
journals installed. Saved originals незмінні d0-20261003-clean34/originals.json.
Після daemon: recover-journal --host-version43 із новим tag; зберегти й
аналізувати; restore → restore-host → verify всі5 originals з новими tags.
Якщо PS1/невідоме native ownership — без PUT/KILL, потрібен clean reboot.
N95 залишається restored original20/5SHA equal/PS0, повторно не запускати.

Current out/arm host43, out/dsp ring52, proof d1-ring-v56-artifacts.json,
SIS out/sis/c55stream-d1-v43-r56_sha1.sis. Runner default43/revision56,
**не запускати з початку** після failure. Candidate54 N95 та E9054/55/56
samples не змішані. tools/summarize_ring.py публікує всі accepted journals/
timing arrays, boot/clocks/restoration/status і features; assess_ring_candidates
перераховує conditional D2. Статуси: D0 complete, D1/D2 in_progress.
Тести15/15, ARM/SIS і staticABI audits пройшли; не full D0–D2 completion.

## 2026-10-03: фінальний checkpoint — всі journals отримано, originals5 на обох

ring56-recovery02 GET до PUT: boot33773, PS0, journal25662456… завершується
ROUTING queue0/c819ba98, ДО native ring allocation/map/own create/RUN.
Усі три interrupted commands54/55/56 зупинились у initial/native-memory
diagnostics, а не у DSP packet loop. Exact exception cause невідома.
ring56 restore/hostrestore complete; verify01 мав connect timeout без
нового host START. Після user reboot boot101039 verify02 підтвердив5 originals.

Документація daemon описує autolock/Wi-Fi parking і WAKE. Candidate57
host43 + controller --keep-awake пройшов короткий batch8 frames8. Потім
користувач уточнив: **E90 перезавантажується сам**, daemon auto-starts,
взлом/Open4All не запускається автоматично. Тому довгі57 серії **не
виконувались**; WAKE-only гіпотеза недостатня. Originals5 повернуті й
звірені ring57-final-verify01. Не називати ці події тільки sleep/transport.

Host44/candidate58 додав read-only boot-info, bypass Research: тільки
HAL::Get ESystemStartupReason/ESystemException та UserHal FaultReason/
ExceptionId/ExceptionInfo. DSP open/RUN і patcher не використовуються.
ARM/SIS0; boot58-info01 FINAL/EXIT0, boot101039 незмінний. Getter rc0,
startup0, exception156, fault−1604135081(A062D757), code0/data480/extra5BC.
Це raw поля після manual reboot, не proof previous kernel panic cause.
boot58-final-restore01/host-restore01/verify01 повернули **всі5 originals**
GET/SHA-equal на E90, PS c55stream/ocprobe0; N95 original5 залишаються
verified. Ні active owner, ні QUARANTINE, ні потрібної фізичної дії наразі нема.

Поточний source/out ARM44, DSP ring52/protocol38. Artifacts58 містять
read-only host44; жодного нового DSP RUN із44 не було. Ring runner defaults
host43/revision57, але **не запускати його unchanged**: довгі E90 runs
мають чекати конкретного safe native-reader contract/fault investigation.
Після automatic reboot fault probe потрібно отримати до ручного reboot;
current cold boot не дозволяє приписати raw exception156 нашим спробам.

Результати: N95 candidate54 три серії9360 correct packets; E9054/55/56
окремі cohorts360/360/3240 packets, останній має одну повну серію, не три.
Native flags17, byte→word units, four CMM pages і release order proven
апаратно; native chunk attrs/DSP cache/publish та raw reader lifetime
не закриті повністю. D2 — conditional formula/scenarios, application T/A/W
не виміряні, emulator unchanged. D0 complete на обох, D1/D2 in_progress.
Усі accepted journals/clocks/samples/SHA та restoration reports опубліковані
в docs/evidence/2026-10-03, генератори summarize_ring/assess_ring_candidates.
Наступна незалежна робота: native IPC processor-state/queue API й fault
contract, заміна небезпечних non-atomic foreign snapshots; не новий перебір RUN.
Користувацькі APPLICATION_CANDIDATES.md, CODEX_TASK і Gemini scratch не
змінені/не включені в commit. Goal не оголошений complete чи новим blocked.
Фінальні checks:16 unit tests, verify_ring_publication21 journals/13320
packets, clocks/failure boundaries/restorations; check_state друкує
актуальні D0 complete/D1 in_progress/D2 in_progress. Canonical LF hashes
publication окремі від SHA original daemon files, щоб Git EOL conversion
не псувала checksum перевірку. Hardware не повторювати для перевірки commit.

## 2026-10-04: native E90 ring61, три повні серії даних

D0 complete обом. E90 host46/candidate61 завершив12 довгих runs,
9360 packets, boot60136 незмінний. N95 candidate54 уже мав той самий
data criterion. Native ring mode використовує ioctl2 cached own-state,
BridgeUtil1 own pages до/після, retained own-node env/state і live DSP base,
без raw RomPatcher snapshots/global queue enumeration. Причина попередніх
pre-RUN reboots невідома; це успіх нового шляху, не root-cause diagnosis.

Усі6 E90 native61 clock brackets: **self-test−20**, лише HAL CPU330MHz.
Помилку old runner complete=true acceptance виправлено; failed clock
probe тепер зупиняє серію до наступного RUN. Журнали збережені правдиво,
DSP/bus clock unconfirmed. Async Open4All E90 без reboot запит ще відкритий.
Після відповіді лише clocks/new tag і GET/parse, перед будь-яким новим RUN.

Native backing38 instructions/phone простежено до retained bridgecfg
hardware chunk(attrs1044), global CMM suballocation lifetime. Compiled
DSP order перевірено, але незалежний OMAP2420 external-write/notification
visibility contract відкритий. D1/D2 in_progress; application gain не заявлено.
D2 перерахунок окремо для N95/E90 synthetic scenarios; emulator unchanged.

19 tests, source-independent33 runs/22680 packets verification і
check_state -RequireArtifacts -RequireStreamArtifacts успішні. Обом
originals5 повернуто GET/SHA-equal, c55stream/ocprobe PS0. Детальна точка
продовження — HANDOFF_NATIVE_RING_2026-10-04.md; proof — native-ring-results.
Код і докази опубліковано commit `233740c31dbf218d0ea7201f60ddd60fa9fa181f`.
Push private main успішний; independent ls-remote підтвердив той самий SHA.
Сторонні APPLICATION_CANDIDATES і Gemini scratch files не входять до нього.

## 2026-10-04: DCR і native mailbox audit

Offline audit29 instruction sites/phone + DSM cinit table підтвердив
native BIOS5.10, user-init BCLR ST3_MPNMC/RET, STRM_issue callback і
copy/zero-copy SHM notification paths. Первинний TI BIOS5.41 gbl.h55
ідентифікує DCR I/O port200/WPE mask80. Read-only extraction selected
InstallJammer records без запуску installer; hashes і посилання опубліковані
в dsp-native-notification-audit.json. N95 BIOS_init на4 bytes пізніший
за E90, export resolved окремо; global relocation delta не припускається.

Фактичне значення WPE не виміряне, mailbox status polling не доведений
як SDRAM drain. DSP compiler publication audit збережений partial і
пов'язаний із новим firmware audit. Майбутній distinct diagnostic може
тільки читати port200 після fresh clock gate; kernel register writes не потрібні.
Нових phone I/O/DSP RUN цього offline продовження немає. Обидва phones
лишилися на verified originals; pending Open4All question ще без відповіді.
D1/D2 in_progress. Оновлено HANDOFF; native audit, publication verification
(33 runs/22680 packets) і check_state з обома artifact flags пройшли.
Audit публікується окремим commit/push, без сторонніх user files.
