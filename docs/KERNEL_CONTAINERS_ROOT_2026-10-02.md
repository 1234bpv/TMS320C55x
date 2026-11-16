# Origin of the kernel container root and object chain (2026-10-02)

## Purpose and context

The previous audit (`docs/ARM_MESSAGE_RUNTIME_2026-10-02.md`) identified the chain
of pointers from the `board` object to the message context, the reader (`reader`),
and the shared `fromDSP` window. However, the BSS variable `C8010B20` turned out to
be an initialization flag rather than the root of the structure.

This document and the reproducible script `tools/rev/audit_kernel_containers.py`
prove the exact origin of the kernel object root (the `DObjectCon` containers)
via kernel export 251, the identification of the PDD factory by its vtable,
and the transition to the DSP processor manager, the board interface (`board`),
and the message context. The audit was performed offline on saved original ROM
images of the E90 and N95, without running phone commands.

## Audit results

### 1. Root of the kernel container array (`Kern::Containers`)

In the Symbian EKA2 kernel (`ekern.exe`), export 251 returns a pointer to the root
array of `DObjectCon*` container pointers:

- **E90**: export 251 at address `80037778` loads literal `80038084` = **`C80019D4`**.
- **N95**: export 251 at address `8008CE40` loads literal `8008DC1C` = **`C80019F0`**.

### 2. Number and types of containers (`TObjectType`)

In the system call for object lookup (`TFindHandleBase::NextObject`, `ekern.exe` `8002B930`):
- Bounds check: `8002B934: cmp r0, #17` (exactly 17 object types: 0..16).
- If `r0 >= 17`, a panic is generated: `8002B93C: movcs r0, #25` (`EBadObjectType` = 25 from `e32kpan.h`).
- Array size: 17 words of 4 bytes = 68 bytes. For the E90, the range is `C80019D4`–`C8001A18`.
  The upper limit is confirmed by the check `8003FCD0: cmp r4, #17` with literal `8003FD2C` = `C8001A18`.

Cross-referencing with the opcodes of the `TFind*::Next` functions in `euser.dll` (`movs r2, #type`):
- **Type 0**: Thread (`DThread`, `_ZN11TFindThread4Next...`)
- **Type 1**: Process (`DProcess`, `_ZN12TFindProcess4Next...`)
- **Type 2**: Chunk (`DChunk`, `_ZN10TFindChunk4Next...`)
- **Type 3**: Library (`DLibrary`, `_ZN12TFindLibrary4Next...`)
- **Type 4**: Semaphore (`DSemaphore`, `_ZN14TFindSemaphore4Next...`)
- **Type 5**: Mutex (`DMutex`, `_ZN10TFindMutex4Next...`)
- **Type 7**: Server (`DServer`, `_ZN11TFindServer4Next...`)
- **Type 9**: Logical device LDD (`DLogicalDevice`, `_ZN18TFindLogicalDevice4Next...`)
- **Type 10**: Physical device PDD (`DPhysicalDevice`, `_ZN19TFindPhysicalDevice4Next...`)

PDD container slot in the array:
- **E90**: `C80019D4 + 10 * 4` = **`C80019FC`**
- **N95**: `C80019F0 + 10 * 4` = **`C8001A18`**

### 3. Structure of the `DObjectCon` container

Kernel export 12 (`80038290` on the E90, `8008D638` on the N95) is `DObjectCon::operator[](TInt aIndex)`:
- `container + 16` (`+0x10`): object count `iCount`.
- `container + 20` (`+0x14`): pointer to the array of pointers `DObject** iObjects`.
- `container + 24` (`+0x18`): pointer to the locking mutex `iMutex`.
- Index check: if `index < 0` or `index >= iCount`, panic `"DOBJECT"`, 8 is raised.

### 4. Identification of the `ehwaomap` factory in the PDD container

PDD export 1 (`803DD8A4` on the E90, `80199254` on the N95) allocates 120 bytes for the `DPhysicalDevice` object:
- The constructor (`803DD7D8` on the E90) writes the vtable at offset 0.
- **E90 vtable**: **`803F8380`** (literal `803DDA6C`).
- **N95 vtable**: **`801B3D44`** (literal `8019941C`).

Identification rule: among the pointers `iObjects[0..count-1]` in the PDD container, the
factory of the driver `ehwaomap` is uniquely identified by the condition:
`*(TUint32*)obj == 0x803F8380` (on the E90).

### 5. Traversal from factory to manager and board

1. **Factory → Processor 0 manager (DSP)**:
   - Processor fields have a step of 32 bytes.
   - At offset `factory + 48` (`+0x30`), a pointer to the allocated manager (68 bytes) is stored.
   - The manager constructor (`803E32E8`) writes:
     - `manager + 0`: signature magic word **`434F5250` ('PROC')**;
     - `manager + 56`: back-pointer to `factory`;
     - `manager + 60`: processor index `0`.

2. **Manager → Board (`board`)**:
   - The manager setup function (`803E3348`) for processor 0 allocates 336 bytes for the `board` object.
   - The `board` constructor (`803EFFCC`) initializes the board.
   - 8 is added to the returned pointer (`common board = board + 8`).
   - The pointer `board + 8` is stored in `manager + 44` (`+0x2C`).
   - Accordingly, the base address of the board: `board = *(TUint32*)(manager + 44) - 8`.

3. **Board → Context → Reader → DSP window**:
   - `board + 236`: exchange acknowledgment byte (`swap_byte`, initialized to 1).
   - `board + 264`: pointer to the allocated message context (364 bytes).
   - `context + 48`: consistency check — must equal `board + 8`.
   - `context + 24`: pointer to the reader = `board + 172`.
   - `reader + 0`: base address of the ARM shared window for the DSP.
   - `reader + 64`: acknowledgment byte (must equal the value at `board + 236`).
   - `context + 224`: header of the `fromDSP` queue.
   - `context + 240`: array of records `records = fromDSP + 8`.
   - `context + 16`: queue source; `context + 40`: active receive wait.

## Design of a safe bounded read-only snapshot

To read the live state without modifying memory, a step-by-step validation protocol was developed:

1. **Input control**:
   - Verification of MachineUid (`0x20002496` for the E90).
   - Reading the container root `0xC80019D4`.

2. **PDD container validation**:
   - Read the PDD container pointer from slot `0xC80019FC`.
   - Verify that the address range is within the kernel (`0xC8000000`–`0xC8100000`).
   - Read the container header (24 bytes): the counter `count` must satisfy `1 <= count <= 32`.
   - Verify the address of the pointer array `iObjects`.

3. **Factory lookup by vtable**:
   - Read the object pointers. For each, read the first word (vtable).
   - Find the object with `vtable == 0x803F8380`.
   - If the object is not found — immediate exit without a crash.

4. **Manager validation**:
   - Read the pointer at `factory + 48`.
   - Verify the word at `manager + 0` is equal to `0x434F5250` ('PROC').
   - Verify `manager + 56 == factory` and `manager + 60 == 0`.

5. **Computation of board and context addresses**:
   - Read `common_board = manager + 44`.
   - `board = common_board - 8`.
   - Verify `board + 264` (context). Read `context + 48` and check against `common_board`.
   - Read `context + 24` (reader) and verify equality to `board + 172`.
   - Read `reader + 0` (ARM base address of the shared window).
   - Read `reader + 64` and `board + 236`.

6. **Reading the message queue**:
   - Verify that `context + 224` (header `fromDSP`) lies within the shared window.
   - Read the header, offsets, and current queue values without opening the DSP processor.

All read operations are performed exclusively into the process's own buffer in user RAM.
No writes to kernel memory, system registers, or PRCM take place.

## Artifacts and scripts

- Reproducible audit script: `tools/rev/audit_kernel_containers.py`.
- Evidence publication script: `tools/summarize_kernel_containers.py`.
- Generated evidence: `docs/evidence/2026-10-02/kernel-containers-audit.json`.
- Unit test: `tools/test_e90_task_session.py` (`test_kernel_containers_audit_proves_e90_and_n95_root_and_factory`).
