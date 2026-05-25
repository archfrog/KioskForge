# KioskForge Manual
KioskForge is a free, open-source software (FOSS) program that automates and simplifies the setup of a new kiosk machine.

## Synopsis
KioskForge is intended for somewhat non-technical users to set up a kiosk machine for browsing a given website, or for more advanced users to set up a kiosk that runs a CLI or GUI app of the user's choice.

KioskForge takes two inputs:

1. An Ubuntu Server 24.04.x/26.04 installation medium created using [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. A "kiosk file", which is a configuration file that specifies the values of all the settings that KioskForge supports.

The first, the Ubuntu Server installation medium, is automatically located by KioskForge if it is present on the host system.  The kiosk file name can be passed as an argument to KioskForge or double-clicked to open KioskForge.

KioskForge then modifies the Ubuntu Server installation medium so that, the first time a system boots from it, a kiosk is created ready for deployment.

The total size of the files KioskForge adds to the kiosk machine is currently less than 1 megabyte.

## Features
KioskForge currently supports these things:

* Ubuntu Server 24.04.x LTS or Ubuntu Server 26.04.x LTS.
* 64-bit Raspberry Pi 4B and Raspberry Pi 5 (with 2+ GB RAM) ARM64 (aarch64).
* Creating a kiosk that allows browsing a website using Chromium in kiosk mode (without a URL address bar).
* Creating a kiosk that runs a command-line (CLI) application programmed by the user.
* Touch screen input, insofar as the particular touch screen is supported out of the box by the target operating system.
* Ethernet and/or Wi-Fi networking.
* Configuring basic Linux things such as hostname, keyboard layout, locale, time zone, etc.
* Rotating normal and touch-panel displays.

Please notice that the kiosk needs either internet access or a real-time clock (RTC) for its automatic, daily maintenance to work reliably.  If the kiosk does not have internet access, it should be a Pi 5 with an RTC backup battery.  If not, the kiosk may reboot at seemingly random times because the system clock is wrong.  At this time, we cannot recommend using Raspberry Pi 4B without internet access.  It is best that the kiosk has internet access all the time or at a fixed, daily interval.

## Security
Ideally, you use a tool like [KeePassXC](https://keepassxc.org/) to manage the passwords to your kiosks and make sure that each kiosk has its own password so that getting access to one kiosk does not automatically grant access to every kiosk that you operate.

To avoid problems with hackers and hostile visitors, you should **always** make sure that all kiosks run on their own, private subnet (`192.168.x.*`).  This will become much more important in the future, so heed our advice and implement this already now.

## Overview
This chapter aims to give you a basic understanding of how to use KioskForge.

### Audience
KioskForge is intended to be used by all sorts of users, for which reason it strives to require as little technical knowledge as possible and to automate the creation (the forging) of the kiosk as much as possible.

### Process
KioskForge works by modifying a supported Ubuntu Server installation medium according to the settings the user has given in a
`.kiosk` file (an INI-style configuration file).  The format of the `.kiosk` file is very simple and does not require significant
technical knowledge.  After the installation medium has been configured by KioskForge, it is inserted into the target machine,
which is then powered on, and the actual "forge process" takes place.  Over less than thirty minutes, the forge process configures,
updates, modifies, and prepares the target kiosk machine to work as a kiosk machine (on a permanent basis, not requiring any
maintenance whatsoever after the initial deployment).

### Starting KioskForge with a given kiosk file
You can easily open any `.kiosk` file in KioskForge simply by double-clicking the file if you have installed KioskForge using the
Windows installer.  This is the recommended way of loading a `.kiosk` file in KioskForge on Windows systems.

Alternatively, you can supply the path of the kiosk file on the command line if starting `KioskForge.exe` from a console window.

### Creating a new kiosk file from scratch
To create a new, blank `.kiosk` file, use the `New` right-click context menu in Windows Explorer.

### Configuring the Kiosk
To configure your kiosk, use your favorite editor, such as Notepad.  You can right-click the file and select `Edit`.

**NOTE:** You *cannot* use Microsoft Word or similar word processing software to edit the `.kiosk` file.

**HINT:** Please check *every* option in the `.kiosk` file before you try to forge a kiosk.  There are only about 25 options, all
fairly decently documented in the `.kiosk` file itself.  If you make an error, you'll have to re-forge a newly prepared kiosk
installation medium once again!  So, review the entire kiosk file before you try to forge your first kiosk.

### Configuring the Kiosk Installation Medium
When you have started KioskForge by double-clicking the kiosk file, you must make sure that the kiosk installation medium is made with [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or [Rufus](https://rufus.ie), is inserted into a USB port in your Windows computer, then you simply double-click the kiosk file, and KioskForge will quickly modify the installation medium to prepare it for making a new kiosk.

Once KioskForge has updated the kiosk installation medium, it will ask you to safely remove the medium and insert it into the kiosk machine.  Just follow the instructions and then power on the kiosk to begin the actual process of forging the desired kiosk.

## Installation
This chapter explains the current method of installing KioskForge for the first time on a new Windows PC.

Please note that we recommend a specific Python version to ensure the best, most efficient experience for you.  You are free to try with other versions of these tools, but we cannot guarantee that they will work.

### Windows
Download the most recent version of `KioskForge-x.yy-Setup.exe` from [KioskForge.org](https://kioskforge.org/downloads/).

Navigate to the `Downloads` folder and double-click on the `KioskForge-x.yy-Setup.exe` file.  Follow the prompts to install.  If you have installed KioskForge before, you should probably skim the `CHANGES.html` file and see if there are any important changes.

After this, you can launch KioskForge directly from Windows Explorer by double-clicking a `.kiosk` file.

**NOTE:** There's currently no point in starting KioskForge from the Windows Start menu: It will fail because it needs the name of a kiosk file to open.  You can, however, run it from a console if you are so inclined, insofar as you pass the name of a kiosk file.  If you run it from the command line, you need to add the `apply` keyword before the actual path of the `.kiosk` file to use.

### Linux
Install a recent version of the [Python v3.13+ programming language](https://python.org).  On most Linuxes, this can be done with
the system-wide package manager such as `apt`, `dnf`, `pacman`, and so on.  Make sure to install Python v3.13+.  Earlier versions
should work fine, especially v3.10+, but I don't test against these and don't use older versions of Python during development.

Then fetch KioskForge from GitHub using the following command:

```bash
git clone https://github.com/archfrog/KioskForge
```

#### Activating the Python Virtual Environment
Before you can use the KioskForge scripts, you need to activate the Python virtual environment:

```bash
.venv/Scripts/activate
```

If you don't use the Bash shell, you need to check the `.venv/Scripts` folder for a compatible `activate` script for your shell.

This sets up the runtime environment needed to execute KioskForge.

#### Execute Permissions
You need to make sure that the script `KioskForge.py` has execute permissions (use `chmod u+x KioskForge.py` to set them), then you can invoke it using `./KioskForge.py`.

#### Specifying the Installation Medium Mount Point
`KioskForge.py` does not yet auto-detect the Ubuntu Server installation medium so you need to specify a mount point to the `KioskForge.py prepare` command.  If the `.kiosk` file is named `Test.kiosk` and the mount point for the Ubuntu Server installation medium is `/mnt/sdcard`, you need to execute this command:

```bash
./KioskForge.py prepare Test.kiosk /mnt/sdcard
```

### Macintosh
I don't have access to a Mac computer, so no development or testing is done on this platform.  Feel free to port the script and submit a pull request.  Please make sure that the result generates a valid, reliable kiosk before submitting the pull request.

## Limitations
KioskForge is currently a console command, but a GUI version is in the works and will be released eventually.

KioskForge currently uses the X11 windowing system when running Chromium (the open source version of Google Chrome).  This will be changed eventually so that KioskForge uses the more modern, slightly better-supported Wayland windowing system in the kiosk.

KioskForge currently only supports DHCP-assigned LAN IP addresses, so there's no way of specifying a fixed LAN IP address.  This basically means you need to talk to your network administrator about getting a static DHCP lease for the kiosk machine itself, which is a very good idea, anyway, as you don't want to work blindly if the kiosk suddenly misbehaves and needs fixing.

## Usage
KioskForge is a simple application that modifies an Ubuntu Server 24.04.x/26.04.x installation medium so that it creates a kiosk from a so-called "kiosk file" when booted the first time.  A kiosk file is a simple configuration file composed of lines that can be blank, a comment (starting with `#`), or a field assignment of the form `name=value`.  Each kiosk file defines a kiosk and its forging.

The only GUI way to use KioskForge is to double-click a kiosk file (which ends in `.kiosk` and has the Windows Explorer file type
`KioskForge Kiosk`).

If there is one or more errors in the kiosk file, KioskForge will report them, wait for you to hit enter, and then exit.

If there are no errors in the kiosk file, KioskForge will look through all drives in the system to see if it can recognize a valid
Linux installation medium.  If it finds one, it will ask you to review the settings and then update the medium so that it will
create a kiosk the first time that the kiosk machine is booted off that medium.

**NOTE:** The kiosk MUST be connected to the internet while it is being forged!  After this, it can stay offline forever.  You can disable updates by setting the `update_time` option blank (`update_time=`).

**NOTE:** Web-type kiosks should be permanently online that they can update Chromium and other system software.  But it can work without, and there are good reasons for keeping it offline: Updates MAY break the system!  This happens occasionally and is beyond our control.

**NOTE:** We generally recommend MicroSD cards over USB keys as the latter have a tendency to get very hot and unreliable.

The procedure is as follows:

1. Create an `Ubuntu Server 24.04.x/26.04.x` installation media for Raspberry Pi 4B (ARM64) using a USB key or a MicroSD card:
     1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
     2. This link points to a pretty good guide on how to use [Raspberry Pi Imager](https://www.raspberrypi.com/documentation/computers/getting-started.html#raspberry-pi-imager).
     3. You'll find `Ubuntu Server 24.04.x/26.04.x` in the subcategory `Ubuntu` of the category `Other general-purpose OS`. If you do not see `Ubuntu` in the `Other general-purpose OS` list, Raspberry Pi Imager is to blame.  Just wait a few minutes and try again.  Raspberry Pi Imager sometimes bugs out and refuses to display the list of supported Linux images.
     4. Be aware that newer Ubuntu Server versions may pop up in the list when released, so be careful what you select!
     5. Also, be sure to **not** select `Ubuntu Desktop` (KioskForge will detect this, though, and report an error).
     6. Make sure you click `SKIP CUSTOMISATION` before you get to the screen with `WRITE`.  Any and all OS customizations that you may want to make **must** be made in the `.kiosk` file, not in RPI Imager.
     7. When Raspberry Pi Imager is done writing Ubuntu Server, exit Raspberry Pi Imager.
     8. If Raspberry Pi Imager ejects the medium so KioskForge can't find it, simply unplug it and insert it again.
2. Right-click on empty space on your Desktop, or the folder where you want to place the `.kiosk` file, and select `New`, then `KioskForge Kiosk`.  Please assign the new kiosk file a meaningful name so you can easily see its purpose.
3. Edit the new kiosk by opening it in `Notepad` (right-click on the kiosk icon and select `Edit`).  Save it using `Ctrl-S`.
4. Double-click on the new kiosk file to open it in KioskForge.
5. KioskForge will present a summary of the kiosk file and ask you to hit `ENTER` to continue.  To abort, hit `Ctrl-C`.
6. KioskForge will now prepare the kiosk install image to forge the new kiosk.
7. KioskForge then asks you to press `ENTER` to exit KioskForge.  Press `ENTER` to continue and exit KioskForge.
8. Use Windows' *Safe Removal* feature or `Eject` from Windows Explorer to safely disconnect the installation media.
9. Move the installation media to the powered-off kiosk machine.
10. Power on the kiosk machine.
11. Wait 5 to 30 minutes (this depends on the Raspberry Pi model, the I/O speed of the installation media, and your internet speed) until the kiosk has been forged, which is shown by the kiosk rebooting into kiosk mode.
12. Try out and test the new kiosk.  If you find issues, please either modify your `.kiosk` file or report bugs to us.
13. You can SSH into the box (the LAN IP address is shown when the kiosk boots) to power it off using the private key associated with the public key added in the `.kiosk` file.
14. Mount the Raspberry Pi in whatever enclosure you are using for your kiosk, which is typically custom-made by carpenters.

After that, the kiosk should *theoretically* run nicely and reliably for years and years.  However, you may want to log in to it using SSH once in a while to verify that logs are being rotated, that there is sufficient disk space available, and so on.  The kiosk is set up to automatically reclaim as much space as it can whenever the daily maintenance script runs.

If you SSH into the kiosk or use a local keyboard to log in, you can use the `kiosklog` command to view `syslog` entries related
to KioskForge.

## Bugs and Ideas
Please report bugs and ideas on [KioskForge Issues at GitHub](https://github.com/archfrog/KioskForge/issues) or by mail to the team at [KioskForge team](mailto:contact@kioskforge.org).  The former is preferred, but use whichever method suits you best.

When you report a bug, please first log into the kiosk and run the command shown below to create a ZIP file containing the
*redacted* kiosk files:

```bash
KioskForge/KioskReport.py
```

This will create the archive `kiosklogs.zip` which you can then download from the kiosk using `scp` or [WinSCP](https://winscp.net).  Please attach the `kiosklogs.zip` file to your bug report, whether by email or via GitHub.

All sensitive information (comment, user password, Wi-Fi name, Wi-Fi password, and the public SSH key) has been redacted out of the `.kiosk` file before inclusion in the ZIP archive.  You can search the unzipped `Kiosk.kiosk` file for the string `REDACTED` to verify this.

**NOTE:** If you are uncomfortable submitting the ZIP archive to GitHub, you are more than welcome to send it attached to an email.
