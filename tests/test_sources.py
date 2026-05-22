import unittest
from urllib.parse import quote_plus

from twiglterm.sources import (
    ShaderSourceError,
    adapt_fragcoord_source,
    adapt_shadertoy_source,
    fetch_shader_source,
)


class SourceTests(unittest.TestCase):
    def test_twigl_query_source(self):
        code = "precision highp float; uniform float time; void main(){gl_FragColor=vec4(time);}"
        source = fetch_shader_source("https://twigl.app/?mode=0&source=" + quote_plus(code))
        self.assertEqual(source.source, code)
        self.assertIn("twigl", source.label)

    def test_shadertoy_query_source_adapts_main_image(self):
        code = "void mainImage(out vec4 c, in vec2 p){c=vec4(iTime+iResolution.x+p.x);}"
        source = fetch_shader_source("https://www.shadertoy.com/view/test?source=" + quote_plus(code))
        self.assertIn("void main(){mainImage", source.source)
        self.assertIn("time", source.source)
        self.assertIn("resolution", source.source)

    def test_shadertoy_id_without_source_errors(self):
        with self.assertRaises(ShaderSourceError):
            fetch_shader_source("https://www.shadertoy.com/view/MdX3Rr")

    def test_fragcoord_adaptation(self):
        adapted = adapt_fragcoord_source(
            "uniform vec2 u_resolution;\nuniform float u_time;\nvoid main(){fragColor=vec4(u_time+u_resolution.x);}"
        )
        self.assertIn("uniform vec2 resolution", adapted)
        self.assertIn("uniform float time", adapted)
        self.assertIn("gl_FragColor", adapted)


if __name__ == "__main__":
    unittest.main()

