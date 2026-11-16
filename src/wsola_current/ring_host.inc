// Current SMLAD and historical scalar baselines paired with exact DSP63.
// Timings are buffered; oracle checks and journal I/O remain outside A/H+D.
struct TWsolaCurrentTiming {
    TUint32 scalar,current,pack,notification,ready,checked,dsp,counts;
    TInt offset,scored; TInt32 score;
    TUint16 before,after;
    };
static TWsolaCurrentTiming wsolaCurrentTimings[120];
static TUint32 WsolaCurrentArmBatch(TInt& last)
    {
    TUint32 begin=User::FastCounter();
    for (TInt i=0;i<64;++i) {
        last=WsolaBestOffsetCurrent(wsolaTemplate,wsolaSearch,220,441);
        wsolaSink+=last;
        }
    return User::FastCounter()-begin;
    }
static TInt RingWsolaCurrentFrames(RRaw& channel,TInt handle,TPtr8& nativeRing,TUint32 mapped,TInt frames)
    {
    RRaw util; TInt rc=util.OpenUtil(); if (rc) return rc;
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    TUint32 address=(TUint32)nativeRing.Ptr(),bytes=16384,packets=0;
    TUint16* ring=(TUint16*)nativeRing.Ptr(); Mem::FillZ(ring,bytes);
    Log(_L8("RING WSOLA CURRENT CONFIG bytes=16384 frames=%d input_slots=4 output_slots=1 payload_words=880 protocol=40 useful_ARM_W=0 performance_reservation=0"),frames);
    for (TInt frame=1;frame<=frames;++frame) {
        WsolaDataset(frame,wsolaTemplate,wsolaSearch); TWsolaResult expected=WsolaReference(wsolaTemplate,wsolaSearch);
        TInt last=-1,currentLast=-1,bad=0,slot=packets%15;
        TUint32 index=65520u+packets; TWsolaCurrentTiming& t=wsolaCurrentTimings[frame-1];
        if (frame&1) { t.scalar=WsolaArmBatch(last); t.current=WsolaCurrentArmBatch(currentLast); }
        TUint32 packBegin=User::FastCounter(); TInt32 sum=0;
        for (TInt k=0;k<4;++k) {
            TUint32 number=index+k; TUint16* input=ring+512+((slot+k)%15)*256; Mem::FillZ(input,512);
            input[0]=0xc55a; input[1]=(TUint16)(65520u+number); input[2]=256; input[3]=(TUint16)(number/15);
            input[4]=(TUint16)number; input[5]=(TUint16)(number>>16);
            for (TInt j=0;j<240;++j) {
                TInt at=k*240+j; TInt16 value=at<220?(wsolaTemplate[at*2]>>6):at<880?(wsolaSearch[(at-220)*2]>>6):0;
                input[16+j]=(TUint16)value; if (at<880) sum+=(TInt32)value*(at+1);
                }
            }
        TUint16* output=ring+4352+slot*256; for (TInt j=0;j<256;++j) output[j]=0xdead;
        Mem::FillZ(ring,1024); ring[0]=0xd16a; ring[1]=40; ring[2]=4; ring[3]=(TUint16)slot;
        ring[4]=(TUint16)index; ring[5]=(TUint16)(index>>16); ring[6]=(TUint16)((frame-1)%8);
        Mem::FillZ(inputWords,512); Mem::FillZ(outputWords,512);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)frame; inputWords[2]=256;
        inputWords[6]=(TUint16)(mapped/2); inputWords[7]=(TUint16)(mapped/2>>16);
        inputWords[8]=0xd16c; inputWords[9]=(TUint16)slot; inputWords[10]=4; inputWords[12]=frame==frames;
        t.pack=User::FastCounter()-packBegin; inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter(); rc=util.Ctl(2,&address,&bytes);
        TInt ro=rc?rc:channel.Ctl(0x08000010,(TAny*)handle,&out),ri=ro?ro:channel.Ctl(0x0800000e,(TAny*)handle,&in);
        if (rc || ro || ri) { util.Close(); return rc?rc:ro?ro:ri; }
        TInt di=Wait(inputStatus,5000),dout=Wait(outputStatus,5000);
        if (!di && !dout) rc=util.Ctl(2,&address,&bytes);
        if (di || dout || rc) { util.Close(); return di?di:dout?dout:rc; }
        t.notification=User::FastCounter()-begin;
        t.offset=output[16]; t.scored=output[17]; t.score=(TInt32)((TUint32)output[18]|((TUint32)output[19]<<16));
        t.ready=User::FastCounter()-packBegin;
        if (t.offset!=expected.offset || t.score!=expected.score || t.scored!=expected.scored) ++bad;
        if (outputWords[0]!=0xc55b || outputWords[1]!=frame || outputWords[4]!=40 || Get32(6) ||
            outputWords[12]!=(frame==frames) || outputWords[13]!=0xdc01 || ring[256]!=0xd16b || ring[257]!=frame || ring[258]!=4 || ring[259]!=slot) ++bad;
        for (TInt direction=0;direction<2;++direction) {
            TInt slots=direction?1:4;
            for (TInt k=0;k<slots;++k) {
                TUint32 number=index+k; const TUint16* p=ring+(direction?4352:512)+((slot+k)%15)*256;
                for (TInt j=0;j<256;++j) {
                    TUint16 value=0;
                    if (j==0) value=direction?0xc55b:0xc55a; if (j==1) value=(TUint16)(65520u+number); if (j==2) value=256;
                    if (j==3) value=(TUint16)(number/15); if (j==4) value=(TUint16)number; if (j==5) value=(TUint16)(number>>16);
                    if (!direction && j>=16) {
                        TInt at=k*240+j-16; value=at<220?(TUint16)(wsolaTemplate[at*2]>>6):at<880?(TUint16)(wsolaSearch[(at-220)*2]>>6):0;
                        }
                    if (direction) {
                        if (j==16) value=(TUint16)expected.offset; if (j==17) value=(TUint16)expected.scored;
                        if (j==18) value=(TUint16)expected.score; if (j==19) value=(TUint16)((TUint32)expected.score>>16);
                        if (j==20) value=(TUint16)sum; if (j==21) value=(TUint16)((TUint32)sum>>16);
                        if (j==22) value=880; if (j==23) value=40;
                        }
                    if (p[j]!=value) ++bad;
                    }
                }
            }
        t.checked=User::FastCounter()-packBegin; t.dsp=Get32(8); t.counts=Get32(10); t.before=outputWords[14]; t.after=outputWords[15];
        if (!(frame&1)) { t.current=WsolaCurrentArmBatch(currentLast); t.scalar=WsolaArmBatch(last); }
        if (last!=expected.offset || currentLast!=expected.offset || !t.scalar || !t.current) ++bad;
        if (bad) { Log(_L8("RING WSOLA CURRENT FAIL frame=%d errors=%d"),frame,bad); util.Close(); return KErrCorrupt; }
        packets+=4;
        }
    util.Close();
    for (TInt frame=1;frame<=frames;++frame) {
        const TWsolaCurrentTiming& t=wsolaCurrentTimings[frame-1];
        Log(_L8("RING WSOLA CURRENT RESULT frame=%d case=%d index=%u slot=%d offset=%d score=%d scored=%d errors=0 checked_words=1280 scalar_oracle=0 current_oracle=0"),frame,(frame-1)%8,65520u+(frame-1)*4,(frame-1)*4%15,t.offset,t.score,t.scored);
        Log(_L8("RING WSOLA CURRENT TIMING frame=%d scalar_iterations=16 current_iterations=64 scalar_ticks=%u current_ticks=%u arm_first=%d pack_ticks=%u notification_ticks=%u result_ticks=%u checked_ticks=%u cpu_us=-1 raw_dsp_ticks=%u counts_per_ms=%u oracle_outside=1"),frame,t.scalar,t.current,frame&1,t.pack,t.notification,t.ready,t.checked,t.dsp,t.counts);
        Log(_L8("DCR READ frame=%d protocol=40 marker=dc01 io_port=0200 before=%04x after=%04x wpe_before=%d wpe_after=%d writes=0 diagnostic_only=1"),frame,t.before,t.after,(t.before&0x80)!=0,(t.after&0x80)!=0);
        }
    Log(_L8("RING WSOLA CURRENT PASS jobs=%d input_slots_per_job=4 output_slots_per_job=1 checked_words_per_job=1280 protocol=40 ownership=whole_region useful_ARM_W=0"),frames);
    return KErrNone;
    }
