"""Windows launcher: ``python run.py <command> [args...]`` records the run, then runs the command.

Every ``windows\\bin\\<command>.bat`` is the same line and passes its own name. The command is
``shared\\<command>.py`` or ``windows\\<command>.py``; either imports utilkit from here.
"""
import runpy
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
sys.path.insert(0, str(SHARED))

from utilkit import usage  # noqa: E402


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: run.py <command> [args...]")
    command, args = sys.argv[1], sys.argv[2:]
    tool = next((p for p in (SHARED / f"{command}.py", SHARED.parent / "windows" / f"{command}.py") if p.is_file()), None)
    if tool is None:
        sys.exit(f"{command}: no shared\\{command}.py or windows\\{command}.py")
    usage.record(command)
    sys.argv = [str(tool), *args]
    runpy.run_path(str(tool), run_name="__main__")


if __name__ == "__main__":
    main()
