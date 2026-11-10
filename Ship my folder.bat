@echo off
rem Sends the changes in your own members\<you>\ folder. They merge by themselves once the guard check passes.
cd /d "%~dp0"
set "MSG="
set /p "MSG=What changed? "
py -3 tools\ch.py ship -m "%MSG%"
pause
