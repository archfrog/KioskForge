# KioskForge Frequently Asked Questions
This is the official *Frequently Asked Questions (FAQ)* list for the KioskForge project.

Please feel free to submit additional questions in the GitHub issue tracker.  Alternatively, you can mail me the issue, and I'll create a new issue if needed.

## Contacting the Developer
The team can be contacted directly by mail at `contact@kioskforge.org`.

If you have a GitHub account, please use the official issue tracker in the KioskForge repository found at:

* https://github.com/archfrog/KioskForge.

## Technical Issues
This section contains various common questions about technical issues with KioskForge.

### I am unable to connect to my Wi-Fi network?
This is most likely because you have misspelled the Wi-Fi network name or are using the wrong password.  Please note that both are *case-sensitive*, so `Test WiFi` is different from `Test WIFI`.  You need to spell both exactly as they were given to you.

The values of `wifi_country` and `wifi_hidden` also need to be correct, although this is mostly important when accessing 5G+ networks using the AC+ standards.

A tip is to try creating a new connection on your phone to see if that works.  If either the Wi-Fi network name or the password is incorrect, it will fail too.

### What kind of storage medium should I use?
As a rule of thumb, we recommend MicroSD cards over USB keys because the latter tend to become very hot and then malfunction.

As for MicroSD cards, it depends on how long the kiosk is expected to operate.  If it is to be deployed for weeks, months, or a few years, virtually any MicroSD card should do.  If you plan for the kiosk to operate for a decade or so, you should probably buy an "industrial grade" card with wear leveling, which significantly reduces wear on the card.  I know that SanDisk and Kingston both produce MicroSD cards named "... Industrial", both of which include wear leveling.  These cards are typically a couple of times more expensive than plain, non-wear-leveling cards, but I think the money is well spent because if your kiosk suddenly dies from a MicroSD failure, you'll probably waste hours dismounting, reforging, and remounting the kiosk.

If you have experience or knowledge that contradicts the above, please feel free to email me.

### How much space does KioskForge take up on the kiosk machine?
As of this writing, less than half a megabyte.  This is negligible and should not cause any concern for you.

All files created by and used by KioskForge are located in `~/KioskForge`.  Please do *not* remove this folder as it is required.

The setup script, `KioskSetup.py`, *intentionally* copies `KioskForge.py` (the main program) onto the target for posterity.

### How do I become `root` after login?
You should generally try to avoid becoming `root`, and instead use the `sudo` command with the `kiosk` user, but if you really need
to, you can use this procedure:

```bash
# Log into the kiosk as the 'kiosk' user using SSH or local login.
# Execute the commands below and fill in the requested passwords.
sudo -s
# Enter password for the 'kiosk' user at the prompt.
passwd
# Enter NEW password for the 'root' user at the prompt.
# Retype NEW password for the 'root' user at the prompt.
```

This step is only done the very first time you `su` to root.  Unfortunately, there's no way we can do this automatically.

### I am getting errors during the forge proccess about accessing the Ubuntu repositories?
This is almost certainly a temporary issue with your Internet Service Provider (ISP).  Wait thirty minutes and try again.  Your ISP
may be rebooting a DNS server or doing some other maintenance work.  I too run into this issue now and then.  Be patient!  :-)

### I get weird errors about `set chanspec 0xNNNN fail, reason -52`
I'm pretty sure these *were* caused by the lack of the `wifi_country` option in pre-v0.20 releases of KioskForge.  Basically, the network driver was complaining that an incorrect channel was attempted selected because the Ubuntu Server Wi-Fi subsystem did not know the correct country for the network card.  The new `wifi_country` option is used to tell the Wi-Fi subsystem the legal set of channels that can and may be used in the kiosk.

I have not seen these errors since v0.20, so please let me know if they suddenly pop up again.

### The kiosk fails because `apt` is already using a lock file?
KioskForge tries to take the fact that `apt` is a rude process, that keeps meddling with central lock files at arbitrary times, into consideration (`apt` runs in the background even if the package `unattended-upgrades` has been completely removed), by waiting for the lock files to be unlocked again, so you should not run into this issue.

If you run into this issue, please report it.

### I get spurious errors while the kiosk is being forged?
The most likely reason for this issue is that your installation media, typically a MicroSD card, is becoming worn and unreliable from overuse.  Another possibility is that your USB key is too hot, which happens quite often.

Try another installation media (a USB key or another MicroSD card), and the error(s) should disappear.

If the problem persists, report it as a bug.  It may be some obscure error in KioskForge.

## Development Issues
This section contains various common questions about the development of KioskForge.

### Will KioskForge support other Linux distributions?
For the time being, I am very happy with Ubuntu Server (which I have used as a web server for a decade or so), so this is not very likely.

I could theoretically add support for a host of Linux distributions, but I don't really see the point.  Ubuntu Server is free, very stable, and well-documented.  The software is also reasonably up-to-date, and security issues get fixed quite quickly in my experience.

Adding support for a single target platform can take weeks or months, as Linux is a mess when it comes to operating system administration.  Almost every distro does things in its own way, and I, honestly, don't feel like battling a lost war on the intricacies of a bunch of Linux distros.

Debian could become a candidate for KioskForge support sometime down the road, because Ubuntu is based on Debian and because Ubuntu is getting rather annoying these days (snaps, snaps, snaps, everywhere, even though the technology is only half-baked yet).  Chromium (the open-source variant of the Chrome web browser) has been quite a pain to work with because it is a snap, not a standard Ubuntu <code>apt</code> package.

### Will KioskForge support PCs?
No, the problem is that PCs are non-standard in every way, from the CPU to the graphics to the audio, and so on.  I prefer to make KioskForge as stable and reliable as at all possible, instead of having to support a crazy number of possible and real PC builds.

Supporting only two very standard target platforms at the time of this writing makes my job *a lot* easier and, hopefully, yields a stable, trustworthy, and flexible product that you and others can use for free.

### Why was KioskForge written in Python v3.x?
I originally wrote the first version of KioskForge in Bash because it was very simple at the beginning, but I soon realized Python was much more intuitive and logical.

In short, because Python v3. x is preinstalled on many Linux distributions, and Python is a great scripting language.

### Why can't you use KioskForge with Linux?
This is a work in progress; pretty soon, you will be able to use KioskForge on both Windows and Linux.  Feel free to request this.

### Why can't you use KioskForge on Apple equipment?
I don't have any Apple boxes and don't feel like spending a fortune to add support for a platform I don't use myself.

### Will KioskForge ever invoke 'Raspberry Pi Imager' (RPI) directly?
Not likely.

It could do this by using the `wmi` package for Python (as RPI requires a physical drive to be specified).  But I am much more focused on making a Linux newbie-friendly solution than offering all sorts of gimmicks.  It is important to me, and most users, that they can launch KioskForge simply by double-clicking it without having any technical knowledge of Python, Linux, and kiosks as such, so I won't be exploring this path anytime soon.

Also, I sleep better knowing that people can't accidentally erase important data using KioskForge.
