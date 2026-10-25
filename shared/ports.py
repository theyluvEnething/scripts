#!/usr/bin/env python3
"""ports — list every listening TCP port with its owning process."""
import sys

from utilkit import ports as backend
from utilkit import ui


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: ports")
        print("Lists all listening TCP ports and the process that owns each.")
        sys.exit(0)

    entries = backend.list_listening()
    if not entries:
        ui.info("No listening TCP ports found.")
        return

    ui.header(f"Listening ports ({len(entries)})")
    rows = [
        [str(e["port"]), e["process"], str(e["pid"]), e["cmdline"] or "—"]
        for e in entries
    ]
    headers = ["PORT", "PROCESS", "PID", "PATH"]
    if sys.stdout.isatty():  # fit the window; piped output keeps whole paths
        fixed = sum(max(len(h), *(len(r[i]) for r in rows)) + 2 for i, h in enumerate(headers[:3]))
        for row in rows:
            row[3] = ui.truncate(row[3], max(20, ui.term_width() - fixed))
    ui.table(rows, headers, aligns=["r", "l", "r", "l"])


if __name__ == "__main__":
    main()
