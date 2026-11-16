"""Verify published D1 journals/checksums without phone or ignored work files."""
import hashlib
import math
import json
from pathlib import Path
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import stats

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/2026-10-03"


def checked(relative, sha):
    raw = (ROOT / relative).read_bytes()
    # Git checkout may use CRLF. Publication hash is canonical LF UTF-8.
    canonical = raw.replace(b"\r\n", b"\n")
    assert hashlib.sha256(canonical).hexdigest().upper() == sha, relative
    return canonical.decode("utf-8")


def verify_native(path=EVIDENCE / "d1-native-ring-results.json"):
    result = json.loads(path.read_text())
    device = result["device"]
    assert device in ("e90", "n95")
    assert result["candidate"] == 61 and result["host_version"] == 46
    assert (result["completed_series"], result["accepted_runs"], result["packets"]) == (3, 12, 9360)
    assert {(run["series"], run["batch"]) for run in result["runs"]} == {
        (series, batch) for series in (1, 2, 3) for batch in (1, 2, 8, 15)}
    for run in result["runs"]:
        text = checked(run["published_journal"], run["published_sha256"])
        validate_journal(text, f"dmm-ring-native batch={run['batch']} frames=120", 46)
        frames = [[int(v) for v in row] for row in re.findall(
            r"^RING FRAME frame=(\d+) slot=(\d+) batch=(\d+) packet_start=(\d+) wall_us=(\d+) cpu_us=(\d+) bad_words=(\d+) dsp_ticks=(\d+)$", text, re.M)]
        assert len(frames) == 120 and run["packets"] == run["batch"] * 120
        assert [row[4] for row in frames] == run["wall_us"]
        assert [row[5] for row in frames] == run["cpu_us"]
        assert [row[7] for row in frames] == run["dsp_ticks_unconverted"]
        pages = re.findall(r"^NATIVE PAGE phase=(\d+) index=(\d+) linear=([0-9a-f]+) physical=([0-9a-f]+)$", text, re.M)
        assert [list(row) for row in pages] == run["pages_before_after"]
        timing = re.search(r"RING LIFECYCLE setup_us=(\d+) teardown_us=(\d+) includes_journaling=1 status=0", text)
        assert [int(timing[1]), int(timing[2])] == [run["setup_us"], run["teardown_us"]]
    assert len(result["clocks"]) == 6
    for clock in result["clocks"]:
        text = "".join(checked(probe["published_path"], probe["published_sha256"]) for probe in clock["probes"])
        assert stock_clock_matches(text, device) == clock["stock_verified"]
        assert [int(value) for value in re.findall(r"ECPUSpeed\(kHz\) = (\d+)", text)] == clock["HAL_CPU_kHz"]
        if not clock["stock_verified"]:
            assert device == "e90" and path == EVIDENCE / "d1-native-ring-results.json"
            assert not clock["DSP_frequency_confirmed"] and clock["failure"]
            assert text.count("engine NOT ready: err -20 at step [patcher self-test]") == 2
    for batch, aggregate in result["aggregate"].items():
        selected = [run for run in result["runs"] if run["batch"] == int(batch)]
        wall = [v for run in selected for v in run["wall_us"]]
        cpu = [v for run in selected for v in run["cpu_us"]]
        assert aggregate["exchange_wall_us"] == stats(wall)
        assert aggregate["thread_cpu_us"] == stats(cpu)
        assert aggregate["useful_bidirectional_MB_s"] == len(wall) * int(batch) * 960 / sum(wall)
        assert aggregate["thread_cpu_percent"] == 100 * sum(cpu) / sum(wall)
    for restoration in result["restoration"].values():
        report = json.loads(checked(restoration["published_path"], restoration["published_sha256"]))
        assert report["complete"] and report["files"] == restoration["files"]
        assert len(report["files"]) == 5 and all(item["equal_original"] for item in report["files"])
        assert report["c55stream_processes"] == report["ocprobe_processes"] == ["OK ps 0"]
    for command, entry in result["native_query"].items():
        validate_journal(checked(entry["published_path"], entry["published_sha256"]), command, 45)
    if device == "n95":
        assert all(clock["stock_verified"] for clock in result["clocks"])
    print(f"Verified {device} native candidate61: 12 runs/9360 packets, page brackets, timings, explicit frequency status and five-original restorations.")


def main():
    result = json.loads((EVIDENCE / "d1-ring-results.json").read_text())
    runs, packets = 0, 0
    for label, device in result["devices"].items():
        for run in device["runs"]:
            text = checked(run["published_journal"], run["published_sha256"])
            validate_journal(text, f"dmm-ring batch={run['batch']} frames=120", device["host_version"])
            wall = [int(value) for value in re.findall(r"^RING FRAME .*wall_us=(\d+) ", text, re.M)]
            cpu = [int(value) for value in re.findall(r"^RING FRAME .*cpu_us=(\d+) ", text, re.M)]
            assert wall == run["wall_us"] and cpu == run["cpu_us"]
            assert "sequence_wrap=1" in text and "counter_32bit_carry=1" in text
            runs += 1
            packets += run["packets"]
        for clock in device["clocks"]:
            text = "".join(checked(probe["published_path"], probe["published_sha256"])
                           for probe in clock["probes"])
            assert stock_clock_matches(text, "n95" if label == "n95" else "e90")
    for label, filename in (("e90", "e90-ring-b8-recovered.txt"),
                            ("e90_candidate55", "e90-ring55-recovered.txt"),
                            ("e90_candidate56", "e90-ring56-recovered.txt")):
        failure = result["devices"][label]["interruption"]
        text = checked("docs/evidence/2026-10-03/" + filename, failure["published_sha256"])
        assert text.splitlines()[-1] == failure["last_journal_line"]
        assert "RING map=" not in text and "BEGIN create" not in text and "BEGIN execute" not in text
    for device in ("e90", "n95"):
        restoration = result["devices"][device]["restoration"]
        report = json.loads(checked(f"docs/evidence/2026-10-03/{device}-ring-final-verify.json",
                                    restoration["published_report_sha256"]))
        assert report["complete"] and report["c55stream_processes"] == ["OK ps 0"]
        assert len(report["files"]) == 5 and all(item["equal_original"] for item in report["files"])
    validate_journal(checked("docs/evidence/2026-10-03/e90-boot58-info.txt",
                             result["boot_probe58"]["published_sha256"]), "boot-info", 44)
    assert (runs, packets) == (21, 13320)
    print(f"Verified historical {runs} published runs/{packets} packets, clocks, interruption boundaries and historical restorations.")
    verify_native()
    verify_native(ROOT / "docs/evidence/2026-10-04/d1-n95-native-ring-results.json")
    audit = json.loads((ROOT / "docs/evidence/2026-10-04/e90-patcher-clock-recovery-audit.json").read_text())
    assert len(audit["variants"]) == 5
    for variant in audit["variants"]:
        assert variant["logical_channel"] == "RomPatcherPlus.Driver"
        assert (variant["getter_control"], variant["copy_control"], variant["free_shadow_control"]) == (
            (105, 102, 104) if variant["name"].startswith("RDomain") else (103, 105, 100))
    for clock in audit["clocks"]:
        text = "".join(checked(probe["published_path"], probe["published_sha256"]) for probe in clock["probes"])
        assert stock_clock_matches(text, "e90") == clock["stock_verified"]
    failed = checked(audit["own_ram_failure"]["published_path"], audit["own_ram_failure"]["published_sha256"])
    assert "destination=c0000000" in failed and failed.splitlines()[-1] == "FINAL status=-20"
    print("Verified five driver API contracts and the separate failed/recovered E90 clock boundary; loaded identity/reboot cause remain unproved.")
    reboot = json.loads((ROOT / "docs/evidence/2026-10-04/e90-daemon-reboot-audit.json").read_text())
    reports = {item["event"]: checked(item["path"], item["sha256"]) for item in reboot["reports"]}
    assert "< OK shot 844854 800x352 fb mode11" in reports["ui_completed"]
    assert "socket.create_connection" in reports["next_connection_failed"]
    assert not any(line.startswith("> ") for line in reports["next_connection_failed"].splitlines())
    boundary = checked(reboot["daemon_log"]["extract_path"], reboot["daemon_log"]["extract_sha256"])
    assert "[814919] client done\n[94415] === daemon start (tick=93682 boot=0 by=n) ===" in boundary
    assert reboot["next_attempt"]["commands_sent"] == 0 and reboot["daemon_log"]["fresh_fault_or_panic_reason"] is None
    print("Verified completed UI delivery, next-connect failure before commands, and separate system-tick reset evidence; reboot cause unknown.")
    dcr = json.loads((ROOT / "docs/evidence/2026-10-04/n95-dcr62-results.json").read_text())
    text = checked(dcr["published_journal"], dcr["published_sha256"])
    validate_journal(text, dcr["command"], 47)
    assert dcr["packets"] == 120 and len(dcr["readings"]) == 8
    records = re.findall(r"DCR READ frame=(\d+) protocol=39 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01])", text)
    assert [[str(row["frame"]), row["before"], row["after"], str(row["WPE_before"]), str(row["WPE_after"])] for row in dcr["readings"]] == [list(row) for row in records]
    assert dcr["WPE_disabled_for_all_samples"] and all(row[1:] == ("0000", "0000", "0", "0") for row in records)
    for clock in dcr["clock_brackets"]:
        assert stock_clock_matches("".join(checked(probe["published_path"], probe["published_sha256"]) for probe in clock["probes"]), "n95")
    restoration = dcr["restoration"]
    saved = json.loads(checked(restoration["published_path"], restoration["published_sha256"]))
    assert saved["complete"] and saved["files"] == restoration["files"] and all(item["equal_original"] for item in saved["files"])
    instructions = json.loads((ROOT / dcr["instruction_audit"]).read_text())
    assert instructions["helper_code_hex"] == "A45102004804" and instructions["helper_io_writes"] == 0
    assert instructions["DSP_sha256"] == dcr["DSP_sha256"]
    print("Verified distinct N95 DCR62 pilot: 120 packets, sixteen zero-WPE readings, two stock brackets and five-original restoration.")
    calculation = json.loads((ROOT / "docs/evidence/2026-10-04/ring-candidates-n95-native61-calculation.json").read_text())
    inputs = {path: json.loads(checked(path, sha)) for path, sha in calculation["source_sha256"].items()}
    n95 = inputs["docs/evidence/2026-10-04/d1-n95-native-ring-results.json"]
    e90 = inputs["docs/evidence/2026-10-03/d1-native-ring-results.json"]
    for scenario in calculation["conditional_synthetic_scenarios"]:
        aggregate = (n95 if scenario["device"] == "n95" else e90)["aggregate"][str(scenario["batch"])]
        t, s, a = aggregate["exchange_wall_us"]["p50"], aggregate["instrumented_S_us"]["p50"], scenario["A_us_scenario"]
        assert scenario["candidate"] == 61 and scenario["T_us_synthetic_scenario"] == t
        assert scenario["S_us_instrumented"] == s and scenario["W_strictly_greater_than_us"] == t + s/scenario["N"] - a
        assert scenario["minimum_N_setup_only"] == math.floor(s/a)+1
        assert scenario["blocking_gain_scenario"] == (t+s/scenario["N"] < a)
    print("Verified separate native61 D2 synthetic scenarios against source cohorts; application speedup remains unmeasured.")


if __name__ == "__main__":
    main()
