# sweep.ps1 - прогнати одну точку матриці навантажень на DSP і зібрати серію.
#
#   .\tools\sweep.ps1 -Reps 1000 -Workload 2 -Runs 4 -Tag int32
#
# Один вимір = один прогін (вузол створюється раз за прогін), тому серія - це
# просто повторний запуск ТОГО САМОГО бінарника. Завада може лише сповільнити,
# тож підсумок точки - МІНІМУМ серії (той самий принцип, що й на ARM-боці).
#
# Навантаження: 0=none 1=Q15dot 2=int32 3=fp32 4=branch (див. bench_node.c).

param(
    [Parameter(Mandatory)][string]$Ip,
    [ValidateSet('n95','e90')][string]$Device = 'n95',
    [int]$Reps = 0,
    [int]$Workload = 1,
    [int]$Runs = 4,
    [string]$Tag = "point",
    [int]$Probe = 0,
    [int]$VectorLength = 1024,
    [ValidateRange(0,3)][int]$DataSegment = 0,
    [ValidateRange(1,180)][int]$RunTimeoutSec = 30,
    [switch]$SkipBuild,
    # Додаткові прапорці ARM-боку, дописуються до командного рядка (розбір у
    # dsptest.cpp - пошук підрядка, тож склеювання безпечне). Потрібне для
    # досліду про губернатор: 'armwatch' / 'armbusy'.
    [string]$Extra = ""
)

$ErrorActionPreference = 'Stop'
$proj = Split-Path $PSScriptRoot -Parent
$client = Join-Path $PSScriptRoot 'strict_net.py'
if ($Device -ne 'n95') { throw 'Legacy dsptest has only an N95 firmware profile; use c55stream for E90' }
if ($Tag -notmatch '^[A-Za-z0-9_-]+$') { throw 'Tag must contain only letters, digits, underscores and hyphens' }

Set-Location $proj

if (-not $SkipBuild) {
    & pwsh -NoProfile -File tools\run_bounded.ps1 -Command "call tools\build_dsp_node.cmd $Reps $Workload $Probe $VectorLength $DataSegment" -TimeoutSec 120 -Log out\sweep-build.log | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'node build failed' }
    if (-not (Test-Path "out\dsp\bench.dll55l")) { throw "node build failed" }
}

# Explicit device/IP prevents a LAN scan selecting the other phone.
$ip = $Ip

# Вузол кладемо один раз, далі ганяємо той самий бінарник.
& python $client --ip $ip --device $Device --put 'out\dsp\bench.dll55l' 'E:\bench.dll55l' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'node deployment failed' }

# ARM-бік теж мусить бути свіжим. Спершу цей скрипт клав лише вузол - і прогони
# мовчки виконувались СТАРИМ dsptest.exe, у якого стеля очікування була 4.7 с.
# Через це два навантаження "дали результат" рівно 4.70 с: то був мій власний
# таймаут, а не робота DSP. Правило: точка виміру дійсна лише тоді, коли обидва
# бінарники походять з поточного дерева.
$exe = Join-Path $proj 'out\arm\dsptest.exe'
if (-not (Test-Path $exe)) { throw "no dsptest.exe - run tools\build.cmd first" }
& python $client --ip $ip --device $Device --put $exe 'E:\sys\bin\dsptest.exe' `
    --hash-remote 'C:\sys\hash\dsptest.exe' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'ARM deployment failed' }

$times = @()
foreach ($i in 1..$Runs) {
    $out = "out\sweep_${Tag}_$i.log"
    $command = "EXEC $($RunTimeoutSec*1000) E:\sys\bin\dsptest.exe baseonlydcdopnobench$Extra"
    & python $client --ip $ip --device $Device --timeout ($RunTimeoutSec+5) `
        --cmd $command --require-exit-zero --get 'E:\dsptest.log' $out | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "device run $i failed" }
    $txt = Get-Content $out -ErrorAction SilentlyContinue
    $line = ($txt | Select-String "WALL TIME").Line
    $st   = ($txt | Select-String "node-create status").Line
    # Точка дійсна ЛИШЕ якщо створення завершилось нулем. Інакше час міряє
    # таймаут або аварію, а не роботу DSP (спіймано на fp32/branch/int32).
    #
    # Час витягуємо ОКРЕМИМ -match і одразу зберігаємо: в `A -and B` автоматична
    # $Matches лишається від ОСТАННЬОЇ вдалої відповідності, тобто від перевірки
    # статусу, де групи 1 нема - і серія мовчки збирала нулі.
    $us = $null
    if ($line -match '(\d+) us') { $us = [int]$Matches[1] }
    if ($null -ne $us -and $st -match 'status: 0\s*$') {
        $times += $us
    } elseif ($st) {
        "  [відкинуто] $($st.Trim())"
    }
}

# Частка успіхів - самостійний результат, а не діагностика: за межею ~1 с
# роботи у фазі create вузол створюється НЕ ЗАВЖДИ (виміряно: 1.20 с -> -2,
# 1.38 с -> 0, 1.57 с -> -2). Тому друкуємо ok/Runs завжди, і відсутність
# успіхів - це теж точка даних, а не помилка скрипта.
if ($times.Count -eq 0) {
    "{0,-10} wl={1} reps={2,-7} ok=0/{3}  (жодного успішного створення)" -f `
        $Tag, $Workload, $Reps, $Runs
    return
}
$min = ($times | Measure-Object -Minimum).Minimum
$max = ($times | Measure-Object -Maximum).Maximum
"{0,-10} wl={1} reps={2,-7} min={3,9} us  max={4,9} us  spread={5:P0}  ok={6}/{7}" -f `
    $Tag, $Workload, $Reps, $min, $max, (($max - $min) / $min), $times.Count, $Runs
