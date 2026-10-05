#!/usr/bin/env python3
"""t3-pair: print a fresh T3 Code pairing link, for the Mac to open in its T3 app.

Run it on the PC over SSH when the Mac's T3 session has ended or expired::

    ssh pc t3-pair
    ssh pc t3-pair | pbcopy

The link is the only thing on stdout, so the pipe puts nothing else on the clipboard.
It works once and lapses after --ttl. T3's server has to be running already.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from utilkit import ui

_LINK = re.compile(r"^Pairing URL:\s*(\S+)", re.MULTILINE)


def _t3():
    """t3 is a .cmd launcher: found on PATH, or where its installer puts it."""
    found = shutil.which("t3") or str(Path.home() / ".local" / "bin" / "t3.cmd")
    return found if Path(found).exists() else None


def main():
    parser = argparse.ArgumentParser(prog="t3-pair", description="Print a fresh T3 Code pairing link.")
    parser.add_argument("--label", default="MacBook",
                        help="name in T3's connections list, which pc status looks for (default: MacBook)")
    parser.add_argument("--ttl", default="30m",
                        help="how long the link stays valid, for example 5m or 1h (default: 30m)")
    args = parser.parse_args()

    t3 = _t3()
    if not t3:
        ui.error("t3 is neither on PATH nor in ~/.local/bin.")
        sys.exit(1)

    run = subprocess.run([t3, "pair", "--tailscale", "--ttl", args.ttl, "--label", args.label],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = run.stdout + run.stderr
    link = _LINK.search(output)
    if run.returncode != 0 or not link:
        ui.error("t3 pair gave no pairing link.")
        # The QR code has no letters. t3 puts its error after its first ERROR marker and
        # follows it with a stack trace and advice for other setups, so show two lines.
        lines = [line.strip() for line in output.splitlines() if re.search(r"[A-Za-z]", line)]
        first = next((i for i, line in enumerate(lines) if "ERROR" in line), 0)
        for line in lines[first:first + 2]:
            print(f"  {line}", file=sys.stderr)
        print("  Is the server up? Get-ScheduledTask 'T3 Code server'", file=sys.stderr)
        sys.exit(1)

    print(f"Pairing link for {args.label}, valid for {args.ttl}, works once:", file=sys.stderr)
    print(link.group(1))


if __name__ == "__main__":
    main()
