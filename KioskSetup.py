#!/usr/bin/env python3
#**********************************************************************************************************************************
# BSD 3-Clause License for KioskForge - https://kioskforge.org:
#
# Copyright © 2024-2026 The KioskForge Team.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following
# conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#**********************************************************************************************************************************

# This script is responsible for setting up the Linux kiosk machine (forging it) according to the user's kiosk configuration.

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import cast, List

import os
import shlex
import stat
import sys
import time

from kiosklib.actions import AppendTextAction, AptAction, CreateTextAction, CreateTextWithUserAndModeAction, CustomAction
from kiosklib.actions import ExternalAction, InstallFontsAction, InstallPackagesAction, InstallPackagesNoRecommendsAction
from kiosklib.actions import PurgePackagesAction, RemoveFolderAction, ReplaceTextAction
from kiosklib.builder import TextBuilder
from kiosklib.detect import pi_board_get
from kiosklib.driver import KioskDriver
from kiosklib.errors import KioskError
from kiosklib.fstab import Filesystems, Mount
from kiosklib.invoke import invoke_text_safe
from kiosklib.kiosk import Kiosk
from kiosklib.logger import Logger
from kiosklib.network import internet_active, lan_broadcast_address, lan_address, wait_for_internet_active, wifi_boost
from kiosklib.script import Script
from kiosklib.various import custom_fonts_get, screen_clear


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
	"""Defines the 'KioskSetup' class, which configures a supported Ubuntu Server system to become a web kiosk."""

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
		# pylint: disable-next=no-member
		if os.geteuid() != 0:		# pyrefly: ignore[missing-attribute]
			raise KioskError("You must be root to run this script")

		# Check that we have got an active, usable internet connection, otherwise wait indefinitely for it come up.
		# NOTE: We wait on ports.ubuntu.com to be available as we need it for virtually all 'apt' operations below.
		if not internet_active("ports.ubuntu.com"):
			logger.write("*** NETWORK DOWN: Waiting indefinitely for the kiosk to come online")
			logger.write()
			wait_for_internet_active("ports.ubuntu.com")

		# Display LAN IP - not everybody has access to the router in charge of assigning a LAN IP via DHCP.
		logger.write("*** LAN IP: " + lan_address())
		logger.write()

		# This script is launched by a systemd service, so we need to remove the service (to avoid starting on every boot).
		# ...Disable the system service.
		invoke_text_safe("systemctl disable KioskSetup")

		# ...Remove the .service file itself.
		invoke_text_safe("rm -f /etc/systemd/system/KioskSetup.service")

		# ...Remove the artifact left over from installing KioskForge and the user application using 'kiosk_booter.py'.
		# NOTE: The KioskForge.old folder is removed after the initial installation to avoid confusing the kiosk owner.
		invoke_text_safe("rm -fr /home/kiosk/KioskForge.old")

		# Load settings generated by KioskForge on the desktop machine.
		kiosk = Kiosk(self.version)
		kiosk.load_safe(logger, origin + os.sep + "KioskForge.kiosk")

		# Notify the KioskForge user that the forge process has begun.
		logger.write("Forging kiosk (takes a while depending on media speed and kiosk board type):")
		logger.write()

		# Set environment variable to stop dpkg from running interactively.
		# TODO: Does this have any effect at all or does the new environment need to be passed to every action?
		os.environ["DEBIAN_FRONTEND"] = "noninteractive"

		# Build the script to execute.
		script = Script(logger)

		script += CustomAction("Preparing system for forge process:", lambda: None)

		# Stop the unattended-packages package as it causes endless problems for people using apt programmatically.
		script += ExternalAction("... Stopping service unattended-upgrades.", "systemctl stop unattended-upgrades")

		# Instruct snap to never upgrade by itself (we upgrade in the 'KioskUpdate.py' script, which honors 'upgrade_time=HH:MM').
		# NOTE: Putting all AUTOMATIC snap upgrades on hold does NOT prevent installing new snaps: Tested and verified.
		script += ExternalAction("... Disabling automatic upgrades of snaps.", "snap refresh --hold")

		# Set environment variable on every boot to stop dpkg from running interactively.
		lines  = TextBuilder()
		lines += 'DEBIAN_FRONTEND="noninteractive"'
		script += AppendTextAction(
			"... Configuring 'apt', etc. to never interact with the user.",
			"/etc/environment",
			lines.text
		)
		del lines

		# Disable interactive activity from needrestart (otherwise it could get stuck in a TUI dialogue during an upgrade).
		script += ReplaceTextAction(
			"... Configuring 'needrestart' to never interact with the user.",
			"/etc/needrestart/needrestart.conf",
			"$nrconf{restart} = 'i';",
			"$nrconf{restart} = 'a';"
		)

		# Configure 'apt' to never update package lists on its own.  We do this in a cron job below.
		script += ReplaceTextAction(
			"... Configuring 'apt' to never update package lists automatically.",
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
			"... Instructing 'dpkg' to keep existing configuration files on upgrades.",
			"/etc/apt/apt.conf.d/00local",
			"root",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)
		del lines

		# Create ~kiosk/.bash_aliases to add the 'kiosklog' command used for quickly viewing the Kiosk*.py log entries.
		lines  = TextBuilder()
		lines += "#!/usr/bin/bash"
		lines += "# Function that displays all syslog entries made by Kiosk*.py."
		lines += "kiosklog() {"
		lines += "\t# Use 'kiosklog -p 3' only see kiosk-related errors, instead of all messages."
		lines += "\tjournalctl -o short-iso $* | grep -F Kiosk | grep -Fv systemd\\["
		lines += "}"
		script += CreateTextWithUserAndModeAction(
			"Creating 'kiosklog' command for the kiosk user to enable status discovery.",
			"/home/kiosk/.bash_aliases",
			"kiosk",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)

		# Create '~kiosk/.hushlogin' to silence the Ubuntu login Message of the Day (MOTD) scripts.
		# NOTE: To see the MOTD system status info, use the Ubuntu command 'landscape-sysinfo'.
		script += CreateTextWithUserAndModeAction(
			"Creating .hushlogin to enable silent logins.",
			"/home/kiosk/.hushlogin",
			"kiosk",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			""
		)

		# Uninstall package unattended-upgrades as I couldn't get it to work even after spending many hours on it.
		# NOTE: Remove unattended-upgrades very early on as it likes to interfere with APT and the package manager.
		script += PurgePackagesAction("Purging package unattended-upgrades.", ["unattended-upgrades"])
		script += RemoveFolderAction("Removing remains of package unattended-upgrades.", "/var/log/unattended-upgrades")

		# Install US English and user-specified locales (purge all others).
		script += CustomAction("Configuring system locale:", lambda: None)
		script += ExternalAction("... Generating system locales.", f"locale-gen --purge en_US.UTF-8 {kiosk.locale.data}")
		# Configure system to use user-specified locale (keep messages and error texts in US English).
		script += ExternalAction("... Setting system locale.", f"update-locale LANG={kiosk.locale.data} LC_MESSAGES=en_US.UTF-8")

		# Update package lists to avoid getting all sorts of bizarre HTTP errors due to outdated package lists.
		# NOTE: If this step is left out, you risk getting tons of HTTP 404 errors when trying to install, say, the audio packages.
		script += AptAction("Updating package lists before installing anything.", "apt-get update")

		# Configure and activate firewall, allowing only SSH at port 22.
		script += CustomAction("Configuring firewall:", lambda: None)
		script += ExternalAction("... Disabling firewall log.", "ufw logging off")
		script += ExternalAction("... Allowing SSH through firewall.", "ufw allow ssh")
		script += ExternalAction("... Enabling firewall.", "ufw --force enable")

		# ...Install SSH public key, if any, so that the user can SSH into the box as 'kiosk' in case of errors or other issues.
		if kiosk.ssh_key_public.data:
			script += CustomAction("Configuring Secure Shell (ssh):", lambda: None)

			# Install and configure SSH server to require a key and disallow root access if a public key is specified.
			# ...Install OpenSSH server.
			script += InstallPackagesAction("... Installing OpenSSH server.", ["openssh-server"])

			# ...Limit root login to key authentication only if the kiosk is managed (the default is: no login).
			if not kiosk.managed.data:
				script += ReplaceTextAction(
					"... Disabling root login completely.",
					"/etc/ssh/sshd_config",
					"#PermitRootLogin prohibit-password",
					"PermitRootLogin no"
				)

			#...Disable password-only authentication if not already disabled.
			script += ReplaceTextAction(
				"... Disabling SSH password authentication altogether.",
				"/etc/ssh/sshd_config",
				"#PasswordAuthentication yes",
				"PasswordAuthentication no"
			)

			#...Disable empty passwords (probably redundant, but it doesn't hurt).
			script += ReplaceTextAction(
				"... Disabling empty SSH password login.",
				"/etc/ssh/sshd_config",
				"#PermitEmptyPasswords no",
				"PermitEmptyPasswords no"
			)

			# Install public SSH key for the 'kiosk' user.
			script += CreateTextWithUserAndModeAction(
				"... Installing public SSH key for the kiosk user.",
				"/home/kiosk/.ssh/authorized_keys",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR,
				kiosk.ssh_key_public.data + os.linesep
			)

			if kiosk.managed.data:
				# Install public SSH key in /root/.ssh to enable passwordless root logins for KioskForge management operations.
				script += CreateTextWithUserAndModeAction(
					"... Installing public SSH key for root user.",
					"/root/.ssh/authorized_keys",
					"root",
					stat.S_IRUSR | stat.S_IWUSR,
					kiosk.ssh_key_public.data + os.linesep
				)

		# Create udev rule to grant the kiosk user access to the Raspberry Pi 4B and 5 GPIO chips (the various headers).
		# NOTE: The kiosk user has already been added to the 'gpio' group by the CloudInit part set up by KioskForge.py.
		# NOTE: https://oneuptime.com/blog/post/2026-03-02-how-to-configure-gpio-access-on-ubuntu-for-raspberry-pi/view
		lines  = TextBuilder()
		lines += ' # Allow members of the gpio group to access GPIO character devices.'
		lines += 'SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"'
		lines += ''
		lines += '# Also allow access to the GPIO export interface (for legacy support).'
		lines += 'SUBSYSTEM=="gpio", GROUP="gpio", MODE="0660"'
		script += CreateTextWithUserAndModeAction(
			"Enabling kiosk access to the various GPIO headers.",
			"/etc/udev/rules.d/99-gpio.rules",
			"root",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)
		del lines

		if kiosk.wifi_name.data and kiosk.wifi_boost.data:
			# Disable Wi-Fi power-saving mode, something that can cause Wi-Fi instability and slow down the Wi-Fi network a lot.
			# NOTE: I initially did this via a @reboot cron job, but it didn't work as cron was run too early.
			# NOTE: Package 'iw' is needed to disable power-saving mode on a specific network card.
			# NOTE: Package 'net-tools' contains the 'netstat' utility.
			script += CustomAction("Enabling Wi-Fi Boost:", lambda: None)
			script += InstallPackagesAction("... Installing tools to disable Wi-Fi power-saving mode.", ["iw", "net-tools"])
			script += CustomAction("... Disabling Wi-Fi power-saving mode.", lambda: wifi_boost(True))

		# Install PipeWire audio system only if explicitly enabled.
		if kiosk.sound_card.data != "none":
			# NOTE: Uncommenting '#hdmi_drive=2' in 'config.txt' MAY be necessary in some cases, albeit it works without for me.

			script += CustomAction("Configuring audio subsystem:", lambda: None)

			# Install PipeWire audio subsystem, which is configured in 'KioskStart.py' (all attempts of configuring PipeWire
			# with 'sudo', 'os.seteuid()', and so on in 'KioskConfig.py' failed).
			# NOTE: "pulseaudio-utils" is required because 'wpctl' is unusable for scripting purposes so we install 'pactl'.
			script += InstallPackagesAction("... Installing PipeWire packages.", ["pipewire-audio", "pulseaudio-utils"])

		#************************************ Kiosk Browser Service **************************************************************
		if kiosk.managed.data:
			script += CustomAction("Configuring kiosk as manageable by KioskForge:", lambda: None)

			# Allow UDP broadcasts through the firewall.
			# NOTE: /16 means that the subnets of the form xxx.yyy.???.??? can contact the kiosk broadcast server.
			# TODO: Redo this to be sensible and flexible.  The current approach is sort of proof-of-concept hack.
			subnet = lan_broadcast_address() + "/16"
			script += ExternalAction(
				"... Opening firewall port to allow broadcast messages from LAN (/16) subnets.",
				f"ufw allow in proto udp to {subnet} from {subnet}"
			)
			del subnet

			# Create '~root/.hushlogin' to silence the Ubuntu login Message of the Day (MOTD) scripts.
			# NOTE: To see the MOTD system status info, use the Ubuntu command 'landscape-sysinfo'.
			script += CreateTextWithUserAndModeAction(
				"... Creating ~root/.hushlogin to enable silent logins for management purposes.",
				"/root/.hushlogin",
				"root",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP,
				""
			)

			# Run 'KioskDiscoveryServer.py' on every boot by creating a suitable 'systemd' service to start it.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge: LAN Broadcast Identity Server"
			lines += "After=network-online.target"
			lines += "Before=multi-user.target"
			lines += ""
			lines += "[Service]"
			lines += "Type=simple"
			lines += "Restart=on-failure"
			lines += "ExecStart="
			lines += "ExecStart=/home/kiosk/KioskForge/KioskDiscoveryServer.py"
			lines += ""
			lines += "[Install]"
			lines += "WantedBy=multi-user.target"
			script += CreateTextWithUserAndModeAction(
				"... Creating systemd service to start LAN broadcast server.",
				"/etc/systemd/system/kiosk-broadcast-server.service",
				"root",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
				lines.text
			)
			del lines

			# Enable AND start 'kiosk-server' systemd service so that it runs immediately and also on every future boot.
			script += ExternalAction(
				"... Enabling and starting systemd kiosk-broadcast-server service.",
				"systemctl enable --now kiosk-broadcast-server.service"
			)

		# Remove some packages that we don't need in kiosk mode to save a tiny bit of memory.
		script += PurgePackagesAction("Purging unwanted packages.", ["modemmanager", "open-vm-tools", "needrestart"])

		# Clean, Update, and upgrade the system (including snaps)
		script += ExternalAction("Upgrading system (packages and snaps).", "/home/kiosk/KioskForge/KioskUpdate.py --initial")

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

			# Install Chromium as we use its kiosk mode (also installs CUPS, see below).
			script += ExternalAction("Installing Chromium web browser.", "snap install chromium")

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
				"/home/kiosk/snap/chromium/common/chromium/Default/Preferences",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines

			script += ExternalAction("Configuring starting page in Chromium.", f"snap set chromium url={kiosk.command.data}")

			# Tell Wayland to rotate the screen as per the kiosk configuration.
			if kiosk.screen_rotation.data != "none":
				orientation = WAYLAND_ORIENTATION[kiosk.screen_rotation.data]
				script += ExternalAction(
					"Configure Wayland to rotate the screen.",
					'snap set ubuntu-frame display="' + WAYLAND_CONFIGURATION.format(orientation=orientation) + '"'
				)
				del orientation
		elif kiosk.type.data in ["x11", "web"]:
			script += CustomAction("Installing X11 with Openbox window manager:", lambda: None)

			# Install X Windows server and the Openbox window manager.
			script += InstallPackagesNoRecommendsAction(
				"... Installing X Windows and Openbox window manager.",
				["xserver-xorg", "x11-xserver-utils", "xinit", "openbox", "xdg-utils"]
			)

			# Ubuntu Server 24.04.x on Raspberry Pi 5 needs an obscure fix for X11 to discover its GPU and screens.
			# Source: https://forums.raspberrypi.com/viewtopic.php?t=358853
			if pi_board_get() == "Pi 5":
				script += CustomAction("Installing Raspberry Pi 5 graphics drivers:", lambda: None)
				script += InstallPackagesNoRecommendsAction("... Installing Rasperry Pi System Configuration tool", ["raspi-config"])
				script += ExternalAction(
					"... Downloading X11 graphics driver for Pi 5.",
					"wget -q https://archive.raspberrypi.org/debian/pool/main/g/gldriver-test/gldriver-test_0.15_all.deb"
				)
				script += AptAction("... Installing X11 graphics driver for Pi 5.", "apt-get install -y ./gldriver-test_0.15_all.deb")
				script += ExternalAction("... Deleting downloaded Pi 5 graphics driver file.", "rm -f gldriver-test_0.15_all.deb")

				script += AptAction(
					"... Installing GPU drivers for hardware Pi 5 H.265 decoder.",
					"apt-get install -y linux-firmware-raspi mesa-utils libgl1-mesa-dri"
				)

				# Create X11 configuration file to enable Pi 5 hardware H.265 decoder.
				lines  = TextBuilder()
				lines += 'Section "Device"'
				lines += '\tIdentifier "Card1"'
				lines += '\tDriver "modesetting"'
				lines += '\tOption "kmsdev" "/dev/dri/card1"'
				lines += '\tOption "ShadowFB" "false"'
				lines += 'EndSection'
				lines += ''
				lines += 'Section "Screen"'
				lines += '\tIdentifier "Screen0"'
				lines += '\tDevice "Card1"'
				lines += 'EndSection'
				script += CreateTextWithUserAndModeAction(
					"... Creating X11 configuration file to enable Pi 5 H.265 hardware decoder.",
					"/etc/X11/xorg.conf.d/20-modesetting.conf",
					"root",
					stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
					lines.text
				)
				del lines

				# Create X11 configuration file to use Pi 5 graphics driver.
				lines  = TextBuilder()
				lines += 'Section "OutputClass"'
				lines += '\tIdentifier "vc4"'
				lines += '\tMatchDriver "vc4"'
				lines += '\tDriver "modesetting"'
				lines += '\tOption "PrimaryGPU" "true"'
				lines += 'EndSection'
				script += CreateTextWithUserAndModeAction(
					"... Creating X11 configuration file to enable Pi 5 GPU.",
					"/etc/X11/xorg.conf.d/99-v3d.conf",
					"root",
					stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
					lines.text
				)
				del lines

			# Create X11 configuration file to rotate the TOUCH panel, not the display itself (see KioskDesktop.py).
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
					"... Creating X11 configuration file to rotate touch panel (if any).",
					"/etc/X11/xorg.conf.d/99-kiosk-set-touch-rotation.conf",
					"root",
					stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH,
					lines.text
				)
				del lines

			# Create fresh Openbox autostart script (overwrite the existing autostart script, if any).
			# NOTE: Openbox does honor the shebang (#!) as Openbox always uses the 'dash' shell.
			# NOTE: For this reason, we start the Python script indirectly through an-hoc Dash script.
			lines  = TextBuilder()
			lines += "#!/usr/bin/dash"
			lines += "/home/kiosk/KioskForge/KioskDesktop.py"
			script += CreateTextWithUserAndModeAction(
				"... Creating Openbox startup script.",
				"/home/kiosk/.config/openbox/autostart",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR,
				lines.text
			)
			del lines

			if kiosk.type.data == "web":
				script += CustomAction("Installing Chromium web browser:", lambda: None)

				# Install Chromium as we use its kiosk mode (also installs CUPS, see below).
				script += ExternalAction("... Installing 'chromium' snap.", "snap install chromium")

				# ...Stop and remove the Common Unix Printing Server (cups) as it is a security risk that we don't need in a kiosk.
				script += ExternalAction(
					"... Purging Common Unix Printing System (cups) installed with Chromium.",
					"snap remove --purge cups"
				)

				# NOTE: Do NOT remove the 'gnome-42-2204' snap as this makes Chromium fail silently!
				# NOTE: Do NOT remove the 'gtk-common-themes' snap as this makes Chromium crash and refuse to restart!

				# Write almost empty Chromium preferences file to disable translate.
				lines = TextBuilder()
				lines += '{"translate":{"enabled":false}}'
				script += CreateTextWithUserAndModeAction(
					"... Disabling Translate feature in Chromium web browser.",
					"/home/kiosk/snap/chromium/common/chromium/Default/Preferences",
					"kiosk",
					stat.S_IRUSR | stat.S_IWUSR,
					lines.text
				)
				del lines

				# Install 'xprintidle' used to detect X idle periods and restart the browser (required even if idle_timeout == 0).
				script += InstallPackagesNoRecommendsAction(
					"... Installing 'xprintidle' used to restart Chromium when idle timeout expires.",
					["xprintidle"]
				)
			elif kiosk.type.data == "x11":
				# Currently nothing to do.
				pass
		elif kiosk.type.data == "cli":
			# Currently nothing to do, KioskStart.py handles this case completely.
			pass
		else:
			raise KioskError(f"Unknown kiosk type: {kiosk.type.data}")

		# If the user_packages option is specified, install the extra package(s).
		if kiosk.user_packages.data:
			script += InstallPackagesAction("Installing user-specified (custom) packages", shlex.split(kiosk.user_packages.data))

		if kiosk.type.data == "web-wayland":
			# If using Wayland.

			# Create systemd service to allocate a session for the kiosk user.
			lines  = TextBuilder()
			lines += "[Service]"
			lines += "# This is what causes a user session to be allocated for the kiosk user."
			lines += "User=kiosk"
			lines += "PAMName=login"
			lines += "TTYPath=/dev/tty1"
			lines += "ExecStart="
			lines += "ExecStart=/usr/bin/systemctl --user start --wait user-session.target"
			script += CreateTextWithUserAndModeAction(
				"Creating global systemd script to allocate a session for the user.",
				"/etc/systemd/system/user-session.service",
				"root",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
				lines.text
			)
			del lines
			script += ExternalAction("Enabling global systemd user-session service.", "systemctl enable user-session.service")

			# Create systemd service to run Ubuntu Frame under the kiosk user.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge: Ubuntu Frame launcher"
			lines += "Before=xdg-desktop-autostart.target"
			lines += "BindsTo=graphical-session.target"
			lines += "[Service]"
			lines += "ExecStartPre=/usr/bin/dbus-update-activation-environment --systemd WAYLAND_DISPLAY=wayland-0"
			lines += "ExecStart="
			lines += "ExecStart=/snap/bin/ubuntu-frame"
			script += CreateTextWithUserAndModeAction(
				"Creating user-specific systemd service to launch Ubuntu Frame.",
				"/home/kiosk/.config/systemd/user/ubuntu-frame.service",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Enabling custom systemd Ubuntu Frame service.", "systemctl enable ubuntu-frame.service")

			# Create systemd service to launch Chromium.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge: Chromium launcher"
			lines += "After=ubuntu-frame.service"
			lines += "[Service]"
			lines += "ExecStart="
			lines += f"ExecStart=/snap/bin/chromium --kiosk '{kiosk.command.data}'"
			script += CreateTextWithUserAndModeAction(
				"Creating user-specific systemd service to launch Chromium.",
				"/home/kiosk/.config/systemd/user/chromium.service",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Enabling custom systemd Chromium service.", "systemctl enable chromium.service")

			# Start all of the above in one operation.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge: Chromium launcher"
			lines += "Wants=ubuntu-frame.service chromium.service"
			script += CreateTextWithUserAndModeAction(
				"Creating user-specific systemd service to launch Chromium.",
				"/home/kiosk/.config/systemd/user/user-session.target",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines
			script += ExternalAction("Start Wayland and then Chromium when booting.", "systemctl add-wants graphical.target user-session.service")
		else:
			# Append lines to '~kiosk/.bash_login' to execute the startup script (which handles redundant requests, etc.).
			lines  = TextBuilder()
			lines += '#!/usr/bin/bash'
			lines += ''
			lines += "# Make sure Python doesn't litter everything and wear the storage medium by writing bytecode everywhere."
			lines += 'export PYTHONDONTWRITEBYTECODE=1'
			lines += ''
			# NOTE: Don't use 'set -e', it logs out whenever an error occurs in the logged in SSH session...
			# NOTE: Don't logout as 'systemd' will respawn the login process right away, causing havoc as it restarts X11, etc.
			# NOTE: Not logging out leads to a "zombie" shell session, but it dies very soon when 'KioskUpdate.py' reboots.
			lines += '# If an interactive login (not an SSH session), start KioskStart.py.'
			lines += 'if [[ -z "$SSH_CLIENT" ]]; then'
			lines += "\t# Wait for the 'kiosk-booter-finish.flag' file to be created in ~/.signals."
			lines += '\twhile [ ! -f /home/kiosk/.signals/kiosk-booter-finish.flag ]; do'
			lines += '\t\tsleep 1;'
			lines += '\tdone'
			lines += "# Remove the flag file after we've seen it as nobody else does it."
			lines += '\trm -f /home/kiosk/.signals/kiosk-booter-finish.flag'
			lines += ''
			lines += '\t# Start the KioskStart.py script, which is responsible for starting X11 and/or the kiosk.'
			lines += '\t/home/kiosk/KioskForge/KioskStart.py'
			lines += 'fi'
			lines += ''
			lines += '# An SSH session, simply set up the environment, incl. the kiosklog() function, and let the user inside.'
			lines += '. ~/.bashrc'
			script += CreateTextWithUserAndModeAction(
				"Creating ~kiosk/.bash_login to start up the kiosk at every boot.",
				"/home/kiosk/.bash_login",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR,
				lines.text
			)
			del lines

			# Set up automatic login for the kiosk user using systemd.
			lines  = TextBuilder()
			lines += "[Unit]"
			lines += "Description=KioskForge: Auto-login kiosk user and start kiosk"
			lines += "Requires=network-online.target"
			lines += "Requires=multi-user.target"
			lines += ""
			lines += "[Service]"
			lines += "Type=simple"
			lines += "ExecStart="
			lines += "ExecStart=-/sbin/agetty --noissue --autologin kiosk %I $TERM"
			script += CreateTextWithUserAndModeAction(
				"Creating systemd auto-login override to start the kiosk.",
				"/etc/systemd/system/getty@tty1.service.d/override.conf",
				"root",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
				lines.text
			)
			del lines
#		else:
#			# NOTE: I never did manage to get the systemd service to even start up (I've stopped playing with it for now).
#			lines  = TextBuilder()
#			lines += "[Unit]"
#			lines += "Description=KioskForge: Kiosk launcher"
#			lines += "After=network-online.target"
#			lines += "After=multi-user.target"
#			lines += ""
#			lines += "[Service]"
#			lines += "User=kiosk"
#			lines += "Group=kiosk"
#			lines += "Type=simple"
#			lines += "ExecStart="
#			lines += "ExecStart=/home/kiosk/KioskForge/KioskStart.py"
#			lines += "StandardOutput=tty"
#			lines += "StandardError=tty"
#			lines += ""
#			lines += "[Install]"
#			lines += "WantedBy=multi-user.target"
#			script += CreateTextWithUserAndModeAction(
#				"Creating systemd kiosk service.",
#				"/etc/systemd/system/kiosk.service",
#				"root",
#				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH,
#				lines.text
#			)
#
#			# Enable the new systemd unit.
#			script += ExternalAction("Enabling systemd kiosk service", "systemctl enable kiosk")

		# Create disk swap file in case the system gets very low on memory.
		if kiosk.swap_size.data > 0:
			script += CustomAction("Enabling disk swap file:", lambda: None)

			script += ExternalAction("... Allocating swap file.", f"fallocate -l {kiosk.swap_size.data}G /swapfile",)
			script += ExternalAction("... Setting permissions on new swap file.", "chmod 600 /swapfile")
			script += ExternalAction("... Formatting swap file.", "mkswap /swapfile")
			script += AppendTextAction(
				"... Creating '/etc/fstab' entry.",
				"/etc/fstab",
				"/swapfile\tnone\tswap\tsw\t0\t0"
			)

		if kiosk.wear_reduction.data:
			script += CustomAction("Enabling wear reduction on system medium:", lambda: None)

			# Attempt to reduce wear on micro-SD storage by moving swap, /tmp, and /var/log to memory.
			# NOTE: See https://linuxblog.io/raspberry-pi-performance-add-zram-kernel-parameters/ for more information.
			script += AptAction("... Installing 'zram-tools' to configure compressed swap in memory.", "apt-get install -y zram-tools")

			script += ReplaceTextAction(
				"... Configuring zram swap to use the zstd compression algorithm.",
				"/etc/default/zramswap",
				"#ALGO=lz4",
				"ALGO=zstd"
			)

			script += ReplaceTextAction(
				"... Configuring zram swap to use one quarter of available memory.",
				"/etc/default/zramswap",
				"#PERCENT=50",
				"PERCENT=25"
			)

			# Configure the kernel for using the RAM swap file aggressively (to speed up the system and reduce media wear).
			# NOTE: See https://linuxblog.io/raspberry-pi-performance-add-zram-kernel-parameters/ for more information.
			lines  = TextBuilder()
			lines += "# Created by KioskForge to enable aggressive swap mode per the 'ram_boost=true' option."
			lines += "# See https://linuxblog.io/raspberry-pi-performance-add-zram-kernel-parameters/ for more information."
			lines += "vm.vfs_cache_pressure=500"
			lines += "vm.swappiness=100"
			lines += "vm.dirty_background_ratio=1"
			lines += "vm.dirty_ratio=50"
			script += CreateTextWithUserAndModeAction(
				"... Setting kernel swap mode to aggressive.",
				"/etc/sysctl.d/20-kiosk-zram-swap-aggressive.conf",
				"kiosk",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
				lines.text
			)
			del lines

			def fstab_append_options_to_ext4() -> None:
				fstab = Filesystems()
				fstab.load("/etc/fstab")

				for line in fstab.lines:
					if not isinstance(line, Mount):
						continue

					mount = cast(Mount, line)
					if mount.type != "ext4":
						continue

					# Add the 'noatime' (don't update access time) to the system 'ext4' partition.
					mount.options = mount.options + ["noatime"]

					# Change commit value from the default (5) to 1,000 and add 'noatime' to reduce wear on the micro-SD even further.
					# NOTE: I don't dare increasing the commit value to 1,000 seconds as some kiosks are powered off abruptly.
					# See: https://forums.raspberrypi.com/viewtopic.php?t=328888 for more information.
					# mount.options = mount.options + "commit=1000"]

				fstab.save("/etc/fstab")

			script += CustomAction(
				"... Setting the 'noatime' flag on the system ext4 partition.",
				fstab_append_options_to_ext4
			)
			del fstab_append_options_to_ext4

			# Move /tmp to a RAM disk - we have no persistent data in /tmp and it SHOULD be wiped on every boot, anyway.
			# NOTE: Some KioskForge signals are created in the on-disk /tmp and later attempted read from the ramdisk /tmp...
			lines  = TextBuilder()
			lines += "tmpfs /tmp tmpfs defaults,noatime,size=256m 0 0"
			script += AppendTextAction("... Moving /tmp to an ad-hoc RAM disk.", "/etc/fstab", lines.text)
			del lines

			# Move /var/log to a RAM disk - most frequently, nobody looks at these logs anyway (I don't dare do this yet!).
			# NOTE: This would effectively mean losing all logs on every reboot, not very good for debugging and status checks.
			#lines  = TextBuilder()
			#lines += "tmpfs /var/log tmpfs defaults,noatime,nosuid,size=256m 0 0"
			#script += AppendTextAction("... Moving /var/log to a RAM disk.", "/etc/fstab", lines.text)
			#del lines

		# Create cron job to compact system logs so these are compacted daily at reboot and at 05:00.
		# NOTE: The @reboot ensures the journals are vacuumed if the kiosk is rebooted on a daily basis, the time of 05:00 ensures
		# NOTE: the journals are vacuumed even if the kiosk is never updated and therefore perhaps never rebooted.
		lines  = TextBuilder()
		lines += "# Cron jobs to compact system logs using journalctl."
		lines += f"@reboot\t\troot\tsleep 5m; /usr/bin/journalctl --vacuum-size={kiosk.vacuum_size.data}M"
		lines += f"00 05 * * *\troot\t/usr/bin/journalctl --vacuum-size={kiosk.vacuum_size.data}M"
		script += CreateTextWithUserAndModeAction(
			"Creating cron job to vacuum system logs at every boot and every night at 05:00.",
			"/etc/cron.d/kiosk-vacuum-logs",
			"root",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)
		del lines

		# Create cron job to clear out the /home/kiosk/.signals folder for old, stale sentinel files.
		lines  = TextBuilder()
		lines += "# Cron job to clean the /home/kiosk/.signals folder."
		lines += "@reboot\t\troot\trm -fr /home/kiosk/.signals/*"
		script += CreateTextWithUserAndModeAction(
			"Creating cron job to clean up the KioskForge signals folder at every boot.",
			"/etc/cron.d/kiosk-clean-signals",
			"root",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)
		del lines

		# Create cron job to purge, update, upgrade, clean, and reboot/shutdown the system every day at the given time.
		if kiosk.upgrade_time.data:
			lines  = TextBuilder()
			lines += "# Cron job to upgrade, clean, and reboot the system every day."
			lines += f"{kiosk.upgrade_time.data[3:5]} {kiosk.upgrade_time.data[0:2]} * * *\troot\t/home/kiosk/KioskForge/KioskUpdate.py"
			script += CreateTextWithUserAndModeAction(
				"Creating cron job to upgrade system once a day at the configured time.",
				"/etc/cron.d/kiosk-upgrade-system",
				"root",
				stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
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

		# Install user-supplied fonts, if any (basically any TrueType font files found in the user_folder folder).
		# NOTE: This step requires that X11 or Wayland has been installed above.
		appdir = "/home/kiosk/Application"
		if kiosk.type.data in ["web", "x11", "web-wayland"] and custom_fonts_get(appdir):
			# Report that we're installing custom fonts.
			script += CustomAction("Installing custom fonts:", lambda: None)

			target = "/home/kiosk/.local/share/fonts/KioskForge"
			script += InstallFontsAction("... Installing fonts found in Application folder.", appdir, target)
			del target

			# Update the font cache.
			script += ExternalAction("... Updating kiosk user's font cache.", "sudo -u kiosk fc-cache -f")
		del appdir

		# Change ownership of all files in the user's home dir to that of the user as we create a few files as sudo (root).
		script += ExternalAction(
			"Setting the owner of all files in the kiosk home directory to 'kiosk'.",
			"chown -R kiosk:kiosk /home/kiosk"
		)

		# Run 'KioskConfig.py' from 'kiosk-booter.py' at boot by creating a suitable systemd service to perform run both.
		# NOTE: The ConditionPathExists line is there to ensure that only ONE copy of kiosk-booter.py is ever launched.
		# NOTE: I'll probably die not knowing why systemd does not offer this feature on its own.
		lines  = TextBuilder()
		lines += "[Unit]"
		lines += "Description=KioskForge: Upgrader and Configurator"
		lines += "After=pipewire.service"
		lines += "After=pipewire-pulse.service"
		lines += "After=multi-user.target"
		lines += "ConditionPathExists=!/home/kiosk/.signals/kiosk-booter-launch.flag"
		lines += ""
		lines += "[Service]"
		lines += "Type=oneshot"
		lines += "Restart=no"
		lines += "RemainAfterExit=yes"
		lines += "ExecStart=/home/kiosk/KioskForge/kiosk-booter.py /home/kiosk/KioskForge/KioskConfig.py"
		lines += "ExecStartPost=/usr/bin/touch /home/kiosk/.signals/kiosk-booter-launch.flag"
		lines += ""
		lines += "[Install]"
		lines += "WantedBy=multi-user.target"
		script += CreateTextWithUserAndModeAction(
			"Configuring systemd to run kiosk-booter.py then KioskConfig.py on every boot.",
			"/etc/systemd/system/kiosk-booter.service",
			"root",
			stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH,
			lines.text
		)
		del lines

		# Enable 'kiosk-booter' systemd service so that it runs on every future boot.
		script += ExternalAction(
			"... Enabling systemd kiosk-booter service.",
			"systemctl enable kiosk-booter.service"
		)

		# Synchronize all changes to disk (may take a while on microSD cards).
		script += ExternalAction(
			"Flushing disk buffers before rebooting (may take a while on a slow medium).",
			"sync"
		)

		# Execute the script (simply hang on errors so that the user can read any error messages).
		result = script.execute()
		if result.status != 0:
			raise KioskError("*** FAILURE - UNABLE TO COMPLETE FORGE PROCESS")

		# Wait a few seconds for users to be able to spot errors and/or read how long the forge process took.
		logger.write("*** SUCCESS - REBOOTING SYSTEM INTO KIOSK MODE IN 10 SECONDS")
		time.sleep(10)

		# NOTE: The reboot takes place immediately, control never returns from the 'execute()' method below!
		ExternalAction("Rebooting system NOW!", "reboot").execute()


if __name__ == "__main__":
	sys.exit(KioskSetup().main(sys.argv))
