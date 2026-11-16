"""Publish host29 read-copy evidence, pointer audit and exact E90 restoration."""
import hashlib
import json
from pathlib import Path
import re
import sys

from e90_task_session import validate_journal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from audit_arm_message_runtime import audit

SESSION = ROOT / "work/evidence/e90/d0-20261002-pointer"
OUT = ROOT / "docs/evidence/2026-10-02"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    check = json.loads((SESSION / "readcheck01.json").read_text(encoding="utf-8"))
    journal = (SESSION / "readcheck01.log").read_bytes()
    validate_journal(journal.decode("ascii"), "patcher-read-check", 29)
    if not check["complete"] or check["journal_sha256"] != hashlib.sha256(journal).hexdigest().upper():
        raise RuntimeError("successful read-copy journal/report mismatch")
    final = json.loads((SESSION / "resume-finalverify01.json").read_text(encoding="utf-8"))
    if (not final["complete"] or len(final["files"]) != 5 or
            not all(f["equal_original"] for f in final["files"]) or
            final["c55stream_processes"] != ["OK ps 0"] or final["ocprobe_processes"] != ["OK ps 0"]):
        raise RuntimeError("five restored originals and PS0 required")
    def start_tick(report):
        line = next(s for s in report["info_after"] if s.startswith("tick "))
        return int(re.search(r"startTick (\d+)", line)[1])
    if start_tick(check) != start_tick(final):
        raise RuntimeError("daemon continuity changed during restoration")
    proofs = {}
    for stem in ("snapshot01", "host29-deploy01", "readcheck01", "resume-reader01",
                 "resume-restore01", "resume-hostrestore01", "resume-finalverify01"):
        for suffix in (".json", "-transport.txt", ".log"):
            local = SESSION / (stem + suffix)
            if not local.exists():
                continue
            target = OUT / ("e90-pointer-" + stem + (".txt" if suffix == ".log" else suffix))
            data = local.read_bytes()
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError("published raw proof changed: " + str(target))
            target.write_bytes(data)
            proofs[local.name] = {"path": target.relative_to(ROOT).as_posix(),
                                 "sha256": hashlib.sha256(data).hexdigest().upper()}
    static = audit(ROOT / "work/evidence/e90/rom")
    (OUT / "e90-arm-message-pointer-audit.json").write_text(json.dumps(static, indent=2) + "\n", encoding="utf-8")
    result = {
        "utc": final["utc"], "scope": "E90 host29 copy check, static pointer audit, restoration; no new MSG/RUN",
        "read_copy": {"host": 29, "three_passes": True, "destination": "own process RAM",
                      "sources": ["own RAM", "803F7664 ROM reader code", "C8010B20 module BSS"],
                      "FINAL_EXIT": 0, "DSP_open": False, "kernel_code_writes": False, "PRCM_writes": False},
        "runtime_message_reader_observed": False,
        "runtime_message_context_root_verified": False,
        "E90_restoration": {"all_five_GET_equal": True, "host": 20,
                            "c55stream_processes": 0, "ocprobe_processes": 0,
                            "daemon_startTick": start_tick(final)},
        "N95": "No commands in this continuation; last verified restored host20/PS0 in worker-message-checkpoint.json",
        "new_official_RUN_calls": 0, "new_MSG_diagnostics": 0, "phone_KILL_calls": 0,
        "D0_accepted_cycles": 0, "historical_experimental_RUN_calls": 5,
        "D1": "pending D0", "D2": "provisional",
        "next": "Derive a live board/context root through an audited native object lookup, including allocation bounds and lifetime, before following the reader/window/queue pointers.",
        "proofs": proofs,
    }
    (OUT / "arm-message-runtime-checkpoint.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(proofs)} raw proofs; static audit {static['checked_instructions']} instructions; E90 five originals exact/PS0.")


if __name__ == "__main__":
    main()
