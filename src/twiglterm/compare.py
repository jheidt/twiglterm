from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from .ansi import RenderStyle, resize_pixels_nearest


@dataclass(frozen=True)
class ComparisonResult:
    mse: float
    mae: float
    psnr: float
    luminance_correlation: float
    bright_overlap: float

    @property
    def score(self) -> float:
        corr = max(0.0, self.luminance_correlation)
        return (corr * 0.65) + (self.bright_overlap * 0.35)


def load_reference(path: Path, width: int, height: int) -> np.ndarray:
    image = Image.open(path).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.uint8)


def compare_rgb(rendered: np.ndarray, reference: np.ndarray) -> ComparisonResult:
    rgb = _rgb(rendered)
    ref = _rgb(reference)
    if rgb.shape != ref.shape:
        ref = resize_pixels_nearest(ref, rgb.shape[1], rgb.shape[0])

    diff = rgb.astype(np.float32) - ref.astype(np.float32)
    mse = float(np.mean(diff * diff))
    mae = float(np.mean(np.abs(diff)))
    psnr = 99.0 if mse == 0.0 else float(20.0 * np.log10(255.0 / np.sqrt(mse)))
    lum = _luma(rgb)
    ref_lum = _luma(ref)
    corr = _corr(lum, ref_lum)
    overlap = _bright_overlap(lum, ref_lum)
    return ComparisonResult(mse=mse, mae=mae, psnr=psnr, luminance_correlation=corr, bright_overlap=overlap)


def terminal_preview_pixels(pixels: np.ndarray, style: RenderStyle) -> np.ndarray:
    rgb = _rgb(pixels)
    h, w = rgb.shape[:2]
    if style == RenderStyle.drawille:
        return _drawille_preview(rgb)
    if h % 2:
        pad = np.zeros((1, w, 3), dtype=rgb.dtype)
        rgb = np.vstack([rgb, pad])
        h += 1
    rows = []
    for y in range(0, h, 2):
        top = rgb[y : y + 1]
        bottom = rgb[y + 1 : y + 2]
        rows.append(np.vstack([top, bottom]))
    return np.vstack(rows)


def parse_time_scan(value: str) -> list[float]:
    parts = [float(part) for part in value.split(":")]
    if len(parts) != 3:
        raise ValueError("time scan must be START:END:STEP")
    start, end, step = parts
    if step <= 0:
        raise ValueError("time scan step must be positive")
    times: list[float] = []
    current = start
    while current <= end + 1e-9:
        times.append(current)
        current += step
    return times


def _rgb(pixels: np.ndarray) -> np.ndarray:
    if pixels.ndim != 3 or pixels.shape[2] < 3:
        raise ValueError("pixels must be HxWxRGB/RGBA")
    return pixels[:, :, :3]


def _luma(rgb: np.ndarray) -> np.ndarray:
    data = rgb.astype(np.float32)
    return data[:, :, 0] * 0.2126 + data[:, :, 1] * 0.7152 + data[:, :, 2] * 0.0722


def _corr(left: np.ndarray, right: np.ndarray) -> float:
    a = left.reshape(-1).astype(np.float32)
    b = right.reshape(-1).astype(np.float32)
    a -= float(np.mean(a))
    b -= float(np.mean(b))
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _bright_overlap(left: np.ndarray, right: np.ndarray) -> float:
    left_mask = left >= np.percentile(left, 90)
    right_mask = right >= np.percentile(right, 90)
    union = np.logical_or(left_mask, right_mask)
    if not np.any(union):
        return 1.0
    return float(np.logical_and(left_mask, right_mask).sum() / union.sum())


def _drawille_preview(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    out = np.zeros_like(rgb)
    for y in range(0, h, 4):
        for x in range(0, w, 2):
            cell = rgb[y : y + 4, x : x + 2]
            if cell.size == 0:
                continue
            luma = _luma(cell)
            mask = luma >= 32.0
            if np.any(mask):
                color = np.mean(cell[mask], axis=0)
            else:
                color = np.mean(cell.reshape(-1, 3), axis=0)
            out[y : y + 4, x : x + 2] = color
    return out.astype(np.uint8)

