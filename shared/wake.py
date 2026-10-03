#!/usr/bin/env python3
"""wake <NAME|MAC> — turn on a computer on this network with a Wake-on-LAN packet.

Names come from the ``[wake]`` table in ``~/.config/utilkit/config.toml``::

    [wake]
    pc = "34:5a:60:57:c2:e6"

The packet only reaches computers on the same local network, so from outside
home it needs a device there to send it.
"""
import re
import shutil
import socket
import subprocess
import sys

from utilkit import config, ui

_MAC = re.compile(r"^[0-9a-fA-F]{2}([:-]?)(?:[0-9a-fA-F]{2}\1){4}[0-9a-fA-F]{2}$")


def _names():
    path = config.config_dir() / "config.toml"
    try:
        import tomllib

        with open(path, "rb") as f:
            return tomllib.load(f).get("wake", {})
    except (OSError, ImportError, ValueError):
        return {}


def _broadcasts():
    """Every local broadcast address. macOS refuses 255.255.255.255 ("No route to host"),
    so the network's own address (e.g. 192.168.1.255 from ifconfig) has to be used too."""
    found = ["255.255.255.255"]
    if shutil.which("ifconfig"):
        out = subprocess.run(["ifconfig"], capture_output=True, text=True).stdout
        found += re.findall(r"\bbroadcast (\d+\.\d+\.\d+\.\d+)", out)
    return list(dict.fromkeys(found))


def main():
    names = _names()
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: wake <NAME|MAC>")
        if names:
            print("Known: " + ", ".join(f"{n} ({m})" for n, m in sorted(names.items())))
        sys.exit(0 if len(sys.argv) == 2 else 1)

    target = sys.argv[1]
    mac = names.get(target, target)
    if not _MAC.match(mac):
        ui.error(f"'{target}' is neither a known name nor a MAC address.")
        sys.exit(1)

    packet = b"\xff" * 6 + bytes.fromhex(re.sub(r"[:-]", "", mac)) * 16
    sent = []
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for address in _broadcasts():
            try:
                for _ in range(3):
                    s.sendto(packet, (address, 9))
                sent.append(address)
            except OSError:
                pass
    if not sent:
        ui.error("Could not send on any network. Are you on the same network as the computer?")
        sys.exit(1)
    ui.ok(f"Sent a wake packet to {ui.style(target, 'bold')} ({mac.lower()}) via {', '.join(sent)}.")


if __name__ == "__main__":
    main()
