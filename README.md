# KioskForge Master README File
KioskForge is a portable tool to automate and simplify the process of setting up a new kiosk machine for browsing a website.

KioskForge currently supports these things:

* Ubuntu Server 24.04.* for AMD64 and ARM64 architectures.
* Creating a kiosk that allows browsing a website using Chromium, which has no address bar so new URLs cannot be entered.
* Touch screen input insofar the particular touch screen is supported out of the box by the supported operating systems.
* Ethernet and/or WIFI networking.

## Development
To develop on KioskForge, install Python v3.11+ and set up these environment variables:

1. `PYTHONDONTWRITEBYTECODE` should be set to `1` to disable the generation of needless Python byte-code files everywhere.
2. `RAMDISK` should be set to point to a temporary folder, preferably on a ram disk.  This is used for caching MyPy data, etc.

Run the script `test.bat` (Windows only) or `test.sh` (Linux only) to make MyPy test the code and report any errors.

**NOTE:**
Currently, the MyPy test is a bit broken because the script uses both Windows-only and Linux-only features, something which
MyPy isn't all that happy about.  This will be fixed in not too long.

