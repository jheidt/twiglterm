import os
import re
import shlex
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


INTERACTIVE_COMMANDS = {
    "uv run twiglterm shell examples/gradient.frag -- $SHELL",
}


class ReadmeExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.commands = _readme_commands()

    def test_readme_commands_are_covered(self):
        self.assertGreater(len(self.commands), 8)
        for command in self.commands:
            with self.subTest(command=command):
                if command.startswith("uv sync "):
                    continue
                if _is_launcher(command):
                    self.assertTrue(_launcher_path(command).exists())
                    continue
                if command in INTERACTIVE_COMMANDS:
                    self.assertIn("shell", command)
                    continue
                self.assertIsNotNone(_smoke_command(command))

    def test_readme_cli_examples_smoke(self):
        for command in self.commands:
            if command.startswith("uv sync ") or command in INTERACTIVE_COMMANDS or _is_launcher(command):
                continue
            with self.subTest(command=command):
                argv, stdin = _smoke_command(command)
                result = subprocess.run(
                    argv,
                    input=stdin,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    cwd=ROOT,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout.strip() or "compare" in command)

    def test_performance_cli_smoke(self):
        commands = [
            ["play", "examples/gradient.frag", "--duration", "0.02", "--fps", "0", "--redraw", "diff"],
            ["bench", "examples/gradient.frag", "--terminal-width", "12", "--terminal-height", "6", "--iterations", "1"],
        ]
        for args in commands:
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, "-m", "twiglterm.cli", *args, "--render-width", "24", "--render-height", "12"],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    cwd=ROOT,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                    timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_pipe_diff_keeps_text_visible(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "twiglterm.cli",
                "pipe",
                "examples/gradient.frag",
                "--duration",
                "0.02",
                "--fps",
                "0",
                "--redraw",
                "diff",
                "--terminal-width",
                "12",
                "--terminal-height",
                "6",
                "--render-width",
                "24",
                "--render-height",
                "12",
            ],
            input="VISIBLE",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=ROOT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VISIBLE", ANSI_RE.sub("", result.stdout))


def _readme_commands() -> list[str]:
    text = README.read_text(encoding="utf-8")
    commands: list[str] = []
    for fence in re.finditer(r"```(?:bash|powershell)\n(.*?)```", text, re.DOTALL):
        for line in fence.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            commands.append(line)
    return commands


def _is_launcher(command: str) -> bool:
    return command.startswith("examples/") or command.startswith(r".\examples")


def _launcher_path(command: str) -> Path:
    return ROOT / command.replace(r".\\", "").replace(r".\examples", "examples")


def _smoke_command(command: str):
    stdin = None
    if command.startswith("cat "):
        left, right = command.split("|", 1)
        stdin = (ROOT / left.split()[1]).read_text(encoding="utf-8")
        command = right.strip()
    if command.startswith("uv run twiglterm frame https://twigl.app/"):
        return _twigl_url_smoke_command(command), stdin
    if not command.startswith("uv run twiglterm "):
        return None

    args = shlex.split(command.removeprefix("uv run twiglterm "), posix=False)
    args = [arg.strip('"') for arg in args]
    args = _bound_args(args)
    return [sys.executable, "-m", "twiglterm.cli", *args], stdin


def _twigl_url_smoke_command(command: str) -> list[str]:
    return [
        sys.executable,
        "-m",
        "twiglterm.cli",
        "info",
        command.removeprefix("uv run twiglterm frame ").split()[0],
    ]


def _bound_args(args: list[str]) -> list[str]:
    out: list[str] = []
    skip_next = False
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg in {
            "--terminal-width",
            "--width",
            "--terminal-height",
            "--height",
            "--render-width",
            "--render-height",
            "--duration",
            "--fps",
            "--time-scan",
            "--iterations",
        }:
            skip_next = True
            continue
        out.append(arg)

    command = out[0]
    if command in {"frame", "pipe", "play", "compare", "bench"}:
        out.extend(["--terminal-width", "12", "--terminal-height", "6"])
    if command in {"frame", "pipe", "play", "compare", "bench"}:
        out.extend(["--render-width", "24", "--render-height", "12"])
    if command in {"play", "pipe"}:
        out.extend(["--duration", "0.02", "--fps", "1"])
    if command == "bench":
        out.extend(["--iterations", "1"])
    if command == "compare":
        out.extend(["--time-scan", "11:11:1", "--min-score", "0.1"])
    return out


if __name__ == "__main__":
    unittest.main()
