// Separate user-mode calibration. No DSP, patcher, PRCM or performance channel.
#include <e32base.h>
#include <f32file.h>
#include <hal.h>

static TUint32 counterHz;
static volatile TUint32 sink=1;
struct TSample {
    TInt repeat,sleep,yield,requested,beforeRc,afterRc;
    TUint32 innerTicks,outerTicks,tickDelta;
    TInt64 utcUs,cpuBefore,cpuAfter;
    };
static TSample samples[36];

static void Busy(TInt us)
    {
    TUint32 begin=User::FastCounter();
    TUint32 ticks=(TUint32)(((TUint64)us*counterHz+999999)/1000000);
    do { sink=sink*1664525u+1013904223u; }
    while (User::FastCounter()-begin<ticks);
    }

static TInt Probe(RFile& log)
    {
    TInt hz=0,uid=0;
    TInt rc=HAL::Get(HALData::EFastCounterFrequency,hz);
    if (rc || hz<=0) return rc?rc:KErrCorrupt;
    rc=HAL::Get(HALData::EMachineUid,uid);
    if (rc || uid!=0x20002d84) return rc?rc:KErrNotSupported;
    counterHz=(TUint32)hz;
    TInt count=0;
    const TInt durations[]={1000,10000,200000};
    for (TInt repeat=0;repeat<3;++repeat) {
        for (TInt duration=0;duration<3;++duration) {
            for (TInt sleep=0;sleep<2;++sleep) {
                for (TInt yield=0;yield<2;++yield) {
                    TSample& s=samples[count++];
                    s.repeat=repeat; s.sleep=sleep; s.yield=yield; s.requested=durations[duration];
                    // Prime before the CPU baseline to expose delayed slice accounting.
                    Busy(20000);
                    if (yield) User::After(1);
                    TTime utcBegin,utcEnd;
                    utcBegin.UniversalTime();
                    TUint32 outerBegin=User::FastCounter(),tickBegin=User::NTickCount();
                    TTimeIntervalMicroSeconds cpuBefore,cpuAfter;
                    s.beforeRc=RThread().GetCpuTime(cpuBefore);
                    TUint32 innerBegin=User::FastCounter();
                    if (sleep) User::After(s.requested); else Busy(s.requested);
                    if (yield) User::After(1); // Included in both timing windows.
                    s.innerTicks=User::FastCounter()-innerBegin;
                    s.afterRc=RThread().GetCpuTime(cpuAfter);
                    s.outerTicks=User::FastCounter()-outerBegin;
                    s.tickDelta=User::NTickCount()-tickBegin;
                    utcEnd.UniversalTime();
                    s.utcUs=utcEnd.MicroSecondsFrom(utcBegin).Int64();
                    s.cpuBefore=cpuBefore.Int64(); s.cpuAfter=cpuAfter.Int64();
                    if (s.beforeRc || s.afterRc) rc=KErrNotSupported;
                    }
                }
            }
        }
    // Write only after all timing samples; no file I/O within their windows.
    TBuf8<512> line;
    line.Format(_L8("COUNTERPROBE v1 machine=%08x fast_counter_hz=%u samples=%d prime_busy_us=20000 no_dsp=1 no_patcher=1 no_performance_reservation=1\r\n"),uid,counterHz,count);
    TInt ioRc=log.Write(line);
    for (TInt i=0;i<count && !ioRc;++i) {
        const TSample& s=samples[i];
        line.Format(_L8("CPU SAMPLE index=%d repeat=%d sleep=%d boundary_yield=%d requested_us=%d inner_ticks=%u outer_ticks=%u nticks=%u utc_us=%d before_rc=%d after_rc=%d before_hi=%08x before_lo=%08x after_hi=%08x after_lo=%08x\r\n"),
            i,s.repeat,s.sleep,s.yield,s.requested,s.innerTicks,s.outerTicks,s.tickDelta,(TInt)s.utcUs,s.beforeRc,s.afterRc,
            (TUint32)(s.cpuBefore>>32),(TUint32)s.cpuBefore,(TUint32)(s.cpuAfter>>32),(TUint32)s.cpuAfter);
        ioRc=log.Write(line);
        }
    line.Format(_L8("FINAL status=%d sink=%08x\r\n"),rc,sink);
    if (!ioRc) ioRc=log.Write(line);
    if (!ioRc) ioRc=log.Flush();
    return ioRc?ioRc:rc;
    }

GLDEF_C TInt E32Main()
    {
    User::SetJustInTime(EFalse);
    CTrapCleanup* cleanup=CTrapCleanup::New();
    if (!cleanup) return KErrNoMemory;
    RFs fs;
    TInt rc=fs.Connect();
    RFile log;
    if (!rc) rc=log.Replace(fs,_L("E:\\counterprobe.log"),EFileWrite|EFileShareAny);
    if (!rc) rc=Probe(log);
    log.Close(); fs.Close(); delete cleanup;
    return rc;
    }
