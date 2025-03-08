# KioskForge Frequently Asked Questions

## Questions and Answers
This section contains various common questions and the answers to them.  Please feel free to submit more questions at GitHub.

### I am unable to connect to my WIFI network?
The most likely cause of this issue is that you have misspelled the WIFI network name or used a wrong password.  Please notice
that both are *case sensitive* so that `Test wifi` is different from `Test WIFI`.  You need to spell both precisely as given to
you.

### I get weird errors about "set chanspec 0xNNNN fail, reason -52"
To be honest, I get a bunch of these errors pretty much every time I install Ubuntu Server on the Raspberry Pi 4+.  I think that
they are related to the WIFI network card by Broadcomm, but I have no idea what they mean and why they pop up.

Please ignore these errors - as far as I can tell, the WIFI card works as it should and the kiosk runs reliably as it should.

### The Linux installer fails with an `apt` error because `apt` is already using a lock file?
KioskForge tries to take the fact that `apt` is a rude process that keeps meddling with central lock files at arbitrary times into
consideration (i.e., it runs in the background even if `unattended-upgrades` has been completely removed), by waiting for the lock
files to be unlocked again, so you should no longer run into this issue.  If you still run into this issue, please feel free to
report it.

### I get spurious errors while the Linux installer (`KioskSetup.py`) is running?
The most likely reason of this issue is that your installation media, typically a MicroSD card, is becoming bad and unreliable
from overuse.  Try with another installation media (USB key or another MicroSD card), and the problems should disappear.

If the problem persists, report it as a bug.  It may be some obscure error in KioskForge.

