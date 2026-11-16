#include "mix.h"
void spu_mix_job_arm(spu_s32* sums,const spu_s32* samples,const spu_s32* volumes,int voices)
{
    int v;
    for (v=0;v<voices;++v)
        spu_mix_chan_arm(sums,64,volumes[v*2],volumes[v*2+1],samples+v*64);
}
