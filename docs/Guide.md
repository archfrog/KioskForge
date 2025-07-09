# KioskForge Guide
This document presents a number of supported scenarios for how to use KioskForge.  Actual samples are work in progress.

## Displaying a Remote Website
This is the simplest case, the one that KioskForge was originally made for.  With this scenario, you'll get a finished kiosk ready
to deploy using a Raspberry Pi 4B or 5 with at least 2 gigabytes of RAM and your choice of storage medium.

**Hint:** The website to be displayed should support the default resolution that your (touch) screen supports.

Please read the [Manual](Manual.html) for instructions on how to install KioskForge, Python and Raspberry Pi Imager, and how to use
KioskForge together with these tools.  Expect to redeploy a few times until all settings are at their correct values.

When you want to display a remote website using your new kiosk, you have to focus primarily on these options:

| Name             | Option name       | Comment                                                                                  |
| ---------------- | ----------------- | ---------------------------------------------------------------------------------------- |
| Comment          | `comment`         | A string describing the kiosk and its purpose (for your records).                        |
| Device type      | `device`          | `pi4b` for a 4B model, and `pi5` for a Pi 5.                                             |
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

You still need to supply values for all the other options that are described in the kiosk file (`*.kiosk`).

## Displaying a Local Website
This case is very useful for displaying a static, local website without network access (except, perhaps, for upgrading the kiosk).

An example of this is a website that displays a set of images with titles, one at a time, and then after a certain interval moves
on to the next image.  Once the end is reached, the display begins at the first image again.

**Hint:** The website to be displayed should support the default resolution that your (touch) screen supports.

**Hint:** You may want to resize large images to a smaller size such as Full HD (1920x1080) to not overload the Pi.

Please read the [Manual](Manual.html) for instructions on how to install KioskForge, Python and Raspberry Pi Imager, and how to use
KioskForge together with these tools.  Expect to redeploy a few times until all settings are at their correct values.

When you want to display a local website using your new kiosk, you especially have to be aware of these options:

| Name             | Option name       | Comment                                                                                  |
| ---------------- | ----------------- | ---------------------------------------------------------------------------------------- |
| Comment          | `comment`         | A description of the kiosk and its purpose (for your records).                           |
| Device type      | `device`          | The device model: `pi4b` or `pi5`.                                                       |
| Sound card       | `sound_card`      | This should be set to `none` as pictures don't include sound.                            |
| Mouse cursor     | `mouse`           | This should be disabled (`false`) to hide the mouse cursor.                              |
| Idle timeout     | `idle_timeout`    | This should be set to zero as the user will not be able to navigate away from your site. |
| User folder      | `user_folder`     | Set to the location, on the host machine, of the folder with the website.                |
| CPU overclocking | `cpu_boost`       | This could well be disabled (`false`) as displaying images doesn't require too much CPU. |
| Wi-Fi boost      | `wifi_boost`      | This should probably be disabled (`false`) as local websites require no LAN access.      |

[^1]: The `command` option is a bit peculiar.  You need to specify a `file://` URL to tell Chromium that it is displaying local
files.  The URL needs to be *carefully* specified as the kiosk will fail to display anything if it is wrong.  Let's say that you've
set `user_name` to `test` and `user_folder` equal to `Website`.  Then your URL needs to be: `file:///home/test/Website/index.html`,
which is the value that you should give in the `command` option.

You still need to supply values for all the other options that are described in the kiosk file (`*.kiosk`).

## Using a Touch Screen
Many kiosks have touch screens.  This section highlights the most important options related strictly to screens and touch screens.

Please read the [Manual](Manual.html) for instructions on how to install KioskForge, Python and Raspberry Pi Imager, and how to use
KioskForge together with these tools.  Expect to redeploy a few times until all settings are at their correct values.

The important options to be aware of, when forging a kiosk with touch screen, are these:

| Name              | Option name        | Comment                                                                           |
| ----------------- | ------------------ | ----------------------------------------------------------------------------------|
| Screen Rotation   | `screen_rotation`  | If the screen needs to be rotated, use a value other than `none`.                 |
| Chromium Autoplay | `chromium_autolay` | If videos need to play immediately upon page load (no user interaction required). |

You still need to supply values for all the other options that are described in the kiosk file (`*.kiosk`).
