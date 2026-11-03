@echo off
setlocal
cd /d "%~dp0"
set "U2NET_HOME=%~dp0models"
py -3.13 -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
pause
