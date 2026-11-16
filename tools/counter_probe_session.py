"""Bounded N95-only counter calibration; owns only three initially absent files."""
import argparse
import contextlib
import datetime
import hashlib
import json
import re
from pathlib import Path

from e90_task_session import run
from strict_net import Device
from summarize_ring import boot, digest

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "work/evidence/n95/d0-20261003-clean34"
PROOF = ROOT / "docs/evidence/2026-10-04/n95-counterprobe-artifacts.json"
REMOTES = ("E:\\sys\\bin\\counterprobe.exe", "C:\\sys\\hash\\counterprobe.exe", "E:\\counterprobe.log")
EPOCH = "62209 boot 0 by n"


def validate(text):
    lines = text.splitlines()
    assert lines[0] == "COUNTERPROBE v1 machine=20002d84 fast_counter_hz=32768 samples=36 prime_busy_us=20000 no_dsp=1 no_patcher=1 no_performance_reservation=1"
    pattern = r"CPU SAMPLE index=(\d+) repeat=(\d+) sleep=([01]) boundary_yield=([01]) requested_us=(\d+) inner_ticks=(\d+) outer_ticks=(\d+) nticks=(\d+) utc_us=(\d+) before_rc=0 after_rc=0 before_hi=([0-9a-f]{8}) before_lo=([0-9a-f]{8}) after_hi=([0-9a-f]{8}) after_lo=([0-9a-f]{8})"
    assert len(lines) == 38 and re.fullmatch(r"FINAL status=0 sink=[0-9a-f]{8}",lines[-1])
    rows = [re.fullmatch(pattern,line) for line in lines[1:-1]]
    assert all(rows)
    assert [int(row[1]) for row in rows] == list(range(36))
    assert {(int(r[2]),int(r[3]),int(r[4]),int(r[5])) for r in rows} == {
        (repeat,sleep,yield_,duration) for repeat in range(3) for sleep in range(2)
        for yield_ in range(2) for duration in (1000,10000,200000)}
    for row in rows:
        assert int(row[7]) >= int(row[6]) > 0 and int(row[9]) > 0
        assert int(row[12]+row[13],16) >= int(row[10]+row[11],16)
    return [row.groups() for row in rows]


def record():
    assert not PROOF.exists(), "proof already exists"
    exe = ROOT / "out/arm/counterprobe.exe"
    assert b"COUNTERPROBE v1 " in exe.read_bytes()
    files = [exe,ROOT / "src/cpu_counter_probe.cpp",ROOT / "tools/stage_counter_probe.py",
             ROOT / "tools/build_counter_probe.cmd",ROOT / "tools/counter_probe_session.py",
             ROOT / "out/counterprobe-build/group/counterprobe.mmp",ROOT / "out/n95-counter-probe-build01.log"]
    report = {"scope":"standalone N95 user-mode CPU counter calibration; no DSP/patcher/DVFS writes",
              "executable_sha256":digest(exe),"files":[{"path":p.relative_to(ROOT).as_posix(),"sha256":digest(p),"bytes":p.stat().st_size} for p in files]}
    PROOF.write_bytes((json.dumps(report,indent=2)+"\n").encode())
    print(PROOF)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("record","deploy","run","remove"))
    parser.add_argument("--tag")
    args = parser.parse_args()
    if args.action == "record":
        record()
        return
    if not args.tag or not re.fullmatch(r"[a-z0-9-]+",args.tag) or any(DIRECTORY.glob(args.tag+"*")):
        parser.error("a unique lowercase tag is required")
    proof = json.loads(PROOF.read_text())
    exe = (ROOT / "out/arm/counterprobe.exe").read_bytes()
    assert hashlib.sha256(exe).hexdigest().upper() == proof["executable_sha256"]
    payloads = (exe,hashlib.sha1(exe).digest())
    report = {"action":args.action,"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"complete":False,"files":[]}
    try:
        with (DIRECTORY / (args.tag+"-transport.txt")).open("x",encoding="utf-8") as stream,contextlib.redirect_stdout(stream):
            d = Device("192.168.3.22","n95",connect_timeout=8)
            try:
                report["info_before"] = d.cmd("INFO")
                assert boot(report) == EPOCH, "daemon epoch changed; stop before mutation/START"
                for name in ("counterprobe*","c55stream*","ocprobe*"):
                    assert d.cmd("PS "+name) == ["OK ps 0"]
                if args.action == "deploy":
                    report["absent_before"] = [d.cmd("LS "+p) for p in REMOTES]
                    assert report["absent_before"] == [["OK ls 0"]]*3,"refuse preexisting files"
                for i,(remote,payload) in enumerate(zip(REMOTES,payloads)):
                    if args.action == "deploy":
                        d.put(remote,payload)
                    path = DIRECTORY / (args.tag+f"-readback-{i}.bin")
                    d.get(remote,path)
                    assert path.read_bytes()==payload,"artifact drift: "+remote
                    report["files"].append({"remote":remote,"sha256":digest(path),"equal":True})
                if args.action == "run":
                    report["exit"] = run(d,REMOTES[0],30)
                    log = DIRECTORY / (args.tag+".log")
                    d.get(REMOTES[2],log)
                    validate(log.read_text(encoding="ascii"))
                    report["journal_sha256"] = digest(log)
                elif args.action == "remove":
                    # Require our successful deployment and exact final journal before removal.
                    deployed = json.loads((DIRECTORY / "counterprobe-deploy01.json").read_text())
                    final_run = json.loads((DIRECTORY / "counterprobe-series03.json").read_text())
                    assert deployed["complete"] and deployed["absent_before"]==[["OK ls 0"]]*3 and final_run["complete"]
                    remote_log = DIRECTORY / (args.tag+"-log-readback.log")
                    d.get(REMOTES[2],remote_log)
                    assert digest(remote_log)==final_run["journal_sha256"]
                    for remote in REMOTES:
                        assert d.cmd("DEL "+remote)==["OK 0"]
                        assert d.cmd("LS "+remote)==["OK ls 0"]
                    report["absent_after"] = True
                report["info_after"] = d.cmd("INFO")
                assert boot(report,"info_after")==EPOCH
                report["complete"] = True
            finally:
                d.close()
    finally:
        (DIRECTORY / (args.tag+".json")).write_bytes((json.dumps(report,indent=2)+"\n").encode())
        print(json.dumps(report,indent=2))


if __name__ == "__main__":
    main()
