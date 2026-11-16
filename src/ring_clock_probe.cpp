// E90 stock-clock snapshot using the captured RPDomain v2.3 driver API.
// The build stages the existing engine with copy102/free-shadow104. There is
// no command-line path to change clocks or start a DSP task.
#include <e32base.h>
#include <f32file.h>
#include <hal.h>
#include <sysutil.h>
#include "ocengine.h"

static RFile journal;
static void Log(TRefByValue<const TDesC8> fmt,...)
    {
    VA_LIST list; VA_START(list,fmt);
    TBuf8<512> line; line.AppendFormatList(fmt,list); VA_END(list);
    line.Append(_L8("\r\n")); journal.Write(line); journal.Flush();
    }
static TInt SnapshotL()
    {
    TInt uid=0,hal=0;
    HAL::Get(HALData::EMachineUid,uid); HAL::Get(HALData::ECPUSpeed,hal);
    TBuf<256> firmware; TInt fw=SysUtil::GetSWVersion(firmware);
    Log(_L8("RINGCLOCK v1 machine=%08x driver=RDomain.ldd copy_control=102 free_shadow_control=104"),uid);
    Log(_L8("ECPUSpeed(kHz) = %d"),hal);
    if (uid!=0x20002496 || fw || firmware.Find(_L("400.34.93"))==KErrNotFound ||
        firmware.Find(_L("RA-6"))==KErrNotFound) return KErrNotSupported;
    Log(_L8("RINGCLOCK firmware_guard=0 profile=RA-6/400.34.93"));
    COcEngine* engine=COcEngine::NewL();
    CleanupStack::PushL(engine); engine->SetProfile(KProfileE90);
    TInt rc=engine->Prepare();
    Log(_L8("RINGCLOCK prepare=%d failed_step=%d"),rc,engine->FailedAt());
    if (!rc) {
        const TUint32 addresses[]={KRegClkSel1Pll,KRegClkSel2Pll,KRegClkSelMpu,KRegClkSel1Core,
            KRegFclkenDsp,KRegIclkenDsp,KRegIdlestDsp,KRegClkSelDsp};
        const TUint32 expected[]={0x00056400u,2u,2u,0x04360626u,0x401u,2u,0u,0x343u};
        const char* names[]={"CM_CLKSEL1_PLL","CM_CLKSEL2_PLL","CM_CLKSEL_MPU","CM_CLKSEL1_CORE",
            "CM_FCLKEN_DSP","CM_ICLKEN_DSP","CM_IDLEST_DSP","CM_CLKSEL_DSP"};
        TUint32 values[8]={0,0,0,0,0,0,0,0};
        rc=engine->ReadRegs(addresses,values,8);
        Log(_L8("RINGCLOCK read_regs=%d single_snapshot=1 prcm_writes=0 dsp_open=0"),rc);
        for (TInt i=0;i<8;++i) {
            TPtrC8 name((const TUint8*)names[i]);
            Log(_L8("RINGCLOCK REG %S address=%08x value=%08x expected=%08x"),&name,addresses[i],values[i],expected[i]);
            if (values[i]!=expected[i]) rc=KErrCorrupt;
            }
        TInt restore=engine->EndPatchSession(),verified=engine->VerifyRestored();
        Log(_L8("RINGCLOCK restore=%d original_body_verified=%d"),restore,verified);
        if (restore || verified!=1) rc=KErrCorrupt;
        if (!rc) {
            TUint32 core=((values[0]>>12)&0x7ff)*19200u/5u*2u;
            Log(_L8("RINGCLOCK FREQUENCY core_khz=%u arm_khz=%u bus_khz=%u dsp_khz=%u"),
                core,core/(values[2]&31),core/(values[3]&15),core/(values[7]&15));
            Log(_L8("RINGCLOCK PASS stock=1 compatible_driver_api=1 prcm_writes=0 dsp_open=0"));
            }
        }
    CleanupStack::PopAndDestroy(engine);
    return rc;
    }
static void RunL()
    {
    RFs fs; User::LeaveIfError(fs.Connect()); CleanupClosePushL(fs);
    User::LeaveIfError(journal.Replace(fs,_L("E:\\ocprobe.log"),EFileWrite));
    CleanupClosePushL(journal);
    TRAPD(error, { TInt rc=SnapshotL(); Log(_L8("FINAL status=%d"),rc); });
    if (error) Log(_L8("FINAL status=%d"),error);
    CleanupStack::PopAndDestroy(2,&fs);
    }
TInt E32Main()
    {
    CTrapCleanup* cleanup=CTrapCleanup::New(); if (!cleanup) return KErrNoMemory;
    TRAPD(error,RunL()); delete cleanup;
    return error;
    }
