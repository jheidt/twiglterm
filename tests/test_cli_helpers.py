import unittest

from twiglterm.ansi import RenderStyle
from twiglterm.terminal import frame_delay, render_size, terminal_pixel_size
from twiglterm.text import text_cells


class CliHelperTests(unittest.TestCase):
    def test_render_size_half(self):
        self.assertEqual(render_size(10, 5, RenderStyle.half), (10, 10))

    def test_render_size_drawille(self):
        self.assertEqual(render_size(10, 5, RenderStyle.drawille), (20, 20))

    def test_render_size_explicit_backend(self):
        self.assertEqual(render_size(10, 5, RenderStyle.drawille, 64, 32), (64, 32))

    def test_terminal_pixel_size(self):
        self.assertEqual(terminal_pixel_size(10, 5, RenderStyle.half), (10, 10))

    def test_unbounded_fps_delay(self):
        self.assertIsNone(frame_delay(0))
        self.assertIsNone(frame_delay(-1))

    def test_text_cells_wrap(self):
        cells = text_cells("abcd", 2, 2)
        self.assertEqual(cells[0][0].data, "a")
        self.assertEqual(cells[0][1].data, "b")
        self.assertEqual(cells[1][0].data, "c")
        self.assertEqual(cells[1][1].data, "d")


if __name__ == "__main__":
    unittest.main()
