#!/usr/bin/env python3
# Script that converts an Ubuntu Server box into a kiosk machine that displays the specified URL in kiosk mode using Chromium.
#
# Notes:
#   1. This script is in fact THREE scripts!  This to avoid duplicating code and maintaining identical code in three files.
#      The script is invoked as 'KioskForge.py' and then copies itself to the installation medie and customizes cloud-init in such
#      a way that the script is automatically invoked as 'KioskSetup.py' very late in the installation process, after which it
#      creates a symbolic link to itself with the name 'KioskStart.py', which launches Chrome and monitors its execution.
#	2. This script assumes a clean installation with no modifications whatsoever prior to it being invoked.  As such, it can
#	   "safely" abort upon errors as the user can simply re-flash his system using Raspberry Pi Imager once again.  There are no
#	   features to safely roll back the changes made during the customization of the system for kiosk mode usage!

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, Dict, List, Optional, TextIO, Tuple

import abc
import glob
import hashlib
import os
import platform
import shlex
import shutil
import stat
import string
import subprocess
import sys
import time
import types

from kiosk.builder import TextBuilder
from kiosk.convert import STRING_TO_BOOLEAN
from kiosk.errors import *
import kiosk.KioskClass
from kiosk.logger import Logger, TextWriter
from kiosk.invoke import Result
from kiosk.setup import *
# Import COMPANY, CONTACT, TESTING, and VERSION global constants.
# TODO: Make the 'kiosk.version.*' "constants" readonly somehow.
from kiosk.version import *


# Try to import bcrypt.  If not found, try to silently install it and try to import it once more.
if platform.system() == "Windows":
	try:
		import bcrypt
	except ModuleNotFoundError:
		try:
			subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			import bcrypt
		except subprocess.CalledProcessError:
			print("*** Error: Unable to automatically install 'bcrypt' module.  Please report this issue.")
			if platform.system() == "Windows" and not "PROMPT" in os.environ:
				input("Press ENTER to continue and close this window")
			sys.exit(1)


def password_crypt(text : str) -> str:
	assert(len(text) >= 1 and len(text) <= 72)
	data = text.encode('utf-8')
	hash = bcrypt.hashpw(data, bcrypt.gensalt()).decode('utf-8')
	return hash


class Target(object):
	"""Simple class that encapsulates all information about the target system."""

	def __init__(self, kind : str, basedir : str, product : str, edition : str, version : str, cpukind : str, install : str) -> None:
		# Check arguments (mostly for the sake of documenting the valid values).
		assert(kind in ["PC", "PI"])
		assert(cpukind in ["amd64", "arm64"])
		assert(install in ["cloud-init", "subiquity"])

		# Initialize instance.
		self.__kind = kind
		self.__basedir = basedir
		self.__product = product
		self.__edition = edition
		self.__version = version
		self.__cpukind = cpukind
		self.__install = install

	@property
	def basedir(self) -> str:
		return self.__basedir

	@property
	def cpukind(self) -> str:
		return self.__cpukind

	@property
	def edition(self) -> str:
		return self.__edition

	@property
	def install(self) -> str:
		return self.__install

	@property
	def kind(self) -> str:
		return self.__kind

	@property
	def product(self) -> str:
		return self.__product

	@property
	def version(self) -> str:
		return self.__version


class Recognizer(object):
	"""Simple base class that defines the layout of a recognizer that recognizes one or more target systems."""

	def __init__(self) -> None:
		pass

	def _identify(self, path : str) -> Optional[Target]:
		raise NotImplementedError("Abstract method called")

	def identify(self) -> Optional[Target]:
		if platform.system() != "Windows":
			raise KioskError("KioskForge.py only runs on Windows")

		# Scan all mount points/drives and see if there are any of the reserved files we're looking for.
		targets : List[Target] = []
		attempts = 0
		while True:
			if platform.system() == "Windows":
				mounts = os.listdrives()
			elif platform.system() == "Linux":
				raise InternalError("Feature not finished")
				mounts = 'df -a -T -h -t vfat | grep -Fv "/boot/efi" | grep -Fv "Use%"'

			# Check each mount point/Windows drive for a recognizable installation media.
			for mount in mounts:
				for recognizer in RECOGNIZERS:
					target = recognizer._identify(mount)
					if target:
						targets.append(target)

			# If zero kiosk images were found, let the user fix the error and try again.
			if len(targets) == 0:
				# Only wait three seconds five times so as to not force the user to hit Ctrl-C.
				if attempts == 5:
					return None
				attempts += 1

				# NOTE: Windows takes a little while to discover the written image, so we try once more if we fail at first.
				print("ALERT: Waiting three seconds for installation media to be discovered by the host operating system...")
				print("ALERT: If you have not already done so, please insert the installation media to proceed.")
				print()
				time.sleep(3)
				continue

			# Handle more than one target drives.
			if len(targets) >= 2:
				raise KioskError("More than one USB key or MicroSD card found")

			break

		assert(len(targets) == 1)
		return targets[0]


class PcRecognizer(Recognizer):
	"""Derived class which recognizes Ubuntu Server 24.04.1 in a PC install image."""

	def __init__(self) -> None:
		Recognizer.__init__(self)

	def _identify(self, path : str) -> Optional[Target]:
		info_name = path + ".disk" + os.sep + "info"

		if not os.path.isfile(info_name):
			return None

		# Parse the /.disk/info file to get the information we're looking for.
		info_data = open(info_name, "rt").read().strip()
		fields = shlex.split(info_data)
		if len(fields) != 8:
			return None
		(product, version, support, codename, dash, release, cpukind, date_num) = fields

		# Check the info file and report one or more errors if we don't support the found target.
		errors = []
		if product != "Ubuntu-Server":
			errors.append("Error: Unsupported operating system: %s" % product)
		if version != "24.04.1":
			errors.append("Error: Unsupported version: %s" % version)
		if support != "LTS":
			errors.append("Error: Unsupported support lifetime: %s" % support)
		if cpukind != "amd64":
			errors.append("Error: Unsupported CPU kind: %s" % cpukind)

		# If one or more errors were found, report them and don't recognize this target.
		if errors:
			for error in errors:
				print("%s: %s" % (path, error))
			return None

		return Target("PC", path, "Ubuntu", "Server", "24.04.1", "amd64", "subiquity")


SHA512_UBUNTU_SERVER_24_04_1_ARM64  = '1d6c8d010c34f909f062533347c91f28444efa6e06cd55d0bdb39929487d17a8be4cb36588a9cbfe0122ad72fee72086d78cbdda6d036a8877e2c9841658d4ca'
SHA512_UBUNTU_DESKTOP_24_04_1_ARM64 = 'ce3eb9b96c3e458380f4cfd731b2dc2ff655bdf837cad00c2396ddbcded64dbc1d20510c22bf211498ad788c8c81ba3ea04c9e33d8cf82538be0b1c4133b2622'
SHA512_UBUNTU_SERVER_24_04_2_ARM64  = '5c62b93b8d19e8d7ac23aa9759a23893af5dd1ab5f80e4fb71f7b4fd3ddd0f84f7c82f9342ea4c9fdba2c350765c2c83eaaa6dcaac236f9a13f6644386e6a1d2'
SHA512_UBUNTU_DESKTOP_24_04_2_ARM64 = '32825b5b770f94996f05a9f2fa95e8f7670944de5990a258d10d95c5bd0062123a707d8b943d23e7b0d54e8c3ff8440b0fd7ebbb8dc42bc20da8a77b3f3f6408'

class PiRecognizer(Recognizer):
	"""Derived class that recognizes Ubuntu Desktop or Server 24.04.x in a Raspberry Pi 4B install image."""

	def __init__(self) -> None:
		Recognizer.__init__(self)

	def _identify(self, path : str) -> Optional[Target]:
		if not os.path.isfile(path + "cmdline.txt"):
			return None

		if not os.path.isfile(path + "initrd.img"):
			return None

		hash = hashlib.sha512(open(path + "initrd.img", "rb").read()).hexdigest()
		if hash == SHA512_UBUNTU_SERVER_24_04_1_ARM64:
			return Target("PI", path, "Ubuntu", "Server", "24.04.1", "arm64", "cloud-init")
		elif hash == SHA512_UBUNTU_SERVER_24_04_2_ARM64:
			return Target("PI", path, "Ubuntu", "Server", "24.04.2", "arm64", "cloud-init")
		elif hash == SHA512_UBUNTU_DESKTOP_24_04_1_ARM64:
			return Target("PI", path, "Ubuntu", "Desktop", "24.04.1", "arm64", "cloud-init")
		elif hash == SHA512_UBUNTU_DESKTOP_24_04_2_ARM64:
			return Target("PI", path, "Ubuntu", "Desktop", "24.04.2", "arm64", "cloud-init")

		return None


# List of systems that can be recognized and thus are supported.
RECOGNIZERS = [
	PiRecognizer(),
	PcRecognizer()
]


class KernelOptions(object):
	"""Small class that handles adding kernel options to the Raspberry PI 'cmdline.txt' file."""

	def __init__(self) -> None:
		self.__options : List[str] = []

	@property
	def options(self) -> List[str]:
		return self.__options

	def append(self, option : str) -> None:
		self.__options.append(option)

	def load(self, path : str) -> None:
		self.__options = open(path, "rt", encoding="utf-8").read().strip().split(' ')

	def save(self, path : str) -> None:
		open(path, "wt", encoding="utf-8").write(' '.join(self.__options))


class Editor(object):
	"""Very simple editor for selecting choices and editing configurations."""

	def confirm(self, question : str) -> bool:
		answer = ""
		while answer not in STRING_TO_BOOLEAN:
			answer = input(question + " (y/n)? ").strip().lower()
		return STRING_TO_BOOLEAN[answer]

	def edit(self, setup : Setup) -> bool:
		changed = False
		fields = vars(setup)
		names = {}
		while True:
			index = 0
			for name, field in fields.items():
				index += 1
				names[index] = name
				print("%2d) %-13s = %s" % (index, name, field.data))
			print()

			answer = input("Please enter number or ENTER to quit: ").strip()
			if answer == "":
				return changed

			if not answer.isdigit():
				print("Error: Enter a valid number")
				continue

			choice = int(answer)
			if choice == 0 or choice > index:
				print("Error: Enter a valid number in the range 1 through %d" % index)
				continue

			print("Hint: %s" % getattr(setup, names[choice]).text)
			value = input("Enter new value (ENTER to leave unchanged): ").strip()
			if value == "":
				continue

			try:
				getattr(setup, names[choice]).parse(value)
				changed = True
			except InputError as that:
				print(that.text)

		return changed

	def select(self, title : str, choices : List[str]) -> int:
		print(title + ":")

		while True:
			print()
			index = 0
			while index < len(choices):
				value = choices[index]
				index += 1
				print("%2d) %s" % (index, value))
			print()
			del index

			answer = input("Enter choice (ENTER to quit): ").strip()
			print()

			if answer == "":
				return -1

			if not answer.isdigit():
				print("Error: Invalid value entered")
				continue

			choice = int(answer) - 1
			if choice < 0 or choice >= len(choices):
				print("Error: Enter a valid number")
				continue

			break

		return choice


class KioskForge(kiosk.KioskClass.KioskClass):
	"""This class contains the 'KioskForge' code, which prepares a boot image for running 'KioskSetup' on a kiosk machine."""

	def __init__(self) -> None:
		kiosk.KioskClass.KioskClass.__init__(self)
		self.version = Version("KioskForge", VERSION, COMPANY, CONTACT, TESTING)

	def saveCloudInitMetaData(self, setup : Setup, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(
				"# Cloud-init meta-data file generated by %s v%s.  DO NOT EDIT!" % (self.version.program, self.version.version)
			)
			stream.write()

			# Write network-config values, copied verbatim from the Raspberry Pi 4B setup written by Raspberry Pi Imager.
			stream.write("dsmode: local")
			stream.write("instance_id: cloud-image")

	def saveCloudInitNetworkConfig(self, setup : Setup, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(
				"# Cloud-init network-config file generated by %s v%s.  DO NOT EDIT!" % (
					self.version.program,
					self.version.version
				)
			)
			stream.write()

			# Write custom network-config, which uses the current target's configuration.
			stream.write("network:")
			stream.indent()
			stream.write("version: 2")
			stream.write()
			stream.write("ethernets:")
			stream.indent()
			stream.write("eth0:")
			stream.indent()
			stream.write("dhcp4: true")
			stream.write("optional: %s" % ("true" if setup.wifi_name.data else "false"))
			stream.write()
			stream.dedent(3)

			if setup.wifi_name.data:
				stream.indent()
				stream.write("wifis:")
				stream.indent()
				stream.write("renderer: networkd")
				stream.write("wlan0:")
				stream.indent()
				stream.write("dhcp4: true")
				stream.write("optional: false")
				stream.write("access-points:")
				stream.indent()
				stream.write('"%s":' % setup.wifi_name.data)
				stream.indent()
				stream.write('password: "%s"' % setup.wifi_code.data)
				stream.dedent(5)

	def saveCloudInitUserData(self, setup : Setup, target : Target, path : str) -> None:
		with TextWriter(path) as stream:
			output = "/home/%s" % setup.user_name.data

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(
				"# Cloud-init user-data file generated by %s v%s.  DO NOT EDIT!" % (self.version.program, self.version.version)
			)
			stream.write()

			# Write users: block, which lists the users to be created in the final kiosk system.
			stream.write("users:")
			stream.indent()
			stream.write("- name: %s" % setup.user_name.data)
			stream.indent()
			stream.write("gecos: Administrator")
			stream.write("groups: users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo")
			stream.write("shell: /bin/bash")
			stream.write("lock_passwd: false")
			stream.write('passwd: "%s"' % password_crypt(setup.user_code.data))
			# NOTE: The line below is way too dangerous if somebody gets through to the shell.
			#stream.write("sudo: ALL=(ALL) NOPASSWD:ALL")
			stream.dedent()
			stream.dedent()
			stream.write()

			# Write timezone (to get date and time in logs correct).
			stream.write("timezone: %s" % setup.timezone.data)
			stream.write()

			# Write keyboard layout (I haven't found a reliable way to do this in any other way).
			stream.write("keyboard:")
			stream.indent()
			stream.write("layout: %s" % setup.keyboard.data)
			stream.write("model: pc105")
			stream.dedent()
			stream.write()

			# Write commands to write a custom /usr/lib/systemd/system/KioskSetup.service file (it is enabled further below).
			stream.write("write_files:")
			stream.write("- path: /usr/lib/systemd/system/KioskSetup.service")
			stream.indent()
			stream.write("content: |")
			stream.indent()
			stream.write("[Unit]")
			stream.write("Description=KioskForge automatic configuration of new kiosk machine.")
			stream.write("After=network-online.target")
			stream.write("After=cloud-init.target")
			stream.write("After=multi-user.target")
			stream.write()
			stream.write("[Service]")
			stream.write("Type=simple")
			stream.write("ExecStart=%s/KioskForge/KioskSetup.py" % output)
			stream.write("StandardOutput=tty")
			stream.write("StandardError=tty")
			stream.write()
			stream.write("[Install]")
			stream.write("WantedBy=cloud-init.target")
			stream.dedent()
			stream.write("owner: 'root:root'")
			stream.write("permissions: '664'")
			stream.dedent()
			stream.write()

			# Compute locations of source files.
			if target.kind == "PI":
				source = "/boot/firmware"
			elif target.kind == "PC":
				source = "/cdrom"
			else:
				raise InternalError("Unknown kiosk machine kind: %s" % target.kind)

			# Write commands to copy and then make this script executable (this is done late in the boot process).
			stream.write("runcmd:")
			stream.indent()
			stream.write("- cp -pR %s/KioskForge %s" % (source, output))
			stream.write("- chown -R %s:%s %s/KioskForge" % (setup.user_name.data, setup.user_name.data, output))
			stream.write("- chmod -R u+x %s/KioskForge" % output)
			stream.write("- chmod a-x %s/KioskForge/KioskForge.cfg" % output)
			stream.write("- systemctl daemon-reload")
			stream.write("- systemctl enable KioskSetup")
			stream.dedent()
			stream.write()
			del source

			# Write commands to reboot the machine once the dust settles for Cloud-Init.
			stream.write("power_state:")
			stream.indent()
			stream.write("delay: now")
			stream.write("mode: reboot")
			stream.write("message: Rebooting the system to set up the kiosk.")
			stream.dedent()
			stream.write()

			# Write commands to update and upgrade the system before we reboot the first time.
			if False:
				# TODO: Either reenable cloud-init updates or disable AutoInstall updates.
				# NOTE: Temporarily disabled it possibly causes an issue where cloud-init times out.
				# NOTE: We're rebooting with the "power_state" key above, not only in case of a kernel upgrade
				# NOTE: ("package_reboot_if_required").
				stream.write("package_update: true")
				stream.write("package_upgrade: true")
				stream.write()

			# Write commands to install and/or enable Network Time Protocol (NTP).
			stream.write("ntp:")
			stream.indent()
			stream.write("enabled: true")
			stream.dedent()
			stream.write()

	def saveAutoinstallYaml(self, setup : Setup, target : Target, path : str) -> None:
		with TextWriter(path) as stream:
			origin = "/home/%s" % setup.user_name.data

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(
				"# Cloud-init user-data file generated by %s v%s.  DO NOT EDIT!" % (self.version.program, self.version.version)
			)
			stream.write()

			# Write autoinstall.yaml opening tag and version info.
			stream.write("autoinstall:")
			stream.indent()
			stream.write("version: 1")

			stream.write("apt:")
			stream.indent()
			stream.write("disable_components: []")
			stream.write("fallback: offline-install")
			stream.write("geoip: true")
			stream.write("mirror-selection:")
			stream.indent()
			stream.write("primary:")
			stream.write("- country-mirror")
			stream.write("- arches: &id001")
			stream.indent()
			stream.write("- amd64")
			stream.write("- i386")
			stream.write("uri: http://archive.ubuntu.com/ubuntu/")
			stream.dedent()
			stream.write("- arches: &id002")
			stream.indent()
			stream.write("- s390x")
			stream.write("- arm64")
			stream.write("- armhf")
			stream.write("- powerpc")
			stream.write("- ppc64el")
			stream.write("- riscv64")
			stream.write("uri: http://ports.ubuntu.com/ubuntu-ports")
			stream.dedent()
			stream.dedent()
			stream.write("preserve_sources_list: false")
			stream.write("security:")
			stream.write("- arches: *id001")
			stream.indent()
			stream.write("uri: http://security.ubuntu.com/ubuntu/")
			stream.dedent()
			stream.write("- arches: *id002")
			stream.indent()
			stream.write("uri: http://ports.ubuntu.com/ubuntu-ports")
			stream.dedent()
			stream.dedent()
			stream.write("codecs:")
			stream.indent()
			stream.write("install: false")
			stream.dedent()
			stream.write("drivers:")
			stream.indent()
			stream.write("install: false")
			stream.dedent()
			stream.write("error-commands:")
			stream.indent()
			stream.write("- mkdir -p %s" % origin)
			stream.write("- tar -czf %s/installer-logs.tar.gz /var/log/installer/" % origin)
			stream.write("- journalctl -b > %s/installer-journal.log" % origin)
			stream.dedent()
			stream.write("identity:")
			stream.indent()
			stream.write("hostname: %s" % setup.hostname.data)
			stream.write("realname: %s" % "Kiosk")
			stream.write("username: %s" % setup.user_name.data)
			stream.write('password: "%s"' % password_crypt(setup.user_code.data))
			stream.dedent()
			stream.write("kernel:")
			stream.indent()
			stream.write("package: linux-generic")
			stream.dedent()

			# Write keyboard configuration.
			stream.write("keyboard:")
			stream.indent()
			stream.write("layout: %s" % setup.keyboard.data)
			stream.write("toggle: null")
			stream.write("variant: ''")
			stream.dedent()

			# Write locale information.
			stream.write("locale: %s" % setup.locale.data)

			# Write network configuration.
			stream.write("network:")
			stream.indent()
			stream.write("version: 2")
			stream.write("ethernets:")
			stream.indent()
			stream.write("eth0:")
			stream.indent()
			stream.write("dhcp4: true")
			stream.write("optional: true")
			stream.dedent()
			stream.dedent()

			if setup.wifi_name.data:
				stream.write("wifis:")
				stream.indent()
				stream.write("wlp1s0:")
				stream.indent()
				stream.write("dhcp4: true")
				stream.write("optional: false")
				stream.write("access-points:")
				stream.indent()
				stream.write('"%s":' % setup.wifi_name.data)
				stream.indent()
				stream.write('password: "%s"' % setup.wifi_code.data)
				stream.dedent(4)

			stream.dedent()

			stream.write("oem:")
			stream.indent()
			stream.write("install: auto")
			stream.dedent()
			stream.write("refresh-installer:")
			stream.indent()
			# TODO: Disable 'update: true' so that `KioskSetup.py` always handles all system updates.  This requires a test PC.
			stream.write("update: true")
			stream.dedent()
			stream.write("source:")
			stream.indent()
			stream.write("id: ubuntu-server")
			stream.write("search_drivers: false")
			stream.dedent()

			# Write SSH configuration settings.
			stream.write("ssh:")
			stream.indent()
			stream.write("allow-pw: false")
			stream.write("install-server: true")
			stream.write("authorized-keys:")
			stream.write("- '%s'" % setup.ssh_key.data)
			stream.dedent()

			stream.write("storage:")
			stream.indent()
			stream.write("layout:")
			stream.indent()
			stream.write("name: direct")
			stream.dedent()
			stream.dedent()

			stream.write("updates: all")

			stream.dedent()

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# NOTE: No need for a logger in KioskForge as it does very few things and some of them interactively.

		# Output copyright information, etc.
		print(self.version.banner())
		print()

		# Check that we're running on Windows.
		if platform.system() != "Windows":
			raise KioskError("This script can currently only be run on a Windows machine")

		# Parse command-line arguments.
		if len(arguments) != 0:
			raise SyntaxError("\"KioskForge.py\"")

		# Show the main menu.
		# TODO: Warn the user against saving if the kiosk is blank.
		editor = Editor()
		setup = Setup()
		changed = False
		filename = ""
		while True:
			try:
				# Present a menu of valid choices for the user to make.
				choices = [
					"Create new kiosk in memory",
					"Load existing kiosk from disk",
					"Edit created or loaded kiosk",
					"Save kiosk to disk",
					"Update Raspberry Pi Imager prepared installation media",
				]
				choice = editor.select("Select a menu choice", choices)

				# Process the requested menu command.
				if choice == -1:
					if changed:
						raise KioskError("Kiosk has unsaved changes")

					# Exit program.
					break
				elif choice == 0:
					# Create new kiosk.
					setup = Setup()
					filename = ""
					changed = False

					print("New kiosk successfully created in memory.")
					print()
				elif choice == 1:
					# Load existing kiosk from disk.
					answer = input("Please enter or paste full path of kiosk file (*.cfg): ").strip()
					print()

					if answer == "":
						continue

					try:
						setup.load(answer)
						filename = answer
					except FileNotFoundError:
						raise KioskError("Unable to load the specified file - is the path correct?")

					print("Kiosk successfully loaded from disk")
					print()

					changed = False
				elif choice == 2:
					# Edit kiosk.
					# Allow the user to re-edit the kiosk as long as there are errors.
					changed |= editor.edit(setup)

					# Report errors detected after changing the selected kiosk.
					errors = setup.check()
					if not errors:
						continue

					print()
					print("Warnings(s) detected in configuration:")
					print()
					for error in errors:
						print(">>> " + error)
					print()
					del errors
				elif choice == 3:
					# Save kiosk.
					# Allow the user to save the kiosk.
					if changed:
						while True:
							answer = input("Please enter or paste full path of kiosk file (*.cfg): ").strip()
							print()

							if answer == "":
								continue

							if not answer.endswith(".cfg"):
								raise KioskError("KioskForge kiosk configuration files MUST end in .cfg")

							# Create new folder, if any, and save the configuration.
							folder = os.path.split(answer)[0]
							os.makedirs(folder, exist_ok=True)
							setup.save(answer, self.version)
							del folder
							changed = False

							filename = answer
							del answer

							# Break INNER while loop, don't break the OUTER as that makes the program stop.
							break
					else:
						raise KioskError("Kiosk not changed, no need to save it")
				elif choice == 4:
					# Check if a kiosk has been created or loaded.
					if not filename and not changed:
						raise KioskError("No kiosk defined, cannot forge the kiosk")

					# Update installation media.
					# Identify the kind and path of the kiosk machine image (currently only works on Windows).
					target = Recognizer().identify()

					# Fail if no target was identified.
					if not target:
						raise KioskError("Unable to locate or identify install image - did you select Ubuntu Server?")

					# Report the kind of image that was discovered.
					print(
						"Discovered %s kiosk %s %s v%s (%s) install image at %s." %
						(
							target.kind, target.product, target.edition, target.version, target.cpukind, target.basedir
						)
					)
					print()

					# Only accept Server images for now.
					if target.edition != "Server":
						raise KioskError("Only Ubuntu Server 24.04.x images are supported")

					print("Preparing kiosk image for first boot.")
					print()

					# Append options to quiet both the kernel and systemd.
					if target.kind == "PI":
						kernel_options = KernelOptions()
						kernel_options.load(target.basedir + "cmdline.txt")
						#...Ask the kernel to shut up.
						kernel_options.append("quiet")
						#...Ask the kernel to only report errors, critical errors, alerts, and emergencies.
						kernel_options.append("log_level=3")
						#...Ask systemd to shut up.
						kernel_options.append("systemd.show_status=auto")
						kernel_options.save(target.basedir + "cmdline.txt")
					elif target.kind == "PC":
						# TODO: Figure out a way to provide kernel command-line options when targeting a PC (not done easily).
						pass
					else:
						raise InternalError("Unknown target kind: %s" % target.kind)

					# Write cloud-init or Subiquity configuration files to automate install completely.
					if target.install == "cloud-init":
						# Generate cloud-init's meta-data file from scratch (to be sure of what's in it).
						self.saveCloudInitMetaData(setup, target.basedir + "meta-data")

						# Generate cloud-init's network-config file from scratch (to be sure of what's in it).
						self.saveCloudInitNetworkConfig(setup, target.basedir + "network-config")

						# Generate Cloud-init's user-data file from scratch (to be sure of what's in it).
						self.saveCloudInitUserData(setup, target, target.basedir + "user-data")
					elif target.install == "subiquity":
						# Generate Subiquity's autoinstall.yaml file.
						self.saveAutoinstallYaml(setup, target, target.basedir + "autoinstall.yaml")
					else:
						raise KioskError("Unknown installer type: %s" % target.install)

					# Compute output folder.
					output = target.basedir + "KioskForge" + os.sep

					# Remove previous KioskForge folder on installation medium, if any.
					if os.path.isdir(output):
						shutil.rmtree(output)

					# Create KioskForge folder on the installation medium.
					os.makedirs(output)

					# Write configuration to the target.
					setup.save(output + os.sep + "KioskForge.cfg", self.version, False)

					# Copy KioskForge files to the installation medium.
					for file in ["KioskSetup.py", "KioskStart.py"]:
						shutil.copyfile(origin + os.sep + file, output + file)
					shutil.copytree(origin + os.sep + "kiosk", output + "kiosk")

					# Report success to the log.
					print("Preparation of boot image successfully completed - please eject/unmount %s safely." % target.basedir)
					print()
				else:
					raise KioskError("Unknown main menu choice: %d" % choice)
			except KioskError as that:
				print("*** Error: %s" % that.text)
				print()

if __name__ == "__main__":
	app = KioskForge()
	code = app.main(sys.argv)
	sys.exit(code)

