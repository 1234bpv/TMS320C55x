/*
 * (C) Gražvydas "notaz" Ignotas, 2011
 *
 * This work is licensed under the terms of any of these licenses
 * (at your option):
 *  - GNU GPL, version 2 or later.
 *  - GNU LGPL, version 2.1 or later.
 * See the COPYING file in the top-level directory.
 */

.syntax unified
.arm
.text
.align 2
.global spu_mix_chan_arm
.type spu_mix_chan_arm,%function
spu_mix_chan_arm: @ (int *SSumLR, int count, int lv, int rv)
    stmfd       sp!, {r4-r8,lr}
    orr         r3, r2, r3, lsl #16
    lsl         r3, #1                 @ packed multipliers << 1
    mov         r2, r0
    ldr         r0, [sp, #24]
0:
    ldmia       r0!, {r4,r5}
    ldmia       r2, {r6-r8,lr}
    lsl         r4, #1                 @ adjust for mul
    lsl         r5, #1
    smlawb      r6, r4, r3, r6
    smlawt      r7, r4, r3, r7
    smlawb      r8, r5, r3, r8
    smlawt      lr, r5, r3, lr
    subs        r1, #2
    blt         mc_finish
    stmia       r2!, {r6-r8,lr}
    bgt         0b
    ldmeqfd     sp!, {r4-r8,pc}

mc_finish:
    stmia       r2!, {r6,r7}
    ldmfd       sp!, {r4-r8,pc}
.size spu_mix_chan_arm,.-spu_mix_chan_arm
.section .note.GNU-stack,"",%progbits
