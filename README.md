# pywatchdog

<p align="left">
<a><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/pywatchdog"></a>
<a href="https://pypi.org/project/pywatchdog/"><img alt="PyPI" src="https://img.shields.io/pypi/v/pywatchdog"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
<a><img alt="License" src="https://img.shields.io/pypi/l/pywatchdog"></a>
</p>

* [What's a watchdog?](#whats-a-watchdog)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
  * [API](#api)
  * [CLI](#cli)
    * [`find-module`](#find-module)
    * [`test-reboot`](#test-reboot)
* [Example](#example)
* [Do I have a watchdog?](#do-i-have-a-watchdog)
* [Contributing](#contributing)
* [Based on](#based-on)

## What's a watchdog?

A watchdog (or watchdog timer, WDT) is a hardware component that reboots your system
if it is not notified regularly from the user space, usually by a daemon.
If user space fails for any reason, the watchdog will stop being notified and when the timeout occurs,
it will reboot the system.

On the software side, once the kernel driver is loaded,
communication with the hardware is done via the special device file `/dev/watchdog`.

It is useful when you have for example a remote system that you don't have physical access to,
and you want to ensure that it will not freeze and become unavailable indefinitely until you get physical access again.

## Requirements

* Linux with root privileges
* a watchdog (see [Do I have a watchdog?](#do-i-have-a-watchdog) for basic help)
* Python 3.7+

## Installation

Using `pip`:

```
sudo -H pip install pywatchdog
```

For a specific Python version if you have multiple:

```
sudo -H python3.x -m pip install pywatchdog
```

Directly from the repository for the latest changes:

```
sudo -H pip install git+https://github.com/AT0myks/pywatchdog
sudo -H python3.x -m pip install git+https://github.com/AT0myks/pywatchdog
```

## Usage

### API

The recommended usage is with a context manager:

```python
from pywatchdog import Watchdog
with Watchdog() as wdt:
    ...
```

`Watchdog` takes as an argument the device file.
It defaults to `/dev/watchdog`, which should work in most cases.

You can also manually `open` and `close` the file:

```python
wdt = Watchdog()
wdt.open()
...
wdt.close()
```

Once the file is open, if the watchdog is not pinged before the timeout occurs, the computer will reboot.

To ping the watchdog use the `keep_alive` method:

```python
wdt.keep_alive()
```

The timeout can be queried, and for some drivers it can also be modified on the fly:

```python
print("The timeout is", wdt.timeout, "seconds")
wdt.timeout = 45  # Has no effect if unsupported.
print("The timeout is now", wdt.timeout, "seconds")
```

Note that some devices have a granularity of minutes for their timeout.
In this case the example above will print `The timeout is now 60 seconds`.

Some watchdog drivers have the ability to report the remaining time before the system will reboot:

```python
print("Time left before reboot:", wdt.time_left, "seconds")  # Prints None if unsupported.
```

Here's the rest of properties. The only one you can set is `pretimeout`:

```python
print(wdt.identity)  # A string identifying the watchdog driver. Example: 'iTCO_wdt'.
print(wdt.firmware_version)  # Shortcut for wdt.support.firmware_version.
print(wdt.options)  # A list of flags describing what the device supports.
print(wdt.pretimeout)  # Returns the pretimeout in seconds.
wdt.pretimeout = 15  # Seconds. Set to 0 to disable. Unsettable for some drivers.
print(wdt.support)  # Returns an instance of watchdog_info.
print(wdt.status)  # Current status, not always supported.
print(wdt.boot_status)  # Status at the last reboot, not always supported.
print(wdt.temperature)  # In Fahrenheit, not always supported.
```

If a property is not supported by a driver, `None` is returned.

Some watchdogs can be enabled and disabled:

```python
wdt.enable()  # Turn on the watchdog timer.
wdt.disable()  # Turn off the watchdog timer.
```

And a few drivers have the ability to cause a kernel panic when the system overheats:

```python
wdt.temp_panic()
```

Once this option is enabled, it cannot be disabled without removing the kernel module and readding it.
Also, its status cannot be queried.

See the docstrings for more information on the properties and methods.

### CLI

This package also provides a `pywatchdog` command. It has two subcommands:

#### `find-module`

Get a list of potential kernel watchdog drivers for your system.

```
usage: pywatchdog find-module [-a]

optional arguments:
  -a, --all   only look for the presence of /dev/watchdog
```

This is done by trying every module in `/lib/modules/$(uname -r)/kernel/drivers/watchdog` and testing which ones,
when inserted, result in the availability of both `/dev/watchdog` and `/dev/watchdog0`.
When the `--all` option is specified, it only looks for `/dev/watchdog`.

Since I don't know the difference between having just `/dev/watchdog` and having both,
the `--all` option is provided just in case.

The `softdog` module is always ignored because it is a software watchdog and should work for all systems anyway.
You should always use a hardware watchdog when possible.

#### `test-reboot`

Test if a watchdog correctly reboots your computer.

```
usage: pywatchdog test-reboot [-t TIMEOUT] [-d DEVICE]

optional arguments:
  -t TIMEOUT, --timeout TIMEOUT    the timeout that will be set for the test
  -d DEVICE, --device DEVICE       default: /dev/watchdog
```

This will open the device file without notifying the watchdog,
which means that when the timeout occurs, the computer should reboot.

A countdown before reboot will be shown.
Make sure to save your work before using this command.
Use Ctrl-C to abort.

## Example

This example assumes you are on a distribution with `systemd`.

Two files are provided to create an example daemon:
a [script](https://github.com/AT0myks/pywatchdog/blob/main/example.py)
and a [systemd service file](https://github.com/AT0myks/pywatchdog/blob/main/example.service).
The script is a simple infinite loop that pings the watchdog every second.
The service file runs the script as root and makes sure it is restarted in case it fails,
and it can also be used to load the watchdog module at boot.

In this example we are in the home directory of user `ben` and the watchdog module is `iTCO_wdt`.

Download the two files:

```
wget https://raw.githubusercontent.com/AT0myks/pywatchdog/main/example.py
wget https://raw.githubusercontent.com/AT0myks/pywatchdog/main/example.service
```

Let's rename them to something more meaningful:

```
mv example.py pywatchdog.py
mv example.service pywatchdog.service
```

Make the script executable:

```
chmod +x pywatchdog.py
```

Move the service file to `/etc/systemd/system/`:

```
sudo mv -i pywatchdog.service /etc/systemd/system/
```

Edit the `[Service]` section of the service file with

```
sudo systemctl edit --full pywatchdog
```

and specify the correct path to the script:

```
ExecStart=/home/ben/pywatchdog.py
```

If the watchdog module is not loaded at boot (should not be the case for a Raspberry Pi),
you can use the service file to do it (please see the note at the bottom of this section)
by adding these two lines under `[Service]`:

```
ExecStartPre=/usr/sbin/modprobe iTCO_wdt
ExecStopPost=/usr/sbin/modprobe -r iTCO_wdt
```

You can find the absolute path of `modprobe` with `which modprobe`.

Now enable (start automatically at boot) and start the watchdog daemon:

```
sudo systemctl enable pywatchdog
sudo systemctl start pywatchdog
```

You can now see the status of the daemon:

```
systemctl status pywatchdog
```

And its logs:

```
journalctl -u pywatchdog
```

Note: because of the hard blacklisting of watchdog modules (at least on Ubuntu),
we use the service file to load a module at boot instead of the regular ways (like `/etc/modules`).
See for example [here](https://bugs.launchpad.net/ubuntu/+source/systemd/+bug/1535840)
and [here](https://bugs.launchpad.net/ubuntu/+source/systemd/+bug/1767172).

<!-- For a more advanced daemon, see [pywatchdogd](https://github.com/AT0myks/pywatchdogd). -->

## Do I have a watchdog?

If you have a `/dev/watchdog` file, then yes.
This should already be the case if for example you are working with a Raspberry Pi.
You can also check by typing the command `sudo wdctl`.
If you get `wdctl: cannot open /dev/watchdog: No such file or directory`, keep reading.

If you don't have a `/dev/watchdog` file,
chances are you have a watchdog but need to find the appropriate kernel module to load for your specific hardware.
The modules that work in my case are `sp5100_tco` for a computer with (pretty recent, if it matters) AMD hardware
and `iTCO_wdt` for another with Intel hardware.
Once you've found the module, load it with `sudo modprobe <module>`.

You can also use the [`pywatchdog find-module`](#find-module) command.

You should avoid loading a watchdog module if you don't have a daemon feeding it, to prevent unexpected reboots.

## Contributing

You are welcome to contribute to this project.
Feel free to open an issue or a pull request if you encounter any bug or want to add/fix something.

## Based on

* [The Linux Watchdog driver API](https://github.com/torvalds/linux/blob/master/Documentation/watchdog/watchdog-api.rst)
* [ioctl.h](https://github.com/torvalds/linux/blob/master/include/uapi/asm-generic/ioctl.h)
* [watchdog.h](https://github.com/torvalds/linux/blob/master/include/uapi/linux/watchdog.h)
