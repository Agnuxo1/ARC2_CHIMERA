# PROJECT STATUS — Read This First

## This is a research proof-of-concept. NOT an ARC Prize submission.

**Current benchmark accuracy on ARC-AGI tasks: ~2-5%** (measured on 100-task
subsets across v5-v10 variants). The 85% target required to be competitive in
the ARC Prize 2025 is far out of reach with the current code.

The symbolic reasoning engine does **not yet perform**. Publishing this as an
"ARC solver" or "AGI architecture" would be misleading. It is being released
honestly as a research artifact.

## What actually works

The **GPU compute-shader architecture** is the reusable portion:

- Matmul kernels (GLSL compute)
- GELU / activation kernels
- Diffusion-style update passes
- Cellular-automaton texture updates
- Holographic-memory read/write passes
- Zero-roundtrip GPU state loop (all state in textures across frames)

These run correctly on any OpenGL 4.3+ GPU via `moderngl`. They are fast and
framework-free (no PyTorch, no TensorFlow). If you want to experiment with
GPU-native symbolic primitives, this code is a useful starting point.

## What is missing

To reach competitive accuracy on ARC, the project would need (at minimum):

- A correct-enough DSL operator set (the current `CHIMERA_DSL` is too narrow
  and its search is too shallow to cover the ARC task distribution).
- A real symbolic-reasoning integration layer on top of the GPU primitives —
  currently the "reasoning" is diffusion over textures, which does not
  generalize to ARC's compositional rules.
- A program-synthesis / neuro-symbolic search component.
- Training / fitting beyond the hand-crafted heuristics.

## Variants in this repository

- `CHIMERA/` — earliest Kaggle-style submission script (unverified format).
- `CHIMERA_ARC_OpenGL/` — iterative v5-v10 development. **v10 is the primary
  code path** exposed by the `arc2-chimera` package.
- `CHIMERA_ENIGMA/` — experimental variant with biological-memory ideas.
- `CHIMERA_RIVER/` — ensemble/flow variant.

Older variants are kept for historical reference; the installable package
targets v10 only.

## Disclaimers

- No claim is made that this repository solves ARC.
- No claim is made that this repository is ready for the ARC Prize 2025.
- Accuracy numbers reported elsewhere in the repo were measured on small
  subsets and should not be interpreted as competitive results.
- The architecture described is exploratory.

Author: Francisco Angulo de Lafuente — April 2026.
