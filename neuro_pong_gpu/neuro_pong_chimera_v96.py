#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroPong (CHIMERA v9.6 Educational Arcade Demo)
=================================================

Overview
--------
This is an educational, *real-time* visualization of CHIMERA's neuromorphic
frame applied to a simple, classic arcade-style game: **Pong**.

- The game world is mapped to a **grid** (default 30×30). Each grid cell is
  an integer in [0..9] (like ARC). We'll call this the *symbolic state*.
- The CHIMERA "brain" is a single **RGBA tensor** (H×W×4):
    R = current state (normalized from symbols 0..9 to [0,1])
    G = evolving memory (exponential moving average of the result, i.e., how the
        brain consolidates short-term experience)
    B = result field (the instantaneous "prediction/intent" computed by the
        operators; here it encodes the predicted target row for the AI paddle)
    A = confidence (here we keep it simple and set it to 1; you can change it)

- Every frame we:
    1) Encode the current game grid into **R**.
    2) Compute **features** using a 3×3 neighborhood operator (edges, majority).
    3) Compute a **result** field **B** by predicting where the ball will intersect
       the AI paddle column; we paint a Gaussian band at that target row.
    4) Evolve the **memory G** with G <- (1-α)·G + α·B.
    5) Use the (argmax over rows) of B or G to drive the AI paddle in real time.

You can **see all four channels** updating live, side-by-side with the game.
Everything is pure CPU/NumPy + Pygame for portability; if you want, you can
replace the CPU feature/result passes with ModernGL shaders (the APIs are aligned).

Controls
--------
- Up/Down arrows: Move the HUMAN paddle (left).
- A / Z:        Adjust evolution alpha (α) down/up by 0.01 (clamped to [0,1]).
- Space:        Pause/Resume.
- F:            Toggle AI source (use B vs use G to aim the AI paddle).
- R:            Reset ball and paddles.
- Esc/Q:        Quit.

Requirements
------------
- Python 3.8+
- numpy
- pygame

Run
---
    pip install pygame numpy
    python neuro_pong_chimera_v96.py

Author
------
CHIMERA Project, 2025
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass
from typing import Tuple, List

import numpy as np

try:
    import pygame
except Exception as e:
    print("This demo requires 'pygame'. Install it with: pip install pygame")
    raise


# ===========================================================
# Utility: color palette (10 ARC-like symbols -> RGB)
# ===========================================================

def palette_rgb() -> List[Tuple[int, int, int]]:
    """
    A high-contrast palette for symbols 0..9. Index equals symbol value.
    You can change this freely; the "logic" runs on the integer grid anyway.
    """
    return [
        (0, 0, 0),        # 0 black (empty/background)
        (255, 255, 255),  # 1 white (walls)
        (255, 0, 0),      # 2 red (ball)
        (0, 255, 0),      # 3 green
        (0, 0, 255),      # 4 blue
        (255, 255, 0),    # 5 yellow
        (255, 0, 255),    # 6 magenta (left paddle)
        (0, 255, 255),    # 7 cyan    (right paddle / AI)
        (255, 128, 0),    # 8 orange
        (128, 0, 255),    # 9 violet
    ]


# ===========================================================
# Game model: grid-based Pong
# ===========================================================

@dataclass
class GameConfig:
    grid_h: int = 30
    grid_w: int = 30
    paddle_len: int = 5
    ball_speed: float = 10.0  # cells per second
    ai_column: int = 28       # x-index of the AI paddle (right)
    human_column: int = 1     # x-index of the human paddle (left)
    wall_symbol: int = 1
    ball_symbol: int = 2
    human_symbol: int = 6
    ai_symbol: int = 7


@dataclass
class GameState:
    ball_y: float
    ball_x: float
    vy: float
    vx: float
    human_center_y: float
    ai_center_y: float
    score_human: int = 0
    score_ai: int = 0


def init_game_state(cfg: GameConfig) -> GameState:
    """Create an initial state with the ball in the center moving toward the human."""
    return GameState(
        ball_y=cfg.grid_h / 2,
        ball_x=cfg.grid_w / 2,
        vy=0.7,  # normalized direction; actual speed comes from cfg.ball_speed
        vx=-0.7,
        human_center_y=cfg.grid_h / 2,
        ai_center_y=cfg.grid_h / 2
    )


def step_game(cfg: GameConfig, st: GameState, dt: float) -> None:
    """
    Advance the game physics by dt seconds. Handles wall/paddle bounces.
    Updates the state in-place.
    """
    # Move ball
    st.ball_y += st.vy * cfg.ball_speed * dt
    st.ball_x += st.vx * cfg.ball_speed * dt

    # Bounce on top/bottom walls
    if st.ball_y < 1:
        st.ball_y = 1
        st.vy = abs(st.vy)
    if st.ball_y > cfg.grid_h - 2:
        st.ball_y = cfg.grid_h - 2
        st.vy = -abs(st.vy)

    # Check paddles
    # Human paddle at x = human_column
    if int(round(st.ball_x)) == cfg.human_column + 1:
        if abs(st.ball_y - st.human_center_y) <= (cfg.paddle_len / 2):
            st.vx = abs(st.vx)  # bounce to the right
            # Add spin based on impact offset
            st.vy += (st.ball_y - st.human_center_y) * 0.05

    # AI paddle at x = ai_column
    if int(round(st.ball_x)) == cfg.ai_column - 1:
        if abs(st.ball_y - st.ai_center_y) <= (cfg.paddle_len / 2):
            st.vx = -abs(st.vx)  # bounce to the left
            st.vy += (st.ball_y - st.ai_center_y) * 0.05

    # Score if ball crosses left/right borders
    if st.ball_x < 0:
        st.score_ai += 1
        reset_ball(cfg, st, direction=1)
    elif st.ball_x > cfg.grid_w - 1:
        st.score_human += 1
        reset_ball(cfg, st, direction=-1)


def reset_ball(cfg: GameConfig, st: GameState, direction: int = 1) -> None:
    """Center the ball and launch it towards 'direction': +1 (right) or -1 (left)."""
    st.ball_y = cfg.grid_h / 2
    st.ball_x = cfg.grid_w / 2
    st.vy = (np.random.rand() * 2.0 - 1.0) * 0.9
    st.vx = direction * (0.6 + np.random.rand() * 0.4)


def encode_grid(cfg: GameConfig, st: GameState) -> np.ndarray:
    """
    Convert the current game state into a H×W integer grid (symbols 0..9).
    Walls=1, Ball=2, Human=6, AI=7, everything else 0.
    """
    g = np.zeros((cfg.grid_h, cfg.grid_w), dtype=np.int32)
    # Walls (top/bottom)
    g[0, :] = cfg.wall_symbol
    g[-1, :] = cfg.wall_symbol

    # Paddles (clamped)
    def draw_paddle(center_y: float, x: int, sym: int):
        half = cfg.paddle_len // 2
        y0 = int(round(center_y)) - half
        y1 = y0 + cfg.paddle_len
        y0 = max(1, y0)
        y1 = min(cfg.grid_h - 1, y1)
        g[y0:y1, x] = sym

    draw_paddle(st.human_center_y, cfg.human_column, cfg.human_symbol)
    draw_paddle(st.ai_center_y, cfg.ai_column, cfg.ai_symbol)

    # Ball
    by = int(round(st.ball_y))
    bx = int(round(st.ball_x))
    by = np.clip(by, 1, cfg.grid_h - 2)
    bx = np.clip(bx, 1, cfg.grid_w - 2)
    g[by, bx] = cfg.ball_symbol

    return g


# ===========================================================
# CHIMERA brain (CPU implementation for education)
# ===========================================================

@dataclass
class BrainConfig:
    alpha: float = 0.20  # evolution step for memory G
    gauss_sigma: float = 1.25  # width of the result band painted at target row


@dataclass
class BrainState:
    R: np.ndarray  # current normalized state [0,1]
    G: np.ndarray  # evolving memory
    B: np.ndarray  # instantaneous result
    A: np.ndarray  # confidence [0,1]
    features: np.ndarray  # (H,W,3): [same_color_ratio, edge_flag, majority_color_norm]


def init_brain(cfg: GameConfig, bc: BrainConfig) -> BrainState:
    """Initialize the neuromorphic frame and feature buffer."""
    H, W = cfg.grid_h, cfg.grid_w
    zeros = np.zeros((H, W), dtype=np.float32)
    feats = np.zeros((H, W, 3), dtype=np.float32)
    return BrainState(R=zeros.copy(), G=zeros.copy(), B=zeros.copy(),
                      A=np.ones((H, W), dtype=np.float32), features=feats)


def grid_to_R(grid: np.ndarray) -> np.ndarray:
    """Convert integer grid [0..9] to normalized float [0,1] for channel R."""
    return grid.astype(np.float32) / 9.0


def features_3x3(R: np.ndarray) -> np.ndarray:
    """
    Compute simple 3×3 features:
      - same_color_ratio: fraction of neighbors equal to center
      - edge_flag: 1 if < 5 same neighbors, else 0
      - majority_color_norm: argmax color in 3×3, normalized to [0,1] by /9
    R is assumed to encode the color index in [0,1] (i.e., real index / 9).
    """
    H, W = R.shape
    same = np.zeros((H, W), dtype=np.float32)
    counts = np.zeros((H, W, 10), dtype=np.int32)

    # Pad edges by clamping
    Rp = np.pad(R, 1, mode="edge")

    # Iterate 8 neighbors
    neigh = [(-1, -1), (0, -1), (1, -1),
             (-1,  0),          (1,  0),
             (-1,  1), (0,  1), (1,  1)]
    center_idx = np.rint(R * 9.0).astype(np.int32)
    for dy, dx in neigh:
        N = Rp[1+dy:H+1+dy, 1+dx:W+1+dx]
        Ni = np.rint(N * 9.0).astype(np.int32)
        same += (Ni == center_idx).astype(np.float32)
        for c in range(10):
            counts[:, :, c] += (Ni == c).astype(np.int32)

    same_ratio = same / 8.0
    edge_flag = (same < 5).astype(np.float32)
    majority = np.argmax(counts, axis=2).astype(np.float32) / 9.0

    feats = np.stack([same_ratio, edge_flag, majority], axis=2)
    return feats


def predict_ball_intercept(cfg: GameConfig, st: GameState) -> Tuple[int, float]:
    """
    Predict the row (y) where the ball will intersect the AI paddle column.
    We simulate straight motion with vertical wall bounces only.
    Returns (target_row_int, time_to_hit_seconds).
    """
    y = st.ball_y
    x = st.ball_x
    vy = st.vy * cfg.ball_speed
    vx = st.vx * cfg.ball_speed

    if vx <= 0:
        # Ball going left: predict where it would intersect the *left* border,
        # but we still use it as an intent signal (AI can reposition proactively).
        target_x = cfg.human_column
    else:
        target_x = cfg.ai_column

    # If horizontal speed is near zero, avoid division by zero
    if abs(vx) < 1e-5:
        return int(round(y)), 9999.0

    dt_hit = abs((target_x - x) / vx)
    # Reflect vertical motion on walls during dt_hit
    y_future = y
    vy_sign = 1.0 if vy >= 0 else -1.0
    vy_abs = abs(vy)
    t = 0.0
    # Compute bounces analytically by unfolding the interval [1, H-2]
    Hmin = 1.0
    Hmax = cfg.grid_h - 2.0
    yf = y + vy * dt_hit
    # Mirror across walls to simulate bounces
    span = Hmax - Hmin
    if span <= 0:
        return int(round(y)), dt_hit
    # Map to a "triangle wave" between [Hmin, Hmax]
    # Shift to 0..span
    y0 = y - Hmin
    yf0 = y0 + vy * dt_hit
    k = math.floor(yf0 / span)
    r = yf0 - k * span
    if k % 2 == 0:
        y_future = Hmin + r
    else:
        y_future = Hmax - r

    return int(round(np.clip(y_future, 1, cfg.grid_h - 2))), max(0.0, dt_hit)


def paint_result_band(B: np.ndarray, target_row: int, sigma: float) -> None:
    """
    Paint a horizontal Gaussian band on B centered at target_row.
    B is modified in-place. Values are clamped to [0,1].
    """
    H, W = B.shape
    ys = np.arange(H).reshape(H, 1)
    band = np.exp(-0.5 * ((ys - target_row) / max(1e-3, sigma)) ** 2)
    # Normalize to max 1
    band = band / np.max(band)
    # Fill entire columns (intent across the width)
    B[:] = np.clip(band, 0.0, 1.0)


def neuromorphic_step(brain: BrainState, alpha: float) -> None:
    """
    Evolve the memory G with the current result B:
        G <- (1-α)·G + α·B
    """
    brain.G = (1.0 - alpha) * brain.G + alpha * brain.B


def decide_ai_from_field(field: np.ndarray) -> int:
    """
    Choose the row (argmax) from a vertical preference field. If multiple maxima
    exist, pick the median of their indices.
    """
    col = np.max(field, axis=1)  # reduce across X
    maxv = np.max(col)
    rows = np.where(np.abs(col - maxv) < 1e-6)[0]
    if rows.size == 0:
        return field.shape[0] // 2
    return int(rows[len(rows) // 2])


# ===========================================================
# Visualization with Pygame
# ===========================================================

@dataclass
class ViewConfig:
    cell_pix: int = 20
    gap: int = 8
    font_size: int = 18


def grid_to_surface(grid: np.ndarray, cell_pix: int, pal: List[Tuple[int, int, int]]) -> "pygame.Surface":
    """
    Render an integer grid as colored rectangles using the provided palette.
    """
    H, W = grid.shape
    surf = pygame.Surface((W * cell_pix, H * cell_pix))
    for y in range(H):
        for x in range(W):
            color = pal[int(grid[y, x]) % 10]
            pygame.draw.rect(surf, color, (x * cell_pix, y * cell_pix, cell_pix, cell_pix))
    return surf


def field_to_surface(field: np.ndarray, cell_pix: int) -> "pygame.Surface":
    """
    Render a scalar field in [0,1] as a grayscale surface.
    """
    H, W = field.shape
    data = np.clip((field * 255.0).astype(np.uint8), 0, 255)
    # Expand to RGB
    rgb = np.repeat(data[:, :, None], 3, axis=2)
    surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
    return pygame.transform.scale(surf, (W * cell_pix, H * cell_pix))


def triple_to_surface(feats: np.ndarray, cell_pix: int) -> "pygame.Surface":
    """
    Render 3-channel features (same_ratio, edge_flag, majority_norm) into RGB.
    Each channel is assumed to be in [0,1].
    """
    H, W, C = feats.shape
    assert C == 3
    data = np.clip((feats * 255.0).astype(np.uint8), 0, 255)
    surf = pygame.surfarray.make_surface(np.transpose(data, (1, 0, 2)))
    return pygame.transform.scale(surf, (W * cell_pix, H * cell_pix))


# ===========================================================
# Main App
# ===========================================================

def run():
    # --- configurations ---
    cfg = GameConfig()
    bc = BrainConfig(alpha=0.20, gauss_sigma=1.25)
    vc = ViewConfig(cell_pix=20, gap=8, font_size=18)
    pal = palette_rgb()

    # --- init pygame ---
    pygame.init()
    pygame.font.init()
    font = pygame.font.SysFont("consolas", vc.font_size)

    grid_w_pix = cfg.grid_w * vc.cell_pix
    grid_h_pix = cfg.grid_h * vc.cell_pix
    gap = vc.gap

    # Layout: [Game] [R] [G] on first row; [B] [A] [Features] on second row
    width = grid_w_pix * 3 + gap * 4
    height = grid_h_pix * 2 + gap * 3 + 40  # +40 for HUD
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("NeuroPong — CHIMERA v9.6 Brain Viewer (Educational)")

    # --- init game and brain ---
    st = init_game_state(cfg)
    brain = init_brain(cfg, bc)
    paused = False
    use_memory_for_ai = False  # False -> use B, True -> use G

    clock = pygame.time.Clock()
    last_time = time.time()

    while True:
        # --- events ---
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit(0)
                elif ev.key == pygame.K_SPACE:
                    paused = not paused
                elif ev.key == pygame.K_r:
                    st = init_game_state(cfg)
                elif ev.key == pygame.K_f:
                    use_memory_for_ai = not use_memory_for_ai
                elif ev.key == pygame.K_a:
                    bc.alpha = max(0.0, bc.alpha - 0.01)
                elif ev.key == pygame.K_z:
                    bc.alpha = min(1.0, bc.alpha + 0.01)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            st.human_center_y = max(1, st.human_center_y - 0.5)
        if keys[pygame.K_DOWN]:
            st.human_center_y = min(cfg.grid_h - 2, st.human_center_y + 0.5)

        # --- timing ---
        now = time.time()
        dt = now - last_time
        last_time = now
        dt = max(0.0, min(dt, 0.05))  # clamp

        # --- physics ---
        if not paused:
            step_game(cfg, st, dt)

        # --- encode grid into R ---
        grid = encode_grid(cfg, st)
        brain.R = grid_to_R(grid)

        # --- compute features ---
        brain.features = features_3x3(brain.R)

        # --- compute result B: predict intercept and paint band ---
        target_row, t_hit = predict_ball_intercept(cfg, st)
        brain.B.fill(0.0)
        paint_result_band(brain.B, target_row, bc.gauss_sigma)

        # --- evolve memory G ---
        neuromorphic_step(brain, bc.alpha)

        # --- AI paddle control ---
        field = brain.G if use_memory_for_ai else brain.B
        ai_target = decide_ai_from_field(field)
        # Move AI paddle smoothly towards target
        if not paused:
            if ai_target < st.ai_center_y - 0.25:
                st.ai_center_y -= 0.5
            elif ai_target > st.ai_center_y + 0.25:
                st.ai_center_y += 0.5

        # --- draw ---
        screen.fill((25, 25, 28))

        # First row
        x = gap
        y = gap + 40  # reserve top bar

        surf_game = grid_to_surface(grid, vc.cell_pix, pal)
        screen.blit(surf_game, (x, y)); x += grid_w_pix + gap

        surf_R = field_to_surface(brain.R, vc.cell_pix)
        screen.blit(surf_R, (x, y)); x += grid_w_pix + gap

        surf_G = field_to_surface(brain.G, vc.cell_pix)
        screen.blit(surf_G, (x, y))

        # Second row
        x = gap
        y += grid_h_pix + gap

        surf_B = field_to_surface(brain.B, vc.cell_pix)
        screen.blit(surf_B, (x, y)); x += grid_w_pix + gap

        surf_A = field_to_surface(brain.A, vc.cell_pix)
        screen.blit(surf_A, (x, y)); x += grid_w_pix + gap

        surf_feats = triple_to_surface(brain.features, vc.cell_pix)
        screen.blit(surf_feats, (x, y))

        # --- HUD ---
        hud_text = (
            f"NeuroPong — CHIMERA v9.6 | "
            f"Score H:{st.score_human}  AI:{st.score_ai} | "
            f"alpha={bc.alpha:.2f} | "
            f"{'AI uses G (memory)' if use_memory_for_ai else 'AI uses B (instant result)'} | "
            f"Controls: ↑/↓ move, A/Z alpha, F toggle G/B, Space pause, R reset, Q/Esc quit"
        )
        text_surf = font.render(hud_text, True, (220, 220, 220))
        screen.blit(text_surf, (gap, 8))

        # Labels for panels
        labels = ["GAME (grid)", "R: state", "G: memory", "B: result", "A: confidence", "features 3×3 (RGB)"]
        lx = [gap, gap + grid_w_pix + gap, gap + 2*(grid_w_pix + gap),
              gap, gap + grid_w_pix + gap, gap + 2*(grid_w_pix + gap)]
        ly = [40 + gap - 20, 40 + gap - 20, 40 + gap - 20,
              40 + gap + grid_h_pix + gap - 20,
              40 + gap + grid_h_pix + gap - 20,
              40 + gap + grid_h_pix + gap - 20]
        for i, lab in enumerate(labels):
            ls = font.render(lab, True, (180, 180, 180))
            screen.blit(ls, (lx[i], ly[i]))

        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    run()
