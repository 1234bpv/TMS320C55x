"""Record the separate E90/RDomain clock probe artifact (no phone access)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    executable = ROOT / "out/arm/ringclock.exe"
    stage = ROOT / "out/ringclock-build"
    manifest = json.loads((stage / "manifest.json").read_text())
    assert manifest["staged_engine_sha256"] == hashlib.sha256((stage / "src/ocengine.cpp").read_bytes()).hexdigest().upper()
    source = (ROOT / "src/ring_clock_probe.cpp").read_text()
    assert "User::CommandLine" not in source and "ApplyDspDiv" not in source and "ApplyClocks" not in source
    files = []
    for path in (executable, ROOT / "src/ring_clock_probe.cpp", ROOT / "tools/stage_ring_clock.py",
                 stage / "src/ocengine.cpp", stage / "src/ocengine.h", stage / "group/ringclock.mmp"):
        raw = path.read_bytes()
        files.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                      "sha256": hashlib.sha256(raw).hexdigest().upper()})
    result = {"scope": "E90/RA-6 400.34.93 stock-clock snapshot; RDomain copy102/free-shadow104; separate E0001022 UID",
              "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest().upper(),
              "files": files, "staging": manifest,
              "limits": ["uses existing guarded engine's temporary Usbc READ patch/unshadow; no PRCM writes or DSP open",
                         "own-RAM API self-test must pass before any ROM patch; standard driver control102 produces a different own-RAM result and is rejected",
                         "source SymbianOverclock and original ocprobe files are unchanged; staged copy remains local"]}
    path = ROOT / "docs/evidence/2026-10-04/ringclock-rdomain-artifacts.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
