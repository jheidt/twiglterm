// Source: https://fragcoord.xyz/s/bky38y8x
// Title: Basic Cartesian Grid
// SPDX-License-Identifier: CC0-1.0
// Copyright (c) Public domain
// License: https://creativecommons.org/publicdomain/zero/1.0/
// Adapted from FragCoord uniforms: u_time -> time, u_resolution -> resolution,
// fragColor -> gl_FragColor.

precision highp float;

uniform vec2 resolution;
uniform float time;

vec2 rotate2d(vec2 p, float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c) * p;
}

// 2D Shapes | Inigo Quilez (iquilezles.org)
// Snippet: https://fragcoord.xyz/snippet/25ee0ac7-8300-4e40-9000-fa8089c77746b000
float sd_segment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

void main() {
    float zoom = 4.0 + cos(time / 2.0);
    float pixel = zoom / resolution.y;
    vec2 uv = pixel * (2.0 * gl_FragCoord.xy - resolution);

    uv = rotate2d(uv, time / 10.0);

    vec3 col = vec3(0.02, 0.01, 0.05);

    float grid = min(abs(0.5 - fract(uv.y + 0.5)), abs(0.5 - fract(uv.x + 0.5)));
    grid = tanh(pixel / abs(grid));
    col = mix(col, vec3(1.5, 0.5, 3.0), grid);

    float axis = min(abs(uv.x), abs(uv.y));
    axis = tanh(pixel / abs(axis));
    col = mix(col, vec3(4.0, 1.0, 2.0), axis);

    vec3 A = vec3(3.82, 0.0, 2.82);
    vec3 B = vec3(0.2568, 2.547, 1.56);
    vec3 C = vec3(-1.186, 1.003, 0.553191489362);
    vec3 D = vec3(-1.35, 0.1102, 0.354609929078);
    vec3 E = vec3(-1.382, -0.885, 0.641025641026);
    vec3 F = vec3(0.1387, -2.804, 1.80769230769);

    float circle = length(uv) - 1.0;
    circle = min(circle, length(uv - A.xy) - A.z);
    circle = min(circle, length(uv - B.xy) - B.z);
    circle = min(circle, length(uv - C.xy) - C.z);
    circle = min(circle, length(uv - D.xy) - D.z);
    circle = min(circle, length(uv - E.xy) - E.z);
    circle = min(circle, length(uv - F.xy) - F.z);

    bool inside = circle < 0.0;
    circle = tanh(3.0 * pixel / abs(circle));
    col = mix(col, inside ? vec3(3.0, 2.0, 2.0) : vec3(2.0, 2.0, 5.0), circle);

    float line = sd_segment(uv, A.xy, B.xy);
    line = min(line, sd_segment(uv, B.xy, C.xy));
    line = min(line, sd_segment(uv, C.xy, D.xy));
    line = min(line, sd_segment(uv, D.xy, E.xy));
    line = min(line, sd_segment(uv, E.xy, F.xy));
    line = min(line, sd_segment(uv, F.xy, A.xy));
    line = tanh(3.0 * pixel / line);
    col = mix(col, vec3(2.0, 2.0, 5.0), line);

    gl_FragColor = vec4(vec3(tanh(0.8 * col)), 1.0);
}

