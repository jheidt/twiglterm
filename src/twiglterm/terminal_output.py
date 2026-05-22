from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np


RESET = b"\x1b[0m"
HOME = b"\x1b[H"
HIDE_CURSOR = b"\x1b[?25l"
SHOW_CURSOR = b"\x1b[?25h"

_BRAILLE_WEIGHTS = np.array(((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80)), dtype=np.uint8)


@dataclass(frozen=True)
class FrameBytes:
    data: bytes
    rows: list[bytes]


def frame_from_rows(rows: Sequence[bytes]) -> FrameBytes:
    row_list = list(rows)
    return FrameBytes(b"\n".join(row_list), row_list)


def full_redraw(frame: FrameBytes) -> bytes:
    return HOME + frame.data


def diff_redraw(previous: FrameBytes | None, current: FrameBytes) -> bytes:
    if previous is None:
        return full_redraw(current)
    out: list[bytes] = []
    limit = max(len(previous.rows), len(current.rows))
    blank = RESET
    for row_index in range(limit):
        old = previous.rows[row_index] if row_index < len(previous.rows) else blank
        new = current.rows[row_index] if row_index < len(current.rows) else blank
        if old != new:
            out.append(f"\x1b[{row_index + 1};1H".encode("ascii"))
            out.append(new)
    return b"".join(out)


def encoded_redraw(previous: FrameBytes | None, current: FrameBytes, redraw: str) -> bytes:
    if redraw == "full":
        return full_redraw(current)
    return diff_redraw(previous, current)


def pixels_to_terminal_bytes(
    pixels: np.ndarray,
    color: object = "truecolor",
    style: object = "half",
    drawille_threshold: float = 32.0,
) -> FrameBytes:
    if _enum_value(style) == "drawille":
        return pixels_to_drawille_bytes(pixels, color, drawille_threshold)
    return pixels_to_half_blocks_bytes(pixels, color)


def pixels_to_half_blocks_bytes(pixels: np.ndarray, color: object = "truecolor") -> FrameBytes:
    rgb = _rgb_pixels(pixels)
    h, w = rgb.shape[:2]
    bottom_pad = np.zeros((1, w, 3), dtype=np.uint8)
    rows: list[bytes] = []
    for y in range(0, h, 2):
        top = rgb[y]
        bottom = rgb[y + 1] if y + 1 < h else bottom_pad[0]
        writer = _AnsiRowWriter(color, use_bg=True)
        for x in range(w):
            writer.cell("▀", top[x], bottom[x])
        rows.append(writer.finish())
    return frame_from_rows(rows)


def pixels_to_drawille_bytes(
    pixels: np.ndarray,
    color: object = "truecolor",
    threshold: float = 32.0,
) -> FrameBytes:
    rgb = _rgb_pixels(pixels)
    h, w = rgb.shape[:2]
    pad_h = (-h) % 4
    pad_w = (-w) % 2
    if pad_h or pad_w:
        rgb = np.pad(rgb, ((0, pad_h), (0, pad_w), (0, 0)), mode="constant")

    rows_count = rgb.shape[0] // 4
    cols_count = rgb.shape[1] // 2
    cells = rgb.reshape(rows_count, 4, cols_count, 2, 3).transpose(0, 2, 1, 3, 4)
    luma = cells[..., 0] * 0.2126 + cells[..., 1] * 0.7152 + cells[..., 2] * 0.0722
    lit_mask = luma >= threshold
    bits = (lit_mask.astype(np.uint8) * _BRAILLE_WEIGHTS).sum(axis=(2, 3)).astype(np.uint16)
    colors = _drawille_colors(cells, lit_mask, bits)
    color_name = _enum_value(color)

    rows: list[bytes] = []
    for y in range(rows_count):
        writer = _AnsiRowWriter(color, use_bg=False)
        for x in range(cols_count):
            bitfield = int(bits[y, x])
            char = chr(0x2800 + bitfield) if bitfield else " "
            if color_name == "mono":
                fg_rgb = (255, 255, 255) if bitfield else (0, 0, 0)
            else:
                fg_rgb = colors[y, x]
            writer.cell(char, fg_rgb, None)
        rows.append(writer.finish())
    return frame_from_rows(rows)


def composite_bytes(
    shader_pixels: np.ndarray,
    cells: Iterable[Iterable[object]],
    color: object = "truecolor",
    opacity: float = 0.35,
    cursor: tuple[int, int] | None = None,
) -> FrameBytes:
    rgb = _rgb_pixels(shader_pixels)
    opacity = max(0.0, min(1.0, float(opacity)))
    background = np.clip(rgb.astype(np.float32) * opacity, 0, 255).astype(np.uint8)
    rows: list[bytes] = []
    for y, row in enumerate(cells):
        writer = _AnsiRowWriter(color, use_bg=True)
        src_y = min(y * 2, background.shape[0] - 1)
        for x, cell in enumerate(row):
            src_x = min(x, background.shape[1] - 1)
            is_cursor = cursor == (x, y)
            back_rgb = (230, 230, 230) if is_cursor else background[src_y, src_x, :3]
            fore_rgb = (0, 0, 0) if is_cursor else getattr(cell, "fg", (230, 230, 230))
            char = getattr(cell, "data", " ")
            if char == "\x00":
                char = " "
            writer.cell(char, fore_rgb, back_rgb, bool(getattr(cell, "bold", False)))
        rows.append(writer.finish())
    return frame_from_rows(rows)


def rgb_to_ansi256(r: int, g: int, b: int) -> int:
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return 232 + round(((r - 8) / 247) * 24)
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)


class _AnsiRowWriter:
    def __init__(self, color: object, use_bg: bool) -> None:
        self.color = _enum_value(color)
        self.use_bg = use_bg
        self.parts: list[bytes] = []
        self.current_fg: tuple[int, int, int] | int | None = None
        self.current_bg: tuple[int, int, int] | int | None = None
        self.current_bold = False

    def cell(
        self,
        char: str,
        fg_rgb: Sequence[int] | np.ndarray,
        bg_rgb: Sequence[int] | np.ndarray | None,
        bold: bool = False,
    ) -> None:
        fg_key = _color_key(fg_rgb, self.color)
        bg_key = _color_key(bg_rgb, self.color) if self.use_bg and bg_rgb is not None else None
        sgr: list[str] = []
        if fg_key != self.current_fg:
            sgr.append(_fg_sgr(fg_rgb, self.color, fg_key))
            self.current_fg = fg_key
        if self.use_bg and bg_key != self.current_bg:
            assert bg_rgb is not None
            sgr.append(_bg_sgr(bg_rgb, self.color, bg_key))
            self.current_bg = bg_key
        if bold != self.current_bold:
            sgr.append("1" if bold else "22")
            self.current_bold = bold
        if sgr:
            self.parts.append(("\x1b[" + ";".join(sgr) + "m").encode("ascii"))
        self.parts.append(str(char).encode("utf-8", errors="replace"))

    def finish(self) -> bytes:
        self.parts.append(RESET)
        return b"".join(self.parts)


def _rgb_pixels(pixels: np.ndarray) -> np.ndarray:
    if pixels.ndim != 3 or pixels.shape[2] < 3:
        raise ValueError("pixels must be an HxWxRGB/RGBA array")
    return np.ascontiguousarray(pixels[:, :, :3], dtype=np.uint8)


def _drawille_colors(cells: np.ndarray, lit_mask: np.ndarray, bits: np.ndarray) -> np.ndarray:
    lit = lit_mask[..., None]
    lit_counts = lit_mask.sum(axis=(2, 3)).clip(min=1)[..., None]
    lit_sum = (cells * lit).sum(axis=(2, 3))
    lit_avg = lit_sum / lit_counts
    cell_avg = cells.mean(axis=(2, 3))
    colors = np.where(bits[..., None] > 0, lit_avg, cell_avg)
    return np.clip(colors, 0, 255).astype(np.uint8)


def _fg_sgr(rgb: Sequence[int] | np.ndarray, mode: str, key: tuple[int, int, int] | int) -> str:
    if mode == "mono":
        return "37" if key else "30"
    if mode == "ansi256":
        return f"38;5;{key}"
    r, g, b = _rgb_tuple(rgb)
    return f"38;2;{r};{g};{b}"


def _bg_sgr(rgb: Sequence[int] | np.ndarray, mode: str, key: tuple[int, int, int] | int) -> str:
    if mode == "mono":
        return "47" if key else "40"
    if mode == "ansi256":
        return f"48;5;{key}"
    r, g, b = _rgb_tuple(rgb)
    return f"48;2;{r};{g};{b}"


def _color_key(rgb: Sequence[int] | np.ndarray | None, mode: str) -> tuple[int, int, int] | int:
    if rgb is None:
        return 0
    r, g, b = _rgb_tuple(rgb)
    if mode == "mono":
        return int((r + g + b) / 3 > 127)
    if mode == "ansi256":
        return rgb_to_ansi256(r, g, b)
    return (r, g, b)


def _rgb_tuple(rgb: Sequence[int] | np.ndarray) -> tuple[int, int, int]:
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]))


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))
