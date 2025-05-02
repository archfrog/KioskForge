# KioskForge README File
[KioskForge](https://kioskforge.org) is a program to automate and simplify the process of setting up a new kiosk machine.

## Synopsis
KioskForge is intended to be used by somewhat non-technical users to set up a kiosk machine for browsing a given website or by more
advanced users to set up a kiosk that runs a CLI or GUI app of the user's choice.

KioskForge takes two inputs:

1. An Ubuntu Server 24.04.2 installation medium (created using [Raspberry Pi Imager](https://www.raspberrypi.com/software/)).
2. A "kiosk file", which is a configuration file that specifies the values of all the settings that KioskForge supports.

The first, the Ubuntu Server installation medium, is automatically located on the host machine, if it is present.  The second,
the kiosk file, is specified as an argument to KioskForge, which is most easily done simply by double-clicking on the kiosk file.

KioskForge then modifies the Ubuntu Server installation medium so that the first time a system is set up using it, a kiosk
ready to deploy will be created.

The total size of the files that KioskForge install on the Ubuntu Server kiosk machine is currently less than 1 MB in total.

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

**NOTE:** Intel Compute Sticks freeze randomly with Ubuntu Server 24.04.x so they are *not* supported at all.

**NOTE:** The PC target is currently likely broken because I don't have a spare PC to test it on.  WIP.

**NOTE:** Prelimary support for Raspberry Pi 5 has been added, but it is not mature yet.  Audio has not been tested yet on Pi5.


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

### Starting KioskForge with a given kiosk file
You can easily open any `.kiosk` file in KioskForge simply by double-clicking the file (this requires that you have installed
KioskForge using the Windows installer).  This is the recommended way of opening a `.kiosk` file in KioskForge.

Alternatively, you can supply the path of the kiosk file on the command-line if starting KioskForge from a console window.

### Creating a new kiosk file from scratch
To create a new, blank `.kiosk` file, use the `New` right-click context menu in Windows Explorer.

### Configuring the Kiosk
To configure your kiosk, edit it using your favorite editor such as `Notepad`.  You can right-click the file and select `Edit`.

**NOTE:** You *cannot* use Microsoft Word or similar word processing software to edit the `.kiosk` file.

**HINT:** Please check *every* option in the `.kiosk` file before you try to forge a kiosk.  There are only about 25 options, all
fairly decently documented in the `.kiosk` file itself.  If you make an error, you'll have to re-forge a newly prepared Linux
installation medium once again!  So try to complete editing the kiosk file before you try to forge your first kiosk.

### Configuring the Linux Installation Medium
When you have started KioskForge by double-clicking the kiosk file, you must make sure that the Linux installation medium, made
with [Raspberry Pi Imager](https://www.raspberrypi.com/software/), is inserted into a USB port in your Windows computer, then you
simply double-click the kiosk file and KioskForge will quickly modify the installation medium to prepare it for making a new kiosk.

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

After this, you can launch KioskForge directly from Windows Explorer, by double-clicking a `.kiosk` file.

**NOTE:** There's currently no point in starting KioskForge from the Windows Start menu: It will fail because it needs the name of
a kiosk file to open.  You can, however, run it from a console if you are so inclined, insofar you pass the name of a kiosk file.


### Linux
**NOTE:** `KioskForge.py` currently *cannot* be run on Linux.  This is a planned feature and is expected to be fixed sometime.

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


## Limitations
KioskForge is currently a console command, but a GUI version is in the works and will probably be released within a few months
(sometime during Summer 2025).

KioskForge currently uses the X11 windowing system when running Chromium (the open source version of Google Chrome).  This will be
changed eventually so that KioskForge uses the more modern and slightly better supported Wayland windowing system in the kiosk.

KioskForge currently only supports DHCP-assigned LAN IP adresses so there's no way of specifying a fixed LAN IP address.  This
basically means you need to talk to your network administrator about getting a static DHCP lease for the kiosk machine itself,
which is a very good idea, anyway, as you don't want to work blindly if the kiosk suddenly misbehaves and needs fixing.


## Usage
KioskForge is a simple application that modifies a Linux installation medium so that it creates a kiosk from a so-called "kiosk
file".  A kiosk file is a simple configuration file that is made up of lines that can either be a comment (starts with `#`) or
a field assignment of the form `name=value`.

The only way to use KioskForge is to double-click a kiosk file (which ends in `.kiosk` and has the Windows Explorer file type
`KioskForge Kiosk`).  A kiosk file defines a kiosk and what how the kiosk is to be forged.

If there are one or more errors in the kiosk file, KioskForge will report them, wait for you to hit enter, and then exit.

If there are no errors in the kiosk file, KioskForge will look through all drives in the system to see if it can recognize a valid
Linux installation medium.  If it finds one, it will update the medium so that it will create a kiosk the first time that the
kiosk machine is booted off that medium.

**NOTE:** The kiosk MUST be connected to the internet while it is being forged!  After this, it can stay offline forever.

It is always best that the kiosk is permanently on the internet so that it can update Chromium, etc.  But it can work without.

The procedure is as follows:

1. Create an `Ubuntu Server 24.04.2` installation media for Raspberry Pi 4B (ARM64) using a USB key or a MicroSD card:
	1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).  Make sure you **don't** use *OS Customisations*.
	2. [Raspberry Pi Imager Guide](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).
	3. You'll find `Ubuntu Server 24.04.2` in the category `Other general-purpose OS`.  Always use 64-bit editions only.
       If you do not see `Ubuntu` in the `Other general-purpose OS` list, Raspberry Pi Imager is to blame.  Just wait a few
       minutes and try again.  Raspberry Pi Imager sometimes bugs out and refuses to display the entire list of Linux images.
	4. Be aware that newer Ubuntu Server server versions may pop up in the list when released so be careful what you select!
	5. Also, be sure to **not** select `Ubuntu Desktop` (KioskForge will detect this, though, and report an error).
	6. When done, leave the installation media in your computer until KioskForge tells you to safely remove it (or dismount it).
	7. Please notice that we recommend MicroSD cards over USB keys as the latter have a tendency to get very hot and unreliable.
2. Right-click on empty space on your Desktop, or the folder where you want to place the `.kiosk` file, and select `New`, then
   `KioskForge Kiosk`.  Please assign the new kiosk file a meaningful name so that you can easily see what purpose of the kiosk is.
3. Edit the new kiosk by opening it in `Notepad` (right-click on the kiosk icon and select `Edit`).  Save it using `Ctrl-S`.
4. Double-clock on the new kiosk file to open it in KioskForge.
5. KioskForge will present a summary of the kiosk file and ask you to hit `ENTER` to continue.  To abort, hit `Ctrl-C`.
6. KioskForge will now prepare the kiosk install image to forge the new kiosk.
7. KioskForge then asks you to press `ENTER` to exit KioskForge.  Press `ENTER` to continue and exit KioskForge.
8. Use Windows' *Safe Removal* feature or `Eject` from Windows Explorer to safely disconnect the installation media.
9. Move the installation media to the powered off kiosk machine.
10. Power on the kiosk machine.
11. Wait 10 to 30 minutes (this depends a lot on the I/O speed of the installation media and on your internet speed) until the
    kiosk has been forged, which is shown by the kiosk rebooting into kiosk mode.
12. Try out and test the new kiosk.  If you find issues, please either modify your `.kiosk` file or report them to us.
13. You can either attach a keyboard or SSH into the box (the LAN IP address is shown when the kiosk boots) to power it off.
14. Mount the Raspberry Pi in whatever enclosure you are using for your kiosk.  This is typically custom made by carpenters.

After that, the kiosk should *theoretically* run nicely and reliably for years and years.  However, you may want to log into it,
using SSH, once in a while to verify that logs are being rotated, that there is sufficient disk space available, and so on.  The
kiosk is set up to automatically reclaim as much space as it can, whenever the daily maintenance script runs.

If you SSH into the kiosk or use a local keyboard to log in, you can use the `kiosklog` command to view `syslog` entries related
to KioskForge.  If you only want to view *errors*, append the option `-p 3`: `kiosklog -p 3 | more`.


## Bugs and Ideas
Please report bugs and ideas on [KioskForge Issues at GitHub](https://github.com/vhmdk/KioskForge/issues) or by mail to
[Mikael Egevig](mailto:me@vhm.dk).  The former is the preferred method, but use whichever method suits you best.

When you report a bug, please log into the kiosk and run this command to create a log file:

```bash
    kiosklog > ~/kiosk.log
```

Then please include the two files `~/kiosk.log` and `~/.xsession-errors` (if it exists) in your bug report.  These files will
likely provide invaluable information about the issue, which makes it so much easier to debug and fix the issue.


## Contributing
This chapter presents some basic information necessary to contribute to KioskForge.


### Philosophy
KioskForge is designed and implemented using three primary requirements:

1. The script must be completely reliable.  This is why we use Python and its exception handling instead of, say, a Bash script.
2. The script must be as user-friendly as possible.  Most people who need a kiosk aren't particularly tech savvy.
3. The script must be portable to all major platforms, Windows and Linux in particular.  This is why we will use Tkinter for Python.

It does not matter the least if the script is ugly, a bit clumsy, somewhat suboptimal in terms of execution speed or algorithms.
People probably only use the script occasionally, albeit we want to automate it as much as possible in the future.


### Developing
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
