"""Validate published D0-D2 checkpoint and reproduce offline calculations."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/2026-10-01"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", action="store_true", help="also verify byte-exact proofs in the Git index")
    parser.add_argument("--artifacts", default="d0-worker-message-v37-artifacts.json", help="latest candidate; older artifact proofs remain historical")
    parser.add_argument("--python", default=sys.executable, help="interpreter for offline reproduction")
    options = parser.parse_args()
    python = Path(options.python)
    # LibreOffice's launcher reports the python-core directory as executable.
    if python.is_dir():
        python = python.parent / "python.exe"
    if not python.is_file():
        parser.error("Python executable not found; supply --python")
    features = json.loads((ROOT / "work/features.json").read_text(encoding="utf-8"))
    stages = features["current_assignment"]["stages"]
    if [(s["id"], s["status"]) for s in stages] != [("D0", "in_progress"), ("D1", "pending"), ("D2", "in_progress")]:
        raise RuntimeError("checkpoint must retain its unmet hardware criteria")
    for stage in stages:
        for path in stage["evidence"] + stage.get("finite_worker_evidence", []):
            if not (ROOT / path).is_file():
                raise FileNotFoundError(path)
    artifacts = read(options.artifacts)
    for entry in artifacts["files"]:
        data = (ROOT / entry["path"]).read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest().upper() != entry["sha256"]:
            raise RuntimeError("artifact/source drift: " + entry["path"])
    for name in ("e90-d0-session-checkpoint.json", "e90-d0-resume-checkpoint.json"):
        checkpoint = read(name)
        for entry in checkpoint["proofs"].values():
            if hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest().upper() != entry["sha256"]:
                raise RuntimeError("proof drift: " + entry["path"])
            if options.index:
                staged = subprocess.run(["git", "show", ":" + entry["path"]], cwd=ROOT,
                                        capture_output=True, timeout=15, check=True).stdout
                if hashlib.sha256(staged).hexdigest().upper() != entry["sha256"]:
                    raise RuntimeError("Git index changed exact proof bytes: " + entry["path"])
    if checkpoint["experimental_RUN_calls"] < 3 or checkpoint["accepted_consecutive_D0_cycles"] != 0 or checkpoint["phone_process_KILL_calls"] != 0:
        raise RuntimeError("RUN counts or failure ownership were incorrectly reported")
    for script, name in (("tools/rev/audit_e90_task.py", "e90-d0-d1-native-audit.json"),
                         ("tools/assess_ps1_candidates.py", "ps1-candidates-calculation.json"),
                         ("tools/rev/audit_dmm_reference.py", "e90-d0-dmm-ti-reference.json")):
        actual = json.loads(subprocess.run([str(python), script], cwd=ROOT, capture_output=True,
                                          text=True, encoding="utf-8", timeout=30, check=True).stdout)
        expected = read(name)
        actual.pop("utc", None)
        expected.pop("utc", None)
        if actual != expected:
            raise RuntimeError("offline reproduction drift: " + name)
    print("PASS source/artifact/proof hashes, D0-D2 evidence paths/statuses, native audit and candidate recalculation")


if __name__ == "__main__":
    main()
