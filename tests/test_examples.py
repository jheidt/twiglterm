import unittest
from pathlib import Path

from twiglterm.renderer import RenderState, ShaderRenderer
from twiglterm.shader import prepare_fragment

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class ExampleShaderTests(unittest.TestCase):
    def test_all_frag_examples_prepare(self):
        for path in sorted(EXAMPLES.glob("*.frag")):
            with self.subTest(path=path.name):
                prepared = prepare_fragment(path.read_text(encoding="utf-8"))
                self.assertIn("void main", prepared.fragment_shader)

    def test_all_frag_examples_render_small_frame(self):
        for path in sorted(EXAMPLES.glob("*.frag")):
            with self.subTest(path=path.name):
                renderer = ShaderRenderer(path.read_text(encoding="utf-8"), 16, 8)
                pixels = renderer.render(RenderState(time=1.0))
                self.assertEqual(pixels.shape, (8, 16, 4))


if __name__ == "__main__":
    unittest.main()

