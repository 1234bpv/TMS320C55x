"""Stage an independent counter calibration without changing existing builds."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    stage = ROOT / "out/counterprobe-build"
    (stage / "src").mkdir(parents=True, exist_ok=True)
    (stage / "group").mkdir(exist_ok=True)
    (stage / "src/cpu_counter_probe.cpp").write_bytes((ROOT / "src/cpu_counter_probe.cpp").read_bytes())
    mmp = """TARGET counterprobe.exe
TARGETTYPE exe
UID 0 0xE0001023
SECUREID 0xE0001023
VENDORID 0
CAPABILITY ReadDeviceData ReadUserData WriteUserData
ALWAYS_BUILD_AS_ARM
OPTION GCCE -march=armv6 -mtune=arm1136j-s -fomit-frame-pointer
EPOCSTACKSIZE 0x5000
EPOCHEAPSIZE 0x10000 0x800000
SOURCEPATH ..\\src
SOURCE cpu_counter_probe.cpp
SYSTEMINCLUDE \\epoc32\\include
LIBRARY euser.lib efsrv.lib hal.lib
"""
    (stage / "group/counterprobe.mmp").write_text(mmp, encoding="ascii")
    (stage / "group/bld.inf").write_text("PRJ_MMPFILES\ncounterprobe.mmp\n", encoding="ascii")
    print(stage)


if __name__ == "__main__":
    main()
