"""Record conditional application decisions from separate measured D1 cohorts."""
import hashlib
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n95-native", action="store_true", help="use the separate stock-qualified N95 native61 cohort")
    parser.add_argument("--output", default="docs/evidence/2026-10-03/ring-candidates-calculation.json")
    args = parser.parse_args()
    if args.n95_native and args.output == "docs/evidence/2026-10-03/ring-candidates-calculation.json":
        parser.error("new N95 cohort requires a separate output; historical scenarios remain immutable")
    sources = {}
    def read(relative):
        path = ROOT / relative
        raw = path.read_bytes()
        sources[relative] = hashlib.sha256(raw.replace(b"\r\n", b"\n") if args.n95_native else raw).hexdigest().upper()
        return json.loads(path.read_text(encoding="utf-8"))
    ring = read("docs/evidence/2026-10-03/d1-ring-results.json")
    native = read("docs/evidence/2026-10-03/d1-native-ring-results.json")
    previous = read("docs/evidence/2026-10-01/ps1-candidates-calculation.json")
    n95 = read("docs/evidence/2026-10-04/d1-n95-native-ring-results.json") if args.n95_native else ring["devices"]["n95"]
    scenarios = []
    # T is explicitly a synthetic-ring scenario, not application H+D.
    for device, revision, aggregates in (("n95", 61 if args.n95_native else 54, n95["aggregate"]),
                                        ("e90", 61, native["aggregate"])):
        for batch, aggregate in aggregates.items():
            t = aggregate["exchange_wall_us"]["p50"]
            s = aggregate["instrumented_S_us"]["p50"]
            for a in (135, 200, previous["wsola"][device]["arm_scalar_us"]):
                scenarios.append({"device": device, "candidate": revision,
                                  "batch": int(batch), "A_us_scenario": a,
                                  "T_us_synthetic_scenario": t, "S_us_instrumented": s, "N": 1000,
                                  "S_over_N_us": s / 1000,
                                  "necessary_setup_condition_met": s / 1000 < a,
                                  "W_strictly_greater_than_us": t + s / 1000 - a,
                                  "minimum_N_setup_only": math.floor(s / a) + 1,
                                  "blocking_gain_scenario": t + s / 1000 < a})
    result = {"stage": "D2", "status": "in_progress", "source_sha256": sources,
              "formula": "max(H+D,W)+S/N < A+W",
              "equivalent_strict_conditions": ["S/N < A", "W > H+D+S/N-A"],
              "measured_transport": f"N95 candidate{61 if args.n95_native else 54} and E90 candidate61: three series/9360 packets each. Synthetic verify/transform, not application kernel. {'N95 native61 has six stock-qualified brackets. ' if args.n95_native else ''}E90 candidate61 DSP/bus clocks unconfirmed: all ocprobe self-tests failed; HAL CPU330MHz only. Earlier E90 cohorts remain separate.",
              "capacity": {"ring_total_bytes": 16384, "control_bytes": 1024,
                           "each_direction_slot_bytes": 7680, "each_direction_payload_bytes": 7200,
                           "MDEC_input_slots_per_1536_byte_block": 4,
                           "MDEC_max_blocks_without_repacking": 3,
                           "MDEC_max_blocks_with_contiguous_repacking_scenario": 4,
                           "MDEC_output_slots_per_block_RGB15_RGB24": [2, 2],
                           "SPU_PCM_2934_bytes_slots": 7,
                           "SPU_int32_7312_bytes_slots": 16,
                           "SPU_int32_single_batch_fits": False,
                           "WSOLA_1760_payload_bytes_input_slots": 4},
              "conditional_synthetic_scenarios": scenarios,
              "decisions": {
                  "MDEC": "No demonstrated gain. Actual IDCT/packing D, asymmetric transport T, ARM A and independent W are unmeasured in this ring; original 16KiB-per-direction assumption is invalid.",
                  "SPU": "Candidate for further measurement, no demonstrated gain. PCM-sized work fits; 7312-byte int32 payload needs tiling. Prior whole-doSamples and sampled MIX times cannot stand in for DSP D or parallel W.",
                  "WSOLA": "Keep current implementation. Prior scalar timing and SMLAD135-200us estimates are scenarios at earlier conditions; the ring synthetic transform is not the WSOLA kernel and current host does no useful ARM W while waiting."},
              "remaining": "Native backing chunk traced; complete independent DSP publication contract and verified E90 frequency brackets. Application-specific T/A/W remain unmeasured for this ring; no application gain demonstrated. Emulator unchanged."}
    if args.n95_native:
        result["source_text_normalization"] = "LF"
        comparison = {}
        for batch in (1, 2, 8, 15):
            comparison[str(batch)] = {}
            for label, cohort in (("candidate54", ring["devices"]["n95"]), ("native61", n95)):
                ticks = sorted(value for run in cohort["runs"] if run["batch"] == batch for value in run["dsp_ticks_unconverted"])
                comparison[str(batch)][label] = {"exchange_p50_us": cohort["aggregate"][str(batch)]["exchange_wall_us"]["p50"],
                                                "raw_DSP_ticks_p50": ticks[math.ceil(len(ticks)/2)-1], "samples": len(ticks)}
        result["N95_separate_cohort_comparison"] = comparison
        result["N95_comparison_limit"] = "Larger batches have increased raw DSP timer spans as well as host exchange latency; network delay alone cannot explain the DSP timer spans. Clock brackets are not continuous runtime traces. Historical WPE was not measured; current DCR62 pilot values cannot be assigned to either historical cohort. No performance root cause is established."
    path = ROOT / args.output
    path.write_bytes((json.dumps(result, indent=2) + "\n").encode("utf-8"))
    print(path)


if __name__ == "__main__":
    main()
