# WSOLA на постійному C55x worker: N95/E90

Дата2026-10-01. Поточна порівняльна серія — **host/protocol20**.
Плани записано до правок: `work/PLAN_V19.md`, `work/PLAN_V20.md`.

## Алгоритм і wire contract

Перенесено `PS1Emulator/src/symbian/snd_symbian.cpp:WsolaBestOffset`, який
викликає `CSymSnd::WsolaFeed`. ARM зберігає вибір вікна, stereo overlap-add
і audio queue. Пошук бере лівий канал після arithmetic `>>6`: template220,
search660, offsets0..440. Coarse оцінює111 offsets з кроком4; refinement
додає3 або6 поблизу грубого максимуму. При ties зберігається вже вибраний
кандидат. Signed32 sum обмежена220×512×512, переповнення немає.

ARM reference має original stereo stride2/shift inner loops. DSP отримує
packed scaled signed16, використовує contiguous dot з CGT4.4.1 `RPT/MACM`.
Усі22 native imports існують в обох base images. Окремий Python reference
обчислює таблицю всіх441 scores, потім відтворює ordered coarse/refine.
Fixtures: PS1 benchmark LCG/layout, silence, positive maximum, negative
scores, left/right refinement, last coarse offset та tie з offset4.
Перший vector: offset172/score4364902. Кожен32-packet run має4 цикли;
LCG seed змінюється між циклами. [Vectors](evidence/2026-10-01/wsola-v19-vectors.json).

Input1792 Б = header32 +880 signed16. Output48 Б = header32 + offset/count,
дві довжини, operation/case і32-bit weighted checksum усього входу.
Native properties незалежно задають896 input/24 output C55 words; обидва
ARM allocations лишаються4096 Б. DCD незмінний; ARM pointers/structs не
передаються на DSP. Перевіряються magic/sequence/length/repetitions/protocol,
score/frame/stop/priority15, offset/count/case/checksum. DSP перевіряє
діапазон−512..511. Control reps0 має той самий wire/checksum шлях без search.

Один create запускає власну TSK у generic library2, node лишається CREATED1,
official RUN відсутній. Last packet stop → output reclaim → idle/reclaim →
SEM post/native TSK exit → join TERMINATED3/cookie/status/pending gate →
task/SEM/streams/context delete → DELETED5/free native/close/FINAL/EXIT0.
Це перевірене завершення коректних packets.

## ARM компіляція і методика

V19 перевірив arithmetic/wire/cleanup, але мав SDK ARMv5 baseline.
ARMv6 pure-function build відрізнявся:260→244 Б. V19 збережено як historical
harness comparison; його ARM час не використано для current PS1 висновку.
V20: CSL GCCE3.4.3, SDK UREL `-O2 -fno-unit-at-a-time`,
`-march=armv6 -mtune=arm1136j-s -fomit-frame-pointer`, як current stage1.
Body пошуку побайтово збігається з ARMv6 pure-function build.
[Codegen](evidence/2026-10-01/wsola-v20-arm-codegen.json).
SDK повторно використав cached object після MMP option edit; до доставки
його перестворено. `build.cmd` тепер очищає обидва research objects.

На кожному v20:9 runs/195 correct packets — one echo512, one short control,
one search і3 paired runs control/search по32 packets. Search97/control97/
echo1; статистики нижче мають96 samples на режим. Run order `[0,1]`,
`[1,0]`, `[0,1]`; ARM/DSP baseline order чергується між packets.
ARM baseline — mean batch16 на тих самих stereo даних, кожен return має
volatile sink. Це warm-cache scalar baseline, без application overhead.

ARM FastCounter32768Hz міряє packing і end-to-end: від deinterleave/shift
до обох transfer completions. Входять DSP input range/checksum, driver,
scheduling і search. Generation/reference/validation/logging лежать поза
interval. Raw DSP ticks/configured164 лишаються diagnostic, не wall time.

| Мікросекунди, pooled96 | N95 | E90 |
|---|---:|---:|
| ARMv6 search, median batch16 mean |999.45|999.45|
| Packing+control round trip, median |518.80|610.35|
| Packing+DSP search+round trip, median |640.87|732.42|
| DSP path p95 / maximum |640.87 /671.39|762.94 /762.94|
| Median same-packet `ARM − DSP path` |385.28|265.12|

DSP path medians по трьох runs: N95640.87/610.35/640.87, E90732.42 на всіх.
Кожен search packet був коротшим за його measured ARM batch mean.
LCG case0 окремо12 samples: ARM median1024.25 на обох, DSP640.87/732.42.
Усі outliers збережено; control maxima885.01/1190.19. V18 E90 equal-size
outlier7.812 мс лишається окремим результатом.

N95 MPU reservation100%, кожен packet before/after100, release0. Fresh
stock guard m86/div3/firmware profile на обох. У v19/v20 correct results,
one create/no RUN/no KILL, FINAL/EXIT0; daemon startTick незмінний у серіях.
Original DSP/clock logs і host20 GET-equal, PS0:
[final state](evidence/2026-10-01/worker-stream-v20-checkpoint-device-status.json).
Пізній reboot N95 після v18 з невідомою причиною залишається окремим фактом.

## Окупність і межі

Create median8.102 мс N95/8.5595 мс E90. За median paired saving **лише
create** окупається після22/33 hops (~110/165 мс звуку). Модель не включає
base/processor load, native allocation або іншу session підготовку.
Потрібна одна TSK на всю сесію. Hop220/44100≈4.989 мс; median DSP path
займає≈13%/15% interval. Середній час і максимум вибірки не гарантують deadline.

Invalid-input/timeout teardown потребує native loader audit: failed join
може лишити live task, unload після callback error не вважається безпечним.
KILL не є перевіреною recovery. Shared ring/DMM ownership, довга робота,
audio coexistence, underrun і application FPS/PCM gain не встановлені.

Integration plan: resident service/active-object completion, queued search
job біля `WsolaFeed`, ownership buffers до completion, ARM overlap-add/ring.
Після safe cancellation/error audit — той самий PCM, кінцевий output,
underrun/tail latency і довга робота з real audio; fallback після завершеного
DSP ownership. Поточний результат дає kernel/канал і обґрунтований цей план.

## Відтворення і докази

Після verified builds/archive, SIS20 на E90 і fresh `prepare_stream.py`:

```powershell
python tools/run_stream.py --device n95 --ip 192.168.3.22 --host-version 20 --mode worker-wsola --reps 1 --frames 1 --preparation work/evidence/n95/NEW-preparation.json --tag NEW-one
python tools/run_wsola_series.py --device n95 --ip 192.168.3.22 --host-version 20 --preparation work/evidence/n95/NEW-preparation.json --tag-prefix NEW-pairs
python tools/recover_stream.py --device n95 --ip 192.168.3.22 --preparation work/evidence/n95/NEW-preparation.json --restore-dsp --tag NEW-recovery
```

Завжди нові імена; після відмови зупинити серію. `summarize_wsola.py` offline
перевіряє historical tags і не перезаписує reports.
[N95](evidence/2026-10-01/n95-wsola-v20-results.json),
[E90](evidence/2026-10-01/e90-wsola-v20-results.json),
[artifact6](evidence/2026-10-01/worker-stream-v6-artifacts.json).
Firmware/EXE/DLL/ASM/SIS/keys/screenshots лишаються локальними.
