# SPU: межа завдання та ціна передачі стану

Це offline audit поточних джерел PS1Emulator, **не hardware SPU замір**.
N95 після MDEC має всі оригінали, PS0; телефон для цього аудиту не опитувався.
Емулятор не змінювався. E90 залишається відкладеним.

## Що саме є кандидатом

do_samples/do_channels включає ADPCM/history, ADSR, noise, pitch/FMOD,
decode-buffer writes голосів1/3, reverb, RAM/DMA coherency та guest IRQ.
mix_chan — лише накопичення post-ADSR ChanBuf у signed32 stereo SSumLR.
На ARM1136 поточний HAVE_ARMV5 assembler використовує smlawb/smlawt;
scalar C не можна видавати за поточну ARM baseline. Перенесення only mix
не забирає основний ADPCM компонент і потребує збереження/передачі
декодованих голосів, які нині обробляються послідовно через один ChanBuf.

У prior GT profile2026-09-28: doSamples A1/A2=968/965ms за600 frames,
середня частка pass3.714%. Sampling1:16 дав dec_adpcm644.4ms,
mix_plain227.9ms, ADSR18.8ms. Mix_plain — приблизно379.833µs/frame
або31.600µs/voice call при7212 calls,5292000 voice samples.
**3.7% — весь doSamples, не бюджет чистого мікшера.** Профіль має стару
збірку й ARM330.24/bus165.12MHz; це не current paired A цього стенду.
Не віднімати від нього current ring latency як від спільного cohort.

## Розміри перевірено ARM-компілятором

GCCE4.6.3 зібрав sizeof/offsetof поточних externals.h і struct spu_worker
без виконання коду. int/pointer4B, NSSIZE914, ADSR16B, SPUCHAN56B,
sample_buf64B. SPUInfo3840B без thread code та5440B із WANT_THREAD_CODE.
Optional work_item8396B:28B header +24×44B channels +7312B sums;
worker33840B. Raw pointers/bitfields/ARM layouts не є C55 wire format.
SPU RAM524288B, history24×64=1536B, і пов'язані heap buffers окремі;
sizeof SPUInfo не означає розмір повного стану SPU.

Для окремого **plain mix24 voices**, зберігаючи samples32, volumes32,
initial stereo accumulator32 та output accumulator32:

| Семплів/job | Input bytes | Output bytes | Input/output slots480B | Вміщується |
|---:|---:|---:|---:|:---|
|32|3520|256|8/1|так|
|64|6848|512|15/2|так|
|66|7056|528|15/2|так|
|68|7264|544|16/2|ні|
|128|13504|1024|29/3|ні|
|914|95248|7312|199/16|ні|

Input=24×samples×4 +24×2×4 +samples×2×4; output=samples×2×4.
Ring16KiB TOTAL має7200 payload bytes кожного напрямку, не16384
payload bytes. Metadata може лежати у control area; pointers не передаються.
Досягти більших batches можна через resident DSP state або іншу межу job,
але це інший контракт, який треба виміряти й перевірити окремо.

Повна stateless копія SPU RAM потребує щонайменше73 input handoffs лише
за capacity, без metadata/state/output. Це кількість передач, **не**
вимір її часу. Resident mirror/delta protocol має забезпечити ordering
DMA/register writes/readbacks, decode history, envelope/noise/reverb,
voice1/3 capture й guest IRQ; PCM-only equality недостатня.

Після цього аудиту probe64 samples для1/8/24 voices виконано:
[SPU67 hardware results](N95_SPU_RING_2026-10-04.md). Exact32-bit sums,
1080 full jobs, blocking winners0/1080 до setup; plain mix залишити ARM.
Stage state залишається на ARM. Це визначає only mix_plain verdict. Повний SPU переносити
зараз не рекомендовано: actual A/H/D, useful independent W і тотожність
PCM/мутабельного стану для такого контракту ще не перевірені.

Докази й hashes джерел: [boundary audit](evidence/2026-10-04/n95-spu-boundary-audit.json).
Відтворення: `python tools/audit_spu_boundary.py` з local emulator і GCCE.
Для D2 лишаються строгі S/N<A та W>H+D+S/N−A; цей аудит не підміняє
hardware timing і не закриває SPU чи independent endpoint publication.
