# E90: reboot after UI control

The user confirmed a physical reboot during the last action. The cause is
**not established**. No new DSP RUN had been made before that, and the
separate `ringclock.exe` had not yet been installed or started even once.

At 00:59:23 UTC a successful session ran INFO, one `KEY down`, a framebuffer
SHOT, and a GET of an 800×352 snapshot. The daemon.log contains the end of the
GET at tick 814907 and the `client done` at 814919. The next attempt, at
00:59:46 UTC, did not connect the socket: the two scheduled keys and the next
SHOT were **not sent**. A journal obtained later shows a new daemon start at
tick 93682. The decrease of the system tick is consistent with the confirmed
reboot. The journal contains no panic/fault cause for this case.

`startTick` is the daemon process start time from `User::NTickCount()`, and
`boot/by` is the classification of its start by an argument or by a time
heuristic. This is **not a unique boot identifier of the phone**. The old
`boot` fields in the publications are kept for compatibility; the runner
conservatively stops the series when the startup tuple changes. A physical
reboot must be proven separately.

The local `tester_input.cpp` and `deploy_daemon.cpp` in the neighboring
SymbianDeployDaemon were reviewed. `KEY down` means a DownArrow press/release
with a 40 ms gap; `KEY` and `SHOT` do not call ResetMachine. SHOT worked
through CFbsScreenDevice/GetScanLine and allocates and frees the line buffers
on the heap. No explicit bounds error or leak was found in the path used.
This does not rule out a graphics driver/kernel fault or a delayed effect of
the patch. The installed daemon binary has not yet been matched against these
sources.

The entry `killed 1 stale instance(s)` comes from the daemon's startup code,
which removes earlier daemon processes; it does not mean a phone reboot. In
this case no REBOOT/RESTART/KILL commands were sent from the client.

The daemon is a possible participant in the failure, but the last failed
connect gives no ground to blame it in particular. The next stage is
INFO-only observation, preservation of the journals, and then separate checks
of the UI commands with time stamps. Until then, do not run a new clock/DSP
test and do not switch the patches at random.

Timeline, hashes and limits of the conclusions:
[e90-daemon-reboot-audit.json](evidence/2026-10-04/e90-daemon-reboot-audit.json).
Current files and the unfinished E90 recovery:
[recovery checkpoint](evidence/2026-10-04/e90-native61-oct04-recovery-checkpoint.json).
