# D0–D2: виконання доручення 2026-10-01

Оновлення04.10: за запитом користувача поточні роботи завершено звітом
docs/CLAUDE_PS1_HANDOFF_2026-10-04.md. Нових hardware experiments
автоматично не починати. D0 clean3 прийнятий; N95 повторні mapping/kernel
measurement завершені, D2 measured blocking verdict delivered (залишити ARM).
DSP publication/ARM caller completion та deferred E90 recovery/frequencies
не прийняті. Нижче — історія, а не поточна команда почати наступний RUN.

Поточне продовження02.10 21:45: E90 reboot/recovery виконано; finite MSG
перевірено на E90 і дозволеному користувачем N95. На обох clean created
delete/free/close, але ARM receive−33 і порожній record. Обидва повністю
GET-equal restored, host20/PS0. Три варіанти E90 більше не повторювати;
далі static audit bounded runtime ARM window/reader/queue snapshot.
Офіційних нових RUN немає, D0 0/3, D1 pending; фізичних дій не потрібно.
Докази — docs/WORKER_MESSAGES_2026-10-02.md.

Наступний крок02.10 після created-worker preflight: human reboot/daemon,
GET journal/PS0→originals3 exact restore; host26 уже GET exact.
`d0-worker-message` пропускає create-only preflight активного worker,
відразу виконує finite final-trigger diagnostic з prearmed receive у
CREATED. No-input stop/join/idle не доведені, їх не повторювати.
Успіх MSG не є D0 cycle; далі wrapper/EXITACK root cause і3 clean own RUN.
D1 має кільце16KiB TOTAL, лише після D0; D2 recalc після measuredD1.

Початковий HEAD: b75853f. До роботи змінені користувачем
docs/APPLICATION_CANDIDATES.md і доданий work/CODEX_TASK_2026-10-01.md;
ці правки зберігаються окремо. Доступний лише E90 192.168.3.21:2323.
N95 не опитується. Початковий INFO: screen800x352, startTick75535,
c55stream/ocprobe PS0; out/d0-e90-initial-connect.log.

1. D0: відтворюваний аудит native loader/cancel/destructor; окремий
   generic library2 RUN + stop/reclaim. Новий host21 утримує небезпечну
   сесію при непідтвердженому teardown; runner не робить KILL за timeout.
   Зберегти DLL/log/ocprobe.log/EXE/hash/SIS до заміни, перевірити частоти
   з регістрів без PRCM writes. Create/delete probe перед RUN; потім три
   послідовні правильні RUN з EXIT/FINAL0 і незмінним daemon startTick.
2. D1 лише після D0: розбір native reserve/map/unmap/cache ABI; один
   мінімальний mapping probe до спільного кільця16KiB. Повторні exchange
   latency/bandwidth, повна перевірка даних/ownership/wrap/teardown.
   Якщо D0 потребує людини, допускається тільки статична підготовка D1.
3. D2: вердикт для MDEC/SPU/WSOLA за max(H+D,W)+S/N < A+W;
   відрізнити старі штатні виміри, поточні E90 частоти, оцінки й невідомі.
   SMLAD135–200us є оцінкою, не фізичним виміром. Емулятор не редагувати.
4. Оригінали повернути GET/SHA256, нові докази/STATE/features/README
   перевірити, commit/push private main. Невиконані апаратні критерії
   зберегти відкритими; фізичні дії записати у HELP_NEEDED.md.

Усі зовнішні команди виконуються через run_bounded.ps1; max3 спроби
однієї проблеми, без повторного RUN після hardware failure/reboot.

## Корекція D0 після першого RUN

Run-stop21 передав8 правильних packets, але повернув execute до hostCtl6;
state3, delete−2, QUARANTINE; після цього людина підтвердила reboot.
Журнал GET до START: resume-recovery02.log CE5B1947…; original DLL/log/
clocklog повернуто GET-equal (resume-restore01). GET-only до цього RUN
також мав окремий reboot; це не другий RUN у наших transport logs.

E90 PDD803DF864 на EXITACK сам викликає delete dispatch803E6860.
Candidate22 (host/protocol лишаються21) після stop/output reclaim чекає
RMS_EXIT з hostCtl6, не issue наступний input. Це відповідає native
Running→Terminating→EXITACK→delete. Проба — нова bounded серія; при
першій відмові негайно зупинитися й не починати наступний RUN.

Третій RUN виконано як generic message diagnostic:3 snapshots, put1 і
valid DSP shared record, потім state3/message-get−2/delete−2. Host22
з EFileShareAny GET підтвердив живий журнал. Ліміт3 вичерпано; hardware
робота далі лише recovery/originals restore, D0 0/3; D1 не відкрито.


Людина о23:22 local зняла загальний ліміт3 за умови нової гіпотези кожного
RUN. Наступна: ROM STRMCOPY при тій самій generic library2. Host23 мав
select−6 до RUN; host24 parse ROM properties0 + research library2 copy
(лише registration/checksum змінено). SIS28 встановлено, host24 GET exact.
Окремі parse знову мали select−6 до RUN; combined properties0/library2
в одному packet вирішили select. Усі code/data/relocations unchanged.
Native control RUN4 дав8 exact echoes, але delete−33/pending/state3.
Повторний native RUN без зміни не планується. Наступна own diagnostic
має STRM snapshots до/після RMS_EXIT та cleanup до return, щоб розрізнити
host message delivery, DSP teardown та native EXITACK. D0 own0/3.

Human reboot02.10 підтверджено, але GET recovery ще не почався через
три connect timeout (3s/8s Python та8s .NET). Перед будь-яким PUT/START
відновити daemon transport, GET journal/PS0 і exact originals restore.
Загальний ліміт reboot знято людиною; unchanged retries заборонені.

02.10 о13:22 після нового human reboot transport відновився.
`native-recovery03`: GET journal RUN4 exact A33A433C… до будь-якого PUT/START,
PS c55stream/ocprobe0, INFO/startTick81256. `native-restore01` повернув
DLL/log/clocklog GET/SHA exact. Host24 ще встановлений.

Наступна контрольована діагностика — host25/package31, own `run-exit-diag`:
8 checked packets; stage4 перед очікуванням RMS_EXIT; stage5 після
NODE_getMsg і stage6 після обох idle у спільному512-Б output. Хост arm
output до control6; status/descriptor живуть до completion або QUARANTINE.
Stage6 доводить лише перший cleanup: діагностичний output ще reissue/reclaim/
idle, тому full завершення визначає delete/free/close/FINAL, а цей RUN
не входить у3 звичайні D0 цикли. SIS доставлено GET exact; встановлення
людиною потрібне через звичайний installer. Restore package32 містить
точний saved host20, його не перебудовано. D1 залишається після D0.
