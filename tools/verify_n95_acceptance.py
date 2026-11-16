"""Verify N95 research acceptance from committed evidence only; never access a phone."""
import json
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import boot
from verify_ring_publication import ROOT,checked,verify_native


def read(entry): return checked(entry["path"],entry["sha256"])


def main():
    audit=json.loads((ROOT/"docs/evidence/2026-10-04/n95-acceptance-audit.json").read_text())
    assert audit["overall_goal_status"]=="in_progress"
    expected_statuses={"D0_normal_cycles":"proven_N95","D0_error_timeout_cancel_audit":"documented_with_limits",
                       "D1_mapping_and_repeated_measurements":"demonstrated_N95","D1_memory_contract":"unproven",
                       "D2_measured_verdict":"delivered_N95_measured_jobs","originals_restoration":"proven_N95_at_timestamp",
                       "E90_followup":"deferred_by_user"}
    assert {r["id"]:r["status"] for r in audit["requirements"]}==expected_statuses
    d0=audit["d0"]; summary=json.loads(read(d0["summary"])); sequence=json.loads(read(d0["sequence"]))
    assert summary["status"]=="complete" and summary["host_version"]==35 and summary["candidate"]==47
    n95=summary["devices"]["n95"]
    assert n95["accepted_consecutive_runs"]==sequence["accepted_runs"]==3 and sequence["complete"]
    assert sequence["host_version_expected"]==35 and sequence["device"]=="n95"
    assert n95["host_sha256"]==sequence["host_sha256"]
    proof=json.loads(read(d0["artifact_proof"]))
    assert next(f["sha256"] for f in proof["files"] if f["path"]=="out/arm/c55stream.exe")==sequence["host_sha256"]
    assert [s["label"] for s in d0["steps"]]==[s["label"] for s in sequence["steps"]]==["inspect","create","run1","run2","run3"]
    for entry,step in zip(d0["steps"],sequence["steps"]):
        text=read(entry["journal"]); assert entry["command"]==step["command"] and entry["journal"]["wire_sha256"]==step["sha256"]
        validate_journal(text,step["command"],35)
        assert step["complete"] and step["exit"]==["EXIT 0 Kill"]
        assert next(s.split(" startTick ")[1] for s in step["info_after"] if s.startswith("tick "))==boot(sequence)==n95["start_tick"]
        if not step["label"].startswith("run"): continue
        saved=next(r for r in n95["runs"] if r["label"]==step["label"])
        assert saved["journal_sha256"]==step["sha256"]
        assert saved["packet_wall_us"]==list(map(int,re.findall(r"^frame=\d+ .*wall_us=(\d+)",text,re.M)))
        assert saved["total_us"]==int(re.search(r"STREAM PASS .*total_us=(\d+)",text)[1])
        sizes=re.findall(r"^SIZE frame=(\d+) input_bytes=512 output_bytes=512 returned_words=256 protocol=21 checked_payload_words=240$",text,re.M)
        assert list(map(int,sizes))==list(range(1,9))
        assert all(s in text.splitlines() for s in ("delete=0 status=0","free task=0","free native out=0","free native in=0","BEGIN close","FINAL status=0"))
    assert len(d0["clocks"])==2 and stock_clock_matches(''.join(read(c) for c in d0["clocks"]),"n95")
    final=audit["final_state"]; verification=json.loads(read(final["verification"])); transport=read(final["transport"])
    assert verification["device"]=="n95" and verification["action"]=="verify" and verification["complete"]
    assert boot(verification)==boot(verification,"info_after")==n95["start_tick"]
    assert verification["c55stream_processes"]==verification["ocprobe_processes"]==["OK ps 0"]
    prior=json.loads((ROOT/"docs/evidence/2026-10-04/n95-wsola68-final-verify02.json").read_text())
    assert len(verification["files"])==len(final["originals"])==5
    assert verification["files"]==prior["files"]
    for row,original in zip(verification["files"],final["originals"]):
        assert row["equal_original"] and {k:row[k] for k in original}==original
    commands=[s[2:] for s in transport.splitlines() if s.startswith("> ")]
    assert all(c=="INFO" or c.startswith(("PS ","GET ")) for c in commands)
    assert [c[4:] for c in commands if c.startswith("GET ")]==[r["remote"] for r in verification["files"]]
    for entry in audit["inputs"].values(): read(entry)
    print("Verified published N95 D0 inspect/create/3 consecutive cycles/24 packets total and2 stock probes, fresh read-only5-original/PS0 checkpoint; unresolved gates preserved.")
    verify_native(ROOT/audit["inputs"]["native61"]["path"])
    import verify_ring_cpu_publication,verify_mdec_publication,verify_spu_publication
    import verify_wsola_current_publication,verify_offload_dependencies,verify_n95_arm_cache,verify_kernel_publish
    for module in (verify_ring_cpu_publication,verify_mdec_publication,verify_spu_publication,
                   verify_wsola_current_publication,verify_offload_dependencies,verify_n95_arm_cache,verify_kernel_publish): module.main()
    print("N95 evidence acceptance checks PASS; overall D0-D2 goal remains in_progress, DSP memory contract unproven and E90 deferred.")


if __name__=="__main__": main()
