// Exact local PS1Emulator WSOLA snapshot; exported entry name only changed.
static TUint32 g_wsTmplW[KWsolaHop / 2];
static TUint32 g_wsSearchA[(KWsolaRange + KWsolaHop) / 2 + 1];
static TUint32 g_wsSearchB[(KWsolaRange + KWsolaHop) / 2 + 1];

#if defined(__GNUC__) && defined(__arm__)
#define WSOLA_SMLAD(aAcc, aX, aY) \
	__asm__("smlad %0, %1, %2, %0" : "+r"(aAcc) : "r"(aX), "r"(aY))
#else
// Portable model of ARMv6 SMLAD (two signed 16x16 products added to a 32-bit accumulator).
#define WSOLA_SMLAD(aAcc, aX, aY) \
	((aAcc) += (TInt32)(TInt16)(aX) * (TInt32)(TInt16)(aY) + \
	           (TInt32)(TInt16)((aX) >> 16) * (TInt32)(TInt16)((aY) >> 16))
#endif

static TInt32 WsolaDot(const TUint32 *aT, const TUint32 *aC, TInt aWords)
	{
	TInt32 s0 = 0, s1 = 0;         // two accumulators hide the smlad result latency
	for (; aWords >= 4; aWords -= 4, aT += 4, aC += 4)
		{
		WSOLA_SMLAD(s0, aT[0], aC[0]);
		WSOLA_SMLAD(s1, aT[1], aC[1]);
		WSOLA_SMLAD(s0, aT[2], aC[2]);
		WSOLA_SMLAD(s1, aT[3], aC[3]);
		}
	for (; aWords > 0; aWords--)
		WSOLA_SMLAD(s0, *aT++, *aC++);
	return s0 + s1;
	}

TInt WsolaBestOffsetCurrent(const TInt16 *aTmpl, const TInt16 *aSearch, TInt aLen, TInt aRange)
	{
	__ASSERT_ALWAYS(aLen <= KWsolaHop && !(aLen & 1) && aRange <= KWsolaRange, User::Invariant());
	const TInt words = aLen / 2;
	for (TInt k = 0; k < words; k++)
		g_wsTmplW[k] = ((TUint32)(aTmpl[k * 4] >> 6) & 0xFFFF) | ((TUint32)(aTmpl[k * 4 + 2] >> 6) << 16);

	const TInt frames = aRange + aLen - 1;
	TInt v0 = aSearch[0] >> 6;
	for (TInt k = 0; k * 2 < frames; k++)
		{
		const TInt v1 = (k * 2 + 1 < frames) ? (aSearch[(k * 2 + 1) * 2] >> 6) : 0;
		const TInt v2 = (k * 2 + 2 < frames) ? (aSearch[(k * 2 + 2) * 2] >> 6) : 0;
		g_wsSearchA[k] = ((TUint32)v0 & 0xFFFF) | ((TUint32)v1 << 16);
		g_wsSearchB[k] = ((TUint32)v1 & 0xFFFF) | ((TUint32)v2 << 16);
		v0 = v2;
		}

	TInt bestOff = 0;
	TInt32 bestSum = 0;
	TBool have = EFalse;
	for (TInt off = 0; off < aRange; off += 4)
		{
		const TInt32 sum = WsolaDot(g_wsTmplW, g_wsSearchA + (off >> 1), words);
		if (!have || sum > bestSum)
			{ bestSum = sum; bestOff = off; have = ETrue; }
		}
	TInt lo = bestOff - 4; if (lo < 0) lo = 0;
	TInt hi = bestOff + 4; if (hi > aRange - 1) hi = aRange - 1;
	for (TInt off = lo; off <= hi; off++)
		{
		if ((off & 3) == 0)
			continue;              // already scored in the coarse pass
		const TUint32 *cand = ((off & 1) ? g_wsSearchB : g_wsSearchA) + (off >> 1);
		const TInt32 sum = WsolaDot(g_wsTmplW, cand, words);
		if (sum > bestSum)
			{ bestSum = sum; bestOff = off; }
		}
	return bestOff;
	}
