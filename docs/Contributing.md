# Contributing to KioskForge
This chapter presents some basic information on how to contribute to KioskForge.

## Philosophy
KioskForge is designed and implemented using three primary requirements:

1. The script must be completely reliable.  This is why we use Python and its exception handling instead of, say, a Bash script.
2. The script must be as user-friendly as possible.  Most people who need a kiosk aren't particularly tech savvy.
3. The script must be portable to all major platforms, Windows and Linux in particular.  This is why we use Tkinter for Python.

It does not matter the least if the script is ugly, a bit clumsy, somewhat suboptimal in terms of execution speed or algorithms.
People probably only use the script occasionally, albeit we want to automate it as much as possible in the future.

## Developing
To develop on KioskForge, install these things first:

```batch
	rem Install Python v3.12+ from https://python.org or using your package manager.
	rem ...

	rem Install MyPy using Pip:
	pip install mypy

	rem Install pylint using Pip:
	pip install pylint

	rem Install bcrypt using Pip:
	pip install bcrypt

	rem Install PyInstaller using Pip:
	pip install pyinstaller

	rem Install pyinstaller-versionfile using Pip:
	pip install pyinstaller-versionfile
```

Then set up these environment variables:

| Environment Variable      | Value | Explanation                                                                             |
| ------------------------- | ----- | --------------------------------------------------------------------------------------- |
| `PYTHONDONTWRITEBYTECODE` | `1`   | Disable the generation of needless Python byte-code files everywhere.                   |
| `RAMDISK` 				| path  | A temporary folder, preferably on a RAM disk.  This is used for caching tool data, etc. |

Run the script `check.py` (all platforms) to make MyPy and pylint test the code and report any discovered warnings and errors.

Run the script `build.py` (all platforms) to build the platform-specific installer, which is normally put at kioskforge.org.

Development currently takes place on a Windows 11 desktop computer, but I'll set up a Linux development environment soon.

