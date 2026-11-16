# Доставка MSG і завершення finite worker — 2026-10-02

Пізніше продовження: host29 read-copy diagnostic і static pointer audit
описані в [ARM_MESSAGE_RUNTIME](ARM_MESSAGE_RUNTIME_2026-10-02.md).
Нових MSG/RUN не було; E90 знову fully restored host20/PS0.
Цей документ лишається звітом чотирьох попередніх finite MSG diagnostics.

Після підтвердженого користувачем reboot E90 старий журнал отримано до
записів: 2092 Б, SHA-256 B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92.
PS0, новий daemon startTick61087; три початкові файли повернуто GET-equal.
Користувач дозволив тести також на N95; його початкові п'ять файлів
збережено до заміни хоста.

## Результат

Один кінцевий STRM input звільняє BIOS worker у CREATED. Worker викликає
NODE_putMsg606/A1B2C3D4/env, повертає STRM snapshot, idle/reclaim і
завершується. ARM перевіряє snapshot і викликає created delete/join.
Офіційного RUN і wrapper EXITACK у цих дослідах немає.

| Апарат / host | ARM receive | DSP put / STRM output | ARM MSG | delete/free/close |
|---|---|---|---|---|
| E90 / 26 | До input | 1 / правильний snapshot | −33, pending | Успішні |
| E90 / 27 | Після output | 1 / правильний snapshot | −33, буфер порожній | Успішні |
| E90 / 27 | До input, додано raw logging | 1 / правильний snapshot | −33, буфер порожній | Успішні |
| N95 / 28 | До input | 1 / правильний snapshot | −33, буфер порожній | Успішні |

FINAL/EXIT у всіх чотирьох −33 через MSG receive; це **не успішні D0 цикли**.
Проте delete=0/status0, стан DELETED5, free task/native buffers0 і close
підтверджені. Pending receive звільнено перед close; QUARANTINE немає.
No-input cleanup, який завис раніше, не повторювався і не виправлений.

Stage7 підтверджує cmd606/arg1A1B2C3D4/arg2env77E0 та raw source77E0.
DSP queue count0, fromDSP header0/0/1 під час snapshot та empty_after1.
Snapshot не атомарний. Зміна empty сумісна з роботою ARM consumer, але
сама не доводить IRQ/DFC, фактичний ARM word order чи вибрану чергу.
Збій повторюється на обох апаратах; точна причина ще не встановлена.

## Частоти і відновлення

E90: прочитаний stock profile ARM330.24/bus110.08/DSP220.16 МГц.
N95: наявний розгін m111, PLL0006F400/sel2=2/MPU2/core04360844/DSP23C3;
за регістрами ARM426.24/bus213.12/DSP284.16 МГц. Старий текст ocprobe
«firmware math CORE660480» використовує stock reference і не є actual
частотою N95 у цій сесії. Перша N95 підготовка з stock guard відмовила
до DSP START; наступна явно перевірила точний наявний профіль m111.
PRCM writes немає. Це snapshot частот перед тестом, не перевірка DVFS
на кожному пакеті і не performance benchmark.

Після тестів на **обох** повернуто DLL/log/ocprobe.log/EXE/hash,
усі п'ять GET/SHA-256 збігаються з originals. На обох встановлений
початковий host20; локальна діагностична збірка — host28/protocol26.
Фінальні c55stream/ocprobe PS0, startTick E9061087/N9522918156 незмінні.
Нових RUN/KILL/reboot у цих тестах немає; загальна історична кількість
experimental RUN лишається5, D0 own0/3. D1 не запускався, D2 попередній.

Докази: [checkpoint](evidence/2026-10-02/worker-message-checkpoint.json),
[E90 до input](evidence/2026-10-02/e90-laptop-worker-prearmed27-worker-message.txt),
[E90 після output](evidence/2026-10-02/e90-laptop-worker-queued01-worker-message-queued.txt),
[N95](evidence/2026-10-02/n95-worker-msg02-worker-message.txt).
Відтворювана публікація: tools/summarize_worker_messages.py;
source/import/DOFF hashes — artifacts35/37 у evidence/2026-10-01.

## Наступна перевірка

Перед новим MSG/RUN потрібен аудит bounded read-only ARM snapshot:
фактична shared-window адреса і DWORD, reader byte64, queue source16,
pending receive40 та consumer count. Це відділить mapping/word order,
вибір черги і completion. Відомі зі статичного коду PDD адреси й offsets
ще не дають безпечного runtime pointer: спочатку простежити його походження
та межі читання. Не патчити reader і не форсувати IRQ/DFC за припущенням.
Три варіанти E90 вже перевірені; той самий receive більше не повторювати
без нової доведеної гіпотези. Фізичних дій зараз не потрібно.
