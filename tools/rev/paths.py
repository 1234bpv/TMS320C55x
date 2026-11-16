"""Shared, relocatable paths; C55_ROM_DIR can select another extracted ROM."""
import os
from pathlib import Path

SHARED = Path(__file__).resolve().parents[3]
ROM = str(Path(os.environ.get("C55_ROM_DIR", SHARED / "eka2l1/data/drives/z/rm-320/sys/bin"))) + os.sep
TC = str(SHARED / "toolchain/CSL_Arm_Toolchain/bin") + os.sep
OD = TC + "arm-none-symbianelf-objdump.exe"
SDKLIB = str(SHARED / "S60_3rd_FP1/Epoc32/release/armv5/lib") + os.sep
