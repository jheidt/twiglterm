from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .shader import PreparedShader, prepare_fragment, uniform_aliases


class RendererError(RuntimeError):
    pass


@dataclass(frozen=True)
class RenderState:
    time: float = 0.0
    frame: int = 0
    mouse: tuple[float, float] = (0.0, 0.0)


class ShaderRenderer:
    def __init__(self, source: str, width: int, height: int, mode: str = "auto") -> None:
        self.width = width
        self.height = height
        self.prepared = prepare_fragment(source, mode)  # type: ignore[arg-type]
        self._ctx = None
        self._program = None
        self._vao = None
        self._fbo = None
        self._color = None
        self._back = None
        self._init_gl()

    @property
    def prepared_shader(self) -> PreparedShader:
        return self.prepared

    def _init_gl(self) -> None:
        try:
            import moderngl
        except Exception as exc:  # pragma: no cover
            raise RendererError("ModernGL is not installed") from exc

        try:
            self._ctx = moderngl.create_standalone_context()
            self._program = self._ctx.program(
                vertex_shader=self.prepared.vertex_shader,
                fragment_shader=self.prepared.fragment_shader,
            )
            vertices = np.array([-1.0, -1.0, 3.0, -1.0, -1.0, 3.0], dtype="f4")
            vbo = self._ctx.buffer(vertices.tobytes())
            self._vao = self._ctx.simple_vertex_array(self._program, vbo, "in_pos")
            self._color = self._ctx.texture((self.width, self.height), 4)
            self._back = self._ctx.texture((self.width, self.height), 4)
            self._fbo = self._ctx.framebuffer(color_attachments=[self._color])
        except Exception as exc:  # pragma: no cover
            detail = str(exc)
            if isinstance(exc, NameError) and "mgl" in detail:
                detail = "ModernGL native extension is unavailable; reinstall moderngl/glcontext"
            raise RendererError(f"Could not create GL renderer: {detail}") from exc

    def resize(self, width: int, height: int) -> None:
        if width == self.width and height == self.height:
            return
        self.width = width
        self.height = height
        assert self._ctx is not None
        self._color = self._ctx.texture((width, height), 4)
        self._back = self._ctx.texture((width, height), 4)
        self._fbo = self._ctx.framebuffer(color_attachments=[self._color])

    def render(self, state: RenderState) -> np.ndarray:
        assert self._ctx is not None
        assert self._program is not None
        assert self._vao is not None
        assert self._fbo is not None
        assert self._color is not None
        assert self._back is not None

        aliases = uniform_aliases(self.prepared.mode)
        self._set_uniform(aliases["resolution"], (float(self.width), float(self.height)))
        self._set_uniform(aliases["mouse"], state.mouse)
        self._set_uniform(aliases["time"], float(state.time))
        self._set_uniform(aliases["frame"], int(state.frame))
        if aliases["backbuffer"] in self._program:
            self._back.use(0)
            self._program[aliases["backbuffer"]].value = 0

        self._fbo.use()
        self._ctx.viewport = (0, 0, self.width, self.height)
        self._vao.render()
        raw = self._fbo.read(components=4, alignment=1)
        pixels = np.frombuffer(raw, dtype=np.uint8).reshape((self.height, self.width, 4))
        pixels = np.flipud(pixels).copy()
        self._back.write(np.flipud(pixels).tobytes())
        return pixels

    def _set_uniform(self, name: str, value: object) -> None:
        assert self._program is not None
        if name not in self._program:
            return
        self._program[name].value = value
