"""N95 SPU67: exact sums, stable pages and complete ownership/lifecycle."""
import re


def validate_spu(log, command, host_version):
    match=re.fullmatch(r"dmm-ring-spu voices=(1|8|24) frames=(8|120)",command)
    assert match and host_version==52
    voices,count=map(int,match.groups()); inputs=(256+voices*132+239)//240
    checked=(inputs+2)*256; lines=log.splitlines()
    assert lines[0].startswith(f"C55STREAM v52 command='{command}'") and lines[-1]=="FINAL status=0"
    assert "machine=20002d84 " in lines[0] and "fast_counter_hz=32768 " in lines[0] and "profile guard=0 " in log
    required=("BASE attach gate=0 reused_running=1 proc_load_calls=0","create=0 status=0 ","execute start=0 status=0",
              "delete=0 status=0","free task=0","RING unmap=0","RING unreserve=0","RING free native=0",
              "free native out=0","free native in=0","BEGIN close",
              f"RING SPU CONFIG bytes=16384 frames={count} voices={voices} samples=64 input_slots={inputs} output_slots=2 sample_bits=32 sum_bits=32 protocol=42 useful_ARM_W=0 performance_reservation=0",
              f"RING SPU PASS jobs={count} voices={voices} samples_per_voice=64 input_slots_per_job={inputs} output_slots_per_job=2 checked_words_per_job={checked} protocol=42 ownership=whole_region useful_ARM_W=0")
    assert all(m in log for m in required)
    assert not any(m in log for m in ("QUARANTINE","POINTER","ROUTING","PATCHREAD","DMM CMM","patcher own-ram","BEGIN base load"))
    gate=re.search(r"^NATIVE pre-RUN gate=0 env=([0-9a-f]{8}) state=1 no_patcher=1 proc_load_calls=0 env_allocator=RMS_MEM_valloc$",log,re.M)
    assert gate and int(gate[1],16)>0
    pages=re.findall(r"^NATIVE PAGE phase=([01]) index=([0-3]) linear=([0-9a-f]{8}) physical=([0-9a-f]{8})$",log,re.M)
    assert len(pages)==8 and [(r[0],r[1]) for r in pages]==[(str(p),str(i)) for p in (0,1) for i in range(4)]
    assert [r[1:] for r in pages[:4]]==[r[1:] for r in pages[4:]]
    assert [int(r[2],16) for r in pages[:4]]==[int(pages[0][2],16)+i*4096 for i in range(4)]
    assert not int(pages[0][2],16)&4095
    assert all(int(r[3],16) not in (0,0xffffffff) and not int(r[3],16)&4095 for r in pages)
    order=("PROCESSOR STATE rc=0","NATIVE PAGES rc=0 phase=0","RING map=0","NATIVE pre-RUN gate=0","BEGIN execute",
           "RING SPU PASS","NATIVE PAGES rc=0 phase=1","BEGIN delete","free task=0","RING unmap=0","RING unreserve=0","RING free native=0","BEGIN close")
    assert all(m in log for m in order) and [log.index(m) for m in order]==sorted(log.index(m) for m in order)
    results=re.findall(r"^RING SPU RESULT frame=(\d+) case=(\d+) voices=(\d+) index=(\d+) slot=(\d+) errors=0 checked_words=(\d+) arm_oracle=0 sums_checked=128$",log,re.M)
    timings=re.findall(r"^RING SPU TIMING frame=(\d+) arm_iterations=256 arm_ticks=(\d+) arm_first=([01]) pack_ticks=(\d+) notification_ticks=(\d+) result_ticks=(\d+) checked_ticks=(\d+) cpu_us=-1 raw_dsp_ticks=(\d+) counts_per_ms=(\d+) oracle_outside=1$",log,re.M)
    dcr=re.findall(r"^DCR READ frame=(\d+) protocol=42 marker=dc01 io_port=0200 before=([0-9a-f]{4}) after=([0-9a-f]{4}) wpe_before=([01]) wpe_after=([01]) writes=0 diagnostic_only=1$",log,re.M)
    for rows in (results,timings,dcr):
        assert len(rows)==count and [int(r[0]) for r in rows]==list(range(1,count+1))
    for i,r in enumerate(results):
        assert list(map(int,r[1:]))==[i%8,voices,65520+i*inputs,i*inputs%15,checked]
    for t in timings:
        assert int(t[2])==int(t[0])%2 and all(int(t[k])>0 for k in (1,3,4,7,8))
        assert int(t[3])+int(t[4])<=int(t[5])<=int(t[6])
    for r in dcr:
        assert bool(int(r[1],16)&0x80)==bool(int(r[3])) and bool(int(r[2],16)&0x80)==bool(int(r[4]))
    return dict(voices=voices,jobs=count,input_slots=inputs,output_slots=2,checked_words=checked,results=results,timings=timings,dcr=dcr)
