"""Run only the c55stream experiment through the existing phone daemon.

START keeps the daemon available. PS observes progress; every
request has a finite timeout. This cannot recover a blocked kernel.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import time
from strict_net import Device
from prepare_stream import stock_clock_matches

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKER_MODES = ("worker-one", "worker-serial", "worker-parallel", "worker-calibrate", "worker-transfer", "worker-wsola")
PREPARED_MODES = ("receive-created", "message-stages", "messages", "execute", "serial", "parallel") + WORKER_MODES


def check_preparation(path, device, ip):
    proof = json.loads(path.read_text(encoding="utf-8"))
    if (proof.get("device") != device or proof.get("ip") != ip or
            proof.get("complete") is not True or "stock_clock" not in proof or
            proof.get("clock_log_restored") is not True):
        raise RuntimeError("successful preparation for this device/IP is required")
    stamp = datetime.datetime.fromisoformat(proof["utc"])
    if stamp.tzinfo is None:
        raise RuntimeError("preparation timestamp must include a timezone")
    age = (datetime.datetime.now(datetime.timezone.utc) - stamp).total_seconds()
    if not -30 <= age <= 600:
        raise RuntimeError("preparation must be no older than 10 minutes")
    evidence = (ROOT / "work/evidence" / device).resolve()

    def saved(relative):
        candidate = (ROOT / relative).resolve()
        if not candidate.is_relative_to(evidence):
            raise RuntimeError("preparation artifact is outside this device evidence directory")
        return candidate

    clock = saved(proof["clock_log"]).read_text(encoding="ascii", errors="replace")
    if not stock_clock_matches(clock, device):
        raise RuntimeError("saved clock probe did not confirm the expected stock state")
    deployed = [f for f in proof["files"] if f.get("remote") == "E:\\c55stream.dll55l" and
                f.get("equal") is True and f.get("readback")]
    if len(deployed) != 1:
        raise RuntimeError("preparation requires exactly one verified DSP deployment")
    entry = deployed[0]
    data = saved(entry["readback"]).read_bytes()
    if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest().upper() != entry["sha256"]:
        raise RuntimeError("saved DSP deployment does not match preparation")
    return proof, data


def info_tick(lines):
    for line in lines:
        found = re.fullmatch(r"tick (\d+) startTick \d+ boot .*", line)
        if found:
            return int(found.group(1))
    raise RuntimeError("INFO lacks the phone uptime tick")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ip", required=True)
    p.add_argument("--device", choices=("n95", "e90"), required=True)
    p.add_argument("--mode", choices=("inspect", "patcher-check", "base", "buffers", "create", "info", "receive-created", "message-stages", "messages", "execute", "serial", "parallel") + WORKER_MODES, required=True)
    p.add_argument("--host-version", type=int, choices=(7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20), default=20)
    p.add_argument("--preparation", type=pathlib.Path, help="fresh successful prepare_stream JSON; required for RUN and receive-created")
    p.add_argument("--reps", type=int)
    p.add_argument("--packet-bytes", type=int, help="total input bytes including the 32-byte protocol header")
    p.add_argument("--frames", type=int)
    p.add_argument("--deadline", type=int, default=30)
    p.add_argument("--exe", choices=("E:\\sys\\bin\\c55stream.exe", "C:\\sys\\bin\\c55stream.exe"), default="E:\\sys\\bin\\c55stream.exe")
    p.add_argument("--tag", required=True)
    a = p.parse_args()
    if a.reps is None:
        a.reps = 0 if a.mode == "worker-transfer" else (1 if a.mode == "worker-wsola" else 1000)
    if a.packet_bytes is None:
        a.packet_bytes = 1792 if a.mode == "worker-wsola" else 512
    if a.frames is None:
        a.frames = 1 if a.mode == "worker-one" else 8
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.tag):
        p.error("tag must contain only letters, digits, underscores and hyphens")
    if not 0 <= a.reps <= 20000 or not 5 <= a.deadline <= 120:
        p.error("reps must be 0..20000 and deadline 5..120 seconds")
    frame_modes = ("worker-one", "worker-serial", "worker-parallel", "worker-transfer", "worker-wsola")
    if (not 512 <= a.packet_bytes <= 4096 or a.packet_bytes % 2 or
            not 1 <= a.frames <= 4096 or (a.mode == "worker-one" and a.frames != 1)):
        p.error("packets must be even 512..4096 bytes, frames 1..4096, worker-one exactly one frame")
    if a.mode == "worker-transfer" and (a.host_version < 18 or a.reps != 0):
        p.error("worker-transfer requires host v18 and reps=0")
    if a.mode == "worker-wsola" and (a.host_version < 19 or a.packet_bytes != 1792 or a.reps > 64):
        p.error("worker-wsola requires host v19, input1792/output48 bytes and reps0..64")
    default_frames = 1 if a.mode == "worker-one" else 8
    if (a.packet_bytes != 512 or a.frames != default_frames) and (a.host_version < 18 or a.mode not in frame_modes):
        p.error("custom packet size/frame count requires a v18 worker frame mode")
    if a.mode in ("info", "messages") and a.host_version < 8:
        p.error("info/messages require host v8 or newer")
    if a.mode == "receive-created" and a.host_version < 9:
        p.error("receive-created requires host v9 or newer")
    if a.mode == "message-stages" and a.host_version < 11:
        p.error("message-stages requires host v11 or newer")
    if a.mode == "patcher-check" and a.host_version < 14:
        p.error("patcher-check requires host v14 or newer")
    if a.mode in WORKER_MODES and a.host_version < 16:
        p.error("worker modes require host v16 or newer")
    if a.mode=="worker-calibrate" and a.host_version<17:
        p.error("worker-calibrate requires host v17")
    if a.mode in PREPARED_MODES and not a.preparation:
        p.error("this mode requires --preparation from a fresh successful prepare_stream run")
    if a.mode == "messages" and a.deadline < 60:
        p.error("messages requires a deadline of at least 60 seconds for bounded cleanup")
    prepared = check_preparation(a.preparation, a.device, a.ip) if a.preparation else None
    host_prefix = f"C55STREAM v{a.host_version} "
    destination = ROOT / "work/evidence" / a.device
    destination.mkdir(parents=True, exist_ok=True)
    transport = destination / (a.tag + "-transport.txt")
    logfile = destination / (a.tag + ".log")
    priorlog = destination / (a.tag + "-prior.log")
    profilelog = destination / (a.tag + "-profile.log")
    if any(f.exists() for f in (transport, logfile, priorlog, profilelog)):
        p.error("tag already exists; evidence is never overwritten")
    def call(command):
        stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with transport.open("a", encoding="utf-8") as f:
            f.write(stamp + " " + command + "\n")
        try:
            output = "\n".join(device.cmd(command))
        except (OSError, RuntimeError) as exc:
            with transport.open("a", encoding="utf-8") as f:
                f.write("REQUEST FAILED " + str(exc) + "\n")
            raise
        with transport.open("a", encoding="utf-8") as f:
            f.write(output + "\n")
        return output

    def run(command, limit):
        response = call(f"START {a.exe} {command}")
        found = re.fullmatch(r"OK proc (\d+)", response)
        if not found:
            raise RuntimeError("no process id from START")
        process = found.group(1)
        until = time.monotonic() + limit
        finished = False
        exit_ok = False
        while time.monotonic() < until:
            response = call("PS c55stream*")
            if not any(x.startswith("1 ") for x in response.splitlines()):
                response = call(f"WAIT {process} 1")
                if not response.startswith("EXIT "):
                    raise RuntimeError("unexpected completed process response")
                exit_ok = response == "EXIT 0 Kill"
                finished = True
                break
            time.sleep(0.5)
        if not finished:
            device.get("E:\\c55stream.log", logfile)
            raise TimeoutError("process exceeded deadline; no KILL: retain live DSP ownership and recover journal")
        return finished, exit_ok

    device = Device(a.ip, a.device)
    try:
        current_info = call("INFO").splitlines()
        if any(x.startswith("1 ") for x in call("PS c55stream*").splitlines()):
            raise RuntimeError("another c55stream process is already active")
        if prepared:
            proof, expected_dsp = prepared
            if info_tick(current_info) < info_tick(proof["info_after"]):
                raise RuntimeError("phone restarted after preparation; repeat the clock guard")
            readback = destination / (a.tag + "-prepared-dsp.dll55l")
            if readback.exists():
                raise RuntimeError("prepared DSP evidence already exists")
            device.get("E:\\c55stream.dll55l", readback)
            if readback.read_bytes() != expected_dsp:
                raise RuntimeError("phone DSP changed after preparation")
            with transport.open("a", encoding="utf-8") as f:
                f.write("PREPARATION VERIFIED " + str(a.preparation) + "\n")
        # Preserve the previous phone journal before even inspect can replace it.
        try:
            device.get("E:\\c55stream.log", priorlog)
        except RuntimeError as exc:
            if str(exc) != "ERR -1":
                raise
        if a.mode != "inspect":
            finished, exit_ok = run("inspect", 5)
            device.get("E:\\c55stream.log", profilelog)
            profile = profilelog.read_text(encoding="ascii", errors="replace")
            if not finished or not exit_ok or not profile.startswith(host_prefix) or not re.search(r"FINAL status=0\s*$", profile):
                raise RuntimeError(f"host v{a.host_version} inspect required before any DSP experiment")
        command = a.mode if a.mode not in ("serial", "parallel", "worker-one", "worker-serial", "worker-parallel") else f"{a.mode} reps={a.reps}"
        if a.host_version >= 18 and a.mode in frame_modes:
            command = f"{a.mode} reps={a.reps} bytes={a.packet_bytes} frames={a.frames}"
        finished, exit_ok = run(command, a.deadline)
        device.get("E:\\c55stream.log", logfile)
        call("INFO")
    finally:
        device.close()
    log = logfile.read_text(encoding="ascii", errors="replace")
    if not finished or not exit_ok or not log.startswith(host_prefix) or not re.search(r"FINAL status=0\s*$", log):
        raise RuntimeError("experiment did not complete successfully; retain the log")
    if a.mode in ("serial", "parallel") and "STREAM PASS frames=8 creates=1" not in log:
        raise RuntimeError("missing stream correctness result")
    if a.mode in WORKER_MODES:
        frames = a.frames
        parallel = int(a.mode == "worker-parallel")
        crc_frames = 0 if a.mode in ("worker-transfer", "worker-wsola") else frames
        expected = ("WORKER CALIBRATION PASS frames=8 creates=1 runs=0 intervals=7 no_crc=1" if a.mode=="worker-calibrate" else
                    f"WORKER WSOLA PASS frames={frames} creates=1 runs=0 reps={a.reps} input_bytes=1792 output_bytes=48 " if a.mode=="worker-wsola" else
                    f"WORKER STREAM PASS frames={frames} creates=1 runs=0 useful_arm_crc={crc_frames} mode={parallel} reps={a.reps} ")
        if expected not in log or "WORKER CLEANUP PASS no_run=1 delete_free_native_close=0" not in log:
            raise RuntimeError("missing worker stream or cleanup result")
        if "BEGIN execute" in log:
            raise RuntimeError("worker mode must not submit official RUN")
        if a.host_version >= 18 and a.mode in frame_modes and a.mode != "worker-wsola":
            if f"packet_bytes={a.packet_bytes} no_crc={int(a.mode == 'worker-transfer')}" not in log:
                raise RuntimeError("missing packet size or CRC mode result")
            size_lines = re.findall(r"^SIZE frame=(\d+) input_bytes=(\d+) output_bytes=(\d+) returned_words=(\d+) protocol=(\d+) checked_payload_words=(\d+)\r?$", log, re.M)
            expected_sizes = [(str(i), str(a.packet_bytes), str(a.packet_bytes),
                               str(a.packet_bytes // 2), str(a.host_version), str(a.packet_bytes // 2 - 16))
                              for i in range(1, frames + 1)]
            if size_lines != expected_sizes:
                raise RuntimeError("packet sizes or complete payload checks differ")
        if a.mode == "worker-wsola":
            from wsola_vectors import vector
            rows = re.findall(r"^WSOLA result frame=(\d+) offset=(\d+) expected_offset=(\d+) score=(-?\d+) expected_score=(-?\d+) scored=(\d+) expected_scored=(\d+) input_sum=(-?\d+) expected_sum=(-?\d+)\r?$", log, re.M)
            expected_rows = []
            for i in range(1, frames + 1):
                ref = vector(i)
                off, score, count = (ref["offset"], ref["score"], ref["scored"]) if a.reps else (0, 0, 0)
                expected_rows.append(tuple(map(str, (i, off, off, score, score, count, count, ref["input_sum"], ref["input_sum"]))))
            if rows != expected_rows or len(re.findall(r"^WSOLA frame=\d+ case=\d+ reps=\d+ put=0/0 get=0/0 errors=0 stop=[01]\r?$", log, re.M)) != frames:
                raise RuntimeError("WSOLA differs from independent integer fixtures or completion failed")
    if a.mode == "messages" and "MESSAGE ECHO PASS creates=1 protocol=8" not in log:
        raise RuntimeError("missing message correctness result")
    if a.mode == "receive-created" and "PENDING RECEIVE CLEANUP PASS no_run=1" not in log:
        raise RuntimeError("missing pending receive cleanup result")
    if a.mode == "message-stages" and "MESSAGE STAGES OBSERVED count=3 get_timeout=0 put_timeout=0" not in log:
        raise RuntimeError("missing message stage observation")
    message_protocol = 15 if a.host_version >= 15 else 12
    if a.mode == "message-stages" and a.host_version >= 13 and f"MESSAGE HELLO AFTER STAGES PASS protocol={message_protocol}" not in log:
        raise RuntimeError("missing message delivery after stages")
    if a.mode == "patcher-check" and "PATCHER OWN RAM PASS no_kernel_patch=1 no_prcm=1" not in log:
        raise RuntimeError("missing patcher own-RAM verification")
    print("VERIFIED " + str(logfile))


if __name__ == "__main__":
    main()
