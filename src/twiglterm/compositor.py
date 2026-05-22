from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .ansi import ColorMode
from .terminal_output import composite_bytes

try:
    import pyte
except Exception:  # pragma: no cover
    pyte = None


@dataclass(frozen=True)
class Cell:
    data: str = " "
    fg: tuple[int, int, int] = (230, 230, 230)
    bold: bool = False
    reverse: bool = False


class TerminalModel:
    def __init__(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        if pyte is None:
            self.screen = None
            self.stream = None
        else:
            self.screen = pyte.Screen(cols, rows)
            self.stream = pyte.Stream(self.screen)

    def resize(self, cols: int, rows: int) -> None:
        self.cols = cols
        self.rows = rows
        if self.screen is not None:
            self.screen.resize(rows, cols)

    def feed(self, data: str) -> None:
        if self.stream is not None:
            self.stream.feed(data)

    def cells(self) -> list[list[Cell]]:
        if self.screen is None:
            return [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]

        out: list[list[Cell]] = []
        for y in range(self.rows):
            line: list[Cell] = []
            for x in range(self.cols):
                char = self.screen.buffer[y][x]
                rgb = _named_color(char.fg)
                line.append(Cell(char.data, rgb, bool(char.bold), bool(char.reverse)))
            out.append(line)
        return out

    @property
    def cursor(self) -> tuple[int, int]:
        if self.screen is None:
            return (0, 0)
        return (self.screen.cursor.x, self.screen.cursor.y)


def composite(
    shader_pixels: np.ndarray,
    cells: Iterable[Iterable[Cell]],
    color_mode: ColorMode = ColorMode.truecolor,
    opacity: float = 0.35,
    cursor: tuple[int, int] | None = None,
) -> str:
    return composite_bytes(shader_pixels, cells, color_mode, opacity, cursor).data.decode("utf-8", errors="replace")


def _named_color(name: str) -> tuple[int, int, int]:
    colors = {
        "black": (0, 0, 0),
        "red": (205, 49, 49),
        "green": (13, 188, 121),
        "brown": (229, 229, 16),
        "blue": (36, 114, 200),
        "magenta": (188, 63, 188),
        "cyan": (17, 168, 205),
        "white": (229, 229, 229),
        "default": (229, 229, 229),
    }
    return colors.get(str(name), colors["default"])
