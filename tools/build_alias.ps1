param(
    [Parameter(Mandatory)][ValidateSet('Create','Remove')][string]$Action,
    [Parameter(Mandatory)][string]$Alias,
    [Parameter(Mandatory)][string]$Project
)
$ErrorActionPreference = 'Stop'
$projectPath = (Resolve-Path -LiteralPath $Project).Path.TrimEnd('\')
$aliasPath = [IO.Path]::GetFullPath($Alias).TrimEnd('\')
$expectedParent = Join-Path ([IO.Path]::GetPathRoot($aliasPath)) 'symbuild'
if ((Split-Path $aliasPath -Parent) -ne $expectedParent -or
    (Split-Path $aliasPath -Leaf) -ne 'c55x') { throw "Unexpected build alias: $aliasPath" }
if (Test-Path -LiteralPath $aliasPath) {
    $item = Get-Item -LiteralPath $aliasPath -Force
    if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw "Build alias is a real directory; refusing to remove it: $aliasPath"
    }
    $target = [IO.Path]::GetFullPath([string](@($item.Target)[0])).TrimEnd('\')
    if ($target -ne $projectPath) { throw "Build alias points to another project: $target" }
    if ($Action -eq 'Remove') { [IO.Directory]::Delete($aliasPath) }
} elseif ($Action -eq 'Create') {
    [IO.Directory]::CreateDirectory($expectedParent) | Out-Null
    New-Item -ItemType Junction -Path $aliasPath -Target $projectPath | Out-Null
}
