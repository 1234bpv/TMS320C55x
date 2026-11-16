/***************************************************************************
 *   Copyright (C) 2010 Gabriele Gorla                                     *
 *   Copyright (C) 2007 Ryan Schultz, PCSX-df Team, PCSX team              *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin Street, Fifth Floor, Boston, MA 02111-1307 USA.           *
 ***************************************************************************/

// C55x adaptation: int->long in wrapper, explicit32-bit rounding literals.
#pragma FUNC_CANNOT_INLINE(idct_fill)
#pragma FUNC_CANNOT_INLINE(idct_spread)
#define DSIZE			8
#define DSIZE2			(DSIZE * DSIZE)

#define SCALE(x, n)		((x) >> (n))
#define SCALER(x, n)	(((x) + ((1 << (n)) >> 1)) >> (n))

#define AAN_CONST_BITS			12
#define AAN_PRESCALE_BITS		16

#define AAN_CONST_SIZE			24
#define AAN_CONST_SCALE			(AAN_CONST_SIZE - AAN_CONST_BITS)

#define AAN_PRESCALE_SIZE		20
#define AAN_PRESCALE_SCALE		(AAN_PRESCALE_SIZE-AAN_PRESCALE_BITS)
#define AAN_EXTRA				12

#define FIX_1_082392200		SCALER(18159528, AAN_CONST_SCALE) // B6
#define FIX_1_414213562		SCALER(23726566, AAN_CONST_SCALE) // A4
#define FIX_1_847759065		SCALER(31000253, AAN_CONST_SCALE) // A2
#define FIX_2_613125930		SCALER(43840978, AAN_CONST_SCALE) // B2

#define MULS(var, const)	(SCALE((var) * (const), AAN_CONST_BITS))

static inline void fillcol(int *blk, int val) {
	blk[0 * DSIZE] = blk[1 * DSIZE] = blk[2 * DSIZE] = blk[3 * DSIZE]
		= blk[4 * DSIZE] = blk[5 * DSIZE] = blk[6 * DSIZE] = blk[7 * DSIZE] = val;
}

static inline void fillrow(int *blk, int val) {
	blk[0] = blk[1] = blk[2] = blk[3]
		= blk[4] = blk[5] = blk[6] = blk[7] = val;
}

// The two trivial cases get functions of their own: inside idct the compiler runs out
// of registers, keeps the loop counter on the stack and stalls on it every iteration.
static void idct_fill(int *blk, int val) {
	int i;
	for (i = 0; i < DSIZE; i++, blk += DSIZE) fillrow(blk, val);
}

// Only the first column is non zero: every row is its first element repeated.
static void idct_spread(int *blk) {
	int i;
	for (i = 0; i < DSIZE; i++, blk += DSIZE) fillrow(blk, blk[0]);
}

static void idct(int *block,int used_col) {
	int tmp0, tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7;
	int z5, z10, z11, z12, z13;
	int *ptr;
	int i;

	// the block has only the DC coefficient
	if (used_col == -1) { 
		idct_fill(block, block[0]);
		return;
	}

	// last_col keeps track of the highest column with non zero coefficients
	ptr = block;
	for (i = 0; i < DSIZE; i++, ptr++) {
		if ((used_col & (1 << i)) == 0) {
			// the column is empty or has only the DC coefficient
			if (ptr[DSIZE * 0]) {
				fillcol(ptr, ptr[0]);
				used_col |= (1 << i);
			}
			continue;
		}

		// further optimization could be made by keeping track of 
		// last_row in rl2blk
		z10 = ptr[DSIZE * 0] + ptr[DSIZE * 4]; // s04
		z11 = ptr[DSIZE * 0] - ptr[DSIZE * 4]; // d04
		z13 = ptr[DSIZE * 2] + ptr[DSIZE * 6]; // s26
		z12 = MULS(ptr[DSIZE * 2] - ptr[DSIZE * 6], FIX_1_414213562) - z13; 
		//^^^^  d26=d26*2*A4-s26

		tmp0 = z10 + z13; // os07 = s04 + s26
		tmp3 = z10 - z13; // os34 = s04 - s26
		tmp1 = z11 + z12; // os16 = d04 + d26
		tmp2 = z11 - z12; // os25 = d04 - d26

		z13 = ptr[DSIZE * 3] + ptr[DSIZE * 5]; //s53
		z10 = ptr[DSIZE * 3] - ptr[DSIZE * 5]; //-d53 
		z11 = ptr[DSIZE * 1] + ptr[DSIZE * 7]; //s17
		z12 = ptr[DSIZE * 1] - ptr[DSIZE * 7]; //d17

		tmp7 = z11 + z13; // od07 = s17 + s53

		z5 = (z12 - z10) * (FIX_1_847759065); 
		tmp6 = SCALE(z10*(FIX_2_613125930) + z5, AAN_CONST_BITS) - tmp7; 
		tmp5 = MULS(z11 - z13, FIX_1_414213562) - tmp6;
		tmp4 = SCALE(z12*(FIX_1_082392200) - z5, AAN_CONST_BITS) + tmp5; 

		// path #1
		//z5 = (z12 - z10)* FIX_1_847759065; 
		// tmp0 = (d17 + d53) * 2*A2

		//tmp6 = DESCALE(z10*FIX_2_613125930 + z5, CONST_BITS) - tmp7; 
		// od16 = (d53*-2*B2 + tmp0) - od07

		//tmp4 = DESCALE(z12*FIX_1_082392200 - z5, CONST_BITS) + tmp5; 
		// od34 = (d17*2*B6 - tmp0) + od25

		// path #2

		// od34 = d17*2*(B6-A2) - d53*2*A2
		// od16 = d53*2*(A2-B2) + d17*2*A2

		// end

		//    tmp5 = MULS(z11 - z13, FIX_1_414213562) - tmp6;
		// od25 = (s17 - s53)*2*A4 - od16

		ptr[DSIZE * 0] = (tmp0 + tmp7); // os07 + od07
		ptr[DSIZE * 7] = (tmp0 - tmp7); // os07 - od07
		ptr[DSIZE * 1] = (tmp1 + tmp6); // os16 + od16
		ptr[DSIZE * 6] = (tmp1 - tmp6); // os16 - od16
		ptr[DSIZE * 2] = (tmp2 + tmp5); // os25 + od25
		ptr[DSIZE * 5] = (tmp2 - tmp5); // os25 - od25
		ptr[DSIZE * 4] = (tmp3 + tmp4); // os34 + od34
		ptr[DSIZE * 3] = (tmp3 - tmp4); // os34 - od34
	}

	ptr = block;
	if (used_col == 1) {
		idct_spread(block);
	} else {
		for (i = 0; i < DSIZE; i++, ptr += DSIZE) {
			z10 = ptr[0] + ptr[4];
			z11 = ptr[0] - ptr[4];
			z13 = ptr[2] + ptr[6];
			z12 = MULS(ptr[2] - ptr[6], FIX_1_414213562) - z13;

			tmp0 = z10 + z13;
			tmp3 = z10 - z13;
			tmp1 = z11 + z12;
			tmp2 = z11 - z12;
			
			z13 = ptr[3] + ptr[5];
			z10 = ptr[3] - ptr[5];
			z11 = ptr[1] + ptr[7];
			z12 = ptr[1] - ptr[7];

			tmp7 = z11 + z13;
			z5 = (z12 - z10) * FIX_1_847759065; 
			tmp6 = SCALE(z10 * FIX_2_613125930 + z5, AAN_CONST_BITS) - tmp7;
			tmp5 = MULS(z11 - z13, FIX_1_414213562) - tmp6;
			tmp4 = SCALE(z12 * FIX_1_082392200 - z5, AAN_CONST_BITS) + tmp5;

			ptr[0] = tmp0 + tmp7;

			ptr[7] = tmp0 - tmp7;
			ptr[1] = tmp1 + tmp6;
			ptr[6] = tmp1 - tmp6;
			ptr[2] = tmp2 + tmp5;
			ptr[5] = tmp2 - tmp5;
			ptr[4] = tmp3 + tmp4;
			ptr[3] = tmp3 - tmp4;
		}
	}
}

// full scale (JPEG)
// Y/Cb/Cr[0...255] -> R/G/B[0...255]
// R = 1.000 * (Y) + 1.400 * (Cr - 128)
// G = 1.000 * (Y) - 0.343 * (Cb - 128) - 0.711 (Cr - 128)
// B = 1.000 * (Y) + 1.765 * (Cb - 128)
#define	MULR(a)			((1434 * (a))) 
#define	MULB(a)			((1807 * (a))) 
#define	MULG2(a, b)		((-351 * (a) - 728 * (b)))
#define MULY(a)			((a) << 10)

static inline int mdec_usat8(int v) {
#ifdef HAVE_ARMV6
	int r;
	asm("usat %0,#8,%1" : "=r" (r) : "r" (v));
	return r;
#else
	return v < 0 ? 0 : (v > 255 ? 255 : v);
#endif
}

// The chroma part of the three channels for one Cr/Cb pair, rounding constant included.
// 351 and 728 share the factor 13, which saves a handful of shifts in the G term; the
// products are the same modulo 2^32.
static inline void mdec_chroma(int Cr, int Cb, u32 *c0, u32 *c1, u32 *c2) {
	u32 t = 27 * (u32)Cb + 56 * (u32)Cr;

	*c0 = 1434 * (u32)Cr + (1UL << 19);
	*c1 = (1UL << 19) - 13 * t;
	*c2 = 1807 * (u32)Cb + (1UL << 19);
}

// One pixel: per channel clamp(SCALER(MULY(y) + chroma, 20) + 128). The chroma terms arrive
// with the rounding constant already added, and the sum is unsigned so it wraps exactly as
// the signed one did. k is 128, held in a register because the shifted add takes it as its
// first operand. The three channels are interleaved by hand: left to the compiler, the
// three instructions of one channel come out back to back and each waits for the one
// before it.
static inline void mdec_px(u32 y, u32 c0, u32 c1, u32 c2, u32 k, u32 *r, u32 *g, u32 *b) {
#ifdef HAVE_ARMV6
	u32 t0, t1, t2;
	asm("add %0,%4,%3,lsl #10\n\t"
		"add %1,%5,%3,lsl #10\n\t"
		"add %2,%6,%3,lsl #10\n\t"
		"add %0,%7,%0,asr #20\n\t"
		"add %1,%7,%1,asr #20\n\t"
		"add %2,%7,%2,asr #20\n\t"
		"usat %0,#8,%0\n\t"
		"usat %1,#8,%1\n\t"
		"usat %2,#8,%2"
		: "=&r" (t0), "=&r" (t1), "=&r" (t2)
		: "r" (y), "r" (c0), "r" (c1), "r" (c2), "r" (k));
	*r = t0; *g = t1; *b = t2;
#else
	*r = mdec_usat8(((int)((y << 10) + c0) >> 20) + (int)k);
	*g = mdec_usat8(((int)((y << 10) + c1) >> 20) + (int)k);
	*b = mdec_usat8(((int)((y << 10) + c2) >> 20) + (int)k);
#endif
}

// Two pixels that share a chroma pair, as six bytes: R0 G0 B0 R1 in *w, G1 B1 in *h.
static inline void mdec_pair(const int *y, u32 c0, u32 c1, u32 c2, u32 k, u32 *w, u32 *h) {
	u32 r0, g0, b0, r1, g1, b1;

	mdec_px(y[0], c0, c1, c2, k, &r0, &g0, &b0);
	mdec_px(y[1], c0, c1, c2, k, &r1, &g1, &b1);
	*w = r0 | (g0 << 8) | (b0 << 16) | (r1 << 24);
	*h = g1 | (b1 << 8);
}

// Black and white: Y on all three channels.
static inline void mdec_row4bw(u32 *d, const int *y) {
	u32 p0 = mdec_usat8((int)((u32)y[0] + 128)) * 0x010101;
	u32 p1 = mdec_usat8((int)((u32)y[1] + 128)) * 0x010101;
	u32 p2 = mdec_usat8((int)((u32)y[2] + 128)) * 0x010101;
	u32 p3 = mdec_usat8((int)((u32)y[3] + 128)) * 0x010101;

	d[0] = p0 | (p1 << 24);
	d[1] = (p1 >> 8) | (p2 << 16);
	d[2] = (p2 >> 16) | (p3 << 8);
}

// The output goes out as three words per four pixels (little endian) instead of twelve
// byte stores. image must be word aligned: DMA addresses are masked to words and every
// length is a whole number of words, so it is, and block_buffer is aligned for the same
// reason.
static void yuv2rgb24(int *blk, u8 *image) {
	const int *Crblk = blk;
	const int *Cbblk = blk + DSIZE2;
	const int *Yblk = blk + DSIZE2 * 2;
	u32 *d = (u32 *)image;
	u32 k = 128;
	int x, y;

#ifdef HAVE_ARMV6
	asm("" : "+r" (k));
#endif
	if (!Config.Mdec) {
		// y is the chroma row: it covers pixel rows 2y and 2y + 1. Y1..Y4 follow each
		// other, left half then right half, top blocks then bottom ones. x counts groups
		// of four pixels, that is two chroma samples, written to both rows at once.
		for (y = 0; y < 8; y++, Crblk += 8, Cbblk += 8, d += 12) {
			const int *Yrow = Yblk + (y >> 2) * (DSIZE2 * 2) + (y & 3) * (DSIZE * 2);

			for (x = 0; x < 4; x++, d += 3) {
				const int *Yp = Yrow + (x >> 1) * DSIZE2 + (x & 1) * 4;
				int Cr = Crblk[x * 2], Cb = Cbblk[x * 2];
				u32 c0, c1, c2;
				u32 w0, h0, w1, h1, v0, t0, v1, t1;

				mdec_chroma(Cr, Cb, &c0, &c1, &c2);
				mdec_pair(Yp, c0, c1, c2, k, &w0, &h0);
				mdec_pair(Yp + DSIZE, c0, c1, c2, k, &w1, &h1);
				d[0] = w0;
				d[12] = w1;

				Cr = Crblk[x * 2 + 1]; Cb = Cbblk[x * 2 + 1];
				mdec_chroma(Cr, Cb, &c0, &c1, &c2);
				mdec_pair(Yp + 2, c0, c1, c2, k, &v0, &t0);
				mdec_pair(Yp + DSIZE + 2, c0, c1, c2, k, &v1, &t1);
				d[1] = h0 | (v0 << 16);
				d[2] = (v0 >> 16) | (t0 << 16);
				d[13] = h1 | (v1 << 16);
				d[14] = (v1 >> 16) | (t1 << 16);
			}
		}
	} else {
		for (y = 0; y < 16; y++, d += 12) {
			const int *Yrow = Yblk + (y >> 3) * (DSIZE2 * 2) + (y & 7) * DSIZE;
			mdec_row4bw(d, Yrow);
			mdec_row4bw(d + 3, Yrow + 4);
			mdec_row4bw(d + 6, Yrow + DSIZE2);
			mdec_row4bw(d + 9, Yrow + DSIZE2 + 4);
		}
	}
}
