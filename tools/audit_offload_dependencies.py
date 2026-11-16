"""Read-only current emulator dependency audit and measured same-ARM serial bounds."""
import hashlib
import json
from pathlib import Path

from summarize_ring import ROOT,stats

DEST=ROOT/"docs/evidence/2026-10-04"


def source(path,anchors):
    absolute=ROOT.parent/path; raw=absolute.read_bytes(); lines=raw.decode("utf-8").splitlines()
    excerpts=[]
    for anchor in anchors:
        needle,occurrence=anchor if isinstance(anchor,tuple) else (anchor,None)
        matches=[i for i,line in enumerate(lines) if needle in line]
        assert matches and (occurrence is not None or len(matches)==1),(path,anchor,matches)
        i=matches[occurrence or 0]; text=lines[i]
        excerpts.append(dict(line=i+1,text=text,sha256=hashlib.sha256(text.encode()).hexdigest().upper()))
    return dict(path=path,sha256=hashlib.sha256(raw).hexdigest().upper(),excerpts=excerpts)


def measurements():
    reports=[]
    for cohort,name,group in ((66,"mdec","macroblocks_per_job"),(67,"spu","voices"),(68,"wsola",None)):
        path=DEST/f"n95-{name}{cohort}-results.json"; raw=path.read_bytes().replace(b"\r\n",b"\n"); result=json.loads(raw)
        selected={}
        for run in result["runs"]:
            if run["pilot"]: continue
            key=str(run[group]) if group else "current_SMLAD"
            rows=selected.setdefault(key,[])
            for i,t in enumerate(run["timing_rows"]):
                if cohort==66:
                    a=t[2]/16; pack=t[4]; notification=run["ready_rows"][i][1]; ready=run["ready_rows"][i][2]
                elif cohort==67:
                    a=t[1]/256; pack=t[3]; notification=t[4]; ready=t[5]
                else:
                    a=t[2]/64; pack=t[4]; notification=t[5]; ready=t[6]
                assert 0<pack<=ready-notification and a>0
                scale=1000000/32768
                rows.append(dict(A_us=a*scale,T_ready_us=ready*scale,pack_us=pack*scale,
                                 serial_outside_notification_us=(ready-notification)*scale,S_us=run["setup_us"]+run["teardown_us"]))
        groups={}
        for key,rows in selected.items():
            h=[r["serial_outside_notification_us"] for r in rows]; a=[r["A_us"] for r in rows]
            groups[key]=dict(jobs=len(rows),A_us=stats(a),T_ready_us=stats([r["T_ready_us"] for r in rows]),
                             pack_us=stats([r["pack_us"] for r in rows]),serial_outside_notification_us=stats(h),
                             pack_less_than_A_jobs=sum(r["pack_us"]<r["A_us"] for r in rows),
                             serial_lower_bound_less_than_A_jobs=sum(hh<aa for hh,aa in zip(h,a)),
                             paired_W_threshold_with_zero_setup_us=stats([r["T_ready_us"]-r["A_us"] for r in rows]),
                             single_ARM_necessary_condition={str(n):sum(r["serial_outside_notification_us"]+r["S_us"]/n<r["A_us"] for r in rows) for n in (16,64,256,1000,10000,1000000)})
        reports.append(dict(cohort=cohort,kernel=name,published_result=path.relative_to(ROOT).as_posix(),
                            result_sha256=hashlib.sha256(raw).hexdigest().upper(),groups=groups))
    return reports


def main():
    sources=[source("PS1Emulator/src/symbian/snd_symbian.cpp",[
        "const TInt off = WsolaBestOffset(iWsTail, search, KWsolaHop, KWsolaRange);",
        "const TInt16 *win = search + off * 2;",
        "Mem::Copy(iWsTail, win + KWsolaHop * 2, KWsolaHop * 2 * sizeof(TInt16));",
        "Mem::Move(iWsBuf, iWsBuf + ss * 2, (iWsLen - ss) * 2 * sizeof(TInt16));",
        "static TBool g_pumpAo = ETrue;","\tSPUasync(a, b);"]),
        source("PS1Emulator/pcsx_rearmed/libpcsxcore/mdec.c",[
            "static const unsigned short *rl2blk(","\t\tidct(blk, used_col);","void psxDma1(u32 adr, u32 bcr, u32 chcr)",
            "\t\t\tyuv2rgb24(blk, image);","set_event(PSXINT_MDECOUTDMA, words * MDEC_BIAS + MDEC_DELAY);","psxRegs.cycle += words * MDEC_BIAS / 4;"]),
        source("PS1Emulator/pcsx_rearmed/plugins/dfsound/spu.c",[
            "static void do_channels(int ns_to)","static const void * const worker = NULL;",
            "if (force_no_thread || worker == NULL || !spu_config.iUseThread)",
            "MixCD(spu.SSumLR, RVB, ns_to, spu.decode_pos);","do_samples_finish(spu.SSumLR, ns_to, silentch, spu.decode_pos);",
            ("d = SSumLR[ns]; SSumLR[ns] = 0;",0),("d = SSumLR[ns]; SSumLR[ns] = 0;",1),"out_current->feed(spu.pSpuBuffer, (unsigned char *)spu.pS - spu.pSpuBuffer);"]),
        source("PS1Emulator/pcsx_rearmed/plugins/dfsound/dma.c",[
            "do_samples_if_needed(cycles, 1, 2);","do_samples_if_needed(cycles + iSize*2 * 4, 1, 2);", "spu.bMemDirty = 1;"]),
        source("PS1Emulator/src/symbian/stage1.cpp",[
            "\tpsxCpu->Execute(&psxRegs);","\t\tps1SndPump();   // service audio callbacks and refill buffer"])]
    result=dict(scope="read-only current source dependency edges plus recomputation of published N95 cohorts66/67/68; no phone commands or emulator edits",
                status="audit_complete",plan_status="in_progress",sources=sources,measurements=measurements(),
                dependencies=dict(
                    WSOLA=dict(submit_boundary="current template + search window",immediate_consumer="offset selects win; overlap-add/tail replacement depend on win; next-hop template depends on previous offset",
                               independent_W_in_unchanged_synchronous_call="0 by scheduling structure, not a measured general emulator W budget",
                               async_requirements=["Keep template/search buffers stable until completion; defer mutation/compaction.","One outstanding search per stream; refill/presentation/guest work is eligible only after proving data/state independence and audio deadlines.","Changing scheduler/reentrancy/guest frame placement is emulator integration outside this research task."]),
                    MDEC=dict(submit_boundary="probe uses post-RLE coefficients + six IDCT + RGB24; source rl2blk interleaves RLE/dequant and IDCT per block",
                              immediate_consumer="yuv2rgb24 writes guest DMA destination before psxDma1 returns and schedules MDECOUTDMA",
                              independent_W_in_unchanged_synchronous_call="0 for a blocking replacement; guest-cycle event delay is not host wall-time W",
                              async_requirements=["Split/stabilize coefficient job and RLE input/DMA output aliasing.","Prove guest RAM visibility, dynarec invalidation, pending DMA, busy/status/IRQ order before running guest CPU concurrently.","RLE of a next macroblock could be pipeline work only after proving independent buffers/state; not measured by cohort66."]),
                    SPU_plain_mix=dict(submit_boundary="post-ADSR ChanBuf + volumes + initial stereo sums",immediate_consumer="next voice reuses ChanBuf/updates shared SSumLR; MixCD/reverb/finish consume accumulated sums",
                                       independent_W_in_unchanged_synchronous_call="0 for the blocking call; optional worker source is a different compiled/state contract",
                                       async_requirements=["Double-buffer/retain per-voice sample data and sum ownership until completion.","FMOD/capture/noise/ADSR and register/DMA/SPU RAM ordering must stay equivalent; normal voices are not proof for all voices.","Full SPU resident mirror/coherency and final PCM/state equivalence not measured by plain-mix67."])),
                models=dict(ideal="max(T,W)+q < A+W iff q<A and W>T+q-A; T=H+D,q=S/N",
                            same_ARM_serial_submission_completion="H+max(D,W)+q < A+W iff H+q<A and W>H+D+q-A",
                            measured_lower_bound="Ready ticks minus notification ticks is the serial pack/setup/result interval outside exchange; notification also includes ARM cache/submission/completion work so total H is not measured separately.",
                            interpretation="Failure of lower-bound+q<A rejects ideal same-thread overlap under this measured stage envelope; passing it is only necessary. Intervals are wall time, CPU time unmeasured. New zero-copy staging/job layout/scheduler can change H and requires new measurement."),
                limits=["Source edges establish consumption/mutation order, not measured useful independent guest work or callback safety.",
                        "No current deployed emulator identity/runtime thread configuration audited; optional SPU worker is conditional and not proven active.",
                        "Elapsed packing/result stages include headers/padding/scratch initialization and any scheduling delay; not a minimum production packing or pure CPU-busy estimate.",
                        "Same-ARM lower bound assumes submission and completion are serial with W on that ARM thread; other placements/refactoring require a different model.",
                        "Measured kernels are isolated synthetic fixtures; neither source nor arithmetic is proof of full-game speedup/PCM/state correctness.",
                        "Independent endpoint publication and E90 frequency/restoration remain open; E90 deferred, no commands."])
    path=DEST/"n95-offload-dependency-audit.json"; path.write_bytes((json.dumps(result,indent=2)+"\n").encode()); print(path)
    for r in result["measurements"]:
        for name,g in r["groups"].items():
            print(r["kernel"],name,"A",round(g["A_us"]["p50"],3),"pack",round(g["pack_us"]["p50"],3),"serial",round(g["serial_outside_notification_us"]["p50"],3),"necessary_without_setup",g["serial_lower_bound_less_than_A_jobs"],"/",g["jobs"])


if __name__=="__main__": main()
