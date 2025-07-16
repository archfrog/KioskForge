#!/usr/bin/env python3
# Tiny script to generate the official KEYBOARDS, LOCALES, and TIMEZONES .html pages published on kioskforge.org.

import os

from kiosklib.convert import KEYBOARDS
from kiosklib.locales import LOCALES
from kiosklib.logger import TextWriter
from kiosklib.timezones import TIMEZONES

# Fetch and normalize RAMDISK environment variable.
ramdisk = os.environ["RAMDISK"]
if ramdisk[-1] != os.sep:
	ramdisk += os.sep

# Prepare creating "keyboards.html".
keyboards_inverted = dict(zip(KEYBOARDS.values(), KEYBOARDS.keys()))

# Create "keyboards.html" (with two mappings, one from full name to abbreviation and the other the inverse mapping).
with TextWriter(ramdisk + "keyboards.html") as stream:
	stream.write(f"<h1>Keyboard Layouts</h1>")
	stream.write(f"<table>")
	names = list(keyboards_inverted.keys())
	names.sort()
	for name in names:
		stream.write(f"<tr><td>{name}</td><td>{keyboards_inverted[name]}</td></tr>")
	stream.write(f"</table>")

# Create "timezones.html".
with TextWriter(ramdisk + "timezones.html") as stream:
	stream.write(f"<h1>Time Zones</h1>")
	stream.write(f"<table>")
	for timezone in TIMEZONES:
		stream.write(f"<tr><td>{timezone}</td></tr>")
	stream.write(f"</table>")



