from __future__ import annotations

from dataclasses import dataclass
import os
import time

import numpy as np

from .ansi import RenderStyle, resize_pixels_nearest, scale_pixels
from .renderer import RenderState, ShaderRenderer


@dataclass(frozen=True)
class RenderGeometry:
    cols: int
    rows: int
    target_width: int
    target_height: int
    render_width: int
    render_height: int


def terminal_grid_size(width: int | None, height: int | None) -> tuple[int, int]:
    try:
        size = os.get_terminal_size()
    except OSError:
        size = os.terminal_size((80, 24))
    return max(1, width or size.columns), max(1, height or size.lines)


def terminal_pixel_size(cols: int, rows: int, style: RenderStyle) -> tuple[int, int]:
    if style == RenderStyle.drawille:
        return cols * 2, rows * 4
    return cols, rows * 2


def render_size(
    terminal_width: int | None,
    terminal_height: int | None,
    style: RenderStyle,
    render_width: int | None = None,
    render_height: int | None = None,
) -> tuple[int, int]:
    cols, rows = terminal_grid_size(terminal_width, terminal_height)
    target_w, target_h = terminal_pixel_size(cols, rows, style)
    return render_width or target_w, render_height or target_h


def geometry(
    terminal_width: int | None,
    terminal_height: int | None,
    style: RenderStyle,
    render_width: int | None = None,
    render_height: int | None = None,
) -> RenderGeometry:
    cols, rows = terminal_grid_size(terminal_width, terminal_height)
    target_w, target_h = terminal_pixel_size(cols, rows, style)
    render_w = render_width or target_w
    render_h = render_height or target_h
    return RenderGeometry(cols, rows, target_w, target_h, render_w, render_h)


def frame_delay(fps: float) -> float | None:
    if fps <= 0:
        return None
    return 1.0 / fps


def sleep_frame(delay: float | None) -> None:
    if delay is not None:
        time.sleep(delay)


def shader_frame(
    renderer: ShaderRenderer,
    state: RenderState,
    target_width: int,
    target_height: int,
    playback_level: float,
) -> np.ndarray:
    pixels = renderer.render(state)
    pixels = resize_pixels_nearest(pixels, target_width, target_height)
    return scale_pixels(pixels, playback_level)

