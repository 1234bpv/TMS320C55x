// dsptest.exe — бенчмарк C55x DSP проти ARM1136 на Nokia N95 8GB (OMAP2420).
//
// Демон запускає його без термінала (findings: SymbianDeployDaemon), тож звіт
// іде у файл E:\dsptest.log, який ПК потім забирає через GET.
//
// СТАН: реалізовано ARM-бік бенчмарку — базова лінія, з якою порівнюватиметься
// DSP. Він самодостатній і запускається на апараті вже зараз (DSP не потрібен).
// DSP-бік іде Шляхом A (вузол dspbridge, не відбір заліза): сам вузол уже
// зібрано й зареєстровано під власним UUID — `out/dsp/bench.dll55l`,
// docs/findings.md §15. Тут лишилось написати завантажувач поверх
// bridgeapi.dll за контрактом §14.1 (attach -> node_allocate(UUID) -> create ->
// run -> put/get msg), і тоді ці ж три ядра можна ганяти на DSP.
//
// Прилад — той самий, що довів справжність розгону в сусідньому проєкті:
// User::FastCounter + best-of-N (завада може лише СПОВІЛЬНИТИ, ніколи не
// пришвидшити, тож найкращий із серії — найчистіший). Абсолютна частота — через
// SpinNop з фіксованою вартістю такту, щоб дати і per-clock числа.
//
// Літерали ASCII: GCCE 3.4.3 + 8-бітні дескриптори, кирилиця в рядках не варта
// ризику.

#include <e32base.h>
#include <e32std.h>
#include <e32cmn.h>
#include <f32file.h>
#include <hal.h>

#include "dspbench.h"

_LIT(KLogFile, "E:\\dsptest.log");
_LIT8(KOn,  "ON");
_LIT8(KOff, "off");
_LIT8(KNul, "");
_LIT8(KSkipped, "  (skipped: level 'dev' not requested)");
_LIT8(KDirTag, "  <dir>");
_LIT8(KPending, " (still pending)");
// Наш DOFF-вузол на апараті (кладе туди tools\build.cmd).
_LIT(KNodePath, "E:\\bench.dll55l");
// Штатний динамічний вузол Nokia/TI з ROM — контроль для ord26.
_LIT(KRefNodePath, "Z:\\system\\apps\\ping\\pingdyn.dll55l");
// Базовий образ DSP/BIOS. Динамічний вузол резолвиться проти його символів
// (_NODE_getMsg тощо), тож без нього в контексті завантажувачу ядра нема проти
// чого резолвити — і саме там гинув апарат.
_LIT(KBasePath, "Z:\\resource\\plugins\\baseimage.dof");
// DOFF лише з DCD-секціями нашого вузла, БЕЗ жодної секції, що алокується чи
// вантажиться (tools\build_dcd_stub.cmd). Дослід: ord26 спершу реєструє DCD і
// лише потім кладе образ на DSP — тож у файлі, де класти нема чого, друга
// стадія має пройти вхолосту, а наш UUID усе одно потрапити в DCD.
// Той самий стаб, але з заголовком, поміченим як ВИКОНУВАНИЙ
// (tools\patch_doff_exec.py): прапорці 0x12E3 + точка входу, як у базового
// образу. Секцій, що алокуються чи вантажаться, у ньому нуль, тож класти на
// DSP нічого — перевіряємо саме гіпотезу про прапорці.
_LIT(KStubPath, "E:\\benchdcdx.dll55l");

static RFs gFs;
static RFile gLog;
static TUint32 gFcFreq = 0;      // частота FastCounter, Гц
static TUint32 gCpuMhz = 0;      // виміряна частота ARM, МГц

// Дільник кількості повторів у ядрах. Повні BENCH_*_REPS дають ~9 с суцільного
// 100% ALU, і кожне завантаження апарата, де це крутилось, закінчилось ребутом
// (findings §17.6). Запас у повторах був надмірний: DOT на повних повторах —
// 774 мс при роздільності FastCounter 30 мкс. Ділимо на 10 → ~77 мс, це все ще
// у 2500 разів більше за роздільність, тобто точність не страждає, а
// навантаження падає на порядок. Повний режим лишається за прапорцем 'heavy'.
static TInt gRepDiv = 10;

// Пауза між ядрами, щоб не тримати ALU під навантаженням суцільним блоком.
static void Breathe()
    {
    User::After(200000);         // 200 мс
    }

static void Log(const TDesC8 &aLine)
    {
    gLog.Write(aLine);
    gLog.Write(_L8("\r\n"));
    gLog.Flush();
    }

static void LogF(TRefByValue<const TDesC8> aFmt, ...)
    {
    VA_LIST list;
    VA_START(list, aFmt);
    TBuf8<512> buf;
    buf.AppendFormatList(aFmt, list);
    VA_END(list);
    Log(buf);
    }

// --- прилад часу ------------------------------------------------------------

static TUint32 ElapsedUs(TUint32 aStart, TUint32 aEnd)
    {
    TUint32 d = aEnd - aStart;         // беззнакове віднімання переживає обгортання
    if (gFcFreq == 0)
        return 0;
    return (TUint32)(((TUint64)d * 1000000u) / gFcFreq);
    }

// Абсолютна частота: 256 незалежних додавань поспіль — ARM1136 одноконвеєрний,
// кожне коштує рівно такт, залежностей і промахів I-cache нема. Метод із ocprobe.
const TUint32 KNopCyclesPerIter = 258;   // 256 add + subs + bne

static void SpinNop(TUint32 aIter)
    {
    __asm__ __volatile__(
        "1:                  \n"
        ".rept 256           \n"
        "   add r3, r3, #1   \n"
        ".endr               \n"
        "   subs %0, %0, #1  \n"
        "   bne  1b          \n"
        : "+r" (aIter) : : "r3", "cc");
    }

static TUint32 MeasureMhz()
    {
    const TUint32 kIter = 400000;
    TUint32 t0 = User::FastCounter();
    SpinNop(kIter);
    TUint32 t1 = User::FastCounter();
    TUint32 us = ElapsedUs(t0, t1);
    return us ? (TUint32)(((TUint64)kIter * KNopCyclesPerIter) / us) : 0;
    }

// --- дослід: губернатор DVFS під час роботи DSP ------------------------------
//
// Гіпотеза. DSP тактується як CORE/3, а CORE ходить удвічі (330/660 МГц) під
// губернатором. Під час нашого виміру головний потік стоїть у User::After і
// чекає на статус create - тобто з боку губернатора процес ВИГЛЯДАЄ ЯК
// ПРОСТІЙ, хоча C55x у цей час рахує. Якщо OPP при цьому опускається, DSP
// падає разом із CORE, і всі наші «такти на операцію» пораховані для частоти,
// якої в момент виміру не було.
//
// Прилад той самий SpinNop, що вимірює частоту ARM: MPU теж живиться від CORE,
// тож просідання OPP видно прямо. Два режими:
//   armwatch - міряти короткими сплесками з паузами (навантаження ~8%), щоб
//              ПОБАЧИТИ частоту, майже не змінюючи умов;
//   armbusy  - крутити безперервно, щоб СКАСУВАТИ простій.
// Різниця часу create між ними і є відповіддю.
enum TArmMode { EArmIdle = 0, EArmWatch = 1, EArmBusy = 2 };
static TInt gArmMode = EArmIdle;

const TInt KMonSlots = 24;
static volatile TInt gMonStop = 0;
static TUint32 gMonMhz[KMonSlots];
static TInt    gMonCount = 0;      // скільки слотів заповнено
static TUint32 gMonTotal = 0;      // скільки замірів усього
static TUint32 gMonMin = 0;
static TUint32 gMonMax = 0;

// Один замір - 20000 витків по 258 тактів = ~5.2 М тактів, тобто ~16 мс на
// 330 МГц. Достатньо коротко, щоб у режимі watch не створювати помітного
// навантаження, і достатньо довго проти роздільності FastCounter (~30 мкс).
static TInt ArmMonThread(TAny *)
    {
    const TUint32 kIter = 20000;
    while (!gMonStop)
        {
        TUint32 t0 = User::FastCounter();
        SpinNop(kIter);
        TUint32 t1 = User::FastCounter();
        TUint32 us = ElapsedUs(t0, t1);
        if (us)
            {
            TUint32 mhz = (TUint32)(((TUint64)kIter * KNopCyclesPerIter) / us);
            if (gMonTotal == 0 || mhz < gMonMin) gMonMin = mhz;
            if (mhz > gMonMax) gMonMax = mhz;
            ++gMonTotal;
            if (gMonCount < KMonSlots)
                gMonMhz[gMonCount++] = mhz;
            }
        if (gArmMode == EArmWatch)
            User::After(200000);      // 200 мс простою між замірами
        }
    return 0;
    }

static RThread gMon;
static TBool gMonRunning = EFalse;

static void MonStart()
    {
    if (gArmMode == EArmIdle)
        return;
    gMonStop = 0;
    gMonCount = 0;
    gMonTotal = 0;
    gMonMin = 0;
    gMonMax = 0;
    // Пріоритет НИЖЧИЙ за звичайний: потік має заповнювати простій, а не
    // конкурувати з головним потоком, який чекає на статус create.
    if (gMon.Create(_L("dspmon"), ArmMonThread, 8192, NULL, NULL) != KErrNone)
        {
        Log(_L8("    [mon] thread create FAILED"));
        return;
        }
    gMon.SetPriority(EPriorityLess);
    gMon.Resume();
    gMonRunning = ETrue;
    }

static void MonStop()
    {
    if (!gMonRunning)
        return;
    TRequestStatus st;
    gMon.Logon(st);
    gMonStop = 1;
    User::WaitForRequest(st);
    gMon.Close();
    gMonRunning = EFalse;

    TBuf8<256> line;
    line.Append(_L8("    [mon] ARM MHz:"));
    for (TInt i = 0; i < gMonCount && line.Length() < 200; ++i)
        line.AppendFormat(_L8(" %u"), gMonMhz[i]);
    Log(line);
    LogF(_L8("    [mon] mode=%d samples=%u min=%u MHz max=%u MHz"),
         gArmMode, gMonTotal, gMonMin, gMonMax);
    }

// --- еталонні ядра на ARM (Q15 fixed-point) ---------------------------------
//
// Написані на прямому C, щоб чесно лягли на набір команд ARM1136 (без NEON — у
// цьому ядрі його нема).

// ВАЖЛИВО про ширину акумулятора. Перша редакція рахувала на ARM у TInt64,
// тоді як C55x-бік (bench_dsp.c) накопичує у 32-бітний `long`, який компілятор
// тримає в 40-бітному AC. Це було НЕ матчено: ARM платив за 64-бітні додавання
// там, де DSP платить за 32-бітні, і порівняння виходило на користь DSP.
// Тепер обидва боки — 32 біти. Результат тотожний: 40-бітний акумулятор C55x
// зрізається до молодших 32 біт, а 32-бітне додавання на ARM — те саме за
// модулем 2^32. Перевірка: контрольні суми мусять лишитись ті самі, що й у
// 64-бітній редакції (85055090 / f5735100 / 22056190).

// Q15 dot-product: sum(a[i]*b[i]). Показовий для dual-MAC C55x.
static TInt32 KernelDot(const TInt16 *a, const TInt16 *b, TInt n)
    {
    TInt32 acc = 0;
    for (TInt i = 0; i < n; ++i)
        acc += (TInt32)a[i] * (TInt32)b[i];
    return acc;
    }

// Q15 FIR: y[k] = sum_{t=0..TAPS-1} h[t]*x[k+t], результат у Q15 (>>15).
// Повертає контрольну суму виходу, щоб довести ідентичність обчислення.
static TInt32 KernelFir(const TInt16 *x, const TInt16 *h, TInt nsamp, TInt ntaps)
    {
    TInt32 chk = 0;
    for (TInt k = 0; k < nsamp; ++k)
        {
        TInt32 acc = 0;
        for (TInt t = 0; t < ntaps; ++t)
            acc += (TInt32)h[t] * (TInt32)x[k + t];
        TInt16 y = (TInt16)(acc >> 15);        // назад у Q15
        chk += y;
        }
    return chk;
    }

// Нейтральне 16-бітне ціле: block[i] = a[i]*3 + 7, сума. Поза сильним боком DSP —
// показує межу, де dual-MAC не допомагає.
static TInt32 KernelBlk(const TInt16 *a, TInt n)
    {
    TInt32 acc = 0;
    for (TInt i = 0; i < n; ++i)
        acc += (TInt16)((TInt16)(a[i] * 3) + 7);
    return acc;
    }

// --- запуск бенчмарку -------------------------------------------------------

// Best-of-N: повертає найменший час (найчистіший прогін) у мкс і кладе
// контрольну суму в aChk.
static TUint32 BestUs(TUint32 (*run)(TInt64 &), TInt aRuns, TInt64 &aChk)
    {
    TUint32 best = 0xFFFFFFFFu;
    for (TInt i = 0; i < aRuns; ++i)
        {
        TInt64 chk = 0;
        TUint32 us = run(chk);
        if (us < best)
            best = us;
        aChk = chk;
        }
    return best == 0xFFFFFFFFu ? 0 : best;
    }

// Друкує рядок результату: MMAC/s (мега-множень-накопичень/с) у сотих + per-clock.
// Контрольна сума — молодші 32 біти в hex: 64-бітні специфікатори у форматтері
// дескриптора ненадійні, а зрізана сума однаково збігається, якщо ARM і DSP
// рахують ідентично.
static void Report(const TDesC8 &aName, TUint64 aMacs, TUint32 aUs, TInt64 aChk)
    {
    // MMAC/s == MACs/us. У сотих, цілочисельно.
    TUint32 mmac100 = aUs ? (TUint32)(((TUint64)aMacs * 100u) / aUs) : 0;
    // MAC/такт у тисячних: macs/(us*MHz).
    TUint32 macPerClk1000 = (aUs && gCpuMhz)
        ? (TUint32)(((TUint64)aMacs * 1000u) / ((TUint64)aUs * gCpuMhz)) : 0;
    LogF(_L8("  %S: %u us, %u.%02u MMAC/s, %u.%03u MAC/clk, chk=%08x"),
         &aName, aUs,
         mmac100 / 100, mmac100 % 100,
         macPerClk1000 / 1000, macPerClk1000 % 1000,
         (TUint32)aChk);
    }

// Буфери — статичні вказівники, щоб ядра-обгортки (сигнатура без аргументів для
// BestUs) їх бачили.
static TInt16 *gA = NULL;
static TInt16 *gB = NULL;
static TInt16 *gX = NULL;      // FIR-сигнал, довжина SAMPLES+TAPS
static TInt16 *gH = NULL;      // FIR-коефіцієнти

static TUint32 RunDot(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TInt32 acc = 0;
    for (TInt r = 0; r < BENCH_DOT_REPS / gRepDiv; ++r)
        acc += KernelDot(gA, gB, BENCH_DOT_N);
    TUint32 t1 = User::FastCounter();
    aChk = acc;
    return ElapsedUs(t0, t1);
    }

// Той самий KernelDot, але на робочому наборі, що вміщується в L1D
// (BENCH_DOTS_N). Дає компонент, вільний від впливу шини пам'яті.
static TUint32 RunDotS(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TInt32 acc = 0;
    for (TInt r = 0; r < BENCH_DOTS_REPS / gRepDiv; ++r)
        acc += KernelDot(gA, gB, BENCH_DOTS_N);
    TUint32 t1 = User::FastCounter();
    aChk = acc;
    return ElapsedUs(t0, t1);
    }

static TUint32 RunFir(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TInt32 acc = 0;
    for (TInt r = 0; r < BENCH_FIR_REPS / gRepDiv; ++r)
        acc += KernelFir(gX, gH, BENCH_FIR_SAMPLES, BENCH_FIR_TAPS);
    TUint32 t1 = User::FastCounter();
    aChk = acc;
    return ElapsedUs(t0, t1);
    }

static TUint32 RunBlk(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TInt32 acc = 0;
    for (TInt r = 0; r < BENCH_BLK_REPS / gRepDiv; ++r)
        acc += KernelBlk(gA, BENCH_BLK_N);
    TUint32 t1 = User::FastCounter();
    aChk = acc;
    return ElapsedUs(t0, t1);
    }

// --- дзеркала навантажень create-каналу -------------------------------------
//
// Побайтові копії того, що виконує вузол у src/dsp/bench_node.c (W_INT32,
// W_FP32, W_BRANCH). Джерело навмисно тримається дослівно однаковим: будь-яка
// "оптимізація" тут зробить порівняння недійсним.
//
// Дані ті самі: gA заповнений тим самим LCG, що й gBuf на DSP.
// Окремий вхідний буфер, бо вузол засіває свій gBuf сідом 12345, а не
// BENCH_LCG_SEED. Для int32/fp32 це байдуже, а для гілкового ядра - ні:
// послідовність переходів визначається саме даними, тож на інших числах
// вимірювалося б інше навантаження.
#define BENCH_CREATE_SEED  12345u
static TInt16 *gS = NULL;      // те саме, що gBuf на DSP
static TInt32 *gL = NULL;      // int32-операнди
static float  *gF = NULL;      // fp32-операнди (на C55x це `double` = 32 біти)

static TInt32 KernelInt32(const TInt32 *a, TInt n)
    {
    TInt32 s = 0;
    for (TInt k = 0; k < n; ++k)
        s += a[k] * a[k];
    return s;
    }

static float KernelFp32(const float *a, TInt n)
    {
    float s = 0.0f;
    for (TInt k = 0; k < n; ++k)
        s += a[k] * a[k];
    return s;
    }

// Дані-залежні гілки: скінченний автомат, як у розборі повідомлень. Саме той
// профіль, що переважає в застосунках, і найгірший для конвеєра DSP.
static TInt32 KernelBranch(const TInt16 *a, TInt n)
    {
    TInt32 acc = 0;
    TInt state = 0;
    for (TInt i = 0; i < n; ++i)
        {
        TInt16 v = a[i];
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

static TUint32 RunInt32(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TInt32 acc = 0;
    for (TInt r = 0; r < BENCH_INT32_REPS / gRepDiv; ++r)
        acc += KernelInt32(gL, BENCH_CREATE_N);
    TUint32 t1 = User::FastCounter();
    aChk = acc;
    return ElapsedUs(t0, t1);
    }

static TUint32 RunFp32(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    float acc = 0.0f;
    for (TInt r = 0; r < BENCH_FP32_REPS / gRepDiv; ++r)
        acc += KernelFp32(gF, BENCH_CREATE_N);
    TUint32 t1 = User::FastCounter();
    aChk = (TInt32)acc;
    return ElapsedUs(t0, t1);
    }

// Дзеркало ділення. XOR, а не сума: на DSP-боці накопичення сумою з маскою
// дозволяло компілятору викинути частину обчислення, тож обидва боки
// накопичують так, щоб жоден біт результату не був зайвим.
static TUint32 RunDiv(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TUint32 s = 0;
    for (TInt r = 0; r < BENCH_DIV_REPS / gRepDiv; ++r)
        for (TInt k = 0; k < BENCH_CREATE_N; ++k)
            s ^= (TUint32)gL[k] / 1000003u;
    TUint32 t1 = User::FastCounter();
    aChk = (TInt32)s;
    return ElapsedUs(t0, t1);
    }

static TUint32 RunBranch(TInt64 &aChk)
    {
    TUint32 t0 = User::FastCounter();
    TInt32 acc = 0;
    for (TInt r = 0; r < BENCH_BRANCH_REPS / gRepDiv; ++r)
        acc += KernelBranch(gS, BENCH_CREATE_N);
    TUint32 t1 = User::FastCounter();
    aChk = acc;
    return ElapsedUs(t0, t1);
    }

static TInt AllocBuffers()
    {
    gA = (TInt16 *)User::Alloc(BENCH_DOT_N * sizeof(TInt16));
    gB = (TInt16 *)User::Alloc(BENCH_DOT_N * sizeof(TInt16));
    gX = (TInt16 *)User::Alloc((BENCH_FIR_SAMPLES + BENCH_FIR_TAPS) * sizeof(TInt16));
    gH = (TInt16 *)User::Alloc(BENCH_FIR_TAPS * sizeof(TInt16));
    gS = (TInt16 *)User::Alloc(BENCH_CREATE_N * sizeof(TInt16));
    gL = (TInt32 *)User::Alloc(BENCH_CREATE_N * sizeof(TInt32));
    gF = (float  *)User::Alloc(BENCH_CREATE_N * sizeof(float));
    if (!gA || !gB || !gX || !gH || !gS || !gL || !gF)
        return KErrNoMemory;
    // Детерміновано, ТИМ САМИМ кодом, що використає DSP-бік (dspbench.h).
    BenchFillQ15(gA, BENCH_DOT_N, BENCH_LCG_SEED);
    BenchFillQ15(gB, BENCH_DOT_N, BENCH_LCG_SEED ^ 0xA5A5A5A5u);
    BenchFillQ15(gX, BENCH_FIR_SAMPLES + BENCH_FIR_TAPS, 0xC0FFEEu);
    BenchFillQ15(gH, BENCH_FIR_TAPS, 0x1234u);

    // Похідні масиви - точно тими самими виразами, що й у BENCH_DSP_create().
    BenchFillQ15(gS, BENCH_CREATE_N, BENCH_CREATE_SEED);
    for (TInt i = 0; i < BENCH_CREATE_N; ++i)
        {
        gL[i] = (TInt32)gS[i] * 65537;
        // Нормовано так само, як на DSP: ненормовані значення переповнюють
        // 32-бітне ціле при зведенні в квадрат і сумуванні (див. bench_node.c).
        gF[i] = (float)gS[i] * (1.0f / 32768.0f);
        }
    return KErrNone;
    }

static void FreeBuffers()
    {
    User::Free(gA); User::Free(gB); User::Free(gX); User::Free(gH);
    User::Free(gS); User::Free(gL); User::Free(gF);
    gA = gB = gX = gH = gS = NULL;
    gL = NULL; gF = NULL;
    }

static void BenchmarkArm()
    {
    LogF(_L8("--- ARM1136 baseline (Q15 fixed-point), rep divisor %d ---"),
         gRepDiv);
    // Робочі набори: показуємо явно, бо саме вони пояснюють, чому DOT і BLK
    // поводяться інакше за DOT-S і FIR (16-КБ L1D в ARM1136).
    LogF(_L8("  working sets: DOT %d KB, DOT-S %d KB, FIR %d KB, BLK %d KB"),
         (BENCH_DOT_N * 2 * 2) / 1024,
         (BENCH_DOTS_N * 2 * 2) / 1024,
         ((BENCH_FIR_SAMPLES + BENCH_FIR_TAPS) * 2 + BENCH_FIR_TAPS * 2) / 1024,
         (BENCH_BLK_N * 2) / 1024);
    if (AllocBuffers() != KErrNone)
        {
        Log(_L8("  buffer alloc failed - skipped"));
        return;
        }

    // Розігрів: перший прогін ловить промахи кешу і можливий підйом частоти
    // губернатором DVFS, у залік не йде.
    TInt64 warm = 0;
    RunDot(warm);
    Breathe();

    TInt64 chk = 0;
    TUint32 us;

    us = BestUs(RunDot, 3, chk);
    Report(_L8("DOT  "), (TUint64)BENCH_DOT_N * (BENCH_DOT_REPS / gRepDiv), us, chk);

    Breathe();
    us = BestUs(RunDotS, 3, chk);
    Report(_L8("DOT-S"), (TUint64)BENCH_DOTS_N * (BENCH_DOTS_REPS / gRepDiv),
           us, chk);

    Breathe();
    us = BestUs(RunFir, 3, chk);
    Report(_L8("FIR  "),
           (TUint64)BENCH_FIR_SAMPLES * BENCH_FIR_TAPS * (BENCH_FIR_REPS / gRepDiv),
           us, chk);

    Breathe();
    us = BestUs(RunBlk, 3, chk);
    Report(_L8("BLK  "), (TUint64)BENCH_BLK_N * (BENCH_BLK_REPS / gRepDiv), us, chk);

    // Дзеркала create-каналу. Для INT32/FP32 одиниця - множення-накопичення,
    // як і вище. Для BRANCH множень нема взагалі, тож колонка "MMAC/s" читається
    // як МЕГАЕЛЕМЕНТІВ/с (оброблених відліків); підписано явно, щоб число не
    // сплутали з обчислювальною пропускною здатністю.
    Breathe();
    us = BestUs(RunInt32, 3, chk);
    Report(_L8("INT32"),
           (TUint64)BENCH_CREATE_N * (BENCH_INT32_REPS / gRepDiv), us, chk);

    Breathe();
    us = BestUs(RunFp32, 3, chk);
    Report(_L8("FP32 "),
           (TUint64)BENCH_CREATE_N * (BENCH_FP32_REPS / gRepDiv), us, chk);

    Breathe();
    us = BestUs(RunBranch, 3, chk);
    Report(_L8("BRNCH"),
           (TUint64)BENCH_CREATE_N * (BENCH_BRANCH_REPS / gRepDiv), us, chk);
    Breathe();
    us = BestUs(RunDiv, 3, chk);
    Report(_L8("DIV32"),
           (TUint64)BENCH_CREATE_N * (BENCH_DIV_REPS / gRepDiv), us, chk);
    Log(_L8("  (DIV32: 'MMAC/s' = Mdiv/s)"));
    Log(_L8("  (BRNCH: 'MMAC/s' = Melem/s - гілки, а не множення)"));

    FreeBuffers();
    }

// --- огляд середовища -------------------------------------------------------

static void ProbeHal()
    {
    Log(_L8("--- HAL ---"));
    struct TEntry { HALData::TAttribute iAttr; const char *iName; };
    const TEntry attrs[] =
        {
            { HALData::ECPUSpeed,             "ECPUSpeed(kHz)"       },
            { HALData::EFastCounterFrequency, "EFastCounterFreq(Hz)" },
            { HALData::ECPU,                  "ECPU"                 },
            { HALData::ECPUABI,               "ECPUABI"              },
            { HALData::EMemoryRAM,            "EMemoryRAM"           }
        };
    const TInt n = sizeof(attrs) / sizeof(attrs[0]);
    for (TInt i = 0; i < n; ++i)
        {
        TInt v = 0;
        TInt r = HAL::Get(attrs[i].iAttr, v);
        TPtrC8 nm((const TUint8 *)attrs[i].iName);
        if (r == KErrNone)
            LogF(_L8("%S = %d"), &nm, v);
        else
            LogF(_L8("%S -> err %d"), &nm, r);
        }
    }

// Перелічує завантажені драйвери — щоб бачити DSP-стек (ebridgeutil, mailboxipc,
// activeadsp...) у живій системі й мати точні зареєстровані імена для Фази 1+.
static void ListDsp()
    {
    Log(_L8("--- loaded LDDs (DSP stack of interest) ---"));
    TFindLogicalDevice findL(_L("*"));
    TFullName name;
    TInt count = 0;
    while (findL.Next(name) == KErrNone)
        {
        TBuf8<256> n8; n8.Copy(name.Left(250));
        LogF(_L8("  LDD %S"), &n8);
        ++count;
        }
    LogF(_L8("  total LDDs: %d"), count);
    }

// --- проба DSP-стеку ---------------------------------------------------------
//
// Мета — звірити статичний реверс (docs/findings.md §16) з ЖИВИМ апаратом,
// перш ніж будувати на ньому завантажувач:
//   1) чи вантажиться `bridgeapi.dll` і чи збігаються адреси 39 ординалів з
//      тими, що ми витягли з ROM-дампа (доводить, що дамп = прошивка апарата);
//   2) чи відкривається LDD `D32HWA` (kernel-бік мосту) — і з якою версією;
//   3) чи пускає нас туди capability-гейт (драйвер перевіряє MultimediaDD).
// Усе — тільки читання й відкриття каналу; нічого на DSP не вантажимо.

_LIT(KBridgeApi, "bridgeapi.dll");
_LIT(KBal,       "bal.dll");
_LIT(KMemMapper, "dspmemmapper.dll");
// Зареєстроване ім'я LDD — саме "Hwa" (так його бачить TFindLogicalDevice, і
// так лежить літерал у bridgeapi @0x80A61DB8). "D32HWA" — рядок з бінарника
// драйвера, але НЕ ім'я каналу: перша проба з ним дала KErrNotFound.
_LIT(KHwaLdd,    "Hwa");
_LIT(KHwaPdd,    "Hwa.Omap");

// Адреси ординалів з ROM-дампа (findings §10). Якщо збігаються з Lookup() на
// апараті — статичний аналіз стоїть на тому самому коді, що виконується.
const TUint32 KRomOrdinal[] =
    {
    0x80A5E483u, 0x80A5E539u, 0x80A5E68Fu, 0x80A5E6BBu, 0x80A5E561u,
    0x80A5E585u, 0x80A5E677u, 0x80A5E4DFu, 0x80A5E43Fu, 0x80A5E409u,
    0x80A5E401u, 0x80A5E401u, 0x80A5E433u, 0x80A5E433u, 0x80A5DC71u,
    0x80A5DC37u, 0x80A5DCDBu, 0x80A5DCA1u, 0x80A5DD0Bu, 0x80A5DD1Bu,
    0x80A5DC2Du, 0x80A5DC2Du, 0x80A5DC35u, 0x80A5DC35u, 0x80A5DAE1u,
    0x80A5D533u, 0x80A5D9B1u, 0x80A5DAC3u, 0x80A5D901u, 0x80A5D87Fu,
    0x80A5D9EDu, 0x80A5D751u, 0x80A5D4FDu, 0x80A5DAA3u, 0x80A5D955u,
    0x80A5D4C9u, 0x80A5D4C9u, 0x80A5D4D9u, 0x80A5D4D9u
    };
const TInt KOrdinalCount = sizeof(KRomOrdinal) / sizeof(KRomOrdinal[0]);

// Канал до kernel-боку мосту. DoCreate/DoControl/DoRequest у RBusLogicalChannel
// захищені, тож потрібен свій нащадок — стандартний прийом для чужого LDD.
// Сирий доступ до вже відкритого каналу: підставляємо чужий хендл через
// RHandleBase::SetHandle і шлемо DoControl напряму, як це робить bal.
class RRawChannel : public RBusLogicalChannel
    {
public:
    TInt Ctl(TInt aFn, TAny *a1, TAny *a2) { return DoControl(aFn, a1, a2); }
    };

class RHwaChannel : public RBusLogicalChannel
    {
public:
    TInt Open(const TVersion &aVer, TBool aWithPdd, TInt aUnit)
        {
        return DoCreate(KHwaLdd, aVer, aUnit, aWithPdd ? &KHwaPdd : NULL,
                        NULL, EOwnerThread);
        }
    TInt Control(TInt aFn, TAny *a1 = NULL, TAny *a2 = NULL)
        { return DoControl(aFn, a1, a2); }
    void Request(TInt aFn, TRequestStatus &aStatus, TAny *a1 = NULL, TAny *a2 = NULL)
        { DoRequest(aFn, aStatus, a1, a2); }
    };

// Вантажить DLL і (для bridgeapi) звіряє таблицю ординалів з ROM-дампом.
// Якщо aKeep != NULL — бібліотека лишається відкритою у виклика́ча.
static void ProbeLibrary(const TDesC &aName, TBool aDumpOrdinals,
                         RLibrary *aKeep = NULL)
    {
    RLibrary local;
    RLibrary &lib = aKeep ? *aKeep : local;
    TInt r = lib.Load(aName);
    TBuf8<64> n8; n8.Copy(aName);
    if (r != KErrNone)
        {
        LogF(_L8("  %S -> load err %d"), &n8, r);
        return;
        }
    LogF(_L8("  %S loaded, uid3=%08x"), &n8, lib.Type()[2].iUid);

    if (aDumpOrdinals)
        {
        // Скільки ординалів реально є: Lookup() віддає NULL за межею.
        TInt live = 0;
        for (TInt i = 1; i <= 64; ++i)
            if (lib.Lookup(i) != NULL)
                live = i;
        LogF(_L8("    highest live ordinal: %d (ROM dump says %d)"),
             live, KOrdinalCount);

        TInt mismatch = 0;
        for (TInt i = 1; i <= KOrdinalCount; ++i)
            {
            TLibraryFunction f = lib.Lookup(i);
            TUint32 a = (TUint32)f;
            // Lookup віддає адресу з THUMB-бітом; ROM-таблиця вже з ним.
            if (a != KRomOrdinal[i - 1])
                {
                if (mismatch < 6)
                    LogF(_L8("    ord %2d: live %08x != rom %08x"),
                         i, a, KRomOrdinal[i - 1]);
                ++mismatch;
                }
            }
        if (mismatch == 0)
            Log(_L8("    ALL 39 ordinal addresses match the ROM dump"));
        else
            LogF(_L8("    %d/%d ordinals differ from the ROM dump"),
                 mismatch, KOrdinalCount);
        }
    if (!aKeep)
        lib.Close();
    }

// Проба класу C з bridgeapi (ординали 25-39) — того, що тримає канал до
// драйвера. Реверс (findings §16):
//   ord 36/37  ctor  — обнуляє об'єкт (використані зсуви 0,4,8,12,16)
//   ord 32     TInt Open(TInt aProcId, TInt aFlag, const TAny* aAttrs24)
//              aProcId мусить бути < 2 (інакше -5): 0 = C55x DSP, 1 = IVA;
//              зберігається у [this+16]. aFlag == 1 додатково вантажить
//              базовий образ через ord 26 — НЕ чіпаємо, бо база вже піднята
//              аудіо-стеком; беремо 0, тобто «лише відкрити канал».
//   ord 33     Close — DoControl(0x04000001) + RHandleBase::Close
// Усе в user-mode: хибний виклик валить лише наш процес, апарат цілий.
static void ProbeBridgeOpen(RLibrary &aLib, TBool aLoadNode, TBool aUseRef,
                            TInt aFlag, TBool aLoadBase, TBool aBaseOnly,
                            TBool aStub, TBool aTask, TBool aReg, TBool aLock,
                            TBool aDump, TBool aDcdOp)
    {
    Log(_L8("  -- class C (ordinals 25-39) open attempt --"));

    // Послідовність — не наш винахід, а дзеркало CBal::Open (@0x80A4165C):
    //   ctorC; ord32(C, 0, 0, NULL); if (!err) ord9(A, C);
    // і CBal::Shutdown (@0x80A41608): ord10(A); ord33(C).
    // Ми свідомо НЕ повторюємо Load/FreePhysicalDevice з CBal: драйвер уже в
    // системі, а саме ці виклики — головна підозра у ребутах (findings §17.7).
    TLibraryFunction ctorC = aLib.Lookup(36);
    TLibraryFunction ctorA = aLib.Lookup(11);
    TLibraryFunction open  = aLib.Lookup(32);
    TLibraryFunction bind  = aLib.Lookup(9);
    TLibraryFunction closeA = aLib.Lookup(10);
    TLibraryFunction close = aLib.Lookup(33);
    if (!ctorC || !ctorA || !open || !bind || !closeA || !close)
        {
        Log(_L8("    lookup failed - skipped"));
        return;
        }

    // Об'єкти із запасом: реверс дає 20 Б для C і 8 Б для A, беремо по 256 і
    // нулі навколо, щоб будь-яке поле поза нашою моделлю читалось як 0.
    TUint8 obj[256];
    TUint8 objA[256];
    Mem::FillZ(obj, sizeof(obj));
    Mem::FillZ(objA, sizeof(objA));

    ((void (*)(TAny *))ctorC)(obj);
    ((void (*)(TAny *))ctorA)(objA);
    LogF(_L8("    after ctor: %08x %08x %08x %08x %08x"),
         *(TUint32 *)(obj + 0), *(TUint32 *)(obj + 4), *(TUint32 *)(obj + 8),
         *(TUint32 *)(obj + 12), *(TUint32 *)(obj + 16));

    // aFlag: 0 = лише відкрити канал; 1 = плюс довантажити БАЗОВИЙ ОБРАЗ.
    // Перші два прогони йшли з 0 і валили апарат на ord26 — і наш вузол, і
    // штатний ping однаково. Причина найімовірніше та, що динамічний вузол
    // резолвиться проти символів бази (_NODE_getMsg тощо), а в нашому
    // контексті бази не було. З aFlag=1 ord32 сам питає драйвер про шлях до
    // бази (DoControl) і вантажить її через ord26 — тобто робить те, що ми
    // пропускали.
    LogF(_L8("    >>> about to call ord32 Open(proc=0, flag=%d)"), aFlag);
    TInt r = ((TInt (*)(TAny *, TInt, TInt, TAny *))open)(obj, 0, aFlag, NULL);
    LogF(_L8("    ord32 Open(proc=0 DSP, flag=%d, NULL) -> %d"), aFlag, r);
    LogF(_L8("    object now: %08x %08x %08x %08x %08x"),
         *(TUint32 *)(obj + 0), *(TUint32 *)(obj + 4), *(TUint32 *)(obj + 8),
         *(TUint32 *)(obj + 12), *(TUint32 *)(obj + 16));

    if (r != KErrNone)
        {
        if (r == -5)
            Log(_L8("    -5 = KErrNotSupported: aProcId rejected"));
        return;
        }

    Log(_L8("    BRIDGE OPEN - user-side DSP processor handle acquired"));

    // ord9(A, C) — те, що CBal робить одразу після вдалого Open: прив'язує
    // об'єкт класу A (UUID/DCD) до відкритого процесора.
    TInt br = ((TInt (*)(TAny *, TAny *))bind)(objA, obj);
    LogF(_L8("    ord9 bind(A, C) -> %d"), br);

    // ord 26 = завантаження DOFF + DCD-реєстрація. Сигнатуру видно з того, як
    // її кличе сам ord 32 (@0x80A5D854): r0 = this, r1 = вказівник на TDes16
    // зі шляхом, r2 = 0. Тобто TInt Load(const TDesC16& aPath, TInt aFlags).
    // Це той самий шлях, яким у ядро потрапляє наш `.dcd_register` з UUID
    // 967CBF11-... (findings §15).
    if (aLoadNode)
        {
        TLibraryFunction load = aLib.Lookup(26);
        if (!load)
            Log(_L8("    ord26 missing - node load skipped"));
        else
            {
            // Контрольна точка ПЕРЕД викликом: лог пишеться з Flush() по рядку,
            // тож якщо апарат помре всередині ord26, останній рядок у файлі
            // однозначно вкаже, на чому саме. Перший прогін показав, що смерть
            // настає саме тут (після "ord9 bind -> 0" файл обривався).
            // Спершу база (якщо просили): динамічний вузол посилається на
            // символи базового образу (_NODE_getMsg тощо), і без неї
            // завантажувач у ядрі не має проти чого резолвити.
            if (aLoadBase)
                {
                const TDesC16 &bp = KBasePath();
                TBuf8<80> b8; b8.Copy(bp.Left(70));
                LogF(_L8("    >>> ord26 Load BASE: %S"), &b8);
                TInt br2 = ((TInt (*)(TAny *, const TDesC16 *, TInt))load)
                           (obj, &bp, 0);
                LogF(_L8("    ord26 Load(base) -> %d"), br2);
                if (br2 != KErrNone)
                    {
                    Log(_L8("    base load failed - not attempting the node"));
                    ((void (*)(TAny *))closeA)(objA);
                    ((void (*)(TAny *))close)(obj);
                    return;
                    }
                }

            if (aBaseOnly)
                {
                // A::ord4(TInt* aOut) — з реверсу: повертає -6 (KErrArgument)
                // на NULL, інакше кладе одне слово з внутрішнього об'єкта A.
                // У bal саме це значення йде у 20-байтовий блок створення
                // задачі, тобто це посилання на DCD. Виклик user-mode і суто
                // читаючий: найгірше, що може статись — паніка нашого процесу.
                // Реєстрація нашого UUID через DCD-стаб (без коду).
                if (aStub)
                    {
                    const TDesC16 &sp2 = KStubPath();
                    TBuf8<64> s8; s8.Copy(sp2);
                    LogF(_L8("    >>> ord26 Load DCD-STUB: %S"), &s8);
                    TInt sr = ((TInt (*)(TAny *, const TDesC16 *, TInt))load)
                              (obj, &sp2, 0);
                    LogF(_L8("    ord26 Load(stub) -> %d"), sr);
                    }

                // Спроба покласти в A наш UUID. ord6 бере рівно один аргумент
                // (пролог зберігає лише r0,r1) і під м'ютексом заповнює
                // 304-байтовий блок властивостей — це схоже на пошук вузла в
                // DCD за ідентифікатором. Формат — канонічний dsp_uuid:
                // {u32, u16, u16, u8, u8, u8[6]}, little-endian.
                // 967CBF11-B90E-4B54-A4D3-3C84249EE1DA
                TLibraryFunction find6 = aLib.Lookup(6);
                if (find6)
                    {
                    TUint8 uuid[16];
                    uuid[0]=0x11; uuid[1]=0xBF; uuid[2]=0x7C; uuid[3]=0x96;
                    uuid[4]=0x0E; uuid[5]=0xB9;
                    uuid[6]=0x54; uuid[7]=0x4B;
                    uuid[8]=0xA4; uuid[9]=0xD3;
                    uuid[10]=0x3C; uuid[11]=0x84; uuid[12]=0x24;
                    uuid[13]=0x9E; uuid[14]=0xE1; uuid[15]=0xDA;
                    TInt f = ((TInt (*)(TAny *, TAny *))find6)(objA, uuid);
                    LogF(_L8("    ord6(A, our UUID) -> %d"), f);

                    // ПРАВИЛЬНИЙ контроль. Перша спроба брала UUID вузла PING,
                    // мовляв "він точно зареєстрований" — це було хибно:
                    // DCD-записи з'являються лише коли відповідний файл
                    // завантажено через ord26, а ми вантажили саму лише базу.
                    // Тому беремо UUID, які реєструє САМА база (її
                    // .dcd_register, findings §15.1):
                    //   EAP_TASK          6130D910-1C2B-40E4-94A4-14EBB314340E
                    //   TESTSERVER_NOKIA  898FCE1D-29B6-454F-9E24-057F81D792ED
                    // Якщо на них ord6 віддасть 0 - формат виклику правильний,
                    // а -6 на нашому означає просто "немає в DCD".
                    TUint8 eap[16];
                    eap[0]=0x10; eap[1]=0xD9; eap[2]=0x30; eap[3]=0x61;
                    eap[4]=0x2B; eap[5]=0x1C;
                    eap[6]=0xE4; eap[7]=0x40;
                    eap[8]=0x94; eap[9]=0xA4;
                    eap[10]=0x14; eap[11]=0xEB; eap[12]=0xB3;
                    eap[13]=0x14; eap[14]=0x34; eap[15]=0x0E;
                    LogF(_L8("    ord6(A, EAP_TASK from base) -> %d"),
                         ((TInt (*)(TAny *, TAny *))find6)(objA, eap));

                    // Чи реєструє систему DCD аудіо-плагінів САМА (на старті
                    // або при піднятті аудіо)? Якщо так - наш вузол треба
                    // подавати тим самим шляхом, а не через ord26.
                    //   PCM_NOKIA        C36A3EBC-09E5-4BED-8FD8-858818315206
                    //   MP3DECSOCKET_TI  B11A1F21-4B05-11D6-B0DC-00C04F1FC036
                    TUint8 pcm[16];
                    pcm[0]=0xBC; pcm[1]=0x3E; pcm[2]=0x6A; pcm[3]=0xC3;
                    pcm[4]=0xE5; pcm[5]=0x09;
                    pcm[6]=0xED; pcm[7]=0x4B;
                    pcm[8]=0x8F; pcm[9]=0xD8;
                    pcm[10]=0x85; pcm[11]=0x88; pcm[12]=0x18;
                    pcm[13]=0x31; pcm[14]=0x52; pcm[15]=0x06;
                    LogF(_L8("    ord6(A, PCM_NOKIA plugin) -> %d"),
                         ((TInt (*)(TAny *, TAny *))find6)(objA, pcm));

                    TUint8 mp3[16];
                    mp3[0]=0x21; mp3[1]=0x1F; mp3[2]=0x1A; mp3[3]=0xB1;
                    mp3[4]=0x05; mp3[5]=0x4B;
                    mp3[6]=0xD6; mp3[7]=0x11;
                    mp3[8]=0xB0; mp3[9]=0xDC;
                    mp3[10]=0x00; mp3[11]=0xC0; mp3[12]=0x4F;
                    mp3[13]=0x1F; mp3[14]=0xC0; mp3[15]=0x36;
                    LogF(_L8("    ord6(A, MP3 plugin) -> %d"),
                         ((TInt (*)(TAny *, TAny *))find6)(objA, mp3));

                    TUint8 ts[16];
                    ts[0]=0x1D; ts[1]=0xCE; ts[2]=0x8F; ts[3]=0x89;
                    ts[4]=0xB6; ts[5]=0x29;
                    ts[6]=0x4F; ts[7]=0x45;
                    ts[8]=0x9E; ts[9]=0x24;
                    ts[10]=0x05; ts[11]=0x7F; ts[12]=0x81;
                    ts[13]=0xD7; ts[14]=0x92; ts[15]=0xED;
                    LogF(_L8("    ord6(A, TESTSERVER from base) -> %d"),
                         ((TInt (*)(TAny *, TAny *))find6)(objA, ts));
                    }

                // --- проба DCD-родини ioctl --------------------------------
                //
                // Уся DCD-робота bridgeapi йде через два диспетчери
                // (0x80A5DB2A синхронний, 0x80A5DB42 асинхронний), які
                // формують код як 0x0400000C + 18 + op. Карта операцій,
                // знята з місць виклику:
                //   op0 0x0400001E   op1 0x0400001F  опис вузла (за ним ord6)
                //   op2 0x04000020   op3 0x04000021  перелік    (за ним ord1)
                //   op4 0x04000022   op5 0x04000023  РОЗБІР ФАЙЛА в DCD
                //
                // op5 - саме те, чого бракує: він наповнює user-side DCD, і
                // якщо його вдасться покликати напряму, ми обійдемо ord26 з
                // його смертельною стадією завантаження образу.
                //
                // Ця родина на кривих аргументах апарат НЕ валить (перевірено
                // на fn=4 і 0x0400000D) - віддає помилку. Тому пробуємо всі
                // шість, спершу з нульовими аргументами (щоб побачити, які
                // взагалі приймаються), потім op5 зі шляхом.
                if (aDcdOp)
                    {
                    RRawChannel raw;
                    raw.SetHandle(*(TInt *)obj);
                    for (TInt op = 0; op <= 5; ++op)
                        {
                        TInt a1 = 0, a2 = 0;
                        TInt rc = raw.Ctl(0x0400001E + op, &a1, &a2);
                        LogF(_L8("    dcd op%d (0x%08x) null args -> %d"),
                             op, 0x0400001E + op, rc);
                        }

                    // Оригінал кличе op5 як DoControl(chan=[loader+52],
                    // a1=[loader+48], a2=0), де loader - 60-байтовий блок за
                    // [C+12], тобто в НАШІЙ купі. Тож просто читаємо його і
                    // беремо звідти справжні аргументи, замість вгадувати.
                    TInt loader = *(TInt *)((TUint8 *)obj + 12);
                    LogF(_L8("    loader block @%08x"), loader);
                    if (loader)
                        {
                        const TUint8 *lp = (const TUint8 *)loader;
                        for (TInt row = 0; row < 4; ++row)
                            {
                            TBuf8<80> h;
                            for (TInt b = 0; b < 16; ++b)
                                h.AppendFormat(_L8("%02x"), lp[row * 16 + b]);
                            LogF(_L8("      +%02x %S"), row * 16, &h);
                            }
                        TInt a1 = *(TInt *)(lp + 48);
                        TInt ch = *(TInt *)(lp + 52);
                        LogF(_L8("      [+48]=%08x  [+52]=%08x"), a1, ch);

                        TInt rc5 = raw.Ctl(0x04000023, (TAny *)a1, 0);
                        LogF(_L8("    dcd op5 with loader[+48] -> %d"), rc5);
                        }

                    // --- ПРЯМИЙ виклик розбору, минаючи ord26 --------------
                    //
                    // 0x80A5F0D4 - це рівно "розбір файла + реєстрація в
                    // user-side DCD". Завантаження образу на DSP (те, що
                    // кладе ядро) робиться ОКРЕМО, власними RFs/RFile далі в
                    // ord26. Функція не експортована, але bridgeapi - XIP:
                    // адреси фіксовані, і ми вже звірили всі 39 ординалів з
                    // ROM-дампом бітово, тож внутрішня адреса так само дійсна.
                    //
                    // ord26 обгортає її парою lock/unlock на тому ж об'єкті -
                    // повторюємо і це. Виклик user-mode: хибна сигнатура
                    // вб'є лише наш процес.
                    if (loader)
                        {
                        typedef void (*TLockFn)(TAny *);
                        typedef TInt (*TParseFn)(TAny *, const TDesC16 *);
                        TLockFn lock2   = (TLockFn)0x80A5EFA1;   // +1 = Thumb
                        TLockFn unlock2 = (TLockFn)0x80A5EF97;
                        TParseFn parse  = (TParseFn)0x80A5F0D5;

                        TBuf16<64> np2;
                        np2.Copy(KNodePath);
                        Log(_L8("    >>> direct parse 0x80A5F0D4 on our node"));
                        lock2((TAny *)loader);
                        TInt pr = parse((TAny *)loader, &np2);
                        unlock2((TAny *)loader);
                        LogF(_L8("    direct parse -> %d"), pr);

                        TUint8 u5[16];
                        u5[0]=0x11; u5[1]=0xBF; u5[2]=0x7C; u5[3]=0x96;
                        u5[4]=0x0E; u5[5]=0xB9; u5[6]=0x54; u5[7]=0x4B;
                        u5[8]=0xA4; u5[9]=0xD3; u5[10]=0x3C; u5[11]=0x84;
                        u5[12]=0x24; u5[13]=0x9E; u5[14]=0xE1; u5[15]=0xDA;
                        // ord7 замість ord6: він робить те саме, плюс кладе у
                        // вузол ДЕСКРИПТОР АРГУМЕНТІВ СТВОРЕННЯ
                        // (0x80A5E0BE зберігає Ptr() і довжину). RMS_createNode
                        // їх очікує, і саме їх бракувало - без них fn=6
                        // завершувався -2 однаково і в нас, і на штатному
                        // вузлі. Наш вузол аргументів не використовує, тож
                        // достатньо порожнього, але валідного дескриптора.
                        static TBuf8<4> createArgs;
                        createArgs.Zero();
                        TInt f5 = ((TInt (*)(TAny *, TAny *, const TDesC8 *))
                                   aLib.Lookup(7))(objA, u5, &createArgs);
                        LogF(_L8("    ord7(A, our UUID, args) -> %d"), f5);
                        if (f5 != KErrNone)
                            {
                            f5 = ((TInt (*)(TAny *, TAny *))aLib.Lookup(6))
                                 (objA, u5);
                            LogF(_L8("    fallback ord6 -> %d"), f5);
                            }

                        // ord6 працює через [A+4], а розбір наповнив об'єкт
                        // [C+12]. Якщо це різні сховища, шукати треба саме в
                        // тому, куди клали. Кличемо внутрішні enumerate/getdef
                        // (ті самі, що вживає ord26) прямо на loader.
                        LogF(_L8("    A[0]=%08x A[4]=%08x loader=%08x"),
                             *(TInt *)objA, *(TInt *)(objA + 4), loader);

                        typedef TInt (*TEnumFn)(TAny *, TInt, TAny *);
                        typedef TInt (*TDefFn)(TAny *, const TAny *, TInt,
                                               TAny *);
                        TEnumFn en = (TEnumFn)0x80A5F56D;
                        TDefFn  gd = (TDefFn)0x80A5F5C3;

                        for (TInt ix = 0; ix < 4; ++ix)
                            {
                            TUint8 uo[16];
                            Mem::FillZ(uo, sizeof(uo));
                            TInt er2 = en((TAny *)loader, ix, uo);
                            if (er2 != KErrNone)
                                {
                                LogF(_L8("      enum(loader,%d) -> %d"),
                                     ix, er2);
                                continue;
                                }
                            TBuf8<48> uh;
                            for (TInt b = 0; b < 16; ++b)
                                uh.AppendFormat(_L8("%02x"), uo[b]);
                            LogF(_L8("      enum(loader,%d) -> 0  %S"),
                                 ix, &uh);
                            }

                        // Третій аргумент getdef - ТИП об'єкта DCD. Значення
                        // 3/4/5, які перебирає гілка 0x80A5E6DC, - це
                        // бібліотеки фаз (CREATELIB/EXECUTELIB/DELETELIB) з
                        // dspbridge; 0 = вузол, 1 = процесор, 2 = бібліотека.
                        // Динамічному вузлу потрібні не лише запис вузла, а й
                        // записи бібліотек - перевіряємо, які з них є.
                        for (TInt ty = 0; ty <= 5; ++ty)
                            {
                            TUint8 def[320];
                            Mem::FillZ(def, sizeof(def));
                            TInt dr = gd((TAny *)loader, u5, ty, def);
                            if (dr != KErrNone)
                                {
                                LogF(_L8("      getdef(type=%d) -> %d"),
                                     ty, dr);
                                continue;
                                }
                            TBuf8<100> dh;
                            for (TInt b = 0; b < 32; ++b)
                                dh.AppendFormat(_L8("%02x"), def[b]);
                            LogF(_L8("      getdef(type=%d) -> 0  %S"),
                                 ty, &dh);
                            LogF(_L8("        props[288..295] "
                                     "%02x%02x%02x%02x %02x%02x%02x%02x"),
                                 def[288], def[289], def[290], def[291],
                                 def[292], def[293], def[294], def[295]);
                            }
                        if (f5 == KErrNone)
                            {
                            TInt ref2 = 0;
                            TInt g5 = ((TInt (*)(TAny *, TInt *))aLib.Lookup(4))
                                      (objA, &ref2);
                            LogF(_L8("    OUR NODE IS IN THE DCD; ord4 -> %d, "
                                     "ref=%08x"), g5, ref2);

                            // І одразу створюємо задачу ДЛЯ НАШОГО вузла - тим
                            // самим викликом, який уже спрацював на вузлі бази
                            // (fn=4, TBuf8<20>, ref у слові 2).
                            if (g5 == KErrNone && ref2)
                                {
                                TBuf8<20> par;
                                par.SetMax();
                                TInt *pp = (TInt *)par.Ptr();
                                pp[0] = 0; pp[1] = 0; pp[2] = ref2;
                                pp[3] = 0; pp[4] = 0;
                                TInt outh = 0;
                                Log(_L8("    >>> create task for OUR node"));
                                TInt cr2 = raw.Ctl(4, &par, &outh);
                                LogF(_L8("    DoControl(4) -> %d, "
                                         "taskHandle=%08x"), cr2, outh);
                                if (cr2 == KErrNone)
                                    {
                                    Log(_L8("    *** OUR C55x NODE HAS A TASK "
                                            "ON THE DSP ***"));

                                    // ПОВНА послідовність із bal (0x80A41E26):
                                    //   fn=4  створити задачу -> handle
                                    //   fn=5  СТВОРИТИ ВУЗОЛ на DSP (async!)
                                    //         + WaitForRequest
                                    //   fn=6  далі
                                    // Крок fn=5 я спершу пропустив: у розгортці
                                    // він повертав 0, але я не чекав на статус,
                                    // тобто асинхронну частину не завершував.
                                    // ЧАС створення вузла - це і є наш вимір:
                                    // усередині create на C55x крутиться
                                    // Q15-ядро BENCH_CREATE_REPS разів.
                                    static TRequestStatus cst2;
                                    cst2 = KRequestPending;
                                    // Дослід про губернатор: монітор стартує
                                    // ДО ct0 і зупиняється ПІСЛЯ ct1, тобто
                                    // накриває рівно те вікно, у якому рахує
                                    // C55x.
                                    MonStart();
                                    TUint32 ct0 = User::FastCounter();
                                    TInt c5 = raw.Ctl(5, (TAny *)outh, &cst2);
                                    LogF(_L8("    DoControl(5) node-create "
                                             "-> %d"), c5);
                                    // Стеля очікування має бути ЗАВІДОМО
                                    // більша за найдовше навантаження, інакше
                                    // вимір показує не роботу DSP, а власний
                                    // таймаут. Спіймано на fp32/branch: обидва
                                    // дали однакові 4.7 с - рівно 300 тиків по
                                    // ~15.6 мс (гранулярність нанокернела, а не
                                    // замовлені 10 мс).
                                    // 2400 * 50 мс = 120 с замовленого часу;
                                    // за фактичною гранулярністю ~62 мс це
                                    // приблизно 150 с. Зовнішній EXEC має
                                    // окрему, явно задану стелю очікування.
                                    for (TInt w = 0; w < 2400 &&
                                         cst2 == KRequestPending; ++w)
                                        User::After(50000);   // ~62 мс -> ~150 с
                                    TUint32 ct1 = User::FastCounter();
                                    MonStop();
                                    LogF(_L8("    node-create WALL TIME: "
                                             "%u us"), ElapsedUs(ct0, ct1));
                                    LogF(_L8("    node-create status: %d%S"),
                                         cst2.Int(),
                                         cst2 == KRequestPending
                                             ? &KPending() : &KNul());
                                    if (cst2 == KErrNone)
                                        Log(_L8("    *** NODE CREATED ON THE "
                                                "C55x ***"));

                                    // --- обмін повідомленнями з вузлом -----
                                    //
                                    // Клас B будується точно як у bal
                                    // (0x80A41E2E): [B+0] = хендл задачі,
                                    // [B+4..15] = копія C[0..11] (канал).
                                    // Розмір 16 Б.
                                    //
                                    // ord16 -> 0x0C000001 (put), ord18 ->
                                    // 0x0C000002 (get); обидва синхронні
                                    // (усередині WaitForRequest). Кличемо саме
                                    // ординали, а не сирий ioctl: структуру
                                    // для ядра будує сам bridgeapi.
                                    //
                                    // Наш вузол на CMD_SETUP (cmd=0) відповідає
                                    // завжди - тож успішний put+get і буде
                                    // доказом, що BENCH_DSP_execute крутиться
                                    // на C55x.
                                    TUint8 objB[64];
                                    Mem::FillZ(objB, sizeof(objB));
                                    *(TInt *)objB = outh;
                                    Mem::Copy(objB + 4, obj, 12);

                                    // bal працює з вузлом НЕ через ord15..18
                                    // (він їх навіть не імпортує), а через
                                    // родину задачі, у формі
                                    //   DoControl(канал = B+4, fn, handle,
                                    //             &status) + WaitForRequest
                                    // з fn = 0x08000007 (bal ord28) і
                                    // 0x08000008 (bal @0x80A41A11).
                                    // Обидві - з перевіреного безпечного
                                    // діапазону 0..17. Раніше вони давали
                                    // -18/-2 саме тому, що вузол не був
                                    // створений; тепер він створений.
                                    RRawChannel bch;
                                    bch.SetHandle(*(TInt *)(objB + 4));
                                    const TInt kNodeFns[] = { 7, 8 };
                                    for (TInt n = 0; n < 2; ++n)
                                        {
                                        static TRequestStatus nst;
                                        nst = KRequestPending;
                                        TInt nr = bch.Ctl(
                                            0x08000000 + kNodeFns[n],
                                            (TAny *)outh, &nst);
                                        for (TInt w = 0; w < 15 &&
                                             nst == KRequestPending; ++w)
                                            User::After(100000);
                                        LogF(_L8("    node fn %d -> %d, "
                                                 "status %d%S"),
                                             kNodeFns[n], nr, nst.Int(),
                                             nst == KRequestPending
                                                 ? &KPending() : &KNul());
                                        }
                                    bch.SetHandle(0);

                                    // bal одразу після створення робить
                                    // DoControl(fn=6, taskHandle, &status) +
                                    // WaitForRequest - це запуск задачі.
                                    //
                                    // TRequestStatus СТАТИЧНИЙ: якщо драйвер
                                    // завершить запит після виходу з функції,
                                    // він писатиме у живу пам'ять, а не в
                                    // знищений кадр стека (урок сусіднього
                                    // проєкту). І не блокуємось назавжди -
                                    // чекаємо обмежено й дивимось на статус.
                                    static TRequestStatus st;
                                    st = KRequestPending;
                                    TInt sr = raw.Ctl(6, (TAny *)outh, &st);
                                    LogF(_L8("    DoControl(6) start -> %d"),
                                         sr);
                                    for (TInt w = 0; w < 20 &&
                                         st == KRequestPending; ++w)
                                        User::After(100000);   // 100 мс
                                    LogF(_L8("    status after wait: %d%S"),
                                         st.Int(),
                                         st == KRequestPending
                                             ? &KPending() : &KNul());

                                    // Родину задачі БІЛЬШЕ НЕ МЕСТИ НАОСЛІП:
                                    // розгортка 0..21 дійшла до fn 18 і поклала
                                    // апарат. Карта того, що встигло пройти, —
                                    // у findings §19; fn 18+ не чіпати.
                                    static TUint8 safe[64];
                                    Mem::FillZ(safe, sizeof(safe));
                                    // fn 3 віддає 268-байтовий блок даних вузла.
                                    // Форма - строго як у bal (0x80A41A63):
                                    // TBuf8<268>, дані за +8. Раніше я подав
                                    // сюди сирий 64-байтовий буфер; ядро
                                    // прочитало з нього сміттєву довжину, і
                                    // "адреси DSP", які я побачив, могли бути
                                    // артефактом. Тепер - справжній дескриптор.
                                    (void)safe;
                                    TBuf8<268> ni;
                                    ni.SetMax();
                                    ni.FillZ();
                                    TInt nir = raw.Ctl(0x08000003,
                                                       (TAny *)outh, &ni);
                                    LogF(_L8("    node info (fn 3) -> %d"), nir);
                                    if (nir == KErrNone)
                                        {
                                        const TUint8 *nb = ni.Ptr();
                                        for (TInt row = 0; row < 6; ++row)
                                            {
                                            TBuf8<80> h;
                                            for (TInt b = 0; b < 16; ++b)
                                                h.AppendFormat(_L8("%02x"),
                                                               nb[row * 16 + b]);
                                            LogF(_L8("      +%02x %S"),
                                                 row * 16, &h);
                                            }
                                        }
                                    }
                                }
                            }
                        }

                    // І варіант зі шляхом, у формі TBuf (не TPtr - урок fn=4).
                    TBuf16<64> path;
                    path.Copy(KNodePath);
                    LogF(_L8("    dcd op5 with TBuf16 path -> %d"),
                         raw.Ctl(0x04000023, &path, 0));

                    TUint8 u4[16];
                    u4[0]=0x11; u4[1]=0xBF; u4[2]=0x7C; u4[3]=0x96;
                    u4[4]=0x0E; u4[5]=0xB9; u4[6]=0x54; u4[7]=0x4B;
                    u4[8]=0xA4; u4[9]=0xD3; u4[10]=0x3C; u4[11]=0x84;
                    u4[12]=0x24; u4[13]=0x9E; u4[14]=0xE1; u4[15]=0xDA;
                    LogF(_L8("    ord6(A, our UUID) after op5 -> %d"),
                         ((TInt (*)(TAny *, TAny *))aLib.Lookup(6))(objA, u4));
                    raw.SetHandle(0);
                    }

                // --- дамп описів зареєстрованих вузлів ---------------------
                //
                // ord1(this, aIndex, aOut) = перелічити об'єкт №aIndex,
                // отримати його опис і скопіювати виклика́чу **152 байти**
                // (`memcpy(aOut, buf304, 0x98)` @0x80A5E4C2). Саме з цього
                // опису ord26 будує запис реєстрації: UUID = байти 0..15,
                // а шукані властивості = байти **16..47** (findings §18).
                //
                // База вже зареєструвала свої об'єкти, а їхні DCD-записи ми
                // знаємо текстом (§15.1) — тож дамп дає пряме зіставлення
                // "текстове поле -> зсув у props", без здогадів.
                if (aDump)
                    {
                    TLibraryFunction enum1 = aLib.Lookup(1);
                    if (enum1)
                        {
                        for (TInt idx = 0; idx < 6; ++idx)
                            {
                            TUint8 nd[256];
                            Mem::FillZ(nd, sizeof(nd));
                            TInt er = ((TInt (*)(TAny *, TInt, TAny *))enum1)
                                      (objA, idx, nd);
                            if (er != KErrNone)
                                {
                                LogF(_L8("    ord1(idx=%d) -> %d"), idx, er);
                                continue;
                                }
                            TBuf8<200> h;
                            for (TInt b = 0; b < 48; ++b)
                                h.AppendFormat(_L8("%02x"), nd[b]);
                            LogF(_L8("    ord1(idx=%d) -> 0"), idx);
                            LogF(_L8("      [0..47]  %S"), &h);
                            h.Zero();
                            for (TInt b = 48; b < 96; ++b)
                                h.AppendFormat(_L8("%02x"), nd[b]);
                            LogF(_L8("      [48..95] %S"), &h);
                            }
                        }
                    }

                // --- реєстрація через ord26 з ЗАБЛОКОВАНИМ файлом ----------
                //
                // Порядок дій усередині ord26 (findings §18): розбір файла й
                // DCD-реєстрація йдуть ПЕРШИМИ, і аж потім - завантаження
                // образу на DSP, яке на переміщуваному DOFF кладе ядро.
                // Образ ord26 відкриває звичайним RFile::Open(fs, name, 1)
                // (EFileShareReadersOnly). Якщо ми тримаємо той самий файл
                // відкритим ЕКСКЛЮЗИВНО, це відкриття зобов'язане впасти -
                // тобто ord26 має повернути помилку вже після реєстрації, не
                // дійшовши до небезпечної стадії.
                if (aLock)
                    {
                    RFile lock;
                    TInt lr = lock.Open(gFs, KNodePath,
                                        EFileRead | EFileShareExclusive);
                    LogF(_L8("    lock our node exclusively -> %d"), lr);
                    if (lr == KErrNone)
                        {
                        const TDesC16 &np = KNodePath();
                        Log(_L8("    >>> ord26 on the LOCKED node"));
                        TInt nr = ((TInt (*)(TAny *, const TDesC16 *, TInt))load)
                                  (obj, &np, 0);
                        LogF(_L8("    ord26(locked node) -> %d"), nr);
                        lock.Close();

                        TUint8 u3[16];
                        u3[0]=0x11; u3[1]=0xBF; u3[2]=0x7C; u3[3]=0x96;
                        u3[4]=0x0E; u3[5]=0xB9;
                        u3[6]=0x54; u3[7]=0x4B;
                        u3[8]=0xA4; u3[9]=0xD3;
                        u3[10]=0x3C; u3[11]=0x84; u3[12]=0x24;
                        u3[13]=0x9E; u3[14]=0xE1; u3[15]=0xDA;
                        LogF(_L8("    ord6(A, our UUID) after -> %d"),
                             ((TInt (*)(TAny *, TAny *))find6)(objA, u3));
                        }
                    }

                // --- пряма DCD-реєстрація нашого UUID ----------------------
                //
                // ord26 реєструє об'єкти так (findings §18): будує однозв'язний
                // список 84-байтових записів {next, uuid[16], props[32], ...}
                // і шле DoControl(0x0400000D, &count, head). Оскільки ord26
                // додатково намагається покласти файл на DSP як ВИКОНУВАНИЙ
                // образ (і на переміщуваному DOFF кладе ядро), пробуємо саму
                // лише реєстрацію, зібравши запис власноруч.
                if (aReg)
                    {
                    RRawChannel raw;
                    raw.SetHandle(*(TInt *)obj);
                    TUint8 rec[84];
                    Mem::FillZ(rec, sizeof(rec));
                    rec[4]=0x11; rec[5]=0xBF; rec[6]=0x7C; rec[7]=0x96;
                    rec[8]=0x0E; rec[9]=0xB9;
                    rec[10]=0x54; rec[11]=0x4B;
                    rec[12]=0xA4; rec[13]=0xD3;
                    rec[14]=0x3C; rec[15]=0x84; rec[16]=0x24;
                    rec[17]=0x9E; rec[18]=0xE1; rec[19]=0xDA;
                    TInt count = 1;
                    Log(_L8("    >>> DoControl(0x0400000D) register our UUID"));
                    TInt rr = raw.Ctl(0x0400000D, &count, rec);
                    LogF(_L8("    register -> %d"), rr);
                    raw.SetHandle(0);

                    TUint8 u2[16];
                    u2[0]=0x11; u2[1]=0xBF; u2[2]=0x7C; u2[3]=0x96;
                    u2[4]=0x0E; u2[5]=0xB9;
                    u2[6]=0x54; u2[7]=0x4B;
                    u2[8]=0xA4; u2[9]=0xD3;
                    u2[10]=0x3C; u2[11]=0x84; u2[12]=0x24;
                    u2[13]=0x9E; u2[14]=0xE1; u2[15]=0xDA;
                    TInt after = ((TInt (*)(TAny *, TAny *))find6)(objA, u2);
                    LogF(_L8("    ord6(A, our UUID) after register -> %d"),
                         after);
                    }

                // --- створення задачі на вже зареєстрованому вузлі ---------
                //
                // Відтворюємо те, що робить bal (0x80A41DDC): бере КАНАЛ із
                // об'єкта класу C і шле DoControl(fn=4, дескриптор(20 Б), &out),
                // після чого out = хендл задачі. Канал беремо з [C+0] через
                // RHandleBase::SetHandle і НЕ закриваємо його — він належить
                // об'єкту класу C.
                //
                // Беремо TESTSERVER_NOKIA, а не EAP_TASK: EAP — це вузол
                // аудіо-тракту (еквалайзер), а TESTSERVER за назвою тестовий,
                // тобто менше шансів зачепити живий звук.
                if (aTask)
                    {
                    TUint8 ts2[16];
                    ts2[0]=0x1D; ts2[1]=0xCE; ts2[2]=0x8F; ts2[3]=0x89;
                    ts2[4]=0xB6; ts2[5]=0x29;
                    ts2[6]=0x4F; ts2[7]=0x45;
                    ts2[8]=0x9E; ts2[9]=0x24;
                    ts2[10]=0x05; ts2[11]=0x7F; ts2[12]=0x81;
                    ts2[13]=0xD7; ts2[14]=0x92; ts2[15]=0xED;
                    TInt sel = ((TInt (*)(TAny *, TAny *))find6)(objA, ts2);
                    TInt ref = 0;
                    TInt g3 = ((TInt (*)(TAny *, TInt *))aLib.Lookup(4))
                              (objA, &ref);
                    LogF(_L8("    task: ord6=%d ord4=%d ref=%08x"),
                         sel, g3, ref);

                    // ref - це адреса в НАШІЙ купі (user-side об'єкт, який
                    // ord6 вибрав у DCD), і саме вона йде у створення задачі.
                    // Якщо цю структуру вдасться відтворити самотужки, DCD
                    // перестане бути потрібним узагалі. Тому дампимо її.
                    if (ref)
                        {
                        const TUint8 *rp = (const TUint8 *)ref;
                        for (TInt row = 0; row < 8; ++row)
                            {
                            TBuf8<80> h;
                            for (TInt b = 0; b < 16; ++b)
                                h.AppendFormat(_L8("%02x"), rp[row * 16 + b]);
                            LogF(_L8("      ref+%02x %S"), row * 16, &h);
                            }
                        }

                    if (sel == KErrNone && g3 == KErrNone && ref)
                        {
                        RRawChannel raw;
                        raw.SetHandle(*(TInt *)obj);

                        // ВАЖЛИВО: a1 має бути вказівником на справжній
                        // TBuf8<20>, а не на TPtr8. Обробник ядра
                        // (0x801B4EA4) робить СИРЕ читання 32 байтів з цього
                        // вказівника у власний буфер-дескриптор, тобто чекає
                        // розкладку "8 Б заголовка + 20 Б даних" — саме таку,
                        // яку будує bal (TBufBase8(20,20), дані за +8).
                        // Перша спроба передала TPtr8 (заголовок + вказівник)
                        // і дістала -2 ще на читанні, до будь-якої логіки.
                        struct TVar { TInt w0, w1, w3, w4; const char *n; };
                        const TVar vars[] =
                            {
                                {  0, 0, 0, 0, "{0,0,ref,0,0}"       },
                                { 20, 0, 0, 0, "{20,0,ref,0,0}"      },
                                {  0, 5, 0, 0, "{0,5,ref,0,0}"       },
                                { 20, 5, 0, 0, "{20,5,ref,0,0}"      }
                            };
                        Log(_L8("    >>> DoControl(fn=4) create task"));
                        for (TInt v = 0;
                             v < (TInt)(sizeof(vars) / sizeof(vars[0])); ++v)
                            {
                            TBuf8<20> params;
                            params.SetMax();
                            TInt *p = (TInt *)params.Ptr();
                            p[0] = vars[v].w0; p[1] = vars[v].w1;
                            p[2] = ref;
                            p[3] = vars[v].w3; p[4] = vars[v].w4;
                            TInt out = 0;
                            TInt cr = raw.Ctl(4, &params, &out);
                            TPtrC8 vn((const TUint8 *)vars[v].n);
                            LogF(_L8("      %S -> %d, taskHandle=%08x"),
                                 &vn, cr, out);
                            if (cr == KErrNone)
                                {
                                Log(_L8("      TASK CREATED ON THE DSP"));
                                // КОНТРОЛЬ: той самий запуск (fn=6), але на
                                // штатному вузлі бази. Якщо і тут -2, то
                                // проблема не в нашому вузлі, а в тому, що
                                // fn=6 вимагає ще якихось кроків.
                                static TRequestStatus cst;
                                cst = KRequestPending;
                                TInt csr = raw.Ctl(6, (TAny *)out, &cst);
                                LogF(_L8("      control: DoControl(6) on stock "
                                         "node -> %d"), csr);
                                for (TInt w = 0; w < 20 &&
                                     cst == KRequestPending; ++w)
                                    User::After(100000);
                                LogF(_L8("      control: status -> %d%S"),
                                     cst.Int(),
                                     cst == KRequestPending
                                         ? &KPending() : &KNul());
                                break;
                                }
                            }
                        raw.SetHandle(0);      // не наш хендл - не закриваємо
                        }
                    }

                TLibraryFunction get4 = aLib.Lookup(4);
                if (get4)
                    {
                    TInt out = 0xDEADBEEF;
                    TInt g = ((TInt (*)(TAny *, TInt *))get4)(objA, &out);
                    LogF(_L8("    ord4(A, &out) -> %d, out=%08x"), g, out);
                    TInt g2 = ((TInt (*)(TAny *, TInt *))get4)(objA, NULL);
                    LogF(_L8("    ord4(A, NULL) -> %d (expect -6)"), g2);
                    }
                Log(_L8("    'baseonly': stopping before the node load"));
                ((void (*)(TAny *))closeA)(objA);
                ((void (*)(TAny *))close)(obj);
                Log(_L8("    ord10/ord33 close done (CBal::Shutdown order)"));
                return;
                }

            Log(_L8("    >>> about to call ord26 Load"));
            // &KNodePath() (а не &KNodePath): треба адреса саме TDesC16, а не
            // літерала TLitC16. Розкладка в них збігається, але покладатись на
            // це при виклику через приведений вказівник — зайвий ризик.
            // 'ref' -> той самий виклик, але на ШТАТНОМУ вузлі Nokia з ROM.
            // Це і є розділювальний дослід: якщо він теж валить апарат, винна
            // наша послідовність/аргументи; якщо проходить - винен наш DOFF.
            const TDesC16 &path = aUseRef ? KRefNodePath() : KNodePath();
            TBuf8<80> p8; p8.Copy(path.Left(70));
            LogF(_L8("    target: %S"), &p8);
            TInt lr = ((TInt (*)(TAny *, const TDesC16 *, TInt))load)
                      (obj, &path, 0);
            LogF(_L8("    ord26 Load -> %d"), lr);
            if (lr == KErrNone)
                Log(_L8("    OUR NODE DOFF ACCEPTED - UUID should now be in DCD"));
            // Другий вузол у тому ж прогоні НЕ вантажимо: якщо перший валить
            // апарат, до другого діло не дійде, а якщо не валить - краще мати
            // чистий однофакторний результат.
            }
        }

    // Згортання — у тому ж порядку, що CBal::Shutdown: спершу A, потім C.
    ((void (*)(TAny *))closeA)(objA);
    ((void (*)(TAny *))close)(obj);
    Log(_L8("    ord10/ord33 close done (CBal::Shutdown order)"));
    }

// Сканує типові місця, куди S60 3rd кладе дампи аварій (MobileCrash). Якщо
// апарат перезавантажився через паніку ядра, тут буде файл із назвою
// компонента-винуватця — це закриє розслідування §16.8 фактом, а не гіпотезою.
// Суто читання каталогів.
static void ScanCrashDumps()
    {
    Log(_L8("--- crash dump scan ---"));
    const TInt kMax = 8;
    _LIT(KD0, "C:\\logs\\");
    _LIT(KD1, "C:\\logs\\mobilecrash\\");
    _LIT(KD2, "C:\\data\\mobilecrash\\");
    _LIT(KD3, "E:\\mobilecrash\\");
    _LIT(KD4, "C:\\mobilecrash\\");
    _LIT(KD5, "E:\\logs\\");
    const TDesC *dirs[] = { &KD0, &KD1, &KD2, &KD3, &KD4, &KD5 };

    TInt total = 0;
    for (TInt i = 0; i < (TInt)(sizeof(dirs) / sizeof(dirs[0])); ++i)
        {
        CDir *dir = NULL;
        TInt r = gFs.GetDir(*dirs[i], KEntryAttMaskSupported, ESortByName, dir);
        TBuf8<80> p8; p8.Copy(*dirs[i]);
        if (r != KErrNone)
            {
            LogF(_L8("  %S -> %d"), &p8, r);
            continue;
            }
        LogF(_L8("  %S -> %d entries"), &p8, dir->Count());
        for (TInt j = 0; j < dir->Count() && j < kMax; ++j)
            {
            const TEntry &e = (*dir)[j];
            TBuf8<80> n8; n8.Copy(e.iName.Left(70));
            LogF(_L8("      %S  %d B%S"), &n8, e.iSize,
                 e.IsDir() ? &KDirTag() : &KNul());
            ++total;
            }
        if (dir->Count() > kMax)
            LogF(_L8("      ... %d more"), dir->Count() - kMax);
        delete dir;
        }
    LogF(_L8("  listed %d entries"), total);
    }

static void ProbeDspStack(TBool aLib, TBool aDev, TBool aChan, TBool aDeep,
                          TBool aLoadNode, TBool aUseRef, TInt aFlag,
                          TBool aLoadBase, TBool aBaseOnly, TBool aStub,
                          TBool aTask, TBool aReg, TBool aLock, TBool aDump,
                          TBool aDcdOp)
    {
    Log(_L8("--- DSP stack probe ---"));

    RLibrary bridge;
    TBool haveBridge = EFalse;
    if (aLib || aDeep)
        {
        // Тільки bridgeapi. bal.dll і dspmemmapper.dll більше не чіпаємо:
        // вони — головні підозрювані у відкладеному ребуті, і для нашої задачі
        // вони не потрібні (потрібні ординали є прямо в bridgeapi).
        ProbeLibrary(KBridgeApi, ETrue, &bridge);
        haveBridge = ETrue;
        }

    // Kernel-бік. НЕ кличемо User::LoadLogicalDevice: драйвер уже в системі
    // (див. список LDD вище), а самостійне завантаження другого екземпляра
    // поряд з активним аудіо-стеком — зайвий ризик. Перевіряємо пасивно.
    TInt r;
        {
        TFindLogicalDevice find(_L("Hwa"));
        TFullName fn;
        r = find.Next(fn);
        TBuf8<64> f8; f8.Copy(fn);
        LogF(_L8("  find LDD 'Hwa' -> %d (%S)"), r, &f8);
        }

    // Версія каналу — з GetCaps драйвера, а не з здогаду.
    // Спостережено: 1.0.1539 (0x06030001 як пакована TVersion).
    TVersion ver(1, 0, 1539);
    RDevice dev;
    r = aDev ? dev.Open(KHwaLdd) : KErrNotReady;
    LogF(_L8("  RDevice::Open('Hwa') -> %d%S"), r,
         aDev ? &KNul() : &KSkipped());
    if (aDev && r == KErrNone)
        {
        TBuf8<64> caps;
        caps.SetMax();
        caps.FillZ();
        dev.GetCaps(caps);
        // TVersion — ПАКОВАНА 4-байтова структура {TInt8 major, TInt8 minor,
        // TInt16 build}, а не три TInt. Перша спроба прочитала її як 3 слова
        // і дала безглузде "100925697.0.0" = 0x06030001, тобто насправді
        // 1.0.1539.
        const TUint8 *c = caps.Ptr();
        ver = TVersion(c[0], c[1], (TInt)(c[2] | (c[3] << 8)));
        LogF(_L8("    caps version: %d.%d.%d"),
             ver.iMajor, ver.iMinor, ver.iBuild);
        dev.Close();
        }

    // Кілька безпечних варіантів DoCreate: не знаємо напевно, чи LDD хоче
    // явний PDD і який номер юніта. Кожен варіант — лише спроба відкриття.
    struct TVariant { TBool iPdd; TInt iUnit; const char *iName; };
    const TVariant vars[] =
        {
            { ETrue,  -1, "pdd=Hwa.Omap unit=none" },
            { EFalse, -1, "pdd=NULL     unit=none" },
            { ETrue,   0, "pdd=Hwa.Omap unit=0"    },
            { EFalse,  0, "pdd=NULL     unit=0"    }
        };
    for (TInt i = 0; aChan && i < (TInt)(sizeof(vars) / sizeof(vars[0])); ++i)
        {
        RHwaChannel ch;
        r = ch.Open(ver, vars[i].iPdd, vars[i].iUnit);
        TPtrC8 vn((const TUint8 *)vars[i].iName);
        LogF(_L8("  Hwa channel v%d.%d.%d %S -> %d"),
             ver.iMajor, ver.iMinor, ver.iBuild, &vn, r);
        if (r == KErrPermissionDenied)
            Log(_L8("    -> capability gate: driver wants MultimediaDD"));
        if (r == KErrNone)
            {
            Log(_L8("    CHANNEL OPEN - kernel side of the bridge is reachable"));
            ch.Close();
            Log(_L8("    channel closed cleanly"));
            break;
            }
        }

    // Ризикова частина — тільки за явним аргументом (дисципліна сусіда).
    if (aDeep && haveBridge)
        ProbeBridgeOpen(bridge, aLoadNode, aUseRef, aFlag, aLoadBase, aBaseOnly,
                        aStub, aTask, aReg, aLock, aDump, aDcdOp);

    if (haveBridge)
        bridge.Close();
    }

static void RunL()
    {
    User::LeaveIfError(gFs.Connect());
    gFs.MkDirAll(KLogFile);
    User::LeaveIfError(gLog.Replace(gFs, KLogFile, EFileWrite | EFileShareAny));

    Log(_L8("== dsptest: C55x-vs-ARM benchmark =="));
    {
    TUint ntick = User::NTickCount();
    TInt np = 1000;
    HAL::Get(HALData::ENanoTickPeriod, np);
    TUint upSec = (TUint)(((TUint64)ntick * (TUint64)np) / 1000000u);
    LogF(_L8("UPTIME: %u s (%u min)"), upSec, upSec / 60u);
    }

    TInt fc = 0;
    if (HAL::Get(HALData::EFastCounterFrequency, fc) == KErrNone && fc > 0)
        gFcFreq = (TUint32)fc;
    if (gFcFreq)
        LogF(_L8("fast counter: %u Hz"), gFcFreq);
    else
        Log(_L8("fast counter: UNAVAILABLE - all timings will read zero"));

    SpinNop(200000);                 // розігрів
    gCpuMhz = MeasureMhz();
    LogF(_L8("ARM clock (NOP): %u MHz"), gCpuMhz);

    // --- рівні проби, вмикаються поіменно з командного рядка ---------------
    //
    // ДВА РЕБУТИ АПАРАТА (2026-08-10) сталися після прогонів, кожен з яких
    // вантажив і ВИВАНТАЖУВАВ bridgeapi/bal/dspmemmapper, а другий ще й
    // відкривав RDevice("Hwa"). Ребут був ВІДКЛАДЕНИЙ — сам процес завершився
    // штатно і лог забрався. Робоча гіпотеза: ці DLL розраховані на єдиного
    // власника (аудіо-сервер), і їхня глобальна де-ініціалізація при вивантаженні
    // чіпає спільний стан DSP, після чого аудіо-стек падає в ядрі.
    //
    // Тому за замовчуванням DSP-стек НЕ чіпаємо взагалі. Рівні вмикаються
    // окремо, щоб бісекцією знайти винуватця, а не гадати:
    //   lib   - лише RLibrary::Load(bridgeapi) + звірка ординалів
    //   dev   - + RDevice::Open("Hwa")/GetCaps
    //   chan  - + RBusLogicalChannel::DoCreate
    //   dsp   - + виклик ординалів bridgeapi (клас C Open/Close)
    TBuf<64> cmd;
    User::CommandLine(cmd);
    cmd.LowerCase();
    const TBool doLib  = (cmd.Find(_L("lib"))  != KErrNotFound);
    const TBool doDev  = (cmd.Find(_L("dev"))  != KErrNotFound);
    const TBool doChan = (cmd.Find(_L("chan")) != KErrNotFound);
    const TBool doRef  = (cmd.Find(_L("ref"))  != KErrNotFound);
    // 'f1' -> ord32 з aFlag=1: хай сам довантажить базовий образ DSP.
    const TInt  openFlag = (cmd.Find(_L("f1")) != KErrNotFound) ? 1 : 0;
    // 'base' -> перед вузлом явно завантажити базовий образ DSP/BIOS.
    const TBool doBase = (cmd.Find(_L("base")) != KErrNotFound);
    // 'baseonly' -> завантажити базу і чисто згорнутись, вузол не чіпати.
    const TBool doBaseOnly = (cmd.Find(_L("baseonly")) != KErrNotFound);
    // 'stub' -> зареєструвати наш UUID через DCD-стаб без коду.
    const TBool doStub = (cmd.Find(_L("stub")) != KErrNotFound);
    // 'task' -> спробувати створити задачу на вузлі, зареєстрованому базою.
    const TBool doTask = (cmd.Find(_L("task")) != KErrNotFound);
    // 'reg' -> пряма DCD-реєстрація нашого UUID через DoControl(0x0400000D).
    const TBool doReg = (cmd.Find(_L("reg")) != KErrNotFound);
    // 'lock' -> ord26 на власному файлі, відкритому нами ексклюзивно.
    const TBool doLock = (cmd.Find(_L("lock")) != KErrNotFound);
    // 'dump' -> зчитати описи вже зареєстрованих вузлів через ord1.
    const TBool doDump = (cmd.Find(_L("dump")) != KErrNotFound);
    // 'dcdop' -> проба DCD-родини ioctl, зокрема op5 (розбір файла).
    const TBool doDcdOp = (cmd.Find(_L("dcdop")) != KErrNotFound);
    const TBool doLoad = (cmd.Find(_L("load")) != KErrNotFound) || doRef
                         || (cmd.Find(_L("base")) != KErrNotFound);
    // 'heavy' повертає повні BENCH_*_REPS (~9 с суцільного ALU). За
    // замовчуванням - десята частина: точність та сама, навантаження на
    // порядок менше (findings §17.6).
    if (cmd.Find(_L("heavy")) != KErrNotFound)
        gRepDiv = 1;
    // Дослід про губернатор DVFS (див. ArmMonThread). Перевіряти 'armbusy'
    // ПЕРШИМ: 'armwatch' і 'armbusy' - різні рядки, але режим має бути один,
    // а busy сильніший за watch.
    if (cmd.Find(_L("armbusy")) != KErrNotFound)
        gArmMode = EArmBusy;
    else if (cmd.Find(_L("armwatch")) != KErrNotFound)
        gArmMode = EArmWatch;
    const TBool doDeep = (cmd.Find(_L("dsp"))  != KErrNotFound) || doLoad;
    TBuf8<64> c8; c8.Copy(cmd);
    LogF(_L8("cmdline: '%S'"), &c8);
    LogF(_L8("probe levels: lib=%S dev=%S chan=%S dsp=%S"),
         doLib ? &KOn() : &KOff(), doDev ? &KOn() : &KOff(),
         doChan ? &KOn() : &KOff(), doDeep ? &KOn() : &KOff());

    ProbeHal();
    ScanCrashDumps();
    ListDsp();
    if (doLib || doDev || doChan || doDeep)
        ProbeDspStack(doLib, doDev, doChan, doDeep, doLoad, doRef, openFlag,
                      doBase, doBaseOnly, doStub, doTask, doReg, doLock,
                      doDump, doDcdOp);
    else
        Log(_L8("--- DSP stack probe: SKIPPED (no level requested) ---"));

    // Бенчмарк — це ~8 с суцільного 100% ALU-навантаження. Для бісекції
    // причини ребутів це ОКРЕМА змінна (апарат був розігнаний до 423 МГц, у
    // системі є dvfs_interface і RomPatcherPlus.Driver), тож його теж треба
    // вміти вимикати: 'nobench'.
    if (cmd.Find(_L("nobench")) != KErrNotFound)
        Log(_L8("--- ARM benchmark: SKIPPED ('nobench') ---"));
    else
        BenchmarkArm();

    Log(_L8("== end =="));
    gLog.Close();
    gFs.Close();
    }

TInt E32Main()
    {
    CTrapCleanup *tc = CTrapCleanup::New();
    if (!tc)
        return KErrNoMemory;
    TRAPD(err, RunL());
    delete tc;
    return err;
    }
