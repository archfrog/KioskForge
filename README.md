# KioskForge Master Readme File
KioskForge is a portable tool to automate and simplify the process of setting up a new kiosk machine for browsing a website.  It is
intended to be used by somewhat non-technical users to set up a kiosk machine for browsing a given website.

KioskForge currently supports these things:

* Ubuntu Server 24.04.2 on Raspberry Pi 4/4B (2+ GB RAM) ARM64 (aarch64) and PC x64/AMD64 machines.
* Creating a kiosk that allows browsing a website using Chromium in kiosk mode (without an URL address bar).
* Touch screen input insofar the particular touch screen is supported out of the box by the target operating system.
* Ethernet and/or Wi-Fi networking.

**NOTE**: Intel Compute Sticks freeze randomly with Ubuntu Server 24.04.x so they are *not* supported at all.
**NOTE**: The PC target is currently partially broken because I don't have a spare PC to test it on.  WIP.


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

#### Download and Install the Python Programming Language
On Windows, you need to download and install Python first:

Open this link: [Python.org](https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe) and save the `python-...exe` file to
your `Downloads` folder.  Then double-click the `python-...exe` file and let it install using its default settings.

### Download and Unpack the KioskForge Program
Download and open the current `KioskForge.zip` archive from the [KioskForge website](https://kioskforge.org/KioskForge.zip).

Navigate to the `Downloads` folder and double-click on the `KioskForge.zip` file.  Mark all files in the archive by right-clicking
on the marked files and selecting `Copy`, or by hitting `Ctrl-A` on your keyboard.

Then navigate to your desktop and create a folder named `KioskForge`.  Open this folder by double-clicking it and then right-click
on the blank screen area in the right side of Windows Explorer and select `Paste`, or hit `Ctrl-V` on your keyboard.

After this, you can launch KioskForge directly from Windows Explorer, by double-clicking it, or directly from the command-line by
invoking the `KioskForge.py` command.


### Linux
**NOTE:** `KioskForge.py` currently **cannot** be run on Linux.  This is work in progress and is expected to be solved pretty soon.

Install a recent version of the [Python v3.12+ programming language](https://python.org).  On most Linuxes, this can be done with
the system-wide package manager such as `apt`, `dnf`, `pacman`, and so on.  Make sure to install Python v3.12+.

You need to make sure that the script, `KioskForge.py`, has execute permissions (use `chmod u+x KioskForge.py` to accomplish that),
then you can invoke it using `./KioskForge.py`.


## Macintosh
I don't have access to a Mac computer, so no development or testing is done on this platform.  Feel free to port the script and
submit a pull request.  Please make sure that the result generates a valid, reliable kiosk before submitting the pull request.


## Configuration
Customization of the target kiosk machine can be done using `KioskForge.py` or using an editor to create an INI-style file:

| Name               | Option name     | Type    | Description                                                                   |
| ----------------   | --------------- | ------  | ----------------------------------------------------------------------------- |
| Comment            | `comment`       | string  | A string describing the kiosk and its purpose (for your records).             |
| Device type        | `device`        | string  | One of `pi4`, `pi4b`, or `pc`.  NOTE: `pc` is currently broken!               |
| Kiosk type         | `type`          | string  | One of `cli`, `x11`, or `web`.  Only `web` is supported currently.            |
| Command            | `command`       | string  | An URL to open (type: web) or a command to run (type: cli/x11).               |
| Host name          | `hostname`      | string  | The unqualified domain name of the kiosk machine.                             |
| Time zone          | `timezone`      | string  | The Linux-compatible time zone name (`CET` or `Europe/Copenhagen`).           |
| Locale             | `locale`        | string  | The system locale (`da_DK.UTF-8` or a similar value).                         |
| Keyboard layout    | `keyboard`      | string  | The name of the kiosk's keyboard layout (`dk`, `en`, etc.).                   |
| Website URL        | `website`       | string  | The full, canonical URL of the website that is opened in the web browser.     |
| Audio volume       | `audio`         | integer | The logarithmic audio volume from 0 through 100 (0 disables audio fully).     |
| Mouse cursor       | `mouse`         | boolean | Whether or not the mouse cursor is visible, should normally be disabled.      |
| Idle timeout       | `idle_timeout`  | seconds | Seconds of idle time before restarting the web browser (0 = never).           |
| User login name    | `user_name`     | string  | The Linux user name of the user owning the web browser process, etc.          |
| User password      | `user_code`     | string  | The raw or `bcrypt`-encoded password of the user.                             |
| Public SSH key     | `ssh_key`       | string  | A public SSH key as generated by `ssh-keygen` for using SSH with the kiosk.   |
| Wi-Fi network      | `wifi_name`     | string  | The name of the Wi-Fi network to connect to (blank = disable Wi-Fi).          |
| Wi-Fi password     | `wifi_code`     | string  | The password, if any, to the Wi-Fi network (blank = don't use a password).    |
| Wi-Fi boost        | `wifi_boost`    | boolean | If enabled, the Wi-Fi card's power saving feature will be disabled.           |
| Snap update time   | `snap_time`     | period  | A period of time, from start to end, when the Snap update process may run.    |
| Swap file size     | `swap_size`     | integer | The size of the swap file in gigabytes (0 = disable swap, not recommended).   |
| APT update time    | `upgrade_time`  | time    | The hour and minute when to perform a global upgrade of packages.             |
| Shutdown time      | `poweroff_time` | time    | The hour and minute when to automatically shut down the kiosk machine.        |
| Vacuum time        | `vacuum_time`   | time    | The hour and minute when to automatically compact and clean log files.        |
| Vacuum retention   | `vacuum_days`   | integer | The number of days of retention of system logs.                               |
| Screen orientation | `orientation`   | integer | 0 = default, 1 = rotate left, 2 = flip upside-down, 3 = rotate right.         |
| User folder        | `user_folder`   | string  | A folder to copy to `~` on the kiosk.  Useful for local websites and scripts. |
| User packages      | `user_packages` | string  | A space-separated list of packages to install while forging the kiosk.        |

KioskForge currently only supports DHCP-assigned LAN IP adresses so there's no way of specifying a fixed LAN IP address.  This
basically means you need to talk to your network administrator about getting a static DHCP lease for the kiosk machine itself.

**NOTE**:
Currently, the interactive TUI editor *cannot* handle blank strings, so you may need to edit the configuration file manually using
your favorite editor such as `Notepad` (you cannot use a word processor such as Word to edit KioskForge configuration files!).


## Usage
KioskForge is a simple application that allows you to create, load, edit, and save a *kiosk configuration* - an INI-style file
that defines the kiosk and what it is supposed to do.  After that, you can choose to *update* an installation media to apply the
configuration during installation.

**NOTE**: The kiosk MUST be connected to the internet while it is being forged!  After this, it can safely stay offline forever.

After that, it doesn't have to although it is strongly recommended that it is permanently on the internet so that it can update
Chromium, etc.

As of now, the procedure is as follows:

1. Create an appropriate `Ubuntu Server 24.04.2` installation media (a USB key or a MicroSD card) using
   [Raspberry Pi Imager](https://www.raspberrypi.com/software/).  Make sure you **don't** use *OS Customisations*.
   When done, leave the installation media in your computer until KioskForge tells you to dismount it or safely remove it.
   Also, be sure to **not** select `Ubuntu Desktop` as this won't work (KioskForge will detect this, though, and report an error).
2. Launch KioskForge as described below.
3. Create a new configuration using menu item `1` or load an existing configuration using menu item `2`.
4. Edit the configuration to ensure that the configuration is correct using menu item `3` or use an external editor.  See the
   chapter `Configuration` above for detailed information each of the options that KioskForge supports.
5. Save the changed configuration, if it has been modified, using menu item `4`.
6. Select the `Update Raspberry Pi Imager prepared installation media` (`5`) to have KioskForge modify the install media so that
   it installs and launches an actual Linux kiosk with the Chromium web browser pointing to whatever URL you have configured.
7. Press `ENTER` to exit KioskForge.
8. Use Windows' *Safe Removal* feature or `Eject` from Windows Explorer to safely unmount the installation media.
9. Move the installation media to the powered off Raspberry Pi 4+.
10. Power on the Raspberry Pi 4+.
11. Wait between 15 and 30 minutes (this depends a lot on the I/O speed of the installation media) until the kiosk has been forged,
    which is shown by the kiosk rebooting into kiosk mode showing the requested URL.
12. Try out and test the new kiosk.  If you find issues, please report them (see the section `Bugs` below).
13. You can either attach a keyboard or SSH into the box (if you know its LAN IP address) to power it off.
14. Mount the Raspberry Pi in whatever enclosure you are using for your kiosk.

After that, the kiosk should *theoretically* run nicely and reliably for years and years.  However, you may want to log into it,
using SSH, once in a while to verify that logs are being rotated, that there is sufficient disk space available, and so on.

If you SSH into the kiosk or use a local keyboard to log in, you can use the `kiosklog` command to view `syslog` entries related
to KioskForge.  If you only want to view *errors*, append the option `-p 3`: `kiosklog -p 3 | more`.


## Development
To develop on KioskForge, install a recent Python (v3.12+) and MyPy, and then set up these environment variables:

| Environment Variable      | Value | Explanation                                                                             |
| ------------------------- | ----- | --------------------------------------------------------------------------------------- |
| `PYTHONDONTWRITEBYTECODE` | `1`   | Disable the generation of needless Python byte-code files everywhere.                   |
| `RAMDISK` 				| path  | A temporary folder, preferably on a ram disk.  This is used for caching MyPy data, etc. |

Run the script `test.bat` (Windows only) or `test.sh` (Linux only) to make MyPy test the code and report any errors.

*Currently, the MyPy test is a bit broken because the script uses both Windows-only and Linux-only features, something which
MyPy isn't all that happy about.  This will be fixed in not too long by splitting the single script into its logical parts.*

Development currently takes place on a Windows 11 Pro desktop computer, but I'll setup a Linux development environment soon.


## Bugs and Ideas
Please report bugs and ideas on [KioskForge Issues at GitHub](https://github.com/vhmdk/KioskForge/issues) or by mail to
[Mikael Egevig](mailto:me@vhm.dk).  The former is the preferred method, but use whichever suits you best.

When you report a bug, please log into the kiosk and run this command to create a log file:

```bash
kiosklog > ~/kiosk.log
```

Then please include the two files `~/.xsession-errors` and `~/kiosk.log` in your bug report.  These files will likely provide
invaluable information about the issue, which makes it so much easier to debug and fix the issue.

