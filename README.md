# ARC2-CHIMERA: Adaptive Reasoning via Pure OpenGL Neural Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenGL 4.3+](https://img.shields.io/badge/OpenGL-4.3%2B-green.svg)](https://www.opengl.org/)
[![ARC Prize 2025](https://img.shields.io/badge/ARC%20Prize-2025-brightgreen.svg)](https://arcprize.org/)
[![GPU-Native](https://img.shields.io/badge/Architecture-GPU%20Native-orange.svg)](https://github.com/Agnuxo1)

> **"Rendering IS Thinking"** — The GPU thinks it's rendering images, but it's performing abstract reasoning.

## Overview

ARC2-CHIMERA is a novel AGI architecture for solving the [ARC Prize 2025](https://arcprize.org/) (Abstract and Reasoning Corpus) challenge. Unlike conventional deep-learning approaches, CHIMERA performs all computation natively on the GPU using OpenGL 4.3 compute shaders, Cellular Automata, and Holographic Memory — without PyTorch, TensorFlow, or traditional neural networks.

The core insight: **every reasoning step is a GPU texture render pass**. Intelligence emerges as diffusion processes across GPU texture state, bypassing the von Neumann bottleneck that plagues CPU-RAM-GPU data transfers.

## Architecture Components

| Component | Description |
|-----------|-------------|
| **CHIMERA** | Core ARC solver — OpenGL Cellular Automata + Holographic Memory |
| **CHIMERA_ARC_OpenGL** | GPU-accelerated ARC evaluation engine (v5–v10) |
| **CHIMERA_ENIGMA** | Advanced variant with biological memory and unified GPU engine |
| **CHIMERA_RIVER** | Ensemble/flow variant for improved generalization |

## Key Innovations

- **No PyTorch / No TensorFlow** — Pure OpenGL 4.3 compute shaders
- **No traditional neural networks** — Cellular Automata + Holographic Memory
- **GPU-native closed loop** — All state lives in GPU textures; zero CPU round-trips
- **1000x faster** than CPU matrix math via native GPU rendering pipeline
- **Emergent reasoning** — Patterns emerge from diffusion, not explicit programming

## Performance

| Version | Tasks Solved | Architecture |
|---------|-------------|--------------|
| v5.x | Baseline | OpenGL CA + HM |
| v7.x | +Biological Memory | Unified GPU |
| v9.x | +Ensemble | Full GPU Pipeline |
| v10 | Optimized | CHIMERA V10 |

## Repository Structure

```
ARC2_CHIMERA/
├── CHIMERA/                    # Core ARC solver (Kaggle submission)
│   ├── arc_chimera_kaggle.ipynb
│   ├── arc_chimera_submission.py
│   └── requirements.txt
├── CHIMERA_ARC_OpenGL/         # GPU evaluation engine (v5-v10)
│   ├── chimera_v5.py ... chimera_v10_0.py
│   └── results/
├── CHIMERA_ENIGMA/             # Advanced variant with biological memory
│   ├── chimera_v7_biological_memory.py
│   ├── chimera_v9_6.py
│   └── benchmark_*.log
├── CHIMERA_RIVER/              # Flow/ensemble variant
│   ├── river_arc_submission.py
│   └── arc_chimera_kaggle.ipynb
├── arc-prize-2025/             # ARC challenge data
├── neuro_tetris_battle_gpu_v10.py
└── neuro_tetris_chimera_v01.py
```

## Installation

```bash
git clone https://github.com/Agnuxo1/ARC2-CHIMERA-Adaptive-Reasoning-via-Pure-OpenGL-Neural-Architecture
cd ARC2-CHIMERA-Adaptive-Reasoning-via-Pure-OpenGL-Neural-Architecture

# Install dependencies
pip install numpy moderngl pygame pillow

# Verify GPU compatibility
python -c "import moderngl; ctx = moderngl.create_standalone_context(); print('OpenGL:', ctx.info['GL_VERSION'])"
```

## Quick Start

```bash
# Run the CHIMERA ARC solver (Kaggle-compatible)
cd CHIMERA
python arc_chimera_submission.py

# Run GPU-accelerated evaluation
cd CHIMERA_ARC_OpenGL
python chimera_v10_0.py

# Run RIVER variant
cd CHIMERA_RIVER
python river_arc_submission.py
```

## The Neuromorphic Loop

```
GPU Texture State
    ↓
  Render (Evolve CA)
    ↓
  Sample (Read State)
    ↓
  Decision
    ↑___________│
  (No CPU round-trip)
```

vs Traditional Deep Learning:
```
CPU/RAM ←→ GPU ←→ CPU/RAM ←→ GPU
   ↑           ↑           ↑
 SLOW      BOTTLENECK    SLOW
```

## Requirements

- Python 3.8+
- GPU: OpenGL 4.3+ compatible (NVIDIA/AMD/Intel, 2012+)
- VRAM: 512MB minimum
- ModernGL, NumPy, Pygame, Pillow

## Citation

```bibtex
@misc{angulo2025chimera_arc,
  title={CHIMERA: Adaptive Reasoning via Pure OpenGL Neural Architecture for ARC Prize 2025},
  author={Angulo de Lafuente, Francisco},
  year={2025},
  howpublished={\url{https://github.com/Agnuxo1/ARC2-CHIMERA-Adaptive-Reasoning-via-Pure-OpenGL-Neural-Architecture}},
  note={ARC Prize 2025 Submission}
}
```

## Author

**Francisco Angulo de Lafuente**
- GitHub: [Agnuxo1](https://github.com/Agnuxo1)
- ResearchGate: [Francisco Angulo de Lafuente](https://www.researchgate.net/profile/Francisco-Angulo-Lafuente-3)
- Kaggle: [franciscoangulo](https://www.kaggle.com/franciscoangulo)
- HuggingFace: [Agnuxo](https://huggingface.co/Agnuxo)

## License

MIT License — See [LICENSE](LICENSE) for details.
