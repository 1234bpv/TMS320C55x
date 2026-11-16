# N95: result dependencies and ARM serial overhead

In the measured blocking WSOLA68, MDEC66, and plain-SPU67, DSP does not provide
a gain against the corresponding ARM kernel. This audit specifies what must be
proven for an asynchronous variant. It does not modify the emulator and does not
execute commands on the phones; N95 remains after verified 5 originals/PS0,
E90 is deferred by the user.

[JSON with hashes, source lines, and all calculations](evidence/2026-10-04/n95-offload-dependency-audit.json)
was obtained from current local PS1Emulator source and published journals of
cohorts 66/67/68. [Audit](../tools/audit_offload_dependencies.py) reads the
neighboring project; [independent verifier](../tools/verify_offload_dependencies.py)
verifies hashed journals, all 2520 full-job timings, and strict inequalities.
Pilot jobs are not included in the statistics. Source excerpts are saved in the JSON;
if the neighboring project is available, the verifier also checks its full hashes.

## Where the result is needed

| Kernel | Current order in source | Requirements for overlap |
|---|---|---|
| WSOLA | `WsolaBestOffset` returns offset; it immediately selects `win` for overlap-add and replacing `iWsTail`. The next hop uses this new template; compaction modifies the search buffer. | Hold template/search until completion, defer mutation. Prove independence of refill/guest work and meeting audio deadlines. Future searches of the same stream are dependent. |
| MDEC | `rl2blk` interleaves RLE/dequant and IDCT of six blocks; `yuv2rgb24` writes guest DMA RAM before returning `psxDma1` and scheduling MDECOUTDMA. | Isolate a stable coefficient job; prove input/output aliasing, guest RAM visibility, dynarec invalidation, and DMA busy/status/IRQ ordering. The next RLE can be pipeline work only after this proof. |
| SPU plain mix | `ChanBuf` is reused by the next voice, `SSumLR` accumulates across voices; then MixCD/reverb/finish consume the sums and produce PCM. | Preserve per-voice samples and sum ownership. Account for FMOD, capture, noise, ADSR, register/DMA/SPU RAM ordering; resident full SPU requires a different contract. |

For an unmodified blocking call, there is no scheduled independent work between
submission and immediate consumption of the result: `W=0` in this structure.
This is not a measurement of the total reserve of guest CPU work, nor is it proof
that another scheduler is impossible. The guest-cycle delay of an MDEC event is
not independent ARM work in host wall time. The shell executes guest Execute,
followed by the audio pump; relocating the callback is not proven by this audit.

SPU has a conditional worker source, but deployed emulator binary and runtime
thread configuration were not tested here. The presence of a worker in the source
does not in itself prove its activity or safe DSP replacement.

## Necessary condition for the same ARM thread

The initial ideal model `max(H+D,W)+q < A+W`, where `q=S/N`, is equivalent to
two strict conditions: `q<A` and `W>H+D+q−A`.

If submission/completion are executed serially with `W` on the same ARM thread,
the model is refined to `H+max(D,W)+q < A+W`. Now `H+q<A` and `W>H+D+q−A` are
necessary: other work does not hide serial packing.

In the journals, `result_ticks−notification_ticks` are elapsed intervals of
packing/preparation/result reconstruction outside notification exchange.
Let us denote them `B`. Notification also includes ARM cache/submission/
completion work, so full `H` is not separately measured. Maintaining this
measured stage envelope, `B+q<A` is merely a necessary condition. This is not
a minimum of production CPU time: intervals include headers/padding/scratch and
possible scheduling delays. Another layout, zero-copy, or scheduler requires
a new measurement.

| Job | A p50, us | Pack p50, us | B p50, us | Jobs with B<A, q=0 | Jobs with B+S/10000<A |
|---|---:|---:|---:|---:|---:|
| MDEC, 1 macroblock | 78.201 | 427.246 | 549.316 | 0/360 | 0/360 |
| MDEC, 2 macroblocks | 110.626 | 732.422 | 976.562 | 0/360 | 0/360 |
| MDEC, 4 macroblocks | 295.639 | 1403.809 | 1922.607 | 1/360 | 1/360 |
| SPU, 1 voice ×64 samples | 3.576 | 213.623 | 305.176 | 0/360 | 0/360 |
| SPU, 8 voices ×64 samples | 27.180 | 671.387 | 762.939 | 0/360 | 0/360 |
| SPU, 24 voices ×64 samples | 40.531 | 885.010 | 946.045 | 0/360 | 0/360 |
| Current WSOLA SMLAD | 337.601 | 91.553 | 91.553 | 359/360 | 359/360 |

Conditions are calculated pairwise for each job with its lifecycle S; the
difference of medians was not used for them. The single MDEC pass is
series 3 / frame 89, batch 4: ARM 463615 ticks/16, B 34 ticks, result 136 ticks.
It is still not a blocking win; this is an isolated slow ARM sample, not
a stable advantage or confirmed overlap.

WSOLA passes the necessary serial condition almost always; however, at N 10000,
independent `W` is required with a paired threshold p50=847.608us in the previous
[WSOLA68 calculation](N95_WSOLA_CURRENT_2026-10-04.md). Neither such useful
work nor audio deadline/PCM equivalence is measured here. At N≤1000,
instrumented lifecycle S does not pass even the necessary condition for any
of 2520 jobs. S includes journaling and is not a minimum production startup.

Current kernels remain on ARM. For D2, a concrete independent W/state contract
is still required; for D1 — an independent OMAP2420 external-memory
publication/notification proof. These criteria remain open; the accuracy of
isolated synthetic jobs does not prove full-game speedup or identity of full
PCM/state.
