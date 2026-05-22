# twiglterm

inspired by textfx, thanks sol :)

a bit of vibes eh, but lots of textmode 

```
uvx run 'git+https://github.com/jheidt/twiglterm' play --fps 60 --style drawille https://fragcoord.xyz/s/lenp0a1d
```

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
uv run twiglterm play examples/gradient.frag --fps 30 --redraw diff
uv run twiglterm info examples/gradient.frag
uv run twiglterm bench examples/gradient.frag --terminal-width 80 --terminal-height 24 --style drawille
uv run twiglterm shell examples/gradient.frag -- $SHELL
uv run twiglterm frame examples/fragcoord-f03tybz5.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/fragcoord-f03tybz5.frag --style drawille --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/twigl-readme.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/twigl-radial-ripple.frag --style drawille --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/twigl-fold.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/fragcoord-s0p2uz5l.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/fragcoord-bky38y8x.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/fragcoord-p0385h9e.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame examples/fragcoord-s7efg0rw.frag --terminal-width 80 --terminal-height 40
uv run twiglterm frame "https://fragcoord.xyz/s/bky38y8x" --terminal-width 80 --terminal-height 40
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

# Animated modes default to row diff redraw; use full when a terminal needs complete repainting.
uv run twiglterm play examples/gradient.frag --redraw full --duration 2

# Foreground mode prints only the shader. Background mode composites text over shader-colored cells.
uv run twiglterm frame examples/gradient.frag --layer foreground
cat examples/piped-text.txt | uv run twiglterm pipe examples/gradient.frag --layer background

```

Shader arguments can be local files or supported URLs:

```bash
# FragCoord public shader URLs are fetched through FragCoord's public API.
uv run twiglterm frame "https://fragcoord.xyz/s/p0385h9e" --terminal-width 80 --terminal-height 40

# twigl.app URLs are supported when the shader is present in a source= query parameter.
uv run twiglterm frame "https://twigl.app/?mode=0&source=void+main()%7Bgl_FragColor%3Dvec4(1,0,1,1)%3B%7D" --terminal-width 20 --terminal-height 10

# Shadertoy source-query URLs are adapted; normal /view/ IDs require a Shadertoy API key and are reported clearly.
uv run twiglterm info "https://www.shadertoy.com/view/example?source=void+mainImage(out+vec4+c,in+vec2+p)%7Bc%3Dvec4(1)%3B%7D"
```

