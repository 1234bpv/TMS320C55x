#requires -Version 7
param(
    [Parameter(Mandatory)][string]$Command,
    [ValidateRange(1,3600)][int]$TimeoutSec = 180,
    [string]$Log = 'out/process.log'
)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path $PSScriptRoot -Parent
$logPath = [IO.Path]::GetFullPath((Join-Path $projectPath $Log))
[IO.Directory]::CreateDirectory((Split-Path $logPath -Parent)) | Out-Null
$start = [Diagnostics.ProcessStartInfo]::new()
$start.FileName = $env:ComSpec
$start.Arguments = '/d /s /c "' + $Command + '"'
$start.WorkingDirectory = $projectPath
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
$process = [Diagnostics.Process]::new()
$process.StartInfo = $start
$startedAt = [DateTime]::UtcNow
try {
    if (-not $process.Start()) { throw 'Process did not start' }
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $finished = $process.WaitForExit($TimeoutSec * 1000)
    if (-not $finished) { $process.Kill($true); $process.WaitForExit() }
    $text = $stdout.GetAwaiter().GetResult() + "`n" + $stderr.GetAwaiter().GetResult()
    $exitCode = if ($finished) { $process.ExitCode } else { 124 }
    $metadata = "UTC=$($startedAt.ToString('o'))`nCOMMAND=$Command`nTIMEOUT_SEC=$TimeoutSec`nEXIT_CODE=$exitCode`n"
    [IO.File]::WriteAllText($logPath, $metadata + $text, [Text.UTF8Encoding]::new($false))
    Write-Output $text
    Write-Output "[bounded] exit=$exitCode log=$logPath"
    exit $exitCode
} finally { $process.Dispose() }
