"""Run three N95-only WSOLA ring63 series with strict stock/epoch brackets."""
import argparse
import json
import re
import sys

import e90_task_session
from run_ring_series import require_stock_clocks
from summarize_ring import ROOT, boot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag-prefix", default="wsola63-stock01")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.tag_prefix):
        parser.error("tag prefix must be a bounded lowercase identifier")
    directory = ROOT / "work/evidence/n95/d0-20261003-clean34"
    epoch = None
    def action(name, tag):
        nonlocal epoch
        sys.argv = ["e90_task_session.py", "--device", "n95", "--session", str(directory),
                    "--host-version", "48", "--action", name, "--tag", tag, "--keep-awake"]
        if epoch is not None:
            sys.argv += ["--expected-boot", epoch]
        if name == "run":
            sys.argv += ["--command", "dmm-ring-wsola frames=120"]
        e90_task_session.main()
        report = json.loads((directory / (tag + ".json")).read_text())
        assert report["complete"]
        if name == "clocks":
            require_stock_clocks(report, directory, "n95")
        for key in ("info_before", "info_after"):
            observed = boot(report, key)
            if epoch is None:
                epoch = observed
            assert observed == epoch, "daemon startup changed during the cohort"
    for series in range(1,4):
        prefix = f"{args.tag_prefix}-s{series}"
        action("clocks", prefix + "-clock-before")
        action("run", prefix + "-run")
        action("clocks", prefix + "-clock-after")
    print(f"N95: three WSOLA ring63 series complete; daemon_startup_tuple={epoch}")


if __name__ == "__main__":
    main()
