# N95: калібровка CPU-лічильника

Окремий user-mode counterprobe v1 завершив три чисті серії по36 samples,
без DSP, patcher чи performance reservation. Журнал записано після всіх
timing windows. Перед кожною baseline —20ms busy prime; порівняно busy/sleep
1/10/200ms із raw boundaries та явним User::After(1) до baseline і після
роботи. Final yield включено в wall/CPU interval.
[Результати](evidence/2026-10-04/n95-cpu-counter-results.json).

Raw busy1ms і10ms у8/9 samples кожен повернули CPU delta0. Raw sleep10ms
у2/9 samples мав CPU delta більшу за outer wall (max16906us проти wall
приблизно11ms). Це відтворює перенесення обліку попереднього CPU slice
через коротку baseline. Воно виникає без DSP і не свідчить про його
навантаження. Для всіх54 samples із boundary yields CPU delta≤outer wall.
Busy1ms із yields має CPU p50=1007us; busy200ms —197937us; sleep200ms —61us.
Після yield wall включає додатковий sleep і не є kernel latency.

Висновок: старі короткі GetCpuTime deltas та обчислені з них N95 ring
CPU percentages не кваліфіковані як завантаження ARM. Raw values збережені;
новою калібровкою їх не виправляємо. WSOLA63 wall/ARM timings мають окремі
таймери й не залежать від цих CPU deltas. Далі потрібне довге aggregate
ring window із settling boundary, без ARM baseline/file I/O всередині.
Pack/cache/checking costs і final yield треба явно врахувати в межах.

Опублікований [Symbian RThread wrapper](https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/blob/0c3208650587ac0230aed8a74e9bddb5288023eb/kernel/eka/euser/us_exec.cpp#L4818)
передає запит ThreadGetCpuTime; [Exec implementation](https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/blob/0c3208650587ac0230aed8a74e9bddb5288023eb/kernel/eka/kernel/sexec.cpp#L2040)
перетворює counter units у us. У пізнішому
[NKern reference](https://github.com/SymbianSource/oss.FCL.sf.os.kernelhwsrv/blob/0c3208650587ac0230aed8a74e9bddb5288023eb/kernel/eka/nkern/sched.cpp#L109)
getter додає current slice до total. Installed N95 kernel не зіставлено
з цим source: спостережена поведінка відрізняється, тому точну firmware
реалізацію й причину відмінності з reference не заявляємо доведеними.

Усі три власні файли counterprobe до deploy були відсутні; EXE/hash
після PUT перевірено GET-equal. Після трьох EXIT0 перевірено exact EXE/hash
і останній журнал, видалено тільки ці три файли, LS підтвердив відсутність.
П'ять оригіналів c55stream/ocprobe не змінювали; E90 не опитували.
[Artifact proof](evidence/2026-10-04/n95-counterprobe-artifacts.json),
[cleanup](evidence/2026-10-04/n95-counterprobe-remove01.json).
