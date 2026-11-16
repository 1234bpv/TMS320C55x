# N95: приймання доказів D0–D2

Поточний етап передано Claude за запитом користувача:
[звіт для PS1](CLAUDE_PS1_HANDOFF_2026-10-04.md). Подальші research runs
не починати автоматично; відкриті нижче gates лишаються непідтвердженими.

Для N95 завершено повторні channel/kernel виміри й доставлено рішення
для виміряних blocking jobs: current WSOLA, MDEC та plain SPU залишити
на ARM. Загальну ціль ще не виконано: контракт DSP publication не
встановлено, E90 відкладено користувачем. Емулятор не реалізували.

Цей checkpoint зіставляє докази з `work/CODEX_TASK_2026-10-01.md`,
зберігає hash доручення та перевіряє фінальний стан телефона.
[Машинний audit](evidence/2026-10-04/n95-acceptance-audit.json)
посилається на повні опубліковані D0 журнали, D1/D2 cohorts та hashes.

| Пункт | Що доведено для N95 | Межа |
|---|---|---|
| D0 normal cycles | Host35/candidate47:3 послідовні RUN,24 packets загалом, кожен8×512B,240 payload words/packet; delete/free/close/FINAL/EXIT0. Опубліковано inspect/create/3RUN journals і2 stock probes. | Positive-cycle acceptance; універсальний safe cancel не заявлено. Uncertain pending/delete ownership веде у QUARANTINE без automatic KILL. |
| D1 shared mapping і повтори | Native61:16KiB TOTAL,3series/12runs/9360 exact packets, pages before/after,6 stock brackets, clean teardown. | Payload shared; notifications використовують native transport. Це не повністю безкопійний канал. |
| D1 CPU | Окремий CPU64:3series/9360 packets, weighted threadCPU45–48% у settled full correctness windows. | Включає packing/cache/checks/yield; це не pure wait CPU і не gameplay. Cohorts не об'єднувати. |
| D1 publication | ARM machine audit:109 words,13 CP15 operations,3 DSB tails. Read-only DSP DCR cohorts мають WPE0. | Незалежний DSP→SDRAM completion перед mailbox notification досі не доведений. ARM DSB не закриває цю межу. |
| D2 | Actual MDEC66, plain-SPU67,current-SMLAD-WSOLA68 A/H+D/S та strict scenarios перевірено з журналів; packet scopes і missing evidence описані в candidates. | Вердикт стосується виміряних jobs. Async/resident/full-state виграш невідомий; full-game/audio інтеграція є наступною окремою роботою. |
| Відновлення | На04.10 о09:32:35 UTC N95 відповів;5 original files GET/SHA-equal, c55stream/ocprobe PS0, незмінний daemon launch tuple. | Snapshot у цей час, не continuous monitoring або унікальний phone boot ID. |

Поточні paired blocking результати (до setup):

| Kernel і job | ARM A p50, us | DSP path ready p50, us | Blocking winners |
|---|---:|---:|---:|
| MDEC66,1/2/4 macroblocks | 78.201 /110.626 /295.639 | 2655.029 /4272.461 /7690.430 | 0/1080 |
| SPU67,1/8/24voices×64samples | 3.576 /27.180 /40.531 | 1617.432 /3295.898 /3540.039 | 0/1080 |
| WSOLA68,current SMLAD | 337.601 | 1098.633 | 0/360 |

Oracle checks/journaling розташовані поза A/H+D. Instrumented S містить
lifecycle journaling; useful async W та application CPU не виміряні.
Сценарій W0 відповідає blocking probes. Невідомий W не перетворювали
на нульовий запас роботи всієї гри. Detailed p95/p99/max, packet formats,
cases та S/N scenarios збережені в окремих reports:
[MDEC](N95_MDEC_RING_2026-10-04.md),[SPU](N95_SPU_RING_2026-10-04.md),
[WSOLA](N95_WSOLA_CURRENT_2026-10-04.md),
[decision](PS1_CANDIDATES_2026-10-01.md),
[dependency audit](N95_OFFLOAD_DEPENDENCIES_2026-10-04.md).

`python tools/verify_n95_acceptance.py` перевіряє published D0 журнали,
свіжий read-only final-state transport і hashes; потім запускає native61,
CPU64,MDEC,SPU,currentWSOLA,dependency, ARM-cache й measured-DSP compiler
order verifiers. Hardware
commands у ньому відсутні. Локальний ignored archive для D0 більше не
потрібний; source/ROM checks додатково виконуються, коли відповідні
локальні джерела доступні.

Далі потрібен OMAP2420-specific DSP endpoint contract і точний
caller/context cache-completion contract. Це відкриті engineering gates;
success packets не підмінюють architecture proof. Після відкладення E90
до завтра: спочатку GET поточного журналу/PS, потім повернення own
originals і compatible clock qualification, без повтору failed RUN без
нової гіпотези. Реалізація async DSP у PS1Emulator цим дорученням заборонена;
відсутність full gameplay/PCM benchmark не є дозволом почати інтеграцію.
