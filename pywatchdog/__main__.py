#!/usr/bin/env python3

import argparse
import errno
import subprocess
import sys
import time
from pathlib import Path
from shutil import which

from pywatchdog import Watchdog

uname = which("uname")
modprobe = which("modprobe")
whoami = which("whoami")


def has_watchdog(strict=False):
    if strict:
        return has_watchdog() and Path("/dev/watchdog0").is_char_device()
    return Path("/dev/watchdog").is_char_device()


def run(args):
    return subprocess.run(
        args, capture_output=True, check=True, text=True
    ).stdout.strip()


def find_module(args):
    if has_watchdog():
        sys.exit("A watchdog module is already loaded.")

    kernel_release = run([uname, "-r"])

    for p in Path(f"/lib/modules/{kernel_release}/kernel/drivers/watchdog").iterdir():
        module = p.stem
        if module == "softdog":
            continue
        try:
            run([modprobe, module])
        except subprocess.CalledProcessError as e:
            if "Operation not permitted" in e.stderr:
                sys.exit(
                    f"User {run(whoami)} doesn't have permission "
                    "to insert a module with modprobe. Try running as root"
                )
            continue
        if has_watchdog(args.all):
            print(f"module {module} might work")
        run([modprobe, "-r", module])


def test_reboot(args):
    with Watchdog(args.device) as wdt:
        if args.timeout is not None:
            wdt.timeout = args.timeout
        has_time_left = wdt.time_left is not None
        time_left = wdt.time_left if has_time_left else wdt.timeout
        sleep = 1
        while True:
            print("Time left before reboot:", time_left, end="    \r")
            try:
                time.sleep(sleep)
            except KeyboardInterrupt:
                print()
                break
            time_left = wdt.time_left if has_time_left else time_left - sleep


def main():
    parser = argparse.ArgumentParser(description="Command-line utility for pywatchdog")
    subparsers = parser.add_subparsers()

    parser_fm = subparsers.add_parser(
        "find-module",
        aliases=["fm"],
        help="""find which watchdog kernel modules might work for your system.
                The softdog module is ignored because it is a software watchdog
             """,
    )

    parser_fm.add_argument(
        "-a",
        "--all",
        action="store_false",
        help="only look for the presence of /dev/watchdog",
    )

    parser_fm.set_defaults(func=find_module)

    parser_tr = subparsers.add_parser(
        "test-reboot",
        aliases=["tr"],
        help="""test the watchdog to see if your computer reboots when the
                timeout occurs. Ctrl-C to abort""",
    )

    parser_tr.add_argument(
        "-t", "--timeout", type=int, help="the timeout that will be set for the test"
    )

    parser_tr.add_argument(
        "-d", "--device", default="/dev/watchdog", help="default: %(default)s"
    )

    parser_tr.set_defaults(func=test_reboot)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit()
    try:
        args.func(args)
    except FileNotFoundError:
        sys.exit(f"{args.device} not found")
    except PermissionError as e:
        if e.errno == errno.EACCES:
            sys.exit(
                f"User {run(whoami)} can't access {args.device}. Try running as root"
            )
        raise
    except OSError as e:
        if e.errno == errno.EBUSY:
            sys.exit(f"{args.device} is already used by a different process")
        raise


if __name__ == "__main__":
    main()
