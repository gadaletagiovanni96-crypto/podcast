@echo off
title Telecomando TV AC
cd /d "%~dp0"
rem Serve come amministratore per aprire la porta 8080 alla rete Wi-Fi
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
netsh advfirewall firewall show rule name="TV AC telecomando" >nul 2>&1 || netsh advfirewall firewall add rule name="TV AC telecomando" dir=in action=allow protocol=TCP localport=8080 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0server.ps1"
pause
