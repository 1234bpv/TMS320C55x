#include "kernel.h"
typedef unsigned int u32;
typedef unsigned char u8;
static struct { int Mdec; } Config;
#define HAVE_ARMV6 1
#include "kernel_arm.inc"

void mdec_kernel_process(mdec_s32* coefficients,const unsigned short* used_columns,
                         mdec_u32* packed_rgb24,unsigned short black_white)
    {
    int block;
    Config.Mdec=black_white!=0;
    for (block=0;block<6;++block)
        idct(coefficients+block*64,(short)used_columns[block]);
    yuv2rgb24(coefficients,(u8*)packed_rgb24);
    }
