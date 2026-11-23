@echo off
title Mostra AC
cd /d "%~dp0"

rem ---- solo la prima volta: apre le porte del programma nel firewall (serve l'amministratore) ----
netsh advfirewall firewall show rule name="Mostra AC" >nul 2>&1
if %errorlevel% neq 0 goto firewall
netsh advfirewall firewall show rule name="Mostra AC ricerca PC" >nul 2>&1
if %errorlevel% neq 0 goto firewall
goto python

:firewall
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo  Prima configurazione: Windows chiedera' il permesso di amministratore. Rispondi SI.
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
netsh advfirewall firewall delete rule name="Mostra AC" >nul 2>&1
netsh advfirewall firewall delete rule name="Mostra AC ricerca PC" >nul 2>&1
netsh advfirewall firewall add rule name="Mostra AC" dir=in action=allow protocol=TCP localport=8080 profile=any >nul
netsh advfirewall firewall add rule name="Mostra AC ricerca PC" dir=in action=allow protocol=UDP localport=47800 profile=any >nul

:python
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
  echo.
  echo  Python non e' installato su questo PC. Lo installo ^(serve Internet, solo la prima volta^)...
  echo.
  winget install -e --id Python.Python.3.12 --scope machine --accept-package-agreements --accept-source-agreements
  if exist "%ProgramFiles%\Python312\python.exe" set "PY="%ProgramFiles%\Python312\python.exe""
)
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  echo.
  echo  ERRORE: Python non trovato.
  echo  Installalo da https://www.python.org/downloads/  ^(spunta "Add python.exe to PATH"^)
  echo  poi fai di nuovo doppio clic su AVVIA.
  echo.
  pause
  exit /b 1
)
%PY% server.py
pause
