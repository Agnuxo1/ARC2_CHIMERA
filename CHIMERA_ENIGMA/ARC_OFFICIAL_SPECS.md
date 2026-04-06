# ARC AGI 2025 - Especificaciones Oficiales
## Información Crítica del Desafío

**Fuente**: Documentación oficial de https://github.com/fchollet/ARC-AGI y Kaggle ARC Prize 2025

---

## 🎨 Sistema de Colores

### Paleta de Colores
- **Cantidad**: Exactamente 10 colores
- **Representación**: Números enteros 0-9
- **Rango**: Todos los grids usan valores en [0, 9]

```
Color Map (estándar en visualización):
0 = Negro
1 = Azul
2 = Rojo
3 = Verde
4 = Amarillo
5 = Gris
6 = Magenta/Púrpura
7 = Naranja
8 = Cián/Turquesa
9 = Marrón
```

### Implicación para CHIMERA
✓ Color mappings solo pueden ser 0-9 → 0-9
✓ No hay "colores infinitos"
✓ Validación: Todas las predicciones deben usar solo 0-9
✓ Background típicamente es 0 (negro) o color fijo

---

## 📏 Especificaciones de Grid

### Tamaño de Grid
- **Mínimo**: 1×1
- **Máximo**: 30×30
- **Típico**: Varía mucho (desde 2×2 a 25×25)

### Restricción Crítica
- Grids son matrices rectangulares (siempre rectángulo, nunca irregular)
- Input y output pueden tener tamaños DIFERENTES
- No hay restricción de que mantengan relación 1:1

### Implicación para CHIMERA
✓ v5.2 falló porque asumía `input.shape == output.shape` (incorrecta)
✓ v5.3 correctamente maneja cambios de tamaño
✓ Máximo 30×30 = 900 celdas máximo
✓ Memorización pura es teóricamente posible

---

## 📊 Estructura de Datos

### Formato JSON

```json
{
  "train": [
    {
      "input": [[lista de listas de enteros 0-9]],
      "output": [[lista de listas de enteros 0-9]]
    },
    {
      "input": [[...]],
      "output": [[...]]
    },
    {
      "input": [[...]],
      "output": [[...]]
    }
  ],
  "test": [
    {
      "input": [[...]],
      "output": [[...]] // NO CONOCEMOS ESTO, es lo que predecimos
    }
  ]
}
```

### Cantidad de Ejemplos
- **Training ejemplos**: Típicamente 3 pares
- **Test ejemplos**: Típicamente 1 par
- **Rango**: 1-5+ ejemplos

### Implicación para CHIMERA
✓ Solo 3 frames para detectar patrón es muy poco
✓ Patrones pueden ser ambiguos con pocas evidencias
✓ Test tiene 1 pair típicamente (a veces 2+)
✓ Múltiples intentos son críticos

---

## ✅ Criterios de Éxito

### Exact Match Required
- ✓ Solución debe ser EXACTA (pixel perfect)
- ✓ No hay "crédito parcial" por aproximación
- ✓ 1 celda incorrecta = FALLO TOTAL

### Allowance
- 3 intentos por test input (Kaggle)
- Si alguno de los 3 es correcto, es éxito

### Implicación para CHIMERA
✓ Precisión > Recall
✓ Mejor tener 2 intentos diferentes que 1 bueno
✓ v5.3 ya generaba 2 intentos (correcto!)
✓ Múltiples hipótesis son CRÍTICAS

---

## 🧠 Principios Inferidos de ARC

### No Explícitamente Documentado, Pero Emergente

1. **Object Recognition**
   - Grids contienen "objetos" (conectados, patrones repetidos)
   - Los objetos se transforman según regla

2. **Transformation Types Observados**
   - Rotación (90°, 180°, 270°)
   - Flip (horizontal, vertical)
   - Scaling (zoom in/out)
   - Translation (movimiento)
   - Coloring (cambio de color)
   - Filling (relleno de áreas)
   - Symmetry (espejo, reflexión)
   - Tiling (repetición)
   - Counting/arithmetic
   - Pattern continuation

3. **Reasoning Required**
   - Inferencia de regla con pocos ejemplos
   - Generalización a caso nuevo
   - Manejo de ambigüedad

---

## 📈 Dataset Statistics (oficial)

### Training Set
- **Total**: 400 tasks
- **Typical**: 3 train, 1 test
- **Difficulty**: Variada

### Evaluation Set
- **Total**: 400 tasks
- **Typical**: 3 train, 1 test
- **Public Scores**: Visible después de submission

---

## 🚨 Errores Comunes (Aprendidos)

### Error 1: Asumir input.shape == output.shape
- ❌ v5.2 cometió esto
- ✓ v5.3 lo corrigió
- ✓ CHIMERA debe estar preparado para cualquier tamaño

### Error 2: Un solo patrón global
- ❌ v5.3 asume UN patrón
- ⚠️ Realidad: Múltiples patrones posibles
- ✓ Solución: Múltiples hipótesis + voting

### Error 3: Ignorar ambigüedad
- ❌ ARC a menudo es ambiguo con 3 ejemplos
- ✓ Solución: Generar múltiples soluciones
- ✓ Dejar que Kaggle elija

### Error 4: No validar colores
- ❌ Soluciones podrían generar colores > 9
- ✓ Validar que todas las celdas ∈ [0, 9]

---

## 💡 Implicaciones para v5.3.1+

### Cambios Requeridos

1. **Validación de Colores**
   ```python
   def validate_solution(grid):
       for val in np.unique(grid):
           if val < 0 or val > 9:
               return False  # Inválido
       return True
   ```

2. **Manejo de Tamaño Variable**
   ✓ Ya hecho en v5.3

3. **Múltiples Hipótesis**
   - Generar 5-10 soluciones diferentes
   - Devolver 2 mejores
   - Deixar que Kaggle vote

4. **Scoring de Confianza**
   ```python
   score = (
       coherence_score(grid) * 0.3 +
       matches_training_colors(grid) * 0.3 +
       size_matches_pattern(grid) * 0.2 +
       consistency_score(grid) * 0.2
   )
   ```

---

## 🎯 Optimizaciones Viables

### Con Esta Información

1. **Validación Estricta**
   - Rechazar cualquier solución con colores > 9
   - Esto eliminaría muchos falsos positivos

2. **Color-Aware Pattern Matching**
   - Detectar qué colores aparecen en entrenamiento
   - Penalizar predicciones con colores nuevos

3. **Size Progression + Color Mapping**
   - Combinar: si size = 2×3, espera estos colores
   - Aumenta confidence si consistente

4. **Background Subtraction**
   - Muchos ARC tienen background fijo (0)
   - Detectar y preservar background
   - Aplicar transformaciones solo al foreground

---

## 📋 Checklist para v5.3.1

- [ ] Validar que todas soluciones usan colores 0-9
- [ ] Detectar color de background (típicamente 0)
- [ ] Implementar múltiples hipótesis (5-10)
- [ ] Scoring basado en confianza
- [ ] Devolver 2 mejores intentos
- [ ] Preservar background si es identificable
- [ ] Validar output size vs. training patterns

---

## 🌊 Conclusión

La documentación oficial confirma que CHIMERA v5.3 está en el camino correcto:
- ✓ Manejo correcto de 10 colores (0-9)
- ✓ Grids variables en tamaño
- ✓ 3 examples → 1 test es la norma
- ✓ Exact match required → 2 intentos > 1

El siguiente paso es **múltiples hipótesis** con mejor scoring y validación de colores.

**Estimado accuracy con v5.3.1**: 8-12%
**Tiempo de implementación**: 2-3 horas

