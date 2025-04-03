@echo off
setlocal

if "%RAMDISK%" == "" goto ErrorRamdisk

set project=KioskForge
mypy --cache-dir %RAMDISK%\%project% --strict KioskForge.py KioskOpenbox.py KioskSetup.py KioskUpdate.py

goto Epilogue

:ErrorRamdisk
echo Error: RAMDISK environment variable not defined
goto Epilogue

:Epilogue
endlocal

