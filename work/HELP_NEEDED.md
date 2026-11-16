# Actions Requiring Human Intervention

**Handoff 04.10:** current work completed with a report for Claude at the user's
request, `docs/CLAUDE_PS1_HANDOFF_2026-10-04.md`. We do not request new physical
actions and do not automatically start new experiments. E90 recovery
remains open for the next assignment; old requests below are historical.

**Current as of 2026-10-04:** the user instructed finishing on N95,
E90 postponed until tomorrow. Currently we do not request a new physical action.
N95 5 originals restored after native61: 3 series/9360 packets/6 stock brackets.
E90 reboot confirmed by the user; daemon journal obtained, reason
unknown. On E90, host46/original DSP remained; restore of EXE/hash/journals
is still needed after returning to E90. Ringclock.exe is not installed.
Old Open4All request below is not a current prerequisite for work on N95.
Current state — HANDOFF_NATIVE_RING_2026-10-04.md.

## 2026-10-01: install research host21 on E90

On **Nokia E90**, without actions on N95, open via file manager
`E:\c55stream-d0-v21.sis` and confirm update of **C55Stream Research
1.00(21)**. Report when installation completes and Wi-Fi daemon is again
available at 192.168.3.21:2323.

This is required for D0 verification: old host20 closes native processor
even after delete error; host21 retains resources until manual recovery
if completion is not proven. A timeout result will not be called a success.

Already done: backup of DLL/log/ocprobe.log/installed EXE/hash; ARM/DSP/SIS
builds with EXIT_CODE0; SIS delivery and GET-equal. Package SHA256:
`A3592773BEB73E75ECBDCE3AD729C97C49F5C5F0A39EA81C1C7EDAEEB0BC1A6D`.
First delivery stopped before PUT due to discrepancy in daemon ERR text;
second after exact STAT parsing was successful. DSP DLL not yet replaced,
new RUN was not called. Direct writing of EXE to E90 is not a verified path;
standard SIS installation is used.

In this session registers show stock profile m86, ARM330.24MHz,
bus110.08MHz, DSP220.16MHz. PRCM was not changed. For D0 these are suitable
actual conditions; returning overclock is not a prerequisite for this test.

If host21 subsequently records `QUARANTINE`, manual reboot of
E90 is needed, restoring Wi-Fi daemon, then journal GET before new START/PUT.
Automatic KILL or unload of a live DSP session is prohibited.

At 19:02 UTC repeated GET confirmed all 5 originals, host20,
c55stream/ocprobe PS0, startTick75535. At 19:10:31 UTC an attempt
to connect for observed SIS installer via live_device.py
ended with `TimeoutError: timed out` in socket.create_connection with
a 3s limit, before INFO/OPEN/KEY. No new action took place on the phone.
Restoring availability of E90 Wi-Fi daemon is also needed. Capability of
OPEN/KEY/SHOT is known from prior installations, but there is no current connection.

Second attempt at 19:12:52 UTC (e90_task_session.py verify02) gave the same
connect timeout 3s before INFO. Two retries are sufficient, no new RUNs occurred.

### User Response, 2026-10-01 22:25 (relayed by PS1Emulator orchestrator)

SIS `c55stream-d0-v21.sis` installed on E90, user confirmed. After
this at 22:30 E90 did not yet respond either to ping 192.168.3.21 or to port 2323;
scan 192.168.3.2-254 found daemon only on N95 (.22). User requested
to launch daemon on E90 and check Wi-Fi. N95 as before do not touch.

### Next Step After User Response

Third connect verify03 after this message also yielded
`TimeoutError: timed out` in connect 3s before INFO. Limit of three attempts
exhausted. **Need only to start Wi-Fi daemon on E90** and restore
availability of 192.168.3.21:2323. No need to reinstall SIS21.
After connection returns GET will verify exact host21; without this RUN
does not start. Previous GET-equal originals was before reported installation.
22:27: user launched daemon on E90; port 192.168.3.21:2323 accepts TCP connections (verified by orchestrator). May continue D0.

## 2026-10-01 19:35 UTC: restore access after first D0 RUN

Host21 confirmed by GET/SHA256 8FD9FAE1…, original DLL/log/clock log
before write exact. Fresh clock probes gave ARM330.24/bus110.08/DSP220.16MHz,
clock log restored exact. Inspect and create/delete gave FINAL/EXIT0.
Next deployed run-stop DLL7B07E8D0… GET-equal, started **one**
run-transfer reps=0 bytes=512 frames=8. Supervisor saw c55stream PS1,
then PS request received TimeoutError 8s. GET on the same socket did not
succeed: OSError cannot read from timed out object. New read-only
connection for journal GET also received connect TimeoutError 3s.
There was no second/third RUN and no KILL. Packet/delete/FINAL unknown;
unknown whether QUARANTINE or other failure. DSP DLL currently research;
it must not be overwritten before confirmed completion or reboot.

**Needed:** if E90 responds to keys, open/launch Wi-Fi daemon
and restore 192.168.3.21:2323 without reboot to retrieve journal
from live session. If device hung, reboot only E90 and start
daemon. Report whether reboot occurred. Do not start C55Stream or other
DSP application: first GET E:\c55stream.log, then restore DLL/log.
N95 do not touch. Evidence: work/evidence/e90/d0-20261001/resume-sequence01*,
out/d0-resume-sequence01.log, out/d0-resume-run1-recovery01.log.
22:33: user reported that E90 was rebooting (reason not known to orchestrator; possibly during RUN host21); after reboot user again launched Wi-Fi daemon. This is not a KILL from PC side; retrieve journal on E90 via GET before new START.
22:36: user reported SECOND reboot of E90. According to journals it occurred during
d0-sequence, step run1 `run-transfer reps=0 bytes=512 frames=8` (out/d0-resume-sequence01.log,
19:34-19:35 UTC: reading daemon response aborted with timeout, recovery at 19:36 no longer connected).
First reboot - between verify01 (19:31:20, complete=True) and clocks01 (19:31:40, connect timeout).
Thus RUN host21 on E90 twice ended with device reboot; this is a hardware fault, not network.
Limit - three identical attempts: before third an approach change is needed (diagnostics without RUN, journal from
E:\c55stream.log after reboot). User launches daemon manually after each reboot.
22:38: response to request above. Yes, E90 was rebooting (user, second reboot after RUN 19:35 UTC); live session is gone. User again launched daemon; orchestrator at 22:38 checked that 192.168.3.21:2323 accepts TCP. Nobody launched C55Stream.

### Retrieved Journal and Clarification of RUN Count

At 19:40:31 UTC GET retrieved journal CE5B1947…: 8 packets correct,
state before delete 3, delete/status−2, QUARANTINE without free/close.
INFO startTick61377, PS0 after confirmed reboot. Original
DLL/log/clocklog restored GET-equal (resume-restore01).
In our transport logs prior to this there is **one** RUN, not two. First
reboot was between read-only GET verify01 and failed connect
clocks01; prior to that new C55Stream START/RUN did not occur. Its cause
cannot be attributed to RUN based on our evidence.

### Second, Altered DSP Candidate: New Recovery Needed

Candidate22 (host21/protocol21) after stop waits for standard RMS_EXIT from
hostCtl6. First RUN resume-sequence02 left process active until
deadline 30s. Daemon responded to PS, no KILL occurred. Journal GET received
**ERR open -14**: host21 holds RFile without permission to another reader, therefore
journal of live QUARANTINE session is inaccessible. Exact location of second failure
is still unknown. DSP DLL2B97836D… currently research and not restored.

**Need again to reboot only E90 and start Wi-Fi daemon**,
do not start C55Stream/other DSP. First GET journal before any START
or PUT, then exact restore. Simultaneously preparing new host with readable
journal so that subsequent timeout can be analyzed without this reboot.
22:57: user rebooted only E90 and launched Wi-Fi daemon; C55Stream was not launched. Orchestrator checked port 192.168.3.21:2323: OK. May GET journal and restore.

## 2026-10-01 20:04 UTC: install host22 with readable journal

After confirmed reboot, GET resume-recovery03 at 19:58:28 UTC retrieved
journal F35CDF7F…: 8 correct packets, before delete state 2,
`delete submitted=0 status=-2147483647`, then `delete=-33` and
QUARANTINE. Host21 remained active, no KILL occurred. This is second RUN;
no third RUN yet. PS0/startTick60875 after reboot confirmed.
Original DLL/log/clocklog restored exact PUT/GET (resume-restore02).

**Need to install only on E90 file E:\c55stream-livejournal-v22.sis**
via regular installer; it is already delivered GET-equal.
SIS SHA2560F8577C66D84C0C2C43FC600AFAB0C77736FC4962084DE95DBFEC0C4084E21BA.
This is runtime host22, package revision 23; DSP protocol remains 21.
Sole host change: EFileShareAny for live journal and version marker.
Installation needed so that subsequent diagnostics does not require reboot
solely for GET E:\c55stream.log. Do not run C55Stream independently;
keep daemon running. After confirmation GET will verify exact EXE.
N95 do not touch. Restore SIS with exact initial host20 also preserved
locally; final EXE restore will require standard SIS install.
23:10: user installed E:\c55stream-livejournal-v22.sis on E90 (host22). Port 192.168.3.21:2323 per orchestrator check: FAIL. C55Stream was not launched by user.

### 2026-10-01 20:11 UTC: after reported install22 only daemon is needed

User reported install22. GET check host22-verify01 received
connect TimeoutError 3s before INFO. No third RUN/PUT/START after install.
Need to start Wi-Fi daemon only on E90 and restore .21:2323.
Do not reinstall SIS22, do not launch C55Stream, do not touch N95.
After connection: GET exact host22, stock clock/inspect/create, one generic
run-message-diag with three read-only DSP MSG snapshots (already built),
without KILL; this is diagnostics, not an accepted D0 cycle.

23:11: user returned E90 to network; orchestrator verified 192.168.3.21:2323: OK. May GET host22.

## 2026-10-01 20:16 UTC: third RUN completed, only recovery of E90

GET host22-verify02 confirmed EXE 35120 B AFF498B8… and originals DLL/log/
clocklog; PS0, startTick91233. message-diag01 had stock clock guards,
inspect/create FINAL/EXIT0, generic diagnostic DSP 3836 B B1CB8409…
PUT/GET-equal. Three STRM snapshots correct: NODE_getMsg(0)=0,
NODE_putMsg(0)=1, fromDSP count1, raw record 0000/0600/000F/0001/
0000/77E0/0000/77E0; ror 16 gives cmd 600/arg1 F0001/arg2/source 77E0.
After return: message-get submitted−2, state 3, delete/status−2,
QUARANTINE. Live GET of journal D29CDA12… successful thanks to host22 sharing.
Supervisor deadline 30s, no KILL. Limit of THREE experimental RUNs
exhausted, no new RUN will take place. D0 0/3, D1 not opened.

**Need to reboot only E90 and launch Wi-Fi daemon.**
Do not launch C55Stream or other DSP programs. Journal is already saved;
after PS0 there will be exact restore of original DLL/log/clocklog. Then will deliver
restore SIS package revision 25 with exact original host20 EXE; installation
via standard installer is required for final restoration of EXE/hash.
Currently DSP diagnostic DLL is still on phone; do not overwrite it prior to reboot.
N95 do not touch. This is recovery after failed ownership, not a new RUN cycle.

### User Decision, 2026-10-01 23:22 (relayed by PS1Emulator orchestrator)

Limit of three experimental RUNs on E90 LIFTED. User writes: to achieve
the previous result with lower DSP latency, around 20
reboots were required, so E90 reboots are an acceptable experiment cost, and
the user performs them on request. Request: plan each RUN more deliberately,
so there are fewer reboots. Before RUN, formulate hypothesis and what
specifically this run is intended to distinguish; collect maximum diagnostics in one
run (live host22 journal, MSG snapshots before and after); do not repeat
a run without a change that tests a new hypothesis. Continue D0 -> D1 -> D2.
Remaining rules unchanged: do not touch N95, no KILL/unload of live DSP session,
requests to user — here.
23:27: user rebooted E90 and started daemon. Port 192.168.3.21:2323 per orchestrator check: OK. C55Stream was not launched.

## 2026-10-01 20:33 UTC: control ROM STRMCOPY, need install host23

After human reboot 23:27 GET final-recovery01 retrieved journal before PUT,
PS0/startTick61475; original DLL/log/clocklog restored exact PUT/GET
(final-restore01). Next read-only GET Z:\system\apps\strmcopy\strmcopydyn.dll55l
retrieved E90 ROM node 4396 B, DLLdump verification passed. Hypothesis
of next RUN: failure occurs in our execute/return or its cleanup,
not across entire native host lifecycle. ROM STRMCOPY executes all DSP phases,
host verifies 8 echo packets of 256 words each; native RUN/delete are the same.
Clean reference will narrow cause to custom node/generic phases; failed
reference will narrow to host/setup/native firmware path. This is a diagnostic
control, by itself does not close D0 for our DSP. No own DSP PUT for
this control. Live journal sharing and state after delete in host23.

**Need to install only on E90 E:\c55stream-native-copy-v23.sis**
(already delivered and GET-equal; package 26, runtime 23).
SIS 21064 B SHA256 D383BF30F371DD8A4CBCB5C7820B25C141CBD60FC7D40AF0EE59C8026D2AC809.
Keep daemon running, do not launch C55Stream; after install GET
will verify exact EXE. If daemon disappears after installation, launch it.
N95 do not touch. Limit of 3 lifted by user decision above; every subsequent RUN
has its own new hypothesis. We do not restore original host20 yet because research
continues; final restore package must be above 26.
23:34: user installed E:\c55stream-native-copy-v23.sis on E90. Port 192.168.3.21:2323 per orchestrator check: OK. C55Stream was not launched.

## 2026-10-01 20:42 UTC: host24 fixes preflight, RUN not yet called

Host23 GET exact 36492 B 31836A0F…; native-reference01 had parseROM0,
but select node−6, FINAL/EXIT−6 before allocate/create/RUN. Thus THREE
experimental RUNs remain, no fourth yet; reboot not needed.
Preflight cause: ROM .dcd_register contains only properties:0, no
library3/2. Did not verify this prior to host23 SIS; this was an unnecessary installation.
Original DLL/log/clocklog restored exact (native-preflight-restore01).

For control, made research-copy E90 ROM DLL 4396 B 308090D3…,
changed only registration:0→:2 and packet checksum (offsets 3807/3883).
All DSP code/data/relocations exact unchanged; DLLdump passed.
ROM/firmware are not written. Host24 parses original ROM properties0,
then E research library2. Control hypothesis remains custom execute
versus native host/setup; library2 now same as in custom probes.
Before RUN, inspect/fresh clock/GET source+derived SHA gates.

**Need to install only on E90 E:\c55stream-native-copy-v24.sis**
(already GET-equal, package 28, runtime 24).
SHA256 CEB641F9956E3CDADECAF865634D21022140C36DD28FCE524603DC5B14DD6B79.
Leave daemon running, do not start C55Stream. After install GET
will confirm exact EXE; do not touch N95. Reboot is not requested here.

### 2026-10-01 20:53 UTC: host24 GET not yet accessible

Read-only host24-verify01 received connect TimeoutError 3s before INFO.
Install24 is not yet GET-confirmed; no fourth RUN. Need
to finish installing E:\c55stream-native-copy-v24.sis, if not yet
installed, and launch Wi-Fi daemon on E90 .21:2323. Do not launch
C55Stream, do not touch N95. Previous record of PS0/original 3 exact
is the last confirmed checkpoint before this connect timeout.
23:56: user message (relayed by orchestrator): "At the moment of installing v24 a reboot occurred. After that I reinstalled it once more. Currently the daemon is accessible." Meaning E90 rebooted DURING v24 installation, then v24 was installed repeatedly. Port 192.168.3.21:2323 per orchestrator check: OK. C55Stream was not launched.

## 2026-10-01 20:59 UTC: TCP accessible to orchestrator, but GET not yet started

host24-verify02 again received connect TimeoutError 3s before INFO; RUN did not
start, install24 confirmed only by human. In daemon source
acceptLoop/serveOne serves one client until close, readLine
is blocking without idle timeout; this is a possible explanation, not a proven cause.
Need to close all E90 TCP connections of orchestrator/other clients and
temporarily cease parallel TCP probes of .21:2323. Leave daemon running.
If it hung after closing clients, restart only the daemon via its
normal interface; do not launch C55Stream. Not asking for reboot right now.
The next single session will verify GET exact host24/PS0/fresh clocks and only
then native library2 control under the already described new hypothesis. Do not touch N95.

## 2026-10-01 21:08 UTC: host24 exact, native reference2 before RUN select−6

TCP recovered without a new reboot request. Native-reference02 GET exact
host24 SHA25612356F00E0163EF0B0823A0E017D38A2796DCE83F2AB1FA85554DCFFF32A09D8,
PS0, startTick35185, fresh stock 330.24/110.08/220.16MHz. Parse ROM0,
parse library2=0, but select−6/FINAL−6/EXIT−6 before allocate/create/RUN.
Still THREE experimental RUNs, no fourth; reboot not needed.
Native-preflight-restore02 returned original DLL/log/clocklog exact.
TCP release request above is no longer relevant; do not launch C55Stream.

Next hypothesis: separate parses do not provide select with the full set of
properties0/library2; combined registry packet in E research copy contains
both entries simultaneously, like our working generic loader. This is a preflight
check, the cause of −6 not yet established. DLL 4476 B C7572358…;
DLLdump PASSED, all non-registration section packets and relocations exact,
only registration size/packet and table offsets/checksums changed.
Host24/SIS remain the same. If select passes, one native RUN with
8 fully verified echo packets will test the prior lifecycle hypothesis;
clean control does not count as own-node D0. No unchanged RUN retry.

## 2026-10-01 21:09 UTC: native control RUN4, need reboot E90

Combined properties0/library2 resolved preflight: select/create/RUN=0.
Native STRMCOPY code/data/relocations unchanged executed 8 exact echo
packets of 512 B (all 256 words), wall_us 579/488/488/488/457/457/488/488.
After control 6 delete=-33, status pending, state 2→3, QUARANTINE without
free/close/FINAL; 30s local deadline. Live GET journal succeeded,
SHA256A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1.
This is FOURTH experimental RUN; D0 own cycles 0/3. ROM control narrowed
cause to host/setup/native lifecycle, custom execute is not the sole
explanation. KILL/unload 0, PRCM writes 0. Further without new RUN until recovery.

**Need to reboot only E90 and launch Wi-Fi daemon .21:2323.**
Do not launch C55Stream. GET journal/PS0 after reboot must precede
PUT/restore. Original DLL/log/clocklog will return exact GET/SHA;
research EXE 24/hash remain until completion of research. Do not touch N95.
While user reboots, native host stream flush/cancel,
MSG delivery/EXITACK, and native application lifecycle from saved ROM are being audited.

## 2026-10-02 04:07 (orchestrator): E90 rebooted, daemon accessible

User rebooted E90 after native control RUN4 and started daemon (on second attempt). Port 192.168.3.21:2323 accepts TCP (verified by orchestrator). Previous Codex process stopped at 00:13 due to OpenAI usage limit, not due to failure. C55Stream was not launched.

## 2026-10-02 04:10 (orchestrator): user unavailable until morning

User went to sleep and until morning cannot reboot E90, launch daemon, or install SIS. Work autonomously. If E90 requires reboot or daemon disappeared, do not wait for response: record state in work/STATE.md and docs/evidence, describe needed action in this file and continue whatever is possible without device (analysis, preparation of next step). Do not touch N95.

## 2026-10-02 01:12 UTC: after confirmed reboot GET/restore not yet started

HELP/user confirmed reboot after RUN4, daemon is launched. Three bounded
read-only attempts of this recovery: native-recovery01 Python connect 3s,
native-recovery02 Python connect 8s, native-recovery-net01 .NET connect 8s —
all TimeoutError before INFO. No PUT/START/RUN/KILL executed in this boot.
PC has Huawei Wi-Fi, 192.168.3.11/24; Find-NetRoute for
.21 routes through this Wi-Fi. Python-only problem was not confirmed.
Last retrieved journal of RUN4 is already saved A33A433C…; new GET/PS0
and exact restore after reboot NOT yet confirmed. Limit of 3 network attempts
for this state reached; unchanged connects are not repeated.

**Need only to restore daemon transport E90 .21:2323:** close
other client TCP connections, verify Wi-Fi/IP on E90 and restart
daemon via standard interface if it hung. Do not launch C55Stream.
Orchestrator to verify one INFO (response screen 800x352 and END), rather than
only TCP handshake, then close socket and provide us one exclusive session
GET journal→PS0→restore. New reboot is not requested now; already performed
reboot is sufficient for recovery if transport returns. Do not touch N95.

Next D0 hypothesis after recovery: distinguish RMS_EXIT delivery from
DSP idle/reclaim and native EXITACK. One modified own-node diagnostic
must transfer STRM snapshots before waiting for EXIT, after NODE_getMsg and after
cleanup before return; host must retrieve them during pending delete. Do not
repeat native control without a new change; its 8 correct echo packets
do not by themselves close D0. D1 hardware still only after 3 own clean cycles.

## 2026-10-02 13:21 (orchestrator): E90 restarted, daemon accessible

User restarted E90 (daemon was not responding since 04:20). Port 192.168.3.21:2323 accepts TCP (verified by orchestrator). User is back online.

## 2026-10-02 13:35 — install diagnostic host25 on E90

Recovery completed: `native-recovery03` retrieved the same RUN4 journal
SHA-256 `A33A433C6B8555C945A58DB7C12D75A3427A285C7337520F3804CC4C0EC47BF1`,
PS c55stream/ocprobe =0, INFO responds, startTick81256. `native-restore01`
restored three initial E: files, all GET/SHA exact. Repeated RUN not yet performed.

Need on **E90** via File Manager to install
`E:\c55stream-exit-diag-v25.sis` (22416 B, package revision 31).
File is already delivered and GET-verified:
`8D0E3BE832E8F81E2538A747D9904FBA37BDEF32F6FCDF614B00BB3EDD51E97A`.
This is an update of only our `C:\sys\bin\c55stream.exe`, runtime v25,
expected EXE SHA-256
`CB74DE96012E3C9D4D7DDE6F783C6A746F75713B83DBF136DF03001C7035CA0A`.
Confirm ordinary installer prompts. Do not launch C55Stream manually;
after installation report here and leave daemon running.

New hypothesis of RUN5: establish whether RMS_EXIT was delivered to NODE_getMsg, whether
STRM_idle(input/output) return, and only then verify native EXITACK.
Own DSP `run-exit-diag` will transfer stage 4 before waiting for EXIT; stage 5 immediately
after NODE_getMsg and stage 6 after idle in shared output packet.
Host orders exit before control 6. After idle, diagnostic output is reissued;
this affects cleanup, therefore RUN5 is not one of three regular D0 cycles.
Pending/failed delete or output → QUARANTINE, without KILL/free/close.
Build/import/DOFF checks successful, all 18 imports exist in saved E90 baseimage.
SIS for final return of exact host20 prepared with higher revision 32.
N95 was not touched. New reboot is not needed now.

## 2026-10-02 13:38 (orchestrator): user permission - replace EXE autonomously

User message: "it is permitted to reinstall apps exe by replacement without my involvement. On e90 hack is active." Meaning SIS installation via File Manager to update only our EXE is not needed: replace C:\sys\bin\c55stream.exe (and hash in C:\sys\hash, if your tool does so) autonomously via daemon, with GET/SHA verification before and after. This also applies to v25 request above: user did NOT install SIS v25 - perform replacement yourself. Reboot and daemon start, as before, require human. Do not touch N95.

## 2026-10-02 13:43 — need reboot of E90 after RUN5

Request for SIS v25 above is no longer needed: per 13:38 permission executed
`host25-deploy01`, backup host24/hash before replacement and GET exact host25/hash
after, PS0. Own diagnostic `exit-diag01` performed only one new RUN.
8 packets 512 B full 240 payload words — correct; stage 4/5/6 delivered.
**RMS_EXIT delivered:** NODE_getMsg result 1, waits 1,
cmd 80000000/arg1=env77E0/arg2=0. **First cleanup clean:**
STRM_idle input/output 0, pending input/output 0, DSP status 00008000.
After extra diagnostic output wrapper/native EXITACK not yet proven:
delete submit 0, after 5000ms −33/status pending, state 3 → QUARANTINE.
Live journal GET successful, SHA-256
`778039EBA2B21B3A07F65FB7EDF89040F2BBB386CF1C11B84157B76023F1691E`.
Did not perform KILL/free/close; local runner deadline 30s stopped polling.

**Needed:** reboot only E90, launch Wi-Fi daemon, report
here after availability of .21:2323. Do not launch C55Stream; do not touch N95.
After reboot first GET of the same journal/PS0, then exact originals 3
restore. Host EXE/hash will subsequently replace myself per permission; SIS installer
not needed. New RUN does not repeat this same diagnostics: now seek
error in wrapper return / outbound RMS_EXITACK / ARM MSG reader, rather than
repeatedly testing delivered RMS_EXIT. D0 own 0/3, experimental 5.

13:54 repeated read-only `exit-recovery01` confirmed unchanged journal
SHA778039EB…, DSP29069D52…, INFO responds, startTick the same 81256,
PS c55stream1/ocprobe0. Reboot has not yet occurred; live QUARANTINE owner
impedes safe restore/subsequent RUN. No PUT/START/KILL in this
check occurred. Request for human reboot above remains relevant.

## 2026-10-02 14:55 (orchestrator): E90 rebooted after RUN5

User rebooted E90 and started daemon. Verification of port by orchestrator - see next launch line. C55Stream was not launched.

## 2026-10-02 15:16 local — created-worker preflight pending, need reboot E90

RUN5 recovery executed: exit-recovery02 journal778039EB… exact/PS0,
exit-restore01 original DSP/log/clocklog PUT→GET exact, startTick65704.
Host26 direct replacement permitted: host25 EXE/hash GET backup before
PUT, host26 EXE 40920 B 2EAC917E…/hash GET exact. New hypothesis:
prearmed outbound MSG in CREATED, without execute wrapper/official RUN.

`worker-msg01` stopped at create-only preflight: create 0/7598us,
state 1; delete submit 0, after 5000ms −33/pending, after state 1.
Planned trigger/MSG diagnostic did NOT start: NODE_putMsg 606 and RUN
were not called. This is not an ARM reader test result and not RUN6.
I repeatedly used create-only preflight for active stream worker;
its cleanup without input/native buffers was not yet proven. Ought
to verify stop→NODE_wait→idle/reclaim/join, while next diagnostic
must immediately supply final trigger after creation, without this preflight.
No unconditional repetition will occur. QUARANTINE, did not do KILL/free/unload.
Live GET journal 2092 B:
`B9B4E282CF099D986E8B1AC08B25F32BFF73E546294316379563613DB084EA92`.
Clock log 1249 B restored exact; DSP/log research26, host26/hash research.

**Need to reboot only E90, start Wi-Fi daemon .21:2323
and report here.** Do not launch C55Stream; do not touch N95.
After report first GET journal/PS0, then originals 3 restore;
next test only after audit of this new cleanup branch.
D0 own 0/3, experimental RUN5 unchanged; D1 pending, D2 provisional.

## 2026-10-02 15:21 (orchestrator): accidental LS on E90

Around 15:21 my deploy_net.ps1, addressed to N95 (.22), due to temporary unavailability of N95 itself found E90 and executed there a single read-only command: LS E:\PS1\cfg\. No write, PUT, START, or KILL occurred. If E90 daemon journal has this connection - that is it. deploy_net.ps1 fixed (SymbianDeployDaemon 2743c6c): explicit -Ip no longer scans network.

## 2026-10-02 15:28 (orchestrator): work stopped per human instruction

User is moving SSD to laptop; codex exec process (session 01a0f8bc-b1b0-77a1-8d92-45a5a49ed009) stopped by orchestrator at 15:28 in the middle of a turn. After resumption: first verify E90 state (GET journal/PS0, whether an incomplete operation from this turn remained), only then proceed. User clarified goal: tasks on DSP must provide true concurrency with ARM (DSP processes asynchronously, ARM meanwhile performs other work), not synchronous calls.

## 2026-10-02 evening — all physical recovery requests closed

User confirmed reboot of E90; laptop-recovery01 GET retrieved old
journal B9B4E282… exact, PS0/startTick61087. Originals 3 restored.
Under new user permission tested N95 as well. Four finite MSG
diagnostics clean delete/free/close, but ARM receive−33; no new RUNs.
After them **both phones fully restored**: DLL/log/clocklog/EXE/hash
GET/SHA-equal, host20, c55stream/ocprobe PS0. Daemon startTick E9061087,
N9522918156 unchanged. No request for reboot/installer exists currently.
Subsequent work — native runtime reader/window/queue audit;
docs/WORKER_MESSAGES_2026-10-02.md and docs/evidence/2026-10-02/worker-message-checkpoint.json.

## 2026-10-03 01:25 UTC: historical request after D0 Cycle 1

During first D0 cycle `run-transfer reps=0 bytes=512 frames=8` (session `d0-20261003-cycle1`, launch `run01`):
- All 8 frames transferred and verified (`STREAM PASS frames=8 creates=1 useful_arm_crc=0 mode=0 total_us=3230`, 3.23 ms).
- At deletion phase (Ctl 6) timeout occurred `delete=-33` (5000 ms), which put process into standard `QUARANTINE` (infinite sleep `User::After(1000000)` without calling free/close to protect the device).
- Process `c55stream.exe[e0001021]0001` is currently active in quarantine on E90, Wi-Fi daemon at 192.168.3.21:2323 responds.
- According to safety rules, automatic KILL of active process is strictly prohibited.

**Root cause analysis:**
- Full disassembly of `ehwaomap.pdd` (addresses `803e69b4`, `803df7dc`, `803df850`, `803df864`) showed:
  In RUNNING state (2) Ctl(6) sends `RMS_EXIT` (0x80000000) and waits for `RMS_EXITACK` (0x40000000) from DSP.
  ARM consumer compares `source` of incoming message with `queue->source` (0x000077E0).
  In run01 build function `fix_caller_env` mistakenly swapped 16-bit words in `nodeEnv` stack slot, causing DSP to send `source = 0x77E00000`. ROM reader `803f7664` performed `ror #16`, which gave `0x77E00000 != 0x000077E0`, consumer ignored `RMS_EXITACK`, did not call `803e6860` (`NODE_delete`), and 5-second timer completed with timeout -33.
- Mistaken word swapping completely removed from `src/dsp/stream_node.c`, DSP DLL rebuilt (`out/dsp/c55stream-run-stop.dll55l`) and verified in `docs/evidence/2026-10-03/d0-run-stop-v40-artifacts.json`.

**Required action:**
1. Reboot Nokia E90 physically.
2. Launch Wi-Fi daemon on E90 (192.168.3.21:2323).
3. Report reboot. Do not touch N95.
After connection returns:
- Check `PS c55stream* = 0` and restore of 5 original files will be performed.
- Clean series of 3 D0 cycles with fixed DSP node will be performed.

## 2026-10-03: actual actions after Codex routing diagnostic

Previous request and causal explanation above are obsolete; return of E90
is confirmed by startTick33897/PS0. User in Gemini transcript permitted
KILL as needed and working with both phones; old blanket no-KILL
text does not reflect this clarification.

1. E90: enable Open4All in RomPatcher. GET C:\sys\bin\c55stream.exe
   returned ERR open−46, therefore EXE/hash are not restored; DLL/log/clocklog
   already original GET-equal. After access returns restore-host→verify
   in work/evidence/e90/d0-20261003-cycle2 with new codex tags.
2. N95: reboot and launch daemon. Runtime snapshot revealed
   old kernel queues and two source 77E0, despite PS0 before probe.
   Correct EXITACK40000000/8000 did not complete delete of new node.
   Journal saved; quarantined host removed by permitted KILL;
   all 5 originals restored and SHA-equal verified, no active processes.
   Reboot needed for clean routing, not for file restoration.

Both actions requested via async user input. Next host34 guard
refuses before RUN if matching queue for env is not exactly one.
D0 remains 0/3; next series does not start from dirty kernel state.
Document and continuation point: docs/MESSAGE_ROUTING_2026-10-03.md.

## 2026-10-03: actual request — reboot with already installed host35

Previous Open4All/reboot actions executed. Host34 guard refused before RUN
on both phones: its PROC_Load repeatedly loaded DSP base given existing
standard native queues. Unconditional stop/load/start confirmed on two ROMs.

Host35 is already installed on N95/E90: uses running base without
PROC_Load. Attach/create/delete/free verified 0 on both; old conflict
still exists. No quarantine or active c55stream/ocprobe. DLL/log/clocklog
original GET/SHA-equal; v35 EXE/hash deliberately left installed,
original EXE/hash saved in d0-20261003-clean34.

Need to physically restart **both** phones, restore daemon and
Open4All and report readiness. This is a new request after old host34
reload; prior user reboot was executed. Async request sent.
After startTick change — d0-sequence host35 candidate47, tag attach-sequence02.
Details: docs/BASE_ATTACH_2026-10-03.md. D0 0/3; no new official RUNs.

## 2026-10-03: actual reboot request closed, D0 successful

User confirmed new reboot of both; daemon/Open4All accessible.
E90 startTick60327 / N95 62209. Host35 candidate47 passed 3/3 clean
ordinary D0 cycles on each, boot unchanged, all lifecycle statuses 0.
Original DLL/log/clocklog restored, host35 installed for D1, PS0.
No new physical actions needed. Next — D1 mapping/ring probe.
Evidence: docs/evidence/2026-10-03/d0-attach-success.json.

## 2026-10-03: actual step — Open4All only on E90

D0 successful on both. N95 completed 3 series of D1, all 5 originals restored,
PS0; no physical actions on N95 needed now.

E90 restored connection after boot change during initial routing snapshot
host41. GET journal saved before PUT, PS0. Original DLL/log/clocklog
restored. Exact original EXE/hash restore stopped before PUT due to
`ERR open -46` in C:\sys. **Enable Open4All on E90**, leave daemon
192.168.3.21:2323 accessible and report. New reboot not needed.

After this agent will itself restore EXE/hash, verify 5 originals, and
continue with new hypothesis host42/candidate55; do not repeat unchanged host41 run.
Detailed continuation point — last section of STATE.md.
D1/D2 remain open; root cause of boot change not yet proven.

## 2026-10-03: actual step — restore E90 after candidate56

Previous Open4All executed, 5 originals restored, candidate55
aborted before map/RUN and also restored. Candidate56/host43 completed
one full series and s2-b1, but during s2-b2 daemon disappeared. Journal not
yet retrieved, current EXE/hash/DSP research installed. Async request:
verify E90 and restore daemon/Open4All, if needed — reboot.

After accessibility agent will GET journal/PS before any PUT, analyze and
restore 5 originals. New unchanged 56 RUN prohibited. N95 restored,
do not touch it. Current continuation point — last STATE section.

## 2026-10-03: all physical requests closed

User returned E90 and confirmed automatic reboot, not merely Wi-Fi
timeout. All 54/55/56 failure journals retrieved before PUT; latest readable
journal aborted before DSP RUN. Probe57 was only brief; long series
canceled after clarification. Read-only boot-info44 completed clean.

**N95/E90 all 5 originals GET/SHA-equal, c55stream/ocprobe PS0.** No new
physical actions needed now. Next — safe native reader/state/
queue contract and cause investigation before new E90 RUN; not unchanged retry.
Current source44 is a local research artifact, on phones original20.
