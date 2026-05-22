uniform vec2 u_resolution;
uniform float u_time;

//[CONVERT] GLSL
// SPDX-License-Identifier: CC-BY-4.0
// Copyright (c) 2026 @Xor
//[LICENSE] https://creativecommons.org/licenses/by/4.0/

uniform sampler2D u_main;

//[CONVERT] GLSL
void main() {
    // SPDX-License-Identifier: CC-BY-4.0
    // Copyright (c) 2026 @Xor
    //[LICENSE] https://creativecommons.org/licenses/by/4.0/
    
    vec3 p = vec3(gl_FragCoord.xy * 2.0 - u_resolution, 0.0) / u_resolution.y;
    vec3 s = vec3(sqrt(max(.5 - dot(p, p), 0.)), p);
    vec3 a = vec3(cos(u_time + vec3(0, 11, -u_time)));
    fragColor.rgb = .1 / abs(mix(a * dot(a, s), s, .8) - .6 * cross(a, s)) / (1.0 + dot(p, p));
    fragColor = tanh(fragColor + length(fragColor/5.0));
}