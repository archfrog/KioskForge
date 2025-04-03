@echo off
setlocal

if "%RAMDISK%" == "" goto ErrorRamdisk

set project=KioskForge
mypy --cache-dir %RAMDISK%\%project%\MyPy --strict KioskForge.py KioskOpenbox.py KioskSetup.py KioskStartX11.py KioskUpdate.py build.py %*

goto Epilogue

:ErrorRamdisk
echo Error: RAMDISK environment variable not defined
goto Epilogue

:Epilogue
endlocal

