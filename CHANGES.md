# KioskForge Change Log
This document presents the important changes made to each KioskForge release from v0.18 and onwards:

## Version 0.18 (2025.04.25)
1. Initial support for the Raspberry Pi 5 has been added.  Sound does not yet work on the Raspberry Pi 5, though.
2. The KioskForge setup program now includes a change log of changes made to KioskForge, which is now shown by the installer.
3. The vacuuming of logs on the target kiosk machine now actually works (a lowercase 'm' was changed to an uppercase ditto).
4. KioskForge now runs using codepage 65001 (UTF-8) on Windows.
5. The HTML documentation is now quite a bit prettier than before.
6. Added detection of, but not support for, Ubuntu Desktop/Server 25.04 so that KioskForge gracefully fails on these.
7. Made the detection logic more robust in preparation for detecting numerous future Ubuntu releases.

