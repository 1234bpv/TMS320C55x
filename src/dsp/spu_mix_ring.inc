/* Exact arithmetic of current ARM mix_chan, including packed-gain sign spill
 * and wrap32 accumulator. Full decode/ADSR/reverb/IRQ stays outside this job. */
static unsigned short spu_ring_word(volatile unsigned short *ring,unsigned int slot,unsigned int at)
{ return ring[512+((slot+at/240)%15)*256+16+at%240]; }
static unsigned long spu_ring_long(volatile unsigned short *ring,unsigned int slot,unsigned int at)
{ return (unsigned long)spu_ring_word(ring,slot,at)|((unsigned long)spu_ring_word(ring,slot,at+1)<<16); }
static long spu_smlaw_product(long sample,short gain)
{
    unsigned long x=(unsigned long)sample<<1;
    long high=(long)(short)(x>>16),low=(long)(unsigned short)x;
    // Split32x16 -> exact signed48 product>>16; each partial fits signed32.
    return high*(long)gain+((low*(long)gain)>>16);
}
static unsigned int ring_spu_exchange(unsigned short *notification,unsigned long *sums)
{
    unsigned long address=(unsigned long)notification[6]|((unsigned long)notification[7]<<16);
    volatile unsigned short *ring=(volatile unsigned short *)address;
    volatile unsigned short *p;
    unsigned int slot=notification[9],voices,inputs,k,j,base,at;
    unsigned long index,number,packed,sample,bits;
    unsigned short value;
    short left,right;
    if (!address || address>=0x00800000UL || slot>=15) return 1;
    voices=ring[6];
    if ((voices!=1 && voices!=8 && voices!=24) || ring[7]!=64) return 2;
    inputs=(256+voices*132+239)/240;
    if (ring[0]!=0xd16a || ring[1]!=42 || ring[2]!=inputs || ring[3]!=slot || notification[10]!=inputs) return 3;
    index=(unsigned long)ring[4]|((unsigned long)ring[5]<<16);
    for (k=0;k<inputs;++k) {
        number=index+k; p=ring+512+((slot+k)%15)*256;
        for (j=0;j<16;++j) {
            value=0;
            if (j==0) value=0xc55a; if (j==1) value=(unsigned short)(65520UL+number); if (j==2) value=256;
            if (j==3) value=(unsigned short)(number/15); if (j==4) value=(unsigned short)number; if (j==5) value=(unsigned short)(number>>16);
            if (p[j]!=value) return 4;
        }
        for (j=16;j<256;++j) if (k*240+j-16>=256+voices*132 && p[j]) return 5;
    }
    for (j=0;j<128;++j) sums[j]=spu_ring_long(ring,slot,j*2);
    for (k=0;k<voices;++k) {
        base=256+k*132;
        packed=(spu_ring_long(ring,slot,base+128)|(spu_ring_long(ring,slot,base+130)<<16))<<1;
        left=(short)packed; right=(short)(packed>>16);
        for (j=0;j<64;++j) {
            sample=spu_ring_long(ring,slot,base+j*2);
            sums[j*2]+=(unsigned long)spu_smlaw_product((long)sample,left);
            sums[j*2+1]+=(unsigned long)spu_smlaw_product((long)sample,right);
        }
    }
    for (k=0;k<2;++k) {
        number=index+k; p=ring+4352+((slot+k)%15)*256;
        for (j=0;j<256;++j) p[j]=0;
        p[0]=0xc55b; p[1]=(unsigned short)(65520UL+number); p[2]=256;
        p[3]=(unsigned short)(number/15); p[4]=(unsigned short)number; p[5]=(unsigned short)(number>>16);
    }
    for (j=0;j<128;++j) {
        at=j*2; bits=sums[j]; p=ring+4352+((slot+at/240)%15)*256+16+at%240;
        p[0]=(unsigned short)bits; p[1]=(unsigned short)(bits>>16);
    }
    ring[256]=0xd16b; ring[257]=notification[1]; ring[258]=inputs; ring[259]=slot; ring[260]=2;
    return 0;
}
