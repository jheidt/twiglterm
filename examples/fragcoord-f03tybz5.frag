// Source: https://fragcoord.xyz/s/f03tybz5
// Title: Flare 2 [160]
// Original language: FragCoord golf
// Manual GLSL translation for twiglterm classic mode.

precision highp float;

uniform vec2 resolution;
uniform float time;

void main() {
    vec4 color = vec4(0.0);
    vec2 p = vec2(0.0);

    for (float i = -1.0; i < 1.0; i += 0.1) {
        p = ((2.0 * gl_FragCoord.xy - resolution) / resolution.y + i) / 0.2;
        vec4 phase = time - i - length(p) * 0.3 - vec4(0.0, 11.0, 33.0, 0.0);
        mat2 warp = mat2(cos(phase));

        vec2 flare = p * sin(p * warp);
        color += (cos(i / 0.3 + vec4(0.0, 1.0, 2.0, 0.0)) + 1.0)
            / (length(flare) + i * i);
    }

    gl_FragColor = tanh(color * color / 400.0);
}
