$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-Location $PSScriptRoot

# Download complete dependency graph for Windows x64 / CPython 3.13.
py -3.13 -m pip download --dest wheelhouse --only-binary=:all: --python-version 3.13 --platform win_amd64 --implementation cp --abi cp313 -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Wheel download failed' }

# NumPy and Pandas MUST already be installed on the target PC.
# Exclude only their wheels; preserve all other dependencies.
Get-ChildItem wheelhouse -File | Where-Object { $_.Name -match '^(numpy|pandas)-.*\.whl$' } | ForEach-Object {
  Write-Host "Excluding preinstalled package: $($_.Name)"
  Remove-Item $_.FullName -Force
}

New-Item -ItemType Directory -Force -Path models | Out-Null
$uri='https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-portrait-epoch_150.onnx'
Invoke-WebRequest -Uri $uri -OutFile models/birefnet-portrait.onnx
$model = Get-Item models/birefnet-portrait.onnx
if ($model.Length -lt 100MB) { throw 'Incomplete model file' }
$hash=(Get-FileHash models/birefnet-portrait.onnx -Algorithm MD5).Hash.ToLowerInvariant()
if ($hash -ne 'c3a64a6abf20250d090cd055f12a3b67') { throw "Wrong model checksum: $hash" }
Compress-Archive -Path app.py,requirements.txt,START_STREAMLIT.cmd,INSTALL_OFFLINE.cmd,wheelhouse,models -DestinationPath PortraitStudio_WIN11_PY313_NO_NUMPY_PANDAS.zip -Force
