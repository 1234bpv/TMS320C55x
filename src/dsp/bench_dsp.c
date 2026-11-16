/*
 * bench_dsp.c - benchmark compute core for TMS320C55x.
 *
 * The same three Q15 kernels as the ARM side (src/dsptest.cpp), size-agnostic:
 * buffers and lengths arrive from ARM via shared memory (node message), so
 * there is no data generation and no dependency on dspbench.h here - just the
 * arithmetic. This is the future body of the dspbridge node execute phase
 * (template: the ping node).
 *
 * C55x type note (CGT 4.4.1): char/int = 16 bits, long = 32 bits, accumulators
 * AC0..AC3 = 40 bits. Therefore:
 *   - loop counters `int` (our n <= 8192 < 32767) are fine;
 *   - the wide accumulator is `long` (32-bit), held by the compiler in a 40-bit
 *     AC register;
 *   - result/checksum are returned as 32-bit (`long`) to match the ARM side's
 *     32-bit reduction.
 *
 * Verified: cl55 -v5510 -o3 emits RPT + MACM for dot/FIR.
 * ASCII only: old cl55 preprocessor chokes on non-ASCII bytes.
 */

/* Q15 dot-product: sum(a[i]*b[i]) in a 40-bit AC, return low 32 bits.
 * C55x showcase: the inner loop collapses to RPT CSR / MACM. */
long dsp_q15_dot(const short *a, const short *b, int n)
{
    long acc = 0;
    int i;
    for (i = 0; i < n; i++)
        acc += (long)a[i] * (long)b[i];
    return acc;
}

/* Q15 FIR: y[k] = (sum_t h[t]*x[k+t]) >> 15, returns the sum of outputs
 * (checksum). nsamp output samples, ntaps coefficients; x has length
 * nsamp+ntaps. */
long dsp_q15_fir(const short *x, const short *h, int nsamp, int ntaps)
{
    long chk = 0;
    int k, t;
    for (k = 0; k < nsamp; k++)
    {
        long acc = 0;
        for (t = 0; t < ntaps; t++)
            acc += (long)h[t] * (long)x[k + t];
        chk += (short)(acc >> 15);
    }
    return chk;
}

/* Neutral 16-bit integer: sum( (short)(a[i]*3 + 7) ). Outside the DSP's strong
 * suit - a control that shows where dual-MAC does not help. */
long dsp_blk(const short *a, int n)
{
    long acc = 0;
    int i;
    for (i = 0; i < n; i++)
        acc += (short)((short)(a[i] * 3) + 7);
    return acc;
}
