@echo off
set PYTHONDONTWRITEBYTECODE=x
cd %~dp0
if %processor_architecture%==x86 (
set ConEmu=lib\ConEmu\ConEmu.exe
set PYTHON="C:\Program Files\LieYing\Plugin\PyRun.exe" --normal
) else (
set ConEmu=lib\ConEmu\ConEmu64.exe
set PYTHON="C:\Program Files (x86)\LieYing\Plugin\PyRun.exe" --normal
)
start %ConEmu% -NoSingle -noupdate -run %PYTHON% test.py
pause
exit