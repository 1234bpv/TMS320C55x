"""Independent integer fixtures for the exact PS1 stereo coarse/refine search."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

NAMES = ("ps1-benchmark-lcg", "silence", "positive-maximum", "negative-scores",
         "refine-left-1", "refine-right-439", "last-coarse-440", "tie-keeps-coarse-4")


def vector(sequence):
    if sequence < 1:
        raise ValueError("positive sequence required")
    case = (sequence - 1) % 8
    seed = (0x87654321 + (sequence - 1) // 8 * 0x1020304) & 0xffffffff
    stereo = []
    for _ in range(1762):
        seed = (seed * 1103515245 + 12345) & 0xffffffff
        bits = seed >> 16
        stereo.append(bits if bits < 32768 else bits - 65536)
    search, template = stereo[:1320], stereo[1322:]
    if case:
        template[::2] = [0] * 220
        search[::2] = [0] * 660
        if case in (2, 3):
            template[::2] = [32767] * 220
            search[::2] = [32767 if case == 2 else -32768] * 660
        elif case >= 4:
            template[220] = 32767
            peaks = {4: ((111, 32767),), 5: ((546, 16000), (549, 32767)),
                     6: ((550, 32767),), 7: ((114, 32767), (111, 32767))}
            for index, value in peaks[case]:
                search[index * 2] = value
    # Score every valid offset independently; selection then follows the
    # original ordered coarse/refine passes (never a global argmax shortcut).
    t = [value >> 6 for value in template[::2]]
    s = [value >> 6 for value in search[::2]]
    scores = [sum(a * b for a, b in zip(t, s[off:off + 220])) for off in range(441)]
    best = max(range(0, 441, 4), key=lambda off: scores[off])
    lo, hi = max(0, best - 4), min(440, best + 4)
    refinement = [off for off in range(lo, hi + 1) if off % 4]
    for off in refinement:
        if scores[off] > scores[best]:
            best = off
    packed = t + s
    data = struct.pack("<880h", *packed)
    return {"sequence": sequence, "case": case, "name": NAMES[case],
            "offset": best, "score": scores[best], "scored": 111 + len(refinement),
            "input_sum": sum(value * (i + 1) for i, value in enumerate(packed)),
            "packed_sha256": hashlib.sha256(data).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--frames", type=int, default=32)
    a = p.parse_args()
    if a.report.exists() or not 8 <= a.frames <= 4096:
        p.error("new report and frames8..4096 required")
    results = [vector(i) for i in range(1, a.frames + 1)]
    if [row["offset"] for row in results[1:8]] != [0, 0, 0, 1, 439, 440, 4]:
        raise RuntimeError("edge/tie fixtures do not express their intended cases")
    report = {"input_bytes": 1792, "output_bytes": 48, "header_bytes": 32,
              "template_values": 220, "search_values": 660, "range": 441,
              "coarse_step": 4, "refinement": 4, "tie_rule": "strict >; keep earlier scored candidate",
              "source": "PS1Emulator/src/symbian/snd_symbian.cpp WsolaBestOffset and sndSymbianWsolaBench",
              "arithmetic": "left stereo channel, arithmetic >>6, signed32 accumulation",
              "hardware_verified": False, "vectors": results}
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(a.report), "vectors": len(results), "first": results[0]}))


if __name__ == "__main__":
    main()
