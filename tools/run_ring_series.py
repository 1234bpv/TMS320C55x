"""Run three bounded D1 series; stop at the first failure, without KILL."""
import argparse
import json
import re
import sys
from pathlib import Path

import e90_task_session
from prepare_stream import stock_clock_matches

ROOT = Path(__file__).resolve().parents[1]


def require_stock_clocks(report, directory, device):
    combined = "".join((directory / probe["path"]).read_text(encoding="ascii")
                       for probe in report["probes"])
    if not stock_clock_matches(combined, device):
        raise RuntimeError("clock probe completed but stock register measurements failed; stop before another RUN")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("e90", "n95"), required=True)
    parser.add_argument("--host-version", type=int, choices=(41, 42, 43, 46), default=46)
    parser.add_argument("--revision", type=int, choices=(54, 55, 56, 57, 61), default=61)
    parser.add_argument("--keep-awake", action="store_true")
    parser.add_argument("--clock-probe", choices=("ocprobe", "rdomain"), default="ocprobe")
    parser.add_argument("--tag-prefix", help="new evidence cohort for the same immutable artifact; existing tags are never overwritten")
    args = parser.parse_args()
    if (args.host_version == 46) != (args.revision == 61):
        parser.error("native ring requires host46/candidate61; legacy artifacts remain separate")
    prefix = args.tag_prefix or f"ring-r{args.revision}"
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", prefix):
        parser.error("tag prefix must contain lowercase letters, digits and hyphens")
    session = f"work/evidence/{args.device}/d0-20261003-clean34"
    boot = None
    def action(name, tag, command=None):
        nonlocal boot
        sys.argv = ["e90_task_session.py", "--device", args.device, "--session", session,
                    "--action", name, "--host-version", str(args.host_version), "--tag", tag]
        if command:
            sys.argv += ["--command", command]
        if args.keep_awake:
            sys.argv += ["--keep-awake"]
        sys.argv += ["--clock-probe", args.clock_probe]
        if boot is not None:
            sys.argv += ["--expected-boot", boot]
        e90_task_session.main()
        report = json.loads((ROOT / session / f"{tag}.json").read_text())
        assert report["complete"]
        if name == "clocks":
            require_stock_clocks(report, ROOT / session, args.device)
        for key in ("info_before", "info_after"):
            observed = next(line.split(" startTick ")[1] for line in report[key] if line.startswith("tick "))
            if boot is None:
                boot = observed
            assert observed == boot, "boot changed during D1"
    for series in range(1, 4):
        action("clocks", f"{prefix}-s{series}-clock-before")
        for batch in (1, 2, 8, 15):
            mode = "dmm-ring-native" if args.host_version >= 46 else "dmm-ring"
            action("run", f"{prefix}-s{series}-b{batch}", f"{mode} batch={batch} frames=120")
        action("clocks", f"{prefix}-s{series}-clock-after")
    print(f"{args.device}: three D1 series complete; boot={boot}")


if __name__ == "__main__":
    main()
