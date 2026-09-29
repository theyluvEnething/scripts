# utility

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
