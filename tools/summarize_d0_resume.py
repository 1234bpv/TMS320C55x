"""Publish the bounded E90 continuation without ROM, binaries or device I/O."""
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "work/evidence/e90/d0-20261001"
OUT = ROOT / "docs/evidence/2026-10-01"


def main():
    proofs = {}
    names = []
    for tag in ("resume-verify01", "resume-clocks01", "resume-sequence01",
                "resume-recovery02", "resume-restore01", "resume-sequence02",
                "resume-recovery03", "resume-restore02", "livejournal-sis01",
                "host22-verify01", "host22-verify02", "message-diag01"):
        names.extend((tag + ".json", tag + "-transport.txt"))
    for tag in ("resume-sequence01", "resume-sequence02"):
        names.extend(tag + "-" + suffix + ".log" for suffix in
                     ("inspect", "create", "engine", "dsp"))
    names.extend(("resume-recovery02.log", "resume-recovery03.log"))
    names.extend("message-diag01-" + suffix + ".log" for suffix in
                 ("inspect", "create", "engine", "dsp", "message-stages"))
    for optional in ("final-recovery01", "final-restore01", "restore-r25-sis01", "final-verify01",
                     "native-copy-sis01", "host23-verify01", "host23-verify02", "native-reference01",
                     "native-preflight-restore01", "native-preflight-restore02", "native-copy-v24-sis01", "host24-verify01", "host24-verify02", "native-reference02", "native-reference03", "native-recovery01", "native-recovery02", "native-recovery-net01", "native-recovery03", "native-restore01", "exit-diag-sis01", "host25-deploy01", "host25-verify01", "host25-verify02", "exit-diag01", "exit-recovery01", "exit-recovery02", "exit-restore01", "host26-deploy01", "worker-msg01", "worker-msg02", "worker-recovery01", "worker-recovery02", "worker-restore01", "worker-restore02"):
        if (SESSION / (optional + ".json")).exists():
            names.append(optional + ".json")
            if optional != "native-recovery-net01" or (SESSION / (optional + "-transport.txt")).exists():
                names.append(optional + "-transport.txt")
            if (SESSION / (optional + ".log")).exists():
                names.append(optional + ".log")
    for tag in ("native-reference01", "native-reference02", "native-reference03"):
        for suffix in ("inspect", "engine", "dsp", "native-copy"):
            name = tag + "-" + suffix + ".log"
            if (SESSION / name).exists():
                names.append(name)
    for suffix in ("inspect", "create", "engine", "dsp", "exit-stages"):
        name = "exit-diag01-" + suffix + ".log"
        if (SESSION / name).exists():
            names.append(name)
    for tag in ("worker-msg01", "worker-msg02"):
        for suffix in ("inspect", "create", "engine", "dsp", "worker-message"):
            name = tag + "-" + suffix + ".log"
            if (SESSION / name).exists():
                names.append(name)
    for name in names:
        data = (SESSION / name).read_bytes()
        target = OUT / ("e90-d0-" + (name[:-4] + ".txt" if name.endswith(".log") else name))
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError("refuse to change published raw proof: " + str(target))
        target.write_bytes(data)
        proofs[name] = {"path": target.relative_to(ROOT).as_posix(),
                        "sha256": hashlib.sha256(data).hexdigest().upper()}

    def read(tag):
        return json.loads((SESSION / (tag + ".json")).read_text(encoding="utf-8"))

    runs = []
    for index, recovery in enumerate(("resume-recovery02", "resume-recovery03"), 1):
        log = (SESSION / (recovery + ".log")).read_text(encoding="ascii")
        frames = re.findall(r"^frame=(\d+) put=0/0 get=0/0 wall_us=(\d+)", log, re.M)
        errors = re.findall(r"^  result=0 expected=0 ticks=\d+ counts_per_ms=\d+ errors=0 stop=([01])$", log, re.M)
        sizes = re.findall(r"^SIZE frame=(\d+) input_bytes=512 output_bytes=512 returned_words=256 protocol=21 checked_payload_words=240$", log, re.M)
        if [f[0] for f in frames] != [str(n) for n in range(1, 9)] or sizes != [f[0] for f in frames] or errors != ["0"] * 7 + ["1"]:
            raise RuntimeError("the eight correct packets are not established")
        deletion = re.search(r"^delete=(-?\d+) status=(-?\d+)$", log, re.M)
        if not deletion or "QUARANTINE" not in log or "FINAL status=0" in log:
            raise RuntimeError("failed teardown must remain explicit")
        runs.append({"experimental_run": index,
                     "candidate_revision": 20 + index,
                     "host_version": 21, "protocol": 21,
                     "correct_packets": 8, "packet_bytes_each_direction": 512,
                     "delete_rc": int(deletion[1]), "delete_status": int(deletion[2]),
                     "accepted_d0": False, "FINAL_present": "FINAL status=" in log,
                     "quarantined": True,
                     "packet_wall_us": [int(f[1]) for f in frames],
                     "journal_proof": proofs[recovery + ".log"]})
    latest_restore = next(tag for tag in ("worker-restore02", "worker-restore01", "exit-restore01", "native-restore01", "native-preflight-restore02", "native-preflight-restore01", "final-restore01", "resume-restore02") if (SESSION / (tag + ".json")).exists())
    restored = read(latest_restore)
    if not restored["complete"] or not all(f["equal"] for f in restored["files"]):
        raise RuntimeError("exact three-file restoration missing")
    times = [t for run in runs for t in run["packet_wall_us"]]
    diag = (SESSION / "message-diag01-message-stages.log").read_text(encoding="ascii")
    if any(marker not in diag for marker in (
        "stage=3 size=256 protocol=15 result=1 env=000077e0",
        "raw_words=0000/0600/000f/0001/0000/77e0/0000/77e0",
        "message get submitted=-2", "delete=-2 status=-2", "QUARANTINE")):
        raise RuntimeError("message diagnostic not established")
    final_verified = read("final-verify01") if (SESSION / "final-verify01.json").exists() else None
    originals_restored = bool(final_verified and final_verified["complete"] and all(f["equal_original"] for f in final_verified["files"]))
    references = []
    native_run_count = 0
    for tag in ("native-reference01", "native-reference02", "native-reference03"):
        if (SESSION / (tag + ".json")).exists():
            entry = read(tag)
            native_journal = SESSION / (tag + "-native-copy.log")
            entry["RUN_observed"] = native_journal.exists() and "execute start=0 status=0" in native_journal.read_text(encoding="ascii")
            native_run_count += int(entry["RUN_observed"])
            references.append(entry)
    native_control = None
    if (SESSION / "native-reference03-native-copy.log").exists():
        control_log = (SESSION / "native-reference03-native-copy.log").read_text(encoding="ascii")
        control_frames = re.findall(r"^reference frame=(\d+) put=0/0 get=0/0 bytes=512 bad_words=0 wall_us=(\d+)$", control_log, re.M)
        if [frame[0] for frame in control_frames] != [str(i) for i in range(1, 9)] or "delete=-33 status=-2147483647" not in control_log or "QUARANTINE" not in control_log:
            raise RuntimeError("native control packet/failure evidence changed")
        native_control = {"experimental_RUN": 4, "host_version": 24, "correct_packets": 8,
                          "checked_words_per_frame": 256, "packet_bytes_each_direction": 512,
                          "packet_wall_us": [int(frame[1]) for frame in control_frames],
                          "delete_rc": -33, "delete_status": -2147483647,
                          "state_before_delete": 2, "state_after_delete": 3,
                          "FINAL_EXIT0": False, "live_journal_GET_succeeded": True,
                          "proof": proofs["native-reference03-native-copy.log"],
                          "limit": "Native code/data/relocations unchanged; narrows failure to host/setup/native path, without proving the specific cause."}
    exit_diagnostic = None
    exit_run_count = 0
    diagnostic_log = SESSION / "exit-diag01-exit-stages.log"
    if diagnostic_log.exists():
        log = diagnostic_log.read_text(encoding="ascii")
        exit_run_count = int("execute start=0 status=0" in log)
        frames = re.findall(r"^frame=(\d+) put=0/0 get=0/0 wall_us=(\d+)", log, re.M)
        stages = []
        for match in re.finditer(r"^EXITDIAG stage=(\d+) protocol=(\d+) result=(\d+) env=([0-9a-f]+) cmd=([0-9a-f]+) arg1=([0-9a-f]+) arg2=([0-9a-f]+)$", log, re.M):
            stage = int(match[1])
            ownership = re.search(rf"^EXITDIAG stage={stage} input_pending=(\d+) output_pending=(\d+) idle_input=(-?\d+) idle_output=(-?\d+) waits=(\d+) status=([0-9a-f]+)$", log, re.M)
            stages.append({"stage": stage, "protocol": int(match[2]), "get_result": int(match[3]),
                           "env": match[4], "cmd": match[5], "arg1": match[6], "arg2": match[7],
                           "input_pending": int(ownership[1]) if ownership else None,
                           "output_pending": int(ownership[2]) if ownership else None,
                           "idle_input": int(ownership[3]) if ownership else None,
                           "idle_output": int(ownership[4]) if ownership else None,
                           "waits": int(ownership[5]) if ownership else None,
                           "status": ownership[6] if ownership else None})
        deletion = re.search(r"^delete=(-?\d+) status=(-?\d+)$", log, re.M)
        exit_diagnostic = {"experimental_RUN": 5 if exit_run_count else None, "host_version": 25,
                           "RUN_observed": bool(exit_run_count), "correct_packet_transfers": len(frames),
                           "packet_wall_us": [int(f[1]) for f in frames], "stages": stages,
                           "delete_rc": int(deletion[1]) if deletion else None,
                           "delete_status": int(deletion[2]) if deletion else None,
                           "quarantined": "QUARANTINE" in log,
                           "FINAL_EXIT0": "FINAL status=0" in log,
                           "accepted_D0": False, "proof": proofs[diagnostic_log.name],
                           "limit": "The post-idle output reissue perturbs cleanup. Only clean delete proves final reclaim/idle/EXITACK; this diagnostic does not count toward three ordinary D0 cycles."}
    worker_controls = [read(tag) for tag in ("worker-msg01", "worker-msg02") if (SESSION / (tag + ".json")).exists()]
    restored_after_worker = bool(worker_controls and restored["utc"] > worker_controls[-1]["utc"])
    worker_pending = bool(worker_controls and not worker_controls[-1]["complete"] and not restored_after_worker)
    result = {
        "scope": "E90 D0 continuation; failed own-node and ROM-reference RUN; D1 hardware prohibited until D0 accepted",
        "ip": "192.168.3.21", "N95_connections": 0,
        "experimental_RUN_calls": 3 + native_run_count + exit_run_count, "initial_three_RUN_limit_hit": True,
        "limit_lifted_by_human": "HELP_NEEDED.md, decision passed via orchestrator 2026-10-01 23:22 local; a new documented hypothesis per RUN required",
        "accepted_consecutive_D0_cycles": 0,
        "required_consecutive_D0_cycles": 3, "runs": runs,
        "diagnostic_packet_wall_us": {"count": len(times), "median": statistics.median(times),
                                      "min": min(times), "max": max(times)},
        "timing_limit": "Correct packet timings from failed lifecycle runs are diagnostics, not accepted D1 latency or application speedup.",
        "clock_kHz_from_read_only_registers": {"ARM": 330240, "bus": 110080, "DSP": 220160},
        "PRCM_writes": False, "phone_process_KILL_calls": 0,
        "third_RUN_message_diagnostic": {
            "host_version": 22, "candidate_revision": 24, "protocol": 15,
            "three_STRM_snapshots": True, "NODE_getMsg_timeout0_result": 0,
            "NODE_putMsg_timeout0_result": 1, "fromDSP_count": 1,
            "fromDSP_empty_at_snapshot": 1,
            "record_ror16": {"cmd": "00000600", "arg1": "000F0001", "arg2": "000077E0", "source": "000077E0"},
            "host_message_get_rc": -2, "state_before_delete": 3, "delete_rc": -2,
            "live_journal_GET_succeeded": True, "FINAL_EXIT0": False,
            "proof": proofs["message-diag01-message-stages.log"],
            "limit": "A valid DSP record is not proof of ARM reader flags, IRQ/DFC execution, or successful EXITACK delivery.",
        },
        "recoveries": [read("resume-recovery02"), read("resume-recovery03")],
        "last_exact_research_file_restore": restored,
        "original_host_restored": originals_restored,
        "final_verified": final_verified,
        "host22_delivery": read("livejournal-sis01"),
        "host22_GET_verified": read("host22-verify02"),
        "ROM_reference_controls": references,
        "fourth_RUN_ROM_reference": native_control,
        "fifth_RUN_RMS_EXIT_diagnostic": exit_diagnostic,
        "host25_SIS_delivery": read("exit-diag-sis01") if (SESSION / "exit-diag-sis01.json").exists() else None,
        "host25_GET_verified": next((read(tag) for tag in ("host25-verify02", "host25-verify01") if (SESSION / (tag + ".json")).exists()), None),
        "host25_direct_deployment": read("host25-deploy01") if (SESSION / "host25-deploy01.json").exists() else None,
        "host26_direct_deployment": read("host26-deploy01") if (SESSION / "host26-deploy01.json").exists() else None,
        "created_worker_message_controls": worker_controls,
        "created_worker_controls_accepted_as_D0": False,
        "post_RUN5_recovery": read("exit-recovery02") if (SESSION / "exit-recovery02.json").exists() else None,
        "direct_EXE_hash_replacement_authorized": "HELP_NEEDED.md 2026-10-02 13:38: human allows replacing our research EXE/hash without SIS installer",
        "research_files_restored_after_RUN5": (SESSION / "exit-restore01.json").exists(),
        "research_files_currently_restored": (not worker_controls or restored_after_worker) and latest_restore in ("exit-restore01", "worker-restore01", "worker-restore02"),
        "post_RUN4_recovery_attempts": [read(tag) for tag in ("native-recovery01", "native-recovery02", "native-recovery-net01", "native-recovery03") if (SESSION / (tag + ".json")).exists()],
        "research_files_restored_after_RUN4": (SESSION / "native-restore01.json").exists(),
        "native_copy_host23_SIS_delivery": read("native-copy-sis01") if (SESSION / "native-copy-sis01.json").exists() else None,
        "native_copy_host24_SIS_delivery": read("native-copy-v24-sis01") if (SESSION / "native-copy-v24-sis01.json").exists() else None,
        "pending": ("Created worker no-input create-only preflight failed delete -33/pending/state1 before MSG trigger; no new RUN. Manual E90 reboot/daemon required, then GET/PS0/exact originals restore. Host26 and finite-message diagnostic prepared; skip unproven no-input preflight. D0 0/3; D1 pending; HELP_NEEDED.md" if worker_pending else "RUN5 recovery GET/PS0 and exact originals restore verified. Diagnose outbound MSG and wrapper return; D0 0/3, D1 pending; HELP_NEEDED.md"),
        "D1": "No reserve/map/ring or new latency/bandwidth measurement; no proven negative zero-copy conclusion.",
        "D2": "Prior copy-channel calculation remains provisional; docs/PS1_CANDIDATES_2026-10-01.md",
        "proofs": proofs,
    }
    if (SESSION / "laptop-final-verify01.json").exists():
        from summarize_worker_messages import summarize
        current, summary_path = summarize()
        verified = read("laptop-final-verify01")
        result.update({"original_host_restored": True, "final_verified": verified,
                       "research_files_currently_restored": True,
                       "last_exact_research_file_restore": read("laptop-prearmed-restore01"),
                       "current_devices": current["current_devices"],
                       "finite_worker_message_diagnostics": current["attempts"],
                       "pending": current["next"] + " D0 0/3; D1 pending. No physical recovery currently required."})
        result["proofs"].update(current["proofs"])
        result["proofs"]["worker-message-checkpoint.json"] = {
            "path": summary_path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest().upper()}
        originals_restored = True
    (OUT / "e90-d0-resume-checkpoint.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(proofs)} raw proofs; {result['experimental_RUN_calls']} experimental RUN, D0 0/3; original host restored={originals_restored}.")


if __name__ == "__main__":
    main()
