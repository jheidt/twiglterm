from __future__ import annotations

from .compositor import Cell


def text_cells(text: str, cols: int, rows: int) -> list[list[Cell]]:
    cells = blank_cells(cols, rows)
    y = 0
    x = 0
    for char in text.replace("\r\n", "\n").replace("\r", "\n"):
        if char == "\n":
            y += 1
            x = 0
            if y >= rows:
                break
            continue
        if char == "\t":
            spaces = 4 - (x % 4)
            for _ in range(spaces):
                if x < cols:
                    cells[y][x] = Cell(" ")
                    x += 1
            continue
        if x >= cols:
            y += 1
            x = 0
            if y >= rows:
                break
        cells[y][x] = Cell(char)
        x += 1
    return cells


def blank_cells(cols: int, rows: int) -> list[list[Cell]]:
    return [[Cell() for _ in range(cols)] for _ in range(rows)]

