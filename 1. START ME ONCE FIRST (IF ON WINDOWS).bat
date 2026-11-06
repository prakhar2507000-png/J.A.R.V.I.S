@echo off
REM ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
title J.A.R.V.I.S.
cd /d "%~dp0"

set "PY="
where py >nul 2>nul
if %errorlevel%==0 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if %errorlevel%==0 set "PY=python"
)
if not defined PY (
    echo.
    echo   Python 3.9 or newer is required.
    echo   Install it from https://www.python.org/downloads/
    echo   Tick "Add Python to PATH" during setup, then run this again.
    echo.
    pause
    exit /b 1
)

%PY% "jarvis_setup.py"
if errorlevel 1 pause
exit /b 0
