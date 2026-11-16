# Handoff of Work to agy — 2026-10-02

## Task and Completion Boundary

The user permitted pushing commits and continuing until full completion
of the plan. The last request is to preserve this summary for agy.
Active assignment: `work/CODEX_TASK_2026-10-01.md`, plan
`work/PLAN_D0_D2.md`, status `work/features.json`. Historical F01–F08
are completed in the research scope; this **does not mean completion of D0–D2**.

- D0: three consecutive clean cycles of custom create → official RUN → packets
  → delete/free/close, FINAL/EXIT0, device availability after each.
  Current result **0/3**, historical experimental RUN calls **5**.
- D1: after D0, verify DMM/zero-copy, ring **16 KiB TOTAL**, correctness,
  ownership/cache/wrap/cleanup; repeated latency/bandwidth measurements.
  Hardware D1 has not yet been run.
- D2: measured MDEC/SPU/WSOLA verdicts by
  `max(H + D, W) + S/N < A + W`. Current conclusion provisional;
  update after D1. Do not edit emulator and browser in this assignment.

General intent: DSP performs work asynchronously, ARM at this time performs
other useful work. Do not substitute this criterion with a synchronous DSP call.

## What Was Completed in This Session

1. Context was restored and uncommitted host29 diagnostic was found, newer
   than the last STATE entry. Its `patcher-read-check` had already executed in
   the previous incomplete turn; there was no repeated run.
2. Preserved read-copy journal was repeatedly retrieved from E90 before writes:
   SHA-256 `56167F767D4B30FF225DA24BFB0F6666FD25F16B9FB22B1398D4DBB911195D76`.
   Proven three copies of 24 B each into custom user buffer: own RAM, ROM reader
   `803F7664`, module BSS `C8010B20`; FINAL/EXIT0, without DSP processor open,
   kernel code writes, or PRCM writes.
3. Added `tools/rev/audit_arm_message_runtime.py`: static verification
   of 28 instructions, two BL targets, BSS header, and reader body.
   Added `tools/summarize_arm_message_runtime.py` for offline publication
   of 16 raw proofs, pointer audit, and restoration checkpoint.
4. Strengthened validator in `tools/e90_task_session.py`: exact ROM words,
   source addresses, size, order, shared destination, firmware/profile,
   FINAL0, and absence of DSP open; accounted for CRLF of real journal.
   Nine offline tests pass; environment/artifact check successful.
5. E90 returned all five originals: DLL/log/ocprobe.log/EXE/hash.
   PUT→GET and final SHAs match. Host20, c55stream/ocprobe PS0,
   daemon startTick61087 unchanged. Reboot not needed.
6. Following explicit permission from the user, two commits were pushed to private main:
   `5fc3071` and `26d6354`. Remote HEAD verified:
   `26d63542d08be5c07b38e4896745d9cf24e0e147`.
7. After push, executed only local analysis of ROM kernel containers,
   factory, and manager. Its intermediate results are recorded below.
   No new phone INFO/PUT/START/MSG/RUN occurred after restore.

Current report: `docs/ARM_MESSAGE_RUNTIME_2026-10-02.md`.
Current evidence: `docs/evidence/2026-10-02/arm-message-runtime-checkpoint.json`.
Previous finite MSG diagnostics:
`docs/WORKER_MESSAGES_2026-10-02.md` and
`docs/evidence/2026-10-02/worker-message-checkpoint.json`.

## Devices, Versions, and Unresolved Problem

Both devices are permitted, always with explicit IP and identity check:
E90 `192.168.3.21:2323`, screen 800x352, MachineUid20002496;
N95 `192.168.3.22:2323`, screen 320x240, MachineUid20002D84.

E90 last verified state — five originals exact, host20/PS0.
N95 was not polled in this continuation; last previous proof —
five originals exact, host20/PS0, startTick22918156. Before a new action,
verify state anew, do not declare old proof as current live state.
Previous clock snapshots: E90 ARM330.24/bus110.08/DSP220.16 MHz;
N95 existing m111 ARM426.24/bus213.12/DSP284.16 MHz, without PRCM writes.

Local EXE — host29, DSP diagnostic protocol26; artifact38:
`docs/evidence/2026-10-01/d0-worker-message-v38-artifacts.json`.
Source/EXE hashes reconciled with it. On phone after restore host20.
Do not confuse local host29 with the installed version.

Four previous finite CREATED MSG diagnostics (three E90, one N95)
yielded DSP put1 and correct STRM snapshot, but ARM receive−33/empty record.
Created delete/free/close clean. These are not D0 cycles. Do not repeat the same
MSG receive variants without new evidence.
No-input worker cleanup hung earlier and is still not fixed.

## Verified Static MSG Pointer Chain

- board+264 → context, allocation 364 B.
- context+48 = common board = board+8.
- context+24 → reader = common board+164 = board+172.
- reader byte64 = board byte236; setup writes 1.
- reader DWORD0 = shared-memory ARM base; this is not yet fromDSP header.
- context+224 → fromDSP header; context+240 → records = header+8.
- queue+16 — source; queue+40 — pending receive.

`C8010B20` — six BSS words/flags, **not** MSG context root.
Real reader byte64, runtime shared mapping, and queue routing have not yet
been measured. Prior to pointer traversal, live root provenance,
identity, allocation/mapping bounds, and lifetime are required; numerical kernel range
in itself is not sufficient. Snapshots are non-atomic.

## Latest Local Analysis — Promising Path to Root

These results were obtained after commit 26d6354. These are static observations,
not yet a separate automated audit and not permission to execute kernel calls.

1. In N95 `memoryaccess.ldd` native object enumeration calls stub
   `8038F5B0` → kernel `8008CE40`, actual export ordinal251.
   Caller indexes the returned array of containers. In E90 actual ordinal251
   → `80037778`: `ldr r0,[pc,#2308]; bx lr`, literal `80038084` =
   **`C80019D4`**. This is statically found container array root;
   its RAM has not yet been read. The name Kern::Containers is inferred from enumeration
   behavior, not from the E90 symbol table.
2. N95 container At stub `8038F590` → `8008D638`, actual ordinal12;
   E90 ordinal12 → `80038290`. Body checks index against count+16,
   then reads array+20 and array[index]. Container type indices and
   root array length still require audit; do not assume them from memory.
3. E90 PDD export1 → factory entry `803DD8A4`, allocation 120 B.
   Constructor `803DD7D8` sets vtable **`803F8380`**.
   This is candidate identity for locating the factory in the correct container.
   Per-processor fields have stride32, two entries. Factory+44 — state/flag,
   **not a pointer**; factory+48 — manager allocation 68 B;
   factory+68 — configuration allocation 1136 B.
4. Manager constructor `803E32E8` sets word0 magic
   **`434F5250` (PROC)**, not vtable; factory at manager+56,
   processor index at manager+60. Manager+44 → board interface.
5. Manager setup `803E3348`: branch processor0 allocates 336 B,
   constructor `803EFFCC`, adds 8 to returned pointer before store+44.
   Branch processor1 allocates 372 B, constructor `803F3B0C`, different layout.
   It is branch0 that aligns with previously audited board/common+8 chain.
   Must trace complete returned pointer/identity/lifetime before runtime.

Intermediate local ignored files for disassembler:
`out/e90-kernel-code.bin`, `out/e90-kernel-disasm.txt`,
`out/e90-pdd-code.bin`, `out/e90-pdd-disasm.txt`, `out/e90-ldd-code.bin`.
In `out/e90-ldd-disasm.txt` there was an erroneous adjust-vma 803F863C;
real base LDD **803F8648**. Regenerate this disasm before use.
Authoritative saved ROM: `work/evidence/e90/rom/{ekern.exe,ehwaomap.pdd,ehwa.ldd}`.
N95 ROM: `../eka2l1/data/drives/z/rm-320/sys/bin/`.
An attempt to extract memoryaccess from E90 4MiB window did not find it;
E90 memoryaccess module was not obtained, kernel ordinal mapping was read
directly from saved E90 ekern export table.

## Next Actions

1. Complete offline audit of container root: length/type/index, headers,
   array bounds, factory identity, and manager→board→context chain.
   Verify instruction signatures and module hashes with a reproducible script.
2. Design a bounded read-only snapshot with proven root/lifetime
   and mapping bounds. Do not force IRQ/DFC and do not patch reader based on a hypothesis.
3. Before runtime, verify specific device/PS and back up five files.
   After diagnostic — journal GET, clean ownership release, exact restore.
   In case of unknown/pending teardown, do not KILL/free/unload a live owner;
   record recovery in HELP_NEEDED, request physical reboot from the user.
4. Only after new evidence — MSG/RUN, eliminate native delivery/EXITACK,
   execute D0 three clean cycles; then D1 and D2 according to the full plan.

## Environment and Verifications

Root: `D:\VsCodeProjects\SymbianProjects\TMS320C55x test`.
PowerShell 7; Python 3.12:
`C:\Program Files\LibreOffice\program\python.exe` (python/py absent in PATH).
Python sys.executable in LibreOffice may point to python-core;
for subprocess explicitly use wrapper exe if needed.
SDK and ARM toolchain are neighboring directories, TI CGT 4.4.1 on C:;
`tools/env.cmd` locates them. External experiments/builds bounded via
`tools/run_bounded.ps1`, without LAN fallback, each hypothesis has a separate proof.

Latest successful local checks:

```powershell
& 'C:\Program Files\LibreOffice\program\python.exe' -m unittest discover -s tools -p test_e90_task_session.py -v
& 'C:\Program Files\LibreOffice\program\python.exe' tools\summarize_arm_message_runtime.py
pwsh -NoProfile -File tools\check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

Git requires per-command safe.directory due to ownership of different Windows users:
`git -c safe.directory='D:/VsCodeProjects/SymbianProjects/TMS320C55x test' ...`.
External initial edits preserved separately: modified
`docs/APPLICATION_CANDIDATES.md`, untracked `work/CODEX_TASK_2026-10-01.md`.
Do not reset them or accidentally include them in own commits.

## Safety Classifier

First git push was rejected by auto-review due to unconfirmed permission
to export code/hardware journals to GitHub. The user explicitly permitted
pushing commits; after that push completed and remote HEAD verified.
Latest environment instructions: danger-full-access, network enabled,
approval policy never; do not pass `sandbox_permissions` in commands.
This does not waive hardware discipline or requirements to prove pointer provenance.
No new visible tool rejections occurred after permission; the user
reported a classifier complaint without new specific text.

Sensitive mechanism of diagnostic: control 105 of `patcher.ldd` copies source
memory to destination. In proven host29 diagnostic destination
was process's own RAM; kernel code/PRCM were not written.
New runtime traversal is not implemented and was not launched.
