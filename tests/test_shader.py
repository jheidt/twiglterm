import unittest

from twiglterm.shader import prepare_fragment, resolve_mode, uniform_aliases


class ShaderTests(unittest.TestCase):
    def test_classic_mode_detection(self):
        src = "precision highp float; uniform float time; void main(){gl_FragColor=vec4(time);}"
        self.assertEqual(resolve_mode(src, "auto"), "classic")

    def test_geek_mode_detection(self):
        src = "uniform float t; void main(){gl_FragColor=vec4(t);}"
        self.assertEqual(resolve_mode(src, "auto"), "geek")

    def test_fragment_wraps_webgl_output(self):
        prepared = prepare_fragment("precision highp float;\nvoid main(){gl_FragColor=vec4(1.);}")
        self.assertIn("#version 330", prepared.fragment_shader)
        self.assertNotIn("precision highp float", prepared.fragment_shader)
        self.assertIn("_twigl_out=vec4", prepared.fragment_shader)

    def test_geek_aliases(self):
        aliases = uniform_aliases("geek")
        self.assertEqual(aliases["resolution"], "r")
        self.assertEqual(aliases["backbuffer"], "b")


if __name__ == "__main__":
    unittest.main()

