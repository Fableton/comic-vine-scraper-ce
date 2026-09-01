<#
.SYNOPSIS
    Builds the distributable .crplugin package, without requiring Ant or
    ipy.exe -- a PowerShell equivalent of build.xml's "dist" target.

.DESCRIPTION
    Flattens src/ (same subfolder list as build.xml's <path id="include.paths">,
    minus src/py/tests) into a clean build/zip directory, substitutes the real
    version (from src/resources/Package.ini) for the "!DEV!" placeholder in
    resources.py, and zips the result into build/ComicVineScraper-<version>.crplugin.

.EXAMPLE
    .\build.ps1
#>

$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
$srcDir = Join-Path $repoRoot 'src'
$buildDir = Join-Path $repoRoot 'build'
$zipDir = Join-Path $buildDir 'zip'

# same subfolder list as build.xml's <path id="include.paths">, minus
# src/py/tests (test-only code, never shipped in the plugin)
$includeDirs = @(
    'py',
    'py\book',
    'py\database',
    'py\database\comicvine',
    'py\gui',
    'py\gui\forms',
    'py\utils',
    'resources',
    'resources\languages'
)

if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
New-Item -ItemType Directory -Path $zipDir | Out-Null

foreach ($rel in $includeDirs) {
    $dir = Join-Path $srcDir $rel
    if (-not (Test-Path $dir)) {
        Write-Warning "Expected source folder missing, skipping: $dir"
        continue
    }
    Get-ChildItem -Path $dir -File | Where-Object { $_.Name -ne '__init__.py' } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $zipDir -Force
    }
}

$packageIni = Join-Path $zipDir 'Package.ini'
$resourcesPy = Join-Path $zipDir 'resources.py'
if (-not (Test-Path $packageIni)) { throw "Package.ini not found in build output" }

$versionLine = Get-Content $packageIni | Where-Object { $_ -match '^\s*Version\s*=' } | Select-Object -First 1
if (-not $versionLine) { throw "Version not found in Package.ini" }
$version = ($versionLine -split '=', 2)[1].Trim()

(Get-Content $resourcesPy -Raw) -replace '"!DEV!"', "`"$version`"" |
    Set-Content -Path $resourcesPy -NoNewline

$pluginPath = Join-Path $buildDir "ComicVineScraper-$version.crplugin"
$tempZip = Join-Path $buildDir "ComicVineScraper-$version.zip"
Compress-Archive -Path (Join-Path $zipDir '*') -DestinationPath $tempZip -Force
Move-Item -Path $tempZip -Destination $pluginPath -Force
Remove-Item $zipDir -Recurse -Force

Write-Output "Built $pluginPath"
