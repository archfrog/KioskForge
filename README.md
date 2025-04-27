# KioskForge Readme File
KioskForge is a portable tool to automate and simplify the process of setting up a new kiosk machine for browsing a website.  It is
intended to be used by somewhat non-technical users to set up a kiosk machine for browsing a given website.

KioskForge currently supports these things:

* Ubuntu Server 24.04.2 on Raspberry Pi 4B/5 (2+ GB RAM) ARM64 (aarch64) and PC x64/AMD64 machines (4+ GB RAM).
* Creating a kiosk that allows browsing a website using Chromium in kiosk mode (without an URL address bar).
* Touch screen input insofar the particular touch screen is supported out of the box by the target operating system.
* Ethernet and/or Wi-Fi networking.

**NOTE**: Intel Compute Sticks freeze randomly with Ubuntu Server 24.04.x so they are *not* supported at all.

**NOTE**: The PC target is currently likely broken because I don't have a spare PC to test it on.  WIP.

**NOTE**: Prelimary support for Raspberry Pi 5 has been added, but it is not mature yet.  Audio does not yet work on Pi5.


## Philosophy
KioskForge is designed and implemented using three primary requirements:

1. The script must be completely reliable.  This is why we use Python and its exception handling instead of, say, a Bash script.
2. The script must be as user-friendly as possible.  Most people who need a kiosk aren't particularly tech savvy.
3. The script must be portable to all major platforms, Windows and Linux in particular.  This is why we use Tkinter for Python.

It does not matter the least if the script is ugly, a bit clumsy, somewhat suboptimal in terms of execution speed or algorithms.
People probably only use the script occasionally, albeit we want to automate it as much as possible in the future.


## Installation
This chapter explains the current method of installing KioskForge on a new PC without any KioskForge installation.

Please notice that we recommend specific versions of Python and Raspberry Pi Imager as we want to ensure the best, most efficient
experience for you.  You are free to try with other versions of these tools, but we cannot guarantee that they work.

### Windows
Download the most recent version of `KioskForge-x.yy-Setup.exe` from [KioskForge.org](https://kioskforge.org/downloads/).

Navigate to the `Downloads` folder and double-click on the `KioskForge-x.yy-Setup.exe` file.  Follow the prompts to install.

After this, you can launch KioskForge directly from Windows Explorer, by double-clicking a `.kiosk` file, or from the Start menu
by clicking on the `KioskForge` command.


### Linux
**NOTE:** `KioskForge` currently *cannot* be run on Linux.  This is a planned feature and is expected to be fixed soon.

Install a recent version of the [Python v3.13+ programming language](https://python.org).  On most Linuxes, this can be done with
the system-wide package manager such as `apt`, `dnf`, `pacman`, and so on.  Make sure to install Python v3.13+.  Earlier versions
should work fine, especially v3.10+, but I don't test against these and don't use older versions of Python during development.

You need to make sure that the script, `KioskForge.py`, has execute permissions (use `chmod u+x KioskForge.py` to accomplish that),
then you can invoke it using `./KioskForge.py`.


### Macintosh
I don't have access to a Mac computer, so no development or testing is done on this platform.  Feel free to port the script and
submit a pull request.  Please make sure that the result generates a valid, reliable kiosk before submitting the pull request.


## Configuration
Customization of the target kiosk machine can be done using `KioskForge.py` or using an editor to create an INI-style file:

| Name               | Option name       | Type    | Description                                                                 |
| ------------------ | ----------------- | ------  | --------------------------------------------------------------------------- |
| Comment            | `comment`         | string  | A string describing the kiosk and its purpose (for your records).           |
| Device type        | `device`          | string  | One of `pi4b`, or `pc`.  NOTE: `pc` is currently broken!                    |
| Kiosk type         | `type`            | string  | One of `cli`, `x11`, or `web`.  Only `cli` and `web` are supported now.     |
| Command            | `command`         | string  | An URL to open (type: `web`) or a command to run (type: `cli`/`x11`).       |
| Host name          | `hostname`        | string  | The unqualified domain name of the kiosk machine.                           |
| Time zone          | `timezone`        | string  | The Linux-compatible time zone name (`CET` or `Europe/Copenhagen`).         |
| Locale             | `locale`          | string  | The system locale (`da_DK.UTF-8`, etc. - always ends in `.UTF-8`).          |
| Keyboard layout    | `keyboard`        | string  | The name of the kiosk's keyboard layout (`dk`, `en`, etc.).                 |
| Sound card         | `sound_card`      | string  | `none`, Pi4B: `jack`, `hdmi1`, or `hdmi2`.  PC: Not yet supported.          |
| Sound volume       | `sound_level`     | integer | The logarithmic audio volume from 0 through 100 (0 disables audio fully).   |
| Mouse cursor       | `mouse`           | boolean | Whether or not the mouse cursor is visible, should normally be disabled.    |
| User login name    | `user_name`       | string  | The Linux user name of the user owning the web browser process, etc.        |
| User password      | `user_code`       | string  | The raw or `bcrypt`-encoded password of the user.                           |
| Public SSH key     | `ssh_key`         | string  | A public SSH key as generated by `ssh-keygen` for using SSH with the kiosk. |
| Wi-Fi network      | `wifi_name`       | string  | The name of the Wi-Fi network to connect to (blank = disable Wi-Fi).        |
| Wi-Fi password     | `wifi_code`       | string  | The password, if any, to the Wi-Fi network (blank = don't use a password).  |
| Wi-Fi boost        | `wifi_boost`      | boolean | If enabled, the Wi-Fi card's power saving feature will be disabled.         |
| Swap file size     | `swap_size`       | integer | The size of the swap file in gigabytes (0 = disable swap, not recommended). |
| System update time | `upgrade_time`    | time    | The hour and minute when to perform a global upgrade of packages and snaps. |
| Shutdown time      | `poweroff_time`   | time    | The hour and minute when to automatically shut down the kiosk machine.      |
| Vacuum retention   | `vacuum_size`     | integer | The number of megabytes data to keep in system logs before deleting it.     |
| Screen rotation    | `screen_rotation` | integer | The screen and touch panel rotation: none, left, flip, or right.            |
| User folder        | `user_folder`     | string  | A folder to copy to `~` on the kiosk.  See `GUIDE.html` for more info.      |
| User packages      | `user_packages`   | string  | A space-separated list of packages to install while forging the kiosk.      |
| CPU overclocking   | `cpu_boost`       | boolean | 0 = disable default overclocking, 1 = enable default overclocking.          |
| Idle timeout       | `idle_timeout`    | seconds | Number of idle seconds before restarting the web browser (0 = never).       |

KioskForge currently only supports DHCP-assigned LAN IP adresses so there's no way of specifying a fixed LAN IP address.  This
basically means you need to talk to your network administrator about getting a static DHCP lease for the kiosk machine itself,
which is a very good idea, anyway, as you don't want to port scan and stuff if the kiosk suddenly misbehaves and needs fixing.

**NOTE**:
Currently, the interactive TUI editor *cannot* handle blank strings, so you may need to edit the configuration file manually using
your favorite editor such as `Notepad` (you cannot use a word processor such as Word to edit KioskForge configuration files!).

The easiest way to create a new `.kiosk` file is to launch KioskForge, select `4`, and save to the desired location and file name.
After this, you can edit the `.kiosk` file using your favorite editor (such as `Notepad`).  After you have modified the `.kiosk`
file, you can simply double-click it in Windows Explorer to open it in KioskForge.  After this, you just hit `5` in KioskForge.


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
	5. When done, leave the installation media in your computer until KioskForge tells you to dismount it or safely remove it.
	6. Also, be sure to **not** select `Ubuntu Desktop` (KioskForge will detect this, though, and report an error).
	7. Please notice that we recommend MicroSD cards over USB keys as the latter have a tendency to get very hot and unreliable.
2. Launch KioskForge as described below.
3. Create a new configuration using menu item `1` or load an existing configuration using menu item `2`.
4. Edit the configuration to ensure that the configuration is correct using menu item `3` or use an external editor (an external
   editor is the recommended way of modifying a `.kiosk` configuration file.  See the chapter `Configuration` above for detailed
   information each of the options that KioskForge supports.
5. Save the changed configuration, if it has been modified, using menu item `4`.
6. Select the `Update Raspberry Pi Imager prepared installation media` (`5`) to have KioskForge modify the install media so that
   it installs and launches an actual Linux kiosk with the Chromium web browser pointing to whatever URL you have configured.
7. Press `ENTER` to exit KioskForge.
8. Use Windows' *Safe Removal* feature or `Eject` from Windows Explorer to safely unmount the installation media.
9. Move the installation media to the powered off Raspberry Pi 4+.
10. Power on the Raspberry Pi 4+.
11. Wait 10 to 30 minutes (this depends a lot on the I/O speed of the installation media) until the kiosk has been forged,
    which is shown by the kiosk rebooting into kiosk mode.
12. Try out and test the new kiosk.  If you find issues, please report them (see the section `Bugs` below).
13. You can either attach a keyboard or SSH into the box (the LAN IP address is shown when the kiosk boots) to power it off.
14. Mount the Raspberry Pi in whatever enclosure you are using for your kiosk.  This is typically custom made by carpenters.

After that, the kiosk should *theoretically* run nicely and reliably for years and years.  However, you may want to log into it,
using SSH, once in a while to verify that logs are being rotated, that there is sufficient disk space available, and so on.

If you SSH into the kiosk or use a local keyboard to log in, you can use the `kiosklog` command to view `syslog` entries related
to KioskForge.  If you only want to view *errors*, append the option `-p 3`: `kiosklog -p 3 | more`.


## Development
To contribute to KioskForge, install these things first:

```batch
rem Install Python v3.13+ from https://python.org.
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

