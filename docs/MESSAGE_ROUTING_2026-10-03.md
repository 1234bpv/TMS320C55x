# Routing collision of DSP messages on the N95

A continuation after Gemini established a new fact: **PS0 does not mean the
absence of old kernel DSP nodes**. During the new diagnostic RUN on the N95,
two queues with the same source `000077E0` existed. The native consumer
selects the first match, so the correct EXITACK of the new node may reach
the old node. The collision is proven; a check of the full teardown after a
clean reboot is still needed.

## E90 recovery

The E90 responded at 12:08 UTC, PS c55stream/ocprobe0, startTick 33897.
The obtained journal of the last Gemini `create02` run ends at
`BEGIN select node`, before create/GetState/teardown. The hypothesis of a
failure in GetState is not confirmed by this journal.

The session `work/evidence/e90/d0-20261003-cycle2`, `codex-recover01` saved
the journal and the DSP SHA. `codex-restore01` returned the original
DLL/log/clocklog with a GET check. The restore host and the full verify were
rejected with `ERR open -46` on the GET of `C:\sys\bin\c55stream.exe`. The
EXE/hash remain unrestored until access through Open4All is returned. There
was no repeated RUN on the E90.

## New N95 experiment

Session `work/evidence/n95/d0-20261003-codex-routing`:

- The five originals were saved before the changes.
- Host33: inspect and create-only passed; delete/free/close/FINAL0.
- Clocks01: stock m86, ARM 330240 / BUS 165120 / DSP 220160 kHz, DSP
  divider 3; the stock guard was confirmed, and ocprobe.log was restored.
- Routing01 was rejected by the parser before the DSP because of a missing
  frameMode of the new mode. This was fixed; candidate43 must not be used for
  run-routing.
- Routing02, candidate44: official RUN, eight correct packets of 512 B, total
  2987 us; after that, delete −33/pending/quarantine.
- The journal was obtained before recovery. An authorized KILL removed the
  quarantined host; after that, restore02/hostrestore01/finalverify01
  confirmed all five originals and the absence of an active c55stream. This
  is not a clean D0 teardown.

## Observations before and after delete

Before delete, the queues in the pool were in this order:

| Queue | Source | PDD node | State / phase / timeout |
| --- | --- | --- | --- |
| 0, C81D0B78 | 000077E0 | C81CF8D0 | 2 / 2 / 00002710 |
| 1, C81AD478 | 00007700 | C81AD2B0 | 2 / 2 / 00002710 |
| 2, C81BE0C0 | 000077E0 | C81BBDE0 | 2 / 2 / FFFFFFFF |

The new candidate uses timeout FFFFFFFF. Already before its delete, there are
old queues with timeout 2710 and a duplicated env/source77E0.

After delete, the shared record decoded as
`40000000 / 00008000 / 00000000 / 000077E0`: the correct EXITACK/EOK/source.
In the old first node, env became 0, phase 6; in the new one, env remained
77E0, phase 6. Both were observed in PDD state 11. Two more queues appeared.
The host deleteStatus remained pending, LDD state 3.

The best current explanation: the ACK was matched with the old first queue,
and the new node did not receive the expected completion. The causality of
all earlier failures, the mechanism of the state 11 transition, and the
origin of each old node have not yet been established. The snapshot is
non-atomic.

## Static contract and changes

`tools/rev/audit_message_routing.py` checks 18 E90 PDD instructions, the BL
to the automatic delete, and list First() in the saved ROM dump.
Consumer: context+32→pool, pool+8→list, item+12→queue, queue+16→source,
queue+36→node; the first matching EXITACK itself calls delete. The phase 3
callback sets PDD state 3; phase 6 is delete completion. Gemini wrongly
equated phase 3/state 3 with the need for a repeated delete. The Task 3 user
journal also contains an LDD state, which differs from the PDD state.

Host33 removes Gemini's new NULL-status/two-delete path and adds bounded
read-only routing snapshots to the diagnostic `run-routing`. Host34
additionally obtains the native NodeInfo env before RUN and requires exactly
one matching kernel queue. On refusal it does not call RUN and removes its
own CREATED node. The guard does not change the kernel code, PRCM, or the
queue sources; it does not remove the old nodes. This is a protection
against the observed collision, not a proven completion of D0.

The DSP remains byte-for-byte candidate41/42 (`7E1D922E…`); for the next clean
probe only the host changes. The DSP delay before return remains Gemini's old
diagnostic hypothesis, not a proven mutex fix.

The runner now uses the correct EXE path for E90/N95, allows the necessary
N95 preflight/deploy actions, and collects clock probes for the selected
device. The validator rejects a diagnostic RUN as D0 and, for host34,
requires the unique-source guard before BEGIN execute. 13 offline tests pass.

## Continuation

**Update after preparing the phones:** the host34 guard was checked on both,
refusal before RUN with clean cleanup. An unconditional PROC_Load
stop/load/start was found. Host35 is already installed and works by
attaching to the current base. The current checkpoint and the next commands
are in [BASE_ATTACH_2026-10-03.md](BASE_ATTACH_2026-10-03.md). The plan for
host34 given below is historical.

1. N95 reboot/daemon; check the new startTick. Open4All on the E90 for
   restoring the EXE/hash and further deploy. Both actions have been
   requested from the user.
2. Backup/verify, host34+DSP41, create-only preflight. Before the next RUN the
   unique-source guard must pass; on refusal there is no new RUN.
3. One clean normal run-transfer probe. Only after confirmed
   delete/free/close/FINAL/EXIT0 — a series of three consecutive D0 cycles.
4. D1 (ring 16 KiB TOTAL) and D2 remain after D0.

Publication of the observations: `tools/summarize_message_routing.py`.
Evidence: `docs/evidence/2026-10-03/n95-message-routing-checkpoint.json` and
`docs/evidence/2026-10-03/message-routing-native-audit.json`.
