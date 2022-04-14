"""This package defines a class to interact with a Linux watchdog.

See https://github.com/torvalds/linux/blob/master/Documentation/watchdog/watchdog-api.rst.
Most of the documentation is copied or inspired from this file.
"""

import ctypes
import os
from fcntl import ioctl as ioctl_

from .watchdog import Request, Status, Option, watchdog_info


class Watchdog:
    """A class to interact with the ioctl API of a watchdog driver."""

    def __init__(self, file="/dev/watchdog"):
        self._file = file
        self._fd = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        return "{} [version {}] via {}".format(
            self.identity, self.firmware_version, self._file
        )

    @property
    def identity(self):
        """Return a string identifying the watchdog driver."""
        return bytes(self.support.identity).decode().strip("\x00")

    @property
    def firmware_version(self):
        """Return the firmware version of the card if available."""
        return self.support.firmware_version

    @property
    def options(self):
        """Return a list of flags describing what the device supports."""
        return [s for s in Status if self.support.options & s and s >= 0]

    @property
    def timeout(self):
        """Return the timeout in seconds."""
        return self._ioctl_get(Request.WDIOC_GETTIMEOUT)

    @timeout.setter
    def timeout(self, value):
        """Set the timeout in seconds.

        The actual timeout might differ from the requested one due to
        limitation of the hardware.
        """
        if Status.WDIOF_SETTIMEOUT in self.options:
            ioctl_(self._fd, Request.WDIOC_SETTIMEOUT, ctypes.c_int(value))

    @property
    def pretimeout(self):
        """Return the pretimeout in seconds.

        The pretimeout is the number of seconds before the time when the
        timeout will go off. This is not the number of seconds until the
        pretimeout. For instance, if you set the timeout to 60 seconds and the
        pretimeout to 10 seconds, the pretimeout will go off in 50 seconds.
        """
        return self._ioctl_get(Request.WDIOC_GETPRETIMEOUT)

    @pretimeout.setter
    def pretimeout(self, value):
        """Set the pretimeout in seconds if possible, else do nothing.

        Setting the pretimeout to 0 disables it.
        """
        try:
            ioctl_(self._fd, Request.WDIOC_SETPRETIMEOUT, ctypes.c_int(value))
        except OSError:
            pass

    @property
    def time_left(self):
        """Return the remaining time before the system will reboot.

        Return None if not supported by the driver.
        """
        return self._ioctl_get(Request.WDIOC_GETTIMELEFT)

    @property
    def support(self):
        """Return an instance of watchdog_info describing the watchdog.

        All drivers support this feature.
        """
        return self._ioctl_get(Request.WDIOC_GETSUPPORT, watchdog_info)

    @property
    def status(self):  # Should this be called regularly for temperature trip?
        """Return a list of flags describing the current status."""
        res = self._ioctl_get(Request.WDIOC_GETSTATUS)
        if res == 0:
            return None
        return [s for s in Status if res & s and s >= 0]

    @property
    def boot_status(self):
        """Return a list of flags describing the status at the last reboot."""
        res = self._ioctl_get(Request.WDIOC_GETBOOTSTATUS)
        if res == 0:
            return None
        return [s for s in Status if res & s and s >= 0]

    @property
    def temperature(self):
        """Return the temperature of the card in degrees Fahrenheit."""
        return self._ioctl_get(Request.WDIOC_GETTEMP)

    def _ioctl_get(self, request, type_=ctypes.c_int):
        res = type_()
        try:
            ioctl_(self._fd, request, res)
        except OSError:
            return None
        try:
            return res.value
        except AttributeError:
            return res

    def keep_alive(self):
        """Ping the watchdog to postpone the reboot."""
        ioctl_(self._fd, Request.WDIOC_KEEPALIVE)

    def enable(self):
        """Turn on the watchdog timer. This is ignored by some drivers."""
        ioctl_(
            self._fd, Request.WDIOC_SETOPTIONS, ctypes.c_int(Option.WDIOS_ENABLECARD)
        )

    def disable(self):
        """Turn off the watchdog timer. This is ignored by some drivers."""
        ioctl_(
            self._fd, Request.WDIOC_SETOPTIONS, ctypes.c_int(Option.WDIOS_DISABLECARD)
        )

    def temp_panic(self):  # Add instance variable for status?
        """Enable kernel panic on temperature trip.

        There is no way to get the status of this option, or to disable it
        during execution. To reset this option, remove and readd the module.
        Raises OSError if not supported by the driver.
        """
        ioctl_(self._fd, Request.WDIOC_SETOPTIONS, ctypes.c_int(Option.WDIOS_TEMPPANIC))

    def open(self):
        self._fd = os.open(self._file, os.O_WRONLY)

    def close(self):
        if Status.WDIOF_MAGICCLOSE in self.options:
            os.write(self._fd, b"V")  # Disable the watchdog.
        os.close(self._fd)
        self._fd = None
