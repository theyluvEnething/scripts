"""The user's settings: ``~/.config/utilkit/config.toml`` (or ``$UTILKIT_CONFIG_DIR``).

Today only ``wake`` reads it, for its ``[wake]`` table of names.
"""
import os
import tomllib
from pathlib import Path


def config_dir():
    """Per-user config directory, the same on Windows and macOS."""
    override = os.environ.get("UTILKIT_CONFIG_DIR")
    return Path(override) if override else Path.home() / ".config" / "utilkit"


def load():
    """The parsed ``config.toml``, or an empty dict if it is missing or unreadable."""
    try:
        with open(config_dir() / "config.toml", "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
