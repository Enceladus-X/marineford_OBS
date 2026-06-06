$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$version = "1.4"
$exeName = "Marineford_OBS_v$version"

if (-not (Get-Command py -ErrorAction SilentlyContinue) -and -not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python 3 is required to build the release executable."
}

$python = "python"
if (Get-Command py -ErrorAction SilentlyContinue) {
  $python = "py -3"
}

Invoke-Expression "$python -m pip show pyinstaller *> `$null"
if ($LASTEXITCODE -ne 0) {
  Invoke-Expression "$python -m pip install pyinstaller"
}

Invoke-Expression "$python -m pip show qrcode *> `$null"
if ($LASTEXITCODE -ne 0) {
  Invoke-Expression "$python -m pip install `"qrcode[pil]`""
}

Remove-Item -LiteralPath "$root\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$root\dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath "$root\$exeName.spec" -Force -ErrorAction SilentlyContinue

$pyInstallerArgs = @(
  "-m", "PyInstaller",
  "--noconfirm",
  "--clean",
  "--onefile",
  "--name", $exeName,
  "--hidden-import", "qrcode.image.svg",
  "--add-data", "control.html;.",
  "--add-data", "tablet.html;.",
  "--add-data", "overlay.html;.",
  "--add-data", "editor.html;.",
  "--add-data", "state.example.json;.",
  "--add-data", "images;images",
  "server.py"
)

if ($python -eq "py -3") {
  & py -3 @pyInstallerArgs
} else {
  & python @pyInstallerArgs
}

$exePath = Join-Path $root "dist\$exeName.exe"
if (-not (Test-Path -LiteralPath $exePath)) {
  throw "Build failed: $exePath was not created."
}

Write-Host ""
Write-Host "Built release executable:"
Write-Host $exePath
