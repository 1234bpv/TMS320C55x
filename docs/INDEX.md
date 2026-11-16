# Documentation index

Every English document has its Ukrainian original beside it as `NAME.uk.md`.
Dated reports (`NAME_YYYY-MM-DD.md`) record one stage of the work and are not
updated afterwards; a later report may narrow or overturn an earlier one, and
the newer date wins. Raw data are in `docs/evidence/<date>/`.

The undated documents `findings`, `DSP_GUIDE`, `WRITEUP` and `CHARACTERIZATION`
grew chronologically and still contain statements that later sections or
reports correct. Known cases: the "~60 MHz" DSP clock in the header of
`DSP_GUIDE` §1 and the "clock not measured" notes in `DSP_GUIDE` §9 and
`findings` §20 (corrected in `DSP_GUIDE` §10 and §15 and in `ANSWER_DSP_CLOCK`:
CORE/3, 220.16 MHz at nominal CORE, lowered by the DVFS governor when the ARM
idles); the audio stack as the cause of the falling benchmark estimates
(`DSP_GUIDE` §15.7 attributes it to the governor); the message queue described
as unusable in `DSP_GUIDE` §7 (see the stream reports). In
`CLAUDE_PS1_HANDOFF_2026-10-04` the N95 stock bus is given as 110.08 MHz; the
measured N95 value is 165.12 MHz (`DMM_RING_2026-10-03`,
`MESSAGE_ROUTING_2026-10-03`), and 110.08 MHz is the E90 value.

## Start here

| Document | Answers |
|---|---|
| [README](../README.md) | What the project is, its main results and open limits. |
| [GETTING_STARTED](GETTING_STARTED.md) | How to build, run and verify a C55x node on these phones, and when it is worth it. |
| [DSP_GUIDE](DSP_GUIDE.md) | How to write reliable C55x code on OMAP2420 Symbian: types, overflow, memory, safety, clocks, ioctl map. |
| [BUILD](BUILD.md) | Exact build and run commands for every host and node variant, as used during the research. |
| [REFERENCES](REFERENCES.md) | TI manuals, bridge sources and included third-party code. |

## Current results (October 2026)

| Document | Answers |
|---|---|
| [N95_ACCEPTANCE_2026-10-04](N95_ACCEPTANCE_2026-10-04.md) | Which goals of D0–D2 are proven on the N95, with which evidence and limits. |
| [CLAUDE_PS1_HANDOFF_2026-10-04](CLAUDE_PS1_HANDOFF_2026-10-04.md) | What the measurements mean for the PS1 emulator; job formats and the async model. |
| [PS1_CANDIDATES_2026-10-01](PS1_CANDIDATES_2026-10-01.md) | The decision for each emulator workload, measured values separated from estimates. |
| [N95_WSOLA_CURRENT_2026-10-04](N95_WSOLA_CURRENT_2026-10-04.md) | Current ARM SMLAD WSOLA against the DSP path. |
| [N95_MDEC_RING_2026-10-04](N95_MDEC_RING_2026-10-04.md) | MDEC through the ring: exact results, no blocking gain. |
| [N95_SPU_RING_2026-10-04](N95_SPU_RING_2026-10-04.md) | The plain SPU mix through the ring. |
| [N95_SPU_BOUNDARY_2026-10-04](N95_SPU_BOUNDARY_2026-10-04.md) | Where an SPU job ends and what moving its state would cost. |
| [N95_WSOLA_RING_2026-10-04](N95_WSOLA_RING_2026-10-04.md) | The earlier WSOLA kernel through the native ring. |
| [N95_OFFLOAD_DEPENDENCIES_2026-10-04](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md) | Who consumes each result, and the serial ARM bounds for offloading. |
| [N95_RING_CPU_2026-10-04](N95_RING_CPU_2026-10-04.md) | The ARM CPU cost of a whole ring window. |
| [N95_CPU_COUNTER_2026-10-04](N95_CPU_COUNTER_2026-10-04.md) | Why short-window CPU percentages are not usable. |
| [N95_DCR_2026-10-04](N95_DCR_2026-10-04.md) | A read-only DSP DCR diagnostic. |
| [N95_ARM_CACHE_2026-10-04](N95_ARM_CACHE_2026-10-04.md) | The exact ARM cache maintenance path used for the ring. |
| [E90_DAEMON_REBOOT_2026-10-04](E90_DAEMON_REBOOT_2026-10-04.md) | The last E90 reboot and what is known about it. |

## The channel between ARM and DSP (September–October 2026)

| Document | Answers |
|---|---|
| [STREAM_RESEARCH](STREAM_RESEARCH.md) | The stream contracts of the bridge and the experiments that led to the worker. |
| [PACKET_SIZES](PACKET_SIZES.md) | Exchange time for packets of 512 to 4096 bytes on both phones. |
| [WSOLA](WSOLA.md) | The WSOLA search on a resident DSP worker. |
| [LIFECYCLE_DMM_2026-10-01](LIFECYCLE_DMM_2026-10-01.md) | The E90 node lifecycle and the DMM mapping calls. |
| [WORKER_MESSAGES_2026-10-02](WORKER_MESSAGES_2026-10-02.md) | Message delivery and completion of a finite worker. |
| [ARM_MESSAGE_RUNTIME_2026-10-02](ARM_MESSAGE_RUNTIME_2026-10-02.md) | Reading kernel memory and the origin of message pointers. |
| [KERNEL_CONTAINERS_ROOT_2026-10-02](KERNEL_CONTAINERS_ROOT_2026-10-02.md) | Where the kernel container root and the object chain come from. |
| [BASE_ATTACH_2026-10-03](BASE_ATTACH_2026-10-03.md) | Attaching to the running DSP base without reloading the audio firmware. |
| [MESSAGE_ROUTING_2026-10-03](MESSAGE_ROUTING_2026-10-03.md) | The collision of DSP message routing between nodes. |
| [DMM_ABI_2026-10-03](DMM_ABI_2026-10-03.md) | The DMM page list and ownership transfer. |
| [DMM_RING_2026-10-03](DMM_RING_2026-10-03.md) | The 16 KiB shared ring and its measurements. |
| [APPLICATION_CANDIDATES](APPLICATION_CANDIDATES.md) | Where the C55x could be used in the neighbouring projects. |

## Benchmark and reverse engineering (August 2026)

| Document | Answers |
|---|---|
| [findings](findings.md) | The chronological record of what was established about the C55x on the N95, each fact with its source; read with the note above. |
| [WRITEUP](WRITEUP.md) | The August benchmark report. |
| [CHARACTERIZATION](CHARACTERIZATION.md) | Measured C55x against ARM1136 for each kind of workload. |
| [ANSWER_DSP_CLOCK](ANSWER_DSP_CLOCK.md) | The real DSP clock and why the benchmark was lower than expected. |
| [MEASUREMENT_PLAN](MEASUREMENT_PLAN.md) | The characterization plan and its state. |
| [RESEARCH_PLAN](RESEARCH_PLAN.md) | The initial research plan for access to the C55x. |
| [SESSION_2026_09_30](SESSION_2026_09_30.md) | The log of the session that restored the builds on 2026-09-30. |

Data files: [base_syms.txt](base_syms.txt) (symbols of the N95 DSP base image),
[ehwaomap.strings.txt](ehwaomap.strings.txt) (strings of the bridge PDD). Some
reports mention `docs/bridgeapi_fns.txt`, a disassembly listing of
`bridgeapi.dll`; it is not published because it is Nokia code. It can be
regenerated from a local ROM with `tools/rev/fn.py`.

## Working notes (`work/`)

These are the research's own coordination files: plans, state for resuming,
hand-offs between agents, and requests to the user. They are kept for the
record; read the reports above for results.

| Document | Answers |
|---|---|
| [PLAN](../work/PLAN.md) | The plan for continuing the ARM ↔ C55x research. |
| [PLAN_D0_D2](../work/PLAN_D0_D2.md) | Execution of the D0–D2 assignment. |
| [PLAN_V17](../work/PLAN_V17.md) … [PLAN_V20](../work/PLAN_V20.md) | Plans of the host versions 17 to 20. |
| [CODEX_TASK_2026-10-01](../work/CODEX_TASK_2026-10-01.en.md) | The D0–D2 assignment itself; the original is `CODEX_TASK_2026-10-01.md`. |
| [STATE](../work/STATE.md) | The state log for resuming the work. |
| [HELP_NEEDED](../work/HELP_NEEDED.md) | Actions that needed the user. |
| [FINAL_AUDIT](../work/FINAL_AUDIT.md) | Audit of the full research assignment. |
| [GEMINI_REVIEW_2026-10-03](../work/GEMINI_REVIEW_2026-10-03.md), [HANDOFF_AGY_2026-10-02](../work/HANDOFF_AGY_2026-10-02.md), [HANDOFF_NATIVE_RING_2026-10-04](../work/HANDOFF_NATIVE_RING_2026-10-04.md) | Hand-offs to and from other agents. |
| `work/research/*.txt` | Prompts given to research agents. |
| [RELEASE_1.0](../work/RELEASE_1.0.md) | Plan, acceptance and state of the 1.0 release. |

## Archive

| Document | Answers |
|---|---|
| [README-2026-10-04.uk.md](archive/README-2026-10-04.uk.md) | The README as it stood on 2026-10-04, a running log of the research, in Ukrainian. Replaced by the current README. |
