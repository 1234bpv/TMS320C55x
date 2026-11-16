# Розміри пакетів: N95 та E90, v18

План етапу — `work/PLAN_V18.md`; повний обсяг — `work/PLAN.md`.
V18 продовжує підтверджений у v17 власний worker: generic library2,
CREATED, `NODE_wait(NULL, ...)`, explicit stop і join до звільнення ресурсів.
Штатний RUN не використовується. Це дослідницький прототип.

## Контракт і артефакти

Host properties input+184/output+1592 містять stream size у полі+4.
PDD N95 `8019FE38` та E90 `803E4478` копіює його до RMS stream definition+0
без масштабування. Це C55 16-бітні слова; descriptor length у transfer —
ARM-байти. Інструкції, що задають розміри, звірено на обох ROM:
[контракт](evidence/2026-10-01/n95-e90-stream-size-contract.json),
`tools/rev/check_stream_sizes.py`. DCD лишився без змін.

Native allocation mode2 потребує додатного розміру, кратного4096.
Прототип виділяє по4096 байтів input/output і обмежує packet512–4096 Б,
парною довжиною. Це межа цього прототипу, а не встановлений максимум драйвера.
Worker приймає однакові input/output sizes256–2048 C55-слів, перевіряє
reclaimed length і header length, перетворює весь payload. Q15 dot240
рахується лише на перших240 значеннях; coefficient/state contract не змінено.

Host29760 Б SHA-256 `571C5A6221C7E7815558A2C3AE5F6665D8D7DE0B82D676488869C7BAA260F14F`;
DSP4852 Б `DD8D50DC20F66F44A7212D86B364C4905EF37227C1A3BF945A26B9CE95510AD3`.
DOFF/imports/ASM і новий immutable archive:
[артефакти](evidence/2026-10-01/worker-stream-v4-artifacts.json).
SIS v18 доставлено й встановлено на E90; EXE збігся читанням назад і пройшов
runtime profile. Raw firmware, binaries, keys та screenshots не публікуються.

## Методика

На кожному телефоні: мінімальні one512/1792/4096, Q15 reps1000 на восьми
4096-байтових пакетах і три серії шести розмірів по32 пакети.
Разом **22 успішні запуски й 587 правильних пакетів на кожному**.
Порядок розмірів у серіях прямий, зворотний, потім з циклічним зсувом.
До кожного run: inspect, точний GET DSP, перевірка fresh preparation.
На N95 MPU percent=100 до/після кожного пакета; на E90 N95 dvfs API не викликається.

`worker-transfer` має reps0 і не рахує ARM CRC. Для кожного пакета
FastCounter32768 Гц фіксує початок перед submit і спостережуване завершення
після двох Wait. В інтервалі є driver issue/wait/scheduling, transport та
повне DSP echo. Генерація input, перевірка output, логування і одноразовий
create перебувають поза ним. Роздільність лічильника — приблизно30.5 мкс.
Це **час до спостережуваного завершення**, не чиста DMA latency/bandwidth.

Таблиця містить96 пакетів на розмір. p95 — емпіричний nearest-rank percentile;
max збережено без вилучення повільних пакетів. Ці числа не є гарантованими
межами дедлайну. Один create підтримує32 пакети, а не96: це три окремі runs.

| Packet / payload, Б | N95 median / p95 / max, мкс | E90 median / p95 / max, мкс |
|---|---:|---:|
| 512 / 480 | 335 / 366 / 640 | 396 / 396 / 488 |
| 1568 / 1536 | 518 / 518 / 579 | 610 / 640 / 793 |
| 1792 / 1760 | 518 / 518 / 549 | 640 / 701 / 7812 |
| 2048 / 2016 | 549 / 579 / 671 | 701 / 762 / 7690 |
| 2304 / 2272 | 610 / 640 / 3021 | 762 / 793 / 3234 |
| 4096 / 4064 | 885 / 946 / 1251 | 1129 / 1220 / 2502 |

[N95: усі runs і byte-exact журнали](evidence/2026-10-01/n95-packet-sizes-v18-results.json),
[E90](evidence/2026-10-01/e90-packet-sizes-v18-results.json).
`tools/summarize_packet_sizes.py` незалежно перевіряє packet counts/sizes,
Q15 проти обчисленого еталона, CRC, sequence/stop, per-frame MPU, точний DSP,
FINAL/EXIT0, delete/free та відсутність RUN/KILL. У цій серії немає перезапусків.

## Наслідки для прикладних задач

WSOLA передає1760 Б даних; із header32 це **1792 Б input**. Цей розмір
проходить одним пакетом. Нині output теж1792 Б, хоча справжньому search
потрібні лише offset/score. Вимір518/640 мкс є орієнтиром для echo такого
розміру; час WSOLA, підготовка і короткий output ще не виміряні.
На E90 один correct packet тривав7.812 мс, що більше hop220/44100≈4.99 мс.
Тому для такого offload потрібні черга, запас семплів і вимір underrun;
одна медіана не доводить придатності синхронного виклику на кожен hop.

MDEC input1536 Б потребує1568 Б з header, output RGB15/24 —544/800 Б.
Сумарний application transfer був би2112/2368 Б з двома headers.
Нинішній1568-byte echo передає1568 Б у кожному напрямку, тобто3136 Б.
Не підміняти асиметричний MDEC обмін сумою input/output як розміром одного
симетричного пакета. Наступний gate — actual kernel, короткий output,
порядок DMA, rounding/flags і вимір `A,D,H,S` на тому самому вході.

Original DSP після обох серій повернуто GET-equal, PS0:
[N95 recovery](evidence/2026-10-01/n95-packet-sizes-v18-recovery.json),
[E90 recovery](evidence/2026-10-01/e90-packet-sizes-v18-recovery.json).
Пізніша повторна звірка E90 підтвердила original DSP/log і host v18:
[E90 status](evidence/2026-10-01/e90-packet-sizes-v18-device-status.json).
Після відповіді користувача повторний GET N95 також збігся для всіх трьох
файлів, PS0: [N95 status](evidence/2026-10-01/n95-packet-sizes-v18-device-status.json),
[спільний checkpoint](evidence/2026-10-01/worker-stream-v18-checkpoint-device-status.json).
Між завершеною серією та цією пізнішою звіркою uptime N95 зменшився;
це нове завантаження після дослідів. Причина ще не з'ясована, користувачу
надіслано уточнення. Воно не приховується твердженням про відсутність
перезапусків усередині вже перевіреної серії.
Довга стабільність, audio coexistence, timer/idle та negative lifecycle
залишаються відкритими. F05–F08 поки не позначаються завершеними.
