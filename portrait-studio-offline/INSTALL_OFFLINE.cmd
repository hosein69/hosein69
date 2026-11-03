@echo off
setlocal
cd /d "%~dp0"
if not exist "wheelhouse" (echo Missing wheelhouse & pause & exit /b 1)
if not exist "models\birefnet-portrait.onnx" (echo Missing ONNX model & pause & exit /b 1)
echo Checking Python 3.13 and preinstalled NumPy/Pandas ...
py -3.13 -c "import numpy, pandas; print('NumPy:', numpy.__version__, '| Pandas:', pandas.__version__)"
if errorlevel 1 (
 echo ERROR: NumPy and Pandas must be installed in the SAME Python 3.13 environment.
 pause
 exit /b 1
)
py -3.13 -m pip install --no-index --find-links="%~dp0wheelhouse" -r requirements.txt
if errorlevel 1 (echo Offline installation failed: check preinstalled NumPy/Pandas compatibility & pause & exit /b 1)
py -3.13 -m pip check
if errorlevel 1 (echo Dependency check failed & pause & exit /b 1)
echo Offline installation successful.
pause
