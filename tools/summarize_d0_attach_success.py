"""Validate the two host35 fresh-boot D0 series and publish compact evidence."""
import hashlib
import json
import re
from pathlib import Path

from e90_task_session import validate_journal

ROOT = Path(__file__).resolve().parents[1]


def main():
    devices = {}
    for name, previous in (("e90", "33897"), ("n95", "64375")):
        session = ROOT / "work/evidence" / name / "d0-20261003-clean34"
        report = json.loads((session / "attach-sequence02.json").read_text())
        assert report["complete"] and report["accepted_runs"] == 3
        tick = next(line.split(" startTick ")[1] for line in report["info_before"] if line.startswith("tick "))
        assert tick.split()[0] != previous
        runs = []
        for step in report["steps"]:
            assert step["complete"] and step["exit"] == ["EXIT 0 Kill"]
            assert next(line.split(" startTick ")[1] for line in step["info_after"] if line.startswith("tick ")) == tick
            raw = (session / step["journal"]).read_bytes()
            log = (session / step["journal"]).read_text(encoding="ascii")
            validate_journal(log, step["command"], 35)
            if step["label"].startswith("run"):
                runs.append({"label": step["label"], "journal_sha256": hashlib.sha256(raw).hexdigest().upper(),
                             "total_us": int(re.search(r"STREAM PASS .*total_us=(\d+)", log)[1]),
                             "packet_wall_us": [int(v) for v in re.findall(r"^frame=\d+ .*wall_us=(\d+)", log, re.M)],
                             "frames": 8, "packet_bytes": 512, "payload_words_checked": 240,
                             "delete_free_close_final_exit": "all zero"})
        assert len(runs) == 3
        devices[name] = {"start_tick": tick, "accepted_consecutive_runs": 3,
                         "host_sha256": report["host_sha256"], "runs": runs}
    evidence = {"stage": "D0", "status": "complete", "host_version": 35,
                "candidate": 47, "base_reload_calls": 0, "devices": devices,
                "limit": "Packet-copy lifecycle only; not D1 shared-ring measurements or application speedup."}
    path = ROOT / "docs/evidence/2026-10-03/d0-attach-success.json"
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    features_path = ROOT / "work/features.json"
    features = json.loads(features_path.read_text(encoding="utf-8-sig"))
    assignment = features["current_assignment"]
    assignment["hardware_dependency"] = "Fresh reboot confirmed on both phones; host35/candidate47 D0 passed three consecutive ordinary RUN cycles on each. D1 hardware gate open; native allocation/map/ownership still to be verified. Original DLL/log/clocklog restored; host35 remains installed, original EXE/hash saved."
    d0 = next(stage for stage in assignment["stages"] if stage["id"] == "D0")
    d0.update(status="complete", accepted_runs=3, accepted_runs_per_device={"e90": 3, "n95": 3},
              experimental_run_calls_minimum=16, remaining="D0 complete on both phones. Restore original EXE/hash after research.")
    for item in (str(path.relative_to(ROOT)).replace("\\", "/"), "tools/summarize_d0_attach_success.py"):
        if item not in d0["evidence"]:
            d0["evidence"].append(item)
    next(stage for stage in assignment["stages"] if stage["id"] == "D1")["status"] = "in_progress"
    features_path.write_text(json.dumps(features, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
