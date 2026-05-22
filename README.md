# twiglterm

`twiglterm` renders twigl-style fragment shaders in modern terminals.

## Install

```bash
uv sync --extra posix --extra test
```

On Windows Terminal:

```powershell
uv sync --extra windows --extra test
```

## Usage

```bash
uv run twiglterm frame examples/gradient.frag --terminal-width 40 --terminal-height 20
uv run twiglterm play examples/gradient.frag --fps 30
uv run twiglterm info examples/gradient.frag
uv run twiglterm shell examples/gradient.frag -- $SHELL
uv run twiglterm frame examples/fragcoord-f03tybz5.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/fragcoord-f03tybz5.frag --style drawille --terminal-width 80 --terminal-height 40
cat examples/piped-text.txt | uv run twiglterm pipe examples/fragcoord-f03tybz5.frag --duration 6
```

Supported twigl v1 modes are `classic` and `geek`.

Sizing and playback:

```bash
# Terminal cell size defaults to the current terminal when omitted.
uv run twiglterm play examples/fragcoord-f03tybz5.frag --terminal-width 100 --terminal-height 36

# Render framebuffer size can be independent from terminal output size.
uv run twiglterm frame examples/fragcoord-f03tybz5.frag --terminal-width 80 --terminal-height 24 --render-width 320 --render-height 160

# fps=0 is unbounded; playback-rate changes shader time speed; playback-level scales output intensity.
uv run twiglterm play examples/gradient.frag --fps 0 --duration 2 --playback-rate 0.5 --playback-level 1.4

# Foreground mode prints only the shader. Background mode composites text over shader-colored cells.
uv run twiglterm frame examples/gradient.frag --layer foreground
cat examples/piped-text.txt | uv run twiglterm pipe examples/gradient.frag --layer background

# Compare Flare 2 against the reference render.
uv run twiglterm compare examples/fragcoord-f03tybz5.frag examples/flare2-reference.png --terminal-width 160 --terminal-height 90 --render-width 320 --render-height 180 --time-scan 0:12:1
```

`examples/fragcoord-f03tybz5.frag` is a GLSL translation of the public FragCoord shader at <https://fragcoord.xyz/s/f03tybz5>. The original golf source is preserved in `examples/fragcoord-f03tybz5.golf`.
`examples/flare2-reference.png` is the reference render used by `twiglterm compare`.

Example launchers:

```bash
examples/fullscreen-drawille.sh
examples/pipe-text.sh
examples/compare-flare2.sh
```

```powershell
.\examples\fullscreen-drawille.ps1
.\examples\pipe-text.ps1
.\examples\compare-flare2.ps1
```
