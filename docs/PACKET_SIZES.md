# Packet sizes: N95 and E90, v18

The stage plan is `work/PLAN_V18.md`; the full scope is `work/PLAN.md`.
V18 continues the own worker confirmed in v17: generic library2, CREATED,
`NODE_wait(NULL, ...)`, an explicit stop, and a join before the resources are
released. The official RUN is not used. This is a research prototype.

## Contract and artifacts

The host properties input+184/output+1592 contain the stream size in field
+4. The PDD of N95 `8019FE38` and of E90 `803E4478` copies it to RMS stream
definition+0 without scaling. These are C55 16-bit words; the descriptor
length in the transfer is in ARM bytes. The instructions that set the sizes
were checked on both ROMs:
[contract](evidence/2026-10-01/n95-e90-stream-size-contract.json),
`tools/rev/check_stream_sizes.py`. The DCD was left unchanged.

Native allocation mode 2 requires a positive size that is a multiple of 4096.
The prototype allocates 4096 bytes each for input and output and limits the
packets to 512–4096 B with an even length. This is the limit of this
prototype, not an established maximum of the driver. The worker accepts
identical input/output sizes of 256–2048 C55 words, checks the reclaimed
length and the header length, and transforms the whole payload. Q15 dot240 is
computed only over the first 240 values; the coefficient/state contract is
unchanged.

Host 29760 B, SHA-256 `571C5A6221C7E7815558A2C3AE5F6665D8D7DE0B82D676488869C7BAA260F14F`;
DSP 4852 B `DD8D50DC20F66F44A7212D86B364C4905EF37227C1A3BF945A26B9CE95510AD3`.
DOFF/imports/ASM and the new immutable archive:
[artifacts](evidence/2026-10-01/worker-stream-v4-artifacts.json).
SIS v18 was delivered and installed on E90; the EXE matched on read-back and
passed the runtime profile. Raw firmware, binaries, keys and screenshots are
not published.

## Method

On each phone: minimal single-packet runs of 512, 1792 and 4096 B, Q15 with
reps 1000 on eight 4096-byte packets, and three series of six sizes, 32
packets each. In total **22 successful runs and 587 correct packets on each
phone**. The order of the sizes within the series is forward, then reverse,
then with a cyclic shift. Before each run: inspect, an exact GET of the DSP,
and a check of a fresh preparation. On N95 the MPU percent=100 before and
after each packet; on E90 the N95 dvfs API is not called.

`worker-transfer` has reps0 and does not compute the ARM CRC. For each packet,
the FastCounter (32768 Hz) records the start before the submit and the
observed completion after two Waits. The interval contains the driver
issue/wait/scheduling, the transport and the full DSP echo. Input generation,
output checking, logging and the one-time create lie outside it. The counter
resolution is approximately 30.5 µs. This is **the time to the observed
completion**, not a pure DMA latency/bandwidth.

The table contains 96 packets per size. p95 is an empirical nearest-rank
percentile; the max is kept without removing slow packets. These numbers are
not guaranteed deadline limits. One create supports 32 packets, not 96: these
are three separate runs.

| Packet / payload, B | N95 median / p95 / max, µs | E90 median / p95 / max, µs |
|---|---:|---:|
| 512 / 480 | 335 / 366 / 640 | 396 / 396 / 488 |
| 1568 / 1536 | 518 / 518 / 579 | 610 / 640 / 793 |
| 1792 / 1760 | 518 / 518 / 549 | 640 / 701 / 7812 |
| 2048 / 2016 | 549 / 579 / 671 | 701 / 762 / 7690 |
| 2304 / 2272 | 610 / 640 / 3021 | 762 / 793 / 3234 |
| 4096 / 4064 | 885 / 946 / 1251 | 1129 / 1220 / 2502 |

[N95: all runs and byte-exact journals](evidence/2026-10-01/n95-packet-sizes-v18-results.json),
[E90](evidence/2026-10-01/e90-packet-sizes-v18-results.json).
`tools/summarize_packet_sizes.py` independently checks the packet counts and
sizes, Q15 against the computed reference, CRC, sequence/stop, per-frame MPU,
the exact DSP, FINAL/EXIT0, delete/free, and the absence of RUN/KILL. There
are no restarts in this series.

## Consequences for application tasks

WSOLA transfers 1760 B of data; with the 32-byte header this is **1792 B
input**. This size goes through in a single packet. At present the output is
also 1792 B, although the real search needs only the offset and the score. The
measurement of 518/640 µs is a reference point for an echo of this size; the
WSOLA time, the preparation and the short output have not been measured yet.
On E90 one correct packet took 7.812 ms, which is more than the hop
220/44100≈4.99 ms. Therefore such an offload requires a queue, a sample margin
and a measurement of underruns; a single median does not prove the suitability
of a synchronous call for each hop.

MDEC input of 1536 B needs 1568 B with the header; output RGB15/24 — 544/800 B.
The total application transfer would be 2112/2368 B with two headers. The
current 1568-byte echo transfers 1568 B in each direction, that is 3136 B.
Do not replace the asymmetric MDEC exchange with the sum of input/output as
the size of a single symmetric packet. The next gate is the actual kernel,
the short output, the DMA order, rounding/flags, and a measurement of
`A,D,H,S` on the same input.

The original DSP after both series returned GET-equal, PS0:
[N95 recovery](evidence/2026-10-01/n95-packet-sizes-v18-recovery.json),
[E90 recovery](evidence/2026-10-01/e90-packet-sizes-v18-recovery.json).
A later re-check of E90 confirmed the original DSP/log and host v18:
[E90 status](evidence/2026-10-01/e90-packet-sizes-v18-device-status.json).
After the user's reply, a repeated GET of N95 also matched for all three
files, PS0: [N95 status](evidence/2026-10-01/n95-packet-sizes-v18-device-status.json),
[shared checkpoint](evidence/2026-10-01/worker-stream-v18-checkpoint-device-status.json).
Between the completed series and this later check the N95 uptime decreased;
this is a new boot after the experiments. The cause is not yet established,
and a clarification was sent to the user. This is not hidden by a claim of no
restarts within the series already checked. Long-run stability, audio
coexistence, timer/idle and the negative lifecycle remain open. F05–F08 are
not yet marked as complete.
