"""Recalculate the PS1 decision from saved v18/v20 measurements, offline.

DMM is unmeasured. Bandwidth and SMLAD timings below are explicit scenarios,
not new device measurements. Output retains source hashes and strict bounds.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    sources = {}
    wsola = {}
    echo = {}
    for device in ("n95", "e90"):
        for kind, target in (("wsola-v20", wsola), ("packet-sizes-v18", echo)):
            path = ROOT / f"docs/evidence/2026-10-01/{device}-{kind}-results.json"
            data = path.read_bytes()
            sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(data).hexdigest().upper()
            target[device] = json.loads(data)
    for relative in ("../PS1Emulator/plans/reports/perf-dsp-analysis-2026-10-01.md",
                     "../PS1Emulator/plans/runs/2026-09-28_gemini/n95-spustage-result.md"):
        sources[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest().upper()
    ws = {}
    for device, result in wsola.items():
        agg = result["aggregate"]
        t = agg["1"]["end_to_end_us"]["median_us"]
        a = agg["1"]["arm_per_search_us"]["median_us"]
        s = result["create_median_us"]
        ws[device] = {
            "arm_scalar_us": a, "measured_H_plus_D_us": t,
            "control_us": agg["0"]["end_to_end_us"]["median_us"],
            "same_packet_saving_us": agg["1"]["saving_us"]["median_us"],
            "create_only_S_us": s,
            "create_only_N_scalar": math.floor(s / (a - t)) + 1,
            "SMLAD_unmeasured_scenarios": [{
                "A_us": optimized, "W_strictly_greater_than_us_at_N1000": t + s / 1000 - optimized,
                "minimum_N_if_W_ge_T_create_only": math.floor(s / optimized) + 1,
                "blocking_gain": False,
            } for optimized in (135, 200)],
        }
    # 32-byte header in each direction; existing native allocations are 4KiB each.
    mdec = []
    for capacity in (4096, 16384):
        for output_per_block in (512, 768):
            k = (capacity - 32) // 1536
            i = 32 + k * 1536
            o = 32 + k * output_per_block
            h = 500 + (i + o) / 9.0  # us: scenario B=9 decimal MB/s, L=500us
            mdec.append({"capacity_each_direction_bytes": capacity, "blocks": k,
                         "input_bytes": i, "output_bytes": o,
                         "A_batch_us_scenario": 50 * k,
                         "H_batch_us_scenario_D0": h,
                         "H_per_block_us_scenario": h / k,
                         "W_strictly_greater_than_us_no_setup_D0": h - 50 * k})
    result = {
        "scope": "Offline prior copy-channel decision; D0 acceptance and DMM measurement pending",
        "formula": "max(T,W)+S/N < A+W, T=H+D",
        "equivalent_strict_condition": "S/N < A and W > T+S/N-A",
        "source_sha256": sources,
        "echo_e90_repeated_measurements": echo["e90"]["size_summary"],
        "wsola": ws,
        "mdec_scenarios": mdec,
        "mdec_minimum_bandwidth_MB_s_if_L_D_setup_zero": {"RGB15_int32": 2048/50, "RGB24_int32": 2304/50},
        "spu": {"whole_doSamples_mean_us_per_call": [965000/609, 974000/609],
                "mix_mean_us_per_call_sampled_estimate": [225400/609, 230300/609],
                "scene_clocks_kHz": {"ARM":330240, "bus":165120},
                "calls":609, "total_generated_samples":446816,
                "mean_samples_per_call":446816/609,
                "mean_stereo_pcm_bytes_per_call":446816*4/609,
                "mean_pcm_only_traffic_floor_us_at_9MB_s":446816*4/609/9,
                "stereo_pcm_only_traffic_floor_us_at_9MB_s": 3656/9,
                "int32_SSumLR_only_traffic_floor_us_at_9MB_s": 7312/9,
                "D_kernel_measured": False, "input_dirty_bytes_measured": False},
        "limits": ["Create-only S omits base/processor load, other startup and cleanup.",
                   "9MB/s and L500us are inherited scenario estimates, not isolated measured bandwidth/latency.",
                   "Full overlap assumes H does not occupy ARM; actual host CPU/cache contention remains unmeasured.",
                   "SPU A is a scene mean; MIX is extrapolated from 1:16 sampling. PCM3656B is maximum capacity, not mean output.",
                   "No new N95 connection and no emulator modification."],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
