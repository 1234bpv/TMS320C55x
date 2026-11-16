/*
 * bench_node.c - C55x dspbridge benchmark node (create/execute/delete phases).
 *
 * Modeled on felipec/dsp-dummy (dummy_dsp.c) + the pcmdll/pingdyn structure
 * found in this phone's ROM. The execute phase loops on NODE_getMsg, runs our
 * Q15 kernel `reps` times over buffers in DMM memory, and replies via
 * NODE_putMsg. The ARM side (dsptest.exe through bridgeapi.dll) times the
 * round trip; the node additionally reports its own CLK_gethtime delta so the
 * compute time can be read off a second, independent instrument.
 *
 * Phase function names are BENCH_DSP_* to match the DCD record in
 * bench_dcd.s55 - the loader looks the three phases up by the names written
 * there (without the leading underscore).
 *
 * Large data model (--mem_model:data=large): buffers live in external memory
 * mapped into DSP space via DMM, so 23-bit data pointers are needed - the
 * 16-bit small model used for the standalone kernel compile is not enough.
 *
 * Compute kernels live in bench_dsp.c (linked together).
 * ASCII only: old cl55 preprocessor chokes on non-ASCII bytes.
 */

#include <stddef.h>
#include "node.h"

/* Kernels from bench_dsp.c. */
extern long dsp_q15_dot(const short *a, const short *b, int n);
extern long dsp_q15_fir(const short *x, const short *h, int nsamp, int ntaps);
extern long dsp_blk(const short *a, int n);

/* Shared parameter block: ARM fills buffer addresses (in DSP space) and sizes,
 * the node writes result and its own timing. Layout must match the ARM side.
 * All fields 32-bit (`long` on C55x) so the struct is laid out identically on
 * both sides. */
typedef struct {
    unsigned long a;        /* buffer A address (DSP space) */
    unsigned long b;        /* buffer B */
    unsigned long x;        /* FIR signal */
    unsigned long h;        /* FIR coefficients */
    long          n;        /* length for DOT/BLK */
    long          nsamp;    /* FIR: output samples */
    long          ntaps;    /* FIR: taps */
    long          reps;     /* kernel repetitions (so time >> IPC) */
    long          result;   /* out: checksum / accumulator */
    unsigned long ticks;    /* out: CLK_gethtime delta over the run */
    unsigned long countspms;/* out: high-res timer counts per millisecond */
} bench_params;

/* Message commands. */
#define CMD_SETUP     0u          /* arg_1 = address of bench_params */
#define CMD_DOT       1u
#define CMD_FIR       2u
#define CMD_BLK       3u
#define CMD_EXIT      0x80000000u

/*
 * Канал вимірювання без черги повідомлень.
 *
 * Історичні виклики повідомлень з тодішніми аргументами спричиняли аварії.
 * Це не доказ відсутності API: у вересні розібрано task20/21, STRM передав
 * пакети, DSP NODE get/put повернули 0/1; ARM delivery і RUN cleanup відкриті.
 * Актуальні докази та обмеження: docs/STREAM_RESEARCH.md.
 * Повернене з create значення на ARM теж не потрапляє (перевірено: create
 * повертав 0x1234, а node-create однаково давав 0).
 *
 * Лишається канал, який не потребує ні повідомлень, ні читання пам'яті DSP:
 * ПРОГНАТИ РОБОТУ ВСЕРЕДИНІ create І ВИМІРЯТИ ЧАС НА ARM. Створення вузла
 * синхронне (DoControl(5) + очікування статусу), тож час цього виклику
 * зростає рівно на час обчислення на C55x.
 *
 * Фіксовані накладні (завантаження бібліотеки, RMS-обмін) скорочуються
 * різницею двох прогонів з різним BENCH_CREATE_REPS - тому це саме
 * диференційний вимір, а не абсолютний.
 *
 * Буфер статичний і в .bss вузла: жодної спільної пам'яті з ARM не треба.
 */
#ifndef BENCH_CREATE_REPS
#define BENCH_CREATE_REPS 0
#endif

/* Вибір навантаження на етапі збірки: аргументів у create нема, тож інакше
 * параметр у вузол не передати. Значення мусять збігатися з ARM-боком
 * (src/dsptest.cpp) - там ті самі ядра для чесного порівняння. */
#define W_NONE   0
#define W_DOT16  1               /* Q15 dot-product, апаратний dual-MAC */
#define W_INT32  2               /* 32x32 множення - через _mpyli з бази */
#define W_FP32   3               /* плаваюча кома - через _mpyd/_addd з бази */
#define W_BRANCH 4               /* дані-залежні гілки, "як у застосунку" */
#define W_REGMAC 5               /* MAC без звернень до пам'яті - діагностика */
#define W_INT32M 6               /* 32x32 вручну через три 16x16 */
#define W_FP32M  7               /* fp32 вручну, без __mpyd/__addd */
#define W_DIVC   8               /* ділення оператором / (виклик __divul) */
#define W_DIVM   9               /* ділення вручну зсувом-відніманням */
#define W_CLKP   10              /* вимір частоти DSP через CLK_gethtime */
#define W_FREQ   11              /* прочитати _BRIDGEINIT_DSP_FREQ з бази */
#define W_DOT2   12              /* той самий Q15 dot, але з ДВОХ масивів */

/* Скільки тактів DSP насправді в секунді - невідомо: номінал 220 МГц, а з
 * вимірів виходить у 3-4 рази менше. Прочитати CLK_gethtime на ARM нічим
 * (цей legacy host його не читає), тому значення КОДУЄТЬСЯ В ЧАС: після заміру фаза крутить
 * ще (тики >> 10) повторів того самого ядра. Різниця часу між збіркою з
 * BENCH_PROBE=0 і BENCH_PROBE=1 дає кількість тиків, а поділена на виміряний
 * час - частоту лічильника. */
#ifndef BENCH_PROBE
#define BENCH_PROBE 0
#endif

/* Ручні реалізації. САМЕ ЗАГОЛОВОК, а не окремий модуль: у першій версії вони
 * лежали в bench_math.c, і на кожен елемент ішов виклик функції замість трьох
 * множень - ручний mul32 вийшов ВТРИЧІ повільнішим за компіляторний __mpyli.
 * Міжмодульного інлайнингу cl55 без -pm не робить. */
#include "c55math.h"

#ifndef BENCH_WORKLOAD
#define BENCH_WORKLOAD W_DOT16
#endif

/* Довжина робочого вектора. Параметр збірки, бо від неї залежить, У ЯКИЙ
 * СЕГМЕНТ пам'яті DSP лоадер покладе .bss вузла.
 *
 * Таблиця динамічних сегментів лежить у самій базі, у секції `.dspbridge_mem`
 * (baseimage.dof, символи DYNM_0..DYNM_3), і читається так:
 *
 *   segid=0 DYN_DARAM     base=0x007f00 len=0x00100 (    256 слів)
 *   segid=1 DYN_SARAM     base=0x008008 len=0x0111d (   4381 слово)
 *   segid=2 DYN_EXTERNAL  base=0x0b0000 len=0x70000 ( 458752 слів)
 *   segid=3 DYN_SRAM      base=0x068000 len=0x18000 (  98304 слова)
 *
 * segid для даних - молодший байт поля 30 DCD-запису (bench_dcd.s55).
 *
 * Це пояснює і давню аварію: коли .bss виріс до ~5120 слів (усі три масиви
 * одночасно), він перестав влазити навіть у SARAM (4381), і створення вузла
 * почало давати -2 без діагностики.
 *
 * DARAM - двопортова: два операнди MACM за такт. SARAM - однопортова, звідси
 * виміряні 2 такти на MACM. Щоб потрапити в DARAM, УСЯ .bss має вміститися в
 * 256 слів. */
#ifndef BENCH_CREATE_N
#define BENCH_CREATE_N 1024
#endif

/* Масиви оголошуються ЛИШЕ під своє навантаження. Спершу я тримав усі три в
 * спільному коді - і базовий прогін, який доти стабільно завершувався за 8 мс,
 * почав зависати: .bss вузла виріс з 1024 до ~5120 слів C55x. Пам'ять вузла на
 * DSP обмежена, і надлишок не діагностується помилкою - вузол просто не
 * створюється. Тримати .bss мінімальним - обов'язкова дисципліна. */
static short gBuf[BENCH_CREATE_N];
#if BENCH_WORKLOAD == W_DOT2
/* Другий масив - щоб два операнди MACM бралися з РІЗНИХ адрес, а не з однієї.
 * Виміряно, що W_DOT16 коштує рівно ~2 такти на MACM при 1 такті на регістрову
 * ALU-операцію. Найпростіше пояснення: dsp_q15_dot(gBuf, gBuf, N) читає той
 * самий масив двома вказівниками, а блок пам'яті вузла віддає лише одне
 * звернення за такт. Якщо так - з двома масивами має вийти ~1 такт. Якщо час
 * не зміниться, справа не в конфлікті блоку, а в сталому такті очікування. */
static short gBuf2[BENCH_CREATE_N];
#endif
#if BENCH_WORKLOAD == W_INT32 || BENCH_WORKLOAD == W_INT32M \
 || BENCH_WORKLOAD == W_DIVC  || BENCH_WORKLOAD == W_DIVM
static long  gL[BENCH_CREATE_N];
#endif
#if BENCH_WORKLOAD == W_FP32M
/* Бітові подання float32. Будуються арифметично, БЕЗ жодної операції з
 * плаваючою комою: інакше ініціалізація тягла б за собою __fltid/__mpyd з
 * базового образу, тобто саме те, що ми тут і намагаємось обійти. */
static long  gFB[BENCH_CREATE_N];
#endif
#if BENCH_WORKLOAD == W_FP32
static double gF[BENCH_CREATE_N];    /* на C55x double == float == 32 біти */
#endif

/* Усі результати - глобальні, інакше -o3 викине обчислення як мертві. */
long   gAcc;
#if BENCH_WORKLOAD == W_CLKP
unsigned long gTicks;            /* глобальна, інакше -o3 викине сам вимір */
#endif
#if BENCH_WORKLOAD == W_FREQ
/* Тактова частота DSP так, як її ЗНАЄ ARM-драйвер.
 *
 * `ehwaomap.pdd` містить рядок `_BRIDGEINIT_DSP_FREQ` (docs/ehwaomap.strings.txt)
 * і адресує його з коду - це стандартний крок TI-моста: після завантаження
 * базового образу драйвер знаходить цей символ і ВПИСУЄ туди частоту DSP, щоб
 * DSP/BIOS міг правильно налаштувати таймери. Символ є в docs/base_syms.txt,
 * отже лоадер зв'яже наше посилання з тією самою коміркою.
 *
 * Це прямий доказ проти непрямої оцінки "~60 МГц з машинних операцій": тут
 * значення не виводиться, а читається. Одиниці - за угодою TI кілогерци.
 */
extern unsigned long BRIDGEINIT_DSP_FREQ;
unsigned long gFreq;
#endif
#if BENCH_WORKLOAD == W_FP32
double gFAcc;
#endif

/* Навантаження з умовними переходами. Імітує розбір/фільтрацію, як у
 * застосунках: гілки залежать від даних, тож передбачувач і конвеєр працюють
 * у найгіршому для DSP режимі. C55x має глибокий конвеєр і дорогі переходи,
 * тому саме тут очікується найгірший для нього результат. */
#if BENCH_WORKLOAD == W_BRANCH
static long bench_branch(const short *a, int n)
{
    long acc = 0;
    int i, state = 0;
    for (i = 0; i < n; i++)
        {
        short v = a[i];
        if (v < 0)
            { state = 1; acc -= v; }
        else if (v < 8192)
            { state = 2; acc += v >> 1; }
        else if ((v & 1) != 0)
            { state = 3; acc += v + state; }
        else
            { acc ^= v; }
        if (state == 3 && (acc & 3) == 0)
            acc += 7;
        }
    return acc;
}
#endif

unsigned int BENCH_DSP_create(void)
{
    int i;
    /* УВАГА: лічильник повторів - `long`, а НЕ `int`. На C55x `int` 16-бітний,
     * тож `for (int i = 0; i < 100000; i++)` ніколи не завершується: i доходить
     * до 32767, перевертається в -32768 і цикл крутиться вічно. Саме це
     * виглядало як "DSP завис на довгій задачі" - насправді вузол справно
     * виконував нескінченний цикл. Межа для `int` тут - 32767 повторів. */
    long r;
    long acc = 0;
    unsigned long x = 12345u;

    /* Той самий детермінований LCG, що й на ARM (dspbench.h).
     * Похідні масиви заповнюються лише там, де потрібні: інакше базовий прогін
     * платив би за ініціалізацію, якої в ньому нема сенсу. Ця вартість фіксована
     * (поза циклом повторів), тож у диференційному вимірі вона все одно
     * скорочується. */
    for (i = 0; i < BENCH_CREATE_N; i++)
        {
        x = x * 1664525u + 1013904223u;
        gBuf[i] = (short)(x >> 16);
        }
#if BENCH_WORKLOAD == W_DOT2
    /* Інші значення, ніж у gBuf: інакше компілятор міг би довести рівність
     * масивів. Ціна фіксована (поза циклом повторів), тож у нахилі її нема. */
    for (i = 0; i < BENCH_CREATE_N; i++)
        {
        x = x * 1664525u + 1013904223u;
        gBuf2[i] = (short)(x >> 16);
        }
#endif
#if BENCH_WORKLOAD == W_INT32 || BENCH_WORKLOAD == W_INT32M \
 || BENCH_WORKLOAD == W_DIVC  || BENCH_WORKLOAD == W_DIVM
    for (i = 0; i < BENCH_CREATE_N; i++)
        gL[i] = (long)gBuf[i] * 65537L;
#endif
#if BENCH_WORKLOAD == W_FP32M
    /* Порядок 127 -> значення в [1,2); мантиса з gBuf. Нуль виключено, бо
     * dsp_fmul трактує нульовий порядок як нуль і вийшов би вироджений цикл. */
    for (i = 0; i < BENCH_CREATE_N; i++)
        gFB[i] = (long)(0x3F800000uL
                        | (((unsigned long)(gBuf[i] & 0x7FFF)) << 8));
#endif
#if BENCH_WORKLOAD == W_FP32
    /* Нормування в [-1,1) - НЕ косметика. Спершу тут стояло gBuf[i]*1.000123,
     * тобто значення до ~32767; квадрат дає ~1e9, а сума за 1024 елементи
     * ~3.6e11, що не влазить у 32-бітний long. Перетворення (long)s через
     * __fixdli з таким аргументом валило створення вузла: fp32-прогін давав
     * -2 ЗАВЖДИ при reps>0 (навіть на 144 мс), тоді як reps=0 проходив. */
    for (i = 0; i < BENCH_CREATE_N; i++)
        gF[i] = (double)gBuf[i] * (1.0 / 32768.0);
#endif

    for (r = 0; r < (long)BENCH_CREATE_REPS; r++)
        {
#if BENCH_WORKLOAD == W_DOT16
        /* Маска - діагностична. dsp_q15_dot(gBuf,gBuf,N) - сума квадратів, тобто
         * ОДНЕ Й ТЕ САМЕ додатне число щоразу, і acc переповнює 32-бітний long
         * тим швидше, чим більше повторів. Перевіряємо, чи саме це робить
         * створення вузла детерміновано невдалим для певних значень reps. */
        acc += (dsp_q15_dot(gBuf, gBuf, BENCH_CREATE_N) & 0x3F);
#elif BENCH_WORKLOAD == W_DOT2
        acc += (dsp_q15_dot(gBuf, gBuf2, BENCH_CREATE_N) & 0x3F);
#elif BENCH_WORKLOAD == W_INT32
        {
        int k; long s = 0;
        for (k = 0; k < BENCH_CREATE_N; k++)
            s += gL[k] * gL[k];
        acc += s;
        }
#elif BENCH_WORKLOAD == W_FP32
        {
        int k; double s = 0.0;
        for (k = 0; k < BENCH_CREATE_N; k++)
            s += gF[k] * gF[k];
        gFAcc += s;      /* глобальна, тож -o3 не викине цикл як мертвий */
        }
#elif BENCH_WORKLOAD == W_BRANCH
        acc += bench_branch(gBuf, BENCH_CREATE_N);

#elif BENCH_WORKLOAD == W_REGMAC
        /* Ті самі 1024 MAC, але операнди в регістрах. Різниця з W_DOT16 - це
         * рівно ціна звернень до пам'яті вузла. */
        acc += (dsp_reg_mac(3, 5, BENCH_CREATE_N) & 0x3F);

#elif BENCH_WORKLOAD == W_INT32M
        {
        int k; long s = 0;
        /* XOR, а НЕ "+ (x & 0x3F)". Маска тут була грубою помилкою виміру:
         * dsp_mul32 інлайниться, а молодші 6 біт добутку залежать лише від
         * молодших бітів співмножників - компілятор законно викидав два з трьох
         * часткових добутків. Вийшло "33 MMAC/s", тобто ~2 машинні операції на
         * 32x32 множення, чого не буває. XOR зберігає всі 32 біти (отже жодну
         * частину обчислення не можна прибрати) і не переповнюється. */
        for (k = 0; k < BENCH_CREATE_N; k++)
            s ^= dsp_mul32(gL[k], gL[k]);
        acc += (s & 0x3F);
        }

#elif BENCH_WORKLOAD == W_FP32M
        {
        int k; long s = 0;
        for (k = 0; k < BENCH_CREATE_N; k++)
            s = dsp_fadd(s, dsp_fmul(gFB[k], gFB[k]));
        acc += (s & 0x3F);
        }

#elif BENCH_WORKLOAD == W_DIVC
        {
        int k; long s = 0;
        for (k = 0; k < BENCH_CREATE_N; k++)
            s ^= (long)((unsigned long)gL[k] / 1000003uL);
        acc += (s & 0x3F);
        }

#elif BENCH_WORKLOAD == W_DIVM
        {
        int k; long s = 0;
        for (k = 0; k < BENCH_CREATE_N; k++)
            s ^= (long)dsp_divu32((unsigned long)gL[k], 1000003uL);
        acc += (s & 0x3F);
        }
#endif
        }

#if BENCH_WORKLOAD == W_CLKP
    /* Окремо від головного циклу: тут кількість роботи залежить від виміряного
     * значення, а не від сталої. */
    {
    unsigned long t0 = CLK_gethtime();
    unsigned long ticks;
    long r2;
    for (r = 0; r < (long)BENCH_CREATE_REPS; r++)
        acc += (dsp_q15_dot(gBuf, gBuf, BENCH_CREATE_N) & 0x3F);
    ticks = CLK_gethtime() - t0;
    gTicks = ticks;
#if BENCH_PROBE
    for (r2 = 0; r2 < (long)(ticks >> 10); r2++)
        acc += (dsp_q15_dot(gBuf, gBuf, BENCH_CREATE_N) & 0x3F);
#endif
    }
#endif

#if BENCH_WORKLOAD == W_FREQ
    /* Канал читання той самий, що й у W_CLKP: значення КОДУЄТЬСЯ В ЧАС, бо
     * цей legacy host не реалізує зворотний канал (див. коментар вище).
     *
     *   BENCH_PROBE=0  базова лінія: символ прочитано, роботи нема;
     *   BENCH_PROBE=2  калібрування: рівно 50000 повторів ядра -> ціна повтору;
     *   BENCH_PROBE=1  вимір: (значення >> 2) повторів.
     *
     * Тоді  значення = 4 * (t1 - t0) / ((t2 - t0) / 50000).
     * Зсув на 2 - щоб типове 220000 (кГц) дало ~55000 повторів, тобто час
     * порядку секунди: достатньо довго проти похибки і достатньо коротко, щоб
     * не впертись у стелю очікування на ARM. Обмеження зверху обов'язкове:
     * якщо драйвер раптом пише герци, без нього фаза крутилась би годинами.
     */
    {
#if BENCH_PROBE == 4
    unsigned long v = 100000uL;          /* еталон: те саме, але з ВІДОМИМ v */
#else
    unsigned long v = BRIDGEINIT_DSP_FREQ;
#endif
    unsigned long t0, tcal, q;
    long n;

    gFreq = v;

    /* Самонормування. Перша спроба (кількість повторів = v>>2) дала розкид
     * 2.3x між прогонами, бо час = повтори/швидкість, а швидкість вузла
     * від прогону до прогону не стала. Тут швидкість вимірюється ТУТ ЖЕ,
     * лічильником CLK_gethtime, який тактується системним кварцом (26.8 МГц)
     * і від частоти ядра DSP не залежить (виміряно раніше). Кількість
     * повторів множиться на виміряну швидкість, тож у добутку
     * повтори/швидкість швидкість скорочується і час залежить ЛИШЕ від v. */
    t0 = CLK_gethtime();
    for (n = 0; n < 5000L; n++)
        acc += (dsp_q15_dot(gBuf, gBuf, BENCH_CREATE_N) & 0x3F);
    tcal = CLK_gethtime() - t0;
    if (tcal == 0uL) tcal = 1uL;

#if BENCH_PROBE == 3 || BENCH_PROBE == 4
    if (v > 400000uL) v = 400000uL;      /* інакше v*5000 переповнить 32 біти */
    q = (v * 5000uL) / tcal;             /* повтори на одиницю v */
    for (n = 0; n < (long)(q * 122uL); n++)
        acc += (dsp_q15_dot(gBuf, gBuf, BENCH_CREATE_N) & 0x3F);
#endif
    /* BENCH_PROBE == 5: лише калібрувальний цикл - це базова лінія. */
    }
#endif

    gAcc = acc;
    return 0x8000;               /* RMS success */
}

unsigned int BENCH_DSP_delete(void)
{
    return 0x8000;
}

unsigned int BENCH_DSP_execute(void *env)
{
    dsp_msg_t msg;
    bench_params *p = NULL;
    unsigned char done = 0;
    unsigned char timed;         /* this command ran a kernel */
    unsigned char reply;         /* this command gets an acknowledgement */
    unsigned long t0 = 0;
    long r, acc;

    while (!done) {
        NODE_getMsg(env, &msg, (unsigned)-1);

        acc = 0;
        timed = 0;
        reply = 0;

        switch (msg.cmd) {
        case CMD_SETUP:
            p = (bench_params *)(msg.arg_1);
            reply = 1;           /* ack, so ARM knows the node is alive */
            break;

        case CMD_DOT:
            if (p) {
                timed = 1; reply = 1;
                t0 = CLK_gethtime();
                for (r = 0; r < p->reps; r++)
                    acc += dsp_q15_dot((const short *)p->a,
                                       (const short *)p->b, (int)p->n);
            }
            break;

        case CMD_FIR:
            if (p) {
                timed = 1; reply = 1;
                t0 = CLK_gethtime();
                for (r = 0; r < p->reps; r++)
                    acc += dsp_q15_fir((const short *)p->x,
                                       (const short *)p->h,
                                       (int)p->nsamp, (int)p->ntaps);
            }
            break;

        case CMD_BLK:
            if (p) {
                timed = 1; reply = 1;
                t0 = CLK_gethtime();
                for (r = 0; r < p->reps; r++)
                    acc += dsp_blk((const short *)p->a, (int)p->n);
            }
            break;

        case CMD_EXIT:
            done = 1;
            break;

        default:
            break;
        }

        /* One reply path for all commands: stamp result and DSP-side elapsed
         * time, then acknowledge with the command echoed back so the ARM side
         * can match reply to request. A separate `timed` flag rather than
         * "t0 != 0" - the high-res counter is free-running and legitimately
         * passes through zero. */
        if (timed) {
            p->ticks = CLK_gethtime() - t0;   /* unsigned: survives wrap */
            p->countspms = CLK_countspms();
            p->result = acc;
        }
        if (reply)
            NODE_putMsg(env, NULL, &msg, 0);
    }

    return 0x8000;
}
