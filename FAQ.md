# KioskForge Frequently Asked Questions
This is the official *Frequently Asked Questions (FAQ)* list for the KioskForge project.

Please feel free to submit more questions in the issue tracker at GitHub.  Alternatively you can mail me the issue and I'll create a new issue, if needed.

## Contacting the Developer
The developer is named *Mikael Egevig* and can be contacted directly by mail at `me@vhm.dk`.  If you have a GitHub account, please use the official issue tracker in the KioskForge repository found at https://github.com/vhmdk/KioskForge.

## Technical Issues
This section contains various common questions about technical issues with KioskForge.

### I am unable to connect to my Wi-Fi network?
This is most likely because you have misspelled the Wi-Fi network name or are using a wrong password.  Please notice that both are *case sensitive* so that `Test WiFi` is different from `Test WIFI`.  You need to spell both precisely as given to you.

A tip is to try to create a new connection with your phone to see if that works.  If either the Wi-Fi network name or the password is incorrect, it will fail too.

### How much space does KioskForge take up on the kiosk machine?
As of this writing, less than half a megabyte.  This is negible and should not cause any concern on your part.

All files created by and used by KioskForge are located in `~/KioskForge`.  Please do *not* remove this folder as it is required.

The setup script, `KioskSetup.py`, *intentionally* copies `KioskForge.py` (the main program) onto the target for posterity.

### I get weird errors about `set chanspec 0xNNNN fail, reason -52`
To be honest, I get a bunch of these errors every time I install Ubuntu Server on the Raspberry Pi 4+.  I think that they are related to the Wi-Fi network card by Broadcomm, but I have no idea what they mean or why they pop up.

This *may* be caused by the code that disables the Wi-Fi power saving feature.  This feature is called `wifi_boost`.

Please ignore these errors - as far as I can tell, the Wi-Fi card works as it should and the kiosk runs reliably as it should.

### The forge process on Linux fails because `apt` is already using a lock file?
KioskForge tries to take the fact that `apt` is a rude process, that keeps meddling with central lock files at arbitrary times, into consideration (`apt` runs in the background even if the package `unattended-upgrades` has been completely removed), by waiting for the lock files to be unlocked again, so you should not run into this issue.

If you run into this issue, please report it.

### I get spurious errors while the kiosk is being forged?
The most likely reason of this issue is that your installation media, typically a MicroSD card, is becoming bad and unreliable from overuse.  Another possibility is that your USB key is too hot, which happens quite often.

Try with another installation media (USB key or another MicroSD card), and the error(s) should disappear.

If the problem persists, report it as a bug.  It may be some obscure error in KioskForge.

## Development Issues
This section contains various common questions about the development of KioskForge.

### Will KioskForge support Linux distribution X?
For the time being, I am very happy about Ubuntu Server (which I use and have used as a web server for a decade or so), so this is not very likely.

I could theoretically add support for a host of Linux distributions, but I don't really see the point.  Ubuntu Server is free, very stable, and well documented.  The software is also reasonably up-to-date and security issues get fixed quite quickly in my experience.  Furthermore, Ubuntu supports Raspberry Pi and PCs equally well, something that not all Linux distros do.  It is a hard requirement that both PCs and PIs are equally well supported.

Adding support for a single target platform takes weeks or months, as Linux is a mess when it comes to administration of the operating system.  Almost every distro does things in its own way and I, honestly, don't feel like battling a lost war on the intricacies of a bunch of Linux distros.

### Why was KioskForge written in Python v3.x?
I originally wrote the first version of KioskForge in Bash, because it was very simple in the beginning, but soon came to rediscover that Bash *is* a pain to use if things go wrong.  The `set -e` command does not make a script truly reliable and I demand reliability of my tools.

In short: Because Python v3.x is preinstalled on many Linux distributions and because Python is a great scripting language.

### Why does KioskForge use Tkinter for Python?
Because it is readily available on all platforms that support Python v3.x and because it is sufficient for the task at hand.

### Why can't you use KioskForge on Linux?
This is work in progress, pretty soon you will be able to use KioskForge on both Windows and Linux.  Feel free to request this.

### Why can't you use KioskForge on Apple?
I don't have any Apple gear and don't feel like spending a fortune on adding support for a platform that I don't use myself.

### Will KioskForge ever invoke 'Raspberry Pi Imager' (RPI) directly?
Not likely.

It could do this by using the `wmi` package for Python (as RPI requires a physical drive to be specified).  But I am much more focused on making a Linux newbie friendly solution than offering all sorts of gimmicks.  It is important to me, and most users, that they can launch KioskForge simply by double-clicking it without having any technical knowledge of Python, Linux, and kiosks as such, so I won't be exploring this path anytime soon.

Also, I sleep better knowing that people can't accidentally erase important data using KioskForge.

