@echo off
REM Launches the Streamlit dashboard from this folder using the local venv.
REM Usage: run_dashboard.bat [port]   (default port 8501)
cd /d "%~dp0"
set PORT=%1
if "%PORT%"=="" set PORT=8501
if not exist venv\Scripts\python.exe (
  echo venv not found. Create it first: py -3.11 -m venv venv ^&^& venv\Scripts\python -m pip install -r requirements.txt -c constraints.txt
  exit /b 1
)
venv\Scripts\python.exe -m streamlit run app.py --server.port %PORT% --server.headless true --browser.gatherUsageStats false
