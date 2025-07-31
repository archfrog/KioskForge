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
# The main driver script for configuring and preparing a Linux installation medium for forging a kiosk from scratch.
#
# Notes:
#	1. This script assumes a clean installation medium with no modifications whatsoever prior to it being invoked.  As such, it
#      can "safely" abort upon errors as the user can simply re-flash his system using Raspberry Pi Imager once again.  There are
#      no features to safely roll back the changes made during the customization of the system for kiosk mode usage!

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import List, Optional

import copy
import glob
import hashlib
import os
import platform
import shutil
import sys
import time

from kiosklib.driver import KioskDriver
from kiosklib.errors import CommandError, InternalError, KioskError
from kiosklib.kiosk import Kiosk
from kiosklib.logger import Logger, TextWriter
from kiosklib.shell import tree_delete
from kiosklib.sources import SOURCES
from kiosklib.various import hostname_create, password_hash, password_hashed
from kiosklib.version import Version


class Target:
	"""Simple class that encapsulates all information about the target system."""

	def __init__(self, kind : str, product : str, edition : str, version : str, cpukind : str, install : str, basedir : str = "") -> None:
		# Check arguments (mostly for the sake of documenting the valid values).
		if install != "cloudinit":
			raise ValueError("Argument 'install' must be 'cloudinit'")

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
		attempt = 1
		while len(targets) == 0:
			mounts : List[str] = []
			if sys.platform == "win32":
				mounts = os.listdrives()
			elif sys.platform == "linux":
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
				if attempt == 60:
					# NOTE: Windows takes a little while to discover the medium, so we don't fail until one minute has passed.
					raise KioskError("Unable to locate a known Linux installation medium")

				if attempt == 1:
					# Output note to the end-user about KioskForge.py waiting for the user and/or operating system to react.
					print("NOTE: Waiting at most one minute for installation media to be inserted and/or discovered by the host...")
					print("NOTE: If you have not already done so, please insert the installation media to proceed.")
					print()

				attempt += 1

				time.sleep(1)
				continue

		return targets


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
	PiRecognizer()
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


def folder_normalize(folder : str) -> str:
	if not folder:
		raise ValueError("'folder' must be non-empty")

	# Make folder name absolute.
	folder = os.path.realpath(folder)

	# Ensure the folder ends in os.sep so we don't need to specify it everywhere.
	if folder[0] != os.sep:
		folder += os.sep

	return folder


class Configurator:
	"""Base class for installation configuration writers."""

	def __init__(self, kiosk : Kiosk, target : Target, version : Version) -> None:
		self.__kiosk  = kiosk			# pylint: disable=unused-private-member
		self.__target = target			# pylint: disable=unused-private-member
		self.__version = version        # pylint: disable=unused-private-member

	@property
	def kiosk(self) -> Kiosk:
		return self.__kiosk

	@property
	def target(self) -> Target:
		return self.__target

	@property
	def version(self) -> Version:
		return self.__version

	def save(self, folder : str) -> None:
		raise NotImplementedError("Abstract virtual method invoked")


class CloudinitConfigurator(Configurator):
	"""Installer configuration writer for Cloud-init, which is used for Raspberry Pi targets."""

	def __init__(self, kiosk : Kiosk, target : Target, version : Version) -> None:
		Configurator.__init__(self, kiosk, target, version)

	def _save_metadata(self, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(f"# Cloud-init meta-data file generated by {self.version.product} v{self.version.version}.")
			stream.write("# To change the values in this file, modify your .kiosk file and rerun KioskForge!")
			stream.write()

			# Write network-config values, copied verbatim from the Raspberry Pi 4B setup written by Raspberry Pi Imager.
			stream.write("dsmode: local")
			stream.write("instance_id: cloud-image")

	def _save_network_config(self, path : str) -> None:
		with TextWriter(path) as stream:
			# Write header to let the user know who generated this particular file.
			stream.write(
				f"# Cloud-init network-config file generated by {self.version.product} v{self.version.version}."
			)
			stream.write("# To change the values in this file, modify your .kiosk file and rerun KioskForge!")
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
			stream.write(f"optional: {'true' if self.kiosk.wifi_name.data else 'false'}")
			stream.write()
			stream.dedent(3)

			if self.kiosk.wifi_name.data:
				stream.indent()
				stream.write("wifis:")
				stream.indent()
				stream.write("renderer: networkd")
				stream.write("wlan0:")
				stream.indent()
				stream.write("dhcp4: true")
				stream.write("optional: false")
				stream.write(f"regulatory-domain: {self.kiosk.wifi_country.data}")
				stream.write("access-points:")
				stream.indent()
				stream.write(f'"{self.kiosk.wifi_name.data}":')
				stream.indent()
				stream.write(f'password: "{self.kiosk.wifi_code.data}"')
				stream.write(f"hidden: {'true' if self.kiosk.wifi_hidden.data else 'false'}")
				stream.dedent(5)

	def _save_user_data(self, path : str) -> None:
		with TextWriter(path) as stream:
			output = f"/home/{self.kiosk.user_name.data}"

			# Write header to let the user know who generated this particular file.
			stream.write("#cloud-config")
			stream.write(
				f"# Cloud-init user-data file generated by {self.version.product} v{self.version.version}.  DO NOT EDIT!"
			)
			stream.write("# To change the values in this file, modify your .kiosk file and rerun KioskForge!")
			stream.write()

			# Set the host name here so that the system log does not loose internal structure due to changing hostname.
			stream.write(f'hostname: "{self.kiosk.hostname.data}"')
			stream.write()

			# Write users: block, which lists the users to be created in the final kiosk system.
			stream.write("users:")
			stream.indent()
			stream.write(f"- name: {self.kiosk.user_name.data}")
			stream.indent()
			stream.write("gecos: Administrator")
			stream.write("groups: users,adm,dialout,audio,netdev,video,plugdev,cdrom,games,input,gpio,spi,i2c,render,sudo")
			stream.write("shell: /bin/bash")
			stream.write("lock_passwd: false")
			stream.write(f'passwd: "{self.kiosk.user_code.data}"')
			# NOTE: The line below is way too dangerous if somebody gets through to the shell.
			#stream.write("sudo: ALL=(ALL) NOPASSWD:ALL")
			stream.dedent()
			stream.dedent()
			stream.write()

			# Write timezone (to get date and time in logs correct).
			stream.write(f"timezone: {self.kiosk.timezone.data}")
			stream.write()

			# Write keyboard layout (I haven't found a reliable way to do this in any other way).
			stream.write("keyboard:")
			stream.indent()
			stream.write(f"layout: {self.kiosk.keyboard.data}")
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
			stream.write("Description=KioskForge kiosk forge driver")
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
			source = "/boot/firmware"

			# Write commands to copy and then make this script executable (this is done late in the boot process).
			stream.write("runcmd:")
			stream.indent()
			stream.write(f"- cp -pR {source}/KioskForge {output}")
			stream.write(f"- chown -R {self.kiosk.user_name.data}:{self.kiosk.user_name.data} {output}/KioskForge")
			stream.write(f"- chmod -R u+x {output}/KioskForge")
			stream.write(f"- chmod a-x {output}/KioskForge/KioskForge.kiosk")

			# Copy user-supplied data folder on install medium to the target, if any, and set owner and permissions.
			# NOTE: We set the execute bit on ALL user files just to be sure that 'KioskRunner.py' can actually run 'command=...'.
			if self.kiosk.user_folder.data:
				basename = os.path.basename(os.path.abspath(self.kiosk.user_folder.data))
				user_source = source + '/' + basename
				user_target = output + '/' + basename
				stream.write(f"- cp -pR {user_source} {output}")
				stream.write(f"- chown -R {self.kiosk.user_name.data}:{self.kiosk.user_name.data} {user_target}")
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

			# Do not update and upgrade packages through CloudInit as it occasionally times out (in my experience).
			stream.write("package_update: false")
			stream.write("package_upgrade: false")
			stream.write()

			# Write commands to install and/or enable Network Time Protocol (NTP).
			stream.write("ntp:")
			stream.indent()
			stream.write("enabled: true")
			stream.dedent()
			stream.write()

	def save(self, folder : str) -> None:
		folder = folder_normalize(folder)

		# Generate Cloud-init's meta-data file from scratch (to be sure of what's in it).
		self._save_metadata(folder + "meta-data")

		# Generate Cloud-init's network-config file from scratch (to be sure of what's in it).
		self._save_network_config(folder + "network-config")

		# Generate Cloud-init's user-data file from scratch (to be sure of what's in it).
		self._save_user_data(folder + "user-data")


class KioskForge(KioskDriver):
	"""This class contains the 'KioskForge' code, which prepares a boot image for running 'KioskSetup' on a kiosk machine."""

	def __init__(self) -> None:
		KioskDriver.__init__(self)

	def create(self, filename : str) -> None:
		print(f"Creating kiosk: {filename}")
		print()

		# Create the new kiosk using the default value for each fields.
		kiosk = Kiosk(self.version)

		# Check that the output does not already exist.
		if os.path.exists(filename):
			raise KioskError(f"Kiosk file already exists: {filename}")

		# Write the new kiosk.
		kiosk.save(filename)

		print("Kiosk created successfully.")

	def prepare(self, logger : Logger, origin : str, filename : str) -> None:
		print(f"Preparing kiosk: {filename}")
		print()

		# Load the kiosk.
		kiosk = Kiosk(self.version)
		kiosk.load_safe(logger, filename)

		# Assign host name to the kiosk, if the user has not provided one.
		if not kiosk.hostname.data:
			kiosk.assign("hostname", hostname_create("kiosk"))

		# Hash the user's password, if not already done.
		if not password_hashed(kiosk.user_code.data):
			kiosk.assign("user_code", password_hash(kiosk.user_code.data))

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

		# Display a synopsis of the selected kiosk, incuding the comment, hostname, and possibly more.
		print("*** Summary (some fields intentionally left out):")
		print()
		print(f"    Kiosk        : {filename}")
		print(f"    Comment      : {kiosk.comment.data}")
		print(f"    Device       : {kiosk.device.data}")
		print(f"    Type         : {kiosk.type.data}")
		print(f"    Command      : {kiosk.command.data}")
		print(f"    Host name    : {kiosk.hostname.data}")
		print(f"    Time zone    : {kiosk.timezone.data}")
		print(f"    Keyboard     : {kiosk.keyboard.data}")
		print(f"    Locale       : {kiosk.locale.data}")
		print(f"    Sound card   : {kiosk.sound_card.data}")
		print(f"    User name    : {kiosk.user_name.data}")
		print(f"    SSH key      : {'Present' if kiosk.ssh_key.data else 'Not present'}")
		print(f"    Wi-Fi name   : {kiosk.wifi_name.data}")
		print(f"    Wi-Fi country: {kiosk.wifi_country.data}")
		print(f"    Upgrade time : {kiosk.upgrade_time.data}")
		print(f"    Poweroff time: {kiosk.poweroff_time.data}")
		print(f"    Rotation     : {kiosk.screen_rotation.data}")
		print(f"    User folder  : {kiosk.user_folder.data}")
		print()

		print("*** Press ENTER to prepare kiosk installation image or Ctrl-C to abort")
		input()

		print("Preparing kiosk image for first boot.")
		print()

		# Append options to quiet both the kernel and systemd.
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
		if kiosk.device.data == "pi4b" and not kiosk.cpu_boost.data:
			with open(target.basedir + "config.txt", "rt", encoding="utf8") as stream:
				text = stream.read()
			text = text.replace("arm_boost=1", "arm_boost=0")
			with open(target.basedir + "config.txt", "wt", encoding="utf8") as stream:
				stream.write(text)

		# Create installer configurator instance and ask it to generate the appropriate installer configuration.
		configurator : Optional[Configurator] = None
		match target.install:
			case "cloudinit":
				configurator = CloudinitConfigurator(kiosk, target, self.version)
			case _:
				raise KioskError(f"Unknown installer type: {target.install}")
		configurator.save(target.basedir)

		# Compute output folder.
		output = target.basedir + "KioskForge"

		# Remove previous KioskForge folder on installation medium, if any (handles read-only files unlike 'shutil.rmtree()').
		if os.path.isdir(output):
			tree_delete(output)

		# Create KioskForge folder on the installation medium.
		os.makedirs(output)

		# Copy KioskForge files to the installation medium (copy KioskForge.py as well for posterity).
		for name in SOURCES + ["docs"]:
			if os.path.isfile(origin + os.sep + name):
				shutil.copyfile(origin + os.sep + name, output + os.sep + name)
			else:
				shutil.copytree(origin + os.sep + name, output + os.sep + name)

		# Copy documentation files found in the root folder into the "docs" folder so as to keep all documentation together.
		for name in ["LICENSE.md", "README.md"]:
			shutil.copyfile(origin + os.sep + name, output + os.sep + "docs" + os.sep + name)

		# Copy user folder, if any, to the install medium so that it can be copied onto the target.
		if kiosk.user_folder.data:
			if kiosk.user_folder.data == "KioskForge":
				raise KioskError("User folder cannot be 'KioskForge' as this is a reserved folder on the target")

			# Use 'abspath' to the handle the case that the user folder is identical to '.'.
			source = os.path.abspath(os.path.join(os.path.dirname(filename), kiosk.user_folder.data))
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
		match platform.system():
			case "Windows":
				action = "eject"
			case "Linux":
				action = "unmount"
			case _:
				raise KioskError(f"Unknown host operating system: {platform.system()}")
		print(f"Preparation of boot image successfully completed - please {action} {target.basedir} safely.")
		print()
		del action

		# NOTE: Save the changes we've made, before we redact the kiosk, so as to ensure that everything is safe and sane.
		# NOTE: This implicitly upgrades the kiosk to the current version!
		kiosk.save(filename)

		# Write REDACTED configuration to the target (to avoid issues with burglars and hackers getting access to the kiosk).
		# NOTE: The redaction is necessary to avoid making it possible for hackers, etc., to simply read the passwords in the
		# NOTE: 'KioskForge.kiosk' file that is created in the '/home/username/KioskForge' folder by the 'KioskForge.py' script.
		kiosk.redact_prepare()
		kiosk.save(output + os.sep + "KioskForge.kiosk")

		print("Kiosk prepared successfully.")

	def upgrade(self, logger : Logger, filename : str) -> None:
		print(f"Upgrading kiosk: {filename}")
		print()

		# Create a kiosk to load the kiosk to be upgraded into.
		kiosk = Kiosk(self.version)

		# Load the kiosk and get the list of errors detected.
		errors = kiosk.load_list(filename)

		# Filter out all errors of the form "Option never assigned: ", these are irrelevant when upgrading a kiosk.
		errors = list(filter(lambda x: not x.text.startswith("Option never assigned: "), errors))

		# If there are errors left, report them and abort the upgrade process.
		if errors:
			for error in errors:
				logger.error(str(error))
			print()
			raise KioskError(f"{len(errors)} error(s) detected while reading file '{filename}'")

		# Save the new, upgraded kiosk.
		kiosk.save(filename)

		print("Kiosk upgraded successfully.")

	def verify(self, logger : Logger, filename : str) -> None:
		print(f"Verifying kiosk: {filename}")
		print()

		# Create a kiosk to be loaded (which implicitly verifies the kiosk).
		kiosk = Kiosk(self.version)
		kiosk.load_safe(logger, filename)
		print("Kiosk verified successfully.")

	def _main(self, logger : Logger, origin : str, arguments : List[str]) -> None:
		# Output copyright information, etc.
		print(self.version.banner())
		print()

		# Check that we're running on Windows.
		if platform.system() != "Windows":
			raise KioskError("This script can currently only be run on a Windows machine")

		# Parse command-line arguments.
		if len(arguments) != 2:
			raise CommandError("\"KioskForge.py\" (create|prepare|upgrade|verify) kiosk-file")

		# "Parse" the command-line arguments.
		command  = arguments[0]
		filename = arguments[1]

		# Forge, create, check, or upgrade the specified kiosk.
		match command:
			case "create":
				self.create(filename)
			case "prepare":
				self.prepare(logger, origin, filename)
			case "upgrade":
				# Create list of files to process.  If input is a file, only one file, else all .kiosk files in the folder tree.
				if os.path.isfile(filename):
					filenames = [filename]
				else:
					filenames = list(filter(lambda x: x.endswith('.kiosk'), glob.glob(filename + os.sep + "**", recursive=True)))

				# Process each file while aborting on the first exception.
				for filename in filenames:
					if filename != filenames[0]:
						print()
						print("*" * 79)
						print()

					self.upgrade(logger, filename)
			case "verify":
				# Create list of fileS to process.  If input is a file, only one file, else all .kiosk files in the folder tree.
				if os.path.isfile(filename):
					filenames = [filename]
				else:
					filenames = list(filter(lambda x: x.endswith('.kiosk'), glob.glob(filename + os.sep + "**", recursive=True)))

				# Process each file while aborting on the first exception.
				for filename in filenames:
					if filename != filenames[0]:
						print()
						print("*" * 79)
						print()

					self.verify(logger, filename)
			case _:
				raise KioskError(f"Invalid command specified: {command}")


if __name__ == "__main__":
	sys.exit(KioskForge().main(sys.argv))
