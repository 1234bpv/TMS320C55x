# Підключення до чинної DSP-бази

Оновлення після нового reboot: **D0 завершено на обох телефонах, 3/3**.
E90 startTick60327, N95 startTick62209; host35 candidate47, base reload0.
Кожен окремий RUN передав8 правильних512-Б packets/protocol21,
delete/free task/free native buffers/close/FINAL/EXIT0. Boot незмінний.
Оригінальні DLL/log/clocklog повернуто GET-equal; host35 залишено для D1.
Докази: [D0 success](evidence/2026-10-03/d0-attach-success.json),
відтворення `tools/summarize_d0_attach_success.py`. D1 hardware gate відкрито;
copy-channel timings нижче не є результатом DMM кільця або speedup.

Попередній результат до reboot: **D0 0/3**, нових official RUN немає. На обох телефонах
host34 виявив duplicate source77E0 до RUN, відмовив з −11 і чисто виконав
delete/free task/free native buffers/close. Це корисна перевірка захисту,
але не успішний D0 цикл.

## Причина, яку потрібно перевірити після свіжого старту

Хост до v34 кожного разу викликав ordinal26 (`PROC_Load`) для базового образу,
хоч DSP уже використовувався штатним аудіо. На обох прошивках native load
має безумовний виклик stop, далі load/start. Running state не є умовою
пропуску stop. Статичний аудит перевіряє 20 інструкцій та три переходи
на кожній прошивці: `tools/rev/audit_processor_reload.py`.

Після такого завантаження runtime зберігає дві native черги з source77E0
(стара штатна і наш новий CREATED node) та ще source7700.
Оскільки consumer обирає перший source, це узгоджується з раніше
зафіксованим ACK, що потрапляв до старого вузла. Роль конкретних аудіовузлів
і причинність усіх історичних невдач ще не доведені.

Host35 прибирає `PROC_Load`, підключається до вже запущеного processor0,
перевіряє manager magic/back-pointer/index/state4 і реєструє лише власну
динамічну бібліотеку через DCD parse. Unique-source guard перед RUN
збережено. Якщо running base не існує, хост відмовляє з очищенням каналу.
Цей хост не відновлює черги, які вже стали неузгодженими після старого load.

## Апаратні перевірки

| Апарат | Host34 | Host35 без нового reboot |
|---|---|---|
| E90, startTick33897 | create clean; guard−11; cleanup0 | attach gate0; create clean; guard−11; cleanup0 |
| N95, startTick64375 | create clean; guard−11; cleanup0 | attach gate0; create clean; guard−11; cleanup0 |

Жоден із цих чотирьох guarded refusals не викликає execute. FINAL/EXIT−11
відображає захисну відмову; це не успішне передавання пакетів.

Candidate47: host35, незмінний DSP41/42, перевірена збірка ARM/SIS/DOFF.
14 offline tests пройшли, validator додатково вимагає збереження running base.
DSP busywait перед return лишився попередньою непідтвердженою гіпотезою.

Оригінальні DLL/log/clocklog обох телефонів повернуто GET/SHA-equal;
host35 та його hash навмисно залишені встановленими. Оригінальні EXE/hash
лежать у `work/evidence/{e90,n95}/d0-20261003-clean34/original-{3,4}.bin`.
Останній verify — `attach-verify01.json`, PS c55stream/ocprobe0 на обох.
Повне відновлення п'яти файлів виконати після завершення дослідів.

## Точна наступна дія

Користувачу запитано фізичний reboot **обох** телефонів і повернення
Wi-Fi daemon/Open4All. Після цього перевірити змінений startTick, PS0,
незмінні candidate47 host SHA та originals3. Не починати зі старого host34.

Для кожного `--device e90` або `--device n95`:

```powershell
& 'C:\Program Files\LibreOffice\program\python.exe' -X utf8 tools/e90_task_session.py --device e90 --session work/evidence/e90/d0-20261003-clean34 --action d0-sequence --host-version 35 --artifact-proof docs/evidence/2026-10-03/d0-attach-base-v47-artifacts.json --tag attach-sequence02
```

Для N95 замінити також сегмент `e90` у session. `d0-sequence` робить
read-only stock clocks, inspect, DSP deploy/readback, create-only,
три normal RUN. За відмови припиняє наступні RUN і зберігає журнал.
Новий тег обов'язковий; старі журнали не перезаписувати.

Після трьох чистих D0 циклів: D1 ring **16KiB TOTAL**, ownership/cache/map
та повторні виміри; далі D2. Даних для завершення цих фаз поки немає.

Повторне складання checkpoint: `tools/summarize_base_attach.py`.
Докази: `docs/evidence/2026-10-03/base-attach-checkpoint.json`,
`processor-reload-native-audit.json`, `d0-attach-base-v47-artifacts.json`
та чотири `*-source-guard.txt` у тому самому каталозі.
