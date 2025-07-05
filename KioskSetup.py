#!/usr/bin/env python3
# KioskForge - https://kioskforge.org
# Copyright (c) 2024-2025 Vendsyssel Historiske Museum (me@vhm.dk). All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following
# conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this list of conditions and the disclaimer below.
#     * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided with the distribution.
#     * Neither the name of Vendsyssel Historiske Museum nor the names of its contributors may be used to endorse or promote
#       products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# This script is responsible for setting up the Linux kiosk machine (forging it) according to the user's kiosk configuration.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List

import os
import shlex
import stat
import sys
import time

from toolbox.actions import AppendTextAction, AptAction, CreateTextAction, CreateTextWithUserAndModeAction, ExternalAction
from toolbox.actions import InstallPackagesAction, InstallPackagesNoRecommendsAction, PurgePackagesAction, RemoveFolderAction
from toolbox.actions import ReplaceTextAction
from toolbox.builder import TextBuilder
from toolbox.driver import KioskDriver
from toolbox.errors import CommandError, InternalError, KioskError
from toolbox.invoke import invoke_text
from toolbox.kiosk import Kiosk
from toolbox.logger import Logger
from toolbox.network import internet_active, lan_ip_address
from toolbox.script import Script
from toolbox.various import screen_clear


# NOTE: The matrices have been verified against https://wiki.ubuntu.com/X/InputCoordinateTransformation.
MATRICES = {
	'none'  : '1 0 0 0 1 0 0 0 1',
	'left'  : '0 -1 1 1 0 0 0 0 1',
	'flip'  : '-1 0 1 0 -1 1 0 0 1',
	'right' : '0 1 0 -1 0 1 0 0 1'
}

WAYLAND_ORIENTATION = {
	"none"  : "normal",
	"left"  : "left",
	"flip"  : "inverted",
	"right" : "right"
}

WAYLAND_CONFIGURATION = """
layouts:
# keys here are layout labels (used for atomically switching between them)
# when enabling displays, surfaces should be matched in reverse recency order
  default:                         # the default layout
    cards:
    # a list of cards (currently matched by card-id)
    - card-id: 0
      HDMI-A-1:
        # This output supports the following modes: 1920x1080@60.0, 1920x1080@59.9,
        # 1920x1080@30.0, 1920x1080@30.0, 1920x1080@50.0, 1920x1080@25.0, 1680x1050@59.9,
        # 1280x1024@75.0, 1280x1024@60.0, 1440x900@75.0, 1440x900@59.9, 1280x960@60.0,
        # 1152x864@75.0, 1280x720@60.0, 1280x720@59.9, 1280x720@50.0, 1440x576@50.0,
        # 1024x768@75.0, 1024x768@70.1, 1024x768@60.0, 800x600@75.0, 800x600@60.3,
        # 800x600@56.2, 720x576@50.0, 720x480@60.0, 720x480@59.9, 640x480@75.0,
        # 640x480@66.7, 640x480@60.0, 640x480@59.9, 720x400@70.1
        #
        # Uncomment the following to enforce the selected configuration.
        # Or amend as desired.
        #
         state: enabled        # "enabled" or "disabled", defaults to "enabled"
         position: [0, 0]      # Defaults to [0, 0]
         orientation: {orientation} # "normal", "left", "right", or "inverted", defaults to "normal"
         scale: 1
         group: 0      # Outputs with the same non-zero value are treated as a single display
      HDMI-A-2:
        # (disconnected)
""".strip()



class KioskSetup(KioskDriver):
	"""This class contains the 'KioskSetup' code, which configures a supported Ubuntu Server system to become a web kiosk."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		if sys.platform == "linux":
			# Clear the screen before we continue, to make the output more comprehensible for the end-user (clear CloudInit noise).
			screen_clear()

		# Output program banner and an empty line.
		logger.write(self.version.banner())
		logger.write()

		# Check that we're running on Linux.
		if sys.platform != "linux":
			raise KioskError("This script can only be run on a Linux kiosk machine")

		# Check that we've got root privileges.
		if os.geteuid() != 0:		# pylint: disable=no-member
			raise KioskError("You must be root (use 'sudo') to run this script")

		# Check that we have got an active, usable internet connection.
		index = 0
		while not internet_active() and index < 6:
			logger.write("*** NETWORK DOWN: Waiting 5 seconds for the kiosk to come online")
			index += 1
			time.sleep(5)
		if index:
			logger.write()
		del index

		# If still no network, abort the forge process.
		if not internet_active():
			logger.error("*" * 79)
			logger.error("*** FATAL ERROR: NO INTERNET CONNECTION AVAILABLE!")
			logger.error("*** (Please check the Wi-Fi name and password - both are case-sensitive.)")
			logger.error("*" * 79)
			raise KioskError("No active network connections detected")

		# Display LAN IP - not everybody has access to the router in charge of assigning a LAN IP via DHCP.
		logger.write("*** LAN IP: " + lan_ip_address())
		logger.write()

		# Parse command-line arguments.
		if len(arguments) >= 2:
			raise CommandError("\"KioskSetup.py\" ?step\nWhere 'step' is an optional resume step from the log.")
		resume = 0
		if len(arguments) == 1:
			resume = int(arguments[0])

		# This script is launched by a systemd service, so we need to eradicate it and all traces of it (once only).
		if resume == 0:
			result = invoke_text("systemctl disable KioskSetup")
			if os.path.isfile("/usr/lib/systemd/system/KioskSetup.service"):
				os.unlink("/usr/lib/systemd/system/KioskSetup.service")
			if result.status != 0:
				raise KioskError("Unable to disable the KioskSetup service")

		# Load settings generated by KioskForge on the desktop machine.
		kiosk = Kiosk(self.version)
		kiosk.load_safe(logger, origin + os.sep + "KioskForge.kiosk")

		# Build the script to execute.
		logger.write("Forging kiosk (takes between 10 and 30 minutes):")
		logger.write()
		script = Script(logger, resume)

		# Ensure NTP is enabled (already active in Ubuntu Server 24.04+).
		script += ExternalAction("Enabling Network Time Protocol (NTP).", "timedatectl set-ntp on")

		# Set environment variable to stop dpkg from running interactively.
		os.environ["DEBIAN_FRONTEND"] = "noninteractive"

		# Set environment variable on every boot to stop dpkg from running interactively.
		lines  = TextBuilder()
		lines += 'DEBIAN_FRONTEND="noninteractive"'
		script += AppendTextAction(
			"Configuring 'apt', 'dpkg', etc. to never interact with the user.",
			"/etc/environment",
			lines.text
		)
		del lines

		# Disable interactive activity from needrestart (otherwise it could get stuck in a TUI dialogue during an upgrade).
		script += ReplaceTextAction(
			"Configuring 'needrestart' to NOT use interactive dialogues during upgrades.",
			"/etc/needrestart/needrestart.conf",
			"$nrconf{restart} = 'i';",
			"$nrconf{restart} = 'a';"
		)

		# Configure 'apt' to never update package indices on its own.  We do this in a cron job below.
		script += ReplaceTextAction(
			"Configuring 'apt' to never update package indices on its own.",
			"/etc/apt/apt.conf.d/10periodic",
			'APT::Periodic::Update-Package-Lists "1";',
			'APT::Periodic::Update-Package-Lists "0";'
		)

		# Create file instructing 'apt' to never replace existing local configuration files during upgrades.
		lines  = TextBuilder()
		lines += '// Instruct dpkg to never replace existing local configuration files during upgrades.'
		lines += '// See https://raphaelhertzog.com/2010/09/21/debian-conffile-configuration-file-managed-by-dpkg/'
		lines += 'Dpkg::Options {'
		lines += '    "--force-confdef";'
		lines += '    "--force-confold";'
		lines += '}'
		script += CreateTextWithUserAndModeAction(
			"Creating 'apt' configuration file to keep existing configuration files during upgrades.",
			"/etc/apt/apt.conf.d/00local",
			"root",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)
		del lines

		# Append lines to .bashrc to create 'kiosklog' function used for quickly viewing the Kiosk*.py log entries.
		lines  = TextBuilder()
		lines += ""
		lines += "# Function that displays all syslog entries made by Kiosk*.py."
		lines += "kiosklog() {"
		lines += "\t# Use 'kiosklog -p 3' only see kiosk-related errors, instead of all messages."
		lines += "\tjournalctl -o short-iso $* | grep -F Kiosk | grep -Fv systemd\\["
		lines += "}"
		script += AppendTextAction(
			"Creating 'kiosklog' Bash function for easier debugging and status discovery.",
			f"{os.path.dirname(origin)}/.bashrc",
			lines.text
		)

		if kiosk.wifi_name.data and kiosk.wifi_boost.data:
			# Disable Wi-Fi power-saving mode, something that can cause Wi-Fi instability and slow down the Wi-Fi network a lot.
			# NOTE: I initially did this via a @reboot cron job, but it didn't work as cron was run too early.
			# NOTE: Package 'iw' is needed to disable power-saving mode on a specific network card.
			# NOTE: Package 'net-tools' contains the 'netstat' utility.
			script += InstallPackagesAction("Installing network tools to disable Wi-Fi power-saving mode.", ["iw", "net-tools"])

		# Install and configure SSH server to require a key and disallow root access if a public key is specified.
		#...Install OpenSSH server.
		script += InstallPackagesAction("Installing OpenSSH server.", ["openssh-server"])

		# ...Install SSH public key, if any, so that the user can SSH into the box in case of errors or other issues.
		if kiosk.ssh_key.data:
			script += AppendTextAction(
				"Installing public SSH key in user's home directory.",
				f"{os.path.dirname(origin)}/.ssh/authorized_keys",
				kiosk.ssh_key.data + "\n"
			)
			#...Disable root login, if not already disabled.
			script += ReplaceTextAction(
				"Disabling root login using SSH.",
				"/etc/ssh/sshd_config",
				"#PermitRootLogin prohibit-password",
				"PermitRootLogin no"
			)
			#...Disable password-only authentication if not already disabled.
			script += ReplaceTextAction(
				"Disabling password authentication (requiring private SSH key to log in).",
				"/etc/ssh/sshd_config",
				"#PasswordAuthentication yes",
				"PasswordAuthentication no"
			)

		#...Disable empty passwords (probably superflous, but it doesn't hurt).
		script += ReplaceTextAction(
			"Disabling empty SSH password login.",
			"/etc/ssh/sshd_config",
			"#PermitEmptyPasswords no",
			"PermitEmptyPasswords no"
		)

		# Uninstall package unattended-upgrades as I couldn't get it to work even after spending many hours on it.
		# NOTE: Remove unattended-upgrades early on as it likes to interfere with APT and the package manager.
		script += PurgePackagesAction("Purging package unattended-upgrades.", ["unattended-upgrades"])
		script += RemoveFolderAction("Removing remains of package unattended-upgrades.", "/var/log/unattended-upgrades")

		# Install US English and user-specified locales (purge all others).
		script += ExternalAction("Configuring system locales.", f"locale-gen --purge en_US.UTF-8 {kiosk.locale.data}")

		# Configure system to use user-specified locale (keep messages and error texts in US English).
		script += ExternalAction("Setting system locale.", f"update-locale LANG={kiosk.locale.data} LC_MESSAGES=en_US.UTF-8")

		# Set timezone to use user's choice.
		script += ExternalAction("Setting timezone.", f"timedatectl set-timezone {kiosk.timezone.data}")

		# Configure and activate firewall, allowing only SSH at port 22.
		script += ExternalAction("Disabling firewall log.", "ufw logging off")
		script += ExternalAction("Allowing SSH through firewall.", "ufw allow ssh")
		script += ExternalAction("Enabling firewall.", "ufw --force enable")

		# Remove some packages that we don't need in kiosk mode to save some memory.
		script += PurgePackagesAction("Purging unwanted packages.", ["modemmanager", "open-vm-tools", "needrestart"])

		# Update and upgrade the system, including snaps (everything).
		script += ExternalAction("Upgrading all snaps.", "snap refresh")

		# Instruct snap to never upgrade by itself (we upgrade in the 'KioskUpdate.py' script, which follows 'upgrade_time=HH:MM').
		script += ExternalAction("Disabling automatic upgrades of snaps.", "snap refresh --hold")

		# NOTE: Use 'AptAction' to automatically wait for apt's lock to be released if in use.
		script += AptAction("Updating system package indices.", "apt-get update")
		script += AptAction("Upgrading all installed packages.", "apt-get dist-upgrade -y")

		# Install audio system (Pipewire) only if explicitly enabled.
		if kiosk.sound_card.data != "none":
			# NOTE: Uncommenting '#hdmi_drive=2' in 'config.txt' MAY be necessary in some cases, albeit it works without for me.
			# Install Pipewire AND pulseaudio-utils as the script 'KioskStart.py' uses 'pactl' from the latter package.
			script += InstallPackagesAction("Installing Pipewire audio subsystem.", ["pipewire", "pulseaudio-utils"])

		# Configure the kiosk according to its type.
		if kiosk.type.data == "web-wayland":
			# Install Ubuntu Frame (Wayland-based) instead of X11.
			script += ExternalAction("Installing Ubuntu Frame for Wayland.", "snap install ubuntu-frame")
			script += ExternalAction("Configuring Ubuntu Frame for kiosk use.", "snap set ubuntu-frame daemon=true")

			# Install Chromium as we use its kiosk mode (also installs CUPS, see below).
			script += ExternalAction("Installing Chromium web browser.", "snap install chromium")
			script += ExternalAction("Configuring Chromium for Ubuntu Frame.", "snap set chromium daemon=true")
			script += ExternalAction("Connecting Chromium with Wayland.", "snap connect chromium:wayland")

			# NOTE: The line below appears to be irrelevant for browsing local files in the HOME folder.
			# script += ExternalAction("Making Chromium able to access to local files.", "snap connect chromium:removable-media")

			script += ExternalAction("Configuring starting page in Chromium.", f"sudo snap set chromium url={kiosk.command.data}")

			# ...Stop and remove the Common Unix Printing Server (cups) as it is a security risk that we don't need in a kiosk.
			script += ExternalAction(
				"Purging Common Unix Printing System (cups) installed automatically with Chromium.",
				"snap remove --purge cups"
			)

			# NOTE: Do NOT remove the 'gnome-42-2204' snap as this makes Chromium fail silently!
			# NOTE: Do NOT remove the 'gtk-common-themes' snap as this makes Chromium crash and refuse to restart!

			# Write almost empty Chromium preferences file to disable translate feature.
			lines = TextBuilder()
			lines += '{"translate":{"enabled":false}}'
			script += CreateTextWithUserAndModeAction(
				"Disabling Translate feature in Chromium web browser.",
				f"{os.path.dirname(origin)}/snap/chromium/common/chromium/Default/Preferences",
				kiosk.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines

			# Tell Wayland to rotate the screen as per the kiosk configuration.
			if kiosk.screen_rotation.data != "none":
				orientation = WAYLAND_ORIENTATION[kiosk.screen_rotation.data]
				script += ExternalAction(
					"Configure Wayland to rotate the screen.",
					'snap set ubuntu-frame display="' + WAYLAND_CONFIGURATION.format(orientation=orientation) + '"'
				)
				del orientation
		elif kiosk.type.data in ["x11", "web"]:
			# Install X Windows server and the OpenBox window manager.
			script += InstallPackagesNoRecommendsAction(
				"Installing X Windows and OpenBox window manager.",
				# NOTE: First element used to be 'xserver-xorg', then '"xserver-xorg-core', and no 'xorg'.
				# NOTE: Changed because of unmet dependencies; i.e. apt suddenly wouldn't install it anymore.
				["xserver-xorg", "x11-xserver-utils", "xinit", "openbox", "xdg-utils"]
			)

			# Ubuntu Server 24.04.x on Raspberry Pi 5 needs an obscure fix for X11 to discover its GPU and screens.
			if kiosk.device.data == "pi5":
				script += InstallPackagesNoRecommendsAction("Installing Rasperry Pi System Configuration tool", ["raspi-config"])
				script += ExternalAction(
					"Downloading X11 graphics driver for Pi5",
					"wget -q https://archive.raspberrypi.org/debian/pool/main/g/gldriver-test/gldriver-test_0.15_all.deb"
				)
				script += AptAction("Installing X11 graphics driver for Pi5", "apt-get install -y ./gldriver-test_0.15_all.deb")
				script += ExternalAction("Removing downloaded graphics driver for Pi5", "rm -f gldriver-test_0.15_all.deb")

				# Create X11 configuration file to use Pi5 graphics driver.
				lines  = TextBuilder()
				lines += 'Section "OutputClass"'
				lines += '    Identifier "vc4"'
				lines += '    MatchDriver "vc4"'
				lines += '    Driver "modesetting"'
				lines += '    Option "PrimaryGPU" "true"'
				lines += 'EndSection'
				script += CreateTextWithUserAndModeAction(
					"Creating X11 configuration file to use Pi5 graphics driver",
					"/etc/X11/xorg.conf.d/99-v3d.conf",
					"root",
					stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
					lines.text
				)
				del lines

			# Create X11 configuration file to rotate the TOUCH panel, not the display itself (see KioskOpenbox.py).
			# NOTE: This file is always created, when the screen is rotated, but has no effect on non-touch displays.
			# NOTE: I'd love to create this file in 'KioskStart.py', but it runs as the created user, not as root.
			if kiosk.screen_rotation.data != "none":
				# Write '/etc/X11/xorg.conf.d/99-kiosk-set-touch-rotation.conf' to make X11 rotate the touch panel itself.
				# Source: https://gist.github.com/autofyrsto/6daa5d41c7f742dd16c46c903ba15c8f
				lines  = TextBuilder()
				lines += 'Section "InputClass"'
				lines += '\tIdentifier "Coordinate Transformation Matrix"'
				lines += '\tMatchIsTouchscreen "on"'
				lines += '\tMatchDevicePath "/dev/input/event*"'
				lines += '\tMatchDriver "libinput"'
				lines += f'\tOption "CalibrationMatrix" "{MATRICES[kiosk.screen_rotation.data]}"'
				lines += 'EndSection'
				script += CreateTextWithUserAndModeAction(
					"Creating X11 configuration file to rotate touch panel (if any).",
					"/etc/X11/xorg.conf.d/99-kiosk-set-touch-rotation.conf",
					"root",
					stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
					lines.text
				)
				del lines

			# Create fresh OpenBox autostart script (overwrite the existing autostart script, if any).
			# NOTE: OpenBox does not seem to honor the shebang (#!) as OpenBox always uses the 'dash' shell.
			# NOTE: For this reason, we start the Python script indirectly through an-hoc Dash script.
			lines  = TextBuilder()
			lines += "#!/usr/bin/dash"
			lines += f"{origin}/KioskOpenbox.py"
			script += CreateTextWithUserAndModeAction(
				"Creating OpenBox startup script.",
				f"{os.path.dirname(origin)}/.config/openbox/autostart",
				kiosk.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR,
				lines.text
			)
			del lines

			if kiosk.type.data == "web":
				# Install Chromium as we use its kiosk mode (also installs CUPS, see below).
				script += ExternalAction("Installing Chromium web browser.", "snap install chromium")

				# ...Stop and remove the Common Unix Printing Server (cups) as it is a security risk that we don't need in a kiosk.
				script += ExternalAction(
					"Purging Common Unix Printing System (cups) installed automatically with Chromium.",
					"snap remove --purge cups"
				)

				# NOTE: Do NOT remove the 'gnome-42-2204' snap as this makes Chromium fail silently!
				# NOTE: Do NOT remove the 'gtk-common-themes' snap as this makes Chromium crash and refuse to restart!

				# Write almost empty Chromium preferences file to disable translate.
				lines = TextBuilder()
				lines += '{"translate":{"enabled":false}}'
				script += CreateTextWithUserAndModeAction(
					"Disabling Translate feature in Chromium web browser.",
					f"{os.path.dirname(origin)}/snap/chromium/common/chromium/Default/Preferences",
					kiosk.user_name.data,
					stat.S_IRUSR | stat.S_IWUSR,
					lines.text
				)
				del lines

				# Install 'xprintidle' used to detect X idle periods and restart the browser (required even if idle_timeout == 0).
				script += InstallPackagesNoRecommendsAction(
					"Installing 'xprintidle' used to restart browser whenever idle timeout expires.",
					["xprintidle"]
				)
			elif kiosk.type.data == "x11":
				raise InternalError("The type=x11 option is not supported yet")
		elif kiosk.type.data == "cli":
			# Currently nothing to do, KioskStart.py handles this case completely.
			pass
		else:
			raise KioskError(f"Unknown kiosk type: {kiosk.type.data}")

		# If the user_packages option is specified, install the extra package(s).
		if kiosk.user_packages.data:
			script += InstallPackagesAction("Installing user-specified (custom) packages", shlex.split(kiosk.user_packages.data))

		# Create swap file in case the system gets low on memory.
		if kiosk.swap_size.data > 0:
			script += ExternalAction("Allocating swap file.", f"fallocate -l {kiosk.swap_size.data}G /swapfile",)
			script += ExternalAction("Setting permissions on new swap file.", "chmod 600 /swapfile")
			script += ExternalAction("Formatting swap file.", "mkswap /swapfile")
			script += AppendTextAction(
				"Creating '/etc/fstab' entry for the new swap file.",
				"/etc/fstab",
				"/swapfile\tnone\tswap\tsw\t0\t0"
			)

		if kiosk.type.data == "web-wayland":
			# If using Wayland.

			# Create systemd service to allocate a session for the kiosk user.
			lines  = TextBuilder()
			lines += "[Service]"
			lines += "# This is what causes a user session to be allocated for the kiosk user."
			lines += f"User={kiosk.user_name.data}"
			lines += "PAMName=login"
			lines += "TTYPath=/dev/tty1"
			lines += "ExecStart=/usr/bin/systemctl --user start --wait user-session.target"
			script += CreateTextWithUserAndModeAction(
				"Creating global systemd script to allocate a session for the user.",
				"/usr/lib/systemd/system/user-session.service",
				"root",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Enabling global systemd user-session service.", "systemctl enable user-session.service")

			# Create systemd service to run Ubuntu Frame under the kiosk user.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge (Ubuntu Frame launcher)"
			lines += "Before=xdg-desktop-autostart.target"
			lines += "BindsTo=graphical-session.target"
			lines += "[Service]"
			lines += "ExecStartPre=/usr/bin/dbus-update-activation-environment --systemd WAYLAND_DISPLAY=wayland-0"
			lines += "ExecStart=/snap/bin/ubuntu-frame"
			script += CreateTextWithUserAndModeAction(
				"Creating user-specific systemd service to launch Ubuntu Frame.",
				f"{os.path.dirname(origin)}/.config/systemd/user/ubuntu-frame.service",
				kiosk.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Enabling custom systemd Ubuntu Frame service.", "systemctl enable ubuntu-frame.service")

			# Create systemd service to launch Chromium.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge (Chromium launcher)"
			lines += "After=ubuntu-frame.service"
			lines += "[Service]"
			lines += f"ExecStart=/snap/bin/chromium --kiosk '{kiosk.command.data}'"
			script += CreateTextWithUserAndModeAction(
				"Creating user-specific systemd service to launch Chromium.",
				f"{os.path.dirname(origin)}/.config/systemd/user/chromium.service",
				kiosk.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Enabling custom systemd Chromium service.", "systemctl enable chromium.service")

			# Start all of the above in one operation.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge (Chromium launcher)"
			lines += "Wants=ubuntu-frame.service chromium.service"
			script += CreateTextWithUserAndModeAction(
				"Creating user-specific systemd service to launch Chromium.",
				f"{os.path.dirname(origin)}/.config/systemd/user/user-session.target",
				kiosk.user_name.data,
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Start Wayland and then Chromium when booting.", "systemctl add-wants graphical.target user-session.service")
		else:
			# Append lines to .bash_profile to execute the startup script (only if not already started once).
			lines  = TextBuilder()
			lines += ""
			lines += "# Execute the startup script 'KioskStart.py' once only (presumably for the automatically logged in user)."
			lines += "if [ ! -f /tmp/kiosk_started ]; then"
			lines += "\ttouch /tmp/kiosk_started"
			lines += f"\t{origin}/KioskForge/KioskStart.py"
			lines += "\trm -f /tmp/kiosk_started"
			# Clear the screen to hide any private information such as the LAN IP.
			lines += "\tclear"
			# Sleep until the system is rebooted shortly just to disallow kiosk users from entering commands.
			lines += "sleep 1d"
			# NOTE: Don't logout as 'systemd' will respawn the login process right away, causing havoc as it restarts X11, etc.
			# NOTE: Not logging out leads to a "zombie" shell session, but it dies very soon when 'KioskUpdate.py' reboots.
			lines += "fi"
			script += AppendTextAction(
				"Appending lines to ~/.bash_profile to start up the kiosk.",
				f"{os.path.dirname(origin)}/.bash_profile",
				lines.text
			)
			del lines

			# Set up automatic login for the named user.
			lines  = TextBuilder()
			lines += "[Service]"
			lines += "ExecStart="
			lines += f"ExecStart=-/sbin/agetty --noissue --autologin {kiosk.user_name.data} %I $TERM"
			lines += "Type=simple"
			script += CreateTextWithUserAndModeAction(
				"Creating systemd auto-login override.",
				"/etc/systemd/system/getty@tty1.service.d/override.conf",
				"root",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
#		else:
#			# NOTE: I never did manage to get the systemd service to even start up (I've stopped playing with it for now).
#			lines  = TextBuilder()
#			lines += "[Unit]"
#			lines += "Description=KioskForge (Kiosk launcher)"
#			lines += "After=network-online.target"
#			lines += "After=cloud-init.target"
#			lines += "After=multi-user.target"
#			lines += ""
#			lines += "[Service]"
#			lines += f"User={kiosk.user_name.data}"
#			lines += f"Group={kiosk.user_name.data}"
#			lines += "Type=simple"
#			lines += "ExecStart="
#			lines += f"ExecStart={origin}/KioskStart.py"
#			lines += "StandardOutput=tty"
#			lines += "StandardError=tty"
#			lines += ""
#			lines += "[Install]"
#			lines += "WantedBy=cloud-init.target"
#			script += CreateTextWithUserAndModeAction(
#				"Creating systemd kiosk service.",
#				"/usr/lib/systemd/system/kiosk.service",
#				"root",
#				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
#				lines.text
#			)
#
#			# Enable the new systemd unit.
#			script += ExternalAction("Enabling systemd kiosk service", "systemctl enable kiosk")

		# Change ownership of all files in the user's home dir to that of the user as we create a few files as sudo (root).
		script += ExternalAction(
			"Setting ownership of all files in user's home directory to that user.",
			f"chown -R {kiosk.user_name.data}:{kiosk.user_name.data} {os.path.dirname(origin)}"
		)

		# Free disk space by purging unused packages.
		script += AptAction("Purging all unused packages to free disk space.", "apt-get autoremove --purge -y")

		# Free disk space by cleaning the apt cache.
		script += AptAction("Cleaning package cache.", "apt-get clean")

		# Empty snap cache.
		script += ExternalAction("Purging snap cache to free disk space", "rm -fr /var/lib/snapd/cache/*")

		# Create cron job to compact logs, update, upgrade, clean, and reboot the system every day at a given time.
		if kiosk.upgrade_time.data != "":
			lines  = TextBuilder()
			lines += "# Cron job to upgrade, clean, and reboot the system every day."
			lines += f'{kiosk.upgrade_time.data[3:5]} {kiosk.upgrade_time.data[0:2]} * * *\troot\t{origin}/KioskUpdate.py'
			script += CreateTextAction(
				"Creating cron job to upgrade system once a day at the configured time.",
				"/etc/cron.d/kiosk-upgrade-system",
				lines.text
			)
			del lines

		# Create cron job to power off the system at a given time (only usable when the kiosk is manually turned on again).
		if kiosk.poweroff_time.data != "":
			lines  = TextBuilder()
			lines += "# Cron job to shut down the kiosk machine nicely every day."
			lines += f"{kiosk.poweroff_time.data[3:5]} {kiosk.poweroff_time.data[0:2]} * * *\troot\tpoweroff"
			script += CreateTextAction(
				"Creating cron job to power off the system every day at the configured time.",
				"/etc/cron.d/kiosk-power-off",
				lines.text
			)
			del lines

		# Synchronize all changes to disk (may take a while on microSD cards).
		script += ExternalAction(
			"Flushing disk buffers before rebooting (may take a while when using slow media).",
			"sync"
		)

		# Execute the script.
		result = script.execute()
		if result.status != 0:
			raise KioskError(result.output)

		# NOTE: The reboot takes place immediately, control never returns from the 'execute()' method below!
		logger.write("*** SUCCESS - REBOOTING SYSTEM INTO KIOSK MODE")
		ExternalAction("Rebooting system NOW!", "reboot").execute()


if __name__ == "__main__":
	sys.exit(KioskSetup().main(sys.argv))
