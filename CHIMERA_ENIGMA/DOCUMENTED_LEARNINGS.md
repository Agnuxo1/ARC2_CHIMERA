# CHIMERA - Learnings with Official Documentation

**Actualizado**: 2025-10-28 después de estudiar documentación oficial de ARC AGI 2025

---

## 📚 Documentación Oficial Estudiada

1. ✓ GitHub: https://github.com/fchollet/ARC-AGI
2. ✓ Kaggle: https://www.kaggle.com/competitions/arc-prize-2025/data
3. ✓ Dataset format y especificaciones

---

## 🎨 Descubrimientos Críticos sobre Color

### Sistema de Colores Confirmado
```
Colores disponibles: 10 (números 0-9)
Representación: Enteros únicamente
Rango: [0, 9] (inclusive)

Mapeo Visual Estándar (en visualización):
0 = Negro
1 = Azul oscuro
2 = Rojo
3 = Verde
4 = Amarillo
5 = Gris
6 = Magenta
7 = Naranja
8 = Cián
9 = Marrón
```

### Implicación Crítica para CHIMERA
- ❌ v5.3 nunca valida que predicciones usen solo 0-9
- ✓ Necesitamos validación: `assert all(0 <= c <= 9 for c in output)`
- ✓ Si alguna celda > 9 o < 0 → FALLO automático

---

## 📏 Especificaciones de Grid (CONFIRMADAS)

### Tamaños
```
Mínimo: 1×1
Máximo: 30×30
Típico: 2×2 hasta 20×20
```

### PUNTOS CRÍTICOS
1. **Input y Output pueden tener tamaños DIFERENTES**
   - ✓ v5.3 lo maneja correctamente
   - ✗ v5.2 fracasó por asumir igualdad

2. **Grids siempre rectangulares**
   - No hay formas irregulares
   - Siempre (rows, cols) bien definidas

3. **Max 900 celdas**
   - 30×30 = máximo teórico
   - Memorización exhaustiva potencialmente posible

---

## 📊 Dataset Oficial

### Training Set
- 400 tareas
- Cada tarea: 3 ejemplos de training (típico)
- Cada tarea: 1 test (típico)
- Formato: JSON con "train" y "test"

### Evaluation Set
- 400 tareas (competencia Kaggle)
- Mismo formato
- Solo conocemos "train" + test "input"
- Debemos predecir test "output"

### Formato JSON Confirmado
```json
{
  "train": [
    {"input": [[...]], "output": [[...]]},
    {"input": [[...]], "output": [[...]]},
    {"input": [[...]], "output": [[...]]}
  ],
  "test": [
    {"input": [[...]]}  // No conocemos output
  ]
}
```

---

## ✅ Criterios de Éxito (Críticos)

### Exact Match Required
- Solución debe ser PIXEL PERFECT
- 1 celda incorrecta = FALLO TOTAL
- No hay "crédito parcial"

### Kaggle Allowance
- **3 intentos por test input**
- Si cualquiera de los 3 es correcto = éxito
- Nuestras 2 predicciones (attempt_1, attempt_2) + 1 bonus

### Implicación para CHIMERA
- ✓ Es MEJOR tener 2 soluciones diferentes que 1 perfecta
- ✓ Múltiples hipótesis = mayor probabilidad de acertar
- ✓ v5.3 ya genera 2 intentos (estrategia correcta!)

---

## 🧠 Reasoning Principles (INFERIDOS)

La documentación oficial NO explica los "principios de reasoning", pero de ejemplos:

### Transformaciones Observadas
1. **Geométricas**: Rotación, flip, scaling, translation
2. **Coloréticas**: Recolor, color mapping, swapping
3. **Estructurales**: Expansion, contraction, filling, tiling
4. **Topológicas**: Conectividad, counting, arithmetic
5. **Simétricas**: Reflexión, patrón repetido

### Patrones Comunes
- **Objects**: Grids contienen "objetos" que se transforman
- **Invariants**: Algunos elementos permanecen iguales
- **Progressions**: Series temporal de cambios
- **Rules**: Regla única aplicada uniformemente (idealmente)

---

## 🚨 Validaciones Requeridas para v5.3.1

### 1. Color Validation (CRÍTICO)
```python
def validate_colors(grid):
    """Asegurar que todas las celdas están en [0, 9]"""
    for row in grid:
        for cell in row:
            if not (0 <= cell <= 9):
                return False
    return True
```

### 2. Size Validation
```python
def validate_size(grid):
    """Grids deben ser rectángulos válidos"""
    if not grid or not grid[0]:
        return False
    width = len(grid[0])
    for row in grid:
        if len(row) != width:
            return False
    return True
```

### 3. Consistency Validation
```python
def validate_with_training(pred_grid, training_examples):
    """Comparar con patrones de entrenamiento"""
    # ¿Usa colores que aparecen en training?
    train_colors = set()
    for ex in training_examples:
        for row in ex['output']:
            train_colors.update(row)

    pred_colors = set()
    for row in pred_grid:
        pred_colors.update(row)

    # Bonus si usa solo colores vistos
    return pred_colors.issubset(train_colors)
```

---

## 📈 Estrategia para v5.3.1+ (CON ESPECIFICACIONES)

### Multiple Hypotheses Mejorada
```python
def generate_hypotheses(training_examples):
    """Generar 10 hipótesis validadas"""
    hypotheses = [
        # Básicas
        color_mapping(training_examples),
        size_progression(training_examples),
        identity_transform(),

        # Rotaciones (válido solo si square)
        rotation_90(training_examples),
        rotation_180(training_examples),
        rotation_270(training_examples),

        # Flips
        flip_horizontal(training_examples),
        flip_vertical(training_examples),

        # Otros
        tiling(training_examples),
        fill_pattern(training_examples),
    ]

    # Filtrar: solo hipótesis válidas
    return [h for h in hypotheses if h and validate(h)]

def apply_with_validation(hypothesis, test_input):
    """Aplicar hipótesis y validar resultado"""
    try:
        result = hypothesis.apply(test_input)
        if validate_colors(result) and validate_size(result):
            return result
    except:
        pass
    return None

def score_solution(solution, training_examples):
    """Puntuación basada en especificaciones ARC"""
    score = 0.0

    # 1. Color validity (must have)
    if not validate_colors(solution):
        return 0.0
    score += 1.0

    # 2. Color consistency (bonus)
    train_colors = extract_colors(training_examples)
    pred_colors = set(np.unique(solution))
    if pred_colors.issubset(train_colors):
        score += 2.0

    # 3. Size reasonableness
    if 1 <= solution.shape[0] <= 30 and 1 <= solution.shape[1] <= 30:
        score += 1.0

    # 4. Spatial coherence
    # (detectar si tiene "objetos" coherentes)
    score += coherence_metric(solution) * 0.5

    return score
```

---

## 🎯 Plan de v5.3.1

### Cambios Mínimos, Impacto Máximo

1. **Agregar Validación de Colores** (30 min)
   - Rechazar soluciones con colores > 9
   - Esto solo elimina soluciones claramente inválidas

2. **Implementar Múltiples Hipótesis** (1 hora)
   - 5-10 transformaciones diferentes
   - Aplicar a test input
   - Coleccionar todas las soluciones válidas

3. **Scoring Inteligente** (1 hora)
   - Puntuación basada en ARC specs
   - Color validity (crítico)
   - Color consistency (bonus)
   - Size reasonableness (bonus)

4. **Devolver Top 2** (30 min)
   - Attempt_1: Mejor puntuación
   - Attempt_2: Segunda mejor (diferente estrategia)

### Total Estimado
- Tiempo de implementación: 3-4 horas
- Accuracy esperada: 8-12% (vs actual 2-5%)
- Mejora: 1.6-6× mejor

---

## 🔍 Validación contra Especificaciones Oficiales

### ✓ Cumplimos
- [x] Grids en JSON format
- [x] 10 colores (0-9)
- [x] Tamaños variable (1-30)
- [x] 3 ejemplos → 1 test

### ⚠️ Faltantes en v5.3
- [ ] Validación de colores
- [ ] Múltiples hipótesis
- [ ] Scoring robusto
- [ ] Background subtraction

### 🎯 Será en v5.3.1
- [ ] Validación estricta de colores
- [ ] 5-10 hipótesis diferentes
- [ ] Scoring según ARC specs
- [ ] Devolver 2 mejores intentos

---

## 💡 Cambios de Mentalidad Post-Documentación

### Antes (Asumimos)
- "No sabemos los detalles de ARC"
- "Trabajamos con lo que tenemos"

### Después (Documentado)
- ✓ 10 colores exactos: Validar!
- ✓ Grids hasta 30×30: OK
- ✓ Exact match required: Preciso > Recall
- ✓ 3 intentos permitidos: Múltiples hipótesis > 1 perfecta

### Impacto
- Cambio NO en filosofía
- Cambio SÍ en implementación (validación + multiple attempts)
- Resultado: 8-12% realistic vs 2-5% actual

---

## 🌊 Conclusión

La documentación oficial VALIDA nuestra estrategia pero AÑADE restricciones claras:

1. **Validación de colores es CRÍTICA**
   - Antes: Asumíamos "si funciona, funciona"
   - Ahora: "Solo 0-9, nada más"

2. **Múltiples hipótesis es INTELIGENTE**
   - Antes: "Detectar patrón, aplicar"
   - Ahora: "5-10 hipótesis, votar 2 mejores"

3. **Scoring robusto es POSIBLE**
   - Antes: "Confianza = detección fué OK"
   - Ahora: "Confianza = color valid + coherencia + training consistency"

**Siguiente paso: Implementar v5.3.1 con estas validaciones**

---

