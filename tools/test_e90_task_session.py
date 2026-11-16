import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile

from e90_task_session import run, validate_journal, validate_worker_message, n95_m111_clock_matches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/rev"))
from audit_kernel_containers import audit_e90, audit_n95


def complete_log():
    lines = ["C55STREAM v21 command='run-transfer reps=0 bytes=512 frames=8'",
             "create=0 status=0 wall_us=10", "execute submitted=0 status=0",
             "execute start=0 status=0"]
    for i in range(1, 9):
        lines.extend([f"frame={i} put=0/0 get=0/0 wall_us=10 crc=00000000",
                      f"SIZE frame={i} input_bytes=512 output_bytes=512 returned_words=256 protocol=21 checked_payload_words=240",
                      f"  result=0 expected=0 ticks=1 counts_per_ms=164 errors=0 stop={int(i == 8)}"])
    return "\n".join(lines + ["STREAM PASS frames=8 creates=1 useful_arm_crc=0 mode=0 total_us=80",
                              "delete=0 status=0", "free task=0", "free native out=0",
                              "free native in=0", "BEGIN close", "FINAL status=0"]) + "\n"


class Acceptance(unittest.TestCase):
    def test_new_boot_stops_action_before_start_put_or_wake(self):
        import e90_task_session as session
        commands = []
        class NewBoot:
            def __init__(self, *args, **kwargs):
                pass
            def cmd(self, command):
                commands.append(command)
                if command != "INFO":
                    raise AssertionError("command after changed boot: " + command)
                return ["OK info", "tick 120000 startTick 93971 boot 0 by n"]
            def close(self):
                pass
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / "work/evidence/e90/session"
            argv = ["e90_task_session.py", "--device", "e90", "--session", str(directory),
                    "--action", "run", "--host-version", "46", "--command", "dmm-ring-native batch=1 frames=8",
                    "--tag", "boot-guard", "--keep-awake", "--expected-boot", "67736 boot 0 by n"]
            with patch.object(session, "ROOT", root), patch.object(session, "Device", NewBoot), \
                    patch.object(sys, "argv", argv), patch("builtins.print"):
                with self.assertRaisesRegex(RuntimeError, "boot changed before action; no START/PUT"):
                    session.main()
            self.assertEqual(commands, ["INFO"])

    def test_dcr_diagnostic_rejects_e90_before_connecting(self):
        import e90_task_session as session
        with patch("sys.argv", ["e90_task_session.py", "--device", "e90", "--action", "run", "--host-version", "47",
                                "--session", "work/evidence/e90/d0-20261003-clean34", "--tag", "test-do-not-create",
                                "--command", "dmm-ring-dcr batch=15 frames=8"]), patch("e90_task_session.Device") as connect, patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                session.main()
            connect.assert_not_called()

    def test_wsola_ring_rejects_e90_before_connecting(self):
        import e90_task_session as session
        with patch("sys.argv", ["e90_task_session.py", "--device", "e90", "--action", "run", "--host-version", "48",
                                "--session", "work/evidence/e90/d0-20261003-clean34", "--tag", "test-do-not-create",
                                "--command", "dmm-ring-wsola frames=8"]), patch("e90_task_session.Device") as connect, patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                session.main()
            connect.assert_not_called()

    def test_counter_calibration_rejects_missing_cases_and_failed_calls(self):
        from counter_probe_session import validate
        log = (ROOT / "docs/evidence/2026-10-04/n95-counterprobe-series01.txt").read_text(encoding="ascii")
        self.assertEqual(len(validate(log)),36)
        for bad in (log.replace("index=35", "index=34"),
                    log.replace("before_rc=0", "before_rc=-5"),
                    log.replace("machine=20002d84", "machine=20002496"),
                    log.replace("requested_us=200000", "requested_us=100000"),
                    log.replace("FINAL status=0", "FINAL status=-2")):
            with self.assertRaises(AssertionError):
                validate(bad)

    def test_cpu_window_rejects_e90_before_connecting(self):
        import e90_task_session as session
        with patch("sys.argv", ["e90_task_session.py", "--device", "e90", "--action", "run", "--host-version", "49",
                                "--session", "work/evidence/e90/d0-20261003-clean34", "--tag", "test-do-not-create",
                                "--command", "dmm-ring-window batch=15 frames=8"]), patch("e90_task_session.Device") as connect, patch("sys.stderr"):
            with self.assertRaises(SystemExit):
                session.main()
            connect.assert_not_called()

    def test_cpu_window_rejects_wrong_scope_or_impossible_time(self):
        command="dmm-ring-window batch=15 frames=8"
        log=(ROOT / "docs/evidence/2026-10-04/n95-window64-pilot-b15-f8-01.txt").read_text(encoding="ascii")
        validate_journal(log,command,49)
        for bad in (log.replace("cpu_us=38300", "cpu_us=1000000"),
                    log.replace("boundary_yield=1", "boundary_yield=0"),
                    log.replace("journaling_inside=0", "journaling_inside=1"),
                    log.replace("outer_ticks=2561", "outer_ticks=2560"),
                    log.replace("cpu_us=-1", "cpu_us=0"),
                    log.replace("machine=20002d84", "machine=20002496")):
            with self.assertRaises(RuntimeError):
                validate_journal(bad,command,49)

    def test_wsola_ring_rejects_wrong_results_and_broken_ownership(self):
        command = "dmm-ring-wsola frames=8"
        log = (ROOT / "docs/evidence/2026-10-04/n95-wsola63-pilot-f8-01.txt").read_text(encoding="ascii")
        validate_journal(log, command, 48)
        for bad in (log.replace("offset=172 expected_offset=172", "offset=171 expected_offset=172"),
                    log.replace("score=4364902 expected_score=4364902", "score=4364901 expected_score=4364902"),
                    log.replace("checked_words=1280", "checked_words=1279"),
                    log.replace("protocol=40", "protocol=39"),
                    log.replace("TIMING frame=8", "TIMING frame=7"),
                    log.replace("wpe_after=0", "wpe_after=1"),
                    log.replace("RING unmap=0", "RING unmap=-2"),
                    log.replace("machine=20002d84", "machine=20002496")):
            with self.subTest(bad=bad[-120:]), self.assertRaises(RuntimeError):
                validate_journal(bad, command, 48)

    def test_completed_clock_action_is_not_frequency_acceptance(self):
        from run_ring_series import require_stock_clocks
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "probe.log").write_text("ECPUSpeed(kHz) = 330000\nengine NOT ready: err -20 at step [patcher self-test]\n")
            with self.assertRaisesRegex(RuntimeError, "stop before another RUN"):
                require_stock_clocks({"complete": True, "probes": [{"path": "probe.log"}]}, directory, "e90")

    def test_native_ring_rejects_moved_pages_and_kernel_snapshots(self):
        command = "dmm-ring-native batch=2 frames=8"
        lines = [f"C55STREAM v46 command='{command}'", "BASE attach gate=0 reused_running=1 proc_load_calls=0",
                 "PROCESSOR STATE rc=0 state=1 expected=1 native_ioctl=2 cached=1 no_patcher=1 no_proc_load=1"]
        def pages(phase):
            return [f"NATIVE PAGE phase={phase} index={i} linear={0xced43000+i*4096:08x} physical={0x81643000+i*4096:08x}" for i in range(4)]
        lines.extend(pages(0))
        lines.extend(["NATIVE PAGES rc=0 phase=0 pages=4 bytes=16384 no_patcher=1 immutable_compare=0", "RING map=0",
                      "create=0 status=0 ", "NATIVE pre-RUN gate=0 env=00007654 state=1 no_patcher=1 proc_load_calls=0 env_allocator=RMS_MEM_valloc",
                      "BEGIN execute", "execute start=0 status=0"])
        lines.extend(f"RING FRAME frame={i+1} slot={i*2%15} batch=2 packet_start={i*2} wall_us=300 cpu_us=100 bad_words=0 dsp_ticks=12" for i in range(8))
        lines.append("RING DATA PASS bytes=16384 packets=16 frames=8 batch=2 total_exchange_us=2400")
        lines.extend(pages(1))
        lines.extend(["NATIVE PAGES rc=0 phase=1 pages=4 bytes=16384 no_patcher=1 immutable_compare=1", "BEGIN delete", "delete=0 status=0",
                      "free task=0", "RING unmap=0", "RING unreserve=0", "RING free native=0", "free native out=0", "free native in=0", "BEGIN close", "FINAL status=0"])
        log = "\n".join(lines) + "\n"
        validate_journal(log, command, 46)
        for bad in (log.replace("phase=1 index=0 linear=ced43000 physical=81643000", "phase=1 index=0 linear=ced43000 physical=81649000"),
                    log.replace("BEGIN execute", "POINTER snapshot=0\nBEGIN execute"),
                    log.replace("env=00007654", "env=00000000"),
                    log.replace("NATIVE PAGES rc=0 phase=1", "NATIVE PAGES rc=-20 phase=1")):
            with self.assertRaises(RuntimeError):
                validate_journal(bad, command, 46)

    def test_dcr_diagnostic_rejects_missing_protocol_and_inconsistent_wpe(self):
        command = "dmm-ring-dcr batch=15 frames=8"
        path = ROOT / "docs/evidence/2026-10-04/n95-dcr62-pilot-b15-f8-01.txt"
        log = path.read_text(encoding="ascii")
        validate_journal(log, command, 47)
        for bad in (log.replace("protocol=39", "protocol=38"),
                    log.replace("wpe_before=0", "wpe_before=1"),
                    log.replace("machine=20002d84", "machine=20002496"),
                    log.replace("DCR READ frame=8 ", "DCR READ frame=7 "),
                    log.replace("writes=0", "writes=1")):
            with self.assertRaises(RuntimeError):
                validate_journal(bad, command, 47)
        ordinary = log.replace(f"command='{command}'", "command='dmm-ring-native batch=15 frames=8'")
        with self.assertRaises(RuntimeError):
            validate_journal(ordinary, "dmm-ring-native batch=15 frames=8", 47)

    def test_ring_requires_all_packets_and_mapping_release_after_task_free(self):
        command = "dmm-ring batch=2 frames=8"
        lines = [f"C55STREAM v38 command='{command}'", "BASE attach gate=0 reused_running=1 proc_load_calls=0",
                 "create=0 status=0 ", "execute start=0 status=0", "matching_queues=1 require_unique=1",
                 "ROUTING pre-RUN gate=0 no_run_on_failure=1"]
        lines.extend(f"RING FRAME frame={i+1} slot={i*2%15} batch=2 packet_start={i*2} wall_us=300 cpu_us=100 bad_words=0 dsp_ticks=12" for i in range(8))
        lines.extend(["RING DATA PASS bytes=16384 packets=16 frames=8 batch=2 total_exchange_us=2400",
                      "BEGIN delete", "delete=0 status=0", "free task=0", "RING unmap=0", "RING unreserve=0",
                      "RING free native=0", "free native out=0", "free native in=0", "BEGIN close", "FINAL status=0"])
        log = "\n".join(lines) + "\n"
        validate_journal(log, command, 38)
        for bad in (log.replace("bad_words=0", "bad_words=1", 1),
                    log.replace("packet_start=2", "packet_start=0", 1),
                    log.replace("free task=0\nRING unmap=0", "RING unmap=0\nfree task=0"),
                    log.replace("RING unreserve=0", "RING unreserve=-2")):
            with self.assertRaises(RuntimeError):
                validate_journal(bad, command, 38)

    def test_host35_preserves_running_base(self):
        log = complete_log().replace("v21 ", "v35 ").replace(
            "create=0", "BASE attach gate=0 reused_running=1 proc_load_calls=0\ncreate=0").replace(
            "execute submitted=", "ROUTING preflight env=00007620 matching_queues=1 require_unique=1\n"
            "ROUTING pre-RUN gate=0 no_run_on_failure=1\nBEGIN execute\nexecute submitted=")
        validate_journal(log, "run-transfer reps=0 bytes=512 frames=8", 35)
        for bad in (log.replace("BASE attach gate=0", "BASE attach gate=-18"),
                    log.replace("proc_load_calls=0", "proc_load_calls=1"),
                    log.replace("BASE attach gate=0", "BEGIN base load\nBASE attach gate=0")):
            with self.assertRaises(RuntimeError):
                validate_journal(bad, "run-transfer reps=0 bytes=512 frames=8", 35)

    def test_host34_requires_unique_source_before_run(self):
        log = complete_log().replace("v21 ", "v34 ").replace(
            "execute submitted=", "ROUTING preflight env=000077e0 matching_queues=1 require_unique=1\n"
            "ROUTING pre-RUN gate=0 no_run_on_failure=1\nBEGIN execute\nexecute submitted=")
        validate_journal(log, "run-transfer reps=0 bytes=512 frames=8", 34)
        for bad in (
            log.replace("matching_queues=1", "matching_queues=2"),
            log.replace("env=000077e0", "env=00000000"),
            log.replace("gate=0", "gate=-11"),
            log.replace("BEGIN execute\n", "").replace("create=0", "BEGIN execute\ncreate=0"),
        ):
            with self.assertRaises(RuntimeError):
                validate_journal(bad, "run-transfer reps=0 bytes=512 frames=8", 34)

    def test_routing_diagnostic_cannot_count_as_d0(self):
        for log, command in (
            (complete_log().replace("run-transfer", "run-routing"), "run-routing reps=0 bytes=512 frames=8"),
            (complete_log().replace("BEGIN close", "ROUTING phase=before-delete diagnostic_only=1\nBEGIN close"), "run-transfer reps=0 bytes=512 frames=8"),
        ):
            with self.assertRaises(RuntimeError):
                validate_journal(log, command)

    def test_patcher_read_requires_exact_rom_words_and_three_ordered_copies(self):
        words = "e5d00040/e5911000/e3500000/01a00001/11a00861/e12fff1e"
        log = ("C55STREAM v29 command='patcher-read-check' machine=20002496 fast_counter_hz=32768\n"
               "profile guard=0 delta=ff99ca70\n"
               f"PATCHREAD pass=0 rc=0 source=004195b0 destination=00419570 bytes=24 words={words}\n"
               f"PATCHREAD pass=1 rc=0 source=803f7664 destination=00419570 bytes=24 words={words}\n"
               "PATCHREAD pass=2 rc=0 source=c8010b20 destination=00419570 bytes=24 words=00000000/00000001/00000001/00000000/00000000/00000001\n"
               "PATCHREAD PASS destination_own_ram=1 kernel_code_writes=0 prcm_writes=0 dsp_open=0 no_run=1\n"
               "FINAL status=0\n")
        validate_journal(log, "patcher-read-check", 29)
        validate_journal(log.replace("\n", "\r\n"), "patcher-read-check", 29)
        for bad in (log.replace("e5d00040", "00000000"),
                    log.replace("source=803f7664", "source=803f7668"),
                    log.replace("machine=20002496", "machine=20002d84"),
                    log.replace("pass=2", "pass=1"),
                    log.replace("destination=00419570 bytes=24 words=00000000", "destination=00419574 bytes=24 words=00000000"),
                    log.replace("profile guard=0", "profile guard=-20"),
                    log.replace("FINAL status=0", "BEGIN processor open\nFINAL status=0")):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                validate_journal(bad, "patcher-read-check", 29)

    def test_pointer_snapshot_journal_validation(self):
        log = (
            "C55STREAM v30 command='pointer-snapshot' machine=20002496 fast_counter_hz=32768 firmware_rc=0 firmware='V 07.38.39.1'\n"
            "profile guard=0 delta=ff99ca70\n"
            "POINTER load=0\n"
            "POINTER open=0\n"
            "POINTER pdd_slot=c80019fc container=c8004f20 rc=0\n"
            "POINTER pdd_count=12 objects_ptr=c8005380\n"
            "POINTER pdd_obj[0]=c800a120 vtable=803f8380\n"
            "POINTER factory=c800a120 expected_vtable=803f8380\n"
            "POINTER manager_ptr=c800a300 rc=0\n"
            "POINTER manager magic=434f5250 back_factory=c800a120 proc_index=0 common_board=c800a408\n"
            "POINTER board=c800a400 board_swap_byte=01 context=c800a600\n"
            "POINTER ctx_reader=c800a4ac ctx_board=c800a408 ctx_from_dsp=c800a6e0 ctx_records=c800a6f0 queue16=c800a610 queue40=c800a628\n"
            "POINTER shared_base=c8012000 reader_swap_byte=01\n"
            "POINTER SNAPSHOT PASS root_provenance=1 factory_matched=1 manager_valid=1 board_valid=1 destination_own_ram=1 kernel_code_writes=0 prcm_writes=0 dsp_open=0 no_run=1\n"
            "FINAL status=0\n"
        )
        validate_journal(log, "pointer-snapshot", 30)
        validate_journal(log.replace("\n", "\r\n"), "pointer-snapshot", 30)
        for bad in (
            log.replace("v30", "v29"),
            log.replace("machine=20002496", "machine=12345678"),
            log.replace("profile guard=0", "profile guard=-20"),
            log.replace("POINTER SNAPSHOT PASS", "POINTER SNAPSHOT FAIL"),
            log.replace("FINAL status=0", "FINAL status=-1"),
            log.replace("FINAL status=0", "BEGIN processor open\nFINAL status=0"),
            log.replace("FINAL status=0", "QUARANTINE\nFINAL status=0"),
        ):
            with self.subTest(bad=bad), self.assertRaises(RuntimeError):
                validate_journal(bad, "pointer-snapshot", 30)

    def test_existing_n95_clock_profile_rejects_changed_or_missing_registers(self):
        engine = ("EMachineUid = 536882564\nengine self-check done\n"
                  "restore check: stock DoControl(1,0) -> 129  ok\n"
                  "CM_CLKSEL1_PLL @c6008540 = 0006f400\nCM_CLKSEL2_PLL @c6008544 = 00000002\n"
                  "CM_CLKSEL_MPU @c6008140 = 00000002\nCM_CLKSEL1_CORE @c6008240 = 04360844\n")
        dsp = ("EMachineUid = 536882564\nprofile: RM-320 35.0.001/31.0.015\n"
               "NOT STOCK AT START: m=111 CLKSEL1_CORE=04360844 CLKSEL_MPU=00000002\n"
               "CM_CLKSEL_DSP @c6008840 = 000023c3\nDSP probe done\n"
               "restore check: stock DoControl(1,0) -> 129  ok\n")
        self.assertTrue(n95_m111_clock_matches(engine, dsp))
        for bad in (engine.replace("0006f400", "00056400"), engine.replace("04360844", "04360644"),
                    engine.replace("CM_CLKSEL_MPU", "unknown"), engine + "CM_CLKSEL_MPU @c6008140 = 00000004\n"):
            self.assertFalse(n95_m111_clock_matches(bad, dsp))
        self.assertFalse(n95_m111_clock_matches(engine, dsp.replace("000023c3", "000023c4")))

    def test_clean_eight_packets(self):
        validate_journal(complete_log(), "run-transfer reps=0 bytes=512 frames=8")

    def test_installed_host_version_must_match(self):
        host22 = complete_log().replace("C55STREAM v21 ", "C55STREAM v22 ")
        with self.assertRaises(RuntimeError):
            validate_journal(host22, "run-transfer reps=0 bytes=512 frames=8")
        validate_journal(host22, "run-transfer reps=0 bytes=512 frames=8", 22)

    def test_false_success_is_rejected(self):
        log = complete_log()
        for bad in (log.replace("errors=0 stop=1", "errors=1 stop=1"),
                    log.replace("frame=4 put=0/0", "frame=4 put=0/-33"),
                    log.replace("SIZE frame=4", "SIZE frame=5"),
                    log.replace("delete=0 status=0", "delete=-2 status=-2"),
                    log.replace("stop=1", "stop=0"),
                    log + "QUARANTINE\n"):
            with self.subTest(bad=bad[-100:]), self.assertRaises(RuntimeError):
                validate_journal(bad, "run-transfer reps=0 bytes=512 frames=8")

    def test_clean_diagnostic_is_not_an_ordinary_d0_cycle(self):
        ordinary = complete_log().replace("C55STREAM v21 ", "C55STREAM v25 ")
        diagnostic = ordinary.replace("command='run-transfer reps=0 bytes=512 frames=8'", "command='exit-stages'")
        with self.assertRaises(RuntimeError):
            validate_journal(diagnostic, "run-transfer reps=0 bytes=512 frames=8", 25)
        with self.assertRaises(RuntimeError):
            validate_journal(diagnostic, "exit-stages", 25)
        with self.assertRaises(RuntimeError):
            validate_journal(ordinary.replace("BEGIN close", "EXITDIAG stage=6\nBEGIN close"), "run-transfer reps=0 bytes=512 frames=8", 25)

    def test_deadline_preserves_live_owner(self):
        class Busy:
            calls = []
            def cmd(self, command):
                self.calls.append(command)
                return ["OK proc 42"] if command.startswith("START ") else ["OK", "1 c55stream"]
        device = Busy()
        with patch("e90_task_session.time.monotonic", side_effect=[0, 0, 31]), patch("e90_task_session.time.sleep"):
            with self.assertRaises(TimeoutError):
                run(device, "C:\\sys\\bin\\c55stream.exe run-transfer", 30)
        self.assertEqual(device.calls, ["START C:\\sys\\bin\\c55stream.exe run-transfer", "PS c55stream*"])

    def test_created_worker_message_requires_delivery_and_cannot_count_as_d0(self):
        log = ("C55STREAM v26 command='worker-message'\ncreate=0 status=0 wall_us=10\n"
               "EXITDIAG stage=7 protocol=26 result=1\n"
               "message cmd=00000606 arg1=a1b2c3d4\nMSGWORKER delivery=0 overall=0 no_run=1\n"
               "delete=0 status=0\nfree task=0\nfree native out=0\nfree native in=0\nBEGIN close\nFINAL status=0\n")
        validate_worker_message(log,26)
        queued = log.replace("C55STREAM v26 ", "C55STREAM v28 ").replace("command='worker-message'", "command='worker-message-queued'")
        validate_worker_message(queued,28)
        with self.assertRaises(RuntimeError):
            validate_journal(queued,"worker-message-queued",28)
        for bad in (log.replace("delivery=0", "delivery=-33"), log.replace("free native in=0", "free native in=-2"),
                    log.replace("BEGIN close", "BEGIN execute\nBEGIN close")):
            with self.assertRaises(RuntimeError):
                validate_worker_message(bad,26)
        with self.assertRaises(RuntimeError):
            validate_journal(log,"worker-message",26)

    def test_nonzero_process_exit_is_rejected(self):
        class Failed:
            def cmd(self, command):
                if command.startswith("START "):
                    return ["OK proc 42"]
                return ["EXIT -2 Kill"] if command.startswith("WAIT ") else ["OK", "0"]
        with self.assertRaises(RuntimeError):
            run(Failed(), "C:\\sys\\bin\\c55stream.exe create")

    def test_boot_probe_accepts_explicit_unsupported_getters_and_rejects_dsp(self):
        log = "\n".join(("C55STREAM v44 command='boot-info'",
                         "BOOT HAL startup_rc=-5 startup=0 exception_rc=-5 exception=0",
                         "BOOT USER fault_rc=-5 fault=0 id_rc=-5 id=0 info_rc=-5 code=00000000 data=00000000 extra=00000000",
                         "BOOT PROBE COMPLETE no_dsp_open=1 no_patcher=1 readonly_HAL=1",
                         "FINAL status=0"))
        validate_journal(log, "boot-info", 44)
        with self.assertRaises(RuntimeError):
            validate_journal(log.replace("FINAL status=0", "BEGIN processor open\nFINAL status=0"), "boot-info", 44)

    def test_native_processor_query_rejects_nonrunning_and_research_paths(self):
        log = "\n".join(("C55STREAM v45 command='processor-state'", "processor open=0",
                         "PROCESSOR STATE rc=0 state=1 expected=1 native_ioctl=2 cached=1 no_patcher=1 no_proc_load=1",
                         "PROCESSOR STATE PASS native_ioctl=2 no_patcher=1 no_create=1 no_run=1",
                         "BEGIN close", "FINAL status=0"))
        validate_journal(log, "processor-state", 45)
        for bad in (log.replace("state=1 expected", "state=2 expected"),
                    log.replace("rc=0 state", "rc=-5 state"),
                    log.replace("BEGIN close", "BEGIN execute\nBEGIN close"),
                    log.replace("BEGIN close", "POINTER snapshot=0\nBEGIN close")):
            with self.assertRaises(RuntimeError):
                validate_journal(bad, "processor-state", 45)

    def test_kernel_containers_audit_proves_e90_and_n95_root_and_factory(self):
        e90 = audit_e90(ROOT / "work/evidence/e90/rom")
        self.assertEqual(e90["container_root"]["root_address"], "C80019D4")
        self.assertEqual(e90["container_root"]["total_containers"], 17)
        self.assertEqual(e90["container_root"]["pdd_container_type_index"], 10)
        self.assertEqual(e90["container_root"]["pdd_container_slot_address"], "C80019FC")
        self.assertEqual(e90["factory_identity"]["vtable"], "803F8380")
        self.assertEqual(e90["manager_identity"]["magic_word0"], "434F5250 (PROC)")
        self.assertEqual(e90["manager_identity"]["board_pointer_offset"], 44)
        self.assertEqual(e90["board_identity"]["adjustment_to_base"], -8)

        n95 = audit_n95(ROOT / "../eka2l1/data/drives/z/rm-320/sys/bin")
        if n95.get("available"):
            self.assertEqual(n95["container_root"]["root_address"], "C80019F0")
            self.assertEqual(n95["factory_vtable"], "801B3D44")
            self.assertEqual(n95["manager_magic"], "434F5250 (PROC)")


if __name__ == "__main__":
    unittest.main()
