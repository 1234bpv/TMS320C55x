# Колізія маршрутизації DSP-повідомлень на N95

Продовження після Gemini встановило новий факт: **PS0 не означає відсутність
старих kernel DSP-вузлів**. Під час нового diagnostic RUN на N95 існували
дві черги з однаковим source `000077E0`. Native consumer обирає перший
збіг, тож правильний EXITACK нового вузла може потрапити до старого вузла.
Колізія доведена; перевірка повного teardown після чистого reboot ще потрібна.

## Відновлення E90

E90 відповів о 12:08 UTC, PS c55stream/ocprobe0, startTick33897.
Отриманий журнал останнього Gemini `create02` закінчується на
`BEGIN select node`, ще до create/GetState/teardown. Гіпотеза про відмову
в GetState цим журналом не підтверджується.

Сесія `work/evidence/e90/d0-20261003-cycle2`, `codex-recover01` зберегла
журнал і DSP SHA. `codex-restore01` повернула original DLL/log/clocklog
з GET-перевіркою. Restore-host і повний verify відхилені `ERR open -46`
на GET `C:\sys\bin\c55stream.exe`. EXE/hash лишаються невідновленими
до повернення доступу Open4All. Повторного RUN на E90 не було.

## Новий експеримент N95

Сесія `work/evidence/n95/d0-20261003-codex-routing`:

- П'ять originals збережені до змін.
- Host33: inspect і create-only пройшли; delete/free/close/FINAL0.
- Clocks01: штатний m86, ARM330240/BUS165120/DSP220160 kHz,
  DSP divider3; stock guard підтверджений, ocprobe.log відновлений.
- Routing01 відхилений parser до DSP через пропущений frameMode нового
  режиму. Це виправлено; candidate43 не використовувати для run-routing.
- Routing02, candidate44: official RUN, вісім правильних packets512 Б,
  total2987 us; після цього delete−33/pending/quarantine.
- Журнал отриманий до recovery. Авторизований KILL зняв quarantined host;
  після цього restore02/hostrestore01/finalverify01 підтвердили всі п'ять
  originals і відсутність активного c55stream. Це не clean D0 teardown.

## Спостереження до/після delete

До delete черги в pool мали порядок:

| Черга | Source | PDD node | State / phase / timeout |
| --- | --- | --- | --- |
| 0, C81D0B78 | 000077E0 | C81CF8D0 | 2 / 2 / 00002710 |
| 1, C81AD478 | 00007700 | C81AD2B0 | 2 / 2 / 00002710 |
| 2, C81BE0C0 | 000077E0 | C81BBDE0 | 2 / 2 / FFFFFFFF |

Новий кандидат використовує timeout FFFFFFFF. Уже до його delete є
старі черги з timeout2710 і дубльованим env/source77E0.

Після delete shared record декодовано як
`40000000 / 00008000 / 00000000 / 000077E0`: правильний EXITACK/EOK/source.
У старого першого node env став0, phase6; у нового env лишився77E0,
phase6. Обидва спостерігались у PDD state11. З'явилися ще дві черги.
Host deleteStatus лишився pending, LDD state3.

Найкраще поточне пояснення: ACK був зіставлений зі старою першою чергою,
а новий вузол не отримав очікуване завершення. Причинність усіх попередніх
відмов, механізм переходу state11 і походження кожного старого вузла
ще не встановлені. Snapshot неатомарний.

## Статичний контракт і зміни

`tools/rev/audit_message_routing.py` перевіряє 18 E90 PDD instructions,
BL до automatic delete і list First() у збереженому ROM dump.
Consumer: context+32→pool, pool+8→list, item+12→queue,
queue+16→source, queue+36→node; перший matching EXITACK сам викликає delete.
Callback phase3 ставить PDD state3; phase6 є delete completion.
Gemini неправильно ототожнював phase3/state3 з необхідністю повторного delete.
Task3 user journal також містить LDD state, що відрізняється від PDD state.

Host33 прибирає новий NULL-status/two-delete шлях Gemini й додає bounded
read-only routing snapshots у діагностичному `run-routing`.
Host34 додатково перед RUN отримує native NodeInfo env і вимагає рівно одну
matching kernel queue. За відмови не викликає RUN, видаляє свій CREATED node.
Guard не змінює kernel code, PRCM або джерела черг; старі вузли не видаляє.
Це захист від спостереженої колізії, а не доведене завершення D0.

DSP лишається побайтово candidate41/42 (`7E1D922E…`); для наступної чистої
проби змінюється лише host. Затримка DSP перед return лишається старою
діагностичною гіпотезою Gemini, не доведеним mutex fix.

Runner тепер використовує правильний EXE path E90/N95, дозволяє необхідні
N95 preflight/deploy actions і збирає clock probes для обраного пристрою.
Validator відхиляє діагностичний RUN як D0 і для host34 вимагає unique-source
guard перед BEGIN execute. 13 offline tests проходять.

## Продовження

**Оновлення після підготовки телефонів:** host34 guard перевірено на обох,
відмова до RUN з чистим cleanup. Виявлено безумовний PROC_Load stop/load/start.
Host35 уже встановлено й працює через attach до чинної бази. Поточний
checkpoint та наступні команди — [BASE_ATTACH_2026-10-03.md](BASE_ATTACH_2026-10-03.md).
Наведений нижче план для host34 є історичним.

1. N95 reboot/daemon; перевірити новий startTick. Open4All на E90 для
   відновлення EXE/hash і подальшого deploy. Обидві дії запитані користувачу.
2. Backup/verify, host34+DSP41, create-only preflight. Перед наступним RUN
   має пройти unique-source guard; за відмови нового RUN немає.
3. Одна чиста normal run-transfer проба. Лише після підтвердженого
   delete/free/close/FINAL/EXIT0 — серія трьох послідовних D0 циклів.
4. D1 (ring16KiB TOTAL) і D2 лишаються після D0.

Публікація спостережень: `tools/summarize_message_routing.py`.
Докази: `docs/evidence/2026-10-03/n95-message-routing-checkpoint.json` і
`docs/evidence/2026-10-03/message-routing-native-audit.json`.
