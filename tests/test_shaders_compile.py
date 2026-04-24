import pytest

from arc2_chimera import shaders


def test_all_shaders_are_strings():
    for name, src in shaders.ALL_SHADERS.items():
        assert isinstance(src, str), name
        assert "#version" in src, name
        assert "void main" in src, name


def test_get_shader_unknown_raises():
    with pytest.raises(KeyError):
        shaders.get_shader("no-such-shader")


def test_shader_compile_if_gpu_available():
    mgl = pytest.importorskip("moderngl")
    try:
        ctx = mgl.create_standalone_context(require=430)
    except Exception as e:
        pytest.skip(f"no OpenGL 4.3 context available: {e!r}")
    try:
        for name, src in shaders.ALL_SHADERS.items():
            ctx.compute_shader(src)  # raises on compile error
    finally:
        ctx.release()
