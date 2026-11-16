"""Check full published compiler listings independently of local build archives."""
import hashlib
import json
import re

from verify_ring_publication import ROOT, checked


def instructions(text):
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0].strip()
        code = re.sub(r"^\|\|\s*", "", code)
        if code and not code.startswith((".", "*")):
            rows.append((number, code))
    return rows


def one(rows, code):
    found = [i for i, (_, value) in enumerate(rows) if value == code]
    assert len(found) == 1, (code, found)
    return found[0]


def main():
    path = ROOT / "docs/evidence/2026-10-04/n95-kernel-publish-audit.json"
    report = json.loads(path.read_text())
    assert report["status"] == "compiler_order_verified_endpoint_contract_unproven"
    assert [r["kernel"] for r in report["kernels"]] == ["wsola63", "mdec65", "spu67"]
    configs = {"wsola63": ("wsola", 40, "AR6", 4, "MOV #40, *AR5(#23)"),
               "mdec65": ("mdec", 41, "AR5", 5, "MOV HI(AC0), *AR3(#4369)"),
               "spu67": ("spu", 42, "AR5", 5, "MOV HI(AC1), *AR3(#4369)")}
    for entry in report["kernels"]:
        name = entry["kernel"]; variant, protocol, ringreg, fields, last_payload = configs[name]
        listing = json.loads(checked(entry["assembly"]["path"], entry["assembly"]["sha256"]))
        asm = "".join(listing["lines"])
        raw = asm.encode("ascii")
        assert hashlib.sha256(raw).hexdigest().upper() == entry["assembly"]["canonical_assembly_sha256"]
        assert entry["assembly"]["wire_line_endings"] in ("LF", "CRLF")
        wire = raw if entry["assembly"]["wire_line_endings"] == "LF" else raw.replace(b"\n", b"\r\n")
        assert hashlib.sha256(wire).hexdigest().upper() == entry["assembly"]["wire_sha256"]
        assert len(wire) == entry["assembly"]["original_bytes"]
        proof = json.loads(checked(entry["build_proof"]["path"], entry["build_proof"]["sha256"]))
        result = json.loads(checked(entry["measured_results"]["path"], entry["measured_results"]["sha256"]))
        files = {r["path"]: r for r in proof["files"]}
        original = files[entry["assembly"]["original_path"]]
        assert entry["assembly"]["wire_sha256"] == original["sha256"]
        assert entry["assembly"]["original_bytes"] == original["bytes"]
        assert files[f"out/dsp/c55stream-dmm-ring-{variant}.dll55l"]["sha256"] == entry["DSP_sha256"] == result["DSP_sha256"]
        assert entry["protocol"] == proof["protocol"] == protocol
        rows = instructions(asm)
        start = one(rows, f"_ring_{variant}_exchange:")
        execute = one(rows, "_STREAM_DSP_execute:")
        kernel = rows[start:execute]
        assert one(kernel, f"MOV AC0, X{ringreg}") < one(kernel, f"CMP *{ringreg}(short(#1)) == #{protocol}, TC1")
        control = [i for i, (_, code) in enumerate(kernel)
                   if re.match(rf"MOV .+, \*{ringreg}\(#(?:256|257|258|259|260)\)$", code)]
        assert len(control) == fields
        assert [int(re.search(r"\(#(\d+)\)$", kernel[i][1])[1]) for i in control] == list(range(256, 256 + fields))
        assert kernel[control[0]][1] == f"MOV #53611, *{ringreg}(#256)"
        assert one(kernel, last_payload) < control[0] < control[-1] < one(kernel, "RET")
        assert one(kernel, "MOV #0, T0") < control[-1]
        assert not any(re.match(r"(?:B|BCC|CALL|RPTB|RPTBLOCAL)\b", c) for _, c in kernel[control[0]:])
        if variant == "wsola":
            assert one(kernel, "MOV #880, *AR5(#22)") < one(kernel, last_payload)
            assert one(kernel, "CALL #_dsp_wsola_best") < one(kernel, last_payload)
            assert one(kernel, "RPTBLOCAL $C$L25-1") < one(kernel, "$C$L25:") < one(kernel, last_payload)
        else:
            accumulator = "AC0" if variant == "mdec" else "AC1"
            low = "AR2" if variant == "mdec" else accumulator
            end_label = "$C$L30:" if variant == "mdec" else "$C$L34:"
            repeat = "RPTB $C$L30-1" if variant == "mdec" else "RPTB $C$L34-1"
            count = 191 if variant == "mdec" else 127
            assert one(kernel, f"MOV #{count}, BRC0") < one(kernel, repeat) < one(kernel, f"MOV {low}, *AR3(#4368)") < one(kernel, last_payload) < one(kernel, end_label) < control[0]
            if variant == "mdec":
                assert one(kernel, "CALL #_mdec_kernel_process") < one(kernel, repeat)
                assert one(kernel, "BCC $C$L26,T3 != #0") > one(kernel, end_label)
                assert one(kernel, "BCC $C$L26,T3 != #0") < control[0]
        caller = rows[execute:]
        call = one(caller, f"CALL #_ring_{variant}_exchange")
        issue = next(i for i in range(call + 1, len(caller)) if caller[i][1] == "CALL #_STRM_issue")
        tail = caller[call + 1:issue]
        expected_calls = ["CALL #_ring_read_dcr", "CALL #_CLK_gethtime", "CALL #_CLK_countspms"]
        assert [c for _, c in tail if c.startswith("CALL ")] == expected_calls
        assert one(tail, "CALL #_ring_read_dcr") < one(tail, "MOV T0, *AR3(#15)") < one(tail, "CALL #_CLK_gethtime") < one(tail, "MOV AR1, *AR3(#12)")
        assert one(tail, f"MOV #{protocol}, *AR3(short(#4))") < one(tail, "MOV AR1, *AR3(#12)")
        assert all(any(re.match(rf"MOV .+, \*AR3\((?:short\()?#{offset}\)\)?$", c) for _, c in tail) for offset in range(6, 13))
        audit = proof["read_only_DCR_instruction_audit"]
        assert audit["DSP_sha256"] == entry["DSP_sha256"] and audit["helper_code_hex"] == "A45102004804"
        assert audit["helper_io_writes"] == audit["helper_relocations"] == 0
        print(f"{name}: payload -> {fields} completion words -> RET -> DCR read -> timing/notification -> STRM_issue; compiler order PASS")
    print("All three measured DSP compiler artifacts verified; OMAP endpoint and ARM caller/context completion remain unproven.")


if __name__ == "__main__":
    main()
