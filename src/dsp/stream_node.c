/* Minimal C55x stream node. Interfaces checked against TI strm.h/rms_sh.h
 * and the device's STRMCOPY_TI disassembly. One instance per process.
 * C55x char/short/int are 16 bits; long and RMS_WORD are 32 bits. */
#include <stddef.h>
#include "node.h"
#ifdef EXEC_DMM_MDEC
#include "mdec/kernel.h"
#endif
#if defined(CREATE_WORKER_ONCE) || defined(CREATE_WORKER_PARKED) || defined(CREATE_STREAM_WORKER)
#include "bios_task.h"
#endif
#ifdef CREATE_RESIDENT_CHECK
extern volatile unsigned long resident_cookie;
unsigned long STREAM_DSP_delete(void *env);
#endif
typedef struct { int nbufs, segid, align; unsigned int timeout; } stream_attrs;
typedef struct {
    unsigned long size, nbufs, segid, align, timeout;
    char name[1];
} stream_def;
extern void *STRM_create(char *, int, unsigned long, stream_attrs *);
extern void *STRM_allocateBuffer(void *, unsigned long);
extern int STRM_issue(void *, void *, unsigned long, unsigned long, void *);
extern long STRM_reclaim(void *, void **, unsigned long *, void **);
extern int STRM_idle(void *, int);
extern int STRM_delete(void *);
extern int STRM_freeBuffer(void *, void *, unsigned long);
extern unsigned int NODE_wait(void *, void **, unsigned int, unsigned int,
    unsigned int *);
extern void *MEM_valloc(int, unsigned int, unsigned int, char);
extern int MEM_free(int, void *, unsigned int);
extern long dsp_q15_dot(const short *, const short *, int);
extern long dsp_wsola_best(const short *,const short *,unsigned short *,unsigned short *);
#ifdef EXEC_DMM_DCR_READ
extern unsigned short ring_read_dcr(void);
#endif

/* Firmware STRMCOPY uses env->moreEnv at word offset 12. Its create,
 * execute and delete all use that context. Do not depend on phase-local BSS. */
typedef struct { unsigned short message[12]; void *moreEnv; } node_env;
typedef struct {
    void *input, *output;
    unsigned short *inbuf, *outbuf;
    unsigned long insize, outsize;
    int input_pending,output_pending;
    short coefficients[240];
#ifdef EXEC_DMM_WSOLA
    short ring_audio[880];
#endif
#ifdef EXEC_DMM_MDEC
    long mdec_coefficients[384];
    unsigned long mdec_rgb[192];
    unsigned short mdec_used[6];
#endif
#ifdef EXEC_DMM_SPU
    unsigned long spu_sums[128];
#endif
#if defined(CREATE_WORKER_ONCE) || defined(CREATE_WORKER_PARKED) || defined(CREATE_STREAM_WORKER)
    volatile unsigned int worker_seen;
    volatile unsigned long worker_cookie;
#endif
#ifdef CREATE_WORKER_PARKED
    void *worker_task,*worker_gate;
    volatile int worker_wait;
#endif
#ifdef CREATE_STREAM_WORKER
    void *worker_task,*worker_done;
    volatile int worker_stop;
    volatile unsigned long worker_status,worker_frames;
    volatile unsigned int worker_last_stop;
#ifdef CREATE_WORKER_MSG
    void *worker_env;
#endif
#endif
#ifdef CREATE_RESIDENT_CHECK
    unsigned long resident_delete_address;
#endif
} stream_context;
typedef char env_offset_check[offsetof(node_env, moreEnv)==12 ? 1 : -1];

static void put32(unsigned short *b, int offset, unsigned long value)
{ b[offset] = (unsigned short)value; b[offset+1] = (unsigned short)(value >> 16); }

#ifdef EXEC_DMM_RING
/* The notification stream owns the hand-off of the entire 16KiB region.
 * ARM does not touch any ring line until the output notification completes.
 * Mapped byte addresses are divided by two on the ARM for C55x word pointers. */
static unsigned int ring_exchange(unsigned short *notification,unsigned short *debug)
{
    unsigned long address=(unsigned long)notification[6] | ((unsigned long)notification[7]<<16);
    volatile unsigned short *ring=(volatile unsigned short *)address;
    unsigned int slot=notification[9],batch=notification[10],k,j;
    unsigned long index;
    unsigned short seq,generation,value;
    volatile unsigned short *input,*output;
    if (!address || address>=0x00800000UL || slot>=15 || !batch || batch>15) return 1;
    for (j=0;j<8;++j) debug[j]=ring[j];
    debug[8]=(unsigned short)address; debug[9]=(unsigned short)(address>>16);
    if (ring[0]!=0xd16a || ring[1]!=38 || ring[2]!=batch || ring[3]!=slot) return 2;
    index=(unsigned long)ring[4] | ((unsigned long)ring[5]<<16);
    for (k=0;k<batch;++k) {
        seq=(unsigned short)(65520UL+index+k); generation=(unsigned short)((index+k)/15);
        input=ring+512+((slot+k)%15)*256;
        output=ring+4352+((slot+k)%15)*256;
        for (j=0;j<256;++j) {
            value=j<16?0:(unsigned short)(j*137u+seq*31u);
            if (j==0) value=0xc55a;
            if (j==1) value=seq;
            if (j==2) value=256;
            if (j==3) value=generation;
            if (j==4) value=(unsigned short)(index+k);
            if (j==5) value=(unsigned short)((index+k)>>16);
            if (input[j]!=value) return 3;
            if (j==0) output[j]=0xc55b;
            else output[j]=j<16?value:(unsigned short)(value*3u+seq);
        }
    }
    ring[256]=0xd16b; ring[257]=notification[1]; ring[258]=batch; ring[259]=slot;
    return 0;
}
#endif

#ifdef EXEC_DMM_SPU
#include "spu_mix_ring.inc"
#endif
#ifdef EXEC_DMM_MDEC
static unsigned short mdec_input_word(volatile unsigned short *ring,unsigned int slot,unsigned int at)
{
    return ring[512+((slot+at/240)%15)*256+16+at%240];
}
/* Six int32 IDCT blocks followed by RGB24 for each macroblock. Serialization
 * is explicit low/high16; scratch lives in the node's allocated context. */
static unsigned int ring_mdec_exchange(unsigned short *notification,stream_context *s)
{
    unsigned long address=(unsigned long)notification[6] | ((unsigned long)notification[7]<<16);
    volatile unsigned short *ring=(volatile unsigned short *)address;
    unsigned int slot=notification[9],macros,k,j,inputs,outputs,at,base;
    unsigned long index,number,bits;
    unsigned short value,seq,generation,bw;
    volatile unsigned short *input,*output;
    if (!address || address>=0x00800000UL || slot>=15) return 1;
    macros=ring[6];
    if (macros!=1 && macros!=2 && macros!=4) return 2;
    inputs=(775*macros+239)/240; outputs=(384*macros+239)/240;
    if (ring[0]!=0xd16a || ring[1]!=41 || ring[2]!=inputs || ring[3]!=slot || notification[10]!=inputs) return 3;
    index=(unsigned long)ring[4] | ((unsigned long)ring[5]<<16);
    for (k=0;k<inputs;++k) {
        number=index+k; seq=(unsigned short)(65520UL+number); generation=(unsigned short)(number/15);
        input=ring+512+((slot+k)%15)*256;
        for (j=0;j<16;++j) {
            value=0;
            if (j==0) value=0xc55a; if (j==1) value=seq; if (j==2) value=256;
            if (j==3) value=generation; if (j==4) value=(unsigned short)number; if (j==5) value=(unsigned short)(number>>16);
            if (input[j]!=value) return 4;
        }
        for (j=16;j<256;++j) if (k*240+j-16>=775*macros && input[j]) return 5;
    }
    for (k=0;k<outputs;++k) {
        number=index+k; output=ring+4352+((slot+k)%15)*256;
        for (j=0;j<256;++j) output[j]=0;
        output[0]=0xc55b; output[1]=(unsigned short)(65520UL+number); output[2]=256;
        output[3]=(unsigned short)(number/15); output[4]=(unsigned short)number; output[5]=(unsigned short)(number>>16);
    }
    for (k=0;k<macros;++k) {
        base=775*k;
        for (j=0;j<384;++j) {
            bits=(unsigned long)mdec_input_word(ring,slot,base+j*2) |
                 ((unsigned long)mdec_input_word(ring,slot,base+j*2+1)<<16);
            s->mdec_coefficients[j]=(long)bits;
        }
        for (j=0;j<6;++j) s->mdec_used[j]=mdec_input_word(ring,slot,base+768+j);
        bw=mdec_input_word(ring,slot,base+774);
        if (bw>1) return 6;
        mdec_kernel_process(s->mdec_coefficients,s->mdec_used,s->mdec_rgb,bw);
        for (j=0;j<192;++j) {
            at=k*384+j*2; bits=s->mdec_rgb[j];
            output=ring+4352+((slot+at/240)%15)*256+16+at%240;
            output[0]=(unsigned short)bits; output[1]=(unsigned short)(bits>>16);
        }
    }
    ring[256]=0xd16b; ring[257]=notification[1]; ring[258]=inputs; ring[259]=slot; ring[260]=outputs;
    return 0;
}
#endif

#ifdef EXEC_DMM_WSOLA
/* One audio search: four input payloads (880 useful words), one result slot.
 * Scratch is owned by this node context; no stack-sized audio buffer. */
static unsigned int ring_wsola_exchange(unsigned short *notification,
    unsigned short *debug,short *audio)
{
    unsigned long address=(unsigned long)notification[6] | ((unsigned long)notification[7]<<16);
    volatile unsigned short *ring=(volatile unsigned short *)address;
    unsigned int slot=notification[9],k,j;
    unsigned short offset,scored;
    unsigned long index,number;
    volatile unsigned short *input,*output;
    long score,sum=0;
    unsigned short value,seq,generation;
    if (!address || address>=0x00800000UL || slot>=15 || notification[10]!=4) return 1;
    if (ring[0]!=0xd16a || ring[1]!=40 || ring[2]!=4 || ring[3]!=slot || ring[6]>=8) return 2;
    index=(unsigned long)ring[4] | ((unsigned long)ring[5]<<16);
    for (k=0;k<4;++k) {
        input=ring+512+((slot+k)%15)*256;
        number=index+k; seq=(unsigned short)(65520UL+number);
        generation=(unsigned short)(number/15);
        for (j=0;j<16;++j) {
            value=0;
            if (j==0) value=0xc55a;
            if (j==1) value=seq;
            if (j==2) value=256;
            if (j==3) value=generation;
            if (j==4) value=(unsigned short)number;
            if (j==5) value=(unsigned short)(number>>16);
            if (input[j]!=value) return 3;
        }
        for (j=0;j<240;++j) {
            unsigned int at=k*240+j;
            value=input[16+j];
            if (at<880) {
                audio[at]=(short)value;
                if (audio[at]<-512 || audio[at]>511) return 5;
                sum+=(long)audio[at]*(at+1);
            }
            else if (value) return 4;
        }
    }
    score=dsp_wsola_best(audio,audio+220,&offset,&scored);
    output=ring+4352+slot*256;
    for (j=0;j<256;++j) output[j]=0;
    output[0]=0xc55b; output[1]=(unsigned short)(65520UL+index); output[2]=256;
    output[3]=(unsigned short)(index/15); output[4]=(unsigned short)index; output[5]=(unsigned short)(index>>16);
    output[16]=offset; output[17]=scored;
    output[18]=(unsigned short)score; output[19]=(unsigned short)((unsigned long)score>>16);
    output[20]=(unsigned short)sum; output[21]=(unsigned short)((unsigned long)sum>>16);
    output[22]=880; output[23]=40;
    debug[0]=offset; debug[1]=scored;
    ring[256]=0xd16b; ring[257]=notification[1]; ring[258]=4; ring[259]=slot;
    return 0;
}
#endif

#ifdef CREATE_WORKER_MSG
static void message_snapshot(unsigned short *,void *,stream_context *,
    unsigned int,unsigned int,dsp_msg_t *);
#endif

#ifdef CREATE_STREAM_WORKER
/* No RMS execute/EXITACK is involved. Generic library2 retains this code
 * while the host node stays CREATED. Native NODE_wait explicitly supports
 * a NULL env: it waits on the streams without attaching an RMS message
 * queue. The last response is reclaimed before the worker returns. */
static unsigned long stream_worker_loop(stream_context *s)
{
    unsigned long status=0x80008008UL,t0,t1;
    unsigned int ready,messages,seq,reps,stop;
    unsigned short offset,scored;
    unsigned short *inbuf=s->inbuf,*outbuf=s->outbuf;
    volatile long result;
    long count;
    long input_sum;
    int i,r,waits=0,idle_input,idle_output;
    void *arg;
    if (STRM_issue(s->input,inbuf,s->insize,s->insize,NULL)) goto cleanup;
    s->input_pending=1;
    for (;;) {
        s->worker_seen=0xc561;
        if (s->worker_stop) {
            if (!s->worker_frames) status=0x8000UL;
            break;
        }
        messages=0;
        ready=NODE_wait(NULL,&s->input,1,100,&messages);
        if (messages) break;
        if (!ready) { if (++waits>=100) break; else continue; }
        waits=0;
        count=STRM_reclaim(s->input,(void **)&inbuf,NULL,&arg);
        if (count<0) break;
        s->input_pending=0;
        if (count!=(long)s->insize || inbuf[0]!=0xc55a ||
            inbuf[2]!=(unsigned short)s->insize) break;
        seq=inbuf[1]; reps=inbuf[3]; stop=inbuf[12];
        if (reps>20000 || stop>1 || seq!=s->worker_frames+1) break;
#ifdef CREATE_WORKER_MSG
        {
            dsp_msg_t msg;
            unsigned int sent;
            if (seq!=1 || reps || stop!=1 || !s->worker_env) break;
            msg.cmd=0x606UL; msg.arg_1=0xa1b2c3d4UL;
            msg.arg_2=(unsigned long)s->worker_env;
            sent=NODE_putMsg(s->worker_env,NULL,&msg,100);
            for (i=0;i<256;++i) outbuf[i]=0;
            message_snapshot(outbuf,s->worker_env,s,7,sent,&msg);
            put32(outbuf,62,sent?0x8000UL:0x80008008UL);
            if (STRM_issue(s->output,outbuf,256,s->outsize,NULL)) break;
            s->output_pending=1;
            if (STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg)<0) break;
            s->output_pending=0;
            s->worker_frames=1; s->worker_last_stop=1;
            status=sent?0x8000UL:0x80008008UL;
            break;
        }
#else
        input_sum=0; offset=0; scored=0;
        if (s->outsize==24) {
            if (inbuf[4]!=1 || inbuf[5]>7 || reps>64) break;
            for (i=16;i<896;++i) {
                short value=(short)inbuf[i];
                if (value < -512 || value > 511) goto cleanup;
                input_sum+=(long)value*(long)(i-15);
            }
        }
        s->worker_seen=0xc562;
        t0=CLK_gethtime(); result=0;
        for (r=0;r<(int)reps;++r) {
            if (s->outsize==24)
                result=dsp_wsola_best((short *)(inbuf+16),(short *)(inbuf+236),&offset,&scored);
            else result=dsp_q15_dot((short *)(inbuf+16),s->coefficients,240);
        }
        t1=CLK_gethtime();
        for (i=0;i<16;++i) outbuf[i]=0;
        if (s->outsize==24) {
            outbuf[16]=offset; outbuf[17]=scored;
            outbuf[18]=(unsigned short)s->insize; outbuf[19]=(unsigned short)s->outsize;
            outbuf[20]=inbuf[4]; outbuf[21]=inbuf[5];
            put32(outbuf,22,(unsigned long)input_sum);
        }
        else for (i=16;i<(int)s->outsize;++i)
            outbuf[i]=(unsigned short)(inbuf[i]*3u+seq);
        outbuf[0]=0xc55b; outbuf[1]=seq; outbuf[2]=(unsigned short)count;
        outbuf[3]=reps; outbuf[4]=20;
        outbuf[5]=(unsigned short)++s->worker_frames;
        put32(outbuf,6,(unsigned long)result);
        put32(outbuf,8,t1-t0); put32(outbuf,10,CLK_countspms());
        outbuf[12]=stop; outbuf[13]=15;
        /* Absolute timer stamp for cross-packet ARM-bracket calibration.
         * Pointer cookie remains mandatory in the create/delete gates. */
        put32(outbuf,14,t1);
        if (STRM_issue(s->output,outbuf,s->outsize,s->outsize,NULL)) break;
        s->output_pending=1;
        if (STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg)<0) break;
        s->output_pending=0;
        if (stop) {
            s->worker_last_stop=1; status=0x8000UL;
            break;
        }
        if (STRM_issue(s->input,inbuf,s->insize,s->insize,NULL)) break;
        s->input_pending=1;
#endif
    }
cleanup:
    s->worker_seen=0xc563;
    idle_input=STRM_idle(s->input,1); idle_output=STRM_idle(s->output,1);
    if (idle_input || idle_output) status=0x80008008UL;
    if (s->input_pending && STRM_reclaim(s->input,(void **)&inbuf,NULL,&arg)>=0)
        s->input_pending=0;
    if (s->output_pending && STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg)>=0)
        s->output_pending=0;
    s->inbuf=inbuf; s->outbuf=outbuf;
    if (s->input_pending || s->output_pending) status=0x80008008UL;
    return status;
}

static void stream_worker(bios_arg context,bios_arg cookie,bios_arg a2,bios_arg a3,
    bios_arg a4,bios_arg a5,bios_arg a6,bios_arg a7)
{
    stream_context *s=(stream_context *)context;
    (void)a2; (void)a3; (void)a4; (void)a5; (void)a6; (void)a7;
    s->worker_cookie=(unsigned long)cookie;
    s->worker_status=stream_worker_loop(s);
    s->worker_seen=0xc564;
    SEM_post(s->worker_done);
    /* Native task startup invokes TSK_exit after this callback returns. */
}

static int join_stream_worker(stream_context *s)
{
    bios_task_stat stat,current_stat;
    int ok;
    if (!s->worker_task || !s->worker_done || !KNL_curtask) return 0;
    TSK_stat(KNL_curtask,&current_stat);
    /* Keep callback return/TSK_exit ahead of the awakened dispatcher. */
    if (current_stat.mode!=BIOS_TASK_RUNNING || current_stat.attrs.priority>=15)
        return 0;
    s->worker_stop=1;
    /* This timeout is in BIOS ticks, not milliseconds. Normally the last
     * packet has already completed the task and posted this semaphore. */
    if (!SEM_pend(s->worker_done,5000)) return 0;
    TSK_stat(s->worker_task,&stat);
    if (stat.mode!=BIOS_TASK_TERMINATED) return 0;
    ok=s->worker_seen==0xc564 && s->worker_cookie==0x00123456UL &&
       s->worker_status==0x8000UL && !s->input_pending && !s->output_pending &&
       (!s->worker_frames || s->worker_last_stop==1);
    TSK_delete(s->worker_task); s->worker_task=NULL;
    SEM_delete(s->worker_done); s->worker_done=NULL;
    return ok;
}

static int start_stream_worker(stream_context *s)
{
    bios_task_attrs attrs;
    bios_task_stat stat;
    if (!KNL_curtask) return 0;
    TSK_stat(KNL_curtask,&stat);
    if (stat.mode!=BIOS_TASK_RUNNING || stat.attrs.priority<1 ||
        stat.attrs.priority>=15) return 0;
    attrs=TSK_ATTRS;
    if (attrs.stack || !attrs.name || attrs.stackseg<0) return 0;
    s->worker_done=SEM_create(0,NULL);
    if (!s->worker_done) return 0;
    attrs.priority=15; attrs.stacksize=2048; attrs.sysstacksize=512;
    attrs.environ=NULL; attrs.exitflag=0; attrs.initstackflag=1;
    s->worker_status=0x80008008UL;
    s->worker_task=TSK_create(stream_worker,&attrs,(bios_arg)s,
        (bios_arg)0x00123456UL,(bios_arg)0,(bios_arg)0,(bios_arg)0,
        (bios_arg)0,(bios_arg)0,(bios_arg)0);
    if (!s->worker_task) {
        SEM_delete(s->worker_done); s->worker_done=NULL;
        return 0;
    }
    TSK_stat(s->worker_task,&stat);
    if (stat.mode==BIOS_TASK_BLOCKED && s->worker_seen==0xc561 &&
        s->worker_cookie==0x00123456UL && s->input_pending && !s->output_pending)
        return 1;
    /* Request bounded cooperative stop; never delete a task which still
     * owns a stream buffer. A failed join is retained for delete's gate. */
    join_stream_worker(s);
    return 0;
}
#endif

#ifdef CREATE_WORKER_ONCE
/* No resources are acquired by this callback. Priority 15 only covers these
 * stores and return. Join and TSK_delete happen before the create phase can
 * unload any code; this does not test persistence across phases. */
static void worker_once(bios_arg context,bios_arg cookie,bios_arg a2,bios_arg a3,
    bios_arg a4,bios_arg a5,bios_arg a6,bios_arg a7)
{
    stream_context *s=(stream_context *)context;
    (void)a2; (void)a3; (void)a4; (void)a5; (void)a6; (void)a7;
    s->worker_cookie=(unsigned long)cookie;
    s->worker_seen=0xc55d;
}

static int check_worker_once(stream_context *s)
{
    bios_task_attrs attrs;
    bios_task_stat stat;
    void *current=KNL_curtask,*task;
    int ok;
    if (!current) return 0;
    TSK_stat(current,&stat);
    /* Enforce preemption rather than assume the RMS dispatcher's priority.
     * The callback cannot block; returning invokes native TSK_exit. */
    if (stat.mode!=BIOS_TASK_RUNNING || stat.attrs.priority<1 ||
        stat.attrs.priority>=15) return 0;
    attrs=TSK_ATTRS;
    if (attrs.stack || !attrs.name || attrs.stackseg<0) return 0;
    attrs.priority=15; attrs.stacksize=1024; attrs.sysstacksize=256;
    attrs.environ=NULL; attrs.exitflag=0; attrs.initstackflag=1;
    s->worker_seen=0; s->worker_cookie=0;
    task=TSK_create(worker_once,&attrs,(bios_arg)s,(bios_arg)0x00123456UL,
                    (bios_arg)0,(bios_arg)0,(bios_arg)0,(bios_arg)0,
                    (bios_arg)0,(bios_arg)0);
    if (!task) return 0;
    TSK_stat(task,&stat);
    ok=stat.mode==BIOS_TASK_TERMINATED && s->worker_seen==0xc55d &&
       s->worker_cookie==0x00123456UL;
    /* The task is never the current task and owns no streams, locks or
     * external buffers, including the defensive failure path. */
    TSK_delete(task);
    return ok;
}
#endif

#ifdef CREATE_WORKER_PARKED
/* The generic DCD keeps this callback resident through created-state
 * delete. Its sole wait has a finite BIOS tick count; no STRM or locks are
 * acquired. Delete posts the semaphore and joins before freeing context. */
static void worker_parked(bios_arg context,bios_arg cookie,bios_arg a2,bios_arg a3,
    bios_arg a4,bios_arg a5,bios_arg a6,bios_arg a7)
{
    stream_context *s=(stream_context *)context;
    (void)a2; (void)a3; (void)a4; (void)a5; (void)a6; (void)a7;
    s->worker_cookie=(unsigned long)cookie;
    s->worker_seen=0xc551;
    s->worker_wait=SEM_pend(s->worker_gate,30000);
    s->worker_seen=0xc552;
}

static int start_worker_parked(stream_context *s)
{
    bios_task_attrs attrs;
    bios_task_stat stat;
    void *current=KNL_curtask;
    int ok;
    if (!current) return 0;
    TSK_stat(current,&stat);
    if (stat.mode!=BIOS_TASK_RUNNING || stat.attrs.priority<1 ||
        stat.attrs.priority>=15) return 0;
    attrs=TSK_ATTRS;
    if (attrs.stack || !attrs.name || attrs.stackseg<0) return 0;
    s->worker_gate=SEM_create(0,NULL);
    if (!s->worker_gate) return 0;
    attrs.priority=15; attrs.stacksize=1024; attrs.sysstacksize=256;
    attrs.environ=NULL; attrs.exitflag=0; attrs.initstackflag=1;
    s->worker_seen=0; s->worker_cookie=0; s->worker_wait=0;
    s->worker_task=TSK_create(worker_parked,&attrs,(bios_arg)s,
        (bios_arg)0x00123456UL,(bios_arg)0,(bios_arg)0,(bios_arg)0,
        (bios_arg)0,(bios_arg)0,(bios_arg)0);
    if (!s->worker_task) {
        SEM_delete(s->worker_gate); s->worker_gate=NULL;
        return 0;
    }
    TSK_stat(s->worker_task,&stat);
    ok=stat.mode==BIOS_TASK_BLOCKED && s->worker_seen==0xc551 &&
        s->worker_cookie==0x00123456UL;
    if (!ok) {
        /* External TSK_delete unlinks a blocked task from its wait queue.
         * Native 25B737..25B755 verifies both queue removals. */
        SEM_post(s->worker_gate);
        TSK_delete(s->worker_task); s->worker_task=NULL;
        SEM_delete(s->worker_gate); s->worker_gate=NULL;
    }
    return ok;
}

static int finish_worker_parked(stream_context *s)
{
    bios_task_stat stat;
    int ok;
    if (!s->worker_task || !s->worker_gate) return 0;
    TSK_stat(s->worker_task,&stat);
    ok=stat.mode==BIOS_TASK_BLOCKED && s->worker_seen==0xc551 &&
       s->worker_cookie==0x00123456UL;
    SEM_post(s->worker_gate);
    /* The unblocked priority-15 callback does two stores and returns,
     * preempting the lower-priority RMS delete dispatcher. */
    TSK_stat(s->worker_task,&stat);
    ok=ok && stat.mode==BIOS_TASK_TERMINATED &&
       s->worker_seen==0xc552 && s->worker_wait==1;
    TSK_delete(s->worker_task); s->worker_task=NULL;
    SEM_delete(s->worker_gate); s->worker_gate=NULL;
    return ok;
}
#endif

#if defined(EXEC_MSG_STAGES) || defined(EXEC_EXIT_DIAG) || defined(CREATE_WORKER_MSG)
/* Public MSG exports, matched to .bss symbols in this baseimage. Read only.
 * MSG_Obj occupies 12 C55 words; count/notifyType/handle/status are at
 * word offsets 4/6/8/10. The memory-window header is four C55 words. */
extern volatile unsigned short MSG_toGPP[12];
extern volatile unsigned short *MSG_pfromDSPBuffer;
extern volatile unsigned short *MSG_ptoDSPBuffer;
extern unsigned int MSG_maxMessages;
static void message_snapshot(unsigned short *b, void *env, stream_context *s,
    unsigned int stage, unsigned int result, dsp_msg_t *msg)
{
    int i;
    for (i=0; i<80; ++i) b[i]=0;
    b[0]=0xc55d; b[1]=stage; b[2]=256;
#ifdef CREATE_WORKER_MSG
    b[3]=26;
#elif defined(EXEC_EXIT_DIAG)
    b[3]=25;
#else
    b[3]=15;
#endif
    b[4]=result;
    put32(b,6,(unsigned long)env);
    put32(b,8,msg->cmd); put32(b,10,msg->arg_1);
    put32(b,12,msg->arg_2);
    put32(b,16,(unsigned long)MSG_toGPP);
    for (i=0; i<12; ++i) b[18+i]=MSG_toGPP[i];
    b[30]=MSG_maxMessages;
    put32(b,32,(unsigned long)MSG_pfromDSPBuffer);
    put32(b,38,(unsigned long)MSG_ptoDSPBuffer);
    for (i=0; i<4; ++i) {
        if (MSG_pfromDSPBuffer) b[34+i]=MSG_pfromDSPBuffer[i];
        if (MSG_ptoDSPBuffer) b[40+i]=MSG_ptoDSPBuffer[i];
    }
    /* MSG_MemWindow's first record follows its four-word control header.
     * Snapshot raw C55 words; do not impose the host's long-word order.
     * Retain header checks on both sides of the copy to expose races. */
    if (MSG_pfromDSPBuffer && b[36]>0 && b[36]<=MSG_maxMessages) {
        b[44]=1;
        for (i=0; i<8; ++i) b[46+i]=MSG_pfromDSPBuffer[4+i];
        b[54]=MSG_pfromDSPBuffer[0]; b[55]=MSG_pfromDSPBuffer[2];
    }
    b[56]=s->input_pending; b[57]=s->output_pending;
    /* The first host->DSP record is a raw observation, even after dequeue.
     * Its header may change concurrently; this is not an atomic snapshot. */
    if (MSG_ptoDSPBuffer && MSG_maxMessages) {
        b[64]=1;
        for (i=0; i<8; ++i) b[66+i]=MSG_ptoDSPBuffer[4+i];
        b[74]=MSG_ptoDSPBuffer[0]; b[75]=MSG_ptoDSPBuffer[2];
    }
}
static int message_stage(void *env, stream_context *s, unsigned int stage,
    unsigned int result, dsp_msg_t *msg)
{
    int i;
    void *arg;
    if (!s || !s->output || !s->outbuf || s->output_pending) return 0;
    for (i=0; i<256; ++i) s->outbuf[i]=0;
    message_snapshot(s->outbuf,env,s,stage,result,msg);
    if (STRM_issue(s->output,s->outbuf,256,s->outsize,NULL)) return 0;
    s->output_pending=1;
    if (STRM_reclaim(s->output,(void **)&s->outbuf,NULL,&arg)<0) return 0;
    s->output_pending=0;
    return 1;
}
#endif

unsigned long STREAM_DSP_create(int argc, char *args, int nin,
    unsigned long indef[], int nout, unsigned long outdef[], void *env)
{
#ifdef MSG_BARE_NODE
    /* Message-only control: native task-node ABI, zero STRM definitions.
     * Removes all STRM/MEM setup from create and cleanup from delete. */
    (void)argc; (void)args; (void)indef; (void)outdef;
    return (!env || nin || nout) ? 0x80008015UL : 0x8000UL;
#else
    stream_def *a, *b;
    stream_attrs attrs;
    stream_context *s;
    int i;
    (void)argc; (void)args;
    if (!env) return 0x80008015UL;
    ((node_env *)env)->moreEnv=NULL;
#ifdef CREATE_RESIDENT_CHECK
    if (resident_cookie!=0x1badb002UL) return 0x80008015UL;
#endif
    s=(stream_context *)MEM_valloc(0,sizeof(*s),0,0);
    ((node_env *)env)->moreEnv=s;
    if (!s) return 0x8000800cUL;
    for (i=0;i<(int)sizeof(*s);++i) ((unsigned short *)s)[i]=0;
    if (nin != 1 || nout != 1 || !indef || !outdef) return 0x80008015UL;
    a = (stream_def *)indef[0]; b = (stream_def *)outdef[0];
    if (!a || !b) return 0x80008015UL;
#ifdef CREATE_STREAM_WORKER
    /* Equal-size echo or the fixed WSOLA896/24-word contract. Independent
     * native stream attributes carry words; allocations remain4096 bytes. */
    if (!((a->size>=256 && a->size<=2048 && b->size==a->size) ||
          (a->size==896 && b->size==24))) return 0x80008015UL;
#else
    if (a->size!=256 || b->size!=256) return 0x80008015UL;
#endif
    attrs.nbufs=(int)a->nbufs; attrs.segid=(int)a->segid;
    attrs.align=(int)a->align; attrs.timeout=1000;
    s->input = STRM_create(a->name, 0, a->size, &attrs);
    attrs.nbufs=(int)b->nbufs; attrs.segid=(int)b->segid;
    attrs.align=(int)b->align;
    s->output = STRM_create(b->name, 1, b->size, &attrs);
    if (!s->input || !s->output) return 0x80008015UL;
    s->insize=a->size; s->outsize=b->size;
    s->inbuf=(unsigned short *)STRM_allocateBuffer(s->input, s->insize);
    s->outbuf=(unsigned short *)STRM_allocateBuffer(s->output, s->outsize);
    if (!s->inbuf || !s->outbuf || s->inbuf == (void *)-1 || s->outbuf == (void *)-1)
        return 0x8000800cUL;
    for (i=0; i<240; ++i) s->coefficients[i]=(short)((i & 15)-7);
#ifdef CREATE_WORKER_ONCE
    if (!check_worker_once(s)) return 0x80008015UL;
#endif
#ifdef CREATE_WORKER_PARKED
    if (!start_worker_parked(s)) return 0x80008015UL;
#endif
#ifdef CREATE_STREAM_WORKER
#ifdef CREATE_WORKER_MSG
    s->worker_env=env;
#endif
    if (!start_stream_worker(s)) return 0x80008015UL;
#endif
#ifdef CREATE_RESIDENT_CHECK
    s->resident_delete_address=(unsigned long)STREAM_DSP_delete;
    resident_cookie=0xc55dc0deUL;
#endif
    return 0x8000UL;
#endif
}


unsigned long STREAM_DSP_execute(void *env)
{
#if defined(CREATE_WORKER_ONCE) || defined(CREATE_WORKER_PARKED) || defined(CREATE_RESIDENT_CHECK) || defined(CREATE_STREAM_WORKER)
    /* Probe only supports created-state delete. No official RUN. */
    (void)env;
    return 0x80008015UL;
#elif defined(EXEC_SMOKE)
    /* Isolate the host RUN/RMS contract from all stream operations. */
    (void)env;
    return 0x8000UL;
#elif defined(EXEC_MSG_STAGES)
    /* Use the previously working STRM output to locate the first message
     * call that fails. Both message calls are nonblocking (timeout=0).
     * Return afterwards; the native wrapper owns the EXITACK attempt. */
    dsp_msg_t msg;
    unsigned int result;
    stream_context *s;
    if (!env) return 0x80008015UL;
    s=(stream_context *)((node_env *)env)->moreEnv;
    msg.cmd=msg.arg_1=msg.arg_2=0;
    if (!message_stage(env,s,1,0,&msg)) return 0x80008008UL;
    result=NODE_getMsg(env,&msg,0);
    if (!message_stage(env,s,2,result,&msg)) return 0x80008008UL;
    msg.cmd=0x600UL; msg.arg_1=0x000f0001UL; msg.arg_2=(unsigned long)env;
    result=NODE_putMsg(env,NULL,&msg,0);
    if (!message_stage(env,s,3,result,&msg)) return 0x80008008UL;
    return 0x8000UL;
#elif defined(EXEC_MSG_DIAG)
    /* Establish execute entry, both directions, and RMS_EXIT receipt.
     * The native task wrapper, not this entry point, sends EXITACK. */
    dsp_msg_t msg;
    unsigned int waits,echoes=0;
    if (!env) return 0x80008015UL;
    msg.cmd=0x600UL; msg.arg_1=0x00080001UL; msg.arg_2=(unsigned long)env;
    if (!NODE_putMsg(env,NULL,&msg,100)) return 0x80008008UL;
    for (waits=0; waits<150; ++waits) {
        if (!NODE_getMsg(env,&msg,100)) continue;
        if (msg.cmd==0x80000000UL) {
            msg.cmd=0x603UL; msg.arg_1=0x80000000UL; msg.arg_2=echoes;
            if (!NODE_putMsg(env,NULL,&msg,100)) return 0x80008008UL;
            return 0x8000UL;
        }
        if (msg.cmd==0x601UL) {
            msg.cmd=0x602UL; ++echoes;
            if (!NODE_putMsg(env,NULL,&msg,100)) return 0x80008008UL;
        }
    }
    return 0x80008008UL;
#elif defined(EXEC_RMS_WAIT)
    /* TI PING waits for RMS_EXIT before returning. Isolate that lifecycle
     * from STRM_issue/wait/idle/reclaim without changing create/delete.
     * Native NODE_getMsg returns 1 after copying a three-long message;
     * a finite timeout bounds a missing exit request. */
    dsp_msg_t msg;
    unsigned int waits;
    if (!env) return 0x80008015UL;
    for (waits=0; waits<100; ++waits) {
        msg.cmd=0;
        if (NODE_getMsg(env,&msg,100) && msg.cmd==0x80000000UL)
            return 0x8000UL;
    }
    return 0x80008008UL;
#else
    long count;
    unsigned long frame=0, t0, t1;
    unsigned int seq, reps, stop;
    unsigned int messages,ready;
    int i, r, waits=0, idle_input, idle_output;
    unsigned long status=0x80008008UL;
#ifdef EXEC_EXIT_DIAG
    dsp_msg_t exit_msg;
    unsigned int exit_result=0,exit_waits=0,exit_diag_ready=0;
#endif
    volatile long result;
    stream_context *s;
    unsigned short *inbuf,*outbuf;
    void *arg;
    if (!env || !((node_env *)env)->moreEnv) return 0x80008015UL;
    s=(stream_context *)((node_env *)env)->moreEnv;
    if (!s->input || !s->output || !s->inbuf || !s->outbuf) return 0x80008015UL;
    inbuf=s->inbuf; outbuf=s->outbuf;
    if (STRM_issue(s->input,inbuf,s->insize,s->insize,NULL)) goto cleanup;
    s->input_pending=1;
    for (;;) {
        /* Match the firmware reference: wait for a ready stream before
         * reclaiming it. An RMS exit message is consumed separately. */
        messages=0;
        ready=NODE_wait(env,&s->input,1,100,&messages);
        if (messages) {
            dsp_msg_t msg;
            if (NODE_getMsg(env,&msg,0) && msg.cmd==0x80000000UL) {
                status=0x8000UL;
                break;
            }
        }
        if (!ready) { if (++waits>=300) break; else continue; }
        waits=0;
        count=STRM_reclaim(s->input,(void **)&inbuf,NULL,&arg);
        if (count < 0) break;
        s->input_pending=0;
        if (s->output_pending) {
            if (STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg) < 0) break;
            s->output_pending=0;
        }
        if (count != 256 || inbuf[0] != 0xc55a || inbuf[2] != 256) break;
        seq=inbuf[1]; reps=inbuf[3]; stop=inbuf[12];
        if (reps > 20000) break;
        t0=CLK_gethtime();
        result=0;
        for (r=0; r<(int)reps; ++r)
            result=dsp_q15_dot((short *)(inbuf+16),s->coefficients,240);
        t1=CLK_gethtime();
        for (i=0; i<16; ++i) outbuf[i]=0;
        for (i=16; i<256; ++i)
            outbuf[i]=(unsigned short)(inbuf[i]*3u+seq);
#ifdef EXEC_DMM_RING
        if (inbuf[8]==0xd16b) {
#ifdef EXEC_DMM_DCR_READ
            outbuf[14]=ring_read_dcr();
#endif
            t0=CLK_gethtime();
            result=ring_exchange(inbuf,outbuf+16);
#ifdef EXEC_DMM_DCR_READ
            outbuf[15]=ring_read_dcr();
            outbuf[13]=0xdc01;
#endif
            t1=CLK_gethtime();
        }
#endif
#ifdef EXEC_DMM_WSOLA
        if (inbuf[8]==0xd16c) {
            outbuf[14]=ring_read_dcr();
            t0=CLK_gethtime();
            result=ring_wsola_exchange(inbuf,outbuf+16,s->ring_audio);
            outbuf[15]=ring_read_dcr(); outbuf[13]=0xdc01;
            t1=CLK_gethtime();
        }
#endif
#ifdef EXEC_DMM_MDEC
        if (inbuf[8]==0xd16d) {
            outbuf[14]=ring_read_dcr(); t0=CLK_gethtime();
            result=ring_mdec_exchange(inbuf,s);
            outbuf[15]=ring_read_dcr(); outbuf[13]=0xdc01; t1=CLK_gethtime();
        }
#endif
#ifdef EXEC_DMM_SPU
        if (inbuf[8]==0xd16e) {
            outbuf[14]=ring_read_dcr(); t0=CLK_gethtime();
            result=ring_spu_exchange(inbuf,s->spu_sums);
            outbuf[15]=ring_read_dcr(); outbuf[13]=0xdc01; t1=CLK_gethtime();
        }
#endif
        outbuf[0]=0xc55b; outbuf[1]=seq; outbuf[2]=(unsigned short)count;
        outbuf[3]=reps;
#if defined(EXEC_RUN_STOP) || defined(EXEC_EXIT_DIAG)
        outbuf[4]=21;
#ifdef EXEC_DMM_RING
#ifdef EXEC_DMM_MDEC
        if (inbuf[8]==0xd16d) outbuf[4]=41;
#endif
#ifdef EXEC_DMM_SPU
        if (inbuf[8]==0xd16e) outbuf[4]=42;
#endif
#ifdef EXEC_DMM_WSOLA
        if (inbuf[8]==0xd16c) outbuf[4]=40;
#endif
        if (inbuf[8]==0xd16b) {
#ifdef EXEC_DMM_DCR_READ
            outbuf[4]=39; /* Distinct diagnostic notification; ring layout remains38. */
#else
            outbuf[4]=38;
#endif
        }
#endif
#else
        outbuf[4]=7;
#endif
        outbuf[5]=(unsigned short)++frame;
        put32(outbuf,6,(unsigned long)result);
        put32(outbuf,8,t1-t0); put32(outbuf,10,CLK_countspms());
        outbuf[12]=stop;
        if (STRM_issue(s->output,outbuf,256,s->outsize,NULL)) break;
        s->output_pending=1;
#if defined(EXEC_RUN_STOP) || defined(EXEC_EXIT_DIAG)
        /* Reclaim output but remain RUNNING until host control6 sends EXIT.
         * Native EXITACK automatically dispatches delete. An early return
         * would race a later host delete against that automatic phase. */
        if (stop) {
#ifndef EXEC_EXIT_DIAG
            dsp_msg_t exit_msg;
#endif
            if (STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg)<0) break;
            s->output_pending=0;
#ifdef EXEC_EXIT_DIAG
            s->inbuf=inbuf; s->outbuf=outbuf;
            exit_msg.cmd=exit_msg.arg_1=exit_msg.arg_2=0;
            if (!message_stage(env,s,4,0,&exit_msg)) break;
            outbuf=s->outbuf;
#endif
#ifndef EXEC_EXIT_DIAG
            exit_msg.cmd = 0;
            for (waits = 0; waits < 100; ++waits) {
                if (NODE_getMsg(env, &exit_msg, 100) && exit_msg.cmd == 0x80000000UL) {
                    status = 0x8000UL;
                    break;
                }
            }
#else
            for (waits=0; waits<100; ++waits) {
                exit_result=NODE_getMsg(env,&exit_msg,100);
                exit_waits=waits+1;
                if (exit_result && exit_msg.cmd==0x80000000UL) {
                    status=0x8000UL;
                    break;
                }
            }
#endif
#ifdef EXEC_EXIT_DIAG
            for (i=0; i<256; ++i) outbuf[i]=0;
            message_snapshot(outbuf,env,s,5,exit_result,&exit_msg);
            outbuf[60]=exit_waits; put32(outbuf,62,status);
            exit_diag_ready=1;
#endif
            break;
        }
#endif
        /* The last-frame marker is echoed, but does not stop execute.
         * Prime input even after that frame, as TI STRMCOPY does. The
         * host's channel control 6 sends RMS_EXIT and waits for RMS_EXITACK
         * before the delete phase; returning early bypasses that lifecycle. */
        if (STRM_issue(s->input,inbuf,s->insize,s->insize,NULL)) break;
        s->input_pending=1;
    }
cleanup:
    /* Firmware STRMCOPY idles, then reclaims every outstanding buffer.
     * A buffer still owned by the stream must not be freed by delete. */
    idle_input=STRM_idle(s->input,1);
    idle_output=STRM_idle(s->output,1);
    if (idle_input || idle_output) status=0x80008008UL;
    if (s->input_pending && STRM_reclaim(s->input,(void **)&inbuf,NULL,&arg)>=0)
        s->input_pending=0;
    if (s->output_pending && STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg)>=0)
        s->output_pending=0;
    s->inbuf=inbuf; s->outbuf=outbuf;
    if (s->input_pending || s->output_pending) status=0x80008008UL;
#ifdef EXEC_EXIT_DIAG
    if (exit_diag_ready && !s->input_pending && !s->output_pending) {
        /* Capture both idle results before diagnostic output is reissued.
         * Idle flushes a stream; it does not delete it. This extra exchange
         * perturbs cleanup and is never an accepted normal D0 cycle. */
        message_snapshot(outbuf+96,env,s,6,exit_result,&exit_msg);
        outbuf[96+58]=(unsigned short)idle_input;
        outbuf[96+59]=(unsigned short)idle_output;
        outbuf[96+60]=exit_waits; put32(outbuf+96,62,status);
        if (STRM_issue(s->output,outbuf,256,s->outsize,NULL))
            return 0x80008008UL;
        s->output_pending=1;
        if (STRM_reclaim(s->output,(void **)&outbuf,NULL,&arg)<0)
            return 0x80008008UL;
        s->output_pending=0; s->outbuf=outbuf;
        if (STRM_idle(s->output,1)) status=0x80008008UL;
    }
#endif
#if defined(EXEC_RUN_STOP)
    if (status == 0x8000UL) {
        unsigned long delay_start = CLK_gethtime();
        volatile unsigned long spin_guard = 0;
        /* ~30 ms delay gives ARM channel.Ctl(6) time to release its kernel mutex
         * and return to user space before RMS_EXITACK arrives at the ARM mailbox DFC. */
        while ((unsigned long)(CLK_gethtime() - delay_start) < 600000UL && ++spin_guard < 5000000UL) {
        }
    }
#endif
    return status;
#endif
}

unsigned long STREAM_DSP_delete(void *env)
{
#ifdef MSG_BARE_NODE
    (void)env;
    return 0x8000UL;
#else
    stream_context *s;
#if defined(CREATE_WORKER_PARKED) || defined(CREATE_STREAM_WORKER)
    int worker_ok;
#endif
#ifdef CREATE_RESIDENT_CHECK
    int resident_ok;
#endif
    if (!env) return 0x80008015UL;
    s=(stream_context *)((node_env *)env)->moreEnv;
#ifdef CREATE_RESIDENT_CHECK
    /* Always release the ordinary streams/context, even if the loader
     * reinitialized data or changed the delete entry's program address. */
    resident_ok=resident_cookie==0xc55dc0deUL && s &&
        s->resident_delete_address==(unsigned long)STREAM_DSP_delete;
#endif
    if (!s) {
#if defined(CREATE_RESIDENT_CHECK) || defined(CREATE_WORKER_PARKED) || defined(CREATE_STREAM_WORKER)
        /* A missing context must fail the diagnostic rather than bypass
         * its data/address or parked-task assertions. */
        return 0x80008015UL;
#else
        return 0x8000UL;
#endif
    }
#ifdef CREATE_WORKER_PARKED
    worker_ok=finish_worker_parked(s);
#endif
#ifdef CREATE_STREAM_WORKER
    worker_ok=join_stream_worker(s);
    /* An active task keeps code, context and stream ownership alive. */
    if (s->worker_task) return 0x80008008UL;
#endif
    if (s->input_pending || s->output_pending) return 0x80008008UL;
    if (s->input && s->inbuf && s->inbuf != (void *)-1)
        STRM_freeBuffer(s->input,s->inbuf,s->insize);
    if (s->output && s->outbuf && s->outbuf != (void *)-1)
        STRM_freeBuffer(s->output,s->outbuf,s->outsize);
    if (s->input) STRM_delete(s->input);
    if (s->output) STRM_delete(s->output);
    MEM_free(0,s,sizeof(*s));
    ((node_env *)env)->moreEnv=NULL;
#ifdef CREATE_RESIDENT_CHECK
    resident_cookie=0x1badb002UL;
    if (!resident_ok) return 0x80008015UL;
#endif
#if defined(CREATE_WORKER_PARKED) || defined(CREATE_STREAM_WORKER)
    if (!worker_ok) return 0x80008015UL;
#endif
    return 0x8000UL;
#endif
}
