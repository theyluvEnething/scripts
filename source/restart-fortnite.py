#!/usr/bin/env python3
"""restart-fortnite — close every EpicWebHelper.exe left behind by Fortnite/UEFN.

When a UEFN session crashes, its EpicWebHelper processes survive and block the
next launch, so the usual fix is ending each one by hand in Task Manager. This
does the same thing in one command: a polite close first, a terminate if the
process ignores it. ``--dry-run`` only lists what would be closed.
"""
import json
import os
import sys

from utilkit import platform_ps, ui

PROCESS_NAME = "EpicWebHelper"

_PS_LIST = r"""
$ErrorActionPreference = 'SilentlyContinue'
$out = foreach ($p in Get-Process -Name '%s') {
    [pscustomobject]@{
        pid  = $p.Id
        path = if ($p.Path) { $p.Path } else { '' }
    }
}
$out | ConvertTo-Json -Compress -Depth 3
""" % PROCESS_NAME

# Mirrors Task Manager's "End task": ask a windowed process to close, then
# terminate anything still alive (EpicWebHelper is windowless, so in practice
# this is the terminate branch).
_PS_STOP = r"""
$ErrorActionPreference = 'SilentlyContinue'
$out = foreach ($p in Get-Process -Name '%s') {
    $id = $p.Id
    $path = if ($p.Path) { $p.Path } else { '' }
    $method = 'closed'
    if ($p.MainWindowHandle -ne 0) {
        $null = $p.CloseMainWindow()
        $null = $p.WaitForExit(2000)
    }
    $p.Refresh()
    if (-not $p.HasExited) {
        $method = 'terminated'
        Stop-Process -Id $id -Force
        $null = $p.WaitForExit(3000)
    }
    $p.Refresh()
    [pscustomobject]@{ pid = $id; path = $path; method = $method; ok = $p.HasExited }
}
$out | ConvertTo-Json -Compress -Depth 3
""" % PROCESS_NAME


def _run(script):
    """Run a PowerShell script and return its rows as a list of dicts."""
    code, out, err = platform_ps.run(script, timeout=60)
    if code != 0:
        ui.error(err.strip() or "PowerShell call failed.")
        sys.exit(1)
    if not out.strip():
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        ui.error("Could not read the process list from PowerShell.")
        sys.exit(1)
    return [data] if isinstance(data, dict) else data


def main():
    args = sys.argv[1:]
    dry_run = False
    if "--dry-run" in args:
        dry_run = True
        args = [a for a in args if a != "--dry-run"]

    if args:
        print("Usage: restart-fortnite [--dry-run]")
        sys.exit(0 if args[0] in ("-h", "--help") else 1)

    if os.name != "nt":
        ui.error("restart-fortnite is Windows-only — Fortnite and UEFN do not run elsewhere.")
        sys.exit(1)

    running = _run(_PS_LIST)
    if not running:
        ui.info(f"No {ui.style(PROCESS_NAME + '.exe', 'bold')} processes are running. Nothing to do.")
        return

    if dry_run:
        ui.header(f"Would close {len(running)} {PROCESS_NAME}.exe process(es)")
        rows = [[str(p["pid"]), p["path"] or "—"] for p in running]
        ui.table(rows, ["PID", "PATH"], aligns=["r", "l"])
        return

    ui.header(f"Closing {len(running)} {PROCESS_NAME}.exe process(es)")
    failures = 0
    for entry in _run(_PS_STOP):
        label = f"{PROCESS_NAME}.exe (PID {entry['pid']})"
        if entry.get("ok"):
            ui.ok(f"{entry.get('method', 'closed')} {ui.style(label, 'bold')}")
        else:
            ui.error(f"failed to close {label}")
            failures += 1

    if failures:
        ui.warn("Some processes survived — try again from an elevated prompt (`admin`).")
        sys.exit(1)

    ui.info("Fortnite and UEFN can be started fresh now.")


if __name__ == "__main__":
    main()
