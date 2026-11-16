// Plain mix only; coefficient/PCM generation and all correctness checks
// remain outside A and H+D. No short CPU counters or per-frame file I/O.
static spu_s32 spuScratch[128],spuDspSums[128];
static volatile spu_u32 spuSink;
struct TSpuTiming {
    TUint32 arm,pack,notification,ready,checked,dsp,counts,index;
    TUint16 before,after;
    };
static TSpuTiming spuTimings[120];

static TInt SpuArm(TInt frame,TInt voices,TUint32& ticks)
    {
    TInt c=(frame-1)%8,choice=voices==1?0:voices==8?1:2;
    // Prove one complete job before timing; repeated additions can wrap.
    Mem::Copy(spuScratch,spu_initial[c],512);
    spu_mix_job_arm(spuScratch,&spu_samples[c][0][0],&spu_volumes[c][0][0],voices);
    for (TInt j=0;j<128;++j) if (spuScratch[j]!=spu_expected[c][choice][j]) return KErrCorrupt;
    Mem::Copy(spuScratch,spu_initial[c],512);
    TUint32 begin=User::FastCounter();
    for (TInt repeat=0;repeat<256;++repeat) {
        spu_mix_job_arm(spuScratch,&spu_samples[c][0][0],&spu_volumes[c][0][0],voices);
        spuSink=(spu_u32)spuScratch[127];
        }
    ticks=User::FastCounter()-begin;
    for (TInt j=0;j<128;++j) {
        spu_u32 expected=(spu_u32)spu_initial[c][j]+((spu_u32)spu_expected[c][choice][j]-(spu_u32)spu_initial[c][j])*256u;
        if ((spu_u32)spuScratch[j]!=expected) return KErrCorrupt;
        }
    return KErrNone;
    }
static TUint16 SpuInputWord(TInt frame,TInt voices,TInt at)
    {
    TInt c=(frame-1)%8; spu_u32 value;
    if (at>=256+voices*132) return 0;
    if (at<256) value=(spu_u32)spu_initial[c][at/2];
    else {
        TInt v=(at-256)/132,j=(at-256)%132;
        value=(spu_u32)(j<128?spu_samples[c][v][j/2]:spu_volumes[c][v][(j-128)/2]);
        }
    return (TUint16)(value>>((at&1)*16));
    }
static TUint16 SpuOutputWord(TInt frame,TInt voices,TInt at)
    {
    if (at>=256) return 0;
    TInt choice=voices==1?0:voices==8?1:2;
    return (TUint16)((spu_u32)spu_expected[(frame-1)%8][choice][at/2]>>((at&1)*16));
    }
static TInt RingSpuFrames(RRaw& channel,TInt handle,TPtr8& nativeRing,TUint32 mapped,TInt voices,TInt frames)
    {
    RRaw util; TInt rc=util.OpenUtil(); if (rc) return rc;
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    TUint32 address=(TUint32)nativeRing.Ptr(),bytes=16384,packets=0;
    TUint16* ring=(TUint16*)nativeRing.Ptr(); Mem::FillZ(ring,bytes);
    TInt inputs=(256+voices*132+239)/240,outputs=2;
    Log(_L8("RING SPU CONFIG bytes=16384 frames=%d voices=%d samples=64 input_slots=%d output_slots=2 sample_bits=32 sum_bits=32 protocol=42 useful_ARM_W=0 performance_reservation=0"),frames,voices,inputs);
    TUint32 warm; rc=SpuArm(1,voices,warm);
    if (rc) { Log(_L8("SPU ARM warm oracle=%d"),rc); util.Close(); return rc; }
    for (TInt frame=1;frame<=frames;++frame) {
        TSpuTiming& t=spuTimings[frame-1];
        TInt slot=packets%15,bad=0; TUint32 index=65520u+packets;
        if (frame&1) {
            rc=SpuArm(frame,voices,t.arm);
            if (rc) { Log(_L8("SPU ARM frame=%d oracle=%d"),frame,rc); util.Close(); return rc; }
            }
        TUint32 packBegin=User::FastCounter();
        for (TInt k=0;k<inputs;++k) {
            TUint32 number=index+k; TUint16* p=ring+512+((slot+k)%15)*256;
            Mem::FillZ(p,512); p[0]=0xc55a; p[1]=(TUint16)(65520u+number); p[2]=256;
            p[3]=(TUint16)(number/15); p[4]=(TUint16)number; p[5]=(TUint16)(number>>16);
            for (TInt j=0;j<240;++j) p[16+j]=SpuInputWord(frame,voices,k*240+j);
            }
        for (TInt k=0;k<outputs;++k) {
            TUint16* p=ring+4352+((slot+k)%15)*256;
            for (TInt j=0;j<256;++j) p[j]=0xdead;
            }
        Mem::FillZ(ring,1024); ring[0]=0xd16a; ring[1]=42; ring[2]=(TUint16)inputs; ring[3]=(TUint16)slot;
        ring[4]=(TUint16)index; ring[5]=(TUint16)(index>>16); ring[6]=(TUint16)voices; ring[7]=64;
        Mem::FillZ(inputWords,512); Mem::FillZ(outputWords,512);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)frame; inputWords[2]=256;
        inputWords[6]=(TUint16)(mapped/2); inputWords[7]=(TUint16)(mapped/2>>16);
        inputWords[8]=0xd16e; inputWords[9]=(TUint16)slot; inputWords[10]=(TUint16)inputs; inputWords[12]=frame==frames;
        t.pack=User::FastCounter()-packBegin; inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter(); rc=util.Ctl(2,&address,&bytes);
        TInt ro=rc?rc:channel.Ctl(0x08000010,(TAny*)handle,&out),ri=ro?ro:channel.Ctl(0x0800000e,(TAny*)handle,&in);
        if (rc || ro || ri) { util.Close(); return rc?rc:ro?ro:ri; }
        TInt di=Wait(inputStatus,5000),dout=Wait(outputStatus,5000);
        if (!di && !dout) rc=util.Ctl(2,&address,&bytes);
        if (di || dout || rc) { util.Close(); return di?di:dout?dout:rc; }
        t.notification=User::FastCounter()-begin;
        for (TInt j=0;j<128;++j) {
            TInt at=j*2; const TUint16* p=ring+4352+((slot+at/240)%15)*256+16+at%240;
            spuDspSums[j]=(spu_s32)((TUint32)p[0]|((TUint32)p[1]<<16));
            }
        t.ready=User::FastCounter()-packBegin;
        for (TInt j=0;j<128;++j) if (spuDspSums[j]!=spu_expected[(frame-1)%8][voices==1?0:voices==8?1:2][j]) ++bad;
        if (outputWords[0]!=0xc55b || outputWords[1]!=frame || outputWords[4]!=42 || Get32(6) ||
            outputWords[13]!=0xdc01 || outputWords[12]!=(frame==frames) || ring[256]!=0xd16b || ring[257]!=frame || ring[258]!=inputs || ring[259]!=slot || ring[260]!=2) ++bad;
        for (TInt direction=0;direction<2;++direction) {
            TInt slots=direction?outputs:inputs;
            for (TInt k=0;k<slots;++k) {
                TUint32 number=index+k; const TUint16* p=ring+(direction?4352:512)+((slot+k)%15)*256;
                for (TInt j=0;j<256;++j) {
                    TUint16 value=0;
                    if (j==0) value=direction?0xc55b:0xc55a; if (j==1) value=(TUint16)(65520u+number); if (j==2) value=256;
                    if (j==3) value=(TUint16)(number/15); if (j==4) value=(TUint16)number; if (j==5) value=(TUint16)(number>>16);
                    if (j>=16) value=direction?SpuOutputWord(frame,voices,k*240+j-16):SpuInputWord(frame,voices,k*240+j-16);
                    if (p[j]!=value) ++bad;
                    }
                }
            }
        t.checked=User::FastCounter()-packBegin; t.dsp=Get32(8); t.counts=Get32(10); t.before=outputWords[14]; t.after=outputWords[15]; t.index=index;
        if (bad) { Log(_L8("RING SPU FAIL frame=%d errors=%d result=%u"),frame,bad,Get32(6)); util.Close(); return KErrCorrupt; }
        if (!(frame&1)) {
            rc=SpuArm(frame,voices,t.arm);
            if (rc) { Log(_L8("SPU ARM frame=%d oracle=%d"),frame,rc); util.Close(); return rc; }
            }
        packets+=inputs;
        }
    util.Close();
    for (TInt frame=1;frame<=frames;++frame) {
        const TSpuTiming& t=spuTimings[frame-1];
        Log(_L8("RING SPU RESULT frame=%d case=%d voices=%d index=%u slot=%u errors=0 checked_words=%d arm_oracle=0 sums_checked=128"),frame,(frame-1)%8,voices,t.index,(t.index-65520)%15,(inputs+outputs)*256);
        Log(_L8("RING SPU TIMING frame=%d arm_iterations=256 arm_ticks=%u arm_first=%d pack_ticks=%u notification_ticks=%u result_ticks=%u checked_ticks=%u cpu_us=-1 raw_dsp_ticks=%u counts_per_ms=%u oracle_outside=1"),frame,t.arm,frame&1,t.pack,t.notification,t.ready,t.checked,t.dsp,t.counts);
        Log(_L8("DCR READ frame=%d protocol=42 marker=dc01 io_port=0200 before=%04x after=%04x wpe_before=%d wpe_after=%d writes=0 diagnostic_only=1"),frame,t.before,t.after,(t.before&0x80)!=0,(t.after&0x80)!=0);
        }
    Log(_L8("RING SPU PASS jobs=%d voices=%d samples_per_voice=64 input_slots_per_job=%d output_slots_per_job=2 checked_words_per_job=%d protocol=42 ownership=whole_region useful_ARM_W=0"),frames,voices,inputs,(inputs+outputs)*256);
    return KErrNone;
    }
