# KioskForge Guide
This document presents a number of supported scenarios for how to use KioskForge.

## Displaying a Public Website
This is the simplest case, the one that KioskForge was originally made for.  With this scenario, you'll get a finished kiosk ready
to deploy using a Raspberry Pi 4B with at least 2 gigabytes of RAM and your choice of storage medium.

**Hint:** The website to be displayed should support any resolution that your touch screen supports.

Please read the `README.md` file for instructions on how to install KioskForge, Python and Raspberry Pi Imager, and how to use
KioskForge together with these tools.  Expect to redeploy a few times until all settings are at their correct values.

When you want to display a website using your new kiosk, you especially have to be aware of these options:

1. Device type (`device`): This should be `pi4` for a plain Raspberry Pi 4, `pi4b` for a 4B model, and `pc` for a standard PC.
2. Website URL (`website`): This should begin with `https://` and be the full address of the website you want to display.
3. Audio volume (`audio`): This should be non-zero only if the website in question has videos or other sources of audio.  It
   specifies the logarithmic level of the device's volume control so as value of, say, `60` or `80` would typically be fine.
   You'll have to experiement with the `audio` volume level (`0` = disabled) to match your particular touch screen, etc.
4. Mouse cursor (`mouse`): This should be disabled (`0`) for a kiosk with a touch panel, to avoid showing a mouse cursor.
5. Idle timeout (`idle_timeout`): This should be set to a non-zero number of seconds between restarts of the browser so that
   naughty customers cannot disable the kiosk for prolonged periods of time (especially younger people like to do this).
   **NOTE**: The current method of reloading the starting page, by terminating the web browser gracefully and restarting it, is
   far from optimal, a better solution may come up some day, but until then, this is, unfortunately, all that KioskForge offers.
6. Data folder (`data_folder`): This value should be left blank as it is only useful for displaying a local file-based website.

