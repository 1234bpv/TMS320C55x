"""Check archived TI DMM sample conventions, not Nokia runtime behavior."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "work/vendor/userspace-dspbridge/source"


def main():
    paths = ("VisionTest/MPU/inc/dbdefs.h", "samples/mpu/src/dmmcopy/dmmcopy.c",
             "samples/dsp/dmmcopyExecute.c")
    sources = {p: (VENDOR / p).read_bytes() for p in paths}
    flags = {name: int(value, 16) for name, value in re.findall(
        r"^#define (DSP_MAP\w+)\s+(0x[0-9A-Fa-f]+)", sources[paths[0]].decode("ascii"), re.M)}
    expected = {"DSP_MAPVIRTUALADDR": 0, "DSP_MAPPHYSICALADDR": 1,
                "DSP_MAPBIGENDIAN": 2, "DSP_MAPLITTLEENDIAN": 0,
                "DSP_MAPMIXEDELEMSIZE": 4, "DSP_MAPELEMSIZE8": 8,
                "DSP_MAPELEMSIZE16": 16, "DSP_MAPELEMSIZE32": 32,
                "DSP_MAPELEMSIZE64": 64, "DSP_MAPVMALLOCADDR": 128}
    if flags != expected:
        raise RuntimeError("TI reference map flags changed")
    host = sources[paths[1]].decode("ascii")
    for token in ("g_dwDSPWordSize = 2;", "(DWORD)aDspRecvBuffer / g_dwDSPWordSize",
                  "(DWORD)cBytesRead / g_dwDSPWordSize", "DSPProcessor_FlushMemory",
                  "DSPProcessor_InvalidateMemory"):
        if token not in host:
            raise RuntimeError("TI reference convention changed: " + token)
    result = {
        "scope": "Archived TI userspace reference only; E90 DMM ABI/flags/cache/pinning unverified; no device I/O",
        "source_sha256": {p: hashlib.sha256(data).hexdigest().upper() for p, data in sources.items()},
        "map_flag_reference": flags,
        "C55_reference_conventions": [
            "Host selects g_dwDSPWordSize=2 for DSPTYPE_55.",
            "Host divides returned mapping byte address and byte length by DSP word size before notifying the DSP.",
            "Host flushes ARM input before DSP work and invalidates ARM output after completion.",
            "The sample synchronizes through NODE messages; E90 message delivery remains a D0 diagnostic gate.",
        ],
        "not_established_on_E90": ["returned mapping address units", "actual native flag interpretation",
                                  "ARM cache API and ownership", "nonpageable lifetime",
                                  "16KiB ring wrap/ordering/notification", "latency/bandwidth"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
