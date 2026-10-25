"""The usage log: one line per run of a command, written by the launchers, read by ``scripts``.

Each machine keeps its own log, ``~/.local/state/scripts/usage.tsv`` on the Mac and
``%LOCALAPPDATA%\\scripts\\usage.tsv`` on Windows. A line has four tab-separated fields::

    2026-10-25T21:03:11+0200    pc    status    terminal

the time, the command, its subcommand (pc and vienna only, never other arguments), and
``terminal`` when a person typed it or ``script`` when an agent or another program ran it.
macos/run writes the same format from the shell.
"""
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


def log_path():
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "scripts" / "usage.tsv"
    return Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "scripts" / "usage.tsv"


def record(command, verb="", *, terminal=None, path=None):
    """Append one run. Never fails the command it counts."""
    if terminal is None:
        terminal = sys.stdin is not None and sys.stdin.isatty()
    line = "\t".join([datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"), command, verb,
                      "terminal" if terminal else "script"])
    path = Path(path) if path else log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")
    except OSError:
        pass


@dataclass
class Run:
    when: datetime
    command: str
    verb: str
    terminal: bool


def parse(text):
    """The runs in a log's text, skipping lines that don't parse."""
    runs = []
    for line in text.splitlines():
        parts = line.rstrip("\r").split("\t")
        if len(parts) != 4 or not parts[1]:
            continue
        try:
            when = datetime.strptime(parts[0], "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            continue
        runs.append(Run(when, parts[1], parts[2], parts[3] == "terminal"))
    return runs


def read(path=None):
    try:
        return parse(Path(path or log_path()).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


@dataclass
class Tally:
    runs: int = 0
    by_you: int = 0
    last: datetime | None = None
    verbs: Counter = field(default_factory=Counter)


def tally(runs):
    """Runs per command: total, typed by a person, the latest, and per subcommand."""
    out = {}
    for run in runs:
        t = out.setdefault(run.command, Tally())
        t.runs += 1
        t.by_you += run.terminal
        if t.last is None or run.when > t.last:
            t.last = run.when
        if run.verb:
            t.verbs[run.verb] += 1
    return out
