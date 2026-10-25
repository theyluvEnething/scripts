"""Unit tests for utilkit. Run: python -m unittest discover shared/tests"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utilkit import config, ports, ui, usage  # noqa: E402

SHARED = Path(__file__).resolve().parent.parent
# Listens on a free port and prints it; with an argument it also ignores SIGTERM.
LISTENER = """
import signal, socket, sys, time
if len(sys.argv) > 1:
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
s = socket.socket()
s.bind(("127.0.0.1", 0))
s.listen()
print(s.getsockname()[1], flush=True)
time.sleep(60)
"""


class TestPorts(unittest.TestCase):
    def listener(self, *args):
        proc = subprocess.Popen([sys.executable, "-c", LISTENER, *args], stdout=subprocess.PIPE, text=True)
        for cleanup in (proc.wait, proc.kill, proc.stdout.close):  # run in reverse order
            self.addCleanup(cleanup)
        return proc, int(proc.stdout.readline())

    def test_ps_durations(self):
        self.assertEqual(ports._seconds("05:07"), 307)
        self.assertEqual(ports._seconds("01:02:03"), 3723)
        self.assertEqual(ports._seconds("2-01:00:00"), 176400)
        self.assertAlmostEqual(ports._seconds("0:00.52"), 0.52)

    def test_finds_describes_and_stops_a_listener(self):
        proc, port = self.listener()
        entries = ports.on_port(port)
        self.assertEqual([e["pid"] for e in entries], [proc.pid])
        self.assertTrue(entries[0]["cmdline"], "no executable path")
        detail = ports.process_detail(proc.pid)
        self.assertEqual(detail["pid"], proc.pid)
        self.assertGreater(detail["memory_mb"], 0)
        ok, how = ports.kill(proc.pid)
        self.assertTrue(ok, how)
        self.assertIn(how, ("stopped", "killed"))
        self.assertEqual(ports.on_port(port), [])

    def test_force_kills_what_ignores_the_request(self):
        if os.name == "nt":
            self.skipTest("Windows force-stops at once")
        proc, _ = self.listener("ignore-term")
        self.assertEqual(ports.kill(proc.pid, grace=0.5), (True, "killed"))
        self.assertEqual(proc.wait(5), -9)


class TestUsage(unittest.TestCase):
    def test_records_read_back_and_tally(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp, "nested", "usage.tsv")
            usage.record("pc", "status", terminal=True, path=log)
            usage.record("pc", "", terminal=False, path=log)
            usage.record("ports", terminal=False, path=log)
            with open(log, "a", encoding="utf-8") as f:
                f.write("garbage line\nnot-a-date\tports\t\tterminal\n")
            runs = usage.read(log)
            self.assertEqual([r.command for r in runs], ["pc", "pc", "ports"])
            tallies = usage.tally(runs)
            self.assertEqual((tallies["pc"].runs, tallies["pc"].by_you), (2, 1))
            self.assertEqual(dict(tallies["pc"].verbs), {"status": 1})
            self.assertEqual(tallies["ports"].runs, 1)

    def test_macos_run_writes_the_same_format(self):
        if os.name == "nt":
            self.skipTest("macos/run is a shell script")
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, XDG_STATE_HOME=tmp)
            subprocess.run([str(SHARED.parent / "macos" / "run"), "pc", "help"], env=env,
                           stdin=subprocess.DEVNULL, capture_output=True, check=True)
            runs = usage.read(Path(tmp, "scripts", "usage.tsv"))
            self.assertEqual([(r.command, r.verb, r.terminal) for r in runs], [("pc", "help", False)])

    def test_windows_run_records_then_runs_the_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, XDG_STATE_HOME=tmp, LOCALAPPDATA=tmp)
            out = subprocess.run([sys.executable, str(SHARED / "run.py"), "check-port", "--help"], env=env,
                                 stdin=subprocess.DEVNULL, capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("Usage: check-port", out.stdout)
            log = Path(tmp, "scripts", "usage.tsv")
            self.assertEqual([r.command for r in usage.read(log)], ["check-port"])
            missing = subprocess.run([sys.executable, str(SHARED / "run.py"), "no-such-tool"], env=env,
                                     capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)


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
