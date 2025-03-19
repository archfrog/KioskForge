@echo off
setlocal

rem Call MyPy to check for obvious errors.
call test.bat
pause

rem Show git status (everything should be checked in).
git status
pause

rem Prepare distribution archive.
set image=%RAMDISK%\KioskForge.zip
if exist "%image%" del "%image%"
7z a "%image%" KioskForge.py FAQ.md README.md LICENSE

rem Upload distribution archive to Egevig.org (temporary solution).
"C:\Program Files\Git\usr\bin\scp.exe" -F u:\.ssh\config -p "%image%" web:web/pub/kioskforge.org/KioskForge.zip

rem Clean up the Ram disk after use.
if exist "%image%" del "%image%"

endlocal
