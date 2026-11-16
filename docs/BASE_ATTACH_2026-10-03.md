# Attachment to the current DSP base

Update after the new reboot: **D0 completed on both phones, 3/3**.
E90 startTick 60327, N95 startTick 62209; host35 candidate47, base reload 0.
Each individual RUN transferred 8 correct 512 B packets/protocol 21,
delete/free task/free native buffers/close/FINAL/EXIT0. The boot is
unchanged. The original DLL/log/clocklog were returned GET-equal; host35 was
left in place for D1.
Evidence: [D0 success](evidence/2026-10-03/d0-attach-success.json),
reproduction `tools/summarize_d0_attach_success.py`. The D1 hardware gate is
open; the copy-channel timings below are not a result of the DMM ring or a
speedup.

Earlier result before the reboot: **D0 0/3**, no new official RUN. On both
phones, host34 detected a duplicate source77E0 before RUN, refused with −11,
and cleanly performed delete/free task/free native buffers/close. This is a
useful check of the protection, but not a successful D0 cycle.

## A cause to be checked after a fresh start

Before v34, the host called ordinal 26 (`PROC_Load`) for the base image every
time, although the DSP was already in use by the standard audio. On both
firmwares the native load has an unconditional call to stop, then load/start.
The running state is not a condition for skipping the stop. The static audit
checks 20 instructions and three branches on each firmware:
`tools/rev/audit_processor_reload.py`.

After such a load, the runtime keeps two native queues from source77E0 (the
old standard one and our new CREATED node) and also source 7700. Since the
consumer selects the first source, this is consistent with the earlier
recorded ACK that reached the old node. The role of the specific audio nodes
and the causality of all historical failures are not yet proven.

Host35 removes `PROC_Load`, attaches to the already running processor0,
checks the manager magic/back-pointer/index/state 4, and registers only its
own dynamic library through DCD parse. The unique-source guard before RUN is
kept. If the running base does not exist, the host refuses and clears the
channel. This host does not repair the queues that have already become
inconsistent after the old load.

## Hardware checks

| Phone | Host34 | Host35 without a new reboot |
|---|---|---|
| E90, startTick 33897 | create clean; guard −11; cleanup 0 | attach gate 0; create clean; guard −11; cleanup 0 |
| N95, startTick 64375 | create clean; guard −11; cleanup 0 | attach gate 0; create clean; guard −11; cleanup 0 |

None of these four guarded refusals calls execute. FINAL/EXIT −11 reflects
the protective refusal; this is not a successful transfer of packets.

Candidate 47: host35, unchanged DSP 41/42, a verified build of ARM/SIS/DOFF.
14 offline tests passed; the validator additionally requires that the
running base be kept. The DSP busy-wait before return remains an earlier
unconfirmed hypothesis.

The original DLL/log/clocklog of both phones were returned GET/SHA-equal;
host35 and its hash were deliberately left installed. The original EXE/hash
are in `work/evidence/{e90,n95}/d0-20261003-clean34/original-{3,4}.bin`.
The last verify is `attach-verify01.json`, PS c55stream/ocprobe0 on both.
The full restoration of the five files is to be carried out after the
experiments are complete.

## The exact next action

The user has been asked for a physical reboot of **both** phones and for the
return of the Wi-Fi daemon/Open4All. After that, check the changed startTick,
PS0, the unchanged candidate47 host SHA and originals 3. Do not start with
the old host34.

For each `--device e90` or `--device n95`:

```powershell
& 'C:\Program Files\LibreOffice\program\python.exe' -X utf8 tools/e90_task_session.py --device e90 --session work/evidence/e90/d0-20261003-clean34 --action d0-sequence --host-version 35 --artifact-proof docs/evidence/2026-10-03/d0-attach-base-v47-artifacts.json --tag attach-sequence02
```

For the N95, also replace the `e90` segment in the session path. `d0-sequence`
performs read-only stock clocks, inspect, DSP deploy/readback, create-only,
three normal RUNs. On a refusal it stops the subsequent RUNs and keeps the
journal. A new tag is required; old journals must not be overwritten.

After three clean D0 cycles: the D1 ring **16 KiB TOTAL**, ownership/cache/map
and repeated measurements; then D2. There is no data yet to complete these phases.

Regenerating the checkpoint: `tools/summarize_base_attach.py`.
Evidence: `docs/evidence/2026-10-03/base-attach-checkpoint.json`,
`processor-reload-native-audit.json`, `d0-attach-base-v47-artifacts.json`
and the four `*-source-guard.txt` files in the same directory.
