# KioskForge ReadMe
[KioskForge](https://kioskforge.org) generates kiosks on top of Ubuntu Server 24.04.

## Introduction
KioskForge saves you hundreds of hours of research and configuration of a new Raspberry Pi kiosk, and possibly also a load of money
needed to pay for commercial kiosk solutions.  Furthermore, making your own kiosk is a tough ride with respect to security and
system optimizations.

The level of IT expertise needed to use KioskForge, as an end-user, is about *intermediate*.  You don't have to know Linux or how
to run programs on Linux, all you need to know is how to edit a well documented text file, make an installation medium, and invoke
KioskForge to make its modifications of the installation medium.  After the forge process is over, something which takes 5 to 30
minutes depending on the speed of the medium and the target Raspberry Pi (5 is much faster than 4B), you simply turn off the kiosk
(using either SSH, and the Linux `poweroff` command, or by simply unplugging the Pi) and deploy it where you need it deployed.

The basic idea behind KioskForge is that it should be **easy**, **safe**, and **automatic** to deploy a new kiosk.

**NOTE:** Presently, KioskForge can only be used from Windows desktops.  Linux support is work in progress.

## Features
KioskForge v0.24 supports the following features:

* Deployment of Ubuntu Server 24.04 (a Long Term Support release, which is supported until June 2029).
* 64-bit Raspberry Pi 4B and Raspberry Pi 5.
* Windows 10+ setup program.
* International users (there are configuration settings for language, keyboard, and Wi-Fi region).
* Creating a kiosk that allows browsing a website using Chromium in kiosk mode (without an URL address bar).
* Creating a kiosk that runs a command-line (CLI) application programmed by the user.
* Touch screen input insofar the particular touch screen is supported out of the box by the target operating system.
* Rotating normal and touch-panel displays (sometimes kiosk screens are mounted in a rotated fashion).
* Ethernet and/or Wi-Fi networking.
* Configuring basic Linux things such as host name, keyboard layout, locale, time zone, etc.

**NOTE:** *We recommend that all KioskForge kiosks have 24/7 internet access to facilitate automatic upgrades of the kiosk.*

## Documentation
Currently, the primary source of documentation for KioskForge is the documentation installed with the Windows installer as `.html`
files with links in the `Start` menu's `KioskForge` folder.  The documentation can also be found as Markdown in `docs`.

## History
KioskForge was made for the Danish museum [Vendsyssel Historiske Museum](https://vhm.dk) as the museum has a constant need for
deploying kiosks.

KioskForge started out as a manual procedure for configuring a new Raspberry Pi 4B machine to become a web browser kiosk.  As there
was a huge need to automate the process, the manual procedure was made into a Bash script.  As the project grew quickly and as Bash
doesn't offer strong scripting features (OOP, exceptions, etc.), the project was rewritten in Python v3.10+.

Today, KioskForge is a nearly automatic tool for creating new Raspberry Pi 4B and Raspberry Pi 5 kiosks from scratch.  The only
part of the process that is still manual, is the actual creation of the installation medium used to set up the kiosk.  However,
once the installation medium has been made, using [Raspberry Pi Imager](https://www.raspberrypi.com/software/), KioskForge takes
over and the rest of the installation process is as automatic as it can possibly be.
