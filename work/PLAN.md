# ARM ↔ C55x Research Continuation Plan

Start date: 2026-09-29. Task owner: the user. Check status: `work/features.json`; current state and next action: `work/STATE.md`.

## 1. Full Task

Continue the assignment from Claude's last conversation: eliminate obstacles for work on the temporary PC; create a GitHub repository using the active user account; investigate and attempt to implement streaming processing on the C55x so that ARM and DSP can perform useful work in parallel without recreating the node for each batch; verify N95 and E90; evaluate applications in PS1Emulator and ModernBrowser, specifically audio and video.

Approximately 9 ms in the old materials is a measurement of the time of the empty node creation phase after preliminary preparation. The cost of transferring a single packet to an ever-living node has not yet been established. This distinction defines the subject of the research.

## 2. Initial State Verified Before Starting Modifications

- The project does not have `.git`; code, scripts, and hardware test journals are dated August.
- ARM host: `src/dsptest.cpp`; DSP node: `src/dsp/bench_node.c`; registration: `src/dsp/bench_dcd.s55`.
- Working path: `Hwa` / `bridgeapi.dll`, computation in the `BENCH_DSP_create` phase, completion via `TRequestStatus`.
- Some scripts contain old D: paths and the TI CGT path on C:. The tools actually reside on H: and G:.
- Left from Claude are the `harness=true` decision and two research prompts; `R3_prompt.txt` is incomplete. The plan, feature list, and environment bring-up script have not been created.
- Calls to messages 15–18, task command 18, and improper use of `ord26` caused crashes in previous tests. Repetition without new evidence of argument correctness is not a method of research.

## 3. Sequence of Work and Evidence of Completion

### F01. Plan, Harness, and Reproducible State

Create this plan, a structured requirements list, a state file, and an environment verification script. For each result, record the command, conditions, result, and path to evidence. The verification script must not itself launch a hardware experiment.

Criterion: files exist, JSON is readable, the script completes with an unambiguous result; incomplete requirements are marked explicitly.

### F02. Portable Build of ARM and DSP

Determine SDK, toolchain, daemon, and project directory relative to scripts; locate TI CGT via explicit override and verified locations. Preserve C:/E:/Z: paths on phones. Account for the space in the project name, the Perl 5.20 requirement, the SDK drive, and the legacy `ABLD.BAT`. Adapt batch scripts and reverse-engineering tools needed for this research.

Criterion: ARM host and DSP node are built from the current tree on this PC; journals contain successful completions; artifacts and dependencies are unambiguously defined. The presence of an old binary does not count as a build.

### F03. Git and GitHub

Verify the active account, initialize local history, configure exclusions for generated files, create a repository, and push a commit. Visibility according to the user's response, private in the absence of a response. Do not publish credentials or journals containing secrets.

Criterion: URL, owner, and visibility are known; local HEAD matches the remote branch; necessary source files and documentation are present.

### F04. Map of Potential ARM ↔ DSP Channels

Correlate existing ARM code, ioctls, ROM clients, and TI Bridge source code. Separately investigate streams/buffers (`STRM`, `SIO`), DMM/shared memory, notify, starting/stopping execute, DSP/BIOS task creation, and semaphores. Mark for each statement: verified on hardware, established from code/disassembly, hypothesis, or unknown. Check which steps can be performed once and whether ARM can already perform work while create is in progress.

Criterion: report with exact sources and candidate contracts; ranked list of experiments; absence of an API is not inferred solely from an incomplete export list. TI/Linux materials are used as a source of hypotheses, not proof of an identical Symbian contract.

### F05. Streaming Prototype and True Concurrency on N95

Based on the results of F04, implement the best-justified channel: a single launch of long-lived DSP code, a sequence of data portions, verification of sequence number/length and correctness of results, explicit termination. Determine buffer ownership, cache coherence, C55x addressing units, wait timeouts, and resource cleanup.

Criterion of a positive result: many portions processed without repeated create; results match the ARM reference; start, transfer, computation, and latency measured; ARM performs separate useful work concurrently with DSP; wall-clock measurement compared against sequential mode. At least three runs in identical conditions and verified status of each.

If a candidate does not work, record the specific contract and reason for failure, check the next justified path. An exploratory negative conclusion is possible only after testing available candidates; an untested channel remains open. A single failed API does not prove the impossibility of streaming processing.

### F06. Porting and Verification on E90

Determine firmware and ROM version, extract firmware-dependent addresses/profiles, verify them before use. Do not port N95 addresses to E90 without verification. Reproduce loading of a custom node, baseline measurement, and, if available, the streaming prototype.

Criterion: journals from a real E90 with device identification, clocking, correct results, and completion. If the device is unavailable, the requirement remains incomplete.

### F07. Practical Application in PS1Emulator and ModernBrowser

Review current implementations of SPU, MDEC, GTE/GPU, and background execution/media in the browser. For candidates, establish data format, chunk sizes, call frequency, dependencies, existing threads, time fraction, and synchronization cost. Compare them with the measured properties of the channel and C55x, not merely with the nominal number of MACs.

Criterion: specific files and functions, justified selection of suitable stages, rejected candidates with reasons, transfer payoff calculation, and integration plan. Introducing changes into neighboring projects requires write access outside the current working root.

### F08. Reconciled Documentation and Final Verification

Resolve contradictions regarding frequency, DVFS, audio preemption, memory, and creation time. Preserve the history of refuted hypotheses with an explicit mark. Describe the reproducible current state and limitations in README. Verify each F-requirement against its evidence and synchronize the remote repository.

Criterion: no completed requirement relies solely on intention, an old binary, or an indirect test; open questions and unavailable devices are explicitly listed. All promised hardware results have journals.

## 4. Hardware Experiment Discipline

1. Before writing, verify the specific device and transport; back up files that will be replaced, and record current clocking. Read N95 and E90 results separately.
2. Perform a static contract check before a new kernel call. Do not iterate through unknown ioctls or addresses blindly.
3. For each hypothesis, first local analysis, then a single minimal hardware test. Maximum of two identical failed tests; the next run requires new evidence or an altered contract.
4. Each process and request has a finite time limit. Timeout, pending, and non-zero status are not considered success. Reconcile true wait limits in code and documentation.
5. Measure both architectures in the same state; record frequencies and ARM/DVFS load. Do not aggregate gains from different scenes or modes.
6. After the test, terminate node/task, close the channel, restore replaced files, and verify phone availability. In case of a crash, abort the series and perform recovery before the next experiment.

## 5. Completion Condition

The task is complete when F01–F08 have evidence in accordance with the criteria above. For channel investigation, an honest negative result is acceptable if it is substantiated by checks and explicitly describes the boundaries of the conclusion. Unavailability of hardware, an unverified prototype, or an unperformed publication is not a completion of the corresponding requirement.

## Completion of research criteria —2026-10-01

F01–F08 reconciled with evidence in FINAL_AUDIT.md. Persistent stream/useful
ARM overlap/N95/E90/WSOLA ARMv6/evaluation of PS1 and Browser confirmed within
the criteria above. Source/evidence checkpoint e8f38c1 private/LOCAL=REMOTE
verified; final completion metadata committed separately. Production audio/
error lifecycle/application integration remain outside the scope of this research result.
