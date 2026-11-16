"""Publish finite worker MSG diagnostics and exact restoration proofs, offline."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/evidence/2026-10-02"


def summarize():
    OUT.mkdir(parents=True, exist_ok=True)
    proofs = {}
    attempts = []
    restored = {}
    for device, session, prefix, final_tag, tags in (
        ("e90", "d0-20261001", "laptop-", "laptop-final-verify01",
         ("laptop-worker-msg01", "laptop-worker-queued01", "laptop-worker-prearmed27")),
        ("n95", "d0-20261002", "", "final-verify01", ("worker-msg02",)),
    ):
        directory = ROOT / "work/evidence" / device / session
        for local in sorted(directory.glob(prefix + "*")):
            if local.suffix not in (".json", ".txt", ".log"):
                continue
            target = OUT / (device + "-" + local.stem + (".txt" if local.suffix == ".log" else local.suffix))
            data = local.read_bytes()
            if target.exists() and target.read_bytes() != data:
                raise RuntimeError("published raw proof changed: " + str(target))
            target.write_bytes(data)
            proofs[device + "/" + local.name] = {
                "path": target.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(data).hexdigest().upper(),
            }
        final = json.loads((directory / (final_tag + ".json")).read_text())
        if (not final["complete"] or len(final["files"]) != 5 or
                not all(f["equal_original"] for f in final["files"]) or
                final["c55stream_processes"] != ["OK ps 0"] or
                final["ocprobe_processes"] != ["OK ps 0"]):
            raise RuntimeError("all five originals and PS0 required: " + device)
        tick = next(x for x in final["info_after"] if x.startswith("tick "))
        final_start = int(re.search(r"startTick (\d+)", tick)[1])
        restored[device] = {"utc": final["utc"], "daemon_startTick": final_start,
                            "all_five_files_GET_equal": True, "processes": {"c55stream": 0, "ocprobe": 0},
                            "proof": proofs[device + "/" + final_tag + ".json"]}
        for tag in tags:
            report = json.loads((directory / (tag + ".json")).read_text())
            step = next(s for s in report["steps"] if s["command"].startswith("worker-message"))
            local = directory / step["journal"]
            log = local.read_text(encoding="ascii")
            required = ("MSGWORKER trigger completion input=0/0 output=0/0",
                        "EXITDIAG stage=7 protocol=26 result=1 env=000077e0 cmd=00000606 arg1=a1b2c3d4 arg2=000077e0",
                        "MSGWORKER delivery=-33 overall=-33 no_run=1", "delete=0 status=0",
                        "free task=0", "free native out=0", "free native in=0", "BEGIN close", "FINAL status=-33")
            if any(marker not in log for marker in required) or "BEGIN execute" in log or "QUARANTINE" in log:
                raise RuntimeError("finite MSG failure with clean cleanup not proven: " + tag)
            before_tick = next(x for x in report["info_before"] if x.startswith("tick "))
            if int(re.search(r"startTick (\d+)", before_tick)[1]) != final_start:
                raise RuntimeError("daemon continuity changed: " + tag)
            raw = "message header=3000000c max=12 cmd=00000000 arg1=00000000 arg2=00000000"
            attempts.append({"device": device, "tag": tag, "host_version": report["host_version_expected"],
                             "receive_timing": "after output" if step["command"].endswith("queued") else "before input",
                             "DSP_NODE_putMsg_result": 1, "STRM_snapshot_received": True,
                             "ARM_receive": -33, "ARM_record_observed_empty": True if raw in log else None,
                             "created_delete_free_close_clean": True, "FINAL_EXIT0": False,
                             "official_RUN_calls": 0, "proof": proofs[device + "/" + local.name]})
    result = {"utc": max(x["utc"] for x in restored.values()),
              "attempts": attempts, "current_devices": restored, "proofs": proofs,
              "new_official_RUN_calls": 0, "phone_process_KILL_calls": 0, "PRCM_writes": False,
              "accepted_D0_cycles": 0, "D1_mapping_or_ring_tests": 0,
              "clock_kHz_from_registers": {"e90": {"ARM": 330240, "bus": 110080, "DSP": 220160},
                                           "n95": {"ARM": 426240, "bus": 213120, "DSP": 284160}},
              "conclusion": "Finite CREATED worker cleanup succeeds on both devices, while prearmed ARM MSG receive times out. E90 queued receive also times out. ARM record is empty in host27/28 observations. Exact ARM consumer execution, runtime reader flag, mapping and queue source remain unmeasured.",
              "next": "Audit a bounded read-only native snapshot of ARM window, reader flag and queue routing before another MSG/RUN experiment. Shared header changes alone do not establish the failing boundary."}
    target = OUT / "worker-message-checkpoint.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(proofs)} raw proofs; {len(attempts)} finite diagnostics; both devices PS0 and all five originals exact.")
    return result, target


if __name__ == "__main__":
    summarize()
