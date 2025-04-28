# KioskForge Change Log
This document presents the important changes made to each KioskForge release from v0.18 and onwards:

## Version 0.18 (2025.04.28)
1. Initial support for the Raspberry Pi 5 has been added.  Sound support on the Pi 5 has not been tested yet, though.
2. The KioskForge setup program now includes a change log of changes made to KioskForge, which can be shown by the installer.
3. The built-in editor and menu has been removed: KioskForge can now only be used to prepare a kiosk installation medium.
4. A new file type, `KioskForge Kiosk`, has been added to the Windows Explorer `New` menu.  Use this to create a new kiosk.
5. The cleaning of logs on the target kiosk machine now actually works (a lowercase 'm' was changed to an uppercase ditto).
6. The `cpu_boost` option is now honored properly.  Previously, all kiosks were created as if `cpu_boost` was always disabled.
7. KioskForge now reports all detected issues and exits gracefully if you open an invalid `.kiosk` file in the program.
8. The HTML documentation in `C:\Program Files\KioskForge` is now much prettier than before.
9. Added detection of, but not support for, Ubuntu Desktop and Server 25.04 so that KioskForge gracefully fails on these.

