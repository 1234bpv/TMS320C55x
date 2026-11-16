"""Publish the saved N95 routing experiment; no phone access."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
session = ROOT / "work/evidence/n95/d0-20261003-codex-routing"
logfile = session / "routing02.log"
log = logfile.read_text(encoding="ascii")
if re.findall(r"^SIZE frame=(\d+) input_bytes=512 output_bytes=512 returned_words=256 protocol=21 checked_payload_words=240$", log, re.M) != [str(i) for i in range(1, 9)]:
    raise ValueError("eight packet sizes missing")
if "delete=-33 status=-2147483647" not in log or "QUARANTINE" not in log:
    raise ValueError("expected failed teardown missing")
snapshots = {}
for section in log.split("ROUTING phase=")[1:]:
    phase = section.split()[0]
    record = re.search(r"decoded=([0-9a-f]{8})/([0-9a-f]{8})/([0-9a-f]{8})/([0-9a-f]{8})", section)
    queues = re.findall(r"ROUTING queue\[(\d+)\]=([0-9a-f]{8}) source=([0-9a-f]{8}) node=([0-9a-f]{8})", section)
    if not record or "ROUTING snapshot=0 " not in section:
        raise ValueError("complete native routing snapshot missing")
    snapshots[phase] = {"record": dict(zip(("cmd", "arg1", "arg2", "source"), record.groups())),
                        "queues": [dict(zip(("index", "address", "source", "node"), q)) for q in queues]}
before = snapshots["before-delete"]["queues"]
duplicates = sorted({q["source"] for q in before if sum(x["source"] == q["source"] for x in before) > 1})
ack = snapshots["after-failed-delete"]["record"]
if duplicates != ["000077e0"] or ack != {"cmd": "40000000", "arg1": "00008000", "arg2": "00000000", "source": "000077e0"}:
    raise ValueError("collision/EXITACK observation changed")
restored = json.loads((session / "finalverify01.json").read_text())
if not restored["complete"] or not all(f["equal_original"] for f in restored["files"]):
    raise ValueError("N95 exact restoration missing")
result = {
    "scope": "one diagnostic official RUN on N95; not an accepted D0 cycle",
    "session": session.relative_to(ROOT).as_posix(),
    "journal_sha256": hashlib.sha256(logfile.read_bytes()).hexdigest().upper(),
    "diagnostic_only": True, "accepted_d0_runs": 0, "frames": 8,
    "duplicate_sources_before_delete": duplicates, "snapshots": snapshots,
    "inference": "first-match native routing can deliver this ACK to the older duplicate queue; a fresh-device test is still required",
    "n95_original_files_restored": True,
    "n95_reboot_required_for_clean_routing_test": True,
    "e90": "DLL/log/clocklog restored; EXE/hash restoration blocked by ERR open -46 after reboot",
    "limits": ["snapshots are not atomic", "PS0 is not proof that kernel DSP queues were released", "D1 and D2 remain pending"],
}
report = ROOT / "docs/evidence/2026-10-03/n95-message-routing-checkpoint.json"
report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(report)
