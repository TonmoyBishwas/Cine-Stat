@echo off
REM ---------------------------------------------------------------------------
REM  CineStat - start the application (Windows)
REM
REM  Double-click this file, or run it from a terminal:
REM      run.bat                     the dataset that ships with the repo
REM      run.bat data\tmdb.csv       the big Kaggle dataset, if you have it
REM
REM  It prefers the virtual environment made by setup.bat, falls back to the
REM  "py" launcher that the official Python installer puts on the PATH, and
REM  falls back again to plain "python" for anyone who installed it another
REM  way. If the program stops with an error the window is held open so the
REM  message can actually be read - a batch file launched from Explorer
REM  otherwise closes the instant it finishes, taking the error with it.
REM ---------------------------------------------------------------------------

setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    goto :run
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=py -3"
    goto :run
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON=python"
    goto :run
)

echo.
echo Python was not found on this computer.
echo.
echo Install it from https://www.python.org/downloads/windows/ and tick
echo "Add python.exe to PATH" on the first page of the installer, then run
echo setup.bat in this folder.
echo.
pause
exit /b 1

:run
%PYTHON% main.py %*
if %errorlevel% neq 0 (
    echo.
    echo CineStat stopped with an error - the message above says why.
    echo If a package is missing, run setup.bat in this folder first.
    echo.
    pause
)
endlocal
