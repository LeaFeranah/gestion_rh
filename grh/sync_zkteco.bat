@echo off
REM Synchro ZKTeco (SQL Server) -> PostgreSQL, resultat dans logs\sync_zkteco.log
REM Chemins relatifs a ce .bat (dans back_rh\grh, Python dans back_rh\env)

set PROJET=%~dp0
set PYTHON=%~dp0..\env\Scripts\python.exe

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%PROJET%"
if not exist logs mkdir logs
echo. >> logs\sync_zkteco.log
echo ===== %date% %time% ===== >> logs\sync_zkteco.log
if not exist "%PYTHON%" (
  echo Python introuvable : %PYTHON% >> logs\sync_zkteco.log
  exit /b 1
)
"%PYTHON%" manage.py sync_zkteco >> logs\sync_zkteco.log 2>&1