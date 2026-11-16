# ARM MSG: читання пам'яті та походження вказівників

Продовження відновило результат незавершеного попереднього ходу:
host29 уже був встановлений на E90, а `patcher-read-check` завершився
успішно. Збережений журнал повторно отримано до записів: SHA-256
56167F767D4B30FF225DA24BFB0F6666FD25F16B9FB22B1398D4DBB911195D76,
PS c55stream/ocprobe0, daemon startTick61087 без зміни.
Повторного запуску цього diagnostic не було.

## Що доведено

Control105 копіює 24 байти з адреси у TPtrC8 до буфера нашого процесу.
Три перевірені джерела: власна RAM, ROM-код reader803F7664 і
24-байтова BSS PDD за C8010B20. Перші два дали точні шість очікуваних
ARM instructions. Третій дав DWORD0/1/1/0/0/1. FINAL/EXIT0;
DSP processor не відкривався, kernel code і PRCM не змінювались.

Це доводить примітив читання RAM ядра. **C8010B20 не є адресою MSG
context або reader.** Статичний код використовує перше слово як
прапорець zero/nonzero. Читання цих шести слів не вимірює reader byte64,
адресу спільного вікна чи маршрутизацію повідомлень.

## Перевірений статичний ланцюг

`tools/rev/audit_arm_message_runtime.py` перевіряє 28 instructions,
два BL targets, ROM header BSS address/size і повний reader body.
Публікує адреси, поля й SHA-256 діапазонів; ROM лишається локально.

| Поле | Походження |
|---|---|
| board+264 | Вказівник на context після allocation364 Б і constructor |
| context+48 | Common board, переданий як board+8 |
| context+24 | Reader: common board+164, тобто board+172 |
| reader byte64 | board byte236, у setup записано1 |
| reader DWORD0 | ARM base спільної пам'яті; це ще не fromDSP header |
| context+224 | fromDSP header, обчислений із shared base+16 та layout offset |
| context+240 | Records: fromDSP header+8 |
| queue+16 | Source binding, без перетворення в setter |
| queue+40 | Pending receive; consumer очищує після completion |

Це статичні контракти, а не значення живих об'єктів. Для наступного
snapshot потрібно спочатку довести live board/context root через
аудитований native object lookup, межі allocation/mapping і lifetime.
Самої перевірки числового діапазону kernel pointer недостатньо.
Snapshot буде неатомарним; обхід черг має мати явну межу кількості.

## Відновлення й перевірки

E90 повернуто всі п'ять originals: DLL/log/ocprobe.log/EXE/hash.
Кожний PUT перевірено GET, фінальний verify показав усі п'ять SHA equal,
host20 і PS0. N95 у цьому продовженні не опитувався; його останній
доведений стан лишається restored host20/PS0 з попереднього checkpoint.
Нових MSG/RUN/KILL немає; D0 own0/3, historical experimentalRUN5,
D1 pending, D2 provisional. Перезавантаження чи інша фізична дія не потрібні.

Validator тепер перевіряє точні ROM words, source addresses, розмір,
порядок і спільну destination трьох копій, firmware identity/profile,
FINAL0 і відсутність DSP open. Дев'ять offline tests проходять,
включно з відхиленням пошкоджених/неповних read-copy proofs.
Поточний ARM host29 не перебудовувався: його source/EXE exact hashes
та успішна bounded build збережені в artifact38.

Докази: [поточний checkpoint](evidence/2026-10-02/arm-message-runtime-checkpoint.json),
[статичний аудит](evidence/2026-10-02/e90-arm-message-pointer-audit.json),
[журнал read-copy](evidence/2026-10-02/e90-pointer-readcheck01.txt),
[відновлення](evidence/2026-10-02/e90-pointer-resume-finalverify01.json).
Відтворювана публікація: `tools/summarize_arm_message_runtime.py`;
потребує збережених session/ROM files і не звертається до телефонів.
