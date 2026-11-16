// Arithmetic and traversal of PS1Emulator's WsolaBestOffset (220/441).
// Stereo left channel and >>6 stay inside the inner loop for the ARM baseline.
#include "wsola_reference.h"

// Timed baseline: original return value and inner loops, without score/count
// instrumentation. Kept in a separate translation unit to prevent hoisting.
TInt WsolaBestOffsetOriginal(const TInt16 *tmpl,const TInt16 *search)
    {
    TInt bestOff=0; TInt32 bestSum=0; TBool have=EFalse;
    for (TInt off=0;off<441;off+=4) {
        const TInt16 *cand=search+off*2; TInt32 sum=0;
        for (TInt i=0;i<220;++i)
            sum+=(TInt32)(tmpl[i*2]>>6)*(TInt32)(cand[i*2]>>6);
        if (!have || sum>bestSum) { bestSum=sum; bestOff=off; have=ETrue; }
        }
    TInt lo=bestOff-4; if (lo<0) lo=0;
    TInt hi=bestOff+4; if (hi>440) hi=440;
    for (TInt off=lo;off<=hi;++off) {
        if ((off&3)==0) continue;
        const TInt16 *cand=search+off*2; TInt32 sum=0;
        for (TInt i=0;i<220;++i)
            sum+=(TInt32)(tmpl[i*2]>>6)*(TInt32)(cand[i*2]>>6);
        if (sum>bestSum) { bestSum=sum; bestOff=off; }
        }
    return bestOff;
    }

TWsolaResult WsolaReference(const TInt16 *tmpl,const TInt16 *search)
    {
    TWsolaResult result; result.offset=0; result.score=0; result.scored=0;
    TBool have=EFalse;
    for (TInt off=0;off<441;off+=4) {
        const TInt16 *cand=search+off*2;
        TInt32 sum=0;
        for (TInt i=0;i<220;++i)
            sum+=(TInt32)(tmpl[i*2]>>6)*(TInt32)(cand[i*2]>>6);
        ++result.scored;
        if (!have || sum>result.score) {
            result.score=sum; result.offset=off; have=ETrue;
            }
        }
    TInt lo=result.offset-4; if (lo<0) lo=0;
    TInt hi=result.offset+4; if (hi>440) hi=440;
    for (TInt off=lo;off<=hi;++off) {
        if ((off&3)==0) continue;
        const TInt16 *cand=search+off*2;
        TInt32 sum=0;
        for (TInt i=0;i<220;++i)
            sum+=(TInt32)(tmpl[i*2]>>6)*(TInt32)(cand[i*2]>>6);
        ++result.scored;
        if (sum>result.score) { result.score=sum; result.offset=off; }
        }
    return result;
    }

void WsolaDataset(TInt sequence,TInt16 *tmpl,TInt16 *search)
    {
    const TInt which=(sequence-1)%8;
    TUint32 seed=0x87654321u+(TUint32)((sequence-1)/8)*0x1020304u;
    // Same 881-frame stereo LCG layout as sndSymbianWsolaBench. Search uses
    // frames0..659; frame660 is the original gap; template uses661..880.
    for (TInt i=0;i<1762;++i) {
        seed=seed*1103515245u+12345u;
        TInt16 value=(TInt16)(seed>>16);
        if (i<1320) search[i]=value;
        else if (i>=1322) tmpl[i-1322]=value;
        }
    if (!which) return;
    // Right channels retain independent random data and must be ignored.
    for (TInt i=0;i<220;++i) tmpl[i*2]=0;
    for (TInt i=0;i<660;++i) search[i*2]=0;
    if (which==2 || which==3) {
        for (TInt i=0;i<220;++i) tmpl[i*2]=32767;
        for (TInt i=0;i<660;++i) search[i*2]=which==2?32767:-32768;
        }
    else if (which>=4) {
        tmpl[110*2]=32767;
        if (which==4) search[111*2]=32767; // refine to offset1
        if (which==5) { search[546*2]=16000; search[549*2]=32767; } //439
        if (which==6) search[550*2]=32767; // last coarse offset440
        if (which==7) { search[114*2]=32767; search[111*2]=32767; } //tie:4
        }
    }
