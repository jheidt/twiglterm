// Source: https://github.com/doxas/twigl readme example
// Mode: classic

precision highp float;
uniform float time;

void main() {
    vec4 p = vec4(gl_FragCoord.xy / 400.0, 0.0, -4.0);
    for (int i = 0; i < 9; ++i) {
        p += vec4(
            sin(-(p.x + time * 0.2)) + atan(p.y * p.w),
            cos(-p.x) + atan(p.z * p.w),
            cos(-(p.x + sin(time * 0.8))) + atan(p.z * p.w),
            0.0
        );
    }
    gl_FragColor = p;
}

