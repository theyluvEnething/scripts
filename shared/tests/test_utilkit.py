"""Unit tests for utilkit. Run: python -m unittest discover shared/tests"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utilkit import config, ui  # noqa: E402


class TestConfig(unittest.TestCase):
    def test_reads_tables_and_tolerates_a_broken_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["UTILKIT_CONFIG_DIR"] = tmp
            try:
                self.assertEqual(config.load(), {})
                Path(tmp, "config.toml").write_text('[wake]\npc = "34:5a:60:57:c2:e6"\n')
                self.assertEqual(config.load()["wake"]["pc"], "34:5a:60:57:c2:e6")
                Path(tmp, "config.toml").write_text("[wake\n")
                self.assertEqual(config.load(), {})
            finally:
                del os.environ["UTILKIT_CONFIG_DIR"]


class TestUI(unittest.TestCase):
    def test_truncate_no_reset_when_plain(self):
        self.assertEqual(ui.truncate("abcdefghij", 5), "abcd…")
        self.assertNotIn("\x1b", ui.truncate("abcdefghij", 5))

    def test_truncate_closes_color(self):
        out = ui.truncate("\x1b[31mabcdefghij\x1b[0m", 5)
        self.assertTrue(out.endswith("\x1b[0m"))

    def test_truncate_keeps_short_text(self):
        self.assertEqual(ui.truncate("abc", 10), "abc")

    def test_card_lines_are_aligned(self):
        os.environ["COLUMNS"] = "100"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ui.card("title here", [
                ("PID", "1234"),
                ("Location", "C:/a/very/long/path/to/some/executable/program.exe"),
                (None, None),
                ("Memory", "20 MB"),
            ])
        widths = {ui.visible_len(line) for line in buf.getvalue().splitlines()}
        self.assertEqual(len(widths), 1, f"card lines misaligned: {widths}")


if __name__ == "__main__":
    unittest.main()
