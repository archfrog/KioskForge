#!/usr/bin/env python3
# KioskForge - https://kioskforge.org
# Copyright (c) 2024-2025 Vendsyssel Historiske Museum (me@vhm.dk). All Rights Reserved.
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
# The main driver script for configuring and preparing a Linux installation medium for forging a kiosk from scratch.
#
# Notes:
#	1. This script assumes a clean installation medium with no modifications whatsoever prior to it being invoked.  As such, it
#      can "safely" abort upon errors as the user can simply re-flash his system using Raspberry Pi Imager once again.  There are
#      no features to safely roll back the changes made during the customization of the system for kiosk mode usage!

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

import bcrypt

from toolbox.builder import TextBuilder
from toolbox.convert import BOOLEANS
from toolbox.driver import KioskDriver
from toolbox.errors import *
from toolbox.logger import Logger, TextWriter
from toolbox.invoke import Result
from toolbox.setup import *
# Import COMPANY, CONTACT, TESTING, and VERSION global constants.
from toolbox.version import *


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
	"""Simple base class that defines the layout of a recognizer that identifiers one or more target Linux distributions."""

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
		while answer not in BOOLEANS:
			answer = input(question + " (y/n)? ").strip().lower()
		return BOOLEANS[answer]

	def edit(self, setup : Setup) -> bool:
		changed = False
		fields = vars(setup)
		names = {}
		while True:
			try:
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
					raise InputError("Enter a valid number")

				choice = int(answer)
				if choice == 0 or choice > index:
					raise InputError("Enter a valid number in the range 1 through %d" % index)

				print("Hint: %s" % getattr(setup, names[choice]).hint)
				value = input("Enter new value (ENTER to leave unchanged): ").strip()
				if value == "":
					break

				# Attempt to assign the new field value, this may cause a 'FieldError' exception to be thrown.
				getattr(setup, names[choice]).parse(value)
				changed = True
			except FieldError as that:
				print("Error: Invalid value entered for field %s: %s" % (that.field, that.text))
			except InputError as that:
				print("Error: %s" % that.text)

		return changed

	def select(self, title : str, choices : List[str]) -> int:
		print(title + ":")

		while True:
			try:
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
					raise InputError("Please enter an integer between 1 and %d" % len(choices))

				choice = int(answer) - 1
				if choice < 0 or choice >= len(choices):
					raise InputError("Please enter a number between 1 and %d" % len(choices))

				break
			except InputError as that:
				raise KioskError(that.text)

		return choice


class KioskForge(KioskDriver):
	"""This class contains the 'KioskForge' code, which prepares a boot image for running 'KioskSetup' on a kiosk machine."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
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
			stream.write("- chmod a-x %s/KioskForge/KioskForge.kiosk" % output)

			# Copy user-supplied data folder on install medium to the target, if any, and set owner and permissions.
			# NOTE: We set the execute bit on ALL user files just to be sure that 'KioskRunner.py' can actually run 'command=...'.
			if setup.user_folder.data:
				basename = os.path.basename(os.path.abspath(setup.user_folder.data))
				user_source = source + '/' + basename
				user_target = output + '/' + basename
				stream.write("- cp -pR %s %s" % (user_source, output))
				stream.write("- chown -R %s:%s %s" % (setup.user_name.data, setup.user_name.data, user_target))
				stream.write("- chmod -R u+x %s" % user_target)
				del user_source
				del user_target

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
			source = "/cdrom/"
			output = "/home/%s" % setup.user_name.data

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
			stream.write("- mkdir -p %s" % output)
			stream.write("- tar -czf %s/installer-logs.tar.gz /var/log/installer/" % output)
			stream.write("- journalctl -b > %s/installer-journal.log" % output)
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

			# Copy KioskForge to the target so that it can be invoked.
			stream.write("late-commands:")
			stream.indent()
			stream.write("- curtin in-target -- mkdir -p %s" % output)
			stream.write("- curtin in-target -- cp -pR %s/KioskForge %s" % (source, output))

			# TODO: Copy user-supplied data folder to the target, if any.
			if setup.user_folder.data:
				raise InternalError("user_folder is not yet implemented for PC targets")
				stream.write("- curtin in-target -- cp -pR %s %s" % (setup.user_folder.data, output))

			# Continue the installation of the kiosk (late-commands is executed just before the system is rebooted).
			stream.write("- %s/KioskForge/KioskSetup.y" % output)
			stream.dedent()

			stream.dedent()

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# NOTE: No need for a logger in KioskForge as it does very few things and some of them interactively.
		del logger

		# Output copyright information, etc.
		print(self.version.banner())
		print()

		# Check that we're running on Windows.
		if platform.system() != "Windows":
			raise KioskError("This script can currently only be run on a Windows machine")

		# Parse command-line arguments.
		if len(arguments) > 1:
			raise SyntaxError("\"KioskForge.py\"")

		# Bloody hack to support double-clicking on a '.kiosk' file in Windows Explorer follows...
		if len(arguments) == 1:
			first_path = arguments[0]
		else:
			first_path = ""

		# Show the main menu.
		# TODO: Warn the user against saving if the kiosk is blank.
		setup = Setup()
		editor = Editor()
		changed = False
		filename = ""
		while True:
			try:
				if first_path:
					setup.load(first_path)
					filename = first_path
					changed = False
					first_path = ""

				print("Kiosk file: %s" % (filename if filename != "" else "(none)"))
				print()

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
					if changed:
						raise KioskError("Kiosk has unsaved changes")

					# Create new kiosk.
					setup = Setup()
					filename = ""
					changed = False

					print("New kiosk successfully created in memory.")
					print()
				elif choice == 1:
					# Load existing kiosk from disk.
					answer = input("Please enter or paste full path of kiosk file (*.kiosk): ").strip()
					print()

					if answer == "":
						continue

					try:
						setup.load(answer)
						filename = answer

						print("Kiosk successfully loaded from disk")
					except FileNotFoundError:
						raise KioskError("Unable to load the specified file - is the path correct?")
					except FieldError as that:
						raise KioskError("Invalid value entered for field %s: %s" % (that.field, that.text))
					except InputError as that:
						raise KioskError(that.text)
					print()

					changed = False
				elif choice == 2:
					# Edit kiosk.
					# Allow the user to re-edit the kiosk as long as there are errors.
					try:
						changed |= editor.edit(setup)
					except FieldError as that:
						print("Error: Invalid value entered for field %s: %s" % (that.field, that.text))
						continue
					except InputError as that:
						print("Error: %s" % that.text)
						continue

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
					answer = input("Please enter/paste full path: (blank = %s): " % filename).strip()
					print()

					if answer == "":
						answer = filename

					if not answer.endswith(".kiosk"):
						raise KioskError("KioskForge kiosk configuration files MUST end in .kiosk")

					# Create new folder, if any, and save the configuration.
					folder = os.path.dirname(answer)
					os.makedirs(folder, exist_ok=True)
					setup.save(answer, self.version)
					del folder
					changed = False

					filename = answer
					del answer
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

						# If cpu_boost is false, disable the default CPU overclocking in the config.txt file.
						text = open(target.basedir + "config.txt", "rt").read()
						text = text.replace("arm_boost=1", "#arm_boost=1")
						open(target.basedir + "config.txt", "wt").write(text)
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
					output = target.basedir + "KioskForge"

					# Remove previous KioskForge folder on installation medium, if any.
					if os.path.isdir(output):
						shutil.rmtree(output)

					# Create KioskForge folder on the installation medium.
					os.makedirs(output)

					# Write configuration to the target.
					setup.save(output + os.sep + "KioskForge.kiosk", self.version, False)

					# Copy KioskForge files to the installation medium (copy KioskForge.py as well for posterity).
					for name in ["KioskForge.py", "KioskOpenbox.py", "KioskSetup.py", "KioskStart.py", "KioskUpdate.py", "toolbox"]:
						if os.path.isfile(origin + os.sep + name):
							shutil.copyfile(origin + os.sep + name, output + os.sep + name)
						else:
							shutil.copytree(origin + os.sep + name, output + os.sep + name)

					# Copy user folder, if any, to the install medium so that it can be copied onto the target.
					if setup.user_folder.data:
						if setup.user_folder.data == "KioskForge":
							raise KioskError("User folder cannot be 'KioskForge' as this is a reserved folder on the target")

						# Use 'abspath' to the handle the case that the user folder is identical to '.'.
						source = os.path.abspath(os.path.join(os.path.dirname(filename), setup.user_folder.data))
						# Extract the last portion of the source's full path to get the name of the folder on the install medium.
						basename = os.path.basename(source)
						destination = target.basedir + os.sep + basename
						del basename

						if os.path.isdir(destination):
							shutil.rmtree(destination)

						shutil.copytree(source, destination)
						del source
						del destination

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

