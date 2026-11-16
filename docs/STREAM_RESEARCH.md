# ARM–C55x streaming channel: research 2026-09-30

## New assignment D0–D2, 2026-10-01

Current [E90 lifecycle/DMM audit](LIFECYCLE_DMM_2026-10-01.md):
failed delete is not protection against unload; cancel rc0 requires separate
completion of transfer status. Host21 holds an indeterminate session until manual
reboot, supervisor does not send KILL. Generic RUN-stop candidate built,
but three clean official RUNs have not yet been verified; physical SIS install is needed.
DMM ordinals refined: reserve27/map31/unmap34/unreserve28. Mapping,
ring16KiB and bandwidth not measured. N95 was not queried. Intermediate
[PS1 decision](PS1_CANDIDATES_2026-10-01.md) uses old v18/v20
measurements and separately marked scenarios. Research history is preserved below.

## Limit of evidence

Static analysis of stock ROM RM-320 and new hardware results are presented below. On N95, custom node transferred 8 valid packets in a single create/RUN, but full cleanup ended in an error. Parallel speedup has not yet been measured. Old message crashes do not prove the absence of other channels. Approximately 9 ms from old `CHARACTERIZATION.md` relates to creating an empty node, rather than transferring a slice to a long-lived node.

## Established contracts of RM-320

Tools: `tools/rev/exports.py`, `fn.py`, `words.py`; ARM for `ehwa.ldd`/`ehwaomap.pdd`, Thumb for `bal.dll`/`bridgeapi.dll` functions with odd exports. `fn.py` now uses a separate temporary file for each process: previous parallel analyses with shared `_fn.bin` have been discarded.

| Operation | Source | What is established |
|---|---|---|
| Task / node creation | `bal.dll:80A41DDC`, existing host | `Ctl(4, raw32, &handle)`; SDK `TBuf8<20>` has only 28 B, then `Ctl(5, handle, &status)` and status completion |
| Execute launch | `bal.dll:80A41976`, LDD `801B4294`, PDD `801A1404` | `0x08000007`; PDD virtual slot +32; separate launch after create |
| Completion / deletion | `bal.dll:80A41F4C`, LDD `801B5118`, PDD `801A25C4/801A2374` | `Ctl(6, handle, &status)`; in running branch when PDD node+440=0 sends RMS_EXIT, ACK triggers delete; after success `Ctl(7)` frees host task |
| ARM → DSP | `bal.dll` ord6 `80A41863`, LDD `801B4988/801B4478`, PDD `801A1A90` | `0x0800000E`, 28-byte packet; PDD slot +60 |
| DSP → ARM | `bal.dll` ord5 `80A418BF`, same LDD functions, PDD `801A1890` | `0x08000010`, same packet; PDD slot +52 |
| Stream cancellation | `bal.dll:80A41AD9/80A41AEB` | task15/task17; stream index argument must be preserved |
| Buffers | `balbuffers.dll:80A42408`, bridgeapi ord30 `80A5D87F` | stock client requests buffer rounded up to 4 KiB in mode 2; mode 0 via `User::Alloc` also exists |

Streaming operation packet is copied by LDD via `ThreadRawRead(..., 28)`. The first three words are `TPtr8` representation (type/length, maximum length, address), followed by `TRequestStatus` address, data length, additional argument, and stream index. `bal.dll:80A41F2C` copies these seven words. Input PDD uses length, and both directions use status and index. Final value of the additional argument and completion behavior must be verified before the test.

DNode virtual methods table found via RTTI `801B397C`, reference `801B3DE4`, start `801B3DE8`. This independently links LDD with the required PDD functions; name of an arbitrary disassembler file is not evidence of operation.

`bridgeapi` ord3 specifies 176-byte stream structure **by value**, not by pointer: index in r1, direction in r2, first word of structure in r3, remainder on the stack (`80A5E68E/80A5E064`). Internal stream descriptors: input +184, output +1592 from props; up to eight of each, step 176. Initial descriptor contains no usable buffer size; before create it must be filled.

In ROM there is dynamic `STRMCOPY_TI`: `system/apps/strmcopy/strmcopydyn.dll55l`, UUID `7EEB2C7E_785A_11D4_A650_00C04F0C04F3`, one input and one output. This is a node example, not processor base image. Its `.dof55l` should not be passed to PROC-load instead of `baseimage.dof`.

## Candidates and verification order

1. Stock host streams: custom TASK node with one input/output, configured props, single create/run, transfer of multiple packets via task14/task16. Strongest candidate: used by production `bal.dll`.
2. Native buffers and DSP mapping: analyze ord30 and `dspmemmapper` together with cache maintenance in `ebridgeutil`; confirm DSP addressing in 16-bit words and buffer owner. Mere fact of ARM buffer allocation does not prove DSP access.
3. Shared ring buffer: possible after proof of mapping, coherence, and notify; do not use guessed physical address.
4. DSP/BIOS worker via `TSK_create`/`SEM`: alternative method of long-lived execution, but without a return channel does not provide a streaming prototype.
5. Messages: preserve old risky attempts as negative results of specific arguments. Repeat only after a new complete contract.

For comparison, primary source code of [TI Bridge node.c](https://android.googlesource.com/kernel/common/+/f761237eee55222fdb509c79e784a67ab3d72cbd/drivers/staging/tidspbridge/rmgr/node.c), [Linux v2.6.37 tidspbridge](https://github.com/torvalds/linux/tree/v2.6.37/drivers/staging/tidspbridge), and [original dsp-dummy](https://github.com/felipec/dsp-dummy) was used. Their Linux ABI does not transfer to Symbian.

## New hardware readings

- N95: INFO 320×240; live `bridgeapi.dll` read via daemon, 20544 bytes, code `80A5D458`. Read-only `ocprobe patcher dsp 1` ended in `EXIT 0 Kill`: current multiplier 111, DSP divider 3 (`CM_CLKSEL_DSP=000023C3`), hence DSP 284160 kHz at current DPLL. In old ocprobe the "firmware math" line uses **stock** CORE and is not the frequency of this run.
- E90: INFO 800×352; read-only clock probe ended in `EXIT 0 Kill`, profile RA-6 400.34.93, divider 3 (`00000343`), without NOT STOCK message. Direct reading of `Z:\sys\bin\bridgeapi.dll` by daemon rejected with `-46`; likewise STAT in `sys\bin`. This is a limit of daemon permissions, not absence of DSP.
- Both previous `E:\ocprobe.log` preserved in `work/device-backups`; DSP host/node have not yet been replaced. New journals are `work/evidence/{n95,e90}/clock-before.log`.

These are initial session readings. Later results and changes are given below.

## TI STRM ABI and phase context

Primary source: local copy of [TI userspace-dspbridge](https://github.com/kpykc/userspace-dspbridge),
commit `342b027b642eed909e232b2bc1fa144fb0a94c8c`; `strm.h`, `rms_sh.h`,
`rmsdefs.h`, `node.h`, and `source/samples/dsp/strmcopy{Create,Execute,Delete}.c`.
Firmware `STRMCOPY_TI` additionally verified via `DLLdump` and `dis55`.

- `RMS_STATUS` / STRM sizes — 32-bit `long`; on C55x `char`/`short`/`int`
  are 16 bits, and stream MAU is a 16-bit word. 256 MAU = 512 ARM bytes.
- `RMS_StrmDef`: five 32-bit words size/nbufs/segid/align/timeout, then
  name in 16-bit characters. `STRM_Attrs`: four 16-bit fields
  nbufs/segid/align/timeout. `STRM_INPUT=0`, `STRM_OUTPUT=1`.
- `STRM_issue(stream, ptr, datasize, bufsize, arg)` transfers buffer ownership;
  reclaim permitted only after issue. `STRM_reclaim(..., NULL, ...)` for
  optional pbufsize explicitly permitted by TI and used by firmware node.
- Stock execute first issues input, then `NODE_wait`, and reclaim output
  performs only after prior issue output. Specific timeouts and cleanup
  must be verified in live node state.
- Firmware stores context in `env->moreEnv` at offset **12 C55x words**;
  create allocates it via `MEM_valloc`, execute/delete retrieve it from there.
  New prototype reproduces this and has compile-time offset verification. Previous
  variant with phase static/BSS fields preserved in results history.

## N95 hardware journal

Profile: RM-320, `V 35.0.001 / 11-11-09`, MachineUid `20002D84`.
All 39 exports and start of internal DCD parser verified before driver
calls. ARM FastCounter time has resolution of 1/32768 s (~30,5 µs).

| Experiment | Result | Evidence |
|---|---|---|
| First base load, initial state m111/div3 | Reboot, last entry BEGIN base load | local `stream-create-first.log`, user reply |
| Base-only after reboot, stock m86/div3 | base load=0, close, FINAL=0 | [base stock](evidence/2026-09-30/n95-stream-base-stock.txt) |
| Node with 1 input / 1 output: create/delete | create=0, 5584 µs; delete=0; FINAL=0 | [create stock](evidence/2026-09-30/n95-stream-create-stock.txt) |
| First execute, phase-local BSS | Reboot, last entry BEGIN execute | [first execute](evidence/2026-09-30/n95-stream-echo-recovered.txt) |
| Execute-smoke: three DSP instructions return RMS_EOK, without STRM | RUN=0/status=0; delete timeout −33; phone remained accessible | [smoke](evidence/2026-09-30/n95-stream-execute-smoke.txt) |
| `env->moreEnv` + NODE_wait: create/delete | create=0, 7415 µs; delete=0; free task=0; FINAL=0 | [context create](evidence/2026-09-30/n95-stream-context-create.txt) |
| Same node, first packet, reps=0 | RUN=0/status=0; put/get status −2; 18585 µs; journal cuts off at BEGIN delete | [context first packet](evidence/2026-09-30/n95-stream-context-echo-recovered.txt) |

Measurement of the first packet above **is not** latency of successful streaming exchange.
Later successful exchange is given below. Simultaneous useful work of two
processors and time gain not yet proven.
Context changes and NODE_wait introduced together; single run does not establish which of
them resolved early failure. Stock base load after prior reboot
does not prove that overclock was the cause of first crash.

Smoke DSP SHA-256: `9BB4672A3FC0AB8FC40D85ACC264B39C189CE7EE115B4F652E46A38E1C3F0287`.
Context DSP: `BFF843C2BA3FEA82A643A2654D8DAF5E7FBEFCC0134D5CFB8119CB70F0A157BE`.
Host context build: `224D206F609D427B04C01B02FA169B7D8CE790862C05B36C18A079C25A699E3E`.
Build journals — `out/stream-{dsp,arm}-*-build.log`; rebuild alters artifacts.


### Host connection and the first 8 packets

PDD `8019FF5C` creates a host stream only when the props field **+24 = 0**.
Function `8019FB58` for this mode creates internal connection kind 2.
Initial DCD value 1 denotes device connection and does not create the required
host stream objects. In v6 the attr[6] field is corrected to 0 for both directions.
A separate create/delete with these props yielded FINAL=0:
[create v6](evidence/2026-09-30/n95-stream-host-connect-create-v6.txt).

In [serial reps=0 v6](evidence/2026-09-30/n95-stream-host-echo-v6.txt) a single
create (7446 µs) and RUN processed 8 packets of 256 C55x words. All put/get
statuses 0, errors=0; sequence numbers, lengths, and all 240 words of transformation
matched the ARM baseline. CRC of 64 KiB ARM work each time `CD837CD0`.
Reps=0 does not verify non-zero Q15 computation.

Frames 1–7: wall 17486–18127 µs; frame 8: 345275 µs;
STREAM PASS total=468868 µs. This wall includes sequential CRC, hence it
**is not** a measurement of transmission latency. State before delete=3; delete/status=−2,
FINAL/EXIT=−2. The phone remained accessible after this attempt. DSP of this run:
SHA-256 `45F877E2A18B392DF8E9EBA2DCE2947B148FD6B9E9AEE408DB3012CA6FD79873`.

Next DSP variant moved idle before reclaim of the last output.
[Transport journal](evidence/2026-09-30/n95-stream-final-idle-transport.txt)
cuts off with PS timeout after START. The phone journal has not yet been read;
fact of automatic reboot and exact failure point are not established.

### Stock RMS lifecycle: static evidence and v7

Channel 6 control passes through LDD `801B5118` to PDD slot +92
(`801A25C4`). For running state=2 with node+440=0 `801A2374` sends `{RMS_EXIT=80000000,
arg1=nodeEnv}`; PDD `8019B1AC` receives RMS_EXITACK=40000000 and calls
`801A2220`, which launches delete phase. This is already existing control 6 path.
The node+440 field is copied from processor+64 (`801A0344`, getter `8019F28C`),
and processor+64 — from configuration +588 (`8019EE68`). With non-zero field
another path `801A3DF4` is called; value and full contract of this
variant are still being refined. Mere fact of control 6 does not prove RMS_EXIT delivery.

DSP/BIOS task wrapper `24E6F0` calls execute with nodeEnv, then forms
`{40000000, returned_status, 0}` and calls NODE_putMsg with destination=NULL
and timeout=FOREVER. Thus, stock wrapper already sends EXITACK after
execute return. Manual ACK addition requires separate justification.

State=3 cannot be counted as successful completion: PDD `801A2D2C`
sets it, in particular, on processor failure (`8019DAD8`). V6 return after
in-band stop bypassed waiting for RMS_EXIT; causal connection with specific
crash still requires hardware confirmation.

V7 re-issues input after each frame, including the last one,
waits for RMS_EXIT in NODE_wait/getMsg, then idle/reclaim outstanding buffers.
Host waits for control 6 and frees host task only after success. Native free
is not called if transfer status remained pending. Packet contains protocol
version 7, host checks it and last marker. Added separate ARM CRC,
issue, wait, and observed completion time; parallel completion time
includes ARM work and is not exact moment of DSP completion.

V7 ARM/DSP built and partially verified on devices. E90 minimal
ordinary execute without host frames confirmed RUN=0/status=0, but control 6
left deleteStatus pending and gave FINAL/EXIT=−33. N95 separate RMS-only
execute has the same result; details below. Serial/parallel
remain pending verification of clean completion.

### Recovered N95 and RMS-only isolation

Two full scans of 192.168.3.1–254 on TCP 2323 initially found only E90.
The user reported that N95 was on a different subnet. After correction,
N95 at `.22` answered INFO 320×240. Prior to new c55stream runs, preserved
old EXE/hash, DLL, and [idle-first journal](evidence/2026-09-30/n95-stream-idle-first-recovered.txt).
This v6 journal has 7 valid frames, last entry is frame=7;
frame=8, delete, and FINAL are absent. This is a separate attempt, it does not replace
previous evidence of 8 frames with delete −2. Read DLL is 3644 B,
SHA-256 `EC11FC17EB22B8B9539BCFB8C109A7F4A362D11C438714A0383AD351764911BF`.

NODE_getMsg `24D790` returns BOOL=1 after copying three longs;
NODE_wait, NODE_getMsg, RMS_executeNode, and task wrapper are byte-identical
in common-code N95/E90, although entire section differs in 116 bytes.
[Comparison evidence](evidence/2026-09-30/n95-e90-dsp-rms-code-comparison.json)
obtained from 64 DOFF packets with 12-byte headers.

Variant `build_stream_node.cmd rms` repeats TI PING approach: execute
only waits for RMS_EXIT via NODE_getMsg; limit is 100×100 ms. Create/delete
still create and release ordinary stream objects, but execute does not
call issue/wait/idle/reclaim. Host v7, SHA-1 loader hash, and DLL 2700 B
read back and matched byte-for-byte before test.

- [Create/delete](evidence/2026-09-30/n95-stream-create-v7-rms-wait.txt):
  create=8361 µs, delete/free task=0, EXIT/FINAL=0.
- [Execute](evidence/2026-09-30/n95-stream-execute-v7-rms-wait.txt):
  RUN=0/status=0, state=2; delete=−33/status=pending, FINAL/EXIT=−33.
  [Transport](evidence/2026-09-30/n95-stream-execute-v7-rms-wait-transport.txt)
  confirms N95 accessibility after host process completion.
- [Read-only clock](evidence/2026-09-30/n95-clock-before-v7-rms-wait.txt):
  stock m86, DSP divider 3, firmware math 220160 kHz;
  HAL ARM ECPUSpeed=206438 kHz at probe moment. This is not an overlap measurement.
- [Original ocprobe.log](evidence/2026-09-30/n95-restored-original-ocprobe.json)
  1259 B restored and verified byte-for-byte. After isolation, regular
  v7 DLL 3668 B with SHA-256
  `5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9`
  returned to phone; its execute on N95 has not yet run.

RMS-only failure does not depend on STRM operations in its execute. It does not
yet determine whether exit request, execute return, or ACK was lost;
next contract must distinguish these cases.

Messages remain a separate candidate: LDD task20 `801B44F0`
reads 8-byte pair `{status*, record*}`. PDD `801A1D58` reads **24 raw
bytes** of record, in which header/max occupy 8 bytes and then cmd/arg1/arg2.
Get-info task2 copies 112 bytes; nodeEnv — data offset 64
(`801A11F0`). These contracts established statically, not verified by a new
hardware messaging test. SDK TBuf8<12> (20 B) and TBuf8<104> (112 B)
must be distinguished from explicit size of kernel raw copy.

### V8: get-info on N95 and precise messaging ABI

[Get-info v8](evidence/2026-09-30/n95-stream-info-v8-raw-record.txt)
executed **without RUN** on normal DSP v7: create=5859 µs, task2 rc=0,
header/max `30000068/104`, nodeEnv `000077e0`; delete/free task=0,
EXIT/FINAL=0. [Transport](evidence/2026-09-30/n95-stream-info-v8-raw-record-transport.txt)
ends with successful INFO. This is a check of record and nodeEnv, not execute.
In this first journal, payload+52 field was named `timeout=3`;
static proof establishes only PDD node+112. Label corrected to
`property112` in subsequent build; time units for this field not proven.

Static route: PDD put `801AF3A0` writes queue+16 into destination
frame; setter `801AF45C` receives returned nodeEnv after create ACK
(`801A27F4..801A2800`). PDD shared-record writer `8019AF44..8019AFAC`
forms 16-byte `{cmd,arg1,arg2,destination}`. MSG-toDSP SWI `24D498`
enqueues message to destination and calls MSG_notify `24E758`.
Native NODE_putMsg, MSG-toDSP SWI, and MSG_notify, as well as required LDD
put/get/info/dispatcher fragments of N95/E90 are byte-identical:
[addresses and SHA-256](evidence/2026-09-30/n95-e90-message-routing-contract.json).
This is code proof of both firmwares; get-info/messages on E90 v8 have not yet run.

PDD queued receive `801AF284` and pending receive `8019B048` write
**24 B**. Record v8 has explicit padding; it is not interpreted. Task20/21
receive 8-B pair `{TRequestStatus*,record*}`. Dispatcher has commands
0–21, separate cancel22/23 do not exist; after timeout new receive is not
sent on top of pending. Statuses and records live until channel close;
timeout and late completion are not counted as clean success.

New messages variant isolates execute from
STRM. Hello `{600,00080001,nodeEnv}` confirms execute entry;
host `{601,12345678,a5c55a5a}` should yield echo `{602,...}`; message
`{603,80000000,echo_count}` shows receipt of RMS_EXIT before return.
Stock wrapper forms EXITACK itself. DSP receive limited to 150×100 ms,
host preserves first error and allows additional 15 s for pending delete;
runner has deadline not less than 60 s. Only echo together with receipt,
delete/free, and EXIT/FINAL=0 opens the next streaming probe.

After eight-hour pause, INFO on both IPs got connect timeout.
PC remained `192.168.3.11`, gateway `.1` answered; reason for phones
unavailability not established. After successful get-info, new RUN and delivery
of messages DLL not yet performed. Preparatory `prepare_stream.py`
makes backup, read-only clock probe, restores ocprobe.log, and verifies
EXE/hash/DLL by readback.

**Further availability 10:59 UTC:** prepare on N95 succeeded:
[metadata/readback](evidence/2026-09-30/n95-messages-v8-preparation.json),
[clock](evidence/2026-09-30/n95-clock-before-messages-v8.txt).
Stock m86/div3, firmware math 220160 kHz, HAL ARM 206438 kHz;
original ocprobe.log 1259 B returned with the same SHA-256 1ABC8073... .
Host 18668 B 0900DFE3... and messages DLL 2924 B 5A06007E... delivered
and read back. [Create/info/delete](evidence/2026-09-30/n95-stream-info-v8-messages-create.txt)
with this DLL: create=6347 µs, header/max 30000068/104, nodeEnv=000077e0;
delete/free task=0, EXIT/FINAL=0, new label property112=3.

**Message RUN:** START accepted at 11:00:20 UTC, PS multiple times
showed live process. Next PS got response timeout;
new connect/GET also timeout before command. Phone journal not yet
read, hence hello/echo/RMS_EXIT receipt, FINAL/EXIT, and exact
failure point unknown. Phone reboot not confirmed.
Evidence — [transport](evidence/2026-09-30/n95-stream-messages-v8-routing-transport.txt)
and [state](evidence/2026-09-30/device-status-after-v8-message-run.json).
E90 fresh INFO successful, PS c55stream*=0; new DSP RUN on it
was not performed. Next — read N95 journal and DLL before new START,
after quiescent PS return normal DLL from backup and verify GET.
Prepare verified on hardware; success messages not yet proven.


## E90: separate live ROM

MachineUid **20002496**, RA-6 `400.34.93 / 21-04-2009`. Read-only ocprobe
read ROM window `80000000..803FFFFF`; files identified by TRomEntry and
120-byte TRomImageHeader, not by guessing addresses.

| Module | Code address | SHA-256 |
|---|---|---|
| bridgeapi.dll | `803F9EC8` | `003D47B0778D1E6687BDEEB456E4E02BFE64D8763E4178CFAECFDDDBA994C6FE2` |
| ehwa.ldd | `803F8648` | `07731D17142D8D45EF29229F00D7856135CE59D2F51935DB1DF96AD742E9A70D` |
| ehwaomap.pdd | `803DD788` | `D2818CC222051D3C1B2C61ACB17E14D72B964AB173EDC04A493C31A4CC6CFAB4` |

39 bridgeapi ordinals have offset `FF99CA70` from N95; live inspect confirmed
all 39 and FINAL=0: [E90 inspect](evidence/2026-09-30/e90-stream-inspect-recovered.txt).
DCD parse — `803FBB45`, lock/unlock — `803FBA11/803FBA07`.
General offset **does not apply to PDD**: function prologues were matched
separately; RUN `803E5A44`, input `803E60D0`, output `803E5ED0`.
Three required LDD fragments are byte-identical, in corresponding PDD functions
BL addresses differ. This is static comparison, not result of E90 DSP test.

Its `baseimage.dof` (155708 B) has SHA-256
`180F95602B078111F617F459620C4AECD203ECB730E91803AEF9E591E5D22F35`;
phone's own `Z:\resource\plugins\baseimage.dof` is used.
First inspect failure occurred in daemon WAIT with process alive; recovered
journal had FINAL=0, user reported daemon crash. DSP driver was not
called then. Runner now waits for completion via PS and only then reads WAIT.

After SIS update and user assistance,
[inspect](evidence/2026-09-30/e90-stream-verify-v3.txt) confirmed host v3.
[Base](evidence/2026-09-30/e90-stream-base-v3.txt) and
[create/delete](evidence/2026-09-30/e90-stream-context-create-v3.txt)
ended in EXIT/FINAL=0; create=6774 µs, free task=0. This is preliminary
v3 stage prior to update, without RUN and without v6 host connection fix.

After manual installation of SIS revision 7 by the user,
[inspect](evidence/2026-09-30/e90-stream-v7-user-installed.txt) confirmed
host v7, UID 20002496, and all 39 exports. DSP DLL 3668 B written and
read back; bytes are identical to local v7 with SHA-256
`E039E983AA042EF1397368151E671FEB8D29BA0828A576139223367CF6FEF5C1`.

| E90 v7 mode | Result | Evidence |
|---|---|---|
| Base | load/close=0, EXIT/FINAL=0 | [base](evidence/2026-09-30/e90-stream-base-v7.txt) |
| Native buffers | two alloc/free of 4096 B, EXIT/FINAL=0 | [buffers](evidence/2026-09-30/e90-stream-buffers-v7.txt) |
| Create/delete | create=8697 µs, delete/free=0, EXIT/FINAL=0 | [create](evidence/2026-09-30/e90-stream-create-v7.txt) |
| Execute without host frames | RUN=0/status=0; delete pending/−33, EXIT/FINAL=−33 | [execute](evidence/2026-09-30/e90-stream-execute-v7-minimum.txt), [transport](evidence/2026-09-30/e90-stream-execute-v7-minimum-transport.txt) |

[Clock probe](evidence/2026-09-30/e90-clock-before-v7-min-execute.txt)
confirmed stock m86/div3, firmware math DSP 220160 kHz; original
ocprobe.log after probe returned and compared byte-for-byte. Phone answered
immediately after −33. Later connect had timeout; during RMS-only
preparation on E90 there was no PUT/START command. Next INFO again
successful, but uptime shorter than previous: between checks there is sign
of reboot, reason not established. Minimal journal and normal v7 DLL
read again, bytes unchanged. [Current state of both phones](evidence/2026-09-30/device-status-after-n95-subnet-recovery.json).

### Get-info E90: custom PDD getter and delivered v8

`tools/rev/compare_node_info.py` compared task2 raw copy (100 B), node-info
adapter (56 B), and constructor (44 B): LDD code is byte-identical. Adapter
calls PDD vtable slot20. On N95 this is table801B3DE8/getter801A11B8,
on E90 — table803F8424/getter803E57F8; vtable entries verified separately.
92-B getter differs only in ARM BL at +20, which goes to different import stubs.
Remaining 88 B are identical. In particular, node+44 is written into payload+64 via
N95 801A11F0/801A11F4 and E90 803E5830/803E5834. This confirms info
format without transferring bridgeapi general delta to PDD.
[JSON](evidence/2026-09-30/n95-e90-get-info-contract.json) contains all hashes,
vtable, call targets, and offsets. property112 value received no time units.

11:30 UTC `E:\c55stream-v8.sis` (11716 B,
SHA-256804B1533...) transferred to E90, readback equal. Prior to write, preserved EXE/hash/DLL/log;
versioned SIS path was previously absent. Old SIS and DSP DLL not replaced,
OPEN/SHOT/START did not occur in this step. [Delivery evidence](evidence/2026-09-30/e90-host-v8-sis-delivery.json).
Later GET of installed EXE gave v7 hash87CEA30C...; installation of v8
is awaited. Next test — inspect, stock clock guard, and create/info/delete
without RUN. This is not yet a hardware verification of v8 on E90.

N95 is still unavailable: recovery01/02 stopped at connect timeout before first
daemon command; full TCP2323 scan found only E90. Message RUN
journal and normal DSP restore remain pending. `recover_stream.py` preserves
journal/current DLL, reads fresh PS, and allows restore only after c55stream
completion and with known before/after hashes. Compile/help passed;
positive hardware execution of recovery has not yet occurred.

Later check of E90 revealed stock guard error in prepare: it required
restore-check100 for both devices, although E90 normally returns 1. First attempt
guard01 gave complete=false before DSP PUT and returned original ocprobe.log.
After separating UID/profile/restore-code, guard02 passed complete=true:
stock m86/div3, firmware math DSP220160 kHz, HAL ARM330000 kHz; normal
DLL E039E983... and ocprobe.log BE58F5EF... read back, bytes equal.
[Journal](evidence/2026-09-30/e90-clock-before-info-v8.txt),
[preparation](evidence/2026-09-30/e90-info-v8-preparation.json).

E90 recovery actually passed: previous minimum-execute journal preserved,
INFO/PS0, current DLL was already exact backup, PUT skipped, GET equal.
[Metadata](evidence/2026-09-30/e90-idempotent-dsp-recovery.json) and transport
confirm this case. This is not a result of v8 info/messages and not a check of
restoring modified N95 DLL. On N95 journal/normal restore still pending.


## Native buffers, DMM, notify and worker

Statically established: bridgeapi ord30 has form
`Alloc(processor, TDes8*, sizeBytes, unused=0, unused=0, mode)`.
Mode 0 calls `User::Alloc`, mode 1/2 require positive size,
multiple of 4096, and pass descriptor to `Ctl(0x0400000B, descriptor, size)`.
Production `balbuffers:80A42408` rounds size up to 4 KiB and uses mode 2;
ord29 frees corresponding descriptor and zeroes it.
[Separate N95 buffers test](evidence/2026-09-30/n95-stream-native-buffers-v4.txt)
confirmed two allocations of 4096 bytes and both free=0, FINAL=0. Precisely these
buffers were used in 8-packet v6 test. This is not isolated evidence that previous
−2 was caused by ordinary user buffer; connection fix has separate
static justification.

`dspmemmapper.dll` has 11 exports; internal records are 48 B per mapping.
Ord9 (`80A44743`) takes `{armAddress, byteSize, flags, slot}` and replace flag,
checks slot and non-zero size, saves DSP-address result of ord31.
Ord2 tears down mapping via ord34, ord6 after this tears down reservation via
ord28 (reservation created by ord27). Ord3/4 read saved addresses. Full contract of reservation,
DSP-address access, and cache ownership not yet verified on hardware.

`ebridgeutil` fn1 translates pages via LinearToPhysical; this reading
of addresses **is not evidence of pinning**. Fn2 performs cache clean/flush. Ring buffer
requires separate proof of page lifecycle, index publication order,
coherence, and completion. Node state notify analyzed below; separate
notify for arbitrary shared ring buffer not established.

Base image exports `TSK_create`/`TSK_delete`, `SEM_*`, `CLK_*`, `STRM_*`,
`NODE_wait/getMsg/putMsg`. Worker launched once from create is a separate
candidate, but it requires task ABI, custom stack, and return channel for
results. Non-presence of `SIO_*` in export table does not prove absence
of this capability inside BIOS. Hardware worker/DMM/ring prototype not yet run.

## Notify, one-time preparation and completion of F04 channel map

### Node state notify

**Statically established, not called on hardware:** task5 `08000005`, LDD
`801B4418`, reads 8 bytes `{TRequestStatus*, flags}`. Pointer is saved
in LDD node +36, flags — +40; PDD virtual slot +96 checks initial state.
Re-registration when status pointer exists is not permitted.

In `801B4384` LDD writes new state into +20. If state changed from
previous value **2** and notification is registered, it sets
completion=0 in +44 and queues DFC +48 via `801B5598`.
DFC `801B40C8` completes saved request via `801B5698`.
Task6 `08000006` cancels specifically this notification with status −3.
This is **different command** than lifecycle control 6 without `08000000` prefix.

PDD slot +96 (`801A2D50`) has separate checks state=11, flags bit0, and
message queue. Flags values and all cases of initial completion not
verified on phone. State notification does not prove existence of arbitrary
inter-processor doorbell and is not used for ring indices.

On DSP `NODE_wait` per TI `node.h` waits for STRM readiness or message;
stream mask and messagesReady are 16-bit `Uns`, timeout is milliseconds.
Wait with timeout>0 requires task context and has `SEM_pend` constraint.
For current node stream mask 1 indicates single input ready. This path
additionally confirmed by re-transmitting 8 packets; API for arbitrary
shared buffer does not follow from this.

### What is executed once

| Stage | Frequency in prototype | Evidence / limit |
|---|---|---|
| Firmware check, processor open, DCD bind, base load | Once per process | ARM code and base/create hardware journals |
| DCD parse, select, stream props, allocate host task | Once before create | ARM code and v6 journals |
| DSP create: context, STRM objects, DSP buffers, coefficients | Once per node | DSP code; 8 packets have one create |
| Native ARM buffers ord30 | Two allocations per process | Separate buffers test, both free=0 |
| RUN execute | Once per node | RUN=0 and 8 frames without repeated RUN |
| Host input/output requests, issue/reclaim, computation | For each slice | Hardware-confirmed transfer; reps=0 does not yet prove Q15 workload |
| RMS_EXIT → ACK → delete → free host task | Once at completion | Static stock path; after streaming RUN clean completion not yet proven |

Create uses status pointer: LDD `801B5014` passes it to PDD via
slot +12 (`801A1038`), return completion passes through DFC. This allows
ARM code to perform work **after DoControl returns and before Wait**. Part
of preparation/loading of code may execute inside DoControl; its
duration separately has not yet been measured. Current host immediately waits for create, hence
physical ARM/create overlap is not claimed. Create timer includes submission
and wait. For long-lived channel this cost is paid once.

### Evidence matrix for candidates

| Candidate | Contract / source | Current evidence | What remains to be verified |
|---|---|---|---|
| Host STRM, TASK execute | LDD task14/16, 28 B; PDD connection=0; TI strmcopy | 8×512 B in one create/RUN | Stock exit, Q15, component timing, serial/parallel |
| Native allocation and DMM | Ord30/29; dspmemmapper ord9, bridge ord31/34/27/28 | Alloc/free mode2 on N95; mapping analyzed statically | All mapping flags, DSP-address access, pinning, and cache ownership |
| Shared ring + notify | DMM and ebridgeutil fn1/2; node state notification task5 | Components exist; no shared ring test | Indices publication, barriers, coherence, data signal, and wraparound |
| TSK/SEM worker from create | Native TSK/SEM ABI, generic library2, created-state lifetime | On N95/E90 finite task and parked task: block in create, wake/join/delete in delete; data/address preserved | STRM in created state, stop/cleanup, Q15, and useful ARM overlap |
| Messages | Task20/21 pair8 B + raw record24 B; TI RMS_DSPMSG | N95 DSP get0/put1, queue→shared window; created pending get cancelled −3 on N95/E90 | ARM delivery, echo, RMS_EXIT/ACK, and bounded shutdown |

Order of experiments: complete strongest already functional STRM candidate;
then measure transfer and overlap; DMM/ring or custom messages needed
if measured cost of STRM does not suit specific application. Worker by
itself does not eliminate need for data channel. No negative conclusion about these
alternatives: their hardware contracts remain open.

F04 completed as **channel and evidence map** according to PLAN. This is not
completion of streaming prototype F05, E90 F06, or payback measurements F07.


## New hardware evidence: recovery, receive, and MSG stages (13:15–15:54 UTC)

Previous entries above describe the state at the time of the respective experiment.
N95 recovery and E90 v8/v14 installation have already been completed.

| Verification | Result and limit of evidence | Journal in evidence/2026-09-30 |
|---|---|---|
| N95 v8 recovery | Old journal read; hello −33, last entry BEGIN delete. Normal5B6BE15B… returned PUT/GET byte-for-byte | n95-messages-v8-recovery.json/.txt |
| N95 v9/v10 receive-created | Create/get-info, get pending before RUN; delete/free0 → get −3; EXIT/FINAL0 | n95-receive-created-v9.txt, n95-receive-created-v10.txt |
| N95 messages-bare | DCD zero streams, create/info/delete clean. RUN without STRM in any phase: hello/delete −33; phone remained accessible | n95-info-v9-bare-messages.txt, n95-messages-v9-bare.txt |
| N95 v11 markers | Three STRM output512 B; execute entry, NODE_getMsg(0)=0, NODE_putMsg(0)=1; delete/FINAL/EXIT−33 | n95-message-stages-v11.txt |
| N95 v12 windows | DSP toGPP count0, fromDSP window count1 after put; ARM get not yet posted; delete−33 | n95-message-windows-v12.txt |
| N95 v13 get after markers | After put empty0/count1 in fromDSP window; custom ARM get pending/−33, delete/FINAL/EXIT−33 | n95-message-windows-v13.txt |
| N95/E90 v14 patcher | Write105 into own RAM0, actual51/a7/3c/d2, EXIT/FINAL0; without DSP/PRCM/kernel patch | n95-patcher-own-ram-v14.txt, e90-patcher-own-ram-v14.txt |
| E90 v14 after reboot | EXE/hash equal to local build; inspect39 exports; fresh stock guard; info and receive-created EXIT/FINAL0, without RUN | e90-v14-installed-after-reboot.json, e90-v14-postreboot-preparation.json, e90-info-v14-postreboot.txt, e90-receive-created-v14.txt |

N95 v9–v14 had the same daemon startTick7928381 and increasing uptime.
After each bare/stages variant normal DSP5B6BE15B… restored GET-equal;
E90 normalE039E983… was not replaced by variants. This is verification of phone
file, not evidence of successful completion of previous DSP worker.

### Allocation and pending receive

Control4 LDD copies **32 bytes** (`801B4EE8`, E90 `803F9528`).
SDK `TBuf8<20>` occupies 28; v10 introduced explicit32 record with header30000014,
max20, five payload DWORDs, and padding. Last DWORD is not passed
to allocator. Over-read corrected, but not established as cause of MSG
failure. Compile-time assertions and successful build verify both sizes.

`tools/rev/compare_receive_cleanup.py` verified byte-equal ranges N95/E90:
node destructor, cancel saved get/put, free control7, and allocation copy.
[Static contract](evidence/2026-09-30/n95-e90-allocation-receive-contract.json).
In state1 delete completes, free calls LDD destructor, which completes
saved get status with value KErrCancel−3. N95 v9/v10 and E90 v14 confirmed
this on hardware. For state2 timeout delete this positive conclusion does not apply.

Runner now requires fresh successful preparation for receive and all RUN
modes and verifies current DSP before START. E90 info v8 was mistakenly
launched after rejected clock guard03: 8758 µs is genuine result of
create/info, but **not a measurement under confirmed frequencies**. New v14 info6652 µs
has its own successful guard; these single numbers are not assessment of performance between versions.

### DSP messenger and ARM receive window

TI primary header `msg.h` from userspace-dspbridge342b… specifies
WORKNEEDED=1, BUFFEREMPTY=2, ENABLE=4. Native SWI mailbox3 denotes
work+bufferempty; this **is not evidence of OEM enable gate**. NODE_enableMsg is absent
among exports; call to unknown address is not justified.

Readonly DSP snapshots v12/v13 showed:

- MSG_toGPP0012AC38: count0, notify2000, notifyHandle raw words0000/7AE6,
  maxMessages16. V12 erroneously printed handle via low-word-first Get32
  as 7AE60000; v13 preserves raw words. This v12 format is not an address.
- MSG_pfromDSPBuffer→0008FEF8: count0 before put and 1 after put.
- MSG_ptoDSPBuffer→0008FF7C: empty1/count0.
- Native NODE_put24DD5C copies three longs into frame and source=nodeEnv;
  MSG_notify24E758 posts fromDSP SWI. MSG_fromDSPFxn24C928 transfers
  records to shared window, sets empty0, and calls MSG_interruptGPP24EC70.

Combination of queue0/window count1 is evidence of DSP progress toward shared window.
V13 ARM task21 pending after three markers does not prove that ARM received
IRQ or found correct queue. Native wrapper24E6F0 already sends ACK;
manual ACK duplication without new contract is not needed.

Reproducible `tools/rev/compare_message_window.py` compared consumer744 B
N95/E90: differ only in nine relocated BLs. Reader24 B, DFC88 B,
configuration copy, and window setup are identical. E90 reader803F7664 found
by unique instructions and four actual BLs; general relocation
does not apply to it. [Contract and hashes](evidence/2026-09-30/n95-e90-message-window-consumer.json).

ARM PDD consumer `8019B0A8` takes window at context+224, message from +240,
reads four 32-bit fields via `801B3028`, and compares source with queue+16.
Reader performs ror16 if byte+64 of its embedded memory-interface
is non-zero. This is a different object than processor+64 from configuration+588. Match of ordinary
message: pending user-record in queue+40 or list of queued receive;
ACK40000000 passes separately. DFC `8019BA84` calls consumer after
mailbox service. Static code does not establish actual runtime flag,
IRQ/DFC execution, record source, or mapping. Next localization must
distinguish these conditions, rather than repeat v13 without new information.

### E90 patcher and reboot

E90 guard03 and separate old ocprobe level1 before reboot gave self-test−20;
original ocprobe.log restored. On-disk patcher C:/E: had identical hash,
but state of loaded resident driver was not measured. V14 SIS transferred
14:38 UTC, readback equal; user reported automatic reboot
and installation. In this session E90 DSP RUN was not called; reason for reboot unknown.

15:52–15:54 UTC installed host22408 B5F1C77CF… matched local v14.
Own-RAM patcher load/open/write0, readback51/a7/3c/d2. New clock probe
confirmed m86/div3, HAL ARM330000, firmware DSP math220160 kHz; all
logs restored. E90 restore-check1 — comparison of six live Usbc instructions;
old ocprobe signs it with generic DoControl, which for E90 is inaccurate.
Positive results after reboot do not establish reason for previous −20.

### V15: actual record and reader object refinement (16:14 UTC)

[Journal v15](evidence/2026-09-30/n95-message-records-v15.txt) contains snapshot
of eight words of first shared record. Count1/empty0 before and after reading:
`0000/0600/000F/0001/0000/77E0/0000/77E0`. Native long-word-first yields
cmd600, arg1F0001, arg2/source77E0 — expected fields of this probe.
ARM raw little-endian read yields cmd06000000/source77E00000; ror16 returns
correct values. Execute entry and put1 confirmed again;
ARM get/delete/FINAL/EXIT−33. Normal5B6BE15B… returned exact GET,
phone accessible/startTick constant. No new successful MSG delivery.

Refinement of v14 static conclusion: consumer passes reader pointer from
context+24. Setup8019BC8C/getter801AA98C sets it as object from
context+48 plus 164. Reader byte+64 belongs to this embedded memory-interface;
**cannot be identified with processor+64**, which takes configuration+588
and controls another exit path. Old association corrected in report and metadata.
Getter/setup byte-equal on E90, verified by compare_message_window.py.
Values of runtime reader flag, window mapping, and IRQ/DFC unknown. Valid
DSP record fields do not prove that ARM read them with required flag.


### TSK worker alternative: native ABI and brief probe

[TI C55x DSP/BIOS API guide, SPRU404Q](https://www.ti.com/lit/ug/spru404q/spru404q.pdf),
pp. 447,455–457, describes dynamic task with attributes, up to eight Args,
automatic TSK_exit after function return, and explicit TSK_delete.
Attributes account for separate C55 system stack. Higher priority can
launch new task immediately; with barrier priority−1 it waits for elevation.
Guide2012 is not self-contained proof of ABI of old Nokia firmware.

Local base DOFF exports TSK_create25A5B4, TSK_delete25B6FC,
TSK_ATTRS255814. Native code24B0FC–24B130 reads default attrs from C55
word12AC0A, copies **14 C55 words** (RPT13), specifies priority−1 and two
stack sizes, then calls TSK_create for wrapper24E6F0. This confirms
actual attrs extent and deferred start in this ROM.

New `extract_doff_section.py` verifies header/verification/table/packet
checksums and preserves instruction bytes without reordering. Common section
65266 B matched independent previous extraction completely. Synthetic COFF
allowed dis55 to disassemble `.bios`; local ROM/COFF/assembler are not published.
`compare_bios_tasks.py` confirmed TSK_stat/startup/argument setup byte-equal
on N95/E90; create/delete/exit differ only in seven verified
references to the same BIOS data symbols.

Native startup25CF3B–25CF4D passes first five arguments in **XAR0–4**.
Eight Args occupy 16 C55words; this is pointer ABI, not ABI `long` via AC.
In large model container pointer is 32 bits, address is 23 bits. TSK_Stat
has 22 C55words, mode at offset14; native exit sets task mode3.
Header `bios_task.h` verifies sizeof/offsetof under cl55 4.4.1, while assembler
probe confirmed entry in AC0, attrs/8 Arg on stack, and callback XAR0/XAR1.

`CREATE_WORKER_ONCE` verifies priority of current RMS task (<15), creates
finite task with priority15, stack1024/sysstack256, and eight pointer Args.
Callback performs only volatile stores of marker/cookie and returns. Create
returns success only after verifying marker, cookie00123456, and stat.mode3;
TSK_delete is called while still inside create. Callback owns no STRM,
locks, or external buffers; task code cannot remain active after
return of this phase. This is a check of task ABI and cleanup, not persistence.

| Phone / host | DLL | create, µs | delete / free / FINAL / EXIT | Official RUN |
|---|---|---:|---|---|
| N95 / v15 | 3172 B, 0709550C… | 10131 | 0 / 0 / 0 / 0 | None |
| E90 / v14 | Same DLL | 9368 | 0 / 0 / 0 / 0 | None |

Create timing includes ordinary STRM/MEM setup and task probe; this is not time
of empty create or packet processing cost. Fresh stock guard m86/div3
passed on both, original clocklogs restored, daemon startTick did not change.
After PS0 returned exact normal DLL N955B6BE15B…/E90E039E983… and GET-equal.
Evidence: [task contract](evidence/2026-09-30/n95-e90-bios-task-contract.json),
[artifact](evidence/2026-09-30/worker-once-artifacts.json),
[N95](evidence/2026-09-30/n95-worker-once.txt),
[E90](evidence/2026-09-30/e90-worker-once.txt),
[results](evidence/2026-09-30/worker-once-device-results.json).

Worker from create is considered as next channel: host holds node
in created state, worker exchanges STRM packets, explicit stop frame
terminates worker before control6/delete. This is architectural hypothesis, not ready
bypass of RMS lifecycle. Attributes/Args/termination confirmed by brief
probe, but lifetime of dynamic code/data between create/delete is still open.
Ordinary node has phase library types3/4/5. For subsequent worker probes
added generic library type2; its create/delete residency and parked task
already confirmed below. Single create and genuine serial/parallel/Q15 measurements
remain criteria for F05.

### Type 2 library and task after create

Verified 2026-09-30 22:19–22:45 UTC (2026-10-01 local time).
`compare_node_loader.py` compares two ROMs and both base DOFFs. Native
bridge fallback80A5E188/803FABF8 upon missing create library3/−6 repeats
lookup from library2. Caller80A5E742/803FB1B2 skips separate execute/delete
lists after this fallback. Both ranges byte-equal.

PDD sets phase_split according to lists+196/+200/+204, offset208. **Create code
remains loaded in CREATED**, even with split phases. RUN can
unload create; created-state delete preserves create and, for split,
loads delete separately. Final free unloads loaded libraries. This is
native Symbian contract; previous Linux analogy of immediate unload after
create cannot be transferred to these firmwares. Assumption of preserving
identical data instance does not follow from this static fact.

V1 resident probe contains initialized downloadable `.data` with stamp
1BADB002. Create verifies it, writes C55DC0DE, and stores program
address delete in MEM context. Delete verifies **both** conditions and always
releases ordinary resources. Generic0/2 and split0/3/4/5 have identical raw
`.text` bytes; registration differs.

Control split on N95: create0/7415us, delete−2, last entry BEGIN close;
connection lost. Recovery retrieved journal 2039 B 81DC64C0… and returned normal DLL
GET-equal. Before recovery uptime became lower, daemon was started afresh;
reboot reason not established. Negative joint check indicates change in
stamp **or** delete address; separate reasons not measured. This experiment did not
create TSK and did not call RUN.

In initial v1 positive probes delete could return 8000 on null context,
bypassing check. This loophole closed in **v2**: null env/context —
negative error. V1 positive journals preserved as preliminary results;
proof of assertions is new v2 runs with fresh preparation.

Generic library2 v2 passed on **both** phones: create/delete/free,
FINAL/EXIT0. In these runs data stamp and delete address preserved. Native
RMS24B225–24B238 passes return AC0 in reply24E684; PDD signed comparison
801A27A8/803E6DE8 reflects negative RMS return into host−2. Therefore accidental
positive return0x1234 from legacy probe does not refute our negative
gates 80008015. Split control actually returned −2; generic — 0.

Next `worker-parked` requires no initialized globals. Create
creates SEM(count0) and task(priority15, stack1024/sysstack256). Callback
writes pointer cookie00123456/stageC551 and blocks on SEM_pend30000 BIOS
ticks. Create verifies stat.mode2. Delete re-verifies blocked2,
wakes callback via SEM_post, verifies terminated3/stageC552/pend1,
then TSK_delete and SEM_delete. Only after this streams and
MEM context are released. Task does not seize STRM, locks, or external buffers.

| Variant | N95 host15 create, µs | E90 host14 create, µs | Delete/free/FINAL/EXIT |
|---|---:|---:|---|
| resident-check v2, library2, 3000 B D229D53F… | 9399 | 6744 | 0/0/0/0 on both |
| worker-parked v2, library2, 3592 B ED8C2862… | 7873 | 9277 | 0/0/0/0 on both |

Time includes ordinary STRM/MEM setup and probe; it is not packet latency.
These are checks of conditions in specific hashed DSP artifacts and native RMS mapping;
ARM did not log task fields independently. SEM ABI confirmed by emitted ASM
and native code; N95/E90 differ only in seven verified symbolic data
references. SEM timeout is measured in BIOS ticks, not automatically in milliseconds.

Fresh stock guards and restore of original ocprobe.log passed. Daemon startTick
did not change during each generic/parked preparation→recovery. No
active c55stream; normalN955B6BE15B…/E90E039E983… returned GET-equal.
Evidence: [native contract](evidence/2026-09-30/n95-e90-node-loader-sem-contract.json),
[generic results](evidence/2026-09-30/resident-generic-v2-device-results.json),
[parked artifact](evidence/2026-09-30/worker-parked-v2-artifacts.json),
[parked results](evidence/2026-09-30/worker-parked-v2-device-results.json),
[failed control](evidence/2026-09-30/resident-phase-device-result.json).

This parked probe proves task life after create return and its
termination via created-state delete for generic node. It has not yet
tested STRM, Q15, and useful ARM overlap; next series presented below.
Suitability of computations alongside audio tasks not established. Official
RUN with library2 did not occur.


## Streaming worker in CREATED — v16, both phones

Hardware series completed 2026-09-30 23:35 UTC. Host v16 24464 B
AB016003… on both; DSP worker DLL4792 B DE7DF926… with 22 imports,
verified in both base images. DOFF dump PASSED; emitted ASM confirms
pointer Arg, task entry AC0, NULL-env NODE_wait, and SEM timeout argument.
[Artifact v2](evidence/2026-09-30/worker-stream-v2-artifacts.json) contains
exact source/DCD/ASM/EXE hashes; v1 with different host preserved separately.

### Native contract and completion

`compare_created_stream.py` verifies byte-equal LDD submit, direction slots,
PDD input/output state gates, and 320 B native NODE_wait. PDD does not reject
CREATED1: excludes states9/13/4/10/11/0. LDD copies transfer record28 B;
status12/length16/arg20/index24, task14 input/task16 output.
NODE_wait(NULL,...) skips RMS message queue and writes messagesReady=0.
[Static contract](evidence/2026-09-30/n95-e90-created-stream-contract.json)
is not self-contained evidence of transmission — journals below are.

Create configures STRM/MEM and TSK priority15, stack2048/sysstack512;
verifies blocked2, input pending, pointer cookie00123456, and stageC561.
Node remains CREATED; control8/RUN is not called. Worker:

1. Awaits input via stream-only NODE_wait with finite timeout.
2. Verifies 256 words, magic, sequence, length, reps, and stop0/1.
3. Computes Q15 dot240 repeated reps and returns transformed payload,
   result, raw DSP ticks, reported counts/ms, and protocol16/cookie/priority.
4. Reclaim output is performed before new input. On last stop input
   is not posted repeatedly; STRM idle/reclaim returns pending ownership.
5. Callback posts completion SEM and returns via native TSK_exit.
   Delete waits up to 5000 **BIOS ticks**, requires terminated3, successful
   status, stop, and zero pending; only then deletes task/SEM, streams/context.
   Failed join does not release context of active task.

**LDD reported DELETED=5 differs from PDD internal deleted=4.**
Native getter LDD node+20 overrides PDD state in response. In first N95
one test packet and cleanup worked, but host required 4, hence FINAL/EXIT−20.
Host corrected to expected5; DSP was not changed, new one test passed.
[First journal](evidence/2026-09-30/n95-worker-stream-first-state-v16.txt)
preserved. Journal-only recovery without --restore-dsp did not restore DLL;
subsequent preparation correctly rejected this state before write/new test.
Separate restore returned exact normal, after which fresh preparation performed.
These negative results are not concealed and not included in successful measurements.

### Hardware correctness and wall time

On **each** phone passed one reps0, 8 packets reps0, 8 packets
reps1000, and three pairs of serial/parallel reps10000. In each run single create;
each packet512 B, output echo/result match, sequence/stop correct.
ARM CRC 64 KiB on each packet = cd837cd0. In parallel, CRC executes
between put and wait for get; in serial — after DSP completion.
Put/get statuses, errors, delete/free/native/close/FINAL/EXIT=0 in all
18 successful runs. No official RUN or transport KILL.

| Phone / pair | Serial, µs | Parallel, µs | Wall time change |
|---|---:|---:|---:|
| N95 / 1 | 406551 | 150968 | −62.866% |
| N95 / 2 | 399838 | 149868 | −62.518% |
| N95 / 3 | 249324 | 149593 | −40.001% |
| E90 / 1 | 266809 | 160305 | −39.918% |
| E90 / 2 | 263363 | 164517 | −37.532% |
| E90 / 3 | 257351 | 159542 | −38.006% |

Order: S1/P1, P2/S2, S3/P3. Table covers cycle of 8 packets with CRC,
transmission, and wait; excludes create, CRC baseline preparation,
logging, and cleanup. **These are observed changes, not isolated overlap gain.**
On N95 serial1 in frames4–8 simultaneously doubled ARM CRC (~18.4→36.8 ms),
DSP raw ticks (~239834→479669), and completion (~12.8→25.5 ms).
This is compatible with frequency mode change, but PRCM was not read for each
packet and reason not proven. E90 is significantly more consistent, conditions also require
control. Criterion of three N95 pairs under identical conditions not yet closed.

In multi reps0 observed completion512 B was N95 **335 µs** and E90
**396 µs**: issue/wait/echo/header checks, without CRC. This is not pure DMA latency
and not bandwidth measurement. FastCounter 32768 Hz gives step of about 30.5 µs.
For reps1000 completion — N951525–1556 µs, E901617–1647 µs, with correct
non-zero Q15 results. Successful one create — N958087/E907507 µs;
setup includes STRM/MEM/task, it does not need to be added to each packet.

CLK_countspms=164 does not agree with raw ticks and ARM wall time. Native
CLK_gethtime25D5C4 returns AC0 after reading timer ports7814/7815;
CLK_countspms25D649 reads double-word BIOS RAM01316A into AC0. Hence existing
32-bit return ABI is correct, but timer scale has not yet been calibrated.
From raw ticks in this report **DSP milliseconds are not computed**.

In each preparation passed stock clock guard and return of original log;
daemon startTick did not change over series. E90 SIS v16 installed via
observed installer; EXE GET matched ARM artifact. Recovery returned
normal N955B6BE15B…/E90E039E983… and original logs readback-equal; PS0.
[N95 results](evidence/2026-09-30/n95-worker-stream-v16-results.json),
[E90 results](evidence/2026-09-30/e90-worker-stream-v16-results.json),
[final checkpoint](evidence/2026-09-30/worker-stream-v16-checkpoint-device-status.json).
Raw phone journals preserved byte-for-byte with SHA-256; Git -text leaves CRLF.

Demonstrated working STRM/Q15 channel and useful simultaneous ARM work on both
phones in brief series. Prolonged operation, audio coexistence, tail latency,
larger packets, error-path lifecycle, and application integration not verified.


## V17: stock MPU reservation and timer calibration

2026-10-01 UTC: code and plan [PLAN_V17](../work/PLAN_V17.md), DSP4800 B
41D14CD4…/22 imports, host28456 BC8B08E8C… on both phones.
[Artifact v3](evidence/2026-10-01/worker-stream-v3-artifacts.json) preserves
exact hashes. Protocol17 replaced wire cookie with absolute DSP timestamp
offset14; pointer cookie remains mandatory create/delete gate.
Q15 workload240×reps and 512-byte packet layout of remaining fields unchanged.

### N95: stock mode control

`check_n95_performance.py` verifies dvfs_interface getter, request0,
SetPerformance, and destructor. In native SetPerformance80148460 only a2
is compared with 50; >50 adds reservation, <=50 removes. Resource66 is fixed,
this API does not accept arbitrary frequency. Getter control1 divides MPU clock
by 3300000 and returns integer percent. Destructor deletes residual
reservation of client. Four live fingerprints verified before API;
no PRCM writes or ROM-shadow patches in host.
[Native contract](evidence/2026-10-01/n95-stock-performance-contract.json).

V17 calls request0/a2=100 before processor setup and release0 after close;
request storage persistent, bounded5000 ms wait. In all N95 runs
reserve/release/status0, MPU100% before/after each packet. After release
possible 50 or 100 via stock policy/other clients; this is not requirement
to immediately return specific frequency. E90 skips this branch: N95 API and
addresses not used there. All DSP/bus clock domains not sampled by this.

| Phone / pair v17 | Serial, µs | Parallel, µs | Wall time change |
|---|---:|---:|---:|
| N95 / 1 | 251154 | 148953 | −40.693% |
| N95 / 2 | 250148 | 151211 | −39.551% |
| N95 / 3 | 249994 | 150205 | −39.917% |
| E90 / 1 | 259791 | 155729 | −40.056% |
| E90 / 2 | 258508 | 157467 | −39.086% |
| E90 / 3 | 263087 | 159878 | −39.230% |

Order S1/P1,P2/S2,S3/P3, single create and 8 packets in each run,
reps10000, useful ARM CRC64KiB/frame. Scope total_us the same as in v16:
without create/CRC baseline/logging/cleanup. N95 raw dot ticks239834–239854
almost identical, doubled intervals absent in this series. This is stronger
evidence of useful overlap than mixed frequency conditions of v16. Percentages apply
to this synthetic workload; application speedup not measured.

### DSP timer: short intervals and long pause

`worker-calibrate` processes 8 correct echo packets without CRC, with pauses
of 100/200/400/800/100/200/400 ms. DSP t1 recorded before reply;
host records FastCounter before submit and after completion. For two stamps
time delta lies between begin2−done1 and done2−begin1; bounds widened by
one counter tick error. Verifier independently recalculates all bounds
from journals. On each phone three such runs with FINAL/EXIT0.

Under short 100–400 ms nominal 19.2 MHz falls within all measured bounds.
Their intersection N95 **19185149–19213529 Hz**, E90
**19182339–19218353 Hz**. These are bounds of this experiment and short-interval model,
not calibration of all conditions. CLK_countspms remains 164.

In all six 800-ms intervals DSP delta corresponds to only **501.06–501.36 ms**
at 19.2 MHz. ARM brackets — **828.19–875.89 ms**. Apparent average rate
on these intervals N95~11.6 MHz, E90~11.0–11.6 MHz. Correct packets and
cleanup passed; necessary conclusion — **timer cannot be considered
continuous wall clock during long idle**. Deficit appears on both
E90 and N95 with MPU100%, hence MPU DVFS alone does not explain it.
Stopping/gating of DSP or timer itself after ~500 ms is hypothesis; runtime
PRCM/idle-policy contract not yet measured. Do not discard these intervals
to obtain neat common calibration rate.

On both repeated one/multi reps0, Q15 reps1000, three pairs, and
three calibrations — **24 successful runs v17**. Completion512 B reps0
N95335/E90396 µs. Not a single RUN, KILL, or reboot in the series. E90 SIS16776 B
9C04181A… installed via observed installer, EXE GET-equal. Recovery
returned original DSP and clocklogs exact, PS0; final INFO/GET preserved.
[N95 v17](evidence/2026-10-01/n95-worker-stream-v17-results.json),
[E90 v17](evidence/2026-10-01/e90-worker-stream-v17-results.json),
[final checkpoint](evidence/2026-10-01/worker-stream-v17-checkpoint-device-status.json).
Report preserves raw ticks/bounds and does not convert them using reported164.

## Next experiment

1. Measure packet1760/2048/2304/4096 B, jitter, and buffer ownership boundaries.
   Compare these results with WSOLA/MDEC formats and browser media stages.
2. Analyze native timer/idle contract for ~500-ms pause and distinguish
   timer stop from clock domains change. For wall time comparisons ARM
   FastCounter remains; do not transfer short rate to long idle.
3. Verify error/timeout lifecycle prior to application integration and audio
   coexistence for audio candidates. Do not launch old failed RUNs.
4. Verify F05–F08 requirements against real evidence. MSG route remains
   open: v15 shared record is valid, runtime reader/routing/IRQ
   not established; existing working STRM is not evidence of MSG operation.

## V18: lengths and cost of packet echo — 2026-10-01

Static native contract on both ROMs: properties size+4 -> RMS size+0,
C55 words; ARM descriptor length — bytes. DCD unchanged. Host v18 and
worker protocol18 support identical input/output packet512–4096 B;
this is limit of prototype allocation4096, not maximum of native allocator.

On both phones verified 512/1568/1792/2048/2304/4096 B, 32 packets
per single create, 3 ordered runs per size. One512/1792/4096 and Q15×8 on 4096
also passed. On each 22 runs/587 correct packets, clean FINAL/EXIT0,
no official RUN/KILL/reboot. Original DSP returned GET-equal.

Worker-transfer mode does not count ARM CRC/Q15 repetitions. ARM issue-to-
observed-completion for 1792 B: N95 median518/max549us, E90 median640/
max7812us. Max is not removed; this does not prove audio deadline hop≈4.99ms.
Actual WSOLA, short output, and MDEC not measured. Timer conclusions of v17
are not superseded by recalculation with counts/ms164.

Full method, table, and evidence: [PACKET_SIZES.md](PACKET_SIZES.md).
Sizes — from 32-byte header: WSOLA input1792, MDEC input1568/output544
or 800. Do not substitute them with a single symmetric packet2048/2304.

## Current application kernel and audit: v19/v20 — 2026-10-01

WSOLA220/441 exact coarse/refine ported to resident STRM worker: input896/
output24 C55 words (1792/48 B), independent properties, unchanged DCD.
V20 scalar ARMv6 baseline matches current PS1 compiler options and codegen.
On each 9 runs/195 correct packets, 97 searches; three paired runs of 32 each.
ARM median999.45us, packing+DSP+completion median640.87/732.42us.
One create/no RUN, valid stop/join/DELETED5/free/native close/FINAL/EXIT0;
originals/clock logs returned GET-equal. Method/raw journals/results — WSOLA.md.

Native copy path coherence/ownership validated for these packets; shared
ring/DMM cache ownership does not follow from this. Error/timeout/live-task unload
not verified and require native audit prior to integration; audio/long-run
stability and application gain unknown. Native164/long idle timer not conversion.
Scope/criteria audit: ../work/FINAL_AUDIT.md.