"""Publish distinct N95 DCR measurement, clock brackets and restoration."""
import json
import re
from pathlib import Path

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT, boot, digest, load, publish_text

DEST = ROOT / "docs/evidence/2026-10-04"
SESSION = ROOT / "work/evidence/n95/d0-20261003-clean34"


def main():
    tag = "dcr62-pilot-b15-f8-01"
    command = "dmm-ring-dcr batch=15 frames=8"
    report = load(SESSION / (tag + ".json"))
    journal = SESSION / (tag + ".log")
    log = journal.read_text(encoding="ascii")
    proof = load(DEST / "n95-dcr62-artifacts.json")
    assert report["complete"] and report["exit"] == ["EXIT 0 Kill"]
    assert digest(journal) == report["journal_sha256"]
    assert boot(report) == boot(report, "info_after") == "62209 boot 0 by n"
    hashes = {item["path"]: item["sha256"] for item in proof["files"]}
    assert report["host_sha256"] == hashes["out/arm/c55stream.exe"]
    assert report["dsp_sha256"] == hashes["out/dsp/c55stream-dmm-ring-dcr.dll55l"]
    validate_journal(log, command, 47)
    published = DEST / ("n95-" + tag + ".txt")
    journal_sha = publish_text(journal, published)
    readings = [{"frame": int(frame), "before": before, "after": after,
                 "WPE_before": int(wpe_before), "WPE_after": int(wpe_after)}
                for frame, before, after, wpe_before, wpe_after in re.findall(
                    r"DCR READ frame=(\d+) protocol=39 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01])", log)]
    clocks = []
    for position in ("before", "after"):
        clock = load(SESSION / f"dcr62-pilot-clock-{position}01.json")
        assert clock["complete"] and boot(clock) == boot(clock, "info_after") == boot(report)
        combined = ""
        probes = []
        for probe in clock["probes"]:
            source = SESSION / probe["path"]
            assert digest(source) == probe["sha256"]
            combined += source.read_text(encoding="ascii")
            target = DEST / ("n95-" + source.stem + ".txt")
            probes.append({"published_path": target.relative_to(ROOT).as_posix(),
                           "published_sha256": publish_text(source, target)})
        assert stock_clock_matches(combined, "n95") and clock["stock_verified"]
        clocks.append({"position": position, "stock_verified": True, "probes": probes})
    restore_source = SESSION / "dcr62-final-verify01.json"
    restoration = load(restore_source)
    assert restoration["complete"] and len(restoration["files"]) == 5
    assert all(item["equal_original"] for item in restoration["files"])
    assert restoration["c55stream_processes"] == restoration["ocprobe_processes"] == ["OK ps 0"]
    target = DEST / "n95-dcr62-final-verify01.json"
    result = {"scope": "distinct N95 candidate62/host47/protocol39 pilot; not candidate61 qualification",
              "status": "measurement_complete", "D1_status": "in_progress", "packets": 120,
              "frames": 8, "batch": 15, "command": command,
              "daemon_startup_tuple": boot(report), "startup_tuple_is_phone_boot_id": False,
              "host_sha256": report["host_sha256"], "DSP_sha256": report["dsp_sha256"],
              "published_journal": published.relative_to(ROOT).as_posix(), "published_sha256": journal_sha,
              "readings": readings, "WPE_disabled_for_all_samples": all(
                  reading["WPE_before"] == reading["WPE_after"] == 0 for reading in readings),
              "clock_brackets": clocks, "teardown": "clean native delete/free task/unmap/unreserve/free buffers/close/FINAL0/EXIT0",
              "restoration": {"utc": restoration["utc"], "published_path": target.relative_to(ROOT).as_posix(),
                              "published_sha256": publish_text(restore_source, target), "files": restoration["files"]},
              "instruction_audit": "docs/evidence/2026-10-04/n95-dcr62-instruction-audit.json",
              "limits": ["DCR measurements apply to this new pilot; historical candidate54/61 WPE remains unknown",
                         "DCR reads can perturb timing/ordering; do not merge pilot timings into original transport cohorts",
                         "non-posted mode identification does not alone document end-to-end OMAP2420 memory/notification ordering",
                         "no DCR/PRCM configuration writes or emulator changes; E90 deferred by user"]}
    output = DEST / "n95-dcr62-results.json"
    output.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(output)


if __name__ == "__main__":
    main()
