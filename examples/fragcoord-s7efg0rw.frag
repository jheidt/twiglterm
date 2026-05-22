// Source: https://fragcoord.xyz/s/s7efg0rw
// Title: sdf log spiral
// SPDX-License-Identifier: MIT
// Copyright (c) 2026 @krisselden
// License: https://opensource.org/licenses/MIT
// Adapted from FragCoord uniforms: u_time -> time, u_resolution -> resolution,
// fragColor -> gl_FragColor. FragCoord UI uniforms are constants below.

precision highp float;

uniform vec2 resolution;
uniform float time;

const float u_b = 0.15;
const float u_zoom = 1.0;
const float u_width = 0.005;

const float PI = 3.141592653589793;
const float TAU = 6.283185307179586;

vec2 rotate2d(vec2 p, float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c) * p;
}

float safe_b(float b) {
    if (abs(b) < 1e-4) return (b < 0.0) ? -1e-4 : 1e-4;
    return b;
}

float refine_theta(vec2 p, float b, float theta) {
    float rho = length(p);
    float phi = atan(p.y, p.x);
    for (int i = 0; i < 6; ++i) {
        float eb = exp(b * theta);
        float u = theta - phi;
        float cu = cos(u);
        float su = sin(u);
        float f = b * eb - rho * (b * cu - su);
        float fp = b * b * eb + rho * (b * su + cu);
        float denom = abs(fp) < 1e-5 ? (fp < 0.0 ? -1e-5 : 1e-5) : fp;
        theta -= f / denom;
    }
    return theta;
}

vec4 spiral_exact_distance_and_gradient(vec2 p, float b) {
    float rho = length(p);
    if (rho < 1e-6) return vec4(0.0, 0.0, 1.0, 0.0);

    float phi = atan(p.y, p.x);
    float bb = safe_b(b);
    float base_theta = log(rho) / bb;
    float nearest_turn = round((base_theta - phi) / TAU);
    float best_d2 = 1e20;
    vec2 best_diff = vec2(0.0);

    for (int k = -2; k <= 2; ++k) {
        float turn = nearest_turn + float(k);

        float theta_a = refine_theta(p, bb, phi + TAU * turn);
        float r_a = exp(bb * theta_a);
        vec2 s_a = r_a * vec2(cos(theta_a), sin(theta_a));
        vec2 d_a = p - s_a;
        float d2a = dot(d_a, d_a);
        if (d2a < best_d2) {
            best_d2 = d2a;
            best_diff = d_a;
        }

        float theta_b = refine_theta(p, bb, base_theta + TAU * float(k));
        float r_b = exp(bb * theta_b);
        vec2 s_b = r_b * vec2(cos(theta_b), sin(theta_b));
        vec2 d_b = p - s_b;
        float d2b = dot(d_b, d_b);
        if (d2b < best_d2) {
            best_d2 = d2b;
            best_diff = d_b;
        }
    }

    float d = sqrt(best_d2);
    vec2 grad2 = d > 1e-6 ? best_diff / d : vec2(0.0);
    return vec4(grad2, 0.0, d);
}

vec3 palette(float t) {
    return 0.58 + 0.42 * cos(TAU * (vec3(t) + vec3(0.00, 0.16, 0.33)));
}

void main() {
    vec2 uv = (2.0 * gl_FragCoord.xy - resolution.xy) / resolution.y;
    uv = uv / u_zoom;
    uv = rotate2d(uv, time * 0.3);

    float b = safe_b(u_b);
    vec4 dg = spiral_exact_distance_and_gradient(uv, b);
    vec2 grad2 = normalize(dg.xy);
    float d = dg.w;

    float aa = max(fwidth(d) * 1.2, 1e-4);
    float line = 1.0 - smoothstep(u_width, u_width + aa, d);

    float s = 38.0 * d;
    float band = 0.5 + 0.5 * cos(TAU * s);
    band *= exp(-2.0 * d);

    float rho = length(uv);
    float phi = atan(uv.y, uv.x);

    vec2 guv = uv * 4.0;
    vec2 fw = max(fwidth(guv), vec2(1e-4));
    vec2 g = abs(fract(guv - 0.5) - 0.5) / fw;
    float grid = (1.0 - min(min(g.x, g.y), 1.0)) * 0.08;

    float axis = 0.0;
    axis += 1.0 - smoothstep(0.0, 0.003 + max(fwidth(uv.x), 1e-4), abs(uv.x));
    axis += 1.0 - smoothstep(0.0, 0.003 + max(fwidth(uv.y), 1e-4), abs(uv.y));
    axis = clamp(axis, 0.0, 1.0);

    vec3 bg = vec3(0.035, 0.050, 0.070) + grid;
    bg += 0.11 * axis * vec3(0.40, 0.55, 0.75);

    float grad_angle = atan(grad2.y, grad2.x) / TAU + 0.5;
    vec3 contour_col = palette(fract(grad_angle));
    contour_col = mix(
        contour_col,
        vec3(0.95, 0.73, 0.35),
        0.18 * (0.5 + 0.5 * cos(2.0 * phi + 0.35 * log(max(rho, 1e-4))))
    );

    vec3 col = bg + band * contour_col * 0.62;
    vec3 line_col = mix(vec3(1.0, 0.82, 0.45), vec3(1.0, 0.58, 0.30), 0.5 + 0.5 * sin(phi * 3.0));
    col = mix(col, line_col, line);

    gl_FragColor = vec4(col, 1.0);
}

