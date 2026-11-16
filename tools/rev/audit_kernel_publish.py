"""Publish the exact measured kernel compiler artifacts; no device access."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs/evidence/2026-10-04"
KERNELS = (
    ("wsola63", "c55stream-dmm-ring-wsola-v63", "", "wsola", 63, 68),
    ("mdec65", "c55stream-dmm-ring-mdec-v65", "out/dsp", "mdec", 65, 66),
    ("spu67", "c55stream-dmm-ring-spu-v67", "out/dsp", "spu", 67, 67),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def main():
    report = {"scope": "Measured N95 DSP63/65/67 compiler output, reused by WSOLA68/MDEC66/SPU67; no hardware I/O",
              "status": "compiler_order_verified_endpoint_contract_unproven",
              "claim": "On successful kernel paths, ring result stores precede completion-control stores and return; the caller then reads DCR, obtains timing, writes notification fields and calls STRM_issue.",
              "limits": ["Compiler listing order is not an OMAP interconnect fence or external-memory acknowledgement proof.",
                         "The binary hashes bind these listings to the recorded builds; this is not a fresh decode of every linked machine instruction.",
                         "Error returns can bypass result/control publication and are reported through the notification result field.",
                         "The DCR helper is read-only; WPE0 evidence does not establish mailbox/SDRAM ordering.",
                         "ARM caller/context cache completion remains a separate open gate."],
              "kernels": []}
    for name, archive, subdir, variant, revision, measured in KERNELS:
        proof_path = DEST / f"n95-{name}-artifacts.json"
        proof = json.loads(proof_path.read_text())
        files = {r["path"]: r for r in proof["files"]}
        original = f"out/dsp/stream_node-dmm-ring-{variant}.asm"
        binary = f"out/dsp/c55stream-dmm-ring-{variant}.dll55l"
        directory = ROOT / "work/evidence/artifacts" / archive / subdir
        raw = (directory / Path(original).name).read_bytes()
        dll = (directory / Path(binary).name).read_bytes()
        assert sha(raw) == files[original]["sha256"] and len(raw) == files[original]["bytes"]
        assert sha(dll) == files[binary]["sha256"] and len(dll) == files[binary]["bytes"]
        result_path = DEST / f"n95-{variant}{measured}-results.json"
        result = json.loads(result_path.read_text())
        assert result["DSP_sha256"] == sha(dll)
        canonical = raw.replace(b"\r\n", b"\n")
        # JSON lines preserve every assembler space without Git whitespace errors.
        assert raw in (canonical, canonical.replace(b"\n", b"\r\n"))
        line_endings = "LF" if raw == canonical else "CRLF"
        published = DEST / f"n95-{name}-compiler-assembly.json"
        serialized = (json.dumps({"lines": canonical.decode("ascii").splitlines(keepends=True)}, indent=2) + "\n").encode("utf-8")
        published.write_bytes(serialized)
        report["kernels"].append({"kernel": name, "DSP_revision": revision, "measured_cohort": measured,
                                  "protocol": proof["protocol"], "DSP_sha256": sha(dll),
                                  "assembly": {"path": published.relative_to(ROOT).as_posix(),
                                               "sha256": sha(serialized), "wire_sha256": sha(raw),
                                               "canonical_assembly_sha256": sha(canonical), "wire_line_endings": line_endings,
                                               "original_path": original, "original_bytes": len(raw)},
                                  "build_proof": {"path": proof_path.relative_to(ROOT).as_posix(),
                                                  "sha256": sha(proof_path.read_bytes().replace(b"\r\n", b"\n"))},
                                  "measured_results": {"path": result_path.relative_to(ROOT).as_posix(),
                                                       "sha256": sha(result_path.read_bytes().replace(b"\r\n", b"\n"))}})
    target = DEST / "n95-kernel-publish-audit.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
