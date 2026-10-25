"""admin — open an elevated Command Prompt in the current directory.

Windows asks for consent (UAC) as usual. Paths with spaces, ampersands or brackets work, since
the directory travels quoted to cmd's /k instead of through a PowerShell command line.
"""
import ctypes
import os
import sys


def main():
    if len(sys.argv) > 1:
        print("Usage: admin")
        sys.exit(0 if sys.argv[1] in ("-h", "--help") else 1)
    if os.name != "nt":
        sys.exit("admin is Windows-only.")
    # ShellExecuteW returns a value above 32 on success; 5 means the UAC prompt was declined.
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f'/k cd /d "{os.getcwd()}"', None, 1)
    if result <= 32:
        sys.exit("Not elevated: the UAC prompt was declined." if result == 5 else f"Could not start an elevated prompt (error {result}).")


if __name__ == "__main__":
    main()
