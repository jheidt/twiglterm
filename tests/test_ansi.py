import unittest

import numpy as np

from twiglterm.ansi import (
    ColorMode,
    RenderStyle,
    dim_pixels,
    pixels_to_drawille,
    pixels_to_half_blocks,
    pixels_to_terminal,
    resize_pixels_nearest,
    rgb_to_ansi256,
    scale_pixels,
)


class AnsiTests(unittest.TestCase):
    def test_dim_pixels(self):
        pixels = np.array([[[100, 50, 25, 255]]], dtype=np.uint8)
        self.assertEqual(dim_pixels(pixels, 0.5)[0, 0, 0], 50)

    def test_half_blocks_line_count(self):
        pixels = np.zeros((4, 3, 4), dtype=np.uint8)
        text = pixels_to_half_blocks(pixels, ColorMode.truecolor)
        self.assertEqual(len(text.splitlines()), 2)

    def test_ansi256_range(self):
        self.assertGreaterEqual(rgb_to_ansi256(255, 0, 0), 16)
        self.assertLessEqual(rgb_to_ansi256(255, 0, 0), 231)

    def test_drawille_line_count(self):
        pixels = np.full((8, 4, 4), 255, dtype=np.uint8)
        text = pixels_to_drawille(pixels, ColorMode.truecolor)
        self.assertEqual(len(text.splitlines()), 2)
        self.assertIn("⣿", text)

    def test_terminal_style_switch(self):
        pixels = np.full((4, 2, 4), 255, dtype=np.uint8)
        text = pixels_to_terminal(pixels, ColorMode.truecolor, RenderStyle.drawille)
        self.assertIn("⣿", text)

    def test_scale_pixels_clips(self):
        pixels = np.array([[[200, 10, 0, 255]]], dtype=np.uint8)
        self.assertEqual(scale_pixels(pixels, 2.0)[0, 0, 0], 255)

    def test_resize_pixels_nearest(self):
        pixels = np.zeros((2, 2, 4), dtype=np.uint8)
        resized = resize_pixels_nearest(pixels, 4, 4)
        self.assertEqual(resized.shape, (4, 4, 4))


if __name__ == "__main__":
    unittest.main()
