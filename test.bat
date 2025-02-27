@echo off
setlocal
set project=KioskForge
mypy --cache-dir %RAMDISK%\%project% --strict %project%.py
endlocal
