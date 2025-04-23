# KioskForge Main Task List
Please notice that the task list of KioskForge is *currently* spread over two places:

1. This document, which is updated most frequently.
2. The source code itself, these `TODO:` comments are typically intended to be read and acted upon by actual developers.
   Ideally, there shouldn't be any `TODO:` markers in the source code, but they are very easy to create and documents things.


## Task Priorities
1. `U` = Urgent Priority, must be fixed as soon as possible.
2. `H` = High Priority, something that should be worked on after the urgent priority tasks have been closed.
3. `M` = Medium Priority, something that should be worked on after the high priority tasks have been closed.
4. `L` = Low Priority, something that should be worked on after the medium priority tasks have been closed.
5. `D` = Dropped, a task that has been dropped for some reason.
6. `[x]` = Completed, a task that has been closed for some reason.


## Tasks in the Source Code
**NOTE:** Use `grep -FR TODO: *.py` to see the current list of task items embedded in the source code.


## Open Tasks
# TODO:
- [ ] 2024.04.23.22.25 H Enhance KioskForge to detect Ubuntu 25.04 installation medias so that a suitable error is reported.
- [ ] 2024.04.23.14.44 H Add "Kioskforge Kiosk file (.kiosk)" to the `New` menu of explorer so that users can create new kiosks.
- [ ] 2024.04.23.14.45 H Remove everything related to the editor from the TUI version of KioskForge.  Let people use `Notepad` as
                         the TUI editor is broken anyway, the user can't input blank entries at all.
- [ ] 2025.04.04.16.13 H Make the box easier to deploy - allow the use of `poweroff` instead of `reboot` at the last stage.
                         Add `finish` (?) option with one of two values: `shutdown` or `restart` to control the above.
- [ ] 2025.04.13.17.47 H Fix the crappy "restart Chromium" code by replacing it with an ad-hoc Chromium extension:
                         https://chromewebstore.google.com/detail/kiosk-extension/hbpkaaahpgfafhefiacnndahmanhjagi?hl=en
                         https://greasyfork.org/en/scripts/487498-useless-things-series-blur-screen-after-idle/code
- [ ] 2025.03.27.20.15 H Would it be beneficial to create scripts on the host and simply copy them onto the target?  Almost there.
- [ ] 2025.03.21.20.26 H Add WIFI country code and configure it properly with both Cloud-Init and AutoInstall (it works?!).
- [ ] 2025.04.09.11.03 H Eliminate the use of `pactl`, use `wpctl` instead (by parsing the output of `wpctl status --name`).
- [ ] 2025.04.09.11.02 H Make KioskForge much more flexible by configuring most system-specific thing at boot, not while forging.
- [ ] 2025.04.09.11.00 H Test the absense of a network connection by using a cable while forging the box and an invalid Wi-Fi.
- [ ] 2025.04.07.09.39 H The setup program suggests `C:\Program Files\KioskForge` even on a Danish Windows...  Inno setup is to
                         blame.  Apparently, it doesn't support a localized `Program Files` name.  Perhaps a `.msi` installer is
                         needed to handle the intricacies of Windows path names.  For now, the Inno solution is acceptable, though.
- [ ] 2025.04.07.03.50 H Would be nifty the the `command` option worked relative to `~`.  I think it does, but am not sure.
- [ ] 2025.04.07.03.42 H `KioskSetup.py`, and other target-side scripts, are likely to *explode* if there are spaces in path names.
- [ ] 2025.04.07.03.38 H `KioskForge.py` crashes if you make the install medium twice with read-only files in the user folder.
- [ ] 2025.04.07.00.42 H Explore avoiding the PyInstaller `--onefile` option as some actively suggest to not use it.
- [ ] 2025.04.07.00.08 H Check out if any more options need to be optional.
- [ ] 2025.04.06.23.58 H Move `build.py` into its own, closed-source project (?), at least figure out what to do with it.
- [ ] 2025.04.04.15.42 H Should `pip` be allowed to update in `KioskUpdate.py`?  This will probably break things after a while.
- [ ] 2025.04.04.15.42 H Add option `user_modules` to install Python modules with `pip`.
- [ ] 2025.03.29.21.11 H Go through all options and create a two-level "hierarchy" of options: `target.*`, `system.*`, `user`, etc.
- [ ] 2025.03.29.22.14 H Update `README.md`, `FAQ.md`, and `GUIDE.md` with the new names of the options in the new "hierarchy".
- [ ] 2025.03.29.21.17 H Consider to pass in the `Setup` instance to each option: `sound_card` depends on `device`, etc.
- [ ] 2025.03.29.21.00 H Rewrite `Setup.save()` to use a new `???` method, which returns the *external* representation for `.cfg`.
- [ ] 2025.03.27.14.09 H Modules: Every module should be an instance of the class `Module` and should provide the following:
						    1. A textual description, which may be made up of multiple lines of text.
                            2. A default configuration, which is provided as a Python `Dict[str, str]`.
                            3. The default configuration makes it possible to read and display the *default module settings*.
                            4. A way of asking the module if it can be rolled back or not (not all changes can be undone).
                            5. A means of changing its configuration, both single-value and dictionary of multiple values.
                            6. A method of committing a configuration (perform the necessary changes to the kiosk system).
                            7. A method of rolling back a configuration.
                            8. A method of diffing any multi-module configuration to determine what needs to be undone.
                         Furthermore, it would be *awesome* if modules could be tested easily from scripts or the prompt.
- [ ] 2025.01.29.xx.xx H Make most steps in the setup process optional as not all users need every step.
- [ ] 2025.03.24.03.24 H Test forging a PC target.  It is probably broken by now.  Also, it needs to be automatic, not manual.
                         The AUTOSTART code is not implemented in the Subiquity (AutoInstall) writer, so this is broken by now.
- [ ] 2024.11.26.xx.xx H Fix the broken PC install.  The script is copied to `/`, not `/home/user` (the code runs as root...).
- [ ] 2025.03.19.23.14 H Make the `pinch` feature optional, currently it is hard-coded so that pinch always is enabled (???).
- [ ] 2025.03.15.19.15 H Loading a configuration with missing values should auto-assign defaults and report suitable warning(s).
- [ ] 2025.02.28.02.05 H The `TESTING` variable should use an environment variable rather than a hard-coded value.
- [ ] 2025.02.27.16.48 H Make the configuration include information on what operating system image is being used.  This to allow
                         full reproducibility of already deployed kiosks.  Upgrading cfgs can be done with `sed` or an editor.
- [ ] 2025.03.16.03.31 H GUI: Make the Kiosk configuration reader and writer handle multi-line text lines for the `comment` field.
- [ ] 2025.03.16.03.31 H GUI: Consider adding purely administrative fields such as `IP address` and possibly others like that.
- [ ] 2025.03.09.10.15 H GUI: Consider using tabs for the different configuration sections (General, Network, ...).
- [ ] 2025.03.09.00.53 H GUI: Make a guide/wizard for the `Edit (guided)` menu item so that any user can configure a kiosk easily.
- [ ] 2025.03.07.07.43 H GUI: Make a checkbox next to each optional field that disables or enables the input value.
                         This to provide a visual clue on which fields are optional and which are not.
- [ ] 2024.11.12.12.47 H Wrap all I/O operations in suitable `try`/`except` statements to avoid crashes on I/O errors.
- [ ] 2025.04.07.03.01 H Add full support for IPv6.  Some users will likely need this, eventually.
- [ ] 2025.03.15.18.43 M GUI: Add tab for the target device (Raspberry Pi, PC), where overclocking (wifi, cpu) can be configured.
- [ ] 2025.03.16.06.07 M GUI: Add option to control overclocking of RPI4 and RPI5.
- [ ] 2025.03.09.09.55 M GUI (on Linux): Check that tkinter is available and perhaps also that X11/Wayland is installed.
                         The purpose of this task is to finally eliminate MyPy's constant whining over Linux-specific logging code.
- [ ] 2025.03.19.09.47 M Consider to move SHA512 sums for Ubuntu versions into an .INI file so that it is easy to adjust and expand.
- [ ] 2024.09.xx.xx.xx M Add support for virtual keyboard to the kiosk (larger task, ref. `onboard` and `Florence`).
- [ ] 2024.12.17.xx.xx M Add support for a local NGINX/Apache web server so that the kiosk can serve a PHP web site locally, it
                         should also be possible to specify a .sql file to import into MariaDB, etc., after installation.
- [ ] 2024.12.17.xx.xx M Write documentation on how to update the files served by the local web server, if any, using `WinSCP`.
- [ ] 2025.03.09.06.39 M Make KioskForge check that it is running on a supported Windows such as Windows 10+.
- [ ] 2024.11.07.20.33 M Validate setup **much** better so that it can actually be relied on (blank or not is not good enough).
- [ ] 2025.02.27.16.46 M Make the script scriptable by allowing the user to provide a configuration file, a destination, etc.
- [ ] 2025.03.19.23.08 M Open up the GitHub repository for the public once most of the high priority tasks are completed and a
                         kiosk has proven itself for a while.  Wait until the GUI is complete and works as intended.
- [ ] 2025.03.19.23.18 M Test out and document how to use a `syslog` client to view the status of the kiosk setup scripts.
                         https://github.com/MaxBelkov/visualsyslog
- [ ] 2025.03.24.05.49 M Redo the `Logger` class so that it **only** uses Python's `logging` module as outlined in this article:
                         https://stackoverflow.com/questions/3968669/how-to-configure-logging-to-syslog-in-python
						 2025.04.11: I spent two hours trying to get this to work, but either got too much or too little output.
						 Syslog entries didn't appear at all and console output didn't work unless I used a simple `print`.
- [ ] 2025.03.28.13.14 L The Linux version of KioskForge (when, if) must be built on Linux and packaged using `tar` to ensure that
                         the main executable is executable on such systems.  So we need `KioskForge-m.nn.tar.gz` and
                         `KioskForge-m.nn.zip`, the latter for Windows users.  Ideally, there'd only be one executable for each
                         platform.
                         There is now only a single installer image for Windows.  This needs to made for Linux as well.
- [ ] 2025.03.27.15.15 L Add option to allow the installation of user-specified packages.
- [ ] 2025.03.27.14.05 L Dynamic Reconfiguration: That `KioskSetup.py` is run every configuration change and automatically
                         installs, removes, and configures packages and the system according to the configuration on every boot.
- [ ] 2025.03.19.10.07 L Consider to add color support to the TUI version of the script, most noticable red colors for errors.
- [ ] 2025.03.19.22.04 L Rewrite detector logic so that the known platforms are defined by a list of detector instances.
- [ ] 2025.03.19.01.39 L Check if the kiosk supports audio playback at all (when `audio=1`).  People report issues with this:
                         https://forums.raspberrypi.com/viewtopic.php?p=1979825#p1979542
- [ ] 2025.03.09.05.18 L Try out [PyPy](https://github.com/pypy/pypy), it should support Tkinter.  Recommended by Alexandre ("pypy is just a python with jit").  Probably not relevant then due to lack of intensive computing tasks.  The most important thing for KioskForge is that Python is easy to install.
                         PyPy cannot easily generate stand-alone executables so `PyInstaller` is better for now.
- [ ] 2024.11.12.13.00 L Make the script completely resumable so that it can be rerun over and over again without issues.
                         This could, perhaps, be done by saving a list of already performed steps or by adding a feature to undo a
						 step that has already been done, although this is a more complicated than just skipping successful steps.
- [ ] 2025.03.05.18.25 L Make the script download the current [Ubuntu Server image](https://cdimage.ubuntu.com/releases/noble/release/ubuntu-24.04.2-preinstalled-server-arm64+raspi.img.xz).
- [ ] 2024.10.10.xx.xx L Support Wayland instead of X11.  Use [wlr-randr](https://github.com/emersion/wlr-randr) instead of `xrandr`.

## Completed Tasks
- [x] 2025.04.15.05.03 H The `DEBIAN_FRONTEND` environment variable is *not* passed to the invocations of `apt`, etc.!
                         This is a left-over from the original Bash version, `AptAction` should set `DEBIAN_FRONTEND` instead.
						 I just tested and `DEBIAN_FRONTEND` *is* passed through `subprocess.run()` in *all* cases.
- [x] 2025.04.13.23.03 H `KioskStart.py` often starts without network.  Should it wait for this to come up if `network=always`?
- [x] 2025.04.09.05.43 H Solve the problem that some kiosks only have Wi-Fi during the forge process.  Recommend cabled network.
                         Also consider to add an option, `network=always|install` to make the kiosk forget Wi-Fi network after use.
						 Not a good idea, if the kiosk is taken back for maintenance.  Better as it is now, it works as it should.
- [x] 2025.03.16.06.03 H Rewrite all Bash scripts generated by KioskForge into Python3 scripts so as to allow access to the
                         configuration file (`KioskForge.cfg`) on the target kiosk so that the user *can* change a setting
						 simply by logging in, preferably using SSH, editing `KioskForge.cfg`, and then rebooting the kiosk.
- [x] 2025.03.27.16.55 H Investigate how to make minijack work even though is not recommended by most (requires an amplifier).
                         Works fine, just plug in a couple of amplifying loud speakers and it works just as expected.
- [x] 2025.03.27.17.38 H Make the kiosk configuration more flexible: Prepare for doing motion detector + custom script, etc.
                         This was solved by adding the `type=web|x11|cli` option and is in actual production use.
- [x] 2025.04.09.09.52 H Consider to add "stages": Stage 1 is host, stage 2 is first run, stage 3 is second run, stage 4 = poweroff.
                         No longer necessary, all kernels are now installed by using `apt-get dist-upgrade -y` in `KioskSetup.py`.
- [x] 2025.04.12.06.14 H `../bld/KioskForge.iss` - the RAMDISK path should be configured by `build.py`, not hard-coded.
- [x] 2025.04.13.06.45 H Make visual guide (with pictures) of how to make an installation medium using Raspberry Pi Imager.
                         Found one in the documentation for Raspberry Pi Imager, I've linked to it in the `README.md` file.
- [x] 2025.04.13.08.04 H Why does `journalctl --vacuum-time=30d` vacuum everything?  Probably NTP not synced time yet.
                         Change KioskForge to use `vacuum_size` instead of `vacuum_days`, the former does not need an RTC.
- [x] 2025.04.09.05.45 H Fix the annoying problem that the kernel is not always updated completely, because there may be more than
                         one in the package repository.  Either repeat upgrading until there are no upgrades left or use CloudInit
						 to perform the system upgrade.  Unfortunately, I have seen this time out at least once.
						 Fixed by using `apt-get dist-upgrade -y` instead of `apt-get upgrade -y` in `KioskSetup.py`.
- [x] 2025.04.13.09.07 U The `KioskUpdate.py` script does *not* wait for `apt` to release its lock files, if locked!
- [x] 2025.04.11.03.40 H Make MyPy check everything without any warnings or errors.  Finally, this worked with MyPy v1.15.
- [x] 2025.04.03.06.09 H Rewrite build batch scripts (`test.bat`, `test.sh`) into Python for portability and consistency.
- [x] 2025.03.28.12.23 H The auto-installation of `bcrypt` should specify a version to ensure continued operation for a while.
                         `bcrypt` is now bundled as part of the PyInstaller `.exe` file so this is no longer an issue.
- [x] 2025.03.29.21.11 H Rename `orientation` to `display_rotation`.
- [x] 2025.03.09.00.04 H As KioskForge grows, the need for it to run in a virtual environment probably does too.
                         Only if extra, non-standard packages are used such as `bcrypt`, which KioskForge uses.
                         As of 2025.04.09, `KioskForge` is bundled a single executable using `PyInstaller`.  No need for venvs.
- [x] 2025.03.19.07.35 H Protect against "injection attacks": Quote all user-supplied data passed to cloud-init, etc.  Bah.
- [x] 2025.03.27.18.37 H Make `KioskStart.py` responsible for configuring Pipewire (to give access to the `Setup` instance).
                         This should be done by the login shell, if possible, as people may want audio for non-browser-kiosks.
						 Create a new script, `KioskSound.py`, which handles the configuration of Pipewire.
						 This is done by the `KioskStart.py` script which doesn't have root priveleges (it works...).
- [x] 2025.04.07.02.31 H Consider to rename `upgrade_time` to `maintenance` or something like that.  Nope, it only does upgrades.
- [x] 2025.04.09.12.56 H Move `journalctl vacuum` to `KioskStart.py` so that is invoked on every boot, not on a preset time.
                         This is a good way to solve the problem that some kiosks never have network and thus no upgrades are done.
                         Nope, this is not a usable way as `KioskStart.py` runs as the created user, not as root.  Moved to its
                         own `@reboot` cron job.  This should ensure it is run whether or not there is any internet or not.
- [x] 2025.04.09.10.34 H Display the LAN IP on every boot, not just when forging the kiosk.  In some places, DHCP is volatile.
- [x] 2025.04.09.11.15 H Merge `KioskStartX11.py` and `KioskRunner.py` into one script called - ... - `KioskStart.py`.
                         Remember to update code that copies KioskForge around: `KioskForge.py` and `KioskSetup.py`.
- [x] 2025.03.27.18.25 H Check if the PI4B audio device names (`wpctl status --name`) are board dependent.
                         They are currently hardcoded in the `KioskStartX11.py` script generated by `KioskSetup.py`.
						 KioskForge works with audio on several different PI4B boards, so they are not board dependent.
- [x] 2025.04.07.09.24 H Make `build.py` export the correct version number to the Inno Setup compiler.
- [x] 2025.04.07.10.19 H Fix bogus hint about `vacuum_time` being set: that option no longer exists.
- [x] 2025.04.07.01.30 H How does `user_folder` work with the new installer?  I guess will be completely broken...
                         The solution is to work relative to the '.kiosk' file in `KioskForge.py`, allowing `user_folder=.`.
- [x] 2025.04.07.02.17 H Add support for the user double-clicking a `.kiosk` file in Windows Explorer (i.e. an argument).
- [x] 2025.04.07.02.03 H Use `.kiosk` as the extension of KioskForge configuration files instead of `.cfg`.
- [x] 2025.04.07.01.53 H Eliminate the `vacuum_time` option, this should be done as part `KioskUpdate.py` to keep things simple.
- [x] 2025.03.15.18.58 H Make the `wifi_boost` setting optional.
- [x] 2025.03.28.12.17 H Check out https://thisdavej.com/share-python-scripts-like-a-pro-uv-and-pep-723-for-easy-deployment/ to
                         see if this is something of value for the KioskForge project.  Not relevant when we use `PyInstaller`.
- [x] 2025.03.28.13.27 H Finish up the `GUIDE.md` document and make sure to document the more peculiar options such as `snap_time`.
						 Also, expand the `README.md` guide (perhaps an appendix) to explain each option in detail.
						 `snap_time` has been removed and is now integrated into the `KioskUpdate.py` script.
- [x] 2025.03.31.22.00 H It may be useful to start the kiosk using a systemd job instead of through `.bashrc`.  This would fix the
                         problem that the kiosk is started twice if you SSH into the kiosk machine.
						 I have spent hours on this - with no success whatsoever - so I dropped doing this for now.
- [x] 2025.04.03.06.51 H Figure out what to do about the `ship.bat` script; it really shouldn't be part of the public GitHub repo.
                         The `ship.bat` script is now part of the `build.py` script, which shouldn't be part of the repository.
- [x] 2025.04.04.16.13 H Add option `network` to allow disabling network completely, after forging is complete.  This should imply
                         `snap_time=`, `update_time=`, `wifi_name=`, etc.
						 This has been fixed with two changes: 1) snap is now updated in `KioskUpdate.py` and 2) `KioskUpdate.py`
						 now ignores the request to upgrade everything if there is no internet available.
- [x] 2025.03.29.21.12 H Introduce symbolic names for the four screen rotations: `none`, `left`, `right`, and `flip` (upside-down).
- [x] 2025.03.27.19.04 H Change `audio` option to be one of `none`, `auto`, `jack`, `hdmi1`, `hdmi2`.  Configure accordingly.
                         `auto` will only work on PCs, which I cannot develop nor test at this point in time.
						 This was done with the update that introduced `sound_card` and renamed `audio` to `sound_level`.
- [x] 2025.03.27.20.28 M Would it make sense to merge all target scripts into a single script to simplify exception handling? No.
- [x] 2025.04.04.16.10 H Support disabling snap updates using the `snap refresh --hold` command (let `KioskUpdate.py` do it).
- [x] 2025.04.04.17.23 H Snaps ought to be updated in the `KioskUpgrade.py` script, to make things simpler for the end-user.
- [x] 2025.03.31.16.20 H Rename `KioskStart.py` to something better, `KioskOpenBox.py` for instance.
- [x] 2025.03.31.20.31 H Handle the case that the kiosk has no internet graciously!  Internet is required for the forge process.
                         Check if the cron update jobs fail or what happens.  The update cron job now check if there is internet.
- [x] 2025.04.03.02.43 H Add option to enable/disable ARM CPU overclocking (enabled by default by Raspberry Pi Imager).
- [x] 2025.04.03.00.44 H Stop writing `KioskStartX11.py` dynamically, make it a driver like the other Python scripts.
- [x] 2025.03.27.10.19 H Power-saving should **not** be disabled in the `KioskOpenbox.py` script but in a systemd service!
- [x] 2025.03.31.22.28 H Add option (`offline`?) to let the user specify whether the system is expected to be online or not.
                         I think it is better to make KioskForge so that a forged kiosk can work in both states.
- [x] 2025.03.29.21.31 H Rename `data_folder` to `user_folder`?
- [x] 2025.03.29.22.38 H Rename `platform` to `device`.
- [x] 2025.03.29.20.53 H It still isn't possible to exit `KioskForge.py` if there are errors in the configuration.
- [x] 2025.03.29.20.58 H Errors during editing are first caught by the main menu, so the user drops out to it on errors...
- [x] 2025.03.29.21.02 H Add proper checks of all settings, especially `sound_card` and stuff that depends on other options.
- [x] 2025.03.27.18.57 H The output device should be user-selectable: HDMI1, HDMI2 or Jack. (on my Raspberry Pi 4B):
                         1. Jack: `alsa_output.platform-bcm2835_audio.stereo-fallback`.
                         2. HDMI1: `alsa_output.platform-fef00700.hdmi.hdmi-stereo`.
                         3. HDMI2: `alsa_output.platform-fef05700.hdmi.hdmi-stereo`
                         THE VALUES GIVEN ABOVE ARE PROBABLY DEVICE-SPECIFIC AND MUST BE FETCHED FROM `wpctl`.
						 The values are very unlikely to be valid for Raspberry Pi 5 (even if they work on 4B).
- [x] 2025.03.29.20.51 H Rename `audio` option to `sound_level`.  Introduce `sound_card`.
- [x] 2025.03.27.16.53 H Create `kiosklog` function early on so that the user can SSH in and follow the progress easily.  Document!
- [x] 2025.03.27.20.47 H Rewrite 'KioskLaunchX11.sh' Bash script into Python.
- [x] 2025.03.27.14.22 H New option: `ip_address`, could be used to let KioskForge "deregister" a known host in `known_hosts`.
                         This should be part of a `build` script or something, KF shouldn't mess around with the hosts' SSH files.
- [x] 2025.03.27.17.48 H Create `cron` job to clear the apt cache regularly: `apt clean`.  (This is done by the upgrade cron job.)
- [x] 2025.03.27.11.19 H Audio *is* broken in Chromium and KioskForge.  Works beautifully in Ubuntu Desktop 24.04.2/ARM64.
                         The problem was that the --no-installs-recommends option was given to `apt`.
- [x] 2025.03.20.03.51 U X11 does not always start up, if `audio=1`: it fails with the error from pipewire) shown below:
                         `Translate ID error: [-1] is not a valid ID (returned by default-nodes-api)`
						 This is partially solved by installing the `rtkit` package and enabling its `systemd` service.
						 [Translate console error](https://forums.gentoo.org/viewtopic-t-1168313-start-0.html)
						 [jackdbus syslog error](https://forums.linuxmint.com/viewtopic.php?t=408389)
- [x] 2025.03.20.04.07 H Pipewire audio does not appear to work (I don't have any suitable headphones at hand).
- [x] 2025.03.19.05.33 H Not sure if the `audio` kiosk settings work (`mouse` appears to work just fine).
- [x] 2025.03.19.04.59 H Investigate if `xrandr` is better at providing useful output than `xinput` (requires a touch screen).
- [x] 2025.03.26.05.41 H What about the case that there's both a mouse and a touch screen/panel?  `xrandr` only supports mice, but
                         the coordinate transformation given to `xinput` probably blows both to kingdom come.
						 The touch panel is now rotated using an X11 configuration file which does not apply to the screen.
- [x] 2025.03.26.12.19 H Set host name as the very first operation to avoid two different host names in syslog.
- [x] 2025.03.26.04.58 H Rename `invoke` to `invoke_text` globally.
- [x] 2025.03.24.03.18 H Why is `idle_timeout` written to the configuration file as a string, not as an integer?  Typo, fixed.
- [x] 2025.03.24.04.17 H Only modify `/etc/ssh/sshd.conf` to **require** a private key if a public key has been specified.
- [x] 2025.03.19.23.26 H Explore `cx_freeze` to generate a stand-alone `.exe` file that the end-user can run without having to
                         install Python and so on.  [cx-freeze](https://cx-freeze.readthedocs.io/en/stable/)
						 Decided to go with [PyInstaller](https://pyinstaller.org/en/stable/) instead as `cx_freeze` was way too
						 difficult to configure and make work as intended.
- [x] 2025.03.05.16.28 H Change `logger` local into a global variable so it is accessible everywhere (crude hack due to laziness).
                         (Dropped, no particular need for the above change.)
- [x] 2025.03.19.22.17 H Always use the name `KioskForge.cfg` for the configuration file so as to not confuse end users.
- [x] 2025.02.27.13.59 H Split the three Kiosk* classes into separate modules so as to be able to run `PyPi` without errors and
                         make KioskForge run as a [PyInstaller(https://pyinstaller.org/en/stable/) stand-alone executable.
- [x] 2025.03.22.00.24 H Python v3.x (until v3.15) uses Windows' code page, not UTF-8, as the default stream character set...
                         All streams **must** be opened with `, encoding='utf-8'`.
- [x] 2025.03.20.04.04 H Check `syslog` for errors from the installed packages, etc. so as to detect other possible problems.
- [x] 2025.03.19.09.11 H Separate `rotate_screen` `xinput` logic from `xrandr` logic as not everybody needs the former.
                         This makes the configuration of a kiosk rather error-prone as the user probably forgets to enable `xinput`
						 when enabling `xrandr` and vice versa.  For now, they work in unison.
- [x] 2025.03.15.19.00 H Uninstall the Ubuntu package `needrestart` as the kiosk always reboots after upgrading.
- [x] 2025.02.28.01.12 H Consider making a server in Python that the kiosks can report their IP and status to.  Use broadcasts.
                         Not necessary, the user can simply check his or her router UI for this information and even lock the IP.
- [x] 2025.03.19.04.35 H Investigate if this entry can be used for anything (not very likely):
                         [Get list of touch screens using `xinput`](https://gist.github.com/rubo77/daa262e0229f6e398766?permalink_comment_id=1763721#gistcomment-1763721)
						 I have already implemented similar code, which handles multiple touch screens as well as a single one.
- [x] 2025.03.19.04.53 H KioskForge fails to report an error if completely unable to identify the install image.
- [x] 2025.03.19.01.35 H Parse output of `xinput list` and keep all `Virtual core pointer` values but `Virtual core XTEST pointer`:
                         One person on the 'net reported that he or she had to use `Virtual core XTEST pointer` as the choice.
                         Filter out the two Raspberry Pi 4 devices (RPI5?) `vc4-hdmi-0` and `vc4-hdmi-1`.
                         This is the list of devices that need a transformation matrix to operate with a rotated display.
						 Consider or experiment with only keeping values that match `touch` (case-insensitive).
- [x] 2025.03.19.04.28 H Mark errors **much** more visible, possibly by writing three stars in front of them.
- [x] 2025.03.09.16.28 H Begin using [type_enforced](https://github.com/connor-makowski/type_enforced) globally in the project.
                         This *may* require installing the module via `pip`, but in that case the script should detect that the
						 module is missing and automatically install it (perhaps with a confirmation).
- [x] 2025.03.09.16.44 H I spent like fifteen minutes on trying out `type_enforced` and didn't manage to get it to work.  Most
                         noticably, it doesn't yet really support global enforcement, only per-class and per-function.  Looks good,
						 but probably needs a bit more work before I can use it as I plan to (on all of my code).
- [x] 2025.02.28.05.15 H Add support for Ubuntu Server (and Desktop) v24.04.2 to the operating system detector.
- [x] 2025.03.19.04.45 H TUI version: Suggest to save to same folder as was loaded from.  Don't generate a path.
                         The TUI version already does this, a path is only generated if a configuration wasn't loaded beforehand.
- [x] 2025.03.19.08.08 H Make the `xinput` configuration code in `KioskStart` use device ids rather than device names to avoid
                         the problem that device names either are not found or are listed twice by `xinput`.
- [x] 2025.03.19.01.03 H If using `bcrypt`, passwords can only be 72 chars in length.  Check this in the `Setup()` class.
- [x] 2025.03.15.19.53 H Add `rotate_screen` option: `0`=`normal`, `1`=`left`, `2`=`inverse`, and `3` = `right` (`xrandr` values).
- [x] 2025.03.16.05.34 H Change boolean configuration options into using `0` and `1` as their values instead of `n` and `y`.
- [x] 2025.03.05.16.29 H Figure out why `ExternalAptAction.execute()` does not work when the `lsof` code is enabled then enable it.
                         An `InternalError` exception was thrown in `Result.__init__()` when `status` was zero and `output` empty.
- [x] 2025.03.05.16.35 H Investigate if background `apt` services can be temporarily stopped while running `KioskSetup.py`.
                         Not necessary, I finally found and removed the incorrect parameter check in `Result.__init__()`.
- [x] 2024.11.14.14.00 H Make the script fail graciously if it can see a Linux media but not recognize the version.
- [x] 2025.02.27.16.49 H Remove explanatory comments from configuration files (people use the TUI/GUI to edit these values).
- [x] 2025.02.28.00.56 H I believe I left the Pi on yet it was off after five hours.  I'll try again over the night.
                         This issue has not been recreated, but it *may* be caused by the idle timeout code.  Perhaps a process
						 that is not closed down correctly or Chromium that crashes when restarted.
						 X11 left this error in its log file (`.xsession-errors`):
						 `XIO: fatal IO error 4 (Interrupted system call) on X server ":0" after 4801 requests (4798 known processed) with 0 events remaining.`
						 After which X11 seems to have crashed, pulling down the entire kiosk (into a dead state).
						 I reread the code in `KioskStart.py` and an assignment statement was missing, possibly causing the issue.
						 I am going to make a new kiosk and leave it running through the night.
						 04:25 So far, the box has run without issues, I am confident that the missing assignment statement was the
						 cause of the X11 crash because it meant that a dead process was occasionally attempted killed.
- [x] 2025.02.28.01.44 H I observed cloud-init report "ERROR: Timeout was reached" (?), which could indicate that I am giving
                         cloud-init too much work during the initial boot.  I am going to disable cloud-init upgrades for now.
                         Remember to disable upgrades when using autoinstall.yaml (Subiquity).
- [x] 2025.03.03.15.10 H Make the script report no active internet connection loudly and clearly.
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
	  This has been implemented, in March, 2025, as a permanent feature by setting `AUTOSTART` to `True` as this simplifies life
	  enormously for the end-user who no longer needs to log into the kiosk machine to start the configuration process.
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
- [x] 2025.02.22.13.58 H Rename the `KioskMaker` project to something else - the name is already taken by an Italian entity.
                         Names such as `KioskBuilder`, `KioskSetup`, `OpenKiosk`, `Kiosk Master` were all taken but `KioskForge`
						 turned out to be free, according to Google, so I chose that and have registered the .org domain already.
- [x] 2025.02.26.11.54 M Investigate [Open Kiosk](https://openkiosk.mozdevgroup.com/).  It might be worth a try!  Too complex!
- [x] 2025.02.27.17.21 L Make the script invoke `Raspberry Pi Imager` directly so that the burning step is eliminated:
                         "c:\Program Files (x86)\Raspberry Pi Imager\rpi-imager-cli.cmd" --cli --disable-verify --disable-eject --enable-writing-system-drives "c:\Users\Mikael\Downloads\ubuntu-24.04.2-preinstalled-server-arm64+raspi.img.xz" \\.\PhysicalDrive2
                         This requires finding the physical path of the USB key, which can be done with `wmi` for Python, but I am
                         not happy about the prospect of the user accidentally deleting a drive with valuable data, so this is dropped.
						 Furthermore, it will require the installation of two additional packages for Python, something I doubt the
						 average KioskForge user will be capable of.

