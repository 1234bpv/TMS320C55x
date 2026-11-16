import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import e90_task_session as session
from wsola_current_session_support import validate_current,reference
from device_work_lock import device_lock
import msvcrt
import tempfile

ROOT=Path(__file__).resolve().parents[1]; COMMAND="dmm-ring-wsola-current frames=8"


class CurrentPreflight(unittest.TestCase):
    def test_exclusive_session_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"phone.lock"
            with device_lock(path),device_lock(path):
                with path.open("r+b") as competing:
                    with self.assertRaises(OSError): msvcrt.locking(competing.fileno(),msvcrt.LK_NBLCK,1)
            with device_lock(path): pass
    def test_e90_rejected_before_connect(self):
        for action,extra in (("run",["--command",COMMAND]),("deploy-dsp",["--artifact","out/dsp/c55stream-dmm-ring-wsola.dll55l"])):
            with patch.object(sys,"argv",["e90_task_session.py","--device","e90","--session","work/evidence/e90/d0-20261003-clean34","--tag","test-current-no-create","--host-version","53","--action",action]+extra),patch.object(session,"Device") as connect,patch("sys.stderr"):
                with self.assertRaises(SystemExit): session.main()
                connect.assert_not_called()

    def test_tie_and_boundary_order(self):
        self.assertEqual([reference(i)[0] for i in range(2,9)],[0,0,0,1,439,440,4])


class CurrentAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/"docs/evidence/2026-10-04/n95-wsola68-pilot-f8-01.txt"
        if not path.exists(): raise unittest.SkipTest("hardware journal not published yet")
        cls.log=path.read_text()

    def test_exact_pilot(self): self.assertEqual(validate_current(self.log,COMMAND,53)["jobs"],8)

    def test_corruption_rejected(self):
        for before,after in (("offset=1 score=","offset=2 score="),("index=65520 slot=0","index=65521 slot=0"),("current_oracle=0","current_oracle=-20"),("current_iterations=64","current_iterations=16"),("oracle_outside=1","oracle_outside=0"),("wpe_before=0","wpe_before=1"),("RING unmap=0","RING unmap=-20"),("FINAL status=0","FINAL status=-20")):
            with self.subTest(before=before),self.assertRaises(AssertionError): validate_current(self.log.replace(before,after,1),COMMAND,53)


if __name__=="__main__": unittest.main()
