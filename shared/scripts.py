#!/usr/bin/env python3
"""scripts — list every command here with how often it ran and when it last did.

Doubles as the index for a forgotten command name. Counts come from this machine's usage log,
which every launcher appends to (see utilkit/usage.py). ``--all`` on the Mac adds the Windows PCs'
logs over SSH; a PC that does not answer is skipped.
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from utilkit import ui, usage

ROOT = Path(__file__).resolve().parent.parent
# Commands whose file describes a different command first.
DESCRIPTIONS = {"vienna": "pc for the Vienna PC (DESKTOP-V13NNA): the same subcommands"}
REMOTE_LOG = "Get-Content -Raw -ErrorAction SilentlyContinue (Join-Path $env:LOCALAPPDATA 'scripts\\usage.tsv')"


def installed(windows):
    """The commands a machine's launcher folder offers."""
    folder = ROOT / ("windows" if windows else "macos") / "bin"
    return sorted(p.stem for p in folder.iterdir() if p.is_file() and not p.name.startswith("."))


def source(command, windows):
    if not windows and command in ("pc", "vienna"):
        return ROOT / "macos" / "pc" / "pc"
    for folder in ("shared", "windows"):
        path = ROOT / folder / f"{command}.py"
        if path.is_file():
            return path
    return None


def describe(command, windows):
    """The first sentence of the command's docstring or header comment, without its name."""
    if command in DESCRIPTIONS:
        return DESCRIPTIONS[command]
    path = source(command, windows)
    if path is None:
        return "no longer installed"
    text = path.read_text(encoding="utf-8", errors="replace")
    doc = re.search(r'"""(.+)', text) if path.suffix == ".py" else re.search(r"^# (.+)", text, re.MULTILINE)
    if not doc:
        return ""
    first = re.sub(rf"^{re.escape(command)}\b[^—:]*[—:]\s*", "", doc.group(1).split('"""')[0].strip())
    first = re.split(r"\.(?:\s|$)", first)[0]
    return first[:1].upper() + first[1:]


def when(moment, now):
    if moment is None:
        return "never"
    days = (now.date() - moment.date()).days
    if days == 0:
        return f"today {moment:%H:%M}"
    if days == 1:
        return f"yesterday {moment:%H:%M}"
    if days < 7:
        return f"{days} days ago"
    return f"{moment.day} {moment:%b %Y}" if moment.year != now.year else f"{moment.day} {moment:%b}"


def show(title, runs, commands, windows):
    tallies = usage.tally(runs)
    now = datetime.now().astimezone()
    names = sorted(set(commands) | set(tallies), key=lambda c: (-tallies.get(c, usage.Tally()).runs, c))
    rows = []
    for name in names:
        t = tallies.get(name, usage.Tally())
        rows.append([name, str(t.runs), str(t.by_you), when(t.last, now), describe(name, windows)])
    headers = ["COMMAND", "RUNS", "BY YOU", "LAST RUN", "WHAT IT DOES"]
    fixed = sum(max(len(h), *(len(r[i]) for r in rows)) + 2 for i, h in enumerate(headers[:4]))
    room = max(20, min(ui.term_width(), 120) - fixed)
    for row in rows:
        row[4] = ui.truncate(row[4], room)
    ui.header(title)
    ui.table(rows, headers, aligns=["l", "r", "r", "l", "l"])
    for name in names:
        verbs = tallies.get(name, usage.Tally()).verbs
        if verbs:
            print(ui.style(f"  {name}: " + ", ".join(f"{v} {n}" for v, n in verbs.most_common()), "dim"))
    first = min((r.when for r in runs), default=None)
    print(ui.style(f"  Counting since {first:%d %b %Y}." if first else "  Nothing counted yet.", "dim"))


def remote(host):
    try:
        out = subprocess.run(["ssh", "-o", "ConnectTimeout=8", "-o", "BatchMode=yes", host, REMOTE_LOG],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return usage.parse(out.stdout) if out.returncode == 0 else None


def main():
    parser = argparse.ArgumentParser(prog="scripts", description="List every command with its run count and last run.")
    parser.add_argument("--all", action="store_true", help="also show the Windows PCs (pc, vienna) over SSH, from the Mac")
    args = parser.parse_args()

    windows = os.name == "nt"
    show(f"Commands on this {'PC' if windows else 'Mac'}", usage.read(), installed(windows), windows)
    print(ui.style(f"  Log: {usage.log_path()}", "dim"))
    if args.all and not windows:
        for host in ("pc", "vienna"):
            print()
            runs = remote(host)
            if runs is None:
                ui.warn(f"ssh {host} did not answer; its counts are not shown.")
                continue
            show(f"Commands on {host}", runs, installed(True), True)


if __name__ == "__main__":
    sys.exit(main())
