from __future__ import annotations

import os
import queue
import selectors
import sys
import threading
import time

from .ansi import ColorMode, clear_screen, show_cursor
from .compositor import TerminalModel
from .renderer import RenderState, ShaderRenderer
from .terminal import frame_delay, shader_frame, sleep_frame
from .terminal_output import FrameBytes, composite_bytes, encoded_redraw


def run_shell_loop(
    child,
    renderer: ShaderRenderer,
    model: TerminalModel,
    idle_fps: float,
    active_fps: float,
    opacity: float,
    color: ColorMode,
    playback_rate: float,
    playback_level: float,
    render_width: int | None,
    render_height: int | None,
    redraw: str = "diff",
) -> None:
    if os.name == "nt":
        _run_windows_shell_loop(
            child,
            renderer,
            model,
            idle_fps,
            active_fps,
            opacity,
            color,
            playback_rate,
            playback_level,
            render_width,
            render_height,
            redraw,
        )
    else:
        _run_posix_shell_loop(
            child,
            renderer,
            model,
            idle_fps,
            active_fps,
            opacity,
            color,
            playback_rate,
            playback_level,
            render_width,
            render_height,
            redraw,
        )


def _stdout_write(data: bytes) -> None:
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        sys.stdout.write(data.decode("utf-8", errors="replace"))
        return
    buffer.write(data)


def _stdout_flush() -> None:
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        sys.stdout.flush()
        return
    buffer.flush()


def draw_shell_frame(
    renderer,
    model,
    start,
    frame_no,
    opacity,
    color,
    playback_rate,
    playback_level,
    previous: FrameBytes | None,
    redraw: str,
) -> FrameBytes:
    pixels = shader_frame(
        renderer,
        RenderState((time.monotonic() - start) * playback_rate, frame_no),
        model.cols,
        model.rows * 2,
        playback_level,
    )
    output = composite_bytes(pixels, model.cells(), color, opacity, model.cursor)
    _stdout_write(encoded_redraw(previous, output, redraw))
    _stdout_flush()
    return output


def resize_shell(
    child,
    renderer: ShaderRenderer,
    model: TerminalModel,
    render_width: int | None = None,
    render_height: int | None = None,
) -> None:
    try:
        size = os.get_terminal_size()
    except OSError:
        return
    cols = max(1, size.columns)
    rows = max(1, size.lines)
    if cols == model.cols and rows == model.rows:
        return
    model.resize(cols, rows)
    renderer.resize(render_width or cols, render_height or rows * 2)
    child.resize(cols, rows)


def _run_posix_shell_loop(
    child,
    renderer,
    model,
    idle_fps,
    active_fps,
    opacity,
    color,
    playback_rate,
    playback_level,
    render_width,
    render_height,
    redraw,
) -> None:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    sel = selectors.DefaultSelector()
    sel.register(fd, selectors.EVENT_READ)
    sel.register(child.proc.fd, selectors.EVENT_READ)
    start = time.monotonic()
    frame_no = 0
    last_activity = start
    previous: FrameBytes | None = None
    _stdout_write(clear_screen().encode("ascii"))
    try:
        tty.setraw(fd)
        while child.isalive():
            resize_shell(child, renderer, model, render_width, render_height)
            active = time.monotonic() - last_activity < 0.2
            timeout = frame_delay(active_fps if active else idle_fps) or 0.0
            for key, _ in sel.select(timeout):
                if key.fileobj == fd:
                    data = os.read(fd, 4096)
                    if data:
                        child.write(data)
                        last_activity = time.monotonic()
                else:
                    data = child.read(4096)
                    if data:
                        model.feed(data.decode(errors="replace"))
                        last_activity = time.monotonic()
            previous = draw_shell_frame(
                renderer, model, start, frame_no, opacity, color, playback_rate, playback_level, previous, redraw
            )
            frame_no += 1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        _stdout_write((show_cursor() + "\n").encode("ascii"))


def _run_windows_shell_loop(
    child,
    renderer,
    model,
    idle_fps,
    active_fps,
    opacity,
    color,
    playback_rate,
    playback_level,
    render_width,
    render_height,
    redraw,
) -> None:
    import msvcrt

    output: queue.Queue[bytes] = queue.Queue()
    stop = threading.Event()

    def reader() -> None:
        while not stop.is_set() and child.isalive():
            try:
                data = child.read(4096)
            except Exception:
                break
            if data:
                output.put(data)

    threading.Thread(target=reader, daemon=True).start()
    start = time.monotonic()
    frame_no = 0
    last_activity = start
    previous: FrameBytes | None = None
    _stdout_write(clear_screen().encode("ascii"))
    try:
        while child.isalive():
            resize_shell(child, renderer, model, render_width, render_height)
            while msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0") and msvcrt.kbhit():
                    ch += msvcrt.getwch()
                child.write(ch.encode(errors="replace"))
                last_activity = time.monotonic()
            while True:
                try:
                    data = output.get_nowait()
                except queue.Empty:
                    break
                model.feed(data.decode(errors="replace"))
                last_activity = time.monotonic()
            previous = draw_shell_frame(
                renderer, model, start, frame_no, opacity, color, playback_rate, playback_level, previous, redraw
            )
            frame_no += 1
            active = time.monotonic() - last_activity < 0.2
            sleep_frame(frame_delay(active_fps if active else idle_fps))
    finally:
        stop.set()
        _stdout_write((show_cursor() + "\n").encode("ascii"))
