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
from typing import List, Optional

import copy
import hashlib
import os
import platform
import shlex
import shutil
import sys
import time

import bcrypt

from toolbox.convert import BOOLEANS
from toolbox.driver import KioskDriver
from toolbox.errors import CommandError, FieldError, InputError, InternalError, KioskError
from toolbox.logger import Logger, TextWriter
from toolbox.setup import Setup
from toolbox.version import Version


def password_crypt(text : str) -> str:
	if len(text) < 1 or len(text) > 72:
		raise ValueError("Argument 'text' must be between 1 and 72 charaters in length")

	data = text.encode('utf-8')
	return bcrypt.hashpw(data, bcrypt.gensalt()).decode('utf-8')


class Target:
	"""Simple class that encapsulates all information about the target system."""

	def __init__(self, kind : str, product : str, edition : str, version : str, cpukind : str, install : str, basedir : str = "") -> None:
		# Check arguments (mostly for the sake of documenting the valid values).
		if install not in ["cloudinit", "subiquity"]:
			raise ValueError("Argument 'install' must be either 'cloudinit' or 'subiquity'")

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

	@basedir.setter
	def basedir(self, value : str) -> None:
		if self.__basedir != "":
			raise ValueError(".basedir already set")
		self.__basedir = value

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


class Recognizer:
	"""Simple base class that defines the layout of a recognizer that identifiers one or more target Linux distributions."""

	def __init__(self) -> None:
		pass

	def _identify(self, path : str) -> Optional[Target]:
		raise NotImplementedError("Abstract method called")

	def identify(self) -> List[Target]:
		# Scan all mount points/drives and see if there are any of the reserved files we're looking for.
		targets : List[Target] = []
		attempts = 0
		while True:
			if platform.system() == "Windows":
				mounts = os.listdrives()
			elif platform.system() == "Linux":
				# TODO: mounts = 'df -a -T -h -t vfat'; grep -Fv "/boot/efi"'
				raise InternalError("Feature not finished - Linux host not yet supported")
			else:
				raise InternalError(f"Unknown target platform: {platform.system()}")

			# Check each mount point/Windows drive for a recognizable installation media.
			for mount in mounts:
				for recognizer in RECOGNIZERS:
					target = recognizer._identify(mount)
					if target:
						targets.append(target)

			# If zero kiosk images were found, let the user fix the error and try again.
			if len(targets) == 0:
				# Wait three seconds once so as to not force the user to hit Ctrl-C because we keep waiting too long.
				if attempts == 1:
					raise KioskError("Unable to locate a known Linux installation medium")
				attempts += 1

				# NOTE: Windows takes a little while to discover the written image, so we try once more if we fail at first.
				print("NOTE: Waiting three seconds for installation media to be discovered by the host operating system...")
				print("NOTE: If you have not already done so, please insert the installation media to proceed.")
				print()
				time.sleep(3)
				continue

			break

		return targets


class PcRecognizer(Recognizer):
	"""Derived class which recognizes Ubuntu Server 24.04.1 in a PC install image."""

	def __init__(self) -> None:
		Recognizer.__init__(self)

	def _identify(self, path : str) -> Optional[Target]:
		info_name = path + ".disk" + os.sep + "info"

		if not os.path.isfile(info_name):
			return None

		# Parse the /.disk/info file to get the information we're looking for.
		with open(info_name, "rt", encoding="utf8") as stream:
			info_data = stream.read().strip()
			fields = shlex.split(info_data)
			if len(fields) == 7:
				# Ubuntu 25.04+ only provides seven fields because it is not an LTS release (sigh).
				(product, version, codename, dash, release, cpukind, date_num) = fields
				support = "STS"			# Short Term Support (STS) as opposed to Long Term Support (LTS).
			elif len(fields) == 8:
				# Ubuntu 24.04 provides eight fields because it is an LTS release.
				(product, version, support, codename, dash, release, cpukind, date_num) = fields
			else:
				print("Warning: Unsupported .disk/info file - too few or too many fields")
				return None
			del codename
			del dash
			del release
			del date_num
			del support

		# Munge about with the product string so that it fits our needs...
		if product == "Ubuntu-Server":
			product = "Ubuntu"
			edition = "Server"
		elif product == "Ubuntu":
			edition = "Desktop"
		else:
			return None

		# Return a new target instance with the information we learned from .disk/info.
		return Target("PC", product, edition, version, cpukind, "subiquity", path)


SHA512_UBUNTU_DESKTOP_24_04_1_ARM64 = 'ce3eb9b96c3e458380f4cfd731b2dc2ff655bdf837cad00c2396ddbcded64dbc1d20510c22bf211498ad788c8c81ba3ea04c9e33d8cf82538be0b1c4133b2622'
SHA512_UBUNTU_SERVER__24_04_1_ARM64 = '1d6c8d010c34f909f062533347c91f28444efa6e06cd55d0bdb39929487d17a8be4cb36588a9cbfe0122ad72fee72086d78cbdda6d036a8877e2c9841658d4ca'
SHA512_UBUNTU_DESKTOP_24_04_2_ARM64 = '32825b5b770f94996f05a9f2fa95e8f7670944de5990a258d10d95c5bd0062123a707d8b943d23e7b0d54e8c3ff8440b0fd7ebbb8dc42bc20da8a77b3f3f6408'
SHA512_UBUNTU_SERVER__24_04_2_ARM64 = '5c62b93b8d19e8d7ac23aa9759a23893af5dd1ab5f80e4fb71f7b4fd3ddd0f84f7c82f9342ea4c9fdba2c350765c2c83eaaa6dcaac236f9a13f6644386e6a1d2'
SHA512_UBUNTU_DESKTOP_25_04_0_ARM64 = 'fa8750e5f71adc4d0cff50c985e499d7dc0ce18132489a52d4c3df9d0c321100d5b1d93c5804dd9c88986e2a8e67cbd413d325576081f3d2b20046987bb26b63'
SHA512_UBUNTU_SERVER__25_04_0_ARM64 = 'ef1f10d7cc59d8761490b0e0f3be0882d4781870e920d66f0b7ae440a940bf19fa689cc16ee06a0c81b5333b7ecc65fdb4137e050db1133a77fd117c03034157'

PI_OPERATING_SYSTEMS = {
	SHA512_UBUNTU_DESKTOP_24_04_1_ARM64 : Target("PI", "Ubuntu", "Desktop", "24.04.1", "arm64", "cloudinit"),
	SHA512_UBUNTU_SERVER__24_04_1_ARM64 : Target("PI", "Ubuntu", "Server", "24.04.1", "arm64", "cloudinit"),
	SHA512_UBUNTU_DESKTOP_24_04_2_ARM64 : Target("PI", "Ubuntu", "Desktop", "24.04.2", "arm64", "cloudinit"),
	SHA512_UBUNTU_SERVER__24_04_2_ARM64 : Target("PI", "Ubuntu", "Server", "24.04.2", "arm64", "cloudinit"),
	SHA512_UBUNTU_DESKTOP_25_04_0_ARM64 : Target("PI", "Ubuntu", "Desktop", "25.04", "arm64", "cloudinit"),
	SHA512_UBUNTU_SERVER__25_04_0_ARM64 : Target("PI", "Ubuntu", "Server", "25.04", "arm64", "cloudinit"),
}

class PiRecognizer(Recognizer):
	"""Derived class that recognizes some Ubuntu Desktop/Server releases on a Raspberry Pi 4B installation medium."""

	def __init__(self) -> None:
		Recognizer.__init__(self)

	def _identify(self, path : str) -> Optional[Target]:
		if not os.path.isfile(path + "cmdline.txt"):
			return None

		if not os.path.isfile(path + "initrd.img"):
			return None

		with open(path + "initrd.img", "rb") as stream:
			sha512 = hashlib.sha512(stream.read()).hexdigest()

		# If unable to recognize the SHA512 sum of the 'initrd.img' file, refuse to recognize this installation medium.
		if not PI_OPERATING_SYSTEMS.get(sha512):
			return None

		target = copy.copy(PI_OPERATING_SYSTEMS[sha512])
		target.basedir = path
		return target


# List of systems that can be recognized and thus are supported.
RECOGNIZERS = [
	PiRecognizer(),
	PcRecognizer()
]


class KernelOptions:
	"""Small class that handles adding kernel options to the Raspberry PI 'cmdline.txt' file."""

	def __init__(self) -> None:
		self.__options : List[str] = []

	@property
	def options(self) -> List[str]:
		return self.__options

	def append(self, option : str) -> None:
		self.__options.append(option)

	def load(self, path : str) -> None:
		with open(path, "rt", encoding="utf-8") as stream:
			self.__options = stream.read().strip().split(' ')

	def save(self, path : str) -> None:
		with open(path, "wt", encoding="utf-8") as stream:
			stream.write(' '.join(self.__options))


def menu_select(title : str, choices : List[str]) -> int:
	print(title + ":")

	while True:
		try:
			print()
			index = 0
			while index < len(choices):
				value = choices[index]
				index += 1
				print(f"{index:2d}) {value}")
			print()
			del index

			answer = input("Enter choice (ENTER to quit): ").strip()
			print()

			if answer == "":
				return -1

			if not answer.isdigit():
				raise InputError(f"Please enter an integer between 1 and {len(choices)}")

			choice = int(answer) - 1
			if choice < 0 or choice >= len(choices):
				raise InputError(f"Please enter a number between 1 and {len(choices)}")

			break
		except InputError as that:
			raise KioskError(that.text) from that

	return choice


class KioskForge(KioskDriver):
	"""This class contains the 'KioskForge' code, which prepares a boot image for running 'KioskSetup' on a kiosk machine."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)
		self.version = Version(self.project)

	def save_cloudinit_metadata(self, setup : Setup, path : str) -> None:
		del setup

		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(f"# Cloud-init meta-data file generated by {self.version.product} v{self.version.version}.  DO NOT EDIT!")
			stream.write()

			# Write network-config values, copied verbatim from the Raspberry Pi 4B setup written by Raspberry Pi Imager.
			stream.write("dsmode: local")
			stream.write("instance_id: cloud-image")

	def save_cloudinit_network_config(self, setup : Setup, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(
				f"# Cloud-init network-config file generated by {self.version.product} v{self.version.version}.  DO NOT EDIT!"
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
			stream.write(f"optional: {'true' if setup.wifi_name.data else 'false'}")
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
				stream.write(f'"{setup.wifi_name.data}":')
				stream.indent()
				stream.write(f'password: "{setup.wifi_code.data}"')
				stream.dedent(5)

	def save_cloudinit_userdata(self, setup : Setup, target : Target, path : str) -> None:
		with TextWriter(path) as stream:
			output = f"/home/{setup.user_name.data}"

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(
				f"# Cloud-init user-data file generated by {self.version.product} v{self.version.version}.  DO NOT EDIT!"
			)
			stream.write()

			# Write users: block, which lists the users to be created in the final kiosk system.
			stream.write("users:")
			stream.indent()
			stream.write(f"- name: {setup.user_name.data}")
			stream.indent()
			stream.write("gecos: Administrator")
			stream.write("groups: users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo")
			stream.write("shell: /bin/bash")
			stream.write("lock_passwd: false")
			stream.write(f'passwd: "{password_crypt(setup.user_code.data)}"')
			# NOTE: The line below is way too dangerous if somebody gets through to the shell.
			#stream.write("sudo: ALL=(ALL) NOPASSWD:ALL")
			stream.dedent()
			stream.dedent()
			stream.write()

			# Write timezone (to get date and time in logs correct).
			stream.write(f"timezone: {setup.timezone.data}")
			stream.write()

			# Write keyboard layout (I haven't found a reliable way to do this in any other way).
			stream.write("keyboard:")
			stream.indent()
			stream.write(f"layout: {setup.keyboard.data}")
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
			stream.write(f"ExecStart={output}/KioskForge/KioskSetup.py")
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
				raise InternalError(f"Unknown kiosk machine kind: {target.kind}")

			# Write commands to copy and then make this script executable (this is done late in the boot process).
			stream.write("runcmd:")
			stream.indent()
			stream.write(f"- cp -pR {source}/KioskForge {output}")
			stream.write(f"- chown -R {setup.user_name.data}:{setup.user_name.data} {output}/KioskForge")
			stream.write(f"- chmod -R u+x {output}/KioskForge")
			stream.write(f"- chmod a-x {output}/KioskForge/KioskForge.kiosk")

			# Copy user-supplied data folder on install medium to the target, if any, and set owner and permissions.
			# NOTE: We set the execute bit on ALL user files just to be sure that 'KioskRunner.py' can actually run 'command=...'.
			if setup.user_folder.data:
				basename = os.path.basename(os.path.abspath(setup.user_folder.data))
				user_source = source + '/' + basename
				user_target = output + '/' + basename
				stream.write(f"- cp -pR {user_source} {output}")
				stream.write(f"- chown -R {setup.user_name.data}:{setup.user_name.data} {user_target}")
				stream.write(f"- chmod -R u+x {user_target}")
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
				# TODO: Either reenable CloudInit updates or disable AutoInstall updates.
				# NOTE: Temporarily disabled it possibly causes an issue where CloudInit times out.
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

	def save_subiquity_yaml(self, setup : Setup, target : Target, path : str) -> None:
		del target

		with TextWriter(path) as stream:
			source = "/cdrom/"
			output = f"/home/{setup.user_name.data}"

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(f"# Cloud-init user-data file generated by {self.version.product} v{self.version.version}.  DO NOT EDIT!")
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
			stream.write(f"- mkdir -p {output}")
			stream.write(f"- tar -czf {output}/installer-logs.tar.gz /var/log/installer/")
			stream.write(f"- journalctl -b > {output}/installer-journal.log")
			stream.dedent()
			stream.write("identity:")
			stream.indent()
			stream.write(f"hostname: {setup.hostname.data}")
			stream.write("realname: Kiosk")
			stream.write(f"username: {setup.user_name.data}")
			stream.write(f'password: "{password_crypt(setup.user_code.data)}"')
			stream.dedent()
			stream.write("kernel:")
			stream.indent()
			stream.write("package: linux-generic")
			stream.dedent()

			# Write keyboard configuration.
			stream.write("keyboard:")
			stream.indent()
			stream.write(f"layout: {setup.keyboard.data}")
			stream.write("toggle: null")
			stream.write("variant: ''")
			stream.dedent()

			# Write locale information.
			stream.write(f"locale: {setup.locale.data}")

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
				stream.write(f'"{setup.wifi_name.data}":')
				stream.indent()
				stream.write(f'password: "{setup.wifi_code.data}"')
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
			stream.write(f"- '{setup.ssh_key.data}'")
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
			stream.write(f"- curtin in-target -- mkdir -p {output}")
			stream.write(f"- curtin in-target -- cp -pR {source}/KioskForge {output}")

			# TODO: Copy user-supplied data folder to the target, if any.
			if setup.user_folder.data:
				stream.write(f"- curtin in-target -- cp -pR {setup.user_folder.data} {output}")
				raise InternalError("user_folder is not yet implemented for PC targets")

			# Continue the installation of the kiosk (late-commands is executed just before the system is rebooted).
			stream.write(f"- {output}/KioskForge/KioskSetup.py")
			stream.dedent()

			stream.dedent()

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Output copyright information, etc.
		print(self.version.banner())
		print()

		# Check that we're running on Windows.
		if platform.system() != "Windows":
			raise KioskError("This script can currently only be run on a Windows machine")

		# Parse command-line arguments.
		if len(arguments) != 1:
			raise CommandError("\"KioskForge.py\" kiosk-file")

		# "Parse" the command-line arguments.
		filename = arguments[0]

		# Load the specified kiosk.
		setup = Setup()
		setup.load_safe(logger, filename)

		print(f"Kiosk file: {filename}")
		print()

		# Update installation media.

		# Identify the kind and path of the kiosk machine image (currently only works on Windows).
		targets = Recognizer().identify()
		match len(targets):
			case 0:
				raise KioskError("Unable to locate/identify installation medium on this machine")
			case 1:
				target = targets[0]
			case _:
				raise KioskError("More than one installation medium detected - please remove all but one")
		del targets

		# Report the kind of image that was discovered.
		print(
			f"Discovered {target.kind} {target.product} {target.edition} {target.version}" +
			f" ({target.cpukind.upper()}) installation medium at {target.basedir}"
		)
		print()

		# Only accept Ubuntu Server images for AMD64/ARM64 for now.
		accept = True
		accept &= (target.product == "Ubuntu")
		accept &= (target.edition == "Server")
		accept &= (target.version in ["24.04.1", "24.04.2"])
		accept &= (target.cpukind in ["amd64", "arm64"])
		if not accept:
			raise KioskError("Only Ubuntu Server 24.04.x images for AMD64/ARM64 CPUs are supported")
		del accept

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
			if setup.device.data == "pi4b" and not setup.cpu_boost.data:
				with open(target.basedir + "config.txt", "rt", encoding="utf8") as stream:
					text = stream.read()
				text = text.replace("arm_boost=1", "arm_boost=0")
				with open(target.basedir + "config.txt", "wt", encoding="utf8") as stream:
					stream.write(text)
		elif target.kind == "PC":
			# TODO: Figure out a way to provide kernel command-line options when targeting a PC (not done easily).
			pass
		else:
			raise InternalError(f"Unknown target kind: {target.kind}")

		# Write cloudinit or Subiquity configuration files to automate install completely.
		if target.install == "cloudinit":
			# Generate Cloud-init's meta-data file from scratch (to be sure of what's in it).
			self.save_cloudinit_metadata(setup, target.basedir + "meta-data")

			# Generate Cloud-init's network-config file from scratch (to be sure of what's in it).
			self.save_cloudinit_network_config(setup, target.basedir + "network-config")

			# Generate Cloud-init's user-data file from scratch (to be sure of what's in it).
			self.save_cloudinit_userdata(setup, target, target.basedir + "user-data")
		elif target.install == "subiquity":
			# Generate Subiquity's autoinstall.yaml file.
			self.save_subiquity_yaml(setup, target, target.basedir + "autoinstall.yaml")
		else:
			raise KioskError(f"Unknown installer type: {target.install}")

		# Compute output folder.
		output = target.basedir + "KioskForge"

		# Remove previous KioskForge folder on installation medium, if any.
		if os.path.isdir(output):
			shutil.rmtree(output)

		# Create KioskForge folder on the installation medium.
		os.makedirs(output)

		# Write configuration to the target.
		setup.save(output + os.sep + "KioskForge.kiosk", self.version)

		# Copy KioskForge files to the installation medium (copy KioskForge.py as well for posterity).
		names = ["KioskForge.py", "KioskOpenbox.py", "KioskSetup.py", "KioskStart.py", "KioskUpdate.py", "toolbox"]
		for name in names:
			if os.path.isfile(origin + os.sep + name):
				shutil.copyfile(origin + os.sep + name, output + os.sep + name)
			else:
				shutil.copytree(origin + os.sep + name, output + os.sep + name)
		del names

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
		print(f"Preparation of boot image successfully completed - please eject/unmount {target.basedir} safely.")
		print()


if __name__ == "__main__":
	sys.exit(KioskForge().main(sys.argv))

