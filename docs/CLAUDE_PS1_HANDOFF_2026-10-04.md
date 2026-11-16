# Claude handoff: C55x results for PS1Emulator

Date: 2026-10-04. Current work completed as a research checkpoint per
the user's request. Do not schedule new hardware experiments automatically.
Changes were made in `TMS320C55x test`; PS1Emulator code was not changed.

**Decision for current PS1: leave WSOLA, MDEC, and plain SPU mix on ARM.**
On N95, none of the measured DSP jobs against the corresponding current ARM kernel
won in blocking mode even prior to setup. This is a sufficient result
for selecting the current implementation; general impossibility of async/resident DSP
is not established. The full production contract for shared memory is also not accepted.

## What to pass to PS1 now

1. Update `PS1Emulator/docs/dsp-integration-guide.md` and the DSP plan according to
   this report. Its initial v20/scalar numbers are historical; they do not prove
   a gain against current WSOLA SMLAD. The reference for the current decision is
   [PS1_CANDIDATES](PS1_CANDIDATES_2026-10-01.md), top addition 04.10.
2. Retain the current `WsolaBestOffset` in `src/symbian/snd_symbian.cpp`,
   ARM MDEC, and assembler `mix_chan` as working paths. Do not add blocking
   DSP offload for the measured jobs. Integrating these results by itself
   does not require installing research EXE/DLL on the phone.
3. If a separate experimental DSP branch is created, mark it
   unaccepted, with explicit enablement and profile verification. First close
   publication/ownership/lifecycle gates and define an independent W;
   only then implement a new async/resident job and compare with ARM.
   This is a subsequent assignment, not an incomplete implementation in this repository.

## Evidence D0–D2

| Stage | Achieved | What is not claimed |
|---|---|---|
| D0 | On N95 and E90, 3 consecutive clean create→RUN→packets→delete each, FINAL/EXIT0. Complete N95 inspect/create/3RUN journals published: 24 packets in total. | Universal safe cancel/fault recovery. Unconfirmed pending/delete ownership leads to QUARANTINE without automatic KILL. |
| D1 | Native shared payload ring 16KiB TOTAL; repeats, page identity, wrap/index carry, whole-region ownership, and clean teardown. N95 native 61: 3 series / 12 runs / 9360 packets from 6 stock brackets. | Entire path zero-copy: notifications still use native transport. Universal DSP→SDRAM→mailbox completion contract is not established. |
| D2 | Real paired A/H+D/S, exact outputs, and strict scenarios for MDEC66, SPU67, current-WSOLA68; decision by job sizes recorded. | Full game win, full SPU/PCM, captured gameplay, or useful async W. |

[Acceptance matrix](N95_ACCEPTANCE_2026-10-04.md) contains hashes, complete
journals, limits, and final phone verification. D0 is accepted; D1 memory gate
is open; D2 verdict for the measured jobs is delivered. The entire initial
plan with deferred E90 is not declared completed.

## Numbers on which the decision is based

N95 8GB RM-320, firmware 35.0.001; stock clock brackets:
ARM 330.24MHz, bus 110.08MHz, DSP 220.16MHz. These are snapshots before/after series,
not continuous DVFS trace. Frequencies were not changed during experiments.
Below is p50 of the time of the **entire job**, microseconds. Tail samples were not excluded.

| Job | ARM A p50 | DSP path H+D ready p50 | Paired blocking wins before setup |
|---|---:|---:|---:|
| WSOLA current SMLAD, one search | 337.601 | 1098.633 | 0/360 |
| MDEC 6IDCT+RGB24,1 macroblock | 78.201 | 2655.029 | 0/360 |
| MDEC, 2 macroblocks | 110.626 | 4272.461 | 0/360 |
| MDEC, 4 macroblocks | 295.639 | 7690.430 | 0/360 |
| Plain SPU, 1 voice × 64 samples | 3.576 | 1617.432 | 0/360 |
| Plain SPU, 8 voices × 64 samples | 27.180 | 3295.898 | 0/360 |
| Plain SPU, 24 voices × 64 samples | 40.531 | 3540.039 | 0/360 |

H+D from packing to ready reconstructed result in ARM memory, including
cache/transport/DSP. Oracle/header/input-unchanged checks and recording
of the journal are outside the timed job. A is an isolated warm kernel, averaging
repeats; this is not live gameplay. Pure D must not be deduced by subtracting
overall medians. CPU for these application kernels was not measured (`-1` = unmeasured).

Instrumented S=setup+teardown, p50: WSOLA 865080us, MDEC 840178us,
SPU 863494us. S includes lifecycle journaling; this is not minimum production
startup. Adding S/N only worsens the shown blocking comparison.
WSOLA H+D p95/p99/max=2075.195/8514.404/9155.273us;
MDEC batch 4 max 105682us; SPU 24 voice max 14312.744us.
Detailed distributions/per-case/strict scenarios:
[WSOLA68](N95_WSOLA_CURRENT_2026-10-04.md),
[MDEC66](N95_MDEC_RING_2026-10-04.md), [SPU67](N95_SPU_RING_2026-10-04.md).

Distinct synthetic CPU64,3 series / 9360 packets: batch 1/2/8/15 exchange
p50=915/1190/3021/5126us, weighted threadCPU 45.37/45.87/48.09/45.68%.
Full-window useful bidirectional bandwidth 0.712/0.960/1.357/1.500MB/s.
This is pack/cache/full correctness checks/final yield, not pure wait CPU,
and not application-kernel cohort. [CPU64](N95_RING_CPU_2026-10-04.md).
Do not combine these numbers with faster historical candidate54/v20.

## Job boundaries and materials for possible further integration

Ring: 16KiB **total**, 1024B control + 15 input + 15 output slots of 512B each;
480B payload/slot, 7200B payload in each direction. This is not 16KiB per
direction. C55x `int/char` 16bit, `long` 32bit; serialization of 32-bit values
via explicit low/high 16 words. ARM pointer is not a DSP pointer; a structure
with native pointers is not a wire format. Ownership encompasses the whole ring.

- **WSOLA:** 4 input slots, 1 output; 880 signed 16 samples: 220 template + 660
  search, coarse step 4 / refine ±4, strict `>` ties and the same order.
  Return offset/score/scored. Snapshot current ARM:
  `src/wsola_current/kernel.inc`, `snapshot.json`; CSL 3.4.3/O2/ARMv6,
  5 SMLAD sites. DSP: `src/dsp/wsola_dsp.c`, `ring_wsola_exchange` in
  `src/dsp/stream_node.c`. Next hop depends on previous offset;
  do not fill the ring with independent future searches of a single stream.
- **MDEC:** job after RLE/dequantization, before 6IDCT+RGB24. Per macroblock
  384 signed 32 coefficients + 6 masks + BW flag = 1550B input, 768B output
  (192 uint32 RGB24). Batches 1/2/4: input 4/7/13, output 2/4/7 slots.
  `src/mdec/kernel_arm.inc`, `kernel_c55.inc`, `kernel_c55.c`, fixtures/snapshot;
  `ring_mdec_exchange` in `stream_node.c`. ARM GCCE 4.6.3/O2/ARMv6.
  Current `rl2blk` already invokes IDCT: offload would require changing
  the job boundary while preserving RAM visibility, DMA/IRQ/status, and dynarec invalidation.
- **SPU:** plain post-ADSR mixer, samples 32 / volumes 32 / initial sums 32;
  output 128 stereo sums 32.1/8/24 voice jobs: input 2/6/15 slots, output 2.
  For 24 voices, input 6848B; maximum 66 paired samples in 7200B, whereas
  64 were measured. `src/spu/mix_arm.s`, fixtures/snapshot;
  `src/dsp/spu_mix_ring.inc`. Packed gain/sign spill and modulo 32 sums
  are preserved exactly. This is not ADPCM/ADSR/noise/reverb/capture/IRQ/fullSPU.
  Full-state variant requires coherency of 512KiB SPU RAM and histories;
  optional worker item 8396B does not fit into the current payload.

Fixtures confirm exact outputs in the tested range, not
exhaustive legal game inputs. Do not change signed 32 coefficients to 16bit
for the sake of the packet. Preserve GPL notices/COPYING when porting MDEC/SPU.

## Async: what must be proven prior to a new implementation

According to the guide `T=H+D`, `q=S/N`: `max(T,W)+q<A+W` is equivalent to
**`q<A` and `W>T+q−A`**. For blocking W0, `T+q<A` is required; it does
not pass here. For a single ARM thread, H also occupies this processor:
`H+max(D,W)+q<A+W` additionally requires **`H+q<A`**.
Elapsed intervals outside notification give only conditional bounds for
the same stage envelope, not a production CPU minimum.

W is genuinely independent work before the point of result consumption, not average
frame time / guest cycle delay. In unmodified blocking calls W0; available
W after schedule change is unknown. WSOLA may be the next hypothesis,
but measured H/D/S or theoretical threshold is not an async gain.
[Source dependencies and paired bounds](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md).

For production shared memory, two contracts are open:
DSP external writes completed before visible notification; ARM completion
after invalidation before reading. Saved N95 ARM audit proved clean DSB
and both cache branches; short invalidate MVA routine has no explicit
DSB, caller/context requires separate qualification.
In measured DSP 63/65/67, control stores before RET/STRM_issue are confirmed
by full compiler listings; DCR read-only WPE0 does not establish an OMAP fence.
Successful packets do not replace this contract.
[ARM cache audit](N95_ARM_CACHE_2026-10-04.md),
[DSP compiler listings/audit](evidence/2026-10-04/n95-kernel-publish-audit.json).

A timeout with unconfirmed DSP ownership does not mean permitted ARM
fallback to the same buffers or free/unmap/unload. An accepted
stop/join/ownership return is required; otherwise QUARANTINE and controlled recovery.
The current OS per-device lock protects against competing research sessions,
but is not production DSP resource arbitration.

## Versions, artifacts, and verification without a phone

| Cohort | ARM host | DSP / protocol | DSP SHA256 |
|---|---:|---|---|
| Current WSOLA68 | 53 | exact retained 63 / 40 | `646231C29251F94B688FD89E2F729553CBF5083D1C734FFC6775FEE7E9470BFF` |
| MDEC66 | 51 | exact 65 / 41 | `EA70403E72E513E868D6BCD4D35ABD3D4552A38AFCC258250B00CD3A5845B534` |
| SPU67 | 52 | 67 / 42 | `181D2851F53F3DD155AC0F37DA9288A26CB364865A3336113F0254A76B3B4AE4` |

Host/DSP/source/build hashes are in the respective `*-artifacts.json`, actual
runs — in `*-results.json`. `out/arm/c55stream.exe` is currently host 53;
generic `out/dsp/c55stream.dll55l` is still SPU67. For WSOLA, typed
`c55stream-dmm-ring-wsola.dll55l` is required, not the generic file. On N95,
originals were restored rather than leaving research 53 installed.

At the root of the research repo, with Python 3:

```powershell
python tools/verify_n95_acceptance.py
python tools/verify_kernel_publish.py
.\tools\check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

The master verifier checks hashes / complete N95 D0 journals / native 61 / CPU64 /
MDEC65–66 / SPU67 / current WSOLA68 / dependencies / ARM-cache / compiler order.
It does not connect to phones. Full D0 and kernel listings are published;
ROM/source checks are supplementary when corresponding local files are available.
Artifact/environment check requires SDK and local build outputs.

## Phone state and handoff boundary

**N95:** 04.10 at 09:32:35 UTC last read-only INFO/PS/GET checkpoint:
all 5 originals GET/SHA-equal (DSP, stream log, clock log, EXE, hash),
`c55stream`/`ocprobe` PS0. This is a snapshot at the specified time; no new phone
commands were issued during report completion. Saved originals/manifest:
`work/evidence/n95/d0-20261003-clean34/` (local ignored archive).
Published [final verification](evidence/2026-10-04/n95-acceptance-final-verify.json).

**E90:** deferred by the user; **restoration of EXE/hash/journals is not
yet completed**. Last known host 46, DSP original; compatible RDomain
clock probe built, not installed / not run. No new accepted
frequency qualification. Saved originals:
`work/evidence/e90/d0-20261003-clean34/`. Returning to E90, first
obtain current journals/PS/identity, then return own originals with
GET/SHA verification, and after that decide the need for new probes.
Do not repeat a failed RUN without a new hypothesis. The cause of auto-reboots
is not established; blaming the daemon is not confirmed.
[Recovery checkpoint](evidence/2026-10-04/e90-native61-oct04-recovery-checkpoint.json),
[reboot analysis](E90_DAEMON_REBOOT_2026-10-04.md).

Local saved originals/ROM are not included in Git; verify their presence before
hardware recovery. `daemon startTick/boot/by` is a launch tuple,
not a unique phone reboot ID. For now, no physical actions are required from
the user: a verified research result is being handed off.
