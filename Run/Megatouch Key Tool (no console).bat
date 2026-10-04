@echo off
rem  Same as "Megatouch Key Tool.bat" but without a console window.
setlocal
cd /d "%~dp0"
set "PYW="
where pyw >nul 2>&1 && set "PYW=pyw -3"
if not defined PYW (where pythonw >nul 2>&1 && set "PYW=pythonw")
if not defined PYW (
  call "%~dp0Megatouch Key Tool.bat" %*
  exit /b
)
start "" %PYW% "%~dp0mtkeytool.py" %*
endlocal
