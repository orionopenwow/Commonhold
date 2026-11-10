@echo off
rem Sets up the Commonhold Discord: makes what is missing and posts each channel's purpose. Deletes nothing.
cd /d "%~dp0"
set "REPO="
set /p "REPO=Repo link for #welcome (Enter to leave it out): "
if defined REPO (py -3 commonhold_discord.py --go --repo "%REPO%") else (py -3 commonhold_discord.py --go)
pause
