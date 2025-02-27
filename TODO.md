# KioskForge Main Task List

## GUI Support
`KioskForge` is intended to be used by non-technical users to set up a kiosk machine for browsing a given website.  Initially, I
made a very primitive Text User Interface (TUI) for the application, consisting of a main menu with five menu items.  Feedback
from actual users, however, strongly suggested that they much preferred a real Graphical User Interface (GUI).  `KioskForge` being
written in Python, made it logical and sensible to develop a GUI using TK/Inter for Python.

I see various paths forward for the TK/Inter GUI:

1. A traditional menu-based application that allows the user to create, load, edit, and save a configuration, and then apply it.
2. A wizard-like application that guides the end-user through each of the steps necessary to make a new kiosk.  This approach
   probably sounds sensible, but some users need to deploy more than one kiosk for which reason such an UI is not adequate.
3. A list view that presents all known kiosks and lets the user edit them as he or she wants to.  Very experimental and not good.

I experimentally used a folder structure where the `Kiosks` folder, as a subfolder of the `KioskForge` folder, was used to store
kiosk configurations.  This has turned out to be confusing and unexpected for the end-users as they like to be able to load and
save configurations from anywhere, such as a network share or the window manager's `Desktop` folder.

My current view is that a traditional modal application, with a main menu that provides features for loading and saving kiosks,
would be the best.  The app needs to provide an editor to edit a configuration with proper validation and error handling.

Darren, the main user of the early versions of KioskForge, suggests that the app uses a wizard-like UI as people only use the app
infrequently and likely won't be sure of how to use it.  The `New` menu item in the `File` menu will eventually open this wizard.

Darren also suggested that KioskForge invokes `Raspberry Pi Imager` and thereby creates the USB/SD-card image so that the user
does not need to know how to create a new Linux bootable key or card.

## Open Tasks
- [ ] 2025.02.27.17.21 H Make the script invoke `Raspberry Pi Imager` directly so that this step is eliminated.
- [ ] 2025.02.27.16.48 H Make the configuration include information on what operating system image is being used.  This to allow
                         full reproducibility of already deployed kiosks.  Upgrading cfgs can be done with `sed` or an editor.
- [ ] 2025.02.27.16.49 H Once the GUI version is complete, remove explanatory comments from configuration files.
- [ ] 2024.11.12.12.47 H Wrap all I/O operations in suitable `try`/`except` statements to avoid crashes on I/O errors.
- [ ] 2024.11.14.14.00 H Make the script fail graciously if it can see a Linux media but not recognize the version.
- [ ] 2025.02.27.13.59 M Split the three Kiosk* classes into separate modules so as to be able to run `PyPi` without errors.
- [ ] 2024.11.07.20.33 M Validate setup **much** better so that it can actually be relied on (blank or not is not good enough).
- [ ] 2025.02.27.16.46 M Make the script scriptable by allowing the user to provide a configuration file, a destination, etc.
- [ ] 2024.11.12.13.00 L Make the script completely resumable so that it can be rerun over and over again without issues.

## Completed Tasks
- [x] 2024.11.21.13.58 H Make the script use Linux' 'syslog' facility for logging instead of a local log file.
- [x] 2024.11.08.11.09 H Ask the user if he/she wants to save the changes after having modified the setup (it already does this).
- [x] 2024.11.07.20.27 H Extract all client-dependent options and make them part of the `Setup` class' information:
	1. Cron job, vacuum logs, daily run time (`vacuum_time`).
      2. Cron job, vacuum logs, days (`vacuum_days`).  Default: 7 days.
      3. Cron job, update, upgrade, clean, and reboot the system (`upgrade_time`).
      4. Cron job, shut down the machine (`poweroff_time`).  If blank, no poweroff.
- [x] 2024.11.03.14.28 H Figure out how to autostart `KioskSetup.py` while having a tty (systemd unit or boot stage)?
      Works, but KS messages are interleaved with the console login prompt, and so on.  Not very pretty.
      A preferable solution is to run KioskSetup.py as a quiet script that logs everything reliably.
- [x] 2024.10.30.13.29 M Figure out a safe way to erase a PC disk quickly prior to installing Ubuntu Server (TOO DANGEROUS).
- [x] 2024.10.30.13.25 H Clean up Logger and console output so that no empty lines appear.
- [x] 2024.10.30.13.25 H Write Lines class, which handles the task of merging lines correctly.
- [x] 2024.10.30.13.26 H Determine the cause of odd error with last few lines of `.bash_startx` missing.
- [x] 2024.10.30.13.34 H Delete line 1372 (`open("lines.txt", ...).write(...)`).
- [x] 2024.11.08.17.38 D Introduce `IntervalField` class to handle the `snap` time interval (much more advanced than that)
- [x] 2025.02.21.16.50 H Ask Darren to get those login credentials for the VHM GitHub account so that I can be added as a user.
                         Nobody knows the credentials and the projects on the `vhm` GitHub account are unused and unknown.
- [x] 2025.02.26.xx.xx H Create a new GitHub user `vhmdk`.
- [x] 2026.02.27.14.10 H Create a new repository `KioskForge` on GitHub for the user `vhmdk`.
- [x] 2025.02.21.17.43 H Ask Darren and Rune what their expectations and wishes for KioskForge v2.x are.
- [x] 2025.02.26.11.54 M Investigate [Open Kiosk](https://openkiosk.mozdevgroup.com/).  It might be worth a try!  Too complex!
- [x] 2025.02.22.13.58 H Rename the `KioskForge` project to something else - the name is already taken by an Italian entity:
	1. `KioskBuilder`?  Taken.
    2. `KioskSetup`?  Taken.
    3. `OpenKiosk`?  Taken (see link in above entry on `Open Kiosk`).
    4. `KioskBuild`?  Not taken, but not very good.
    5. `Kiosk Master`?  Taken.
    6. `KioskForge`? Free.  Chosen.
      `KioskMaker` has just now been renamed to `KioskForge` and that is its current and future name from now on.

