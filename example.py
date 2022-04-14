#!/usr/bin/env python3

import time
import signal
from functools import partial

from pywatchdog import Watchdog

DEFAULT_DEVICE = "/dev/watchdog"

# Disable buffering so that messages are instantly displayed in systemctl status.
printnow = partial(print, flush=True)


class SimpleWatchdogDaemon:
    """A very basic daemon that notifies the watchdog every second."""

    def __init__(self, device=DEFAULT_DEVICE):
        self._device = device
        self._running = False
        self._set_handlers()

    def _set_handlers(self):
        signal.signal(signal.SIGINT, self.handler)
        signal.signal(signal.SIGTERM, self.handler)  # Sent by systemd (KillSignal).

    def handler(self, signum, frame):
        self._running = False
        printnow(f"Received {signal.Signals(signum).name}. Stopping...")

    def run(self):
        with Watchdog(self._device) as wdt:
            printnow("pywatchdog daemon started successfully.")
            self._running = True
            while self._running:
                wdt.keep_alive()
                time.sleep(1)


if __name__ == "__main__":
    import argparse
    import errno
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "device", nargs="?", default=DEFAULT_DEVICE, help="default: %(default)s"
    )
    args = parser.parse_args()

    daemon = SimpleWatchdogDaemon(args.device)
    try:
        daemon.run()
    except FileNotFoundError:
        sys.exit(f"{args.device} not found")
    except PermissionError as e:
        if e.errno == errno.EACCES:
            sys.exit(f"Can't access {args.device}. Try running as root")
        raise
    except OSError as e:
        if e.errno == errno.EBUSY:
            sys.exit(f"{args.device} is already used by a different process")
        raise
    printnow("pywatchdog daemon stopped successfully.")
