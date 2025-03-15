@echo off

rem Call MyPy to check for obvious errors.
call test.bat
pause

rem Show git status (everything should be checked in).
git status
pause

rem Prepare distribution archive.
if exist "%RAMDISK%\KioskForge.zip" del "%RAMDISK%\KioskForge.zip"
7z a %RAMDISK%\KioskForge.zip KioskForge.py FAQ.md README.md LICENSE

rem Upload distribution archive to Egevig.org (temporary solution).
"C:\Program Files\Git\usr\bin\scp.exe" -F u:\.ssh\config -p %RAMDISK%\KioskForge.zip web:web/pub/egevig.org/KioskForge.zip

