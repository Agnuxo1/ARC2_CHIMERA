# ARC2-CHIMERA

[![PyPI version](https://img.shields.io/pypi/v/arc2-chimera)](https://pypi.org/project/arc2-chimera/)
[![PyPI downloads](https://img.shields.io/pypi/dm/arc2-chimera)](https://pypi.org/project/arc2-chimera/)
[![License](https://img.shields.io/github/license/Agnuxo1/ARC2_CHIMERA)](https://github.com/Agnuxo1/ARC2_CHIMERA/blob/master/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/arc2-chimera)](https://pypi.org/project/arc2-chimera/)
[![GitHub stars](https://img.shields.io/github/stars/Agnuxo1/ARC2_CHIMERA?style=social)](https://github.com/Agnuxo1/ARC2_CHIMERA)

> **GPU compute-shader playground exploring OpenGL-based primitives for
> symbolic reasoning. Accuracy on ARC is a research baseline, not a
> competitive submission.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![OpenGL 4.3+](https://img.shields.io/badge/OpenGL-4.3%2B-green.svg)](https://www.opengl.org/)
[![Status: Research PoC](https://img.shields.io/badge/status-research--PoC-orange.svg)](./PROJECT_STATUS.md)

<!-- impact-note:start -->
<sub><strong>Efficiency and practical value.</strong> Reusable GLSL primitives and a GPU-resident state loop offer a compact testbed for symbolic-reasoning experiments without rebuilding the graphics-compute plumbing for each study. Avoiding CPU transfers between frames is a specific architectural efficiency opportunity. The practical contribution is reusable shader infrastructure; competitive ARC reasoning performance remains outside the demonstrated results in <a href="PROJECT_STATUS.md">the project status</a>.</sub>
<!-- impact-note:end -->

## Please read [PROJECT_STATUS.md](./PROJECT_STATUS.md) before anything else.

**TL;DR:** this repository is a **research proof-of-concept**. Current
benchmark accuracy on ARC-AGI is **~2-5%** on 100-task subsets — well below
the 85% target of the ARC Prize. **This is not an ARC Prize submission and
should not be described as one.** The reusable value is the GPU compute-shader
architecture, not the reasoning engine.

## What the package is

`arc2-chimera` exposes the v10 OpenGL-based architecture as an installable
Python package so the shader primitives can be reused:

- Matmul / GELU kernels implemented as GLSL compute shaders.
- Cellular-automaton texture update kernels.
- Diffusion-style update passes.
- Holographic-memory read/write passes.
- A GPU-texture state loop (no CPU round-trips between frames).

All of this runs on any OpenGL 4.3+ GPU via `moderngl`. There is no PyTorch
or TensorFlow dependency.

## Install

```bash
pip install arc2-chimera          # core (numpy, Pillow)
pip install arc2-chimera[gpu]     # add moderngl + glfw for real GPU runs
pip install arc2-chimera[dev]     # pytest / build / twine
```

## CLI

```bash
arc2-chimera info                                      # prints status + disclaimer
arc2-chimera evaluate --task-file task.json --output out.json
```

## Repository layout

| Path | Description |
|------|-------------|
| `arc2_chimera/` | Installable package (wraps v10). |
| `CHIMERA_ARC_OpenGL/` | v5-v10 development tree. v10 is the primary code path. |
| `CHIMERA/` | Early Kaggle-style script (historical). |
| `CHIMERA_ENIGMA/` | Experimental biological-memory variant. |
| `CHIMERA_RIVER/` | Ensemble/flow variant. |
| `archive/` | Quarantined scripts (including an unverified submission file). |
| `tests/` | Offline pytest suite. |

## What works / what doesn't

See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for the full list. In short: the
GPU kernels work and are worth reusing. The symbolic reasoning layer on top
of them does not yet perform on ARC.

## License

Apache-2.0. Author: Francisco Angulo de Lafuente <agnuxo1@gmail.com>.

---

## Related projects

Part of the [@Agnuxo1](https://github.com/Agnuxo1) v1.0.0 open-source catalog (April 2026).

**AgentBoot constellation** — agents and research loops
- [AgentBoot](https://github.com/Agnuxo1/AgentBoot) — Conversational AI agent for bare-metal hardware detection and OS install.
- [autoresearch-nano](https://github.com/Agnuxo1/autoresearch) — nanoGPT-based autonomous ML research loop.
- [The Living Agent](https://github.com/Agnuxo1/The-Living-Agent) — 16x16 Chess-Grid autonomous research agent.
- [benchclaw-integrations](https://github.com/Agnuxo1/benchclaw-integrations) — Agent-framework adapters for the BenchClaw API.

**CHIMERA / neuromorphic constellation** — GPU-native scientific computing
- [NeuroCHIMERA](https://github.com/Agnuxo1/NeuroCHIMERA__GPU-Native_Neuromorphic_Consciousness) — GPU-native neuromorphic framework on OpenGL compute shaders.
- [Holographic-Reservoir](https://github.com/Agnuxo1/Holographic-Reservoir) — Reservoir computing with simulated ASIC backend.
- [ASIC-RAG-CHIMERA](https://github.com/Agnuxo1/ASIC-RAG-CHIMERA) — GPU simulation of a SHA-256 hash engine wired into a RAG pipeline.
- [QESN-MABe](https://github.com/Agnuxo1/QESN_MABe_V2_REPO) — Quantum-inspired Echo State Network on a 2D lattice (classical).
- [Quantum-GPS](https://github.com/Agnuxo1/Quantum-GPS-Unified-Navigation-System) — Quantum-inspired GPU navigator (classical Eikonal solver).
