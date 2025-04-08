# KioskForge Guide
This document presents a number of supported scenarios for how to use KioskForge.

## Displaying a Website
This is the simplest case, the one that KioskForge was originally made for.  With this scenario, you'll get a finished kiosk ready
to deploy using a Raspberry Pi 4B with at least 2 gigabytes of RAM and your choice of storage medium.

**Hint:** The website to be displayed should support the default resolution that your (touch) screen supports.

Please read the `README.md` file for instructions on how to install KioskForge, Python and Raspberry Pi Imager, and how to use
KioskForge together with these tools.  Expect to redeploy a few times until all settings are at their correct values.

When you want to display a website using your new kiosk, you especially have to be aware of these options:

| Name             | Option name       | Comment                                                                                  |
| ---------------- | ----------------- | ---------------------------------------------------------------------------------------- |
| Comment          | `comment`         | A string describing the kiosk and its purpose (for your records).                        |
| Device type      | `device`          | `pi4b` for a 4B model, and `pc` for a standard PC (the latter is currently broken).      |
| Kiosk type       | `type`            | This should be `web` to launch Chromium in X11.                                          |
| Command          | `command`         | The URL of the starting page of the website that you want the kiosk to browse.           |
| Sound card       | `sound_card`      | One of `none`, `jack`, `hdmi1`, or `hdmi2`.  Jack requires an amplifier!                 |
| Sound volume     | `sound_level`     | The logarithmic audio volume from 0 through 100 (`80` is typically a good choice).       |
| Mouse cursor     | `mouse`           | This should be disabled (`0`) when using a touch panel, to hide the mouse cursor.        |
| Idle timeout     | `idle_timeout`    | This should be set to a non-zero number of seconds, say `300`, between restarts [^1].    |
| Screen rotation  | `screen_rotation` | none = default, left = rotate left, flip = flip upside-down, right = rotate right.       |
| User folder      | `user_folder`     | This value should be left blank unless you want to display a local file-based website.   |

[^1]: Rude customers may sabotage the kiosk (young people often do this); the restart of the browser resets such sabotage.

**NOTE**: The current method of reloading the starting page, by terminating the web browser gracefully and restarting it, is far
from optimal, a better solution may come up some day, but until then, this is, unfortunately, all that KioskForge offers.

You still need to supply values for most of the other options, as described in the [README.md](README.md) file, though.

