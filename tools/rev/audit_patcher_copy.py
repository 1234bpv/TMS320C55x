"""Audit control105 in the saved E90 patcher driver; no phone access."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    driver = ROOT / "work/evidence/e90/clock-driver-files-01-c-patcher.ldd"
    raw = driver.read_bytes()
    assert hashlib.sha256(raw).hexdigest().upper() == "423E4FF1405C10C3CED21BD8445D7179A69CACBEF0AA51AA8AB43B679A7F4D23"
    tool = ROOT.parent / "S60_3rd_FP1/Epoc32/tools/elf2e32.exe"
    dump = subprocess.run([str(tool), "--e32input=" + str(driver), "--dump=c"],
                          capture_output=True, text=True, timeout=15, check=True).stdout
    rows = re.findall(r"^([0-9a-f]{6}): ((?:[0-9a-f]{8} ?)+)", dump, re.M)
    code = b"".join(struct.pack("<I", int(value, 16)) for _, words in rows for value in words.split())
    assert len(code) == 0x948
    def word(address):
        return struct.unpack_from("<I", code, address - 0x8000)[0]
    checks = {0x8608: 0xE2411064, 0x8624: 0xE3510005, 0x8644: 0x00008658,
              0x8658: 0xE5950000, 0x8668: 0xE5934000, 0x8670: 0xE3C4420F,
              0x8678: 0xE5951000, 0x8680: 0xE1A03004, 0x8684: 0xEBFFFFC6,
              0x85F8: 0xEAFFFFBD, 0x8510: 0xEB0000C9, 0x8520: 0xEB0000A7,
              0x8524: 0xEB0000AE, 0x858C: 0xEB00008C,
              0x87C4: 0xE51FF004, 0x87C8: 725,
              0x8804: 0xE51FF004, 0x8808: 639,
              0x883C: 0xE51FF004, 0x8840: 401,
              0x87E4: 0xE51FF004, 0x87E8: 402}
    assert all(word(address) == expected for address, expected in checks.items())
    reference = ROOT / "out/symbian-ekern-exports-reference.def"
    names = {int(ordinal): name for name, ordinal in re.findall(
        r"^\s*(\S+)\s+@\s+(\d+)\s+NONAME", reference.read_text(), re.M)}
    assert names[725] == "memcpy" and names[401] == "_ZN5NKern13ThreadEnterCSEv"
    print(json.dumps({"scope": "saved E90 installed driver; offline control105 contract, not boot-change root cause proof",
                      "driver_sha256": hashlib.sha256(raw).hexdigest().upper(),
                      "decompressed_code_sha256": hashlib.sha256(code).hexdigest().upper(),
                      "checked_words": len(checks),
                      "imports": {ordinal: names[ordinal] for ordinal in (639, 725, 401, 402)},
                      "control105": "destination = *a1; source = a2 TDesC8::Ptr(); length = descriptor low28 bits",
                      "user_destination_copy": "ThreadEnterCS -> raw memcpy(destination,source,length) -> ThreadLeaveCS; no fixed256B copy limit",
                      "ROM_destination_copy": "different ROM patch branch splits memcpy into32B segments; it is not the user destination branch",
                      "limit": "No independent user destination pin/fault-safe-copy primitive in this path. Pre-touching user pages is a corrective hypothesis, not proof of why E90 rebooted. Source-object lifetime remains the caller's responsibility."}, indent=2))


if __name__ == "__main__":
    main()
