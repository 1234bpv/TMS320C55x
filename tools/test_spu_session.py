import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import e90_task_session as session
from spu_session_support import validate_spu
from stage_spu_mix import fixtures,signed

ROOT=Path(__file__).resolve().parents[1]
COMMAND="dmm-ring-spu voices=24 frames=8"


class SpuPreflight(unittest.TestCase):
    def test_e90_rejected_before_connect(self):
        for action,extra in (("run",["--command",COMMAND]),("deploy-dsp",["--artifact","out/dsp/c55stream-dmm-ring-spu.dll55l"])):
            with patch.object(sys,"argv",["e90_task_session.py","--device","e90","--session","work/evidence/e90/d0-20261003-clean34",
                                          "--tag","test-spu-no-create","--host-version","52","--action",action]+extra),patch.object(session,"Device") as connect,patch("sys.stderr"):
                with self.assertRaises(SystemExit): session.main()
                connect.assert_not_called()

    def test_native_partial_products_match_signed_high48(self):
        for case in fixtures():
            for samples,volumes in zip(case["samples"],case["volumes"]):
                packed=((volumes[0]&0xffffffff)|((volumes[1]<<16)&0xffffffff))<<1
                for sample in samples:
                    x=signed(sample<<1)
                    for gain in (signed(packed,16),signed(packed>>16,16)):
                        result=signed(x>>16,16)*gain+(((x&65535)*gain)>>16)
                        self.assertEqual(result,(x*gain)>>16)


class SpuAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT / "docs/evidence/2026-10-04/n95-spu67-pilot-v24-f8-01.txt"
        if not path.exists(): raise unittest.SkipTest("hardware journal not published yet")
        cls.log=path.read_text()

    def test_exact_journal(self):
        self.assertEqual(validate_spu(self.log,COMMAND,52)["checked_words"],4352)

    def test_corrupted_evidence_rejected(self):
        for before,after in (("index=65520 slot=0","index=65521 slot=0"),("arm_oracle=0","arm_oracle=-20"),
                             ("oracle_outside=1","oracle_outside=0"),("RING unmap=0","RING unmap=-20"),
                             ("FINAL status=0","FINAL status=-20"),("wpe_after=0","wpe_after=1")):
            with self.subTest(before=before),self.assertRaises(AssertionError):
                validate_spu(self.log.replace(before,after,1),COMMAND,52)

    def test_changed_page_identity(self):
        lines=self.log.splitlines()
        for i,line in enumerate(lines):
            if line.startswith("NATIVE PAGE phase=1 index=0 "): lines[i]=line[:-8]+"ffffffff"; break
        with self.assertRaises(AssertionError): validate_spu('\n'.join(lines),COMMAND,52)


if __name__=="__main__": unittest.main()
