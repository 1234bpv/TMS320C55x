"""Stage a read-only-entry E90 clock probe; do not edit SymbianOverclock."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    stage = ROOT / "out/ringclock-build"
    (stage / "src").mkdir(parents=True, exist_ok=True)
    (stage / "group").mkdir(exist_ok=True)
    upstream = ROOT.parent / "SymbianOverclock/src"
    cpp = (upstream / "ocengine.cpp").read_bytes()
    header = (upstream / "ocengine.h").read_bytes()
    assert hashlib.sha256(cpp).hexdigest().upper() == "06CD09B34BC1A5060F1A7586F687EF98167D54937DF45AA79FF32C346C8B5267"
    assert hashlib.sha256(header).hexdigest().upper() == "E9887FF5A2B37AE44C4809C9F1CBC69B13A6A2314462FB9B154721816784B1EF"
    # Exact substitutions only. A source change must be reviewed before build.
    replacements = [(b'_LIT(KPatcherFile, "patcher.ldd");', b'_LIT(KPatcherFile, "RDomain.ldd");'),
                    (b'return DoControl(105, (TAny*)&aAddress, (TAny*)&aBytes);',
                     b'return DoControl(102, (TAny*)&aAddress, (TAny*)&aBytes);'),
                    (b'return DoControl(100, (TAny*)&aAddress, (TAny*)&aLength);',
                     b'return DoControl(104, (TAny*)&aAddress, (TAny*)&aLength);')]
    staged = cpp
    for old, new in replacements:
        assert staged.count(old) == 1
        staged = staged.replace(old, new)
    (stage / "src/ocengine.cpp").write_bytes(staged)
    (stage / "src/ocengine.h").write_bytes(header)
    (stage / "src/ring_clock_probe.cpp").write_bytes((ROOT / "src/ring_clock_probe.cpp").read_bytes())
    mmp = """TARGET ringclock.exe
TARGETTYPE exe
UID 0 0xE0001022
SECUREID 0xE0001022
VENDORID 0
CAPABILITY PowerMgmt WriteDeviceData ReadDeviceData ReadUserData WriteUserData ProtServ CommDD MultimediaDD NetworkControl NetworkServices LocalServices Location SwEvent TrustedUI SurroundingsDD UserEnvironment DiskAdmin
ALWAYS_BUILD_AS_ARM
EPOCSTACKSIZE 0x5000
EPOCHEAPSIZE 0x10000 0x800000
SOURCEPATH ..\\src
SOURCE ring_clock_probe.cpp ocengine.cpp
SYSTEMINCLUDE \\epoc32\\include
LIBRARY euser.lib efsrv.lib hal.lib sysutil.lib
"""
    (stage / "group/ringclock.mmp").write_text(mmp, encoding="ascii")
    (stage / "group/bld.inf").write_text("PRJ_MMPFILES\nringclock.mmp\n", encoding="ascii")
    manifest = {"upstream": "../SymbianOverclock/src", "upstream_sha256": {
        "ocengine.cpp": hashlib.sha256(cpp).hexdigest().upper(),
        "ocengine.h": hashlib.sha256(header).hexdigest().upper()},
        "staged_engine_sha256": hashlib.sha256(staged).hexdigest().upper(),
        "substitutions": [[old.decode(), new.decode()] for old, new in replacements],
        "scope": "separate executable/UID; E90 firmware guard; stock snapshot only; no upstream edits"}
    (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(stage)


if __name__ == "__main__":
    main()
