@echo off
rem  Megatouch Key Tool - launcher
rem  Finds a Python 3 with tkinter and starts the editor. Pass a key file to open it.
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (where python >nul 2>&1 && set "PY=python")

if not defined PY (
  echo.
  echo   Python 3 was not found on this computer.
  echo.
  echo   Install it from https://www.python.org/downloads/ and tick
  echo   "Add python.exe to PATH" in the installer, then run this file again.
  echo.
  pause
  exit /b 1
)

%PY% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
  echo.
  echo   This Python has no tkinter, which the editor needs for its window.
  echo   Re-run the Python installer and enable "tcl/tk and IDLE".
  echo.
  pause
  exit /b 1
)

%PY% "%~dp0mtkeytool.py" %*
if errorlevel 1 (
  echo.
  echo   The editor exited with an error. The message above says why.
  pause
)
endlocal
