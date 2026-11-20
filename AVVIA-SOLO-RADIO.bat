@echo off
title Mostra AC - Radio
cd /d "%~dp0"
rem ---- serve come amministratore per aprire la porta 8080 alla rete Wi-Fi ----
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
netsh advfirewall firewall show rule name="Mostra AC" >nul 2>&1 || netsh advfirewall firewall add rule name="Mostra AC" dir=in action=allow protocol=TCP localport=8080 >nul
rem ---- audio in diretta verso i telefoni: serve l'UDP dalla rete locale ----
netsh advfirewall firewall show rule name="Mostra AC audio" >nul 2>&1 || netsh advfirewall firewall add rule name="Mostra AC audio" dir=in action=allow protocol=UDP remoteip=localsubnet profile=any >nul

rem ---- cerca Python ----
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY (
  echo.
  echo  Python non e' installato su questo PC. Provo a installarlo ^(serve Internet^)...
  echo.
  winget install -e --id Python.Python.3.12 --scope machine --accept-package-agreements --accept-source-agreements
  if exist "%ProgramFiles%\Python312\python.exe" set "PY="%ProgramFiles%\Python312\python.exe""
)
if not defined PY py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  echo.
  echo  ERRORE: Python non trovato.
  echo  Installalo da https://www.python.org/downloads/  ^(spunta "Add python.exe to PATH"^)
  echo  poi fai di nuovo doppio clic su questo file.
  echo.
  pause
  exit /b 1
)
%PY% server.py 8080 qr.html
pause
