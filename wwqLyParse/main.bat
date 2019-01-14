@echo off
set PYTHONDONTWRITEBYTECODE=x
cd %~dp0
if %processor_architecture%==x86 (
set ConEmu=lib\ConEmu\ConEmu.exe
set PYTHON="%~dp0lib\python-3.7.2-embed-amd32\wwqLyParse32.exe"
) else (
set ConEmu=lib\ConEmu\ConEmu64.exe
set PYTHON="%~dp0lib\python-3.7.2-embed-amd64\wwqLyParse64.exe"
)
SysArch.exe | find "Windows XP" && set PYTHON="C:\Program Files\LieYing\Plugin\PyRun.exe" --normal
SysArch.exe | find "2003" && set PYTHON="C:\Program Files\LieYing\Plugin\PyRun.exe" --normal
start %ConEmu% -NoSingle -noupdate -run %PYTHON% main.py --force_start true
exit