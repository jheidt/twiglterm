from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal

ShaderMode = Literal["auto", "classic", "geek"]
ResolvedMode = Literal["classic", "geek"]

CLASSIC_UNIFORMS = ("resolution", "mouse", "time", "frame", "backbuffer")
GEEK_UNIFORMS = ("r", "m", "t", "f", "b")

UNIFORM_RE = re.compile(r"\buniform\s+\w+\s+(\w+)\s*(?:\[[^\]]+\])?\s*;")
PRECISION_RE = re.compile(r"^\s*precision\s+\w+\s+\w+\s*;\s*$", re.MULTILINE)
VERSION_RE = re.compile(r"^\s*#version\b.*$", re.MULTILINE)
GL_FRAG_COLOR_RE = re.compile(r"\bgl_FragColor\b")

VERTEX_SHADER = """#version 330
in vec2 in_pos;
void main() {
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""


@dataclass(frozen=True)
class PreparedShader:
    source: str
    fragment_shader: str
    vertex_shader: str
    mode: ResolvedMode
    declared_uniforms: tuple[str, ...]


def declared_uniforms(source: str) -> tuple[str, ...]:
    return tuple(UNIFORM_RE.findall(source))


def resolve_mode(source: str, mode: ShaderMode) -> ResolvedMode:
    if mode in ("classic", "geek"):
        return mode
    names = set(declared_uniforms(source))
    if names.intersection(GEEK_UNIFORMS):
        return "geek"
    return "classic"


def prepare_fragment(source: str, mode: ShaderMode = "auto") -> PreparedShader:
    resolved = resolve_mode(source, mode)
    body = VERSION_RE.sub("", source)
    body = PRECISION_RE.sub("", body)
    body = GL_FRAG_COLOR_RE.sub("_twigl_out", body)
    fragment = "#version 330\nout vec4 _twigl_out;\n" + body.strip() + "\n"
    return PreparedShader(
        source=source,
        fragment_shader=fragment,
        vertex_shader=VERTEX_SHADER,
        mode=resolved,
        declared_uniforms=declared_uniforms(source),
    )


def uniform_aliases(mode: ResolvedMode) -> dict[str, str]:
    if mode == "geek":
        return {
            "resolution": "r",
            "mouse": "m",
            "time": "t",
            "frame": "f",
            "backbuffer": "b",
        }
    return {name: name for name in CLASSIC_UNIFORMS}

