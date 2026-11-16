"""Validate D1 journals and publish measured, partial evidence."""
import hashlib
import json
import math
import re
from pathlib import Path

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/evidence/2026-10-03"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def publish_text(source, destination):
    # Original wire-file SHA remains separate from canonical Git text SHA.
    destination.write_bytes(source.read_text(encoding="utf-8").encode("utf-8"))
    return digest(destination)


def boot(report, key="info_before"):
    # Historical field name: this is the daemon's launch tick/startup flags,
    # not a unique phone boot ID. Changes still conservatively stop a series.
    return next(line.split(" startTick ")[1] for line in report[key] if line.startswith("tick "))


def stats(values):
    ordered = sorted(values)
    return {"count": len(values), "min": min(values), "mean": sum(values) / len(values),
            **{label: ordered[math.ceil(p * len(values)) - 1]
               for label, p in (("p50", .5), ("p95", .95), ("p99", .99))}, "max": max(values)}


def main():
    assert load(DEST / "d0-attach-success.json")["status"] == "complete"
    devices = {}
    for label, device, revision, version, expected_boot, accepted in (
            ("n95", "n95", 54, 41, "62209 boot 0 by n", 12),
            ("e90", "e90", 54, 41, "60327 boot 0 by n", 2),
            ("e90_candidate55", "e90", 55, 42, "33873 boot 1 by t", 2),
            ("e90_candidate56", "e90", 56, 43, "33372 boot 1 by t", 5)):
        proof = load(DEST / f"d1-ring-v{revision}-artifacts.json")
        hashes = {item["path"]: item["sha256"] for item in proof["files"]}
        directory = ROOT / f"work/evidence/{device}/d0-20261003-clean34"
        runs, aggregates, clocks = [], {}, []
        for series in range(1, 4):
            for position in ("before", "after"):
                tag = f"ring-r{revision}-s{series}-clock-{position}"
                path = directory / (tag + ".json")
                if not path.exists():
                    continue
                report = load(path)
                assert report["complete"] and boot(report) == boot(report, "info_after") == expected_boot
                combined = "".join((directory / probe["path"]).read_text(encoding="ascii") for probe in report["probes"])
                assert stock_clock_matches(combined, device)
                for probe in report["probes"]:
                    assert digest(directory / probe["path"]) == probe["sha256"]
                    published_probe = DEST / f"{device}-{Path(probe['path']).stem}.txt"
                    probe["published_sha256"] = publish_text(directory / probe["path"], published_probe)
                    probe["published_path"] = published_probe.relative_to(ROOT).as_posix()
                clocks.append({"series": series, "position": position, "stock_verified": True,
                               "probes": report["probes"]})
            for batch in (1, 2, 8, 15):
                tag = f"ring-r{revision}-s{series}-b{batch}"
                path = directory / (tag + ".json")
                if not path.exists() or not load(path)["complete"]:
                    continue
                report = load(path)
                assert report["exit"] == ["EXIT 0 Kill"]
                assert boot(report) == boot(report, "info_after") == expected_boot
                assert report["host_sha256"] == hashes["out/arm/c55stream.exe"]
                assert report["dsp_sha256"] == hashes["out/dsp/c55stream-dmm-ring.dll55l"]
                log_path = directory / (tag + ".log")
                assert digest(log_path) == report["journal_sha256"]
                published = DEST / f"{device}-{tag}.txt"
                published_sha = publish_text(log_path, published)
                log = log_path.read_text(encoding="ascii")
                validate_journal(log, f"dmm-ring batch={batch} frames=120", version)
                assert "sequence_wrap=1" in log and "counter_32bit_carry=1" in log
                frames = [[int(v) for v in match] for match in re.findall(
                    r"^RING FRAME frame=(\d+) slot=(\d+) batch=(\d+) packet_start=(\d+) wall_us=(\d+) cpu_us=(\d+) bad_words=(\d+) dsp_ticks=(\d+)$", log, re.M)]
                assert len(frames) == 120
                for index, row in enumerate(frames):
                    assert row[:4] == [index + 1, (index * batch) % 15, batch, index * batch]
                    assert row[4] > 0 and row[5] >= 0 and row[6] == 0
                lifecycle = re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0", log)
                assert lifecycle
                pages = re.findall(r"DMM PAGE index=(\d+) linear=([0-9a-f]+) physical=([0-9a-f]+) expected_physical=([0-9a-f]+)", log)
                assert len(pages) == 4 and all(row[2] == row[3] for row in pages)
                runs.append({"series": series, "batch": batch, "packets": 120 * batch,
                             "journal_sha256": digest(log_path), "source": log_path.relative_to(ROOT).as_posix(),
                             "published_journal": published.relative_to(ROOT).as_posix(),
                             "published_sha256": published_sha,
                             "wall_us": [row[4] for row in frames], "cpu_us": [row[5] for row in frames],
                             "dsp_ticks_unconverted": [row[7] for row in frames],
                             "setup_us": int(lifecycle[1]), "teardown_us": int(lifecycle[2]),
                             "pages": pages, "sequence_wrap": True, "counter_32bit_carry": True,
                             "full_data_and_teardown": True})
        for batch in (1, 2, 8, 15):
            selected = [run for run in runs if run["batch"] == batch]
            if not selected:
                continue
            wall = [value for run in selected for value in run["wall_us"]]
            cpu = [value for run in selected for value in run["cpu_us"]]
            aggregates[str(batch)] = {"series": len(selected), "exchange_wall_us": stats(wall),
                                     "thread_cpu_us": stats(cpu), "thread_cpu_percent": 100 * sum(cpu) / sum(wall),
                                     "useful_bidirectional_MB_s": len(wall) * batch * 960 / sum(wall),
                                     "slot_bidirectional_MB_s": len(wall) * batch * 1024 / sum(wall),
                                     "instrumented_S_us": stats([run["setup_us"] + run["teardown_us"] for run in selected])}
        assert len(runs) == accepted
        completed = sum(all(any(run["series"] == series and run["batch"] == batch for run in runs)
                            for batch in (1, 2, 8, 15)) and
                        all(any(clock["series"] == series and clock["position"] == position for clock in clocks)
                            for position in ("before", "after")) for series in range(1, 4))
        devices[label] = {"candidate": revision, "host_version": version,
                           "completed_series": completed,
                           "accepted_runs": len(runs), "packets": sum(run["packets"] for run in runs),
                           "start_tick": expected_boot, "clocks": clocks, "aggregate": aggregates, "runs": runs}
    recovery_path = ROOT / "work/evidence/e90/d0-20261003-clean34/ring-recovery03.json"
    recovery = load(recovery_path)
    recovery_log = recovery_path.parent / recovery["journal"]
    text = recovery_log.read_text(encoding="ascii")
    assert recovery["complete"] and recovery["c55stream_processes"] == ["OK ps 0"]
    assert boot(recovery) != devices["e90"]["start_tick"]
    assert "RING" not in text and "BEGIN create" not in text and "FINAL" not in text
    compact = DEST / "e90-ring-b8-recovered.txt"
    compact_sha = publish_text(recovery_log, compact)
    devices["e90"]["interruption"] = {"command": "dmm-ring batch=8 frames=120",
                                      "last_journal_line": text.splitlines()[-1],
                                      "journal_sha256": digest(recovery_log), "published_sha256": compact_sha, "recovered_boot": boot(recovery),
                                      "observed": "transport lost; changed boot; recovered journal ends in initial read-only routing snapshot before ring allocation, map, own task create or RUN",
                                      "cause": "unknown; do not replay unchanged", "post_recovery_ps": "0"}
    recovery55 = load(ROOT / "work/evidence/e90/d0-20261003-clean34/ring55-recovery02.json")
    recovered55_log = ROOT / "work/evidence/e90/d0-20261003-clean34" / recovery55["journal"]
    text55 = recovered55_log.read_text(encoding="ascii")
    assert recovery55["complete"] and recovery55["c55stream_processes"] == ["OK ps 0"]
    assert "DMM POOLS" in text55 and "RING map=" not in text55 and "BEGIN create" not in text55
    published55_sha = publish_text(recovered55_log, DEST / "e90-ring55-recovered.txt")
    devices["e90_candidate55"]["interruption"] = {
        "command": "dmm-ring batch=8 frames=120", "cause": "unknown; transport lost again",
        "last_seen_boot": "33873 boot 1 by t", "journal_recovered": True,
        "recovered_boot": boot(recovery55), "journal_sha256": digest(recovered55_log),
        "published_sha256": published55_sha,
        "last_journal_line": text55.splitlines()[-1], "before_mapping_and_own_RUN": True,
        "hypothesis_result": "removing foreign-node dereference did not prevent recurrence; do not replay unchanged"}
    recovery56 = load(ROOT / "work/evidence/e90/d0-20261003-clean34/ring56-recovery02.json")
    recovered56_log = ROOT / "work/evidence/e90/d0-20261003-clean34" / recovery56["journal"]
    text56 = recovered56_log.read_text(encoding="ascii")
    assert recovery56["complete"] and recovery56["c55stream_processes"] == ["OK ps 0"]
    assert "RING map=" not in text56 and "BEGIN create" not in text56 and "FINAL" not in text56
    published56_sha = publish_text(recovered56_log, DEST / "e90-ring56-recovered.txt")
    devices["e90_candidate56"]["interruption"] = {
        "command": "dmm-ring batch=2 frames=120", "series": 2, "cause": "unknown; transport lost",
        "last_seen_boot": "33372 boot 1 by t", "journal_recovered": True,
        "recovered_boot": boot(recovery56), "journal_sha256": digest(recovered56_log),
        "published_sha256": published56_sha,
        "last_journal_line": text56.splitlines()[-1], "before_mapping_and_own_RUN": True,
        "hypothesis_result": "user destination pre-touch and removal of broad board read allowed one full series, but recurrence in next series; stability not established"}
    for device in ("n95", "e90"):
        directory = ROOT / f"work/evidence/{device}/d0-20261003-clean34"
        verify = directory / ("ring-final-verify01.json" if device == "n95" else "boot58-final-verify01.json")
        if verify.exists() and load(verify)["complete"]:
            report = load(verify)
            assert len(report["files"]) == 5 and all(item["equal_original"] for item in report["files"])
            assert report["c55stream_processes"] == ["OK ps 0"]
            devices[device]["restoration"] = {"all_five_originals_equal": True, "files": report["files"],
                                              "report_sha256": digest(verify), "boot": boot(report)}
            devices[device]["restoration"]["published_report_sha256"] = publish_text(verify, DEST / f"{device}-ring-final-verify.json")
        else:
            devices[device]["restoration"] = {"all_five_originals_equal": False,
                                              "previous_five_originals_verified_before_candidate56": True,
                                              "remaining": "candidate56 installed; latest run outcome unknown; GET journal/PS before restore; physical recovery requested"}
    devices["e90_candidate55"]["restoration"] = devices["e90"]["restoration"]
    devices["e90_candidate56"]["restoration"] = devices["e90"]["restoration"]
    boot_path = ROOT / "work/evidence/e90/d0-20261003-clean34/boot58-info01.log"
    boot_report = load(boot_path.with_suffix(".json"))
    assert boot_report["complete"] and boot_report["exit"] == ["EXIT 0 Kill"]
    validate_journal(boot_path.read_text(encoding="ascii"), "boot-info", 44)
    assert digest(boot_path) == boot_report["journal_sha256"]
    boot_published_sha = publish_text(boot_path, DEST / "e90-boot58-info.txt")
    result = {"stage": "D1", "status": "in_progress", "candidate": 54, "host_version": 41,
              "protocol": 38, "quantiles": "nearest rank", "bandwidth_unit": "decimal MB/s",
              "ring_total_bytes": 16384, "control_bytes": 1024, "slots_per_direction": 15,
              "slot_bytes": 512, "payload_bytes_per_slot": 480,
              "extra_native_notification_allocations_bytes": 8192, "notification_bytes_per_exchange": 1024,
              "mapping_flags": 17, "mapped_DSP_byte_address": "00300000", "DSP_word_address": "00180000",
              "ownership": "whole 16KiB region; cache utility2 clean then invalidate before handoff and after output completion; ARM does not access ring while DSP owns it",
              "release_order": "delete -> free task -> unmap -> unreserve -> free native ring -> free notifications -> close",
              "devices": devices,
              "user_observation": "E90 reboots itself, daemon auto-starts, Open4All does not auto-start; confirmed by user. Transport-only/autolock explanation is insufficient.",
              "candidate57": "same host43 with acknowledged WAKE; only short batch8 frames8 passed. Long series cancelled after user confirmed automatic full phone reboot; originals restored.",
              "boot_probe58": {"host_version": 44, "journal_sha256": digest(boot_path),
                               "published_sha256": boot_published_sha,
                               "scope": "read-only HAL/UserHal, no DSP or patcher; performed after manual reboot",
                               "startup": 0, "exception": 156, "fault_signed": -1604135081,
                               "code": "00000000", "data": "00000480", "extra": "000005BC",
                               "limit": "getter return codes0; values uninterpreted, not cause proof for earlier automatic reboot"},
              "limits": ["latency includes cache utility, notification streams and DSP full input verification plus synthetic transform; not isolated H or application H+D",
                         "setup and teardown include synchronous evidence journaling; not production startup",
                         "thread CPU excludes fill/verify/journal outside exchange; ARM does no useful application W during wait",
                         "clocks read at series boundaries, not continuously locked; DSP ticks not converted using CLK_countspms",
                         "N95 completed three series; E90 candidate56 completed one full series and one additional run, then automatically rebooted before map/own RUN; three consecutive full series remain unproven",
                         "runtime CMM range/page provenance established; chunk attributes and an independent DSP cache/order contract remain partially inferred"]}
    path = DEST / "d1-ring-results.json"
    path.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    features_path = ROOT / "work/features.json"
    features = load(features_path)
    assignment = features["current_assignment"]
    assignment["hardware_dependency"] = (
        "D0 complete3/3 each; N95 D1 three full series. E90 candidate56 one full series plus one run, then automatic reboot confirmed by user; all failed journals end before map/own RUN in native-memory diagnostics. "
        "Both originals5 verified, PS0; no physical action currently needed. Do not replay unchanged. Safe reader contract, native chunk/DSP cache and application T/A/W incomplete.")
    d0, d1, d2 = assignment["stages"]
    assert [stage["id"] for stage in (d0, d1, d2)] == ["D0", "D1", "D2"]
    d0["remaining"] = "D0 complete on both; current D1 E90 recovery/originals restoration tracked in D1."
    d1.update(status="in_progress", measured_series={"n95_candidate54": 3, "e90_candidate56": 1},
              remaining="N95 three series verified; E90 automatic reboots at pre-RUN native-memory diagnostics, three consecutive series unproven. All journals recovered and originals5 restored both. Audit safe native reader/state/queue API before further E90 RUN; establish remaining native chunk attrs and DSP cache/publish contract.")
    for relative in ("docs/DMM_RING_2026-10-03.md", "docs/evidence/2026-10-03/d1-ring-results.json",
                     "docs/evidence/2026-10-03/e90-patcher-copy-audit.json", "tools/summarize_ring.py",
                     "tools/run_ring_series.py", "tools/rev/audit_patcher_copy.py"):
        if relative not in d1["evidence"]:
            d1["evidence"].append(relative)
    d2["remaining"] = "Conditional N95 synthetic-ring recalculation recorded; application-specific T/A/W, E90 stable D1 and remaining ownership/cache contract required. No application speedup claimed; emulator unchanged."
    for relative in ("tools/assess_ring_candidates.py", "docs/evidence/2026-10-03/ring-candidates-calculation.json"):
        if relative not in d2["evidence"]:
            d2["evidence"].append(relative)
    features_path.write_text(json.dumps(features, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)
    for device, data in devices.items():
        print(device, data["packets"], {batch: (round(item["exchange_wall_us"]["p50"]), round(item["useful_bidirectional_MB_s"], 3)) for batch, item in data["aggregate"].items()})


if __name__ == "__main__":
    main()
