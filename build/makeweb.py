#!/usr/bin/env python3

import os

from toolbox.convert import KEYBOARDS
from toolbox.locales import LOCALES
from toolbox.logger import TextWriter
from toolbox.timezones import TIMEZONES

# Fetch and normalize RAMDISK environment variable.
ramdisk = os.environ["RAMDISK"]
if ramdisk[-1] != os.sep:
	ramdisk += os.sep

# Prepare creating "keyboards.html".
keyboards_straight = KEYBOARDS
keyboards_inverted = dict(map(reversed, keyboards_straight.items()))

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



