#ifndef C55_SPU_MIX_H
#define C55_SPU_MIX_H
typedef int spu_s32;
typedef unsigned int spu_u32;
typedef char spu_widths[(sizeof(int)==4 && sizeof(short)==2)?1:-1];
#ifdef __cplusplus
extern "C" {
#endif
// The first four arguments preserve the current mix_chan ABI; source is fifth.
void spu_mix_chan_arm(spu_s32* sums,int count,int left,int right,const spu_s32* source);
void spu_mix_job_arm(spu_s32* sums,const spu_s32* samples,const spu_s32* volumes,int voices);
#ifdef __cplusplus
}
#endif
#endif
