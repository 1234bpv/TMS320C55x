#requires -Version 7
param(
    [ValidateRange(1,999)][int]$Revision = 1,
    [string]$BinaryPath,
    [ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$OutputName = 'c55stream'
)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path $PSScriptRoot -Parent
$sdkPath = Join-Path (Split-Path $projectPath -Parent) 'S60_3rd_FP1\Epoc32\tools'
$binary = if ($BinaryPath) { (Resolve-Path -LiteralPath $BinaryPath).Path } else { Join-Path $projectPath 'out\arm\c55stream.exe' }
$sisPath = Join-Path $projectPath 'out\sis'
$signPath = Join-Path $sisPath 'sign'
[IO.Directory]::CreateDirectory($signPath) | Out-Null
if (-not (Test-Path -LiteralPath $binary)) { throw 'Build c55stream.exe first' }
$opensslPath = $env:OPENSSL
if (-not $opensslPath) {
    $gitPath = (Get-Command git.exe).Source
    $opensslPath = [IO.Path]::GetFullPath((Join-Path (Split-Path $gitPath -Parent) '..\usr\bin\openssl.exe'))
    if (-not (Test-Path -LiteralPath $opensslPath)) { $opensslPath = (Get-Command openssl.exe).Source }
}
$key = Join-Path $signPath 'sha1.key'
$cert = Join-Path $signPath 'sha1.cer'
if (-not (Test-Path -LiteralPath $key)) {
    & $opensslPath genrsa -out $key 1024
    if ($LASTEXITCODE) { throw 'OpenSSL key generation failed' }
    & $opensslPath req -new -x509 -sha1 -key $key -out $cert -days 3650 -subj '/CN=C55Stream Research'
    if ($LASTEXITCODE) { throw 'OpenSSL certificate generation failed' }
}
$pkg = Join-Path $sisPath "$OutputName.pkg"
$unsigned = Join-Path $sisPath "$OutputName.sis"
$signed = Join-Path $sisPath "${OutputName}_sha1.sis"
$lines = @('&EN', "#{`"C55Stream Research`"},(0xE0001021),1,0,$Revision", '%{"Pavlo Biletskyi"}', ':"Pavlo Biletskyi"', '[0x101F7961],0,0,0,{"Series60ProductID"}', "`"$binary`"-`"c:\sys\bin\c55stream.exe`"")
[IO.File]::WriteAllText($pkg, ($lines -join "`r`n") + "`r`n", [Text.Encoding]::ASCII)
& (Join-Path $sdkPath 'makesis.exe') $pkg $unsigned
if ($LASTEXITCODE) { throw 'makesis failed' }
& (Join-Path $sdkPath 'signsis.exe') -s $unsigned $signed $cert $key
if ($LASTEXITCODE) { throw 'signsis failed' }
$result = & (Join-Path $sdkPath 'signsis.exe') -o $signed
if ($LASTEXITCODE -or -not ($result -match 'Issued')) { throw 'SIS signature verification failed' }
$result
Get-FileHash -LiteralPath $signed -Algorithm SHA256
