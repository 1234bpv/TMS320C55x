# References

Primary sources used during the research. The TI manuals were consulted as
local copies; they are not redistributed in this repository, so get them from
TI.

## Texas Instruments manuals

| Number | Title | Used for |
|---|---|---|
| SPRU312 | TMS320C55x DSP Functional Overview | CPU and memory architecture, instruction cache ([findings.md](findings.md)) |
| SPRU371F | TMS320C55x DSP CPU Reference Guide | pipeline, completion of memory writes ([N95_ARM_CACHE](N95_ARM_CACHE_2026-10-04.md)) |
| SPRU376A | TMS320C55x DSP Programmer's Guide | write-pending and bypass behaviour, §4.4.3.1 |
| SPRU404 | TMS320C5000 DSP/BIOS Application Programming Interface (API) Reference Guide | `GBL`, `TSK`, `SEM`, `CLK` modules of the node |

Download links (the evidence files cite some of them under other TI mirrors):

- <https://www.ti.com/lit/ug/spru312/spru312.pdf>
- <https://www.ti.com/lit/ug/spru371f/spru371f.pdf>
- <https://www.ti.com/lit/pdf/spru376>
- <https://www.ti.com/lit/ug/spru404q/spru404q.pdf>

The compiler is TI **C5500 Code Generation Tools 4.4.1**.

## TI DSP/BIOS Bridge sources

The Symbian bridge is a port of TI's DSP/BIOS Bridge. Its Linux sources were
used to interpret structures and phase conventions; their Linux ABI does not
carry over to Symbian.

- [kpykc/userspace-dspbridge](https://github.com/kpykc/userspace-dspbridge),
  commit `342b027b642eed909e232b2bc1fa144fb0a94c8c`: `strm.h`, `rms_sh.h`,
  `rmsdefs.h`, `node.h`, the `strmcopy` sample node, and `bridge-tools.tar` with
  `dllcreate.exe` and `DLLdump.exe`.
- [Linux v2.6.37 drivers/staging/tidspbridge](https://github.com/torvalds/linux/tree/v2.6.37/drivers/staging/tidspbridge).
- [TI Bridge node.c in the Android common kernel](https://android.googlesource.com/kernel/common/+/f761237eee55222fdb509c79e784a67ab3d72cbd/drivers/staging/tidspbridge/rmgr/node.c).
- [felipec/dsp-dummy](https://github.com/felipec/dsp-dummy), a minimal node
  written for the C64x; its `BCACHE_*` calls do not exist in the N95 base image.

## Code included from other projects

- `src/mdec/`: MDEC IDCT and YUV-to-RGB from PCSX-ReARMed, copyright Ryan
  Schultz, the PCSX-df and PCSX teams, and Gabriele Gorla; GPL-2.0-or-later.
- `src/spu/`: the SPU mixer `mix_chan` from PCSX-ReARMed `dfsound/arm_utils.S`;
  GPL-2.0-or-later or LGPL-2.1-or-later, used under the GPL.
- `src/wsola_current/`: the WSOLA search of
  [PS1Emulator](https://github.com/1234bpv/PS1Emulator), a project of the same
  author, included under the licence of this repository.

Each directory keeps the original notice and a `snapshot.json` with the hash
of the source it was taken from and the list of adaptations.
