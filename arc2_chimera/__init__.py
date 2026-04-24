"""arc2-chimera — research proof-of-concept.

NOT an ARC Prize submission. Current benchmark accuracy on ARC-AGI is
~2-5% on 100-task subsets (well below the 85% target). The symbolic
reasoning engine does not yet perform. The reusable portion is the
OpenGL compute-shader architecture.

See PROJECT_STATUS.md at the repository root for full context.
"""

__version__ = "1.0.0"
__author__ = "Francisco Angulo de Lafuente"
__email__ = "agnuxo1@gmail.com"
__license__ = "Apache-2.0"

DISCLAIMER = (
    "arc2-chimera is a research proof-of-concept. It is NOT an ARC Prize "
    "submission. Measured ARC-AGI accuracy: ~2-5% on 100-task subsets. "
    "The reusable portion is the GPU compute-shader architecture."
)

BENCHMARK_ACCURACY_RANGE = (0.0192, 0.05)


def get_status() -> dict:
    """Return a machine-readable status summary."""
    return {
        "name": "arc2-chimera",
        "version": __version__,
        "status": "research-proof-of-concept",
        "arc_prize_submission": False,
        "benchmark_accuracy_range": BENCHMARK_ACCURACY_RANGE,
        "disclaimer": DISCLAIMER,
    }


__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "DISCLAIMER",
    "BENCHMARK_ACCURACY_RANGE",
    "get_status",
]
