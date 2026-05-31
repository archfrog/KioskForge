# KioskForge Changes
This document presents the important changes made to each KioskForge release from v0.18 onwards:

## Known Issues
1. The `sound_card` option currently has no effect whatsoever- the code to select the output audio card seems to have "disappeared".  The effect is that the default Pipewire "sink" (audio output device) will be used.  This appears to be "jack" on Pi 4B and "hdmi1" on Pi 5.
2. Some touchscreens need several presses before they react on Ubuntu Server 26.04 so we strongly recommend using 24.04.x for the time being.
3. KioskForge does not currently support using HDMI2 on the Raspberry Pis.  This is a rather low priority issue so let me know if it causes problems for you.
3. KioskForge sorely lacks a GUI.  This is work in progress and will likely be completed in the calendar year of 2026 (using PySide6).
4. Support for remote upgrades of KioskForge and/or the user application via the GUI is work in progress.

## Version 1.04 (2026.05.31)
1. The new `mouse=auto` option has been fixed and tested (I did not have a touchscreen available when I wrote the code).
2. The `sound_card` option now also takes the value `auto`, which means "*Use the jack on a Pi 4B and hdmi1 on a PI 5*".
2. The `device` option has been removed as experience shows that end-users always forget to change it when they switch between a Pi 4B and a Pi 5.  The forge process now detects the kind of system it is running on instead.
3. The `visible` option has been renamed to `managed` to better explain its purpose: To allow KioskForge to manage the kiosk.  Enabling the `managed` option makes the future GUI capable of managing (upgrading, rebooting, powering off, etc.) the kiosk by enabling a tiny broadcast server at boot and by installing an SSH public key for the `root` (Administrator) account so that KioskForge can control the kiosk.
4. The Wi-Fi password is now encoded on the kiosk so that hackers cannot read it in plain text anymore (a security precaution).  This made the crude wipe of the network-data file on the installation medium redundant so that it has been removed.
5. Yet another attempt was made to make Ubuntu Server pick up the "regulatory domain" (Wi-Fi country code) at every boot.  This is not easy, though, because Ubuntu Server for Pi does not provide any working way to set this value.  As far as I can see from posts on the internet, the Linux kernel asks the Access Point (AP) for this information.  Most of the time, this works, but sometimes it doesn't.  There is not anything I can do about it to my knowledge.
6. The kiosk hostname generated if the `hostname` option is empty now includes a separating dash between `kiosk` and the number: `kiosk-34271`.  It is strongly recommended that you specify a hostname, though, as this makes it easy to see the purpose of the kiosk in smarter routers.
7. The kiosk forge process now waits indefinitely until an online network connection is detected so that the end-user has plenty of time to identify and fix the issue.

## Version 1.03 (2026.05.27)
1. Ubuntu Server 26.04.x is now supported by KioskForge.  This is beta as the tests have been limited (everything worked right away in these tests, though).
2. The `mouse` option now supports a third value, `auto`, which causes the kiosk to automatically detect whether the mouse should be enabled.  If a touchscreen is detected, the mouse will be deactivated so that no mouse cursor is displayed.  Otherwise, the mouse will be disabled.  The `auto` setting is the recommended setting for all kiosks going forward.  This solves the problem of developing the kiosk without a touchscreen (mouse=true) and then deploying it to a kiosk with a touchscreen (mouse=false), only to forget the mouse option, which means you have to edit the .kiosk file and forge a new kiosk just because of a tiny mistake.
3. KioskForge now always makes the necessary changes to Ubuntu to support access to the various Raspberry Pi GPIO pins.
4. The documentation was proofread with Grammarly (an AI solution) and many errors were fixed.

## Version 1.02 (2026.05.22)
1. The `shell` user has been retired because it was tedious to log in as the shell user and then use `su kiosk` to access the kiosk.
2. Added support for the Pi 5 H.265 GPU hardware decoder.  The Pi 5 now uses less than 100 percent CPU while displaying an H.265 video at 1920x1080 resolution.  Previously, H.265 movie playback used up all four cores (i.e., 400 percent), and frames were skipped.  This works with the `mpv` video player by adding the options: `--vo=gpu`, `--hwdec=v4l2m2m`, and, optionally, `--profile=fast`.  You need to add the `mpv` package to your `user_packages` setting.
3. The system logs are now vacuumed at every boot and at 05:00, no matter the value of the `update_time` option.
4. All tools now detect more errors in the `.kiosk` file, such as conflicting and meaningless options for the given device.
5. Added support for installing user-supplied fonts using the `user_fonts` option (this is a Boolean setting).
6. Non-ASCII characters (foreign symbols) are now handled correctly when they appear in user file names added with `user_folder`.
7. The ownership and privileges of `cron` job files were corrected so that they're owned by root.
8. Cleaned up the status messages shown during the installation of X11 and Open Box a bit, so they're grouped and indented like the rest.
9. Updated all Python packages to their most recent versions.

## Version 1.01 (2026.05.07)
1. Added support for the X11 kiosk type (`type=x11`) so that the kiosk `command` option launches a pure X11 application.
2. Revised the help text for the `comment` option slightly.
3. Updated all Python packages to their most recent versions.

## Version 1.00 (2026.04.24)
1. Bumped the version to v1.00 as KioskForge is more or less finished.  Not much development is planned from here on, except for stuff needed to support future versions of Ubuntu Server LTS.
2. Updated the documentation a bit; most importantly, it no longer gives a specific version of *Raspberry Pi Imager* to the user.
3. Updated all Python packages and the InnoSetup installer so that KioskForge is fully up to date.

## Version 0.27 (2026.03.16)
1. Made `KioskForge.py prepare` to accept an optional extra argument that specifies the target location.  This way, KioskForge can also be used on Linux and Mac, albeit without automatic detection of the installation medium's location.
2. Greatly improved the help text for the `KioskForge.py` command to now describe all four variants.

## Version 0.26 (2025.11.25)
1. Fixed bad links to the GitHub repository in the documentation.
2. Disabled shipping the built executable to my personal web server, as we now distribute via GitHub's `Releases` feature.

## Version 0.25 (2025.11.18)
1. KioskForge now also supports Ubuntu Server 24.04.3 for Raspberry Pis.
2. A new `visible` option was added that specifies whether the kiosk is discoverable by KioskForge itself.
3. Fixed the broken PipeWire audio subsystem initialization, which was broken by an Ubuntu (kernel?) update.
4. Renamed the `KioskForge` `apply` command to `prepare,` as it really prepares an installation medium for use.
5. The user's password is now hashed (made unreadable) by `KioskForge` on the installation medium for security reasons.
6. The `user_name` kiosk configuration field has been removed as KioskForge now creates two users: `kiosk` and `shell`.  The `kiosk` user is used to launch and run the kiosk.  It is not possible to log in via SSH as that user.  The `shell` user is intended for SSH logins to the kiosk if you need to inspect or modify it after deployment.
7. Upgraded development and embedded Python to v3.13.7.

## Version 0.24 (2025.07.16)
1. Fixed the issue that `KioskForge.py` crashed if an unknown option was encountered (even if it was known in an earlier version).
2. Renamed the `user_options` option to `chromium_autoplay` to make life simpler for everybody.  It enables autoplay in Chromium *without* user interaction, such as clicking the `Play` button.
3. `KioskForge.py`'s `verify` and `upgrade` commands now take a file OR a folder.  If a folder, all `.kiosk` files in it are verified or upgraded (recursively).  The command will stop on the first failed file encountered.
3. Upgraded development and embedded Python to v3.13.5.
4. Updated the documentation to reflect that Tkinter will not be used as the GUI for KioskForge.  Instead, I'll try out [Flet](https://flet.dev), a Flutter-based UI toolkit for Python, as I am not very fond of Tkinter (after battling it).
5. Updated the documentation in general to reflect recent changes, etc.
6. Added two new links to the Windows `Start` menu: `License` and `Read me`.
7. Changed the project to use the [uv](https://github.com/astral-sh/uv) Python package manager instead of `pip`.
8. Changed the project to work in a virtual environment instead of installing dependencies globally.

## Version 0.23 (2025.07.09)
1. The very serious `snap` VFS corruption issue (in long-running kiosks) has now, hopefully, been fixed (I could not recreate the issue despite having both a Pi4B and a Pi5, trying for two days, upgrading and rebooting thousands of times).
2. Fixed an issue with the wrong casing of `wifi_country` values by forcing the value to be written in uppercase only (`us` => `US`).
3. Fixed the issue that `KioskUpdate.py` did *not* update Linux kernels as it should.  Everything should now be upgraded correctly.
4. Fixed the issue that the Common Unix Printing System (`CUPS`) was reinstalled whenever Chromium was upgraded.
5. KioskForge now waits at most 1 minute to allow time to insert the installation medium.
6. The KioskForge Setup program now creates a `Start` menu group that contains links to the various documentation files and to a template kiosk file. You can open it by right-clicking it and selecting `Edit`, then `Save as` when you want to save.
7. There is **intentionally** no link to the program, as you're supposed to run it by double-clicking a .kiosk file or from the command line (using `CMD.EXE`).  A TUI version is being worked on, but this is a fairly low-priority feature.
8. If you have an old link to the `KioskForge.exe` program in your `Start` menu, you can simply uninstall and reinstall KioskForge; this should remove the stale link.  If not, you can delete the link manually (by right-clicking it and selecting `Delete`).
9. The kiosk startup process now shows even less text (by creating `~/.hushlogin`).  Thus, SSHing into the kiosk will show nothing.
10. `README.html` has been renamed to `Manual.html`; this only affects those who actually dug out the file from the app folder.
11. `GUIDE.html` has been renamed to `Guide.html`; this only affects those who actually dug out the file from the app folder.
12. The bug report script `KioskZipper.py` has been renamed to `KioskReport.py`.
13. `KioskReport.py` now generates a list of system units and their statuses in case one or more `systemd` units fail.
14. The `kiosk-disable-wifi-power-saving.sh` is no longer generated by the forge process and has been removed.  The new script `KioskConfig.py` now handles setting up the audio system (if enabled) and disabling Wi-Fi power saving when `wifi_boost` is `True`.  This fixes the issue that Wi-Fi power saving was only disabled during the boot that forged the kiosk, not during subsequent boots.
15. The `KioskSetup.py` script now takes an optional one-based step number, rather than the previous zero-based step number.
16. The kiosk no longer displays its LAN IP address on every boot (only during the first boot while the kiosk is being forged).  This is a small security precaution to prevent kiosk users from discovering the kiosk's LAN IP address.  Kiosks should be on their own LAN.

## Version 0.22 (2025.06.25)
1. The option `user_options` has been added.  This allows the user to specify additional options for Google Chrome.  The most interesting option to add to Chrome is `--autoplay-policy=no-user-gesture-required`, which allows a video to start automatically when a given web page loads (normally, this requires user interaction before the video can play).  This is for making single-video VideoLooper-style kiosks on Pi5, something which VideoLooper does not yet support.
2. Various internal changes of no importance to the end-user.

## Version 0.21 (2025.05.15)
1. The daily upgrade process has been significantly enhanced, as Snap tends to keep many large files around forever.  These files are now removed daily if the kiosk has internet access, so they don't grow to 5-10 gigabytes.
2. The daily kiosk upgrade process is now a bit more graceful as Chromium is stopped before the upgrade process starts.
3. This release contains many minor internal changes resulting from a major code cleanup, which should *not* affect the product in any way.

## Version 0.20 (2025.05.05)
1. A new option, `wifi_country`, was added because Wi-Fi 5G networks mostly worked, but not always.  This option specifies the host country where the kiosk is located.  It is a two-letter abbreviation ("us" = the US, "dk" = Denmark, etc.).
2. A new option, `wifi_hidden`, was added because Linux likes to know this beforehand, so it can scan more quickly or more slowly depending on whether the Wi-Fi network is visible.
3. A problem was fixed in the `KioskForge verify Example.kiosk` command: it did not report missing options, which meant KioskForge verify accepted kiosks that were invalid because they lacked one or more fields (aka options).
4. Various cosmetic changes.

## Version 0.19 (2025.05.03)
1. A new option, `upgrade_post`, which can be either `reboot` or `poweroff`, has been added.  This option controls what the kiosk does after successfully performing maintenance: reboot or power off.
2. `KioskForge.exe` now supports four "subcommands".  They are: `apply`, `create`, `upgrade`, and `verify`.  These commands are currently only usable when invoking KioskForge from the command line, so users who launch it by double-clicking a kiosk file in Windows Explorer do not need to worry about the new subcommands (double-clicking a kiosk file amounts to `KioskForge apply`).  The features offered by the new subcommands will eventually be added to the work-in-progress GUI version of KioskForge.
3. KioskForge.exe now also reports missing options when loading a kiosk.  This is particularly important when loading a kiosk file created in an earlier version of KioskForge.  All errors need to be corrected before the kiosk can be applied and then forged.
4. The help embedded in each kiosk file has been greatly expanded and, hopefully, improved.
5. The `README.html` file has been expanded to include the chapter Synopsis and revised several times.
6. The host name on the kiosk is now set before the forge process begins to avoid cluttering the system log.

## Version 0.18 (2025.04.28)
1. Initial support for the Raspberry Pi 5 has been added.  Sound support on the Pi 5 has not been tested yet, though.
2. The KioskForge setup program now includes a change log of changes made to KioskForge, which can be shown by the installer.
3. The built-in editor and menu have been removed: KioskForge can now only be used to prepare a kiosk installation medium.
4. A new file type, `KioskForge Kiosk`, has been added to the Windows Explorer `New` menu.  Use this to create a new kiosk.
5. The cleaning of logs on the target kiosk machine now actually works (a lowercase 'm' was changed to an uppercase ditto).
6. The `cpu_boost` option is now honored properly.  Previously, all kiosks were created as if `cpu_boost` was always disabled.
7. KioskForge now reports all detected issues and exits gracefully if you open an invalid `.kiosk` file in the program.
8. The HTML documentation in `C:\Program Files\KioskForge` is now much prettier than before.
9. Added detection of, but not support for, Ubuntu Desktop and Server 25.04 so that KioskForge gracefully fails on these.
