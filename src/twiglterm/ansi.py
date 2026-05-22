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


def dim_pixels(pixels: np.ndarray, opacity: float) -> np.ndarray:
    opacity = max(0.0, min(1.0, opacity))
    return np.clip(pixels.astype(np.float32) * opacity, 0, 255).astype(np.uint8)


def scale_pixels(pixels: np.ndarray, level: float) -> np.ndarray:
    level = max(0.0, level)
    return np.clip(pixels.astype(np.float32) * level, 0, 255).astype(np.uint8)


def resize_pixels_nearest(pixels: np.ndarray, width: int, height: int) -> np.ndarray:
    if pixels.ndim != 3:
        raise ValueError("pixels must be an HxWxC array")
    src_h, src_w = pixels.shape[:2]
    if src_w == width and src_h == height:
        return pixels
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    ys = np.linspace(0, src_h - 1, height).round().astype(np.int64)
    xs = np.linspace(0, src_w - 1, width).round().astype(np.int64)
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
    if pixels.ndim != 3 or pixels.shape[2] < 3:
        raise ValueError("pixels must be an HxWxRGB/RGBA array")

    h, w = pixels.shape[:2]
    lines: list[str] = []
    for y in range(0, h, 2):
        parts: list[str] = []
        top = pixels[y, :, :3]
        bottom = pixels[y + 1, :, :3] if y + 1 < h else np.zeros_like(top)
        for x in range(w):
            parts.append(fg(top[x], mode))
            parts.append(bg(bottom[x], mode))
            parts.append("▀")
        parts.append(RESET)
        lines.append("".join(parts))
    return "\n".join(lines)


def pixels_to_drawille(
    pixels: np.ndarray,
    mode: ColorMode = ColorMode.truecolor,
    threshold: float = 32.0,
) -> str:
    if pixels.ndim != 3 or pixels.shape[2] < 3:
        raise ValueError("pixels must be an HxWxRGB/RGBA array")

    h, w = pixels.shape[:2]
    lines: list[str] = []
    for y in range(0, h, 4):
        parts: list[str] = []
        for x in range(0, w, 2):
            cell = pixels[y : y + 4, x : x + 2, :3]
            bits = 0
            lit: list[np.ndarray] = []
            for cy in range(cell.shape[0]):
                for cx in range(cell.shape[1]):
                    rgb = cell[cy, cx]
                    luma = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
                    if luma >= threshold:
                        bits |= BRAILLE_BITS[cy][cx]
                        lit.append(rgb)
            char = chr(0x2800 + bits) if bits else " "
            if mode == ColorMode.mono:
                rgb = np.array((255, 255, 255) if bits else (0, 0, 0))
            else:
                rgb = np.mean(lit if lit else cell.reshape(-1, 3), axis=0)
            parts.append(fg(rgb, mode))
            parts.append(char)
        parts.append(RESET)
        lines.append("".join(parts))
    return "\n".join(lines)


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
