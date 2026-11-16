#requires -Version 7
param([switch]$RequireArtifacts,[switch]$RequireStreamArtifacts)
$ErrorActionPreference = 'Stop'
$env:LC_ALL = 'C'
$projectPath = Split-Path $PSScriptRoot -Parent
Push-Location $projectPath
try {
    $envLines = & $env:ComSpec /d /c 'call tools\env.cmd print'
    if ($LASTEXITCODE -ne 0) { throw 'env.cmd failed' }
    $paths = @{}
    foreach ($line in $envLines) { if ($line -match '^([^=]+)=(.*)$') { $paths[$Matches[1]] = $Matches[2] } }
    $required = @(
        (Join-Path $paths.SDKROOT 'Epoc32\tools\bldmake.bat'),
        (Join-Path $paths.TCROOT 'perl\perl\bin\perl.exe'),
        (Join-Path $paths.TCROOT 'CSL_Arm_Toolchain\bin\arm-none-symbianelf-g++.exe'),
        (Join-Path $paths.DSP_CGT 'bin\cl55.exe'),
        (Join-Path $paths.DSP_DOFFBUILD 'bin\dllcreate.exe'),
        (Join-Path $paths.DAEMON 'tools\deploy_net.ps1')
    )
    foreach ($path in $required) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing tool: $path" }
        Write-Output "OK $path"
    }
    $perlVersion = & (Join-Path $paths.TCROOT 'perl\perl\bin\perl.exe') -e 'print $];'
    if ($perlVersion -notmatch '^5\.020') { throw "Expected Perl 5.20, got $perlVersion" }
    $features = Get-Content -LiteralPath work\features.json -Raw | ConvertFrom-Json
    if ($features.features.Count -ne 8 -or (@($features.features.id | Select-Object -Unique)).Count -ne 8) {
        throw 'Feature manifest must contain F01-F08 exactly once'
    }
    foreach ($id in 1..8) { if ($features.features.id -notcontains ('F{0:D2}' -f $id)) { throw "Missing F$id" } }
    if ($RequireArtifacts) {
        foreach ($artifact in @('out\arm\dsptest.exe','out\dsp\bench.dll55l')) {
            if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) { throw "Missing artifact: $artifact" }
            Write-Output "SHA256 $artifact $((Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash)"
        }
    }
    if ($RequireStreamArtifacts) {
        foreach ($artifact in @('out\arm\c55stream.exe','out\dsp\c55stream.dll55l')) {
            if (-not (Test-Path -LiteralPath $artifact -PathType Leaf)) { throw "Missing artifact: $artifact" }
            Write-Output "SHA256 $artifact $((Get-FileHash -LiteralPath $artifact -Algorithm SHA256).Hash)"
        }
    }
    Write-Output "OK environment and manifest; complete=$(@($features.features | Where-Object status -EQ complete).Count)/8"
    if ($features.current_assignment) {
        Write-Output "Current assignment: $($features.current_assignment.status)"
        foreach ($stage in $features.current_assignment.stages) {
            Write-Output "$($stage.id): $($stage.status)"
        }
    }
} finally { Pop-Location }
