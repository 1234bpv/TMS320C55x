# TMS320C55x на N95 8GB: що встановлено (стартовий збір)

Історичний збір і хронологія. Поточні висновки2026-10-01:
`WSOLA.md`, `STREAM_RESEARCH.md`, `../work/FINAL_AUDIT.md`.
Номінальні220MHz, загальна оцінка audio coexistence і ранні lifecycle
припущення нижче не є підтвердженням сучасного per-packet або audio виміру.

> Дисципліна доказів як у SymbianOverclock: кожен пункт або **підтверджений на
> апараті**, або **виведений з коду ROM / офіційного даташита**, або позначений
> як **ГІПОТЕЗА**. Джерела — у дужках. Дата збору: 2026-08-09.

## 1. Що це за DSP і де він у SoC

- Апарат: **Nokia N95 8GB (RM-320)**, SoC **TI OMAP 2420**. Той самий апарат і
  ROM-дамп, що в сусідньому проєкті SymbianOverclock
  (`../eka2l1/data/drives/z/rm-320/`).
- OMAP2420 містить: **ARM1136** (штатно 330 МГц), **TMS320C55x DSP** (штатно
  ~220 МГц) і окремий блок **IVA** (Imaging & Video Accelerator — власний
  ARM7 + копроцесори). C55x і IVA — **два різні** обчислювачі. (веб: TI/OMAP
  огляди, Wikipedia OMAP.)
- Локальні даташити в папці — **загальні** TI-мануали на ядро C55x:
  `TMS320C55x overview.pdf` = SPRU312 (functional overview),
  `TMS320C55x programming.pdf` = набір команд/програмування. Вони описують
  **саме ядро** (CPU, EMIF, EHPI, DMA, DPLL, IDLE-домени, bootloader у ROM),
  але **не** інтеграцію в OMAP2420 (мапінг у SoC, mailbox, DSP MMU, PRCM).
  Інтеграційну частину дає **OMAP2420 Multimedia Processor TRM** — його треба
  дістати окремо (див. план, Фаза 0).

## 2. Апаратний mailbox ARM↔DSP (підтверджено з mainline Linux DT)

- Блок **MAILBOX** OMAP2420: фізична база **`0x48094000`**, розмір `0x200`,
  переривання **26 і 34**. (kernel `omap2420.dtsi`, `ti,omap2-mailbox`.)
- 4 користувачі / 6 FIFO. Розподіл каналів:
  - **DSP (C55x):** tx = fifo0, rx = fifo1;
  - **IVA (ARM7):** tx = fifo2, rx = fifo3.
- Регістри mailbox у Linux-драйвері адресуються зі зсувами типу `+0x40/+0x44`
  (MESSAGE), плюс FIFOSTATUS/IRQSTATUS/IRQENABLE — точну карту брати з TRM.
- Наслідок: канал ARM↔DSP апаратно існує і адреса відома. Це база для будь-якого
  шляху доступу.

## 3. Symbian САМ керує цим DSP — у ROM є повний стек (ключовий факт)

DSP на цьому апараті **не порожній і не вимкнений**: прошивка вантажить на нього
власний firmware і використовує для аудіо/мультимедіа. У ROM-дампі
(`.../sys/bin`) знайдено цілий стек:

| Модуль | Роль (з назви; треба підтвердити дизасемблером) |
|---|---|
| `ebridgeutil.ldd` | **kernel-side DSP bridge** — ядерний канал до DSP (аналог TI DSP/BIOS Bridge / Nokia DSP Gateway) |
| `mailboxipc.dll` | IPC через апаратний mailbox (§2) |
| `mrmailboxutils.dll` | обв'язка mailbox |
| `dspmemmapper.dll` | **мапінг пам'яті DSP** у простір ARM |
| `activeadsp.dll` | «Active Audio DSP» — користувацький бік аудіо-DSP |
| `einfoadspplugin.dll`, `idspluginhandler.dll` | плагіни/хендлери DSP |

**Наслідок для стратегії.** Доступ до DSP — це **не** «завантажити порожнє
ядро з нуля», а або (A) співіснувати зі стеком Symbian через `ebridge`/mailbox,
або (B) відібрати DSP у аудіо-підсистеми на час тесту й повернути. Обидва шляхи
залежать від розбору цих модулів (Фаза 1).

## 4. Потенційний примітив: `memoryaccess.ldd`

- У ROM є **`memoryaccess.ldd`** (8532 Б — найбільший з драйверів у списку).
  Ім'я відповідає відомому homebrew-драйверу прямого доступу до пам'яті.
- **Розбіжність, яку треба з'ясувати:** інвентаризація SymbianOverclock (§11
  findings) переліком LDD, що дають MMIO, `memoryaccess.ldd` **не назвала**
  (там були лише `d_display`, `d_powerapi`, `custom`, `secldd`, `sosadlserver`,
  `xbus`) — бо шукала імпорт kaomap-примітивів, а цей драйвер може мапити
  пам'ять сам. Якщо `memoryaccess.ldd` дає user-side Read/Write за фізичною
  адресою правильної розрядності — це **значно простіший** примітив, ніж весь
  ланцюг patcher.ldd, і корисний обом проєктам. **Пріоритет розбору.**

## 5. Що вже є готового (успадковано від сусідніх проєктів)

- **Канал доставки:** `SymbianDeployDaemon` — залив `.exe` по WiFi, запуск,
  забір логу (`tools/deploy_net.ps1`). Апарат dev-unlocked (Install Server).
- **Kernel-mode примітиви (SymbianOverclock §18), без Kernel DevKit:**
  1. читання довільної адреси ядра (ROM-shadow патч `dvfs_interface.ldd`
     `DoControl(1)`);
  2. **виконання довільного коду ядра** (той самий патч, `bx r1`) — це і є
     універсальний важіль для будь-якого MMIO (PRCM, CONTROL, DSP MMU, mailbox);
  3. SRAM-плацдарм поза SDRAM (фіз. `0x4029E000`, лін. на апараті `0xCB202000`).
- **kaomap-примітиви** Read32/Write32/Modify32 (мапінг MMIO `фіз+0x7E000000`
  для вікна `0x48xxxxxx`) — вікно `0x48094000` mailbox лягає сюди.
- **ROM-дамп** усього апарата в `../eka2l1/data/drives/z/rm-320/` — джерело для
  дизасемблювання (`objdump -D -b binary -m arm --adjust-vma=<iCodeAddress>`
  після зняття 120-байтового `TRomImageHeader`).
- **Розтиснення ROM-E32:** `../SymbianOverclock/tools/syminflate.js` (власний
  Symbian-inflate) — на випадок стиснених модулів DSP-стеку.

## 6. Обмеження й ризики (відомі наперед)

- **Немає Kernel DevKit** → власний LDD зібрати нічим; або чужі драйвери, або
  примітив exec-коду ядра (§5).
- **DSP зайнятий аудіо-підсистемою.** Відбір DSP може зламати звук; треба
  коректно зупиняти/відновлювати або співіснувати. Тест не має лишати апарат у
  стані, де звук мертвий до ребута.
- **C55x — 16-бітний fixed-point DSP.** Плаваючої точки апаратно немає (емуляція).
  Чесний бенчмарк — fixed-point/dual-MAC (FIR, dot-product, блочний FFT) плюс
  контрольний цілочисловий; порівняння «DSP vs ARM» має бути на класі задач, де
  DSP створений сяяти, і окремо на нейтральному коді. (SPRU312.)
- **Когерентність shared memory / DSP MMU / кеш** — окрема морока (dspmemmapper).
- **Токсичне правило сусіда:** нічого у флеш, усе рантаймове, ребут повертає
  апарат як був; не повторювати те саме після двох невдач.

## 7. Відкриті питання (входять у план як задачі)

1. Чи дає `ebridge`/`activeadsp` **завантаження довільного коду** на DSP, чи
   лише фіксовані аудіо-вузли? (Фаза 1)
2. Чи `memoryaccess.ldd` — готовий user-side MMIO-примітив? (Фаза 1)
3. Точна карта регістрів: PRCM DSP-домен (clock/reset), CONTROL IVA/DSP boot,
   DSP MMU, mailbox — з OMAP2420 TRM. (Фаза 0)
4. Toolchain для C55x: TI `cl55`/CCS чи відкритий — і формат сирого образу +
   boot-вектор DSP. (Фаза 0)
5. Як Symbian **вантажить** DSP-firmware на буті — щоб повторити механізм або
   акуратно поставити паузу. (Фаза 1)

## 8. Карта регістрів OMAP2420 (Крок 1 — виведено з коду; TRM недоступний)

> **TRM статус:** OMAP2420 Multimedia Processor TRM = **SWPU064** (rev D),
> документ WTBU/NDA — публічного PDF немає (`ti.com/lit/.../swpu064d.pdf` → 404,
> `web.archive.org` заблоковано в середовищі). Тому карта нижче **виведена з
> mainline Linux** (`arch/arm/mach-omap2`, `plat-omap`, теги v3.2/v3.10), який
> TI-код прямо цитує як відповідник SWPU064. Кожна адреса має джерело-файл;
> позначки розрядності — 32-біт доступ (урок сусіда §10).

### 8.1. Фізичні бази (з `plat/omap24xx.h`)

| Блок | Макрос | Фіз. адреса | У kaomap-вікні `0x48xxxxxx`? |
|---|---|---|---|
| L4-core / **CONTROL(SCM)** | `OMAP242X_CTRL_BASE` = `L4_24XX_BASE` | `0x48000000` | так |
| **PRCM** (PRM=CM, аліас) | `OMAP2420_PRCM_BASE` | `0x48008000` | так |
| **Mailbox** | `OMAP24XX_MAILBOX_BASE` | `0x48094000` | так |
| DSP-порт **пам'яті** (з L3) | `OMAP2420_DSP_MEM_BASE` | `0x58000000` | **НІ** |
| DSP **IPI** | `OMAP2420_DSP_IPI_BASE` | `0x59000000` | **НІ** |
| DSP **MMU** | `OMAP2420_DSP_MMU_BASE` | `0x5A000000` | **НІ** |

**Наслідок для примітивів:** PRCM/CONTROL/mailbox лягають у kaomap-вікно сусіда
(`фіз+0x7E000000`) → доступні наявним Read32/Write32/Modify32. А **DSP-пам'ять,
IPI і MMU (`0x58/0x59/0x5A`) — поза цим вікном**; для Шляху B під них треба
окремий мапінг (свій kaomap-діапазон або `memoryaccess.ldd`, якщо він мапить
довільну фіз. адресу). Це нова, конкретна вимога до Фази 1.

### 8.2. DSP-домен у PRCM (база `0x48008000` + `OMAP24XX_DSP_MOD` `0x800` = `0x48008800`)

Зсуви CM/PRM у межах домену — з `cm2xxx_3xxx.h` / `prm2xxx.h`:

| Регістр | Зсув | Абс. адреса | Призначення |
|---|---|---|---|
| `CM_FCLKEN_DSP` | `+0x00` | `0x48008800` | функц. клок DSP |
| `CM_ICLKEN_DSP` | `+0x10` | `0x48008810` | інтерфейс. клок DSP |
| `CM_IDLEST_DSP` | `+0x20` | `0x48008820` | статус idle (чи піднявся) |
| `CM_AUTOIDLE_DSP` | `+0x30` | `0x48008830` | автоidle |
| `CM_CLKSEL_DSP` | `+0x40` | `0x48008840` | дільник частоти DSP |
| `CM_CLKSTCTRL_DSP` | `+0x48` | `0x48008848` | контроль clock-домену |
| `RM_RSTCTRL_DSP` | `+0x50` | `0x48008850` | **reset DSP** |
| `RM_RSTST_DSP` | `+0x58` | `0x48008858` | статус reset |
| `PM_PWSTCTRL_DSP` | `+0xE0` | `0x480088E0` | контроль power-стану |
| `PM_PWSTST_DSP` | `+0xE4` | `0x480088E4` | статус power-стану |
| `PRCM_IRQSTATUS_DSP` | `+0xF0` | `0x480088F0` | IRQ-статус домену |
| `PRCM_IRQENABLE_DSP` | `+0xF4` | `0x480088F4` | IRQ-enable домену |

**`RM_RSTCTRL_DSP` біти (з hwmod-reset-lines 2420):** біт 0 = **logic reset**
(ядро DSP), біт 1 = **MMU reset**. Це і є важіль зняти/повернути DSP у Шляху B.

### 8.3. DSP boot на 2420 — НЕ через CONTROL boot-addr

Важливо: `omap_ctrl_write_dsp_boot_addr()` у ядрі має гілки лише для
**243x/34xx/44xx** (регістри `CONTROL_IVA2_BOOTADDR/BOOTMOD`) — для **2420 гілки
нема**. Тобто C55x на 2420 стартує **не** із CONTROL-регістра boot-адреси, як
пізніші C64x/IVA2, а через **reset-вектор C55x + DSP MMU** (класична C55x-схема,
SPRU312). Це прямо формує механізм Шляху B і відрізняє наш чип від 2430+.

### 8.4. Mailbox (уточнення до §2)

База `0x48094000`; DSP: tx=fifo0, rx=fifo1; IRQ 26 (DSP), 34 (IVA) —
підтверджено з hwmod-даних 2420. Повна карта MESSAGE/FIFOSTATUS/IRQ регістрів —
з omap2-mailbox драйвера (Фаза 1, разом з реверсом `mailboxipc.dll`).

**Відкрите, що Крок 1 закрив:** пункт 3 «відкритих питань» (карта PRCM/CONTROL/
MMU/mailbox) — по PRCM/CONTROL/mailbox закрито адресами вище; лишається лише
**внутрішня** карта DSP MMU (TLB/CAM/RAM) — її брати з omap-iommu (Фаза 1).

## 9. Реверс `memoryaccess.ldd` і `ebridgeutil.ldd` (Крок 2)

Метод: `SymbianOverclock/tools/romtool.ps1` (зняти 120-Б `TRomImageHeader`,
`objdump --adjust-vma=iCodeAddress`, резольв import-стубів проти `ekern.exe`).
Артефакти: `SymbianOverclock/out/asm/{memoryaccess,ebridgeutil}.ldd.asm`.

### 9.1. `memoryaccess.ldd` — драйвер об'єктів для таск-менеджера, НЕ MMIO

- Заголовок: iCodeAddress `0x8038D848`, code `8524` Б, 1 export, **59 import-
  стубів** з `ekern.exe`.
- Клас `DMemoryAccess`, ім'я драйвера **`MemoryAccess`/`MemAccess`**; підпис у
  коді: *«Checked by MEMORYACCESS.LDD (Memory Access for Task Managers)»*.
- `DoControl` — **jump-table на 17 команд** (`cmp r4,#16; addls pc,pc,r4,lsl#2`
  на `0x8038EA1C`), не 4. Лог-рядки називають лише 4: `EControlGetObjectInfo`,
  `GetObjectInfoByPtr`, `GetObjectInfoByHandle`, `ObjectDie`.
- **Реверс обробників (семпл idx1 `0x8038E7EC`, idx5 `0x8038E44C`):** кожен
  алокує буфер (0x1280 / 0x2240 Б), викликає внутрішній resolver і **копіює
  метадані kernel-об'єкта** (поля DThread/DProcess за фіксованими зсувами +0x20/
  +0x24/+0x5C/+0x68/+0xB4…, перелік до **1024** code-сегментів) у user-буфер.
  Тобто це **інтроспекція об'єктів** (+ `ObjectDie` = вбивство процесу/потоку),
  а **не** довільний R/W за адресою.
- **Висновок:** цей ROM-`memoryaccess.ldd` — homebrew-**лінія MemoryAccess**, але
  зібраний як **енумератор/кілер kernel-об'єктів для таск-менеджера**. Довільного
  фіз./kernel Read/Write (як у повного homebrew-варіанта) серед семпльованих
  команд **немає**. Це **знімає розбіжність §4 на користь §11 сусіда**: драйвер
  цитувати як MMIO-примітив **не можна**. (Застереження: семпльовано частину з
  17 обробників; повний перелік — низький пріоритет, бо і призначення, і
  сигнатура вказують на об'єкти. Плюс драйвер Nokia-підписаний і, найпевніше,
  capability-gated — окреме питання, чи наш exe взагалі його відкриє.)
- **Наслідок для гейта:** ярлика-MMIO немає → Шлях B для вікна `0x48xxxxxx`
  (PRCM/mailbox) спирається на успадкований exec-примітив ядра (§5), а під
  `0x58/0x5A` (DSP-пам'ять/MMU) все одно треба окреме рішення.

### 9.2. `ebridgeutil.ldd` — kernel-помічник пам'яті DSP-моста (повністю розібрано)

- Заголовок: iCodeAddress `0x801B5888`, code `1252` Б, 1 export, 26 імпортів.
  Клас `DBridgeUtilDevice` (+ `DBridgeUtilChannel`), ім'я **`BridgeUtil`**.
  Це **тонкий** util, не важкий міст.
- Канальний DoControl (`0x801B5AA4`) — лише **2 команди**:
  - **fn 1** (`0x801B5AE4`): бере {лінійна адреса, розмір} з user, посторінково
    (крок 4 КБ) кличе `ekern +0xE718` (**Epoc::LinearToPhysical**) і будує
    таблицю пар **{лінійна сторінка, фіз. сторінка}** назад у user-буфер —
    scatter-list фіз. адрес буфера для передачі DSP.
  - **fn 2** (`0x801B5AC4`): два виклики `ekern +0x943C` / `+0x944C` з (addr,len)
    — **cache clean/flush** (DMA-синхронізація).
  - інші коди → рядок *«!!!!!!!! Not supported !!!!!!!!»*.
- **Висновок:** DSP-shared-буфери адресуються **фізично** з **ручним керуванням
  кешем** — критично для когерентності у Фазах 2–3. `ebridgeutil.ldd` коду на DSP
  **не вантажить**; це перетворення адрес сторінок і cache utility для моста.
  Виклику pin/unpin API в fn1 немає; lifetime/pinning native chunk ще треба
  підтвердити. [Аудит N95/E90 2026-10-03](DMM_ABI_2026-10-03.md).

### 9.3. Справжній DSP-міст — `bridgeapi.dll` (наступна ціль)

У ROM (`sys/bin`) знайдено повний bridge-стек; за розміром і назвою це
**TI DSP/BIOS Bridge (dspbridge)**:

| Модуль | Розмір | Роль |
|---|---|---|
| **`bridgeapi.dll`** | **20544** | **user-side DSP Bridge API** — тут очікуються `Processor_Load`/`Node_Create`/`Node_Run` (завантаження COFF-вузла на DSP) |
| `mrmailboxutils.dll` | 5200 | mailbox-утиліти |
| `mailboxipc.dll` | 3748 | IPC через апаратний mailbox |
| `idspluginhandler.dll` | 5268 | хендлер DSP-плагінів |
| `activeadsp.dll` | 4128 | Active Audio DSP (клієнт) |
| `dspmemmapper.dll` | 1336 | user-обгортка над `ebridgeutil` (мапінг DSP-пам'яті) |
| `bridgecfg.dll` | 1228 | конфіг моста |
| `einfoadspplugin.dll` | 608 | аудіо-плагін |

**Наслідок для ГЕЙТА A/B:** якщо `bridgeapi.dll` експонує завантаження вузла —
Шлях A різко привабливіший: міст уже вирішує найважче (load коду, DSP MMU, cache,
mailbox-протокол). Тому **найвища за цінністю наступна ціль — реверс
`bridgeapi.dll`** (шукати експорти Processor/Node Load/Create/Run і формат
COFF-образу вузла).

## 10. `bridgeapi.dll` = TI DSP/BIOS Bridge — динамічний завантажувач DOFF (Крок 2, продовження)

Заголовок: iCodeAddress `0x80A5D458`, code `0x5040`, iUid3 `0x10006914`,
**39 експортів** (`iExportDir=0x80A6192C`). Імпорти: `euser.dll`, **`efsrv.dll`**
(файловий сервер — читає образи вузлів з диска), `drtaeabi.dll`, `scppnwdl.dll`.

**Ідентифікація за рядками — однозначна.** Це порт **TI DSP/BIOS Bridge**
(dspbridge) із вбудованим **динамічним лоадером DOFF/COFF** (DLOAD):

- Драйвер: `Open UTIL Driver: %d`, `utilDrv.LinearToPhysical: %d`,
  `utilDrv.FlushDataCache` → відкриває **BridgeUtil = `ebridgeutil.ldd`** і
  користає саме fn1/fn2 з §9.2 (підтвердження перехресне).
- DOFF-лоадер: `Bad DOFF version 0x%x`, `Bad target ID 0x%x`, `Bad coff operator
  0x%x`, `Expression stack overflow`, `Relocation value 0x%x overflows %d bits`,
  `Undefined external symbol %s`, `Symbol table addition failed`,
  `Target memory allocate failed, section %s size 0x%x`, `%s to target address
  0x%x failed`, `Write to 0x%x failed`, секції `.cinit`, `.dllview`,
  `.dcd_register`, `.dspbridge_deplibs`.
- Вузли/DCD: `BridgeDcdSync`, `*BridgeDcdSync*`, GUID-форматтер
  `%08X_%04X_%04x_%02x…` → **вузли DSP ідентифікуються UUID і реєструються в DCD**
  (DSP/BIOS Configuration Database). `Hwa.Omap`, `__DLModules`.

**Механізм виконання коду на DSP (класичний dspbridge):** DSP-програма = **DOFF-
образ вузла** (створений TI-toolchain, з фазами create/execute/delete й UUID);
лоадер парсить DOFF, робить релокації, алокує пам'ять DSP, пише секції в адресний
простір DSP (через BridgeUtil LinearToPhysical + DSP MMU + mailbox), реєструє
вузол у DCD; далі node-API запускає вузол і обмінюється повідомленнями/потоками.

**Export-мапа (ординал → адреса; імена в ROM відсутні — C++-клас, пари aliased):**
`1→0x80A5E483 2→0x80A5E539 3→0x80A5E68F 4→0x80A5E6BB 5→0x80A5E561 6→0x80A5E585
7→0x80A5E677 8→0x80A5E4DF 9→0x80A5E43F 10→0x80A5E409 11/12→0x80A5E401
13/14→0x80A5E433 15→0x80A5DC71 16→0x80A5DC37 17→0x80A5DCDB 18→0x80A5DCA1
19→0x80A5DD0B 20→0x80A5DD1B 21/22→0x80A5DC2D 23/24→0x80A5DC35 25→0x80A5DAE1
26→0x80A5D533 27→0x80A5D9B1 28→0x80A5DAC3 29→0x80A5D901 30→0x80A5D87F
31→0x80A5D9ED 32→0x80A5D751 33→0x80A5D4FD 34→0x80A5DAA3 35→0x80A5D955
36/37→0x80A5D4C9 38/39→0x80A5D4D9` (`bridgeapi.dll.asm` в `out/asm/`).
Прив'язку ординалів до імен API робити у Фазі 2 (за лог-рядками кожної функції +
експерименти на апараті).

## 11. ГЕЙТ РІШЕННЯ A vs B — вирішено (з доказів Кроків 1–2)

| | **Шлях A — вузол через `bridgeapi.dll`** | **Шлях B — керований відбір DSP** |
|---|---|---|
| Механізм | зібрати власний DOFF-вузол з UUID, зареєструвати в DCD, вантажити через bridge, гнати node-повідомлення | загейтити DSP-домен (§8), map `0x58/0x5A`, зупинити/reset DSP, залити сирий C55x-блоб, reset-вектор, пуск, читання результату |
| Апаратний ризик | **низький** — reset DSP не потрібен, співіснування з аудіо | **вищий** — вбиває DSP/BIOS-аудіо до ребута (прийнятно за правилами) |
| Що вже маємо | export-мапа, підтверджений mem/cache-механізм | **повну карту регістрів (§8)**, kernel exec-примітив, reset-біти `RM_RSTCTRL_DSP` |
| Чистота бенчмарку | гірша — накладні DSP/BIOS + node-IPC | **краща** — прямий цикл-каунт без RTOS |
| Toolchain | TI cl55 **+ dspbridge node SDK + DCD-реєстрація** | TI cl55 (лише сирий asm/лінк) |
| Головний блокер | **DCD на роздрібному апараті може бути фіксований у ROM** (чи можна додати новий UUID динамічно — невідомо); реверс 39-export API | точний **reset-вектор C55x на 2420** (внутрішня DSP MMU — з omap-iommu, Фаза 1) |

**Рішення: почати зі Шляху B.** Причини: (1) toolchain легший — лише сирий C55x-
асемблер, без node-SDK і без невизначеної DCD-реєстрації; (2) чистіший вимір
(ціль проєкту — бенчмарк); (3) майже всі примітиви вже наші (лишається мапінг
`0x58/0x5A` — тривіально через kernel exec-примітив, і reset-вектор — Фаза 1);
(4) повний контроль = плацдарм для будь-яких DSP-проєктів. Шлях A лишаємо як
пізніший «продакшн-варіант співіснування», коли базу доведено.

**СПІЛЬНИЙ БЛОКЕР обох шляхів — C55x code-gen.** Відкритого зрілого асемблера
C55x немає (naken_asm та ін. C55x не підтримують). Потрібен **TI C5500 Code
Generation Tools (`cl55`)** — безкоштовний, але пропрієтарний; входить у Code
Composer Studio або окремим пакетом. Його встановлення — крок, що потребує
користувача (ліцензія-клік, можливий TI-логін на завантаженні).

## 12. На апараті лежить повний набір sample-вузлів dspbridge (ПЕРЕГЛЯД ГЕЙТА → Шлях A)

Скан Z: знайшов готові **DOFF-образи C55x-вузлів** і базу DSP/BIOS:

| Файл | Розмір | Що це |
|---|---|---|
| `resource/plugins/baseimage.dof` | 155756 | **Nokia аудіо-база DSP/BIOS** (== `dynbase.dof55l`): `COMMON_NOKIA_eCntr`, `SRC_TII_FILTER` (SRC), EAP, `.dman` (динамічний лоадер на DSP), `.bridge`, DARAM/SARAM/SHMSEG heaps |
| `system/apps/ping/Ping.dof55l` | 51268 | **PING-вузол** (статичний), TI-семпл |
| `system/apps/ping/pingdyn.dll55l` | 4092 | **PING-вузол динамічний** — доказ runtime-завантаження |
| `system/apps/{scale,dmmcopy,strmcopy}/*.dof55l` | — | стандартні семпли dspbridge (scale/dmmcopy/strmcopy) |
| `system/data/Iva_base.dof` | — | база для IVA (окремий копроцесор) |

**Формат DOFF підтверджено:** заголовок Ping — `... 03 02 01 00 ...` (DOFF
byte-order magic, саме те, що перевіряє bridgeapi §10). Секції: `.text .cinit
.bios .bridge .sysinit .dcd_register .dspbridge_symbols`.

**UUID вузлів (з `.dcd_register`):**
- **PING = `12A3C3C1-D015-11D4-9F69-00C04F3A59AE`** (той самий у Ping.dof55l і
  pingdyn.dll55l); фази `_PING_TI_create/execute/delete`, обмін
  `_NODE_putMsg/getMsg`.
- **RMS (Resource Manager Server) = `93FA56D0-6FE5-11D4-B747-006008BDB66F`** —
  стандартний dspbridge RMS; присутній і в базі, і в ping (приймає node-команди
  через mailbox).

### ГЕЙТ ПЕРЕГЛЯНУТО: Шлях A (нові докази переважують)

Рішення §11 (Шлях B) ухвалене ДО знахідки цих семплів. Нові докази:
1. **Динамічне завантаження вузлів доведено робочим на пристрої** (`pingdyn.dll55l`
   + `.dman` у базі) — головний сумнів Шляху A (чи закрита DCD) знято: реєстрація
   динамічна.
2. На апараті є **готові DOFF-семпли** — і шаблон для власного вузла, і мішень для
   першого запуску.
3. Шлях A не чіпає reset DSP → **аудіо не ламається**, менший ризик.

**Новий план:**
- **Milestone 1 «Hello, DSP» — БЕЗ toolchain:** тригернути існуючий **PING-вузол**
  (UUID `12A3C3C1…`) через `bridgeapi.dll` → allocate/create/run + node-ping-
  повідомлення → доказ виконання коду на DSP. cl55 тут НЕ потрібен.
- **Milestone 2 «Бенчмарк»:** зібрати власний C55x-вузол з Q15-ядрами (шаблон —
  ping/pingdyn) — тут уже потрібен **cl55** (+ node-SDK/DCD-опис).

**Наслідок для `cl55`:** для Milestone 1 toolchain НЕ потрібен → можна робити
прогрес автономно (реверс node-load API у `bridgeapi.dll`). `cl55` стає потрібен
лише на Milestone 2.

**Лишається розібрати (Milestone 1):** прив'язка 39 експортів `bridgeapi.dll` до
послідовності attach-processor → node-allocate(UUID) → node-create → node-run →
put/get-msg; і хто на ARM-боці штатно драйвить міст (ймовірно `activeadsp.dll` —
прямих import-стубів у ROM не видно через IAT-лінкування XIP, не через
`E51FF004`).

## 13. TI C5500 CGT встановлено і валідовано на нашому коді (2026-08-09)

- Встановлено: `C:\Program Files (x86)\Texas Instruments\C5500 Code Generation
  Tools 4.4.1\bin\` — cl55/asm55/lnk55/ar55/hex55 + **dis55, ofd55, nm55**.
- **Формат виходу підтверджено правильним:** `ofd55` на тест-`.obj` →
  **«TI-COFF Version 2, Machine: TI C55x»**, memory model small, calling
  c55_std. Саме це очікує DOFF-лоадер `bridgeapi.dll` (§10).
- **Наші 3 бенчмарк-ядра компілюються оптимально** (`src/dsp/bench_dsp.c`,
  `cl55 -v5510 -o3`):
  - `dsp_q15_dot` → `RPT CSR` + `MACM *AR1+,*AR0+,AC0,AC0` (1 MAC/такт у 40-біт AC);
  - `dsp_q15_fir` → `RPTBLOCAL` (по відліках) + вкладений `RPT CSR; MACM` (по taps);
  - `dsp_blk` → `RPTBLOCAL; MPYMK *AR0+,#3,AC1` (нейтральний).
- **`ofd55`/`dis55` НЕ читають `.dll55l`/`.dof55l`** («failed to read») — це DOFF,
  не сирий COFF. Підтверджує: конвертація COFF→DOFF робиться **окремою утилітою
  dspbridge** (не в базовому CGT).

**Стан Milestone 2:** компіляція/асемблювання/лінк C55x — **готово**. Лишилось
одне: **dspbridge dsp-side пакет** (утиліта COFF→DOFF + node-обгортка/headers +
за потреби DSP/BIOS) — щоб загорнути `bench_dsp.obj` у `.dll55l`-вузол (легший
динамічний варіант, як `pingdyn`, лінкується проти символів бази — без повного
BIOS). C55x-типи-пастка: на C55x `int`=16 біт, `long`=32, AC=40 — ядра написані з
урахуванням (лічильники 16-біт ок для n≤8192, акумулятор `long`).

## 14. DSP-вузол зібрано до relocatable COFF; ARM-API-контракт зафіксовано (2026-08-09)

### 14.1. ARM-side node-load API (з `felipec/dsp-dummy` dsp_bridge.h — аналог bridgeapi)

Відкритий Linux-аналог `bridgeapi.dll`. Канонічна послідовність (те, що наш
ARM-завантажувач має відтворити через 39 експортів bridgeapi — «ключ» до
Milestone 1):
```
h = dsp_open()                        # /dev/DspBridge <-> RBusLogicalChannel
dsp_attach(h, 0)                      # приєднатися до DSP-процесора
dsp_reserve(h, size) + dsp_map(...)   # DMM: замапити ARM-буфери у простір DSP
dsp_node_allocate(h, proc, &UUID)     # алокувати вузол за UUID
dsp_node_create(h, node)
dsp_node_run(h, node)
dsp_node_put_message / get_message    # обмін {cmd,arg_1,arg_2}
dsp_node_terminate(h) / dsp_node_free / dsp_detach / dsp_close
```
Плюс `dsp_flush/dsp_invalidate` (кеш ARM-боку), `dsp_register_notify`,
`dsp_enum`, `dsp_register` (динамічна DCD-реєстрація вузла). Ці ~30 операцій
відповідають 39 ординалам bridgeapi (пари aliased = const/non-const).

### 14.2. Модель вузла (шаблон dsp-dummy + Ping)

Три фази `create/execute/delete`; `execute(env)` крутить `NODE_getMsg` → обробка
cmd → `NODE_putMsg`; повідомлення `{cmd,arg_1,arg_2}` (3×32-біт); кеш на DSP —
`BCACHE_inv` (перед читанням) / `BCACHE_wbInv` (після запису).

### 14.3. Наш вузол зібрано (крім DOFF)

`src/dsp/bench_node.c` + `node.h` + `bench_dsp.c` → `cl55 -v5510 -o3
--mem_model:data=large -c` → `lnk55 -r -cr` → **`bench.x55` = TI-COFF v2,
TI C55x, relocatable** (`tools/build_dsp_node.cmd`). Символи:
- **T (визначені нами):** `_bench_create/_delete/_execute`, `_dsp_q15_dot/_fir`,
  `_dsp_blk`;
- **U (резолвляться базою при DOFF-load):** `_NODE_getMsg/putMsg`,
  `_BCACHE_inv/wbInv` — рівно як у `pingdyn`.

### 14.4. DOFF-блокер ЗНЯТО — повний DSP-білд на Windows (2026-08-09)

`doffbuild` (з **`dllcreate.exe` — PE32 Windows**, не лише Linux `DLLcreate`)
витягнуто з `bridge-tools.tar` у репо **`kpykc/userspace-dspbridge`** (дзеркало
dev.omapzoom.org tidspbridge). Встановлено в
`toolchain\ti\dspbridge\dsp\doffbuild`. Є також `DLLdump.exe`, `dbsymgen.exe`,
`dynmap.exe`.

**Весь ланцюг працює нативно на Windows** (Linux-VM НЕ потрібна):
`cl55 -c` → `lnk55 -r -cr` → `dllcreate.exe bench.x55 -o=bench.dll55l`. Одна
команда `tools\build_dsp_node.cmd` → **`out/dsp/bench.dll55l`** (7672 Б).
Верифікація: `DLLdump.exe` → «Verifying Sections.. PASSED»; заголовок збігається
з еталонним `pingdyn.dll55l` (DOFF magic `03 02 01 00` на зсуві 8). Зауваги:
`-o=` передавати через cmd/bat (PowerShell маглить `=`); дужки в `echo` всередині
`if()`-блоку батника ламають потік (використано `goto`).

**Стан Milestone 2 DSP-боку: ГОТОВО** — власний вузол збирається з коду у
завантажуваний DOFF. Лишилось (потребує апарата): (1) призначити вузлу **UUID +
DCD-запис** (наш мінімальний вузол ще без DCD-об'єкта — треба `.dcd_register` з
UUID, як у ping) — **зроблено, §15**; (2) **ARM-завантажувач** у `dsptest.exe` —
драйвити `bridgeapi.dll` за контрактом §14.1 (allocate/create/run/msg);
(3) прогін на N95.

## 15. Формат DCD розкодовано; наш вузол зареєстровано під власним UUID (2026-08-10)

Метод: `DLLdump.exe` (doffbuild) на еталонних вузлах з ROM + прямий розбір
секцій DOFF. Рядки в DOFF-секціях C55x лежать **по одному символу на 16-бітне
слово** (`00 XX`, big-endian) — звідси скрипт вибірки.

### 15.1. Дві секції, які роблять вузол видимим

DOFF-вузол реєструється двома **неалокованими** секціями (DOFF-прапорці
`0x101`: «no space allocation / no download» — їх читає ARM-бік з файла, на DSP
вони не потрапляють):

| Секція | Вміст |
|---|---|
| `.dcd_register` | індекс: `"<UUID_з_підкресленнями>:<тип>,"` для кожного об'єкта; **тип 0 = вузол, 1 = процесор/RMS** |
| `.<UUID_з_підкресленнями>` | сам об'єкт: 31 поле через кому |

Приклад-еталон (`pcmdll.dll55L`, 5896 Б — найменший **виробничий** вузол Nokia,
саме він узятий за шаблон): `.dcd_register` = 39 символів = `0x4e` байт.
`baseimage.dof` реєструє три об'єкти одним індексом (`EAP_TASK`,
`TESTSERVER_NOKIA` + RMS `93FA56D0…:1`).

### 15.2. Карта 31 поля вузла (виведено з 28 об'єктів у ROM)

Порядок і значення підтверджені перехресно: поле 4 = `02H` рівно у тих вузлах,
що звуться `*SOCKET*` (DAIS-socket) і `01H` у task-вузлах; поле 29 = `0` рівно у
статичних (`Ping.dof55l`, вузли всередині бази) і `1` рівно у динамічних
(`pingdyn`, всі `*_SN.dll55L`).

```
 1 cb_struct=1024      2 UUID              3 ім'я           4 ntype(1=task,2=socket)
 5 cache_on_gpp        6 req.cb_struct     7 staticData     8 globalData
 9 progMem            10 wcExec           11 wcPeriod      12 wcDeadline
13 avgExec            14 minPeriod        15 prio          16 stack
17 sysStack           18 stackSeg         19 msgDepth      20 nIn   21 nOut
22 timeout            23/24/25 create/execute/delete (імена БЕЗ підкреслення)
26 00H  27 08000H     28 algName          29 loadType(0=static,1=dyn)
30 dataMemSegMask     31 codeMemSegMask
```

Поля 7–14 ідентичні в **усіх** 28 об'єктах ROM → копіюються дослівно. Поля 26/27
теж константні всюди; семантику не встановлено (позначено як «копія»).

**Діапазон пріоритетів — з апарата, не з здогаду:** об'єкт RMS
(`93FA56D0…`, тип 1) у `baseimage.dof` дає `node_min_priority=01H`,
`node_max_priority=0fH`, а також `processor_family=0157cH` (**5500**) і
`processor_type=01586H` (**5510**) — незалежне підтвердження, що база зібрана
саме під наш C5510.

**Маски сегментів:** усі вузли Nokia, зібрані під **цю** базу (Aug 2007),
вживають пару `0ff3f3f00H` / `0ff3f3f02H`; TI-семпли `pingdyn`/`scaledyn`
(2006) — `…00H`/`…01H`. Беремо мажоритарну, рідну для апарата.

### 15.3. КРИТИЧНО: у базі NEMA `BCACHE_*` — вузол з ними не завантажився б

Символьну таблицю `baseimage.dof` витягнуто повністю (**1678 символів**,
`DLLdump`). Перевірка кожного extern'а нашого вузла:

| Символ | У базі | Наслідок |
|---|---|---|
| `_NODE_getMsg`, `_NODE_putMsg`, `_c_int00` | так | ок |
| `_BCACHE_inv`, `_BCACHE_wbInv` | **НІ** | «Undefined external symbol» на завантаженні |
| `_CLK_gethtime`, `_CLK_countspms` | так | **новий прилад, див. 15.4** |

`BCACHE` — API DSP/BIOS для **C64x**; ми взяли його з `dsp-dummy` (C64x-орієнтований
семпл, §14.2). На C55x кеш **лише інструкційний** (база експортує
`_ENABLEICACHE` / `_ICache_Flush`, жодного `BCACHE_*`) — кеш **даних** на C55x
відсутній, тому DSP-боку нічого підтримувати; когерентність тримає ARM-бік через
`ebridgeutil` clean/flush (§9.2). Виклики BCACHE прибрано з `node.h`/`bench_node.c`.

Це — приклад того, чому «взяти з аналога» треба звіряти з символами **цієї**
бази, а не з апстрімного семпла.

### 15.4. DSP-бічний прилад часу знайдено (закриває Фазу 3.3)

База експортує `_CLK_gethtime` (лічильник високої роздільності) і
`_CLK_countspms` (тактів цього лічильника на мілісекунду). Вузол тепер міряє
**сам себе** і повертає `ticks` + `countspms` у блоці параметрів — це та сама
«друга незалежна вимірювальна голка», якої вимагає Фаза 4, тепер **на боці DSP**,
незалежно від ARM-ського `User::FastCounter`. Також доступні `_STS_*`,
`_TSK_setpri`, `_GBL_freq`.

### 15.5. Що зроблено в коді

- **UUID вузла: `967CBF11-B90E-4B54-A4D3-3C84249EE1DA`** (v4). Перевірено проти
  **всіх 28** DCD-об'єктів апарата — колізій нема.
- `src/dsp/bench_dcd.s55` — `.dcd_register` + `.<UUID>` + `.dspbridge_symbols`
  вручну (штатно їх генерує tconf з `.cdb`, якого в нас нема; формат — рівно той,
  що `doffbuild/tconf/asmgen.tcf` пише через `.sect`/`.string`).
  `.string` на C55x кладе символ у слово і **не** додає термінатор (це `.cstring`)
  — тому наш `.dcd_register` вийшов `0x4e` байт, байт-у-байт як у `pcmdll`.
- `src/dsp/bench_node.lcf` — три метасекції як `type = COPY`, інакше lnk55 робить
  їх звичайними даними і DLLcreate ставить `0x131` (алокувати + завантажити) —
  ~1.4 КБ ASCII поїхало б у пам'ять DSP.
- Фази перейменовано на `BENCH_DSP_create/execute/delete` (мають збігатися з
  іменами в DCD-записі).
- **Пастка з entries-файлом:** `dllcreate -e bios_entries.ent` **локалізує** всі
  символи, яких не назвав, включно з нашими трьома фазами → RMS не знайшов би їх
  за іменами з DCD. Стоковий entries-файл НЕ використовуємо; `.debug_*` знімаємо
  через `--symdebug:none`.
- **Пастка з asm55:** викликаний напряму, він штампує об'єкт як `Tag_Memory_Model=1`
  (small) і lnk55 відмовляється зліпити його з large-model C-об'єктами. `.s55`
  подається через `cl55` разом із `.c`.

**Верифікація (DLLdump, `out/dsp/bench.dll55l`, 2836 Б):** Headers/Sections/
Symbols — PASSED. Форма збігається з `pcmdll.dll55L`:

| | наш | pcmdll |
|---|---|---|
| `.text` | `0x208`, flags `0x230` | `0xbd3`, flags `0x230` |
| `.dcd_register` | `0x4e`, `0x101` | `0x4e`, `0x101` |
| `.dspbridge_symbols` | `0x326`, `0x101` | `0x338`, `0x101` |
| `.<UUID>` | `0x1e8`, `0x101` | `0x1fa`, `0x101` |

Невизначені зовнішні — рівно 5, усі є в базі: `_NODE_getMsg`, `_NODE_putMsg`,
`_CLK_gethtime`, `_CLK_countspms`, `_c_int00`. Визначені й видимі:
`_BENCH_DSP_create/execute/delete`, `_dsp_q15_dot/_fir`, `_dsp_blk`.
Кодогенерація не постраждала (`dis55`): `RPT CSR; MACM` у dot і FIR, `MPYMK` у BLK.

**Лишається (обидва потребують апарата):** (1) ARM-завантажувач — реверс 39
ординалів `bridgeapi.dll` під контракт §14.1; (2) прогін на N95.

## 16. Реверс ARM-боку: справжня архітектура мосту (2026-08-10)

### 16.1. Головна знахідка: увесь dspbridge живе в ЯДРІ, за LDD `Hwa`

`bridgeapi.dll` — не самодостатній міст. Пошук по ROM за рядком `Hwa.Omap`
(UTF-16 у `bridgeapi`) вивів на пару драйверів, яку попередні кроки не бачили:

| Модуль | Розмір | Роль |
|---|---|---|
| **`ehwa.ldd`** | 6140 | LDD-фасад; реєстроване ім'я каналу — **`Hwa`** |
| **`ehwaomap.pdd`** | 110168 | **весь dspbridge**: DOFF-лоадер, DSP MMU, RMS-протокол, mailbox, живлення |

Доказ із рядків `ehwaomap.pdd`: `RMS_createNode/deleteNode/executeNode/
configureServer`, `RMS_STATUS:NodeCreate/Execute/Suspend/Resume/Delete/
SetPriority`, `*** DSP MMU Fault ***`, `DDspObject::MMUInit, AddDSPMMUEntry
(lp=%d, pa=0x%x, va=0x%x, sz=%d)`, `DSP RESET`, `DYN_DARAM/DYN_SARAM/
DYN_EXTERNAL/DYN_SRAM`, `_BRIDGEINIT_DSP_FREQ`, класи `DBridgePdd`,
`DDspObject`, `DIvaObject`, `DNode`, `DBridgeFactory`.

Рядок з `ehwa.ldd`: **«MultimediaDD capability is checked by DSP Bridge LDD»** →
клієнт мусить мати **MultimediaDD** (додано в `dsptest.mmp`).

**`D32HWA` — це НЕ ім'я каналу**, а внутрішній рядок драйвера: перша проба з
ним дала `KErrNotFound`. Реєстроване ім'я LDD — **`Hwa`** (підтверджено і
`TFindLogicalDevice` на апараті, і літералом у `bridgeapi` @`0x80A61DB8`), PDD —
`Hwa.Omap` (Symbian вимагає префікс «ім'я LDD + крапка» — сходиться).

### 16.2. Структура 39 ординалів виведена, БЕЗ здогадів

Шість ординалів aliased попарно: 11/12, 13/14, 21/22, 23/24, 36/37, 38/39.
В Itanium C++ ABI пари `C1`/`C2` (конструктори) і `D1`/`D2` (деструктори)
компонуються на одну адресу. Кожна пара стоїть **в кінці суцільного блоку
ординалів** → три класи, у кожного {методи…, ctor, ctor, dtor, dtor}:

| Клас | Ординали | Методи | ctor | dtor | Що це |
|---|---|---|---|---|---|
| A | 1–14 | 1–10 | 11/12 | 13/14 | UUID/DCD-об'єкти (TLex-парсинг, `%08X_%04X_…`) |
| B | 15–24 | 15–20 | 21/22 | 23/24 | асинхронні операції (ord 16/18 = `User::WaitForRequest`); ord 20 — 1766 Б розбору дескрипторів |
| C | 25–39 | 25–35 | 36/37 | 38/39 | **процесор/канал**: тримає `RBusLogicalChannel`, файли, чанки |

Порядок ординалів у Symbian — алфавітний за **манґленим** іменем; це
підтверджено незалежно на `euser.dso` (символ із `st_value = (ординал−1)*4`,
імена йдуть строго за абеткою).

**Звірено з апаратом:** `dsptest.exe` витягнув `RLibrary::Lookup(1..39)` наживо
— **усі 39 адрес збіглися з ROM-дампом** біт-у-біт. Тобто дамп = прошивка
апарата, і весь статичний аналіз стоїть на коді, що реально виконується.

### 16.3. Клас C — розібрані сигнатури

- **ord 36/37 ctor** — обнуляє поля 0,4,8,12; ord 32 пише ще й [this+16].
  Об'єкт ≥20 Б; `RBusLogicalChannel` лежить за зсувом **0** (методи euser
  кличуться з `r0 = this`).
- **ord 32 = `TInt Open(TInt aProcId, TInt aFlag, const TAny* aAttrs24)`**
  - `aProcId` перевіряється `cmp #2; bcc` → лише **0 або 1** (інакше −5);
    кладеться в `[this+16]`. Це вибір обчислювача: **0 = C55x DSP, 1 = IVA**.
  - `aAttrs24 != NULL` → копіює 24 Б у щойно виділений блок.
  - `aFlag == 1` → після `DoCreate` будує рядок-шлях і кличе **ord 26**, тобто
    довантажує базовий образ. Для нас це небажано (база вже піднята аудіо).
  - всередині: `TVersion`, `DoCreate`, `operator new(60)`, `DoControl`.
- **ord 26 = завантаження DOFF-файла + DCD-реєстрація**: будує список записів
  по 84 Б, копіюючи в кожен **16 Б UUID** та 32 Б властивостей, далі
  `RFs::Connect` → `RFile::Open` → `RFile::Size` → `DoControl` → `RChunk::Base`.
  Саме цим механізмом реєструється наш вузол.
- **ord 33 = Close/Detach**: звільняє блок [this+12], далі
  `DoControl(0x04000001, this+16, 0)` і `RHandleBase::Close`.
- **Коди DoControl драйвера — база `0x04000001`** (літерал @`0x80A5D8F4`),
  сусідні команди адресуються як база+N (ord 26 вживає `+12` = `0x0400000D`).

### 16.4. Клієнти мосту в ROM (знайдені перехресними посиланнями)

XIP не лишає import-стубів з іменами, тому клієнтів шукано скануванням усього
`sys/bin` на 32-бітні літерали, рівні адресам експортів `bridgeapi`:

| Клієнт | Скільки ординалів | Роль |
|---|---|---|
| **`bal.dll`** (клас **`CBal`**, 30 експортів) | 18 | «Bridge Abstraction Layer»; сам вантажить `EHWAOMAP`/`EHWA`, тримає по одному об'єкту класів A, B, C |
| `dspmemmapper.dll` | 5 (25,27,28,31,34) | мапінг пам'яті |
| `balbuffers.dll` | 2 (29,30) | буфери |

`CBal::NewL` (bal ord 26) → ctor+ConstructL (bal ord 22), а ConstructL
послідовно: `ord10(A)`, `ord33(C)`, `Free/LoadPhysicalDevice("EHWAOMAP")`,
`LoadLogicalDevice("EHWA")`, `ord32(C)`, `ord9(A)`, `ord36/21/11` (ctor'и трьох
членів). Тонкі 1:1-обгортки `CBal` дають прив'язку: bal 11→ap 2, bal 14→ap 19,
bal 15→ap 20, bal 24→ap 35, bal 25→ap 7, bal 1→ap 4, bal 16/17→ap 3.

### 16.5. Інструменти реверсу (у scratchpad, відтворювані)

`xref.py` (пошук клієнтів за літералами й BL/BLX по всьому ROM), `exports.py`
(таблиця експортів XIP: `iExportDirCount` @+0x3C, `iExportDir` @+0x40),
`annotate.py` (дизасемблер Thumb з іменуванням КОЖНОГО імпорту: ROM-таблиця
експортів + `.dso` з SDK дають `модуль::ordN ім'я`), `romstr.py` (8- і 16-бітні
рядки ROM-модуля).

### 16.6. Збірка ARM-боку була зламана — виправлено

`abld` віддає `makmake` шлях **без лапок**, тож пробіл у
`…\TMS320C55x test\group\DSPTEST` розбивав його на два аргументи і makmake
просто друкував довідку; далі йшло невиразне «No rule to make target». Отже
ARM-бік **ніколи не збирався**, попри запис у README. Виправлено junction'ом
без пробілу, який `tools\build.cmd` створює сам.

**Уточнення (пізніше).** Спершу junction лежав поряд із проєктом
(`…\TMS320C55x_test`) і виглядав як другий, дубльований каталог — плутанина,
на яку слушно вказав власник. Тепер він створюється **поза деревом проєктів**
(`D:\symbuild\c55x`) і **знімається одразу після збірки**, тож зайвої теки не
лишається. Диск саме `D:`: `EPOCROOT` заданий без літери диска й резолвиться
відносно поточного, тож із `C:` збірка шукала б SDK не там. Знімати junction
можна **тільки `rmdir` без `/s`** — з `/s` він видалив би файли, на які вказує.

### 16.7. Перший реальний ARM-замір (і перехресна перевірка приладу)

| Ядро | час | MMAC/s | MAC/такт | chk |
|---|---|---|---|---|
| DOT (8192×2000) | 774 мс | 21.2 | 0.065 | `85055090` |
| FIR (4096×32×200) | 1011 мс | 25.9 | 0.080 | `f5735100` |
| BLK (8192×2000) | 908 мс | 18.0 | 0.055 | `22056190` |

**Перевірка приладу:** перший прогін застав апарат на **423 МГц** (залишок
розгону від сусіднього проєкту), після ребута — стокові **324 МГц**. Абсолютні
часи змінилися пропорційно, а **MAC/такт лишився ідентичним до тисячних**
(0.065 / 0.080 / 0.055). Дві різні частоти дали ту саму нормовану цифру — це
незалежне підтвердження, що і `User::FastCounter`, і калібрування `SpinNop`
міряють те, що треба. HAL при цьому вперто каже `ECPUSpeed = 206438 kHz` —
тобто HAL брехливий, а наш прилад ні.

### 16.9. ARM-базова лінія НЕ відтворювана між завантаженнями (пам'ять, не ядро)

Той самий бінарник, та сама виміряна частота ядра — інші числа:

| ядро | завантаження C (324 МГц) | завантаження D (327 МГц) | зміна |
|---|---|---|---|
| DOT | 774 мс (0.065 MAC/такт) | **508 мс (0.098)** | ×1.52 |
| BLK | 908 мс (0.055) | **648 мс (0.077)** | ×1.40 |
| FIR | 1010 мс (0.080) | 990 мс (0.080) | ×1.02 |

Контрольні суми в обох випадках ті самі (`85055090` / `f5735100` / `22056190`),
тобто обчислюється буквально те саме. Частота ядра однакова з точністю до 1%.

Пояснення узгоджене: **DOT і BLK потоково читають по 16 КБ** (два буфери по
8192×2 Б — більше за 16-КБ L1D ARM1136), тобто впираються в пам'ять; **FIR
перевикористовує вікно `x[]` у кеші** й упирається в ALU. Змінилась швидкість
підсистеми пам'яті (DVFS/OPP ядра L3/SDRAM), а не тактова частота ARM.

**Наслідки, які треба врахувати в порівнянні з DSP:**
1. «Best-of-N» захищає від завад **усередині** прогону, але **не** від зміни
   стану системи між завантаженнями — це різні речі, і раніше я їх плутав
   (§16.7 подавав збіг MAC/такт на двох частотах як доказ надійності приладу;
   для FIR це так, для DOT/BLK — ні).
2. Два з трьох наших «ARM-еталонів» насправді міряють **пам'ять**, а не ядро.
   Для чесного порівняння з C55x це принципово: DSP ходить у ту саму SDRAM
   через DSP MMU, тож частину різниці визначатиме шина, а не dual-MAC.
3. ARM- і DSP-заміри треба знімати **в одному прогоні**, а не порівнювати
   числа з різних завантажень.

### 16.8. ДВА РЕБУТИ АПАРАТА — розслідування (відкрите)

Після кожного з двох прогонів, що чіпали DSP-стек, апарат **згодом**
перезавантажувався. Ребут **відкладений**: сам процес завершувався штатно
(`EXIT 0`), лог забирався, і лише через хвилини апарат ішов у ребут.

Спільне в обох прогонах: `RLibrary::Load` + `Close` для **`bridgeapi.dll`,
`bal.dll`, `dspmemmapper.dll`**; у другому — ще `RDevice::Open("Hwa")` +
`GetCaps` + `Close` (перший давав `KErrNotFound` через хибне ім'я `D32HWA`).

**Робоча гіпотеза (не факт):** ці DLL розраховані на єдиного власника —
аудіо-сервер. Їх вивантаження запускає глобальні деструктори, які чіпають
спільний стан DSP; аудіо-стек потім падає в ядрі → ребут. `RDevice::Close` на
живому драйвері — другий підозрюваний.

**Реакція за правилом «не повторювати те саме після двох невдач»:** проби
розділено на рівні (`lib`/`dev`/`chan`/`dsp`), за замовчуванням DSP-стек **не
чіпається взагалі**; `bal.dll` і `dspmemmapper.dll` не вантажимо більше ніколи
(вони й не потрібні — усі потрібні ординали є в `bridgeapi`). Далі — бісекція
з витримкою після кожного прогону, по одному рівню за раз.

## 18. МІСТ ВІДКРИТО НА ЗАЛІЗІ; базовий образ вантажиться (2026-08-10)

Прогони на N95. Кожен рядок логу пишеться з `Flush()`, тож навіть коли апарат
гине, останній рядок точно вказує місце.

### 18.1. Що працює — підтверджено на апараті

```
ord32 Open(proc=0 DSP, flag=0, NULL) -> 0
object now: 00030002 00000000 00000000 007000f0 00000000
ord9 bind(A, C) -> 0
ord26 Load BASE: Z:\resource\plugins\baseimage.dof -> 0
```

- **`ord32` відкриває міст до C55x.** Виведена реверсом сигнатура
  `(aProcId=0, aFlag=0, aAttrs=NULL)` підтверджена на живому залізі: у `[0]`
  з'явився хендл каналу `0x00030002`, у `[12]` — вказівник на 60-байтовий блок
  (`0x007000F0`), у `[16]` — наш `procId`.
- **`ord9(A, C)` = прив'язка** класу A до процесора — `0`.
- **`ord26` вантажить базовий образ DSP/BIOS** (155 КБ) — `0`. Тобто і виклик,
  і аргументи `(this, aPath)` правильні.

### 18.2. Що падає і чому — `ord26` не для вузлів

Апарат **негайно перезавантажується**, коли `ord26` отримує **динамічний
вузол**: однаково і наш `E:\bench.dll55l`, і штатний
`Z:\system\apps\ping\pingdyn.dll55l` з ROM.

Це і був розділювальний дослід: **штатний вузол Nokia падає так само, як наш**
→ наш DOFF ні до чого, справа в тому, ЯК вантажимо. А оскільки повний базовий
образ тим самим викликом проходить, висновок такий:

> `ord26` — це `PROC_Load` для **образу процесора**, а не для вузла. Вузол у
> dspbridge вантажиться інакше: DCD-реєстрація + `NODE_Allocate` за UUID, після
> чого ядро саме підтягує його бібліотеку динамічним лоадером. Згодовування
> DOFF-бібліотеки в `PROC_Load` кладе ядро.

Перевірено додатково: **третій аргумент `ord26` ніде в тілі не читається**
(`[sp,#88]` не згадується жодного разу), тобто режиму він не вибирає.

Спроба `ord32(aFlag=1)`, де функція сама питає драйвер про шлях до бази
(`DoControl(0x04000000, буфер)`), дала **`-38 KErrBadDescriptor`** — чисто, без
ребуту, з відкотом об'єкта. Тому базу вантажимо явним шляхом.

### 18.3. Шлях створення вузла знайдено (`bal`, `0x80A41DDC`)

```
r5 = клас C (процесор), r4 = клас B (задача)
блок 20 Б = { [arg+4], [arg+0], [CBal+48], [arg+8], [arg+12] }
ret = helper(C, aOp=4, &блок, &out)
якщо ret == 0:
    C[0..11] -> B[4..15]     ; канал копіюється в задачу
    out      -> B[0]         ; ХЕНДЛ ЗАДАЧІ
```

Перед цим `bal ord 1` кличе **`A::ord4(&[CBal+48])`**, і результат стає одним зі
слів блоку — тобто клас A спершу **резолвить UUID у посилання на DCD**, і лише
тоді твориться задача.

**Поправка до §17.3:** клас B — **16 байтів**, а не 8. Конструктор (ord 21)
обнуляє лише перші 8, але сюди копіюється 12 байтів за зсувом +4. У розкладці
`CBal` це закриває і те «невідоме поле +32», яке я раніше виніс окремо: воно
частина B.

### 18.4. Стабільна послідовність, підтверджена на апараті

```
cmdline 'baseonlynobench', uptime 896 с
  ord32 Open(proc=0 DSP, flag=0, NULL) -> 0
  ord9 bind(A, C)                      -> 0
  ord26 Load(Z:\resource\plugins\baseimage.dof) -> 0
  ord10/ord33 close  (порядок CBal::Shutdown)
  == end ==            <- прогін завершився, апарат живий
```

Тобто **відкриття мосту + прив'язка + завантаження базового образу +
коректне згортання не валять апарат**. Це остаточно знімає підозру з бази:
вбиває саме `ord26` на **вузлі**.

> **Обережно з висновками про «не виконався».** Спроба `baseonly` перед цим
> виглядала як ще один ребут, і я почав будувати на цьому гіпотезу «руйнівна
> саме база». Насправді прогін **не стартував**: у виводі не було жодного
> `OK <байти>`, а в лозі на апараті лишався попередній `cmdline`. Ознака
> реального прогону — рядки `OK` від PUT і свіжий `cmdline` у першому рядку
> логу; без них падіння стосується стану апарата **до** нашої команди.

### 18.5. Клас A: `ord4` розшифровано й перевірено, `ord6` — ще ні

```
ord4(A, &out)  -> 0, out=00000000
ord4(A, NULL)  -> -6            <- рівно як передбачав дизасемблер
ord6(A, our UUID 16 B)  -> -6
ord6(A, PING UUID 16 B) -> -6
```

- **`ord4(TInt* aOut)` підтверджено на залізі**: `NULL` → `-6 KErrArgument`,
  інакше `0` і одне слово з `[A+0]`. Зараз воно нульове — у класі A ще не
  вибрано вузол, і саме це значення `bal` кладе у блок створення задачі.
- **`ord6` бере не сирий UUID.** Контроль вирішальний: той самий `-6` прийшов і
  на UUID штатного `PING`, який на цьому апараті зареєстрований напевно. Отже
  справа не у вмісті, а у **типі аргументу** — найімовірніше це дескриптор
  (`TDesC`), а не 16-байтовий блок. Перевіряти далі — через внутрішню
  `0x80A5F5C2`, куди `ord6` передає `(об'єкт [A+4], аргумент, 0, буфер 304 Б)`
  під м'ютексом.

> **Виправлення власної атрибуції.** Раніше я записав, що `ord4` розбирає рядок
> через `TLex`. Це артефакт вікна дизасемблера: `ord4` — лише 32 байти, а `TLex`
> належить сусідній **неекспортованій** функції `0x80A5E6DC`, у яку залазило
> вікно, взяте «до наступного експорту». Довжину функції не можна виводити з
> відстані до наступного ординала.

### 18.6. ЗАДАЧУ СТВОРЕНО НА DSP — ланцюг замкнувся

```
ord6(A, TESTSERVER_NOKIA)      -> 0
ord4(A, &ref)                  -> 0, ref = 0x007003B0
DoControl(канал, fn=4, TBuf8<20>{0,0,ref,0,0}, &out) -> 0
                                  taskHandle = 0x00008000
```

Тобто **весь шлях від відкриття мосту до створення задачі на C55x
відтворено власним кодом**, без `bal` і без C++-обгорток вузла.

**Пастка, яка коштувала одного прогону: тип дескриптора.** Перша спроба
передала `TPtr8` і дістала `-2 KErrGeneral`. Обробник ядра (`0x801B4EA4`)
робить **сире читання 32 байтів** з переданого вказівника у власний буфер,
тобто чекає розкладку «8 Б заголовка + 20 Б даних» — це `TBuf8<20>`, а не
`TPtr8` (у якого замість даних лежить вказівник). З `TBuf8<20>` перший же
варіант блоку спрацював.

Заразом це знімає ще одне побоювання: **виклики цієї родини не валять апарат**
— ядро перевіряє аргументи й повертає помилку. Ітерувати тут можна вільно.

### 18.7. Пряма DCD-реєстрація: запис приймається, але вузол не знаходиться

```
DoControl(0x0400000D, &count=1, запис 84 Б з нашим UUID) -> 0
ord6(A, наш UUID) після реєстрації                       -> -6
```

Запис зібрано за розкладкою з `ord26`: `{next(4), uuid(16), props(32), …}`,
`props` заповнено нулями. Ядро виклик **прийняло**, але пошук усе одно не
знаходить вузол — отже ці 32 байти властивостей значущі, і їх треба брати з
розбору `.dcd_register`/UUID-секції, а не вигадувати.

Це і є єдина незакрита ланка. Джерело правди — вихідний формат парсера
`0x80A5F0D4` (записи по 48 Б: `{uuid(16), props(32)}`).

### 18.8. Ще одна пастка інструментів: несвіжий бінарник

`ABLD.BAT` може повернути 0 навіть коли `make` впав. У результаті
`tools\build.cmd` друкував `built ->` і деплоїв **старий** exe — апарат мовчки
виконував код, що не відповідає джерелу. Спіймано на помилці компіляції
(`uuid` undeclared). Виправлено: цільовий exe тепер видаляється перед збіркою,
тож несвіжий бінарник фізично не може поїхати на апарат.

### 18.9. Порядок усередині `ord26` — я помилявся; зате знайдено безпечний виклик

Гіпотеза була: `ord26` спершу реєструє DCD (user-space), потім вантажить образ,
тож якщо зламати другу стадію — реєстрація лишиться. Перевірка: відкрити наш
вузол **ексклюзивно** своїм `RFile`, щоб внутрішній
`RFile::Open(..., EFileShareReadersOnly)` в `ord26` не вдався.

```
lock our node exclusively -> 0
ord26(locked node)        -> -14      (KErrInUse, БЕЗ падіння апарата)
ord6(A, our UUID) after   -> -6       (реєстрації не сталося)
```

**Гіпотезу спростовано.** DCD-розбір робить **ядро**, а не user-space: у
`0x80A5F0D4` шлях іде в драйвер асинхронним `DoControl` (op=5), і файл читає
саме драйвер. Наш лок зупинив усе ще до реєстрації, а не після неї.

**Але побічний результат цінний сам по собі:** це **безпечний спосіб кликати
`ord26` на вузлі** — заблокований файл дає чисте `-14` замість ребуту. Тобто
експерименти з цією гілкою більше не коштують перезавантажень.

### 18.10. Заголовок DOFF розшифровано (і його можна правити)

Зіставленням сирих байтів із полями `DLLdump` на чотирьох файлах:

| зсув | поле | наш вузол |
|---|---|---|
| `+0x00` | `strtab_size` | `0x168` |
| `+0x04` | **`entrypt`** | `0` (у бази `0x273BB`) |
| `+0x08` | `byte_order` | `0x00010203` |
| `+0x0C` | `scn_name_size` | `0x69` |
| `+0x10` | `{u16 no_syms, u16 max_str_len}` | `0x0027000E` |
| `+0x14` | `{u16 no_scns, u16 target_scns}` | `0x00010005` |
| `+0x18` | `{u16 doff_version, u16 target_id}` | `0x009C0000` |
| `+0x1C` | **`{u16 flags, u16 entry_secn}`** | `0x000012E0` (у бази `0xFFFF12E3`) |
| `+0x20` | `checksum` | `0xFF3AE938` |

**Правило контрольної суми: `checksum = ~(сума 8 попередніх слів)`** — тобто
сума всіх дев'яти слів дорівнює `0xFFFFFFFF`. Перевірено на `baseimage.dof`,
`pingdyn.dll55l`, нашому вузлі й нашому DCD-стабі — збіг у всіх чотирьох.

Практичний наслідок: заголовок DOFF можна модифікувати й лишити валідним
(зокрема виставити «виконувані» прапорці `0x12E3` та `entrypt`), перерахувавши
одне слово. Чи має це сенс — окреме питання: `PROC_Load` з виконуваними
прапорцями спробує покласти секції як образ процесора, а для вузла з кодом це
означало б запис поверх пам'яті базового образу.

### 18.11. Опис вузла прочитано; DCD виявився ДВОБІЧНИМ

`ord1(this, aIndex, aOut)` = перелічити об'єкт №`aIndex`, узяти його опис і
скопіювати виклика́чу **152 байти** (`memcpy` @`0x80A5E4C2`). Це рівно той
буфер, з якого `ord26` будує запис реєстрації. Дамп на апараті:

```
ord1(idx=0) -> 0  10d930612b1ce44094a414ebb314340e  "EAP_TASK"…
ord1(idx=1) -> 0  1dce8f89b6294f459e24057f81d792ed  "TESTSERVER_NOKIA"
ord1(idx=2..5) -> -6
```

- байти **0..15** — UUID (`dsp_uuid`, little-endian);
- байти **16..47** — **ім'я вузла в UTF-16, рівно 16 символів** (у
  `TESTSERVER_NOKIA` це 32 байти без залишку; у `EAP_TASK` хвіст — сміття від
  попереднього запису в тому ж буфері).

Отже запис реєстрації — це `{next(4), uuid(16), ім'я UTF-16(32)}`, і мій
здогад про «32 байти властивостей» був неточним: там просто ім'я.

**Але це ж пояснює, чому пряма реєстрація не спрацювала.** DCD **двобічний**:

| сторона | наповнюється | читається |
|---|---|---|
| user-side (у класі A) | розбором файла всередині `ord26` | `ord1`, `ord6`, `ord4` |
| kernel-side | `DoControl(0x0400000D)` | RMS при створенні вузла |

Ми зробили лише другу половину — тому `DoControl` повернув `0`, а `ord6`
далі не бачив вузла. А розбір, який наповнює першу половину, вварений в
`ord26` (єдиний виклик `0x80A5F0D4` у всій бібліотеці — перевірено пошуком).

### 18.12. `ref` — це не структура, а пул рядків

Дамп за адресою, яку віддає `ord4`:

```
ref+00  e00b0030 e00b0000
ref+08  "TESTSERVER_NOKIA_tn_create\0" … "TESTSERVER_NOKIA_tn_execute\0"
        … "TESTSERVER_NOKIA_tn_delete\0" "init\0" ".stack\0" ".hst\0" ".DARAM$…"
```

Тобто два слова-вказівники (`0x30000BE0` і `0x00000BE0` — різняться рівно на
`0x30000000`, схоже на «адреса DSP» проти «зсув») і далі **пул рядків**: імена
трьох фаз вузла та імена секцій DSP. Відтворити його вручну можна, але це
крихка конструкція з внутрішніми зсувами.

### 18.13. Гіпотезу «винні прапорці DOFF» не підтверджено

Стаб було пропатчено на виконуваний заголовок
(`tools\patch_doff_exec.py`: прапорці `0x12E3`, точка входу як у бази,
перерахована контрольна сума — `DLLdump` валідацію проходить) і подано в
`ord26`. Секцій, що алокуються чи вантажаться, у ньому **нуль**, тобто класти
на DSP нічого.

**Апарат усе одно впав.** Отже прапорців і точки входу **недостатньо** —
різниця між `baseimage.dof` і вузлом глибша (найімовірніше в тому, що
`PROC_Load` очікує образ із таблицею секцій BIOS/RMS, а не бібліотеку).
Гіпотезу §18.2 у частині «справа лише в прапорцях» знято.

### 18.13a. Карта DCD-родини ioctl (знята з місць виклику)

Уся DCD-робота `bridgeapi` іде через два диспетчери, які формують код як
`0x0400000C + 18 + op`: **`0x80A5DB2A`** (синхронний, `DoControl`) і
**`0x80A5DB42`** (асинхронний). Обидва відсікають `op >= 10` з `-5`.
Номери операцій витягнуто з усіх десяти місць виклику:

| op | ioctl | виклик | де вживається |
|---|---|---|---|
| 0 | `0x0400001E` | sync | `0x80A5F070` |
| 1 | `0x0400001F` | sync | **опис вузла** — `0x80A5F5C2`, за ним `ord6` |
| 2 | `0x04000020` | async | `0x80A5F26E`, `0x80A5F500` |
| 3 | `0x04000021` | async | **перелік** — `0x80A5F566`, за ним `ord1` |
| 4 | `0x04000022` | sync | перелік (варіант) — `0x80A5F580`, `0x80A5F5AC` |
| **5** | `0x04000023` | async | **розбір файла в user-side DCD** — `0x80A5F106` |

**`op=5` — саме те, чого бракує.** Він наповнює user-side DCD, і якщо його
покликати напряму зі свого каналу, `ord26` з його смертельною стадією
завантаження образу стає не потрібен. Пробу вже реалізовано
(`dsptest.exe … dcdop`), лишилось прогнати на апараті.

> **Побічна поправка.** Ці коди (`0x0400001E`+) виходять за межі 24-входової
> таблиці, яку я в §17.2 приписав родині пристрою. Але `op=1` на апараті
> **працює** (через нього `ord6` знайшов вузли бази), отже та таблиця
> обслуговує іншу родину, а не `0x0400_00NN`. Таблицю §17.2 слід читати як
> «знайдений у PDD диспетчер на 24 входи», без прив'язки до конкретної родини.

## 19. НАШ ВУЗОЛ ЗАРЕЄСТРОВАНО І ЗАДАЧУ ДЛЯ НЬОГО СТВОРЕНО (2026-08-10)

### 19.1. Обхід `ord26` знайдено: прямий виклик розбору

`0x80A5F0D4` — це рівно «розбір файла + наповнення user-side DCD»; завантаження
образу на DSP (те, що кладе ядро) робиться **окремо**, власними `RFs`/`RFile`
далі в `ord26`. Функція не експортована, але `bridgeapi` — XIP, адреси
фіксовані, і всі 39 ординалів ми вже звірили з ROM-дампом бітово.

```
lock(0x80A5EFA1);  parse(0x80A5F0D5)(loader, &path);  unlock(0x80A5EF97)
    -> 0
enum(loader, 0)   -> 0   11bf7c96 0eb9544b a4d33c84 249ee1da   <- НАШ UUID
getdef(loader, our UUID, type=0) -> 0
    def[0..15]  = UUID, def[16..47] = "BENCH_DSP" у UTF-16
```

`loader` беремо з `[C+12]`; `A[4]` вказує туди ж, тобто `ord6` дивиться в те
саме сховище.

### 19.2. Чому `ord6` спершу не бачив вузла: бракувало записів бібліотек

**Уточнення 2026-10-01:** висновок нижче описує серпневий тест без library
type2. Native fallback 3→2 та generic library підтверджено статично на
N95/E90 і апаратно на обох: node0+library2 проходить create/delete/free0,
зберігає data stamp та адресу delete. Отже, явні типи 3/4/5 — один із
варіантів реєстрації, а не обов'язкова умова. Див.
[нові результати](STREAM_RESEARCH.md#бібліотека-типу-2-і-задача-після-create).

`props[292]` виявився **типом завантаження**: у нашого вузла там `1`
(динамічний). Для таких `ord6` іде в гілку `0x80A5E6DC`, яка шукає записи
типів **3/4/5** = `CREATELIB`/`EXECUTELIB`/`DELETELIB` (типи DCD з dspbridge).
Без них — `-6`, хоча сам вузол у сховищі вже є.

Жоден вузол у ROM цих типів не оголошує (перевірено всі 30 файлів: 24 мають
лише `:0`, шість — `:0,:1`) — там вони синтезуються під час штатної реєстрації
через `ord26`. Ми ж `ord26` обходимо, тому оголошуємо їх **явно** в
`.dcd_register` нашого вузла:

```
"967CBF11_..._:0," "967CBF11_..._:3," "967CBF11_..._:4," "967CBF11_..._:5,"
```

**Спрацювало:** `ord6(A, наш UUID) -> 0`.

### 19.3. Задачу для НАШОГО вузла створено на DSP

```
ord7(A, наш UUID, args) -> 0        (ord6 + дескриптор аргументів створення)
ord4(A, &ref)           -> 0        ref = 0x007003B0
DoControl(канал, fn=4, TBuf8<20>{0,0,ref,0,0}, &out) -> 0
                                    taskHandle = 0x00008000
```

**Доказ, що вибрано саме наш вузол** — дамп структури за `ref`:

```
ref+00  … "BENCH_DSP_create" … "BENCH_DSP_execute" … "BENCH_DSP_delete"
```

Раніше на тому ж місці були `TESTSERVER_NOKIA_tn_*`. Тобто це не збіг адрес:
структура містить імена фаз **нашого** вузла.

Родина команд задачі на нашому хендлі віддає **адреси у просторі DSP**:
`fn 2 -> 0x30000068`, `fn 3 -> 0x3000010C`, `fn 4 -> 0x3000000C` — тобто
пам'ять під вузол на DSP уже виділено.

### 19.4. Карта родини задачі — і одна смертельна команда

Розгортка `0x08000000 + idx` на власному хендлі (`a2` — валідний буфер, бо
серед команд є асинхронні й нульовий `TRequestStatus` означав би запис ядра за
адресою 0):

| fn | результат | fn | результат |
|---|---|---|---|
| 0 | 0 | 8 | −2 |
| 1 | −18 | 9 | −2 |
| 2 | 0, DSP `0x30000068` | 14 | 0 |
| 3 | 0, DSP `0x3000010C` | 15 | 0 |
| 4 | 0, DSP `0x3000000C` | 16 | 0 |
| 5 | 0 | 17 | 0 |
| 6 | 0 (асинхр. завершується −2) | **18** | **кладе апарат** |
| 7 | −18 | | |

> **Правило: родину задачі НЕ мести наосліп.** На відміну від DCD-родини (де
> всі шість операцій безпечні), тут `fn 18` перезавантажує апарат. Коди 0..17
> перевірені й безпечні; 18 і вище — не чіпати.

### 19.5. ВУЗОЛ СТВОРЕНО НА C55x — бракувало кроку `fn=5`

Пропущеною ланкою був окремий асинхронний крок. Повна послідовність із `bal`
(`0x80A41E26`):

```
fn=4  створити задачу            -> taskHandle
      скопіювати C[0..11] у B[4..15], покласти handle у B[0]
fn=5  СТВОРИТИ ВУЗОЛ на DSP (асинхронно!) + WaitForRequest
fn=6  далі
```

`fn=5` я раніше викликав у розгортці й отримував `0` — але **не чекав на
статус**, тобто асинхронну частину не завершував і вважав крок марним.

З правильним очікуванням:

```
DoControl(4) -> 0, taskHandle = 0x00008000
DoControl(5) node-create -> 0,  status: 0     *** NODE CREATED ON THE C55x ***
DoControl(6)             -> 0,  status: 0     (раніше було -2)
```

**Що це означає:** ядро завантажило наш `bench.dll55l` на DSP, динамічний
лоадер зарезолвив зовнішні символи проти базового образу
(`_NODE_getMsg`, `_NODE_putMsg`, `_CLK_gethtime`, `_CLK_countspms`, `_c_int00`),
і RMS викликав нашу фазу **`BENCH_DSP_create()` на C55x**. `fn=6` після цього
теж проходить — його попереднє `-2` було наслідком нествореного вузла, а не
проблемою з нашим кодом.

> **Ще один випадок тієї самої помилки.** Розміри `ord19`/`ord20` я раніше
> вказав як 16 і 1766 байтів — насправді обидва по 16. 1766 знову прийшло з
> «відстані до наступного ординала», хоча я вже фіксував це правило як хибне.
> Обидва — тонкі обгортки: `ord19` → `DoControl(0x0C000003, handle, &arg)`,
> `ord20` → `0x0C000004` з тією ж формою.

### 19.6. Обмін повідомленнями: структура відома, семантика — ні

`ord16` (клас B) розібрано до кінця:

```
0x80A61CD6(sp+8)  = TBufBase8(12,12)         ; TBuf8<12>, дані за +8
[sp+0] = 0x80000001 ; [sp+4] = 2             ; двослівний заголовок
[sp+16] = { &заголовок, arg1, arg2 }         ; тіло дескриптора
DoControl(канал = this+4, 0x0C000001, taskHandle = [this+0], &TBuf8<12>)
```

Тобто дескриптор для ядра будує сам `bridgeapi` — від нас потрібні лише
правильні C++-аргументи. Об'єкт класу B зібрано як у `bal`
(`[B+0]` = хендл, `[B+4..15]` = копія `C[0..11]`), і це працює: `this+4`
справді читається як `RBusLogicalChannel`.

**Але моя інтерпретація аргументів була хибною.** Я передав
`arg1 = вказівник на {cmd, arg_1, arg_2}` (наше повідомлення вузлу),
`arg2 = таймаут` — і ядро впало. Заголовок `{0x80000001, 2}`, який
`bridgeapi` кладе перед аргументами, більше схожий на **команду рівня RMS**,
ніж на обгортку нашого повідомлення, тобто `arg1`/`arg2` означають щось інше.

Далі вгадувати аргументи, що йдуть у ядро, недоцільно: кожна невдала спроба
коштує перезавантаження апарата. Наступний крок — знайти в `bal` реального
виклика́ча `ord16`/`ord18` і взяти аргументи звідти, як це вже спрацювало для
`fn=4` (`TBuf8` замість `TPtr8`) і для `fn=5` (пропущене очікування статусу).

### 19.6a. ВИПРАВЛЕННЯ: `fn=6` — це видалення вузла

Нижче по тексту `fn=6` названо «запуском» — це **помилка**. `bal` @`0x80A41F4C`
кличе `DoControl(канал, fn=6, taskHandle, &status)` + `WaitForRequest` саме
щоб **згорнути** задачу (шлях обробки помилки в `bal` ord28). Те, що після
створення вузла він почав повертати `0` замість `-2`, пояснюється просто:
видаляти стало що.

Практичний наслідок: `fn=6` треба кликати **завжди**, зокрема в шляхах помилок,
інакше вузол лишається на DSP.

### 19.7. Вузол живий і відповідає драйверу

`bal` керує вузлом **не** через `ord15..18` (він їх навіть не імпортує), а
через родину задачі, у формі, взятій з нього дослівно:

```
DoControl(канал = B+4, fn, taskHandle, &status) + WaitForRequest
   fn = 0x08000007   (bal ord28,  літерал 0x0800000E − 7)
   fn = 0x08000008   (bal @0x80A41A11)
   status ініціалізується як KRequestPending (0x80000001)
```

Результат **після** створення вузла:

```
node fn 7 -> 0, status 0        (до створення було -18 KErrNotReady)
node fn 8 -> 0, status 0        (до створення було -2)
```

Обидві операції змінили результат з помилки на успіх рівно тоді, коли вузол
було створено. Це **четвертий незалежний доказ**, що на C55x живе саме наш
вузол — поряд із (1) успішним `node-create`, (2) іменами
`BENCH_DSP_create/execute/delete` у структурі вузла, (3) виділеними під нього
адресами у просторі DSP.

## 20. ПЕРШІ ЧИСЛА C55x ПРОТИ ARM1136 (2026-08-10)

### 20.1. Канал вимірювання без черги повідомлень

Шлях повідомлень виявився глухим: ординали 15–18 `bridgeapi`
(ioctl `0x0C000001/2`) **не використовує жоден модуль у ROM** — лише сам
`bridgeapi` у таблиці експортів (перевірено скануванням усього `sys/bin`), і
виклик кладе ядро. Повернене з `create` значення на ARM теж не потрапляє
(перевірено: `create` віддавав `0x1234`, `node-create` однаково давав `0`).

Тому вимір побудовано інакше: **робота крутиться всередині фази `create`, а
час міряється на ARM**. Створення вузла синхронне (`DoControl(5)` + очікування
статусу), тож його тривалість зростає рівно на час обчислення на C55x.
Фіксовані накладні (завантаження бібліотеки, обмін з RMS) скорочуються
різницею двох прогонів з різним `BENCH_CREATE_REPS` — це диференційний вимір.
Буфер статичний, у `.bss` вузла: спільна пам'ять не потрібна.

**Це водночас і доказ виконання:** 20000 повторів дають час у ~39 разів
більший за базовий прогін, і час масштабується з кількістю повторів.

### 20.2. Результати

Ядро — Q15 dot-product, `n = 1024` (робочий набір 4 КБ, вміщується в кеш на
обох боках), той самий вихідний код на обох боках. Best-of-N по серіях, бо
завада може лише сповільнити:

| серія | мінімум з N прогонів |
|---|---|
| create, 0 повторів | 7 934 мкс (з 4) |
| create, 10000 повторів | 124 176 мкс (з 4) |
| create, 20000 повторів | 308 197 мкс (з 4) |

| оцінка | MMAC/s | MAC/такт (при 220 МГц) |
|---|---|---|
| 10000 проти базового | 88.1 | 0.400 |
| 20000 проти базового | 68.2 | 0.310 |
| 20000 проти 10000 | 55.6 | 0.253 |

**ARM1136 у тому ж завантаженні** (ядро DOT-S, той самий `n = 1024`):
**32.28 MMAC/s**, **0.099 MAC/такт** при виміряних 324 МГц.

### 20.3. Чесна інтерпретація

Оцінки **монотонно спадають** зі зростанням обсягу роботи (88 → 68 → 56).
Це не розкид, а систематичний ефект: що довше рахує DSP, то більше його
витісняє аудіо-стек, який ним володіє. Тому **єдиного числа заявити не можна**;
чесний результат — діапазон:

> **C55x швидший за ARM1136 приблизно в 1.7–2.7 раза за абсолютною
> продуктивністю і в 2.6–4.0 раза в перерахунку на такт** на Q15
> dot-product з робочим набором, що вміщується в кеш.

Нижня межа (55.6) методологічно найнадійніша — різниця двох робочих точок
скорочує всі фіксовані накладні; верхня (88.1) найчистіша за завадами, але
спирається на базовий прогін, у якому накладні можуть відрізнятися.

**Застереження, які треба тримати при собі:**
1. Частота DSP **не виміряна**, взято номінальні 220 МГц — усі числа
   «на такт» масштабуються разом з цим припущенням.
2. Вимір включає планування задачі на DSP під живим аудіо; це не «чистий»
   бенчмарк ізольованого ядра.
3. C55x-код — звичайний C через `cl55 -o3` (компілюється в `RPT CSR; MACM`),
   без ручної оптимізації. Теоретична межа dual-MAC — 2 MAC/такт, тобто
   отримані 0.25–0.40 далекі від піку, і це очікувано для коду з C.

### 19.8. Що саме лишилось

`fn=6` завершується `-2` — **однаково і на нашому вузлі, і на штатному
`TESTSERVER_NOKIA`**. Це важливо: на цій стадії API наш вузол уже
**не відрізняється від штатного**, тобто справа не в ньому, а в тому, що
послідовність запуску неповна. Гіпотеза: `fn=6` — не «запуск», а очікування
повідомлення (`-2` = немає), а створення/запуск вузла робиться іншими
командами з безпечного набору (0, 5, 14..17) або через родину `0x0C00_00NN`
класу B.

Спроба дати аргументи створення через `ord7` картину не змінила.

### 18.14. Стан бенчмарку і що саме лишилось

**Готове і перевірене:**

| частина | стан |
|---|---|
| ARM-ядра (DOT/FIR/BLK, Q15) | працюють, виміряні на апараті |
| матчення ARM↔DSP (32-бітний акумулятор) | виправлено, доведено збігом контрольних сум |
| C55x-вузол (`bench.dll55l`) | збирається з коду, `RPT CSR; MACM`, форма DOFF як у виробничого вузла Nokia |
| DSP-бічний прилад часу | `CLK_gethtime`/`CLK_countspms` є в базі |
| відкриття мосту, прив'язка, завантаження бази | **працює на апараті** |
| пошук вузла в DCD, посилання на вузол | **працює** |
| створення задачі на DSP | **працює** (`taskHandle 0x8000`) |
| **реєстрація НАШОГО вузла в user-side DCD** | **не працює — єдиний блокер** |

**Блокер, точно локалізований.** Щоб `ord6` побачив наш UUID, файл має пройти
розбір усередині `ord26`; а `ord26` на будь-якому невиконуваному DOFF кладе
ядро — і патч заголовка цього не лікує (§18.13).

**Три шляхи, у порядку привабливості:**

1. **Знайти окремий вхід до розбору.** У `bridgeapi` його нема, але
   `0x80A5F0D4` шле драйверу асинхронний `DoControl` з **op=5** (через
   `0x80A5DB42`, база `0x0400000C + 18`). Тобто розбір робить **ядро**, і його
   можна спробувати викликати напряму зі свого каналу, без `ord26` і без
   стадії завантаження образу. Це найкоротший шлях і він не потребує нових
   знань про формати.
2. **Відтворити пул рядків з §18.12** і підсунути власний `ref` у
   `DoControl(fn=4)`, обійшовши DCD цілком. Крихко, але перевіряється
   безпечно — ядро на кривих аргументах віддає помилку, а не падає.
3. Зібрати вузол як повноцінний образ процесора (потребує DSP/BIOS-бібліотек,
   яких у нас нема) — найдорожчий шлях.

**Безпека прогонів:** усе, крім `ord26` на вузлі, апарат не валить. Якщо
`ord26` таки потрібен — тримати файл відкритим ексклюзивно, тоді він віддає
`-14` замість ребуту (§18.9).

### 18.15. Довідка: прапорці `dsptest.exe`

`lib` `dev` `chan` `dsp` — рівні проб; `load` (наш вузол) / `ref` (штатний
`pingdyn`) / `base` (базовий образ) / `baseonly` (спинитись після бази) /
`stub` / `task` / `reg` / `lock` / `dump` — окремі досліди; `nobench` вимикає
ARM-бенчмарк, `heavy` повертає повні `BENCH_*_REPS`. Прапорці розпізнаються
підрядком, тож їх можна злити в один токен: `baseonlytasknobench`.

Знайти, як у клас A потрапляє UUID (кандидати — ord 6/7, вони єдині з
`TLex`-розбором рядка, і `ord 7` — тонка обгортка над `ord 6`), і як
реєструється DCD нашого вузла. Після цього послідовність замикається:
база → A(UUID) → create task → `0x0C00_00NN` для run/повідомлень.

## 17. Інтерфейс ядра `Hwa` розібрано повністю (2026-08-10)

`ehwa.ldd` виявився кращою ціллю, ніж 39 C++-ординалів: це вузький
цілочисловий ioctl-інтерфейс, і його диспетчер розбирається однозначно.
`DLogicalChannel::Request(aReqNo, a1, a2)` ділить простір запитів на **три
родини за старшими бітами** (`0x801B53B0`):

| Діапазон `aReqNo` | Куди йде | Що це |
|---|---|---|
| `< 0x04000000` | локальні обробники LDD | керування каналом |
| `0x04000000…0x07FFFFFF` | tail-call у **vtable PDD, слот +28** | **команди пристрою** (attach, load DOFF, DCD, пам'ять) |
| `0x08000000…0x08000015` | **таблиця переходів на 22 входи** (`0x801B4B74`) | **команди задачі/вузла** |
| `>= 0x0C000000` | vtable PDD, слот **+84** | третя родина (`0x801B4D18`) |

Саме тому `bridgeapi` тримає літерал `0x04000001` і адресує сусідні команди як
база+N: це прямі коди пристроєвої родини.

### 17.0. Родина каналу `fn 0..10` — тут живе створення задачі

Найнижчий діапазон (`aReqNo < 0x04000000`) я спершу відклав як «керування
каналом». Насправді саме там найважливіше. Диспетчер — `0x801B52A4`:
`cmp r1,#10; addls pc,pc,r1,lsl#2` → таблиця на **11 входів** (`0x801B52C0`);
усе понад 10 іде у родини нижче.

| fn | обробник | | fn | обробник |
|---|---|---|---|---|
| 0 | `0x801B52EC` | | 6 | `0x801B5354` → `0x801B5118` **асинхронна операція над задачею** |
| 1 | `0x801B52F4` | | 7 | `0x801B5364` → `0x801B4DE4` |
| 2 | `0x801B530C` | | 8 | `0x801B5374` |
| 3 | `0x801B5318` | | 9 | `0x801B53A0` → `0x801B505C` |
| **4** | `0x801B5334` → `0x801B4EA4` **створення задачі** | | 10 | `0x801B5330` |
| 5 | `0x801B5344` → `0x801B5014` | | | |

Прив'язка до реального коду: `bal` (`0x80A41DDC`) створює задачу **прямим**
`DoControl(канал_класу_C, fn=4, дескриптор(20 Б), &out)` — жодних C++-обгорток,
`0x80A41F44` виявився просто tail-call у `RBusLogicalChannel::DoControl`. Далі
той самий `bal` робить `DoControl(fn=6, taskHandle, &status)` +
`User::WaitForRequest` — тобто **fn 6 — асинхронна операція над задачею**.

### 17.1. Таблиця з 22 команд задачі (`0x08000000 + idx`)

Перед диспетчером: пошук задачі за хендлом (`[this+92]`), помилки
`Error: no task handle` (−2), `Error: no owning device` (−21), попередження
`task call from other than owning device`. Значення за замовчуванням `r5 = −5`
(`KErrNotSupported`).

| idx | обробник | idx | обробник |
|---|---|---|---|
| 0 | `0x801B4BCC` → `0x801B423C` | 11 | **−5 (немає)** |
| 1 | `0x801B4BDC` (перевіряє `[task+20]`, інакше −18) | 12 | **−5 (немає)** |
| 2 | `0x801B4C08` → `0x801B4A98` | 13 | **−5 (немає)** |
| 3 | `0x801B4C1C` → `0x801B4A2C` | 14 | `0x801B4C90` (arg3=0) |
| 4 | `0x801B4C30` → vtable PDD +28 | 15 | `0x801B4C98` (arg2=0) |
| 5 | `0x801B4C40` → `0x801B4418` | 16 | `0x801B4CA4` → `0x801B4988` (arg3=1) |
| 6 | `0x801B4C50` → `0x801B5698` (arg −3) | 17 | `0x801B4CBC` → `0x801B44B4` (arg2=1) |
| 7 | `0x801B4C60` → `0x801B4294` | 18 | `0x801B4CD0` → vtable PDD +68 |
| 8 | `0x801B4C70` → `0x801B4300` | 19 | `0x801B4CE0` → vtable PDD +72, пише результат у `*a2` |
| 9 | `0x801B4C80` → `0x801B42D4` | 20 | `0x801B4CF8` → `0x801B44F0` |
| 10 | **−5 (немає)** | 21 | `0x801B4D08` → `0x801B4540` |

Тобто робочих команд задачі — **18** (0–9 і 14–21). Пари (14,15) і (16,17)
відрізняються лише булевим прапорцем — класична пара «синхронно/асинхронно»
або «з очікуванням / без».

**Чому це цінно:** цей інтерфейс — те саме, чим користується сам `CBal` у
гарячому шляху (bal ord 27 кличе `RBusLogicalChannel::DoControl/DoRequest`
напряму, минаючи `bridgeapi`). Він вужчий за C++-ординали й не потребує знання
розкладок класів. Мінус — виклики йдуть у ЯДРО: помилка тут коштує ребута, а не
падіння процесу. Тому чіпати його можна лише після того, як з'ясовано причину
ребутів (§16.8), і лише з валідними хендлами, отриманими штатним шляхом.

### 17.2. Родина команд пристрою: 24 входи (`0x04000000 + idx`)

Диспетчер — у `ehwaomap.pdd` @`0x80199FDC`: `add r0, r8, #0xFC000000;
cmp r0, #23; addls pc, pc, r0, lsl #2` → таблиця з **24 входів** на `0x80199FF4`.

| код | idx | обробник | | код | idx | обробник |
|---|---|---|---|---|---|---|
| `0x04000000` | 0 | `0x8019A080` | | `0x0400000C` | 12 | `0x8019A4B4` |
| `0x04000001` | 1 | `0x8019A054` **= ord33 Close** | | `0x0400000D` | 13 | `0x8019A510` **= ord26, завантаження DOFF/DCD** |
| `0x04000002` | 2 | `0x8019A0DC` | | `0x0400000E` | 14 | `0x8019A318` |
| `0x04000003` | 3 | `0x8019A1A4` | | `0x0400000F` | 15 | `0x8019A6A4` |
| `0x04000004` | 4 | `0x8019A280` | | `0x04000010` | 16 | `0x8019A7C0` |
| `0x04000005` | 5 | **немає** | | `0x04000011` | 17 | `0x8019ABB0` (спільний з 8, 20) |
| `0x04000006` | 6 | **немає** | | `0x04000012` | 18 | `0x8019A894` |
| `0x04000007` | 7 | `0x8019A588` | | `0x04000013` | 19 | `0x8019AA2C` |
| `0x04000008` | 8 | `0x8019ABB0` | | `0x04000014` | 20 | `0x8019ABB0` |
| `0x04000009` | 9 | `0x8019A364` | | `0x04000015` | 21 | `0x8019AAFC` |
| `0x0400000A` | 10 | `0x8019A3D8` | | `0x04000016` | 22 | `0x8019A63C` |
| `0x0400000B` | 11 | `0x8019A414` | | `0x04000017` | 23 | `0x8019A670` |

Дві прив'язки до C++-боку вже є з §16.3: `bridgeapi` ord 33 (Close) шле
`0x04000001`, ord 26 (завантаження DOFF + DCD-реєстрація) — `0x0400000D`.

**Підсумок поверхні ядра:** 24 команди пристрою + 18 живих команд задачі
(з 22 входів) + третя родина від `0x0C000000`. Це і є повний ARM↔DSP
інтерфейс апарата.

### 17.3. Клас B = об'єкт задачі; третя родина `0x0C0000NN` розкрита

Розбір ординалів 15–20 замикає картину. Літерали біля них: `0x80A5DD2C` =
`0x80000001` (значення-прапорець), `0x80A5DD30` = **`0x0C000001`** — база
третьої родини.

Кожен метод класу B робить те саме:
```
r0 = this + 4      ; RBusLogicalChannel лежить за зсувом +4
r1 = 0x0C000001 + N ; код запиту (ord 19 -> +2, ord 20 -> +3)
r2 = [this + 0]     ; ХЕНДЛ ЗАДАЧІ
r3 = &аргументи
-> DoControl
```
Отже **об'єкт класу B — рівно 8 байтів: `{TInt iTaskHandle; RBusLogicalChannel
iChannel;}`** (сходиться з 8-байтовим ctor ord 21/22 і порожнім dtor 23/24).

Це замикається з диспетчером LDD (§17): у гілці `aReqNo >= 0x08000000` драйвер
**спершу шукає задачу за `a1`** (`[this+92]`, помилки «no task handle» / «no
owning device»), і лише потім розводить: `0x08000000+0..21` — таблиця з 22
входів у самому LDD, а `>= 0x0C000000` — у vtable PDD слот +84. Тобто `a1`
класу B — це саме той хендл задачі, який шукає драйвер. Збіг повний, з двох
незалежних боків.

**Наслідок для завантажувача:** роль класів тепер не гіпотеза, а висновок —
клас C відкриває канал і вантажить образи (родина `0x0400_00NN`), клас B
керує **задачею/вузлом** (родини `0x0800_00NN` і `0x0C00_00NN`), клас A
обслуговує UUID/DCD. Саме клас B — носій послідовності
allocate → create → run → put/get msg з контракту §14.1.

### 17.4. Підсумкова карта 39 ординалів `bridgeapi.dll`

Що встановлено по кожному. «код» — код ioctl, який метод шле драйверу
(порожньо = у виклик не входить). Ролі класів — з §16.3 і §17.3.

**Клас C — процесор/канал (ord 25–39), об'єкт ≥20 Б, `RBusLogicalChannel` @+0:**

| ord | адреса | код ioctl | що робить |
|---|---|---|---|
| 25 | `80A5DAE1` | — | `RDebug::Printf` + DoRequest + `Close` (шлях помилки) |
| 26 | `80A5D533` | `0x0400000D` | **завантаження DOFF-файла + DCD-реєстрація** (`RFs::Connect`→`RFile::Open`→`Size`→ioctl→`RChunk::Base`); будує записи по 84 Б з 16-Б UUID |
| 27 | `80A5D9B1` | `0x0400000F` | (без викликів euser — тонкий) |
| 28 | `80A5DAC3` | `0x04000010` | тонка обгортка DoRequest |
| 29 | `80A5D901` | `0x0400000C…` | `TDesC8::Ptr`/`User::Free`/`TDes8::Zero` + ioctl (буфер) |
| 30 | `80A5D87F` | `0x04000001` | `User::Alloc` (виділення буфера) |
| 31 | `80A5D9ED` | — | TBuf + `RDebug::Printf` + DoRequest + `Close` |
| 32 | `80A5D751` | (DoCreate) | **`TInt Open(TInt aProcId 0..1, TInt aFlag, const TAny* aAttrs24)`** — `0`=C55x, `1`=IVA у `[this+16]`; `aFlag==1` довантажує базовий образ через ord 26 |
| 33 | `80A5D4FD` | `0x04000001` | **Close/Detach** + `RHandleBase::Close` |
| 34 | `80A5DAA3` | `0x04000013`, `0x04000010` | тонка обгортка |
| 35 | `80A5D955` | `0x04000007`, `0x04000017`, … | **`Control(TInt aOp, …)`** — switch по `aOp` 0..3 (+ два спец-значення), кожна гілка шле свій код; поза діапазоном → `-5` |
| 36/37 | `80A5D4C9` | — | ctor (обнуляє 0,4,8,12) |
| 38/39 | `80A5D4D9` | — | dtor (+ `operator delete`) |

**Клас B — задача/вузол (ord 15–24), об'єкт рівно 8 Б
`{TInt iTaskHandle; RBusLogicalChannel iChannel;}`:**

| ord | адреса | код ioctl | що робить |
|---|---|---|---|
| 15 | `80A5DC71` | `0x0C000001` | 4 аргументи (r1..r3 + this) |
| 16 | `80A5DC37` | `0x0C000001` | те саме + `User::WaitForRequest` → **синхронний варіант** |
| 17 | `80A5DCDB` | `0x0C00000?` | пара до 15 |
| 18 | `80A5DCA1` | `0x0C00000?` | пара до 16 (з очікуванням) |
| 19 | `80A5DD0B` | **`0x0C000003`** | найтонший (16 Б): один ioctl |
| 20 | `80A5DD1B` | **`0x0C000004`** | 1766 Б: важкий розбір дескрипторів (DCD/перелік) |
| 21/22 | `80A5DC2D` | — | ctor (обнуляє 8 Б) |
| 23/24 | `80A5DC35` | — | dtor (порожній) |

**Клас A — UUID/DCD-об'єкти (ord 1–14), об'єкт 8 Б:** ord 4 і 6 розбирають
рядок через `TLex` (це UUID-парсер під формат `%08X_%04X_%04x_%02x…`), ord 7
кличе ord 6, ord 1/8 копіюють через `operator new`+`memcpy`, ord 10 = Close
(звільняє `[this+0]`), ord 13/14 = dtor через ord 10, ord 11/12 = ctor.
Каналу цей клас не тримає — він суто про ідентифікатори вузлів.

**Розміри об'єктів підтверджено незалежно — з розкладки `CBal`.** Деструктор
`CBal` (@`0x80A41BE2`) знімає члени за фіксованими зсувами: `ord13` (dtor A) на
`this+40`, `ord23` (dtor B) на `this+24`, `ord38` (dtor C) на `this+4`. А
`bal ord 27` — це просто `C::Control(this+4, aOp=2, 0)`. Отже:

| член | зсув у `CBal` | розмір |
|---|---|---|
| клас C (процесор/канал) | `+4` | **20 Б** |
| клас B (задача/вузол) | `+24` | **8 Б** |
| (невідоме поле) | `+32` | 8 Б |
| клас A (UUID/DCD) | `+40` | **8 Б** |

Розміри збігаються з тим, що дають конструктори (ord 36 обнуляє 0..12 плюс
ord 32 пише `+16` → 20 Б; ord 21 обнуляє 8 Б; ord 11 обнуляє 8 Б). Два
незалежні джерела, однакова відповідь.

**Перевірений (і знятий) ризик — регістр UUID у назві секції.** Форматтер у
`bridgeapi` @`0x80A61DE8` — `%08X_%04X_%04x_%02x%02x_%02x%02x%02x%02x%02x%02x`:
третя й далі групи друкуються **малими** літерами, тоді як ми назвали секцію
об'єкта повністю великими (`.967CBF11_B90E_4B54_A4D3_3C84249EE1DA`). Якби
лоадер будував ім'я секції цим форматом і порівнював з урахуванням регістру,
вузол не знайшовся б.

Перевірка на самому апараті: **31 вузол у ROM має літери в групах 3–5** — серед
них `AAC_ENC_SN`, `EAACPLUS_DEC_SN`, `G711_DEC/ENC_SN`, `G729_DEC/ENC_SN`,
`ILBC_DEC/ENC_SN`, тобто кодеки, які на цьому апараті працюють щодня, і всі
вони записані **великими**. Отже верхній регістр — робочий; або порівняння
складене (`CompareF`), або форматтер служить для іншого. UUID лишаємо як є.

**Чого ще нема:** точної відповідності «ordinal ↔ ім'я з контракту §14.1»
(`node_allocate` / `node_create` / `node_run` / `put_message`). Але для
реалізації завантажувача імена й не потрібні — потрібні коди ioctl і
розкладки аргументів, а вони тепер відомі з обох боків (C++ і ядро).

### 17.5. Еталонна послідовність із `CBal` — наш завантажувач більше не здогад

Три функції `bal.dll` дають готовий зразок, який лишається лише повторити.

**`CBal::Open` (`0x80A4165C`):**
```
LoadPhysicalDevice("EHWAOMAP")        ; фатально все, КРІМ -11 (KErrAlreadyExists)
LoadLogicalDevice("EHWA")             ; так само; інакше FreePhysicalDevice і вихід
r0 = this+4 (клас C)  r1 = 0  r2 = 0  r3 = 0
ord32(...)                            ; Open(aProcId=0 -> C55x, aFlag=0, aAttrs=NULL)
[this+56] = 1
if (err) CBal::Shutdown()
else     ord9(this+40 /*клас A*/, this+4 /*клас C*/)   ; прив'язка A до процесора
```

**`CBal::LoadImage` (`0x80A41642`):** `ord26(this+4, aPath, 0)`, а при помилці —
`CBal::Shutdown()`.

**`CBal::Shutdown` (`0x80A41608`):** `ord10(this+40)` → `ord33(this+4)` →
`FreeLogicalDevice("EHWA")` → `FreePhysicalDevice("EHWAOMAP")`.

**Що це дає.** Аргументи `ord32`, які ми вивели з дизасемблера самої функції
(`aProcId ∈ {0,1}`, `aFlag`, `aAttrs24`), збігаються **байт у байт** з тим, як
її кличе Nokia: `(C, 0, 0, NULL)`. Тобто точка входу перевірена двома
незалежними шляхами й здогадів у ній не лишилось. Так само підтверджено
сигнатуру `ord26(C, aPath, 0)` і відкрито наступний крок — `ord9(A, C)`.

`dsptest.exe` тепер дзеркалить саме цю послідовність (і порядок згортання
`ord10` → `ord33`), **свідомо пропускаючи** `Load/FreePhysicalDevice`: драйвер
уже піднятий системою, а ці виклики — головна підозра в ребутах (§17.7, пункт 4).

### 17.6. Хід розслідування ребутів (§16.8) — ARM-навантаження виправдано

Бісекція з витримкою (uptime у кожному прогоні — суцільний лічильник, тож
ребут одразу видно як скидання):

| прогін | що робив | uptime на старті | ребут? |
|---|---|---|---|
| контрольний | без DSP-стеку, **з** бенчмарком | 206 с | — |
| витримка +7 хв | без DSP-стеку, з бенчмарком | **666 с** | **ні** |
| scan | без DSP-стеку, без бенчмарку | 713 с | ні |
| (випадково з бенчмарком) | без DSP-стеку | 738 с | ні |
| `lib nobench` | **лише `bridgeapi.dll`** | 773 с | перевіряється |

> ## ⚠ УСЕ ПРО «ВІДКЛАДЕНИЙ РЕБУТ» НИЖЧЕ — ХИБНЕ (спростовано користувачем)
>
> Власник апарата, який спостерігав його наживо, повідомив: **апарат
> перезавантажується ОДРАЗУ**, а не через хвилини. «Затримку» я вигадав,
> вивівши її з того, коли користувач мене зупиняв, щоб повідомити про ребут —
> тобто з таймінгу *повідомлень*, а не з поведінки *апарата*. Це груба
> методична помилка: сторонній сигнал прийнято за вимірювання.
>
> Що з цього лишається чинним:
> - ребути прив'язані до прогонів, які чіпають DSP-стек;
> - прогін `load` убив апарат прямо під час роботи (з'єднання обірвалось на
>   `RUN`, лог лишився обірваним на `ord26`);
> - бісекція «по завантаженнях» і всі висновки про «7–15 хвилин затримки»
>   нижче — **недійсні**, бо будувались на хибній передумові.
>
> Лишаю текст як є, не переписуючи заднім числом: він показує, як хибна
> передумова тягне за собою ланцюг «підтверджень».

> **УВАГА, тут я двічі помилився і двічі виправлявся.** Спершу «винен
> DSP-стек», потім «винен не бенчмарк». Обидва рази помилка була та сама:
> висновок про ЗАВАНТАЖЕННЯ робився з поведінки ВСЕРЕДИНІ завантаження.
> Апарат може пережити прогін і перезавантажитись через 10 хвилин — тому
> одиниця спостереження тут не «прогін», а «завантаження цілком».
> Нижче — і хибні проміжні висновки, і те, що їх спростувало.

**ТРЕТІЙ РЕБУТ ПЕРЕКРЕСЛИВ ЦЮ ЛІНІЮ РОЗСЛІДУВАННЯ.** Повний ряд uptime:

| прогін | що робив | uptime | ребут після? |
|---|---|---|---|
| перший за сесію | DSP-libs + бенчмарк | 26350 с (7.3 год!) | **так** |
| після ребута | DSP-libs + `RDevice` + бенчмарк | 140 с | **так** |
| контрольний | нічого DSP, з бенчмарком | 206 с | ні |
| витримка +7 хв | нічого DSP, з бенчмарком | 666 с | ні |
| scan | нічого DSP, без бенчмарку | 713 с | ні |
| (з бенчмарком) | нічого DSP | 738 с | ні |
| `lib nobench` | лише `bridgeapi.dll` | 773 с | ні |
| витримка +7 хв | **нічого DSP, без бенчмарку** | 1215 с | **так** |

Останній ребут стався після прогону, який **не чіпав ні DSP-стек, ні
бенчмарк** — лише HAL, `TFindLogicalDevice` і `RFs::GetDir`. Отже:

- гіпотеза «винне вивантаження bal/dspmemmapper» — **не підтверджена**;
- гіпотеза «винне ARM-навантаження» — **не підтверджена**;
- натомість видно інший патерн: апарат до початку сесії стояв **7.3 години**,
  а відколи ми почали з ним працювати, живе приблизно **по 20 хвилин**.

Тобто корелює не конкретна проба, а сам факт нашої взаємодії (або щось
незалежне, що почалось одночасно). Кандидати, які ще не розділені: залишки
сусіднього проєкту в системі (`RomPatcherPlus.Driver`, `dvfs_interface` —
видно в переліку LDD), демон розгортання, стан живлення/батареї.

**Контроль «нічого не робимо» — виконано, і він усе перевернув.** Апарат
лишили в спокої: uptime 1331 с → простій 25 хв → **2881 с**, рівно
1331 + 1500 + накладні. Тобто **48 хвилин без ребуту**, з них ~45 хв повного
простою (два легкі `nobench`-прогони по краях).

Тепер порівняння правильною одиницею — по завантаженнях:

| завантаження | ARM-бенчмарк крутили? | скільки прожило |
|---|---|---|
| A | так, 1 раз (на 423 МГц) | ребут |
| B | так, 1 раз | ребут |
| C | так, 3 рази | ~1215 с (20 хв) → ребут |
| **D (поточне)** | **жодного разу** | **2881 с (48 хв), живе** |

**Кожне завантаження, у якому крутився ARM-бенчмарк, закінчилось ребутом;
єдине, де його не було, живе вчетверо довше.** Мій попередній висновок
«бенчмарк виправдано» був хибним: він спирався на те, що апарат вижив *між*
прогонами всередині завантаження C, тоді як ребут стався пізніше в тому ж
завантаженні.

Це правдоподібно і фізично: ~9 с суцільного 100% ALU (три ядра × best-of-3 +
розігрів + калібрування `SpinNop`) на апараті 2007 року, який сесія застала
розігнаним до 423 МГц, з живленням/батареєю невідомого стану.

**Однофакторний дослід — виконано, бенчмарк ТЕЖ спростовано.** На стабільному
завантаженні D прогнали повний бенчмарк (uptime 2961 с), потім 20 хв простою:
**uptime 4171 с (69 хв), безперервно**. Ребуту нема.

### 17.6.1. Правильна ознака знайдена: дотик до `bridgeapi.dll`

Якщо групувати завантаження не за бенчмарком, а за тим, **чи вантажився
`bridgeapi.dll`**, сепарація стає повною:

| завантаження | `RLibrary::Load(bridgeapi)` + `Close`? | прожило |
|---|---|---|
| A | так (+ `LoadLogicalDevice`) | ребут |
| B | так (+ `LoadLogicalDevice`, `RDevice`) | ребут |
| C | так — рівень `lib` на 773 с | ребут пізніше ніж +442 с |
| **D** | **жодного разу** | **69 хв, живе — попри повний бенчмарк** |

**Чому я тричі помилявся.** Кожного разу висновок робився з надто короткого
вікна: рівень `lib` перевірявся через 7 хв і виглядав чистим, а ребут у
завантаженні C стався пізніше. **Затримка тут ~7–15 хвилин**, тож будь-яке
вікно коротше за ~20 хв дає хибне «чисто». Це головний методичний урок цього
розслідування: одиниця спостереження — завантаження цілком, а мінімальне
вікно — 20+ хвилин.

**Механізм — правдоподібний і конкретний.** `bridgeapi.dll` має статичні
конструктори (цикл на `0x80A5D480`), а отже й статичні деструктори, які
виконуються при вивантаженні. Серед його рядків є **`BridgeDcdSync`** і
**`*BridgeDcdSync*`** — імена глобального м'ютекса (§10). Якщо його статична
де-ініціалізація закриває/видаляє глобальний об'єкт синхронізації DCD, яким
далі користується аудіо-стек, відкладена паніка ядра — очікуваний наслідок.

Ключовий нюанс: усе це станеться лише тоді, коли **ми єдиний власник**
бібліотеки. Якщо аудіо-стек тримає `bridgeapi.dll` завантаженою, наш
`Load`/`Close` лише рухає лічильник посилань і статичні деструктори не
запускаються. Тобто ризик залежить від того, чи грає щось на апараті.

### 17.6.2. Що це означає для завантажувача — рішення за користувачем

Ми не можемо просто «не вивантажувати»: у Symbian при завершенні процесу
хендл однаково закривається. Тому варіанти такі:

1. **Змиритись з одним ребутом на прогін.** Ребут відкладений, тож сам прогін
    встигає завершитись і лог забирається. Ціна — після кожного прогону
    потрібно вручну перезапускати демон на апараті.
2. **Тримати `bridgeapi.dll` завантаженою резидентно** (наприклад, самим
    демоном), щоб наш процес ніколи не був останнім власником.
3. **Обійти `bridgeapi` і працювати з каналом `Hwa` напряму** — карта ioctl у
    нас повна (§17.1, §17.2). Плюс: жодної статичної де-ініціалізації. Мінус:
    виклики йдуть у ядро, і помилка коштує ребута, а не падіння процесу.

Це рішення з ціною для користувача (варіант 1 — ручні перезапуски демона,
варіант 2 — зміна в сусідньому проєкті), тому воно за ним, а не за мною.

### 17.7. Сусідній проєкт уже все це проходив — два записи, що змінюють картину

`../SymbianOverclock/docs/state.md` і `WRITEUP.md`:

1. **`| 112+ | 430+ | — | авторебут через хвилини |`** — на множнику DPLL 112+
   (≈430 МГц і вище) апарат **сам перезавантажується через хвилини**.
   Наш найперший прогін цієї сесії виміряв **423 МГц** при uptime 7.3 год —
   тобто апарат був залишений **розігнаним**, майже на порозі авторебуту. Це
   пояснює перший ребут без жодної участі DSP-проб.
2. **WRITEUP §8 «Чотири "перезавантаження" — насправді жодного»**: там те, що
   спостерігач приймав за ребут, було **перезапуском оболонки Symbian**;
   відрізнити можна лише лічильником, який обнуляється тільки повним ребутом.
   Звідси й правило сусіда: «мережева доступність — не доказ того, що апарат
   не перезавантажився».

Тому `UPTIME:` першим рядком логу — не декорація, а головний прилад цього
розслідування. Підтверджено ним: ребути №1 і №2 **справжні** (лічильник
скидався: 26350 → 140, потім 140 → 206). Ребут №3 поки лише зі слів
спостерігача — контрольний прогін після простою покаже, чи був він справжнім.

**Що це означає для методики:** DSP-проби були звинувачені передчасно. Коректна
причинність поки така: апарат стартував сесію розігнаним до режиму з відомим
авторебутом, і принаймні перший ребут пояснюється цим, а не нашим кодом.

3. **Провідна гіпотеза для решти ребутів — теж із досвіду сусіда**
   (`state.md`, «Патч ядра мусить мати відкат»):

   > READ/EXEC-патч тіла `DoControl(1)` живе в ROM-shadow і **переживає наш
   > процес**. Канал `dvfs_interface` відкриває не лише наш код
   > (`mmrmserver.dll`, `fmradiotunercontrol.dll`), тож **лишений патч рано чи
   > пізно перезавантажує апарат**.

   У переліку LDD на апараті присутні і **`dvfs_interface`**, і
   **`RomPatcherPlus.Driver`**. Патерн «ребут рано чи пізно, незалежно від того,
   що робить наш код» — рівно те, що описує сусід. Наш проєкт цього патча не
   накладав і не має засобів його зняти; це питання до сеансу SymbianOverclock
   (там є `EndPatchSession()` з правильним порядком unshadow + перевіркою
   відкату через `DoControl(1,0)`).

4. **Найкраще обґрунтована причина ребутів №1 і №2 — наш власний
   `User::LoadLogicalDevice`.** Розбір `CBal` дає еталон того, як драйвер
   мосту належить піднімати (`0x80A4165C`):

   ```
   LoadPhysicalDevice("EHWAOMAP") -> r4
   if (r4 != 0 && r4 + 11 != 0) bail   ; фатально все, КРІМ -11
   LoadLogicalDevice("EHWA")
   ```

   Тобто Nokia явно очікує `KErrAlreadyExists` (−11) і вважає його нормою —
   ознака, що подвійне завантаження є відомою небезпекою. Парна до неї
   `CBal::Shutdown` (`0x80A41608`) робить зворотне: `ord10` (Close A),
   `ord33` (Close C), `FreeLogicalDevice("EHWA")`, `FreePhysicalDevice("EHWAOMAP")`.

   А наші перші два прогони кликали `User::LoadLogicalDevice("ehwa.ldd")` і
   діставали **`0`, а не `−11`**, хоча драйвер уже був у системі (його видно
   в переліку LDD як `Hwa`). Рівно за цими двома прогонами пішли ребути №1 і
   №2. Виклик прибрано ще до бісекції (замінено на пасивний
   `TFindLogicalDevice`), і відтоді жоден прогін із DSP-пробами ребуту не давав.

   **Статус — гіпотеза, не факт.** За неї: збіг 2 з 2, правдоподібний механізм
   (другий екземпляр драйвера мосту поряд із живим аудіо-стеком, і ми його не
   віддавали) і те, що сама Nokia в `CBal` явно готується до `−11`. Проти неї:
   ми не бачили ні паніки, ні дампа, а `KErrNone` від `LoadLogicalDevice` міг
   бути й нешкідливим. Довести можна лише повторенням саме цього виклику —
   чого робити не будемо: ціна перевірки (ребут) вища за цінність відповіді,
   бо виклик нам однаково не потрібен.

   Ребут №3 цим не пояснюється — він стався після прогону без DSP узагалі.
   Тобто причин щонайменше дві, і друга лежить поза нашим кодом.

**Що потрібно від користувача (єдине, чого не можна з'ясувати звідси):**
чи лишався накладеним dvfs/ROM-shadow-патч від сусіднього проєкту і чи
`RomPatcher+` не застосовує щось автоматично на старті. Поки це відкрито,
будь-яка бісекція наших проб міряє шум, а не сигнал.

**Дампів аварій на апараті нема:** усі шість типових шляхів MobileCrash
(`C:\logs\`, `C:\logs\mobilecrash\`, `C:\data\mobilecrash\`, `E:\mobilecrash\`,
`C:\mobilecrash\`, `E:\logs\`) дають `-12` (KErrPathNotFound) — crash reporter
на цьому апараті не встановлений, тож підтвердити паніку дампом не вийде;
лишається бісекція.

## Потоковий worker — апаратне підтвердження 2026-10-01

Власна TSK-задача у generic library2 обробила 8×512 Б без повторного
create на N95 і E90, залишаючи node у CREATED. Q15 dot results, echo,
sequence і stop correct. Штатний RUN не викликався. Output reclaim,
completion SEM, terminated3, task/SEM delete й звичайний cleanup пройшли
з FINAL/EXIT0. Useful ARM CRC64KiB перекривав DSP у трьох pairs на кожному.

Це новий канал порівняно зі старим create-only bench і невдалими RMS/MSG
experiments; їхні негативні журнали збережено. Успішна коротка серія
не доводить audio coexistence, довгу стабільність або прискорення програм.
N95 мав doubled timing intervals, DSPreportedcounts/ms164 потребує
калібрування. Сирі відсотки не є ізольованим виграшем від overlap.

Контракти, повні виміри й обмеження —
[STREAM_RESEARCH.md](STREAM_RESEARCH.md#потоковий-worker-у-created--v16-обидва-телефони),
[N95](evidence/2026-09-30/n95-worker-stream-v16-results.json),
[E90](evidence/2026-09-30/e90-worker-stream-v16-results.json).
Original DSP files/clocklogs restored readback-equal, PS0. Подальші
перевірки — стабільні частоти, timer calibration й application packets.

### V17: зіставні pairs і межі DSP-таймера

На N95 штатний dvfs_interface request0 резервує MPU100% і звільняє
reservation без patches; live native code перевірено. Три pairs без
doubled intervals: S250–251/P149–151ms, E90 S259–263/P156–160ms.
Correct Q15/echo/useful ARM CRC та чисте завершення у24 v17 runs.
Це~40% скорочення wall time тестового навантаження, не application gain.

Три calibration runs на кожному: короткі100–400ms intervals сумісні з
19.2MHz, але800ms idle дає лише~501ms DSP за цим масштабом проти828–876ms
ARM. Причина unknown; не пояснювати лише MPU DVFS і не ділити raw ticks
на164. Повна методика й bounds — STREAM_RESEARCH.md, докази —
docs/evidence/2026-10-01/{n95,e90}-worker-stream-v17-results.json.
Normal/original logs exact restored, PS0, hosts17 installed/readback-equal.

## V18: перевірені application-size packets, 2026-10-01

На N95/E90 host v18 + worker protocol18 пройшли22 runs/587 packets на
кожному. Generic library2, CREATED, без official RUN;32 packets за один
create, explicit stop, task/SEM/STRM/native cleanup, FINAL/EXIT0.
Перевірено512/1568/1792/2048/2304/4096 Б, включно з32-byte header.
WSOLA1760 Б payload уміщується в1792-byte input; MDEC1536 — у1568.
Q15 dot240, reps1000 та ARM CRC перевірено на8×4096 Б.

У worker-transfer reps0/no ARM CRC96 samples на size. Equal-size echo1792:
N95 median518/max549us; E90 median640/max7812us. Повільні correct packets
не вилучено; придатність actual WSOLA до hop≈4.99ms ще не доведена.
DCD не змінювався; size-bearing native instructions на обох ROM звірено.
Original DSP повернуто GET-equal; пізніший E90 status ще раз підтвердив
original clocklog, host v18 та PS0. N95 при пізнішій повторній звірці не
відповів; користувачу надіслано запит розбудити його. Це не змінює вже
збереженого exact recovery і не доводить поточну доступність N95.

Методика, усі latency samples, byte-exact journals, artifacts і обмеження:
`docs/PACKET_SIZES.md`, `docs/evidence/2026-10-01/` та `work/PLAN_V18.md`.
Raw binaries/firmware/ASM/keys/screenshots лишаються ignored. F05–F08
поки in_progress; повна мета ще потребує окремого completion audit.
