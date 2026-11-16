# D0 і D1: E90 lifecycle та DMM

Вечірнє продовження02.10 supersedes checkpoint нижче: E90 reboot виконано,
finite MSG перевірено на E90/N95. Created worker завершився чисто на обох,
але ARM receive−33, record порожній. Обидва host20/PS0, усі5 originals
повернуті GET-equal; фізичних дій зараз не потрібно. D0 own0/3,
experimental RUN5 unchanged. Докази і наступний runtime audit —
[WORKER_MESSAGES](WORKER_MESSAGES_2026-10-02.md).

Поточний checkpoint02.10: після RUN5 journal/PS0 отримано,
original DLL/log/clocklog повернуто exact. Host26 direct deploy verified.
Created-worker MSG control зупинився на create-only preflight:
create0/7598us, delete−33/pending/state1. Trigger/MSG606/RUN не почались;
experimental RUN5 unchanged, D0 own0/3. Live GET2092Б B9B4E282…,
PS1/startTick65704 unchanged о15:21. HELP15:16 просить reboot/daemon.
DSP/log зараз research26; clocklog original exact, host26/hash research.
D1 hardware pending, D2 provisional.

Статичне уточнення ARM reader: C55 board803F0208 передає common base+8
у context constructor803E011C. Getter803EEFCC додає164, тобто reader
board+172, а його byte64 — board+236. Init803F0308 встановлює r8=1,
803F03C0 записує цей byte. IVA board має іншу layout і не визначає C55
flag. Це доказ початкового store, не live runtime observation.
RMS create result803E6E34–803E6E40 зберігає env у node+44 і передає
той самий value queue setter803F3A98→queue+16, без multiply/word swap.
Native wrapper24E6F0 і MSG functions мають окремі reproducible hashes у
[native audit](evidence/2026-10-01/e90-d0-d1-native-audit.json).

Новий diagnostic [artifact33](evidence/2026-10-01/d0-worker-message-v33-artifacts.json)
відокремлює outbound MSG від execute return: host prearms receive/output
у CREATED, один final input запускає finite worker, той робить
NODE_putMsg606/A1B2C3D4/env і snapshot7/protocol26, reclaim/idle/return;
delete перевіряє terminated worker перед звільненням. Wrapper/EXITACK і
офіційний RUN відсутні, тому успіх не закриє D0. Перший запуск
помилково повторно використав create-only preflight активного worker,
чиє stop без input не було доведене попередніми packet tests.
Скрипт тепер пропускає лише цей preflight; cleanup без input залишається
невирішеним. Після human reboot GET/PS0/restore потрібен один finite
trigger diagnostic, не незмінний повтор no-input delete.
Нижчі розділи зберігають попередні checkpoints.

Після продовження 2026-10-01 **D0 0/3**. Host21 підтверджено GET;
два різні DSP-кандидати виконали RUN і по8 правильних packets, але
delete дав−2 та−33. Обидва host процеси утримували ownership через
QUARANTINE; KILL не було. Після підтверджених людиною reboot журнали
отримано до START/PUT, original DLL/log/clocklog повернуто exact.
[Докази продовження](evidence/2026-10-01/e90-d0-resume-checkpoint.json).
D1 лишається статичним; це не доказ неможливості zero-copy.
N95 у цій сесії не опитувався.

Host22 із EFileShareAny встановлено й підтверджено GET35120 БAFF498B8….
Третій RUN передав3 MSG snapshots: get(0)=0, put(0)=1, shared record
правильний, але message-get−2/state3/delete−2. Живий журнал D29CDA12…
GET отримано успішно. Після human reboot DLL/log/clocklog повернуто
exact. Людина зняла ліміт3 за умови нової гіпотези кожного RUN.
Тест ROM reference на host23 зупинився до RUN: DCD select−6.
Host24 встановлено й GET підтверджено:12356F00….
Separate properties/library2 parse мав select−6 до RUN. Combined registry
packet пройшов select; RUN4 із native STRMCOPY code/data/relocations
передав8 exact echoes по512 Б, але delete−33/pending/state3. Live GET
журналу A33A433C… успішний. Human reboot02.10 підтверджено; після нього
Python connect3s/8s та.NET8s timeout до INFO. GET/PS0/restore ще pending.

## Аудит завершення

Відтворення без апарата: `python tools/rev/audit_e90_task.py`.
Адреси, довжини перевірених ділянок і hashes —
[native audit](evidence/2026-10-01/e90-d0-d1-native-audit.json).
Джерело: збережені E90 ehwaomap.pdd, ehwa.ldd, bridgeapi.dll.
Сирі ROM і дизасемблювання залишаються локальними.

| Ділянка E90 | Встановлений контракт | Наслідок для host |
|---|---|---|
| PDD803E5AB4, RUN | Unload create лише за phase_split1/dynamic1 | Generic library2 утримує code/data між фазами |
| PDD803E6DE8, RMS callback | Негативний DSP статус відображається в−2 | −2 не підтверджує, що задача завершена |
| PDD803E70B8, delete completion | Помилка пропускає success/env clear, але переходить у internal state4 | Сам стан4 не доводить безпечний unload |
| LDD803F87FC, destructor | State4 дозволяє PDD free; PDD803E6758 unload libraries | Close після failed delete може звільнити живий код |
| LDD803F8AF4, cancel adapter | Task15/17 передає index як значення; adapter повертає0 | Потрібен окремий завершений transfer status |
| PDD803E69B4, running delete | State9, queue RMS_EXIT80000000 із nodeEnv | Submit0 не доводить DSP receipt |
| PDD803DF7EC–803DF864, EXITACK | Очікує RMS_EOK8000, перевіряє node, сам dispatch delete | Ранній return може змагатися з hostCtl6; причина конкретної відмови не доведена |

Host21/22 не робить delete/free/close за pending create/RUN/transfer після
спроби cancel; за failed delete/free або pending message утримує
власника ресурсів і пише QUARANTINE. Supervisor має deadline30s і
пробує GET журналу; телефонний процес не отримує KILL. Host21 тримав
exclusive RFile: живий GET дав−14. Host22 використовує EFileShareAny;
GET живої QUARANTINE підтверджено третім RUN. Це утримання до ручного
reboot, **не доведений безпечний cancel**. Синхронний control усередині
ядра може заблокувати телефон; локальний timeout цього не виправляє.

DSP run-stop21: після stop/reclaim ранній return8000. Candidate22
після тих самих packets чекає RMS_EXIT перед return. Новий input після
stop не issue. Ручного дублювання ACK немає. Context явно обнулено;
execute перевіряє context і buffers перед доступом. State3 не доводить
успішний ACK: native fault path також ставить цей стан.

| Кандидат / host | Перед delete | Packets | Delete / status | FINAL / EXIT0 |
|---|---:|---:|---|---|
| run-stop21 /21 | state3 | 8/8 correct | −2/−2 | немає |
| run-stop22 /21 | state2 | 8/8 correct | −33/pending | немає |
| generic message-diag /22 | state3 | 3/3 snapshots | −2/−2 | немає |
| ROM STRMCOPY combined /24 | state2 | 8/8 exact echoes | −33/pending, після state3 | немає |

Packet wall:16 діагностичних observations, median396us,366–488us.
Це не прийнятий D1 latency/bandwidth і не application speedup.
Перше reboot до цих запусків сталося між GET verify і connect clocks;
до нього нового RUN не було. У transport logs чотири RUN: два
own packet tests, MSG diagnostic і ROM control. Окремі select−6 preflight
не є RUN. ROM packet wall median488us, range457–579us — окрема
діагностична вибірка, не прийнятий D1 latency або speedup.

У третьому snapshot fromDSP empty1/count1, raw record
0000/0600/000F/0001/0000/77E0/0000/77E0; ror16 дає
cmd600/arg1F0001/arg2/source77E0. Це рух DSP→shared window, а не доказ
ARM IRQ/DFC, actual reader endian flag або EXITACK delivery. State3
після execute return також не встановлює конкретної причини fault.

## Збірка і наступна діагностика

Артефакти: [run-stop21](evidence/2026-10-01/d0-run-stop-v21-artifacts.json),
[run-stop22](evidence/2026-10-01/d0-run-stop-v22-artifacts.json),
[host22](evidence/2026-10-01/d0-livejournal-v22-artifacts.json),
[generic message diagnostic](evidence/2026-10-01/d0-message-diag-v24-artifacts.json).
DOFF/import/ASM checks є статичними; hardware success не встановлюють.
Останній variant передає3 STRM snapshots: до NODE_getMsg(0), після get,
після NODE_putMsg(0), включно з message windows/record source.
Цей третій RUN виконано і він не зараховується до D0.

Подальша гіпотеза: ROM STRMCOPY із тією самою generic library2
розрізнить custom execute/return та host/native lifecycle. ROM DLL
має лише properties0; додаткова research-копія змінює registration
:0→:2 і checksum, усі instruction/data/relocation bytes незмінні.
[Derivation proof](evidence/2026-10-01/e90-d0-native-library2-derivation.json),
[host24 proof](evidence/2026-10-01/d0-native-copy-host-v24-artifacts.json).
Host23 select−6 був preflight, не четвертий RUN; журнали після нього
повернуто exact без reboot. Host24 parse ROM properties, потім E library2.
Separate parse не вирішив select; combined properties0/library2 вирішив:
[combined proof](evidence/2026-10-01/e90-d0-native-library2-combined-derivation.json),
[same host24, control artifact](evidence/2026-10-01/d0-native-copy-host-v24-combined-artifacts.json).
Усі non-registration packets, включно з DSP code/data/relocations,
побайтово незмінні; збільшено metadata packet і виправлено table offsets/
checksums. RUN4 відкинув власний execute як єдине пояснення lifecycle
failure; конкретну причину host/setup/native path ще не встановлено.
Control не зараховується як три clean own-DSP cycles. Повтор без нової
зміни не планується. Наступний diagnostic повинен відокремити RMS_EXIT
receipt, idle/reclaim і native return/EXITACK через STRM snapshots.

Історична команда вже виконаного probe; повторювати її не можна:

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'python tools/e90_task_session.py --session work/evidence/e90/d0-20261001 --action d0-message-diagnostic --host-version 22 --artifact-proof docs/evidence/2026-10-01/d0-message-diag-v24-artifacts.json --tag message-diag01' -TimeoutSec 120 -Log out/d0-message-diag01.log
```

Fresh clocks, inspect і clean create/delete підтверджені в тому самому
socket session. Після відмови знято живий журнал, RUN зупинено: ліміт3
був вичерпаний до пізнішого дозволу людини. Стару гіпотезу не повторювати.
Original DLL/log/clocklog можна PUT лише після підтвердженого
завершення або reboot. Після встановлення причини повний D0 потребує:

1. Трьох послідовних окремих create/RUN0 із8 ordered packets і
   перевіркою240 payload words, stop, delete/free/native0, FINAL0,
   EXIT0, responsive INFO та незмінним daemon startTick.
2. Exact restore original DLL/log/clocklog GET/SHA256.
3. Після research — install restore SIS з exact original host20 EXE,
   GET перевірка EXE і sys/hash. Номер restore package має перевищувати
   останній встановлений package28; restore29 уже підготовлено. Payload
   не перезбирати.

Інструмент має фіксований E90 IP. Generic run_stream.py лишається для
історичних v7–v20; його timeout також не надсилає KILL. Окремі variants
та immutable local archives збережено; normal PC DSP перебудовується
після діагностичного variant (bounded build EXIT0).

## D1: статична підготовка

Оновлення 2026-10-03: [відтворюваний native page-list/cache audit](DMM_ABI_2026-10-03.md)
зіставив N95/E90, підтвердив пари `{linearPage, physicalPage}`, точну map
signature і cache helper clean→invalidate. Pinning/lifetime, DSP units,
когерентність і всі D1 hardware критерії лишаються неперевіреними.

| Дія bridgeapi.dll | Ordinal | Control | E90 entry |
|---|---:|---|---|
| Reserve DSP range | 27 | 0400000F | 803FA420 |
| Map ARM buffer | 31 | 04000012 | 803FA45C |
| Unmap | 34 | 04000013 | 803FA512 |
| Unreserve | 28 | 04000010 | 803FA532 |

Map payload24 Б: ARM virtual address, byte count, reserved DSP address,
flags, physical page-table pointer, page count. Wrapper працює з4096-Б
сторінками. Native DSP-address units, MMU flags, pinning/cache ABI ще
не доведені. Reserve/map/16KiB transfer у цій сесії не викликалися.

[TI reference audit](evidence/2026-10-01/e90-d0-dmm-ti-reference.json)
фіксує archived primary samples, а не Nokia runtime: map flags
virtual0/physical1, big-endian2, mixed4, element8/16/32/64 bits —
8/10/20/40 hex. Sample для DSPTYPE_55 ділить returned byte address
і byte length на2, flush ARM input перед роботою та invalidate output
після completion. Одиниці й flag bits ще треба підтвердити на E90;
переносити sample як доведений firmware ABI не можна. Його notify
також залежить від NODE message path, який зараз не прийнятий у D0.

Probe після D0: підтвердити allocation/alignment/cache ABI, reserve/map
одну область, перевірити sentinels на16-bit/32-bit/4KiB межах у двох
напрямках; потім unmap/unreserve/free без pending ownership.
Ring16KiB — загальна область. Потрібні producer/consumer indices,
slot ownership, sequence/length, ordering/cache, wraparound і notify.
Wire format: явні16-bit поля; C55 char/int/short16, long32, pointer23 bits.

Вимір: три серії кількох розмірів, byte-equal всі повтори, ARM FastCounter
Hz і p50/p95/p99/max, окремо submit CPU/wall/bytes/s. CLK_countspms164
не використовувати. Негативний DMM результат потребує точного native
error, доведеного ABI й чистого teardown; блокування D0 ним не є.

## Оригінали і фізична залежність

[Початковий checkpoint](evidence/2026-10-01/e90-d0-session-checkpoint.json)
о19:02 UTC довів усі5 original файлів, host20/hash, PS0. Продовження
вище підтвердило host21 та свіжі clock probes: m86/div3,
ARM330.24MHz/bus110.08MHz/DSP220.16MHz, без PRCM writes.

Після другого reboot о19:58 UTC PS0/startTick60875; DLL/log/clocklog
exact restored. Original host20/hash ще не повернуто; host22 GET-proven
після нового daemon startTick91233. Новий SIS20416 Б0F8577C6… GET-equal;
runtime22 не є restore package revision22, який містить host20.

Після третього research reboot startTick61475, original3 exact restored.
Host23 GET-proven36492 Б31836A0F…; native-copy preflight FINAL/EXIT−6
до allocate/create/RUN. Підготовлений package28 host24 доставлено;
остаточний restore host20 має бути package29 або вище поточного SIS.

Фізичний крок — [HELP_NEEDED](../work/HELP_NEEDED.md).
N95 idle-first journal, повернення ocprobe.log і research cleanup
відкладені іншому виконавцю. Проміжне D2 —
[PS1_CANDIDATES](PS1_CANDIDATES_2026-10-01.md).

## Продовження 2026-10-02: recovery та RMS_EXIT diagnostic

Після human reboot о13:21 `native-recovery03` отримав незмінний RUN4
journal A33A433C…; c55stream/ocprobe PS0, INFO/startTick81256.
`native-restore01` повернув три початкові E:-файли із GET/SHA equality.
Host24/hash лишаються дослідними до кінцевого original restore.

Новий [artifact31](evidence/2026-10-01/d0-run-exit-diag-v31-artifacts.json):
host25, DSP5144 Б29069D52…,18 resolved imports, DOFF/ASM verified;
SIS31 доставлено GET exact8D0E3BE8…. `exit-stages` робить8 normal
protocol21 packets, потім діагностичний protocol25. Stage4 — перед
очікуванням RMS_EXIT. Host arm output до control6; DSP фіксує stage5
одразу після NODE_getMsg, stage6 після STRM_idle(input/output), обидві
структури у512Б з offsets0/96 C55 words. Snapshot містить message,
raw shared headers/records обох напрямків, pending ownership, idle/status.
Raw fields можуть змінюватися конкурентно, atomic snapshot не заявляється.

Після stage6 extra output reissue/reclaim/idle ще належить виконати.
Stage6 самостійно не доводить його завершення або wrapper EXITACK.
Діагностичний RUN не зараховується до D0 навіть за clean delete.
Хост зберігає persistent descriptor/status і QUARANTINE на pending output
чи failed delete, без KILL/free/close. До нового RUN потрібне встановлення
SIS31 людиною. Original host20 restore SIS32 готовий, SHA6E6C81E0….

Людина через HELP13:38 дозволила прямий deploy нашого EXE/hash без SIS.
`host25-deploy01` зберіг поточні host24/hash, PUT→GET підтвердив host25
CB74DE96… та SHA1-loader hash (його SHA-256 EDDE22CA…).
`exit-diag01` виконав RUN5 після clean inspect/create/delete preflight і
read-only clock guard330.24/110.08/220.16MHz. Усі8 packets512Б правильні,
240 payload words кожен, median396us/range366–457us, total3169us.
Це failed-lifecycle diagnostic, не D1 exchange benchmark.

Stage4 input/output pending0, message0. Stage5 **get1/waits1**,
cmd80000000/arg1=env77E0/arg2=0; stage6 має **idle input/output0**,
pending0 і status00008000. Отже в цьому RUN доставка RMS_EXIT та перше
очищення потоків фізично доведені. Після diagnostic reissue останній
reclaim/idle й actual execute return ще не спостережені. Delete submit0,
5000ms deadline−33/status pending; state2→3, QUARANTINE без free/close.
Живий GET journal SHA778039EB…; local30s runner не робив phone KILL.
Native EXITACK construction/delivery/consumer і delete callback лишаються
невідомими; state3 не доводить, на якій з цих меж виникла відмова.
Human reboot13:43 запитано у HELP; GET/PS0/restore після нього ще потрібні.
