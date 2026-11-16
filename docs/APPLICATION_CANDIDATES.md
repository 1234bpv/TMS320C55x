# C55x applications in neighboring projects

Current source code and profiles reviewed on 2026-10-01. Streaming STRM/Q15 worker
v17 passed on N95/E90, including useful ARM CRC and clean termination;
v18 added verified larger packets and measurement without CRC/Q15; v20 — actual WSOLA
with ARMv6 baseline and input 1792/output 48 B. [WSOLA.md](WSOLA.md).
Below is assessment of candidates and integration plan; speedup of these applications
is not yet measured. Neighboring repositories were not modified.

## What has already been measured for the channel

8 packets of 512 B each without repeated create; with reps0 observed completion
N95335 us/E90396 us, without ARM CRC inside completion interval. This is issue/wait/echo,
not pure DMA latency and not bandwidth. Reps1000 means repeated dot240,
that is 240 thousand MACs per packet; with completion transfer about 1.5–1.65 ms.
This synthetic kernel is not identical to WSOLA/SPU/MDEC, and its time should not
be linearly transferred to other code/memory/batch size.

In v17 N95 reserves stock MPU mode, verifies 100% for each packet;
three pairs have S250–251/P149–151 ms. E90 S259–263/P156–160 ms.
DSP ticks in N95 are identical without doubled intervals. Reduction of wall time
by about 40% applies to dot240×10000 plus independent CRC, not applications.
Three calibration runs on each give ~19.2 MHz under short pauses, but
timer for 800 ms counts only ~501 ms of this scale; cause unknown.
Reported164 unsuitable for conversion. Compare ARM wall time.
[N95](evidence/2026-10-01/n95-worker-stream-v17-results.json),
[E90](evidence/2026-10-01/e90-worker-stream-v17-results.json).

V18 has 32-byte header and verified 512/1568/1792/2048/2304/4096-byte packets.
WSOLA 1760 B data fit in one 1792-byte input; MDEC 1536 B — in 1568.
On each phone three series of 32 packets per size. Median full echo
1792 B: N95518 us/E90640 us; 1568 B: 518/610 us. Generation of input and
verification of output are not included in this interval; DSP echo and scheduling are included.
This is an orientation `H_echo`, not a measurement of `H` of real application kernel and not its
guaranteed upper bound. The conditional old model of four 512-byte packets
is now replaced by these direct size measurements.

E90 had 1792-byte outlier 7812 us and 2048-byte 7690 us; all packets correct.
Cause not established. For WSOLA hop≈4.99 ms one median is insufficient:
queue/buffering, actual search and underrun measurement are needed. Complete table,
methodology and byte-exact evidence — [PACKET_SIZES.md](PACKET_SIZES.md).
WSOLA asymmetric output/search verified in v20. Long/audio-compatible work
and MDEC asymmetric kernel remain next integration gates.

## Shared profitability condition

Notation: `A` — time of this same kernel on ARM; `D` — DSP; `H` — preparation, transmission in both directions, request completion and coherency; `W` — independent useful ARM work; `S` — one-time node creation; `N` — number of portions.

- Sequential ARM: `A + W`.
- Blocking DSP: `H + D + W + S/N`; gain is possible only with `H + D + S/N < A`.
- Ideally overlapped execution: approximately `max(H + D, W) + S/N`. Real result must be measured by wall-clock time: copying and cache can compete for the bus.
- The stream must also fit in portion deadline, not only improve average time. The model `H ≈ L + (I + O)/B` requires separate estimates of `L`/`B`; v18 echo does not separate pure transport bandwidth from driver/echo/scheduling.

Approximately 9 ms of old empty create phase are included in `S`, not automatically in `H`. The table does not substitute fictitious channel speed.

## PS1Emulator

Paths below are relative to `../PS1Emulator/`.

| Stage | Concrete code and data | Suitability / limit |
|---|---|---|
| WSOLA correlation | `src/symbian/snd_symbian.cpp:WsolaBestOffset`, `CSymSnd::WsolaFeed` | Verified first DSP candidate: exact signed16 coarse/refine search with signed32 sum. ARM retains window selection, overlap-add, speaker queue. Works only with WSOLA enabled; application audio gain is still needed. |
| SPU voices / interpolation / mixing | `pcsx_rearmed/plugins/dfsound/spu.c:decode_block_data`, `do_samples_adpcm`, `do_channel_work`, `queue_channel_work`, `sync_worker_thread` | Regular fixed-point work, but depends on 24 channels, SPU RAM, ADSR, noise/FMod, IRQ and registers. Persistent state on DSP and transferring only changes are needed. |
| MDEC | `pcsx_rearmed/libpcsxcore/mdec.c:rl2blk`, `idct`, `yuv2rgb15`, `yuv2rgb24`, `psxDma1` | Second candidate for FMV: batch of macroblocks. Not universal 3D speedup; in GT/Crash without FMV MDEC may not run. Rounding identity and partial DMA are needed. |
| GTE | `pcsx_rearmed/libpcsxcore/gte.c`, `gte_arm.S`, dynarec calls | Poor first candidate: many small operations with rapid consumption of results by MIPS, flags and wide intermediate values. Without rescheduling synchronization cost outweighs short math. |
| GPU raster | `pcsx_rearmed/plugins/gpu_unai/gpulib_if.cpp` and scanline kernels | Large target by profile and ARM frequency dependency. Investigate command packet with resident data or coordinated mapping; short individual spans do not amortize exchange. C55x speed on real raster kernel is not yet measured. |

### First integration experiment: WSOLA

Current `KWsolaHop=220`, `KWsolaRange=441`, frequency 44100 Hz. The algorithm evaluates only left channel, after arithmetic `>>6`; coarse step 4 and refine near best offset. For one search it is sufficient to transmit 220 template values and 660 search area values: **1760 bytes**, return offset and score. This is 25080 or 25740 MACs; exact count is determined by area boundary. Synthesis hop is approximately **4.99 ms**. Template of next hop depends on result of previous: sending several sequential searches of one audio stream independently is impossible. Queue buffers PCM and allows ARM to perform other work while one search awaits completion.

It is important to preserve arithmetic shift of negative values, 32-bit sum saturation, pass order and selection of first maximum (`>`). Also test silence, equal scores, edges 0/440, minimum/maximum samples and rate change. Transport packet format must be explicitly serialized, without transmitting ARM `struct` to C55x, where `char`/`int` are 16-bit.

Search/offset/score/count/input checksum and short output verified in v20.
ARMv6 median 999 us, DSP end-to-end 641/732 us; create-only model pays off
after 22/33 hops. These are synthetic vectors, not recorded audio scene. Next safe
error/cancel audit, queued integration near `WsolaFeed`, alternating application
ARM/DSP runs with identical PCM, underrun/tail latency and final PCM.
Outside deadline or profitability keep ARM. Methodology and limits — WSOLA.md.

### SPU: worker form already exists, but different DSP

`spu.c` has a conditional worker with four `work_item`; `do_channel_work` is separated from completion on ARM. This is a good sample of task boundary. `spu_c64x.c` and `spu_c64x_dspcode.c` are **C64x**, different syscall/cache/types; their binary and addresses are unusable for C55x. In current Symbian shell sound is created without this worker, `iUseReverb=0`, `iUseInterpolation=0`; regular Gaussian interpolation is not automatically an existing heavy workload.

`NSSIZE=((44100/50+32)&~1)=914`; stereo PCM 16-bit — up to 3656 B per portion; intermediate `SSumLR` with 32-bit sums — 7312 B. SPU RAM — 512 KiB: full copy for each portion is unacceptable, dirty ranges or coordinated mapping are needed. Synchronization is mandatory on DMA/register accesses, IRQ, load/save state, CD mixing and reverb change.

Historical physical profile from 2026-09-23 (`plans/reports/second-opinion-omap2420-2026-09-22.md`, section B2, journals `plans/runs/2026-09-23_spucore_xa_n95/`) contains 4177 active calls and 1 769 816 samples; central interval 1263 ms — on average **0.302 ms per active call**. This is not a new A/B and not the time of individual voice kernel, but shows how small `H` must be. SPUasync=2177 ms includes other/overlapped work; intervals are not added.

Newer N95 GT profile from 2026-09-28: full `doSamples` in control 965/968 ms
for 600 frames, in profiled build 973/974 ms; 609 calls and 446816 output
frames. Stages sampled 1/16: ADPCM 642–646 ms, mix 225–230 ms,
ADSR 17–20 ms. Raw data: `plans/runs/2026-09-28_gemini/n95-spustage/`;
methodology: `spu-fusion-decision.md`. ADPCM timer covers selected path
of sample generation; current `iUseInterpolation=0`, therefore calling these 642 ms
the cost of Gaussian interpolation is incorrect. All stages are already included in
`doSamples`. Full mixer is about 3.7% of this approximately 25.8-second run:
this is the ceiling of eliminating its ARM time, before DSP/transfer costs. One request per
voice would be too fine; a block of all active voices with persistent
state is needed. For heavier scene or enabled quality interpolation priority may
be different; speedup on them is not measured.

### MDEC: format and order

Macroblock 16×16 consists of six IDCT blocks 8×8 (Cr, Cb, four Y). Array of 384 32-bit values is **1536 B**; output RGB15 is **512 B**, RGB24 is **768 B**. Current `rl2blk` already performs `idct` for each sub-block: transmitting its finished result offloads only YUV→RGB. For DSP IDCT+YUV a new boundary is needed after RLE/dequantization, before IDCT; smaller stream is RLE 16-bit plus one-time quantization table, with all `rl2blk/idct` on DSP. For variant with 384 int32 and 32-byte header in each direction this is input 1568/output 544 or 800 B, total 2112/2368 B. V18 measures symmetric echo 1568/1568, not this asymmetric exchange; kernel time is still needed. Reducing coefficients to 16-bit without verifying all ranges and rounding is not allowed.

For frame 320×240 300 macroblocks are needed: output itself 153600/230400 B. Batch multiple blocks and measure FMV scene. Preserve `mdec.block_buffer_pos`, incomplete last DMA, endian/saturation, STP flag and deferred DMA interrupt. GTE/GPU gains from other scenes are not added to MDEC.

### Areas sensitive to core frequency: what measurements really prove

Source: `docs/measurements/f1-core-vs-memory-2026-09-19.md`, completed
series A/D from 2026-09-20 and C from 2026-09-21. Same EXE, GT 7700→8300,
600 frames, window output, `nosnd` (SPU executes during this); three
alternating A/D. Bus A/D 165.12 MHz; ARM 330.24/165.12 MHz. Averages:

| Profile interval | ARM330, ms | ARM165, ms |
|---|---:|---:|
| total |25010|45550|
| emu |22047|40512|
| gpuRaster |10484|19700|

In C ARM 330.24/bus 82.56 MHz: `emu=26486`, `gpuRaster=11959` ms, one
run. This confirms strong sensitivity of raster path to ARM and separate
memory impact. The model of ~84%/88% of work scaling with ARM frequency for emu/raster is
a two-point estimate, not an independent map of physical stalls or DSP prediction.
`gpuRaster` includes command/DMA API, setup and raster; it is already included in
`emu`. Prior thesis "rasterizer is mostly bus-limited" is not supported by these measurements.
Separate review of model limits: report `plans/reports/second-opinion-omap2420-2026-09-22.md`, §3.

For current selection of specific kernel CF profiles from September 23 are more useful:
GT CF000/02b ~577/347 ms; Crash CF0c1 ~1908–1929 ms,
CF0a3 ~863–880 ms for 600 frames. These are inclusive sampled estimates of polygon
setup+spans with residual perturbation ~0.3 s in Crash. WipEout almost entirely
uses existing ARM ASM spans. See `work/state.md`, O2,
and `plans/runs/2026-09-23_cftime_sampled_*_n95/`.

For GPU proposed DSP-job boundary is a group of commands in original order,
or multiple long spans with all needed texels/CLUT/destination tiles.
Internal pixel loop has 32-bit texture gradients, clipping, 15-bit
colors, mask and blending; dot/MAC speed does not characterize this work.
A captured-command/spans benchmark against current ARM ASM/C++ is needed
with byte-exact match of VRAM, including integer rounding. Then —
resident VRAM tiles/dirty updates or verified shared mapping and barriers
on CPU/DMA reading/writing VRAM, texture read-after-write, frame present,
save/load. Current `renderer_flush_queues` is empty, so there is no ready
asynchronous contract in this renderer. Transmitting 1 MiB VRAM
per each frame via current 4096-byte buffers is impractical. C55x GPU gain
remains a hypothesis with large potential budget and complex integration.

Guest R3000A/dynarec and GTE are also sensitive to ARM speed. Dynarec
generates ARM instructions and works with RAM, registers, interrupt/SMC state;
executing it on C55x would mean a new backend/port, not a ready DSP-job.
GTE modifies CP2 registers/flags, and dynarec immediately consumes results and
accounts `gteBusyCycle`. Offloading single RTPS/RTPT/MAC call to channel
with hundreds of microseconds completion has no substantiated profitability. Checking
many dependencies and batching would require a separate redesign.

`vout_symbian.cpp:blitCurrent` has box downscale, `FxaaPixel`, BGR555→565/8888
and RGB24 conversion. Regular image kernels are possible, but finished frame
is large, DSA/WS/GL present remain on ARM, and 1:1 conversion already has
manual ARM loops. Investigate DSP here after mapping or for measured
expensive filtering; do not attribute `blitPresent` time to converter computations.

By practical order: WSOLA integration; MDEC on FMV or GPU batch
benchmark by scene target; SPU on heavy audio profile. WSOLA with typical
disabled Preserve pitch will not speed up the game. Old A/B of full WSOLA
23228→28616 ms (+23.2% on N95) contains crossfade, copying and change
of working set; kernel-delta v20 does not automatically eliminate all of these 23.2%.
After search-only one can separately check full sequential WSOLA on
DSP with resident tail/input state, if ARM copy/overlap-add dominate.

## ModernBrowser

Paths relative to `../ModernBrowser/`.

| Stage | Current implementation | Decision |
|---|---|---|
| JPEG/GIF/BMP decode | `stage0/nsrun/src/nsjpeg.c:nsjpeg_decode`, `symbian_icl.cpp:DecodeFrame/RunJob` | Already uses system Image Conversion Library. Do not write a second JPEG decoder solely for DSP. Whether a specific codec uses DSP is not visible from this API. |
| PNG | `stage0/nsrun/src/nspng.c:nspng_decode`, lodepng | Inflate and filters with variable branches and 8-bit data; C55x requires careful packing of bytes. First profile decode/filter/copy separately. First candidate is row filter or color conversion, if they dominate. |
| Scaling / YUV→RGB / audio resampling | Future proprietary media handler | Regular kernels suitable; first check standard MMF/codec path. Presence of `<audio>/<video>` and performance measurement of custom media pipeline are not established here. |
| JS, DOM, CSS/layout, HTTP/TLS automata | QuickJS, NetSurf, `http_fetcher.c`, `symbian_socket.cpp`, `symbian_tls.c` | Leave on ARM: pointers, dynamic memory, frequent links to UI/network state. Individual TLS math can be separated, see below. |
| TLS ECDHE / public-key math | BearSSL, `macTLS/os9/ostls_tls13_handshake.c:tls13_generate_keypair/tls13_ecdh_shared` | Promising experiment: entire scalar multiplication as single job, small input/output. `ec_c25519_i15.c` and `i15_montmul.c` exist; separate ARM/DSP time does not yet exist. |

PNG currently synchronously decodes full source in `data_complete`, then copies RGBA row by row, converts format and verifies opacity. Even 320×240 image gives **307200 B** RGBA. A separate ARM worker can eliminate UI latency earlier than efficient DSP mapping becomes available.

ICL already has a separate `RThread` with its own scheduler, but `RunJob` **waits** for `thread.Logon` via `User::WaitForRequest`; this is decoder isolation, not UI work overlap. For true background processing needed are job queue, completion in main scheduler, source and bitmap lifetime, cancel on page close; NetSurf calls remain in its thread. Similarly DSP completion must belong to a separate active object. Do not introduce nested scheduler in main thread: socket/ICL code already documents stray-signal errors.

### Measured browser bottlenecks and new candidates

Current `docs/state.md` ends with state of September 19; sources
reviewed October 1 (main `c99c542`). Reconnaissance does not transfer metrics
of other browsers/PCs to this application.

* CSS cascade `t-large`, N95: 4.259/4.264 s with early rejection for nodes
  without attributes, 4.430/4.421 s without it. These are paired measurements under stock
  clocking. `libcss/src/select/css_select.c` works with DOM callbacks,
  node data, arena/interning and computed styles. The most expensive measured
  loading area has poor shape for C55x: serialization of nodes and
  frequent completion do not solve it. Further ARM direction is reuse/shared
  computed styles and reduction of per-node work. Old breakdown init/share/
  create on overclocked device must be remeasured before quantitative
  conclusions; JS and layout have no new proof of DSP suitability.
* E90 scroll benchmark 60 steps: ~31.2 ms/step; paint 151.5 ms and upload 64.4 ms
  per series, present 866.7 ms (~14.4 ms/step). `draw_us` already includes present,
  adding them is not allowed. DSP image kernel will not eliminate EGL/driver present.
  N95 already has GL tile ring; old "4 ms per 32×32 upload" is not valid
  universal bandwidth: `state.md` distinguishes upload to freshly used
  and stale texture.
* HTTP gzip on N95: 38982→146904 B in 53.0 ms and 116875→422279 B in 171.8 ms.
  `http_fetcher.c:send_body` measures `macos9_gunzip_push` together with
  `deliver_body` callback. This is upper bound of isolated inflate, not its
  pure time. Decoder is a resumable Huffman/LZ77 state machine with 32 KiB byte
  history, not a MAC-heavy kernel. A resident chunk worker is possible, but
  ARM delivery/parse remain; first separate counters and
  end-to-end verification are needed. On C55x bytes must be explicitly packed via 16-bit
  `char`, including window, checksum and chunk boundaries.
* PNG decode/filter/format conversion and `symbian_gfx.cpp:sgfx_bitmap`
  copy source image and construct alpha mask; scaling is currently done by
  `CFbsBitGc::DrawBitmap/DrawBitmapMasked`. DSP packet should be formed as
  image operation or row strip and cache result for display
  size. Useful result is ready RGB565 and needed alpha, fewer
  repeated copies/repaints. Merely RGBA→RGB565 with full input/output
  via copy stream may cost more than ARM; first gate is a separate
  profile decode/unfilter/scale/copy and specific image data.

New compact mathematical target is X25519/ECDHE. Both integration points
in TLS 1.3 already call `br_ec_get_default()`. Current ARM default selects
m31 in absence of `BR_LOMUL`; comment about m15 in handshake does not mean
that m15 specifically is executing now. For C55x there is a separate i15 variant: 15-bit
limbs in `uint16_t`, 32-bit products/carries and Montgomery multiplication.
Private scalar and point for X25519 — 32 octets each; result is 32 octets.
It is worthwhile to offload **entire** scalar multiplication, leaving its internal
field multiplies on DSP. Request for each `br_i15_montymul` would be too
fine. Converting serialized octets and controlling unsigned widths
are mandatory; this is not direct compilation of ARM code with its 8-bit `char`.

This is a candidate, not a measured gain: recorded 1.00/1.27 s live TLS handshake
on N95/E90 contain network, certificate processing and socket pump. First
experiment is ARM counters keypair/shared-secret/certificate verify, then
DSP X25519 on public test vectors with exact result, correct handling
of invalid/all-zero results, constant-time code review and clearing
of secret buffers. Measure full job together with session start; the first
short connection cannot ignore startup. RSA/ECDSA verification can
be investigated separately if its budget is significant. Network state machine,
certificate verification and TLS policy remain in the browser.

## Integration sequence after hardware gate

1. Echo v18 up to 4096 B and WSOLA asymmetric 1792/48 v20, correct results/stop/cleanup confirmed. Native allocation 4096 B; 16384 B is not supported by prototype and not verified.
2. WSOLA scalar kernel passed exact ARM/Python comparison and three pairs on both. Useful ARM overlap proven by separate v17 dot+CRC. Application queue/error/cancel/audio/underrun/tail latency — next integration gate.
3. MDEC batch of macroblocks for FMV or captured GPU batch benchmark for 3D; SPU worker with dirty RAM given significant audio budget. Selection by profile of specific scene.
4. Browser: separate counters for TLS math and image stages, asynchronous job queue; DSP X25519/image kernel only upon measured profitability. GPU present/CSS budgets evaluated separately.
5. DSP failure/timeout always returns execution to ARM after safe cleanup; save/load/exit stop the worker. Absence of channel leaves integration experimental.
