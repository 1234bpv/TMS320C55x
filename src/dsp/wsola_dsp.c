/* Exact PS1 coarse/refine search, with stereo deinterleave and >>6 already
 * performed by ARM. C55 int=16, long=32. Scores are bounded by 220*512*512.
 * Separate from the stereo ARM reference; dot emits contiguous RPT/MACM. */
extern long dsp_q15_dot(const short *, const short *, int);

long dsp_wsola_best(const short *tmpl, const short *search,
    unsigned short *offset, unsigned short *scored)
{
    long best=0,sum;
    int off,bestoff=0,have=0,lo,hi,count=0;
    for (off=0;off<441;off+=4) {
        sum=dsp_q15_dot(tmpl,search+off,220); ++count;
        if (!have || sum>best) { best=sum; bestoff=off; have=1; }
    }
    lo=bestoff-4; if (lo<0) lo=0;
    hi=bestoff+4; if (hi>440) hi=440;
    for (off=lo;off<=hi;++off) {
        if ((off&3)==0) continue;
        sum=dsp_q15_dot(tmpl,search+off,220); ++count;
        if (sum>best) { best=sum; bestoff=off; }
    }
    *offset=(unsigned short)bestoff; *scored=(unsigned short)count;
    return best;
}
