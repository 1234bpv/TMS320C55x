"""Strict N95 current WSOLA acceptance, independent signed-sample oracle."""
import re


def reference(frame):
    seed=(0x87654321+((frame-1)//8)*0x1020304)&0xffffffff; values=[]
    for _ in range(1762):
        seed=(seed*1103515245+12345)&0xffffffff; v=seed>>16; values.append(v-65536 if v>=32768 else v)
    search=values[:1320:2]; tmpl=values[1322:1762:2]; case=(frame-1)%8
    if case:
        search=[0]*660; tmpl=[0]*220
        if case in (2,3): tmpl=[32767]*220; search=[32767 if case==2 else -32768]*660
        elif case>=4:
            tmpl[110]=32767
            if case==4: search[111]=32767
            if case==5: search[546]=16000; search[549]=32767
            if case==6: search[550]=32767
            if case==7: search[114]=search[111]=32767
    tmpl=[v>>6 for v in tmpl]; search=[v>>6 for v in search]
    def score(off): return sum(t*search[off+i] for i,t in enumerate(tmpl))
    coarse=list(range(0,441,4)); best=max(coarse,key=score); value=score(best)
    refine=[off for off in range(max(0,best-4),min(440,best+4)+1) if off%4]
    for off in refine:
        current=score(off)
        if current>value: best,value=off,current
    return best,value,len(coarse)+len(refine)


def validate_current(log,command,host_version):
    match=re.fullmatch(r"dmm-ring-wsola-current frames=(8|120)",command); assert match and host_version==53
    count=int(match[1]); lines=log.splitlines()
    assert lines[0].startswith(f"C55STREAM v53 command='{command}'") and lines[-1]=="FINAL status=0"
    assert "machine=20002d84 " in lines[0] and "fast_counter_hz=32768 " in lines[0] and "profile guard=0 " in log
    required=("BASE attach gate=0 reused_running=1 proc_load_calls=0","create=0 status=0 ","execute start=0 status=0","delete=0 status=0",
              "free task=0","RING unmap=0","RING unreserve=0","RING free native=0","free native out=0","free native in=0","BEGIN close",
              f"RING WSOLA CURRENT CONFIG bytes=16384 frames={count} input_slots=4 output_slots=1 payload_words=880 protocol=40 useful_ARM_W=0 performance_reservation=0",
              f"RING WSOLA CURRENT PASS jobs={count} input_slots_per_job=4 output_slots_per_job=1 checked_words_per_job=1280 protocol=40 ownership=whole_region useful_ARM_W=0")
    assert all(m in log for m in required) and not any(m in log for m in ("QUARANTINE","POINTER","ROUTING","PATCHREAD","DMM CMM","patcher own-ram","BEGIN base load"))
    gate=re.search(r"^NATIVE pre-RUN gate=0 env=([0-9a-f]{8}) state=1 no_patcher=1 proc_load_calls=0 env_allocator=RMS_MEM_valloc$",log,re.M); assert gate and int(gate[1],16)>0
    pages=re.findall(r"^NATIVE PAGE phase=([01]) index=([0-3]) linear=([0-9a-f]{8}) physical=([0-9a-f]{8})$",log,re.M)
    assert len(pages)==8 and [(r[0],r[1]) for r in pages]==[(str(p),str(i)) for p in (0,1) for i in range(4)]
    assert [r[1:] for r in pages[:4]]==[r[1:] for r in pages[4:]] and not int(pages[0][2],16)&4095
    assert [int(r[2],16) for r in pages[:4]]==[int(pages[0][2],16)+i*4096 for i in range(4)]
    assert all(int(r[3],16) not in (0,0xffffffff) and not int(r[3],16)&4095 for r in pages)
    order=("PROCESSOR STATE rc=0","NATIVE PAGES rc=0 phase=0","RING map=0","NATIVE pre-RUN gate=0","BEGIN execute","RING WSOLA CURRENT PASS","NATIVE PAGES rc=0 phase=1","BEGIN delete","free task=0","RING unmap=0","RING unreserve=0","RING free native=0","BEGIN close")
    assert all(m in log for m in order) and [log.index(m) for m in order]==sorted(log.index(m) for m in order)
    results=re.findall(r"^RING WSOLA CURRENT RESULT frame=(\d+) case=(\d+) index=(\d+) slot=(\d+) offset=(\d+) score=(-?\d+) scored=(\d+) errors=0 checked_words=1280 scalar_oracle=0 current_oracle=0$",log,re.M)
    timings=re.findall(r"^RING WSOLA CURRENT TIMING frame=(\d+) scalar_iterations=16 current_iterations=64 scalar_ticks=(\d+) current_ticks=(\d+) arm_first=([01]) pack_ticks=(\d+) notification_ticks=(\d+) result_ticks=(\d+) checked_ticks=(\d+) cpu_us=-1 raw_dsp_ticks=(\d+) counts_per_ms=(\d+) oracle_outside=1$",log,re.M)
    dcr=re.findall(r"^DCR READ frame=(\d+) protocol=40 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01]) writes=0 diagnostic_only=1$",log,re.M)
    for rows in (results,timings,dcr): assert len(rows)==count and [int(r[0]) for r in rows]==list(range(1,count+1))
    for i,r in enumerate(results): assert list(map(int,r[1:]))==[i%8,65520+i*4,i*4%15,*reference(i+1)]
    for t in timings:
        assert int(t[3])==int(t[0])%2 and all(int(t[k])>0 for k in (1,2,4,5,8,9)) and int(t[4])+int(t[5])<=int(t[6])<=int(t[7])
    for r in dcr: assert bool(int(r[1],16)&0x80)==bool(int(r[3])) and bool(int(r[2],16)&0x80)==bool(int(r[4]))
    return dict(jobs=count,results=results,timings=timings,dcr=dcr)
