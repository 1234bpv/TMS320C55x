# SPU: task boundary and the cost of transferring state

This is an offline audit of the current PS1Emulator sources, **not a
hardware SPU measurement**. The N95, after MDEC, has all originals and PS0;
the phone was not polled for this audit. The emulator was not changed. The
E90 remains deferred.

## What exactly is the candidate

do_samples/do_channels includes ADPCM/history, ADSR, noise, pitch/FMOD,
decode-buffer writes for voices 1/3, reverb, RAM/DMA coherency and guest IRQ.
mix_chan is only the accumulation of post-ADSR ChanBuf into signed32 stereo
SSumLR. On the ARM1136, the current HAVE_ARMV5 assembler uses smlawb/smlawt;
scalar C cannot be passed off as the current ARM baseline. Moving only the
mix does not take away the main ADPCM component, and it requires saving and
transferring the decoded voices, which are now processed sequentially through
one ChanBuf.

In the prior GT profile 2026-09-28: doSamples A1/A2 = 968/965 ms over 600
frames, average share of pass 3.714%. Sampling 1:16 gave dec_adpcm 644.4 ms,
mix_plain 227.9 ms, ADSR 18.8 ms. Mix_plain is about 379.833 µs/frame, or
31.600 µs/voice call, with 7212 calls and 5292000 voice samples. **3.7% is
the whole doSamples, not the budget of the pure mixer.** The profile has an
old build and ARM 330.24 / bus 165.12 MHz; this is not the current paired A
of this bench. Do not subtract the current ring latency from it as if from a
shared cohort.

## Sizes checked with the ARM compiler

GCCE 4.6.3 built the sizeof/offsetof of the current externals.h and struct
spu_worker without running any code. int/pointer 4 B, NSSIZE 914, ADSR 16 B,
SPUCHAN 56 B, sample_buf 64 B. SPUInfo 3840 B without thread code and 5440 B
with WANT_THREAD_CODE. Optional work_item 8396 B: 28 B header + 24×44 B
channels + 7312 B sums; worker 33840 B. Raw pointers, bitfields and ARM
layouts are not the C55 wire format. SPU RAM 524288 B, history 24×64 = 1536 B,
and the related heap buffers are separate; sizeof SPUInfo does not mean the
size of the full SPU state.

For a separate **plain mix of 24 voices**, keeping samples32, volumes32,
initial stereo accumulator32 and output accumulator32:

| Samples/job | Input bytes | Output bytes | Input/output slots 480 B | Fits |
|---:|---:|---:|---:|:---|
|32|3520|256|8/1|yes|
|64|6848|512|15/2|yes|
|66|7056|528|15/2|yes|
|68|7264|544|16/2|no|
|128|13504|1024|29/3|no|
|914|95248|7312|199/16|no|

Input = 24×samples×4 + 24×2×4 + samples×2×4; output = samples×2×4.
The 16 KiB TOTAL ring has 7200 payload bytes in each direction, not 16384
payload bytes. Metadata may lie in the control area; pointers are not
transferred. Larger batches can be reached through a resident DSP state or
another job boundary, but that is a different contract, which must be
measured and checked separately.

A full stateless copy of the SPU RAM requires at least 73 input handoffs by
capacity alone, without metadata/state/output. This is the number of
transfers, **not** a measurement of their time. A resident mirror/delta
protocol must ensure the ordering of DMA/register writes/readbacks, decode
history, envelope/noise/reverb, voice 1/3 capture and guest IRQ;
PCM-only equality is not sufficient.

After this audit, probe64 samples for 1/8/24 voices were run:
[SPU67 hardware results](N95_SPU_RING_2026-10-04.md). Exact 32-bit sums,
1080 full jobs, blocking winners 0/1080 before setup; the plain mix stays on
the ARM. The stage state stays on the ARM. This determines only the mix_plain
verdict. Moving the full SPU now is not recommended: the actual A/H/D, a
useful independent W, and the identity of the PCM/mutable state for such a
contract have not yet been checked.

Evidence and source hashes: [boundary audit](evidence/2026-10-04/n95-spu-boundary-audit.json).
Reproduction: `python tools/audit_spu_boundary.py` with the local emulator and GCCE.
For D2, the strict conditions S/N<A and W>H+D+S/N−A remain in force; this
audit does not replace the hardware timing and does not close the SPU or the
independent endpoint publication.
