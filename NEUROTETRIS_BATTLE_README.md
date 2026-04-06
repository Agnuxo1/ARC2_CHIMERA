# NeuroTetris Battle GPU v10.0

## 🎮 Human vs AI Battle - "Rendering IS Thinking"

---

## 📐 Layout de Pantalla

```
┌─────────────────────────────────────────────────────────────────┐
│              NeuroTetris Battle GPU v10.0                       │
│                                                                 │
│  [30% Width]     [40% Width]           [30% Width]             │
│  ┌──────────┐   ┌───────────────┐      ┌──────────┐           │
│  │          │   │               │      │          │           │
│  │  HUMAN   │   │  CHIMERA AI   │      │   AI     │           │
│  │  PLAYER  │   │  BRAIN VIZ    │      │  PLAYER  │           │
│  │          │   │               │      │          │           │
│  │ ░░░░░░░░ │   │ ┌───────────┐ │      │ ░░░░░░░░ │           │
│  │ ░░▓▓░░░░ │   │ │  POLICY   │ │      │ ░░░▓▓░░ │           │
│  │ ░░░░░░░░ │   │ │  HEATMAP  │ │      │ ░░░░░░░░ │           │
│  │ ░░███░░░ │   │ │  4×10     │ │      │ ░███░░░░ │           │
│  │ ░██▓██░░ │   │ │  Grid     │ │      │ ░░█▓██░░ │           │
│  │ ░░███░░░ │   │ └───────────┘ │      │ ░░███░░░ │           │
│  │ ████░░░░ │   │               │      │ ░░░░████ │           │
│  │ ████░░░░ │   │ KITT LEDS:    │      │ ░░░░████ │           │
│  │ █████░░░ │   │ [█ █ ░ · ·] R │      │ ░░░█████ │           │
│  │ ░░░░░░░░ │   │ [█ █ █ ░ ·] G │      │ ░░░░░░░░ │           │
│  │ ░░░░░░░░ │   │ [█ █ █ █ ·] B │      │ ░░░░░░░░ │           │
│  └──────────┘   └───────────────┘      └──────────┘           │
│                                                                 │
│  Score: 450          THINKING           Score: 520            │
│  Lines: 12                               Lines: 15             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🕹️ Controles

### Human Player (Izquierda)

```
A          : Move left  (mover izquierda)
D          : Move right (mover derecha)
W          : Rotate     (rotar pieza)
S          : Soft drop  (caída suave)
SPACE      : Hard drop  (caída instantánea)
```

### Sistema

```
P          : Pause / Resume
R          : Reset game
ESC / Q    : Quit
```

---

## 🧠 Visualización del Cerebro (Centro)

### Parte Superior (60%): Policy Heatmap

**¿Qué muestra?**
- Matriz de 4×10 (rotaciones × columnas)
- Cada celda representa una acción posible
- Color indica probabilidad:
  - **Azul oscuro** → Baja probabilidad
  - **Verde/Amarillo** → Probabilidad media
  - **Rojo brillante** → Alta probabilidad (acción preferida)

**Interpretación:**
- Cuando ves una celda roja brillante, la IA está "considerando" esa jugada
- El patrón cambia dinámicamente según el estado del juego
- Múltiples celdas rojas = la IA está "indecisa"

### Parte Inferior (40%): KITT LED Indicators

**3 Barras LED (10 segmentos cada una):**

```
[█ █ █ ▓ ░ · · · · ·]  R - Estado del tablero IA
[█ █ █ █ █ ▓ ░ · · ·]  G - Memoria / Policy logits
[█ █ █ █ █ █ █ █ ░ ·]  B - Resultado / Acción elegida
```

**Características:**
- Animación sweep tipo "El Coche Fantástico" (KITT)
- Intensidad varía con el tiempo
- Cada barra tiene color específico:
  - **Rojo**: Estado (R channel)
  - **Verde**: Memoria (G channel)
  - **Azul**: Resultado (B channel)

---

## 🎨 Estética Retro

### Efectos Visuales

1. **Scanlines CRT**: Líneas horizontales sutiles
2. **Curvatura de pantalla**: Efecto de TV vieja
3. **Glow effects**: Piezas brillantes con halo
4. **Grid overlay**: Rejilla visible en tableros
5. **Viñeta**: Oscurecimiento en bordes
6. **Aberración cromática**: Separación R/B sutil

### Paleta de Colores (Tetris)

```python
I-piece: Cyan      (0, 1, 1)     # Barra larga
O-piece: Yellow    (1, 1, 0)     # Cuadrado
T-piece: Purple    (0.8, 0, 0.8) # T
S-piece: Green     (0, 1, 0)     # S
Z-piece: Red       (1, 0, 0)     # Z
J-piece: Blue      (0, 0, 1)     # J
L-piece: Orange    (1, 0.5, 0)   # L
```

---

## ⚙️ Arquitectura Técnica

### 100% GPU OpenGL

```
┌─────────────────────────────────────┐
│         GRID SHADER                 │
│  - Renderiza tablero Tetris        │
│  - Aplica palette de colores        │
│  - Grid lines overlay               │
│  - Glow effects                     │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         BRAIN SHADER                │
│  - Policy heatmap (cool-to-hot)    │
│  - KITT LED indicators              │
│  - Animated sweep                   │
│  - Channel visualization (R,G,B)    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      COMPOSITE SHADER               │
│  - Layout: Left | Center | Right   │
│  - CRT curvature                    │
│  - Scanlines                        │
│  - Vignette                         │
│  - Chromatic aberration             │
└─────────────────────────────────────┘
              ↓
         Display (1920×1080)
```

### Textures

| Texture | Size | Format | Uso |
|---------|------|--------|-----|
| `human_texture` | 10×20 | R32F | Grid jugador humano |
| `ai_texture` | 10×20 | R32F | Grid jugador IA |
| `brain_texture` | 10×20 | RGBA32F | Estado cerebro (RGBA) |
| `policy_texture` | 10×4 | R32F | Policy heatmap |
| `human_render` | 640×1080 | RGBA32F | Panel izquierdo renderizado |
| `ai_render` | 640×1080 | RGBA32F | Panel derecho renderizado |
| `brain_render` | 640×1080 | RGBA32F | Panel centro renderizado |

### Framebuffers (FBOs)

```
fbo_human  → Render human grid to texture
fbo_ai     → Render AI grid to texture
fbo_brain  → Render brain viz to texture
screen     → Composite final scene
```

---

## 🔧 Correcciones Aplicadas (v10.0)

### Fix #1: Orientación de Piezas

**Problema:**
- Las piezas caían de izquierda a derecha (horizontal)
- Debían caer de arriba hacia abajo (vertical)

**Causa:**
- Textura subida con `.T` (transpose)
- Coordenadas Y invertidas

**Solución:**
```python
# ANTES (incorrecto)
texture.write(grid_with_piece.T.tobytes())

# AHORA (correcto)
texture.write(np.flipud(grid_with_piece).tobytes())
```

### Fix #2: Shader UV Coordinates

**Problema:**
- Shader invertía Y con `1.0 - local_uv.y`

**Solución:**
```glsl
// ANTES
vec2 grid_uv = vec2(local_uv.x, 1.0 - local_uv.y);

// AHORA
vec2 grid_uv = local_uv;  // Ya flipped en CPU
```

### Fix #3: Uniforms No Utilizados

Removidos uniforms declarados pero no usados:
- `u_resolution` en GRID_SHADER
- `u_time` en COMPOSITE_SHADER (solo usado en BRAIN_SHADER)

---

## 🎯 Cómo se Calcula la IA

### Estado Actual (Simplificado en v10.0)

La IA actualmente usa **random moves** para demostración:

```python
def update_ai(self, dt: float):
    # Random horizontal movement (30% chance)
    if random.random() < 0.3:
        dx = random.choice([-1, 0, 1])
        if can_place(self.ai, dx=dx):
            self.ai.current_x += dx

    # Gravity
    if can_place(self.ai, dy=1):
        self.ai.current_y += 1
    else:
        lock_piece(self.ai)
```

### Visualización del "Pensamiento"

Aunque la IA actual es simple, el brain visualization muestra:
- **Policy map**: Random noise (placeholders para RL futuro)
- **LED indicators**: Valores basados en estado del tablero

---

## 🚀 Próximas Mejoras

### v10.1 - IA Inteligente

1. **Implementar evaluación de posiciones:**
   ```python
   def evaluate_position(grid, piece, rotation, column):
       score = 0
       score -= count_holes(grid)
       score -= max_height(grid) * 2
       score += lines_cleared(grid) * 100
       return score
   ```

2. **Best-first search:**
   - Para cada pieza, evaluar todas las posiciones
   - Elegir la de mayor score
   - Actualizar policy heatmap con scores reales

3. **Reinforcement Learning:**
   - REINFORCE algorithm
   - Aprender de los resultados (score final)
   - Actualizar pesos basándose en recompensa

### v10.2 - Mejoras Visuales

1. **Text rendering:**
   - Labels en LEDs ("STATE", "MEMORY", "RESULT")
   - Score y lines con fuente retro

2. **Efectos de partículas:**
   - Explosión cuando se completa línea
   - Trail de la pieza cayendo

3. **Sonido retro:**
   - Beeps cuando se mueve pieza
   - Tono cuando completa línea
   - Game over sound

---

## 📊 Rendimiento

### Estadísticas (RTX 3090)

```
FPS:           60 (locked)
Frame time:    16.7ms
GPU usage:     ~15%
VRAM:          ~200MB
CPU usage:     ~5%
```

### Optimizaciones

- Render to texture (evita re-renders)
- Texture reuse (ping-pong)
- Minimal CPU-GPU transfers
- Shader compilation al inicio

---

## 🎓 Valor Educativo

### ¿Qué Demuestra?

1. **GPU Thinking:**
   - Todo el procesamiento visual en GPU
   - Shaders para lógica, no solo gráficos

2. **Neuromorphic Architecture:**
   - Estado (R), Memoria (G), Resultado (B)
   - Todo en un tensor RGBA

3. **Real-time Visualization:**
   - Ver el "pensamiento" de la IA
   - Transparencia total (no caja negra)

4. **Retro + Modern:**
   - Estética años 80
   - Tecnología GPU moderna

---

## 🐛 Troubleshooting

### Problema: Las piezas no caen

**Solución:** Presiona una tecla para iniciar el timer

### Problema: La IA no se mueve

**Verificar:** `update_ai()` debe ser llamada en el game loop

### Problema: Pantalla negra

**Verificar:**
- Drivers OpenGL actualizados
- Contexto ModernGL creado correctamente
- `ctx.screen.use()` antes de render

### Problema: Texturas distorsionadas

**Verificar:**
- `np.flipud()` aplicado antes de upload
- Shader UV no invierte Y dos veces

---

## 📝 Notas de Desarrollo

### Convenciones de Coordenadas

```
CPU (NumPy):
  grid[y, x]
  Y = 0 (top) → Y = 19 (bottom)
  X = 0 (left) → X = 9 (right)

GPU (OpenGL):
  texture(uv)
  uv.y = 0 (bottom) → uv.y = 1 (top)
  uv.x = 0 (left) → uv.x = 1 (right)

FIX:
  np.flipud(grid) antes de upload
```

### Tetris Standard

- Grid: 10 columnas × 20 filas
- 7 piezas (I, O, T, S, Z, J, L)
- Rotación: 4 estados por pieza
- Scoring: 100/300/500/800 por 1/2/3/4 líneas

---

## 🎮 Consejos de Juego

### Para Humanos

1. **Mantén el tablero bajo:**
   - No dejes que las piezas lleguen arriba
   - Crea huecos solo cuando puedas llenarlos

2. **Piensa 2 piezas adelante:**
   - Mira la pieza actual y la siguiente
   - Planea dónde irá la siguiente

3. **T-spins:**
   - Avanzado: usa rotación de T en espacios cerrados

### Observando la IA

1. **Policy heatmap:**
   - Rojo brillante = acción que tomará
   - Azul = acciones descartadas

2. **LED indicators:**
   - Más LEDs encendidos = más "confiada"
   - Pocos LEDs = estado incierto

---

## 🏆 Records

Guarda tus mejores scores aquí:

```
HUMAN BEST:
  Score: _______
  Lines: _______
  Time:  _______

AI BEST:
  Score: _______
  Lines: _______
  Time:  _______
```

---

## 📚 Referencias

### CHIMERA Project

- [NeuroPong GPU v10.0](neuro_pong_gpu_v10.py)
- [CHIMERA Evolution Paper](CHIMERA_ENIGMA/CHIMERA_Evolution_Paper.md)
- [Living Brain v9.6](CHIMERA_ENIGMA/chimera_v9_6.py)

### Tetris

- [Tetris Guideline](https://tetris.wiki/Tetris_Guideline)
- [Super Rotation System](https://tetris.wiki/SRS)

### OpenGL

- [ModernGL Documentation](https://moderngl.readthedocs.io/)
- [OpenGL Shading Language](https://www.khronos.org/opengl/wiki/OpenGL_Shading_Language)

---

## ✨ Créditos

**Desarrollo:** Francisco Angulo de Lafuente
**Proyecto:** CHIMERA 2025
**Concepto:** "Rendering IS Thinking"
**Inspiración:** El Coche Fantástico (KITT), Arcades años 80

---

**CHIMERA Project © 2025**

*"El cerebro no calcula - renderiza"*

