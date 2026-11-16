# N95: CPU counter calibration

A separate user-mode counterprobe v1 completed three clean series of 36 samples
each, without DSP, patcher or performance reservation. The journal was written
after all timing windows. Before each baseline there is a 20 ms busy prime;
busy/sleep at 1/10/200 ms were compared with raw boundaries, with an explicit
User::After(1) before the baseline and after the work. The final yield is
included in the wall/CPU interval.
[Results](evidence/2026-10-04/n95-cpu-counter-results.json).

Raw busy 1 ms and busy 10 ms in 8/9 samples each returned a CPU delta of 0. Raw
sleep 10 ms in 2/9 samples had a CPU delta larger than the outer wall (max 16906 us
versus a wall of about 11 ms). This reproduces the carry-over of the previous CPU
slice accounting through the short baseline. It occurs without DSP and does not
indicate its load. For all 54 samples with boundary yields, CPU delta ≤ outer
wall. Busy 1 ms with yields has CPU p50 = 1007 us; busy 200 ms — 197937 us; sleep
200 ms — 61 us. After yield, the wall includes the additional sleep and is not
kernel latency.

Conclusion: the old short GetCpuTime deltas, and the N95 ring CPU percentages
computed from them, are not qualified as ARM load. The raw values are kept; we do
not correct them with the new calibration. The WSOLA63 wall/ARM timings have
separate timers and do not depend on these CPU deltas. A long aggregate ring
window with a settling boundary is needed next, without ARM baseline or file I/O
inside. The pack/cache/checking costs and the final yield must be explicitly
accounted for within the boundaries.

The published [Symbian RThread wrapper](https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/blob/0c3208650587ac0230aed8a74e9bddb5288023eb/kernel/eka/euser/us_exec.cpp#L4818)
passes the ThreadGetCpuTime request; the
[Exec implementation](https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/blob/0c3208650587ac0230aed8a74e9bddb5288023eb/kernel/eka/kernel/sexec.cpp#L2040)
converts counter units to us. In the later
[NKern reference](https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/blob/0c3208650587ac0230aed8a74e9bddb5288023eb/kernel/eka/nkern/sched.cpp#L109),
the getter adds the current slice to the total. The installed N95 kernel has not
been compared with this source: the observed behavior differs, so we do not claim
as proven the exact firmware implementation or the reason for the difference from
the reference.

All three of the counterprobe's own files were absent before deploy; the EXE/hash
after PUT was verified GET-equal. After the three EXIT0 runs, the exact EXE/hash
and the last journal were checked; only these three files were removed, and LS
confirmed their absence. The five originals c55stream/ocprobe were not changed;
E90 was not queried.
[Artifact proof](evidence/2026-10-04/n95-counterprobe-artifacts.json),
[cleanup](evidence/2026-10-04/n95-counterprobe-remove01.json).
