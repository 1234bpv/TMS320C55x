"""Portable CP15 decoding and branch/hash checks of the N95 cache-path publication."""
import hashlib
import json
import struct
import sys

from verify_ring_publication import ROOT


def cp15(word):
    if word&0x0f000010!=0x0e000010 or (word>>20)&1 or (word>>8)&15!=15: return None
    return ((word>>21)&7,(word>>16)&15,word&15,(word>>5)&7)


def main():
    report=json.loads((ROOT/"docs/evidence/2026-10-04/n95-arm-cache-path-audit.json").read_text())
    assert report["status"]=="ARM_path_verified_DSP_endpoint_unresolved"
    prior=json.loads((ROOT/"docs/evidence/2026-10-03/dmm-ownership-native-audit.json").read_text())
    assert report["module_sha256"]==prior["n95"]["module_sha256"] and report["utility_order"]==[378,376]
    assert report["exports"]=={str(v["ordinal"]):v["target"] for k,v in prior["n95"]["calls"].items() if k.startswith("cache_")}
    words={}; ranges={}
    for r in report["ranges"]:
        start=int(r["address"],16); assert r["bytes"]==len(r["instructions"])*4
        for i,instruction in enumerate(r["instructions"]):
            assert int(instruction["address"],16)==start+4*i
            assert instruction["address"] not in words
            words[instruction["address"]]=int(instruction["word"],16)
        raw=struct.pack(f"<{len(r['instructions'])}I",*[int(i["word"],16) for i in r["instructions"]])
        assert hashlib.sha256(raw).hexdigest().upper()==r["sha256"]
        ranges[r["label"]]=r
    assert len(words)==109 and len(ranges)==7
    for edge in report["branches"]:
        word=words[edge["address"]]; assert (word>>25)&7==5
        delta=word&0xffffff
        delta=delta if delta<0x800000 else delta-0x1000000
        assert (int(edge["address"],16)+8+delta*4)&0xffffffff==int(edge["target"],16)
    decoded={address:cp15(word) for address,word in words.items() if cp15(word) is not None}
    expected={}
    for label,fields in (("clean_MVA",(0,7,10,1)),("clean_SetWay",(0,7,10,2)),
                         ("invalidate_MVA",(0,7,6,1)),("clean_invalidate_SetWay",(0,7,14,2)),("DSB",(0,7,10,4))):
        for address in report["cp15_operations"][label]: expected[address]=fields
    assert decoded==expected and len(decoded)==13
    for name in ("clean_MVA","clean_SetWay","clean_invalidate_SetWay"):
        r=ranges[name]; tail=r["instructions"][-2:]
        assert cp15(int(tail[0]["word"],16))==(0,7,10,4) and int(tail[1]["word"],16)==0xe12fff1e
    assert all(cp15(int(i["word"],16))!=(0,7,10,4) for i in ranges["invalidate_MVA"]["instructions"])
    assert words["80073444"]==words["80073454"]==0xe3a00006
    assert words["80073368"]==0x13130002 and words["800732F8"]==0xe3150002 and words["8007332C"]==0xe3150001
    sys.path.insert(0,str(ROOT/"tools/rev"))
    from paths import ROM
    from pathlib import Path
    if (Path(ROM)/"ekern.exe").exists():
        from compare_node_info import Module
        module=Module(Path(ROM)/"ekern.exe")
        assert hashlib.sha256(module.data).hexdigest().upper()==report["module_sha256"]["kernel"]
        assert all(module.word(int(address,16))==word for address,word in words.items())
    print("Verified109 published kernel words/436bytes,10 control-flow targets,13 CP15 operations,3 DSB tails and short invalidate scope; no phone access.")


if __name__=="__main__": main()
