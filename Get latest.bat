@echo off
rem Gets everyone's newest work into this folder. Anything you haven't shipped yet stays as it is.
cd /d "%~dp0"
py -3 tools\ch.py sync
pause
