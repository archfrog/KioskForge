@echo off
rem --clean
pyinstaller --console --noupx --onefile --distpath R:\KioskForge-SHIP --workpath R:\KioskForge-TEMP --upx-exclude python3.dll KioskForge.py
