@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Marineford OBS Connector

cd /d "%~dp0"
set "PORT=8000"

echo.
echo ============================================================
echo  Marineford OBS Connector
echo ============================================================
echo.

if not exist "server.py" (
  echo [ERROR] server.py was not found.
  echo Run this file inside the marineford_OBS folder.
  echo.
  pause
  exit /b 1
)

set "PY_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py -3"

if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo [ERROR] Python was not found.
  echo Install Python 3, then run this file again.
  echo https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

set "LAN_IP=127.0.0.1"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$ip='127.0.0.1'; foreach($cfg in Get-NetIPConfiguration){ if($cfg.IPv4Address -and $cfg.NetAdapter.Status -eq 'Up'){ foreach($addr in $cfg.IPv4Address){ if($addr.IPAddress -and $addr.IPAddress -notlike '169.254*' -and $addr.IPAddress -ne '127.0.0.1'){ $ip=$addr.IPAddress; break } } } if($ip -ne '127.0.0.1'){ break } }; $ip"`) do set "LAN_IP=%%I"

set "PORT_PID="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if($c){ @($c)[0].OwningProcess }"`) do set "PORT_PID=%%P"

if defined PORT_PID (
  echo [INFO] Port %PORT% is already in use. PID: !PORT_PID!
  echo If Marineford is already running, use the URLs below.
  echo.
) else (
  echo [INFO] Starting Marineford server in a new window...
  start "Marineford OBS Server" /D "%~dp0" cmd /k "%PY_CMD% server.py"
  echo [INFO] Waiting for server response...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ok = $false; for ($i = 0; $i -lt 20; $i++) { try { $null = Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 'http://127.0.0.1:%PORT%/api/state'; $ok = $true; break } catch { Start-Sleep -Milliseconds 500 } }; if (-not $ok) { exit 1 }"
  if errorlevel 1 (
    echo [WARN] Server did not respond yet.
    echo Check the new "Marineford OBS Server" window for errors.
    echo.
  ) else (
    echo [OK] Server is ready.
    echo.
    start "" "http://127.0.0.1:%PORT%/control.html"
  )
)

echo ------------------------------------------------------------
echo  On the streaming PC
echo ------------------------------------------------------------
echo  Control panel : http://127.0.0.1:%PORT%/control.html
echo  OBS overlay   : http://127.0.0.1:%PORT%/overlay.html
echo  Editor helper : http://127.0.0.1:%PORT%/editor.html
echo.
echo ------------------------------------------------------------
echo  On the tablet
echo ------------------------------------------------------------
echo  Tablet panel  : http://%LAN_IP%:%PORT%/tablet.html
echo  Scan the QR code shown in the Control panel.
echo.
echo If the tablet cannot connect:
echo  1. Put the tablet and streaming PC on the same Wi-Fi/router.
echo  2. Allow Python on private networks if Windows Firewall asks.
echo  3. If the IP looks wrong, run ipconfig and use the IPv4 address.
echo.
echo Keep the "Marineford OBS Server" window open.
echo To stop the server, press Ctrl+C in that server window.
echo.
pause
