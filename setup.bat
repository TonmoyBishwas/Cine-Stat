@echo off
REM ---------------------------------------------------------------------------
REM  CineStat - one-time setup (Windows)
REM
REM  Makes a virtual environment in .venv, installs everything in
REM  requirements.txt into it, checks Tkinter is there, and runs the tests.
REM  Run it once, then use run.bat.
REM
REM  A virtual environment rather than a plain "pip install": it keeps this
REM  project's packages out of the Python the rest of the computer uses, and
REM  it is how run.bat finds the right interpreter without being told. .venv
REM  is listed in .gitignore, so it never reaches GitHub.
REM
REM  NOTE for anyone editing this file: never write %errorlevel% inside a
REM  parenthesised block. cmd expands it when it PARSES the block, which is
REM  before the commands in the block have run, so the test reads a stale
REM  value. That is why this file jumps between labels instead of nesting
REM  if-statements - it is not a style choice.
REM ---------------------------------------------------------------------------

setlocal
cd /d "%~dp0"

echo.
echo  CineStat setup
echo  ==============
echo.

REM ---- 1. find a Python -----------------------------------------------------
where py >nul 2>nul
if %errorlevel% equ 0 goto :have_py

where python >nul 2>nul
if %errorlevel% equ 0 goto :have_python

echo  Python was not found on this computer.
echo.
echo  Install it from https://www.python.org/downloads/windows/ and tick
echo  "Add python.exe to PATH" on the first page of the installer. Leave
echo  "tcl/tk and IDLE" ticked as well - that is Tkinter, and this program
echo  is nothing but Tkinter without it.
echo.
echo  Then run this file again.
echo.
pause
exit /b 1

:have_py
set "LAUNCHER=py -3"
goto :found

:have_python
set "LAUNCHER=python"
goto :found

:found
echo  Using:
%LAUNCHER% --version
echo.

REM ---- 2. the virtual environment -------------------------------------------
REM  A .venv is tied to the Python that made it: its python.exe is only a
REM  launcher that forwards to that install's full path. A .venv copied from
REM  another computer (a zip of the folder, a USB stick) therefore exists but
REM  cannot run - "No Python at 'C:\Users\someone-else\...'". So the test is
REM  whether it runs, not whether it exists, and a dead one is rebuilt.
if not exist ".venv\Scripts\python.exe" goto :make_venv
".venv\Scripts\python.exe" -c "import sys" >nul 2>nul
if %errorlevel% equ 0 goto :venv_ready

echo  The .venv folder here does not work on this computer - it was made
echo  on another one, or by a Python that has since been removed.
echo  Deleting it and making a fresh one ...
rmdir /s /q ".venv"
if exist ".venv" goto :venv_stuck

:make_venv
echo  Creating the virtual environment in .venv ...
%LAUNCHER% -m venv .venv
if %errorlevel% neq 0 goto :venv_failed
goto :venv_ready

:venv_failed
echo.
echo  Could not create the virtual environment - the message above says why.
echo.
pause
exit /b 1

:venv_stuck
echo.
echo  Could not delete the old .venv folder - something may still be using
echo  it. Close CineStat and any terminals open in this folder, delete
echo  .venv by hand, and run this file again.
echo.
pause
exit /b 1

:venv_ready
set "VENV=.venv\Scripts\python.exe"

REM ---- 3. the packages ------------------------------------------------------
echo.
echo  Installing the packages from requirements.txt ...
echo  (pandas, numpy, matplotlib, seaborn, scikit-learn - this takes a minute)
echo.
"%VENV%" -m pip install --upgrade pip
"%VENV%" -m pip install -r requirements.txt
if %errorlevel% neq 0 goto :pip_failed
goto :check_tkinter

:pip_failed
echo.
echo  Installing the packages failed - the message above says why.
echo  The usual causes are no internet connection, or a company proxy.
echo.
pause
exit /b 1

REM ---- 4. Tkinter -----------------------------------------------------------
:check_tkinter
echo.
echo  Checking that Tkinter is there ...
"%VENV%" -c "import tkinter; print('  Tkinter', tkinter.TkVersion, 'OK')"
if %errorlevel% neq 0 goto :no_tkinter
goto :run_tests

:no_tkinter
echo.
echo  Tkinter is missing. It ships with Python but can be unticked during
echo  installation. Re-run the Python installer, choose "Modify", and tick
echo  "tcl/tk and IDLE".
echo.
pause
exit /b 1

REM ---- 5. the tests ---------------------------------------------------------
:run_tests
echo.
echo  Running the tests ...
echo.
"%VENV%" -m unittest discover tests
if %errorlevel% neq 0 goto :tests_failed

echo.
echo  ---------------------------------------------------------------
echo   Setup finished. Start CineStat by double-clicking run.bat
echo  ---------------------------------------------------------------
echo.
pause
exit /b 0

:tests_failed
echo.
echo  Setup finished, but some tests did not pass. The program will probably
echo  still start - run.bat - but the failures above are worth reading.
echo.
pause
exit /b 1
