# KioskForge Changes
This document presents the important changes made to each KioskForge release from v0.18 and onwards:

## Version 0.23 (2025.07.03)
1. The KioskForge Setup program now creates a `Start` menu group, which contains links to the various sources of documentation.
2. There is **intentionally** no link to the program as you're supposed to run it by double-clicking a `.kiosk` file or from the
   command-line (using `CMD.EXE`).  A GUI version is work in progress, but progress is rather slow.
3. If you have an old link to the `KioskForge.exe` program in your `Start` menu, you can simply uninstall and reinstall KioskForge,
   this should remove the stale link.  If not, you can simply delete the link manually.
4. `README.html` has been renamed to `Manual.html`, this only affects those who actually dug out the file from the app folder.
5. `GUIDE.html` has been renamed to `Guide.html`, this only affects those who actually dug out the file from the app folder.

## Version 0.22 (2025.06.25)
1. The option `user_options` has been added.  This allows the user to specify additional options to Google Chrome.  The most
   interesting option to add to Chrome is `--autoplay-policy=no-user-gesture-required`, which allows starting a video automatically
   when a given web page is loaded (normally this requires user-interaction before the video can play).  This is for making single
   video `VideoLooper` style kiosks on Pi5, something which VideoLooper does not yet support.
2. Various internal changes of no importance to the end-user.

## Version 0.21 (2025.05.15)
1. The daily upgrade process has been enhanced significantly as `snap` likes to keep many large files around forever.  These files
   are now removed on a daily basis, if the kiosk has internet access, so that they don't grow to 5-10 gigabytes in size.
2. The daily kiosk upgrade process is now a bit more graceful as Chromium is stopped before the upgrade process starts.
3. This release contains many small internal changes due to a major code cleanup, which should *not* affect the product in any way.

## Version 0.20 (2025.05.05)
1. A new option, `wifi_country`, was added because Wi-Fi 5G networks mostly worked, but not always.  This option is used to specify
   the host country that the kiosk is placed in.  It is a two-letter abbreviation ("us" = the US, "dk" = Denmark", etc.).
2. A new option, `wifi_hidden`, was added because Linux likes to know this beforehand, so that it can scan quickly or more slowly,
   depending on whether or not the Wi-Fi network is visible or not.
3. A problem was fixed in `KioskForge verify Example.kiosk` because it did not report *missing* options, which basically meant that
   `KioskForge verify` accepted kiosks that were invalid as they lacked one or more fields aka options.
4. Various cosmetic changes.

## Version 0.19 (2025.05.03)
1. A new option, `upgrade_post`, which can be either `reboot` or `poweroff`, has been added.  This option controls what the
   kiosk does when it has successfully performed maintenance: reboot or poweroff.
2. `KioskForge.exe` now supports four "subcommands".  They are: `apply`, `create`, `upgrade`, and `verify`.  These commands are
   currently only usable when invoking KioskForge from the command-line so users who launch it by double-clicking a kiosk
   file in Windows Explorer do not need to worry about the new subcommands (double-clicking a kiosk file amounts to `apply`).
   The features offered by the new subcommands will eventually make their way to the work-in-progress GUI version of KioskForge.
3. KioskForge.exe now also reports missing options when loading a kiosk.  This is particularly important when loading a kiosk file
   created in an earlier version of KioskForge.  All errors need to be corrected before the kiosk can be applied and then forged.
4. The help embedded in each kiosk file has been greatly expanded and hopefully made significantly better.
5. The `README.html` file has been expanded with the chapter `Synopsis` and also revised a number of times.
6. The host name on the kiosk is now set before the forge process begins to avoid making a mess of the system log.

## Version 0.18 (2025.04.28)
1. Initial support for the Raspberry Pi 5 has been added.  Sound support on the Pi 5 has not been tested yet, though.
2. The KioskForge setup program now includes a change log of changes made to KioskForge, which can be shown by the installer.
3. The built-in editor and menu has been removed: KioskForge can now only be used to prepare a kiosk installation medium.
4. A new file type, `KioskForge Kiosk`, has been added to the Windows Explorer `New` menu.  Use this to create a new kiosk.
5. The cleaning of logs on the target kiosk machine now actually works (a lowercase 'm' was changed to an uppercase ditto).
6. The `cpu_boost` option is now honored properly.  Previously, all kiosks were created as if `cpu_boost` was always disabled.
7. KioskForge now reports all detected issues and exits gracefully if you open an invalid `.kiosk` file in the program.
8. The HTML documentation in `C:\Program Files\KioskForge` is now much prettier than before.
9. Added detection of, but not support for, Ubuntu Desktop and Server 25.04 so that KioskForge gracefully fails on these.

