/* C55 large-model DSP/BIOS task ABI, verified against this base image.
 * Native startup 25CF3B..25CF4D loads the first five Args into XAR0..4.
 * Arg therefore needs the pointer calling convention, not the long one.
 * Attributes/stat offsets are checked by cl55, in 16-bit C55 words. */
#ifndef C55_BIOS_TASK_H
#define C55_BIOS_TASK_H
#include <stddef.h>

typedef void *bios_arg;
typedef void (*bios_task_fxn)(bios_arg,bios_arg,bios_arg,bios_arg,
                             bios_arg,bios_arg,bios_arg,bios_arg);
typedef struct {
    int priority;
    void *stack;
    size_t stacksize,sysstacksize;
    int stackseg;
    void *environ;
    char *name;
    int exitflag,initstackflag;
} bios_task_attrs;
typedef struct {
    bios_task_attrs attrs;
    int mode;
    void *sp,*ssp;
    size_t used,sysused;
} bios_task_stat;

typedef char bios_arg_size_check[sizeof(bios_arg)==2 ? 1 : -1];
typedef char bios_attrs_size_check[sizeof(bios_task_attrs)==14 ? 1 : -1];
typedef char bios_stack_offset_check[offsetof(bios_task_attrs,stack)==2 ? 1 : -1];
typedef char bios_stacksize_offset_check[offsetof(bios_task_attrs,stacksize)==4 ? 1 : -1];
typedef char bios_sysstack_offset_check[offsetof(bios_task_attrs,sysstacksize)==5 ? 1 : -1];
typedef char bios_segment_offset_check[offsetof(bios_task_attrs,stackseg)==6 ? 1 : -1];
typedef char bios_environ_offset_check[offsetof(bios_task_attrs,environ)==8 ? 1 : -1];
typedef char bios_name_offset_check[offsetof(bios_task_attrs,name)==10 ? 1 : -1];
typedef char bios_exit_offset_check[offsetof(bios_task_attrs,exitflag)==12 ? 1 : -1];
typedef char bios_stat_size_check[sizeof(bios_task_stat)==22 ? 1 : -1];
typedef char bios_mode_offset_check[offsetof(bios_task_stat,mode)==14 ? 1 : -1];
typedef char bios_sp_offset_check[offsetof(bios_task_stat,sp)==16 ? 1 : -1];
typedef char bios_ssp_offset_check[offsetof(bios_task_stat,ssp)==18 ? 1 : -1];
typedef char bios_used_offset_check[offsetof(bios_task_stat,used)==20 ? 1 : -1];

extern const bios_task_attrs TSK_ATTRS;
extern void *volatile KNL_curtask;
extern void *TSK_create(bios_task_fxn,const bios_task_attrs *,...);
extern void TSK_stat(void *,bios_task_stat *);
extern void TSK_delete(void *);
/* Native SEM_create takes count in T0, optional attrs in XAR0. SEM_pend
 * takes its handle in XAR0 and a 16-bit BIOS tick count in T0, returning
 * 0/1 in T0. NULL attrs selects SEM_ATTRS. No attrs layout is assumed. */
extern void *SEM_create(int,const void *);
extern int SEM_pend(void *,unsigned int);
extern void SEM_post(void *);
extern void SEM_delete(void *);
#define BIOS_TASK_RUNNING 0
#define BIOS_TASK_BLOCKED 2
#define BIOS_TASK_TERMINATED 3
#endif
