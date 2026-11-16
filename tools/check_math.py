"""Перевірка ручної арифметики з src/dsp/bench_math.c.

Результати з DSP прочитати нічим (черга повідомлень мертва, значення з фази
create на ARM не доходить), тож правильність цих реалізацій не можна перевірити
на апараті - лише звіркою алгоритму. Тут кожна функція відтворена рядок-у-рядок
з C, з явним маскуванням до 16/32 біт, і звірена з еталонною арифметикою.

Прогін: python tools/check_math.py
"""
import random
import struct

M32 = 0xFFFFFFFF


def u32(x):
    return x & M32


def s32(x):
    x &= M32
    return x - (1 << 32) if x & 0x80000000 else x


def s16(x):
    x &= 0xFFFF
    return x - (1 << 16) if x & 0x8000 else x


# --- 2. dsp_mul32 -----------------------------------------------------------

def dsp_mul32(a, b):
    a, b = u32(a), u32(b)
    al = a & 0xFFFF
    bl = b & 0xFFFF
    ah = s16(a >> 16)
    bh = s16(b >> 16)
    lo = u32(al * bl)
    mid = u32(u32(ah * bl) + u32(al * bh))
    return s32(lo + u32(mid << 16))


# --- 3. dsp_fmul / dsp_fadd -------------------------------------------------

def f32_bits(x):
    return struct.unpack('<I', struct.pack('<f', x))[0]


def bits_f32(b):
    return struct.unpack('<f', struct.pack('<I', u32(b)))[0]


def dsp_fmul(a, b):
    a, b = u32(a), u32(b)
    ea = (a >> 23) & 0xFF
    eb = (b >> 23) & 0xFF
    sign = (a ^ b) & 0x80000000
    if ea == 0 or eb == 0:
        return 0
    ma = (a & 0x7FFFFF) | 0x800000
    mb = (b & 0x7FFFFF) | 0x800000
    ml, mh = ma & 0xFFFF, (ma >> 16) & 0xFFFF
    nl, nh = mb & 0xFFFF, (mb >> 16) & 0xFFFF
    p = u32(u32(mh * nh) << 16)
    p = u32(p + u32(mh * nl))
    p = u32(p + u32(ml * nh))
    p = u32(p + (u32(ml * nl) >> 16))
    e = ea + eb - 127
    if p & 0x80000000:
        p >>= 8
        e += 1
    else:
        p >>= 7
    if e <= 0:
        return s32(sign)
    if e >= 255:
        return s32(sign | 0x7F7FFFFF)
    return s32(sign | (e << 23) | (p & 0x7FFFFF))


def dsp_fadd(a, b):
    a, b = u32(a), u32(b)
    ea = (a >> 23) & 0xFF
    eb = (b >> 23) & 0xFF
    sa = a & 0x80000000
    sb = b & 0x80000000
    if ea == 0:
        return s32(b)
    if eb == 0:
        return s32(a)
    if eb > ea:
        a, b = b, a
        ea, eb = eb, ea
        sa, sb = sb, sa
    d = ea - eb
    if d > 24:
        return s32(a)
    ma = ((a & 0x7FFFFF) | 0x800000) << 3
    mb = (((b & 0x7FFFFF) | 0x800000) << 3) >> d
    e = ea
    if sa == sb:
        r = ma + mb
        if r & 0x8000000:
            r >>= 1
            e += 1
    else:
        if ma >= mb:
            r = ma - mb
        else:
            r = mb - ma
            sa = sb
        if r == 0:
            return 0
        while (r & 0x4000000) == 0:
            r <<= 1
            e -= 1
            if e <= 0:
                return s32(sa)
    r >>= 3
    if e >= 255:
        return s32(sa | 0x7F7FFFFF)
    if e <= 0:
        return s32(sa)
    return s32(sa | (e << 23) | (r & 0x7FFFFF))


# --- 4. dsp_divu32 ----------------------------------------------------------

def dsp_divu32(num, den):
    num, den = u32(num), u32(den)
    if den == 0:
        return M32
    q = r = 0
    for _ in range(32):
        r = u32((r << 1) | ((num >> 31) & 1))
        num = u32(num << 1)
        q = u32(q << 1)
        if r >= den:
            r = u32(r - den)
            q |= 1
    return q


# --- перевірки --------------------------------------------------------------

def check_mul32(n=200000):
    rnd = random.Random(1)
    bad = 0
    for _ in range(n):
        a = rnd.getrandbits(32)
        b = rnd.getrandbits(32)
        if dsp_mul32(a, b) != s32(a * b):
            bad += 1
    return bad


def check_div(n=100000):
    rnd = random.Random(2)
    bad = 0
    for _ in range(n):
        a = rnd.getrandbits(32)
        b = rnd.getrandbits(rnd.randint(1, 32)) or 1
        if dsp_divu32(a, b) != a // b:
            bad += 1
    return bad


def ulp_err(got_bits, ref):
    """Різниця в ULP між нашим результатом і правильно округленим еталоном."""
    if ref == 0.0:
        return 0 if u32(got_bits) in (0, 0x80000000) else 1 << 30
    ref_bits = f32_bits(ref)
    # порівнюємо як цілі: сусідні float відрізняються на 1 у бітовому поданні
    g = u32(got_bits)
    r = u32(ref_bits)
    if (g ^ r) & 0x80000000:
        return 1 << 30
    return abs((g & 0x7FFFFFFF) - (r & 0x7FFFFFFF))


def check_float(n=200000):
    rnd = random.Random(3)
    worst_mul = worst_add = 0
    for _ in range(n):
        # діапазон навмисно помірний: денормалі й Inf свідомо не підтримані
        x = rnd.uniform(-1e3, 1e3)
        y = rnd.uniform(-1e3, 1e3)
        if x == 0 or y == 0:
            continue
        xb, yb = f32_bits(x), f32_bits(y)
        xf, yf = bits_f32(xb), bits_f32(yb)
        worst_mul = max(worst_mul, ulp_err(dsp_fmul(xb, yb), xf * yf))
        worst_add = max(worst_add, ulp_err(dsp_fadd(xb, yb), xf + yf))
    return worst_mul, worst_add


if __name__ == '__main__':
    bad = check_mul32()
    print('mul32   : %d помилок з 200000' % bad)
    bad = check_div()
    print('divu32  : %d помилок з 100000' % bad)
    wm, wa = check_float()
    print('fmul    : найгірша похибка %d ULP' % wm)
    print('fadd    : найгірша похибка %d ULP' % wa)
