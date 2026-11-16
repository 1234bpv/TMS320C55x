"""Publish the last E90 UI-command boundary and the limited daemon audit."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/evidence/2026-10-04"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    successful = ROOT / "out/e90-oct04-patches05-capture.log"
    failed = ROOT / "out/e90-oct04-patches06-capture.log"
    recovery = ROOT / "out/e90-oct04-daemon-read01.log"
    daemon_log = ROOT / "out/e90-oct04-daemon-after-reboot01.log"
    good = successful.read_text(encoding="utf-8-sig")
    bad = failed.read_text(encoding="utf-8-sig")
    recovered = recovery.read_text(encoding="utf-8-sig")
    assert "EXIT_CODE=0" in good and "< OK key 0x11 x1" in good
    assert "< OK shot 844854 800x352 fb mode11" in good
    assert "> GET E:\\codex-oct04-patches05.bmp" in good
    assert "EXIT_CODE=1" in bad and "socket.create_connection" in bad
    assert not any(line.startswith("> ") for line in bad.splitlines())
    assert "EXIT_CODE=0" in recovered and "> GET E:\\ps1_daemon.log" in recovered
    text = daemon_log.read_bytes().decode("latin-1")
    last = text.rsplit("[807473] client connected", 1)[1]
    selected = ["[807473] client connected"] + [
        line for line in last.splitlines()
        if re.fullmatch(r"\[\d+\] (?:GET \d+ bytes rc=0|client done|client connected|=== daemon start .* ===|killed \d+ stale instance\(s\))", line)
    ]
    assert selected[:4] == ["[807473] client connected",
                           "[814907] GET 844854 bytes rc=0", "[814919] client done",
                           "[94415] === daemon start (tick=93682 boot=0 by=n) ==="]
    assert "[94463] killed 1 stale instance(s)" in selected
    extract = DEST / "e90-daemon-reboot-boundary.txt"
    extract.write_bytes(("\n".join(selected) + "\n").encode("utf-8"))
    reports = []
    for label, source in (("ui_completed", successful), ("next_connection_failed", failed),
                          ("daemon_journal_read", recovery)):
        published = DEST / ("e90-daemon-" + label + ".txt")
        published.write_bytes((source.read_text(encoding="utf-8-sig").rstrip() + "\n").encode("utf-8"))
        reports.append({"event": label, "path": published.relative_to(ROOT).as_posix(),
                        "sha256": sha(published)})
    sources = []
    for name, sections in (("tester_input.cpp", ["CmdKey", "RawKey", "WriteBmp", "CmdShot", "CmdInfo"]),
                           ("deploy_daemon.cpp", ["mainL", "spawnSuccessor"])):
        path = ROOT.parent / "SymbianDeployDaemon/src" / name
        code = path.read_text(encoding="utf-8-sig")
        sources.append({"path": "../SymbianDeployDaemon/src/" + name,
                        "sha256": sha(path), "sections_reviewed": sections})
        if name == "tester_input.cpp":
            key = code.split("static TInt CmdKey(", 1)[1].split("// --- TEXT", 1)[0]
            shot = code.split("static TInt CmdShot(", 1)[1].split("// --- вікна", 1)[0]
            assert "ResetMachine" not in key + shot
            assert "User::After(40 * 1000)" in key
            assert "RFbsSession::Disconnect()" in shot
        else:
            assert "g_startTick = User::NTickCount();" in code
    result = {
        "scope": "E90 reboot after UI inspection; no new DSP RUN or compatible clock-probe execution",
        "phone_reboot_confirmed_by": ["user observation", "decreasing system tick in recovered daemon log"],
        "completed_actions": ["INFO", "KEY down (one DownArrow press/release)",
                              "SHOT E:\\codex-oct04-patches05.bmp", "GET screenshot"],
        "next_attempt": {"command_intended": "KEY down press 2 150, then SHOT/GET",
                         "socket_connected": False, "commands_sent": 0},
        "daemon_log": {"raw_local_sha256": sha(daemon_log), "raw_bytes": daemon_log.stat().st_size,
                       "extract_path": extract.relative_to(ROOT).as_posix(), "extract_sha256": sha(extract),
                       "last_success_tick": 814919, "next_daemon_launch_tick": 93682,
                       "fresh_fault_or_panic_reason": None},
        "reports": reports, "local_source_review": sources,
        "findings": [
            "startTick is daemon launch NTickCount; boot/by are startup classification, not a unique phone boot identifier",
            "KEY down defaults to a DownArrow key-down/key-up pair with a 40ms gap; it does not hold the key indefinitely",
            "KEY and SHOT handlers contain no ResetMachine call; explicit REBOOT is a separate command not sent here",
            "SHOT used the framebuffer path through CFbsScreenDevice::GetScanLine; buffers are heap allocated, length checked during pixel conversion and deleted",
            "successful screenshot delivery and client-done preceded the reset; they do not exclude a delayed graphics/kernel failure",
            "new daemon startup kills stale daemon instances; this entry describes daemon processes, not a command to reset the phone"
        ],
        "limits": ["installed daemon executable has not been matched to reviewed local source",
                   "no crash dump or fresh panic category identifies the failing component",
                   "combined KEY/SHOT/GET history cannot isolate a trigger",
                   "clock-driver API mismatch is separately proved; it is not a proved reboot cause"],
        "next_step": "INFO-only stability observations and preserve daemon logs; then isolate individual UI commands with recorded timestamps before clock/DSP work"
    }
    path = DEST / "e90-daemon-reboot-audit.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
