from __future__ import annotations

import os
import platform
import shutil
import subprocess
from typing import Protocol


class PtyProcess(Protocol):
    cols: int
    rows: int

    def read(self, size: int = 4096) -> bytes: ...
    def write(self, data: bytes) -> None:
        ...
    def resize(self, cols: int, rows: int) -> None: ...
    def isalive(self) -> bool: ...


def default_shell() -> list[str]:
    if platform.system() == "Windows":
        for shell in ("pwsh", "powershell", "cmd"):
            found = shutil.which(shell)
            if found:
                return [found]
        return ["cmd"]
    return [os.environ.get("SHELL") or "/bin/sh"]


def shell_command(shell: str | None, command: list[str] | None = None) -> list[str]:
    if command:
        return command
    if shell is None or shell == "auto":
        return default_shell()
    found = shutil.which(shell)
    return [found or shell]


def spawn(argv: list[str], cols: int, rows: int) -> PtyProcess:
    if platform.system() == "Windows":
        return _WindowsPty(argv, cols, rows)
    return _PosixPty(argv, cols, rows)


class _PosixPty:
    def __init__(self, argv: list[str], cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        try:
            from ptyprocess import PtyProcess as RawPty
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install twiglterm[posix] for POSIX shell mode") from exc
        self.proc = RawPty.spawn(argv, dimensions=(rows, cols))

    def read(self, size: int = 4096) -> bytes:
        return self.proc.read(size)

    def write(self, data: bytes) -> None:
        self.proc.write(data)

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        self.proc.setwinsize(rows, cols)

    def isalive(self) -> bool:
        return self.proc.isalive()


class _WindowsPty:
    def __init__(self, argv: list[str], cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        try:
            import winpty
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install twiglterm[windows] for Windows shell mode") from exc

        command = subprocess.list2cmdline(argv)
        self.proc = winpty.PtyProcess.spawn(command, dimensions=(rows, cols))

    def read(self, size: int = 4096) -> bytes:
        data = self.proc.read(size)
        return data.encode(errors="replace") if isinstance(data, str) else data

    def write(self, data: bytes) -> None:
        self.proc.write(data.decode(errors="replace"))

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        self.proc.set_size(cols, rows)

    def isalive(self) -> bool:
        return self.proc.isalive()
