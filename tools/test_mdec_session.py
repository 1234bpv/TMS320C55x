import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import e90_task_session as session
from mdec_session_support import validate_mdec

ROOT=Path(__file__).resolve().parents[1]
COMMAND="dmm-ring-mdec batch=4 frames=8"


class MdecAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log=(ROOT / "docs/evidence/2026-10-04/n95-mdec66-pilot-b4-f8-01.txt").read_text()

    def test_exact_journal(self):
        parsed=validate_mdec(self.log,COMMAND,51)
        self.assertEqual((parsed["input_slots"],parsed["output_slots"],parsed["checked_words"]),(13,7,5120))

    def test_e90_run_and_deploy_rejected_before_connect(self):
        for action,extra in (("run",["--command",COMMAND]),("deploy-dsp",["--artifact","out/dsp/c55stream-dmm-ring-mdec.dll55l"])):
            with patch.object(sys,"argv",["e90_task_session.py","--device","e90","--session","work/evidence/e90/d0-20261003-clean34",
                                          "--tag","test-mdec-no-create","--host-version","51","--action",action]+extra),patch.object(session,"Device") as connect,patch("sys.stderr"):
                with self.assertRaises(SystemExit):
                    session.main()
                connect.assert_not_called()

    def test_wrong_sequence(self):
        with self.assertRaises(AssertionError):
            validate_mdec(self.log.replace("index=65520 slot=0","index=65521 slot=0",1),COMMAND,51)

    def test_oracle_failure(self):
        with self.assertRaises(AssertionError):
            validate_mdec(self.log.replace("arm463_oracle=0","arm463_oracle=-20",1),COMMAND,51)

    def test_missing_result_copy_boundary(self):
        with self.assertRaises(AssertionError):
            validate_mdec("\n".join(l for l in self.log.splitlines() if not l.startswith("RING MDEC READY frame=1 ")),COMMAND,51)

    def test_changed_page_identity(self):
        lines=self.log.splitlines()
        for i,line in enumerate(lines):
            if line.startswith("NATIVE PAGE phase=1 index=0 "):
                lines[i]=line[:-8]+"ffffffff"
                break
        with self.assertRaises(AssertionError):
            validate_mdec("\n".join(lines),COMMAND,51)

    def test_failed_lifecycle(self):
        for before,after in (("RING unmap=0","RING unmap=-20"),("FINAL status=0","FINAL status=-20")):
            with self.assertRaises(AssertionError):
                validate_mdec(self.log.replace(before,after),COMMAND,51)


if __name__=="__main__":
    unittest.main()
