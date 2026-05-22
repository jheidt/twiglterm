import unittest

import numpy as np

from twiglterm.ansi import RenderStyle
from twiglterm.compare import compare_rgb, parse_time_scan, terminal_preview_pixels


class CompareTests(unittest.TestCase):
    def test_identical_images_score_high(self):
        pixels = np.full((4, 4, 3), 120, dtype=np.uint8)
        result = compare_rgb(pixels, pixels.copy())
        self.assertEqual(result.mae, 0.0)
        self.assertGreater(result.score, 0.3)

    def test_parse_time_scan(self):
        self.assertEqual(parse_time_scan("0:1:.5"), [0.0, 0.5, 1.0])

    def test_terminal_preview_shape(self):
        pixels = np.full((8, 4, 4), 255, dtype=np.uint8)
        preview = terminal_preview_pixels(pixels, RenderStyle.drawille)
        self.assertEqual(preview.shape, (8, 4, 3))


if __name__ == "__main__":
    unittest.main()

