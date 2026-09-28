@echo off
REM Synchro ZKTeco (SQL Server) -> PostgreSQL, resultat ajoute dans logs\sync_zkteco.log

set PROJET=D:\Grand_projet_rh\back_rh\grh
set PYTHON=C:\Users\admin\Desktop\Grand_projet_rh\back_rh\env\Scripts\python.exe

REM Force l'UTF-8 pour eviter l'erreur UnicodeEncodeError dans le fichier log
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%PROJET%"
if not exist logs mkdir logs
echo. >> logs\sync_zkteco.log
echo ===== %date% %time% ===== >> logs\sync_zkteco.log
"%PYTHON%" manage.py sync_zkteco >> logs\sync_zkteco.log 2>&1