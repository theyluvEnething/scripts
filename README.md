# toybox

My own tools for the Windows PC and the Mac: bridging a codebase into an LLM and
back, managing local ports, reconnecting to SSH servers, and small fixes for
whatever each system lacks. Tools that run on both systems live in `shared/`,
everything tied to one system in `windows/` or `macos/`.

## Install

On Windows, add `windows\bin` to your user `PATH` and install the one
third-party dependency: `pip install pyperclip`.

On macOS, add `macos/bin` to your `PATH` (mac-setup's `.zshrc` does this). Each
launcher runs its tool with `uv run --project shared`, so the first run creates
`shared/.venv` from `shared/pyproject.toml` and nothing goes into the system
Python.

Then run any command by name (e.g. `ports`, `show-port 5000`).

## Layout

```
shared/          Python tools that run on Windows and macOS, one .py per command
shared/utilkit/  shared library imported by every tool
shared/tests/    unit tests for utilkit
windows/         Windows-only tools: ls, cwd, sh, restart-fortnite
windows/bin/     .bat launchers, the folder Windows has on PATH
macos/awake/     awake, a Swift menu bar app and command line (see below)
macos/bin/       launchers for the shared tools, the folder the Mac has on PATH
docs/            design notes
```

Every launcher is a small shim named after its command.

## Commands

### Ports

| Command | Description |
| --- | --- |
| `ports` | List every listening TCP port and the process that owns it. |
| `show-port <PORT>` | Show what is listening on a port (read-only). Alias: `check-port`. |
| `stop-port <PORT>` | Kill whatever owns a port and report what was killed. `--dry-run` to preview. |

Port lookups use PowerShell (`Get-NetTCPConnection`) on Windows and `ss`/`lsof`
on Unix — invoked internally, so the tools work the same from `cmd`,
PowerShell, or a Unix terminal.

### Wake-on-LAN

| Command | Description |
| --- | --- |
| `wake <NAME\|MAC>` | Turn on a sleeping or shut-down computer on the same network. |

Names go in `~/.config/utilkit/config.toml` as a `[wake]` table, e.g. `pc = "34:5a:60:57:c2:e6"`.
The target needs Wake-on-LAN enabled in its BIOS and network adapter, and the packet only
reaches the local network, so from outside home a device there has to send it.

### SSH sessions

| Command | Description |
| --- | --- |
| `connect-server user@host [-p PORT] [-i KEY] [--label NAME]` | Connect via the system `ssh` client and remember the session. |
| `connect-server` | Pick a previously used server from a most-recent-first list. |
| `connect-server --list` | List saved servers. |
| `connect-server --remove <n>` | Forget the server at position `<n>`. |

Only connection details are stored (in `~/.config/utilkit/servers.json`) —
**never passwords**. Authentication is left entirely to `ssh` (keys, agent, or
its own prompt).

### LLM context bridge

| Command | Description |
| --- | --- |
| `analyze-project` | Collate the project (tree + files) with a read-and-answer prompt → clipboard. |
| `summarize-project` | Same collation with a make-the-change prompt, paired with `generate-project`. |
| `copy-files` | Copy just the XML-wrapped file contents (no prompt, no tree). |
| `project-structure` | Print and copy the directory tree. |
| `generate-project` | Apply `<file>`/`<delete>`/`<rename>` blocks from the clipboard, with a confirm step and path-safety checks. |

Common flags: `--only py` / `--only [py,js]` to include only some extensions,
`--ignore json` to add extra ignores, `--no-tree` to skip the tree.

| Command | Description |
| --- | --- |
| `get-programming-prompt` | Copy the standard engineer + file-format prompt. |
| `get-format-prompt` | Copy a "re-emit your last reply in the file format" prompt. |
| `get-remember-prompt` | Copy a short "keep using the file format" reminder. |

### Unix ergonomics

`extract` runs on both systems. `ls`, `cwd`, `sh` and `admin` are Windows only,
because macOS has its own.

| Command | Description |
| --- | --- |
| `ls [path]` | Colorized, grid-formatted directory listing. |
| `cwd` | Print the current directory with forward slashes and copy it. |
| `extract <archive>` | Unpack `.zip`/`.tar.*`/`.gz` (and `.7z`/`.rar` via helpers) into `./<name>/`, with zip-slip protection. |
| `sh <script.sh>` | Run a simple shell script with a lightweight built-in interpreter. |
| `admin` | Open an elevated prompt in the current directory (Windows). |

### Fortnite / UEFN

| Command | Description |
| --- | --- |
| `restart-fortnite` | Close every leftover `EpicWebHelper.exe`. `--dry-run` to preview. |

A crashed UEFN session leaves its `EpicWebHelper.exe` processes running, which
blocks the next launch until they are ended by hand in Task Manager.
`restart-fortnite` ends them the same way — a polite close, then a terminate for
anything that ignores it — so the editor can be started fresh. Windows only.

### awake (macOS)

Keeps a MacBook running with the lid closed while Claude Code or Codex is
working, and lets it sleep normally otherwise. On Apple Silicon without an
external display, only turning lid sleep off with the kernel's `SleepDisabled`
setting (`pmset -a disablesleep`) does that, and it turns off every other kind
of sleep with it; `caffeinate` only stops idle sleep. awake owns that setting.

Claude Code and Codex hooks mark each session as working from a prompt or
tool call until its turn ends. Lid sleep is off while a turn runs and comes
back on a minute after the last one finishes; if the lid is closed by then,
awake puts the Mac to sleep. A turn that sends no hook for 15 minutes, or whose
agent process is gone, no longer counts.

The cup in the menu bar shows what closing the lid does: an outline cup sleeps,
a filled cup keeps running, and a badge means lid sleep was changed outside
Awake or its helper isn't set up. The menu has:

- **Awake**: keeps the Mac running with the lid closed while Claude or Codex
  works. Unticked, the mode is Off: closing the lid puts the Mac to sleep.
- **Sleep Now**: shown while lid sleep is off, because macOS ignores the Apple
  menu's Sleep then.
- **Settings…**: also has **Stay awake indefinitely**: even when nothing runs,
  until you turn it off, restart or log out. The window shows lid sleep, what
  holds the Mac awake, the battery, the thermal state and Low Power.
- **Uninstall Awake…**: turns lid sleep back on, removes the helper, the login
  items, the Codex hooks and Awake's state and log, and moves the app to the
  Trash.

Whatever the mode, awake lets the Mac sleep at 20 % battery unless it is
charging (until it is back above 25 %), at 40 °C battery temperature (until
below 36 °C) and when the thermal state is high or critical. With the lid
closed on battery it switches to Low Power and restores your energy mode
afterwards. It never touches display settings. Changes go to
`~/Library/Logs/awake.log`.

| Command | Description |
| --- | --- |
| `awake run -- <command>` | Keep the Mac running while the command runs; passes Ctrl-C through and returns its exit code. |
| `awake for 90m` | Keep it running for a time (`90s`, `2h`, `1h30m`). `awake stop` ends every run and for. |
| `awake set off\|auto\|on` | Choose Off, Awake or Stay awake indefinitely. |
| `awake status` | The Settings window's rows: mode, lid sleep, what holds the Mac awake, the battery, the thermal state and Low Power. |

To install, open `Awake-<version>.dmg` from the
[releases](https://github.com/theyluvEnething/toybox/releases), drag Awake to
Applications and open it there. **Set Up Awake** in its setup window installs:

- A helper that runs as root and does nothing but `pmset -a disablesleep 0|1`
  and `pmset -b powermode 0|1|2`, and only for Awake's own app: it checks that
  the caller is signed by Awake's team as Awake. It also switches lid sleep back
  on once at every startup, because macOS keeps `disablesleep` across a restart
  and a crash could leave lid sleep off, and whenever the helper is switched
  off or the app is gone. macOS asks you to allow it in System Settings >
  General > Login Items & Extensions.
- Two login items: the menu, and a check every 30 seconds that keeps working if
  the menu crashes or is quit.
- Its hooks in `~/.codex/hooks.json`, next to your own; trust them once with
  `/hooks` in Codex.

Claude Code's hooks you add yourself: **Copy Hooks** copies them for
`~/.claude/settings.json`, or for
`/Library/Application Support/ClaudeCode/managed-settings.json` where managed
settings allow only managed hooks (that needs an administrator). The command
line is the app's binary, `/Applications/Awake.app/Contents/MacOS/awake`;
`macos/bin/awake` runs it.

`macos/awake/release.sh` builds a release: it builds `Awake.xcodeproj`, checks
both binaries' signatures, notarizes and staples the app, and puts it in a
signed, notarized DMG in `macos/awake/dist/`, next to a Homebrew cask for it.
It signs with the keychain's Developer ID Application identity of team
`KSF29ZC99W` and notarizes with the notarytool keychain profile `notary`;
`AWAKE_TEAM_ID`, `AWAKE_SIGN_IDENTITY` and `AWAKE_NOTARY_PROFILE` override them.
`--skip-notarize` checks everything else with any identity.

## Architecture

Shared logic lives in `shared/utilkit/` so the tools don't duplicate it:

- `config.py` — the single source of truth for ignore rules; extendable via
  `~/.config/utilkit/config.toml`.
- `walk.py` — project walking, tree rendering, binary detection.
- `collate.py` / `prompts.py` — XML collation and the embedded prompts.
- `ports.py` / `platform_ps.py` — port lookup and process control per platform.
- `sessions.py` — the SSH session store.
- `fileops.py` — parsing/applying file-operation blocks.
- `ui.py` — shared colors, tables, and headers (with ASCII fallback on legacy
  consoles).

## Tests

awake: `swift test --package-path macos/awake --scratch-path macos/awake/build`

```
python shared/tests/test_utilkit.py                    # Windows
uv run --project shared shared/tests/test_utilkit.py   # macOS
```

## Configuration

Drop a `~/.config/utilkit/config.toml` to extend the ignore lists without
editing source:

```toml
ignore_directories = ["my_cache"]
ignore_extensions = ["bak2"]
ignore_filenames = ["NOTES.txt"]
```

## Disclaimer

`generate-project`, `stop-port`, and `restart-fortnite` change your filesystem /
kill processes. `generate-project` confirms before writing and rejects unsafe
paths; `stop-port` and `restart-fortnite` act immediately (use `--dry-run`
first if unsure).
