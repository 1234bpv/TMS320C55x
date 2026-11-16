"""Exact local current emulator SMLAD WSOLA snapshot; emulator stays read-only."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    path=ROOT.parent / "PS1Emulator/src/symbian/snd_symbian.cpp"; raw=path.read_bytes()
    text=raw.decode("utf-8").replace('\r\n','\n')
    block=text.split("static TUint32 g_wsTmplW",1)[1].split("\nclass CSymSnd",1)[0]
    block="static TUint32 g_wsTmplW"+block
    assert '"smlad %0, %1, %2, %0"' in block and block.count("static TInt WsolaBestOffset(")==1
    adapted=block.replace("static TInt WsolaBestOffset(","TInt WsolaBestOffsetCurrent(")
    header="// Exact local PS1Emulator WSOLA snapshot; exported entry name only changed.\n"
    directory=ROOT / "src/wsola_current"; directory.mkdir(exist_ok=True)
    data=(header+adapted).encode(); target=directory/"kernel.inc"
    if target.exists(): assert target.read_bytes()==data,"snapshot drift"
    else: target.write_bytes(data)
    report=dict(source="PS1Emulator/src/symbian/snd_symbian.cpp",source_sha256=hashlib.sha256(raw).hexdigest().upper(),
                original_block_LF_sha256=hashlib.sha256(block.encode()).hexdigest().upper(),snapshot_sha256=hashlib.sha256(data).hexdigest().upper(),
                adaptation="static WsolaBestOffset entry exported/renamed WsolaBestOffsetCurrent; all packing, SMLAD, traversal, tie and assertion code unchanged",
                scope="isolated current packed SMLAD ARM search; shell compiler CSL343 ARMv6/O2 matches stage1; no emulator writes")
    data=(json.dumps(report,indent=2)+"\n").encode(); target=directory/"snapshot.json"
    if target.exists(): assert target.read_bytes()==data,"metadata drift"
    else: target.write_bytes(data)
    print(json.dumps(report,indent=2))


if __name__=="__main__": main()
