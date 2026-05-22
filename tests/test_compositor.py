import unittest

import numpy as np

from twiglterm.ansi import ColorMode
from twiglterm.compositor import Cell, composite


class CompositorTests(unittest.TestCase):
    def test_composite_includes_text(self):
        pixels = np.zeros((2, 2, 4), dtype=np.uint8)
        out = composite(pixels, [[Cell("A"), Cell("B")]], ColorMode.truecolor)
        self.assertIn("A", out)
        self.assertIn("B", out)


if __name__ == "__main__":
    unittest.main()

