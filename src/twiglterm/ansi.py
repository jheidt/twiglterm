from __future__ import annotations

from enum import Enum
from typing import Iterable

import numpy as np


class ColorMode(str, Enum):
    truecolor = "truecolor"
    ansi256 = "ansi256"
    mono = "mono"


class RenderStyle(str, Enum):
    half = "half"
    drawille = "drawille"


RESET = "\x1b[0m"
BRAILLE_BITS = (
    (0x01, 0x08),
    (0x02, 0x10),
    (0x04, 0x20),
    (0x40, 0x80),
)
_RESIZE_INDEX_CACHE: dict[tuple[int, int, int, int], tuple[np.ndarray, np.ndarray]] = {}


def dim_pixels(pixels: np.ndarray, opacity: float) -> np.ndarray:
    opacity = max(0.0, min(1.0, opacity))
    return np.clip(pixels.astype(np.float32) * opacity, 0, 255).astype(np.uint8)


def scale_pixels(pixels: np.ndarray, level: float) -> np.ndarray:
    level = max(0.0, level)
    if level == 1.0:
        return pixels
    return np.clip(pixels.astype(np.float32) * level, 0, 255).astype(np.uint8)


def resize_pixels_nearest(pixels: np.ndarray, width: int, height: int) -> np.ndarray:
    if pixels.ndim != 3:
        raise ValueError("pixels must be an HxWxC array")
    src_h, src_w = pixels.shape[:2]
    if src_w == width and src_h == height:
        return pixels
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    key = (src_w, src_h, width, height)
    indices = _RESIZE_INDEX_CACHE.get(key)
    if indices is None:
        ys = np.linspace(0, src_h - 1, height).round().astype(np.int64)
        xs = np.linspace(0, src_w - 1, width).round().astype(np.int64)
        indices = (ys, xs)
        _RESIZE_INDEX_CACHE[key] = indices
    ys, xs = indices
    return pixels[ys][:, xs]


def rgb_to_ansi256(r: int, g: int, b: int) -> int:
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return 232 + round(((r - 8) / 247) * 24)
    return 16 + 36 * round(r / 255 * 5) + 6 * round(g / 255 * 5) + round(b / 255 * 5)


def fg(rgb: Iterable[int], mode: ColorMode) -> str:
    r, g, b = (int(x) for x in rgb)
    if mode == ColorMode.mono:
        return "\x1b[37m" if (r + g + b) / 3 > 127 else "\x1b[30m"
    if mode == ColorMode.ansi256:
        return f"\x1b[38;5;{rgb_to_ansi256(r, g, b)}m"
    return f"\x1b[38;2;{r};{g};{b}m"


def bg(rgb: Iterable[int], mode: ColorMode) -> str:
    r, g, b = (int(x) for x in rgb)
    if mode == ColorMode.mono:
        return "\x1b[47m" if (r + g + b) / 3 > 127 else "\x1b[40m"
    if mode == ColorMode.ansi256:
        return f"\x1b[48;5;{rgb_to_ansi256(r, g, b)}m"
    return f"\x1b[48;2;{r};{g};{b}m"


def pixels_to_half_blocks(pixels: np.ndarray, mode: ColorMode = ColorMode.truecolor) -> str:
    from .terminal_output import pixels_to_half_blocks_bytes

    return pixels_to_half_blocks_bytes(pixels, mode).data.decode("utf-8", errors="replace")


def pixels_to_drawille(
    pixels: np.ndarray,
    mode: ColorMode = ColorMode.truecolor,
    threshold: float = 32.0,
) -> str:
    from .terminal_output import pixels_to_drawille_bytes

    return pixels_to_drawille_bytes(pixels, mode, threshold).data.decode("utf-8", errors="replace")


def pixels_to_terminal(
    pixels: np.ndarray,
    color: ColorMode = ColorMode.truecolor,
    style: RenderStyle = RenderStyle.half,
    drawille_threshold: float = 32.0,
) -> str:
    if style == RenderStyle.drawille:
        return pixels_to_drawille(pixels, color, drawille_threshold)
    return pixels_to_half_blocks(pixels, color)


def clear_screen() -> str:
    return "\x1b[?25l\x1b[H"


def show_cursor() -> str:
    return "\x1b[?25h" + RESET
