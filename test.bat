@echo off
setlocal

if "%RAMDISK%" == "" goto ErrorRamdisk

set project=KioskForge
mypy --cache-dir %RAMDISK%\%project% --strict %project%.py

goto Epilogue

:ErrorRamdisk
echo Error: RAMDISK environment variable not defined
goto Epilogue

:Epilogue
endlocal

