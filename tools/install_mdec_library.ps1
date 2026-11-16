param([Parameter(Mandatory)][string]$SdkRoot)
$ErrorActionPreference='Stop'
$projectPath=Split-Path $PSScriptRoot -Parent
$builtLibrary=Join-Path $projectPath 'out/mdec-kernel/mdec_probe463.lib'
$sdkLibrary=Join-Path $SdkRoot 'Epoc32/release/armv5/urel/c55xmdec463research.lib'
$ownershipFile=Join-Path $projectPath 'out/mdec-kernel/sdk-library-owner.json'
function LibraryHash([string]$path) {
    $hash=[Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($hash.ComputeHash([IO.File]::ReadAllBytes($path))).Replace('-','') }
    finally { $hash.Dispose() }
}
if (Test-Path -LiteralPath $sdkLibrary) {
    if (-not (Test-Path -LiteralPath $ownershipFile)) { throw 'Refuse preexisting SDK library without ownership record' }
    $previous=Get-Content -LiteralPath $ownershipFile -Raw | ConvertFrom-Json
    if ($previous.path -ne $sdkLibrary -or (LibraryHash $sdkLibrary) -ne $previous.sha256) { throw 'SDK library ownership/hash mismatch' }
}
Copy-Item -LiteralPath $builtLibrary -Destination $sdkLibrary
$metadata=@{path=$sdkLibrary;sha256=(LibraryHash $sdkLibrary)} | ConvertTo-Json
[IO.File]::WriteAllText($ownershipFile,$metadata,[Text.UTF8Encoding]::new($false))
