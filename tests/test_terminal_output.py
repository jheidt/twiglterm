import re
import unittest

import numpy as np

from twiglterm.ansi import ColorMode, RenderStyle, resize_pixels_nearest
from twiglterm.terminal_output import (
    FrameBytes,
    diff_redraw,
    encoded_redraw,
    pixels_to_half_blocks_bytes,
    pixels_to_terminal_bytes,
)


ANSI_RE = re.compile(rb"\x1b\[[0-9;?]*[A-Za-z]")


class TerminalOutputTests(unittest.TestCase):
    def test_drawille_bit_mapping(self):
        pixels = np.zeros((4, 2, 4), dtype=np.uint8)
        pixels[0, 0, :3] = 255
        pixels[3, 1, :3] = 255
        frame = pixels_to_terminal_bytes(pixels, ColorMode.truecolor, RenderStyle.drawille)
        self.assertIn("⢁".encode(), frame.data)

    def test_half_block_cell_text_matches_fixture(self):
        pixels = np.zeros((2, 2, 4), dtype=np.uint8)
        frame = pixels_to_half_blocks_bytes(pixels, ColorMode.mono)
        visible = ANSI_RE.sub(b"", frame.data).decode()
        self.assertEqual(visible, "▀▀")

    def test_ansi_state_compression_keeps_reset(self):
        pixels = np.zeros((2, 4, 4), dtype=np.uint8)
        frame = pixels_to_half_blocks_bytes(pixels, ColorMode.ansi256)
        self.assertLessEqual(frame.data.count(b"\x1b["), 2)
        self.assertTrue(frame.data.endswith(b"\x1b[0m"))

    def test_diff_redraw_only_changed_lines(self):
        previous = FrameBytes(b"one\ntwo", [b"one", b"two"])
        current = FrameBytes(b"one\nTWO", [b"one", b"TWO"])
        out = diff_redraw(previous, current)
        self.assertIn(b"\x1b[2;1H", out)
        self.assertNotIn(b"\x1b[1;1H", out)
        self.assertIn(b"TWO", out)

    def test_full_redraw_emits_all_lines(self):
        frame = FrameBytes(b"one\ntwo", [b"one", b"two"])
        self.assertEqual(encoded_redraw(None, frame, "full"), b"\x1b[Hone\ntwo")

    def test_resize_cache_preserves_selection(self):
        pixels = np.arange(3 * 3 * 4, dtype=np.uint8).reshape(3, 3, 4)
        first = resize_pixels_nearest(pixels, 2, 2)
        second = resize_pixels_nearest(pixels, 2, 2)
        np.testing.assert_array_equal(first, second)
        self.assertEqual(first.shape, (2, 2, 4))


if __name__ == "__main__":
    unittest.main()
