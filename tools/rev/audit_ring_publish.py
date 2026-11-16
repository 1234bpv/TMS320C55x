"""Separate compiler publication order from the remaining hardware contract."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build_report():
    proof_path = ROOT / "docs/evidence/2026-10-03/d1-native-ring-v61-artifacts.json"
    proof = json.loads(proof_path.read_text(encoding="utf-8"))
    archive = ROOT / "work/evidence/artifacts/c55stream-dmm-ring-v61"
    asm_path = archive / "stream_node-dmm-ring.asm"
    dll_path = archive / "c55stream-dmm-ring.dll55l"
    for path, original in ((asm_path, "out/dsp/stream_node-dmm-ring.asm"),
                           (dll_path, "out/dsp/c55stream-dmm-ring.dll55l")):
        expected = next(entry["sha256"] for entry in proof["files"] if entry["path"] == original)
        if hashlib.sha256(path.read_bytes()).hexdigest().upper() != expected:
            raise ValueError("archived DSP artifact differs from deployed proof")
    asm = asm_path.read_text(encoding="ascii")
    ring = asm[asm.index("_ring_exchange:"):asm.index("_STREAM_DSP_execute:")]
    execute = asm[asm.index("_STREAM_DSP_execute:"):]
    expected_tail = ["MOV #53611, *AR5(#256)", "MOV AR1, *AR5(#257)",
                     "MOV AR1, *AR5(#258)", "MOV AR1, *AR5(#259)", "RET"]
    positions = [ring.index(marker) for marker in expected_tail]
    if positions != sorted(positions):
        raise ValueError("ring control stores no longer precede return")
    call = execute.index("CALL #_ring_exchange")
    notify = execute.index("CALL #_STRM_issue", call)
    if execute[call:notify].count("CALL #_CLK_gethtime") != 1:
        raise ValueError("ring result does not precede timing and notification")
    if "MOV AR1, *AR3(#12)" not in execute[call:notify]:
        raise ValueError("notification fields are not stored before STRM_issue")
    return {"scope": "deployed DSP candidate52/protocol38 compiler artifact; no phone I/O",
            "assembly_sha256": hashlib.sha256(asm_path.read_bytes()).hexdigest().upper(),
            "DSP_sha256": hashlib.sha256(dll_path.read_bytes()).hexdigest().upper(),
            "compiler_order_verified": True,
            "order": "volatile ring output stores -> four ring completion-control stores -> return -> CLK_gethtime -> output notification fields -> STRM_issue",
            "references": [
                {"url": "https://www.ti.com/lit/ug/spru312/spru312.pdf", "section": "4.2, instruction cache applies to program-unit fetches; ring accesses are data operands"},
                {"url": "https://www.ti.com/lit/ug/spru371f/spru371f.pdf", "section": "1.7.1, CPU memory writes finish in W+; instruction completion alone must not be called an interconnect fence"},
                {"url": "https://edgeworker.ti.com/lit/pdf/spru376", "section": "4.4.3.1, write-pending and bypass show why volatile/readback alone are not a complete system barrier proof"}],
            "status": "partial",
            "native_notification_audit": "docs/evidence/2026-10-03/dsp-native-notification-audit.json",
            "posted_write_configuration": "TI's OMAP2420 GBL reference sets WPE using I/O port 0x200, mask0x80. Native BIOS5.10 user-init only clears ST3_MPNMC. The runtime WPE value and mailbox read as a SDRAM write drain remain unknown.",
            "remaining": "An OMAP2420-specific external-memory/notification publication contract is still required. Generic C55x instruction-cache documentation, absence of BCACHE exports and successful data tests do not independently prove completion of all external writes before notification visibility.",
            "hardware_evidence": "9360 fully checked packets per phone in three series; this demonstrates this synthetic protocol under measured conditions, not all future mappings/concurrent writers"}


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
