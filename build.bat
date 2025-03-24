@echo off
rem TODO: Figure out how to make the Linux scripts, and the 'kiosk' module, available to the KioskForge.exe program.
rem https://stackoverflow.com/questions/11322538/including-a-directory-using-pyinstaller provides tips.
rem --add-data="KioskSetup.py:." --add-data="KioskStart.py:."
pyinstaller --console --noupx --onefile --distpath R:\KioskForge-SHIP --workpath R:\KioskForge-TEMP --upx-exclude python3.dll KioskForge.py

