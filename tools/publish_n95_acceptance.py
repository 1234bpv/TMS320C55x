"""Publish original N95 D0 journals and a read-only final-state/requirements checkpoint."""
import hashlib
import json
import re

from e90_task_session import validate_journal
from prepare_stream import stock_clock_matches
from summarize_ring import ROOT,boot

DEST=ROOT/"docs/evidence/2026-10-04"
SESSION=ROOT/"work/evidence/n95/d0-20261003-clean34"


def sha(raw): return hashlib.sha256(raw).hexdigest().upper()


def publish(source,name):
    raw=source.read_bytes(); canonical=raw.replace(b"\r\n",b"\n")
    destination=DEST/name; destination.write_bytes(canonical)
    return dict(path=destination.relative_to(ROOT).as_posix(),sha256=sha(canonical),wire_sha256=sha(raw))


def existing(relative):
    raw=(ROOT/relative).read_bytes().replace(b"\r\n",b"\n")
    return dict(path=relative,sha256=sha(raw))


def main():
    summary=json.loads((ROOT/"docs/evidence/2026-10-03/d0-attach-success.json").read_text())
    sequence=json.loads((SESSION/"attach-sequence02.json").read_text())
    n95=summary["devices"]["n95"]
    assert summary["status"]=="complete" and sequence["complete"] and sequence["accepted_runs"]==3
    assert sequence["host_sha256"]==n95["host_sha256"] and boot(sequence)==n95["start_tick"]
    d0=dict(summary=existing("docs/evidence/2026-10-03/d0-attach-success.json"),
            artifact_proof=existing("docs/evidence/2026-10-03/d0-attach-base-v47-artifacts.json"),
            sequence=publish(SESSION/"attach-sequence02.json","n95-d0-acceptance-sequence.json"),steps=[],clocks=[])
    for step in sequence["steps"]:
        source=SESSION/step["journal"]; assert sha(source.read_bytes())==step["sha256"]
        validate_journal(source.read_text(),step["command"],35)
        assert step["complete"] and step["exit"]==["EXIT 0 Kill"]
        assert next(s.split(" startTick ")[1] for s in step["info_after"] if s.startswith("tick "))==n95["start_tick"]
        d0["steps"].append(dict(label=step["label"],command=step["command"],journal=publish(source,"n95-d0-"+step["label"]+".txt")))
    for clock in sequence["clock_probes"]:
        source=SESSION/clock["path"]; assert sha(source.read_bytes())==clock["sha256"]
        d0["clocks"].append(publish(source,"n95-d0-"+source.stem.rsplit("-",1)[1]+"-clock.txt"))
    assert stock_clock_matches(''.join((ROOT/c["path"]).read_text() for c in d0["clocks"]),"n95")
    verification=json.loads((SESSION/"n95-acceptance-verify01.json").read_text())
    original=json.loads((SESSION/"originals.json").read_text())
    assert verification["complete"] and verification["action"]=="verify" and verification["device"]=="n95"
    assert boot(verification)==boot(verification,"info_after")==n95["start_tick"]
    assert verification["c55stream_processes"]==verification["ocprobe_processes"]==["OK ps 0"]
    assert len(verification["files"])==5
    for i,row in enumerate(verification["files"]):
        saved=next(f for f in original["files"] if f["remote"]==row["remote"])
        raw=(SESSION/f"n95-acceptance-verify01-file-{i}.bin").read_bytes()
        assert row["equal_original"] and row["sha256"]==saved["sha256"]==sha(raw) and row["bytes"]==saved["bytes"]==len(raw)
    transport=(SESSION/"n95-acceptance-verify01-transport.txt").read_text()
    commands=[s[2:] for s in transport.splitlines() if s.startswith("> ")]
    assert len([c for c in commands if c.startswith("GET ")])==5
    assert all(c=="INFO" or c.startswith(("PS ","GET ")) for c in commands)
    final=dict(verification=publish(SESSION/"n95-acceptance-verify01.json","n95-acceptance-final-verify.json"),
               transport=publish(SESSION/"n95-acceptance-verify01-transport.txt","n95-acceptance-final-transport.txt"),
               originals=[{k:row[k] for k in ("remote","bytes","sha256")} for row in verification["files"]])
    requirement=(ROOT/"work/CODEX_TASK_2026-10-01.md").read_bytes()
    text=requirement.decode("utf-8"); assert all(s in text for s in ("D0. Безпечне завершення.","D1. Канал без копіювання.","D2. Рішення для емулятора.","Реалізацію в емуляторі не роби"))
    inputs={key:existing(path) for key,path in (
        ("native61","docs/evidence/2026-10-04/d1-n95-native-ring-results.json"),
        ("CPU64","docs/evidence/2026-10-04/n95-ring-cpu64-results.json"),
        ("MDEC66","docs/evidence/2026-10-04/n95-mdec66-results.json"),
        ("SPU67","docs/evidence/2026-10-04/n95-spu67-results.json"),
        ("WSOLA68","docs/evidence/2026-10-04/n95-wsola68-results.json"),
        ("dependencies","docs/evidence/2026-10-04/n95-offload-dependency-audit.json"),
        ("ARM_cache","docs/evidence/2026-10-04/n95-arm-cache-path-audit.json"),
        ("DSP_compiler_order","docs/evidence/2026-10-04/n95-kernel-publish-audit.json"))}
    result=dict(scope="N95 research acceptance against original D0-D2 assignment; no emulator implementation or new DSP RUN; E90 deferred",
                overall_goal_status="in_progress",requirements_source=dict(path="work/CODEX_TASK_2026-10-01.md",sha256=sha(requirement)),
                d0=d0,final_state=final,inputs=inputs,
                requirements=[
                    dict(id="D0_normal_cycles",status="proven_N95",criterion="three consecutive create/RUN/checked packets/delete cycles with EXIT/FINAL0 and responding phone",evidence="d0.steps + sequence + fresh final_state",limit="Positive-cycle acceptance; not a claim of universal safe cancel or reboot-free failure handling."),
                    dict(id="D0_error_timeout_cancel_audit",status="documented_with_limits",criterion="audit native loader/host error,timeout,cancel paths",evidence="docs/LIFECYCLE_DMM_2026-10-01.md; src/c55stream.cpp timeout/cancel/quarantine paths; no automatic KILL",limit="Unconfirmed pending/delete ownership retains live process/resources; hardware fault injection and universal safe ARM fallback not accepted."),
                    dict(id="D1_mapping_and_repeated_measurements",status="demonstrated_N95",criterion="16KiB TOTAL shared mapping; repeated latency/bandwidth/page identity/ownership/teardown",evidence="inputs.native61:3series/12runs/9360packets; inputs.CPU64 separate settled CPU cohort",limit="Payload shared mapping; notification buffers still use native transport. Separate cohorts cannot be pooled."),
                    dict(id="D1_memory_contract",status="unproven",criterion="establish memory publication order for a reusable channel",evidence="inputs.ARM_cache + read-only WPE0 cohorts + compiler/native notification audits",limit="DSP external writes reaching SDRAM before mailbox notification not independently established. Successful packets are measured evidence, not a general fence contract."),
                    dict(id="D2_measured_verdict",status="delivered_N95_measured_jobs",criterion="calculate MDEC/SPU/WSOLA with max(H+D,W)+S/N<A+W and record packet scope/verdict/missing evidence",evidence="inputs.MDEC66,SPU67,WSOLA68,dependencies; docs/PS1_CANDIDATES_2026-10-01.md",limit="Current blocking kernels remain ARM; async useful W/resident/full-state benefits unknown. Full gameplay/PCM/callback integration belongs to a later task."),
                    dict(id="originals_restoration",status="proven_N95_at_timestamp",criterion="restore changed originals with GET/SHA256 verification",evidence="final_state verification:5files equal_original,PS0,read-only INFO/PS/GET",limit="Snapshot at the recorded UTC timestamp, not continuous phone monitoring."),
                    dict(id="E90_followup",status="deferred_by_user",criterion="resume E90 restoration and frequency qualification tomorrow",evidence="user instruction2026-10-04; docs/E90_DAEMON_REBOOT_2026-10-04.md",limit="No E90 commands in this checkpoint; overall goal not complete.")],
                next_steps=["Resolve DSP endpoint publication and caller/context cache completion without assuming volatile/readback or ARM DSB is an OMAP fence.",
                            "After user-deferred E90 date: recover current journal/state before changes, restore own originals, qualify compatible RDomain clock probe; do not replay failed runs unchanged."],
                outside_current_implementation_scope=["Editing PS1Emulator to add async/resident DSP.","Full-game/audio integration acceptance is future work; unknown outcomes must remain explicit in research verdict."])
    path=DEST/"n95-acceptance-audit.json"; path.write_bytes((json.dumps(result,indent=2,ensure_ascii=False)+"\n").encode()); print(path)


if __name__=="__main__": main()
