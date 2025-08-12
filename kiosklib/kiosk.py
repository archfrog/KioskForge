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

from string import punctuation
from typing import List

from kiosklib.convert import KEYBOARDS
from kiosklib.locales import LOCALES
from kiosklib.setup import BooleanField, ChoiceField, Fields, NaturalField, OptionalRegexField, OptionalStringField
from kiosklib.setup import OptionalTimeField, PasswordField, RegexField, StringField
from kiosklib.timezones import TIMEZONES
from kiosklib.various import password_create
from kiosklib.version import Version


COMMAND_HELP = """
This is the action that the kiosk should take when it starts up.

For 'web' type kiosks (see 'type'), this field specifies the local or
remote URL to display in Chromium.

For 'x11' and 'cli' type kiosks, this field specifies an actual Linux
command (script or binary) that is launched upon starting up.  The latter
two types are used for custom solutions that do not necessarily require a
web browser, such as a Pi kiosk that detects motion and then plays a sound.
""".strip()


COMMENT_HELP = """
A short description of the the kiosk machine.  The string may at most be 128
characters long and cannot contain quotes (") and vertical bars (|).

Please describe the kiosk's intended usage.  The string is later used to
identify the kiosk when you browse the local network for active kiosks.
""".strip()


CPU_BOOST_HELP = """
If the CPU should be overclocked.

This field currently only works with Raspberry Pi 4B targets.

Enabling the field will increase the processing speed (CPU clock rate) of
the target kiosk by 20 percent from 1.5 gigahertz to 1.8 gigahertz.  This
translates to extra performance at the cost of a signficantly hotter CPU.
If processor speed matters, and cooling is good or heat is not a
significant issue, then you should enable this setting.

This setting is most useful with 'web' type kiosks as these need lots of
power to process complex websites and display these.
""".strip()


DEVICE_HELP = """
Specifies the hardware type of the kiosk.  Valid values are:

    pi4b: Raspberry Pi 4B with at least 2 GB RAM.
    pi5 : Raspberry Pi 5 with at least 2 GB RAM.

This setting affects the 'sound_card' and 'cpu_boost' field as follows:

1. 'sound_card' depends entirely on the target device type.  See the
   'sound_card' field for more information.
2. 'cpu_boost' can only be activated for Raspberry Pi 4B kiosks.
""".strip()


CHROMIUM_AUTOPLAY_HELP = """
Whether or not Chromium should autoplay videos without user interaction.

This option is meant primarly for simple VideoLooper-style kiosks (VL does
not yet support the Raspberry Pi 5) where a video needs to be played as
soon as Chromium opens the web site with the video on it, without waiting
for user interaction such as clicking the 'Play' button.
""".strip()


HOSTNAME_HELP = """
The unqualified host name, which may consists of US English letters, digits,
and dashes (-).  It must be 1 to 63 characters long.

Most commonly, you don't need to worry about the kiosk host name at all.

If this field is left empty, the forge process will automatically create a
host name of the form "kioskN", where N is a number in the range 0 through
99,999.

IMPORTANT:
You should never have two machines with the same host name on a local area
network (LAN).  This may cause issues with Windows and other systems.
""".strip()


IDLE_TIMEOUT_HELP = """
The number of seconds of idle time before Chromium is restarted.  A value
in the range 0 (disabled) to 86.400 (one full day).

This field has no effect for kiosk types other than 'web'.

Some visitors to kiosks like to sabotage the kiosk, which is the primary
reason why this field exists.  Also, it is nice to be able to reset a web
kiosk back to its starting page after a given period of user inactivity.
""".strip()


KEYBOARD_HELP = """
The keyboard layout.  This is primarily important to those who access the
kiosk remotely using SSH and also the web browser, if any.

The complete list of valid keyboard layouts can be found at:

https://kioskforge.org/keyboards.html
""".strip()


LOCALE_HELP = """
The locale to use on the kiosk machine.

The locale affects the display of dates, currencies, the default sorting
order, etc.

You should pick the most narrow match, say "fr_CA" over "fr" if you're a
Canadian living in a region of Canada where French is the main language.

Please notice that KioskForge has only been tested with UTF-8 locales:
Those that end in '.UTF-8'.  No warranties are given for other locales.

A complete list of valid locales can be found at:

https://manpages.ubuntu.com/manpages/noble/man3/DateTime::Locale::Catalog.3pm.html
""".strip()


MOUSE_HELP = """
If the mouse should be enabled.

Valid values are 'true' (enabled) and 'false' (disabled).

You generally want to avoid enabling the mouse on kiosks with touch screens
as this makes the mouse cursor visible to the user.
""".strip()


POWEROFF_TIME_HELP = """
The time of day to power off the system.

An empty string disables this field, otherwise it must be a time string of
the form HH:MM, which is the hour and minute of when the operation is done.

This field is primarily intended for environments where there are no
visitors to the kiosk during the night.  In such cases, the kiosk needs to be
powered on by a time switch in the morning.

If you use a time switch, please remember to gracefully shut down the kiosk.
Most computers benefit from being shut down gracefully rather than abruptly
by loss of power.

You do not need to use this field if you set "upgrade_post" to "poweroff":
in this case, you can safely ignore this field.

The preferred way of shutting down a kiosk is through the "upgrade_post"
field as it ensures the system is upgraded, if there is access to the
internet from the kiosk, before it, gets powered down, something that the
"poweroff_time" field does not.  The "poweroff_time" field works
independently of the upgrade process, which can cause serious issues if
the kiosk is shut down in the middle of an upgrade.

The only reason this field currently exists is because some users need it.

IMPORTANT:
Raspberry Pi 4Bs do not have a built-in real-time clock (RTC) so they need
network access to set the system time after they have rebooted, which again
affects the scheduled processes as they cannot run at a known time if the
kiosk's real-time clock is not set accurately.  The result is that RPI4Bs
should only be used for kiosks that are normally on the internet.
""".strip()


SCREEN_ROTATION_HELP = """
Specify rotation of screen and/or touch panel.

The valid values are:

1. none : The screen is mounted straight up and is not rotated in any way.
2. left : The screen has been rotated 90 degrees to the left.
3. flip : The screen has been mounted upside-down.
4. right: The screen has been rotated 90 degrees to the right.

Please notice that this setting affects both standard screens (without a
touch panel) and screens with a touch panel.
""".strip()


SOUND_CARD_HELP = """
The sound card to use, if any.

This available sound cards depends entirely on the target system:

    pi4b: none, jack, hdmi1, or hdmi2.
    pi5 : none, hdmi1, or hdmi2.

If you don't need any audio in your kiosk, you should use the value 'none'.

Please notice that the jack stick on the Pi4B requires amplification.
""".strip()


SOUND_LEVEL_HELP = """
The logarithmic audio level ranging from 0 through 100.

This value is only valid if 'sound_card' is different from 'none'.

The value 0 should only be used when 'sound_card' has been set to 'none' as
it effectively disables audio altogether.

A good value to use, which should avoid clipping (reduction of audio
quality), is 80 if 'sound_card' has been set to something other than 'none'.
If 'sound_card' is 'none', this value will be completely ignored.
""".strip()


SSH_KEY_HELP = """
The public SSH key for accessing the kiosk using the 'ssh' command.

If empty, SSH access is disabled and you'll need a monitor and a keyboard to
log into the kiosk machine.

The key can be generated using the 'ssh-keygen' command, which is part of
Linux but also available on numerous public websites that you can use to
generate an SSH key pair.  Just do a google of "ssh-keygen online".

To access the kiosk using SSH, you can use 'Putty' (GUI) or 'Windows OpenSSH'
(CLI/non-GUI).

IMPORTANT:
If you lose your private key, you cannot access the kiosk using SSH anymore.
""".strip()


SWAP_SIZE_HELP = """
The size in gigabytes of the system swap file, if any.

The value zero (0) disables the swap file altogether.  A typical size of the
swap file is twice that of the size of system RAM.  However, a value of 4
(gigabytes) should be sufficient for most kiosks.

You need to ensure that there is sufficient space on the installation medium
(MicroSD card or USB key) to store the swap file itself.  As a rule of thumb,
you can safely use 4 gigabytes on an installation medium that is 16 gigabytes
or larger.  The Linux operating system itself uses less than 8 gigabytes but
there must always be ample room for system logs, fetched upgrades, and so on.
""".strip()


TIMEZONE_HELP = """
The time zone of the kiosk.

This is typically the local time zone of where the kiosk is located.

Please be aware that the time zone affects time stamps in logs, the time
seen by the the web browser, and so on.

Use the most specific, precise time zone from the list below.  There are time
zones for all regions of Earth, just search for "Africa/" or "Europe/", etc.

The complete list of valid time zones can be found at:

https://kioskforge.org/timezones.html
""".strip()


TYPE_HELP = """
The type of kiosk.

The valid values are:

1. web: A legacy kiosk that displays a given website on X11 using Chromium
   as the web browser.  X11 does not offer GPU acceleration on Pi5.
2. x11: A custom, X11 app installed during forging of the kiosk.
3. cli: A custom, console app installed during forging of the kiosk.
4. web-wayland: A modern kiosk that displays a website on Wayland using
   Chromium as the web browser.  Wayland does offer GPU accelleration.

NOTE: The "web-wayland" type of kiosk is not yet finished: don't use it!

The website URL or custom command is specified using the 'command' field.

The 'web' type is by far the most commonly used type, but the 'cli' type is
very useful for things like making a designated kiosk that starts playing a
given sound whenever somebody approaches the kiosk machine (using a motion
detector).
""".strip()


UPGRADE_POST_HELP = """
The action that the kiosk should take when it has finished up cleaning up
logs and upgrading the kiosk.

There are two valid choices:

1. reboot  : The kiosk will reboot back to kiosk mode after the upgrade.
2. poweroff: The kiosk will shut down after the upgrade.

Most users will want the kiosk to simply reboot but some users will want
the kiosk to shut down during the night and to be started by a time switch.

Please notice that the "poweroff" choice requires that the power is cycled
so that the kiosk starts up again, this should happen when the kiosk is to
start up again, and is typically implemented using a simple time switch.

If you set this field to "poweroff", you can safely disregard the
"poweroff_time" field as there's no sense in powering off twice in a day.
""".strip()


UPGRADE_TIME_HELP = """
The time of day to upgrade the system.

If empty, this field is disabled.  This is not recommended as virtually
all kiosks should be rebooted at least once a day so as to reduce the
size of system logs and other things that grow quietly in the background.

During the upgrade, the following things take place:

1. System logs are reduced to the size given in the 'vacuum_size' field.
2. If there is no network access, the system upgrade skips to step 7.
3. Snaps are upgraded.
4. Snap's excessive disk usage is reduced to the bare minimum.
5. The apt repository is emptied so as to not take up disk space.
6. Ubuntu's apt package manager packages are upgraded.
7. The system is rebooted or powered off according to 'upgrade_post'.

Please notice that the maintenance process gracefully handles lack of
internet.  In that case, no upgrades will performed.
""".strip()


USER_CODE_HELP = """
The password for the user whose name is given in the 'user_name' field.

There is technically no maximum limit to the length of the password, but you
should always use between 16 and 132 characters.

This setting is of very little signficance if you provide an SSH public key
using the 'ssh_key' field as this installs a key file on the kiosk so that
you can log into the kiosk using SSH without entering a password.  However,
the password will still be required to perform administrative commands on the
kiosk.  For this reason, you should use an SSH public key and a fairly safe
password.

If you opt to not enable the secure SSH access method, you should provide a
secure password of minimum 32 random characters so as to not allow hackers
into the kiosk.
""".strip()


USER_FOLDER_HELP = """
The path of a user folder to copy from the host to the kiosk.

If empty, nothing will be copied, otherwise the given folder is copied.

A "user folder" is a custom folder that may contain various files needed by
the kiosk, but which are not part of KioskForge.

For instance, a 'web' type kiosk that browses local files only, need these
files to be copied from the host to the kiosk.  Similarly, 'cli' or 'x11'
type kiosks also need the custom app to be copied to the kiosk.

The last part of the path specified, which is relative to the main '.kiosk'
file that contains the kiosk configuration, is used as the name of the folder
that's being created on the kiosk.

For instance, if you set 'user_folder' to 'Website', then the local folder
'Website', in the same folder as the main configuration file, will be copied
to the kiosk so that a new folder '/home/username/Website' is created and
populated by the files it contains on the host.

If you are creating a 'web' type kiosk that browses a remote website, you
generally don't need to specify a value for this setting.
""".strip()


USER_NAME_HELP = """
The user name of the non-root primary Linux user.

Technically, a user name can be from 1 to 256 characters, but most Linux
tools only a maximum of 32 characters, so this is the limit in KioskForge.
The user name may only consist of US letters, digits, and underscores (_).

This is the user who runs X11, Chromium and/or any custom user apps.

This user is very central to the kiosk as everything, but the forge process
itself, runs under this user.

For most users, though, you just need to specify a valid name and only worry
about it if you use SSH to access the kiosk.
""".strip()


USER_PACKAGES_HELP = """
A space-separated list of user packages to install when forging of the kiosk.

If empty, this feature is disabled.

This field is rarely necessary, but if you are forging a 'cli' or 'x11' type
kiosk, you may need to install additional Ubuntu packages while forging the
kiosk.
""".strip()


VACUUM_SIZE_HELP = """
The maximum size, in megabytes, of system log files.

This value ranges from 0 (= unlimited) through 4096 (4 gigabytes).

A good value that provides room for weeks of logging of a kiosk is 256.

System logs are cleaned out as the first step of the mandatory daily
maintenance controlled by the 'upgrade_time' field.
""".strip()


WEAR_REDUCTION_HELP = """
Move certain system files, including swap, to memory.

If enabled, KioskForge will set up a compressed swap file about one quarter
of the size of the RAM available in the system, which is compressed using
the 'zstd' compression algorithm, which is fairly fast and efficient.

Furthermore, KioskForge will move /tmp to a RAM disk.

The above changes reduce wear on the storage medium and also make the system
more snappy and less laggy, this in particular for slow storage medias.

The recommended setting is enabled.  If you run into problems with this
setting, you can always disable it.
""".strip()


WIFI_BOOST_HELP = """
If Wi-Fi power-saving should be enabled.

If 'true', the kiosk will be configured to NOT use power-saving on its Wi-Fi
network card.  This means two things: The kiosk will use slightly more power
and the kiosk will access the internet quite a bit faster.

If your kiosk is a 'web' type kiosk, you should probably enable this field.
In most other cases, this field has no significant effect and should be
disabled.
""".strip()


WIFI_CODE_HELP = """
The password to the Wi-Fi network, if any.

A Wi-Fi WPK (password) may consist of 8 to 63 extended characters, but it is
advisable to only use printable ASCII characters to be able to enter the
password in various operating systems and/or tools.

This setting is case sensitive so that "Pass" is different from "pass".

If empty and the 'wifi_name' setting is non-empty, the Wi-Fi connection
will be assumed to be public and open to everybody (without a password).
""".strip()


WIFI_COUNTRY_HELP = """
The country code of the "regulatory domain" for the Wi-Fi card.

The uppercase two-letter code of the country that the Wi-Fi card is being
used in.  This is required to determine legal Wi-Fi frequencies, etc.

Documentation of the valid values can be found at:

    https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

NOTE: KioskForge does not currently verify the value of this field!
""".strip()


WIFI_HIDDEN_HELP = """
Some hardware needs a bit of help to find hidden Wi-Fi networks, so this
field is used to instruct them whether or not the desired Wi-Fi network
is in fact hidden.

The value 'false' indicates that the desired Wi-Fi network is standard,
publicly visible network and the value 'true' indicates that it is a
hidden network, which may slow down network scanning time a bit.

Most users will want to use the default value of 'false' here.
""".strip()


WIFI_NAME_HELP = """
The Wi-Fi network name (SSID).

A Wi-Fi SSID (network name) may consists of 1 to 32 characters of any
value.  In other words, you can use pretty much anything.  However, it is
advisable to only use ASCII characters so as to make it practical to use
the network name and also avoid breaking or confusing supporting tools.

This setting is case sensitive so that "MyWiFi" is different from "mywifi".

If empty, Wi-Fi is disabled altogether and no Wi-Fi network is configured.
In this case, 'wifi_code', 'wifi_country', and 'wifi_hidden' are ignored.
""".strip()


class Kiosk(Fields):
	"""The definition of a kiosk."""

	def __init__(self, version : Version) -> None:
		Fields.__init__(self, version)

		# Build regex for comments, it is a bit complicated.
		# ...Quote slash, it is not quoted in string.punctuation.
		comment_regex = punctuation.replace("\\", "\\\\")
		# ...Allow spaces.
		comment_regex = comment_regex + " "
		# ... Quote terminating brace (]) as it is not quoted in string.punctuation.
		comment_regex = comment_regex.replace(']', r'\]')
		# ...Disallow vertical slash (|).
		comment_regex = comment_regex.replace('|', '')
		# ...Disallow quotes (") as we may LATER need to quote the comment somewhere.
		comment_regex = comment_regex.replace('"', '')
		# ...Change the string into a character class match, which also allows for printable Unicode characters.
		comment_regex = r"[\w|" + comment_regex + "]"
		# ...Limit the string to between 1 and 128 characters.
		comment_regex = comment_regex + "{1,128}"

		# NOTE: Only fields whose type begins with "Optional" are truly optional and can be empty.  All other fields must be set.
		self += OptionalRegexField("comment", "", COMMENT_HELP, comment_regex)
		self += ChoiceField("device", "pi4b", DEVICE_HELP, ["pi4b", "pi5"])
		self += ChoiceField("type", "web", TYPE_HELP, ["cli", "x11", "web", "web-wayland"])
		self += StringField("command", "https://google.com", COMMAND_HELP)
		self += OptionalRegexField("hostname", "", HOSTNAME_HELP, r"[A-Za-z0-9-]{1,63}")
		self += ChoiceField("timezone", "America/Los_Angeles", TIMEZONE_HELP, TIMEZONES)
		self += ChoiceField("keyboard", "us", KEYBOARD_HELP, list(KEYBOARDS.keys()))
		self += ChoiceField("locale", "en_US.UTF-8", LOCALE_HELP, LOCALES)
		self += ChoiceField("sound_card", "none", SOUND_CARD_HELP, ["none", "jack", "hdmi1", "hdmi2"])
		self += NaturalField("sound_level", "80", SOUND_LEVEL_HELP, 0, 100)
		self += BooleanField("mouse", "false", MOUSE_HELP)
		self += RegexField("user_name", "kiosk", USER_NAME_HELP, r"[A-Za-z0-9_]{1,32}")
		self += PasswordField("user_code", password_create(32), USER_CODE_HELP)
		self += OptionalStringField("ssh_key", "", SSH_KEY_HELP)
		self += OptionalRegexField("wifi_name", "", WIFI_NAME_HELP, r".{1,32}")
		self += OptionalRegexField("wifi_code", "", WIFI_CODE_HELP, r"[\u0020-\u007e\u00a0-\u00ff]{8,63}")
		self += RegexField("wifi_country", "US", WIFI_COUNTRY_HELP, r"[A-Z]{2}")
		self += BooleanField("wifi_hidden", "false", WIFI_HIDDEN_HELP)
		self += BooleanField("wifi_boost", "true", WIFI_BOOST_HELP)
		self += BooleanField("cpu_boost", "true", CPU_BOOST_HELP)
		self += BooleanField("wear_reduction", "true", WEAR_REDUCTION_HELP)
		self += NaturalField("swap_size", "4", SWAP_SIZE_HELP, 0, 128)
		self += NaturalField("vacuum_size", "256", VACUUM_SIZE_HELP, 0, 4096)
		self += ChoiceField("upgrade_post", "reboot", UPGRADE_POST_HELP, ["poweroff", "reboot"])
		self += OptionalTimeField("upgrade_time", "05:00", UPGRADE_TIME_HELP)
		self += OptionalTimeField("poweroff_time", "", POWEROFF_TIME_HELP)
		self += NaturalField("idle_timeout", "0", IDLE_TIMEOUT_HELP, 0, 24 * 60 * 60)
		self += ChoiceField("screen_rotation", "none", SCREEN_ROTATION_HELP, ["none", "left", "flip", "right"])
		self += OptionalStringField("user_folder", "", USER_FOLDER_HELP)
		self += OptionalStringField("user_packages", "", USER_PACKAGES_HELP)
		self += BooleanField("chromium_autoplay", "false", CHROMIUM_AUTOPLAY_HELP)

	def redact(self, fields : List[str]) -> None:
		"""
			Redacts the specified fields in the kiosk by replacing their values with 'REDACTED'.

			NOTE: Be careful to NOT use any of the redacted fields after they have been set to 'REDACTED'!
		"""
		for field in fields:
			self.assign(field, "REDACTED")

	def redact_prepare(self) -> None:
		"""Redacts the kiosk for use by the 'KioskForge.py' script when it prepares the installation medium for use."""
		self.redact(["wifi_code"])

	def redact_report(self) -> None:
		"""Redacts the kiosk for use by the 'KioskReport.py' script when it includes the redacted kiosk in the Zip archive."""
		self.redact(["comment", "user_name", "user_code", "wifi_name", "wifi_code", "ssh_key"])
