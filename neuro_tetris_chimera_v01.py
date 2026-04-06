#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroTetris (CHIMERA v9.6 Educational Demo)
===========================================

Summary
-------
An educational, real-time CHIMERA "brain viewer" that learns to play a
grid-based **Tetris** while exposing the neuromorphic frame:

- **State (R):** board occupancy (symbols 0..9 normalized to [0,1]).
- **Memory (G):** policy logits over (rotation, column).
- **Result (B):** softmax policy π over (rotation, column).
- **Confidence (A):** advantage/baseline signal (learning weight).

This first version prioritizes clarity and portability:
- Uses **pygame** to create the window and gather input.
- Uses **ModernGL** (OpenGL 3.3) to render the game and visualize the brain.
- The Tetris physics and the REINFORCE update are implemented in **NumPy** for
  readability. (A full "compute-via-shaders" version can replace those later
  without changing the viewer.)

Controls
--------
- LEFT / RIGHT : Move piece
- UP          : Rotate piece (clockwise)
- DOWN        : Soft drop
- SPACE       : Hard drop
- A           : Toggle AI control (on/off)
- B           : Toggle using G (logits) vs B (softmax) to pick actions
- L / K       : Increase / Decrease learning rate
- R           : Reset game
- P           : Pause / Resume
- ESC / Q     : Quit

Requirements
------------
    pip install pygame moderngl numpy

Run
---
    python neuro_tetris_chimera_v01.py

Author
------
CHIMERA Project, 2025
"""

from __future__ import annotations

import math
import sys
import time
import random
from dataclasses import dataclass
from typing import Tuple, List, Dict

import numpy as np

# --- Window & GL ---
import pygame
from pygame.locals import DOUBLEBUF, OPENGL

import moderngl


# ==============================
# TETROMINO DEFINITIONS (CPU)
# ==============================

TETROMINOES: Dict[str, List[np.ndarray]] = {}

def _rotations(shape: List[str]) -> List[np.ndarray]:
    grid = np.array([[1 if c == 'X' else 0 for c in row] for row in shape], dtype=np.int32)
    rots = []
    g = grid.copy()
    for k in range(4):
        rots.append(g.copy())
        g = np.rot90(g, k=-1)  # clockwise
    # Make 4x4 masks
    fixed = []
    for r in rots:
        h, w = r.shape
        pad = np.zeros((4, 4), dtype=np.int32)
        pad[:h, :w] = r
        fixed.append(pad)
    return fixed

# Standard 7 tetrominoes
TETROMINOES['I'] = _rotations([
    "XXXX",
])
TETROMINOES['O'] = _rotations([
    "XX",
    "XX",
])
TETROMINOES['T'] = _rotations([
    ".X.",
    "XXX",
])
TETROMINOES['S'] = _rotations([
    ".XX",
    "XX.",
])
TETROMINOES['Z'] = _rotations([
    "XX.",
    ".XX",
])
TETROMINOES['J'] = _rotations([
    "X..",
    "XXX",
])
TETROMINOES['L'] = _rotations([
    "..X",
    "XXX",
])

TETROMINO_KEYS = list(TETROMINOES.keys())


# ==============================
# GAME MODEL (CPU)
# ==============================

@dataclass
class GameConfig:
    W: int = 10
    H: int = 20
    fall_delay: float = 0.6  # seconds per cell
    empty_symbol: int = 0


@dataclass
class GameState:
    board: np.ndarray  # HxW int32 (0 empty, 1..7 filled colors)
    bag: List[str]
    cur_piece: str
    cur_rot: int
    cur_x: int
    cur_y: int
    score: int
    lines: int
    game_over: bool


def new_bag() -> List[str]:
    b = TETROMINO_KEYS.copy()
    random.shuffle(b)
    return b


def init_game(cfg: GameConfig) -> GameState:
    board = np.zeros((cfg.H, cfg.W), dtype=np.int32)
    bag = new_bag()
    cur_piece = bag.pop()
    st = GameState(
        board=board,
        bag=bag,
        cur_piece=cur_piece,
        cur_rot=0,
        cur_x=cfg.W // 2 - 2,
        cur_y=0,
        score=0,
        lines=0,
        game_over=False,
    )
    if not can_place(cfg, st, st.cur_x, st.cur_y, st.cur_rot):
        st.game_over = True
    return st


def can_place(cfg: GameConfig, st: GameState, x: int, y: int, rot: int) -> bool:
    mask = TETROMINOES[st.cur_piece][rot]
    h, w = mask.shape
    for yy in range(h):
        for xx in range(w):
            if mask[yy, xx] == 0:
                continue
            bx = x + xx
            by = y + yy
            if bx < 0 or bx >= cfg.W or by < 0 or by >= cfg.H:
                return False
            if st.board[by, bx] != 0:
                return False
    return True


def place_piece(cfg: GameConfig, st: GameState) -> Tuple[int, bool]:
    mask = TETROMINOES[st.cur_piece][st.cur_rot]
    h, w = mask.shape
    for yy in range(h):
        for xx in range(w):
            if mask[yy, xx] == 0:
                continue
            bx = st.cur_x + xx
            by = st.cur_y + yy
            if 0 <= bx < cfg.W and 0 <= by < cfg.H:
                st.board[by, bx] = (1 + TETROMINO_KEYS.index(st.cur_piece))  # 1..7

    lines_before = st.lines
    full = np.where(np.all(st.board != 0, axis=1))[0]
    if full.size > 0:
        st.board = np.vstack([np.zeros((full.size, cfg.W), dtype=np.int32),
                              st.board[np.setdiff1d(np.arange(cfg.H), full)]])
        st.lines += int(full.size)
        st.score += [0, 100, 300, 500, 800][min(4, int(full.size))]

    if not st.bag:
        st.bag = new_bag()
    st.cur_piece = st.bag.pop()
    st.cur_rot = 0
    st.cur_x = cfg.W // 2 - 2
    st.cur_y = 0
    if not can_place(cfg, st, st.cur_x, st.cur_y, st.cur_rot):
        st.game_over = True
        return (st.lines - lines_before), False

    return (st.lines - lines_before), True


def hard_drop(cfg: GameConfig, st: GameState) -> int:
    dist = 0
    while can_place(cfg, st, st.cur_x, st.cur_y + 1, st.cur_rot):
        st.cur_y += 1
        dist += 1
    lines, ok = place_piece(cfg, st)
    return dist


def step_gravity(cfg: GameConfig, st: GameState) -> bool:
    if st.game_over:
        return False
    if can_place(cfg, st, st.cur_x, st.cur_y + 1, st.cur_rot):
        st.cur_y += 1
        return True
    _, ok = place_piece(cfg, st)
    return ok


# ==============================
# CHIMERA BRAIN (CPU math + GL viz)
# ==============================

@dataclass
class BrainConfig:
    alpha: float = 0.2
    lr: float = 0.1
    use_memory_for_action: bool = False
    baseline_decay: float = 0.99


@dataclass
class BrainState:
    R: np.ndarray
    G: np.ndarray
    B: np.ndarray
    A: np.ndarray
    baseline: float


def init_brain(cfg: GameConfig, bc: BrainConfig) -> BrainState:
    R = np.zeros((cfg.H, cfg.W), dtype=np.float32)
    G = np.zeros((4, cfg.W), dtype=np.float32)
    B = np.zeros_like(G)
    A = np.ones_like(G)
    return BrainState(R=R, G=G, B=B, A=A, baseline=0.0)


def board_to_R(cfg: GameConfig, board: np.ndarray, st: GameState) -> np.ndarray:
    R = (board.astype(np.float32) / 9.0).copy()
    mask = TETROMINOES[st.cur_piece][st.cur_rot]
    h, w = mask.shape
    for yy in range(h):
        for xx in range(w):
            if mask[yy, xx] == 0:
                continue
            by = st.cur_y + yy
            bx = st.cur_x + xx
            if 0 <= by < cfg.H and 0 <= bx < cfg.W:
                R[by, bx] = 2.0 / 9.0
    return R


def evaluate_columns(cfg: GameConfig, st: GameState, rot: int) -> List[int]:
    mask = TETROMINOES[st.cur_piece][rot]
    cols = []
    for c in range(-3, cfg.W):
        x = c
        y = 0
        if not can_place(cfg, st, x, y, rot):
            continue
        while can_place(cfg, st, x, y + 1, rot):
            y += 1
        # Ensure some visible lock
        visible = False
        h, w = mask.shape
        for yy in range(h):
            for xx in range(w):
                if mask[yy, xx] == 0: continue
                by = y + yy; bx = x + xx
                if 0 <= by < cfg.H and 0 <= bx < cfg.W:
                    visible = True; break
            if visible: break
        if visible:
            cols.append(x)
    mapped = [min(max(0, c), cfg.W - 1) for c in cols]
    return sorted(list(set(mapped)))


def rollout_features_and_reward(cfg: GameConfig, board: np.ndarray) -> Tuple[int, int, int, int]:
    H, W = cfg.H, cfg.W
    cleared = int(np.sum(np.all(board != 0, axis=1)))
    holes = 0
    heights = np.zeros(W, dtype=np.int32)
    for x in range(W):
        col = board[:, x]
        filled = np.where(col != 0)[0]
        if filled.size == 0:
            heights[x] = 0
        else:
            heights[x] = H - filled[0]
            holes += int(np.sum(col[filled[0]:] == 0))
    bump = int(np.sum(np.abs(np.diff(heights))))
    return cleared, holes, int(heights.max()), bump


def simulate_place(cfg: GameConfig, st: GameState, rot: int, col: int) -> np.ndarray:
    mask = TETROMINOES[st.cur_piece][rot]
    x = col
    y = 0
    if not can_place(cfg, st, x, y, rot):
        return None
    while can_place(cfg, st, x, y + 1, rot):
        y += 1
    newb = st.board.copy()
    h, w = mask.shape
    for yy in range(h):
        for xx in range(w):
            if mask[yy, xx] == 0: continue
            by = y + yy; bx = x + xx
            if 0 <= by < cfg.H and 0 <= bx < cfg.W:
                newb[by, bx] = (1 + TETROMINO_KEYS.index(st.cur_piece))
    full = np.where(np.all(newb != 0, axis=1))[0]
    if full.size > 0:
        newb = np.vstack([np.zeros((full.size, cfg.W), dtype=np.int32),
                          newb[np.setdiff1d(np.arange(cfg.H), full)]])
    return newb


def update_policy(brain: BrainState, legal_mask: np.ndarray, reward: float, bc: BrainConfig) -> None:
    brain.baseline = bc.baseline_decay * brain.baseline + (1.0 - bc.baseline_decay) * reward
    adv = reward - brain.baseline
    chosen = (legal_mask == 2).astype(np.float32)
    legal = (legal_mask > 0).astype(np.float32)
    pi = brain.B * legal
    s = np.sum(pi)
    if s > 0:
        pi = pi / s
    brain.G += bc.lr * adv * (chosen - pi)
    brain.A[:] = adv


def softmax_over_legal(logits: np.ndarray, legal_mask: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    legal = (legal_mask > 0).astype(np.float32)
    x = logits.copy() / max(1e-6, temperature)
    x = x - np.max(x)
    e = np.exp(x) * legal
    s = np.sum(e)
    if s <= 0:
        return legal / max(1.0, np.sum(legal))
    return e / s


def choose_action(brain: BrainState, legal_mask: np.ndarray, bc: BrainConfig) -> Tuple[int, int]:
    legal = (legal_mask > 0).astype(np.float32)
    if np.sum(legal) == 0:
        return 0, brain.B.shape[1] // 2
    if bc.use_memory_for_action:
        masked = brain.G.copy()
        masked[legal == 0] = -1e9
        idx = np.argmax(masked)
        r = idx // brain.G.shape[1]
        c = idx % brain.G.shape[1]
        return int(r), int(c)
    else:
        flat = brain.B.flatten()
        probs = flat * legal.flatten()
        s = probs.sum()
        if s <= 0:
            probs = legal.flatten() / max(1.0, legal.sum())
        else:
            probs = probs / s
        idx = np.random.choice(np.arange(flat.size), p=probs)
        r = idx // brain.B.shape[1]; c = idx % brain.B.shape[1]
        return int(r), int(c)


# ==============================
# GL RENDERING (ModernGL)
# ==============================

VERT_SRC = """
#version 330
in vec2 in_pos;
out vec2 uv;
void main(){
    uv = (in_pos + 1.0) * 0.5;
    gl_Position = vec4(in_pos, 0.0, 1.0);
}
"""

FRAG_BOARD = """
#version 330
uniform sampler2D u_board;   // R: board state normalized 0..1 (H x W)
uniform ivec2 u_grid;        // (H, W)
in vec2 uv;
out vec4 color;

vec3 palette(int v){
    if(v==0) return vec3(0.05,0.05,0.06);
    if(v==1) return vec3(1.0,1.0,1.0);
    if(v==2) return vec3(1.0,0.2,0.2);
    if(v==3) return vec3(0.2,1.0,0.2);
    if(v==4) return vec3(0.2,0.6,1.0);
    if(v==5) return vec3(1.0,1.0,0.2);
    if(v==6) return vec3(1.0,0.2,1.0);
    if(v==7) return vec3(0.2,1.0,1.0);
    if(v==8) return vec3(1.0,0.6,0.2);
    return vec3(0.6,0.2,1.0);
}

void main(){
    ivec2 coord = ivec2( floor(vec2(u_grid.y, u_grid.x) * uv) );
    coord = clamp(coord, ivec2(0), u_grid - ivec2(1));
    float r = texelFetch(u_board, coord, 0).r;
    int vi = int(round(r * 9.0));
    vec3 c = palette(vi);
    color = vec4(c, 1.0);
}
"""

FRAG_HEAT = """
#version 330
uniform sampler2D u_heat;    // 4xW heatmap (R channel used)
uniform ivec2 u_size;        // (4, W)
in vec2 uv;
out vec4 color;

void main(){
    ivec2 coord = ivec2( floor(vec2(u_size.y, u_size.x) * uv) );
    coord = clamp(coord, ivec2(0), u_size - ivec2(1));
    float v = texelFetch(u_heat, coord, 0).r;
    color = vec4(vec3(v), 1.0);
}
"""


class GLViz:
    def __init__(self, W: int, H: int, title: str="NeuroTetris — CHIMERA v9.6"):
        pygame.init()
        pygame.display.set_caption(title)
        self.screen_w = 1100
        self.screen_h = 700
        pygame.display.set_mode((self.screen_w, self.screen_h), DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)

        self.ctx = moderngl.create_context()
        self.ctx.viewport = (0, 0, self.screen_w, self.screen_h)

        verts = np.array([-1.0, -1.0,  1.0, -1.0, -1.0, 1.0,  1.0, 1.0], dtype='f4')
        self.vbo = self.ctx.buffer(verts.tobytes())
        self.prog_board = self.ctx.program(vertex_shader=VERT_SRC, fragment_shader=FRAG_BOARD)
        self.prog_heat = self.ctx.program(vertex_shader=VERT_SRC, fragment_shader=FRAG_HEAT)
        self.vao_board = self.ctx.simple_vertex_array(self.prog_board, self.vbo, 'in_pos')
        self.vao_heat = self.ctx.simple_vertex_array(self.prog_heat, self.vbo, 'in_pos')

        self.grid_h = H
        self.grid_w = W
        self.board_tex = self.ctx.texture((W, H), 1, dtype='f4')
        self.board_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)

        self.heat_tex_G = self.ctx.texture((W, 4), 1, dtype='f4')
        self.heat_tex_G.filter = (moderngl.NEAREST, moderngl.NEAREST)

        self.heat_tex_B = self.ctx.texture((W, 4), 1, dtype='f4')
        self.heat_tex_B.filter = (moderngl.NEAREST, moderngl.NEAREST)

        self.heat_tex_A = self.ctx.texture((W, 4), 1, dtype='f4')
        self.heat_tex_A.filter = (moderngl.NEAREST, moderngl.NEAREST)

    def upload_board(self, R_norm: np.ndarray) -> None:
        self.board_tex.write(R_norm.astype('f4').tobytes())

    def upload_heat(self, tex, heat: np.ndarray) -> None:
        tex.write(np.ascontiguousarray(heat[::-1, :].astype('f4')).tobytes())

    def draw(self, brain_lines: List[str]) -> None:
        self.ctx.clear(0.06, 0.06, 0.08, 1.0)

        # Layout
        bw = int(self.screen_w * 0.5)
        bh = int(self.screen_h * 0.95)
        bx = 10
        by = (self.screen_h - bh) // 2

        rw = int(self.screen_w * 0.4)
        rh = int((self.screen_h * 0.9) // 3)
        rx = self.screen_w - rw - 10
        ry_top = (self.screen_h - (3*rh + 20)) // 2

        # Board
        self.ctx.viewport = (bx, by, bw, bh)
        self.board_tex.use(location=0)
        self.prog_board['u_board'].value = 0
        self.prog_board['u_grid'].value = (self.grid_h, self.grid_w)
        self.vao_board.render(moderngl.TRIANGLE_STRIP)

        # G
        self.ctx.viewport = (rx, ry_top, rw, rh)
        self.heat_tex_G.use(location=0)
        self.prog_heat['u_heat'].value = 0
        self.prog_heat['u_size'].value = (4, self.grid_w)
        self.vao_heat.render(moderngl.TRIANGLE_STRIP)

        # B
        self.ctx.viewport = (rx, ry_top + rh + 10, rw, rh)
        self.heat_tex_B.use(location=0)
        self.vao_heat.render(moderngl.TRIANGLE_STRIP)

        # A
        self.ctx.viewport = (rx, ry_top + 2*(rh + 10), rw, rh)
        self.heat_tex_A.use(location=0)
        self.vao_heat.render(moderngl.TRIANGLE_STRIP)

        # Reset viewport and draw HUD text with pygame
        self.ctx.viewport = (0, 0, self.screen_w, self.screen_h)
        surf = pygame.display.get_surface()
        y = 8
        for s in brain_lines:
            text = self.font.render(s, True, (220, 220, 220))
            surf.blit(text, (10, y))
            y += 20

        pygame.display.flip()
        self.clock.tick(60)


def main():
    cfg = GameConfig()
    bc = BrainConfig()
    st = init_game(cfg)
    brain = init_brain(cfg, bc)

    gl = GLViz(cfg.W, cfg.H, title="NeuroTetris — CHIMERA v9.6 (Educational)")

    paused = False
    ai_on = False
    last_fall = time.time()

    while True:
        # Events
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit(0)
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit(0)
                elif ev.key == pygame.K_p:
                    paused = not paused
                elif ev.key == pygame.K_r:
                    st = init_game(cfg); brain = init_brain(cfg, bc)
                elif ev.key == pygame.K_a:
                    ai_on = not ai_on
                elif ev.key == pygame.K_b:
                    bc.use_memory_for_action = not bc.use_memory_for_action
                elif ev.key == pygame.K_l:
                    bc.lr = min(1.0, bc.lr * 1.25)
                elif ev.key == pygame.K_k:
                    bc.lr = max(1e-4, bc.lr / 1.25)
                elif ev.key == pygame.K_SPACE and not ai_on:
                    hard_drop(cfg, st)
                elif ev.key == pygame.K_UP and not ai_on:
                    nr = (st.cur_rot + 1) % 4
                    if can_place(cfg, st, st.cur_x, st.cur_y, nr):
                        st.cur_rot = nr

        keys = pygame.key.get_pressed()
        if not ai_on and not paused and not st.game_over:
            if keys[pygame.K_LEFT] and can_place(cfg, st, st.cur_x - 1, st.cur_y, st.cur_rot):
                st.cur_x -= 1
            if keys[pygame.K_RIGHT] and can_place(cfg, st, st.cur_x + 1, st.cur_y, st.cur_rot):
                st.cur_x += 1
            if keys[pygame.K_DOWN] and can_place(cfg, st, st.cur_x, st.cur_y + 1, st.cur_rot):
                st.cur_y += 1

        # Gravity
        now = time.time()
        if not paused and not ai_on and (now - last_fall) >= cfg.fall_delay and not st.game_over:
            if not step_gravity(cfg, st):
                pass
            last_fall = now

        # Encode R
        brain.R = board_to_R(cfg, st.board, st)

        # Legal mask 4xW
        legal_mask = np.zeros((4, cfg.W), dtype=np.int32)
        for r in range(4):
            cols = evaluate_columns(cfg, st, r)
            for c in cols:
                legal_mask[r, c] = 1

        # B = softmax over legal
        brain.B = softmax_over_legal(brain.G, legal_mask, temperature=1.0).reshape(4, cfg.W)

        # AI
        if ai_on and not st.game_over and not paused:
            rot, col = choose_action(brain, legal_mask, bc)
            legal_upd = legal_mask.copy()
            legal_upd[rot, col] = 2

            st.cur_rot = rot
            st.cur_x = int(np.clip(col, -3, cfg.W-1))
            hard_drop(cfg, st)

            cleared, holes, maxh, bump = rollout_features_and_reward(cfg, st.board)
            reward = cleared*1.0 - 0.5*holes - 0.05*maxh - 0.02*bump

            update_policy(brain, legal_upd, reward, bc)
            last_fall = now

        # Upload to GL
        gl.upload_board(brain.R)
        def norm01(x):
            if np.allclose(x, 0.0):
                return np.zeros_like(x)
            m, M = np.min(x), np.max(x)
            if abs(M - m) < 1e-6:
                return np.zeros_like(x)
            return (x - m) / (M - m)
        gl.upload_heat(gl.heat_tex_G, norm01(brain.G))
        gl.upload_heat(gl.heat_tex_B, brain.B)
        gl.upload_heat(gl.heat_tex_A, np.clip((brain.A - np.min(brain.A)) / (np.ptp(brain.A) + 1e-6), 0, 1))

        # Draw
        hud = [
            f"NeuroTetris — CHIMERA v9.6 | Score: {st.score} | Lines: {st.lines} | {'GAME OVER' if st.game_over else ''}",
            f"AI: {'ON' if ai_on else 'OFF'} | Source: {'G (logits)' if bc.use_memory_for_action else 'B (softmax)'} | LR: {bc.lr:.3f} | α={bc.alpha:.2f}",
            "Controls: ←/→ move, ↑ rotate, ↓ soft drop, SPACE hard drop, A toggle AI, B toggle source, L/K LR±, P pause, R reset, Q/Esc quit",
        ]
        gl.draw(hud)


if __name__ == "__main__":
    main()
