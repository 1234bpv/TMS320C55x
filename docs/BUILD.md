# Building on current PC and after migration

Update 02.10 after SSD return: root is again D:\VsCodeProjects\SymbianProjects;
SDK/toolchain are found nearby, TI CGT 4.4.1 — on C:. ARM host 28 builds,
local artifacts 37 are verified; on phones host 20 was restored after tests.
Python 3.12 is available via `C:\Program Files\LibreOffice\program\python.exe`.
Standard `python/python3/py` are absent in PATH. Harness should be run via
run_bounded with the full path of this Python. For scripts with subprocess
sys.executable, take into account that LibreOffice returns the python-core
directory; check_d0_checkpoint.py already handles it or accepts --python.
Hardware results and recovery — [WORKER_MESSAGES](WORKER_MESSAGES_2026-10-02.md).

For assignment D0–D2: host 25 is built by build.cmd, DSP candidates —
build_stream_node.cmd run-stop / run-message-diag / run-exit-diag; package —
build_stream_sis.ps1 -Revision31 -OutputName c55stream-exit-diag-v25.
DOFF/imports/ASM verification and immutable archive — record_d0_artifacts.py.
Four experimental RUNs yielded failed teardown, D0 0/3. The user permitted
new attempts with a separate hypothesis; next one — own-node RMS_EXIT/idle
snapshots during pending delete. ROM STRMCOPY control has already been
completed. Details and recovery procedure — [LIFECYCLE_DMM](LIFECYCLE_DMM_2026-10-01.md).

Package for restoring original EXE without rebuilding host:

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'pwsh -NoProfile -File tools/build_stream_sis.ps1 -Revision 29 -BinaryPath work/evidence/e90/d0-20261001/original-3.bin -OutputName c55stream-restore-v20-r29' -TimeoutSec 60 -Log out/d0-restore-v20-r29-sis.log
```

Revision 29 supersedes prepared package 28; payload remains exact
original host 20. Old restore 22/25 are preserved as historical artifacts.
The installer creates sys/hash; verify both files after recovery.

`tools/env.cmd` determines neighboring SDKs, toolchain, and daemon from the project directory. Perl must be 5.20. TI CGT is searched via `DSP_CGT`, PATH, and installation `Texas Instruments/C5500 Code Generation Tools 4.4.1` on available drives; `DSP_DOFFBUILD` can be overridden.

Run from project root in PowerShell 7:

```powershell
pwsh -NoProfile -File tools/check_state.ps1
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/arm-build-desktop.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_dsp_node.cmd 0 1' -TimeoutSec 120 -Log out/dsp-build-desktop.log
pwsh -NoProfile -File tools/check_state.ps1 -RequireArtifacts
```

ARM artifact is copied to `out/arm/dsptest.exe`, DSP node — to `out/dsp/bench.dll55l`. Before ARM build, previous target EXE is deleted, so absence of a new file is an error. Absence of `dllcreate` also results in an error, not in apparent success of a partial DSP build.

For the old SDK the project is built via junction `<SDK drive>:/symbuild/c55x`. Script `build_alias.ps1` verifies the location, link type, and its target before deletion. A real directory or a link to another project is not deleted.

`tools/sweep.ps1` requires explicit `-Ip`; legacy `dsptest` supports only N95
and rejects `-Device e90`. The series writes node and ARM host to the phone;
save replaced files before it. `strict_net.py` is used with INFO check,
without LAN fallback. EXEC has its own limit `RunTimeoutSec`, socket — another
5 seconds; non-zero process exit terminates the series after retrieving journal.

## Streaming prototype c55stream

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/stream-arm-build.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_stream_node.cmd' -TimeoutSec 120 -Log out/stream-dsp-build.log
pwsh -NoProfile -File tools/check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

Artifacts: `out/arm/c55stream.exe`, `out/dsp/c55stream.dll55l`;
`stream.x55` and `stream_node.asm` remain in ignored `out/dsp`.
Current host is **v18**, the runner expects v18 by default.
V17 is installed on both phones; E90 uses EXE in C:\sys\bin.
Host checks
MachineUid, all 39 live exports, and parser start prior to DSP driver calls.
Other firmware is rejected. Historical host can be explicitly selected via
`--host-version`; new mode requires its own minimum version.

### Dedicated DSP variants

| build_stream_node.cmd argument | Purpose | Separate DLL |
|---|---|---|
| Without argument | Normal stream, single create, multiple chunks | c55stream.dll55l |
| smoke | Execute immediately returns 8000, without STRM | c55stream-smoke.dll55l |
| rms | Execute awaits RMS_EXIT, without STRM in execute | c55stream-rms.dll55l |
| messages | Hello/echo/RMS_EXIT, normal create/delete | c55stream-messages.dll55l |
| messages-bare | Same messages, zero STRM in DCD/create/delete | c55stream-messages-bare.dll55l |
| message-stages | Three STRM markers and readonly shared record around NODE get/put | c55stream-message-stages.dll55l |
| worker-once | Short TSK task, stat/Arg check and TSK_delete inside create | c55stream-worker-once.dll55l |
| resident-check | Type 2 library, check of data stamp and delete address between create/delete | c55stream-resident-check.dll55l |
| resident-phase | Historical control with types 3/4/5; delete −2, close abort on N95 | c55stream-resident-phase.dll55l |
| worker-parked | Type 2, TSK awaits SEM after create; delete wakes, checks and deletes task/SEM | c55stream-worker-parked.dll55l |
| worker-stream | Type 2, TSK handles STRM in CREATED; explicit stop, join, and cleanup | c55stream-worker-stream.dll55l |

**Each variant also overwrites the main DLL in out/dsp.** Build normal
node after it. A separate assembler of each variant is preserved.
Bare did not eliminate message timeout. V11–v13 markers confirmed execute,
get=0, put=1 and DSP → shared window, but ARM get and delete gave −33.
Do not repeat these unsuccessful RUNs without new proof or modified contract.

`worker-once` is verified by `info` mode on existing host v15/N95 and
v14/E90, with explicitly supplied fresh `--preparation` for this DLL.
In this variant **do not call execute/serial/parallel**: task is already
completed and deleted before create returns. Resident worker is a separate
variant `worker-stream`, described below.
On both phones create/delete/free/EXIT 0 passed; evidence —
[worker-once-device-results.json](evidence/2026-09-30/worker-once-device-results.json).

`resident-check` and `worker-parked` also use **only `info`**
with fresh preparation. Type 2 is supported by native fallback 3→2; generic
list does not create separate execute/delete libraries. On both phones
resident data/address checks and parked-task checks passed with
delete/free/EXIT/FINAL 0. `worker-parked` has finite SEM timeout **30000
BIOS ticks**, not 30000 ms; priority 15 performs only stores/wait/return.
It does not handle STRM. After test, restore exact backup via recovery.
`resident-phase` already gave a negative result; repeat without a new
contract is not needed. Historical v1 hashes are tied to preserved
artifacts. **V2** additionally returns negative error on null env/context,
so mandatory assertions cannot be bypassed. On both phones v2
passed repeated fresh-preparation runs; they are the evidence.

Static reconciliation of native loader, RMS return, and SEM ABI:

```powershell
python tools/rev/compare_node_loader.py --e90-rom work/evidence/e90/rom --e90-base work/evidence/e90/baseimage.dof
```

Vtable is taken from separate constructor literal of each firmware; code
address difference was not applied to storage vtable. JSON contains hashes,
offsets, and verified symbolic BIOS data references; ROM bytes are not published.

### Preparation and launch conditions

`prepare_stream.py` saves previous phone files, checks expected
SHA-256 of current DSP, performs read-only stock clock probe, restores
original `ocprobe.log`, and verifies EXE/hash/DLL by reading back.
On N95 `--host` updates EXE and SHA-1 file; on E90 host is installed via SIS.
Prepare does not start c55stream or DSP RUN. Clock probe itself temporarily
uses patcher to read registers, without PRCM writes.

Modes `receive-created`, `message-stages`, `messages`, `execute`,
`serial`, `parallel`, `worker-one`, `worker-serial`, `worker-parallel`
**require `--preparation`**. Before connecting, the runner
verifies success, device/IP, stock guard, journal restore, time not older
than 10 minutes, and preserved DSP/hash. After connecting, it checks uptime
and current DSP bytes. Preparation failure stops launch before START.
Rebooting the phone requires fresh preparation.

Example of clean verification on N95 without RUN; DSP is exact normal backup
of this phone, and expected hash should be taken from current GET:

```powershell
python tools/prepare_stream.py --ip 192.168.3.22 --device n95 --tag prepare_unique --host out/arm/c55stream.exe --dsp work/evidence/n95/stream-v8-messages-prepare-01-before.dll55l --expect-dsp-sha256 5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
python tools/run_stream.py --ip 192.168.3.22 --device n95 --mode info --preparation work/evidence/n95/prepare_unique-preparation.json --tag info_unique
if ($LASTEXITCODE -ne 0) { throw 'Info failed' }
python tools/run_stream.py --ip 192.168.3.22 --device n95 --mode receive-created --preparation work/evidence/n95/prepare_unique-preparation.json --tag receive_unique
```

`info` — create/get-info/delete. `receive-created` additionally places get
into pending **before RUN**, then checks delete/free and cancellation −3.
N95 v9/v10 and E90 v14 passed this mode; it does not prove receipt of a
message from executing DSP. Raw allocation now has explicit 32 bytes
according to LDD of both firmwares; SDK `TBuf8<20>` has 28 bytes.

For a new justified RUN, prepare corresponding separate DLL and pass
successful preparation JSON to the runner. `messages` requires `--deadline 60`
or more. Start `serial/parallel --reps 0` and measurement series after
clean hello/echo and delete/free, EXIT/FINAL=0. Such a result is not yet available.

The runner saves previous journal prior to START and launches inspect before
the mode. Each tag is unique; evidence is not overwritten. PS monitors
the process, WAIT is called after its completion. Deadline 5–120 seconds,
reps 0–20000. Pending, timeout, non-zero EXIT/FINAL are not counted as
success even with STREAM PASS present. Journals — `work/evidence/<device>`.

### Streaming worker without RUN (v18)

```powershell
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build_stream_node.cmd worker-stream' -TimeoutSec 120 -Log out/worker_dsp_unique.log
pwsh -NoProfile -File tools/run_bounded.ps1 -Command 'call tools\build.cmd' -TimeoutSec 180 -Log out/worker_arm_unique.log
pwsh -NoProfile -File tools/build_stream_sis.ps1 -Revision 18
```

DLL has generic registration library 2. Use only `worker-one`,
`worker-serial`, `worker-parallel`, `worker-calibrate`, `worker-transfer`;
**stock execute/RUN is forbidden**. Worker-one processes 1 packet, other modes
by default — 8. V18 frame modes accept `--packet-bytes` (even
512–4096 B, including 32-B header) and `--frames` (1–4096, one only 1).
Calibrate remains 8×512 B. Reps 0 verifies STRM/echo,
reps 1000–10000 — correct Q15 dot with useful ARM CRC 64 KiB per chunk.
Priority 15 / stack 2048 / sysstack 512; usability alongside audio is not yet measured.
Join awaits SEM up to 5000 BIOS ticks, not automatically 5000 ms. Task is deleted
only after terminated 3 and return of pending buffers.

Starting with v17, host on N95 checks four live fingerprints dvfs_interface, routinely
reserves MPU mode request 0 / a2=100, and releases it a2=0 before FINAL.
Frame before/after must show 100%; all DSP/bus clocks are not measured by this.
No PRCM writes or ROM patches. E90 skips this N95 branch.
Protocol 18, like 17, at offset 14 returns absolute DSP timestamp instead of wire
cookie; pointer cookie remains mandatory DSP create/delete gate.
`worker-calibrate` transfers 8 echo packets without CRC with pauses 100/200/400/800 ms,
records ARM FastCounter brackets and bounds timer Hz. At 800 ms count
lags behind wall time on both phones; do not treat 19.2 MHz as
continuous wall clock. Countspms 164 is not a usable calibration factor.

Example for N95 after verifying actual address and exact normal hash:

```powershell
python tools/prepare_stream.py --ip 192.168.3.22 --device n95 --tag worker_prepare_unique --host out/arm/c55stream.exe --dsp out/dsp/c55stream-worker-stream.dll55l --expect-dsp-sha256 5B6BE15B20E73D8D318FDF9C5E5050C16AA28994BC422C891C2B0132EA4AB9F9
if ($LASTEXITCODE -ne 0) { throw 'Preparation failed' }
python tools/run_stream.py --ip 192.168.3.22 --device n95 --host-version 18 --mode worker-one --reps 0 --preparation work/evidence/n95/worker_prepare_unique-preparation.json --tag worker_one_unique
if ($LASTEXITCODE -ne 0) { throw 'Worker failed; recover journal before another test' }
python tools/recover_stream.py --ip 192.168.3.22 --device n95 --preparation work/evidence/n95/worker_prepare_unique-preparation.json --tag worker_recovery_unique --restore-dsp
```

On E90 install v18 SIS, do not pass `--host` to prepare; use
its normal hash E039E983… and `--exe 'C:\sys\bin\c55stream.exe'` in runner.
Full hashes/proofs are in device results. Tag is always new; preparation
is valid for 10 minutes. After variant, restore normal main DLL on PC.
DOFF/ASM/imports archival: `record_worker_stream.py` with new revision/report;
for v18 host-version/protocol18. `worker-transfer` requires reps 0 and does not compute
ARM CRC. Example after successful one, before recovery:

```powershell
python tools/run_stream.py --ip 192.168.3.22 --device n95 --host-version 18 --mode worker-transfer --packet-bytes 1792 --frames 32 --preparation work/evidence/n95/worker_prepare_unique-preparation.json --tag worker_transfer_unique
```

Full v18 series: `run_packet_series.py` with explicit IP/device/preparation/tag-prefix.
Verification and publication of specifically preserved v18 series:
`summarize_packet_sizes.py --device n95 --out docs/evidence/2026-10-01`.
It expects historical tags v18; for another series first agree on tags and new
result name. Old v16/v17 journals are verified by
`summarize_worker_stream.py --version 17` (or historical 16).
Published results
preserve raw journals and do not compute DSP milliseconds from CLK_countspms=164.

### Recovery after a diagnostic variant

`recover_stream.py` first retrieves journal and current DLL, checks INFO/PS.
**Without `--restore-dsp` this is merely reading the journal**: complete=true does not mean
DSP return. With this flag exact backup from preparation is restored;
mandatory check dsp_restored=true and final hash. Live c55stream
or unknown hash DLL forbids restore. START/WAIT/KILL are not called.
On N95 replacing messages/stages DLL back to normal was actually verified,
PUT and final GET are equal. E90 idempotent path was also verified.

```powershell
python tools/recover_stream.py --ip 192.168.3.22 --device n95 --preparation work/evidence/n95/prepare_unique-preparation.json --tag recovery_unique --restore-dsp
```

### E90: current v18 and previous installations

V18 installed via observed installer 1.00(18), host 29760 B
SHA-256571C5A6221C7E7815558A2C3AE5F6665D8D7DE0B82D676488869C7BAA260F14F.
GET and runtime match; 22 runs / 587 correct packets passed on each.
Evidence: `e90-host-v18-delivery.json` (moment of OPEN),
`e90-host-v18-installed.json`, `e90-packet-sizes-v18-results.json` and
`e90-packet-sizes-v18-device-status.json` in `docs/evidence/2026-10-01`.

V17 SIS 16776 B SHA-2569C04181AE3A79FF4B54C73F3E2446A671CF65D1274436F461DFD18C51F8F8460
installed via actual installer. EXE 28456 B on both phones
C8B08E8C0442F1E58CB07C40B5299E4FE6FD5DE873B3F3536014A72C1B284163;
GET and runtime inspect match. One/multi/Q15/3 calibration/3 pairs
passed on both. Delivery snapshot installed=false describes moment of OPEN;
final checkpoint proves installed EXE. Preserved previous results:

V16 installed via daemon from SIS 14604 B, SHA-256
6422DAE688C1C071843F5B26DB0707EE0CC6E2DC9EE57FAADBE6F9AC2C93BC5D.
Installed C:\sys\bin\c55stream.exe 24464 B on E90 and E:\sys\bin on N95:
AB016003DD44751FDDE19B57C37B9FD79E0D3A1BC40C0462EE4E9ADFAFFC43AB.
One/multi/Q15/3 pairs passed; raw delivery snapshot with installed=false
describes moment of OPEN before installation, while final checkpoint proves new EXE.
Below historical result v14 is preserved.

Writing to E90 sys/bin by daemon is not permitted in verified configuration;
use SIS. Package revision 14 delivered as `E:\c55stream-v14.sis`
and installed by the user. GET of installed EXE 22408 B matched local
SHA-256 `5F1C77CF7914312818F63D77AA950DED5B1208F454E986CF55C68EAD9E47274A`.
Package does not install DSP DLL. Next build of package on PC:

```powershell
pwsh -NoProfile -File tools/build_stream_sis.ps1 -Revision 18
python tools/run_stream.py --ip 192.168.3.21 --device e90 --exe 'C:\sys\bin\c55stream.exe' --host-version 18 --mode inspect --tag e90_inspect_unique
```

`patcher-check` v14 writes four bytes **only to its own RAM** via known
control 105 and reads them via volatile pointer. Kernel patch, PRCM and DSP
RUN are absent. On both phones `PATCHER OWN RAM PASS` and
EXIT/FINAL=0 were obtained. It is suitable for clarifying primitive failure before clock guard:

```powershell
python tools/run_stream.py --ip 192.168.3.21 --device e90 --exe 'C:\sys\bin\c55stream.exe' --host-version 18 --mode patcher-check --tag e90_patcher_unique
```

E90 before reboot twice failed patcher self-test with −20.
After reboot v14 own-RAM test and fresh stock guard passed:
m86/div3, HAL ARM330000, firmware math DSP220160 kHz. Concrete reason
of previous failure is not proven. After guard original ocprobe.log 1249 B
was restored byte-for-byte. Normal DSP E90 has separate hash E039E983…;
N95 backup cannot be used as its original restore.

Stock guard checks UID/profile and restore result separately: N95 100,
E90 1. In old ocprobe generic label DoControl is imprecise: on E90 it is
comparison of six live Usbc words, while on N95 — stock DVFS percentage.
On E90 v14 create/info/delete and receive-created completed cleanly,
without DSP RUN. Before new RUNs a refined message/lifecycle contract is needed.

### Installer control via a single connection

`live_device.py` accepts JSON operations from stdin and executes all I/O
sequentially. Between commands every 2 seconds INFO is sent. Connection checks
device by screen, does not reconnect and does not seek another IP; journal
is created only in absence of file. Duration limit 30–600 seconds,
wait for single daemon command — 30 seconds. On E90 heartbeat and file
operations were verified, but subsequent connection abort remained.

Run in an interactive terminal, specifying a new journal name:

```powershell
python -u tools/live_device.py --ip 192.168.3.21 --device e90 --log work/evidence/e90/installer_unique.txt --duration 300
```

Next, enter one JSON object per line, for example:

```json
{"cmd":"FG"}
{"get":["E:\\ps1_daemon.log","work/evidence/e90/daemon_unique.log"]}
{"close":true}
```

GET does not overwrite local file. Execute OPEN/KEY according to actual state
of the installer; do not send keys based on an old snapshot. This client does not replace
version guard, preserving previous journal, and checks of `run_stream.py`.

`tools/rev` tools use shared relative paths. Variable `C55_ROM_DIR` specifies `sys/bin` directory of another unpacked ROM. Example of static check:

```powershell
python tools/rev/exports.py bridgeapi.dll
python tools/rev/compare_node_info.py --e90-rom work/evidence/e90/rom
```

Second command compares LDD get-info and its PDD vtable/getter across two
firmwares. It does not substitute generic N95 address difference for E90 PDD;
distinct BL and addresses of its import stubs are listed separately. ROM remains
local; JSON contains hashes and contract of 112-B record.

Checks 2026-09-30: ARM and DSP builds completed with code 0; environment and JSON check passed; export list of `bridgeapi.dll` contains expected 39 ordinals. Commands and checksums are given in `docs/SESSION_2026_09_30.md`.

## WSOLA / ARMv6 — current build 20

MMP research host has -march=armv6 -mtune=arm1136j-s -fomit-frame-pointer;
SDK UREL -O2 -fno-unit-at-a-time. Added wsola_reference.cpp and DSP
wsola_dsp.c (contiguous RPT/MACM dot), input 1792 / output 48 B.
build.cmd clears c55stream.o and wsola_reference.o: SDK does not invalidate them
solely upon MMP compiler-option change. Before delivery verified 244-byte ARM
body, DOFF/imports/ASM and source/host hashes: artifact 6 / codegen evidence.

Builds: tools/build.cmd, tools/build_stream_node.cmd worker-stream,
tools/build_stream_sis.ps1 -Revision 20. Dedicated worker archive is unchanged;
after series tools/build_stream_node.cmd rebuilds main normal DLL.
run_stream.py default host 20; for historical evidence specify version explicitly.
WSOLA series helper has --host-version 19/20. Screenshots installers may
take over 8 s; daemon native command OPEN, timeout 30 s, observed KEY/SHOT.
OPENSIS is not supported. Reproduction/limits — WSOLA.md.

Combined reference for host 24 (already performed control, not repeat command):
`python tools/prepare_native_library2.py --combined` creates local DOFF 4476 B
with properties 0 / library 2 in one packet. Non-registration packets and
relocations exact; DLLdump passed. Proof —
`e90-d0-native-library2-combined-derivation.json`, artifact 30 —
`d0-native-copy-host-v24-combined-artifacts.json`. Host/SIS same v24 / package 28.
RUN 4 transferred 8 exact echoes, but delete −33 / pending; this is failed lifecycle.
`e90_task_session.py` now has connect timeout 8 s only in E90 session;
after three post-reboot connect failures next retry awaits transport change.

Current E90 diagnostic — host 26 / protocol 26, `worker-message`, package 33.
ARM/DSP build EXIT 0,25 imports/DOFF/ASM checked; immutable artifact 33.
Finite CREATED worker sends one MSG 606 and read-only snapshot, no RUN.
Default checkpoint checker uses this artifact; old proofs are historical.
Direct replacement of our C:\sys\bin\c55stream.exe and C:\sys\hash\c55stream.exe
permitted by the user: `e90_task_session.py --action deploy-host --host-version 26`
with matching `--artifact-proof` saves GET backups before PUT and checks GET after.
`restore-host` restores exact saved host 20 and exact saved hash; only on PS 0
and original DSP. Installer is no longer needed. New worker-msg01 had
failed create-only preflight delete −33 / pending prior to MSG/RUN; repeating it
is not allowed. Further only after reboot/GET/PS0/restore with skipped no-input preflight.
