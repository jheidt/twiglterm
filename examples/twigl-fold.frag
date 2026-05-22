// Source: https://webgl.souhonzan.org/entry/?v=1709
// Mode: classic

precision highp float;
uniform vec2 resolution;
uniform vec2 mouse;
uniform float time;

void main() {
    vec2 r = resolution;
    vec2 p = (gl_FragCoord.xy * 2.0 - r) / min(r.y, r.x) - mouse;
    for (int i = 0; i < 8; ++i) {
        p.xy = abs(p) / abs(dot(p, p)) - vec2(0.9 + cos(time * 0.2) * 0.4);
    }
    gl_FragColor = vec4(p.x, p.x, p.y, 1.0);
}

