# KioskForge Readme File
[KioskForge](https://kioskforge.org) is a program to automate and simplify the process of setting up a new kiosk machine.  It is
intended to be used by somewhat non-technical users to set up a kiosk machine for browsing a given website or by more advanced
users to set up a kiosk that runs a CLI or GUI app of the user's choice.

## Features
KioskForge currently supports these things:

* Ubuntu Server 24.04.2 (this is a Long Term Support release, which will be supported by Ubuntu until June 2029).
* Raspberry Pi 4B/5 (2+ GB RAM) ARM64 (aarch64) and PC x64/AMD64 machines (4+ GB RAM).
* Creating a kiosk that allows browsing a website using Chromium in kiosk mode (without an URL address bar).
* Creating a kiosk that runs a command-line (CLI) application programmed by the user.
* Touch screen input insofar the particular touch screen is supported out of the box by the target operating system.
* Ethernet and/or Wi-Fi networking.
* Configuring basic Linux things such as host name, keyboard layout, locale, time zone, etc.
* Rotating standard or touch-panel displays.

**NOTE**: Intel Compute Sticks freeze randomly with Ubuntu Server 24.04.x so they are *not* supported at all.

**NOTE**: The PC target is currently likely broken because I don't have a spare PC to test it on.  WIP.

**NOTE**: Prelimary support for Raspberry Pi 5 has been added, but it is not mature yet.  Audio has not been tested yet on Pi5.


## Overview
### Audience
KioskForge is intended to be used by all sorts of users for which reason it strives to require as little technical knowledge as
possible and to automate the creation (forging) of the kiosk as much as possible.

### Process
KioskForge works by modifying a supported Ubuntu Server installation medium according to the settings the user has given in a
`.kiosk` file (an INI-style configuration file).  The format of the `.kiosk` file is very simple and does not require a lot of
technical knowledge.  After the installation medium has been configured by KioskForge, it is inserted into the target machine,
which is then powered on, and the actual "forge process" takes place.  Over a period of 10 to 30 minutes, the forge process
configures, updates, modifies, and prepares the target kiosk machine to work as a kiosk machine (on a permanent basis, not
requiring any maintenance whatsoever after the initial deployment).

### Starting KioskForge with a given Kiosk file
You can easily open any `.kiosk` file in KioskForge simply by double-clicking the file (this requires that you have installed
KioskForge using the Windows installer).  This is the recommended way of opening a `.kiosk` file in KioskForge.

### Creating a New Kiosk from Scratch
To create a new, blank `.kiosk` file, start KioskForge (either from the Windows Start menu or by double-clicking a `.kiosk` file)
and then select `1` to create new, blank kiosk in memory.  Then save that new, blank kiosk to disk using menu item `4`.

### Configuring the Kiosk
To configure your kiosk, make a copy of a blank `.kiosk` file and edit it using your favorite editor such as `Notepad`.  Please
notice that you *cannot* use Microsoft Word or similar word processing software to edit the `.kiosk` file.

**HINT**: Please check *every* option in the `.kiosk` file before you try to make a kiosk.  There are only about 25 options, all
fairly decently documented in the `.kiosk` file that KioskForge saves to disk, and if you make a simple, tiny error, you'll have
to spend another half hour forging the kiosk again!

**NOTE**:
Currently, the interactive editor in KioskForge *cannot* handle blank strings, so you may need to edit the configuration file
manually using your favorite editor such as `Notepad` (you cannot use a word processor such as Word to edit KioskForge
configuration files!).

### Configuring the Linux Installation Medium
When you have started KioskForge by double-clicking a `.kiosk` file, you make sure the Linux installation medium, made with
[Raspberry Pi Imager](https://www.raspberrypi.com/software/), is inserted into a USB port in your Windows computer, then you simply
select menu item `5` in KioskForge and it will very quickly modify the installation medium to prepare it for making a new kiosk.

Once KioskForge has updated the Linux installation medium, it will ask you to safely remove the medium and insert it into the kiosk
machine.  Just follow the instructions and then power on the kiosk to begin the actual process of forging the desired kiosk.


## Installation
This chapter explains the current method of installing KioskForge on a new PC without any KioskForge installation.

Please notice that we recommend specific versions of Python and Raspberry Pi Imager as we want to ensure the best, most efficient
experience for you.  You are free to try with other versions of these tools, but we cannot guarantee that they work.

### Windows
Download the most recent version of `KioskForge-x.yy-Setup.exe` from [KioskForge.org](https://kioskforge.org/downloads/).

Navigate to the `Downloads` folder and double-click on the `KioskForge-x.yy-Setup.exe` file.  Follow the prompts to install.  If
you have installed KioskForge before, you should probably skim the `CHANGES.html` file and see if there's anything important to
you.

After this, you can launch KioskForge directly from Windows Explorer, by double-clicking a `.kiosk` file, or from the Start menu
by clicking on the `KioskForge` command.


### Linux
**NOTE:** `KioskForge` currently *cannot* be run on Linux.  This is a planned feature and is expected to be fixed sometime.

Install a recent version of the [Python v3.12+ programming language](https://python.org).  On most Linuxes, this can be done with
the system-wide package manager such as `apt`, `dnf`, `pacman`, and so on.  Make sure to install Python v3.12+.  Earlier versions
should work fine, especially v3.10+, but I don't test against these and don't use older versions of Python during development.

Then fetch KioskForge from GitHub using the following command:

```bash
git clone https://github.com/vhmdk/KioskForge
```

You need to make sure that the script, `KioskForge.py`, has execute permissions (use `chmod u+x KioskForge.py` to accomplish that),
then you can invoke it using `./KioskForge.py`.


### Macintosh
I don't have access to a Mac computer, so no development or testing is done on this platform.  Feel free to port the script and
submit a pull request.  Please make sure that the result generates a valid, reliable kiosk before submitting the pull request.


## Philosophy
KioskForge is designed and implemented using three primary requirements:

1. The script must be completely reliable.  This is why we use Python and its exception handling instead of, say, a Bash script.
2. The script must be as user-friendly as possible.  Most people who need a kiosk aren't particularly tech savvy.
3. The script must be portable to all major platforms, Windows and Linux in particular.  This is why we will use Tkinter for Python.

It does not matter the least if the script is ugly, a bit clumsy, somewhat suboptimal in terms of execution speed or algorithms.
People probably only use the script occasionally, albeit we want to automate it as much as possible in the future.


## Limitations
KioskForge is currently an interactive console command, but a GUI version is in the works and will probably be released within a
few months (sometime during Summer 2025).

KioskForge currently uses the X11 windowing system when running Chromium (the open source version of Google Chrome).  This will be
changed eventually so that KioskForge uses the more modern and slightly faster Wayland windowing system.

KioskForge currently only supports DHCP-assigned LAN IP adresses so there's no way of specifying a fixed LAN IP address.  This
basically means you need to talk to your network administrator about getting a static DHCP lease for the kiosk machine itself,
which is a very good idea, anyway, as you don't want to work blindly if the kiosk suddenly misbehaves and needs fixing.


## Usage
KioskForge is a simple application that allows you to create, load, edit, and save a *kiosk configuration* - an INI-style file
that defines the kiosk and what it is supposed to do.  After that, you can choose to *update* an installation media to apply the
configuration during installation.

**NOTE**: The kiosk MUST be connected to the internet while it is being forged!  After this, it can stay offline forever.

It is always best that the kiosk is permanently on the internet so that it can update Chromium, etc.  But it can work without.

As of now, the procedure is as follows:

1. Create an `Ubuntu Server 24.04.2` installation media for Raspberry Pi 4B (ARM64) using a USB key or a MicroSD card:
	1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).  Make sure you **don't** use *OS Customisations*.
	2. [Raspberry Pi Imager Guide](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).
	3. You'll find `Ubuntu Server 24.04.2` in the category `Other general-purpose OS`.  Always use 64-bit editions only.
	4. Be aware that newer Ubuntu Server server versions may pop up in the list when released so be careful what you select!
	5. When done, leave the installation media in your computer until KioskForge tells you to safely remove it (or dismount it).
	6. Also, be sure to **not** select `Ubuntu Desktop` (KioskForge will detect this, though, and report an error).
	7. Please notice that we recommend MicroSD cards over USB keys as the latter have a tendency to get very hot and unreliable.
2. Copy the file `Template.kiosk` from `C:\Program Files\KioskForge\Template.kiosk` to your Desktop or wherever you want it.
   Please rename the `Template.kiosk` file to something more appropriate after having copied it.
3. Edit the new, renamed `.kiosk` by opening it in `Notepad`.  When you are done editing it, save it to disk using `Ctrl-S`.
4. Double-clock on the new, renamed `.kiosk` file to open it in KioskForge.
5. Select the `Update Raspberry Pi Imager prepared installation media` (`5`) to have KioskForge modify the install media so that
   it installs and launches an actual Linux kiosk as per your specification in the new, renamed `.kiosk` file.
6. Press `ENTER` to exit KioskForge.
7. Use Windows' *Safe Removal* feature or `Eject` from Windows Explorer to safely unmount the installation media.
8. Move the installation media to the powered off kiosk machine.
9. Power on the kiosk machine.
10. Wait 10 to 30 minutes (this depends a lot on the I/O speed of the installation media) until the kiosk has been forged,
    which is shown by the kiosk rebooting into kiosk mode.
11. Try out and test the new kiosk.  If you find issues, please either modify your `.kiosk` file or report them to us.
12. You can either attach a keyboard or SSH into the box (the LAN IP address is shown when the kiosk boots) to power it off.
13. Mount the Raspberry Pi in whatever enclosure you are using for your kiosk.  This is typically custom made by carpenters.

After that, the kiosk should *theoretically* run nicely and reliably for years and years.  However, you may want to log into it,
using SSH, once in a while to verify that logs are being rotated, that there is sufficient disk space available, and so on.  The
kiosk is set up to automatically reclaim as much space as it can, whenever the daily maintenance script runs.

If you SSH into the kiosk or use a local keyboard to log in, you can use the `kiosklog` command to view `syslog` entries related
to KioskForge.  If you only want to view *errors*, append the option `-p 3`: `kiosklog -p 3 | more`.


## Development
To contribute to KioskForge, install these things first:

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

Development currently takes place on a Windows 11 Pro desktop computer, but I'll set up a Linux development environment soon.


## Bugs and Ideas
Please report bugs and ideas on [KioskForge Issues at GitHub](https://github.com/vhmdk/KioskForge/issues) or by mail to
[Mikael Egevig](mailto:me@vhm.dk).  The former is the preferred method, but use whichever suits you best.

When you report a bug, please log into the kiosk and run this command to create a log file:

```bash
kiosklog > ~/kiosk.log
```

Then please include the two files `~/kiosk.log` and `~/.xsession-errors` (if it exists) in your bug report.  These files will
likely provide invaluable information about the issue, which makes it so much easier to debug and fix the issue.

