# V17: measurement conditions and the DSP timer

Full scope and criteria: work/PLAN.md; F05–F08 remain open.
Starting checkpoint 1430722: a working worker 512 B/Q15/ARM overlap/cleanup
on both phones, but the N95 frequency changes and the timer scale have not
been applied.

1. Verify the N95 ROM's dvfs_interface request0/reserve100/release0, the
   percent getter, and the destructor. Before native calls, check the live
   fingerprints. Use the standard reservation; there are no new kernel/PRCM
   patches.
2. Host v17 reserves the standard mode on the N95, records the MPU percent
   before and after each packet, and releases it before FINAL. On the E90
   this branch is not executed.
3. Worker protocol17 returns the absolute CLK_gethtime at offset14 instead of
   the wire cookie; the pointer cookie remains a mandatory create/delete gate.
   The rest of the 512-byte format and the Q15 workload do not change.
4. worker-calibrate: 8 correct echo packets, reps0, without CRC; pauses of
   100/200/400/800 ms. The DSP stamp must lie between the ARM issue and
   completion. For delta timestamps, compute the bounds on the DSP timer rate
   in Hz from the FastCounter brackets, allowing for one counter tick of
   error. Do not use 164.
5. Source/ASM/imports/DOFF preflight, immutable archive; fresh preparation and
   exact backup. First N95 one; after a clean cleanup — calibration, Q15, and
   three alternating same-condition pairs. Do not repeat the negative without
   a new contract, journal recovery, and a normal readback.
6. Repeat the confirmed protocol on the E90 after SIS. After each series,
   exact normal and original clocklog restore, PS/INFO/readback.
7. Update the honest timing bounds and the assessment of application packets;
   keep the source/proofs in private GitHub; the full completion audit
   separately.
