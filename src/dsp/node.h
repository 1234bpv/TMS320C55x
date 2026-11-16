/*
 * node.h - minimal dspbridge node interface for TMS320C55x.
 *
 * Nothing here is defined by us. These symbols are exported by the DSP/BIOS
 * base image (baseimage.dof) and resolved by the dynamic loader when the node
 * is loaded, so they are extern decls only.
 *
 * IMPORTANT: every symbol below was checked against the base image's own DOFF
 * symbol table (1678 symbols, DLLdump of baseimage.dof) - an extern this base
 * does not export makes the node fail to load with "Undefined external
 * symbol". See docs/findings.md 15.3.
 *
 * Message model: standard dspbridge three 32-bit words {cmd, arg_1, arg_2}
 * (verified against felipec/dsp-dummy node.h and ROM node symbols).
 * On C55x, 32-bit == unsigned long.
 *
 * ASCII only: the old cl55 (v4.4.1) preprocessor chokes on non-ASCII bytes.
 */

#ifndef DSP_NODE_H
#define DSP_NODE_H

typedef struct {
    unsigned long cmd;
    unsigned long arg_1;
    unsigned long arg_2;
} dsp_msg_t;

/* Node<->ARM messaging via RMS/mailbox. Present in the base. */
extern unsigned short NODE_getMsg(void *env, dsp_msg_t *msg, unsigned int timeout);
extern unsigned short NODE_putMsg(void *env, void *dest, dsp_msg_t *msg, unsigned int timeout);

/*
 * DSP/BIOS high-resolution clock - our DSP-side instrument, the second
 * independent measurement the plan (Phase 4) requires next to the ARM-side
 * FastCounter.
 *
 *   CLK_gethtime()   raw high-resolution timer count
 *   CLK_countspms()  base image's configured counts per millisecond
 *
 * Physical v17 probes on N95/E90 give about 19.2 MHz over short intervals,
 * whereas CLK_countspms returns 164. An 800-ms idle interval advances the
 * DSP counter by only about 500 ms at that short-interval rate. Do not
 * assume a continuously running wall clock or convert ticks using 164.
 * See docs/STREAM_RESEARCH.md and the v17 calibration journals.
 *
 * Both are exported by this base image. Return type is DSP/BIOS LgUns = 32-bit
 * = `unsigned long` on C55x.
 *
 * NOTE - no BCACHE here on purpose. The C55x has an instruction cache only
 * (the base exports _ENABLEICACHE / _ICache_Flush and no BCACHE_* at all), so
 * there is no DSP-side data cache to maintain over shared buffers; ARM-side
 * coherency is handled by ebridgeutil's clean/flush (findings 9.2). An earlier
 * revision of this header declared BCACHE_inv/BCACHE_wbInv copied from the
 * C64x-oriented dsp-dummy sample - that would have made the node unloadable.
 */
extern unsigned long CLK_gethtime(void);
extern unsigned long CLK_countspms(void);

#endif /* DSP_NODE_H */
