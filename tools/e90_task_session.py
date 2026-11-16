"""Bounded D0 session, with snapshot and exact file restoration.

No network fallback and no process KILL. A failed native teardown stays alive
for manual recovery; --restore refuses a live c55stream. Run via run_bounded.
"""
import argparse
import contextlib
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import time

from strict_net import Device
from prepare_stream import stock_clock_matches

ROOT = Path(__file__).resolve().parents[1]
IP = "192.168.3.21"
REMOTE = ("E:\\c55stream.dll55l", "E:\\c55stream.log", "E:\\ocprobe.log",
          "C:\\sys\\bin\\c55stream.exe", "C:\\sys\\hash\\c55stream.exe")


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def n95_m111_clock_matches(engine, dsp):
    """Accept only the observed existing N95 clock profile, without changing it."""
    expected = {"CM_CLKSEL1_PLL": "0006f400", "CM_CLKSEL2_PLL": "00000002",
                "CM_CLKSEL_MPU": "00000002", "CM_CLKSEL1_CORE": "04360844"}
    for register, value in expected.items():
        if re.findall(rf"^\s*{register}\s+@[0-9a-f]+ = ([0-9a-f]+)$", engine, re.M) != [value]:
            return False
    return ("EMachineUid = 536882564" in engine and "engine self-check done" in engine and
            "restore check: stock DoControl(1,0) -> 129  " in engine and
            "EMachineUid = 536882564" in dsp and "profile: RM-320 35.0.001/31.0.015" in dsp and
            "NOT STOCK AT START: m=111 CLKSEL1_CORE=04360844 CLKSEL_MPU=00000002" in dsp and
            "CM_CLKSEL_DSP @c6008840 = 000023c3" in dsp and "DSP probe done" in dsp and
            "restore check: stock DoControl(1,0) -> 129  " in dsp)


def validate_journal(log, command, host_version=21):
    lines = log.splitlines()
    if (not lines or not lines[0].startswith(f"C55STREAM v{host_version} command='{command}'") or
            lines[-1] != "FINAL status=0" or "QUARANTINE" in log):
        raise RuntimeError("journal did not prove clean host completion")
    if command == "inspect":
        if "profile guard=0 " not in log:
            raise RuntimeError("missing profile guard")
        return
    if command == "boot-info":
        if (host_version < 44 or "BOOT PROBE COMPLETE no_dsp_open=1 no_patcher=1 readonly_HAL=1" not in log
                or "BOOT HAL startup_rc=" not in log or "BOOT USER fault_rc=" not in log
                or "BEGIN processor" in log or "POINTER" in log or "BEGIN execute" in log):
            raise RuntimeError("read-only boot probe did not complete")
        return
    if command == "processor-state":
        required = ("processor open=0", "PROCESSOR STATE rc=0 state=1 expected=1 native_ioctl=2 cached=1 no_patcher=1 no_proc_load=1",
                    "PROCESSOR STATE PASS native_ioctl=2 no_patcher=1 no_create=1 no_run=1", "BEGIN close")
        forbidden = ("BEGIN execute", "BEGIN DCD bind", "BEGIN create", "POINTER", "patcher own-ram", "base load=")
        if (host_version < 45 or any(marker not in lines for marker in required)
                or any(marker in log for marker in forbidden)):
            raise RuntimeError("native processor state query did not complete without research reads")
        return
    if command == "patcher-read-check":
        records = re.findall(
            r"^PATCHREAD pass=(\d+) rc=0 source=([0-9a-f]{8}) destination=([0-9a-f]{8}) bytes=24 "
            r"words=([0-9a-f]{8}(?:/[0-9a-f]{8}){5})$", "\n".join(lines), re.M)
        reader_words = "e5d00040/e5911000/e3500000/01a00001/11a00861/e12fff1e"
        if (host_version < 29 or "machine=20002496 " not in lines[0] or
                "profile guard=0 " not in log or
                "PATCHREAD PASS destination_own_ram=1 kernel_code_writes=0 prcm_writes=0 dsp_open=0 no_run=1" not in lines or
                "BEGIN processor open" in lines or len(records) != 3 or
                [r[0] for r in records] != ["0", "1", "2"] or
                records[1][1] != "803f7664" or records[2][1] != "c8010b20" or
                any(r[3] != reader_words for r in records[:2]) or
                len({r[2] for r in records}) != 1 or int(records[0][2], 16) == 0):
            raise RuntimeError("patcher source-pointer read gates failed")
        return
    if command == "pointer-snapshot":
        snap = re.search(
            r"^POINTER SNAPSHOT PASS root_provenance=1 factory_matched=1 manager_valid=([01]) board_valid=([01]) destination_own_ram=1 kernel_code_writes=0 prcm_writes=0 dsp_open=0 no_run=1$",
            "\n".join(lines), re.M)
        if (host_version < 30 or ("machine=20002496 " not in lines[0] and "machine=20002d84 " not in lines[0]) or
                "profile guard=0 " not in log or not snap or
                "BEGIN processor open" in lines):
            raise RuntimeError("pointer snapshot gates failed")
        return
    if host_version >= 35 and ("BASE attach gate=0 reused_running=1 proc_load_calls=0" not in lines or
                               "BEGIN base load" in lines or "base load=" in log):
        raise RuntimeError("existing running DSP base was not preserved")
    if command in ("dmm-provenance", "dmm-map"):
        if (host_version < 36 or
                "DMM PROVENANCE PASS bytes=16384 pages=4 cmm_range=1 physical_translation=1 no_map=1 no_run=1" not in lines or
                "free native in=0" not in lines or "BEGIN close" not in lines or
                "BEGIN execute" in lines or "BEGIN allocate" in lines):
            raise RuntimeError("native 16KiB provenance/free/close not proven")
        if command == "dmm-map" and (host_version < 37 or
                f"DMM MAP PASS bytes=16384 flags={17 if host_version >= 40 else 16} reserve_map_unmap_unreserve=0 no_dsp_access=1 no_run=1" not in lines or
                "DMM unmap=0 " not in log or "DMM unreserve=0 " not in log):
            raise RuntimeError("16KiB map/unmap/unreserve not proven")
        return
    required = ("create=0 status=0 ", "delete=0 status=0", "free task=0", "BEGIN close")
    if any(marker not in log for marker in required):
        raise RuntimeError("missing clean lifecycle step")
    if command == "create":
        if "BEGIN execute" in lines:
            raise RuntimeError("create probe unexpectedly invoked RUN")
        return
    if command == "native-copy":
        required = ("node reference_rom=1", "execute start=0 status=0",
                    "REFERENCE COPY PASS frames=8 checked_words_per_frame=256 no_own_execute=1",
                    "free native out=0", "free native in=0")
        frames = re.findall(r"^reference frame=(\d+) put=0/0 get=0/0 bytes=512 bad_words=0 wall_us=\d+$", log, re.M)
        if any(marker not in log for marker in required) or frames != [str(i) for i in range(1, 9)]:
            raise RuntimeError("ROM reference copy lifecycle not clean")
        return
    if command.startswith("dmm-ring-wsola-current "):
        from wsola_current_session_support import validate_current
        validate_current(log,command,host_version)
        return
    if command.startswith("dmm-ring-spu "):
        from spu_session_support import validate_spu
        validate_spu(log,command,host_version)
        return
    if command.startswith("dmm-ring-mdec "):
        from mdec_session_support import validate_mdec
        validate_mdec(log,command,host_version)
        return
    wsola_command = re.fullmatch(r"dmm-ring-wsola frames=(8|120)", command)
    if wsola_command:
        count = int(wsola_command[1])
        required = ("execute start=0 status=0", "RING unmap=0", "RING unreserve=0",
                    "RING free native=0", "free native out=0", "free native in=0",
                    f"RING WSOLA PASS jobs={count} input_slots_per_job=4 output_slots_per_job=1 checked_words_per_job=1280 protocol=40 ownership=whole_region useful_ARM_W=0")
        gate = re.search(r"^NATIVE pre-RUN gate=0 env=([0-9a-f]{8}) state=1 no_patcher=1 proc_load_calls=0 env_allocator=RMS_MEM_valloc$", log, re.M)
        pages = re.findall(r"^NATIVE PAGE phase=([01]) index=([0-3]) linear=([0-9a-f]{8}) physical=([0-9a-f]{8})$", log, re.M)
        if (host_version < 48 or "machine=20002d84 " not in lines[0] or not gate or int(gate[1],16)==0
                or any(marker not in log for marker in required)
                or any(marker in log for marker in ("POINTER", "ROUTING", "PATCHREAD", "DMM CMM", "patcher own-ram"))
                or len(pages)!=8 or [(row[0],row[1]) for row in pages]!=[(str(p),str(i)) for p in (0,1) for i in range(4)]
                or [row[1:] for row in pages[:4]]!=[row[1:] for row in pages[4:]]
                or [int(row[2],16) for row in pages[:4]]!=[int(pages[0][2],16)+i*4096 for i in range(4)]
                or any(int(row[3],16) in (0,0xffffffff) or int(row[3],16)&4095 for row in pages)
                or int(pages[0][2],16)&4095):
            raise RuntimeError("WSOLA native ownership/page/lifecycle gates failed")
        ordered = ("PROCESSOR STATE rc=0", "NATIVE PAGES rc=0 phase=0", "RING map=0", "NATIVE pre-RUN gate=0", "BEGIN execute",
                   "RING WSOLA PASS", "NATIVE PAGES rc=0 phase=1", "BEGIN delete", "free task=0", "RING unmap=0", "RING unreserve=0", "RING free native=0", "BEGIN close")
        if any(marker not in log for marker in ordered) or [log.index(marker) for marker in ordered]!=sorted(log.index(marker) for marker in ordered):
            raise RuntimeError("WSOLA ring ownership order failed")
        results = re.findall(r"^RING WSOLA RESULT frame=(\d+) case=(\d+) slot=(\d+) offset=(\d+) expected_offset=(\d+) score=(-?\d+) expected_score=(-?\d+) scored=(\d+) expected_scored=(\d+) errors=0 checked_words=1280$", log, re.M)
        timings = re.findall(r"^RING WSOLA TIMING frame=(\d+) arm_iterations=16 arm_ticks=(\d+) arm_first=([01]) pack_ticks=(\d+) transfer_ticks=(\d+) end_to_end_ticks=(\d+) cpu_us=(\d+) raw_dsp_ticks=(\d+) counts_per_ms=(\d+)$", log, re.M)
        dcr = re.findall(r"^DCR READ frame=(\d+) protocol=40 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01]) writes=0 diagnostic_only=1$", log, re.M)
        if (any(len(rows)!=count or [int(row[0]) for row in rows]!=list(range(1,count+1)) for rows in (results,timings,dcr))
                or any(int(row[1])!=i%8 or int(row[2])!=i*4%15 or row[3]!=row[4] or row[5]!=row[6] or row[7]!=row[8] for i,row in enumerate(results))
                or any(int(row[2])!=int(row[0])%2 or any(int(row[k])<=0 for k in (1,4,5,7,8)) for row in timings)
                or any(bool(int(row[1],16)&0x80)!=bool(int(row[3])) or bool(int(row[2],16)&0x80)!=bool(int(row[4])) for row in dcr)):
            raise RuntimeError("WSOLA reference results, timing or DCR records failed")
        return
    ring_command = re.fullmatch(r"dmm-ring(-native|-dcr|-window)? batch=(1|2|8|15) frames=(8|120)", command)
    if ring_command:
        native_mode = bool(ring_command.group(1))
        dcr_read = ring_command.group(1) == "-dcr"
        cpu_window = ring_command.group(1) == "-window"
        batch, count = map(int, ring_command.groups()[1:])
        required = ("execute start=0 status=0", "RING unmap=0", "RING unreserve=0",
                    "RING free native=0", "free native out=0", "free native in=0")
        if native_mode:
            gate = re.search(r"^NATIVE pre-RUN gate=0 env=([0-9a-f]{8}) state=1 no_patcher=1 proc_load_calls=0 env_allocator=RMS_MEM_valloc$", log, re.M)
            if (host_version < 46 or not gate or int(gate.group(1), 16) == 0
                    or any(marker in log for marker in ("POINTER", "ROUTING", "PATCHREAD", "DMM CMM", "patcher own-ram"))
                    or "PROCESSOR STATE rc=0 state=1 expected=1 native_ioctl=2 cached=1 no_patcher=1 no_proc_load=1" not in lines):
                raise RuntimeError("native state/retained env gate not proven without kernel snapshots")
            pages = re.findall(r"^NATIVE PAGE phase=([01]) index=([0-3]) linear=([0-9a-f]{8}) physical=([0-9a-f]{8})$", log, re.M)
            if (len(pages) != 8 or [(r[0], r[1]) for r in pages] != [(str(p), str(i)) for p in (0, 1) for i in range(4)]
                    or [r[1:] for r in pages[:4]] != [r[1:] for r in pages[4:]]
                    or any(int(r[3], 16) in (0, 0xffffffff) or int(r[3], 16) & 4095 for r in pages)
                    or [int(r[2], 16) for r in pages[:4]] != [int(pages[0][2], 16) + i*4096 for i in range(4)]
                    or int(pages[0][2], 16) & 4095):
                raise RuntimeError("native ring page identity/lifetime brackets failed")
            ordered_native = ("PROCESSOR STATE rc=0", "NATIVE PAGES rc=0 phase=0", "RING map=0", "NATIVE pre-RUN gate=0", "BEGIN execute",
                              "RING DATA PASS", "NATIVE PAGES rc=0 phase=1", "BEGIN delete")
            if any(marker not in log for marker in ordered_native) or [log.index(m) for m in ordered_native] != sorted(log.index(m) for m in ordered_native):
                raise RuntimeError("native ring state/page ownership ordering failed")
        else:
            required += ("ROUTING pre-RUN gate=0 no_run_on_failure=1", "matching_queues=1 require_unique=1")
        rows = re.findall(r"^RING FRAME frame=(\d+) slot=(\d+) batch=(\d+) packet_start=(\d+) wall_us=(\d+) cpu_us=(-?\d+) bad_words=0 dsp_ticks=(\d+)$", log, re.M)
        if (host_version < 38 or any(marker not in log for marker in required) or len(rows) != count or
                [int(row[0]) for row in rows] != list(range(1, count + 1)) or
                any(int(row[1]) != ((i * batch) % 15) or int(row[2]) != batch or int(row[3]) != i * batch for i, row in enumerate(rows)) or
                f"RING DATA PASS bytes=16384 packets={count * batch} frames={count} batch={batch} " not in log):
            raise RuntimeError("ring correctness/wrap and complete lifecycle not proven")
        ordered = ("BEGIN delete", "free task=0", "RING unmap=0", "RING unreserve=0", "RING free native=0", "BEGIN close")
        if [log.index(marker) for marker in ordered] != sorted(log.index(marker) for marker in ordered):
            raise RuntimeError("mapping was released before native task completion")
        if dcr_read:
            readings = re.findall(r"^DCR READ frame=(\d+) protocol=39 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01]) writes=0 diagnostic_only=1$", log, re.M)
            if (host_version < 47 or "machine=20002d84 " not in lines[0]
                    or len(readings) != count or [int(row[0]) for row in readings] != list(range(1, count + 1))
                    or any(bool(int(row[1], 16) & 0x80) != bool(int(row[3])) or
                           bool(int(row[2], 16) & 0x80) != bool(int(row[4])) for row in readings)):
                raise RuntimeError("distinct N95 read-only DCR diagnostic records not proven")
        elif "DCR READ" in log:
            raise RuntimeError("DCR diagnostic cannot be counted as the original ring cohort")
        if cpu_window:
            measurement = re.search(r"^RING CPU WINDOW frames=(\d+) batch=(\d+) outer_ticks=(\d+) loop_ticks=(\d+) final_yield_ticks=(\d+) cpu_us=(\d+) before_rc=0 after_rc=0 pack_checks_included=1 journaling_inside=0 arm_baseline_inside=0 boundary_yield=1 useful_ARM_W=0$",log,re.M)
            if (host_version != 49 or "machine=20002d84 " not in lines[0] or not measurement
                    or list(map(int,measurement.groups()[:2])) != [count,batch]
                    or int(measurement[3]) < int(measurement[4])+int(measurement[5])
                    or min(map(int,measurement.groups()[2:5])) <= 0
                    or int(measurement[6])*32768 > (int(measurement[3])+2)*1000000
                    or any(int(row[5])!=-1 for row in rows)
                    or log.index("RING CPU WINDOW") > log.index("RING FRAME")):
                raise RuntimeError("aggregate CPU window boundaries/timing not proven")
        elif "RING CPU WINDOW" in log:
            raise RuntimeError("CPU window cannot be counted as historical ring cohort")
        return
    if command != "run-transfer reps=0 bytes=512 frames=8" or "EXITDIAG" in log or "diagnostic_only=1" in log:
        raise RuntimeError("diagnostic or unknown mode cannot count as an ordinary D0 cycle")
    required = ("execute submitted=0 status=", "execute start=0 status=0",
                "STREAM PASS frames=8 creates=1 useful_arm_crc=0 mode=0 ",
                "free native out=0", "free native in=0")
    if any(marker not in log for marker in required):
        raise RuntimeError("missing clean RUN/packet/cleanup step")
    if host_version >= 34:
        gate = re.search(r"^ROUTING preflight env=([0-9a-f]{8}) matching_queues=1 require_unique=1$", log, re.M)
        if (not gate or int(gate.group(1), 16) == 0 or
                "ROUTING pre-RUN gate=0 no_run_on_failure=1" not in lines or "BEGIN execute" not in lines or
                log.index("ROUTING pre-RUN gate=0") > log.index("BEGIN execute")):
            raise RuntimeError("unique source routing before RUN was not proven")
    frames = re.findall(r"^frame=(\d+) put=0/0 get=0/0 .*", log, re.M)
    sizes = re.findall(r"^SIZE frame=(\d+) input_bytes=512 output_bytes=512 returned_words=256 protocol=21 checked_payload_words=240$", log, re.M)
    results = re.findall(r"^  result=0 expected=0 ticks=\d+ counts_per_ms=\d+ errors=0 stop=([01])$", log, re.M)
    if frames != [str(i) for i in range(1, 9)] or sizes != frames or results != ["0"] * 7 + ["1"]:
        raise RuntimeError("eight ordered byte-checked packets and stop were not proven")


def run(device, command, seconds=30, kill_on_timeout=False, keep_awake=False):
    response = device.cmd("START " + command)
    if len(response) != 1 or not response[0].startswith("OK proc "):
        raise RuntimeError("START did not return process ID")
    proc = int(response[0].split()[2])
    name = Path(command.split()[0].replace("\\", "/")).stem
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if keep_awake and device.cmd("WAKE") != ["OK wake"]:
            raise RuntimeError("daemon WAKE was not acknowledged")
        if not any(line.startswith("1 ") for line in device.cmd("PS " + name + "*")):
            result = device.cmd(f"WAIT {proc} 1")
            if result != ["EXIT 0 Kill"]:
                raise RuntimeError("process exit: " + repr(result))
            return result
        time.sleep(0.25)
    if kill_on_timeout:
        try:
            device.cmd(f"KILL {proc}")
        except Exception:
            pass
        raise TimeoutError(f"deadline exceeded ({seconds}s); process {proc} killed")
    raise TimeoutError("deadline exceeded; no KILL; save journal and request manual recovery")


def validate_worker_message(log, host_version):
    validate_journal(log.replace("command='worker-message-queued'", "command='create'").replace("command='worker-message'", "command='create'"), "create", host_version)
    required = ("MSGWORKER delivery=0 overall=0 no_run=1", "cmd=00000606 arg1=a1b2c3d4",
                "EXITDIAG stage=7 protocol=26 result=1", "free native out=0", "free native in=0")
    if any(marker not in log for marker in required) or "BEGIN execute" in log:
        raise RuntimeError("created worker did not prove prearmed outbound MSG and clean cleanup")


def _main():
    global IP, REMOTE
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--device", choices=("e90", "n95"), default="e90")
    p.add_argument("--ip", help="explicit address; defaults to the selected device's known address")
    p.add_argument("--clock-profile", choices=("stock", "n95-m111"), default="stock")
    p.add_argument("--session", required=True, type=Path)
    p.add_argument("--action", choices=("snapshot", "clocks", "deliver-sis", "deploy-host", "restore-host", "deploy-dsp", "run", "restore", "verify", "d0-sequence", "d0-message-diagnostic", "d0-exit-diagnostic", "d0-worker-message", "d0-worker-message-queued", "d0-native-reference", "d0-native-library2", "recover-journal"), required=True)
    p.add_argument("--artifact", type=Path)
    p.add_argument("--artifact-proof", type=Path, default=ROOT / "docs/evidence/2026-10-01/d0-run-stop-v21-artifacts.json")
    p.add_argument("--command")
    p.add_argument("--host-version", type=int, choices=range(21, 54), default=21)
    p.add_argument("--sis-name", choices=("c55stream-d0-v21.sis", "c55stream-livejournal-v22.sis", "c55stream-native-copy-v23.sis", "c55stream-native-copy-v24.sis", "c55stream-exit-diag-v25.sis", "c55stream-restore-v20.sis", "c55stream-restore-v20-r25.sis", "c55stream-restore-v20-r32.sis"), default="c55stream-d0-v21.sis")
    p.add_argument("--allow-kill", action="store_true", help="kill process on deadline expiration")
    p.add_argument("--keep-awake", action="store_true", help="acknowledged daemon WAKE before action and during finite run polling")
    p.add_argument("--clock-probe", choices=("ocprobe", "rdomain"), default="ocprobe")
    p.add_argument("--expected-boot", help="require the qualified clock cohort's boot before any START/PUT")
    p.add_argument("--tag", required=True)
    a = p.parse_args()
    if a.device != "n95" and ((a.command or "").startswith(("dmm-ring-dcr ", "dmm-ring-wsola ", "dmm-ring-wsola-current ", "dmm-ring-window ", "dmm-ring-mdec ", "dmm-ring-spu ")) or
                              (a.artifact and a.artifact.name in ("c55stream-dmm-ring-dcr.dll55l", "c55stream-dmm-ring-wsola.dll55l", "c55stream-dmm-ring-window.dll55l", "c55stream-dmm-ring-mdec.dll55l", "c55stream-dmm-ring-spu.dll55l"))):
        p.error("DCR diagnostic is restricted to N95; no connection attempted")
    if a.clock_profile != "stock" and (a.device != "n95" or a.action not in ("d0-worker-message", "d0-worker-message-queued", "d0-sequence")):
        p.error("n95-m111 is restricted to finite N95 worker MSG diagnostics and d0-sequence")
    IP = a.ip or {"e90": "192.168.3.21", "n95": "192.168.3.22"}[a.device]
    REMOTE = ("E:\\c55stream.dll55l", "E:\\c55stream.log", "E:\\ocprobe.log",
              ("C:" if a.device == "e90" else "E:") + "\\sys\\bin\\c55stream.exe",
              "C:\\sys\\hash\\c55stream.exe")
    if a.device == "n95" and (a.action not in ("snapshot", "clocks", "recover-journal", "restore", "restore-host", "verify", "deploy-host", "deploy-dsp", "run", "d0-worker-message", "d0-worker-message-queued", "d0-sequence") or a.host_version < 28):
        p.error("N95 supports only host28+ finite diagnostics/d0-sequence and backup/restore actions")
    directory = a.session.resolve()
    evidence_root = (ROOT / "work/evidence" / a.device).resolve()
    if not directory.is_relative_to(evidence_root):
        p.error("session must be inside this device's work/evidence directory")
    if not a.tag or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in a.tag):
        p.error("invalid tag")
    directory.mkdir(parents=True, exist_ok=True)
    proof = directory / "originals.json"
    report = directory / (a.tag + ".json")
    if report.exists() or (directory / (a.tag + "-transport.txt")).exists():
        p.error("tag exists")
    result = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "ip": IP,
              "device": a.device, "action": a.action, "host_version_expected": a.host_version, "complete": False}
    try:
        with (directory / (a.tag + "-transport.txt")).open("x", encoding="utf-8") as out, contextlib.redirect_stdout(out):
            d = Device(IP, a.device, connect_timeout=8)
            try:
                result["info_before"] = d.cmd("INFO")
                if a.expected_boot is not None:
                    result["expected_boot"] = a.expected_boot
                    observed = [line.split(" startTick ")[1] for line in result["info_before"]
                                if line.startswith("tick ") and " startTick " in line]
                    if observed != [a.expected_boot]:
                        raise RuntimeError("boot changed before action; no START/PUT")
                if a.keep_awake:
                    result["wake_before"] = d.cmd("WAKE")
                    if result["wake_before"] != ["OK wake"]:
                        raise RuntimeError("daemon WAKE was not acknowledged")
                result["c55stream_processes"] = d.cmd("PS c55stream*")
                if a.action != "recover-journal" and any(line.startswith("1 ") for line in result["c55stream_processes"]):
                    raise RuntimeError("live c55stream; only manual recovery can release uncertain ownership")
                result["ocprobe_processes"] = d.cmd("PS ocprobe*")
                if a.action != "recover-journal" and any(line.startswith("1 ") for line in result["ocprobe_processes"]):
                    raise RuntimeError("live ocprobe; do not overwrite its journal")
                if a.action == "snapshot":
                    if proof.exists():
                        raise RuntimeError("original snapshot exists")
                    originals = []
                    for index, remote in enumerate(REMOTE):
                        local = directory / f"original-{index}.bin"
                        if local.exists():
                            raise RuntimeError("partial snapshot exists; preserve it and choose a new session")
                        d.get(remote, local)
                        data = local.read_bytes()
                        originals.append({"remote": remote, "local": local.name,
                                          "bytes": len(data), "sha256": digest(data)})
                    result["files"] = originals
                else:
                    saved = json.loads(proof.read_text(encoding="utf-8"))
                    def original(remote):
                        entry = next(f for f in saved["files"] if f["remote"] == remote)
                        data = (directory / entry["local"]).read_bytes()
                        if digest(data) != entry["sha256"] or len(data) != entry["bytes"]:
                            raise RuntimeError("backup mismatch")
                        return data
                    def put_checked(remote, data, suffix):
                        d.put(remote, data)
                        local = directory / (a.tag + suffix)
                        d.get(remote, local)
                        if local.read_bytes() != data:
                            raise RuntimeError("readback mismatch " + remote)
                        return {"remote": remote, "bytes": len(data), "sha256": digest(data), "equal": True}
                    if a.action == "recover-journal":
                        # Read only, including when the quarantined owner is alive.
                        local = directory / (a.tag + ".log")
                        d.get(REMOTE[1], local)
                        result["journal"] = local.name
                        result["journal_sha256"] = digest(local.read_bytes())
                        dsp = directory / (a.tag + "-dsp.dll55l")
                        d.get(REMOTE[0], dsp)
                        result["dsp_sha256"] = digest(dsp.read_bytes())
                    elif a.action in ("d0-sequence", "d0-message-diagnostic", "d0-exit-diagnostic", "d0-worker-message", "d0-worker-message-queued", "d0-native-reference", "d0-native-library2"):
                        host = directory / (a.tag + "-host-readback.exe")
                        d.get(REMOTE[3], host)
                        if host.read_bytes() != (ROOT / "out/arm/c55stream.exe").read_bytes():
                            raise RuntimeError(f"D0 requires the exact built host{a.host_version}")
                        if f"C55STREAM v{a.host_version} ".encode() not in host.read_bytes():
                            raise RuntimeError("host version marker mismatch")
                        expected = json.loads(a.artifact_proof.read_text(encoding="utf-8"))
                        expected_host = next(f for f in expected["files"] if f["path"] == "out/arm/c55stream.exe")
                        if digest(host.read_bytes()) != expected_host["sha256"]:
                            raise RuntimeError("installed host differs from artifact proof")
                        result["host_sha256"] = digest(host.read_bytes())
                        current = directory / (a.tag + "-dsp-before.dll55l")
                        d.get(REMOTE[0], current)
                        if current.read_bytes() != original(REMOTE[0]):
                            raise RuntimeError("D0 requires the saved original DSP before deployment")
                        d.get(REMOTE[1], directory / (a.tag + "-log-before.log"))
                        d.get(REMOTE[2], directory / (a.tag + "-clock-before.log"))
                        if (directory / (a.tag + "-clock-before.log")).read_bytes() != original(REMOTE[2]):
                            raise RuntimeError("clock log changed; preserve it before restoring")
                        result["clock_probes"] = []
                        try:
                            for mode in ("engine", "dsp 1"):
                                result["clock_exit"] = run(d, "E:\\sys\\bin\\ocprobe.exe patcher " + mode + " " + a.device, 15)
                                local = directory / (a.tag + "-" + mode.split()[0] + ".log")
                                d.get(REMOTE[2], local)
                                result["clock_probes"].append({"path": local.name, "sha256": digest(local.read_bytes())})
                                if mode == "dsp 1":
                                    dsp_log = local.read_text(encoding="ascii", errors="replace")
                                    matches = stock_clock_matches(dsp_log, a.device)
                                    if a.clock_profile == "n95-m111":
                                        engine_log = (directory / (a.tag + "-engine.log")).read_text(encoding="ascii", errors="replace")
                                        matches = n95_m111_clock_matches(engine_log, dsp_log)
                                        result["clock_profile"] = "existing n95-m111; no PRCM writes"
                                        result["clock_kHz_from_registers"] = {"ARM": 426240, "bus": 213120, "DSP": 284160}
                                    if not matches:
                                        raise RuntimeError("read-only DSP clock/profile guard failed; no research RUN")
                        finally:
                            result["clock_restored"] = put_checked(REMOTE[2], original(REMOTE[2]), "-clock-restored.log")
                        result["steps"] = []
                        def step(label, command):
                            entry = {"label": label, "command": command, "complete": False}
                            result["steps"].append(entry)
                            logfile = directory / (a.tag + "-" + label + ".log")
                            try:
                                entry["exit"] = run(d, REMOTE[3] + " " + command, 30, kill_on_timeout=a.allow_kill)
                            except Exception as exc:
                                entry["run_error"] = type(exc).__name__ + ": " + str(exc)
                                raise
                            finally:
                                active_error = sys.exc_info()[0] is not None
                                try:
                                    d.get(REMOTE[1], logfile)
                                    entry["journal"] = logfile.name
                                    entry["sha256"] = digest(logfile.read_bytes())
                                except Exception as exc:
                                    entry["journal_error"] = type(exc).__name__ + ": " + str(exc)
                                    if not active_error:
                                        raise
                            if command in ("message-stages", "exit-stages", "worker-message", "worker-message-queued"):
                                # Diagnostic only, never counts toward the three clean packet cycles.
                                entry["diagnostic_only"] = True
                                if command in ("worker-message", "worker-message-queued"):
                                    validate_worker_message(logfile.read_text(encoding="ascii", errors="replace"), a.host_version)
                            else:
                                validate_journal(logfile.read_text(encoding="ascii", errors="replace"), command, a.host_version)
                            entry["info_after"] = d.cmd("INFO")
                            initial_boot = next(line.split(" startTick ")[1] for line in result["info_before"] if line.startswith("tick "))
                            step_boot = next(line.split(" startTick ")[1] for line in entry["info_after"] if line.startswith("tick "))
                            if initial_boot != step_boot:
                                raise RuntimeError("daemon or boot changed during D0")
                            entry["complete"] = True
                        step("inspect", "inspect")
                        if a.action in ("d0-native-reference", "d0-native-library2"):
                            library2 = a.action == "d0-native-library2"
                            if not a.artifact or a.host_version != (24 if library2 else 23):
                                raise RuntimeError("native control requires matching host and the archived E90 reference")
                            local = directory / (a.tag + "-reference-rom.dll55l")
                            d.get("Z:\\system\\apps\\strmcopy\\strmcopydyn.dll55l", local)
                            if digest(local.read_bytes()) != expected["native_reference"]["sha256"]:
                                raise RuntimeError("E90 ROM reference changed")
                            result["reference_rom_sha256"] = digest(local.read_bytes())
                            if library2:
                                derivative = expected["native_library2"]
                                if digest(a.artifact.read_bytes()) != derivative["derived_sha256"] or result["reference_rom_sha256"] != derivative["source_sha256"]:
                                    raise RuntimeError("native library2 derivation drift")
                                result["deployed"] = put_checked(REMOTE[0], a.artifact.read_bytes(), "-dsp-readback.dll55l")
                            step("native-copy", "native-copy")
                            result["reference_only"] = True
                            result["accepted_runs"] = 0
                        else:
                            variant = {"d0-message-diagnostic": "run-message-diag", "d0-exit-diagnostic": "run-exit-diag", "d0-worker-message": "worker-message", "d0-worker-message-queued": "worker-message"}.get(a.action, "run-stop")
                            artifact_path = f"out/dsp/c55stream-{variant}.dll55l"
                            artifact = (ROOT / artifact_path).read_bytes()
                            dsp_proof = next(f for f in expected["files"] if f["path"] == artifact_path)
                            if digest(artifact) != dsp_proof["sha256"]:
                                raise RuntimeError("run-stop artifact drift")
                            result["deployed"] = put_checked(REMOTE[0], artifact, "-dsp-readback.dll55l")
                            if a.action not in ("d0-worker-message", "d0-worker-message-queued"):
                                step("create", "create")
                            else:
                                # A live stream worker has an armed input. Its
                                # no-input stop/idle path is not proven; drain
                                # the finite final trigger in the diagnostic.
                                result["create_only_preflight_skipped"] = True
                        if a.action == "d0-message-diagnostic":
                            step("message-stages", "message-stages")
                            result["accepted_runs"] = 0
                        elif a.action == "d0-exit-diagnostic":
                            if a.host_version != 25:
                                raise RuntimeError("exit diagnostic requires host25")
                            step("exit-stages", "exit-stages")
                            result["accepted_runs"] = 0
                        elif a.action in ("d0-worker-message", "d0-worker-message-queued"):
                            if a.host_version not in (26, 27, 28, 29) or (a.action == "d0-worker-message-queued" and a.host_version < 27):
                                raise RuntimeError("created worker message diagnostic requires host26/27; queued receive requires host27")
                            mode = "worker-message-queued" if a.action == "d0-worker-message-queued" else "worker-message"
                            step(mode, mode)
                            result["accepted_runs"] = 0
                            result["official_run_count"] = 0
                        elif a.action == "d0-sequence":
                            for index in range(1, 4):
                                step(f"run{index}", "run-transfer reps=0 bytes=512 frames=8")
                            result["accepted_runs"] = 3
                    elif a.action == "clocks":
                        clock_original = original("E:\\ocprobe.log")
                        result["probes"] = []
                        result["clock_probe"] = a.clock_probe
                        try:
                            if a.clock_probe == "rdomain":
                                if a.device != "e90":
                                    raise ValueError("RDomain clock probe is guarded for E90 only")
                                proof = json.loads((ROOT / "docs/evidence/2026-10-04/ringclock-rdomain-artifacts.json").read_text())
                                local_exe = directory / (a.tag + "-clock-exe.bin")
                                d.get("E:\\sys\\bin\\ringclock.exe", local_exe)
                                result["clock_probe_sha256"] = digest(local_exe.read_bytes())
                                if result["clock_probe_sha256"] != proof["executable_sha256"]:
                                    raise RuntimeError("installed RDomain clock probe drift")
                                if d.cmd("PS ringclock*") != ["OK ps 0"]:
                                    raise RuntimeError("clock probe already running")
                                local = directory / (a.tag + "-rdomain.log")
                                try:
                                    run(d, "E:\\sys\\bin\\ringclock.exe", 15, keep_awake=a.keep_awake)
                                finally:
                                    d.get("E:\\ocprobe.log", local)
                                    result["probes"].append({"path": local.name, "sha256": digest(local.read_bytes())})
                            else:
                                for mode in ("engine", "dsp 1"):
                                    run(d, "E:\\sys\\bin\\ocprobe.exe patcher " + mode + " " + a.device, 15)
                                    local = directory / (a.tag + "-" + mode.split()[0] + ".log")
                                    d.get("E:\\ocprobe.log", local)
                                    result["probes"].append({"path": local.name, "sha256": digest(local.read_bytes())})
                        finally:
                            result["restored"] = put_checked("E:\\ocprobe.log", clock_original, "-ocprobe-restored.log")
                        combined = "".join((directory / probe["path"]).read_text(encoding="ascii") for probe in result["probes"])
                        result["stock_verified"] = stock_clock_matches(combined, a.device)
                    elif a.action == "deliver-sis":
                        if not a.artifact:
                            raise ValueError("artifact required")
                        remote = "E:\\" + a.sis_name
                        stat = d.cmd("STAT " + remote, allow_error=True)
                        result["sis_before_stat"] = stat
                        if not (stat[0].startswith("ERR ") and stat[0].split()[-1] == "-1"):
                            d.get(remote, directory / (a.tag + "-before.sis"))
                        result["deployed"] = put_checked(remote, a.artifact.read_bytes(), "-sis-readback.sis")
                    elif a.action in ("deploy-host", "restore-host"):
                        # Human authorization: HELP_NEEDED.md 2026-10-02 13:38.
                        # Only our research EXE/hash; saved originals validated.
                        original(REMOTE[3]); original(REMOTE[4])
                        data = original(REMOTE[3]) if a.action == "restore-host" else (ROOT / "out/arm/c55stream.exe").read_bytes()
                        hash_data = original(REMOTE[4]) if a.action == "restore-host" else hashlib.sha1(data).digest()
                        if a.action == "deploy-host":
                            expected = json.loads(a.artifact_proof.read_text(encoding="utf-8"))
                            entry = next(f for f in expected["files"] if f["path"] == "out/arm/c55stream.exe")
                            if digest(data) != entry["sha256"] or f"C55STREAM v{a.host_version} ".encode() not in data:
                                raise RuntimeError("host artifact/version drift")
                        result["before"] = []
                        for index, remote in enumerate(REMOTE[3:]):
                            local = directory / (a.tag + f"-before-{index}.bin")
                            d.get(remote, local)
                            result["before"].append({"remote": remote, "local": local.name,
                                                     "bytes": local.stat().st_size, "sha256": digest(local.read_bytes())})
                        current = directory / (a.tag + "-dsp-before.dll55l")
                        d.get(REMOTE[0], current)
                        if current.read_bytes() != original(REMOTE[0]):
                            raise RuntimeError("restore DSP/original journals before host replacement")
                        result["files"] = [put_checked(REMOTE[3], data, "-host-readback.exe"),
                                           put_checked(REMOTE[4], hash_data, "-hash-readback.bin")]
                        result["original_host_restored"] = a.action == "restore-host"
                    elif a.action == "deploy-dsp":
                        if not a.artifact:
                            raise ValueError("artifact required")
                        dcr_deploy = a.artifact.name == "c55stream-dmm-ring-dcr.dll55l"
                        wsola_deploy = a.artifact.name == "c55stream-dmm-ring-wsola.dll55l"
                        window_deploy = a.artifact.name == "c55stream-dmm-ring-window.dll55l"
                        mdec_deploy = a.artifact.name == "c55stream-dmm-ring-mdec.dll55l"
                        spu_deploy = a.artifact.name == "c55stream-dmm-ring-spu.dll55l"
                        if spu_deploy and (a.device != "n95" or a.host_version != 52):
                            raise RuntimeError("ring SPU is restricted to N95 host52")
                        if mdec_deploy and (a.device != "n95" or a.host_version not in (50,51)):
                            raise RuntimeError("ring MDEC is restricted to N95 host50")
                        if window_deploy and (a.device != "n95" or a.host_version != 49):
                            raise RuntimeError("ring CPU window is restricted to N95 host49")
                        if wsola_deploy and (a.device != "n95" or a.host_version not in (48,53)):
                            raise RuntimeError("ring WSOLA is restricted to N95 host48")
                        if dcr_deploy and (a.device != "n95" or a.host_version != 47):
                            raise RuntimeError("DCR diagnostic is restricted to N95 host47")
                        ring_deploy = (a.artifact.name == "c55stream-dmm-ring.dll55l" and a.host_version >= 38) or dcr_deploy or wsola_deploy or window_deploy or mdec_deploy or spu_deploy
                        built_dsp = "out/dsp/c55stream-dmm-ring-spu.dll55l" if spu_deploy else "out/dsp/c55stream-dmm-ring-mdec.dll55l" if mdec_deploy else "out/dsp/c55stream-dmm-ring-window.dll55l" if window_deploy else "out/dsp/c55stream-dmm-ring-wsola.dll55l" if wsola_deploy else "out/dsp/c55stream-dmm-ring-dcr.dll55l" if dcr_deploy else "out/dsp/c55stream-dmm-ring.dll55l" if ring_deploy else "out/dsp/c55stream-run-stop.dll55l"
                        if a.artifact.read_bytes() != (ROOT / built_dsp).read_bytes():
                            raise RuntimeError("D0 deployment accepts only the verified run-stop artifact")
                        if ring_deploy:
                            expected = json.loads(a.artifact_proof.read_text(encoding="utf-8"))
                            entry = next(item for item in expected["files"] if item["path"] == built_dsp)
                            if digest(a.artifact.read_bytes()) != entry["sha256"]:
                                raise RuntimeError("D1 ring artifact proof mismatch")
                        host = directory / (a.tag + "-host-readback.exe")
                        d.get(REMOTE[3], host)
                        if host.read_bytes() != (ROOT / "out/arm/c55stream.exe").read_bytes():
                            raise RuntimeError(f"install the built v{a.host_version} host before deploying DSP code")
                        current = directory / (a.tag + "-dsp-before.dll55l")
                        d.get(REMOTE[0], current)
                        if current.read_bytes() != original(REMOTE[0]):
                            raise RuntimeError("current DSP file differs from the saved original")
                        result["deployed"] = put_checked(REMOTE[0], a.artifact.read_bytes(), "-dsp-readback.dll55l")
                    elif a.action == "run":
                        allowed = ("boot-info", "processor-state", "inspect", "patcher-read-check", "pointer-snapshot", "dmm-provenance", "dmm-map", "create", "run-transfer reps=0 bytes=512 frames=8", "run-routing reps=0 bytes=512 frames=8")
                        is_wsola = re.fullmatch(r"dmm-ring-wsola frames=(8|120)", a.command)
                        is_current = re.fullmatch(r"dmm-ring-wsola-current frames=(8|120)",a.command)
                        if is_current and (a.device != "n95" or a.host_version != 53):
                            raise RuntimeError("current WSOLA is restricted to N95 host53")
                        is_mdec = re.fullmatch(r"dmm-ring-mdec batch=(1|2|4) frames=(8|120)", a.command)
                        is_spu = re.fullmatch(r"dmm-ring-spu voices=(1|8|24) frames=(8|120)", a.command)
                        if is_spu and (a.device != "n95" or a.host_version != 52):
                            raise RuntimeError("ring SPU is restricted to N95 host52")
                        if is_mdec and (a.device != "n95" or a.host_version not in (50,51)):
                            raise RuntimeError("ring MDEC is restricted to N95 host50")
                        is_ring = is_current or is_spu or is_mdec or is_wsola or re.fullmatch(r"dmm-ring(?:-native|-dcr|-window)? batch=(1|2|8|15) frames=(8|120)", a.command)
                        is_window = a.command.startswith("dmm-ring-window ")
                        if is_window and (a.device != "n95" or a.host_version != 49):
                            raise RuntimeError("ring CPU window is restricted to N95 host49")
                        if is_wsola and (a.device != "n95" or a.host_version != 48):
                            raise RuntimeError("ring WSOLA is restricted to N95 host48")
                        is_dcr = a.command.startswith("dmm-ring-dcr ")
                        if is_dcr and (a.device != "n95" or a.host_version != 47):
                            raise RuntimeError("DCR diagnostic is restricted to N95 host47")
                        if a.command not in allowed and not is_ring:
                            raise ValueError("only explicitly audited D0 commands are allowed")
                        if a.command.startswith("dmm-"):
                            accepted = json.loads((ROOT / "docs/evidence/2026-10-03/d0-attach-success.json").read_text())
                            if accepted["status"] != "complete" or accepted["devices"][a.device]["accepted_consecutive_runs"] != 3:
                                raise RuntimeError("D1 requires accepted D0 on this device")
                        host = directory / (a.tag + "-host-readback.exe")
                        d.get(REMOTE[3], host)
                        if host.read_bytes() != (ROOT / "out/arm/c55stream.exe").read_bytes():
                            raise RuntimeError(f"installed host differs from the built v{a.host_version} artifact")
                        if f"C55STREAM v{a.host_version} ".encode() not in host.read_bytes():
                            raise RuntimeError("host version marker mismatch")
                        result["host_sha256"] = digest(host.read_bytes())
                        if a.command not in ("boot-info", "processor-state", "inspect", "patcher-read-check", "pointer-snapshot", "dmm-provenance", "dmm-map"):
                            current = directory / (a.tag + "-dsp-before.dll55l")
                            d.get(REMOTE[0], current)
                            dsp_path = "out/dsp/c55stream-dmm-ring-spu.dll55l" if is_spu else "out/dsp/c55stream-dmm-ring-mdec.dll55l" if is_mdec else "out/dsp/c55stream-dmm-ring-window.dll55l" if is_window else "out/dsp/c55stream-dmm-ring-wsola.dll55l" if is_wsola or is_current else "out/dsp/c55stream-dmm-ring-dcr.dll55l" if is_dcr else "out/dsp/c55stream-dmm-ring.dll55l" if is_ring else "out/dsp/c55stream-run-stop.dll55l"
                            if current.read_bytes() != (ROOT / dsp_path).read_bytes():
                                raise RuntimeError("D0 requires the exact run-stop DSP artifact")
                            result["dsp_sha256"] = digest(current.read_bytes())
                        d.get("E:\\c55stream.log", directory / (a.tag + "-prior.log"))
                        try:
                            result["exit"] = run(d, REMOTE[3] + " " + a.command, 30, kill_on_timeout=a.allow_kill, keep_awake=a.keep_awake)
                        except Exception as exc:
                            result["run_error"] = type(exc).__name__ + ": " + str(exc)
                            try:
                                d.get("E:\\c55stream.log", directory / (a.tag + ".log"))
                            except Exception as journal_exc:
                                result["journal_error"] = type(journal_exc).__name__ + ": " + str(journal_exc)
                            raise
                        else:
                            d.get("E:\\c55stream.log", directory / (a.tag + ".log"))
                        log = (directory / (a.tag + ".log")).read_text(encoding="ascii", errors="replace")
                        if a.command.startswith("run-routing "):
                            result["diagnostic_only"] = True
                            if not log.splitlines() or log.splitlines()[-1] != "FINAL status=0" or "ROUTING snapshot=0 " not in log or "QUARANTINE" in log:
                                raise RuntimeError("routing diagnostic did not finish cleanly")
                        else:
                            validate_journal(log, a.command, a.host_version)
                        result["journal_sha256"] = digest((directory / (a.tag + ".log")).read_bytes())
                        if a.command == "pointer-snapshot":
                            result["pointers"] = {}
                            patterns = [
                                ("pdd_slot", r"POINTER pdd_slot=([0-9a-f]{8}) container=([0-9a-f]{8})"),
                                ("pdd_objects", r"POINTER pdd_count=(\d+) objects_ptr=([0-9a-f]{8})"),
                                ("factory", r"POINTER factory=([0-9a-f]{8}) expected_vtable=([0-9a-f]{8})"),
                                ("manager_ptr", r"POINTER manager_ptr=([0-9a-f]{8})"),
                                ("manager", r"POINTER manager magic=([0-9a-f]{8}) back_factory=([0-9a-f]{8}) proc_index=(\d+) common_board=([0-9a-f]{8})"),
                                ("board", r"POINTER board=([0-9a-f]{8}) board_swap_byte=([0-9a-f]{2}) context=([0-9a-f]{8})"),
                                ("context", r"POINTER ctx_reader=([0-9a-f]{8}) ctx_board=([0-9a-f]{8}) ctx_from_dsp=([0-9a-f]{8}) ctx_records=([0-9a-f]{8}) queue16=([0-9a-f]{8}) queue40=([0-9a-f]{8})"),
                                ("reader", r"POINTER shared_base=([0-9a-f]{8}) reader_swap_byte=([0-9a-f]{2})"),
                            ]
                            for key, pat in patterns:
                                m = re.search(pat, log)
                                if m:
                                    result["pointers"][key] = m.groups()
                    elif a.action == "restore":
                        result["files"] = []
                        # Host/SIS installation is a separate, explicitly recorded update.
                        for remote in REMOTE[:3]:
                            result["files"].append(put_checked(remote, original(remote), f"-restored-{len(result['files'])}.bin"))
                    elif a.action == "verify":
                        result["files"] = []
                        for index, remote in enumerate(REMOTE):
                            local = directory / (a.tag + f"-file-{index}.bin")
                            d.get(remote, local)
                            data = local.read_bytes()
                            result["files"].append({"remote": remote, "bytes": len(data),
                                                    "sha256": digest(data), "equal_original": data == original(remote)})
                        result["installed_host_matches_built"] = (
                            (directory / (a.tag + "-file-3.bin")).read_bytes() ==
                            (ROOT / "out/arm/c55stream.exe").read_bytes())
                result["info_after"] = d.cmd("INFO")
                result["complete"] = True
                if a.action == "snapshot":
                    proof.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            finally:
                d.close()
    except Exception as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"{report}: complete={result['complete']}")


def main():
    from device_work_lock import device_lock
    device=sys.argv[sys.argv.index("--device")+1] if "--device" in sys.argv else "e90"
    if device not in ("n95","e90"):
        return _main()
    with device_lock(ROOT / f"out/{device}-work.lock"):
        return _main()


if __name__ == "__main__":
    main()
