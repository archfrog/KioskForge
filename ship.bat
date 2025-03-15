@echo off

rem Call MyPy to check for obvious errors.
call test.bat
pause

rem Show git status (everything should be checked in).
git status
pause

rem Prepare distribution archive.
7z a %RAMDISK%\KioskForge.zip KioskForge.py FAQ.md README.md LICENSE

rem Upload distribution archive to Egevig.org (temporary solution).
scp -pf %RAMDISK%\KioskForge.zip web:web/pub/egevig.org/KioskForge.zip

