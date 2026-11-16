# TMS320C55x on N95 8GB: what has been established (initial gathering)

Historical gathering and chronology. Current conclusions 2026-10-01:
`WSOLA.md`, `STREAM_RESEARCH.md`, `../work/FINAL_AUDIT.md`.
Nominal 220MHz, general assessment of audio coexistence and early lifecycle
assumptions below are not confirmation of modern per-packet or audio measurement.

> Discipline of evidence as in SymbianOverclock: each point is either **confirmed on
> the device**, or **derived from ROM code / official datasheet**, or marked
> as **HYPOTHESIS**. Sources are in parentheses. Collection date: 2026-08-09.

## 1. What this DSP is and where it is in the SoC

- Device: **Nokia N95 8GB (RM-320)**, SoC **TI OMAP 2420**. The same device and
  ROM dump as in the neighboring project SymbianOverclock
  (`../eka2l1/data/drives/z/rm-320/`).
- OMAP2420 contains: **ARM1136** (stock 330 MHz), **TMS320C55x DSP** (stock
  ~220 MHz) and a separate **IVA** unit (Imaging & Video Accelerator — proprietary
  ARM7 + coprocessors). C55x and IVA are **two different** computational units. (web: TI/OMAP
  reviews, Wikipedia OMAP.)
- Local datasheets in the folder are **general** TI manuals for the C55x core:
  `TMS320C55x overview.pdf` = SPRU312 (functional overview),
  `TMS320C55x programming.pdf` = instruction set/programming. They describe
  **the core itself** (CPU, EMIF, EHPI, DMA, DPLL, IDLE domains, bootloader in ROM),
  but **not** the integration into OMAP2420 (mapping in SoC, mailbox, DSP MMU, PRCM).
  The integration part is provided by the **OMAP2420 Multimedia Processor TRM** — it must
  be obtained separately (see plan, Phase 0).

## 2. Hardware mailbox ARM↔DSP (confirmed from mainline Linux DT)

- **MAILBOX** block of OMAP2420: physical base **`0x48094000`**, size `0x200`,
  interrupts **26 and 34**. (kernel `omap2420.dtsi`, `ti,omap2-mailbox`.)
- 4 users / 6 FIFOs. Channel distribution:
  - **DSP (C55x):** tx = fifo0, rx = fifo1;
  - **IVA (ARM7):** tx = fifo2, rx = fifo3.
- Mailbox registers in the Linux driver are addressed with offsets like `+0x40/+0x44`
  (MESSAGE), plus FIFOSTATUS/IRQSTATUS/IRQENABLE — take the exact map from TRM.
- Consequence: ARM↔DSP channel exists in hardware and the address is known. This is the base for any
  access path.

## 3. Symbian ITSELF manages this DSP — complete stack in ROM (key fact)

The DSP on this device is **neither empty nor disabled**: the firmware loads its own
firmware onto it and uses it for audio/multimedia. In the ROM dump
(`.../sys/bin`) an entire stack was found:

| Module | Role (from name; needs confirmation via disassembler) |
|---|---|
| `ebridgeutil.ldd` | **kernel-side DSP bridge** — kernel channel to DSP (analogue of TI DSP/BIOS Bridge / Nokia DSP Gateway) |
| `mailboxipc.dll` | IPC via hardware mailbox (§2) |
| `mrmailboxutils.dll` | mailbox wrapper |
| `dspmemmapper.dll` | **DSP memory mapping** into ARM space |
| `activeadsp.dll` | "Active Audio DSP" — user side of audio DSP |
| `einfoadspplugin.dll`, `idspluginhandler.dll` | DSP plugins/handlers |

**Consequence for strategy.** Access to the DSP is **not** "booting an empty
core from scratch", but either (A) coexisting with the Symbian stack via `ebridge`/mailbox,
or (B) taking the DSP away from the audio subsystem for the duration of the test and returning it. Both paths
depend on dissecting these modules (Phase 1).

## 4. Potential primitive: `memoryaccess.ldd`

- In ROM there is **`memoryaccess.ldd`** (8532 B — the largest of the drivers in the list).
  The name corresponds to the well-known homebrew driver for direct memory access.
- **Discrepancy to be resolved:** the SymbianOverclock inventory (§11
  findings) **did not name** `memoryaccess.ldd` in the list of LDDs providing MMIO
  (there were only `d_display`, `d_powerapi`, `custom`, `secldd`, `sosadlserver`,
  `xbus`) — because it searched for kaomap primitives import, while this driver might map
  memory itself. If `memoryaccess.ldd` provides user-side Read/Write at a physical
  address of proper bit width — this is a **substantially simpler** primitive than the entire
  patcher.ldd chain, and useful to both projects. **Analysis priority.**

## 5. What is already ready (inherited from neighboring projects)

- **Delivery channel:** `SymbianDeployDaemon` — uploading `.exe` via WiFi, launch,
  fetching log (`tools/deploy_net.ps1`). Device is dev-unlocked (Install Server).
- **Kernel-mode primitives (SymbianOverclock §18), without Kernel DevKit:**
  1. reading arbitrary kernel address (ROM-shadow patch `dvfs_interface.ldd`
     `DoControl(1)`);
  2. **execution of arbitrary kernel code** (the same patch, `bx r1`) — this is
     the universal lever for any MMIO (PRCM, CONTROL, DSP MMU, mailbox);
  3. SRAM staging area outside SDRAM (phys `0x4029E000`, linear on device `0xCB202000`).
- **kaomap primitives** Read32/Write32/Modify32 (MMIO mapping phys+0x7E000000
  for window `0x48xxxxxx`) — mailbox window `0x48094000` falls here.
- **ROM dump** of the entire device in `../eka2l1/data/drives/z/rm-320/` — source for
  disassembly (`objdump -D -b binary -m arm --adjust-vma=<iCodeAddress>`
  after stripping 120-byte `TRomImageHeader`).
- **Decompression of ROM-E32:** `../SymbianOverclock/tools/syminflate.js` (custom
  Symbian-inflate) — in case of compressed DSP stack modules.

## 6. Limitations and risks (known in advance)

- **No Kernel DevKit** → nothing to build our own LDD with; either third-party drivers or
  the kernel code exec primitive (§5).
- **DSP is occupied by audio subsystem.** Taking the DSP may break sound; must
  stop/restore correctly or coexist. The test must not leave the device in a
  state where sound is dead until reboot.
- **C55x is a 16-bit fixed-point DSP.** Floating-point is not present in hardware (emulation).
  A fair benchmark is fixed-point/dual-MAC (FIR, dot-product, block FFT) plus
  a control integer one; "DSP vs ARM" comparison must be on a class of tasks where
  the DSP was created to shine, and separately on neutral code. (SPRU312.)
- **Coherence of shared memory / DSP MMU / cache** — a separate hassle (dspmemmapper).
- **Neighbor's toxic rule:** nothing into flash, everything runtime, reboot restores
  device to original state; do not repeat the same thing after two failures.

## 7. Open questions (included in the plan as tasks)

1. Does `ebridge`/`activeadsp` provide **loading of arbitrary code** onto DSP, or
   only fixed audio nodes? (Phase 1)
2. Is `memoryaccess.ldd` a ready user-side MMIO primitive? (Phase 1)
3. Exact register map: PRCM DSP domain (clock/reset), CONTROL IVA/DSP boot,
   DSP MMU, mailbox — from OMAP2420 TRM. (Phase 0)
4. Toolchain for C55x: TI `cl55`/CCS or open-source — and format of raw image +
   DSP boot vector. (Phase 0)
5. How Symbian **loads** DSP firmware at boot — to replicate the mechanism or
   cleanly pause it. (Phase 1)

## 8. OMAP2420 register map (Step 1 — derived from code; TRM unavailable)

> **TRM status:** OMAP2420 Multimedia Processor TRM = **SWPU064** (rev D),
> WTBU/NDA document — no public PDF exists (`ti.com/lit/.../swpu064d.pdf` → 404,
> `web.archive.org` is blocked in the environment). Therefore the map below is **derived from
> mainline Linux** (`arch/arm/mach-omap2`, `plat-omap`, tags v3.2/v3.10), which
> TI code directly quotes as the equivalent of SWPU064. Each address has a source file;
> bit width marks denote 32-bit access (neighbor's lesson §10).

### 8.1. Physical bases (from `plat/omap24xx.h`)

| Block | Macro | Phys address | In kaomap window `0x48xxxxxx`? |
|---|---|---|---|
| L4-core / **CONTROL(SCM)** | `OMAP242X_CTRL_BASE` = `L4_24XX_BASE` | `0x48000000` | yes |
| **PRCM** (PRM=CM, alias) | `OMAP2420_PRCM_BASE` | `0x48008000` | yes |
| **Mailbox** | `OMAP24XX_MAILBOX_BASE` | `0x48094000` | yes |
| DSP **memory** port (from L3) | `OMAP2420_DSP_MEM_BASE` | `0x58000000` | **NO** |
| DSP **IPI** | `OMAP2420_DSP_IPI_BASE` | `0x59000000` | **NO** |
| DSP **MMU** | `OMAP2420_DSP_MMU_BASE` | `0x5A000000` | **NO** |

**Consequence for primitives:** PRCM/CONTROL/mailbox fall into the neighbor's kaomap window
(phys+0x7E000000) → accessible via existing Read32/Write32/Modify32. And **DSP memory,
IPI and MMU (`0x58/0x59/0x5A`) are outside this window**; for Path B they need
a separate mapping (custom kaomap range or `memoryaccess.ldd`, if it maps
arbitrary phys address). This is a new, concrete requirement for Phase 1.

### 8.2. DSP domain in PRCM (base `0x48008000` + `OMAP24XX_DSP_MOD` `0x800` = `0x48008800`)

Offsets of CM/PRM within the domain — from `cm2xxx_3xxx.h` / `prm2xxx.h`:

| Register | Offset | Abs address | Purpose |
|---|---|---|---|
| `CM_FCLKEN_DSP` | `+0x00` | `0x48008800` | DSP func clock |
| `CM_ICLKEN_DSP` | `+0x10` | `0x48008810` | DSP interface clock |
| `CM_IDLEST_DSP` | `+0x20` | `0x48008820` | idle status (whether brought up) |
| `CM_AUTOIDLE_DSP` | `+0x30` | `0x48008830` | autoidle |
| `CM_CLKSEL_DSP` | `+0x40` | `0x48008840` | DSP frequency divider |
| `CM_CLKSTCTRL_DSP` | `+0x48` | `0x48008848` | clock domain control |
| `RM_RSTCTRL_DSP` | `+0x50` | `0x48008850` | **DSP reset** |
| `RM_RSTST_DSP` | `+0x58` | `0x48008858` | reset status |
| `PM_PWSTCTRL_DSP` | `+0xE0` | `0x480088E0` | power state control |
| `PM_PWSTST_DSP` | `+0xE4` | `0x480088E4` | power state status |
| `PRCM_IRQSTATUS_DSP` | `+0xF0` | `0x480088F0` | domain IRQ status |
| `PRCM_IRQENABLE_DSP` | `+0xF4` | `0x480088F4` | domain IRQ enable |

**`RM_RSTCTRL_DSP` bits (from hwmod reset lines 2420):** bit 0 = **logic reset**
(DSP core), bit 1 = **MMU reset**. This is the lever to take/restore DSP in Path B.

### 8.3. DSP boot on 2420 — NOT via CONTROL boot-addr

Important: `omap_ctrl_write_dsp_boot_addr()` in kernel has branches only for
**243x/34xx/44xx** (registers `CONTROL_IVA2_BOOTADDR/BOOTMOD`) — for **2420 no branch
exists**. That is, C55x on 2420 starts **not** from a CONTROL register boot address, as
later C64x/IVA2 do, but via **C55x reset vector + DSP MMU** (classic C55x scheme,
SPRU312). This directly shapes the mechanism of Path B and distinguishes our chip from 2430+.

### 8.4. Mailbox (clarification to §2)

Base `0x48094000`; DSP: tx=fifo0, rx=fifo1; IRQ 26 (DSP), 34 (IVA) —
confirmed from 2420 hwmod data. Complete map of MESSAGE/FIFOSTATUS/IRQ registers —
from omap2-mailbox driver (Phase 1, along with reversing `mailboxipc.dll`).

**Open questions resolved by Step 1:** item 3 of "open questions" (map of PRCM/CONTROL/
MMU/mailbox) — for PRCM/CONTROL/mailbox resolved by addresses above; only the
**internal** DSP MMU map (TLB/CAM/RAM) remains — take it from omap-iommu (Phase 1).

## 9. Reversing `memoryaccess.ldd` and `ebridgeutil.ldd` (Step 2)

Method: `SymbianOverclock/tools/romtool.ps1` (strip 120 B `TRomImageHeader`,
`objdump --adjust-vma=iCodeAddress`, resolve import stubs against `ekern.exe`).
Artifacts: `SymbianOverclock/out/asm/{memoryaccess,ebridgeutil}.ldd.asm`.

### 9.1. `memoryaccess.ldd` — object driver for task manager, NOT MMIO

- Header: iCodeAddress `0x8038D848`, code `8524` B, 1 export, **59 import
  stubs** from `ekern.exe`.
- Class `DMemoryAccess`, driver name **`MemoryAccess`/`MemAccess`**; signature in
  code: *"Checked by MEMORYACCESS.LDD (Memory Access for Task Managers)"*.
- `DoControl` — **jump table for 17 commands** (`cmp r4,#16; addls pc,pc,r4,lsl#2`
  at `0x8038EA1C`), not 4. Log strings name only 4: `EControlGetObjectInfo`,
  `GetObjectInfoByPtr`, `GetObjectInfoByHandle`, `ObjectDie`.
- **Handler reverse engineering (sample idx1 `0x8038E7EC`, idx5 `0x8038E44C`):** each
  allocates a buffer (0x1280 / 0x2240 B), calls an internal resolver and **copies
  kernel object metadata** (DThread/DProcess fields at fixed offsets +0x20/
  +0x24/+0x5C/+0x68/+0xB4..., list of up to **1024** code segments) into user buffer.
  That is, this is **object introspection** (+ `ObjectDie` = process/thread kill),
  and **not** arbitrary R/W by address.
- **Conclusion:** this ROM `memoryaccess.ldd` is of the homebrew **MemoryAccess lineage**, but
  built as a **kernel object enumerator/killer for task manager**. Arbitrary
  phys/kernel Read/Write (as in the full homebrew variant) is **not present** among sampled
  commands. This **resolves discrepancy §4 in favor of neighbor's §11**: the driver
  **cannot** be cited as an MMIO primitive. (Caveat: a fraction of the 17 handlers
  was sampled; full list is low priority, as both purpose and signature
  point to objects. Plus the driver is Nokia-signed and, most likely,
  capability-gated — separate question whether our exe opens it at all.)
- **Consequence for gate:** no MMIO shortcut exists → Path B for window `0x48xxxxxx`
  (PRCM/mailbox) relies on inherited kernel exec primitive (§5), while for
  `0x58/0x5A` (DSP memory/MMU) a separate solution is needed anyway.

### 9.2. `ebridgeutil.ldd` — DSP bridge memory kernel helper (completely disassembled)

- Header: iCodeAddress `0x801B5888`, code `1252` B, 1 export, 26 imports.
  Class `DBridgeUtilDevice` (+ `DBridgeUtilChannel`), name **`BridgeUtil`**.
  This is a **thin** util, not a heavy bridge.
- Channel DoControl (`0x801B5AA4`) — only **2 commands**:
  - **fn 1** (`0x801B5AE4`): takes {linear address, size} from user, page by page
    (step 4 KB) calls `ekern +0xE718` (**Epoc::LinearToPhysical**) and builds
    a table of pairs **{linear page, phys page}** back into user buffer —
    scatter list of buffer phys addresses for passing to DSP.
  - **fn 2** (`0x801B5AC4`): two calls `ekern +0x943C` / `+0x944C` with (addr,len)
    — **cache clean/flush** (DMA synchronization).
  - other codes → string *"!!!!!!!! Not supported !!!!!!!!\"*.
- **Conclusion:** DSP shared buffers are addressed **physically** with **manual cache
  management** — critical for coherence in Phases 2–3. `ebridgeutil.ldd` **does not
  load** code onto DSP; this is page address translation and cache utility for bridge.
  Pin/unpin API call is not in fn1; lifetime/pinning native chunk still needs to be
  confirmed. [N95/E90 audit 2026-10-03](DMM_ABI_2026-10-03.md).

### 9.3. The real DSP bridge — `bridgeapi.dll` (next target)

In ROM (`sys/bin`) a complete bridge stack was found; by size and name it is
**TI DSP/BIOS Bridge (dspbridge)**:

| Module | Size | Role |
|---|---|---|
| **`bridgeapi.dll`** | **20544** | **user-side DSP Bridge API** — `Processor_Load`/`Node_Create`/`Node_Run` expected here (loading COFF node onto DSP) |
| `mrmailboxutils.dll` | 5200 | mailbox utilities |
| `mailboxipc.dll` | 3748 | IPC via hardware mailbox |
| `idspluginhandler.dll` | 5268 | DSP plugin handler |
| `activeadsp.dll` | 4128 | Active Audio DSP (client) |
| `dspmemmapper.dll` | 1336 | user wrapper over `ebridgeutil` (DSP memory mapping) |
| `bridgecfg.dll` | 1228 | bridge config |
| `einfoadspplugin.dll` | 608 | audio plugin |

**Consequence for GATE A/B:** if `bridgeapi.dll` exposes node loading —
Path A is drastically more attractive: the bridge already solves the hardest parts (code load, DSP MMU, cache,
mailbox protocol). Therefore **the highest-value next target is reverse engineering
`bridgeapi.dll`** (searching for Processor/Node Load/Create/Run exports and format of
COFF node image).

## 10. `bridgeapi.dll` = TI DSP/BIOS Bridge — dynamic DOFF loader (Step 2, continued)

Header: iCodeAddress `0x80A5D458`, code `0x5040`, iUid3 `0x10006914`,
**39 exports** (`iExportDir=0x80A6192C`). Imports: `euser.dll`, **`efsrv.dll`**
(file server — reads node images from disk), `drtaeabi.dll`, `scppnwdl.dll`.

**Identification from strings is unambiguous.** This is a port of **TI DSP/BIOS Bridge**
(dspbridge) with built-in **dynamic DOFF/COFF loader** (DLOAD):

- Driver: `Open UTIL Driver: %d`, `utilDrv.LinearToPhysical: %d`,
  `utilDrv.FlushDataCache` → opens **BridgeUtil = `ebridgeutil.ldd`** and
  uses precisely fn1/fn2 from §9.2 (cross-confirmation).
- DOFF loader: `Bad DOFF version 0x%x`, `Bad target ID 0x%x`, `Bad coff operator
  0x%x`, `Expression stack overflow`, `Relocation value 0x%x overflows %d bits`,
  `Undefined external symbol %s`, `Symbol table addition failed`,
  `Target memory allocate failed, section %s size 0x%x`, `%s to target address
  0x%x failed`, `Write to 0x%x failed`,
  sections .cinit`, `.dllview`,
  `.dcd_register`, `.dspbridge_deplibs`.
- Nodes/DCD: `BridgeDcdSync`, `*BridgeDcdSync*`, GUID formatter
  `%08X_%04X_%04x_%02x…` → **DSP nodes are identified by UUID and registered in DCD**
  (DSP/BIOS Configuration Database). `Hwa.Omap`, `__DLModules`.

**Code execution mechanism on DSP (classic dspbridge):** DSP program = **DOFF
node image** (created by TI toolchain, with create/execute/delete phases and UUID);
loader parses DOFF, performs relocations, allocates DSP memory, writes sections into DSP
address space (via BridgeUtil LinearToPhysical + DSP MMU + mailbox), registers
node in DCD; then node API runs the node and exchanges messages/streams.

**Export map (ordinal → address; names absent in ROM — C++ class, pairs aliased):**
`1→0x80A5E483 2→0x80A5E539 3→0x80A5E68F 4→0x80A5E6BB 5→0x80A5E561 6→0x80A5E585
7→0x80A5E677 8→0x80A5E4DF 9→0x80A5E43F 10→0x80A5E409 11/12→0x80A5E401
13/14→0x80A5E433 15→0x80A5DC71 16→0x80A5DC37 17→0x80A5DCDB 18→0x80A5DCA1
19→0x80A5DD0B 20→0x80A5DD1B 21/22→0x80A5DC2D 23/24→0x80A5DC35 25→0x80A5DAE1
26→0x80A5D533 27→0x80A5D9B1 28→0x80A5DAC3 29→0x80A5D901 30→0x80A5D87F
31→0x80A5D9ED 32→0x80A5D751 33→0x80A5D4FD 34→0x80A5DAA3 35→0x80A5D955
36/37→0x80A5D4C9 38/39→0x80A5D4D9` (`bridgeapi.dll.asm` in out/asm/).
Map ordinals to API names in Phase 2 (from log strings of each function +
experiments on the device).

## 11. DECISION GATE A vs B — resolved (from evidence of Steps 1–2)

| | **Path A — node via `bridgeapi.dll`** | **Path B — controlled capture of DSP** |
|---|---|---|
| Mechanism | build custom DOFF node with UUID, register in DCD, load via bridge, drive node messages | gate DSP domain (§8), map `0x58/0x5A`, stop/reset DSP, inject raw C55x blob, reset vector, run, read result |
| Hardware risk | **low** — DSP reset not needed, coexistence with audio | **higher** — kills DSP/BIOS audio until reboot (acceptable by rules) |
| What we already have | export map, confirmed mem/cache mechanism | **complete register map (§8)**, kernel exec primitive, reset bits `RM_RSTCTRL_DSP` |
| Benchmark purity | worse — DSP/BIOS overhead + node IPC | **better** — direct cycle count without RTOS |
| Toolchain | TI cl55 **+ dspbridge node SDK + DCD registration** | TI cl55 (raw asm/link only) |
| Main blocker | **DCD on retail device might be fixed in ROM** (whether new UUID can be added dynamically is unknown); reverse engineering 39-export API | exact **C55x reset vector on 2420** (internal DSP MMU — from omap-iommu, Phase 1) |

**Decision: start with Path B.** Reasons: (1) lighter toolchain — raw C55x
assembler only, without node SDK and without undefined DCD registration; (2) cleaner measurement
(project goal is benchmark); (3) almost all primitives are already ours (mapping
`0x58/0x5A` remains — trivial via kernel exec primitive, and reset vector — Phase 1);
(4) complete control = bridgehead for any DSP projects. Path A is left as
later "production coexistence variant", once base is proven.

**COMMON BLOCKER for both paths — C55x code-gen.** No open-source mature C55x
assembler exists (naken_asm etc. do not support C55x). **TI C5500 Code
Generation Tools (`cl55`)** needed — free, but proprietary; included in Code
Composer Studio or standalone package. Installing it is a step requiring
the user (click-through license, possible TI login on download).

## 12. Complete set of dspbridge sample nodes lies on device (GATE REVISED → Path A)

Scan of Z: found ready **DOFF images of C55x nodes** and DSP/BIOS base:

| File | Size | What it is |
|---|---|---|
| `resource/plugins/baseimage.dof` | 155756 | **Nokia audio base DSP/BIOS** (== `dynbase.dof55l`): `COMMON_NOKIA_eCntr`, `SRC_TII_FILTER` (SRC), EAP, `.dman` (dynamic loader on DSP), `.bridge`, DARAM/SARAM/SHMSEG heaps |
| `system/apps/ping/Ping.dof55l` | 51268 | **PING node** (static), TI sample |
| `system/apps/ping/pingdyn.dll55l` | 4092 | **PING node dynamic** — proof of runtime loading |
| `system/apps/{scale,dmmcopy,strmcopy}/*.dof55l` | — | standard dspbridge samples (scale/dmmcopy/strmcopy) |
| `system/data/Iva_base.dof` | — | base for IVA (separate coprocessor) |

**DOFF format confirmed:** Ping header — `... 03 02 01 00 ...` (DOFF
byte-order magic, exactly what bridgeapi checks §10). Sections: `.text .cinit
.bios .bridge .sysinit .dcd_register .dspbridge_symbols`.

**UUID of nodes (from `.dcd_register`):**
- **PING = `12A3C3C1-D015-11D4-9F69-00C04F3A59AE`** (the same in Ping.dof55l and
  pingdyn.dll55l); phases `_PING_TI_create/execute/delete`, exchange
  `_NODE_putMsg/getMsg`.
- **RMS (Resource Manager Server) = `93FA56D0-6FE5-11D4-B747-006008BDB66F`** —
  standard dspbridge RMS; present both in base and in ping (receives node commands
  via mailbox).

### GATE REVISED: Path A (new evidence outweighs)

Decision §11 (Path B) was made BEFORE discovery of these samples. New evidence:
1. **Dynamic node loading proven working on device** (`pingdyn.dll55l`
   + `.dman` in base) — main doubt of Path A (whether DCD is closed) removed: registration
   is dynamic.
2. Ready **DOFF samples** exist on device — both a template for own node, and a target for
   first launch.
3. Path A does not touch DSP reset → **audio does not break**, lower risk.

**New plan:**
- **Milestone 1 "Hello, DSP" — WITHOUT toolchain:** trigger existing **PING node**
  (UUID `12A3C3C1…`) via `bridgeapi.dll` → allocate/create/run + node-ping
  messages → proof of code execution on DSP. cl55 is NOT needed here.
- **Milestone 2 "Benchmark":** build own C55x node with Q15 kernels (template —
  ping/pingdyn) — here **cl55** is already needed (+ node SDK/DCD description).

**Consequence for `cl55`:** for Milestone 1 toolchain is NOT needed → can make
progress autonomously (reverse engineering node-load API in `bridgeapi.dll`). `cl55` becomes needed
only at Milestone 2.

**Remains to analyze (Milestone 1):** mapping 39 exports of `bridgeapi.dll` to
sequence attach-processor → node-allocate(UUID) → node-create → node-run →
put/get-msg; and who on ARM side normally drives bridge (likely `activeadsp.dll` —
direct import stubs in ROM are not visible due to XIP IAT linking, not via
`E51FF004`).

## 13. TI C5500 CGT installed and validated on our code (2026-08-09)

- Installed: `C:\Program Files (x86)\Texas Instruments\C5500 Code Generation
  Tools 4.4.1\bin\` — cl55/asm55/lnk55/ar55/hex55 + **dis55, ofd55, nm55**.
- **Output format confirmed correct:** `ofd55` on test `.obj` →
  **"TI-COFF Version 2, Machine: TI C55x"**, memory model small, calling
  c55_std. Exactly what DOFF loader `bridgeapi.dll` expects (§10).
- **Our 3 benchmark kernels compile optimally** (`src/dsp/bench_dsp.c`,
  `cl55 -v5510 -o3`):
  - `dsp_q15_dot` → `RPT CSR` + `MACM *AR1+,*AR0+,AC0,AC0` (1 MAC/cycle in 40-bit AC);
  - `dsp_q15_fir` → `RPTBLOCAL` (across samples) + nested `RPT CSR; MACM` (across taps);
  - `dsp_blk` → `RPTBLOCAL; MPYMK *AR0+,#3,AC1` (neutral).
- **`ofd55`/`dis55` do NOT read `.dll55l`/`.dof55l`** ("failed to read") — this is DOFF,
  not raw COFF. Confirms: COFF→DOFF conversion is done by a **separate dspbridge
  utility** (not in base CGT).

**State of Milestone 2:** C55x compilation/assembling/linking — **done**. Only one thing
remains: **dspbridge dsp-side package** (COFF→DOFF utility + node wrapper/headers +
DSP/BIOS if needed) — to wrap `bench_dsp.obj` into a `.dll55l` node (lighter
dynamic variant, like `pingdyn`, links against base symbols — without full
BIOS). C55x types trap: on C55x `int`=16 bits, `long`=32, AC=40 — kernels written with
this in mind (16-bit counters ok for n≤8192, accumulator `long`).

## 14. DSP node built to relocatable COFF; ARM API contract fixed (2026-08-09)

### 14.1. ARM-side node-load API (from `felipec/dsp-dummy` dsp_bridge.h — bridgeapi analogue)

Open Linux analogue of `bridgeapi.dll`. Canonical sequence (what our
ARM loader must reproduce via 39 bridgeapi exports — the "key" to
Milestone 1):
```
h = dsp_open()                        # /dev/DspBridge <-> RBusLogicalChannel
dsp_attach(h, 0)                      # attach to DSP processor
dsp_reserve(h, size) + dsp_map(...)   # DMM: map ARM buffers into DSP space
dsp_node_allocate(h, proc, &UUID)     # allocate node by UUID
dsp_node_create(h, node)
dsp_node_run(h, node)
dsp_node_put_message / get_message    # exchange {cmd,arg_1,arg_2}
dsp_node_terminate(h) / dsp_node_free / dsp_detach / dsp_close
```
Plus `dsp_flush/dsp_invalidate` (ARM-side cache), `dsp_register_notify`,
`dsp_enum`, `dsp_register` (dynamic DCD registration of node). These ~30 operations
correspond to 39 bridgeapi ordinals (aliased pairs = const/non-const).

### 14.2. Node model (dsp-dummy + Ping template)

Three phases `create/execute/delete`; `execute(env)` spins `NODE_getMsg` → process
cmd → `NODE_putMsg`; messages `{cmd,arg_1,arg_2}` (3×32-bit); cache on DSP —
`BCACHE_inv` (before read) / `BCACHE_wbInv` (after write).

### 14.3. Our node is built (except DOFF)

`src/dsp/bench_node.c` + `node.h` + `bench_dsp.c` → `cl55 -v5510 -o3
--mem_model:data=large -c` → `lnk55 -r -cr` → **`bench.x55` = TI-COFF v2,
TI C55x, relocatable** (`tools/build_dsp_node.cmd`). Symbols:
- **T (defined by us):** `_bench_create/_delete/_execute`, `_dsp_q15_dot/_fir`,
  `_dsp_blk`;
- **U (resolved by base upon DOFF-load):** `_NODE_getMsg/putMsg`,
  `_BCACHE_inv/wbInv` — exactly as in `pingdyn`.

### 14.4. DOFF blocker REMOVED — full DSP build on Windows (2026-08-09)

`doffbuild` (with **`dllcreate.exe` — PE32 Windows**, not just Linux `DLLcreate`)
extracted from `bridge-tools.tar` in repo **`kpykc/userspace-dspbridge`** (mirror of
dev.omapzoom.org tidspbridge). Installed in
`toolchain\ti\dspbridge\dsp\doffbuild`. `DLLdump.exe`, `dbsymgen.exe`,
`dynmap.exe` are also present.

**The entire chain works natively on Windows** (Linux VM NOT needed):
`cl55 -c` → `lnk55 -r -cr` → `dllcreate.exe bench.x55 -o=bench.dll55l`. A single
command `tools\build_dsp_node.cmd` → **`out/dsp/bench.dll55l`** (7672 B).
Verification: `DLLdump.exe` → "Verifying Sections.. PASSED"; header matches
reference `pingdyn.dll55l` (DOFF magic `03 02 01 00` at offset 8). Notes:
pass `-o=` via cmd/bat (PowerShell mangles `=`); parentheses in `echo` inside
`if()` block of bat-file break the flow (`goto` used).

**Milestone 2 DSP-side state: DONE** — own node builds from source into
loadable DOFF. Remains (requires device): (1) assign node a **UUID +
DCD record** (our minimal node still has no DCD object — need `.dcd_register` with
UUID, as in ping) — **done, §15**; (2) **ARM loader** in `dsptest.exe` —
drive `bridgeapi.dll` according to contract §14.1 (allocate/create/run/msg);
(3) run on N95.


## 15. DCD format decoded; our node registered under own UUID (2026-08-10)

Method: `DLLdump.exe` (doffbuild) on reference nodes from ROM + direct parsing of
DOFF sections. Strings in C55x DOFF sections lie **one character per 16-bit
word** (`00 XX`, big-endian) — hence the extraction script.

### 15.1. Two sections that make the node visible

A DOFF node is registered with two **unallocated** sections (DOFF flags
`0x101`: "no space allocation / no download" — the ARM side reads them from the file, they
do not go to the DSP):

| Section | Content |
|---|---|
| `.dcd_register` | index: "<UUID_with_underscores>:<type>," for each object; **type 0 = node, 1 = processor/RMS** |
| .<UUID_with_underscores> | the object itself: 31 fields separated by commas |

Reference example (`pcmdll.dll55L`, 5896 B — smallest **production** Nokia node,
taken as template): `.dcd_register` = 39 characters = `0x4e` bytes.
`baseimage.dof` registers three objects in a single index (`EAP_TASK`,
`TESTSERVER_NOKIA` + RMS `93FA56D0…:1`).

### 15.2. Map of 31 node fields (derived from 28 objects in ROM)

Order and values confirmed by cross-check: field 4 = `02H` in exactly those nodes
named `*SOCKET*` (DAIS-socket) and `01H` in task nodes; field 29 = `0` in exactly
the static ones (`Ping.dof55l`, nodes inside base) and `1` in exactly the dynamic ones
(`pingdyn`, all `*_SN.dll55L`).

```
 1 cb_struct=1024      2 UUID              3 name           4 ntype(1=task,2=socket)
 5 cache_on_gpp        6 req.cb_struct     7 staticData     8 globalData
 9 progMem            10 wcExec           11 wcPeriod      12 wcDeadline
13 avgExec            14 minPeriod        15 prio          16 stack
17 sysStack           18 stackSeg         19 msgDepth      20 nIn   21 nOut
22 timeout            23/24/25 create/execute/delete (names WITHOUT underscores)
26 00H  27 08000H     28 algName          29 loadType(0=static,1=dyn)
30 dataMemSegMask     31 codeMemSegMask
```

Fields 7–14 are identical across **all** 28 ROM objects → copied verbatim. Fields 26/27
are also constant everywhere; semantics not established (marked as "copy").

**Priority range — from device, not from guessing:** RMS object
(`93FA56D0…`, type 1) in `baseimage.dof` gives `node_min_priority=01H`,
`node_max_priority=0fH`, as well as `processor_family=0157cH` (**5500**) and
`processor_type=01586H` (**5510**) — independent confirmation that base was built
specifically for our C5510.

**Segment masks:** all Nokia nodes built for **this** base (Aug 2007)
use the pair `0ff3f3f00H` / `0ff3f3f02H`; TI samples `pingdyn`/`scaledyn`
(2006) — `…00H`/`…01H`. We take the majority one, native to device.

### 15.3. CRITICAL: NO `BCACHE_*` in base — node with them would not load

Symbol table of `baseimage.dof` extracted completely (**1678 symbols**,
`DLLdump`). Verification of each extern of our node:

| Symbol | In base | Consequence |
|---|---|---|
| `_NODE_getMsg`, `_NODE_putMsg`, `_c_int00` | yes | ok |
| `_BCACHE_inv`, `_BCACHE_wbInv` | **NO** | "Undefined external symbol" on load |
| `_CLK_gethtime`, `_CLK_countspms` | yes | **new instrument, see 15.4** |

`BCACHE` is DSP/BIOS API for **C64x**; we took it from `dsp-dummy` (C64x-oriented
sample, §14.2). On C55x the cache is **instruction only** (base exports
`_ENABLEICACHE` / `_ICache_Flush`, no `BCACHE_*`) — **data** cache on C55x
is absent, so DSP side has nothing to maintain; coherence is kept by ARM side via
`ebridgeutil` clean/flush (§9.2). BCACHE calls removed from `node.h`/`bench_node.c`.

This is an example of why "take from analogue" must be verified against symbols of **this**
base, not from an upstream sample.

### 15.4. DSP-side timing instrument found (closes Phase 3.3)

Base exports `_CLK_gethtime` (high-resolution counter) and
`_CLK_countspms` (cycles of this counter per millisecond). The node now measures
**itself** and returns `ticks` + `countspms` in the parameter block — this is the
"second independent measuring needle" required by Phase 4, now **on DSP side**,
independently of ARM's `User::FastCounter`. Also available: `_STS_*`,
`_TSK_setpri`, `_GBL_freq`.

### 15.5. What was done in code

- **Node UUID: `967CBF11-B90E-4B54-A4D3-3C84249EE1DA`** (v4). Verified against
  **all 28** DCD objects of device — no collisions.
- `src/dsp/bench_dcd.s55` — `.dcd_register` + `.<UUID>` + `.dspbridge_symbols`
  by hand (normally tconf generates them from `.cdb`, which we do not have; format is exactly
  what `doffbuild/tconf/asmgen.tcf` writes via `.sect`/`.string`).
  `.string` on C55x places a character in a word and does **not** add a terminator (that is `.cstring`)
  — therefore our `.dcd_register` ended up `0x4e` bytes, byte-for-byte as in `pcmdll`.
- `src/dsp/bench_node.lcf` — three metasections as `type = COPY`, otherwise lnk55 makes
  them regular data and DLLcreate sets `0x131` (allocate + load) —
  ~1.4 KB ASCII would travel into DSP memory.
- Phases renamed to `BENCH_DSP_create/execute/delete` (must match
  names in DCD record).
- **Entries file trap:** `dllcreate -e bios_entries.ent` **localizes** all
  symbols it was not told about, including our three phases → RMS would not find them
  by names from DCD. We do NOT use the stock entries file; `.debug_*` stripped
  via `--symdebug:none`.
- **Trap with asm55:** invoked directly, it stamps object as `Tag_Memory_Model=1`
  (small) and lnk55 refuses to merge it with large-model C objects. `.s55`
  is fed via `cl55` together with `.c`.

**Verification (DLLdump, `out/dsp/bench.dll55l`, 2836 B):** Headers/Sections/
Symbols — PASSED. Shape matches `pcmdll.dll55L`:

| | ours | pcmdll |
|---|---|---|
| `.text` | `0x208`, flags `0x230` | `0xbd3`, flags `0x230` |
| `.dcd_register` | `0x4e`, `0x101` | `0x4e`, `0x101` |
| `.dspbridge_symbols` | `0x326`, `0x101` | `0x338`, `0x101` |
| `.<UUID>` | `0x1e8`, `0x101` | `0x1fa`, `0x101` |

Undefined externals — exactly 5, all present in base: `_NODE_getMsg`, `_NODE_putMsg`,
`_CLK_gethtime`, `_CLK_countspms`, `_c_int00`. Defined and visible:
`_BENCH_DSP_create/execute/delete`, `_dsp_q15_dot/_fir`, `_dsp_blk`.
Codegen was not affected (`dis55`): `RPT CSR; MACM` in dot and FIR, `MPYMK` in BLK.

**Remains (both require device):** (1) ARM loader — reverse engineering 39
ordinals of `bridgeapi.dll` for contract §14.1; (2) run on N95.

## 16. ARM-side reverse engineering: true architecture of the bridge (2026-08-10)

### 16.1. Main finding: entire dspbridge lives in KERNEL, behind LDD `Hwa`

`bridgeapi.dll` is not a self-contained bridge. Search through ROM for string `Hwa.Omap`
(UTF-16 in `bridgeapi`) led to a driver pair that previous steps had not seen:

| Module | Size | Role |
|---|---|---|
| **`ehwa.ldd`** | 6140 | LDD facade; registered channel name is **`Hwa`** |
| **`ehwaomap.pdd`** | 110168 | **entire dspbridge**: DOFF loader, DSP MMU, RMS protocol, mailbox, power |

Proof from strings of `ehwaomap.pdd`: `RMS_createNode/deleteNode/executeNode/
configureServer`, `RMS_STATUS:NodeCreate/Execute/Suspend/Resume/Delete/
SetPriority`, `*** DSP MMU Fault ***`, `DDspObject::MMUInit, AddDSPMMUEntry
(lp=%d, pa=0x%x, va=0x%x, sz=%d)`, `DSP RESET`, `DYN_DARAM/DYN_SARAM/
DYN_EXTERNAL/DYN_SRAM`, `_BRIDGEINIT_DSP_FREQ`, classes DBridgePdd,
`DDspObject`, `DIvaObject`, `DNode`, `DBridgeFactory`.

String from `ehwa.ldd`: **"MultimediaDD capability is checked by DSP Bridge LDD"** →
client must have **MultimediaDD** (added to `dsptest.mmp`).

**`D32HWA` is NOT the channel name**, but an internal driver string: first attempt with
it yielded `KErrNotFound`. Registered LDD name is **`Hwa`** (confirmed both by
`TFindLogicalDevice` on device, and by literal in `bridgeapi` @`0x80A61DB8`), PDD —
`Hwa.Omap` (Symbian requires prefix "LDD name + dot" — matches).

### 16.2. Structure of 39 ordinals deduced, WITHOUT guessing

Six ordinals aliased in pairs: 11/12, 13/14, 21/22, 23/24, 36/37, 38/39.
In Itanium C++ ABI pairs `C1`/`C2` (constructors) and `D1`/`D2` (destructors)
are laid out to the same address. Each pair stands **at the end of a solid block
of ordinals** → three classes, each having {methods..., ctor, ctor, dtor, dtor}:

| Class | Ordinals | Methods | ctor | dtor | What it is |
|---|---|---|---|---|---|
| A | 1–14 | 1–10 | 11/12 | 13/14 | UUID/DCD objects (TLex parsing, `%08X_%04X_…`) |
| B | 15–24 | 15–20 | 21/22 | 23/24 | async operations (ord 16/18 = `User::WaitForRequest`); ord 20 — 1766 B descriptor parsing |
| C | 25–39 | 25–35 | 36/37 | 38/39 | **processor/channel**: holds `RBusLogicalChannel`, files, chunks |

Order of ordinals in Symbian is alphabetical by **mangled** name; this was
confirmed independently on `euser.dso` (symbol with st_value = (ordinal−1)*4,
names go strictly alphabetically).

**Reconciled with device:** `dsptest.exe` extracted `RLibrary::Lookup(1..39)` live
— **all 39 addresses matched the ROM dump** bit-for-bit. That is, dump = device
firmware, and all static analysis stands on code that actually executes.

### 16.3. Class C — dissected signatures

- **ord 36/37 ctor** — clears fields 0,4,8,12; ord 32 also writes [this+16].
  Object ≥20 B; `RBusLogicalChannel` lies at offset **0** (euser methods
  are called with `r0 = this`).
- **ord 32 = `TInt Open(TInt aProcId, TInt aFlag, const TAny* aAttrs24)`**
  - `aProcId` is checked with `cmp #2; bcc` → only **0 or 1** (otherwise −5);
    placed into `[this+16]`. This is core selection: **0 = C55x DSP, 1 = IVA**.
  - `aAttrs24 != NULL` → copies 24 B into newly allocated block.
  - `aFlag == 1` → after `DoCreate` builds path string and calls **ord 26**, that is,
    loads the base image. For us this is undesirable (base is already brought up by audio).
  - inside: `TVersion`, `DoCreate`, `operator new(60)`, `DoControl`.
- **ord 26 = loading DOFF file + DCD registration**: builds list of records
  84 B each, copying into each **16 B UUID** and 32 B properties, then
  `RFs::Connect` → `RFile::Open` → `RFile::Size` → `DoControl` → `RChunk::Base`.
  Our node is registered by precisely this mechanism.
- **ord 33 = Close/Detach**: frees block [this+12], then
  `DoControl(0x04000001, this+16, 0)` and `RHandleBase::Close`.
- **Driver DoControl codes — base `0x04000001`** (literal @`0x80A5D8F4`),
  neighboring commands addressed as base+N (ord 26 uses `+12` = `0x0400000D`).

### 16.4. Bridge clients in ROM (found by cross-references)

XIP leaves no import stubs with names, so clients were sought by scanning entire
`sys/bin` for 32-bit literals equal to export addresses of `bridgeapi`:

| Client | How many ordinals | Role |
|---|---|---|
| **`bal.dll`** (class **`CBal`**, 30 exports) | 18 | "Bridge Abstraction Layer"; itself loads `EHWAOMAP`/`EHWA`, holds one object each of classes A, B, C |
| `dspmemmapper.dll` | 5 (25,27,28,31,34) | memory mapping |
| `balbuffers.dll` | 2 (29,30) | buffers |

`CBal::NewL` (bal ord 26) → ctor+ConstructL (bal ord 22), and ConstructL
sequentially: `ord10(A)`, `ord33(C)`, `Free/LoadPhysicalDevice("EHWAOMAP")`,
`LoadLogicalDevice("EHWA")`, `ord32(C)`, `ord9(A)`, `ord36/21/11` (ctors of three
members). Thin 1:1 wrappers of `CBal` provide mapping: bal 11→ap 2, bal 14→ap 19,
bal 15→ap 20, bal 24→ap 35, bal 25→ap 7, bal 1→ap 4, bal 16/17→ap 3.

### 16.5. Reverse engineering tools (in scratchpad, reproducible)

`xref.py` (search for clients by literals and BL/BLX throughout ROM), `exports.py`
(XIP export table: `iExportDirCount` @+0x3C, `iExportDir` @+0x40),
`annotate.py` (Thumb disassembler with naming of EVERY import: ROM export
table + `.dso` from SDK yield module::ordN name), `romstr.py` (8- and 16-bit
strings of ROM module).

### 16.6. ARM-side build was broken — fixed

`abld` passes path to `makmake` **without quotes**, so the space in
`…\TMS320C55x test\group\DSPTEST` split it into two arguments and makmake
simply printed help; then followed vague "No rule to make target". Thus
the ARM side **was never building**, despite note in README. Fixed with junction
without space, which `tools\build.cmd` creates itself.

**Clarification (later).** Initially junction lay next to project
(`…\TMS320C55x_test`) and looked like a second, duplicate directory — confusion
rightly pointed out by owner. Now it is created **outside project tree**
(`D:\symbuild\c55x`) and **removed immediately after build**, so no extra folder
remains. Drive is specifically `D:`: `EPOCROOT` is specified without drive letter and resolves
relative to current, so from `C:` build would look for SDK in wrong place. Can remove junction
**only via `rmdir` without `/s`** — with `/s` it would delete the files it points to.

### 16.7. First real ARM measurement (and cross-check of instrument)

| Kernel | time | MMAC/s | MAC/cycle | chk |
|---|---|---|---|---|
| DOT (8192×2000) | 774 ms | 21.2 | 0.065 | `85055090` |
| FIR (4096×32×200) | 1011 ms | 25.9 | 0.080 | `f5735100` |
| BLK (8192×2000) | 908 ms | 18.0 | 0.055 | `22056190` |

**Verification of instrument:** first run caught device at **423 MHz** (remnant of
overclocking from neighboring project), after reboot — stock **324 MHz**. Absolute
times changed proportionally, while **MAC/cycle remained identical to thousandths**
(0.065 / 0.080 / 0.055). Two different frequencies yielded the same normalized figure — this
is independent confirmation that both `User::FastCounter` and calibration of `SpinNop`
measure what is needed. HAL meanwhile stubbornly says `ECPUSpeed = 206438 kHz` —
meaning HAL is lying, while our instrument is not.

### 16.9. ARM baseline NOT reproducible between reboots (memory, not core)

The same binary, the same measured core frequency — different numbers:

| kernel | boot C (324 MHz) | boot D (327 MHz) | change |
|---|---|---|---|
| DOT | 774 ms (0.065 MAC/cycle) | **508 ms (0.098)** | ×1.52 |
| BLK | 908 ms (0.055) | **648 ms (0.077)** | ×1.40 |
| FIR | 1010 ms (0.080) | 990 ms (0.080) | ×1.02 |

Checksums in both cases are the same (`85055090` / `f5735100` / `22056190`),
that is, literally the same is being computed. Core frequency is identical within 1%.

Explanation is consistent: **DOT and BLK stream-read 16 KB each** (two buffers of
8192×2 B — larger than 16-KB L1D of ARM1136), that is, bottleneck on memory; **FIR
reuses window `x[]` in cache** and bottlenecks on ALU. Changed speed of memory
subsystem (DVFS/OPP of L3/SDRAM core), not clock frequency of ARM.

**Consequences to consider in comparison with DSP:**
1. "Best-of-N" protects from interference **within** a run, but **not** from changes
   in system state between reboots — these are different things, and earlier I confused them
   (§16.7 presented matching MAC/cycle at two frequencies as proof of instrument reliability;
   for FIR this is true, for DOT/BLK — no).
2. Two of our three "ARM baselines" actually measure **memory**, not core.
   For fair comparison with C55x this is fundamental: DSP visits the same SDRAM
   via DSP MMU, so part of difference will be determined by bus, not dual-MAC.
3. ARM and DSP measurements must be taken **in a single run**, rather than comparing
   numbers from different boots.

### 16.8. TWO DEVICE REBOOTS — investigation (open)

After each of two runs that touched DSP stack, device **eventually**
rebooted. Reboot was **delayed**: process itself finished normally
(`EXIT 0`), log was collected, and only minutes later device went into reboot.

Common to both runs: `RLibrary::Load` + `Close` for **`bridgeapi.dll`,
`bal.dll`, `dspmemmapper.dll`**; in the second — also `RDevice::Open("Hwa")` +
`GetCaps` + `Close` (first gave `KErrNotFound` due to wrong name `D32HWA`).

**Working hypothesis (not a fact):** these DLLs are designed for a single owner —
the audio server. Their unloading triggers global destructors that touch
shared DSP state; audio stack then crashes in kernel → reboot. `RDevice::Close` on
a live driver is the second suspect.

**Reaction following the rule "do not repeat the same thing after two failures":** trials
are partitioned into levels (`lib`/`dev`/`chan`/`dsp`), by default DSP stack **is not
touched at all**; `bal.dll` and `dspmemmapper.dll` we never load again
(they are not needed anyway — all necessary ordinals are in `bridgeapi`). Next — bisection
with holding time after each run, one level at a time.


## 18. BRIDGE OPENED ON HARDWARE; base image loads (2026-08-10)

Runs on N95. Each log line is written with `Flush()`, so even when the device
dies, the last line accurately indicates the location.

### 18.1. What works — confirmed on device

```
ord32 Open(proc=0 DSP, flag=0, NULL) -> 0
object now: 00030002 00000000 00000000 007000f0 00000000
ord9 bind(A, C) -> 0
ord26 Load BASE: Z:\resource\plugins\baseimage.dof -> 0
```

- **`ord32` opens bridge to C55x.** Reverse engineered signature
  `(aProcId=0, aFlag=0, aAttrs=NULL)` confirmed on live hardware: channel handle
  `0x00030002` appeared in `[0]`, pointer to 60-byte block in `[12]`
  (`0x007000F0`), our `procId` in `[16]`.
- **`ord9(A, C)` = binding** of class A to processor — `0`.
- **`ord26` loads DSP/BIOS base image** (155 KB) — `0`. That is, both call
  and arguments `(this, aPath)` are correct.

### 18.2. What crashes and why — `ord26` is not for nodes

Device **immediately reboots** when `ord26` receives a **dynamic
node**: equally with our `E:\bench.dll55l` and stock
`Z:\system\apps\ping\pingdyn.dll55l` from ROM.

This was the resolving experiment: **Nokia's stock node crashes just like ours**
→ our DOFF has nothing to do with it, it is a matter of HOW we load. And since the full base
image passes with that same call, the conclusion is:

> `ord26` is `PROC_Load` for **processor image**, not for a node. A node in
> dspbridge is loaded differently: DCD registration + `NODE_Allocate` by UUID, after
> which the kernel pulls in its library via dynamic loader itself. Feeding
> DOFF library to `PROC_Load` crashes the kernel.

Checked additionally: **third argument of `ord26` is not read anywhere in the body**
(`[sp,#88]` is not mentioned once), meaning it does not select a mode.

Attempt with `ord32(aFlag=1)`, where function asks driver for path to base itself
(DoControl(0x04000000, buffer)), yielded **`-38 KErrBadDescriptor`** — clean, without
reboot, with rollback of object. Therefore we load base via explicit path.

### 18.3. Node creation path found (`bal`, `0x80A41DDC`)

```
r5 = class C (processor), r4 = class B (task)
block 20 B = { [arg+4], [arg+0], [CBal+48], [arg+8], [arg+12] }
ret = helper(C, aOp=4, &block, &out)
if ret == 0:
    C[0..11] -> B[4..15]     ; channel copied to task
    out      -> B[0]         ; TASK HANDLE
```

Before this `bal ord 1` calls **`A::ord4(&[CBal+48])`**, and the result becomes one of
the words of the block — that is, class A first **resolves UUID into DCD reference**, and only
then is the task created.

**Correction to §17.3:** class B is **16 bytes**, not 8. Constructor (ord 21)
clears only the first 8, but 12 bytes at offset +4 are copied here. In the layout of
`CBal` this also covers that "unknown field +32" which I previously set aside: it is
part of B.

### 18.4. Stable sequence confirmed on device

```
cmdline 'baseonlynobench', uptime 896 s
  ord32 Open(proc=0 DSP, flag=0, NULL) -> 0
  ord9 bind(A, C)                      -> 0
  ord26 Load(Z:\resource\plugins\baseimage.dof) -> 0
  ord10/ord33 close  (CBal::Shutdown order)
  == end ==            <- run finished, device alive
```

That is, **opening bridge + binding + loading base image +
correct teardown do not bring down device**. This conclusively clears the base of suspicion:
it is `ord26` on a **node** that kills.

> **Be careful with conclusions about "did not run".** The `baseonly` attempt before this
> looked like another reboot, and I started building hypothesis "base itself is
> destructive" upon it. In reality the run **did not start**: output had no
> OK <bytes>, and the previous `cmdline` remained in log on device. Sign
> of a real run — `OK` lines from PUT and fresh `cmdline` in first line of
> log; without them the crash pertains to device state **prior** to our command.

### 18.5. Class A: `ord4` decoded and checked, `ord6` — not yet

```
ord4(A, &out)  -> 0, out=00000000
ord4(A, NULL)  -> -6            <- exactly as disassembler predicted
ord6(A, our UUID 16 B)  -> -6
ord6(A, PING UUID 16 B) -> -6
```

- **`ord4(TInt* aOut)` confirmed on hardware**: `NULL` → `-6 KErrArgument`,
  otherwise `0` and one word from `[A+0]`. Currently it is zero — node is not yet
  selected in class A, and it is this value that `bal` puts into task creation block.
- **`ord6` does not take raw UUID.** Control is decisive: that same `-6` arrived for
  UUID of stock `PING`, which is definitely registered on this device. Thus
  issue is not in content, but in **argument type** — most likely a descriptor
  (`TDesC`), rather than 16-byte block. Check further — via internal
  `0x80A5F5C2`, where `ord6` passes (object [A+4], argument, 0, buffer 304 B)
  under mutex.

> **Correction of own attribution.** Earlier I wrote that `ord4` parses string
> via `TLex`. This is an artifact of disassembler window: `ord4` is only 32 bytes, while `TLex`
> belongs to adjacent **unexported** function `0x80A5E6DC`, into which the window
> taken "up to next export" reached. Length of function cannot be inferred from
> distance to next ordinal.

### 18.6. TASK CREATED ON DSP — the loop is closed

```
ord6(A, TESTSERVER_NOKIA)      -> 0
ord4(A, &ref)                  -> 0, ref = 0x007003B0
DoControl(channel, fn=4, TBuf8<20>{0,0,ref,0,0}, &out) -> 0
                                  taskHandle = 0x00008000
```

That is, **entire path from opening bridge to creating task on C55x
reproduced with own code**, without `bal` and without node C++ wrappers.

**Trap that cost one run: descriptor type.** First attempt
passed `TPtr8` and got `-2 KErrGeneral`. Kernel handler (`0x801B4EA4`)
does a **raw 32-byte read** from passed pointer into own buffer,
that is, expects "8 B header + 20 B data" layout — this is `TBuf8<20>`, not
`TPtr8` (which holds a pointer instead of data). With `TBuf8<20>` the very first
variant of block worked.

At the same time this resolves another fear: **calls in this family do not crash device**
— kernel validates arguments and returns an error. One can iterate freely here.

### 18.7. Direct DCD registration: entry accepted, but node not found

```
DoControl(0x0400000D, &count=1, 84 B record with our UUID) -> 0
ord6(A, our UUID) after registration                       -> -6
```

Entry assembled according to layout from `ord26`: `{next(4), uuid(16), props(32), …}`,
`props` zero-filled. Kernel **accepted** call, but search still does not
find node — hence these 32 bytes of properties are meaningful, and must be taken from
parsing `.dcd_register`/UUID section, rather than invented.

This is the only open link. Ground truth — output format of parser
`0x80A5F0D4` (records of 48 B: `{uuid(16), props(32)}`).

### 18.8. Another tool trap: stale binary

`ABLD.BAT` may return 0 even when `make` failed. Consequently
`tools\build.cmd` printed `built ->` and deployed **stale** exe — device silently
executed code not matching source. Caught on compilation error
(`uuid` undeclared). Fixed: target exe is now deleted prior to build,
so stale binary physically cannot travel to device.

### 18.9. Order inside `ord26` — I was wrong; but a safe call found

Hypothesis was: `ord26` first registers DCD (user space), then loads image,
so if second stage is broken — registration remains. Verification: open our
node **exclusively** with own `RFile`, so that internal
`RFile::Open(..., EFileShareReadersOnly)` in `ord26` fails.

```
lock our node exclusively -> 0
ord26(locked node)        -> -14      (KErrInUse, WITHOUT device crash)
ord6(A, our UUID) after   -> -6       (registration did not happen)
```

**Hypothesis refuted.** DCD parsing is done by **kernel**, not user space: in
`0x80A5F0D4` path goes to driver via asynchronous `DoControl` (op=5), and file is read
by driver itself. Our lock stopped everything before registration, not after it.

**Yet side result is valuable in itself:** this is a **safe way to call
`ord26` on a node** — locked file gives clean `-14` instead of reboot. That is,
experiments with this branch no longer cost reboots.

### 18.10. DOFF header decoded (and can be edited)

By matching raw bytes with `DLLdump` fields across four files:

| offset | field | our node |
|---|---|---|
| `+0x00` | `strtab_size` | `0x168` |
| `+0x04` | **`entrypt`** | `0` (in base `0x273BB`) |
| `+0x08` | `byte_order` | `0x00010203` |
| `+0x0C` | `scn_name_size` | `0x69` |
| `+0x10` | `{u16 no_syms, u16 max_str_len}` | `0x0027000E` |
| `+0x14` | `{u16 no_scns, u16 target_scns}` | `0x00010005` |
| `+0x18` | `{u16 doff_version, u16 target_id}` | `0x009C0000` |
| `+0x1C` | **`{u16 flags, u16 entry_secn}`** | `0x000012E0` (in base `0xFFFF12E3`) |
| `+0x20` | `checksum` | `0xFF3AE938` |

**Checksum rule: checksum = ~(sum of 8 preceding words)** — that is,
sum of all nine words equals `0xFFFFFFFF`. Verified on `baseimage.dof`,
`pingdyn.dll55l`, our node and our DCD stub — match across all four.

Practical consequence: DOFF header can be modified and left valid
(in particular set "executable" flags `0x12E3` and `entrypt`), recalculating
one word. Whether this makes sense is a separate question: `PROC_Load` with executable
flags will try to place sections as processor image, which for a node with code would
mean writing over memory of base image.

### 18.11. Node description read; DCD turned out to be TWO-SIDED

`ord1(this, aIndex, aOut)` = enumerate object No.`aIndex`, take its description and
copy **152 bytes** to caller (`memcpy` @`0x80A5E4C2`). This is precisely the
buffer from which `ord26` builds registration entry. Dump on device:

```
ord1(idx=0) -> 0  10d930612b1ce44094a414ebb314340e  "EAP_TASK"…
ord1(idx=1) -> 0  1dce8f89b6294f459e24057f81d792ed  "TESTSERVER_NOKIA"
ord1(idx=2..5) -> -6
```

- bytes **0..15** — UUID (`dsp_uuid`, little-endian);
- bytes **16..47** — **node name in UTF-16, exactly 16 characters** (in
  `TESTSERVER_NOKIA` this is 32 bytes with no remainder; in `EAP_TASK` tail is garbage from
  previous entry in same buffer).

Thus registration entry is {next(4), uuid(16), UTF-16 name(32)}, and my
guess about "32 bytes of properties" was inaccurate: simply a name there.

**Yet this also explains why direct registration did not work.** DCD is **two-sided**:

| side | populated by | read by |
|---|---|---|
| user-side (in class A) | file parsing inside `ord26` | `ord1`, `ord6`, `ord4` |
| kernel-side | `DoControl(0x0400000D)` | RMS upon node creation |

We did only the second half — that is why `DoControl` returned `0`, while `ord6`
further did not see node. And parsing that populates the first half is hardwired into
`ord26` (only call to `0x80A5F0D4` in entire library — verified by search).

### 18.12. `ref` is not a struct, but a string pool

Dump at address returned by `ord4`:

```
ref+00  e00b0030 e00b0000
ref+08  "TESTSERVER_NOKIA_tn_create\0" … "TESTSERVER_NOKIA_tn_execute\0"
        … "TESTSERVER_NOKIA_tn_delete\0" "init\0" ".stack\0" ".hst\0" ".DARAM$…"
```

That is two pointer words (`0x30000BE0` and `0x00000BE0` — differing by exactly
`0x30000000`, resembles "DSP address" versus "offset") followed by **string pool**: names
of three node phases and names of DSP sections. Recreating it manually is possible, but is a
fragile construction with internal offsets.

### 18.13. Hypothesis "DOFF flags are to blame" not confirmed

Stub was patched to executable header
(`tools\patch_doff_exec.py`: flags `0x12E3`, entry point as in base,
recalculated checksum — `DLLdump` validation passes) and supplied to
`ord26`. Sections allocated or loaded in it are **zero**, that is, nothing
to place onto DSP.

**Device crashed anyway.** Therefore flags and entry point are **insufficient** —
difference between `baseimage.dof` and node is deeper (most likely in that
`PROC_Load` expects an image with BIOS/RMS section table, not a library).
Hypothesis §18.2 in part "matter is only in flags" dismissed.

### 18.13a. Map of DCD ioctl family (taken from call sites)

All DCD work of `bridgeapi` goes through two dispatchers forming code as
`0x0400000C + 18 + op`: **`0x80A5DB2A`** (synchronous, `DoControl`) and
**`0x80A5DB42`** (asynchronous). Both cut off `op >= 10` with `-5`.
Operation numbers extracted from all ten call sites:

| op | ioctl | call | where used |
|---|---|---|---|
| 0 | `0x0400001E` | sync | `0x80A5F070` |
| 1 | `0x0400001F` | sync | **node description** — `0x80A5F5C2`, followed by `ord6` |
| 2 | `0x04000020` | async | `0x80A5F26E`, `0x80A5F500` |
| 3 | `0x04000021` | async | **enumeration** — `0x80A5F566`, followed by `ord1` |
| 4 | `0x04000022` | sync | enumeration (variant) — `0x80A5F580`, `0x80A5F5AC` |
| **5** | `0x04000023` | async | **file parsing into user-side DCD** — `0x80A5F106` |

**`op=5` is precisely what is missing.** It populates user-side DCD, and if
called directly from own channel, `ord26` with its fatal image loading
stage becomes unnecessary. Probe already implemented
(`dsptest.exe … dcdop`), remains to run on device.

> **Side correction.** These codes (`0x0400001E`+) go beyond the 24-entry
> table that I attributed to device family in §17.2. But `op=1` on device
> **works** (via it `ord6` found base nodes), hence that table
> serves another family, not `0x0400_00NN`. Table §17.2 should be read as
> "24-entry dispatcher found in PDD", without attachment to a specific family.


## 19. OUR NODE REGISTERED AND TASK FOR IT CREATED (2026-08-10)

### 19.1. Bypass for `ord26` found: direct call to parser

`0x80A5F0D4` is precisely "file parsing + populating user-side DCD"; loading
image onto DSP (the part that crashes kernel) is done **separately**, by own `RFs`/`RFile`
further inside `ord26`. Function is not exported, but `bridgeapi` is XIP, addresses
are fixed, and we already verified all 39 ordinals bit-for-bit against ROM dump.

```
lock(0x80A5EFA1);  parse(0x80A5F0D5)(loader, &path);  unlock(0x80A5EF97)
    -> 0
enum(loader, 0)   -> 0   11bf7c96 0eb9544b a4d33c84 249ee1da   <- OUR UUID
getdef(loader, our UUID, type=0) -> 0
    def[0..15]  = UUID, def[16..47] = "BENCH_DSP" in UTF-16
```

We take `loader` from `[C+12]`; `A[4]` points to same place, that is, `ord6` looks into
the same store.

### 19.2. Why `ord6` initially did not see node: library entries were missing

**Clarification 2026-10-01:** conclusion below describes August test without library
type2. Native fallback 3→2 and generic library confirmed statically on
N95/E90 and on hardware on both: node0+library2 passes create/delete/free0,
preserves data stamp and delete address. Thus explicit types 3/4/5 are one of
registration variants, rather than a mandatory condition. See
[new results](STREAM_RESEARCH.md#type-2-library-and-task-after-create).

`props[292]` turned out to be **load type**: in our node it is `1`
(dynamic). For such nodes `ord6` goes into branch `0x80A5E6DC`, which searches for entries
of types **3/4/5** = `CREATELIB`/`EXECUTELIB`/`DELETELIB` (DCD types from dspbridge).
Without them — `-6`, although the node itself is already in the store.

Not a single node in ROM declares these types (checked all 30 files: 24 have
only `:0`, six — `:0,:1`) — there they are synthesized during stock registration
via `ord26`. We, however, bypass `ord26`, so we declare them **explicitly** in
`.dcd_register` of our node:

```
"967CBF11_..._:0," "967CBF11_..._:3," "967CBF11_..._:4," "967CBF11_..._:5,"
```

**Worked:** ord6(A, our UUID) -> 0.

### 19.3. Task for OUR node created on DSP

```
ord7(A, our UUID, args) -> 0        (ord6 + creation arguments descriptor)
ord4(A, &ref)           -> 0        ref = 0x007003B0
DoControl(channel, fn=4, TBuf8<20>{0,0,ref,0,0}, &out) -> 0
                                    taskHandle = 0x00008000
```

**Proof that specifically our node was chosen** — dump of structure at `ref`:

```
ref+00  … "BENCH_DSP_create" … "BENCH_DSP_execute" … "BENCH_DSP_delete"
```

Earlier `TESTSERVER_NOKIA_tn_*` were at that same location. That is, this is not an address coincidence:
the structure contains phase names of **our** node.

Task command family on our handle yields **addresses in DSP space**:
`fn 2 -> 0x30000068`, `fn 3 -> 0x3000010C`, `fn 4 -> 0x3000000C` — that is,
memory for node on DSP is already allocated.

### 19.4. Task family map — and one deadly command

Sweep of `0x08000000 + idx` on own handle (`a2` is valid buffer, as
among commands there are asynchronous ones and zero `TRequestStatus` would mean kernel writing to
address 0):

| fn | result | fn | result |
|---|---|---|---|
| 0 | 0 | 8 | −2 |
| 1 | −18 | 9 | −2 |
| 2 | 0, DSP `0x30000068` | 14 | 0 |
| 3 | 0, DSP `0x3000010C` | 15 | 0 |
| 4 | 0, DSP `0x3000000C` | 16 | 0 |
| 5 | 0 | 17 | 0 |
| 6 | 0 (async completes −2) | **18** | **crashes device** |
| 7 | −18 | | |

> **Rule: do NOT sweep task family blindly.** Unlike DCD family (where
> all six operations are safe), here `fn 18` reboots the device. Codes 0..17
> checked and safe; 18 and above — do not touch.

### 19.5. NODE CREATED ON C55x — step `fn=5` was missing

The missing link was a separate asynchronous step. Complete sequence from `bal`
(`0x80A41E26`):

```
fn=4  create task               -> taskHandle
      copy C[0..11] to B[4..15], put handle into B[0]
fn=5  CREATE NODE on DSP (asynchronously!) + WaitForRequest
fn=6  further
```

`fn=5` I had previously invoked in sweep and received `0` — but **did not wait for
status**, that is, did not complete asynchronous part and considered the step useless.

With proper waiting:

```
DoControl(4) -> 0, taskHandle = 0x00008000
DoControl(5) node-create -> 0,  status: 0     *** NODE CREATED ON THE C55x ***
DoControl(6)             -> 0,  status: 0     (previously was -2)
```

**What this means:** kernel loaded our `bench.dll55l` onto DSP, dynamic
loader resolved external symbols against base image
(`_NODE_getMsg`, `_NODE_putMsg`, `_CLK_gethtime`, `_CLK_countspms`, `_c_int00`),
and RMS invoked our phase **`BENCH_DSP_create()` on C55x**. `fn=6` after this
also succeeds — its previous `-2` was consequence of uncreated node, rather than
problem with our code.

> **Another instance of the same mistake.** Sizes of `ord19`/`ord20` I previously
> stated as 16 and 1766 bytes — in reality both are 16. 1766 again came from
> "distance to next ordinal", although I had already recorded that rule as erroneous.
> Both are thin wrappers: `ord19` → `DoControl(0x0C000003, handle, &arg)`,
> `ord20` → `0x0C000004` of the same form.

### 19.6. Message exchange: structure known, semantics — not

`ord16` (class B) disassembled to the end:

```
0x80A61CD6(sp+8)  = TBufBase8(12,12)         ; TBuf8<12>, data at +8
[sp+0] = 0x80000001 ; [sp+4] = 2             ; two-word header
[sp+16] = { &header, arg1, arg2 }            ; descriptor body
DoControl(channel = this+4, 0x0C000001, taskHandle = [this+0], &TBuf8<12>)
```

That is descriptor for kernel is constructed by `bridgeapi` itself — from us only
valid C++ arguments are required. Object of class B assembled as in `bal`
(`[B+0]` = handle, `[B+4..15]` = copy of `C[0..11]`), and this works: `this+4`
indeed reads as `RBusLogicalChannel`.

**Yet my interpretation of arguments was mistaken.** I passed
arg1 = pointer to {cmd, arg_1, arg_2} (our message to node),
arg2 = timeout — and kernel crashed. Header `{0x80000001, 2}`, which
`bridgeapi` places before arguments, looks more like an **RMS level command**,
than a wrapper of our message, that is, `arg1`/`arg2` mean something else.

Further guessing arguments going to kernel is impractical: each unsuccessful attempt
costs a device reboot. Next step — find in `bal` real
caller of `ord16`/`ord18` and take arguments from there, as already worked for
`fn=4` (`TBuf8` instead of `TPtr8`) and for `fn=5` (missed status waiting).

### 19.6a. CORRECTION: `fn=6` is node deletion

Below in the text `fn=6` is called "running" — this is an **error**. `bal` @`0x80A41F4C`
calls DoControl(channel, fn=6, taskHandle, &status) + `WaitForRequest` precisely
to **tear down** the task (error handling path in `bal` ord28). The fact that after
node creation it started returning `0` instead of `-2` is explained simply:
there was now something to delete.

Practical consequence: `fn=6` must be called **always**, including in error paths,
otherwise node remains on DSP.

### 19.7. Node is alive and responds to driver

`bal` manages node **not** via `ord15..18` (it does not even import them), but
via task family, in form taken from it verbatim:

```
DoControl(channel = B+4, fn, taskHandle, &status) + WaitForRequest
   fn = 0x08000007   (bal ord28,  literal 0x0800000E − 7)
   fn = 0x08000008   (bal @0x80A41A11)
   status is initialized as KRequestPending (0x80000001)
```

Result **after** node creation:

```
node fn 7 -> 0, status 0        (before creation was -18 KErrNotReady)
node fn 8 -> 0, status 0        (before creation was -2)
```

Both operations changed result from error to success precisely when node
was created. This is the **fourth independent proof** that our node specifically lives
on C55x — along with (1) successful `node-create`, (2) names
`BENCH_DSP_create/execute/delete` in node structure, (3) addresses
allocated for it in DSP space.

## 20. FIRST NUMBERS C55x VERSUS ARM1136 (2026-08-10)

### 20.1. Measurement channel without message queue

The message path turned out to be a dead end: ordinals 15–18 of `bridgeapi`
(ioctl `0x0C000001/2`) **are not used by any module in ROM** — only `bridgeapi` itself
in export table (verified by scanning entire `sys/bin`), and
call crashes kernel. Value returned from `create` does not reach ARM either
(verified: `create` returned `0x1234`, `node-create` gave `0` regardless).

Therefore measurement was constructed differently: **work spins inside `create` phase, while
time is measured on ARM**. Node creation is synchronous (`DoControl(5)` + waiting for
status), so its duration increases by exactly the computation time on C55x.
Fixed overhead (library loading, exchange with RMS) is cancelled out by
difference between two runs with different `BENCH_CREATE_REPS` — this is differential measurement.
Buffer is static, in `.bss` of node: shared memory not needed.

**This is simultaneously proof of execution:** 20000 repeats yield time ~39 times
larger than base run, and time scales with number of repeats.

### 20.2. Results

Kernel — Q15 dot-product, `n = 1024` (working set 4 KB, fits in cache on
both sides), same source code on both sides. Best-of-N across series, as
interference can only slow down:

| series | minimum of N runs |
|---|---|
| create, 0 repeats | 7 934 us (of 4) |
| create, 10000 repeats | 124 176 us (of 4) |
| create, 20000 repeats | 308 197 us (of 4) |

| estimate | MMAC/s | MAC/cycle (at 220 MHz) |
|---|---|---|
| 10000 versus baseline | 88.1 | 0.400 |
| 20000 versus baseline | 68.2 | 0.310 |
| 20000 versus 10000 | 55.6 | 0.253 |

**ARM1136 in the same boot** (DOT-S kernel, same `n = 1024`):
**32.28 MMAC/s**, **0.099 MAC/cycle** at measured 324 MHz.

### 20.3. Fair interpretation

Estimates **monotonically decrease** with increasing amount of work (88 → 68 → 56).
This is not spread, but systematic effect: the longer DSP computes, the more it is
preempted by audio stack that owns it. Therefore **a single number cannot be claimed**;
fair result is a range:

> **C55x is faster than ARM1136 by approximately 1.7–2.7 times in absolute
> performance and by 2.6–4.0 times per cycle** on Q15
> dot-product with working set that fits in cache.

Lower bound (55.6) is methodologically most reliable — difference between two operating points
cancels out all fixed overhead; upper bound (88.1) is cleanest from interference, but
relies on baseline run where overhead may differ.

**Caveats to keep in mind:**
1. DSP frequency **was not measured**, nominal 220 MHz taken — all numbers
   "per cycle" scale along with this assumption.
2. Measurement includes task scheduling on DSP under live audio; this is not "clean"
   benchmark of an isolated core.
3. C55x code — plain C via `cl55 -o3` (compiles to `RPT CSR; MACM`),
   without manual optimization. Theoretical dual-MAC limit — 2 MAC/cycle, meaning
   obtained 0.25–0.40 are far from peak, and this is expected for code from C.

### 19.8. What specifically remained

`fn=6` finishes with `-2` — **identically on our node and on stock
`TESTSERVER_NOKIA`**. This is important: at this stage of API our node already
**does not differ from stock**, meaning issue is not in it, but in fact that
launch sequence is incomplete. Hypothesis: `fn=6` is not "running", but waiting for
message (`-2` = none), while creating/launching node is done by other
commands from safe set (0, 5, 14..17) or via `0x0C00_00NN` family of
class B.

Attempt to provide creation arguments via `ord7` did not change picture.

### 18.14. State of the benchmark and what specifically remained

**Ready and verified:**

| part | state |
|---|---|
| ARM kernels (DOT/FIR/BLK, Q15) | working, measured on device |
| ARM↔DSP matching (32-bit accumulator) | fixed, proven by checksum match |
| C55x node (`bench.dll55l`) | builds from source, `RPT CSR; MACM`, DOFF shape as in Nokia production node |
| DSP-side timing instrument | `CLK_gethtime`/`CLK_countspms` present in base |
| bridge opening, binding, base loading | **working on device** |
| finding node in DCD, node reference | **working** |
| creating task on DSP | **working** (`taskHandle 0x8000`) |
| **registration of OUR node in user-side DCD** | **not working — only blocker** |

**Blocker, precisely localized.** For `ord6` to see our UUID, file must undergo
parsing inside `ord26`; while `ord26` on any non-executable DOFF crashes
kernel — and header patch does not cure this (§18.13).

**Three paths, in order of attractiveness:**

1. **Find separate entry point to parser.** In `bridgeapi` there is none, but
   `0x80A5F0D4` sends driver an asynchronous `DoControl` with **op=5** (via
   `0x80A5DB42`, base `0x0400000C + 18`). That is parsing is done by **kernel**, and one
   can try calling it directly from own channel, without `ord26` and without
   image loading stage. This is the shortest path and requires no new
   knowledge of formats.
2. **Recreate string pool from §18.12** and slip own `ref` into
   `DoControl(fn=4)`, bypassing DCD entirely. Fragile, but verified
   safely — kernel on malformed arguments returns an error, rather than crashing.
3. Build node as full processor image (requires DSP/BIOS libraries,
   which we do not have) — most expensive path.

**Safety of runs:** everything except `ord26` on a node does not crash device. If
`ord26` is indeed needed — keep file open exclusively, then it returns
`-14` instead of reboot (§18.9).

### 18.15. Reference: `dsptest.exe` flags

`lib` `dev` `chan` `dsp` — probe levels; `load` (our node) / `ref` (stock
`pingdyn`) / `base` (base image) / `baseonly` (stop after base) /
`stub` / `task` / `reg` / `lock` / `dump` — separate experiments; `nobench` disables
ARM benchmark, `heavy` restores full `BENCH_*_REPS`. Flags recognized by
substring, so can be merged into single token: `baseonlytasknobench`.

Find how UUID gets into class A (candidates — ord 6/7, they are the only ones with
`TLex` string parsing, and `ord 7` — thin wrapper over `ord 6`), and how
DCD of our node is registered. After this sequence closes:
base → A(UUID) → create task → `0x0C00_00NN` for run/messages.


## 17. `Hwa` kernel interface completely dissected (2026-08-10)

`ehwa.ldd` turned out to be a better target than 39 C++ ordinals: it is a narrow
integer ioctl interface, and its dispatcher is dissected unambiguously.
`DLogicalChannel::Request(aReqNo, a1, a2)` divides the request space into **three
families by high bits** (`0x801B53B0`):

| Range `aReqNo` | Where it goes | What it is |
|---|---|---|
| `< 0x04000000` | local LDD handlers | channel management |
| `0x04000000…0x07FFFFFF` | tail-call into **PDD vtable, slot +28** | **device commands** (attach, load DOFF, DCD, memory) |
| `0x08000000…0x08000015` | **jump table for 22 entries** (`0x801B4B74`) | **task/node commands** |
| `>= 0x0C000000` | PDD vtable, slot **+84** | third family (`0x801B4D18`) |

This is why `bridgeapi` holds the literal `0x04000001` and addresses neighboring commands as
base+N: these are direct codes of the device family.

### 17.0. Channel family `fn 0..10` — task creation lives here

The lowest range (`aReqNo < 0x04000000`) I initially set aside as "channel
management". In reality, the most important part is right there. Dispatcher — `0x801B52A4`:
`cmp r1,#10; addls pc,pc,r1,lsl#2` → table for **11 entries** (`0x801B52C0`);
everything above 10 goes to the families below.

| fn | handler | | fn | handler |
|---|---|---|---|---|
| 0 | `0x801B52EC` | | 6 | `0x801B5354` → `0x801B5118` **asynchronous operation on task** |
| 1 | `0x801B52F4` | | 7 | `0x801B5364` → `0x801B4DE4` |
| 2 | `0x801B530C` | | 8 | `0x801B5374` |
| 3 | `0x801B5318` | | 9 | `0x801B53A0` → `0x801B505C` |
| **4** | `0x801B5334` → `0x801B4EA4` **task creation** | | 10 | `0x801B5330` |
| 5 | `0x801B5344` → `0x801B5014` | | | |

Link to real code: `bal` (`0x80A41DDC`) creates task via **direct**
DoControl(class_C_channel, fn=4, descriptor(20 B), &out) — no C++ wrappers,
`0x80A41F44` turned out to be merely a tail-call into `RBusLogicalChannel::DoControl`. Then
the same `bal` does `DoControl(fn=6, taskHandle, &status)` +
`User::WaitForRequest` — that is, **fn 6 is an asynchronous operation on task**.

### 17.1. Table of 22 task commands (`0x08000000 + idx`)

Before dispatcher: task lookup by handle (`[this+92]`), errors
`Error: no task handle` (−2), `Error: no owning device` (−21), warning
`task call from other than owning device`. Default value `r5 = −5`
(`KErrNotSupported`).

| idx | handler | idx | handler |
|---|---|---|---|
| 0 | `0x801B4BCC` → `0x801B423C` | 11 | **−5 (none)** |
| 1 | `0x801B4BDC` (checks `[task+20]`, otherwise −18) | 12 | **−5 (none)** |
| 2 | `0x801B4C08` → `0x801B4A98` | 13 | **−5 (none)** |
| 3 | `0x801B4C1C` → `0x801B4A2C` | 14 | `0x801B4C90` (arg3=0) |
| 4 | `0x801B4C30` → vtable PDD +28 | 15 | `0x801B4C98` (arg2=0) |
| 5 | `0x801B4C40` → `0x801B4418` | 16 | `0x801B4CA4` → `0x801B4988` (arg3=1) |
| 6 | `0x801B4C50` → `0x801B5698` (arg −3) | 17 | `0x801B4CBC` → `0x801B44B4` (arg2=1) |
| 7 | `0x801B4C60` → `0x801B4294` | 18 | `0x801B4CD0` → vtable PDD +68 |
| 8 | `0x801B4C70` → `0x801B4300` | 19 | `0x801B4CE0` → vtable PDD +72, writes result to `*a2` |
| 9 | `0x801B4C80` → `0x801B42D4` | 20 | `0x801B4CF8` → `0x801B44F0` |
| 10 | **−5 (none)** | 21 | `0x801B4D08` → `0x801B4540` |

That is, working task commands — **18** (0–9 and 14–21). Pairs (14,15) and (16,17)
differ only by boolean flag — classic pair "synchronous/asynchronous"
or "with waiting / without".

**Why this is valuable:** this interface is what `CBal` itself uses in the
hot path (bal ord 27 calls `RBusLogicalChannel::DoControl/DoRequest`
directly, bypassing `bridgeapi`). It is narrower than C++ ordinals and does not require knowledge
of class layouts. Downside — calls go to the KERNEL: an error here costs a reboot, rather than
a process crash. Therefore it can be touched only after clarifying the cause of
reboots (§16.8), and only with valid handles obtained through normal path.

### 17.2. Device command family: 24 entries (`0x04000000 + idx`)

Dispatcher — in `ehwaomap.pdd` @`0x80199FDC`: `add r0, r8, #0xFC000000;
cmp r0, #23; addls pc, pc, r0, lsl #2 → table of **24 entries** at 0x80199FF4.

| code | idx | handler | | code | idx | handler |
|---|---|---|---|---|---|---|
| `0x04000000` | 0 | `0x8019A080` | | `0x0400000C` | 12 | `0x8019A4B4` |
| `0x04000001` | 1 | `0x8019A054` **= ord33 Close** | | `0x0400000D` | 13 | `0x8019A510` **= ord26, DOFF/DCD load** |
| `0x04000002` | 2 | `0x8019A0DC` | | `0x0400000E` | 14 | `0x8019A318` |
| `0x04000003` | 3 | `0x8019A1A4` | | `0x0400000F` | 15 | `0x8019A6A4` |
| `0x04000004` | 4 | `0x8019A280` | | `0x04000010` | 16 | `0x8019A7C0` |
| `0x04000005` | 5 | **none** | | `0x04000011` | 17 | `0x8019ABB0` (shared with 8, 20) |
| `0x04000006` | 6 | **none** | | `0x04000012` | 18 | `0x8019A894` |
| `0x04000007` | 7 | `0x8019A588` | | `0x04000013` | 19 | `0x8019AA2C` |
| `0x04000008` | 8 | `0x8019ABB0` | | `0x04000014` | 20 | `0x8019ABB0` |
| `0x04000009` | 9 | `0x8019A364` | | `0x04000015` | 21 | `0x8019AAFC` |
| `0x0400000A` | 10 | `0x8019A3D8` | | `0x04000016` | 22 | `0x8019A63C` |
| `0x0400000B` | 11 | `0x8019A414` | | `0x04000017` | 23 | `0x8019A670` |

Two bindings to C++ side are already present from §16.3: `bridgeapi` ord 33 (Close) sends
`0x04000001`, ord 26 (DOFF load + DCD registration) — `0x0400000D`.

**Summary of kernel surface:** 24 device commands + 18 live task commands
(from 22 entries) + third family from `0x0C000000`. This is the complete ARM↔DSP
interface of the device.

### 17.3. Class B = task object; third family `0x0C0000NN` revealed

Dissecting ordinals 15–20 closes the picture. Literals near them: `0x80A5DD2C` =
`0x80000001` (flag value), `0x80A5DD30` = **`0x0C000001`** — base
of third family.

Each method of class B does the same:
```
r0 = this + 4      ; RBusLogicalChannel lies at offset +4
r1 = 0x0C000001 + N ; request code (ord 19 -> +2, ord 20 -> +3)
r2 = [this + 0]     ; TASK HANDLE
r3 = &arguments
-> DoControl
```
Thus **object of class B is exactly 8 bytes: `{TInt iTaskHandle; RBusLogicalChannel
iChannel;}`** (matches 8-byte ctor ord 21/22 and empty dtor 23/24).

This connects with the LDD dispatcher (§17): in the branch `aReqNo >= 0x08000000` driver
**first looks up task by `a1`** (`[this+92]`, errors "no task handle" / "no
owning device"), and only then branches: `0x08000000+0..21` — table of 22
entries in LDD itself, while `>= 0x0C000000` — in PDD vtable slot +84. That is `a1`
of class B is precisely that task handle the driver looks for. Complete match, from two
independent sides.

**Consequence for loader:** role of classes is now not a hypothesis, but a conclusion —
class C opens channel and loads images (family `0x0400_00NN`), class B
controls **task/node** (families `0x0800_00NN` and `0x0C00_00NN`), class A
services UUID/DCD. Class B is specifically the bearer of sequence
allocate → create → run → put/get msg from contract §14.1.

### 17.4. Summary map of 39 ordinals of `bridgeapi.dll`

What has been established for each. "code" — ioctl code that method sends to driver
(empty = not included in call). Class roles — from §16.3 and §17.3.

**Class C — processor/channel (ord 25–39), object ≥20 B, `RBusLogicalChannel` @+0:**

| ord | address | ioctl code | what it does |
|---|---|---|---|
| 25 | `80A5DAE1` | — | `RDebug::Printf` + DoRequest + `Close` (error path) |
| 26 | `80A5D533` | `0x0400000D` | **DOFF file loading + DCD registration** (`RFs::Connect`→`RFile::Open`→`Size`→ioctl→`RChunk::Base`); builds 84 B records with 16 B UUID |
| 27 | `80A5D9B1` | `0x0400000F` | (no euser calls — thin) |
| 28 | `80A5DAC3` | `0x04000010` | thin DoRequest wrapper |
| 29 | `80A5D901` | `0x0400000C…` | `TDesC8::Ptr`/`User::Free`/`TDes8::Zero` + ioctl (buffer) |
| 30 | `80A5D87F` | `0x04000001` | `User::Alloc` (buffer allocation) |
| 31 | `80A5D9ED` | — | TBuf + `RDebug::Printf` + DoRequest + `Close` |
| 32 | `80A5D751` | (DoCreate) | **`TInt Open(TInt aProcId 0..1, TInt aFlag, const TAny* aAttrs24)`** — `0`=C55x, `1`=IVA in `[this+16]`; `aFlag==1` loads base image via ord 26 |
| 33 | `80A5D4FD` | `0x04000001` | **Close/Detach** + `RHandleBase::Close` |
| 34 | `80A5DAA3` | `0x04000013`, `0x04000010` | thin wrapper |
| 35 | `80A5D955` | `0x04000007`, `0x04000017`, … | **`Control(TInt aOp, …)`** — switch by `aOp` 0..3 (+ two special values), each branch sends own code; out of range → `-5` |
| 36/37 | `80A5D4C9` | — | ctor (clears 0,4,8,12) |
| 38/39 | `80A5D4D9` | — | dtor (+ `operator delete`) |

**Class B — task/node (ord 15–24), object exactly 8 B
`{TInt iTaskHandle; RBusLogicalChannel iChannel;}`:**

| ord | address | ioctl code | what it does |
|---|---|---|---|
| 15 | `80A5DC71` | `0x0C000001` | 4 arguments (r1..r3 + this) |
| 16 | `80A5DC37` | `0x0C000001` | same + `User::WaitForRequest` → **synchronous variant** |
| 17 | `80A5DCDB` | `0x0C00000?` | pair to 15 |
| 18 | `80A5DCA1` | `0x0C00000?` | pair to 16 (with waiting) |
| 19 | `80A5DD0B` | **`0x0C000003`** | thinnest (16 B): single ioctl |
| 20 | `80A5DD1B` | **`0x0C000004`** | 1766 B: heavy descriptor parsing (DCD/enumeration) |
| 21/22 | `80A5DC2D` | — | ctor (clears 8 B) |
| 23/24 | `80A5DC35` | — | dtor (empty) |

**Class A — UUID/DCD objects (ord 1–14), object 8 B:** ord 4 and 6 parse
string via `TLex` (this is UUID parser for format `%08X_%04X_%04x_%02x…`), ord 7
calls ord 6, ord 1/8 copy via `operator new`+`memcpy`, ord 10 = Close
(frees `[this+0]`), ord 13/14 = dtor via ord 10, ord 11/12 = ctor.
This class does not hold a channel — it is purely about node identifiers.

**Object sizes confirmed independently — from `CBal` layout.** Destructor
of `CBal` (@`0x80A41BE2`) tears down members at fixed offsets: `ord13` (dtor A) at
`this+40`, `ord23` (dtor B) at `this+24`, `ord38` (dtor C) at `this+4`. And
`bal ord 27` is simply `C::Control(this+4, aOp=2, 0)`. Thus:

| member | offset in `CBal` | size |
|---|---|---|
| class C (processor/channel) | `+4` | **20 B** |
| class B (task/node) | `+24` | **8 B** |
| (unknown field) | `+32` | 8 B |
| class A (UUID/DCD) | `+40` | **8 B** |

Sizes match what constructors provide (ord 36 clears 0..12 plus
ord 32 writes `+16` → 20 B; ord 21 clears 8 B; ord 11 clears 8 B). Two
independent sources, identical answer.

**Checked (and dismissed) risk — UUID case in section name.** Formatter in
`bridgeapi` @`0x80A61DE8` — `%08X_%04X_%04x_%02x%02x_%02x%02x%02x%02x%02x%02x`:
third and subsequent groups printed in **lowercase**, whereas we named the object
section entirely in uppercase (`.967CBF11_B90E_4B54_A4D3_3C84249EE1DA`). If
loader constructed section name with this format and compared case-sensitively,
node would not be found.

Verification on device itself: **31 nodes in ROM have letters in groups 3–5** — among
them `AAC_ENC_SN`, `EAACPLUS_DEC_SN`, `G711_DEC/ENC_SN`, `G729_DEC/ENC_SN`,
`ILBC_DEC/ENC_SN`, that is, codecs that work on this device every day, and all of
them are written in **uppercase**. Thus uppercase is working; either comparison
is folded (`CompareF`), or formatter serves another purpose. UUID left as is.

**What is not yet present:** exact correspondence "ordinal ↔ name from contract §14.1"
(`node_allocate` / `node_create` / `node_run` / `put_message`). But to
implement loader names are not even needed — ioctl codes and argument
layouts are needed, and they are now known from both sides (C++ and kernel).

### 17.5. Reference sequence from `CBal` — our loader is no longer a guess

Three functions of `bal.dll` provide ready pattern, which only remains to repeat.

**`CBal::Open` (`0x80A4165C`):**
```
LoadPhysicalDevice("EHWAOMAP")        ; fatal for everything EXCEPT -11 (KErrAlreadyExists)
LoadLogicalDevice("EHWA")             ; same; otherwise FreePhysicalDevice and exit
r0 = this+4 (class C)  r1 = 0  r2 = 0  r3 = 0
ord32(...)                            ; Open(aProcId=0 -> C55x, aFlag=0, aAttrs=NULL)
[this+56] = 1
if (err) CBal::Shutdown()
else     ord9(this+40 /*class A*/, this+4 /*class C*/)   ; binding A to processor
```

**`CBal::LoadImage` (`0x80A41642`):** `ord26(this+4, aPath, 0)`, and upon error —
`CBal::Shutdown()`.

**`CBal::Shutdown` (`0x80A41608`):** `ord10(this+40)` → `ord33(this+4)` →
`FreeLogicalDevice("EHWA")` → `FreePhysicalDevice("EHWAOMAP")`.

**What this gives.** Arguments of `ord32`, which we derived from disassembler of function itself
(`aProcId ∈ {0,1}`, `aFlag`, `aAttrs24`), match **byte-for-byte** with how
Nokia calls it: `(C, 0, 0, NULL)`. That is entry point is verified by two
independent paths with no guesses left in it. Likewise confirmed
signature `ord26(C, aPath, 0)` and next step revealed — `ord9(A, C)`.

`dsptest.exe` now mirrors precisely this sequence (and teardown order
`ord10` → `ord33`), **deliberately omitting** `Load/FreePhysicalDevice`: driver
is already brought up by system, and these calls are main suspect in reboots (§17.7, point 4).

### 17.6. Progress of reboot investigation (§16.8) — ARM load acquitted

Bisection with holding time (uptime in each run is continuous counter, so
reboot is immediately visible as reset):

| run | what it did | uptime at start | reboot? |
|---|---|---|---|
| control | without DSP stack, **with** benchmark | 206 s | — |
| holding +7 min | without DSP stack, with benchmark | **666 s** | **no** |
| scan | without DSP stack, without benchmark | 713 s | no |
| (accidentally with benchmark) | without DSP stack | 738 s | no |
| `lib nobench` | **only `bridgeapi.dll`** | 773 s | being checked |

> ## ⚠ EVERYTHING ABOUT "DELAYED REBOOT" BELOW IS FALSE (refuted by user)
>
> Device owner, who observed it live, reported: **device
> reboots IMMEDIATELY**, rather than minutes later. "Delay" was invented by me,
> deduced from when user stopped me to report reboot —
> that is from timing of *messages*, not from behavior of *device*. This is a gross
> methodological error: external signal mistaken for measurement.
>
> What remains valid from this:
> - reboots are tied to runs that touch DSP stack;
> - `load` run killed device right during operation (connection dropped at
>   `RUN`, log remained truncated at `ord26`);
> - bisection "by reboots" and all conclusions about "7–15 minutes delay"
>   below are **invalid**, as they were built on false premise.
>
> Leaving text as is, without rewriting post factum: it shows how false
> premise pulls chain of "confirmations" behind it.

> **ATTENTION, here I erred twice and corrected myself twice.** First "DSP stack
> is to blame", then "benchmark is not to blame". Both times error was same:
> conclusion about BOOT was made from behavior WITHIN boot.
> Device can survive run and reboot 10 minutes later — therefore
> unit of observation here is not "run", but "boot as a whole".
> Below are both false intermediate conclusions and what refuted them.

**THIRD REBOOT CROSSED OUT THIS LINE OF INVESTIGATION.** Complete series of uptime:

| run | what it did | uptime | reboot after? |
|---|---|---|---|
| first in session | DSP-libs + benchmark | 26350 s (7.3 hrs!) | **yes** |
| after reboot | DSP-libs + `RDevice` + benchmark | 140 s | **yes** |
| control | no DSP, with benchmark | 206 s | no |
| holding +7 min | no DSP, with benchmark | 666 s | no |
| scan | no DSP, without benchmark | 713 s | no |
| (with benchmark) | no DSP | 738 s | no |
| `lib nobench` | only `bridgeapi.dll` | 773 s | no |
| holding +7 min | **no DSP, without benchmark** | 1215 s | **yes** |

Last reboot occurred after run that **touched neither DSP stack nor
benchmark** — only HAL, `TFindLogicalDevice` and `RFs::GetDir`. Thus:

- hypothesis "unloading bal/dspmemmapper is to blame" — **not confirmed**;
- hypothesis "ARM load is to blame" — **not confirmed**;
- instead a different pattern is seen: device before start of session stood for **7.3 hours**,
  and since we started working with it, lives approximately **20 minutes each**.

That is correlated is not a specific probe, but the very fact of our interaction (or something
independent that began simultaneously). Candidates not yet separated: remnants of
neighboring project in system (`RomPatcherPlus.Driver`, `dvfs_interface` —
visible in LDD list), deployment daemon, power/battery state.

**Control "doing nothing" — completed, and it turned everything around.** Device
was left alone: uptime 1331 s → idle 25 min → **2881 s**, exactly
1331 + 1500 + overhead. That is **48 minutes without reboot**, of which ~45 min complete
idle (two light `nobench` runs at edges).

Now comparison by proper unit — by boots:

| boot | ARM benchmark run? | how long it lived |
|---|---|---|
| A | yes, 1 time (at 423 MHz) | reboot |
| B | yes, 1 time | reboot |
| C | yes, 3 times | ~1215 s (20 min) → reboot |
| **D (current)** | **not once** | **2881 s (48 min), alive** |

**Every boot in which ARM benchmark ran ended in reboot;
the only one where it did not ran four times longer.** My previous conclusion
"benchmark is acquitted" was mistaken: it relied on device surviving *between*
runs within boot C, whereas reboot happened later in that same
boot.

This is plausible physically: ~9 s solid 100% ALU (three cores × best-of-3 +
warmup + calibration of `SpinNop`) on a 2007 device which session caught
overclocked to 423 MHz, with power/battery in unknown condition.

**Single-factor experiment — completed, benchmark ALSO refuted.** On stable
boot D full benchmark was run (uptime 2961 s), followed by 20 min idle:
**uptime 4171 s (69 min), continuously**. No reboot.

### 17.6.1. Correct symptom found: touching `bridgeapi.dll`

If boots are grouped not by benchmark, but by **whether `bridgeapi.dll`
was loaded**, separation becomes complete:

| boot | `RLibrary::Load(bridgeapi)` + `Close`? | lived |
|---|---|---|
| A | yes (+ `LoadLogicalDevice`) | reboot |
| B | yes (+ `LoadLogicalDevice`, `RDevice`) | reboot |
| C | yes — level `lib` at 773 s | reboot later than +442 s |
| **D** | **not once** | **69 min, alive — despite full benchmark** |

**Why I was mistaken three times.** Each time conclusion was made from too short
a window: level `lib` was checked after 7 min and looked clean, while reboot in
boot C occurred later. **Delay here is ~7–15 minutes**, so any
window shorter than ~20 min gives false "clean". This is the main methodological lesson of this
investigation: unit of observation is boot as a whole, while minimum
window is 20+ minutes.

**Mechanism is plausible and concrete.** `bridgeapi.dll` has static
constructors (loop at `0x80A5D480`), and therefore static destructors that
execute upon unloading. Among its strings are **`BridgeDcdSync`** and
**`*BridgeDcdSync*`** — names of global mutex (§10). If its static
deinitialization closes/deletes global DCD synchronization object which is
subsequently used by audio stack, delayed kernel panic is expected consequence.

Key nuance: all this happens only when **we are sole owner** of
library. If audio stack holds `bridgeapi.dll` loaded, our
`Load`/`Close` only increments reference count and static destructors do not
run. That is risk depends on whether something is playing on device.

### 17.6.2. What this means for loader — decision rests with user

We cannot simply "not unload": in Symbian upon process termination
handle is closed anyway. Therefore options are:

1. **Reconcile with one reboot per run.** Reboot is delayed, so run itself
    manages to finish and log is collected. Cost — after each run
    one must manually restart daemon on device.
2. **Keep `bridgeapi.dll` loaded residently** (e.g. by daemon
    itself), so our process is never the last owner.
3. **Bypass `bridgeapi` and work with `Hwa` channel directly** — ioctl map we
    have complete (§17.1, §17.2). Plus: zero static deinitialization. Minus:
    calls go to kernel, and error costs reboot rather than process crash.

This decision carries cost for user (option 1 — manual daemon restarts,
option 2 — change in neighboring project), so it belongs to them, not to me.

### 17.7. Neighboring project already went through all this — two records changing the picture

`../SymbianOverclock/docs/state.md` and `WRITEUP.md`:

1. **| 112+ | 430+ | — | auto-reboot after minutes |** — at DPLL multiplier 112+
   (≈430 MHz and above) device **reboots on its own after minutes**.
   Our very first run of this session measured **423 MHz** at uptime 7.3 hrs —
   that is device was left **overclocked**, near threshold of auto-reboot. This
   explains first reboot without any involvement of DSP probes.
2. **WRITEUP §8 "Four 'reboots' — actually none"**: there what observer
   took for reboot was **Symbian shell restart**;
   distinguishable only by counter that resets only upon full reboot.
   Hence neighbor's rule: "network availability is not proof that device
   did not reboot".

Therefore `UPTIME:` on first line of log is not decoration, but main instrument of this
investigation. Confirmed by it: reboots No.1 and No.2 are **real** (counter
reset: 26350 → 140, then 140 → 206). Reboot No.3 so far only from words of
observer — control run after idle will show whether it was real.

**What this means for methodology:** DSP probes were blamed prematurely. Correct
causality so far: device started session overclocked to mode with known
auto-reboot, and at least first reboot is explained by this, rather than our code.

3. **Leading hypothesis for remaining reboots — also from neighbor's experience**
   (`state.md`, "Kernel patch must have rollback"):

   > READ/EXEC patch of `DoControl(1)` body lives in ROM-shadow and **survives our
   > process**. Channel `dvfs_interface` is opened not only by our code
   > (`mmrmserver.dll`, `fmradiotunercontrol.dll`), so **abandoned patch sooner or
   > later reboots device**.

   In LDD list on device both **`dvfs_interface`** and
   **`RomPatcherPlus.Driver`** are present. Pattern "reboot sooner or later, regardless of
   what our code does" — exactly what neighbor describes. Our project did not
   apply this patch and has no means to remove it; this is a question for SymbianOverclock session
   (there `EndPatchSession()` exists with proper unshadow order + verification of
   rollback via `DoControl(1,0)`).

4. **Best reasoned cause of reboots No.1 and No.2 — our own
   `User::LoadLogicalDevice`.** Dissecting `CBal` gives benchmark of how bridge
   driver should be brought up (`0x80A4165C`):

   ```
   LoadPhysicalDevice("EHWAOMAP") -> r4
   if (r4 != 0 && r4 + 11 != 0) bail   ; fatal for everything EXCEPT -11
   LoadLogicalDevice("EHWA")
   ```

   That is Nokia clearly expects `KErrAlreadyExists` (−11) and considers it normal —
   sign that duplicate loading is a known hazard. Its pair
   `CBal::Shutdown` (`0x80A41608`) does the reverse: `ord10` (Close A),
   `ord33` (Close C), `FreeLogicalDevice("EHWA")`, `FreePhysicalDevice("EHWAOMAP")`.

   While our first two runs called `User::LoadLogicalDevice("ehwa.ldd")` and
   received **`0`, not `−11`**, although driver was already in system (visible
   in LDD list as `Hwa`). Directly following these two runs came reboots No.1 and
   No.2. Call removed even before bisection (replaced with passive
   `TFindLogicalDevice`), and since then not a single run with DSP probes gave reboot.

   **Status — hypothesis, not fact.** In favor: coincidence 2 of 2, plausible mechanism
   (second instance of bridge driver alongside live audio stack, and we did not
   relinquish it) and that Nokia itself in `CBal` clearly prepares for `−11`. Against:
   we saw neither panic nor dump, and `KErrNone` from `LoadLogicalDevice` might
   have been harmless. Prove can only be done by repeating this exact call —
   which we will not do: cost of check (reboot) is higher than value of answer,
   as call is not needed by us anyway.

   Reboot No.3 is not explained by this — it happened after run without DSP at all.
   That is there are at least two causes, and second lies outside our code.

**What is needed from user (the only thing that cannot be ascertained from here):**
whether dvfs/ROM-shadow patch from neighboring project remained applied and whether
`RomPatcher+` does not apply something automatically at startup. While this is open,
any bisection of our probes measures noise, not signal.

**No crash dumps on device:** all six typical MobileCrash paths
(`C:\logs\`, `C:\logs\mobilecrash\`, `C:\data\mobilecrash\`, `E:\mobilecrash\`,
`C:\mobilecrash\`, `E:\logs\`) yield `-12` (KErrPathNotFound) — crash reporter
not installed on this device, so confirming panic via dump will not work;
bisection remains.

## Streaming worker — hardware confirmation 2026-10-01

Custom TSK task in generic library 2 processed 8×512 B without repeated
create on N95 and E90, leaving node in CREATED. Q15 dot results, echo,
sequence and stop correct. Stock RUN was not called. Output reclaim,
completion SEM, terminated 3, task/SEM delete and normal cleanup succeeded
with FINAL/EXIT0. Useful ARM CRC 64KiB overlapped DSP across three pairs on each.

This is a new channel compared to old create-only bench and unsuccessful RMS/MSG
experiments; their negative journals are preserved. Successful short series
does not prove audio coexistence, long stability or application speedup.
N95 had doubled timing intervals, DSP reported counts/ms 164 requires
calibration. Raw percentages are not isolated gain from overlap.

Contracts, complete measurements and limitations —
[STREAM_RESEARCH.md](STREAM_RESEARCH.md#streaming-worker-in-created--v16-both-phones),
[N95](evidence/2026-09-30/n95-worker-stream-v16-results.json),
[E90](evidence/2026-09-30/e90-worker-stream-v16-results.json).
Original DSP files/clocklogs restored readback-equal, PS0. Further
verifications — stable frequencies, timer calibration and application packets.

### V17: matched pairs and DSP timer boundaries

On N95 stock dvfs_interface request 0 reserves MPU 100% and releases
reservation without patches; live native code verified. Three pairs without
doubled intervals: S250–251/P149–151 ms, E90 S259–263/P156–160 ms.
Correct Q15/echo/useful ARM CRC and clean termination in 24 v17 runs.
This is ~40% reduction in wall time of test load, not application gain.

Three calibration runs on each: short 100–400 ms intervals compatible with
19.2 MHz, but 800 ms idle yields only ~501 ms DSP at this scale versus 828–876 ms
ARM. Cause unknown; do not explain by MPU DVFS alone and do not divide raw ticks
by 164. Complete methodology and bounds — STREAM_RESEARCH.md, evidence —
docs/evidence/2026-10-01/{n95,e90}-worker-stream-v17-results.json.
Normal/original logs exact restored, PS0, hosts 17 installed/readback-equal.

## V18: verified application-size packets, 2026-10-01

On N95/E90 host v18 + worker protocol 18 passed 22 runs/587 packets on
each. Generic library 2, CREATED, without official RUN; 32 packets in a single
create, explicit stop, task/SEM/STRM/native cleanup, FINAL/EXIT0.
Verified 512/1568/1792/2048/2304/4096 B, including 32-byte header.
WSOLA 1760 B payload fits into 1792-byte input; MDEC 1536 — into 1568.
Q15 dot 240, reps 1000 and ARM CRC verified on 8×4096 B.

In worker-transfer reps 0/no ARM CRC 96 samples per size. Equal-size echo 1792:
N95 median 518/max 549 us; E90 median 640/max 7812 us. Slow correct packets
not excluded; suitability of actual WSOLA for hop≈4.99 ms is not yet proven.
DCD was not changed; size-bearing native instructions on both ROMs reconciled.
Original DSP returned GET-equal; later E90 status reconfirmed
original clocklog, host v18 and PS0. N95 upon later recheck did not
respond; request sent to user to wake it up. This does not change the already
saved exact recovery and does not prove current availability of N95.

Methodology, all latency samples, byte-exact journals, artifacts and limitations:
`docs/PACKET_SIZES.md`, `docs/evidence/2026-10-01/` and `work/PLAN_V18.md`.
Raw binaries/firmware/ASM/keys/screenshots remain ignored. F05–F08
so far in_progress; full objective still requires separate completion audit.
