@echo off
setlocal
cd /d "%~dp0"
if not exist "wheelhouse" (echo Missing wheelhouse & pause & exit /b 1)
if not exist "models\birefnet-portrait.onnx" (echo Missing ONNX model & pause & exit /b 1)
py -3.13 -m pip install --no-index --find-links="%~dp0wheelhouse" -r requirements.txt
if errorlevel 1 (echo Offline installation failed & pause & exit /b 1)
echo Offline installation successful.
pause
