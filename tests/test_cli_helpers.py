import unittest

from twiglterm.ansi import RenderStyle
from twiglterm.cli import _frame_delay, _render_size, _terminal_pixel_size, _text_cells


class CliHelperTests(unittest.TestCase):
    def test_render_size_half(self):
        self.assertEqual(_render_size(10, 5, RenderStyle.half), (10, 10))

    def test_render_size_drawille(self):
        self.assertEqual(_render_size(10, 5, RenderStyle.drawille), (20, 20))

    def test_render_size_explicit_backend(self):
        self.assertEqual(_render_size(10, 5, RenderStyle.drawille, 64, 32), (64, 32))

    def test_terminal_pixel_size(self):
        self.assertEqual(_terminal_pixel_size(10, 5, RenderStyle.half), (10, 10))

    def test_unbounded_fps_delay(self):
        self.assertIsNone(_frame_delay(0))
        self.assertIsNone(_frame_delay(-1))

    def test_text_cells_wrap(self):
        cells = _text_cells("abcd", 2, 2)
        self.assertEqual(cells[0][0].data, "a")
        self.assertEqual(cells[0][1].data, "b")
        self.assertEqual(cells[1][0].data, "c")
        self.assertEqual(cells[1][1].data, "d")


if __name__ == "__main__":
    unittest.main()
