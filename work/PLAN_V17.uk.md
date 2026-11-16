# V17: умови вимірювання та DSP-таймер

Повний обсяг і критерії — work/PLAN.md; F05–F08 залишаються відкритими.
Вихідний checkpoint1430722: робочий worker512 Б/Q15/ARM overlap/cleanup
на обох телефонах, але частотні зміни N95 і scale таймера не встановлені.

1. Звірити ROM N95 dvfs_interface request0/reserve100/release0, percent
   getter і destructor. До native calls перевіряти live fingerprints.
   Використовувати штатну reservation; нових kernel/PRCM patches немає.
2. Host v17 резервує штатний режим на N95, записує MPU percent до/після
   кожного packet і release до FINAL. На E90 ця гілка не виконується.
3. Worker protocol17 повертає абсолютний CLK_gethtime на offset14 замість
   wire cookie; pointer cookie лишається обов'язковим create/delete gate.
   Решта512-byte формату й Q15 workload не змінюються.
4. worker-calibrate: 8 correct echo packets reps0, без CRC; паузи
   100/200/400/800 мс. DSP stamp має лежати між ARM issue/completion.
   Для delta timestamps вирахувати bounds DSP timer Hz із FastCounter
   brackets, врахувавши один counter tick похибки. Не використовувати164.
5. Source/ASM/imports/DOFF preflight, immutable archive; fresh preparation
   та exact backup. Спершу N95 one; після чистого cleanup — calibration,
   Q15 та три alternating same-condition pairs. Не повторювати negative
   без нового контракту, recovery журналу та normal readback.
6. Повторити підтверджений протокол на E90 після SIS. Після кожної серії
   exact normal і original clocklog restore, PS/INFO/readback.
7. Оновити чесні timing bounds й оцінку application packets, зберегти
   source/proofs у приватному GitHub; повний completion audit окремо.
