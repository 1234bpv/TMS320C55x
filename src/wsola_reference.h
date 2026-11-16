#ifndef WSOLA_REFERENCE_H
#define WSOLA_REFERENCE_H
#include <e32std.h>
struct TWsolaResult { TInt offset,scored; TInt32 score; };
TWsolaResult WsolaReference(const TInt16 *tmpl,const TInt16 *search);
TInt WsolaBestOffsetOriginal(const TInt16 *tmpl,const TInt16 *search);
TInt WsolaBestOffsetCurrent(const TInt16 *tmpl,const TInt16 *search,TInt length,TInt range);
void WsolaDataset(TInt sequence,TInt16 *tmpl,TInt16 *search);
enum { KWsolaLength=220, KWsolaSearch=660, KWsolaCases=8,
       KWsolaInputBytes=1792, KWsolaOutputBytes=48, KWsolaArmIterations=16 };
#endif
