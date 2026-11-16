"""Preserve a failed stream journal and optionally restore its backed-up DSP.

No START, WAIT or KILL is issued. A live c55stream process prevents restore.
Only the before/after DLL hashes from a completed prepare_stream run are accepted.
"""
import argparse
import contextlib
import datetime
import hashlib
import json
import pathlib
import re

from strict_net import Device

ROOT = pathlib.Path(__file__).resolve().parents[1]
DSP_REMOTE = "E:\\c55stream.dll55l"


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--device", choices=("n95", "e90"), required=True)
    parser.add_argument("--preparation", type=pathlib.Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--restore-dsp", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.tag):
        parser.error("tag must contain letters, digits, underscores and hyphens")
    preparation = json.loads(args.preparation.read_text(encoding="utf-8"))
    if (preparation.get("complete") is not True or
            preparation.get("device") != args.device or preparation.get("ip") != args.ip):
        parser.error("preparation must be complete and identify this device/IP")
    backups = [entry for entry in preparation["files"]
               if entry["remote"] == DSP_REMOTE and "backup" in entry]
    uploaded = [entry for entry in preparation["files"]
                if entry["remote"] == DSP_REMOTE and entry.get("equal") is True]
    if len(backups) != 1 or len(uploaded) != 1:
        parser.error("preparation must identify exactly one old and uploaded DSP")
    backup_path = (ROOT / backups[0]["backup"]).resolve()
    if not backup_path.is_relative_to(ROOT / "work/device-backups") and not backup_path.is_relative_to(ROOT / "work/evidence"):
        parser.error("backup must be inside this project's evidence or backup directory")
    original = backup_path.read_bytes()
    if len(original) != backups[0]["bytes"] or sha256(original) != backups[0]["sha256"]:
        parser.error("backup bytes/hash differ from preparation")
    directory = ROOT / "work/evidence" / args.device
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.glob(args.tag + "*")):
        parser.error("tag already exists; evidence is never overwritten")
    journal = directory / (args.tag + ".log")
    current = directory / (args.tag + "-current.dll55l")
    restored = directory / (args.tag + "-restored.dll55l")
    transport = directory / (args.tag + "-transport.txt")
    proof = directory / (args.tag + ".json")
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": args.device, "ip": args.ip, "restore_requested": args.restore_dsp,
        "journal_recovered": False, "dsp_restored": False, "complete": False,
    }
    try:
        with transport.open("x", encoding="utf-8") as output, contextlib.redirect_stdout(output):
            device = Device(args.ip, args.device)
            try:
                # Preserve evidence before even considering a mutation.
                device.get("E:\\c55stream.log", journal)
                data = journal.read_bytes()
                result["journal_recovered"] = True
                result["journal"] = {"path": journal.relative_to(ROOT).as_posix(),
                                     "bytes": len(data), "sha256": sha256(data)}
                device.get(DSP_REMOTE, current)
                current_hash = sha256(current.read_bytes())
                result["current_dsp"] = {"path": current.relative_to(ROOT).as_posix(),
                                         "bytes": current.stat().st_size, "sha256": current_hash}
                result["info"] = device.cmd("INFO")
                result["ps"] = device.cmd("PS c55stream*")
                if args.restore_dsp:
                    if any(line.startswith("1 ") for line in result["ps"]):
                        raise RuntimeError("c55stream is still live; journal saved, DSP restore withheld")
                    if current_hash not in (backups[0]["sha256"], uploaded[0]["sha256"]):
                        raise RuntimeError("phone DSP is neither the prepared diagnostic nor its backup")
                    if current_hash != backups[0]["sha256"]:
                        device.put(DSP_REMOTE, original)
                    device.get(DSP_REMOTE, restored)
                    if restored.read_bytes() != original:
                        raise RuntimeError("restored DSP readback differs from backup")
                    result["dsp_restored"] = True
                    result["restored_dsp"] = {"path": restored.relative_to(ROOT).as_posix(),
                                              "bytes": len(original), "sha256": sha256(original), "equal": True}
                    result["info_after"] = device.cmd("INFO")
                result["complete"] = True
            finally:
                device.close()
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        proof.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("RECOVERY " + str(proof) + " complete=" + str(result["complete"]))


if __name__ == "__main__":
    main()
