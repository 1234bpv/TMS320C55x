// Included after RRaw, TTransfer and Wait definitions in c55stream.cpp.
// No per-frame file I/O or short-window GetCpuTime readings.
static mdec_s32 mdecScratch[16][4][384];
static mdec_u32 mdecArmRgb[4][192];
static mdec_u32 mdecDspRgb[4][192];
static volatile mdec_u32 mdecSink;
struct TMdecTiming {
    TUint32 arm343,arm463,pack,transfer,total,dsp,counts,index;
    TUint16 dcrBefore,dcrAfter;
    TUint32 notification,resultReady;
    };
static TMdecTiming mdecTimings[120];

static TInt MdecArm(TInt frame,TInt macros,TBool newer,TUint32& ticks)
    {
    for (TInt repeat=0;repeat<16;++repeat)
        for (TInt m=0;m<macros;++m)
            Mem::Copy(mdecScratch[repeat][m],mdec_coefficients[(frame-1+m)%8],384*4);
    TUint32 begin=User::FastCounter();
    for (TInt repeat=0;repeat<16;++repeat) {
        for (TInt m=0;m<macros;++m) {
            TInt c=(frame-1+m)%8;
            if (newer) mdec_kernel_process_arm463(mdecScratch[repeat][m],mdec_used_columns[c],mdecArmRgb[m],mdec_bw[c]);
            else mdec_kernel_process(mdecScratch[repeat][m],mdec_used_columns[c],mdecArmRgb[m],mdec_bw[c]);
            mdecSink=mdecArmRgb[m][191];
            }
        }
    ticks=User::FastCounter()-begin;
    for (TInt m=0;m<macros;++m) {
        TInt c=(frame-1+m)%8;
        for (TInt j=0;j<384;++j) if (mdecScratch[15][m][j]!=mdec_idct[c][j]) return KErrCorrupt;
        for (TInt j=0;j<192;++j) if (mdecArmRgb[m][j]!=mdec_rgb24[c][j]) return KErrCorrupt;
        }
    return KErrNone;
    }

static TUint16 MdecPayloadWord(TInt frame,TInt macros,TInt at)
    {
    if (at>=775*macros) return 0;
    TInt m=at/775,j=at%775,c=(frame-1+m)%8;
    if (j<768) return (TUint16)((TUint32)mdec_coefficients[c][j/2] >> ((j&1)*16));
    if (j<774) return mdec_used_columns[c][j-768];
    return mdec_bw[c];
    }

static TUint16 MdecOutputWord(TInt frame,TInt macros,TInt at)
    {
    if (at>=384*macros) return 0;
    TInt m=at/384,j=at%384,c=(frame-1+m)%8;
    return (TUint16)(mdec_rgb24[c][j/2] >> ((j&1)*16));
    }

static TInt RingMdecFrames(RRaw& channel,TInt handle,TPtr8& nativeRing,TUint32 mapped,TInt macros,TInt frames)
    {
    RRaw util; TInt rc=util.OpenUtil(); if (rc) return rc;
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    TUint32 address=(TUint32)nativeRing.Ptr(),bytes=16384,packets=0;
    TUint16* ring=(TUint16*)nativeRing.Ptr(); Mem::FillZ(ring,bytes);
    TInt inputs=(775*macros+239)/240,outputs=(384*macros+239)/240;
    Log(_L8("RING MDEC CONFIG bytes=16384 frames=%d macroblocks=%d input_slots=%d output_slots=%d coefficient_bits=32 protocol=41 useful_ARM_W=0 performance_reservation=0"),frames,macros,inputs,outputs);
    // Warm both kernels; resets and correctness checks are outside A.
    TUint32 warm;
    rc=MdecArm(1,macros,EFalse,warm); if (!rc) rc=MdecArm(1,macros,ETrue,warm);
    if (rc) { Log(_L8("MDEC ARM warm oracle=%d"),rc); util.Close(); return rc; }
    for (TInt frame=1;frame<=frames;++frame) {
        TMdecTiming& t=mdecTimings[frame-1];
        TInt slot=packets%15,bad=0; TUint32 index=65520u+packets;
        if (frame&1) {
            rc=MdecArm(frame,macros,EFalse,t.arm343); if (!rc) rc=MdecArm(frame,macros,ETrue,t.arm463);
            if (rc) { Log(_L8("MDEC ARM frame=%d oracle=%d"),frame,rc); util.Close(); return rc; }
            }
        TUint32 packBegin=User::FastCounter();
        for (TInt k=0;k<inputs;++k) {
            TUint32 number=index+k; TUint16* input=ring+512+((slot+k)%15)*256;
            Mem::FillZ(input,512);
            input[0]=0xc55a; input[1]=(TUint16)(65520u+number); input[2]=256;
            input[3]=(TUint16)(number/15); input[4]=(TUint16)number; input[5]=(TUint16)(number>>16);
            for (TInt j=0;j<240;++j) input[16+j]=MdecPayloadWord(frame,macros,k*240+j);
            }
        for (TInt k=0;k<outputs;++k) {
            TUint16* output=ring+4352+((slot+k)%15)*256;
            for (TInt j=0;j<256;++j) output[j]=0xdead;
            }
        Mem::FillZ(ring,1024);
        ring[0]=0xd16a; ring[1]=41; ring[2]=(TUint16)inputs; ring[3]=(TUint16)slot;
        ring[4]=(TUint16)index; ring[5]=(TUint16)(index>>16); ring[6]=(TUint16)macros;
        Mem::FillZ(inputWords,512); Mem::FillZ(outputWords,512);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)frame; inputWords[2]=256;
        inputWords[6]=(TUint16)(mapped/2); inputWords[7]=(TUint16)(mapped/2>>16);
        inputWords[8]=0xd16d; inputWords[9]=(TUint16)slot; inputWords[10]=(TUint16)inputs; inputWords[12]=frame==frames;
        t.pack=User::FastCounter()-packBegin;
        inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter();
        rc=util.Ctl(2,&address,&bytes);
        TInt ro=rc?rc:channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt ri=ro?ro:channel.Ctl(0x0800000e,(TAny*)handle,&in);
        if (rc || ro || ri) { util.Close(); return rc?rc:ro?ro:ri; }
        // Whole-region ownership until both notifications and cache operation.
        TInt di=Wait(inputStatus,5000),dout=Wait(outputStatus,5000);
        if (!di && !dout) rc=util.Ctl(2,&address,&bytes);
        if (di || dout || rc) { util.Close(); return di?di:dout?dout:rc; }
        t.notification=User::FastCounter()-begin;
        for (TInt m=0;m<macros;++m) {
            for (TInt j=0;j<192;++j) {
                TInt at=m*384+j*2;
                const TUint16* p=ring+4352+((slot+at/240)%15)*256+16+at%240;
                mdecDspRgb[m][j]=(TUint32)p[0]|((TUint32)p[1]<<16);
                }
            }
        // H+D ends with RGB24 decoded into owned ARM memory. All oracle/header/
        // unchanged-input checks below are outside this comparison interval.
        t.resultReady=User::FastCounter()-packBegin;
        for (TInt m=0;m<macros;++m)
            for (TInt j=0;j<192;++j)
                if (mdecDspRgb[m][j]!=mdec_rgb24[(frame-1+m)%8][j]) ++bad;
        if (outputWords[0]!=0xc55b || outputWords[1]!=frame || outputWords[4]!=41 || Get32(6) ||
            outputWords[13]!=0xdc01 || outputWords[12]!=(frame==frames) || ring[256]!=0xd16b ||
            ring[257]!=frame || ring[258]!=inputs || ring[259]!=slot || ring[260]!=outputs) ++bad;
        for (TInt direction=0;direction<2;++direction) {
            TInt slots=direction?outputs:inputs;
            for (TInt k=0;k<slots;++k) {
                TUint32 number=index+k;
                const TUint16* p=ring+(direction?4352:512)+((slot+k)%15)*256;
                for (TInt j=0;j<256;++j) {
                    TUint16 value=0;
                    if (j==0) value=direction?0xc55b:0xc55a;
                    if (j==1) value=(TUint16)(65520u+number); if (j==2) value=256;
                    if (j==3) value=(TUint16)(number/15); if (j==4) value=(TUint16)number; if (j==5) value=(TUint16)(number>>16);
                    if (j>=16) value=direction?MdecOutputWord(frame,macros,k*240+j-16):MdecPayloadWord(frame,macros,k*240+j-16);
                    if (p[j]!=value) ++bad;
                    }
                }
            }
        t.transfer=User::FastCounter()-begin; t.total=User::FastCounter()-packBegin;
        t.dsp=Get32(8); t.counts=Get32(10); t.dcrBefore=outputWords[14]; t.dcrAfter=outputWords[15]; t.index=index;
        if (bad) { Log(_L8("RING MDEC FAIL frame=%d errors=%d result=%u"),frame,bad,Get32(6)); util.Close(); return KErrCorrupt; }
        if (!(frame&1)) {
            rc=MdecArm(frame,macros,ETrue,t.arm463); if (!rc) rc=MdecArm(frame,macros,EFalse,t.arm343);
            if (rc) { Log(_L8("MDEC ARM frame=%d oracle=%d"),frame,rc); util.Close(); return rc; }
            }
        packets+=inputs;
        }
    util.Close();
    for (TInt frame=1;frame<=frames;++frame) {
        const TMdecTiming& t=mdecTimings[frame-1];
        Log(_L8("RING MDEC RESULT frame=%d case=%d macroblocks=%d index=%u slot=%u errors=0 checked_words=%d arm343_oracle=0 arm463_oracle=0"),frame,(frame-1)%8,macros,t.index,(t.index-65520)%15,(inputs+outputs)*256);
        Log(_L8("RING MDEC TIMING frame=%d arm_iterations=16 arm343_ticks=%u arm463_ticks=%u arm_first=%d pack_ticks=%u transfer_ticks=%u end_to_end_ticks=%u cpu_us=-1 raw_dsp_ticks=%u counts_per_ms=%u"),frame,t.arm343,t.arm463,frame&1,t.pack,t.transfer,t.total,t.dsp,t.counts);
        Log(_L8("RING MDEC READY frame=%d notification_ticks=%u result_ticks=%u result_words=%d oracle_outside=1"),frame,t.notification,t.resultReady,macros*192);
        Log(_L8("DCR READ frame=%d protocol=41 marker=dc01 io_port=0200 before=%04x after=%04x wpe_before=%d wpe_after=%d writes=0 diagnostic_only=1"),frame,t.dcrBefore,t.dcrAfter,(t.dcrBefore&0x80)!=0,(t.dcrAfter&0x80)!=0);
        }
    Log(_L8("RING MDEC PASS jobs=%d macroblocks_per_job=%d input_slots_per_job=%d output_slots_per_job=%d checked_words_per_job=%d protocol=41 ownership=whole_region useful_ARM_W=0"),frames,macros,inputs,outputs,(inputs+outputs)*256);
    return KErrNone;
    }
