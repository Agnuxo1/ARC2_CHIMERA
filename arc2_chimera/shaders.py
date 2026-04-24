"""GLSL compute-shader source strings used by the v10 architecture.

These are the *reusable* portion of the project. They are kept as plain
strings so the package is importable without a GPU — the caller is
responsible for creating a moderngl context and compiling them.
"""
from __future__ import annotations

MATMUL_CS = """
#version 430
layout(local_size_x = 16, local_size_y = 16) in;
layout(std430, binding = 0) readonly buffer A { float a[]; };
layout(std430, binding = 1) readonly buffer B { float b[]; };
layout(std430, binding = 2) writeonly buffer C { float c[]; };
uniform int M;
uniform int N;
uniform int K;
void main() {
    uint row = gl_GlobalInvocationID.y;
    uint col = gl_GlobalInvocationID.x;
    if (row >= uint(M) || col >= uint(N)) return;
    float acc = 0.0;
    for (int k = 0; k < K; ++k) {
        acc += a[row * uint(K) + uint(k)] * b[uint(k) * uint(N) + col];
    }
    c[row * uint(N) + col] = acc;
}
"""

GELU_CS = """
#version 430
layout(local_size_x = 64) in;
layout(std430, binding = 0) buffer X { float x[]; };
uniform int N;
void main() {
    uint i = gl_GlobalInvocationID.x;
    if (i >= uint(N)) return;
    float v = x[i];
    float k0 = 0.7978845608;   // sqrt(2/pi)
    float k1 = 0.044715;
    float t = k0 * (v + k1 * v * v * v);
    x[i] = 0.5 * v * (1.0 + tanh(t));
}
"""

DIFFUSION_CS = """
#version 430
layout(local_size_x = 16, local_size_y = 16) in;
layout(rgba32f, binding = 0) uniform readonly image2D src;
layout(rgba32f, binding = 1) uniform writeonly image2D dst;
uniform float rate;
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz = imageSize(src);
    if (p.x >= sz.x || p.y >= sz.y) return;
    vec4 c = imageLoad(src, p);
    vec4 n = imageLoad(src, ivec2(p.x, max(p.y - 1, 0)));
    vec4 s = imageLoad(src, ivec2(p.x, min(p.y + 1, sz.y - 1)));
    vec4 w = imageLoad(src, ivec2(max(p.x - 1, 0), p.y));
    vec4 e = imageLoad(src, ivec2(min(p.x + 1, sz.x - 1), p.y));
    vec4 lap = (n + s + w + e) - 4.0 * c;
    imageStore(dst, p, c + rate * lap);
}
"""

CELLULAR_AUTOMATON_CS = """
#version 430
layout(local_size_x = 16, local_size_y = 16) in;
layout(r32ui, binding = 0) uniform readonly uimage2D src;
layout(r32ui, binding = 1) uniform writeonly uimage2D dst;
void main() {
    ivec2 p = ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz = imageSize(src);
    if (p.x >= sz.x || p.y >= sz.y) return;
    uint me = imageLoad(src, p).x;
    uint alive = 0u;
    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            if (dx == 0 && dy == 0) continue;
            ivec2 q = clamp(p + ivec2(dx, dy), ivec2(0), sz - ivec2(1));
            alive += imageLoad(src, q).x;
        }
    }
    uint nxt = 0u;
    if (me == 1u && (alive == 2u || alive == 3u)) nxt = 1u;
    if (me == 0u && alive == 3u) nxt = 1u;
    imageStore(dst, p, uvec4(nxt, 0u, 0u, 0u));
}
"""

HOLOGRAPHIC_MEMORY_CS = """
#version 430
layout(local_size_x = 64) in;
layout(std430, binding = 0) readonly buffer Key { float key[]; };
layout(std430, binding = 1) readonly buffer Val { float val[]; };
layout(std430, binding = 2) buffer Mem { float mem[]; };
uniform int D;
void main() {
    uint i = gl_GlobalInvocationID.x;
    if (i >= uint(D)) return;
    // circular convolution-style bind (approximate)
    mem[i] = mem[i] + key[i] * val[i];
}
"""

ALL_SHADERS: dict[str, str] = {
    "matmul": MATMUL_CS,
    "gelu": GELU_CS,
    "diffusion": DIFFUSION_CS,
    "cellular_automaton": CELLULAR_AUTOMATON_CS,
    "holographic_memory": HOLOGRAPHIC_MEMORY_CS,
}


def get_shader(name: str) -> str:
    if name not in ALL_SHADERS:
        raise KeyError(f"unknown shader {name!r}; available: {sorted(ALL_SHADERS)}")
    return ALL_SHADERS[name]
