// Source: https://fragcoord.xyz/s/p0385h9e
// Title: Pulse Test1
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 @yli110
// License: https://opensource.org/licenses/MIT
// Adapted from FragCoord uniforms: u_time -> time, u_resolution -> resolution,
// fragColor -> gl_FragColor.

precision highp float;

uniform vec2 resolution;
uniform float time;

#define R resolution.xy
#define PIXEL 10.0 / min(R.x, R.y)
#define S smoothstep
#define T time
#define L(p, b) length((p) - (b) * clamp(dot((p), (b)) / dot((b), (b)), 0.0, 1.0))

const float a[3] = float[3](0.0, 1.0, -1.0);

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float cn(vec2 a0, vec2 d) {
    float n = hash(a0);
    vec2 c = normalize(a0), l = normalize(d);
    float m = abs(dot(c, l));
    float p = S(0.7, 0.98, m) * 0.75;
    float t = length(a0);
    float ce = 1.0 - S(0.0, 2.0, t);
    p *= S(18.0, 2.0, t);
    p = mix(p, 0.8, ce);
    return mix(1e2, 0.0, step(n, p));
}

void main() {
    vec2 F = gl_FragCoord.xy;
    vec2 uv = (F - 0.5 * R) / R.y;

    float s = 20.0, d = 1e2;
    vec2 u = uv * s;
    vec2 i = floor(u);
    vec2 f = fract(u) - 0.5;

    for (int m = 1; m < 9; ++m) {
        int j = m % 3, k = m / 3;
        vec2 q = vec2(a[j], a[k]), p = i + q * 0.5;
        d = min(d, cn(p, q) + L(f, q * 0.5));
    }

    float t = 0.1;
    float an = atan(i.y, i.x);
    float di = length(uv) * 5.0;
    float l = S(t + PIXEL, t, d) - S(t, 0.0, d);
    float cl = S(t * 0.3 + PIXEL, t * 0.3, d);
    float g = PIXEL / (d + 1e-3);

    float ro = sin(an * 7.1) * 2.5 + cos(an * 3.1) * 2.0;
    float rs = 1.5 + sin(an * 5.0) * 0.5;
    float w = fract(di + ro - T * rs);
    float pu = 0.1 / (1.0 - w + 0.015) * hash(uv);
    pu = max(0.0, pu - 0.05) * S(1.0, 0.95, w);

    vec3 bc = vec3(0.2941, 0.33, 0.388) * l * 1.5;
    vec3 pc = vec3(0.973, 0.443, 0.443) * pu * cl * 4.0;
    pc += vec3(1.0, 0.7, 0.0) * pu * g;

    vec3 c = bc + pc;
    c *= exp(-di * 0.5);

    gl_FragColor = vec4(c, 1.0);
}

