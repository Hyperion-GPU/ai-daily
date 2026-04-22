$ErrorActionPreference = "Stop"

$root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$source = Join-Path $PSScriptRoot "AIDailyLauncher.cs"
$output = Join-Path $root "dist\AI Daily.exe"
$icon = Join-Path $root "assets\branding\ai-daily.ico"

if (-not (Test-Path -LiteralPath $source)) {
    throw "Launcher source not found: $source"
}

if (-not (Test-Path -LiteralPath (Join-Path $root "dist\AI Daily\AI Daily.exe"))) {
    throw "Onedir runtime not found. Run PyInstaller with build\windows\AI Daily.spec first."
}

$cscCandidates = @(
    "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)
$csc = $cscCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $csc) {
    throw "C# compiler not found under $env:WINDIR\Microsoft.NET."
}

if (Test-Path -LiteralPath $output) {
    Remove-Item -LiteralPath $output -Force
}

& $csc `
    /nologo `
    /target:winexe `
    /platform:anycpu `
    "/win32icon:$icon" `
    "/reference:System.Windows.Forms.dll" `
    "/out:$output" `
    "$source"
if ($LASTEXITCODE -ne 0) {
    throw "Launcher compilation failed with exit code $LASTEXITCODE."
}

Write-Host "Built fast launcher: $output"
