# Дії, для яких потрібна людина

**Передача04.10:** поточні роботи завершено звітом для Claude за запитом
користувача, `docs/CLAUDE_PS1_HANDOFF_2026-10-04.md`. Нових фізичних дій
не просимо й нових experiments автоматично не починаємо. E90 recovery
залишається відкритим на наступне доручення; старі запити нижче історичні.

**Актуально 2026-10-04:** користувач доручив доробляти на N95,
E90 відкладено до завтра. Зараз нової фізичної дії не просимо.
N95 original5 відновлені після native61:3 серії/9360 packets/6 stock brackets.
E90 reboot підтверджено користувачем; daemon journal отримано, причина
невідома. На E90 залишився host46/original DSP; restore EXE/hash/journals
ще потрібний після повернення до E90. Ringclock.exe не встановлено.
Старий Open4All запит нижче не є поточною передумовою роботи на N95.
Поточний стан — HANDOFF_NATIVE_RING_2026-10-04.md.

## 2026-10-01: встановити дослідницький host21 на E90

На **Nokia E90**, без дій на N95, відкрити через файловий менеджер
`E:\c55stream-d0-v21.sis` і підтвердити оновлення **C55Stream Research
1.00(21)**. Повідомити, коли установка завершиться й Wi-Fi-демон знову
буде доступний за 192.168.3.21:2323.

Це потрібно для перевірки D0: старий host20 закриває native processor
навіть після помилки delete; host21 утримує ресурси до ручного відновлення,
якщо завершення не доведене. Результат timeout не буде названий успіхом.

Вже зроблено: backup DLL/log/ocprobe.log/installed EXE/hash; ARM/DSP/SIS
збірки з EXIT_CODE0; доставка SIS і GET-equal. SHA256 пакета:
`A3592773BEB73E75ECBDCE3AD729C97C49F5C5F0A39EA81C1C7EDAEEB0BC1A6D`.
Перша доставка зупинилась до PUT через розбіжність тексту daemon ERR;
друга після точного розбору STAT успішна. DSP DLL ще не замінений,
новий RUN не викликався. Прямий запис EXE на E90 не є перевіреним шляхом;
використовується штатне встановлення SIS.

У цій сесії регістри показують штатний профіль m86, ARM330.24MHz,
bus110.08MHz, DSP220.16MHz. PRCM не змінювався. Для D0 це придатні
фактичні умови; повернення розгону не є передумовою цього тесту.

Якщо host21 надалі запише `QUARANTINE`, потрібне ручне перезавантаження
E90, відновлення Wi-Fi-демона, потім GET журналу до нового START/PUT.
Автоматичний KILL або unload живої DSP-сесії заборонені.

О19:02 UTC повторний GET підтвердив усі5 оригіналів, host20,
c55stream/ocprobe PS0, startTick75535. О19:10:31 UTC спроба
підключитися для спостережуваного SIS installer через live_device.py
завершилася `TimeoutError: timed out` у socket.create_connection із
межею3s, до INFO/OPEN/KEY. Жодної нової дії на телефоні не відбулося.
Потрібно також повернути доступність E90 Wi-Fi-демона. Можливість
OPEN/KEY/SHOT відома з попередніх установок, але поточного з'єднання немає.

Друга спроба о19:12:52 UTC (e90_task_session.py verify02) дала той самий
connect timeout3s до INFO. Двох повторів достатньо, нових RUN не було.

### Відповідь людини, 2026-10-01 22:25 (передано оркестратором PS1Emulator)

SIS `c55stream-d0-v21.sis` на E90 встановлено, людина підтвердила. Після
цього о 22:30 E90 ще не відповідав ні на ping 192.168.3.21, ні на порт 2323;
перебір 192.168.3.2-254 знайшов демон лише на N95 (.22). Людину попрошено
запустити демон на E90 і перевірити Wi-Fi. N95 як і раніше не чіпати.

### Наступний крок після відповіді людини

Третій connect verify03 після цього повідомлення також дав
`TimeoutError: timed out` у connect3s до INFO. Ліміт трьох спроб
вичерпано. **Потрібно лише запустити Wi-Fi-демон на E90** та повернути
доступність 192.168.3.21:2323. Повторно встановлювати SIS21 не потрібно.
Після повернення зв'язку GET перевірить exact host21; без цього RUN
не стартує. Попередній GET-equal originals був до повідомленої установки.
22:27: людина запустила демон на E90; порт 192.168.3.21:2323 приймає TCP-з'єднання (перевірено оркестратором). Можна продовжувати D0.

## 2026-10-01 19:35 UTC: повернути доступ після першого D0 RUN

Host21 підтверджено GET/SHA256 8FD9FAE1…, original DLL/log/clock log
до запису exact. Свіжі clock probes дали ARM330.24/bus110.08/DSP220.16MHz,
clock log повернуто exact. Inspect і create/delete дали FINAL/EXIT0.
Далі deployed run-stop DLL7B07E8D0… GET-equal, стартував **один**
run-transfer reps=0 bytes=512 frames=8. Supervisor бачив c55stream PS1,
потім PS request отримав TimeoutError8s. GET на тому самому socket не
вдався: OSError cannot read from timed out object. Нове read-only
з'єднання для GET journal теж отримало connect TimeoutError3s.
Другого/третього RUN і KILL не було. Packet/delete/FINAL невідомі;
невідомо, чи QUARANTINE або інша відмова. DSP DLL наразі дослідницький;
його не можна переписувати до підтвердженого завершення або reboot.

**Потрібно:** якщо E90 відповідає на клавіші, відкрити/запустити Wi-Fi-демон
і повернути 192.168.3.21:2323 без перезавантаження, щоб зняти журнал
із живої сесії. Якщо апарат завис, перезавантажити лише E90 й запустити
демон. Повідомити, чи було reboot. Не запускати C55Stream або інший
DSP-застосунок: спершу GET E:\c55stream.log, потім відновлення DLL/log.
N95 не чіпати. Докази: work/evidence/e90/d0-20261001/resume-sequence01*,
out/d0-resume-sequence01.log, out/d0-resume-run1-recovery01.log.
22:33: людина повідомила, що E90 перезавантажувався (причина не відома оркестратору; можливо, під час RUN host21); після перезавантаження людина знову запустила Wi-Fi-демон. Це не KILL з боку ПК; журнал на E90 забрати GET до нового START.
22:36: людина повідомила про ДРУГЕ перезавантаження E90. За журналами воно сталося під час
d0-sequence, крок run1 `run-transfer reps=0 bytes=512 frames=8` (out/d0-resume-sequence01.log,
19:34-19:35 UTC: читання відповіді демона обірвалося timeout, recovery о 19:36 уже не з'єднався).
Перше перезавантаження - між verify01 (19:31:20, complete=True) і clocks01 (19:31:40, connect timeout).
Отже RUN host21 на E90 двічі закінчився перезавантаженням апарата; це апаратний збій, а не мережа.
Ліміт - три однакові спроби: перед третьою потрібна зміна підходу (діагностика без RUN, журнал з
E:\c55stream.log після перезавантаження). Демон людина запускає вручну після кожного перезавантаження.
22:38: відповідь на запит вище. Так, E90 перезавантажувався (людина, друге перезавантаження після RUN 19:35 UTC); живої сесії вже немає. Людина знову запустила демон; оркестратор о 22:38 перевірив, що 192.168.3.21:2323 приймає TCP. C55Stream ніхто не запускав.

### Отриманий журнал і уточнення кількості RUN

О19:40:31 UTC GET отримав журнал CE5B1947…:8 packets correct,
state before delete3, delete/status−2, QUARANTINE без free/close.
INFO startTick61377, PS0 після підтвердженого reboot. Оригінальні
DLL/log/clocklog повернуто GET-equal (resume-restore01).
У наших transport logs до цього є **один** RUN, а не два. Перше
перезавантаження було між read-only GET verify01 і невдалим connect
clocks01; до того нового C55Stream START/RUN не було. Його причину
не можна приписати RUN за нашими доказами.

### Другий, змінений DSP-кандидат: потрібне нове відновлення

Candidate22 (host21/protocol21) після stop чекає штатний RMS_EXIT із
hostCtl6. Перший RUN resume-sequence02 залишив процес активним до
deadline30s. Демон відповідав на PS, KILL не було. GET журналу отримав
**ERR open -14**: host21 тримає RFile без дозволу іншому reader, тому
журнал живої QUARANTINE-сесії недоступний. Точне місце другої відмови
ще невідоме. DSP DLL2B97836D… наразі дослідницький і не відновлений.

**Потрібно знову перезавантажити лише E90 та запустити Wi-Fi-демон**,
не запускати C55Stream/інший DSP. Спершу GET журналу до будь-якого START
чи PUT, потім exact restore. Одночасно готується новий host із readable
journal, щоб наступний timeout можна було розібрати без цього reboot.
22:57: людина перезавантажила лише E90 і запустила Wi-Fi-демон; C55Stream не запускався. Оркестратор перевірив порт 192.168.3.21:2323: OK. Можна GET журналу й restore.

## 2026-10-01 20:04 UTC: встановити host22 з readable journal

Після підтвердженого reboot GET resume-recovery03 о19:58:28 UTC отримав
журнал F35CDF7F…:8 правильних packets, перед delete state2,
`delete submitted=0 status=-2147483647`, потім `delete=-33` і
QUARANTINE. Host21 лишався активним, KILL не було. Це другий RUN;
третього RUN ще немає. PS0/startTick60875 після reboot підтверджено.
Original DLL/log/clocklog повернуто exact PUT/GET (resume-restore02).

**Потрібно встановити лише на E90 файл E:\c55stream-livejournal-v22.sis**
через звичайний установник; його вже доставлено GET-equal.
SIS SHA2560F8577C66D84C0C2C43FC600AFAB0C77736FC4962084DE95DBFEC0C4084E21BA.
Це runtime host22, package revision23; DSP protocol лишається21.
Єдина зміна host: EFileShareAny для живого журналу та version marker.
Встановлення потрібне, щоб наступна діагностика не вимагала reboot
тільки заради GET E:\c55stream.log. Не запускати C55Stream самостійно;
демон лишити запущеним. Після підтвердження GET перевірить exact EXE.
N95 не чіпати. Restore SIS з exact початковим host20 також збережено
локально; остаточний restore EXE потребуватиме штатного SIS install.
23:10: людина встановила E:\c55stream-livejournal-v22.sis на E90 (host22). Порт 192.168.3.21:2323 за перевіркою оркестратора: FAIL. C55Stream людина не запускала.

### 2026-10-01 20:11 UTC: після повідомленого install22 потрібен лише демон

Людина повідомила про install22. GET-перевірка host22-verify01 отримала
connect TimeoutError3s до INFO. Третього RUN/PUT/START після install немає.
Потрібно запустити Wi-Fi-демон лише на E90 і повернути .21:2323.
SIS22 повторно не встановлювати, C55Stream не запускати, N95 не чіпати.
Після зв'язку: GET exact host22, stock clock/inspect/create, один generic
run-message-diag із трьома read-only DSP MSG snapshots (вже зібраний),
без KILL; це діагностика, а не прийнятий D0 цикл.

23:11: людина повернула E90 у мережу; оркестратор перевірив 192.168.3.21:2323: OK. Можна GET host22.

## 2026-10-01 20:16 UTC: третій RUN завершено, тільки відновлення E90

GET host22-verify02 підтвердив EXE35120 Б AFF498B8… і originals DLL/log/
clocklog; PS0, startTick91233. message-diag01 мав stock clock guards,
inspect/create FINAL/EXIT0, generic diagnostic DSP3836 Б B1CB8409…
PUT/GET-equal. Три STRM snapshots правильні: NODE_getMsg(0)=0,
NODE_putMsg(0)=1, fromDSP count1, raw record0000/0600/000F/0001/
0000/77E0/0000/77E0; ror16 дає cmd600/arg1F0001/arg2/source77E0.
Після return: message-get submitted−2, state3, delete/status−2,
QUARANTINE. Живий GET журналу D29CDA12… успішний завдяки host22 sharing.
Supervisor deadline30s, KILL немає. Ліміт ТРЬОХ експериментальних RUN
вичерпано, нового RUN не буде. D0 0/3, D1 не відкрито.

**Потрібно перезавантажити лише E90 й запустити Wi-Fi-демон.**
C55Stream та інші DSP програми не запускати. Journal уже збережено;
після PS0 буде exact restore original DLL/log/clocklog. Потім доставлю
restore SIS package revision25 з exact original host20 EXE; установка
через штатний installer потрібна для остаточного повернення EXE/hash.
Наразі DSP diagnostic DLL ще на телефоні; його не overwrite до reboot.
N95 не чіпати. Це recovery після failed ownership, а не новий цикл RUN.

### Рішення людини, 2026-10-01 23:22 (передано оркестратором PS1Emulator)

Ліміт трьох експериментальних RUN на E90 ЗНЯТО. Людина пише: щоб досягти
попереднього результату з меншою затримкою DSP, знадобилося близько 20
перезавантажень, тож перезавантаження E90 - прийнятна ціна досліду, і
людина робить їх за запитом. Прохання: планувати кожен RUN обдуманіше,
щоб перезавантажень було менше. Перед RUN формулювати гіпотезу й те, що
саме цей запуск має розрізнити; збирати максимум діагностики за один
запуск (живий журнал host22, знімки MSG до й після); не повторювати
запуск без зміни, яка перевіряє нову гіпотезу. Продовжуй D0 -> D1 -> D2.
Решта правил без змін: N95 не чіпати, без KILL/unload живої DSP-сесії,
запити людині - сюди.
23:27: людина перезавантажила E90 і запустила демон. Порт 192.168.3.21:2323 за перевіркою оркестратора: OK. C55Stream не запускався.

## 2026-10-01 20:33 UTC: контрольний ROM STRMCOPY, потрібен install host23

Після human reboot23:27 GET final-recovery01 отримав journal до PUT,
PS0/startTick61475; original DLL/log/clocklog повернуто exact PUT/GET
(final-restore01). Далі read-only GET Z:\system\apps\strmcopy\strmcopydyn.dll55l
отримав E90 ROM node4396 Б, DLLdump verification passed. Гіпотеза
наступного RUN: відмова виникає в нашому execute/return або його cleanup,
а не в усьому native host lifecycle. ROM STRMCOPY виконує всі DSP фази,
host перевіряє8 echo packets по256 words; нативні RUN/delete ті самі.
Clean reference звузить причину до custom node/generic phases; failed
reference звузить до host/setup/native firmware path. Це diagnostic
control, сам по собі D0 для нашого DSP не закриває. No own DSP PUT для
цього control. Live journal sharing та state after delete у host23.

**Потрібно встановити лише E90 E:\c55stream-native-copy-v23.sis**
(уже доставлено й GET-equal; package26, runtime23).
SIS21064 Б SHA256D383BF30F371DD8A4CBCB5C7820B25C141CBD60FC7D40AF0EE59C8026D2AC809.
Демон лишити запущеним, C55Stream не запускати; після install GET
перевірить exact EXE. Якщо демон зникне після установки, запустити його.
N95 не чіпати. Ліміт3 знято рішенням людини вище; кожний подальший RUN
має свою нову гіпотезу. Original host20 поки не повертаємо, бо дослідження
продовжується; остаточний restore package має бути вище26.
23:34: людина встановила E:\c55stream-native-copy-v23.sis на E90. Порт 192.168.3.21:2323 за перевіркою оркестратора: OK. C55Stream не запускався.

## 2026-10-01 20:42 UTC: host24 виправляє preflight, RUN ще не викликався

Host23 GET exact36492 Б31836A0F…; native-reference01 мав parseROM0,
але select node−6, FINAL/EXIT−6 до allocate/create/RUN. Отже лишається
ТРИ experimental RUN, четвертого ще немає; reboot не потрібен.
Причина preflight: ROM .dcd_register містить лише properties:0, немає
library3/2. Не перевірив це до host23 SIS; це була зайва установка.
Original DLL/log/clocklog повернуто exact (native-preflight-restore01).

Для control зроблено research-copy E90 ROM DLL4396 Б308090D3…,
змінено лише registration:0→:2 і packet checksum (offsets3807/3883).
Усі DSP code/data/relocations exact unchanged; DLLdump passed.
ROM/firmware не записуються. Host24 parse original ROM properties0,
потім E research library2. Гіпотеза control лишається custom execute
versus native host/setup; library2 тепер така сама як у custom probes.
До RUN inspect/fresh clock/GET source+derived SHA gates.

**Потрібно встановити лише на E90 E:\c55stream-native-copy-v24.sis**
(вже GET-equal, package28, runtime24).
SHA256CEB641F9956E3CDADECAF865634D21022140C36DD28FCE524603DC5B14DD6B79.
Демон лишити працювати, C55Stream не запускати. Після install GET
підтвердить exact EXE; N95 не чіпати. Перезавантаження тут не запитується.

### 2026-10-01 20:53 UTC: host24 GET поки недоступний

Read-only host24-verify01 отримав connect TimeoutError3s до INFO.
Install24 ще не GET-підтверджений; четвертого RUN немає. Потрібно
завершити установку E:\c55stream-native-copy-v24.sis, якщо ще не
встановлено, і запустити Wi-Fi-демон на E90 .21:2323. C55Stream не
запускати, N95 не чіпати. Попередній запис про PS0/original3 exact
є останнім підтвердженим checkpoint до цього connect timeout.
23:56: повідомлення людини (передано оркестратором): «В момент встановлення v24 сталося перезавантаження. Після цього я ще раз перевстановив. Зараз демон доступний.» Тобто E90 перезавантажився ПІД ЧАС установки v24, потім v24 встановлено повторно. Порт 192.168.3.21:2323 за перевіркою оркестратора: OK. C55Stream не запускався.

## 2026-10-01 20:59 UTC: TCP доступний оркестратору, але GET ще не почався

host24-verify02 знову отримав connect TimeoutError3s до INFO; RUN не
починався, install24 підтверджений лише людиною. У daemon source
acceptLoop/serveOne обслуговує одного клієнта до закриття, readLine
блокувальний без idle timeout; це можливе пояснення, не доведена причина.
Потрібно закрити всі E90 TCP-з'єднання оркестратора/інших клієнтів і
тимчасово припинити паралельні TCP-проби .21:2323. Демон лишити працювати.
Якщо він завис після закриття клієнтів, перезапустити лише демон його
звичайним інтерфейсом; C55Stream не запускати. Reboot зараз не запитую.
Наступна одна сесія перевірить GET exact host24/PS0/fresh clocks і лише
потім native library2 control за вже описаною новою гіпотезою. N95 не чіпати.

## 2026-10-01 21:08 UTC: host24 exact, native reference2 до RUN select−6

TCP відновився без нового запиту reboot. Native-reference02 GET exact
host24 SHA25612356F00E0163EF0B0823A0E017D38A2796DCE83F2AB1FA85554DCFFF32A09D8,
PS0, startTick35185, fresh stock330.24/110.08/220.16MHz. Parse ROM0,
parse library2=0, але select−6/FINAL−6/EXIT−6 до allocate/create/RUN.
Усе ще ТРИ experimental RUN, четвертого немає; reboot не потрібен.
Native-preflight-restore02 повернув original DLL/log/clocklog exact.
Запит звільнення TCP вище вже не актуальний; C55Stream не запускати.

Наступна гіпотеза: окремі parse не дають select повного набору
properties0/library2; combined registry packet у E research copy містить
обидва записи одночасно, як наш робочий generic loader. Це перевірка
preflight, причину −6 поки не встановлено. DLL4476 БC7572358…;
DLLdump PASSED, усі non-registration section packets і relocations exact,
змінені лише registration size/packet та table offsets/checksums.
Host24/SIS лишаються ті самі. Якщо select пройде, один native RUN із
8 повністю звіреними echo packets перевірить попередню lifecycle гіпотезу;
clean control не зараховується як own-node D0. Ніякого незмінного RUN retry.

## 2026-10-01 21:09 UTC: native control RUN4, потрібен reboot E90

Combined properties0/library2 вирішив preflight: select/create/RUN=0.
Native STRMCOPY code/data/relocations unchanged виконав8 exact echo
packets по512 Б (усі256 words), wall_us579/488/488/488/457/457/488/488.
Після control6 delete=-33, status pending, state2→3, QUARANTINE без
free/close/FINAL;30s local deadline. Live GET journal succeeded,
SHA256A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1.
Це ЧЕТВЕРТИЙ experimental RUN; D0 own cycles0/3. ROM control звузив
причину до host/setup/native lifecycle, власний execute не є єдиним
поясненням. KILL/unload0, PRCM writes0. Далі без нового RUN до recovery.

**Потрібно перезавантажити лише E90 і запустити Wi-Fi-демон .21:2323.**
C55Stream не запускати. GET journal/PS0 після reboot мають передувати
PUT/restore. Original DLL/log/clocklog повернуться exact GET/SHA;
research EXE24/hash лишаються до завершення дослідження. N95 не чіпати.
Поки людина перезавантажує, аудитується native host stream flush/cancel,
MSG delivery/EXITACK та native application lifecycle із saved ROM.

## 2026-10-02 04:07 (оркестратор): E90 перезавантажено, демон доступний

Людина перезавантажила E90 після native control RUN4 і запустила демон (з другої спроби). Порт 192.168.3.21:2323 приймає TCP (перевірено оркестратором). Попередній процес Codex зупинився о 00:13 через ліміт використання OpenAI, а не через збій. C55Stream не запускався.

## 2026-10-02 04:10 (оркестратор): людина недоступна до ранку

Людина лягла спати й до ранку не зможе ні перезавантажувати E90, ні запускати демон, ні встановлювати SIS. Працюй сам. Якщо E90 потребує перезавантаження або демон зник, не чекай відповіді: зафіксуй стан у work/STATE.md і docs/evidence, опиши потрібну дію в цьому файлі й продовжуй те, що можна без апарата (аналіз, підготовка наступного кроку). N95 не чіпати.

## 2026-10-02 01:12 UTC: після підтвердженого reboot GET/restore ще не почались

HELP/user підтвердили reboot після RUN4, демон запущено. Три bounded
read-only спроби цього відновлення: native-recovery01 Python connect3s,
native-recovery02 Python connect8s, native-recovery-net01 .NET connect8s —
усі TimeoutError до INFO. Жодного PUT/START/RUN/KILL у цьому завантаженні
не виконано. ПК має Wi-Fi Huawei,192.168.3.11/24; Find-NetRoute для
.21 веде через цей Wi-Fi. Python-only проблема не підтвердилася.
Останній отриманий journal RUN4 уже збережено A33A433C…; новий GET/PS0
та exact restore після reboot ще НЕ підтверджені. Ліміт3 network attempts
цього стану досягнуто; незмінні connect не повторюються.

**Потрібно лише відновити daemon transport E90 .21:2323:** закрити
інші клієнтські TCP-з'єднання, перевірити на E90 Wi-Fi/IP і перезапустити
демон через звичайний інтерфейс, якщо він завис. C55Stream не запускати.
Оркестратору перевірити один INFO (відповідь screen800x352 і END), а не
лише TCP handshake, потім закрити сокет і дати нам одну exclusive сесію
GET journal→PS0→restore. Нове reboot зараз не запитується; вже зроблене
reboot достатнє для recovery, якщо транспорт повернеться. N95 не чіпати.

Наступна D0 гіпотеза після recovery: відрізнити RMS_EXIT delivery від
DSP idle/reclaim та native EXITACK. Один змінений own-node diagnostic
має передати STRM snapshots до очікування EXIT, після NODE_getMsg і після
cleanup до return; host має забрати їх під час pending delete. Не
повторювати native control без нової зміни; його8 correct echo packets
самостійно D0 не закривають. D1 hardware все ще лише після3 own clean cycles.

## 2026-10-02 13:21 (оркестратор): E90 перезапущено, демон доступний

Людина перезапустила E90 (демон не відповідав з 04:20). Порт 192.168.3.21:2323 приймає TCP (перевірено оркестратором). Людина знову на зв'язку.

## 2026-10-02 13:35 — встановити діагностичний host25 на E90

Recovery завершено: `native-recovery03` отримав той самий журнал RUN4
SHA-256 `A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1`,
PS c55stream/ocprobe =0, INFO відповідає, startTick81256. `native-restore01`
повернув три початкові E:-файли, усі GET/SHA точні. Повторний RUN ще не робився.

Потрібно на **E90** через File Manager встановити
`E:\c55stream-exit-diag-v25.sis` (22416Б, package revision31).
Файл уже доставлено й GET-перевірено:
`8D0E3BE832E8F81E2538A747D9904FBA37BDEF32F6FCDF614B00BB3EDD51E97A`.
Це оновлення лише нашого `C:\sys\bin\c55stream.exe`, runtime v25,
очікуваний EXE SHA-256
`CB74DE96012E3C9D4D7DDE6F783C6A746F75713B83DBF136DF03001C7035CA0A`.
Підтвердити звичайні запити установника. Сам C55Stream вручну не запускати;
після встановлення повідомити тут і залишити демон запущеним.

Нова гіпотеза RUN5: встановити, чи доставлено RMS_EXIT у NODE_getMsg, чи
повертаються STRM_idle(input/output), і лише потім перевірити native EXITACK.
Own DSP `run-exit-diag` передасть stage4 до очікування EXIT; stage5 одразу
після NODE_getMsg та stage6 після idle у спільному вихідному пакеті.
Хост замовляє вихід до control6. Після idle діагностичний output перевидається;
це впливає на cleanup, тому RUN5 не є одним із трьох звичайних D0 циклів.
Pending/failed delete чи output → QUARANTINE, без KILL/free/close.
Build/import/DOFF перевірки успішні, усі18 imports є у збереженому E90 baseimage.
SIS для кінцевого повернення точного host20 підготовлено з вищою revision32.
N95 не чіпався. Нове перезавантаження зараз не потрібне.

## 2026-10-02 13:38 (оркестратор): дозвіл людини - EXE підміняти самостійно

Повідомлення людини: «можна перевстановлювати exe застосунків підміною без моєї участі. На e90 взлом активний.» Тобто встановлення SIS через File Manager для оновлення лише нашого EXE не потрібне: підміни C:\sys\bin\c55stream.exe (і хеш у C:\sys\hash, якщо так робить ваш інструмент) самостійно через демон, з GET/SHA-перевіркою до й після. Це стосується й запиту v25 вище: людина SIS v25 НЕ встановлювала - виконай підміну сам. Перезавантаження й запуск демона, як і раніше, потребують людини. N95 не чіпати.

## 2026-10-02 13:43 — потрібне перезавантаження E90 після RUN5

Запит на SIS v25 вище вже не потрібний: за дозволом13:38 зроблено
`host25-deploy01`, backup host24/hash до заміни й GET exact host25/hash
після, PS0. Own diagnostic `exit-diag01` зробив лише один новий RUN.
8 packets512Б full240 payload words — correct; stage4/5/6 доставлено.
**RMS_EXIT доставлено:** NODE_getMsg result1, waits1,
cmd80000000/arg1=env77E0/arg2=0. **Перший cleanup чистий:**
STRM_idle input/output0, pending input/output0, DSP status00008000.
Після extra diagnostic output wrapper/native EXITACK ще не доведено:
delete submit0, через5000ms −33/status pending, state3 → QUARANTINE.
Живий журнал GET успішний, SHA-256
`778039EBA2B21B3A07F65FB7EDF89040F2BBB386CF1C11B84157B76023F1691E`.
KILL/free/close не робили; local runner deadline30s зупинив опитування.

**Потрібно:** перезавантажити лише E90, запустити Wi-Fi-демон, повідомити
тут після доступності .21:2323. Сам C55Stream не запускати; N95 не чіпати.
Після reboot спершу GET того самого journal/PS0, потім exact originals3
restore. Host EXE/hash далі підмінятиму сам згідно з дозволом; SIS installer
не потрібен. Новий RUN не повторює цю саму діагностику: тепер шукати
помилку wrapper return / outbound RMS_EXITACK / ARM MSG reader, а не
повторно перевіряти доставлений RMS_EXIT. D0 own0/3, experimental5.

13:54 повторний read-only `exit-recovery01` підтвердив незмінний journal
SHA778039EB…, DSP29069D52…, INFO відповідає, startTick той самий81256,
PS c55stream1/ocprobe0. Reboot ще не відбулося; живий QUARANTINE owner
перешкоджає безпечному restore/наступному RUN. PUT/START/KILL у цій
перевірці не було. Запит human reboot вище залишається актуальним.

## 2026-10-02 14:55 (оркестратор): E90 перезавантажено після RUN5

Людина перезавантажила E90 і запустила демон. Перевірка порту оркестратором - див. наступний рядок запуску. C55Stream не запускався.

## 2026-10-02 15:16 local — created-worker preflight pending, потрібен reboot E90

RUN5 recovery виконано: exit-recovery02 journal778039EB… exact/PS0,
exit-restore01 original DSP/log/clocklog PUT→GET exact, startTick65704.
Host26 direct replacement дозволений: host25 EXE/hash GET backup до
PUT, host26 EXE40920Б2EAC917E…/hash GET exact. Нова гіпотеза:
prearmed outbound MSG у CREATED, без execute wrapper/офіційного RUN.

`worker-msg01` зупинився на create-only preflight: create0/7598us,
state1; delete submit0, через5000ms−33/pending, після state1.
Планований trigger/MSG diagnostic НЕ почався: NODE_putMsg606 і RUN
не викликались. Це не результат ARM reader test і не RUN6.
Я повторно використав create-only preflight для active stream worker;
його cleanup без input/native buffers ще не був доведений. Належить
перевірити stop→NODE_wait→idle/reclaim/join, а наступний diagnostic
має одразу подавати кінцевий trigger після створення, без цього preflight.
Безумовного повтору не буде. QUARANTINE, KILL/free/unload не робив.
Live GET journal2092Б:
`B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92`.
Clock log1249Б відновлено exact; DSP/log research26, host26/hash research.

**Потрібно перезавантажити лише E90, запустити Wi-Fi-демон .21:2323
і повідомити тут.** Сам C55Stream не запускати; N95 не чіпати.
Після повідомлення спершу GET journal/PS0, потім originals3 restore;
наступний тест лише після аудиту цієї нової cleanup гілки.
D0 own0/3, experimental RUN5 unchanged; D1 pending, D2 provisional.

## 2026-10-02 15:21 (оркестратор): випадковий LS на E90

Близько 15:21 мій deploy_net.ps1, адресований N95 (.22), через тимчасову недоступність N95 сам знайшов E90 і виконав там одну команду лише читання: LS E:\PS1\cfg\. Запису, PUT, START чи KILL не було. Якщо в журналі демона E90 є це з'єднання - це воно. deploy_net.ps1 виправлено (SymbianDeployDaemon 2743c6c): явний -Ip більше не сканує мережу.

## 2026-10-02 15:28 (оркестратор): роботу зупинено за вказівкою людини

Людина переносить SSD на ноутбук; процес codex exec (сесія 01a0f8bc-b1b0-77a1-8d92-45a5a49ed009) зупинено оркестратором о 15:28 посеред ходу. Після відновлення: спершу перевірити стан E90 (GET journal/PS0, чи не лишилось незавершеної операції з цього ходу), лише потім продовжувати. Людина уточнила мету: задачі на DSP мають давати справжню паралельність з ARM (DSP обробляє асинхронно, ARM тим часом робить іншу роботу), а не синхронні виклики.

## 2026-10-02 вечір — усі запити фізичного відновлення закриті

Користувач підтвердив reboot E90; laptop-recovery01 GET отримав старий
журнал B9B4E282… exact, PS0/startTick61087. Originals3 відновлено.
За новим дозволом користувача тестували також N95. Чотири finite MSG
diagnostics clean delete/free/close, але ARM receive−33; нових RUN немає.
Після них **обидва телефони повністю restored**: DLL/log/clocklog/EXE/hash
GET/SHA-equal, host20, c55stream/ocprobe PS0. Daemon startTick E9061087,
N9522918156 незмінні. Жодного запиту на reboot/installer зараз немає.
Подальша робота — native runtime reader/window/queue audit;
docs/WORKER_MESSAGES_2026-10-02.md і docs/evidence/2026-10-02/worker-message-checkpoint.json.

## 2026-10-03 01:25 UTC: історичний запит після D0 Cycle 1

Під час першого D0 циклу `run-transfer reps=0 bytes=512 frames=8` (сесія `d0-20261003-cycle1`, запуск `run01`):
- Усі 8 кадрів передано та верифіковано (`STREAM PASS frames=8 creates=1 useful_arm_crc=0 mode=0 total_us=3230`, 3.23 мс).
- На фазі видалення (Ctl 6) виник таймаут `delete=-33` (5000 мс), що перевело процес у штатний `QUARANTINE` (нескінченний сон `User::After(1000000)` без виклику free/close для захисту апарата).
- Процес `c55stream.exe[e0001021]0001` наразі активний у карантині на E90, Wi-Fi-демон на 192.168.3.21:2323 відповідає.
- Відповідно до правил безпеки, автоматичний KILL активного процесу суворо заборонений.

**Аналіз причини:**
- Повний дизасемблер `ehwaomap.pdd` (адреси `803e69b4`, `803df7dc`, `803df850`, `803df864`) показав:
  При стані RUNNING (2) Ctl(6) надсилає `RMS_EXIT` (0x80000000) та чекає `RMS_EXITACK` (0x40000000) від DSP.
  ARM consumer порівнює `source` вхідного повідомлення з `queue->source` (0x000077E0).
  У збірці run01 функція `fix_caller_env` помилково переставила 16-бітні слова у слоті стеку `nodeEnv`, через що DSP надіслав `source = 0x77E00000`. ROM reader `803f7664` виконав `ror #16`, що дало `0x77E00000 != 0x000077E0`, споживач проігнорував `RMS_EXITACK`, не викликав `803e6860` (`NODE_delete`), і 5-секундний таймер завершився таймаутом -33.
- Помилкову перестановку слів повністю видалено з `src/dsp/stream_node.c`, DSP DLL перезібрано (`out/dsp/c55stream-run-stop.dll55l`) та верифіковано в `docs/evidence/2026-10-03/d0-run-stop-v40-artifacts.json`.

**Потрібна дія:**
1. Перезавантажити Nokia E90 фізично.
2. Запустити Wi-Fi-демон на E90 (192.168.3.21:2323).
3. Повідомити про перезапуск. N95 не чіпати.
Після повернення зв'язку:
- Буде виконано перевірку `PS c55stream* = 0` та відновлення 5 оригінальних файлів.
- Буде виконано чисту серію з 3 циклів D0 із виправленим DSP вузлом.

## 2026-10-03: актуальні дії після Codex routing diagnostic

Попередній запит і причинне пояснення вище застаріли; повернення E90
підтверджене startTick33897/PS0. Користувач у Gemini-транскрипції дозволив
KILL за потреби та роботу з обома телефонами; старий blanket no-KILL
текст не відображає це уточнення.

1. E90: увімкнути Open4All у RomPatcher. GET C:\sys\bin\c55stream.exe
   повернув ERR open−46, тому EXE/hash не відновлені; DLL/log/clocklog
   уже original GET-equal. Після повернення доступу restore-host→verify
   у work/evidence/e90/d0-20261003-cycle2 з новими codex tags.
2. N95: перезавантажити й запустити daemon. Runtime snapshot виявив
   старі kernel queues і два source77E0, попри PS0 перед пробою.
   Correct EXITACK40000000/8000 не завершив delete нового вузла.
   Journal збережений; quarantined host знятий дозволеним KILL;
   всі5 originals відновлені та SHA-equal verified, активних процесів немає.
   Reboot потрібен для чистої маршрутизації, а не для відновлення файлів.

Обидві дії запитані через async user input. Наступний host34 guard
відмовляє до RUN, якщо matching queue для env не рівно одна.
D0 лишається0/3; наступна серія не починається з dirty kernel state.
Документ і точка продовження: docs/MESSAGE_ROUTING_2026-10-03.md.

## 2026-10-03: актуальний запит — reboot з уже встановленим host35

Попередні Open4All/reboot дії виконано. Host34 guard відмовив до RUN
на обох телефонах: його PROC_Load повторно завантажив DSP-базу при наявних
штатних native queues. Безумовний stop/load/start підтверджено на двох ROM.

Host35 вже встановлено на N95/E90: використовує running base без
PROC_Load. Attach/create/delete/free перевірено0 на обох; старий конфлікт
ще існує. Quarantine й активних c55stream/ocprobe немає. DLL/log/clocklog
оригінальні GET/SHA-equal; v35 EXE/hash навмисно залишені встановленими,
оригінальні EXE/hash збережені у d0-20261003-clean34.

Потрібно фізично перезапустити **обидва** телефони, повернути daemon та
Open4All й повідомити про готовність. Це новий запит після старого host34
reload; попередній reboot користувача був виконаний. Async запит надіслано.
Після зміни startTick — d0-sequence host35 candidate47, tag attach-sequence02.
Деталі: docs/BASE_ATTACH_2026-10-03.md. D0 0/3; нових official RUN немає.

## 2026-10-03: актуальний reboot запит закрито, D0 успішний

Користувач підтвердив новий reboot обох; daemon/Open4All доступні.
E90 startTick60327 / N95 62209. Host35 candidate47 пройшов3/3 чисті
ordinary D0 cycles на кожному, boot незмінний, усі lifecycle statuses0.
Original DLL/log/clocklog restored, host35 встановлений для D1, PS0.
Нових фізичних дій не потрібно. Наступне — D1 mapping/ring probe.
Доказ: docs/evidence/2026-10-03/d0-attach-success.json.

## 2026-10-03: актуальний крок — Open4All лише на E90

D0 успішний на обох. N95 завершив3 серії D1, усі5 originals повернуті,
PS0; жодних фізичних дій на N95 зараз не потрібно.

E90 відновив зв'язок після boot change під час initial routing snapshot
host41. Журнал GET збережений до PUT, PS0. Original DLL/log/clocklog
відновлені. Exact original EXE/hash restore зупинився до PUT через
`ERR open -46` у C:\sys. **Увімкнути Open4All на E90**, залишити daemon
192.168.3.21:2323 доступним і повідомити. Новий reboot не потрібен.

Після цього агент сам відновить EXE/hash, перевірить5 originals і
продовжить із новою гіпотезою host42/candidate55; unchanged host41 run
не повторювати. Детальна точка продовження — останній розділ STATE.md.
D1/D2 залишаються відкритими; root cause boot change ще не доведено.

## 2026-10-03: актуальний крок — повернути E90 після candidate56

Попередній Open4All виконано, originals5 відновлено, candidate55
перерився до map/RUN і також відновлений. Candidate56/host43 пройшов
одну повну серію та s2-b1, але під час s2-b2 daemon зник. Журнал ще
не отриманий, current EXE/hash/DSP research installed. Запит async:
перевірити E90 і повернути daemon/Open4All, якщо потрібно — reboot.

Після доступності агент GET journal/PS до будь-якого PUT, аналізує й
відновлює originals5. Новий unchanged56 RUN заборонений. N95 restored,
його не чіпати. Поточна точка продовження — останній STATE розділ.

## 2026-10-03: усі фізичні запити закриті

Користувач повернув E90 та підтвердив automatic reboot, а не лише Wi-Fi
timeout. Усі54/55/56 failure journals отримані до PUT; latest readable
журнал обірвався до DSP RUN. Probe57 був лише короткий; довгу серію
скасовано після уточнення. Read-only boot-info44 завершився чисто.

**N95/E90 всі5 originals GET/SHA-equal, c55stream/ocprobe PS0.** Нових
фізичних дій зараз не потрібно. Наступне — безпечний native reader/state/
queue contract і cause investigation до нового E90 RUN; не unchanged retry.
Current source44 є локальним research artifact, на телефонах original20.
