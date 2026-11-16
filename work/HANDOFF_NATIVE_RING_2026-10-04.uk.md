# Продовження для agy: native ring, 2026-10-04

## Актуальне steering: N95 зараз, E90 завтра

Користувач відновив ціль і доручив доробляти на N95; E90 відкладено до
завтра. **Не виконувати нових E90 phone commands**, включно з restore,
поки це відкладення чинне. Старі запити Open4All нижче вже не актуальні.

N95 host46/candidate61: нові3 повні серії,12 runs/9360 packets,
усі6 stock clock brackets PASS, startup tuple62209 незмінний. Originals5
повернуті й GET/SHA-equal. Новий batch15 p50=5249us/2.713MB/s,
повільніший за окремий old54 cohort; причина ще не доведена.
Evidence — docs/evidence/2026-10-04/d1-n95-native-ring-results.json.
Distinct N95 host47/candidate62/protocol39 DCR pilot уже PASS:8 exchanges,
120 packets,16 reads port0x200 all0000/WPE0, два stock clock brackets.
Originals5 після pilot restored+verified, PS0. Helper bytesA45102004804
не мають writes/relocations. Published n95-dcr62-results.json і
docs/N95_DCR_2026-10-04.md. Runtime62 не кваліфікує минулі54/61.
Source/out тепер host47/DCR62; старий ring61 DSP і archive61 unchanged.
Далі OMAP2420 endpoint publication contract та distinct WSOLA ring/A
measurement; не запускати default46 runner проти newly built47.

E90: stock clock02 пройшов після user toggle, але до нового DSP deployment
стався user-confirmed automatic reboot. Наступна UI-сесія KEY down/SHOT/GET
повністю завершилась; наступний connect не вдався до будь-якої команди.
Користувач підтвердив фізичний reboot; daemon log потім показав reset tick.
Причина не встановлена; нових DSP RUN немає. Докази та source audit —
docs/E90_DAEMON_REBOOT_2026-10-04.md і e90-daemon-reboot-audit.json.
`startTick` — daemon launch tick, не unique phone boot ID. Останній
INFO/GET-only recovery мав startTick93682; автоматичний reboot не можна
виводити лише зі зміни startup tuple. Команд REBOOT/RESTART/KILL не слали.

E90 standard patcher copy105/free100/getter103 проти RDomain copy102/
free104/getter105 під тим самим RomPatcherPlus.Driver: offline5-variant
контракт доведено, actual loaded module identity не прочитано.
Окрему ringclock.exe зібрано (SHA95CEE1F7…4560), **ніколи не встановлено
й не запускали**:4 deploy attempts зупинилися до PUT, остання LS−46.
E90 known host46/original DSP; EXE/hash/journals restore pending.
Збережені originals — work/evidence/e90/d0-20261003-clean34/original-*.bin.
Згодом прибрати тільки власні E:\\codex-oct04-patches03/04/05.bmp.
N95 та E90 restoration не плутати: E90 final-verify01 був до redeploy46.

22 tests PASS; publication verifier45 runs/32040 packets across separate
cohorts. D0 complete, D1/D2 in_progress. Попередній текст нижче — історія.

Робоча папка `D:\VsCodeProjects\SymbianProjects\TMS320C55x test`.
Доручення D0–D2 лишається активним; не позначати весь план завершеним.
Поточний код host46, DSP candidate52/protocol38; на телефонах **original20**.

## Завершені результати

- D0: по3 ordinary RUN/8 correct packets на N95/E90, clean teardown.
- N95 candidate54/host41:3 повні D1 серії,12 runs/9360 packets, stock clocks.
- E90 native candidate61/host46:3 повні D1 серії,12 runs/9360 packets,
  boot60136 незмінний. Native ioctl2 own-channel cached state1, retained
  own-node state1/nonzero RMS MEM_valloc env,4 pages GET via BridgeUtil1
  до/після exchanges, exact identities. Жодного RomPatcher snapshot у
  native ring mode; окремі clock probes робили patcher own-buffer self-test.
- Повна перевірка256 input і256 output words/packet, sequence wrap,
  32-bit carry, delete/free task/unmap/unreserve/free ring/notifications/close.
- Native CMM backing:38 instructions та3 kernel imports/phone простежують
  ASIC selector2 → retained bridgecfg DPlatChunkHw(attrs1044) → reader
  → context → CMM register. Cleanup factory передає обидва chunks.
  Public attributes: user RW, buffered uncached L1, uncached L2.
  ASIC reservation/PTE dump не зроблено; explicit pin/unpin не заявляти.
- Обом повернені5 initial originals GET/SHA256-equal, c55stream/ocprobe PS0.
  E90 final boot60136; N95 залишався original20, свіжий GET-only verify.
- 19 tests проходять. Source-independent publication check:33 long runs,
  22680 packets у separate cohorts. Поточні повні cohorts — по9360.

## Важлива виправлена помилка обліку

`run_ring_series.py` раніше перевіряв лише complete=true clock action.
Усі6 native61 brackets на E90 мають **ocprobe self-test−20**, HAL CPU330MHz,
без PRCM DSP/bus read. Stock для цих brackets **не підтверджений**.
Summary і independent verifier зберігають явний failed clock status.
Runner тепер перевіряє stock_clock_matches й зупиняється до наступного RUN;
negative regression test доводить, що completed action не означає clock pass.

Async запит користувачу: увімкнути Open4All на E90, без reboot, і повідомити.
Останнє «Продовжуй роботу» не підтверджує виконання цього фізичного кроку.
Після відповіді спершу лише clocks action/new tag, GET logs і parse.
Якщо self-test знову відмовить, аналізувати own-buffer driver contract;
не подавати відмову як доказ stock і не починати новий DSP RUN.
Успішний новий clock bracket не підтверджує частоти минулої native61 серії.
Якщо потрібні3 stock-qualified серії, створити новий evidence cohort із
тим самим immutable host46/candidate61/DSP після clock validation:
`run_ring_series.py --device e90 --host-version 46 --revision 61
--tag-prefix native61-stock02 --keep-awake`. Не overwrite старі61 tags.

## Інша відкрита частина D1

`dsp-ring-publish-audit.json`: archived deployed compiler assembly доводить
volatile output/control stores → return → timer → notification fields
→ STRM_issue. Generic C55x manuals описують W/W+, write-pending і bypass;
це не самостійний OMAP2420 interconnect visibility/fence contract.
Потрібен незалежний firmware/hardware аудит зовнішніх записів перед
native notification visibility. Не називати volatile readback full barrier.

Offline продовження04.10: `dsp-native-notification-audit.json` і
`tools/rev/audit_dsp_notification.py` перевіряють29 instruction sites/phone,
DSM cinit table, BIOS5.10/user-init та mailbox paths. TI BIOS5.41
`gbl.h55` із primary installer підтвердив DCR I/O port200, WPE mask80.
Installer лише прочитано/розпаковано selected records, не виконано.
Downloaded immutable package лишився `out/bios_setuplinux_5_41_13_42.bin`;
audit відтворюється з ним і saved baseimages. SHA містяться в JSON.
Фактичний WPE невідомий; відсутність symbol у5.10 не означає non-posted.
Читання mailbox7F1041 перед message7F1022 не доведене як SDRAM drain.
Окремий майбутній read-only DSP diagnostic port200 допустимо підготувати
після fresh clock validation; не write DCR/не зараховувати його за61.
Dynamic channel/copy function pointer історичних runs не прочитані цим audit.

D2 оновлено для окремих N95/E90 synthetic T/S scenarios. MDEC/SPU/WSOLA
через саме це кільце не виміряні; application gain не доведений.
135–200us SMLAD — попередня оцінка, не новий hardware measurement.
Емулятор не редагували. D1/D2 залишаються in_progress.

## Докази та команди

`docs/evidence/2026-10-03/d1-native-ring-results.json` і12 published journals;
`native-ring-backing-audit.json`, `native-processor-state-audit.json`,
`native-ring-owner-audit.json`, `dsp-ring-publish-audit.json`;
`d1-native-ring-v61-artifacts.json`, published final verify обох.
Generator `tools/summarize_native_ring.py`, verifier `tools/verify_ring_publication.py`.
E90 p50 batch1/2/8/15=640/793/1831/3021us, useful bidirectional
MB/s=1.449/2.316/4.100/4.598; DSP clock unknown.

Python: `C:\Program Files\LibreOffice\program\python.exe -X utf8`;
запуск через `tools/run_bounded.ps1`. LO Python не викликає себе через
subprocess; orchestration імпортує main() з окремим sys.argv.
Device runner: `tools/e90_task_session.py --device e90 --session
work/evidence/e90/d0-20261003-clean34 --action clocks --host-version46
--tag <new-unused-tag> --keep-awake` (у реальному CLI `--host-version 46`).
Saved originals: `work/evidence/{device}/d0-20261003-clean34/original-{0..4}.bin`.
IPs: E90 .21:2323; N95 .22:2323; strict device identity guards, без scans.

Не торкатися сторонніх змін `docs/APPLICATION_CANDIDATES.md`,
`work/CODEX_TASK_2026-10-01.md` та Gemini scratch tools/files.
Commit/push private main дозволено користувачем; stage лише власні зміни.
Код/докази: commit `233740c31dbf218d0ea7201f60ddd60fa9fa181f`, pushed
private main, independent ls-remote підтвердив SHA. STATE містить запис.
Після наступних змін оновити checkpoint і перевірити push.
Якщо Open4All крок не відповіли, не повторювати запит без нової причини.
