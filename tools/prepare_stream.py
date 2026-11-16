"""Back up stream files, record the clocks, deploy and read back artifacts.

This performs no c55stream START or DSP RUN. Use run_stream.py separately.
The clock probe uses the existing ocprobe executable and its read-only mode.
"""
import argparse
import contextlib
import datetime
import hashlib
import json
import pathlib
import re
import time

from strict_net import Device

ROOT = pathlib.Path(__file__).resolve().parents[1]
CLOCK_PROFILES = {
    "n95": {"uid": 0x20002D84, "profile": "RM-320 35.0.001/31.0.015", "restore_code": 100},
    "e90": {"uid": 0x20002496, "profile": "RA-6 400.34.93", "restore_code": 1},
}


def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()


def stock_clock_matches(clock, device):
    if "RINGCLOCK v1 " in clock:
        expected = {"CM_CLKSEL1_PLL": ("c6008540", "00056400"),
                    "CM_CLKSEL2_PLL": ("c6008544", "00000002"),
                    "CM_CLKSEL_MPU": ("c6008140", "00000002"),
                    "CM_CLKSEL1_CORE": ("c6008240", "04360626"),
                    "CM_FCLKEN_DSP": ("c6008800", "00000401"),
                    "CM_ICLKEN_DSP": ("c6008810", "00000002"),
                    "CM_IDLEST_DSP": ("c6008820", "00000000"),
                    "CM_CLKSEL_DSP": ("c6008840", "00000343")}
        return (device == "e90" and
                clock.splitlines()[0] == "RINGCLOCK v1 machine=20002496 driver=RDomain.ldd copy_control=102 free_shadow_control=104" and
                clock.count("RINGCLOCK v1 ") == 1 and
                "RINGCLOCK firmware_guard=0 profile=RA-6/400.34.93" in clock and
                "RINGCLOCK prepare=0 " in clock and
                "RINGCLOCK read_regs=0 single_snapshot=1 prcm_writes=0 dsp_open=0" in clock and
                "RINGCLOCK restore=0 original_body_verified=1" in clock and
                "RINGCLOCK FREQUENCY core_khz=660480 arm_khz=330240 bus_khz=110080 dsp_khz=220160" in clock and
                "RINGCLOCK PASS stock=1 compatible_driver_api=1 prcm_writes=0 dsp_open=0" in clock and
                clock.splitlines()[-1] == "FINAL status=0" and
                re.findall(r"^FINAL status=(-?\d+)$", clock, re.M) == ["0"] and
                all(re.findall(rf"^RINGCLOCK REG {name} address=([0-9a-f]+) value=([0-9a-f]+) expected=([0-9a-f]+)$", clock, re.M)
                    == [(address, value, value)] for name, (address, value) in expected.items()))
    # VerifyRestored returns a DVFS percentage on N95 and a six-word live
    # Usbc body comparison on E90. The old probe labels both as DoControl.
    # Both values were observed after patch restoration.
    profile = CLOCK_PROFILES[device]
    return ("NOT STOCK" not in clock and "stock mult 86" in clock and
            "fields: DSP[3:0]=3 " in clock and "DSP probe done" in clock and
            "EMachineUid = %d" % profile["uid"] in clock and
            "profile: " + profile["profile"] in clock and
            "restore check: stock DoControl(1,0) -> %d  " % profile["restore_code"] in clock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--device", choices=("n95", "e90"), required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--host", type=pathlib.Path)
    parser.add_argument("--dsp", type=pathlib.Path, required=True)
    parser.add_argument("--expect-dsp-sha256", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.tag):
        parser.error("tag must contain letters, digits, underscores and hyphens")
    if not re.fullmatch(r"[A-Fa-f0-9]{64}", args.expect_dsp_sha256):
        parser.error("expected DSP hash must have 64 hex digits")
    if args.host and args.device != "n95":
        parser.error("direct EXE deployment is verified only on N95; use SIS on E90")
    host = args.host.read_bytes() if args.host else None
    dsp = args.dsp.read_bytes()
    if not dsp or (host is not None and len(host) < 120):
        parser.error("empty DSP or invalid host artifact")
    directory = ROOT / "work/evidence" / args.device
    directory.mkdir(parents=True, exist_ok=True)
    transport = directory / (args.tag + "-preparation-transport.txt")
    proof = directory / (args.tag + "-preparation.json")
    if any(directory.glob(args.tag + "*")):
        parser.error("tag already exists; evidence is never overwritten")
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "device": args.device, "ip": args.ip, "files": [],
        "clock_log_restored": False, "complete": False,
    }

    def local(suffix):
        return directory / (args.tag + suffix)

    def backup(remote, suffix):
        path = local(suffix)
        device.get(remote, path)
        data = path.read_bytes()
        result["files"].append({
            "remote": remote, "backup": path.relative_to(ROOT).as_posix(),
            "bytes": len(data), "sha256": sha256(data),
        })
        return data

    def deploy(remote, data, suffix):
        path = local(suffix)
        device.put(remote, data)
        device.get(remote, path)
        if path.read_bytes() != data:
            raise RuntimeError("readback mismatch: " + remote)
        result["files"].append({
            "remote": remote, "readback": path.relative_to(ROOT).as_posix(),
            "bytes": len(data), "sha256": sha256(data), "equal": True,
        })

    def call(command):
        print(datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
        return device.cmd(command)

    try:
        with transport.open("x", encoding="utf-8") as journal, contextlib.redirect_stdout(journal):
            device = Device(args.ip, args.device)
            try:
                result["info_before"] = call("INFO")
                for name in ("c55stream*", "ocprobe*"):
                    if any(line.startswith("1 ") for line in call("PS " + name)):
                        raise RuntimeError("process already running: " + name)
                previous_dsp = backup("E:\\c55stream.dll55l", "-before.dll55l")
                if sha256(previous_dsp) != args.expect_dsp_sha256.upper():
                    raise RuntimeError("current phone DSP differs from expected image")
                backup("E:\\c55stream.log", "-before.log")
                if host is not None:
                    backup("E:\\sys\\bin\\c55stream.exe", "-before.exe")
                    backup("C:\\sys\\hash\\c55stream.exe", "-before.hash")
                original_clock = backup("E:\\ocprobe.log", "-before-ocprobe.log")
                clock_started = False
                try:
                    clock_started = True
                    command = "START E:\\sys\\bin\\ocprobe.exe patcher dsp 1"
                    if args.device == "e90":
                        command += " e90"
                    response = call(command)
                    match = re.fullmatch(r"OK proc (\d+)", "\n".join(response))
                    if not match:
                        raise RuntimeError("clock probe START returned no process id")
                    process = match.group(1)
                    finished = False
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        if not any(line.startswith("1 ") for line in call("PS ocprobe*")):
                            if call("WAIT " + process + " 1") != ["EXIT 0 Kill"]:
                                raise RuntimeError("clock probe failed")
                            finished = True
                            break
                        time.sleep(0.5)
                    if not finished:
                        call("KILL " + process)
                        raise RuntimeError("clock probe exceeded its deadline")
                    device.get("E:\\ocprobe.log", local("-clock.log"))
                    clock = local("-clock.log").read_text(encoding="ascii", errors="replace")
                    result["clock_log"] = local("-clock.log").relative_to(ROOT).as_posix()
                    result["clock_profile"] = CLOCK_PROFILES[args.device]
                    # Recorded, not enforced: the E90 lives overclocked and must not be
                    # returned to stock (owner's decision 2026-10-22), so a run on a
                    # raised clock is allowed and the clock log goes with the result.
                    result["stock_clock"] = stock_clock_matches(clock, args.device)
                finally:
                    if clock_started:
                        deploy("E:\\ocprobe.log", original_clock, "-ocprobe-restored.log")
                        result["clock_log_restored"] = True
                if host is not None:
                    deploy("E:\\sys\\bin\\c55stream.exe", host, "-host-readback.exe")
                    deploy("C:\\sys\\hash\\c55stream.exe", hashlib.sha1(host).digest(), "-host-readback.hash")
                deploy("E:\\c55stream.dll55l", dsp, "-dsp-readback.dll55l")
                result["info_after"] = call("INFO")
                result["complete"] = True
            finally:
                device.close()
    except Exception as error:
        result["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        proof.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print("PREPARATION " + str(proof) + " complete=" + str(result["complete"]))


if __name__ == "__main__":
    main()
