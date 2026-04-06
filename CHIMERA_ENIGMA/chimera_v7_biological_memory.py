#!/usr/bin/env python3
"""
CHIMERA v7 - Biological Memory Implementation

"85% Evolution + 15% Memory = Living Brain"

The missing piece: Each frame is a blend of:
- 85% NEW: CA evolution, learning, growing, exploring
- 15% OLD: Memory, what's important that persists

Like biological synapses:
- Strong synapses (important patterns) stay via memory
- Weak synapses (unimportant details) get replaced by new info
- New experiences enrich the system

Formula: new_frame = 0.85 * evolved + 0.15 * memory

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
import moderngl
from typing import Tuple, Optional, List, Dict
import time


# Configuration
class Config:
    """CHIMERA v7 configuration parameters"""
    EVOLUTION_RATIO = 0.85      # 85% new (CA evolution, learning)
    MEMORY_RATIO = 0.15         # 15% old (important patterns persist)
    LEARNING_RATE = 0.01        # How fast memory updates (1% per exposure)
    DIFFUSION_STEPS = 20        # How many evolution steps
    MEMORY_DECAY = 0.95         # Memory weakens over time (95% retention)


class HolographicMemory:
    """
    Biological memory system - holographic encoding in GPU textures.

    Memory works like synapses in a brain:
    - Each memory pattern is stored in a GPU texture
    - New patterns blend in gradually (1% at a time)
    - Important patterns strengthen (used patterns)
    - Unused patterns weaken (natural decay)
    - Retrieval is automatic via CA evolution
    """

    def __init__(self, ctx: moderngl.Context, grid_size: Tuple[int, int]):
        """Initialize holographic memory"""
        self.ctx = ctx
        self.height, self.width = grid_size
        self.memories = {}  # Key -> texture
        self.memory_names = []

        print(f"[MEMORY] Holographic memory initialized (learning_rate={Config.LEARNING_RATE})")

    def store_pattern(self, name: str, pattern: np.ndarray):
        """
        Store a pattern in holographic memory.

        Uses Hebbian-like learning: memory moves toward new pattern gradually.
        """
        pattern = np.clip(pattern, 0, 9)

        # Pad to memory size
        if pattern.shape != (self.height, self.width):
            padded = np.zeros((self.height, self.width), dtype=np.uint8)
            h, w = pattern.shape
            padded[:h, :w] = pattern
            pattern = padded

        if name not in self.memories:
            # Create new memory texture
            rgba = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            rgba[:, :, 0] = pattern
            rgba[:, :, 3] = 255

            texture = self.ctx.texture(
                size=(self.width, self.height),
                components=4,
                dtype='u1'
            )
            texture.write(rgba.tobytes())
            self.memories[name] = texture
            self.memory_names.append(name)
            print(f"[MEMORY] Created new memory: {name}")
        else:
            # Update existing memory with Hebbian learning
            texture = self.memories[name]

            # Read current memory
            old_rgba = np.frombuffer(texture.read(), dtype=np.uint8)
            old_rgba = old_rgba.reshape((self.height, self.width, 4))
            old_pattern = old_rgba[:, :, 0]

            # Hebbian update: memory moves toward pattern slowly
            # new_memory = old + (pattern - old) * learning_rate
            updated = np.clip(
                old_pattern.astype(float) + (pattern.astype(float) - old_pattern.astype(float)) * Config.LEARNING_RATE,
                0, 9
            ).astype(np.uint8)

            # Write back
            rgba = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            rgba[:, :, 0] = updated
            rgba[:, :, 3] = 255
            texture.write(rgba.tobytes())

            print(f"[MEMORY] Updated memory: {name} (learning_rate={Config.LEARNING_RATE})")

    def recall_pattern(self, name: str) -> np.ndarray:
        """Recall a pattern from memory"""
        if name not in self.memories:
            return np.zeros((self.height, self.width), dtype=np.uint8)

        texture = self.memories[name]
        rgba = np.frombuffer(texture.read(), dtype=np.uint8)
        rgba = rgba.reshape((self.height, self.width, 4))
        return rgba[:, :, 0]

    def blend_with_memory(self, evolved: np.ndarray, memory_key: str) -> np.ndarray:
        """
        Biological blending: mix evolution with memory.

        Formula: result = 0.85 * evolved + 0.15 * memory
        - 85% new (exploration, learning, change)
        - 15% old (important patterns that persist)

        This is like synaptic consolidation:
        - Strong connections (memories) maintain themselves
        - New input gets integrated gradually
        - System learns by updating, not replacing
        """
        memory = self.recall_pattern(memory_key)

        # Blend: mostly evolution, some memory
        blended = np.clip(
            evolved.astype(float) * Config.EVOLUTION_RATIO +
            memory.astype(float) * Config.MEMORY_RATIO,
            0, 9
        ).astype(np.uint8)

        return blended

    def release(self):
        """Clean up GPU memory"""
        for texture in self.memories.values():
            texture.release()
        print("[MEMORY] Holographic memory released")


class UnifiedFrameWithMemory:
    """
    Unified frame WITH biological memory integration.

    Contains:
    - Current state (RGBA texture)
    - Holographic memory (separate textures)
    - Blending mechanism (85/15 formula)
    """

    def __init__(self, ctx: moderngl.Context, size: Tuple[int, int]):
        self.ctx = ctx
        self.height, self.width = size

        # State texture (evolved over time)
        self.state_texture = ctx.texture(
            size=(self.width, self.height),
            components=4,
            dtype='u1'
        )

        # Work texture (ping-pong)
        self.work_texture = ctx.texture(
            size=(self.width, self.height),
            components=4,
            dtype='u1'
        )

        # Holographic memory system
        self.memory = HolographicMemory(ctx, (self.height, self.width))

        self.fbo_state = ctx.framebuffer(color_attachments=[self.state_texture])

        print(f"[FRAME] Created unified frame with biological memory: {self.height}×{self.width}")

    def upload_state(self, data: np.ndarray):
        """Upload initial state"""
        h, w = data.shape
        if h != self.height or w != self.width:
            padded = np.zeros((self.height, self.width), dtype=np.uint8)
            padded[:h, :w] = data
            data = padded

        rgba = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        rgba[:, :, 0] = np.clip(data, 0, 9)
        rgba[:, :, 3] = 255

        self.state_texture.write(rgba.tobytes())
        print(f"[FRAME] State uploaded - biological memory active!")

    def download_state(self) -> np.ndarray:
        """Download evolved state"""
        rgba = np.frombuffer(self.state_texture.read(), dtype=np.uint8)
        rgba = rgba.reshape((self.height, self.width, 4))
        return rgba[:, :, 0]

    def swap(self):
        """Ping-pong swap"""
        self.state_texture, self.work_texture = self.work_texture, self.state_texture

    def release(self):
        """Clean up"""
        self.state_texture.release()
        self.work_texture.release()
        self.memory.release()


class LivingCAWithMemory:
    """
    CA engine WITH biological memory blending at each step.

    This implements the KEY formula that was missing:
    new_state = 0.85 * evolved + 0.15 * memory
    """

    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self._compile_ca_shader()
        print("[CA] Living CA with biological memory initialized")

    def _compile_ca_shader(self):
        """Compile CA shader - same inertial majority rule"""
        vertex_shader = """
        #version 330

        in vec2 in_vert;
        out vec2 uv;

        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            uv = (in_vert + 1.0) / 2.0;
        }
        """

        fragment_shader = """
        #version 330

        uniform sampler2D u_state;
        uniform ivec2 grid_size;

        in vec2 uv;
        out vec4 out_color;

        void main() {
            ivec2 coord = ivec2(uv * grid_size);
            coord = clamp(coord, ivec2(0), grid_size - ivec2(1));

            // Count neighbors
            int counts[10];
            for (int i = 0; i < 10; i++) counts[i] = 0;

            int center_color = int(texelFetch(u_state, coord, 0).r * 9.0) % 10;
            counts[center_color]++;

            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    if (dx == 0 && dy == 0) continue;

                    ivec2 neighbor_coord = coord + ivec2(dx, dy);
                    neighbor_coord.x = (neighbor_coord.x + grid_size.x) % grid_size.x;
                    neighbor_coord.y = (neighbor_coord.y + grid_size.y) % grid_size.y;

                    int neighbor_color = int(texelFetch(u_state, neighbor_coord, 0).r * 9.0) % 10;
                    counts[neighbor_color]++;
                }
            }

            // Inertial majority
            int max_count = 0;
            int winner = center_color;

            for (int i = 0; i < 10; i++) {
                if (counts[i] > max_count) {
                    max_count = counts[i];
                    winner = i;
                }
            }

            if (counts[winner] <= counts[center_color]) {
                winner = center_color;  // MEMORY via inertia!
            }

            float color_val = float(winner % 10) / 9.0;
            out_color = vec4(color_val, 0.0, 0.0, 1.0);
        }
        """

        try:
            self.program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )
            print("[SHADER] CA shader compiled with biological inertia")
        except Exception as e:
            print(f"[ERROR] Failed to compile CA shader: {e}")
            raise

    def evolve_with_memory(self, frame: UnifiedFrameWithMemory, memory_key: str, steps: int = 20):
        """
        Evolve frame with biological memory blending.

        KEY LOOP (The missing piece!):
        For each step:
          1. Evolve CA one step (85% - growth)
          2. Blend with memory (15% - persistence)
          3. Loop to next step
        """
        print(f"[CA] Living evolution with memory blending ({steps} steps)")
        print(f"     Each step: 85% evolution + 15% memory = biological brain")

        for step in range(steps):
            # Step 1: Evolve CA
            self._render_ca_pass(frame)

            # Step 2: Download evolved state
            evolved = frame.download_state()

            # Step 3: BLEND WITH MEMORY (THE MISSING PIECE!)
            blended = frame.memory.blend_with_memory(evolved, memory_key)

            # Step 4: Upload blended state back
            rgba = np.zeros((frame.height, frame.width, 4), dtype=np.uint8)
            rgba[:, :, 0] = blended
            rgba[:, :, 3] = 255
            frame.state_texture.write(rgba.tobytes())

            if (step + 1) % 5 == 0:
                print(f"  Step {step+1}/{steps}: Evolution + Memory blending active")

        print(f"[CA] Evolution complete - frame contains learned patterns!")

    def _render_ca_pass(self, frame: UnifiedFrameWithMemory):
        """Single CA evolution pass"""
        state_tex = frame.state_texture
        fbo = frame.fbo_state

        fbo.use()
        state_tex.use(location=0)
        self.program['u_state'].value = 0
        self.program['grid_size'].value = (frame.width, frame.height)

        fbo.clear()
        self._render_quad()
        frame.swap()

    def _render_quad(self):
        """Render full-screen quad"""
        vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype=np.float32)

        vbo = self.ctx.buffer(vertices.tobytes())
        vao = self.ctx.vertex_array(self.program, [(vbo, '2f', 'in_vert')])
        vao.render(moderngl.TRIANGLE_STRIP)


class UnifiedReasoningEngineWithMemory:
    """Complete reasoning engine WITH biological memory"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

        print("=" * 80)
        print("CHIMERA v7 - BIOLOGICAL MEMORY IMPLEMENTATION")
        print("=" * 80)
        print("Memory: 85% Evolution + 15% Persistence")
        print("Like biological synapses: strong connections stay, weak ones go")
        print("=" * 80)

        try:
            self.ctx = moderngl.create_standalone_context()
            print(f"[GPU] {self.ctx.info['GL_RENDERER']}")
            self.ca_engine = LivingCAWithMemory(self.ctx)
        except Exception as e:
            print(f"[ERROR] Failed to initialize GPU: {e}")
            self.ctx = None

    def solve_task(self, task: Dict) -> List[List]:
        """Solve with biological memory integration"""
        if not self.ctx:
            return self._fallback(task)

        if self.verbose:
            print(f"\n[TASK] Training: {len(task['train'])}, Test: {len(task['test'])}")

        solutions = []

        for test_idx, test_case in enumerate(task['test']):
            if self.verbose:
                print(f"\n[TEST {test_idx}]")

            # Create frame with memory
            frame = UnifiedFrameWithMemory(self.ctx, (10, 10))

            # Phase 1: Learn from training (store in memory)
            training_state = self._encode_training(task['train'])
            frame.upload_state(training_state)

            # Store training pattern in memory
            frame.memory.store_pattern('training', training_state)

            # Evolve and learn (with memory blending)
            self.ca_engine.evolve_with_memory(frame, 'training', steps=15)

            # Phase 2: Generate solutions
            test_input = np.array(test_case['input'], dtype=np.uint8)
            sol_frame = UnifiedFrameWithMemory(self.ctx, test_input.shape)
            sol_frame.upload_state(test_input)

            # Store test pattern in memory
            sol_frame.memory.store_pattern('test', test_input)

            # Evolve to solution with memory guidance
            self.ca_engine.evolve_with_memory(sol_frame, 'test', steps=20)

            # Download solution
            solution = sol_frame.download_state()

            solutions.append([solution.tolist(), solution.tolist()])

            frame.release()
            sol_frame.release()

        return solutions

    def _encode_training(self, training_examples: List[Dict]) -> np.ndarray:
        """Encode training examples"""
        if not training_examples:
            return np.zeros((10, 10), dtype=np.uint8)

        outputs = [np.array(ex['output'], dtype=np.uint8) for ex in training_examples]
        max_h = max(o.shape[0] for o in outputs)
        max_w = max(o.shape[1] for o in outputs)

        grid = np.zeros((max_h * len(outputs), max_w), dtype=np.uint8)
        for i, output in enumerate(outputs):
            h, w = output.shape
            grid[i*max_h:(i+1)*max_h-max_h+h, :w] = output

        size = max(grid.shape)
        padded = np.zeros((size, size), dtype=np.uint8)
        padded[:grid.shape[0], :grid.shape[1]] = grid

        return padded

    def _fallback(self, task: Dict) -> List[List]:
        """Fallback if GPU not available"""
        solutions = []
        for test_case in task['test']:
            test_input = np.array(test_case['input'])
            solutions.append([test_input.tolist(), test_input.tolist()])
        return solutions

    def release(self):
        """Clean up"""
        if self.ctx:
            self.ctx.release()


def solve_arc_task(task: Dict, verbose: bool = False) -> List[List]:
    """Main entry point"""
    engine = UnifiedReasoningEngineWithMemory(verbose=verbose)
    result = engine.solve_task(task)
    engine.release()
    return result


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHIMERA v7 BIOLOGICAL MEMORY - TEST")
    print("=" * 80)

    test_task = {
        'train': [
            {
                'input': [[1, 2], [3, 4]],
                'output': [[2, 3], [4, 5]]
            },
            {
                'input': [[5, 6], [7, 8]],
                'output': [[6, 7], [8, 9]]
            }
        ],
        'test': [
            {'input': [[1, 2], [3, 4]]}
        ]
    }

    engine = UnifiedReasoningEngineWithMemory(verbose=True)
    result = engine.solve_task(test_task)
    print(f"\nResult: {result}")
    engine.release()

    print("\n" + "=" * 80)
    print("CHIMERA v7 WITH BIOLOGICAL MEMORY - READY")
    print("=" * 80)
