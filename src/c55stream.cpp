// Minimal host; firmware addresses must match all 39 live exports before use.
#include <e32base.h>
#include <f32file.h>
#include <hal.h>
#include <sysutil.h>
#include <e32hal.h>
#include "wsola_reference.h"
#include "mdec/fixtures.h"
#include "spu/fixtures.h"

static RFile logFile;
static TUint32 counterHz;
static void Log(TRefByValue<const TDesC8> fmt,...)
    {
    VA_LIST list; VA_START(list,fmt);
    TBuf8<512> line; line.AppendFormatList(fmt,list); VA_END(list);
    line.Append(_L8("\r\n")); logFile.Write(line); logFile.Flush();
    }
static TUint32 Us(TUint32 start)
    { return (TUint32)(((TUint64)(User::FastCounter()-start)*1000000)/counterHz); }
static TInt Wait(TRequestStatus& status,TInt ms=3000)
    {
    if (status!=KRequestPending) return status.Int();
    RTimer timer; TInt rc=timer.CreateLocal(); if (rc) return rc;
    TRequestStatus expired; timer.After(expired,ms*1000);
    User::WaitForRequest(status,expired);
    if (expired==KRequestPending) { timer.Cancel(); User::WaitForRequest(expired); }
    timer.Close();
    return status==KRequestPending ? KErrTimedOut : status.Int();
    }
class RRaw : public RBusLogicalChannel
    {
    public:
    TInt Ctl(TInt fn,TAny* a,TAny* b) { return DoControl(fn,a,b); }
    TInt OpenPatcher() {
        return DoCreate(_L("RomPatcherPlus.Driver"),TVersion(0,0,0),KNullUnit,NULL,NULL,EOwnerProcess);
        }
    TInt OpenUtil() {
        TInt rc=User::LoadLogicalDevice(_L("ebridgeutil.ldd"));
        if (rc!=KErrNone && rc!=KErrAlreadyExists) return rc;
        return DoCreate(_L("BridgeUtil"),TVersion(0,0,0),KNullUnit,NULL,NULL,EOwnerProcess);
        }
    };
static TRequestStatus performanceStatus;
class RPerformance : public RBusLogicalChannel
    {
    TBool held;
    TInt Request(TInt value) {
        // Persistent storage is never reused while a native request is pending.
        if (performanceStatus==KRequestPending) return KErrInUse;
        performanceStatus=KRequestPending;
        DoRequest(0,performanceStatus,(TAny*)0,(TAny*)value);
        return Wait(performanceStatus,5000);
        }
    public:
    RPerformance():held(EFalse) {}
    ~RPerformance() { Stop(); }
    TBool Active() const { return held; }
    TInt Percent() { return DoControl(1,(TAny*)0); }
    TInt Start(TUint32 uid) {
        if (uid==0x20002496) return KErrNone; // No CPU dvfs channel on E90.
        if (uid!=0x20002d84) return KErrNotSupported;
        const TUint32 addresses[]={0x80148410,0x80148460,0x80148638,0x80148334};
        const TInt words[]={6,56,24,28};
        const TUint32 expected[]={0x75736a35,0x8c9deac3,0x4c360a14,0x4584a74d};
        for (TInt r=0;r<4;++r) {
            const volatile TUint32* code=(const volatile TUint32*)addresses[r];
            TUint32 hash=2166136261u;
            for (TInt i=0;i<words[r];++i) hash=(hash^code[i])*16777619u;
            Log(_L8("PERF guard address=%08x words=%d fnv=%08x expected=%08x"),
                addresses[r],words[r],hash,expected[r]);
            if (hash!=expected[r]) return KErrCorrupt;
            }
        TInt rc=User::LoadLogicalDevice(_L("dvfs_interface.ldd"));
        Log(_L8("PERF load=%d"),rc);
        if (rc!=KErrNone && rc!=KErrAlreadyExists) return rc;
        rc=DoCreate(_L("dvfs_interface"),TVersion(0,0,0),KNullUnit,NULL,NULL,EOwnerProcess);
        Log(_L8("PERF open=%d"),rc); if (rc) return rc;
        performanceStatus=KErrNone;
        TInt before=Percent();
        held=ETrue; // Native count increments before the reservation wait.
        rc=Request(100);
        TInt after=performanceStatus==KRequestPending?KErrTimedOut:Percent();
        Log(_L8("PERF reserve=%d status=%d before=%d after=%d"),rc,performanceStatus.Int(),before,after);
        if (rc) return rc;
        return after==100?KErrNone:KErrCorrupt;
        }
    TInt Stop() {
        TInt rc=KErrNone;
        if (held) {
            rc=Request(0);
            TInt after=performanceStatus==KRequestPending?KErrTimedOut:Percent();
            Log(_L8("PERF release=%d status=%d after=%d"),rc,performanceStatus.Int(),after);
            held=EFalse;
            }
        // Native destructor removes any remaining client reservation.
        Close();
        return rc;
        }
    };
static TInt PatcherCheck()
    {
    // Same control105 as ocengine's level1. Only this process's RAM is written.
    TInt rc=User::LoadLogicalDevice(_L("patcher.ldd"));
    Log(_L8("patcher own-ram load=%d"),rc);
    if (rc!=KErrNone && rc!=KErrAlreadyExists) return rc;
    RRaw patcher; rc=patcher.OpenPatcher();
    Log(_L8("patcher own-ram open=%d"),rc); if (rc) return rc;
    TBuf8<4> target,bytes; target.SetLength(4); target.FillZ(); bytes.SetLength(4);
    bytes[0]=0x51; bytes[1]=0xa7; bytes[2]=0x3c; bytes[3]=0xd2;
    TUint32 address=(TUint32)target.Ptr();
    const TUint32* descriptor=(const TUint32*)&bytes;
    Log(_L8("patcher own-ram target=%08x source=%08x descriptor=%08x header=%08x max=%u length=%u"),
        address,(TUint32)bytes.Ptr(),(TUint32)&bytes,descriptor[0],descriptor[1],bytes.Length());
    rc=patcher.Ctl(105,&address,&bytes);
    volatile const TUint8* observed=target.Ptr();
    TUint8 a=observed[0],b=observed[1],c=observed[2],d=observed[3];
    Log(_L8("patcher own-ram write=%d observed=%02x/%02x/%02x/%02x expected=51/a7/3c/d2"),rc,a,b,c,d);
    patcher.Close();
    if (rc) return rc;
    if (a!=0x51 || b!=0xa7 || c!=0x3c || d!=0xd2) return KErrCorrupt;
    Log(_L8("PATCHER OWN RAM PASS no_kernel_patch=1 no_prcm=1"));
    return KErrNone;
    }
static TInt PatcherReadCheck(TUint32 uid)
    {
    // Control105 writes only our process's destination. The source is a
    // TPtrC8: first verify the descriptor path with our own RAM and ROM.
    // This mode never opens the DSP processor or changes kernel instructions.
    if (uid!=0x20002496) return KErrNotSupported;
    const volatile TUint32* header=(const volatile TUint32*)0x803dd710u;
    if (header[0]!=0x10000079u || header[5]!=0x803dd788u ||
        header[9]!=24 || header[24]!=0xc8010b20u) return KErrCorrupt;
    const TUint32 expected[]={0xe5d00040u,0xe5911000u,0xe3500000u,
        0x01a00001u,0x11a00861u,0xe12fff1eu};
    const volatile TUint32* reader=(const volatile TUint32*)0x803f7664u;
    for (TInt i=0;i<6;++i) if (reader[i]!=expected[i]) return KErrCorrupt;
    TInt rc=User::LoadLogicalDevice(_L("patcher.ldd"));
    Log(_L8("PATCHREAD load=%d"),rc);
    if (rc!=KErrNone && rc!=KErrAlreadyExists) return rc;
    RRaw patcher; rc=patcher.OpenPatcher();
    Log(_L8("PATCHREAD open=%d"),rc); if (rc) return rc;
    TUint32 target[6];
    const volatile TUint32* observed=target;
    for (TInt pass=0;pass<3;++pass) {
        Mem::FillZ(target,sizeof(target));
        const TUint8* source=pass==0?(const TUint8*)expected:
            (const TUint8*)(pass==1?0x803f7664u:0xc8010b20u);
        TPtrC8 bytes(source,sizeof(target));
        TUint32 destination=(TUint32)target;
        rc=patcher.Ctl(105,&destination,&bytes);
        Log(_L8("PATCHREAD pass=%d rc=%d source=%08x destination=%08x bytes=24 words=%08x/%08x/%08x/%08x/%08x/%08x"),
            pass,rc,(TUint32)source,destination,observed[0],observed[1],observed[2],observed[3],observed[4],observed[5]);
        if (rc) break;
        if (pass<2) for (TInt i=0;i<6;++i) if (observed[i]!=expected[i]) rc=KErrCorrupt;
        if (rc) break;
        }
    patcher.Close();
    if (!rc) Log(_L8("PATCHREAD PASS destination_own_ram=1 kernel_code_writes=0 prcm_writes=0 dsp_open=0 no_run=1"));
    return rc;
    }
static TInt ReadKernel(RRaw& patcher,TUint32 source,TAny* destination,TInt length)
    {
    // Control105 uses raw kernel memcpy to our user address, not a fault-safe
    // user-copy primitive. Touch the complete destination from user mode
    // before entering the driver; never depend on kernel stack-page faults.
    Mem::FillZ(destination,length);
    TPtrC8 bytes((const TUint8*)source,length);
    TUint32 destAddr=(TUint32)destination;
    return patcher.Ctl(105,&destAddr,&bytes);
    }
static TInt ReadKernelWord(RRaw& patcher,TUint32 source,TUint32& word)
    {
    word=0;
    return ReadKernel(patcher,source,&word,4);
    }
static TBool KernelSpan(TUint32 address,TUint32 bytes)
    { return !(address&3) && address>=0xC8000000u && address<0xC9000000u && bytes<=0xC9000000u-address; }
static TInt RoutingSnapshot(RRaw& patcher,TUint32 context,TUint32 board,TUint32 sharedBase,TUint32 expectedEnv)
    {
    // Called with a live processor/channel and no host free/close. The native
    // context owns its pool/list/queues; this bounded snapshot is not atomic.
    TUint32 ctx[61];
    if (!KernelSpan(context,sizeof(ctx))) return KErrCorrupt;
    TInt rc=ReadKernel(patcher,context,ctx,sizeof(ctx)); if (rc) return rc;
    if (ctx[6]!=board+172 || ctx[12]!=board+8 || ctx[60]!=ctx[56]+8) return KErrCorrupt;
    TUint32 pool[7];
    if (!KernelSpan(ctx[8],sizeof(pool))) return KErrCorrupt;
    rc=ReadKernel(patcher,ctx[8],pool,sizeof(pool)); if (rc) return rc;
    Log(_L8("ROUTING pool=%08x pending=%u list=%08x limit=%u non_atomic=1 foreign_node_reads=0"),ctx[8],pool[1],pool[2],pool[6]);
    // Read only the native context's first message record, with a live mapping.
    // The context creates fromDSP and records together at mapping setup.
    if (ctx[56]<sharedBase || ctx[56]-sharedBase>0x1000000u || (ctx[56]&3)) return KErrCorrupt;
    TUint32 window[6];
    rc=ReadKernel(patcher,ctx[56],window,sizeof(window)); if (rc) return rc;
    TUint32 readerSwap=0;
    rc=ReadKernelWord(patcher,board+236,readerSwap); if (rc) return rc;
    TUint32 record[4];
    for (TInt i=0;i<4;++i) {
        TUint32 raw=window[2+i];
        record[i]=(readerSwap&255)?(raw>>16)|(raw<<16):raw;
        }
    Log(_L8("ROUTING window=%08x header=%08x/%08x raw=%08x/%08x/%08x/%08x decoded=%08x/%08x/%08x/%08x"),
        ctx[56],window[0],window[1],window[2],window[3],window[4],window[5],record[0],record[1],record[2],record[3]);
    TUint32 link=0;
    if (!KernelSpan(pool[2],8)) return KErrCorrupt;
    rc=ReadKernelWord(patcher,pool[2],link); if (rc) return rc;
    TInt matchingQueues=0;
    for (TInt i=0;i<16 && link!=pool[2];++i) {
        TUint32 item[4],queue[11];
        if (!KernelSpan(link,sizeof(item))) return KErrCorrupt;
        rc=ReadKernel(patcher,link,item,sizeof(item)); if (rc) return rc;
        if (!KernelSpan(item[3],sizeof(queue))) return KErrCorrupt;
        rc=ReadKernel(patcher,item[3],queue,sizeof(queue)); if (rc) return rc;
        Log(_L8("ROUTING queue[%d]=%08x source=%08x node=%08x receive=%08x source_matches=%d"),
            i,item[3],queue[4],queue[9],queue[10],queue[4]==record[3]);
        if (expectedEnv && queue[4]==expectedEnv) ++matchingQueues;
        // Other native clients can destroy their nodes during this non-atomic
        // snapshot. Address-range validation does not retain those objects.
        // Inspect only our queue while our own task handle is retained.
        if (expectedEnv && queue[4]==expectedEnv && KernelSpan(queue[9],448)) {
            TUint32 node[112];
            rc=ReadKernel(patcher,queue[9],node,sizeof(node)); if (rc) return rc;
            if (node[3]!=0x45444f4eu || (node[0]!=0x803f8424u && node[0]!=0x801b3de8u)) return KErrCorrupt;
            Log(_L8("ROUTING node=%08x vtable=%08x internal_state=%u env=%08x phase=%u timeout=%08x expired=%u explicit_delete=%u exit_path=%u"),
                queue[9],node[0],node[10],node[11],node[26],node[27],node[44],node[43],node[110]);
            }
        link=item[0];
        }
    if (link!=pool[2]) return KErrOverflow;
    if (expectedEnv) {
        Log(_L8("ROUTING preflight env=%08x matching_queues=%d require_unique=1"),expectedEnv,matchingQueues);
        if (matchingQueues!=1) return matchingQueues?KErrAlreadyExists:KErrNotFound;
        }
    return KErrNone;
    }
static TInt NativeProvenance(RRaw& patcher,TUint32 manager,TUint32 board,TUint32 address,TUint32 bytes)
    {
    TUint32 cmm=0,region=0,pools=0;
    TInt rc=ReadKernelWord(patcher,manager+32,cmm); if (rc) return rc;
    if (!KernelSpan(cmm,28)) return KErrCorrupt;
    TUint32 cmmWords[7]; rc=ReadKernel(patcher,cmm,cmmWords,sizeof(cmmWords)); if (rc) return rc;
    if (cmmWords[0]!=0x4d4d454du) return KErrCorrupt;
    region=cmmWords[5];
    if (!KernelSpan(region,52)) return KErrCorrupt;
    TUint32 regionWords[13]; rc=ReadKernel(patcher,region,regionWords,sizeof(regionWords)); if (rc) return rc;
    TUint32 linear=regionWords[3],physical=regionWords[4],span=regionWords[2];
    Log(_L8("DMM CMM manager=%08x cmm=%08x region=%08x linear=%08x physical=%08x bytes=%u allocated_list=%08x"),
        manager,cmm,region,linear,physical,span,regionWords[12]);
    if (address<linear || bytes>span || address-linear>span-bytes) return KErrCorrupt;
    // setup passes commonBoard (= board+8) to the physical pool owner.
    rc=ReadKernelWord(patcher,board+8+244,pools); if (rc) return rc;
    if (!KernelSpan(pools,40)) return KErrCorrupt;
    TUint32 pool[10]; rc=ReadKernel(patcher,pools,pool,sizeof(pool)); if (rc) return rc;
    Log(_L8("DMM POOLS record=%08x physical1=%08x linear1=%08x bytes1=%u chunk1=%08x physical2=%08x linear2=%08x bytes2=%u chunk2=%08x"),
        pools,pool[0],pool[1],pool[2],pool[8],pool[3],pool[4],pool[5],pool[9]);
    // Verify the CMM record's physical address against actual page translations.
    RRaw util;
    rc=util.OpenUtil();
    Log(_L8("DMM util open=%d"),rc); if (rc) return rc;
    TUint32 range[2]={address,bytes},pages[10]; Mem::FillZ(pages,sizeof(pages));
    TUint32 count=((address&4095)+bytes+4095)/4096;
    if (count>5) { util.Close(); return KErrOverflow; }
    TUint32 pagePointer=(TUint32)pages;
    rc=util.Ctl(1,range,&pagePointer); Log(_L8("DMM translate=%d"),rc);
    for (TUint32 i=0;!rc && i<count;++i) {
        TUint32 expectedLinear=(address&~4095u)+i*4096;
        TUint32 expectedPhysical=physical+expectedLinear-linear;
        Log(_L8("DMM PAGE index=%u linear=%08x physical=%08x expected_physical=%08x"),i,pages[i*2],pages[i*2+1],expectedPhysical);
        if (pages[i*2]!=expectedLinear || pages[i*2+1]!=expectedPhysical) rc=KErrCorrupt;
        }
    util.Close();
    if (!rc) Log(_L8("DMM PROVENANCE PASS bytes=%u pages=%u cmm_range=1 physical_translation=1 no_map=1 no_run=1"),bytes,count);
    return rc;
    }
static TInt PatcherPointerSnapshot(TUint32 uid,TBool routing=EFalse,TUint32 expectedEnv=0,TBool requireRunning=EFalse,TUint32 nativeAddress=0,TUint32 nativeBytes=0)
    {
    if (uid!=0x20002496u && uid!=0x20002d84u) return KErrNotSupported;
    const TUint32 e90=0x20002496u;
    const TUint32 rootAddr=(uid==e90)?0xC80019D4u:0xC80019F0u;
    const TUint32 expectedVtable=(uid==e90)?0x803F8380u:0x801B3D44u;
    const TUint32 pddSlot=rootAddr+10*4;

    TInt rc=User::LoadLogicalDevice(_L("patcher.ldd"));
    Log(_L8("POINTER load=%d"),rc);
    if (rc!=KErrNone && rc!=KErrAlreadyExists) return rc;
    RRaw patcher; rc=patcher.OpenPatcher();
    Log(_L8("POINTER open=%d"),rc); if (rc) return rc;

    TUint32 pddContainer=0;
    rc=ReadKernelWord(patcher,pddSlot,pddContainer);
    Log(_L8("POINTER pdd_slot=%08x container=%08x rc=%d"),pddSlot,pddContainer,rc);
    if (rc || pddContainer<0xC8000000u || pddContainer>=0xC9000000u) {
        patcher.Close(); return rc?rc:KErrCorrupt;
        }

    TUint32 conHeader[8];
    rc=ReadKernel(patcher,pddContainer,conHeader,sizeof(conHeader));
    if (rc) { patcher.Close(); return rc; }
    TInt count=(TInt)conHeader[4];
    TUint32 objectsPtr=conHeader[5];
    Log(_L8("POINTER pdd_count=%d objects_ptr=%08x"),count,objectsPtr);
    if (count<=0 || count>32 || objectsPtr<0xC8000000u || objectsPtr>=0xC9000000u) {
        patcher.Close(); return KErrCorrupt;
        }

    TUint32 objects[32];
    rc=ReadKernel(patcher,objectsPtr,objects,count*4);
    if (rc) { patcher.Close(); return rc; }

    TUint32 factory=0;
    for (TInt i=0;i<count;++i) {
        TUint32 obj=objects[i];
        if (obj<0xC8000000u || obj>=0xC9000000u) continue;
        TUint32 vtable=0;
        if (ReadKernelWord(patcher,obj,vtable)==KErrNone) {
            Log(_L8("POINTER pdd_obj[%d]=%08x vtable=%08x"),i,obj,vtable);
            if (vtable==expectedVtable) { factory=obj; break; }
            }
        }
    Log(_L8("POINTER factory=%08x expected_vtable=%08x"),factory,expectedVtable);
    if (!factory) { patcher.Close(); return KErrNotFound; }

    TUint32 manager=0;
    rc=ReadKernelWord(patcher,factory+48,manager);
    Log(_L8("POINTER manager_ptr=%08x rc=%d"),manager,rc);
    if (rc) { patcher.Close(); return rc; }

    TUint32 commonBoard=0,board=0,context=0,ctxReader=0,sharedBase=0;
    TUint8 boardSwapByte=0,readerSwapByte=0;
    TUint32 queue16=0,queue40=0;
    TBool routed=EFalse;

    if (manager>=0xC8000000u && manager<0xC9000000u) {
        TUint32 mgrBuf[17];
        rc=ReadKernel(patcher,manager,mgrBuf,sizeof(mgrBuf));
        if (!rc) {
            TUint32 magic=mgrBuf[0];
            commonBoard=mgrBuf[11];
            TUint32 backFactory=mgrBuf[14];
            TUint32 procIndex=mgrBuf[15];
            Log(_L8("POINTER manager magic=%08x back_factory=%08x proc_index=%u common_board=%08x"),
                magic,backFactory,procIndex,commonBoard);
            if (magic==0x434F5250u && backFactory==factory && procIndex==0 &&
                commonBoard>=0xC8000008u && commonBoard<0xC9000000u) {
                Log(_L8("POINTER processor_state=%u require_running=%d"),mgrBuf[2],requireRunning);
                if (requireRunning && mgrBuf[2]!=4) { patcher.Close(); return KErrNotReady; }
                board=commonBoard-8;
                if (nativeAddress) {
                    rc=NativeProvenance(patcher,manager,board,nativeAddress,nativeBytes);
                    patcher.Close(); return rc;
                    }
                TUint32 bWord236=0;
                ReadKernelWord(patcher,board+236,bWord236);
                boardSwapByte=(TUint8)(bWord236&0xFF);
                ReadKernelWord(patcher,board+264,context);
                Log(_L8("POINTER board=%08x board_swap_byte=%02x context=%08x"),
                    board,boardSwapByte,context);
                if (context>=0xC8000000u && context<0xC9000000u) {
                    TUint32 ctxBoard=0,ctxFromDsp=0,ctxRecords=0;
                    ReadKernelWord(patcher,context+24,ctxReader);
                    ReadKernelWord(patcher,context+48,ctxBoard);
                    ReadKernelWord(patcher,context+224,ctxFromDsp);
                    ReadKernelWord(patcher,context+240,ctxRecords);
                    ReadKernelWord(patcher,context+16,queue16);
                    ReadKernelWord(patcher,context+40,queue40);
                    Log(_L8("POINTER ctx_reader=%08x ctx_board=%08x ctx_from_dsp=%08x ctx_records=%08x queue16=%08x queue40=%08x"),
                        ctxReader,ctxBoard,ctxFromDsp,ctxRecords,queue16,queue40);
                    if (ctxReader>=0xC8000000u && ctxReader<0xC9000000u) {
                        ReadKernelWord(patcher,ctxReader,sharedBase);
                        TUint32 rWord64=0;
                        ReadKernelWord(patcher,ctxReader+64,rWord64);
                        readerSwapByte=(TUint8)(rWord64&0xFF);
                        Log(_L8("POINTER shared_base=%08x reader_swap_byte=%02x"),
                            sharedBase,readerSwapByte);
                        if (routing) { rc=RoutingSnapshot(patcher,context,board,sharedBase,expectedEnv); routed=ETrue; }
                        }
                    }
                }
            }
        }

    patcher.Close();
    if (nativeAddress) return rc?rc:KErrNotFound;
    if (routing) {
        if (!routed) rc=KErrNotFound;
        Log(_L8("ROUTING snapshot=%d kernel_code_writes=0 prcm_writes=0"),rc);
        return rc;
        }
    Log(_L8("POINTER SNAPSHOT PASS root_provenance=1 factory_matched=1 manager_valid=%d board_valid=%d destination_own_ram=1 kernel_code_writes=0 prcm_writes=0 dsp_open=0 no_run=1"),
        manager!=0,board!=0);
    return KErrNone;
    }
static const TUint32 ordinals[39]={
    0x80A5E483,0x80A5E539,0x80A5E68F,0x80A5E6BB,0x80A5E561,0x80A5E585,
    0x80A5E677,0x80A5E4DF,0x80A5E43F,0x80A5E409,0x80A5E401,0x80A5E401,
    0x80A5E433,0x80A5E433,0x80A5DC71,0x80A5DC37,0x80A5DCDB,0x80A5DCA1,
    0x80A5DD0B,0x80A5DD1B,0x80A5DC2D,0x80A5DC2D,0x80A5DC35,0x80A5DC35,
    0x80A5DAE1,0x80A5D533,0x80A5D9B1,0x80A5DAC3,0x80A5D901,0x80A5D87F,
    0x80A5D9ED,0x80A5D751,0x80A5D4FD,0x80A5DAA3,0x80A5D955,0x80A5D4C9,
    0x80A5D4C9,0x80A5D4D9,0x80A5D4D9};
static TInt CheckProfile(RLibrary& lib,TUint32 uid,TUint32& delta)
    {
    const TUint32 n95=0x20002d84, e90=0x20002496;
    if (uid==n95) delta=0;
    else if (uid==e90) delta=0x803FAEF3u-0x80A5E483u;
    else return KErrNotSupported;
    for (TInt i=0;i<39;++i)
        {
        TUint32 address=(TUint32)lib.Lookup(i+1);
        Log(_L8("ordinal %d = %08x"),i+1,address);
        if (address!=ordinals[i]+delta) return KErrNotSupported;
        }
    if (lib.Lookup(40)) return KErrNotSupported;
    const TUint16 *parse=(const TUint16*)(0x80A5F0D4u+delta);
    if (parse[0]!=0xb5f3 || parse[1]!=0xb0ff || parse[2]!=0xb0ff || parse[3]!=0xb0ff)
        return KErrCorrupt;
    return KErrNone;
    }
static TRequestStatus createStatus,runStatus,deleteStatus,inputStatus,outputStatus;
static TRequestStatus messagePutStatus,messageGetStatus;
static TUint16 *inputWords,*outputWords;
struct TAllocateRecord
    {
    TUint32 header,maximum,data[5],padding;
    };
// Control 4 copies 32 raw bytes at LDD 801B4EE8, not the SDK's 28 bytes.
__ASSERT_COMPILE(sizeof(TBuf8<20>)==28);
__ASSERT_COMPILE(sizeof(TAllocateRecord)==32);
struct TMessageRecord
    {
    TUint32 header,maximum,command,argument1,argument2,padding;
    };
struct TMessageRequest
    {
    TRequestStatus *status;
    TMessageRecord *record;
    };
__ASSERT_COMPILE(sizeof(TMessageRecord)==24);
__ASSERT_COMPILE(sizeof(TMessageRequest)==8);
static TMessageRecord putMessage,getMessage;
static TMessageRequest putRequest={&messagePutStatus,&putMessage};
static TMessageRequest getRequest={&messageGetStatus,&getMessage};
static void ResetMessage(TMessageRecord& record)
    {
    Mem::FillZ(&record,sizeof(record));
    record.header=0x3000000c; record.maximum=12;
    }
static TInt NodeInfo(RRaw& channel,TInt handle,const TDesC8& phase,TUint32& env)
    {
    // Task 2 copies a 112-byte record, including its 8-byte header.
    // PDD 801A11F0 initializes nodeEnv at payload offset 64.
    static TUint32 record[28]; Mem::FillZ(record,sizeof(record));
    TInt rc=channel.Ctl(0x08000002,(TAny*)handle,record);
    Log(_L8("info phase=%S rc=%d header=%08x max=%u"),&phase,rc,record[0],record[1]);
    if (rc) return rc;
    if (record[0]!=0x30000068 || record[1]!=104) return KErrCorrupt;
    const TUint32* data=record+2;
    env=data[16];
    Log(_L8("  id_word=%08x property112=%u inputs=%u outputs=%u node_env=%08x"),
        data[0],data[13],data[14],data[15],env);
    return env ? KErrNone : KErrCorrupt;
    }
static TInt SubmitGetMessage(RRaw& channel,TInt handle)
    {
    if (messageGetStatus==KRequestPending) return KErrInUse;
    ResetMessage(getMessage); messageGetStatus=KRequestPending;
    // LDD task 21 reads {status*, record*}; PDD writes 24 raw bytes.
    TInt rc=channel.Ctl(0x08000015,(TAny*)handle,&getRequest);
    Log(_L8("message get submitted=%d status=%d"),rc,messageGetStatus.Int());
    return rc;
    }
static TInt FinishGetMessage(const TDesC8& phase,TInt ms=3000)
    {
    TInt rc=Wait(messageGetStatus,ms);
    Log(_L8("message phase=%S completion=%d status=%d"),&phase,rc,messageGetStatus.Int());
    Log(_L8("  message header=%08x max=%u cmd=%08x arg1=%08x arg2=%08x"),
        getMessage.header,getMessage.maximum,getMessage.command,
        getMessage.argument1,getMessage.argument2);
    if (rc) return rc;
    return getMessage.header==0x3000000c && getMessage.maximum==12 ? KErrNone : KErrCorrupt;
    }
static TInt Messages(RRaw& channel,TInt handle,TUint32 env)
    {
    TInt rc=SubmitGetMessage(channel,handle); if (rc) return rc;
    rc=FinishGetMessage(_L8("hello")); if (rc) return rc;
    if (getMessage.command!=0x600 || getMessage.argument1!=0x00080001 ||
        getMessage.argument2!=env) return KErrCorrupt;
    ResetMessage(putMessage);
    putMessage.command=0x601; putMessage.argument1=0x12345678;
    putMessage.argument2=0xa5c55a5a;
    messagePutStatus=KRequestPending;
    // LDD task 20 reads the same 8-byte pair, then PDD reads 24 bytes.
    rc=channel.Ctl(0x08000014,(TAny*)handle,&putRequest);
    Log(_L8("message put submitted=%d status=%d"),rc,messagePutStatus.Int());
    if (!rc) rc=Wait(messagePutStatus);
    Log(_L8("message put completion=%d status=%d"),rc,messagePutStatus.Int());
    if (rc) return rc;
    rc=SubmitGetMessage(channel,handle); if (rc) return rc;
    rc=FinishGetMessage(_L8("echo")); if (rc) return rc;
    if (getMessage.command!=0x602 || getMessage.argument1!=0x12345678 ||
        getMessage.argument2!=0xa5c55a5a) return KErrCorrupt;
    Log(_L8("MESSAGE ECHO PASS creates=1 protocol=8"));
    return KErrNone;
    }
static TInt State(RRaw& channel,TInt handle,const TDesC8& phase,TInt expected=-1)
    {
    // LDD copies 280 raw bytes, including a TBuf8 header. SDK TBuf8<268>
    // is only 276 bytes: use explicit aligned storage for the wire record.
    static TUint32 state[70];
    Mem::FillZ(state,sizeof(state));
    TInt rc=channel.Ctl(0x08000003,(TAny*)handle,state);
    Log(_L8("state phase=%S rc=%d header=%08x max=%u"),&phase,rc,state[0],state[1]);
    if (rc) return rc;
    if (state[0]!=0x3000010c || state[1]!=268) return KErrCorrupt;
    const TUint32* data=state+2;
    Log(_L8("  state=%u detail=%08x streams=%u"),data[0],data[1],data[2]);
    // PDD fills stream records only for connection kind 1. Host copy
    // connections are kind 2, so the remaining kernel stack bytes are ignored.
    return expected>=0 && data[0]!=(TUint32)expected ? KErrCorrupt : KErrNone;
    }
static TInt Native(RLibrary& lib,TAny* processor,TPtr8& buffer,TInt required=512)
    {
    Log(_L8("BEGIN native buffer"));
    TInt rc=((TInt(*)(TAny*,TDes8*,TInt,TInt,TInt,TInt))lib.Lookup(30))
        (processor,&buffer,Max(4096,required),0,0,2);
    Log(_L8("native buffer=%d address=%08x length=%d max=%d"),
        rc,(TUint32)buffer.Ptr(),buffer.Length(),buffer.MaxLength());
    if (!rc && (!buffer.Ptr() || buffer.MaxLength()<required)) return KErrCorrupt;
    return rc;
    }
static TInt ProcessorState(RRaw& channel)
    {
    // LDD control2 copies four bytes using Kern::ThreadRawWrite. PDD open
    // initializes channel state1 from manager running state4 on both ROMs.
    // This is the native channel's cached state, not a global queue snapshot.
    TUint32 state=0xffffffffu;
    TInt rc=channel.Ctl(2,&state,NULL);
    Log(_L8("PROCESSOR STATE rc=%d state=%u expected=1 native_ioctl=2 cached=1 no_patcher=1 no_proc_load=1"),rc,state);
    if (rc) return rc;
    return state==1?KErrNone:KErrNotReady;
    }
static TInt NativeRingPages(TPtr8& buffer,TUint32* previous,TBool compare)
    {
    const TUint32 address=(TUint32)buffer.Ptr(),bytes=16384;
    if (!address || (address&4095) || buffer.MaxLength()<16384) return KErrCorrupt;
    RRaw util; TInt rc=util.OpenUtil(); if (rc) return rc;
    TUint32 range[2]={address,bytes},pages[8]; Mem::FillZ(pages,sizeof(pages));
    TUint32 pagePointer=(TUint32)pages;
    rc=util.Ctl(1,range,&pagePointer); util.Close();
    for (TInt i=0;!rc && i<4;++i) {
        if (pages[i*2]!=address+i*4096 || !pages[i*2+1] ||
            pages[i*2+1]==0xffffffffu || (pages[i*2+1]&4095)) rc=KErrCorrupt;
        if (compare && (pages[i*2]!=previous[i*2] || pages[i*2+1]!=previous[i*2+1])) rc=KErrCorrupt;
        Log(_L8("NATIVE PAGE phase=%d index=%d linear=%08x physical=%08x"),compare,i,pages[i*2],pages[i*2+1]);
        }
    if (!rc && !compare) Mem::Copy(previous,pages,sizeof(pages));
    Log(_L8("NATIVE PAGES rc=%d phase=%d pages=4 bytes=16384 no_patcher=1 immutable_compare=%d"),rc,compare,compare);
    return rc;
    }
static TInt MapProbe(RLibrary& lib,TAny* processor,TPtr8& buffer)
    {
    TUint32 reserved=0,mapped=0,begin=User::FastCounter();
    TInt rc=((TInt(*)(TAny*,TUint32,TUint32*))lib.Lookup(27))(processor,16384,&reserved);
    Log(_L8("DMM reserve=%d address=%08x bytes=16384"),rc,reserved);
    if (rc) return rc;
    rc=((TInt(*)(TAny*,TUint32,TUint32,TUint32,TUint32*,TUint32))lib.Lookup(31))
        (processor,(TUint32)buffer.Ptr(),16384,reserved,&mapped,17);
    Log(_L8("DMM map=%d address=%08x reserved=%08x flags=00000011 setup_us=%u no_dsp_access=1"),rc,mapped,reserved,Us(begin));
    if (rc) {
        Log(_L8("QUARANTINE map failed; preserve native buffer and reservation"));
        for (;;) User::After(1000000);
        }
    TInt unmap=((TInt(*)(TAny*,TUint32))lib.Lookup(34))(processor,mapped);
    Log(_L8("DMM unmap=%d address=%08x"),unmap,mapped);
    if (unmap) {
        Log(_L8("QUARANTINE unmap failed; preserve native buffer and reservation"));
        for (;;) User::After(1000000);
        }
    TInt unreserve=((TInt(*)(TAny*,TUint32))lib.Lookup(28))(processor,reserved);
    Log(_L8("DMM unreserve=%d address=%08x"),unreserve,reserved);
    if (unreserve) {
        Log(_L8("QUARANTINE unreserve failed; preserve native buffer"));
        for (;;) User::After(1000000);
        }
    Log(_L8("DMM MAP PASS bytes=16384 flags=17 reserve_map_unmap_unreserve=0 no_dsp_access=1 no_run=1"));
    return KErrNone;
    }
static TInt RingMap(RLibrary& lib,TAny* processor,TPtr8& buffer,TUint32& reserved,TUint32& mapped)
    {
    TUint32 begin=User::FastCounter();
    TInt rc=((TInt(*)(TAny*,TUint32,TUint32*))lib.Lookup(27))(processor,16384,&reserved);
    Log(_L8("RING reserve=%d address=%08x bytes=16384"),rc,reserved); if (rc) return rc;
    rc=((TInt(*)(TAny*,TUint32,TUint32,TUint32,TUint32*,TUint32))lib.Lookup(31))
        (processor,(TUint32)buffer.Ptr(),16384,reserved,&mapped,17);
    Log(_L8("RING map=%d address=%08x flags=17 setup_us=%u"),rc,mapped,Us(begin));
    if (rc || !mapped || (mapped&4095) || mapped>=0x01000000u) {
        Log(_L8("QUARANTINE ring map/address gate; preserve mapping/buffer"));
        for (;;) User::After(1000000);
        }
    return KErrNone;
    }
static void RingUnmap(RLibrary& lib,TAny* processor,TUint32 reserved,TUint32 mapped)
    {
    TInt rc=((TInt(*)(TAny*,TUint32))lib.Lookup(34))(processor,mapped);
    Log(_L8("RING unmap=%d"),rc);
    if (!rc) {
        rc=((TInt(*)(TAny*,TUint32))lib.Lookup(28))(processor,reserved);
        Log(_L8("RING unreserve=%d"),rc);
        }
    if (rc) {
        Log(_L8("QUARANTINE ring unmap/unreserve; preserve native buffer"));
        for (;;) User::After(1000000);
        }
    }
struct TTransfer
    {
    TPtr8 buffer;
    TRequestStatus *status;
    TInt length,argument,index;
    TTransfer(TUint16* data,TRequestStatus& st,TInt bytes=512)
        :buffer((TUint8*)data,bytes,bytes),status(&st),length(bytes),argument(0),index(0) {}
    };
__ASSERT_COMPILE(sizeof(TTransfer)==28);
static TUint32 Get32(TInt at)
    { return outputWords[at] | ((TUint32)outputWords[at+1]<<16); }
static TUint8 crcData[65536];
static TUint32 Crc()
    {
    TUint32 crc=0xffffffffu;
    for (TInt i=0;i<65536;++i)
        {
        crc^=crcData[i];
        for (TInt j=0;j<8;++j) crc=(crc>>1)^((0u-(crc&1))&0xedb88320u);
        }
    return ~crc;
    }
static TInt Frames(RRaw& channel,TInt handle,TInt reps,TBool parallel,
    TInt frames=8,TBool worker=EFalse,RPerformance* perf=NULL,
    TInt packetBytes=512,TBool doCrc=ETrue,TInt protocol=0)
    {
    TUint32 crcBegin=0,expectedCrc=0,total=0;
    if (doCrc) {
        for (TInt i=0;i<65536;++i) crcData[i]=(TUint8)(i*13+7);
        crcBegin=User::FastCounter(); expectedCrc=Crc();
        Log(_L8("ARM CRC baseline bytes=65536 crc=%08x wall_us=%u"),expectedCrc,Us(crcBegin));
        }
    else Log(_L8("ARM CRC skipped transport measurement no_crc=1"));
    const TInt words=packetBytes/2;
    static TTransfer in(inputWords,inputStatus,packetBytes),out(outputWords,outputStatus,packetBytes);
    for (TInt sequence=1;sequence<=frames;++sequence)
        {
        TInt perfBefore=perf && perf->Active()?perf->Percent():0;
        Mem::FillZ(inputWords,packetBytes); Mem::FillZ(outputWords,packetBytes);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)sequence;
        inputWords[2]=(TUint16)words; inputWords[3]=(TUint16)reps; inputWords[12]=sequence==frames;
        TInt32 expectedDot=0;
        for (TInt i=16;i<words;++i)
            {
            TInt16 value=(TInt16)(((i*17+sequence*11)&255)-128);
            inputWords[i]=(TUint16)value;
            if (i<256) expectedDot+=(TInt32)value*((((i-16)&15))-7);
            }
        if (!reps) expectedDot=0;
        inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter();
        TInt rcOut=channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt rcIn=channel.Ctl(0x0800000e,(TAny*)handle,&in);
        TUint32 issueUs=Us(begin),crc=0,crcUs=0;
        if (parallel && doCrc) {
            crcBegin=User::FastCounter(); crc=Crc(); crcUs=Us(crcBegin);
            }
        TUint32 waitBegin=User::FastCounter();
        TInt doneIn=rcIn?rcIn:Wait(inputStatus);
        TInt doneOut=rcOut?rcOut:Wait(outputStatus);
        TUint32 waitUs=Us(waitBegin),completionUs=Us(begin);
        if (!parallel && doCrc) {
            crcBegin=User::FastCounter(); crc=Crc(); crcUs=Us(crcBegin);
            }
        TUint32 elapsed=Us(begin); total+=elapsed;
        TInt perfAfter=perf && perf->Active()?perf->Percent():0;
        Log(_L8("frame=%d put=%d/%d get=%d/%d wall_us=%u crc=%08x"),
            sequence,rcIn,doneIn,rcOut,doneOut,elapsed,crc);
        Log(_L8("  issue_us=%u arm_crc_us=%u wait_us=%u completion_observed_us=%u"),
            issueUs,crcUs,waitUs,completionUs);
        if (doneIn || doneOut) {
            State(channel,handle,_L8("frame error"));
            return doneIn?doneIn:doneOut;
            }
        TInt bad=0;
        if (outputWords[0]!=0xc55b || outputWords[1]!=sequence ||
            outputWords[2]!=words || outputWords[3]!=reps || outputWords[5]!=sequence ||
            outputWords[4]!=(protocol?protocol:(worker?20:7)) || outputWords[12]!=(sequence==frames) ||
            (TInt32)Get32(6)!=expectedDot || crc!=expectedCrc) ++bad;
        if (worker && outputWords[13]!=15) ++bad;
        if (perf && perf->Active()) {
            Log(_L8("PERF frame=%d before=%d after=%d"),sequence,perfBefore,perfAfter);
            if (perfBefore!=100 || perfAfter!=100) ++bad;
            }
        for (TInt i=16;i<words;++i)
            if (outputWords[i]!=(TUint16)(inputWords[i]*3u+sequence)) ++bad;
        Log(_L8("SIZE frame=%d input_bytes=%d output_bytes=%d returned_words=%u protocol=%u checked_payload_words=%d"),
            sequence,packetBytes,packetBytes,outputWords[2],outputWords[4],words-16);
        Log(_L8("  result=%d expected=%d ticks=%u counts_per_ms=%u errors=%d stop=%d"),
            (TInt32)Get32(6),expectedDot,Get32(8),Get32(10),bad,outputWords[12]);
        if (worker) Log(_L8("  dsp_stamp=%u"),Get32(14));
        if (bad) return KErrCorrupt;
        }
    if (worker) {
        TInt stateRc=State(channel,handle,_L8("worker frames complete"),1);
        if (stateRc) return stateRc;
        Log(_L8("WORKER STREAM PASS frames=%d creates=1 runs=0 useful_arm_crc=%d mode=%d reps=%d total_us=%u packet_bytes=%d no_crc=%d"),
            frames,doCrc?frames:0,parallel,reps,total,packetBytes,!doCrc);
        }
    else Log(_L8("STREAM PASS frames=%d creates=1 useful_arm_crc=%d mode=%d total_us=%u"),frames,doCrc?frames:0,parallel,total);
    return KErrNone;
    }
static TInt ReferenceCopyFrames(RRaw& channel,TInt handle)
    {
    // Control experiment: the E90 ROM node owns create/execute/delete.
    // All 256 words, including the sequence, must echo exactly.
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    for (TInt sequence=1;sequence<=8;++sequence) {
        for (TInt i=0;i<256;++i) inputWords[i]=(TUint16)(i*137+sequence*31);
        inputWords[0]=0xc55e; inputWords[1]=(TUint16)sequence;
        Mem::FillZ(outputWords,512); inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter();
        TInt ri=KErrNone,ro=channel.Ctl(0x08000010,(TAny*)handle,&out);
        ri=channel.Ctl(0x0800000e,(TAny*)handle,&in);
        TInt di=ri?ri:Wait(inputStatus),dout=ro?ro:Wait(outputStatus);
        TInt bad=0;
        if (!di && !dout) for (TInt j=0;j<256;++j) if (inputWords[j]!=outputWords[j]) ++bad;
        Log(_L8("reference frame=%d put=%d/%d get=%d/%d bytes=512 bad_words=%d wall_us=%u"),
            sequence,ri,di,ro,dout,bad,Us(begin));
        if (di || dout) return di?di:dout;
        if (bad) return KErrCorrupt;
        }
    Log(_L8("REFERENCE COPY PASS frames=8 checked_words_per_frame=256 no_own_execute=1"));
    return KErrNone;
    }
struct TRingWindowFrame { TUint32 wall,dspTicks,packetStart; TInt slot,bad; };
static TRingWindowFrame ringWindowFrames[120];
static TInt RingFrames(RRaw& channel,TInt handle,TPtr8& nativeRing,TUint32 mapped,TInt batch,TInt frames,TBool dcrRead,TBool cpuWindow)
    {
    RRaw util; TInt rc=util.OpenUtil(); if (rc) return rc;
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    TUint32 address=(TUint32)nativeRing.Ptr(),bytes=16384,packets=0,total=0;
    TUint16* ring=(TUint16*)nativeRing.Ptr();
    Mem::FillZ(ring,bytes);
    Log(_L8("RING CONFIG bytes=16384 control_bytes=1024 slots_per_direction=15 slot_bytes=512 payload_bytes=480 batch=%d frames=%d dsp_byte_address=%08x dsp_word_address=%08x whole_region_ownership=1"),batch,frames,mapped,mapped/2);
    TTimeIntervalMicroSeconds windowCpuBefore,windowCpuAfter;
    TUint32 windowBegin=0,loopTicks=0,finalYieldTicks=0;
    if (cpuWindow) {
        if (frames>120 || dcrRead) { util.Close(); return KErrArgument; }
        User::After(1); // Settle the prior CPU slice outside the window.
        windowBegin=User::FastCounter();
        rc=RThread().GetCpuTime(windowCpuBefore);
        if (rc) { util.Close(); return rc; }
        }
    for (TInt frame=1;frame<=frames;++frame) {
        TInt slot=packets%15,bad=0;
        for (TInt k=0;k<batch;++k) {
            TUint32 index=65520u+packets+k;
            TUint16 seq=(TUint16)(65520u+index),generation=(TUint16)(index/15);
            TUint16* input=ring+512+((slot+k)%15)*256;
            TUint16* output=ring+4352+((slot+k)%15)*256;
            for (TInt j=0;j<256;++j) {
                input[j]=j<16?0:(TUint16)(j*137+seq*31);
                output[j]=0xdead;
                }
            input[0]=0xc55a; input[1]=seq; input[2]=256; input[3]=generation;
            input[4]=(TUint16)index; input[5]=(TUint16)(index>>16);
            }
        ring[0]=0xd16a; ring[1]=38; ring[2]=(TUint16)batch; ring[3]=(TUint16)slot;
        ring[4]=(TUint16)(65520u+packets); ring[5]=(TUint16)((65520u+packets)>>16);
        Mem::FillZ(inputWords,512); Mem::FillZ(outputWords,512);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)frame; inputWords[2]=256;
        inputWords[6]=(TUint16)(mapped/2); inputWords[7]=(TUint16)(mapped/2>>16);
        inputWords[8]=0xd16b; inputWords[9]=(TUint16)slot; inputWords[10]=(TUint16)batch;
        inputWords[12]=frame==frames;
        inputStatus=outputStatus=KRequestPending;
        TTimeIntervalMicroSeconds cpuBefore,cpuAfter;
        TInt cpuRc=cpuWindow?KErrNotSupported:RThread().GetCpuTime(cpuBefore);
        TUint32 begin=User::FastCounter();
        rc=util.Ctl(2,&address,&bytes); // clean then invalidate before ownership transfer
        TInt ro=rc?rc:channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt ri=ro?ro:channel.Ctl(0x0800000e,(TAny*)handle,&in);
        if (rc || ro || ri) {
            // No subsequent iteration reuses pending descriptors.
            util.Close(); return rc?rc:ro?ro:ri;
            }
        // DSP owns all ring lines here. ARM touches only its notification buffers.
        TInt di=Wait(inputStatus,5000),dout=Wait(outputStatus,5000);
        if (!di && !dout) rc=util.Ctl(2,&address,&bytes);
        TUint32 wall=Us(begin); total+=wall;
        TInt cpuEndRc=cpuWindow?KErrNotSupported:RThread().GetCpuTime(cpuAfter);
        TInt cpuUs=(!cpuRc && !cpuEndRc)?(TInt)(cpuAfter.Int64()-cpuBefore.Int64()):-1;
        if (di || dout || rc) { util.Close(); return di?di:dout?dout:rc; }
        if (!cpuWindow && (frame==1 || outputWords[6])) Log(_L8("RING OBSERVED dsp_control=%04x/%04x/%04x/%04x/%04x/%04x/%04x/%04x dsp_address=%04x/%04x result=%u arm_control=%04x/%04x/%04x/%04x"),
            outputWords[16],outputWords[17],outputWords[18],outputWords[19],outputWords[20],outputWords[21],outputWords[22],outputWords[23],outputWords[24],outputWords[25],outputWords[6],ring[0],ring[1],ring[2],ring[3]);
        if (outputWords[0]!=0xc55b || outputWords[1]!=frame || outputWords[4]!=(dcrRead?39:38) || outputWords[6]) ++bad;
        if (dcrRead) {
            if (outputWords[13]!=0xdc01) ++bad;
            Log(_L8("DCR READ frame=%d protocol=%u marker=%04x io_port=0200 before=%04x after=%04x wpe_before=%d wpe_after=%d writes=0 diagnostic_only=1"),
                frame,outputWords[4],outputWords[13],outputWords[14],outputWords[15],
                (outputWords[14]&0x80)!=0,(outputWords[15]&0x80)!=0);
            }
        if (ring[256]!=0xd16b || ring[257]!=frame || ring[258]!=batch || ring[259]!=slot) ++bad;
        for (TInt k=0;k<batch;++k) {
            TUint32 index=65520u+packets+k;
            TUint16 seq=(TUint16)(65520u+index),generation=(TUint16)(index/15);
            const TUint16* input=ring+512+((slot+k)%15)*256;
            const TUint16* output=ring+4352+((slot+k)%15)*256;
            for (TInt j=0;j<256;++j) {
                TUint16 expectedInput=j<16?0:(TUint16)(j*137+seq*31);
                TUint16 expectedOutput=j<16?0:(TUint16)(expectedInput*3u+seq);
                if (j==0) { expectedInput=0xc55a; expectedOutput=0xc55b; }
                if (j==1) expectedInput=expectedOutput=seq;
                if (j==2) expectedInput=expectedOutput=256;
                if (j==3) expectedInput=expectedOutput=generation;
                if (j==4) expectedInput=expectedOutput=(TUint16)index;
                if (j==5) expectedInput=expectedOutput=(TUint16)(index>>16);
                if (input[j]!=expectedInput || output[j]!=expectedOutput) ++bad;
                }
            }
        if (cpuWindow) {
            TRingWindowFrame& saved=ringWindowFrames[frame-1];
            saved.wall=wall; saved.dspTicks=Get32(8); saved.packetStart=packets; saved.slot=slot; saved.bad=bad;
            }
        else Log(_L8("RING FRAME frame=%d slot=%d batch=%d packet_start=%u wall_us=%u cpu_us=%d bad_words=%d dsp_ticks=%u"),
            frame,slot,batch,packets,wall,cpuUs,bad,Get32(8));
        if (bad) { util.Close(); return KErrCorrupt; }
        packets+=batch;
        }
    if (cpuWindow) {
        loopTicks=User::FastCounter()-windowBegin;
        TUint32 yieldBegin=User::FastCounter();
        User::After(1); // Included in outer wall; settle the last CPU slice.
        rc=RThread().GetCpuTime(windowCpuAfter);
        finalYieldTicks=User::FastCounter()-yieldBegin;
        TUint32 outerTicks=User::FastCounter()-windowBegin;
        TInt cpuUs=(TInt)(windowCpuAfter.Int64()-windowCpuBefore.Int64());
        Log(_L8("RING CPU WINDOW frames=%d batch=%d outer_ticks=%u loop_ticks=%u final_yield_ticks=%u cpu_us=%d before_rc=0 after_rc=%d pack_checks_included=1 journaling_inside=0 arm_baseline_inside=0 boundary_yield=1 useful_ARM_W=0"),
            frames,batch,outerTicks,loopTicks,finalYieldTicks,cpuUs,rc);
        if (rc || cpuUs<0 || (TUint64)cpuUs*counterHz>(TUint64)(outerTicks+2)*1000000) {
            util.Close(); return rc?rc:KErrCorrupt;
            }
        for (TInt frame=1;frame<=frames;++frame) {
            const TRingWindowFrame& saved=ringWindowFrames[frame-1];
            Log(_L8("RING FRAME frame=%d slot=%d batch=%d packet_start=%u wall_us=%u cpu_us=-1 bad_words=%d dsp_ticks=%u"),
                frame,saved.slot,batch,saved.packetStart,saved.wall,saved.bad,saved.dspTicks);
            }
        }
    util.Close();
    Log(_L8("RING DATA PASS bytes=16384 packets=%u frames=%d batch=%d total_exchange_us=%u checked_words_per_packet=512 index_wraps=%u sequence_wrap=%d ownership=whole_region notify_stream_bytes=1024 counter_base=65520 counter_32bit_carry=%d"),
        packets,frames,batch,total,packets/15,packets>32,packets>16);
    return KErrNone;
    }
static TInt16 wsolaTemplate[KWsolaLength*2],wsolaSearch[KWsolaSearch*2];
static volatile TInt wsolaSink;
static TUint32 WsolaArmBatch(TInt& last)
    {
    TUint32 begin=User::FastCounter();
    for (TInt i=0;i<KWsolaArmIterations;++i) {
        last=WsolaBestOffsetOriginal(wsolaTemplate,wsolaSearch);
        wsolaSink+=last;
        }
    return User::FastCounter()-begin;
    }
#include "mdec/ring_host.inc"
#include "spu/ring_host.inc"
#include "wsola_current/ring_host.inc"
static TInt RingWsolaFrames(RRaw& channel,TInt handle,TPtr8& nativeRing,TUint32 mapped,TInt frames)
    {
    RRaw util; TInt rc=util.OpenUtil(); if (rc) return rc;
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    TUint32 address=(TUint32)nativeRing.Ptr(),bytes=16384,packets=0;
    TUint16* ring=(TUint16*)nativeRing.Ptr(); Mem::FillZ(ring,bytes);
    Log(_L8("RING WSOLA CONFIG bytes=16384 frames=%d input_slots=4 output_slots=1 payload_words=880 protocol=40 useful_ARM_W=0 performance_reservation=0"),frames);
    for (TInt frame=1;frame<=frames;++frame) {
        WsolaDataset(frame,wsolaTemplate,wsolaSearch);
        TWsolaResult expected=WsolaReference(wsolaTemplate,wsolaSearch);
        TInt last=-1,bad=0,slot=packets%15,caseId=(frame-1)%8;
        TUint32 armTicks=0,index=65520u+packets;
        if (frame&1) armTicks=WsolaArmBatch(last);
        TUint32 packBegin=User::FastCounter();
        TInt32 sum=0;
        for (TInt k=0;k<4;++k) {
            TUint32 number=index+k;
            TUint16* input=ring+512+((slot+k)%15)*256;
            Mem::FillZ(input,512);
            input[0]=0xc55a; input[1]=(TUint16)(65520u+number); input[2]=256;
            input[3]=(TUint16)(number/15); input[4]=(TUint16)number; input[5]=(TUint16)(number>>16);
            for (TInt j=0;j<240;++j) {
                TInt at=k*240+j;
                TInt16 value=at<220?(wsolaTemplate[at*2]>>6):at<880?(wsolaSearch[(at-220)*2]>>6):0;
                input[16+j]=(TUint16)value;
                if (at<880) sum+=(TInt32)value*(at+1);
                }
            }
        TUint16* output=ring+4352+slot*256;
        for (TInt j=0;j<256;++j) output[j]=0xdead;
        ring[0]=0xd16a; ring[1]=40; ring[2]=4; ring[3]=(TUint16)slot;
        ring[4]=(TUint16)index; ring[5]=(TUint16)(index>>16); ring[6]=(TUint16)caseId;
        Mem::FillZ(inputWords,512); Mem::FillZ(outputWords,512);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)frame; inputWords[2]=256;
        inputWords[6]=(TUint16)(mapped/2); inputWords[7]=(TUint16)(mapped/2>>16);
        inputWords[8]=0xd16c; inputWords[9]=(TUint16)slot; inputWords[10]=4; inputWords[12]=frame==frames;
        TUint32 packTicks=User::FastCounter()-packBegin;
        inputStatus=outputStatus=KRequestPending;
        TTimeIntervalMicroSeconds cpuBefore,cpuAfter; TInt cpuRc=RThread().GetCpuTime(cpuBefore);
        TUint32 begin=User::FastCounter();
        rc=util.Ctl(2,&address,&bytes);
        TInt ro=rc?rc:channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt ri=ro?ro:channel.Ctl(0x0800000e,(TAny*)handle,&in);
        if (rc || ro || ri) { util.Close(); return rc?rc:ro?ro:ri; }
        // DSP owns the whole ring until notification completion/cache invalidate.
        TInt di=Wait(inputStatus,5000),dout=Wait(outputStatus,5000);
        if (!di && !dout) rc=util.Ctl(2,&address,&bytes);
        if (di || dout || rc) { util.Close(); return di?di:dout?dout:rc; }
        TInt offset=output[16],scored=output[17];
        TInt32 score=(TInt32)((TUint32)output[18]|((TUint32)output[19]<<16));
        TUint32 transferTicks=User::FastCounter()-begin,endToEndTicks=User::FastCounter()-packBegin;
        TInt cpuEndRc=RThread().GetCpuTime(cpuAfter);
        TInt cpuUs=(!cpuRc && !cpuEndRc)?(TInt)(cpuAfter.Int64()-cpuBefore.Int64()):-1;
        if (!(frame&1)) armTicks=WsolaArmBatch(last);
        if (last!=expected.offset || !armTicks || offset!=expected.offset || score!=expected.score || scored!=expected.scored) ++bad;
        if (outputWords[0]!=0xc55b || outputWords[1]!=frame || outputWords[4]!=40 || outputWords[6] ||
            outputWords[13]!=0xdc01 || ring[256]!=0xd16b || ring[257]!=frame || ring[258]!=4 || ring[259]!=slot) ++bad;
        for (TInt k=0;k<4;++k) {
            TUint32 number=index+k; const TUint16* input=ring+512+((slot+k)%15)*256;
            for (TInt j=0;j<256;++j) {
                TUint16 value=0;
                if (j==0) value=0xc55a; if (j==1) value=(TUint16)(65520u+number);
                if (j==2) value=256; if (j==3) value=(TUint16)(number/15);
                if (j==4) value=(TUint16)number; if (j==5) value=(TUint16)(number>>16);
                if (j>=16) {
                    TInt at=k*240+j-16;
                    value=at<220?(TUint16)(wsolaTemplate[at*2]>>6):at<880?(TUint16)(wsolaSearch[(at-220)*2]>>6):0;
                    }
                if (input[j]!=value) ++bad;
                }
            }
        for (TInt j=0;j<256;++j) {
            TUint16 value=0;
            if (j==0) value=0xc55b; if (j==1) value=(TUint16)(65520u+index);
            if (j==2) value=256; if (j==3) value=(TUint16)(index/15);
            if (j==4) value=(TUint16)index; if (j==5) value=(TUint16)(index>>16);
            if (j==16) value=(TUint16)expected.offset; if (j==17) value=(TUint16)expected.scored;
            if (j==18) value=(TUint16)expected.score; if (j==19) value=(TUint16)((TUint32)expected.score>>16);
            if (j==20) value=(TUint16)sum; if (j==21) value=(TUint16)((TUint32)sum>>16);
            if (j==22) value=880; if (j==23) value=40;
            if (output[j]!=value) ++bad;
            }
        Log(_L8("RING WSOLA RESULT frame=%d case=%d slot=%d offset=%d expected_offset=%d score=%d expected_score=%d scored=%d expected_scored=%d errors=%d checked_words=1280"),
            frame,caseId,slot,offset,expected.offset,score,expected.score,scored,expected.scored,bad);
        Log(_L8("RING WSOLA TIMING frame=%d arm_iterations=16 arm_ticks=%u arm_first=%d pack_ticks=%u transfer_ticks=%u end_to_end_ticks=%u cpu_us=%d raw_dsp_ticks=%u counts_per_ms=%u"),
            frame,armTicks,frame&1,packTicks,transferTicks,endToEndTicks,cpuUs,Get32(8),Get32(10));
        Log(_L8("DCR READ frame=%d protocol=40 marker=%04x io_port=0200 before=%04x after=%04x wpe_before=%d wpe_after=%d writes=0 diagnostic_only=1"),
            frame,outputWords[13],outputWords[14],outputWords[15],(outputWords[14]&0x80)!=0,(outputWords[15]&0x80)!=0);
        if (bad) { util.Close(); return KErrCorrupt; }
        packets+=4;
        }
    util.Close();
    Log(_L8("RING WSOLA PASS jobs=%d input_slots_per_job=4 output_slots_per_job=1 checked_words_per_job=1280 protocol=40 ownership=whole_region useful_ARM_W=0"),frames);
    return KErrNone;
    }
static TInt WsolaFrames(RRaw& channel,TInt handle,TInt reps,TInt frames,RPerformance& perf)
    {
    static TTransfer in(inputWords,inputStatus,KWsolaInputBytes),
        out(outputWords,outputStatus,KWsolaOutputBytes);
    TUint32 total=0;
    for (TInt sequence=1;sequence<=frames;++sequence) {
        WsolaDataset(sequence,wsolaTemplate,wsolaSearch);
        TWsolaResult expected=WsolaReference(wsolaTemplate,wsolaSearch);
        TInt caseId=(sequence-1)%KWsolaCases,last=-1;
        TInt perfBefore=perf.Active()?perf.Percent():0;
        TUint32 armTicks=0;
        // Alternate the baseline order; neither baseline overlaps this packet.
        if (sequence&1) armTicks=WsolaArmBatch(last);
        Mem::FillZ(inputWords,KWsolaInputBytes); Mem::FillZ(outputWords,KWsolaOutputBytes);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)sequence;
        inputWords[2]=KWsolaInputBytes/2; inputWords[3]=(TUint16)reps;
        inputWords[4]=1; inputWords[5]=(TUint16)caseId; inputWords[12]=sequence==frames;
        TUint32 packBegin=User::FastCounter();
        for (TInt i=0;i<KWsolaLength;++i) inputWords[16+i]=(TUint16)(wsolaTemplate[i*2]>>6);
        for (TInt i=0;i<KWsolaSearch;++i) inputWords[236+i]=(TUint16)(wsolaSearch[i*2]>>6);
        TUint32 packTicks=User::FastCounter()-packBegin;
        inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter();
        TInt rcOut=channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt rcIn=channel.Ctl(0x0800000e,(TAny*)handle,&in);
        TUint32 issueUs=Us(begin);
        TInt doneIn=rcIn?rcIn:Wait(inputStatus);
        TInt doneOut=rcOut?rcOut:Wait(outputStatus);
        TUint32 done=User::FastCounter(),transferTicks=done-begin,endToEndTicks=done-packBegin;
        if (!(sequence&1)) armTicks=WsolaArmBatch(last);
        TInt perfAfter=perf.Active()?perf.Percent():0;
        TInt bad=0;
        if (rcIn || rcOut || doneIn || doneOut) bad=1;
        if (last!=expected.offset || !armTicks) ++bad;
        TInt32 inputSum=0;
        for (TInt i=16;i<896;++i) inputSum+=(TInt32)(TInt16)inputWords[i]*(i-15);
        TInt expectedOff=reps?expected.offset:0,expectedCount=reps?expected.scored:0;
        TInt32 expectedScore=reps?expected.score:0;
        if (outputWords[0]!=0xc55b || outputWords[1]!=sequence || outputWords[2]!=896 ||
            outputWords[3]!=reps || outputWords[4]!=20 || outputWords[5]!=sequence ||
            (TInt32)Get32(6)!=expectedScore || outputWords[12]!=(sequence==frames) ||
            outputWords[13]!=15 || outputWords[16]!=expectedOff || outputWords[17]!=expectedCount ||
            outputWords[18]!=896 || outputWords[19]!=24 || outputWords[20]!=1 ||
            outputWords[21]!=caseId || (TInt32)Get32(22)!=inputSum) ++bad;
        if (perf.Active() && (perfBefore!=100 || perfAfter!=100)) ++bad;
        total+=endToEndTicks;
        Log(_L8("WSOLA frame=%d case=%d reps=%d put=%d/%d get=%d/%d errors=%d stop=%d"),
            sequence,caseId,reps,rcIn,doneIn,rcOut,doneOut,bad,outputWords[12]);
        Log(_L8("WSOLA result frame=%d offset=%u expected_offset=%d score=%d expected_score=%d scored=%u expected_scored=%d input_sum=%d expected_sum=%d"),
            sequence,outputWords[16],expectedOff,(TInt32)Get32(6),expectedScore,
            outputWords[17],expectedCount,(TInt32)Get32(22),inputSum);
        Log(_L8("WSOLA reference frame=%d offset=%d score=%d scored=%d arm_last=%d"),
            sequence,expected.offset,expected.score,expected.scored,last);
        Log(_L8("WSOLA timing frame=%d arm_iterations=%d arm_ticks=%u arm_first=%d pack_ticks=%u transfer_ticks=%u end_to_end_ticks=%u issue_us=%u raw_dsp_ticks=%u dsp_stamp=%u counts_per_ms=%u"),
            sequence,KWsolaArmIterations,armTicks,sequence&1,packTicks,transferTicks,
            endToEndTicks,issueUs,Get32(8),Get32(14),Get32(10));
        Log(_L8("WSOLA size frame=%d input_bytes=1792 output_bytes=48 input_words=%u output_words=%u protocol=%u operation=%u case=%u"),
            sequence,outputWords[18],outputWords[19],outputWords[4],outputWords[20],outputWords[21]);
        if (perf.Active()) Log(_L8("PERF frame=%d before=%d after=%d"),sequence,perfBefore,perfAfter);
        if (bad) return doneIn?doneIn:(doneOut?doneOut:KErrCorrupt);
        }
    TInt rc=State(channel,handle,_L8("worker WSOLA complete"),1); if (rc) return rc;
    Log(_L8("WORKER WSOLA PASS frames=%d creates=1 runs=0 reps=%d input_bytes=1792 output_bytes=48 total_ticks=%u arm_iterations=16 no_crc=1"),
        frames,reps,total);
    return KErrNone;
    }
static TInt Calibrate(RRaw& channel,TInt handle,RPerformance& perf)
    {
    static TTransfer in(inputWords,inputStatus),out(outputWords,outputStatus);
    const TInt delayMs[]={0,100,200,400,800,100,200,400};
    TUint32 previousBegin=0,previousDone=0,previousStamp=0;
    for (TInt sequence=1;sequence<=8;++sequence) {
        User::After(delayMs[sequence-1]*1000);
        Mem::FillZ(inputWords,512); Mem::FillZ(outputWords,512);
        inputWords[0]=0xc55a; inputWords[1]=(TUint16)sequence;
        inputWords[2]=256; inputWords[3]=0; inputWords[12]=sequence==8;
        for (TInt i=16;i<256;++i) inputWords[i]=(TUint16)(i*17+sequence);
        TInt perfBefore=perf.Active()?perf.Percent():0;
        inputStatus=outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter();
        TInt rcOut=channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt rcIn=channel.Ctl(0x0800000e,(TAny*)handle,&in);
        TInt doneIn=rcIn?rcIn:Wait(inputStatus);
        TInt doneOut=rcOut?rcOut:Wait(outputStatus);
        TUint32 done=User::FastCounter(),stamp=Get32(14);
        TInt perfAfter=perf.Active()?perf.Percent():0;
        TInt bad=0;
        if (rcIn || rcOut || doneIn || doneOut) bad=1;
        if (outputWords[0]!=0xc55b || outputWords[1]!=sequence ||
            outputWords[2]!=256 || outputWords[3]!=0 || outputWords[4]!=20 ||
            outputWords[5]!=sequence || Get32(6)!=0 || outputWords[13]!=15 ||
            outputWords[12]!=(sequence==8)) ++bad;
        for (TInt i=16;i<256;++i)
            if (outputWords[i]!=(TUint16)(inputWords[i]*3u+sequence)) ++bad;
        if (perf.Active() && (perfBefore!=100 || perfAfter!=100)) ++bad;
        Log(_L8("CAL frame=%d delay_ms=%d begin=%u done=%u dsp_stamp=%u put=%d/%d get=%d/%d errors=%d"),
            sequence,delayMs[sequence-1],begin,done,stamp,rcIn,doneIn,rcOut,doneOut,bad);
        Log(_L8("CAL conditions frame=%d perf_before=%d perf_after=%d raw_ticks=%u reported_counts_per_ms=%u"),
            sequence,perfBefore,perfAfter,Get32(8),Get32(10));
        if (bad) return KErrCorrupt;
        if (sequence>1) {
            TUint32 low=begin-previousDone,high=done-previousBegin,dsp=stamp-previousStamp;
            // Both timestamp differences carry at most one counter tick error.
            if (low>1) --low; else return KErrCorrupt;
            ++high;
            if (!dsp || high<low) return KErrCorrupt;
            TUint32 minHz=(TUint32)(((TUint64)dsp*counterHz)/high);
            TUint32 maxHz=(TUint32)(((TUint64)dsp*counterHz)/low);
            Log(_L8("CAL interval=%d dsp_delta=%u arm_min_ticks=%u arm_max_ticks=%u hz_min=%u hz_max=%u"),
                sequence-1,dsp,low,high,minHz,maxHz);
            }
        previousBegin=begin; previousDone=done; previousStamp=stamp;
        }
    TInt rc=State(channel,handle,_L8("calibration complete"),1);
    if (rc) return rc;
    Log(_L8("WORKER CALIBRATION PASS frames=8 creates=1 runs=0 intervals=7 no_crc=1"));
    return KErrNone;
    }
static TInt MessageStages(RRaw& channel,TInt handle,TUint32 env)
    {
    static TTransfer out(outputWords,outputStatus);
    for (TInt stage=1;stage<=3;++stage) {
        Mem::FillZ(outputWords,512); outputStatus=KRequestPending;
        TUint32 begin=User::FastCounter();
        TInt rc=channel.Ctl(0x08000010,(TAny*)handle,&out);
        TInt done=rc?rc:Wait(outputStatus);
        Log(_L8("message stage expected=%d get=%d/%d wall_us=%u"),stage,rc,done,Us(begin));
        if (done) return done;
        Log(_L8("  stage header=%04x stage=%u size=%u protocol=%u result=%u env=%08x cmd=%08x arg1=%08x arg2=%08x"),
            outputWords[0],outputWords[1],outputWords[2],outputWords[3],outputWords[4],
            Get32(6),Get32(8),Get32(10),Get32(12));
        Log(_L8("  messenger to_gpp=%08x count=%u notify=%04x handle_raw_words=%04x/%04x status=%04x max_messages=%u"),
            Get32(16),outputWords[22],outputWords[24],outputWords[26],outputWords[27],outputWords[28],outputWords[30]);
        Log(_L8("  from_dsp=%08x empty=%u post_swi=%u count=%u reserved=%u"),
            Get32(32),outputWords[34],outputWords[35],outputWords[36],outputWords[37]);
        Log(_L8("  to_dsp=%08x empty=%u post_swi=%u count=%u reserved=%u"),
            Get32(38),outputWords[40],outputWords[41],outputWords[42],outputWords[43]);
        Log(_L8("  record captured=%u empty_after=%u count_after=%u raw_words=%04x/%04x/%04x/%04x/%04x/%04x/%04x/%04x"),
            outputWords[44],outputWords[54],outputWords[55],outputWords[46],outputWords[47],
            outputWords[48],outputWords[49],outputWords[50],outputWords[51],outputWords[52],outputWords[53]);
        if (outputWords[44]) {
            Log(_L8("  record arm_raw cmd=%08x arg1=%08x arg2=%08x source=%08x"),
                Get32(46),Get32(48),Get32(50),Get32(52));
            Log(_L8("  record arm_ror16 cmd=%08x arg1=%08x arg2=%08x source=%08x"),
                (Get32(46)>>16)|(Get32(46)<<16),(Get32(48)>>16)|(Get32(48)<<16),
                (Get32(50)>>16)|(Get32(50)<<16),(Get32(52)>>16)|(Get32(52)<<16));
            }
        if (outputWords[0]!=0xc55d || outputWords[1]!=stage ||
            outputWords[2]!=256 || outputWords[3]!=15 || Get32(6)!=env) return KErrCorrupt;
        }
    Log(_L8("MESSAGE STAGES OBSERVED count=3 get_timeout=0 put_timeout=0"));
    TInt rc=SubmitGetMessage(channel,handle); if (rc) return rc;
    rc=FinishGetMessage(_L8("hello after stages")); if (rc) return rc;
    if (getMessage.command!=0x600 || getMessage.argument1!=0x000f0001 ||
        getMessage.argument2!=env) return KErrCorrupt;
    Log(_L8("MESSAGE HELLO AFTER STAGES PASS protocol=15"));
    return KErrNone;
    }
static TInt ExitSnapshot(TInt offset,TInt stage,TUint32 env,TInt protocol=25)
    {
    const TUint16* b=outputWords+offset;
    Log(_L8("EXITDIAG stage=%u protocol=%u result=%u env=%08x cmd=%08x arg1=%08x arg2=%08x"),
        b[1],b[3],b[4],Get32(offset+6),Get32(offset+8),Get32(offset+10),Get32(offset+12));
    Log(_L8("EXITDIAG stage=%d input_pending=%u output_pending=%u idle_input=%d idle_output=%d waits=%u status=%08x"),
        stage,b[56],b[57],(TInt16)b[58],(TInt16)b[59],b[60],Get32(offset+62));
    Log(_L8("EXITDIAG stage=%d to_gpp=%08x count=%u notify=%04x handle=%04x/%04x status=%04x max=%u"),
        stage,Get32(offset+16),b[22],b[24],b[26],b[27],b[28],b[30]);
    Log(_L8("EXITDIAG stage=%d from_dsp=%08x header=%04x/%04x/%04x/%04x captured=%u after=%04x/%04x"),
        stage,Get32(offset+32),b[34],b[35],b[36],b[37],b[44],b[54],b[55]);
    Log(_L8("EXITDIAG stage=%d from_raw=%04x/%04x/%04x/%04x/%04x/%04x/%04x/%04x"),
        stage,b[46],b[47],b[48],b[49],b[50],b[51],b[52],b[53]);
    Log(_L8("EXITDIAG stage=%d to_dsp=%08x header=%04x/%04x/%04x/%04x raw_present=%u after=%04x/%04x"),
        stage,Get32(offset+38),b[40],b[41],b[42],b[43],b[64],b[74],b[75]);
    Log(_L8("EXITDIAG stage=%d to_raw=%04x/%04x/%04x/%04x/%04x/%04x/%04x/%04x"),
        stage,b[66],b[67],b[68],b[69],b[70],b[71],b[72],b[73]);
    return b[0]==0xc55d && b[1]==stage && b[2]==256 && b[3]==protocol &&
        Get32(offset+6)==env ? KErrNone : KErrCorrupt;
    }
static TInt ArmExitReport(RRaw& channel,TInt handle)
    {
    // Static descriptor/status survive a pending delete and QUARANTINE.
    static TTransfer out(outputWords,outputStatus);
    Mem::FillZ(outputWords,512); outputStatus=KRequestPending;
    TInt rc=channel.Ctl(0x08000010,(TAny*)handle,&out);
    Log(_L8("EXITDIAG output armed=%d status=%d"),rc,outputStatus.Int());
    return rc;
    }
static TInt WorkerMessage(RRaw& channel,TInt handle,TUint32 env,TBool queued)
    {
    // Receive is queued while CREATED, before the sole input releases the
    // finite worker. No execute wrapper or RMS_EXITACK participates.
    TInt rc=KErrNone;
    const TPtrC8 timing=queued?_L8("after output"):_L8("before input");
    Log(_L8("MSGWORKER receive_timing=%S status_address=%08x record_address=%08x"),
        &timing,
        (TUint32)&messageGetStatus,(TUint32)&getMessage);
    if (!queued) { rc=SubmitGetMessage(channel,handle); if (rc) return rc; }
    rc=ArmExitReport(channel,handle); if (rc) return rc;
    Mem::FillZ(inputWords,512);
    inputWords[0]=0xc55a; inputWords[1]=1; inputWords[2]=256; inputWords[12]=1;
    static TTransfer in(inputWords,inputStatus);
    inputStatus=KRequestPending;
    rc=channel.Ctl(0x0800000e,(TAny*)handle,&in);
    Log(_L8("MSGWORKER trigger=%d input=%d output=%d no_run=1"),rc,inputStatus.Int(),outputStatus.Int());
    TInt ri=Wait(inputStatus,5000),ro=Wait(outputStatus,5000);
    Log(_L8("MSGWORKER trigger completion input=%d/%d output=%d/%d"),ri,inputStatus.Int(),ro,outputStatus.Int());
    if (!rc && ri) rc=ri; if (!rc && ro) rc=ro;
    if (!ro) {
        TInt snapshot=ExitSnapshot(0,7,env,26);
        if (!snapshot && (outputWords[4]!=1 || Get32(8)!=0x606 ||
            Get32(10)!=0xa1b2c3d4 || Get32(12)!=env || Get32(62)!=0x8000)) snapshot=KErrCorrupt;
        if (!rc && snapshot) rc=snapshot;
        }
    if (queued) { TInt submitted=SubmitGetMessage(channel,handle); if (!rc && submitted) rc=submitted; }
    TInt delivered=FinishGetMessage(_L8("created worker"),3000);
    if (!delivered && (getMessage.command!=0x606 ||
        getMessage.argument1!=0xa1b2c3d4 || getMessage.argument2!=env)) delivered=KErrCorrupt;
    if (!rc && delivered) rc=delivered;
    TInt state=State(channel,handle,_L8("created worker complete"),1);
    if (!rc && state) rc=state;
    Log(_L8("MSGWORKER delivery=%d overall=%d no_run=1"),delivered,rc);
    return rc;
    }
static TInt Research(const TDesC& mode,TInt reps,TUint32 uid,TInt packetBytes,TInt frames,TInt batch)
    {
    TUint32 researchBegin=User::FastCounter(),ringSetupUs=0,ringTeardownBegin=0;
    TBool worker=mode==_L("worker-one") || mode==_L("worker-serial") ||
        mode==_L("worker-parallel") || mode==_L("worker-calibrate") || mode==_L("worker-transfer") || mode==_L("worker-wsola");
    const TBool wsola=mode==_L("worker-wsola");
    const TBool routingDiag=mode==_L("run-routing");
    const TBool dcrRead=mode==_L("dmm-ring-dcr");
    const TBool ringWsola=mode==_L("dmm-ring-wsola");
    const TBool ringWsolaCurrent=mode==_L("dmm-ring-wsola-current");
    const TBool cpuWindow=mode==_L("dmm-ring-window");
    const TBool ringMdec=mode==_L("dmm-ring-mdec");
    const TBool ringSpu=mode==_L("dmm-ring-spu");
    if ((dcrRead || ringWsola || ringWsolaCurrent || cpuWindow || ringMdec || ringSpu) && uid!=0x20002d84) return KErrNotSupported;
    const TBool nativeRingMode=mode==_L("dmm-ring-native") || dcrRead || ringWsola || ringWsolaCurrent || cpuWindow || ringMdec || ringSpu;
    const TBool dmmRing=mode==_L("dmm-ring") || nativeRingMode;
    const TBool runTransfer=mode==_L("run-transfer") || routingDiag || dmmRing;
    const TBool nativeCopy=mode==_L("native-copy");
    const TBool exitDiag=mode==_L("exit-stages");
    const TBool workerMsg=mode==_L("worker-message") || mode==_L("worker-message-queued");
    TUint32 diagnosticEnv=0;
    if ((nativeCopy || exitDiag) && uid!=0x20002496) return KErrNotSupported;
    const TInt outputBytes=wsola?KWsolaOutputBytes:packetBytes;
    RLibrary lib; TInt rc=lib.Load(_L("bridgeapi.dll"));
    Log(_L8("library load=%d"),rc); if (rc) return rc;
    TUint32 delta=0; rc=CheckProfile(lib,uid,delta);
    Log(_L8("profile guard=%d delta=%08x"),rc,delta); if (rc) return rc;
    if (mode==_L("inspect")) return 0;
    if (mode==_L("patcher-check")) return PatcherCheck();
    if (mode==_L("patcher-read-check")) return PatcherReadCheck(uid);
    if (mode==_L("pointer-snapshot")) return PatcherPointerSnapshot(uid);
    RPerformance perf;
    if (worker) { rc=perf.Start(uid); if (rc) { perf.Stop(); return rc; } }
    TUint32 object[64],dcd[64]; Mem::FillZ(object,sizeof(object)); Mem::FillZ(dcd,sizeof(dcd));
    ((void(*)(TAny*))lib.Lookup(36))(object);
    ((void(*)(TAny*))lib.Lookup(11))(dcd);
    Log(_L8("BEGIN processor open"));
    rc=((TInt(*)(TAny*,TInt,TInt,TAny*))lib.Lookup(32))(object,0,0,NULL);
    Log(_L8("processor open=%d"),rc); if (rc) return rc;
    RRaw channel; channel.SetHandle((TInt)object[0]);
    TPtr8 nativeIn(NULL,0,0),nativeOut(NULL,0,0);
    TPtr8 nativeRing(NULL,0,0);
    TUint32 ringReserved=0,ringMapped=0;
    TUint32 nativePages[8]; Mem::FillZ(nativePages,sizeof(nativePages));
    TInt handle=0;
    do {
        if (mode==_L("processor-state")) {
            rc=ProcessorState(channel);
            if (!rc) Log(_L8("PROCESSOR STATE PASS native_ioctl=2 no_patcher=1 no_create=1 no_run=1"));
            break;
            }
        Log(_L8("BEGIN DCD bind"));
        rc=((TInt(*)(TAny*,TAny*))lib.Lookup(9))(dcd,object);
        Log(_L8("DCD bind=%d loader=%08x"),rc,object[3]); if (rc) break;
        // PROC_Load stops/reloads the processor without removing the shared
        // native audio queues. Attach to the running firmware base instead.
        // The DCD parse below registers only our dynamic library.
        rc=nativeRingMode?ProcessorState(channel):PatcherPointerSnapshot(uid,ETrue,0,ETrue);
        Log(_L8("BASE attach gate=%d reused_running=1 proc_load_calls=0"),rc);
        if (rc) break;
        if (mode==_L("base")) break;
        if (dmmRing) {
            rc=Native(lib,object,nativeRing,16384); if (rc) break;
            rc=nativeRingMode?NativeRingPages(nativeRing,nativePages,EFalse):
                PatcherPointerSnapshot(uid,EFalse,0,ETrue,(TUint32)nativeRing.Ptr(),16384); if (rc) break;
            rc=RingMap(lib,object,nativeRing,ringReserved,ringMapped); if (rc) break;
            }
        if (mode==_L("dmm-provenance") || mode==_L("dmm-map")) {
            rc=Native(lib,object,nativeIn,16384);
            if (!rc) rc=PatcherPointerSnapshot(uid,EFalse,0,ETrue,(TUint32)nativeIn.Ptr(),16384);
            if (!rc && mode==_L("dmm-map")) rc=MapProbe(lib,object,nativeIn);
            break;
            }
        if (mode==_L("buffers")) {
            rc=Native(lib,object,nativeIn);
            if (!rc) rc=Native(lib,object,nativeOut);
            break;
            }
        typedef TInt(*TLock)(TAny*);
        TLock lock=(TLock)(0x80A5EFA1u+delta),unlock=(TLock)(0x80A5EF97u+delta);
        typedef TInt(*TParse)(TAny*,const TDesC*);
        TParse parse=(TParse)(0x80A5F0D5u+delta);
        TPtrC node(_L("E:\\c55stream.dll55l"));
        if (nativeCopy) node.Set(_L("Z:\\system\\apps\\strmcopy\\strmcopydyn.dll55l"));
        Log(_L8("node reference_rom=%d"),nativeCopy);
        Log(_L8("BEGIN DCD parse"));
        lock((TAny*)object[3]); rc=parse((TAny*)object[3],&node); unlock((TAny*)object[3]);
        Log(_L8("DCD parse=%d"),rc); if (rc) break;
        if (nativeCopy) {
            // ROM has properties registration0 only. The research copy
            // differs only in registration2/checksum, keeping ROM DSP code.
            TPtrC referenceLibrary(_L("E:\\c55stream.dll55l"));
            Log(_L8("BEGIN reference library2 parse"));
            lock((TAny*)object[3]); rc=parse((TAny*)object[3],&referenceLibrary); unlock((TAny*)object[3]);
            Log(_L8("reference library2 parse=%d"),rc); if (rc) break;
            }
        static const TUint8 uuid[]={0x12,0xbf,0x7c,0x96,0x0e,0xb9,0x54,0x4b,0xa4,0xd3,0x3c,0x84,0x24,0x9e,0xe1,0xda};
        static const TUint8 referenceUuid[]={0x7e,0x2c,0xeb,0x7e,0x5a,0x78,0xd4,0x11,0xa6,0x50,0x00,0xc0,0x4f,0x0c,0x04,0xf3};
        static TBuf8<4> args; args.Zero();
        Log(_L8("BEGIN select node"));
        rc=((TInt(*)(TAny*,const TAny*,const TDesC8*))lib.Lookup(7))(dcd,nativeCopy?referenceUuid:uuid,&args);
        Log(_L8("select node=%d"),rc); if (rc) break;
        TInt reference=0;
        rc=((TInt(*)(TAny*,TInt*))lib.Lookup(4))(dcd,&reference);
        Log(_L8("properties=%d reference=%08x"),rc,reference); if (rc || !reference) break;
        const TDesC8* descriptor=(const TDesC8*)reference;
        if (descriptor->Length()<3040) { rc=KErrCorrupt; break; }
        TUint8* properties=(TUint8*)descriptor->Ptr();
        TUint32* nodeTimeout=(TUint32*)(properties+160);
        Log(_L8("node timeout original=%08x"),*nodeTimeout);
        *nodeTimeout=0xFFFFFFFFu;
        Log(_L8("node timeout modified=%08x"),*nodeTimeout);
        for (TInt direction=0;direction<2;++direction)
            {
            TUint32* attr=(TUint32*)(properties+(direction?1592:184));
            Log(_L8("original stream direction=%d attrs=%u/%u/%u/%u/%u id=%u connection=%u"),
                direction,attr[0],attr[1],attr[2],attr[3],attr[4],attr[5],attr[6]);
            // PDD 8019FF5C creates host channels only for connection=0
            // at +24. DCD defaults to 1 (device connection), which leaves
            // task14/task16 without host stream objects.
            attr[0]=0; attr[1]=(direction?outputBytes:packetBytes)/2; attr[2]=2; attr[3]=1000; attr[4]=0; attr[6]=0;
            Log(_L8("stream direction=%d size_words=%u nbufs=%u timeout_ms=%u connection=%u"),
                direction,attr[1],attr[2],attr[3],attr[6]);
            }
        TAllocateRecord params; Mem::FillZ(&params,sizeof(params));
        params.header=0x30000014; params.maximum=20; params.data[2]=(TUint32)reference;
        Log(_L8("BEGIN allocate"));
        rc=channel.Ctl(4,&params,&handle); Log(_L8("allocate=%d handle=%08x"),rc,handle); if (rc) break;
        createStatus=KRequestPending; TUint32 begin=User::FastCounter();
        Log(_L8("BEGIN create"));
        rc=channel.Ctl(5,(TAny*)handle,&createStatus); if (!rc) rc=Wait(createStatus,5000);
        Log(_L8("create=%d status=%d wall_us=%u"),rc,createStatus.Int(),Us(begin)); if (rc) break;
        TInt stateRc=State(channel,handle,_L8("created"),(worker || workerMsg)?1:-1);
        if ((worker || workerMsg) && stateRc) { rc=stateRc; break; }
        if (mode==_L("create")) break;
        TUint32 env=0;
        if (mode==_L("info") || mode==_L("messages") || mode==_L("receive-created") ||
            mode==_L("message-stages") || nativeCopy || exitDiag || workerMsg || runTransfer) {
            rc=NodeInfo(channel,handle,_L8("created"),env); if (rc) break;
            if (exitDiag) diagnosticEnv=env;
            if (mode==_L("info")) break;
            if (mode==_L("receive-created")) {
                // PDD get accepts state 1. No execute or DSP message is sent.
                // A successful delete leaves state 4; control 7 destroys the
                // LDD node, completing its saved receive request with -3.
                rc=SubmitGetMessage(channel,handle);
                if (!rc && messageGetStatus!=KRequestPending) rc=KErrCorrupt;
                Log(_L8("created receive expected_pending=%d rc=%d no_run=1"),
                    messageGetStatus==KRequestPending,rc);
                break;
                }
            }
        if (mode==_L("serial") || mode==_L("parallel") || worker || runTransfer || nativeCopy || exitDiag || workerMsg) {
            rc=Native(lib,object,nativeIn,packetBytes); if (rc) break;
            rc=Native(lib,object,nativeOut,outputBytes); if (rc) break;
            inputWords=(TUint16*)nativeIn.Ptr(); outputWords=(TUint16*)nativeOut.Ptr();
            }
        if (workerMsg) { rc=WorkerMessage(channel,handle,env,mode==_L("worker-message-queued")); break; }
        if (worker) {
            Log(_L8("BEGIN worker stream no_run=1 frames=%d packet_bytes=%d"),frames,packetBytes);
            rc=wsola?WsolaFrames(channel,handle,reps,frames,perf):
                mode==_L("worker-calibrate")?Calibrate(channel,handle,perf):
                Frames(channel,handle,reps,mode==_L("worker-parallel"),frames,ETrue,&perf,
                    packetBytes,mode!=_L("worker-transfer"));
            break;
            }
        if (mode==_L("message-stages")) {
            rc=Native(lib,object,nativeOut); if (rc) break;
            outputWords=(TUint16*)nativeOut.Ptr();
            }
        if (runTransfer) {
            // Legacy diagnostics enumerate native queues. The native mode
            // keeps the running base and relies on the RMS MEM_valloc env
            // lifetime, then queries only our retained CREATED task.
            rc=env?(nativeRingMode?State(channel,handle,_L8("native pre-RUN"),1):PatcherPointerSnapshot(uid,ETrue,env)):KErrCorrupt;
            if (nativeRingMode) Log(_L8("NATIVE pre-RUN gate=%d env=%08x state=1 no_patcher=1 proc_load_calls=0 env_allocator=RMS_MEM_valloc"),rc,env);
            else Log(_L8("ROUTING pre-RUN gate=%d no_run_on_failure=1"),rc);
            if (rc) break;
            }
        Log(_L8("BEGIN execute"));
        runStatus=KRequestPending; rc=channel.Ctl(0x08000007,(TAny*)handle,&runStatus);
        Log(_L8("execute submitted=%d status=%d"),rc,runStatus.Int());
        if (!rc) rc=Wait(runStatus);
        Log(_L8("execute start=%d status=%d"),rc,runStatus.Int()); if (rc) break;
        State(channel,handle,_L8("running"));
        if (mode==_L("execute")) break;
        if (mode==_L("messages")) { rc=Messages(channel,handle,env); break; }
        if (mode==_L("message-stages")) { rc=MessageStages(channel,handle,env); break; }
        if (nativeCopy) { rc=ReferenceCopyFrames(channel,handle); break; }
        if (exitDiag) {
            rc=Frames(channel,handle,0,EFalse,8,EFalse,NULL,512,EFalse,21);
            if (rc) break;
            rc=ArmExitReport(channel,handle); if (rc) break;
            rc=Wait(outputStatus,5000);
            Log(_L8("EXITDIAG before exit output=%d status=%d"),rc,outputStatus.Int());
            if (!rc) rc=ExitSnapshot(0,4,diagnosticEnv);
            break;
            }
        if (dmmRing) { ringSetupUs=Us(researchBegin); Log(_L8("RING SETUP total_us=%u includes_journaling=1"),ringSetupUs); }
        rc=ringWsolaCurrent?RingWsolaCurrentFrames(channel,handle,nativeRing,ringMapped,frames):
            ringSpu?RingSpuFrames(channel,handle,nativeRing,ringMapped,batch,frames):
            ringMdec?RingMdecFrames(channel,handle,nativeRing,ringMapped,batch,frames):
            ringWsola?RingWsolaFrames(channel,handle,nativeRing,ringMapped,frames):
            dmmRing?RingFrames(channel,handle,nativeRing,ringMapped,batch,frames,dcrRead,cpuWindow):
            runTransfer?Frames(channel,handle,reps,EFalse,frames,EFalse,NULL,512,EFalse,21):
            Frames(channel,handle,reps,mode==_L("parallel"));
        if (!rc && nativeRingMode) rc=NativeRingPages(nativeRing,nativePages,ETrue);
        } while (0);
    if (dmmRing) ringTeardownBegin=User::FastCounter();
    if (handle) {
        if (inputStatus==KRequestPending) {
            Log(_L8("cancel input=%d"),channel.Ctl(0x0800000f,(TAny*)handle,0));
            Log(_L8("cancel input completion=%d"),Wait(inputStatus));
            }
        if (outputStatus==KRequestPending) {
            Log(_L8("cancel output=%d"),channel.Ctl(0x08000011,(TAny*)handle,0));
            Log(_L8("cancel output completion=%d"),Wait(outputStatus));
            }
        if (createStatus==KRequestPending || runStatus==KRequestPending ||
            inputStatus==KRequestPending || outputStatus==KRequestPending) {
            Log(_L8("QUARANTINE pending request; no delete/free/close; reboot required"));
            // Each delay is finite. The supervising runner returns on its
            // deadline without killing this resource-owning process.
            for (;;) User::After(1000000);
            }
        if (routingDiag) {
            Log(_L8("ROUTING phase=before-delete diagnostic_only=1"));
            PatcherPointerSnapshot(uid,ETrue);
            }
        // Native delete owns RMS_EXIT -> EXITACK -> delete. Task3 exposes
        // the LDD state, not the PDD internal state or callback phase.
        deleteStatus=KRequestPending;
        TInt stateRc=State(channel,handle,_L8("before delete"),(worker || workerMsg)?1:-1);
        if ((worker || workerMsg) && !rc && stateRc) rc=stateRc;
        TBool expectExitMessage=mode==_L("messages") && !rc;
        TBool expectExitReport=exitDiag && !rc;
        if (expectExitReport) {
            TInt er=ArmExitReport(channel,handle);
            if (er) { rc=er; expectExitReport=EFalse; }
            }
        if (expectExitMessage) {
            TInt gr=SubmitGetMessage(channel,handle);
            if (gr) { rc=gr; expectExitMessage=EFalse; }
            }
        Log(_L8("BEGIN delete"));
        TUint32 deleteBegin=User::FastCounter();
        TInt dr=channel.Ctl(6,(TAny*)handle,&deleteStatus);
        Log(_L8("delete submitted=%d status=%d submit_us=%u"),dr,deleteStatus.Int(),Us(deleteBegin));
        if (expectExitReport) {
            TInt er=Wait(outputStatus,15000);
            Log(_L8("EXITDIAG after exit output=%d status=%d delete_status=%d"),er,outputStatus.Int(),deleteStatus.Int());
            if (!er) {
                er=ExitSnapshot(0,5,diagnosticEnv);
                TInt last=ExitSnapshot(96,6,diagnosticEnv);
                if (!er) er=last;
                Log(_L8("EXITDIAG post-idle output reissued; final reclaim/idle and EXITACK require clean delete"));
                }
            if (!rc && er) rc=er;
            }
        if (expectExitMessage) {
            TInt gr=FinishGetMessage(_L8("rms exit"));
            if (!gr && (getMessage.command!=0x603 ||
                getMessage.argument1!=0x80000000 || getMessage.argument2!=1)) gr=KErrCorrupt;
            if (!rc && gr) rc=gr;
            }
        if (!dr) dr=Wait(deleteStatus,5000);
        Log(_L8("delete=%d status=%d"),dr,deleteStatus.Int()); if (!rc && dr) rc=dr;
        State(channel,handle,_L8("after delete"));
        if (routingDiag && dr) {
            Log(_L8("ROUTING phase=after-failed-delete diagnostic_only=1"));
            PatcherPointerSnapshot(uid,ETrue);
            }
        if (outputStatus==KRequestPending) {
            Log(_L8("QUARANTINE diagnostic output pending; no free/close; reboot required"));
            for (;;) User::After(1000000);
            }
        if (dr && mode!=_L("messages")) {
            Log(_L8("QUARANTINE delete failed=%d; no free/close; reboot required"),dr);
            for (;;) User::After(1000000);
            }
        if ((worker || workerMsg) && !dr) {
            // Task3 reports the LDD state enum (node+20), which overrides
            // the PDD record. Deleted is 5 here; PDD internal state is 4.
            stateRc=State(channel,handle,_L8("worker deleted"),5);
            if (!rc && stateRc) rc=stateRc;
            }
        if (mode==_L("messages") && dr==KErrTimedOut && deleteStatus==KRequestPending) {
            // The DSP diagnostic has a 15-second receive limit. Preserve
            // pending storage and allow its wrapper ACK before closing.
            TInt late=Wait(deleteStatus,15000);
            Log(_L8("delete diagnostic late completion=%d status=%d"),late,deleteStatus.Int());
            if (!late) dr=0; // Keep the original error in rc.
            }
        if (dr) {
            Log(_L8("QUARANTINE delete failed=%d; no free/close; reboot required"),dr);
            for (;;) User::After(1000000);
            }
        if (workerMsg) Log(_L8("MSGWORKER after delete receive_status=%d"),messageGetStatus.Int());
        if (!dr && (mode==_L("receive-created") || (workerMsg && !stateRc) ||
            (messageGetStatus!=KRequestPending && messagePutStatus!=KRequestPending))) {
            TInt freeTask=channel.Ctl(7,(TAny*)handle,0);
            Log(_L8("free task=%d"),freeTask); if (!rc && freeTask) rc=freeTask;
            if (freeTask) {
                Log(_L8("QUARANTINE free task failed; no close; reboot required"));
                for (;;) User::After(1000000);
                }
            if (!freeTask && (mode==_L("receive-created") ||
                (workerMsg && messageGetStatus==KRequestPending))) {
                TInt cancelled=Wait(messageGetStatus,1000);
                Log(_L8("created receive after free=%d status=%d"),cancelled,messageGetStatus.Int());
                if (!rc && cancelled!=KErrCancel) rc=KErrCorrupt;
                if (!rc) Log(_L8("PENDING RECEIVE CLEANUP PASS no_run=1"));
                }
            }
        if (messageGetStatus==KRequestPending || messagePutStatus==KRequestPending)
            {
            Log(_L8("QUARANTINE message pending; no close; reboot required"));
            for (;;) User::After(1000000);
            }
        }
    TBool transfersFinished=inputStatus!=KRequestPending && outputStatus!=KRequestPending;
    if (ringMapped) RingUnmap(lib,object,ringReserved,ringMapped);
    if (nativeRing.Ptr()) {
        TInt ringFree=((TInt(*)(TAny*,TDes8*,TInt))lib.Lookup(29))(object,&nativeRing,2);
        Log(_L8("RING free native=%d"),ringFree); if (!rc && ringFree) rc=ringFree;
        }
    if (!transfersFinished) {
        Log(_L8("native buffers retained: transfer status still pending"));
        if (!rc) rc=KErrTimedOut;
        }
    if (transfersFinished && nativeOut.Ptr()) {
        TInt freeBuffer=((TInt(*)(TAny*,TDes8*,TInt))lib.Lookup(29))(object,&nativeOut,2);
        Log(_L8("free native out=%d"),freeBuffer); if (!rc && freeBuffer) rc=freeBuffer;
        }
    if (transfersFinished && nativeIn.Ptr()) {
        TInt freeBuffer=((TInt(*)(TAny*,TDes8*,TInt))lib.Lookup(29))(object,&nativeIn,2);
        Log(_L8("free native in=%d"),freeBuffer); if (!rc && freeBuffer) rc=freeBuffer;
        }
    channel.SetHandle(0);
    Log(_L8("BEGIN close"));
    ((void(*)(TAny*))lib.Lookup(10))(dcd);
    ((void(*)(TAny*))lib.Lookup(33))(object);
    TInt perfRc=perf.Stop(); if (!rc && perfRc) rc=perfRc;
    if (dmmRing) Log(_L8("RING LIFECYCLE setup_us=%u teardown_us=%u includes_journaling=1 status=%d"),ringSetupUs,Us(ringTeardownBegin),rc);
    if (worker && !rc) Log(_L8("WORKER CLEANUP PASS no_run=1 delete_free_native_close=0"));
    return rc;
    }
GLDEF_C TInt E32Main()
    {
    User::SetJustInTime(EFalse);
    CTrapCleanup* cleanup=CTrapCleanup::New(); if (!cleanup) return KErrNoMemory;
    RFs fs; TInt rc=fs.Connect(); if (rc) { delete cleanup; return rc; }
    rc=logFile.Replace(fs,_L("E:\\c55stream.log"),EFileWrite|EFileStream|EFileShareAny);
    if (rc) { fs.Close(); delete cleanup; return rc; }
    TBuf<128> cmd; User::CommandLine(cmd); cmd.LowerCase();
    TLex options(cmd); TPtrC mode=options.NextToken();
    TBool frameMode=mode==_L("worker-one") || mode==_L("worker-serial") ||
        mode==_L("worker-parallel") || mode==_L("worker-transfer") || mode==_L("worker-wsola") || mode==_L("run-transfer") || mode==_L("run-routing") || mode==_L("dmm-ring") || mode==_L("dmm-ring-native") || mode==_L("dmm-ring-dcr") || mode==_L("dmm-ring-wsola") || mode==_L("dmm-ring-window") || mode==_L("dmm-ring-mdec") || mode==_L("dmm-ring-spu") || mode==_L("dmm-ring-wsola-current");
    TInt reps=(mode==_L("worker-transfer") || mode==_L("run-transfer") || mode==_L("run-routing"))?0:1,packetBytes=mode==_L("worker-wsola")?KWsolaInputBytes:512;
    TInt frames=mode==_L("worker-one")?1:8,batch=1;
    TBool seenReps=EFalse,seenBytes=EFalse,seenFrames=EFalse;
    TPtrC extra;
    while ((extra.Set(options.NextToken()),extra.Length())) {
        TInt at=extra.Locate('=');
        if (at<1) { mode.Set(KNullDesC); break; }
        TPtrC key=extra.Left(at); TLex value(extra.Mid(at+1)); TInt parsed=0;
        if (value.Val(parsed) || !value.Eos()) { mode.Set(KNullDesC); break; }
        if (key==_L("reps") && !seenReps && (frameMode || mode==_L("serial") || mode==_L("parallel"))) {
            reps=parsed; seenReps=ETrue;
            }
        else if (key==_L("bytes") && !seenBytes && frameMode) {
            packetBytes=parsed; seenBytes=ETrue;
            }
        else if (key==_L("frames") && !seenFrames && frameMode) {
            frames=parsed; seenFrames=ETrue;
            }
        else if (key==_L("batch") && (mode==_L("dmm-ring") || mode==_L("dmm-ring-native") || mode==_L("dmm-ring-dcr") || mode==_L("dmm-ring-window") || mode==_L("dmm-ring-mdec"))) { batch=parsed; }
        else if (key==_L("voices") && mode==_L("dmm-ring-spu")) { batch=parsed; }
        else { mode.Set(KNullDesC); break; }
        }
    if (mode==_L("dmm-ring-wsola-current") && (frames>120 || packetBytes!=512 || reps!=1 || batch!=1)) mode.Set(KNullDesC);
    if (batch<1 || (batch>15 && mode!=_L("dmm-ring-spu")) || reps<0 || reps>20000 || packetBytes<512 || packetBytes>4096 ||
        (packetBytes&1) || frames<1 || frames>4096 || (mode==_L("dmm-ring-window") && frames>120) ||
        (mode==_L("dmm-ring-mdec") && (frames>120 || (batch!=1 && batch!=2 && batch!=4) || packetBytes!=512 || reps!=1)) ||
        (mode==_L("dmm-ring-spu") && (frames>120 || (batch!=1 && batch!=8 && batch!=24) || packetBytes!=512 || reps!=1)) ||
        (mode==_L("worker-one") && frames!=1) ||
        (mode==_L("worker-transfer") && reps!=0) ||
        ((mode==_L("run-transfer") || mode==_L("run-routing")) && (packetBytes!=512 || reps!=0)) ||
        (mode==_L("worker-wsola") && (packetBytes!=KWsolaInputBytes || reps>64))) mode.Set(KNullDesC);
    if (mode!=_L("boot-info") && mode!=_L("processor-state") && mode!=_L("inspect") && mode!=_L("base") && mode!=_L("buffers") && mode!=_L("dmm-provenance") && mode!=_L("dmm-map") && mode!=_L("dmm-ring") && mode!=_L("dmm-ring-native") && mode!=_L("dmm-ring-dcr") && mode!=_L("dmm-ring-wsola") && mode!=_L("dmm-ring-window") && mode!=_L("dmm-ring-mdec") && mode!=_L("dmm-ring-spu") && mode!=_L("dmm-ring-wsola-current") &&
        mode!=_L("create") && mode!=_L("info") && mode!=_L("messages") &&
        mode!=_L("receive-created") && mode!=_L("message-stages") && mode!=_L("patcher-check") && mode!=_L("patcher-read-check") &&
        mode!=_L("pointer-snapshot") &&
        mode!=_L("execute") && mode!=_L("serial") &&
        mode!=_L("parallel") && mode!=_L("worker-one") &&
        mode!=_L("worker-serial") && mode!=_L("worker-parallel") &&
        mode!=_L("worker-calibrate") && mode!=_L("worker-transfer") && mode!=_L("worker-wsola") && mode!=_L("run-transfer") && mode!=_L("run-routing") && mode!=_L("native-copy") && mode!=_L("exit-stages") && mode!=_L("worker-message") && mode!=_L("worker-message-queued")) {
        Log(_L8("FINAL status=%d invalid command"),KErrArgument);
        logFile.Close(); fs.Close(); delete cleanup; return KErrArgument;
        }
    TInt hz=0,uid=0; HAL::Get(HALData::EFastCounterFrequency,hz); counterHz=(TUint32)hz;
    HAL::Get(HALData::EMachineUid,uid);
    TBuf<128> fw; TInt fr=SysUtil::GetSWVersion(fw); TBuf8<128> f8; f8.Copy(fw);
    TBuf8<128> cmd8; cmd8.Copy(cmd);
    Log(_L8("C55STREAM v53 command='%S' machine=%08x fast_counter_hz=%u firmware_rc=%d firmware='%S'"),&cmd8,uid,counterHz,fr,&f8);
    if (mode==_L("boot-info")) {
        TInt reason=0,exception=0,fault=0,id=0;
        TExcInfo info; Mem::FillZ(&info,sizeof(info));
        TInt reasonRc=HAL::Get(HALData::ESystemStartupReason,reason);
        TInt exceptionRc=HAL::Get(HALData::ESystemException,exception);
        TInt faultRc=UserHal::FaultReason(fault),idRc=UserHal::ExceptionId(id);
        TInt infoRc=UserHal::ExceptionInfo(info);
        Log(_L8("BOOT HAL startup_rc=%d startup=%d exception_rc=%d exception=%d"),reasonRc,reason,exceptionRc,exception);
        Log(_L8("BOOT USER fault_rc=%d fault=%d id_rc=%d id=%d info_rc=%d code=%08x data=%08x extra=%08x"),
            faultRc,fault,idRc,id,infoRc,(TUint32)info.iCodeAddress,(TUint32)info.iDataAddress,(TUint32)info.iExtraData);
        Log(_L8("BOOT PROBE COMPLETE no_dsp_open=1 no_patcher=1 readonly_HAL=1"));
        rc=KErrNone; // Unsupported getters remain explicit rc values above.
        }
    else if (!counterHz) rc=KErrNotSupported; else rc=Research(mode,reps,(TUint32)uid,packetBytes,frames,batch);
    Log(_L8("FINAL status=%d"),rc);
    logFile.Close(); fs.Close(); delete cleanup; return rc;
    }
