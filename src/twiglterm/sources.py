from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote_plus, urlparse
from urllib.request import Request, urlopen


class ShaderSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class ShaderSource:
    source: str
    label: str


FRAGCOORD_URL = "https://ixyhaetjrmcgekzydqit.supabase.co/rest/v1/shaders"
FRAGCOORD_KEY = "sb_publishable_VTjbNt5YVkFRu7HGxzR0fA_6ZmWiLLD"


def read_shader_source(value: str | Path) -> ShaderSource:
    text = str(value)
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"}:
        return fetch_shader_source(text)
    path = Path(text)
    return ShaderSource(path.read_text(encoding="utf-8"), str(path))


def fetch_shader_source(url: str) -> ShaderSource:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith("fragcoord.xyz"):
        return _fetch_fragcoord(url, parsed)
    if host.endswith("twigl.app"):
        return _fetch_query_source(url, parsed, "twigl")
    if host.endswith("shadertoy.com") or host.endswith("www.shadertoy.com"):
        return _fetch_shadertoy(url, parsed)
    return _fetch_query_source(url, parsed, host or url)


def _fetch_fragcoord(url: str, parsed) -> ShaderSource:
    slug = _last_path_part(parsed.path)
    if not slug:
        raise ShaderSourceError(f"FragCoord URL does not include a shader slug: {url}")
    api_url = f"{FRAGCOORD_URL}?select=*,shader_passes(*)&slug=eq.{slug}"
    request = Request(api_url, headers={"apikey": FRAGCOORD_KEY, "Authorization": f"Bearer {FRAGCOORD_KEY}"})
    with urlopen(request, timeout=30) as response:
        records = json.loads(response.read().decode("utf-8"))
    if not records:
        raise ShaderSourceError(f"FragCoord shader not found: {slug}")
    shader = records[0]
    passes = sorted(shader.get("shader_passes") or [], key=lambda item: item.get("sort_order") or 0)
    glsl_passes = [item for item in passes if (item.get("language") or "glsl").lower() == "glsl"]
    if not glsl_passes:
        raise ShaderSourceError(f"FragCoord shader {slug} has no GLSL passes")
    source = "\n\n".join(item.get("code") or "" for item in glsl_passes)
    source = adapt_fragcoord_source(source)
    title = shader.get("title") or slug
    return ShaderSource(source, f"fragcoord:{slug}:{title}")


def _fetch_shadertoy(url: str, parsed) -> ShaderSource:
    query_source = _query_source(parsed)
    if query_source:
        return ShaderSource(adapt_shadertoy_source(query_source), "shadertoy:query")
    shader_id = _last_path_part(parsed.path)
    raise ShaderSourceError(
        "Shadertoy shader IDs require the Shadertoy API, which needs an API key. "
        f"Unsupported URL for direct fetch: {shader_id or url}"
    )


def _fetch_query_source(url: str, parsed, label: str) -> ShaderSource:
    source = _query_source(parsed)
    if not source:
        raise ShaderSourceError(f"No shader source query parameter found in URL: {url}")
    if label == "twigl":
        source = adapt_twigl_source(source)
    return ShaderSource(source, f"{label}:query")


def _query_source(parsed) -> str | None:
    query = parse_qs(parsed.query)
    for key in ("source", "code", "shader", "fragment", "frag"):
        values = query.get(key)
        if values:
            return unquote_plus(values[0])
    return None


def _last_path_part(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    return parts[-1] if parts else ""


def adapt_twigl_source(source: str) -> str:
    return source


def adapt_shadertoy_source(source: str) -> str:
    out = source
    out = re.sub(r"\biResolution\b", "vec3(resolution, 1.0)", out)
    out = re.sub(r"\biTime\b", "time", out)
    if "mainImage" in out and "void main()" not in out:
        out += "\nvoid main(){mainImage(gl_FragColor, gl_FragCoord.xy);}\n"
    return out


def adapt_fragcoord_source(source: str) -> str:
    out = source
    out = re.sub(r"^\s*uniform\s+vec2\s+u_resolution\s*;.*$", "uniform vec2 resolution;", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*uniform\s+float\s+u_time\s*;.*$", "uniform float time;", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*uniform\s+sampler2D\s+u_main\s*;.*$", "", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*uniform\s+float\s+u_b\s*;.*$", "const float u_b = 0.15;", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*uniform\s+float\s+u_zoom\s*;.*$", "const float u_zoom = 1.0;", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*uniform\s+float\s+u_width\s*;.*$", "const float u_width = 0.005;", out, flags=re.MULTILINE)
    out = re.sub(r"\bu_resolution\b", "resolution", out)
    out = re.sub(r"\bu_time\b", "time", out)
    out = re.sub(r"\bfragColor\b", "gl_FragColor", out)
    return out

