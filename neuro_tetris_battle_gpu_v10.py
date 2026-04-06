#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroTetris Battle GPU v10.0 - Human vs AI Battle
===================================================

CHIMERA Educational Demo - "Rendering IS Thinking"
--------------------------------------------------

Two-player Tetris battle:
- LEFT SIDE: Human player (you)
- RIGHT SIDE: AI player (CHIMERA brain)
- CENTER: Real-time brain visualization with KITT-style indicators

100% GPU OpenGL implementation showing the AI "thinking" visually.

Controls:
---------
HUMAN (Left):
  A/D        : Move piece left/right
  W          : Rotate piece
  S          : Soft drop
  SPACE      : Hard drop

AI (Right):
  Controlled by CHIMERA brain

System:
  P          : Pause/Resume
  R          : Reset game
  L/K        : Adjust AI learning rate
  ESC/Q      : Quit

Requirements:
-------------
  pip install moderngl pygame numpy

Author:
-------
CHIMERA Project, 2025 - Francisco Angulo de Lafuente
"""

import numpy as np
import moderngl
import pygame
from pygame.locals import *
import sys
import time
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    # Display
    window_width: int = 1920
    window_height: int = 1080

    # Grid (standard Tetris)
    grid_width: int = 10
    grid_height: int = 20

    # Game
    drop_speed: float = 1.0  # Seconds per row

    # Brain
    learning_rate: float = 0.1
    alpha: float = 0.2  # Memory evolution rate

    # Visual
    glow_intensity: float = 0.8
    scanline_intensity: float = 0.12
    crt_curvature: float = 0.015


# ============================================================================
# TETROMINO SHAPES
# ============================================================================

SHAPES = {
    'I': [[1,1,1,1]],
    'O': [[1,1],[1,1]],
    'T': [[0,1,0],[1,1,1]],
    'S': [[0,1,1],[1,1,0]],
    'Z': [[1,1,0],[0,1,1]],
    'J': [[1,0,0],[1,1,1]],
    'L': [[0,0,1],[1,1,1]]
}

COLORS = {
    'I': (0, 1, 1),     # Cyan
    'O': (1, 1, 0),     # Yellow
    'T': (0.8, 0, 0.8), # Purple
    'S': (0, 1, 0),     # Green
    'Z': (1, 0, 0),     # Red
    'J': (0, 0, 1),     # Blue
    'L': (1, 0.5, 0)    # Orange
}


def rotate_shape(shape):
    """Rotate shape 90° clockwise."""
    return [list(row) for row in zip(*shape[::-1])]


# ============================================================================
# VERTEX SHADER
# ============================================================================

VERTEX_SHADER = """
#version 330

in vec2 in_vert;
out vec2 uv;

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    uv = (in_vert + 1.0) / 2.0;
}
"""


# ============================================================================
# TETRIS GRID SHADER
# ============================================================================

GRID_SHADER = """
#version 330

uniform sampler2D u_grid;
uniform float u_glow;
uniform vec2 u_offset;      // Position offset (0-1)
uniform vec2 u_size;        // Size (0-1)
uniform int u_grid_w;
uniform int u_grid_h;

in vec2 uv;
out vec4 fragColor;

vec3 palette(float v) {
    if (v < 0.1) return vec3(0.05, 0.05, 0.08);  // Empty
    if (v < 0.2) return vec3(0.0, 1.0, 1.0);     // Cyan
    if (v < 0.3) return vec3(1.0, 1.0, 0.0);     // Yellow
    if (v < 0.4) return vec3(0.8, 0.0, 0.8);     // Purple
    if (v < 0.5) return vec3(0.0, 1.0, 0.0);     // Green
    if (v < 0.6) return vec3(1.0, 0.0, 0.0);     // Red
    if (v < 0.7) return vec3(0.0, 0.0, 1.0);     // Blue
    return vec3(1.0, 0.5, 0.0);                  // Orange
}

void main() {
    // Transform UV to grid space
    vec2 local_uv = (uv - u_offset) / u_size;

    if (local_uv.x < 0.0 || local_uv.x > 1.0 ||
        local_uv.y < 0.0 || local_uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // Sample grid (Y already flipped in CPU)
    vec2 grid_uv = local_uv;
    float cell_value = texture(u_grid, grid_uv).r;

    vec3 color = palette(cell_value);

    // Grid lines
    vec2 grid_coord = local_uv * vec2(u_grid_w, u_grid_h);
    vec2 grid_fract = fract(grid_coord);
    float grid_line = step(0.95, max(grid_fract.x, grid_fract.y));
    color = mix(color, color * 1.5, grid_line * 0.2);

    // Glow
    if (cell_value > 0.1) {
        color *= (1.0 + u_glow * 0.3);
    }

    fragColor = vec4(color, 1.0);
}
"""


# ============================================================================
# BRAIN VISUALIZATION SHADER
# ============================================================================

BRAIN_SHADER = """
#version 330

uniform sampler2D u_brain;      // RGBA brain texture
uniform sampler2D u_policy;     // Policy heatmap (rotation × column)
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_glow;

in vec2 uv;
out vec4 fragColor;

// KITT-style LED indicator
float kitt_led(vec2 pos, float value, float y_offset) {
    float y_pos = 0.1 + y_offset;
    float bar_height = 0.02;

    if (abs(pos.y - y_pos) < bar_height) {
        // 10 LED segments
        for (int i = 0; i < 10; i++) {
            float seg_x = 0.05 + float(i) * 0.09;

            if (pos.x >= seg_x && pos.x <= seg_x + 0.07) {
                float threshold = float(i) / 10.0;
                if (value >= threshold) {
                    float intensity = 1.0 - (value - threshold) * 2.0;
                    intensity = clamp(intensity, 0.4, 1.0);

                    // Animated sweep
                    float sweep = fract(u_time * 0.3 + float(i) * 0.1);
                    intensity *= 0.8 + 0.2 * sweep;

                    return intensity;
                }
            }
        }
    }
    return 0.0;
}

// Policy heatmap visualization
vec3 heatmap_color(float value) {
    // Cool (blue) to hot (red) colormap
    if (value < 0.25) {
        return mix(vec3(0.0, 0.0, 0.5), vec3(0.0, 0.5, 1.0), value * 4.0);
    } else if (value < 0.5) {
        return mix(vec3(0.0, 0.5, 1.0), vec3(0.0, 1.0, 0.5), (value - 0.25) * 4.0);
    } else if (value < 0.75) {
        return mix(vec3(0.0, 1.0, 0.5), vec3(1.0, 1.0, 0.0), (value - 0.5) * 4.0);
    } else {
        return mix(vec3(1.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), (value - 0.75) * 4.0);
    }
}

void main() {
    vec4 brain = texture(u_brain, uv);

    // Channels visualization
    vec3 color = vec3(0.0);

    // Top half: Policy heatmap
    if (uv.y > 0.5) {
        vec2 policy_uv = vec2(uv.x, (uv.y - 0.5) * 2.0);
        float policy_val = texture(u_policy, policy_uv).r;
        color = heatmap_color(policy_val);

        // Grid overlay
        vec2 grid_coord = policy_uv * vec2(10.0, 4.0);
        vec2 grid_fract = fract(grid_coord);
        float grid_line = step(0.9, max(grid_fract.x, grid_fract.y));
        color *= 1.0 - grid_line * 0.3;
    }
    // Bottom half: KITT indicators + info
    else {
        // Background
        color = vec3(0.02, 0.02, 0.04);

        // LED indicators for R, G, B channels
        float led_r = kitt_led(uv, brain.r, 0.0);  // State
        float led_g = kitt_led(uv, brain.g, 0.08); // Memory
        float led_b = kitt_led(uv, brain.b, 0.16); // Result

        color += vec3(1.0, 0.1, 0.0) * led_r * 3.0;  // Red LEDs
        color += vec3(0.1, 1.0, 0.0) * led_g * 3.0;  // Green LEDs
        color += vec3(0.0, 0.3, 1.0) * led_b * 3.0;  // Blue LEDs

        // Labels area (simple bars)
        if (uv.y < 0.05) {
            color += vec3(0.3, 0.3, 0.4) * 0.5;
        }
    }

    // Glow effect
    color *= (1.0 + u_glow * 0.2);

    // Scanlines
    float scanline = sin(uv.y * u_resolution.y * 3.14159) * 0.5 + 0.5;
    color *= 1.0 - scanline * 0.1;

    fragColor = vec4(color, 1.0);
}
"""


# ============================================================================
# COMPOSITE SHADER (Final scene assembly)
# ============================================================================

COMPOSITE_SHADER = """
#version 330

uniform sampler2D u_left_grid;   // Human player
uniform sampler2D u_right_grid;  // AI player
uniform sampler2D u_brain_viz;   // Brain visualization
uniform vec2 u_resolution;
uniform float u_scanline;
uniform float u_curvature;

in vec2 uv;
out vec4 fragColor;

void main() {
    vec2 centered_uv = uv;

    // CRT curvature
    centered_uv = centered_uv * 2.0 - 1.0;
    centered_uv *= 1.0 + u_curvature * dot(centered_uv, centered_uv);
    centered_uv = (centered_uv + 1.0) / 2.0;

    // Out of bounds
    if (centered_uv.x < 0.0 || centered_uv.x > 1.0 ||
        centered_uv.y < 0.0 || centered_uv.y > 1.0) {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec3 color = vec3(0.0);

    // Layout: [Human 30%] [Brain 40%] [AI 30%]
    if (centered_uv.x < 0.3) {
        // Left: Human player
        vec2 local_uv = vec2(centered_uv.x / 0.3, centered_uv.y);
        color = texture(u_left_grid, local_uv).rgb;
    } else if (centered_uv.x < 0.7) {
        // Center: Brain visualization
        vec2 local_uv = vec2((centered_uv.x - 0.3) / 0.4, centered_uv.y);
        color = texture(u_brain_viz, local_uv).rgb;
    } else {
        // Right: AI player
        vec2 local_uv = vec2((centered_uv.x - 0.7) / 0.3, centered_uv.y);
        color = texture(u_right_grid, local_uv).rgb;
    }

    // Scanlines
    float scanline = sin(centered_uv.y * u_resolution.y * 3.14159);
    color *= 1.0 - u_scanline * (0.5 + 0.5 * scanline);

    // Vignette
    float vignette = 1.0 - 0.4 * length(centered_uv - 0.5);
    color *= vignette;

    // Chromatic aberration
    color.r *= 1.03;
    color.b *= 0.97;

    fragColor = vec4(color, 1.0);
}
"""


# ============================================================================
# GAME STATE
# ============================================================================

@dataclass
class TetrisPlayer:
    """State for one Tetris player."""
    grid: np.ndarray  # H×W grid
    current_piece: str
    current_rotation: int
    current_x: int
    current_y: int
    score: int
    lines: int
    game_over: bool
    drop_timer: float
    piece_bag: List[str]


def create_player(cfg: Config) -> TetrisPlayer:
    """Create new player state."""
    return TetrisPlayer(
        grid=np.zeros((cfg.grid_height, cfg.grid_width), dtype=np.float32),
        current_piece='T',
        current_rotation=0,
        current_x=cfg.grid_width // 2 - 1,
        current_y=0,
        score=0,
        lines=0,
        game_over=False,
        drop_timer=0.0,
        piece_bag=list(SHAPES.keys())
    )


def get_rotated_shape(piece: str, rotation: int):
    """Get shape rotated N times."""
    shape = SHAPES[piece]
    for _ in range(rotation % 4):
        shape = rotate_shape(shape)
    return shape


def can_place(player: TetrisPlayer, dx: int = 0, dy: int = 0, drot: int = 0) -> bool:
    """Check if piece can be placed at offset."""
    shape = get_rotated_shape(player.current_piece, player.current_rotation + drot)

    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                new_x = player.current_x + x + dx
                new_y = player.current_y + y + dy

                if (new_x < 0 or new_x >= player.grid.shape[1] or
                    new_y >= player.grid.shape[0] or
                    (new_y >= 0 and player.grid[new_y, new_x] > 0)):
                    return False
    return True


def lock_piece(player: TetrisPlayer):
    """Lock current piece to grid."""
    shape = get_rotated_shape(player.current_piece, player.current_rotation)
    piece_color = list(SHAPES.keys()).index(player.current_piece) / 7.0 + 0.15

    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                grid_y = player.current_y + y
                grid_x = player.current_x + x
                if 0 <= grid_y < player.grid.shape[0]:
                    player.grid[grid_y, grid_x] = piece_color

    # Clear lines
    lines_cleared = 0
    y = player.grid.shape[0] - 1
    while y >= 0:
        if np.all(player.grid[y] > 0):
            player.grid[1:y+1] = player.grid[0:y]
            player.grid[0] = 0
            lines_cleared += 1
        else:
            y -= 1

    if lines_cleared > 0:
        player.lines += lines_cleared
        player.score += [0, 100, 300, 500, 800][min(lines_cleared, 4)]

    # Spawn new piece
    if not player.piece_bag:
        player.piece_bag = list(SHAPES.keys())
        random.shuffle(player.piece_bag)

    player.current_piece = player.piece_bag.pop()
    player.current_rotation = 0
    player.current_x = player.grid.shape[1] // 2 - 1
    player.current_y = 0

    if not can_place(player):
        player.game_over = True


# ============================================================================
# GPU ENGINE
# ============================================================================

class NeuroTetrisBattle:
    """100% GPU Tetris battle: Human vs AI."""

    def __init__(self, config: Config):
        self.cfg = config

        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.window_width, config.window_height),
            DOUBLEBUF | OPENGL
        )
        pygame.display.set_caption("NeuroTetris Battle GPU v10.0")

        # OpenGL context
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        print("=" * 80)
        print("NeuroTetris Battle GPU v10.0")
        print("=" * 80)
        print(f"[GPU] {self.ctx.info['GL_RENDERER']}")
        print("[LAYOUT] Human (Left) | Brain (Center) | AI (Right)")
        print("=" * 80)

        # Compile shaders
        self._compile_shaders()

        # Create textures
        self._create_textures()

        # Setup rendering
        self._setup_rendering()

        # Game state
        self.human = create_player(config)
        self.ai = create_player(config)

        # Brain state (simple policy for now)
        self.brain_state = np.random.rand(config.grid_height, config.grid_width).astype(np.float32)
        self.policy_map = np.random.rand(4, config.grid_width).astype(np.float32)

        self.paused = False
        self.clock = pygame.time.Clock()
        self.start_time = time.time()

        print("[READY] Press any key to start!")
        print("=" * 80)

    def _compile_shaders(self):
        """Compile all shaders."""
        self.grid_program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=GRID_SHADER
        )

        self.brain_program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=BRAIN_SHADER
        )

        self.composite_program = self.ctx.program(
            vertex_shader=VERTEX_SHADER,
            fragment_shader=COMPOSITE_SHADER
        )

        print("[SHADERS] Compiled: grid, brain, composite")

    def _create_textures(self):
        """Create GPU textures."""
        gs = (self.cfg.grid_width, self.cfg.grid_height)

        # Player grids
        self.human_texture = self.ctx.texture(gs, 1, dtype='f4')
        self.ai_texture = self.ctx.texture(gs, 1, dtype='f4')

        # Brain textures
        self.brain_texture = self.ctx.texture(gs, 4, dtype='f4')
        self.policy_texture = self.ctx.texture((self.cfg.grid_width, 4), 1, dtype='f4')

        # Render targets
        self.human_render = self.ctx.texture((640, 1080), 4, dtype='f4')
        self.ai_render = self.ctx.texture((640, 1080), 4, dtype='f4')
        self.brain_render = self.ctx.texture((640, 1080), 4, dtype='f4')

        print("[TEXTURES] Created player grids and brain")

    def _setup_rendering(self):
        """Setup rendering pipeline."""
        vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices.tobytes())

        self.vao_grid = self.ctx.simple_vertex_array(
            self.grid_program, self.vbo, 'in_vert'
        )
        self.vao_brain = self.ctx.simple_vertex_array(
            self.brain_program, self.vbo, 'in_vert'
        )
        self.vao_composite = self.ctx.simple_vertex_array(
            self.composite_program, self.vbo, 'in_vert'
        )

        # FBOs
        self.fbo_human = self.ctx.framebuffer(color_attachments=[self.human_render])
        self.fbo_ai = self.ctx.framebuffer(color_attachments=[self.ai_render])
        self.fbo_brain = self.ctx.framebuffer(color_attachments=[self.brain_render])

    def update_human(self, dt: float):
        """Update human player."""
        if self.human.game_over or self.paused:
            return

        self.human.drop_timer += dt
        if self.human.drop_timer >= self.cfg.drop_speed:
            self.human.drop_timer = 0
            if can_place(self.human, dy=1):
                self.human.current_y += 1
            else:
                lock_piece(self.human)

    def update_ai(self, dt: float):
        """Update AI player (simple random for now)."""
        if self.ai.game_over or self.paused:
            return

        self.ai.drop_timer += dt
        if self.ai.drop_timer >= self.cfg.drop_speed * 0.8:  # AI slightly faster
            self.ai.drop_timer = 0

            # Simple AI: random move
            if random.random() < 0.3:
                dx = random.choice([-1, 0, 1])
                if can_place(self.ai, dx=dx):
                    self.ai.current_x += dx

            if can_place(self.ai, dy=1):
                self.ai.current_y += 1
            else:
                lock_piece(self.ai)

    def handle_input(self):
        """Handle user input."""
        keys = pygame.key.get_pressed()

        # Human controls
        if keys[K_a] and can_place(self.human, dx=-1):
            self.human.current_x -= 1
        if keys[K_d] and can_place(self.human, dx=1):
            self.human.current_x += 1
        if keys[K_w] and can_place(self.human, drot=1):
            self.human.current_rotation = (self.human.current_rotation + 1) % 4
        if keys[K_s]:
            if can_place(self.human, dy=1):
                self.human.current_y += 1

        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q:
                    return False
                elif event.key == K_p:
                    self.paused = not self.paused
                elif event.key == K_r:
                    self.human = create_player(self.cfg)
                    self.ai = create_player(self.cfg)
                elif event.key == K_SPACE:
                    # Hard drop
                    while can_place(self.human, dy=1):
                        self.human.current_y += 1
                    lock_piece(self.human)

        return True

    def render_grid(self, player: TetrisPlayer, fbo, texture):
        """Render a Tetris grid."""
        # Upload grid with current piece
        grid_with_piece = player.grid.copy()
        shape = get_rotated_shape(player.current_piece, player.current_rotation)
        piece_color = list(SHAPES.keys()).index(player.current_piece) / 7.0 + 0.15

        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = player.current_y + y
                    grid_x = player.current_x + x
                    if 0 <= grid_y < self.cfg.grid_height and 0 <= grid_x < self.cfg.grid_width:
                        grid_with_piece[grid_y, grid_x] = piece_color + 0.5  # Brighter for current

        # Upload grid (flip Y for OpenGL convention)
        texture.write(np.flipud(grid_with_piece).tobytes())

        # Render
        fbo.use()
        fbo.clear(0.0, 0.0, 0.0, 1.0)

        self.grid_program['u_grid'] = 0
        self.grid_program['u_glow'] = self.cfg.glow_intensity
        self.grid_program['u_offset'] = (0.1, 0.1)
        self.grid_program['u_size'] = (0.8, 0.8)
        self.grid_program['u_grid_w'] = self.cfg.grid_width
        self.grid_program['u_grid_h'] = self.cfg.grid_height

        texture.use(location=0)
        self.vao_grid.render(moderngl.TRIANGLE_STRIP)

    def render_brain(self):
        """Render brain visualization."""
        # Update brain texture (simple for now)
        brain_rgba = np.stack([
            self.brain_state,
            self.brain_state * 0.8,
            self.brain_state * 0.6,
            np.ones_like(self.brain_state)
        ], axis=-1).astype(np.float32)

        self.brain_texture.write(np.flipud(brain_rgba).tobytes())
        self.policy_texture.write(np.flipud(self.policy_map).tobytes())

        # Render
        self.fbo_brain.use()
        self.fbo_brain.clear(0.0, 0.0, 0.0, 1.0)

        self.brain_program['u_brain'] = 0
        self.brain_program['u_policy'] = 1
        self.brain_program['u_resolution'] = (640, 1080)
        self.brain_program['u_time'] = float(time.time() - self.start_time)
        self.brain_program['u_glow'] = self.cfg.glow_intensity

        self.brain_texture.use(location=0)
        self.policy_texture.use(location=1)

        self.vao_brain.render(moderngl.TRIANGLE_STRIP)

    def render_composite(self):
        """Render final composite scene."""
        self.ctx.screen.use()
        self.ctx.screen.clear(0.0, 0.0, 0.0, 1.0)

        self.composite_program['u_left_grid'] = 0
        self.composite_program['u_right_grid'] = 1
        self.composite_program['u_brain_viz'] = 2
        self.composite_program['u_resolution'] = (self.cfg.window_width, self.cfg.window_height)
        self.composite_program['u_scanline'] = self.cfg.scanline_intensity
        self.composite_program['u_curvature'] = self.cfg.crt_curvature

        self.human_render.use(location=0)
        self.ai_render.use(location=1)
        self.brain_render.use(location=2)

        self.vao_composite.render(moderngl.TRIANGLE_STRIP)

    def run(self):
        """Main game loop."""
        running = True

        while running:
            dt = self.clock.tick(60) / 1000.0

            running = self.handle_input()
            if not running:
                break

            # Update
            self.update_human(dt)
            self.update_ai(dt)

            # Render
            self.render_grid(self.human, self.fbo_human, self.human_texture)
            self.render_grid(self.ai, self.fbo_ai, self.ai_texture)
            self.render_brain()
            self.render_composite()

            pygame.display.flip()

            # Title update
            pygame.display.set_caption(
                f"NeuroTetris Battle | Human: {self.human.score} | AI: {self.ai.score}"
            )

        self.cleanup()

    def cleanup(self):
        """Release GPU resources."""
        print("\n[CLEANUP] Releasing GPU resources...")
        pygame.quit()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("NeuroTetris Battle GPU v10.0")
    print("'Rendering IS Thinking' - Human vs AI")
    print("=" * 80)

    config = Config()
    game = NeuroTetrisBattle(config)

    try:
        game.run()
    except KeyboardInterrupt:
        print("\n[EXIT] User interrupt")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nThanks for playing!")
        print("CHIMERA Project - 2025")
