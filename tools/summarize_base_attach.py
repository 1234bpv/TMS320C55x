"""Publish the guarded pre-RUN tests and current host35 device checkpoint."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from audit_processor_reload import build_report


def main():
    audit = build_report()
    destination = ROOT / "docs/evidence/2026-10-03"
    (destination / "processor-reload-native-audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    devices = {}
    for device in ("e90", "n95"):
        session = ROOT / f"work/evidence/{device}/d0-20261003-clean34"
        attempts = []
        for tag, host in (("sequence01", 34), ("attach-sequence01", 35)):
            report = json.loads((session / (tag + ".json")).read_text(encoding="utf-8"))
            if report["complete"] or [s["complete"] for s in report["steps"]] != [True, True, False]:
                raise ValueError("expected inspect/create success and guarded RUN refusal")
            logpath = session / (tag + "-run1.log")
            log = logpath.read_text(encoding="ascii")
            expected = ("ROUTING preflight env=000077e0 matching_queues=2 require_unique=1",
                        "ROUTING pre-RUN gate=-11 no_run_on_failure=1", "delete=0 status=0",
                        "free task=0", "free native out=0", "free native in=0", "BEGIN close")
            if any(marker not in log for marker in expected) or "BEGIN execute" in log or "QUARANTINE" in log:
                raise ValueError("RUN refusal and clean CREATED-node teardown missing")
            if log.splitlines()[-1] != "FINAL status=-11" or "EXIT -11 Kill" not in report["steps"][-1]["run_error"]:
                raise ValueError("expected source-collision error missing")
            if host == 35 and "BASE attach gate=0 reused_running=1 proc_load_calls=0" not in log:
                raise ValueError("host35 did not preserve the running base")
            target = destination / f"{device}-host{host}-source-guard.txt"
            target.write_bytes(logpath.read_bytes())
            attempts.append({"host": host, "journal": target.relative_to(ROOT).as_posix(),
                             "sha256": hashlib.sha256(logpath.read_bytes()).hexdigest().upper(),
                             "create_preflight": True, "official_run_calls": 0,
                             "source": "000077e0", "matching_queues": 2,
                             "created_node_cleanup": True, "exit_status": -11})
        verified = json.loads((session / "attach-verify01.json").read_text(encoding="utf-8"))
        if (not verified["complete"] or not all(f["equal_original"] for f in verified["files"][:3]) or
                not verified["installed_host_matches_built"] or
                verified["c55stream_processes"] != ["OK ps 0"] or
                verified["ocprobe_processes"] != ["OK ps 0"]):
            raise ValueError("restoration/deployment/process verification failed")
        before = re.findall(r"startTick (\d+)", "\n".join(verified["info_before"]))
        after = re.findall(r"startTick (\d+)", "\n".join(verified["info_after"]))
        if before != after or len(before) != 1:
            raise ValueError("verification changed daemon boot")
        devices[device] = {"session": session.relative_to(ROOT).as_posix(), "attempts": attempts,
                           "startTick": before[0], "original_dsp_and_logs_restored": True,
                           "installed_host": 35, "host_sha256": verified["files"][3]["sha256"],
                           "host_is_original": False, "active_research_processes": 0,
                           "original_exe_hash_backup": "original-3.bin / original-4.bin"}
    result = {"scope": "four guarded refusals; no new official RUN",
              "devices": devices, "accepted_d0_runs": 0,
              "next": "reboot both prepared phones; verify changed startTick; host35 d0-sequence attach-sequence02",
              "limits": ["host35 cannot repair ARM queues already made stale by an earlier PROC_Load",
                         "fresh-boot host35 routing and successful RUN teardown are not yet verified",
                         "D1 and D2 remain pending; DSP pre-return delay remains an unproven earlier hypothesis"]}
    output = destination / "base-attach-checkpoint.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    features = ROOT / "work/features.json"
    state = json.loads(features.read_text(encoding="utf-8"))
    assignment = state["current_assignment"]
    assignment["hardware_dependency"] = (
        "Both phones prepared and accessible; host34 RUN guard rejected duplicate source77E0 after clean create/delete/free. "
        "PROC_Load unconditionally stops/reloads the shared processor, confirmed offline on N95/E90. "
        "Host35/candidate47 attaches to the existing running base without PROC_Load; installed and create/delete/free tested. "
        "Old collisions remain from prior base reload, so another physical reboot with daemon/Open4All requested. "
        "Original DSP/log/clocklog restored; host35 intentionally installed, original EXE/hash backed up; PS0. "
        "Four guarded refusals invoke no official RUN. D0 0/3, D1 pending, D2 provisional. docs/BASE_ATTACH_2026-10-03.md")
    d0 = next(s for s in assignment["stages"] if s["id"] == "D0")
    d0["remaining"] = "After physical reboot: verify fresh startTick, exact host35 candidate47 and stock clocks; 3 clean official RUN cycles without resetting the shared DSP base. Restore all five originals after research."
    for evidence in ("docs/BASE_ATTACH_2026-10-03.md", "docs/evidence/2026-10-03/base-attach-checkpoint.json",
                     "docs/evidence/2026-10-03/processor-reload-native-audit.json",
                     "docs/evidence/2026-10-03/d0-attach-base-v47-artifacts.json"):
        if evidence not in d0["evidence"]:
            d0["evidence"].append(evidence)
    features.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
