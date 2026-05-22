from __future__ import annotations

import sys
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .ansi import (
    ColorMode,
    RenderStyle,
    clear_screen,
    pixels_to_terminal,
    resize_pixels_nearest,
    show_cursor,
)
from .compositor import TerminalModel, composite
from .compare import compare_rgb, load_reference, parse_time_scan, terminal_preview_pixels
from .pty_backend import shell_command, spawn
from .renderer import RenderState, ShaderRenderer
from .renderer import RendererError
from .shader import prepare_fragment
from .shell_loop import run_shell_loop as _run_shell_loop
from .terminal import (
    frame_delay as _frame_delay,
    geometry as _geometry,
    shader_frame as _shader_frame,
    sleep_frame as _sleep_frame,
    terminal_grid_size as _terminal_grid_size,
)
from .text import blank_cells as _blank_cells
from .text import text_cells as _text_cells

app = typer.Typer(no_args_is_help=True)
console = Console()


class Mode(str, Enum):
    auto = "auto"
    classic = "classic"
    geek = "geek"


class LayerMode(str, Enum):
    foreground = "foreground"
    background = "background"


def main() -> None:
    _configure_stdio()
    app()


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _read_shader(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_mouse(value: str) -> tuple[float, float]:
    try:
        left, right = value.split(",", 1)
        return (float(left), float(right))
    except ValueError as exc:
        raise typer.BadParameter("mouse must be X,Y") from exc


def _renderer(source: str, width: int, height: int, mode: str) -> ShaderRenderer:
    try:
        return ShaderRenderer(source, width, height, mode)
    except RendererError as exc:
        console.print(f"[red]renderer error:[/red] {exc}")
        raise typer.Exit(1) from exc


@app.command()
def info(
    shader: Path,
    mode: Mode = typer.Option(Mode.auto),
) -> None:
    source = _read_shader(shader)
    prepared = prepare_fragment(source, mode.value)
    console.print(f"mode: {prepared.mode}")
    console.print("uniforms: " + (", ".join(prepared.declared_uniforms) or "(none)"))
    try:
        renderer = _renderer(source, 2, 2, mode.value)
        renderer.render(RenderState())
        console.print("compile: ok")
    except Exception as exc:
        if isinstance(exc, typer.Exit):
            raise
        console.print(f"compile: failed: {exc}")
        raise typer.Exit(1) from exc


@app.command()
def frame(
    shader: Path,
    mode: Mode = typer.Option(Mode.auto),
    terminal_width: Optional[int] = typer.Option(None, "--terminal-width", "--width"),
    terminal_height: Optional[int] = typer.Option(None, "--terminal-height", "--height"),
    render_width: Optional[int] = None,
    render_height: Optional[int] = None,
    time_value: float = typer.Option(0.0, "--time"),
    frame_value: int = typer.Option(0, "--frame"),
    playback_rate: float = typer.Option(1.0),
    playback_level: float = typer.Option(1.0),
    mouse: str = "0,0",
    color: ColorMode = ColorMode.truecolor,
    style: RenderStyle = RenderStyle.half,
    layer: LayerMode = LayerMode.foreground,
    background_opacity: float = typer.Option(0.35),
    drawille_threshold: float = typer.Option(32.0),
) -> None:
    geo = _geometry(terminal_width, terminal_height, style, render_width, render_height)
    renderer = _renderer(_read_shader(shader), geo.render_width, geo.render_height, mode.value)
    pixels = _shader_frame(
        renderer,
        RenderState(time_value * playback_rate, frame_value, _parse_mouse(mouse)),
        geo.target_width,
        geo.target_height,
        playback_level,
    )
    if layer == LayerMode.background:
        bg_pixels = resize_pixels_nearest(pixels, geo.cols, geo.rows * 2)
        sys.stdout.write(composite(bg_pixels, _blank_cells(geo.cols, geo.rows), color, background_opacity) + "\n")
    else:
        sys.stdout.write(pixels_to_terminal(pixels, color, style, drawille_threshold) + "\n")


@app.command()
def play(
    shader: Path,
    mode: Mode = typer.Option(Mode.auto),
    terminal_width: Optional[int] = typer.Option(None, "--terminal-width", "--width"),
    terminal_height: Optional[int] = typer.Option(None, "--terminal-height", "--height"),
    render_width: Optional[int] = None,
    render_height: Optional[int] = None,
    fps: float = 30.0,
    duration: Optional[float] = None,
    playback_rate: float = typer.Option(1.0),
    playback_level: float = typer.Option(1.0),
    mouse: str = "0,0",
    color: ColorMode = ColorMode.truecolor,
    style: RenderStyle = RenderStyle.half,
    layer: LayerMode = LayerMode.foreground,
    background_opacity: float = typer.Option(0.35),
    drawille_threshold: float = typer.Option(32.0),
) -> None:
    geo = _geometry(terminal_width, terminal_height, style, render_width, render_height)
    renderer = _renderer(_read_shader(shader), geo.render_width, geo.render_height, mode.value)
    start = time.monotonic()
    frame_no = 0
    delay = _frame_delay(fps)
    sys.stdout.write(clear_screen())
    try:
        while duration is None or time.monotonic() - start < duration:
            now = time.monotonic() - start
            pixels = _shader_frame(
                renderer,
                RenderState(now * playback_rate, frame_no, _parse_mouse(mouse)),
                geo.target_width,
                geo.target_height,
                playback_level,
            )
            if layer == LayerMode.background:
                bg_pixels = resize_pixels_nearest(pixels, geo.cols, geo.rows * 2)
                output = composite(bg_pixels, _blank_cells(geo.cols, geo.rows), color, background_opacity)
            else:
                output = pixels_to_terminal(pixels, color, style, drawille_threshold)
            sys.stdout.write("\x1b[H" + output)
            sys.stdout.flush()
            frame_no += 1
            _sleep_frame(delay)
    finally:
        sys.stdout.write(show_cursor() + "\n")


@app.command()
def compare(
    shader: Path,
    reference: Path,
    mode: Mode = typer.Option(Mode.auto),
    terminal_width: Optional[int] = typer.Option(None, "--terminal-width", "--width"),
    terminal_height: Optional[int] = typer.Option(None, "--terminal-height", "--height"),
    render_width: Optional[int] = None,
    render_height: Optional[int] = None,
    time_value: float = typer.Option(0.0, "--time"),
    time_scan: Optional[str] = typer.Option(None),
    frame_value: int = typer.Option(0, "--frame"),
    playback_level: float = typer.Option(1.0),
    mouse: str = "0,0",
    style: RenderStyle = RenderStyle.half,
    min_score: float = typer.Option(0.55),
) -> None:
    geo = _geometry(terminal_width, terminal_height, style, render_width, render_height)
    renderer = _renderer(_read_shader(shader), geo.render_width, geo.render_height, mode.value)
    times = parse_time_scan(time_scan) if time_scan else [time_value]

    best_time = times[0]
    best_shader = None
    best_terminal = None
    best_score = -1.0
    reference_rgb = load_reference(reference, geo.target_width, geo.target_height)

    for sample_time in times:
        pixels = _shader_frame(
            renderer,
            RenderState(sample_time, frame_value, _parse_mouse(mouse)),
            geo.target_width,
            geo.target_height,
            playback_level,
        )
        shader_result = compare_rgb(pixels, reference_rgb)
        terminal_result = compare_rgb(terminal_preview_pixels(pixels, style), reference_rgb)
        combined = (shader_result.score + terminal_result.score) / 2.0
        if combined > best_score:
            best_score = combined
            best_time = sample_time
            best_shader = shader_result
            best_terminal = terminal_result

    assert best_shader is not None
    assert best_terminal is not None
    _print_comparison("shader", best_shader)
    _print_comparison("terminal", best_terminal)
    console.print(f"time: {best_time:.3f}")
    console.print(f"combined_score: {best_score:.3f}")
    if best_score < min_score:
        raise typer.Exit(1)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def shell(
    ctx: typer.Context,
    shader: Path,
    mode: Mode = typer.Option(Mode.auto),
    terminal_width: Optional[int] = typer.Option(None, "--terminal-width", "--width"),
    terminal_height: Optional[int] = typer.Option(None, "--terminal-height", "--height"),
    render_width: Optional[int] = None,
    render_height: Optional[int] = None,
    shell_name: str = typer.Option("auto", "--shell"),
    background_opacity: float = typer.Option(0.35),
    idle_fps: float = typer.Option(30.0),
    active_fps: float = typer.Option(12.0),
    playback_rate: float = typer.Option(1.0),
    playback_level: float = typer.Option(1.0),
    color: ColorMode = ColorMode.truecolor,
) -> None:
    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]
    argv = shell_command(shell_name, command)
    cols, rows = _terminal_grid_size(terminal_width, terminal_height)
    renderer = _renderer(_read_shader(shader), render_width or cols, render_height or rows * 2, mode.value)
    model = TerminalModel(cols, rows)
    child = spawn(argv, cols, rows)
    _run_shell_loop(
        child,
        renderer,
        model,
        idle_fps,
        active_fps,
        background_opacity,
        color,
        playback_rate,
        playback_level,
        render_width,
        render_height,
    )


@app.command("pipe")
def pipe_text(
    shader: Path,
    mode: Mode = typer.Option(Mode.auto),
    terminal_width: Optional[int] = typer.Option(None, "--terminal-width", "--width"),
    terminal_height: Optional[int] = typer.Option(None, "--terminal-height", "--height"),
    render_width: Optional[int] = None,
    render_height: Optional[int] = None,
    fps: float = 30.0,
    duration: Optional[float] = None,
    time_value: float = typer.Option(0.0, "--time"),
    frame_value: int = typer.Option(0, "--frame"),
    playback_rate: float = typer.Option(1.0),
    playback_level: float = typer.Option(1.0),
    mouse: str = "0,0",
    layer: LayerMode = LayerMode.background,
    background_opacity: float = typer.Option(0.35),
    color: ColorMode = ColorMode.truecolor,
) -> None:
    text = sys.stdin.read()
    cols, rows = _terminal_grid_size(terminal_width, terminal_height)
    render_w = render_width or cols
    render_h = render_height or rows * 2
    renderer = _renderer(_read_shader(shader), render_w, render_h, mode.value)
    cells = _text_cells(text, cols, rows)

    if duration is None:
        pixels = _shader_frame(
            renderer,
            RenderState(time_value * playback_rate, frame_value, _parse_mouse(mouse)),
            cols,
            rows * 2,
            playback_level,
        )
        if layer == LayerMode.foreground:
            sys.stdout.write(pixels_to_terminal(pixels, color, RenderStyle.half) + "\n")
        else:
            sys.stdout.write(composite(pixels, cells, color, background_opacity) + "\n")
        return

    start = time.monotonic()
    frame_no = 0
    delay = _frame_delay(fps)
    sys.stdout.write(clear_screen())
    try:
        while time.monotonic() - start < duration:
            now = time.monotonic() - start
            pixels = _shader_frame(
                renderer,
                RenderState(now * playback_rate, frame_no, _parse_mouse(mouse)),
                cols,
                rows * 2,
                playback_level,
            )
            if layer == LayerMode.foreground:
                output = pixels_to_terminal(pixels, color, RenderStyle.half)
            else:
                output = composite(pixels, cells, color, background_opacity)
            sys.stdout.write("\x1b[H" + output)
            sys.stdout.flush()
            frame_no += 1
            _sleep_frame(delay)
    finally:
        sys.stdout.write(show_cursor() + "\n")


def _print_comparison(label: str, result) -> None:
    console.print(
        f"{label}: score={result.score:.3f} corr={result.luminance_correlation:.3f} "
        f"bright_overlap={result.bright_overlap:.3f} mae={result.mae:.2f} "
        f"mse={result.mse:.2f} psnr={result.psnr:.2f}"
    )


if __name__ == "__main__":
    main()
