@echo off
setlocal enabledelayedexpansion
title VibeSpace Launcher
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo  ============================================
echo          VibeSpace - Project Launcher
echo  ============================================
echo.

rem ---------------------------------------------------------------
rem  [1] ENVIRONMENT CHECK
rem ---------------------------------------------------------------
echo  1/5 Environment check
echo  ----------------------
ver
echo  Working folder: %cd%
echo.

set "PYCMD="
where python >nul 2>nul && set "PYCMD=python"
if not defined PYCMD (where py >nul 2>nul && set "PYCMD=py -3")
if not defined PYCMD goto :NO_PYTHON

echo  Python  : %PYCMD%
%PYCMD% --version
%PYCMD% -m pip --version >nul 2>nul && (echo  pip     : available) || (echo  pip     : MISSING)
echo.

where java >nul 2>nul && (echo  Java JDK: FOUND  ^(Java runner enabled^)) || (echo  Java JDK: not found  ^(optional^))
where dotnet >nul 2>nul && (echo  .NET    : FOUND  ^(C# runner enabled^)) || (echo  .NET    : not found  ^(optional^))
where node >nul 2>nul && (echo  Node.js : FOUND) || (echo  Node.js : not found  ^(not required^))
echo.

if exist "static\monaco\vs\loader.js" (echo  Monaco editor : READY - offline) else (echo  WARNING: Monaco editor files missing - code editor may not load)
if exist "vendor\wheels\*.whl" (echo  Local wheels  : READY - offline install possible) else (echo  NOTE: no local wheels found - install needs internet)
echo.

rem ---------------------------------------------------------------
rem  [2] WRITE-ACCESS TEST
rem ---------------------------------------------------------------
set "WTEST=workspace\.writetest"
(echo ok> "%WTEST%") 2>nul && (del "%WTEST%" >nul 2>nul & echo  Write access : OK) || (echo  WARNING: cannot write to this folder - install may fail)
echo.

rem ---------------------------------------------------------------
rem  [3] INSTALL DEPENDENCIES (offline-first)
rem ---------------------------------------------------------------
echo  2/5 Dependencies
echo  ----------------
if exist "vendor\wheels\*.whl" (
    echo  Trying offline install from local wheels...
    %PYCMD% -m pip install --no-index --find-links="vendor\wheels" -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  Local install failed - trying online fallback...
        %PYCMD% -m pip install -r requirements.txt
    )
) else (
    %PYCMD% -m pip install -r requirements.txt
)
echo.

rem ---------------------------------------------------------------
rem  [4] PICK A FREE PORT
rem ---------------------------------------------------------------
echo  3/5 Choosing port
echo  -----------------
set "PORT=5000"
for /f %%p in ('powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $used = (Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue).LocalPort; 1..80 | ForEach-Object { $c = 4990 + $_; if ($used -notcontains $c) { $c } } | Select-Object -First 1 } catch { '5000' }"') do set "PORT=%%p"
if not defined PORT set "PORT=5000"
echo  Using port: %PORT%
echo.

rem ---------------------------------------------------------------
rem  [5] START SERVER + OPEN BROWSER
rem ---------------------------------------------------------------
echo  4/5 Starting server
echo  -------------------
start "VibeSpace Server" cmd /c "%PYCMD% server.py --host 0.0.0.0 --port %PORT%"

echo  5/5 Waiting for server to start...
set /a tries=0
:WAITLOOP
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:%PORT%/health' -TimeoutSec 1).StatusCode | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
if not errorlevel 1 goto :OPEN_BROWSER
set /a tries+=1
if %tries% lss 25 (timeout /t 1 >nul & goto :WAITLOOP)
echo  WARNING: server not responding yet. Open the browser manually:
echo      http://127.0.0.1:%PORT%/
goto :DONE

:OPEN_BROWSER
echo.
echo  Server ready. Opening browser...
if "%OPEN_BROWSER%"=="no" goto :DONE
start "" "http://127.0.0.1:%PORT%/"
goto :DONE

:NO_PYTHON
echo.
echo  *************************************************************
echo  *  ERROR: Python was not found on this computer.            *
echo  *                                                           *
echo  *  VibeSpace needs Python 3.9 or newer.                     *
echo  *  Install Python from https://www.python.org/downloads/    *
echo  *  and TICK "Add Python to PATH" during installation.       *
echo  *************************************************************
echo.
goto :DONE

:DONE
echo.
echo  ============================================
echo    To stop VibeSpace later:
echo    1. Close the "VibeSpace Server" window
echo    ============================================
echo.
pause
exit /b 0