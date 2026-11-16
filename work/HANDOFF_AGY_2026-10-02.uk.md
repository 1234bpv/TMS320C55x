# Передача роботи agy — 2026-10-02

## Завдання та межа завершення

Користувач дозволив надсилати коміти та продовжувати до повного виконання
плану. Останнє прохання — зберегти цей підсумок для agy.
Чинне доручення: `work/CODEX_TASK_2026-10-01.md`, план
`work/PLAN_D0_D2.md`, статус `work/features.json`. Історичні F01–F08
завершені у research scope; це **не означає завершення D0–D2**.

- D0: три послідовні чисті цикли власного create → official RUN → packets
  → delete/free/close, FINAL/EXIT0, доступність телефона після кожного.
  Поточний результат **0/3**, historical experimental RUN calls **5**.
- D1: після D0 перевірити DMM/zero-copy, кільце **16 КіБ TOTAL**, correctness,
  ownership/cache/wrap/cleanup; повторні latency/bandwidth measurements.
  Hardware D1 ще не запускався.
- D2: виміряні вердикти MDEC/SPU/WSOLA за
  `max(H + D, W) + S/N < A + W`. Поточний висновок provisional;
  оновити після D1. Емулятор і браузер у цьому дорученні не редагувати.

Загальний намір: DSP виконує роботу асинхронно, ARM у цей час робить
іншу корисну роботу. Не підміняти цей критерій синхронним викликом DSP.

## Що завершено в цій сесії

1. Відновлено контекст і знайдено незакомічений host29 diagnostic, новіший
   за останній запис STATE. Його `patcher-read-check` уже виконався в
   попередньому незавершеному ході; повторного запуску не було.
2. Збережений read-copy journal повторно отримано з E90 до записів:
   SHA-256 `56167F767D4B30FF225DA24BFB0F6666FD25F16B9FB22B1398D4DBB911195D76`.
   Доведені три копії по24 Б у власний user buffer: own RAM, ROM reader
   `803F7664`, module BSS `C8010B20`; FINAL/EXIT0, без DSP processor open,
   kernel code writes чи PRCM writes.
3. Додано `tools/rev/audit_arm_message_runtime.py`: статична перевірка
   28 instructions, двох BL targets, BSS header і reader body.
   Додано `tools/summarize_arm_message_runtime.py` для offline публікації
   16 raw proofs, pointer audit і restoration checkpoint.
4. Посилено validator у `tools/e90_task_session.py`: точні ROM words,
   source addresses, розмір, порядок, спільна destination, firmware/profile,
   FINAL0 і відсутність DSP open; враховано CRLF реального журналу.
   Дев'ять offline tests проходять; environment/artifact check успішний.
5. E90 повернуто всі п'ять originals: DLL/log/ocprobe.log/EXE/hash.
   PUT→GET і фінальні SHA збігаються. Host20, c55stream/ocprobe PS0,
   daemon startTick61087 без зміни. Перезавантаження не потрібно.
6. Після явного дозволу користувача відправлено два коміти в private main:
   `5fc3071` і `26d6354`. Віддалений HEAD перевірено:
   `26d63542d08be5c07b38e4896745d9cf24e0e147`.
7. Після push виконано тільки локальний розбір ROM контейнерів ядра,
   factory і manager. Його проміжні результати записані нижче.
   Нових телефонних INFO/PUT/START/MSG/RUN після restore не було.

Поточний звіт: `docs/ARM_MESSAGE_RUNTIME_2026-10-02.md`.
Поточний доказ: `docs/evidence/2026-10-02/arm-message-runtime-checkpoint.json`.
Попередні finite MSG diagnostics:
`docs/WORKER_MESSAGES_2026-10-02.md` і
`docs/evidence/2026-10-02/worker-message-checkpoint.json`.

## Апарати, версії та незавершена проблема

Дозволені обидва апарати, завжди з explicit IP та identity check:
E90 `192.168.3.21:2323`, screen800x352, MachineUid20002496;
N95 `192.168.3.22:2323`, screen320x240, MachineUid20002D84.

E90 останній перевірений стан — п'ять originals exact, host20/PS0.
N95 у цьому продовженні не опитувався; останній попередній proof —
п'ять originals exact, host20/PS0, startTick22918156. Перед новою дією
перевірити стан заново, не оголошувати старий proof поточним live станом.
Попередні clock snapshots: E90 ARM330.24/bus110.08/DSP220.16 МГц;
N95 existing m111 ARM426.24/bus213.12/DSP284.16 МГц, без PRCM writes.

Локальний EXE — host29, DSP diagnostic protocol26; artifact38:
`docs/evidence/2026-10-01/d0-worker-message-v38-artifacts.json`.
Source/EXE hashes звірені з ним. На телефоні після restore host20.
Не плутати local host29 з установленою версією.

Чотири попередні finite CREATED MSG diagnostics (три E90, один N95)
дали DSP put1 і правильний STRM snapshot, але ARM receive−33/empty record.
Created delete/free/close чисті. Це не D0 cycles. Ті самі MSG receive
варіанти без нового доказу не повторювати.
No-input worker cleanup раніше завис і досі не виправлений.

## Перевірений статичний MSG pointer chain

- board+264 → context, allocation364 Б.
- context+48 = common board = board+8.
- context+24 → reader = common board+164 = board+172.
- reader byte64 = board byte236; setup записує1.
- reader DWORD0 = shared-memory ARM base; це ще не fromDSP header.
- context+224 → fromDSP header; context+240 → records = header+8.
- queue+16 — source; queue+40 — pending receive.

`C8010B20` — шість BSS слів/прапорців, **не** MSG context root.
Реальний reader byte64, runtime shared mapping і queue routing ще
не виміряні. До pointer traversal потрібні live root provenance,
identity, allocation/mapping bounds і lifetime; числового kernel range
самого по собі недостатньо. Snapshots неатомарні.

## Найновіший локальний розбір — перспективний шлях до root

Ці результати отримані після коміту26d6354. Це статичні observations,
ще не окремий автоматизований audit і не дозвіл виконувати kernel calls.

1. У N95 `memoryaccess.ldd` native object enumeration викликає stub
   `8038F5B0` → kernel `8008CE40`, actual export ordinal251.
   Caller індексує повернений масив контейнерів. У E90 actual ordinal251
   → `80037778`: `ldr r0,[pc,#2308]; bx lr`, literal `80038084` =
   **`C80019D4`**. Це статично знайдений root масиву контейнерів;
   його RAM ще не читали. Назва Kern::Containers виведена з поведінки
   enumeration, а не з symbol table E90.
2. N95 container At stub `8038F590` → `8008D638`, actual ordinal12;
   E90 ordinal12 → `80038290`. Body перевіряє index against count+16,
   потім читає array+20 та array[index]. Індекси типів контейнерів і
   довжина root array ще потребують аудиту; не припускати їх за пам'яттю.
3. E90 PDD export1 → factory entry `803DD8A4`, allocation120 Б.
   Constructor `803DD7D8` встановлює vtable **`803F8380`**.
   Це candidate identity для пошуку factory в правильному контейнері.
   Поля per-processor мають stride32, дві записи. Factory+44 — state/flag,
   **не pointer**; factory+48 — manager allocation68 Б;
   factory+68 — configuration allocation1136 Б.
4. Manager constructor `803E32E8` встановлює word0 magic
   **`434F5250` (PROC)**, не vtable; factory у manager+56,
   processor index у manager+60. Manager+44 → board interface.
5. Manager setup `803E3348`: branch processor0 allocates336 Б,
   constructor `803EFFCC`, додає8 до returned pointer перед store+44.
   Branch processor1 allocates372 Б, constructor `803F3B0C`, інша layout.
   Саме branch0 узгоджується з раніше audited board/common+8 chain.
   Треба простежити повний returned pointer/identity/lifetime перед runtime.

Проміжні local ignored files для дизасемблера:
`out/e90-kernel-code.bin`, `out/e90-kernel-disasm.txt`,
`out/e90-pdd-code.bin`, `out/e90-pdd-disasm.txt`, `out/e90-ldd-code.bin`.
У `out/e90-ldd-disasm.txt` була помилкова adjust-vma803F863C;
реальна base LDD **803F8648**. Цей disasm регенерувати перед використанням.
Authoritative saved ROM: `work/evidence/e90/rom/{ekern.exe,ehwaomap.pdd,ehwa.ldd}`.
N95 ROM: `../eka2l1/data/drives/z/rm-320/sys/bin/`.
Спроба extract memoryaccess з E90 4MiB window не знайшла його;
E90 memoryaccess module не отримано, kernel ordinal mapping читали
безпосередньо з saved E90 ekern export table.

## Наступні дії

1. Завершити offline audit container root: length/type/index, headers,
   array bounds, factory identity і chain manager→board→context.
   Перевірити instruction signatures і module hashes відтворюваним script.
2. Спроєктувати bounded read-only snapshot із доведеними root/lifetime
   та mapping bounds. Не форсувати IRQ/DFC і не патчити reader за гіпотезою.
3. Перед runtime перевірити конкретний апарат/PS та зберегти п'ять файлів.
   Після diagnostic — journal GET, clean ownership release, exact restore.
   При невідомому/pending teardown не KILL/free/unload живого owner;
   recovery записати у HELP_NEEDED, physical reboot просити в людини.
4. Лише після нового доказу — MSG/RUN, усунути native delivery/EXITACK,
   виконати D0 три чисті цикли; потім D1 і D2 за повним планом.

## Середовище та перевірки

Корінь: `D:\VsCodeProjects\SymbianProjects\TMS320C55x test`.
PowerShell7; Python3.12:
`C:\Program Files\LibreOffice\program\python.exe` (python/py у PATH відсутні).
Python sys.executable у LibreOffice може вказувати на python-core;
для subprocess явно використовувати wrapper exe за потреби.
SDK і ARM toolchain — сусідні каталоги, TI CGT4.4.1 — на C:;
`tools/env.cmd` їх знаходить. Зовнішні досліди/збірки bounded через
`tools/run_bounded.ps1`, без LAN fallback, кожна гіпотеза має окремий proof.

Останні успішні локальні перевірки:

```powershell
& 'C:\Program Files\LibreOffice\program\python.exe' -m unittest discover -s tools -p test_e90_task_session.py -v
& 'C:\Program Files\LibreOffice\program\python.exe' tools\summarize_arm_message_runtime.py
pwsh -NoProfile -File tools\check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

Git потребує per-command safe.directory через ownership різних Windows users:
`git -c safe.directory='D:/VsCodeProjects/SymbianProjects/TMS320C55x test' ...`.
Чужі початкові правки збережені окремо: modified
`docs/APPLICATION_CANDIDATES.md`, untracked `work/CODEX_TASK_2026-10-01.md`.
Їх не скидати й не включати випадково у власні коміти.

## Класифікатор безпеки

Перший git push був відхилений auto-review через непідтверджений дозвіл
експорту коду/апаратних журналів до GitHub. Користувач явно дозволив
надіслати коміти; після цього push завершився і remote HEAD звірено.
Останні інструкції середовища: danger-full-access, network enabled,
approval policy never; `sandbox_permissions` у commands не передавати.
Це не скасовує апаратну дисципліну й вимоги довести pointer provenance.
Нових видимих tool rejections після дозволу не було; користувач
повідомив про скаргу класифікатора без нового конкретного тексту.

Чутливий механізм diagnostic: control105 `patcher.ldd` копіює source
memory до destination. У доведеному host29 diagnostic destination
була власна RAM процесу; kernel code/PRCM не записувалися.
Новий runtime traversal не реалізований і не запускався.
