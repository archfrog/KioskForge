# Contributing to KioskForge
This chapter presents some basic information on how to contribute to KioskForge.

## Philosophy
KioskForge is designed and implemented using three primary requirements:

1. The script must be completely reliable.  This is why we use Python and its exception handling instead of, say, a Bash script.
2. The script must be as user-friendly as possible.  Most people who need a kiosk aren't particularly tech savvy.
3. The script must be portable to all major platforms, Windows and Linux in particular.

It does not matter the least if the script is ugly, a bit clumsy, somewhat suboptimal in terms of execution speed or algorithms.
People probably only use the script occasionally, so it doesn't matter if the UI doesn't win any design contests.

## Developing
Contributions to KioskForge are very welcome, be it actual GitHub pull requests (PRs), bug reports, suggestions, or other things.

### Preparation
To prepare for developing on KioskForge, follow this procedure:

1. Install [Python v3.13.7](https://www.python.org/downloads/release/python-3137/) (to be able to use Python globally).
2. Install [uv](https://github.com/astral-sh/uv) as per the `Installation` section on that page.
3. Create and/or change directory to the parent directory of where you want the KioskForge sources to live.
4. Checkout the KioskForge repository using Git: `git clone https://github.com/vhmdk/KioskForge`
5. Change into the KioskForge folder: `cd KioskForge`
6. Activate the virtual environment on Windows: `.venv\Scripts\activate`
7. Activate the virtual environment on Linux/Mac: `source .venv/bin/activate`
8. Download and install required dependencies: `uv sync`
9. Run the static analyzers on Windows: `check.py`
10. Run the static analyzers on Linux: `./check.py`

### Dependencies
The actual list of [PyPi](https://pypi.org) packages that KioskForge uses is as follows:

| PyPi Package              | Description                                                                                    |
| ------------------------- | ---------------------------------------------------------------------------------------------- |
| `bcrypt`                  | A password hasher used to hash the user's password prior to forging the kiosk.                 |
| `MyPy`                    | A static source code analyzer, which can detect a lot of potential issues in the code.         |
| `PyInstaller`             | Generates the single-file `.exe` for running KioskForge on Windows without install Pyton, etc. |
| `pyinstaller-versionfile` | Generates a version file, for use by `PyInstaller`, which contains `.exe` version information. |
| `pylint`                  | A static source code linter, which primarily attempts to ensure good code quality.             |
| `pyrefly`                 | Yet another static source code analyzer, which catches stuff that the others don't.            |

### Environment
Set up these environment variables:

| Environment Variable      | Value | Explanation                                                                             |
| ------------------------- | ----- | --------------------------------------------------------------------------------------- |
| `PYTHONDONTWRITEBYTECODE` | `1`   | Disable the generation of needless Python byte-code files everywhere.                   |
| `RAMDISK` 				| path  | A temporary folder, preferably on a RAM disk.  This is used for caching tool data, etc. |

The environment variables should be set at all times when working on KioskForge, especially when using the `build.py` and
`check.py` development scripts.

Run the script `check.py` (all platforms) to make MyPy and pylint test the code and report any discovered warnings and errors.

Run the script `build.py` (all platforms) to build the platform-specific installer, which is normally downloadable from
[KioskForge.org](https://kioskforge.org).

**NOTE**:
The `build.py` takes an option, `--ship`, which you should not attempt to use.  It builds the Windows setup program using
[Inno Setup](https://jrsoftware.org/isinfo.php) and copies the built setup program to my personal web server so it will fail on
your equipment as you don't have the SSH configuration and private key to my personal web server...

Development currently happens on a Windows 11 desktop computer, but I'll set up a Linux development environment soon.
