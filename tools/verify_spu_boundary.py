"""Check the published ARM layout constants and SPU capacity arithmetic."""
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    r=json.loads((ROOT / "docs/evidence/2026-10-04/n95-spu-boundary-audit.json").read_text())
    evidence=r["compiled_layout_evidence"]; keys=evidence["constant_keys"]
    for key,name in (("constants_hex","layout"),("thread_constants_hex","optional_thread_layout")):
        data=bytes.fromhex(evidence[key]); values=struct.unpack("<"+"I"*len(keys),data)
        assert dict(zip(keys,values))==r[name]
    layout=r["layout"]
    assert layout["NSSIZE"]==((44100//50+32)&~1)==914
    assert layout["work_sums_offset"]==28+24*44==1084
    assert layout["work_item_bytes"]==layout["work_sums_offset"]+914*2*4==8396
    assert layout["worker_bytes"]==256+4*layout["work_item_bytes"]==33840
    assert r["optional_thread_layout"]["SPUInfo_bytes"]-layout["SPUInfo_bytes"]==25*64
    for b in r["post_ADSR_plain_mix_budgets"]:
        n=b["samples"]; inp=24*n*4+24*2*4+n*2*4; out=n*2*4
        assert b["input_bytes"]==inp and b["output_bytes"]==out
        assert b["input_slots"]==(inp+479)//480 and b["output_slots"]==(out+479)//480
        assert b["fits_7200_payload_each_direction"]==(inp<=7200 and out<=7200)
    assert max(n for n in range(2,915,2) if 104*n+192<=7200)==66
    assert r["SPU_RAM_bytes"]==524288 and r["SPU_RAM_copy_payload_handoffs_minimum"]==(524288+7199)//7200==73
    h=r["historical_budget"]
    assert h["doSamples_mean_us_per_frame"]==sum(h["control_doSamples_ms"])*1000/2/h["frames"]
    assert h["mix_plain_reported_mean_us_per_frame"]==h["stage_mix_plain_ms_reported"]*1000/h["frames"]
    assert h["mix_plain_reported_mean_us_per_voice_call"]==h["stage_mix_plain_ms_reported"]*1000/h["stage_voice_calls"]
    assert h["mean_samples_per_voice_call"]==h["stage_voice_samples"]/h["stage_voice_calls"]
    assert h["doSamples_fraction_of_control_pass_percent"]==100*sum(h["control_doSamples_ms"])/sum(h["control_pass_ms"])
    print("Verified offline SPU ABI constants, work/state capacities, max66-sample24-voice plain mix budget and separately attributed historical profile arithmetic; no SPU hardware timing.")


if __name__=="__main__":
    main()
