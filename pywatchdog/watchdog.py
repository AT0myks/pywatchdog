"""Implement the functionality of watchdog.h.

Source: https://github.com/torvalds/linux/blob/master/include/uapi/linux/watchdog.h
"""

import ctypes
from enum import IntEnum, IntFlag

from .ioctl import _IOR, _IOWR

WATCHDOG_IOCTL_BASE = "W"


class watchdog_info(ctypes.Structure):
    _fields_ = [
        ("options", ctypes.c_uint32),
        ("firmware_version", ctypes.c_uint32),
        ("identity", ctypes.c_uint8 * 32),
    ]


class Request(IntEnum):
    """ioctls used to interact with the watchdog driver."""

    WDIOC_GETSUPPORT = _IOR(WATCHDOG_IOCTL_BASE, 0, watchdog_info)
    WDIOC_GETSTATUS = _IOR(WATCHDOG_IOCTL_BASE, 1, ctypes.c_int)
    WDIOC_GETBOOTSTATUS = _IOR(WATCHDOG_IOCTL_BASE, 2, ctypes.c_int)
    WDIOC_GETTEMP = _IOR(WATCHDOG_IOCTL_BASE, 3, ctypes.c_int)
    WDIOC_SETOPTIONS = _IOR(WATCHDOG_IOCTL_BASE, 4, ctypes.c_int)
    WDIOC_KEEPALIVE = _IOR(WATCHDOG_IOCTL_BASE, 5, ctypes.c_int)
    WDIOC_SETTIMEOUT = _IOWR(WATCHDOG_IOCTL_BASE, 6, ctypes.c_int)
    WDIOC_GETTIMEOUT = _IOR(WATCHDOG_IOCTL_BASE, 7, ctypes.c_int)
    WDIOC_SETPRETIMEOUT = _IOWR(WATCHDOG_IOCTL_BASE, 8, ctypes.c_int)
    WDIOC_GETPRETIMEOUT = _IOR(WATCHDOG_IOCTL_BASE, 9, ctypes.c_int)
    WDIOC_GETTIMELEFT = _IOR(WATCHDOG_IOCTL_BASE, 10, ctypes.c_int)


class _IntFlagWithDesc(IntFlag):
    def __new__(cls, value, desc):
        obj = IntFlag.__new__(cls, value)
        obj._value_ = value
        obj.desc = desc
        return obj


class Status(_IntFlagWithDesc):
    """Flags describing various watchdog statuses and capabilities.

    These flags describe what kind of information that the GET_STATUS and
    GET_BOOT_STATUS ioctls can return. They are also used to describe what the
    device can do.
    """

    WDIOF_UNKNOWN = -1, "Unknown flag error"
    WDIOF_OVERHEAT = 0x0001, "Reset due to CPU overheat"  # Status.
    WDIOF_FANFAULT = 0x0002, "Fan failed"  # Status.
    WDIOF_EXTERN1 = 0x0004, "External relay 1"  # Status.
    WDIOF_EXTERN2 = 0x0008, "External relay 2"  # Status.
    WDIOF_POWERUNDER = 0x0010, "Power bad/power fault"  # Status.
    WDIOF_CARDRESET = 0x0020, "Card previously reset the CPU"  # Status.
    WDIOF_POWEROVER = 0x0040, "Power over voltage"  # Status.
    WDIOF_SETTIMEOUT = 0x0080, "Set timeout (in seconds)"  # Capability.
    WDIOF_MAGICCLOSE = 0x0100, "Supports magic close char"  # Capability.
    WDIOF_PRETIMEOUT = 0x0200, "Pretimeout (in seconds), get/set"  # Capability.
    WDIOF_ALARMONLY = (
        0x0400,
        "Watchdog triggers a management or other external alarm not a reboot",
    )  # Capability.
    WDIOF_KEEPALIVEPING = 0x8000, "Keep alive ping reply"  # Status.


class Option(_IntFlagWithDesc):
    """Flags used to control some aspects of the card's operation."""

    WDIOS_UNKNOWN = -1, "Unknown status error"
    WDIOS_DISABLECARD = 0x0001, "Turn off the watchdog timer"
    WDIOS_ENABLECARD = 0x0002, "Turn on the watchdog timer"
    WDIOS_TEMPPANIC = 0x0004, "Kernel panic on temperature trip"
