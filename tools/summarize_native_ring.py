"""Publish immutable candidate61 cohorts separately for each phone/boot."""
import argparse
import json
from pathlib import Path
import re

from summarize_ring import ROOT, DEST, boot, digest, load, publish_text, stats
from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("e90", "n95"), default="e90")
    parser.add_argument("--tag-prefix", default="ring-r61")
    parser.add_argument("--boot", default="60136 boot 0 by n")
    parser.add_argument("--dest", type=Path, default=DEST)
    parser.add_argument("--output", default="d1-native-ring-results.json")
    for device in ("e90", "n95"):
        parser.add_argument(f"--{device}-restoration-tag", default="native-ring61-final-verify01")
    args = parser.parse_args()
    device, dest = args.device, args.dest.resolve()
    dest.mkdir(parents=True, exist_ok=True)
    historical = device == "e90" and args.tag_prefix == "ring-r61"
    directory = ROOT / f"work/evidence/{device}/d0-20261003-clean34"
    proof = load(DEST / "d1-native-ring-v61-artifacts.json")
    hashes = {item["path"]: item["sha256"] for item in proof["files"]}
    expected_boot = args.boot
    runs, clocks = [], []
    for series in range(1, 4):
        for position in ("before", "after"):
            tag = f"{args.tag_prefix}-s{series}-clock-{position}"
            report = load(directory / (tag + ".json"))
            assert report["complete"] and boot(report) == boot(report, "info_after") == expected_boot
            probes = []
            combined = ""
            for probe in report["probes"]:
                source = directory / probe["path"]
                assert digest(source) == probe["sha256"]
                combined += source.read_text(encoding="ascii")
                published = dest / (device + "-" + source.stem + ".txt")
                probes.append({**probe, "published_sha256": publish_text(source, published),
                               "published_path": published.relative_to(ROOT).as_posix()})
            stock = stock_clock_matches(combined, device)
            hal_khz = [int(value) for value in re.findall(r"ECPUSpeed\(kHz\) = (\d+)", combined)]
            assert len(hal_khz) == (1 if report.get("clock_probe") == "rdomain" else 2)
            assert stock or (historical and hal_khz == [330000, 330000] and
                             combined.count("engine NOT ready: err -20 at step [patcher self-test]") == 2)
            clocks.append({"series": series, "position": position, "stock_verified": stock,
                           "probe_implementation": report.get("clock_probe", "ocprobe"),
                           "probe_executable_sha256": report.get("clock_probe_sha256"),
                           "HAL_CPU_kHz": hal_khz, "DSP_frequency_confirmed": stock,
                           "failure": None if stock else "ocprobe patcher self-test -20; no PRCM register measurements",
                           "probes": probes})
        for batch in (1, 2, 8, 15):
            tag = f"{args.tag_prefix}-s{series}-b{batch}"
            report = load(directory / (tag + ".json"))
            assert report["complete"] and report["exit"] == ["EXIT 0 Kill"]
            assert boot(report) == boot(report, "info_after") == expected_boot
            assert report["host_sha256"] == hashes["out/arm/c55stream.exe"]
            assert report["dsp_sha256"] == hashes["out/dsp/c55stream-dmm-ring.dll55l"]
            source = directory / (tag + ".log")
            assert digest(source) == report["journal_sha256"]
            text = source.read_text(encoding="ascii")
            validate_journal(text, f"dmm-ring-native batch={batch} frames=120", 46)
            frames = [[int(v) for v in row] for row in re.findall(
                r"^RING FRAME frame=(\d+) slot=(\d+) batch=(\d+) packet_start=(\d+) wall_us=(\d+) cpu_us=(\d+) bad_words=(\d+) dsp_ticks=(\d+)$", text, re.M)]
            assert len(frames) == 120
            for index, row in enumerate(frames):
                assert row[:4] == [index + 1, index * batch % 15, batch, index * batch]
                assert row[4] > 0 and row[5] >= 0 and row[6] == 0
            lifecycle = re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0", text)
            assert lifecycle
            pages = re.findall(r"^NATIVE PAGE phase=(\d+) index=(\d+) linear=([0-9a-f]+) physical=([0-9a-f]+)$", text, re.M)
            assert len(pages) == 8 and [row[1:] for row in pages[:4]] == [row[1:] for row in pages[4:]]
            published = dest / (device + "-" + tag + ".txt")
            runs.append({"series": series, "batch": batch, "packets": batch * 120,
                         "journal_sha256": digest(source), "published_journal": published.relative_to(ROOT).as_posix(),
                         "published_sha256": publish_text(source, published),
                         "wall_us": [row[4] for row in frames], "cpu_us": [row[5] for row in frames],
                         "dsp_ticks_unconverted": [row[7] for row in frames],
                         "setup_us": int(lifecycle[1]), "teardown_us": int(lifecycle[2]),
                         "pages_before_after": pages, "full_data_and_teardown": True,
                         "sequence_wrap": True, "counter_32bit_carry": True})
    aggregate = {}
    for batch in (1, 2, 8, 15):
        selected = [run for run in runs if run["batch"] == batch]
        wall = [v for run in selected for v in run["wall_us"]]
        cpu = [v for run in selected for v in run["cpu_us"]]
        aggregate[str(batch)] = {"series": len(selected), "exchange_wall_us": stats(wall),
                                "thread_cpu_us": stats(cpu), "thread_cpu_percent": 100 * sum(cpu) / sum(wall),
                                "useful_bidirectional_MB_s": len(wall) * batch * 960 / sum(wall),
                                "slot_bidirectional_MB_s": len(wall) * batch * 1024 / sum(wall),
                                "instrumented_S_us": stats([run["setup_us"] + run["teardown_us"] for run in selected])}
    restoration = {}
    for phone in ("e90", "n95"):
        tag = getattr(args, phone + "_restoration_tag")
        source = ROOT / f"work/evidence/{phone}/d0-20261003-clean34/{tag}.json"
        report = load(source)
        assert report["complete"] and report["c55stream_processes"] == report["ocprobe_processes"] == ["OK ps 0"]
        assert len(report["files"]) == 5 and all(item["equal_original"] for item in report["files"])
        assert boot(report) == boot(report, "info_after")
        name = f"{phone}-native-ring-final-verify.json" if historical else f"{phone}-{tag}.json"
        published = dest / name
        restoration[phone] = {"all_five_originals_equal": True, "utc": report["utc"], "files": report["files"],
                               "boot": boot(report), "published_path": published.relative_to(ROOT).as_posix(),
                               "published_sha256": publish_text(source, published)}
    native_query = {}
    queries = (("native-state60-query02", "processor-state", 45),
               ("native-state60-auto-boot01", "boot-info", 45)) if historical else ()
    for tag, command, version in queries:
        source = directory / (tag + ".log")
        report = load(source.with_suffix(".json"))
        assert report["complete"] and report["exit"] == ["EXIT 0 Kill"]
        assert digest(source) == report["journal_sha256"]
        validate_journal(source.read_text(encoding="ascii"), command, version)
        published = dest / ("e90-" + tag + ".txt")
        native_query[command] = {"published_path": published.relative_to(ROOT).as_posix(),
                                 "published_sha256": publish_text(source, published), "boot": boot(report)}
    result = {"stage": "D1", "hardware_series_status": "complete", "candidate": 61, "host_version": 46,
              "protocol": 38, "device": device, "cohort": args.tag_prefix, "mode": "dmm-ring-native",
              "completed_series": 3, "accepted_runs": len(runs), "packets": sum(run["packets"] for run in runs),
              "start_tick": expected_boot, "ring_total_bytes": 16384, "payload_bytes_per_slot": 480,
              "slots_per_direction": 15, "quantiles": "nearest rank", "bandwidth_unit": "decimal MB/s",
              "artifact_proof": "docs/evidence/2026-10-03/d1-native-ring-v61-artifacts.json",
              "clocks": clocks, "aggregate": aggregate, "runs": runs, "restoration": restoration,
              "native_query": native_query,
              "native_gate": "cached own-channel state1; retained own node state1/nonzero RMS MEM_valloc env; no global queue enumeration or RomPatcher read",
              "limits": ["page identity is bracketed before/after; native allocation remains retained throughout",
                         ("raw boot fields do not identify the previous reboot cause; uptime changed between candidate60 deployment and the first query, before START; manual versus automatic is unknown" if historical else
                          "all accepted run and clock brackets belong to the specified unchanged boot; they do not establish causes of other cohorts' reboots"),
                         "synthetic full-word verification/transform includes cache and stream notifications; it is not application H+D",
                         "restoration entries are dated snapshots; subsequent phone mutations must be read from the latest checkpoint",
                         "setup/teardown include evidence journaling; thread CPU excludes external fill/verify/journal; DSP ticks remain unconverted",
                         ("all six clock brackets report HAL330MHz but fail patcher self-test; DSP/bus clocks are unconfirmed for this cohort; earlier E90 cohorts remain separate" if historical else
                          "all six stock clock brackets passed; frequency qualification applies only to this phone/boot/cohort"),
                         "backing-memory and DSP publication contracts are tracked separately from the completed hardware series"]}
    assert len(runs) == 12 and result["packets"] == 9360
    path = dest / args.output
    path.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(path)


if __name__ == "__main__":
    main()
