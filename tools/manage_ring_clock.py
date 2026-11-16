"""Install/remove only the exact separate ringclock artifact on the known E90."""
import argparse
import contextlib
import hashlib
import json
from pathlib import Path

from strict_net import Device

ROOT = Path(__file__).resolve().parents[1]
REMOTES = ("E:\\sys\\bin\\ringclock.exe", "C:\\sys\\hash\\ringclock.exe")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("deploy", "remove"))
    parser.add_argument("--tag", required=True)
    args = parser.parse_args()
    if not args.tag or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in args.tag):
        parser.error("use lowercase letters/digits/hyphens in the new tag")
    directory = ROOT / "work/evidence/e90/d0-20261003-clean34"
    if any(directory.glob(args.tag + "*")):
        parser.error("tag exists")
    proof = json.loads((ROOT / "docs/evidence/2026-10-04/ringclock-rdomain-artifacts.json").read_text())
    exe = (ROOT / "out/arm/ringclock.exe").read_bytes()
    assert hashlib.sha256(exe).hexdigest().upper() == proof["executable_sha256"]
    payloads = (exe, hashlib.sha1(exe).digest())
    report = {"action": args.action, "complete": False, "files": []}
    try:
        with (directory / (args.tag + "-transport.txt")).open("x", encoding="utf-8") as stream, contextlib.redirect_stdout(stream):
            d = Device("192.168.3.21", "e90", connect_timeout=8)
            try:
                report["info_before"] = d.cmd("INFO")
                for name in ("ringclock*", "ocprobe*", "c55stream*"):
                    assert d.cmd("PS " + name) == ["OK ps 0"]
                d.cmd("WAKE")
                # Open4All may permit GET/PUT while RFs::Entry (STAT) still
                # rejects sys paths. Match only these two exact filenames.
                states = [d.cmd("LS " + remote) for remote in REMOTES]
                report["files_before"] = states
                if args.action == "deploy":
                    assert states == [["OK ls 0"], ["OK ls 0"]], "refuse to overwrite existing files"
                # Check all existing files before deleting either one.
                for index, (remote, payload) in enumerate(zip(REMOTES, payloads)):
                    if args.action == "deploy":
                        d.put(remote, payload)
                    elif states[index] == ["OK ls 0"]:
                        report["files"].append({"remote": remote, "already_absent": True})
                        continue
                    local = directory / (args.tag + f"-readback-{index}.bin")
                    d.get(remote, local)
                    assert local.read_bytes() == payload, "refuse changed artifact: " + remote
                    report["files"].append({"remote": remote, "sha256": hashlib.sha256(payload).hexdigest().upper(), "equal": True})
                if args.action == "remove":
                    for remote in REMOTES:
                        if d.cmd("LS " + remote) != ["OK ls 0"]:
                            assert d.cmd("DEL " + remote) == ["OK 0"]
                        assert d.cmd("LS " + remote) == ["OK ls 0"]
                report["info_after"] = d.cmd("INFO")
                report["complete"] = True
            finally:
                d.close()
    finally:
        (directory / (args.tag + ".json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
