#define MDEC_C55_TARGET 1
#include "kernel.h"
typedef unsigned long u32;
typedef unsigned short u8;
static struct { long Mdec; } Config;
// Preserve ARM int32 arithmetic; C55 int itself is16 bits.
#define int long
#include "kernel_c55.inc"
#undef int

void mdec_kernel_process(mdec_s32* coefficients,const unsigned short* used_columns,
                         mdec_u32* packed_rgb24,unsigned short black_white)
    {
    int block;
    Config.Mdec=black_white!=0;
    for (block=0;block<6;++block)
        idct(coefficients+block*64,(short)used_columns[block]);
    yuv2rgb24(coefficients,(u8*)packed_rgb24);
    }
