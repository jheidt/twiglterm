// Source: https://fragcoord.xyz/s/s0p2uz5l
// SPDX-License-Identifier: CC-BY-NC-SA-4.0
// Copyright (c) 2026 @Jaenam
// License: https://creativecommons.org/licenses/by-nc-sa/4.0/
// Adapted from FragCoord uniforms: u_time -> time, u_resolution -> resolution,
// fragColor -> gl_FragColor.

precision highp float;

uniform vec2 resolution;
uniform float time;

void main() {
    vec2 I = gl_FragCoord.xy;

    float i = 0.0;
    float d = 0.0;
    float w = 0.0;
    float t = time;
    float m = 1.0;
    vec3 p = vec3(0.0);
    vec3 k = vec3(0.0);
    vec3 r = resolution.xyy;
    vec3 Z = vec3(0.0);
    vec4 color = vec4(0.0);

    for (
        color *= i;
        i++ < 100.0 && abs(p.x) < 6.0;
        d += w = 0.01 + 0.07 * abs(
            max(
                mix(
                    sin(length(ceil(4.0 * k.z) + k)),
                    sin(length(p) - 1.0),
                    smoothstep(5.0, 5.5, p.y)
                ),
                sqrt(dot(k, k) + 16.0 - 8.0 * length(k.xy)) - 1.5
            ) - i / 150.0
        ),
        color += max(1.3 / w * sin(vec4(1.0, 2.0, 3.0, 1.0) + i * 0.5), -length(k * k))
    ) {
        k = vec3((I + I - r.xy) / r.y * d, d - 10.0);
        k.xz *= mat2(cos(sin(t / 2.0) * 0.785 + vec4(0.0, 33.0, 11.0, 0.0)));

        if (k.y < -6.3) {
            k.y = -k.y - 9.0;
            m = 0.5;
        }

        p = k * 0.5;
        w = 0.01;
        for (; w < 0.2; w += w) {
            p.yz += cos(p.xy * 0.01)
                - abs(dot(sin(0.02 * p.z + 0.03 * p.y + t + t + 0.3 * p / w), w + Z));
        }
    }

    gl_FragColor = tanh(color * color / 1e6) * m;
}

