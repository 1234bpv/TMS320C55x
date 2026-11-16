"""Verify and archive the worker-stream build before any phone deployment."""
import argparse
import datetime
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from extract_doff_section import Doff, checksum, sha256
from paths import SHARED


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--revision", type=int, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--host-version", type=int, choices=(16,17,18,19,20), default=20)
    p.add_argument("--protocol", type=int, choices=(16,17,18,19,20), default=20)
    a = p.parse_args()
    if a.revision < 1 or a.report.exists():
        p.error("positive revision and a new report path are required")
    dll = ROOT / "out/dsp/c55stream-worker-stream.dll55l"
    asm = ROOT / "out/dsp/stream_node-worker-stream.asm"
    host = ROOT / "out/arm/c55stream.exe"
    data = dll.read_bytes()
    dump = subprocess.run([str(SHARED / "toolchain/ti/dspbridge/dsp/doffbuild/bin/DLLdump.exe"), str(dll)],
                          capture_output=True, text=True, timeout=30, check=True)
    if "Verification PASSED" not in dump.stdout:
        raise RuntimeError("DLLdump did not verify headers/sections/symbols")
    strings_size, _, reshuffle, _, symbols, _, sections, _, version, target, flags, _, _ = struct.unpack_from("<4I8HI", data)
    if version or target != 0x9C or reshuffle != 0x10203 or flags != 0x12E0 or checksum(data[:36]) != 0xFFFFFFFF:
        raise RuntimeError("unexpected dynamic DOFF format")
    strings = data[56:56+strings_size]
    start = 56 + strings_size + sections * 28
    imports = []
    for i in range(symbols):
        name, value, section, storage = struct.unpack_from("<IIhh", data, start+i*12)
        if section == 0 and storage == 2:
            imports.append(strings[name:strings.index(0, name)].decode("ascii"))
    bases = [Doff(SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof"),
             Doff(ROOT / "work/evidence/e90/baseimage.dof")]
    for base in bases:
        missing = set(imports) - base.symbols.keys()
        if missing:
            raise RuntimeError("undefined imports: " + str(missing))
    registration = ROOT / "src/dsp/stream_resident_dcd.s55"
    if b".dcd_register" not in strings or b".dspbridge_symbols" not in strings:
        raise RuntimeError("missing native registration sections")
    text = asm.read_text(encoding="ascii")
    for marker in ("_stream_worker:", "_stream_worker_loop:", "_join_stream_worker:",
                   "CALL #_NODE_wait", "CALL #_STRM_reclaim", "CALL #_SEM_pend",
                   "CALL #_TSK_create", "MOV #2048,", "MOV #512,"):
        if marker not in text:
            raise RuntimeError("missing assembler evidence: " + marker)
    extra = ()
    if a.protocol >= 19:
        extra = (ROOT / "out/dsp/wsola_dsp.asm", ROOT / "out/dsp/bench_dsp.asm")
        if "CALL #_dsp_wsola_best" not in text:
            raise RuntimeError("missing WSOLA worker call")
        wsola_asm, dot_asm = (p.read_text(encoding="ascii") for p in extra)
        if "CALL #_dsp_q15_dot" not in wsola_asm or "MACM" not in dot_asm or "RPT" not in dot_asm:
            raise RuntimeError("WSOLA contiguous dot/MAC assembler missing")
        if f"C55STREAM v{a.host_version} ".encode() not in host.read_bytes():
            raise RuntimeError("host version marker missing")
    archived = ROOT / f"work/evidence/artifacts/c55stream-worker-stream-v{a.revision}"
    archived.mkdir(parents=True, exist_ok=False)
    for path in (dll, asm, host) + extra:
        (archived / path.name).write_bytes(path.read_bytes())
    report = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "revision": a.revision, "host_version": a.host_version, "variant": "worker-stream",
        "bytes": len(data), "sha256": sha256(data),
        "source_sha256": sha256((ROOT / "src/dsp/stream_node.c").read_bytes()),
        "assembler_sha256": sha256(asm.read_bytes()),
        "host_bytes": host.stat().st_size, "host_sha256": sha256(host.read_bytes()),
        "host_source_sha256": sha256((ROOT / "src/c55stream.cpp").read_bytes()),
        "host_mmp_sha256": sha256((ROOT / "group/c55stream.mmp").read_bytes()),
        "registration_source_sha256": sha256(registration.read_bytes()),
        "registration": "node0 plus generic library2", "imports": imports,
        "all_imports_exist_in_both_baseimages": True,
        "dll_dump_verification": "headers/sections/symbols passed",
        "worker_priority": 15, "stack_words": 2048, "sysstack_words": 512,
        "stream_timeout_ms": 1000, "stream_wait_ms": 100,
        "idle_wait_limit": 100, "join_timeout_bios_ticks": 5000,
        "create_gate": "blocked2/stageC561/cookie00123456/input_pending1/output_pending0",
        "delete_gate": "completion semaphore, terminated3/stageC564/cookie/status0, all buffers reclaimed, task/SEM freed",
        "protocol": a.protocol, "official_run": False,
        "packet_size_contract": ({"echo_min_bytes":512,"echo_max_bytes":4096,"even_bytes":True,
                                  "header_bytes":32,"echo_equal_input_output":True,
                                  "wsola_input_bytes":1792,"wsola_output_bytes":48,
                                  "q15_values":240,"wsola_values":880} if a.protocol>=19 else
                                 {"min_bytes":512,"max_bytes":4096,"even_bytes":True,
                                  "header_bytes":32,"equal_input_output":True,
                                  "q15_values":240} if a.protocol>=18 else {"fixed_bytes":512}),
        "hardware_verified": False,
        "limits": ["No hardware result is inferred from this artifact check.",
                   "Heavy MAC/audio coexistence at priority15 is not established.",
                   "An active task or pending stream fails delete; it cannot free its context."],
    }
    if a.protocol >= 19:
        report["wsola_source_sha256"] = sha256((ROOT / "src/dsp/wsola_dsp.c").read_bytes())
        report["arm_reference_source_sha256"] = sha256((ROOT / "src/wsola_reference.cpp").read_bytes())
        report["wsola_assembler_sha256"] = sha256(extra[0].read_bytes())
        report["dot_assembler_sha256"] = sha256(extra[1].read_bytes())
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
