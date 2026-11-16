"""Publish small E90 session proofs; backups, firmware and binaries stay local."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "work/evidence/e90/d0-20261001"
OUT = ROOT / "docs/evidence/2026-10-01"


def main():
    def read(name):
        return json.loads((SESSION / name).read_text(encoding="utf-8"))
    names = ("snapshot01.json", "clocks01.json", "sis01.json", "sis02.json", "verify01.json",
             "clocks01-engine.log", "clocks01-dsp.log", "verify01-transport.txt", "installer01-transport.txt",
             "verify02.json", "verify02-transport.txt")
    proofs = {}
    for name in names:
        data = (SESSION / name).read_bytes()
        target = OUT / ("e90-d0-" + (name[:-4] + ".txt" if name.endswith(".log") else name))
        if target.exists():
            raise FileExistsError(target)
        target.write_bytes(data)
        proofs[name] = {"path": target.relative_to(ROOT).as_posix(),
                        "sha256": hashlib.sha256(data).hexdigest().upper()}
    snapshot, clocks, delivery, verified = (read(n) for n in
                                          ("snapshot01.json", "clocks01.json", "sis02.json", "verify01.json"))
    if not all(r["complete"] for r in (snapshot, clocks, delivery, verified)):
        raise RuntimeError("successful proofs required")
    if not all(f["equal_original"] for f in verified["files"]) or verified["installed_host_matches_v21"]:
        raise RuntimeError("checkpoint expects exact restored original files and host20")
    if any("startTick 75535" not in next(line for line in r["info_after"] if line.startswith("tick "))
           for r in (snapshot, clocks, delivery, verified)):
        raise RuntimeError("daemon continuity changed")
    transport = (SESSION / "verify01-transport.txt").read_text(encoding="utf-8")
    for process in ("c55stream", "ocprobe"):
        if f"> PS {process}*\n< OK ps 0\n" not in transport:
            raise RuntimeError("missing PS0")
    result = {
        "last_successful_verification_utc": verified["utc"], "device": "e90", "ip": "192.168.3.21",
        "d0_accepted_runs": 0, "d1_hardware_mapping_runs": 0, "d2": "provisional prior-copy-channel calculation",
        "clock_registers": {"CM_CLKSEL1_PLL": "00056400", "CM_CLKSEL2_PLL": "00000002",
                            "CM_CLKSEL_MPU": "00000002", "CM_CLKSEL1_CORE": "04360626",
                            "CM_CLKSEL_DSP": "00000343"},
        "clock_kHz_from_registers": {"ARM": 330240, "bus": 110080, "DSP": 220160},
        "all_five_original_files_GET_equal": True, "files": verified["files"],
        "processes": {"c55stream": 0, "ocprobe": 0}, "daemon_startTick": 75535,
        "new_phone_file": delivery["deployed"],
        "sis_first_attempt_error_before_PUT": read("sis01.json")["error"],
        "later_access_attempt": {"utc": "2026-10-01T19:10:31.633673+00:00",
                                 "result": "TimeoutError: timed out during socket.create_connection, timeout3s",
                                 "device_commands_sent": 0, "installer_opened": False},
        "second_access_attempt": read("verify02.json"),
        "proofs": proofs, "pending_physical_action": "Install host21 SIS and restore E90 daemon; work/HELP_NEEDED.md",
        "N95": "No connection; earlier idle-first/clock-log/research cleanup deferred to its assigned executor",
    }
    target = OUT / "e90-d0-session-checkpoint.json"
    with target.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2) + "\n")
    print(f"Published {len(proofs)} small proofs; five originals exact; D0/D1 hardware runs=0")


if __name__ == "__main__":
    main()
