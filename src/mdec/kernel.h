#ifndef C55_MDEC_KERNEL_H
#define C55_MDEC_KERNEL_H
#ifdef MDEC_C55_TARGET
typedef long mdec_s32;
typedef unsigned long mdec_u32;
typedef char mdec_width_check[(sizeof(long)==2 && sizeof(short)==1) ? 1 : -1];
#else
typedef int mdec_s32;
typedef unsigned int mdec_u32;
typedef char mdec_width_check[(sizeof(int)==4 && sizeof(short)==2) ? 1 : -1];
#endif
#ifdef __cplusplus
extern "C" {
#endif
// Mutates 384 pre-IDCT coefficients; output is 192 packed 32-bit RGB24 words.
void mdec_kernel_process(mdec_s32* coefficients,const unsigned short* used_columns,
                         mdec_u32* packed_rgb24,unsigned short black_white);
#ifndef MDEC_C55_TARGET
void mdec_kernel_process_arm463(mdec_s32*,const unsigned short*,mdec_u32*,unsigned short);
#endif
#ifdef __cplusplus
}
#endif
#endif
