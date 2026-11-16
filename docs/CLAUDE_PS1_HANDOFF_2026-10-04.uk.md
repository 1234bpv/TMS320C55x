# Передача Claude: результати C55x для PS1Emulator

Дата: 2026-10-04. Поточні роботи завершено дослідницьким checkpoint за
запитом користувача. Нових апаратних експериментів не планувати автоматично.
Зміни виконані в `TMS320C55x test`; код PS1Emulator не змінювався.

**Рішення для поточного PS1: залишити WSOLA, MDEC і plain SPU mix на ARM.**
На N95 жоден із виміряних DSP jobs проти відповідного поточного ARM kernel
не виграв у блокувальному режимі навіть до setup. Це достатній результат
для вибору поточної реалізації; загальну неможливість async/resident DSP
не встановлено. Повний production-контракт shared memory також не прийнятий.

## Що передати в PS1 зараз

1. Оновити `PS1Emulator/docs/dsp-integration-guide.md` і план DSP за цим
   звітом. Його початкові v20/scalar числа є історичними; вони не доводять
   виграш проти поточного WSOLA SMLAD. Еталон актуального рішення —
   [PS1_CANDIDATES](PS1_CANDIDATES_2026-10-01.md), верхнє доповнення04.10.
2. Зберегти поточний `WsolaBestOffset` у `src/symbian/snd_symbian.cpp`,
   ARM MDEC та assembler `mix_chan` як робочі шляхи. Не додавати blocking
   DSP offload для виміряних jobs. Інтеграція цих результатів сама по собі
   не потребує установки research EXE/DLL на телефон.
3. Якщо створюється окрема експериментальна DSP-гілка, позначити її
   неприйнятою, з явним увімкненням і перевіркою профілю. Спочатку закрити
   publication/ownership/lifecycle gates та визначити незалежну W;
   лише потім реалізовувати новий async/resident job і порівнювати з ARM.
   Це наступне доручення, а не незавершена реалізація в цьому репозиторії.

## Докази D0–D2

| Етап | Досягнуто | Що не заявляється |
|---|---|---|
| D0 | На N95 і E90 по3 послідовні clean create→RUN→packets→delete, FINAL/EXIT0. Повні N95 inspect/create/3RUN journals опубліковані:24 packets загалом. | Універсальний safe cancel/fault recovery. Непідтверджене pending/delete ownership веде в QUARANTINE без automatic KILL. |
| D1 | Native shared payload ring16KiB TOTAL; повтори, page identity, wrap/index carry, whole-region ownership і clean teardown. N95 native61:3series/12runs/9360 packets із6 stock brackets. | Увесь канал без копіювання: notifications досі використовують native transport. Універсальний DSP→SDRAM→mailbox completion contract не встановлено. |
| D2 | Реальні paired A/H+D/S, точні outputs та strict scenarios для MDEC66, SPU67, current-WSOLA68; рішення за розмірами jobs записано. | Виграш усієї гри, full SPU/PCM, captured gameplay або useful async W. |

[Acceptance matrix](N95_ACCEPTANCE_2026-10-04.md) містить hashes, повні
журнали, межі й фінальну перевірку телефона. D0 прийнятий; D1 memory gate
відкритий; D2 вердикт для виміряних jobs доставлений. Увесь початковий
план з відкладеним E90 не оголошується виконаним.

## Числа, на яких базується рішення

N95 8GB RM-320, firmware35.0.001; stock clock brackets:
ARM330.24MHz, bus110.08MHz, DSP220.16MHz. Це snapshots до/після серій,
не continuous DVFS trace. Частоти в дослідах не змінювалися.
Нижче p50 часу **цілого job**, мікросекунди. Tail samples не вилучались.

| Job | ARM A p50 | DSP path H+D ready p50 | Paired blocking wins до setup |
|---|---:|---:|---:|
| WSOLA current SMLAD, один search | 337.601 | 1098.633 | 0/360 |
| MDEC6IDCT+RGB24,1 macroblock | 78.201 | 2655.029 | 0/360 |
| MDEC,2 macroblocks | 110.626 | 4272.461 | 0/360 |
| MDEC,4 macroblocks | 295.639 | 7690.430 | 0/360 |
| Plain SPU,1voice×64samples | 3.576 | 1617.432 | 0/360 |
| Plain SPU,8voices×64samples | 27.180 | 3295.898 | 0/360 |
| Plain SPU,24voices×64samples | 40.531 | 3540.039 | 0/360 |

H+D від packing до готового reconstructed result в ARM memory, включно
з cache/transport/DSP. Oracle/header/input-unchanged checks і запис
журналу поза timed job. A — isolated warm kernel, averaging повторів;
це не live gameplay. Чистий D не виводити відніманням загальних медіан.
CPU для цих прикладних kernels не виміряний (`-1` = unmeasured).

Instrumented S=setup+teardown, p50: WSOLA865080us, MDEC840178us,
SPU863494us. S включає lifecycle journaling; це не minimum production
startup. Додавання S/N лише погіршує наведене blocking порівняння.
WSOLA H+D p95/p99/max=2075.195/8514.404/9155.273us;
MDEC batch4 max105682us; SPU24voice max14312.744us.
Детальні distributions/per-case/strict scenarios:
[WSOLA68](N95_WSOLA_CURRENT_2026-10-04.md),
[MDEC66](N95_MDEC_RING_2026-10-04.md), [SPU67](N95_SPU_RING_2026-10-04.md).

Окремий synthetic CPU64,3series/9360 packets: batch1/2/8/15 exchange
p50=915/1190/3021/5126us, weighted threadCPU45.37/45.87/48.09/45.68%.
Full-window useful bidirectional bandwidth0.712/0.960/1.357/1.500MB/s.
Це pack/cache/full correctness checks/final yield, не pure wait CPU,
і не application-kernel cohort. [CPU64](N95_RING_CPU_2026-10-04.md).
Не об'єднувати ці числа зі швидшими історичними candidate54/v20.

## Межі jobs і матеріали для можливої подальшої інтеграції

Кільце:16KiB **загалом**,1024B control +15input+15output slots по512B;
по480B payload/slot,7200B payload у кожному напрямку. Це не16KiB на
напрямок. C55x `int/char`16bit, `long`32bit; серіалізація32-bit values
явними low/high16 words. ARM pointer не є DSP pointer; структура з
нативними pointers не є wire format. Ownership охоплює все кільце.

- **WSOLA:**4input slots,1output;880 signed16 samples:220 template +660
  search, coarse step4/refine±4, strict `>` ties і той самий порядок.
  Return offset/score/scored. Snapshot current ARM:
  `src/wsola_current/kernel.inc`, `snapshot.json`; CSL3.4.3/O2/ARMv6,
 5SMLAD sites. DSP: `src/dsp/wsola_dsp.c`, `ring_wsola_exchange` у
  `src/dsp/stream_node.c`. Наступний hop залежить від попереднього offset;
  не заповнювати кільце незалежними майбутніми searches одного потоку.
- **MDEC:**job після RLE/dequantization, перед6IDCT+RGB24. На macroblock
  384signed32 coefficients +6 masks +BW flag =1550B input,768B output
  (192uint32 RGB24). Batches1/2/4: input4/7/13,output2/4/7 slots.
  `src/mdec/kernel_arm.inc`, `kernel_c55.inc`, `kernel_c55.c`, fixtures/snapshot;
  `ring_mdec_exchange` у `stream_node.c`. ARM GCCE4.6.3/O2/ARMv6.
  Поточний `rl2blk` уже викликає IDCT: перенесення вимагало б змінити
  межу job, зберігши RAM visibility, DMA/IRQ/status і dynarec invalidation.
- **SPU:**plain post-ADSR mixer, samples32/volumes32/initial sums32;
  output128stereo sums32.1/8/24voice jobs: input2/6/15slots,output2.
  Для24voices input6848B; максимум66 парних samples у7200B, тоді як
  виміряно64. `src/spu/mix_arm.s`, fixtures/snapshot;
  `src/dsp/spu_mix_ring.inc`. Packed gain/sign spill і modulo32 sums
  збережені точно. Це не ADPCM/ADSR/noise/reverb/capture/IRQ/fullSPU.
  Full-state варіант потребує coherency512KiB SPU RAM і histories;
  optional worker item8396B у поточний payload не вміщується.

Fixtures підтверджують exact outputs у випробуваному діапазоні, не
exhaustive legal game inputs. Не міняти signed32 coefficients на16bit
заради пакета. Зберігати GPL notices/COPYING при перенесенні MDEC/SPU.

## Async: що має бути доведено до нової реалізації

За посібником `T=H+D`, `q=S/N`: `max(T,W)+q<A+W` рівносильно
**`q<A` та `W>T+q−A`**. Для blocking W0 потрібне `T+q<A`; воно тут
не проходить. Для одного ARM thread H теж займає цей процесор:
`H+max(D,W)+q<A+W` додатково вимагає **`H+q<A`**.
Elapsed intervals outside notification дають лише умовні bounds для
тієї самої stage envelope, не production CPU minimum.

W — реально незалежна робота до точки споживання result, а не середній
час кадру/guest cycle delay. У незмінених blocking calls W0; доступна
W після зміни schedule невідома. WSOLA може бути наступною гіпотезою,
але measured H/D/S або теоретичний threshold не є async gain.
[Source dependencies і paired bounds](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md).

Для production shared memory відкрито два contracts:
DSP external writes завершені до visible notification; ARM completion
після invalidation перед читанням. Saved N95 ARM audit довів clean DSB
і обидві cache branches; short invalidate MVA routine не має explicit
DSB, caller/context потребує окремої кваліфікації.
У measured DSP63/65/67 control stores перед RET/STRM_issue підтверджено
повними compiler listings; DCR read-only WPE0 не встановлює OMAP fence.
Successful packets не замінюють цього контракту.
[ARM cache audit](N95_ARM_CACHE_2026-10-04.md),
[DSP compiler listings/audit](evidence/2026-10-04/n95-kernel-publish-audit.json).

Timeout із непідтвердженим DSP ownership не означає дозволений ARM
fallback до тих самих буферів або free/unmap/unload. Потрібен accepted
stop/join/ownership return; інакше QUARANTINE та контрольоване відновлення.
Поточний OS per-device lock захищає від конкуруючих research sessions,
але не є production DSP resource arbitration.

## Версії, артефакти й перевірка без телефона

| Cohort | ARM host | DSP / protocol | DSP SHA256 |
|---|---:|---|---|
| Current WSOLA68 | 53 | exact retained63 /40 | `646231C29251F94B688FD89E2F729553CBF5083D1C734FFC6775FEE7E9470BFF` |
| MDEC66 | 51 | exact65 /41 | `EA70403E72E513E868D6BCD4D35ABD3D4552A38AFCC258250B00CD3A5845B534` |
| SPU67 | 52 |67 /42 | `181D2851F53F3DD155AC0F37DA9288A26CB364865A3336113F0254A76B3B4AE4` |

Host/DSP/source/build hashes є у respective `*-artifacts.json`, фактичні
runs — у `*-results.json`. `out/arm/c55stream.exe` зараз host53;
generic `out/dsp/c55stream.dll55l` досі SPU67. Для WSOLA потрібен typed
`c55stream-dmm-ring-wsola.dll55l`, а не generic файл. На N95 відновлено
оригінали, а не залишено research53 встановленим.

У корені дослідницького repo, з Python3:

```powershell
python tools/verify_n95_acceptance.py
python tools/verify_kernel_publish.py
.\tools\check_state.ps1 -RequireArtifacts -RequireStreamArtifacts
```

Master verifier перевіряє hashes/повні N95 D0 journals/native61/CPU64/
MDEC65–66/SPU67/currentWSOLA68/dependencies/ARM-cache/compiler order.
Він не підключається до телефонів. Full D0 і kernel listings опубліковані;
ROM/source checks додаткові, коли відповідні локальні файли доступні.
Artifact/environment check потребує SDK і локальних build outputs.

## Стан телефонів і межа передачі

**N95:**04.10 о09:32:35UTC останній read-only INFO/PS/GET checkpoint:
усі5оригіналів GET/SHA-equal (DSP, stream log, clock log, EXE, hash),
`c55stream`/`ocprobe` PS0. Це snapshot у зазначений час; нових phone
commands під час завершення звіту не було. Saved originals/manifest:
`work/evidence/n95/d0-20261003-clean34/` (локальний ignored archive).
Опублікована [final verification](evidence/2026-10-04/n95-acceptance-final-verify.json).

**E90:**відкладений користувачем; **відновлення EXE/hash/journals ще
не завершене**. Останній known host46, DSP original; compatible RDomain
clock probe зібрана, не встановлена/не запущена. Немає нового прийнятого
frequency qualification. Saved originals:
`work/evidence/e90/d0-20261003-clean34/`. Повернувшись до E90, спершу
отримати поточні журнали/PS/identity, тоді повернути own originals із
GET/SHA verification, після цього вирішувати потребу нових probes.
Не повторювати failed RUN без нової гіпотези. Причина auto-reboots не
встановлена; звинувачення демона не підтверджене.
[Recovery checkpoint](evidence/2026-10-04/e90-native61-oct04-recovery-checkpoint.json),
[reboot analysis](E90_DAEMON_REBOOT_2026-10-04.md).

Локальні saved originals/ROM не входять у Git; перед hardware recovery
перевірити їх наявність. `daemon startTick/boot/by` є launch tuple,
не унікальним ID перезавантаження телефона. Наразі від користувача
фізичних дій не потрібно: передається перевірений дослідницький результат.
