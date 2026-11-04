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
# Include a checked lightweight fallback for malformed/incompatible primary ONNX files.
$fallbackUrl='https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx'
Invoke-WebRequest -Uri $fallbackUrl -OutFile models/u2netp.onnx
$fallbackHash=(Get-FileHash models/u2netp.onnx -Algorithm MD5).Hash.ToLowerInvariant()
if ($fallbackHash -ne '8e83ca70e441ab06c318d82300c84806') { throw "Wrong fallback checksum: $fallbackHash" }

# Test genuine ONNX loading on Windows. A matching hash does not prove loadability.
py -3.13 -m pip install --no-index --find-links=wheelhouse onnxruntime
if ($LASTEXITCODE -ne 0) { throw 'Cannot install runtime for model verification' }
@'
from pathlib import Path
import onnxruntime as ort
for name in ("birefnet-portrait", "u2netp"):
    path=Path("models") / (name+".onnx")
    print("Checking model with ONNX Runtime:", name, "size", path.stat().st_size)
    try:
        s=ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        print("MODEL_OK", name, "inputs:", [x.name for x in s.get_inputs()])
    except Exception as e:
        print("MODEL_FAILED", name, repr(e))
        if name=="u2netp":
            raise
'@ | py -3.13 -
if ($LASTEXITCODE -ne 0) { throw 'Model verification failed' }

Compress-Archive -Path app.py,requirements.txt,START_STREAMLIT.cmd,INSTALL_OFFLINE.cmd,wheelhouse,models -DestinationPath PortraitStudio_WIN11_PY313_NO_NUMPY_PANDAS.zip -Force
