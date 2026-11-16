# N95: acceptance of D0–D2 evidence

The current stage was handed to Claude at the user's request:
[report for PS1](CLAUDE_PS1_HANDOFF_2026-10-04.md). Further research runs
should not be started automatically; the gates that remain open below stay
unconfirmed.

For N95, the repeated channel/kernel measurements are complete, and the
decision for the measured blocking jobs has been delivered: keep current WSOLA,
MDEC and plain SPU on ARM. The overall goal has not yet been reached: the DSP
publication contract is not established, and E90 is deferred by the user. The
emulator was not implemented.

This checkpoint compares the evidence with `work/CODEX_TASK_2026-10-01.md`,
keeps the hash of the task brief, and checks the final state of the phone.
The [machine audit](evidence/2026-10-04/n95-acceptance-audit.json) refers to
the full published D0 journals, the D1/D2 cohorts and the hashes.

| Item | What is proven for N95 | Limit |
|---|---|---|
| D0 normal cycles | Host35/candidate47: 3 consecutive RUNs, 24 packets in total, each 8×512 B, 240 payload words/packet; delete/free/close/FINAL/EXIT0. Published inspect/create/3RUN journals and 2 stock probes. | Positive-cycle acceptance; a universal safe cancel is not claimed. Uncertain pending/delete ownership goes to QUARANTINE without automatic KILL. |
| D1 shared mapping and repeats | Native61: 16 KiB TOTAL, 3 series / 12 runs / 9360 exact packets, pages before/after, 6 stock brackets, clean teardown. | Payload shared; notifications use the native transport. This is not a fully copy-free channel. |
| D1 CPU | Separate CPU64: 3 series / 9360 packets, weighted threadCPU 45–48% in settled full correctness windows. | Includes packing/cache/checks/yield; this is not pure wait CPU and not gameplay. Do not merge the cohorts. |
| D1 publication | ARM machine audit: 109 words, 13 CP15 operations, 3 DSB tails. Read-only DSP DCR cohorts have WPE0. | An independent DSP→SDRAM completion before the mailbox notification is still not proven. The ARM DSB does not close this limit. |
| D2 | Actual MDEC66, plain-SPU67, current-SMLAD-WSOLA68 A/H+D/S and strict scenarios checked from journals; packet scopes and missing evidence are described in the candidates. | The verdict applies to the measured jobs. The async/resident/full-state gain is unknown; full-game/audio integration is a separate next task. |
| Restoration | On 04.10 at 09:32:35 UTC the N95 responded; 5 original files GET/SHA-equal, c55stream/ocprobe PS0, unchanged daemon launch tuple. | A snapshot at that time, not continuous monitoring or a unique phone boot ID. |

Current paired blocking results (before setup):

| Kernel and job | ARM A p50, us | DSP path ready p50, us | Blocking winners |
|---|---:|---:|---:|
| MDEC66,1/2/4 macroblocks | 78.201 / 110.626 / 295.639 | 2655.029 / 4272.461 / 7690.430 | 0/1080 |
| SPU67,1/8/24 voices×64 samples | 3.576 / 27.180 / 40.531 | 1617.432 / 3295.898 / 3540.039 | 0/1080 |
| WSOLA68, current SMLAD | 337.601 | 1098.633 | 0/360 |

Oracle checks and journaling are located outside A/H+D. The instrumented S
includes lifecycle journaling; useful async W and application CPU are not
measured. Scenario W0 corresponds to the blocking probes. The unknown W was not
turned into zero spare work for the whole game. Detailed p95/p99/max, packet
formats, cases and S/N scenarios are kept in separate reports:
[MDEC](N95_MDEC_RING_2026-10-04.md), [SPU](N95_SPU_RING_2026-10-04.md),
[WSOLA](N95_WSOLA_CURRENT_2026-10-04.md),
[decision](PS1_CANDIDATES_2026-10-01.md),
[dependency audit](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md).

`python tools/verify_n95_acceptance.py` checks the published D0 journals, a
fresh read-only final-state transport and the hashes; then it runs the native61,
CPU64, MDEC, SPU, currentWSOLA, dependency, ARM-cache and measured-DSP compiler
order verifiers. It contains no hardware commands. The local ignored archive for
D0 is no longer needed; the source/ROM checks are additionally run when the
corresponding local sources are available.

What is still needed is the OMAP2420-specific DSP endpoint contract and the exact
caller/context cache-completion contract. These are open engineering gates;
success packets do not replace an architecture proof. After E90 is deferred
until tomorrow: first GET the current journal/PS, then the return of the own
original files and compatible clock qualification, without repeating the failed
RUN without a new hypothesis. Implementing async DSP in PS1Emulator is forbidden
by this brief; the absence of a full gameplay/PCM benchmark is not permission to
start integration.
