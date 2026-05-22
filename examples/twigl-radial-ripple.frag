// Source: https://twigl.app shared classic-mode URL indexed publicly
// Mode: classic

precision highp float;
uniform vec2 resolution;
uniform vec2 mouse;
uniform float time;

void main() {
    vec2 p = (gl_FragCoord.xy * 2.0 - resolution) / resolution;
    float l = length(p - mouse / max(resolution, vec2(1.0)) * 0.25);
    vec3 color = vec3(
        sin(l * 50.0 - time),
        sin(l * 47.5 - time),
        sin(l * 45.0 - time)
    );
    float vignette = clamp(1.0 - l, 0.0, 1.0);
    gl_FragColor = vec4(abs(color) * vignette, 1.0);
}

