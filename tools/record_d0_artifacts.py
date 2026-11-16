"""Verify and archive the E90 RUN-stop candidate; no phone access."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", type=int, default=21)
    parser.add_argument("--host-version", type=int, choices=range(21, 50), default=21)
    parser.add_argument("--host-sis", type=Path, default=ROOT / "out/sis/c55stream_sha1.sis")
    parser.add_argument("--dsp-build-log", default=None)
    parser.add_argument("--host-build-log", default=None)
    parser.add_argument("--host-sis-log", default=None)
    parser.add_argument("--restore-sis", type=Path, default=ROOT / "out/sis/c55stream-restore-v20_sha1.sis")
    parser.add_argument("--restore-sis-log", default="out/d0-restore-v20-sis-build.log")
    parser.add_argument("--dsp-variant", choices=("run-stop", "run-message-diag", "run-exit-diag", "worker-message", "dmm-ring", "dmm-ring-dcr", "dmm-ring-wsola", "dmm-ring-window"), default="run-stop")
    parser.add_argument("--reference-node", type=Path)
    parser.add_argument("--reference-derivation", type=Path, default=ROOT / "docs/evidence/2026-10-01/e90-d0-native-library2-derivation.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/evidence/2026-10-01/d0-run-stop-v21-artifacts.json")
    args = parser.parse_args()
    if args.revision < 21 or args.report.exists():
        parser.error("a new positive candidate revision and report path are required")
    dll = ROOT / f"out/dsp/c55stream-{args.dsp_variant}.dll55l"
    data = dll.read_bytes()
    dump = subprocess.run([str(SHARED / "toolchain/ti/dspbridge/dsp/doffbuild/bin/DLLdump.exe"), str(dll)],
                          capture_output=True, text=True, timeout=30, check=True)
    if "Verification PASSED" not in dump.stdout:
        raise RuntimeError("DOFF verification failed")
    size, _, reshuffle, _, symbols, _, sections, _, version, target, flags, _, _ = struct.unpack_from("<4I8HI", data)
    if (version, target, reshuffle, flags, checksum(data[:36])) != (0, 0x9C, 0x10203, 0x12E0, 0xFFFFFFFF):
        raise RuntimeError("unexpected DOFF header")
    strings = data[56:56 + size]
    imports = []
    start = 56 + size + sections * 28
    for i in range(symbols):
        name, _, section, storage = struct.unpack_from("<IIhh", data, start + i * 12)
        if section == 0 and storage == 2:
            imports.append(strings[name:strings.index(0, name)].decode("ascii"))
    base = Doff(ROOT / "work/evidence/e90/baseimage.dof")
    if set(imports) - base.symbols.keys():
        raise RuntimeError("unresolved E90 baseimage imports")
    if args.dsp_variant in ("dmm-ring-dcr", "dmm-ring-wsola"):
        n95 = Doff(SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
        if set(imports) - n95.symbols.keys() or args.host_version != (48 if args.dsp_variant == "dmm-ring-wsola" else 47):
            raise RuntimeError("DCR diagnostic needs N95 imports and host47")
    if args.dsp_variant == "dmm-ring-window":
        n95 = Doff(SHARED / "eka2l1/data/drives/z/rm-320/resource/plugins/baseimage.dof")
        if set(imports)-n95.symbols.keys() or args.host_version != 49:
            raise RuntimeError("CPU window needs N95 imports and host49")
    assembly = ROOT / f"out/dsp/stream_node-{args.dsp_variant}.asm"
    asm = assembly.read_text(encoding="ascii")
    markers = {
        "run-stop": ("_STREAM_DSP_execute:", "MOV #21,", "CALL #_STRM_reclaim", "MOV #32768,"),
        "run-message-diag": ("_STREAM_DSP_execute:", "MOV #15,", "CALL #_NODE_getMsg", "CALL #_NODE_putMsg", "CALL #_STRM_reclaim"),
        "run-exit-diag": ("_STREAM_DSP_execute:", "MOV #25,", "CALL #_NODE_getMsg", "CALL #_STRM_idle", "CALL #_STRM_reclaim"),
        "worker-message": ("_STREAM_DSP_execute:", "MOV #26,", "CALL #_NODE_putMsg", "CALL #_TSK_stat", "CALL #_TSK_delete", "CALL #_STRM_reclaim"),
        "dmm-ring": ("_ring_exchange:", "CALL #_ring_exchange", "MOV #38,", "CALL #_NODE_getMsg", "CALL #_STRM_idle", "CALL #_STRM_reclaim"),
        "dmm-ring-dcr": ("_ring_exchange:", "CALL #_ring_exchange", "MOV #39,", "CALL #_ring_read_dcr", "CALL #_NODE_getMsg", "CALL #_STRM_idle", "CALL #_STRM_reclaim"),
        "dmm-ring-window": ("_ring_exchange:", "CALL #_ring_exchange", "MOV #38,", "CALL #_NODE_getMsg", "CALL #_STRM_idle", "CALL #_STRM_reclaim"),
        "dmm-ring-wsola": ("_ring_wsola_exchange:", "CALL #_ring_wsola_exchange", "CALL #_dsp_wsola_best", "MOV #40,", "CALL #_ring_read_dcr", "CALL #_NODE_getMsg", "CALL #_STRM_idle", "CALL #_STRM_reclaim"),
    }[args.dsp_variant]
    for marker in markers:
        if marker not in asm:
            raise RuntimeError("missing assembler marker " + marker)
    registration = ROOT / "src/dsp/stream_resident_dcd.s55"
    if b".dcd_register" not in strings or b".dspbridge_symbols" not in strings:
        raise RuntimeError("native registration missing")
    host = ROOT / "out/arm/c55stream.exe"
    if f"C55STREAM v{args.host_version} ".encode() not in host.read_bytes() or b"QUARANTINE" not in host.read_bytes():
        raise RuntimeError("fail-stop host version marker missing")
    if args.host_version >= 22 and "EFileShareAny" not in (ROOT / "src/c55stream.cpp").read_text(encoding="utf-8"):
        raise RuntimeError("live journal sharing missing")
    paths = [dll, assembly, host, registration, ROOT / "src/c55stream.cpp",
             ROOT / "src/dsp/stream_node.c", ROOT / "tools/build_stream_node.cmd",
             ROOT / "group/c55stream.mmp", args.host_sis.resolve(),
             args.restore_sis.resolve()]
    if args.dsp_variant in ("dmm-ring", "dmm-ring-dcr", "dmm-ring-wsola", "dmm-ring-window"):
        paths.extend((ROOT / "tools/e90_task_session.py", ROOT / "tools/run_ring_series.py"))
    if args.dsp_variant in ("dmm-ring-dcr", "dmm-ring-wsola"):
        if asm.count("CALL #_ring_read_dcr") != (4 if args.dsp_variant == "dmm-ring-wsola" else 2):
            raise RuntimeError("DCR diagnostic must perform exactly two reads per exchange")
        paths.extend((ROOT / "src/dsp/dcr_read.s55", ROOT / "tools/rev/audit_dcr_read.py"))
    if args.dsp_variant == "dmm-ring-wsola":
        paths.extend((ROOT / "src/dsp/wsola_dsp.c", ROOT / "src/dsp/bench_dsp.c", ROOT / "src/wsola_reference.cpp", ROOT / "src/wsola_reference.h"))
    if args.dsp_variant == "dmm-ring-window":
        paths.append(ROOT / "docs/evidence/2026-10-04/n95-cpu-counter-results.json")
    if args.dsp_variant == "worker-message":
        paths.extend((ROOT / "src/dsp/bios_task.h", ROOT / "src/dsp/node.h"))
    reference_proof = None
    if args.reference_node:
        reference = args.reference_node.resolve()
        refdata = reference.read_bytes()
        refdump = subprocess.run([str(SHARED / "toolchain/ti/dspbridge/dsp/doffbuild/bin/DLLdump.exe"), str(reference)],
                                 capture_output=True, text=True, timeout=30, check=True)
        if "Verification PASSED" not in refdump.stdout or b"STRMCOPY_TI_execute" not in refdata:
            raise RuntimeError("invalid native STRMCOPY reference")
        reference_proof = {"path": reference.relative_to(ROOT).as_posix(), "bytes": len(refdata),
                           "sha256": sha256(refdata), "DLLdump_verification": True,
                           "phone_path": "Z:\\system\\apps\\strmcopy\\strmcopydyn.dll55l",
                           "limits": "ROM control only; no clean native-copy RUN verified yet"}
        paths.append(reference)
    derivation = None
    if args.host_version == 24:
        derivation_path = args.reference_derivation.resolve()
        derivation = json.loads(derivation_path.read_text(encoding="utf-8"))
        derived = ROOT / derivation["derived_path"]
        if not reference_proof or sha256(derived.read_bytes()) != derivation["derived_sha256"] or reference_proof["sha256"] != derivation["source_sha256"]:
            raise RuntimeError("native library2 proof mismatch")
        paths.extend((derived, derivation_path))
    archive = ROOT / f"work/evidence/artifacts/c55stream-{args.dsp_variant}-v{args.revision}"
    archive.mkdir(parents=True, exist_ok=True)
    for path in paths[:3] + [args.host_sis.resolve(), args.restore_sis.resolve()]:
        (archive / path.name).write_bytes(path.read_bytes())
    proof = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "variant": {"run-stop": "generic library2, official RUN, final output reclaim, await RMS_EXIT before EXITACK", "run-message-diag": "generic library2, official RUN, three STRM message snapshots; NODE_getMsg(0)/putMsg(0); no timed cleanup claim", "run-exit-diag": "generic library2, eight checked packets, STRM snapshots before RMS_EXIT and combined after receipt/idle; extra output reissue perturbs cleanup, diagnostic only", "worker-message": "generic library2, finite CREATED-state worker; prearmed ARM receive, one outbound MSG and read-only STRM snapshot; no official RUN/EXITACK", "dmm-ring": "D1 16KiB shared batch ring; whole-region ownership; notification streams; official RUN and proven stop/delete lifecycle", "dmm-ring-dcr": "Distinct N95 DCR I/O port0x200 read-only diagnostic before/after native 16KiB ring exchange; no DCR writes; not retrospective clock/publication proof for candidate61", "dmm-ring-window": "Distinct N95 host49 aggregate CPU window: settled boundaries, pack/cache/full checks inside, deferred file I/O, no useful ARM W; protocol38 transport", "dmm-ring-wsola": "Distinct N95 WSOLA coarse/refine search through native16KiB ring: four input slots, one output slot; ARM scalar baseline; DCR read-only brackets; no useful ARM W/emulator changes"}[args.dsp_variant],
        "candidate_revision": args.revision,
        "host_mode": "E90 ROM STRMCOPY_TI native-copy control; own run-stop retained, not scheduled" if args.host_version in (23,24) else "own DSP candidate",
        "native_reference": reference_proof,
        "native_library2": derivation,
        "host_version": args.host_version, "protocol": {"run-stop":21,"run-message-diag":15,"run-exit-diag":25,"worker-message":26,"dmm-ring":38,"dmm-ring-dcr":39,"dmm-ring-wsola":40,"dmm-ring-window":38}[args.dsp_variant], "hardware_verified": False,
        "d0_accepted_runs": 0, "dll_dump_verification": True,
        "imports_exist_in_saved_e90_baseimage": True, "imports": imports,
        "files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                   "sha256": sha256(p.read_bytes())} for p in paths],
        "builds": [{"log": name, "exit_code": 0} for name in
                   (args.host_build_log or f"out/d0-host-v{args.host_version}-build.log", args.dsp_build_log or (f"out/d0-run-stop-v{args.revision}-build.log" if args.revision > 21 else "out/d0-run-stop-build-final.log"),
                    args.host_sis_log or f"out/d0-host-v{args.host_version}-sis.log", args.restore_sis_log)],
        "limits": ["Assembly/import checks are not proof of RMS EXITACK delivery.",
                   "Fail-stop retains ownership and requires manual recovery; cancel safety is not proven.",
                   "The restore SIS contains the saved original v20 EXE; its package revision is independent of host version."],
    }
    if args.dsp_variant in ("dmm-ring-dcr", "dmm-ring-wsola"):
        from audit_dcr_read import build_report
        proof["read_only_DCR_instruction_audit"] = build_report(args.dsp_variant)
        proof["imports_exist_in_saved_n95_baseimage"] = True
    if args.dsp_variant == "dmm-ring-window":
        proof["imports_exist_in_saved_n95_baseimage"] = True
        proof["CPU_window_limits"] = "Settling boundary yields; pack/cache/full correctness checks inside; file I/O and ARM baseline outside. CPU qualified only after on-device boundary checks, not retrospective correction of candidate61."
    for build in proof["builds"]:
        if "EXIT_CODE=0\n" not in (ROOT / build["log"]).read_text(encoding="utf-8"):
            raise RuntimeError("missing successful bounded build metadata")
    report = args.report
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x", encoding="utf-8") as f:
        f.write(json.dumps(proof, indent=2) + "\n")
    print(f"Verified DOFF, {len(imports)} E90 imports, v{args.host_version} host; hardware runs=0; {report}")


if __name__ == "__main__":
    main()
