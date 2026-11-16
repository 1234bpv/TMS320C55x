"""Audit captured E90 patcher variants and publish the clock recovery boundary.

Offline only. Vendor binaries and screenshots remain local, outside Git.
"""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from prepare_stream import stock_clock_matches
from summarize_ring import boot, publish_text


def main():
    directory = ROOT / "work/evidence/e90/d0-20261003-clean34"
    dest = ROOT / "docs/evidence/2026-10-04"
    dest.mkdir(parents=True, exist_ok=True)
    captures = [("patcher.ldd", directory / "resume-oct04-drivers01/file-0.bin",
                 "423E4FF1405C10C3CED21BD8445D7179A69CACBEF0AA51AA8AB43B679A7F4D23",
                 0x8608, 0x8630, 0x8648, 0x8658, 0x87EC, 103, 105, 100),
                ("patcherShadow.ldd", directory / "resume-oct04-driver-variants01/patcherShadow.ldd",
                 "8D6414CFE3583854044ED1CF9041F8D920FDC1D7C5BF7B3BD01EC659D9C4B753",
                 0x860C, 0x8634, 0x864C, 0x865C, 0x87F8, 103, 105, 100),
                ("patcherS3.ldd", directory / "resume-oct04-driver-variants01/patcherS3.ldd",
                 "A9633C610C16B161B5F30E7686902C2F36A90F8C4594F156A192350726449BD3",
                 0x8624, 0x864C, 0x8664, 0x8674, 0x8818, 103, 105, 100),
                ("RDomain.ldd", directory / "resume-oct04-rdomain01/RDomain.ldd",
                 "76C630AFA3E64952061A2058AE263D71E5B287D7C95BB0D1ECA686880509EECB",
                 0x8608, 0x8630, 0x8648, 0x86C0, 0x87E4, 105, 102, 104),
                ("RDomainShadow.ldd", directory / "resume-oct04-rdomain01/RDomainShadow.ldd",
                 "B791DBCF70FB579F8B11C35AFC1133AC3BE4D32D47FEFD0795F36D86C6F41A2C",
                 0x860C, 0x8634, 0x864C, 0x86C4, 0x87F0, 105, 102, 104)]
    variants = []
    for name, path, sha, subtract, table, getter, copy, veneer, getter_ctl, copy_ctl, free_ctl in captures:
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest().upper() == sha
        dump = subprocess.run([str(ROOT.parent / "S60_3rd_FP1/Epoc32/tools/elf2e32.exe"),
                               "--e32input=" + str(path), "--dump=c"],
                              capture_output=True, text=True, timeout=15, check=True).stdout
        rows = re.findall(r"^([0-9a-f]{6}): ((?:[0-9a-f]{8} ?)+)", dump, re.M)
        code = b"".join(struct.pack("<I", int(v, 16)) for _, words in rows for v in words.split())
        def word(address):
            return struct.unpack_from("<I", code, address - 0x8000)[0]
        checks = {subtract: 0xE2411064, subtract + 28: 0xE3510005,
                  table + (getter_ctl - 100)*4: getter, table + (copy_ctl - 100)*4: copy,
                  getter + 4: 0xE5850000, copy: 0xE5950000,
                  copy + 16: 0xE5934000, copy + 24: 0xE3C4420F,
                  copy + 32: 0xE5951000, copy + 40: 0xE1A03004,
                  veneer: 0xE51FF004, veneer + 4: 360}
        branch = word(getter)
        assert branch >> 24 == 0xEB
        displacement = branch & 0xFFFFFF
        if displacement & 0x800000:
            displacement -= 0x1000000
        assert getter + 8 + displacement * 4 == veneer
        assert all(word(address) == expected for address, expected in checks.items())
        assert b"RomPatcherPlus.Driver" in code
        variants.append({"name": name, "bytes": len(raw), "sha256": sha,
                         "decompressed_code_sha256": hashlib.sha256(code).hexdigest().upper(),
                         "instruction_checks": {f"{address:08x}": f"{value:08x}" for address, value in checks.items()},
                         "logical_channel": "RomPatcherPlus.Driver",
                         "getter_control": getter_ctl, "copy_control": copy_ctl, "free_shadow_control": free_ctl,
                         "free_shadow_entry": f"{word(table+(free_ctl-100)*4):08x}",
                         "getter": "Kern::SuperPage (import360) -> *a1; returns0",
                         "copy": "*a1 destination, a2 descriptor pointer/low28 length -> copy router; no *a1 getter assignment"})
    clock_entries = []
    for tag, expected_stock in (("resume-oct04-clock01", False), ("resume-oct04-clock02", True)):
        report = json.loads((directory / (tag + ".json")).read_text())
        assert report["complete"] and boot(report) == boot(report, "info_after") == "67736 boot 0 by n"
        text, probes = "", []
        for probe in report["probes"]:
            source = directory / probe["path"]
            assert hashlib.sha256(source.read_bytes()).hexdigest().upper() == probe["sha256"]
            text += source.read_text(encoding="ascii")
            published = dest / ("e90-" + source.stem + ".txt")
            probes.append({"published_path": published.relative_to(ROOT).as_posix(),
                           "published_sha256": publish_text(source, published)})
        assert stock_clock_matches(text, "e90") == expected_stock
        if not expected_stock:
            assert text.count("engine NOT ready: err -20 at step [patcher self-test]") == 2
        clock_entries.append({"tag": tag, "boot": boot(report), "stock_verified": expected_stock,
                              "probes": probes, "clock_log_restored": report["restored"]})
    journal = directory / "resume-oct04-patcher-read01.log"
    failed = journal.read_text(encoding="ascii")
    assert "destination=c0000000 bytes=24 words=00000000/00000000/00000000/00000000/00000000/00000000" in failed
    assert failed.splitlines()[-1] == "FINAL status=-20" and "BEGIN processor" not in failed
    published = dest / "e90-resume-oct04-patcher-read01.txt"
    result = {"scope": "offline captured-driver contract plus fresh own-RAM failure/clock recovery; not loaded-module identity proof",
              "variants": variants, "clocks": clock_entries,
              "own_ram_failure": {"published_path": published.relative_to(ROOT).as_posix(),
                                  "published_sha256": publish_text(journal, published),
                                  "dsp_open": False, "new_dsp_run": False},
              "observed_screen": {"application": "RPDomain Plus", "active": ["c2z4bin ARM", "Open4All RP+"],
                                  "inactive": ["c2z4bin THUMB", "Install Server RP+"],
                                  "local_bmp_sha256": hashlib.sha256((ROOT / "out/e90-oct04-patches01.bmp").read_bytes()).hexdigest().upper()},
              "finding": "RDomain and standard patcher share the channel name but have incompatible control numbers. RDomain105 is the SuperPage getter, exactly consistent with the observed changed destination. Standard105 is descriptor copy. RDomain102/104 are copy/free-shadow.",
              "limits": ["saved RDomain API and observed control105 result agree; the actual loaded module code was not read",
                         "fresh clocks passed after user toggled patches, without a boot change; which toggle changed behavior is unknown",
                         "clock recovery cannot qualify earlier E90 runs retrospectively or explain historical automatic reboots",
                         "binaries/screenshots remain local; instruction words are audit checks, not a shipped vendor binary"]}
    path = dest / "e90-patcher-clock-recovery-audit.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
