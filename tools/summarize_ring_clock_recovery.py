"""Publish the E90 pre-DSP reboot/deployment boundary without vendor files."""
import json
from pathlib import Path

from summarize_ring import ROOT, boot, publish_text


def main():
    directory = ROOT / "work/evidence/e90/d0-20261003-clean34"
    dest = ROOT / "docs/evidence/2026-10-04"
    entries = []
    for tag in ("resume-oct04-final-verify01", "native61-oct04-stock01-host-deploy01",
                "native61-oct04-stock01-dsp-deploy01", "native61-oct04-stock01-pre-dsp-recovery01",
                "native61-oct04-stock01-reboot-info01", "rdomain-clock-deploy01",
                "rdomain-clock-deploy02", "rdomain-clock-deploy03",
                "rdomain-clock-pilot-recovery02", "rdomain-clock-deploy04"):
        source = directory / (tag + ".json")
        report = json.loads(source.read_text())
        published = dest / ("e90-" + tag + ".json")
        entries.append({"tag": tag, "complete": report["complete"],
                        "boot_before": boot(report) if "info_before" in report else None,
                        "boot_after": boot(report, "info_after") if "info_after" in report else None,
                        "published_path": published.relative_to(ROOT).as_posix(),
                        "published_sha256": publish_text(source, published)})
    journal = directory / "native61-oct04-stock01-reboot-info01.log"
    published = dest / "e90-native61-oct04-stock01-reboot-info01.txt"
    report = json.loads((directory / "native61-oct04-stock01-pre-dsp-recovery01.json").read_text())
    originals = json.loads((directory / "originals.json").read_text())
    assert report["dsp_sha256"] == originals["files"][0]["sha256"]
    assert all(not entry["complete"] for entry in entries if "clock-deploy" in entry["tag"])
    result = {"scope": "new E90 stock-qualified series has not started; current restoration remains pending connectivity",
              "events": entries, "new_dsp_runs": 0,
              "confirmed_automatic_reboot": {"before": "67736 boot 0 by n", "after": "60715 boot 0 by n",
                                            "boundary": "after clock02 and host46 deployment, before DSP delivery/START", "confirmation": "user reply"},
              "next_observed_boot": "93971 boot 0 by n",
              "next_boot_cause": "manual versus automatic unknown",
              "later_observed_daemon_start": "35467 boot 1 by t",
              "daemon_field_semantics": "startTick is daemon launch NTickCount; boot/by describe startup classification, not a unique phone boot identifier",
              "latest_reboot_investigation": "docs/evidence/2026-10-04/e90-daemon-reboot-audit.json",
              "recovered_dsp_equal_original": True,
              "reboot_journal": {"published_path": published.relative_to(ROOT).as_posix(),
                                 "published_sha256": publish_text(journal, published)},
              "latest_known_files": {"c55stream_host": "host46; boot-info executed successfully on60715; restore EXE/hash still pending",
                                     "c55stream_dsp": "original; new candidate61 DSP delivery never started",
                                     "ringclock": "absent; all four deploy attempts stopped before PUT",
                                     "ocprobe_exe": "unchanged original; separate ringclock target only",
                                     "owned_remote_screenshots_to_remove": ["E:\\codex-oct04-patches03.bmp", "E:\\codex-oct04-patches04.bmp", "E:\\codex-oct04-patches05.bmp"]},
              "next_step": "investigate the user-confirmed reboot with daemon logs and INFO-only observations before further KEY/SHOT/clock/DSP commands; E90 original-file restoration remains pending; compatible ringclock pilot and new native series remain conditional on recovery and validated clock gate",
              "limits": ["STAT−46 did not prove Open4All inactive; later screenshot showed it green; installer now uses exact-file LS",
                         "clock API mismatch is proved offline, but new compatible clock probe has only been built, not installed/run",
                         "five-original E90 verification was before the subsequent host46 redeployment; it is not current restoration proof",
                         "LS also returned -46 in deploy04 despite the preceding green Open4All screenshot",
                         "daemon startup fields alone do not prove a physical reboot; user observation and a decreasing system tick provide separate evidence",
                         "no reboot is attributed to DSP, driver conflict or clock probe without a causal diagnostic"]}
    path = dest / "e90-native61-oct04-recovery-checkpoint.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
