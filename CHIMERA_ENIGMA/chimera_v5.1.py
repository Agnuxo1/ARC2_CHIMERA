#!/usr/bin/env python3
"""
CHIMERA v5.1 - Enhanced Pattern Detection
Cryptographic Cellular Automata Engine with Advanced Heuristics

Mejoras sobre v5.0:
- Detección de objetos conectados (flood fill)
- Análisis de patrones espaciales (simetría, tiling)
- Análisis estructural avanzado
- CA rules adaptativas por tipo de patrón
- Confidence scoring por categoría

Objetivo: Aumentar precisión de 0.4% → 10-15%

Philosophy:
- Training examples = Enigma cipher key
- Test input = Encrypted message
- CA evolution = Turing's Bombe machine
- Output = Decrypted solution

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
import time
from collections import Counter


@dataclass
class CipherKey:
    """
    Enhanced cipher key with multi-level analysis.
    v5.1: Añadidos campos para objetos, espacial y confidence por categoría
    """
    # Básico (v5.0)
    scale_ratio: float = 1.0
    rotation_hint: int = 0  # 0, 90, 180, 270
    flip_horizontal: bool = False
    flip_vertical: bool = False
    color_mappings: Dict[int, int] = None
    color_rules: List[Tuple] = None
    fill_rule: Optional[str] = None
    symmetry: Optional[str] = None
    attraction_points: List[Tuple[int, int]] = None
    repulsion_points: List[Tuple[int, int]] = None
    
    # NUEVO v5.1: Análisis de objetos
    object_transform_type: Optional[str] = None  # 'object_transform', 'replication', 'merge'
    object_mappings: List[Dict] = None
    num_objects_expected: int = 0
    
    # NUEVO v5.1: Análisis espacial
    tiling_pattern: Optional[Dict] = None
    grid_structure: Optional[Dict] = None
    
    # NUEVO v5.1: Confidence por categoría
    confidence_basic: float = 0.0
    confidence_objects: float = 0.0
    confidence_spatial: float = 0.0
    confidence_structural: float = 0.0
    
    # Confidence total (weighted average)
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.color_mappings is None:
            self.color_mappings = {}
        if self.color_rules is None:
            self.color_rules = []
        if self.attraction_points is None:
            self.attraction_points = []
        if self.repulsion_points is None:
            self.repulsion_points = []
        if self.object_mappings is None:
            self.object_mappings = []


class CAEngine:
    """
    v5.1: CA Engine with adaptive rules based on cipher key type
    """
    
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.gl_context = None
        
        if use_gpu:
            try:
                import moderngl
                self.gl_context = moderngl.create_standalone_context()
                print("✓ GPU Mode: OpenGL initialized")
            except:
                print("⚠ GPU unavailable - falling back to NumPy CPU mode")
                self.use_gpu = False
    
    def evolve(self, initial_state: np.ndarray, cipher_key: CipherKey, 
               iterations: int = 100) -> np.ndarray:
        """Evolve CA guided by enhanced cipher key"""
        if self.use_gpu and self.gl_context:
            return self._evolve_gpu(initial_state, cipher_key, iterations)
        else:
            return self._evolve_cpu(initial_state, cipher_key, iterations)
    
    def _evolve_gpu(self, state: np.ndarray, key: CipherKey, iters: int) -> np.ndarray:
        """GPU-accelerated CA evolution"""
        print("  [GPU] CA evolution (shader compilation pending)")
        return self._evolve_cpu(state, key, iters)
    
    def _evolve_cpu(self, state: np.ndarray, key: CipherKey, iters: int) -> np.ndarray:
        """
        v5.1: CPU CA evolution with adaptive rules
        """
        current = state.copy().astype(np.int32)
        h, w = current.shape
        
        # Pre-compute energy landscape
        energy_field = self._compute_energy_field(state, key)
        
        # v5.1: Si detectamos tiling perfecto, aplicar directamente
        if key.tiling_pattern and key.confidence_spatial > 0.7:
            if key.tiling_pattern.get('type') == 'perfect_tiling':
                return self._apply_perfect_tiling(state, key)
        
        for iteration in range(iters):
            next_state = current.copy()
            
            # v5.1: Usar reglas adaptativas
            for i in range(h):
                for j in range(w):
                    neighbors = self._get_neighbors(current, i, j)
                    
                    next_state[i, j] = self._ca_rule_adaptive(
                        current[i, j],
                        neighbors,
                        energy_field[i, j],
                        key,
                        (i, j),
                        current  # Pasar grid completo para reglas avanzadas
                    )
            
            if np.array_equal(current, next_state):
                print(f"  [CA] Converged at iteration {iteration}")
                break
                
            current = next_state
        
        return current
    
    def _apply_perfect_tiling(self, state: np.ndarray, key: CipherKey) -> np.ndarray:
        """v5.1: Aplicar tiling perfecto detectado"""
        tile = key.tiling_pattern['tile']
        reps = key.tiling_pattern['repetitions']
        
        # Crear output tileado
        result = np.tile(tile, reps)
        return result
    
    def _compute_energy_field(self, state: np.ndarray, key: CipherKey) -> np.ndarray:
        """Compute energy landscape from cipher key"""
        h, w = state.shape
        energy = np.zeros((h, w), dtype=np.float32)
        
        for (ai, aj) in key.attraction_points:
            if 0 <= ai < h and 0 <= aj < w:
                for i in range(h):
                    for j in range(w):
                        dist = np.sqrt((i - ai)**2 + (j - aj)**2)
                        energy[i, j] -= 1.0 / (dist + 1.0)
        
        for (ri, rj) in key.repulsion_points:
            if 0 <= ri < h and 0 <= rj < w:
                for i in range(h):
                    for j in range(w):
                        dist = np.sqrt((i - ri)**2 + (j - rj)**2)
                        energy[i, j] += 1.0 / (dist + 1.0)
        
        return energy
    
    def _get_neighbors(self, grid: np.ndarray, i: int, j: int) -> List[int]:
        """Get Moore neighborhood (8 neighbors)"""
        h, w = grid.shape
        neighbors = []
        
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < h and 0 <= nj < w:
                    neighbors.append(grid[ni, nj])
        
        return neighbors
    
    def _ca_rule_adaptive(self, cell: int, neighbors: List[int], energy: float, 
                         key: CipherKey, position: Tuple[int, int], 
                         grid: np.ndarray) -> int:
        """
        v5.1: REGLAS CA ADAPTATIVAS según tipo de cipher key
        
        Prioridades:
        1. Object-based transforms (si confidence_objects > 0.5)
        2. Spatial patterns - tiling (si confidence_spatial > 0.5)
        3. Spatial patterns - symmetry  
        4. Basic transforms (rotations, color maps)
        5. Fallback a reglas básicas
        """
        
        # PRIORIDAD 1: Object-based transforms
        if key.confidence_objects > 0.5 and key.object_transform_type:
            return self._apply_object_rule(cell, neighbors, key, position)
        
        # PRIORIDAD 2: Spatial patterns - Tiling
        if key.confidence_spatial > 0.5 and key.tiling_pattern:
            return self._apply_tiling_rule(cell, position, key)
        
        # PRIORIDAD 3: Spatial patterns - Symmetry
        if key.confidence_spatial > 0.4 and key.symmetry:
            return self._apply_symmetry_rule(cell, position, key, grid)
        
        # PRIORIDAD 4: Basic transforms
        if key.confidence_basic > 0.5:
            return self._ca_rule_basic(cell, neighbors, energy, key)
        
        # FALLBACK: Regla básica
        return self._ca_rule_basic(cell, neighbors, energy, key)
    
    def _apply_object_rule(self, cell: int, neighbors: List[int], 
                          key: CipherKey, position: Tuple[int, int]) -> int:
        """
        v5.1: Regla para transformaciones object-based
        """
        if key.object_transform_type == 'replication':
            # Mantener estructura de objetos
            return cell
        
        elif key.object_transform_type == 'object_transform':
            # Aplicar mappings de objetos
            if cell in key.color_mappings:
                return key.color_mappings[cell]
            return cell
        
        elif key.object_transform_type == 'merge':
            # Fusionar con vecinos del mismo color
            counts = Counter(neighbors)
            if cell != 0 and counts:
                most_common = counts.most_common(1)[0][0]
                if most_common == cell:
                    return cell
            return cell
        
        return cell
    
    def _apply_tiling_rule(self, cell: int, position: Tuple[int, int], 
                          key: CipherKey) -> int:
        """
        v5.1: Aplicar regla de tiling
        """
        if not key.tiling_pattern or 'tile' not in key.tiling_pattern:
            return cell
        
        tile = key.tiling_pattern['tile']
        i, j = position
        
        # Calcular posición dentro del tile
        ti = i % tile.shape[0]
        tj = j % tile.shape[1]
        
        return int(tile[ti, tj])
    
    def _apply_symmetry_rule(self, cell: int, position: Tuple[int, int], 
                            key: CipherKey, grid: np.ndarray) -> int:
        """
        v5.1: Aplicar regla de simetría
        """
        h, w = grid.shape
        i, j = position
        
        if key.symmetry == 'horizontal':
            # Reflejar desde la mitad horizontal
            mirror_i = h - 1 - i
            if mirror_i >= 0 and mirror_i < h:
                return int(grid[mirror_i, j])
        
        elif key.symmetry == 'vertical':
            # Reflejar desde la mitad vertical
            mirror_j = w - 1 - j
            if mirror_j >= 0 and mirror_j < w:
                return int(grid[i, mirror_j])
        
        return cell
    
    def _ca_rule_basic(self, cell: int, neighbors: List[int], 
                      energy: float, key: CipherKey) -> int:
        """
        Reglas CA básicas (v5.0)
        """
        neighbor_counts = Counter(neighbors)
        
        # Rule 1: Color mapping
        if cell in key.color_mappings:
            return key.color_mappings[cell]
        
        # Rule 2: Fill empty cells
        if cell == 0 and len(neighbors) > 0:
            if key.fill_rule == 'expand':
                non_zero = [n for n in neighbors if n != 0]
                if len(non_zero) >= 3:
                    return neighbor_counts.most_common(1)[0][0]
            elif key.fill_rule == 'majority':
                if len(neighbors) >= 5:
                    return neighbor_counts.most_common(1)[0][0]
        
        # Rule 3: Preserve non-zero
        if cell != 0:
            for rule in key.color_rules:
                if rule[0] == 'preserve':
                    return cell
                elif rule[0] == 'replace' and cell == rule[1]:
                    return rule[2]
        
        # Rule 4: Energy-guided
        if energy < -0.5:
            most_common = neighbor_counts.most_common(1)
            if most_common and most_common[0][1] >= 3:
                return most_common[0][0]
        
        return cell


class CipherExtractor:
    """
    v5.1: Enhanced Cipher Extractor with multi-level analysis
    """
    
    def extract_key(self, training_examples: List[Dict]) -> CipherKey:
        """
        v5.1: Extract cipher key with advanced analysis
        """
        if not training_examples:
            return CipherKey(confidence=0.0)
        
        # Analyze all training pairs with advanced heuristics
        transformations = []
        for example in training_examples:
            inp = np.array(example['input'])
            out = np.array(example['output'])
            
            trans = self._analyze_transformation_advanced(inp, out)
            transformations.append(trans)
        
        # Synthesize key with advanced logic
        key = self._synthesize_key_advanced(transformations)
        
        return key
    
    def _analyze_transformation_advanced(self, inp: np.ndarray, out: np.ndarray) -> Dict:
        """
        v5.1: ANÁLISIS MULTI-NIVEL de transformaciones
        
        Niveles:
        1. Basic: Rotaciones, flips, color maps
        2. Objects: Componentes conectados
        3. Spatial: Simetría, tiling
        4. Structural: Tamaño, densidad
        """
        analysis = {
            'basic': self._analyze_basic_transforms(inp, out),
            'objects': self._analyze_objects(inp, out),
            'spatial': self._analyze_spatial_patterns(inp, out),
            'structural': self._analyze_structure(inp, out)
        }
        
        return analysis
    
    # ==================== BASIC TRANSFORMS ====================
    
    def _analyze_basic_transforms(self, inp: np.ndarray, out: np.ndarray) -> Dict:
        """Análisis básico (v5.0)"""
        trans = {
            'scale_change': False,
            'rotation': 0,
            'flip_h': False,
            'flip_v': False,
            'color_map': {},
            'fill_pattern': None
        }
        
        # Check scale
        if inp.shape != out.shape:
            trans['scale_change'] = True
            trans['scale_ratio'] = out.shape[0] / inp.shape[0]
        
        # Check rotations
        if inp.shape == out.shape:
            for k in [0, 1, 2, 3]:
                if np.array_equal(np.rot90(inp, k), out):
                    trans['rotation'] = k * 90
                    return trans
            
            # Check flips
            if np.array_equal(np.fliplr(inp), out):
                trans['flip_h'] = True
                return trans
            if np.array_equal(np.flipud(inp), out):
                trans['flip_v'] = True
                return trans
        
        # Color transformations
        trans['color_map'] = self._extract_color_mapping(inp, out)
        
        # Fill patterns
        trans['fill_pattern'] = self._detect_fill_pattern(inp, out)
        
        return trans
    
    def _extract_color_mapping(self, inp: np.ndarray, out: np.ndarray) -> Dict[int, int]:
        """Extract color transformation rules"""
        mapping = {}
        
        if inp.shape == out.shape:
            for i in range(inp.shape[0]):
                for j in range(inp.shape[1]):
                    in_color = int(inp[i, j])
                    out_color = int(out[i, j])
                    
                    if in_color in mapping:
                        if mapping[in_color] != out_color:
                            pass  # Inconsistent
                    else:
                        mapping[in_color] = out_color
        
        return mapping
    
    def _detect_fill_pattern(self, inp: np.ndarray, out: np.ndarray) -> Optional[str]:
        """Detect filling pattern"""
        inp_zeros = np.sum(inp == 0)
        out_zeros = np.sum(out == 0)
        
        if inp_zeros > out_zeros:
            return 'expand'
        elif inp_zeros < out_zeros:
            return 'contract'
        
        # Check symmetry
        if out.shape == inp.shape:
            if np.array_equal(out, np.fliplr(out)):
                return 'mirror_horizontal'
            if np.array_equal(out, np.flipud(out)):
                return 'mirror_vertical'
        
        return None
    
    # ==================== OBJECT DETECTION ====================
    
    def _analyze_objects(self, inp: np.ndarray, out: np.ndarray) -> Dict:
        """
        v5.1: Detecta componentes conectados (objetos)
        """
        inp_objects = self._find_connected_components(inp)
        out_objects = self._find_connected_components(out)
        
        analysis = {
            'num_objects_in': len(inp_objects),
            'num_objects_out': len(out_objects),
            'transform_type': None,
            'object_mappings': []
        }
        
        # Analizar tipo de transformación
        if len(inp_objects) == 0 or len(out_objects) == 0:
            analysis['transform_type'] = 'creation_deletion'
        elif len(inp_objects) == len(out_objects):
            analysis['transform_type'] = 'object_transform'
            # Nota: _match_objects sería complejo, simplificamos
        elif len(out_objects) > len(inp_objects):
            analysis['transform_type'] = 'replication'
            analysis['replication_factor'] = len(out_objects) / len(inp_objects)
        else:
            analysis['transform_type'] = 'merge'
        
        return analysis
    
    def _find_connected_components(self, grid: np.ndarray) -> List[Dict]:
        """
        v5.1: Encuentra objetos usando flood fill
        """
        objects = []
        visited = np.zeros_like(grid, dtype=bool)
        h, w = grid.shape
        
        for i in range(h):
            for j in range(w):
                if not visited[i, j] and grid[i, j] != 0:
                    obj = self._flood_fill(grid, i, j, visited)
                    objects.append(obj)
        
        return objects
    
    def _flood_fill(self, grid: np.ndarray, start_i: int, start_j: int, 
                    visited: np.ndarray) -> Dict:
        """
        v5.1: Flood fill desde (start_i, start_j)
        """
        color = grid[start_i, start_j]
        pixels = []
        stack = [(start_i, start_j)]
        h, w = grid.shape
        
        while stack:
            i, j = stack.pop()
            if i < 0 or i >= h or j < 0 or j >= w:
                continue
            if visited[i, j] or grid[i, j] != color:
                continue
            
            visited[i, j] = True
            pixels.append((i, j))
            
            # 4-connectivity
            stack.extend([(i+1, j), (i-1, j), (i, j+1), (i, j-1)])
        
        if not pixels:
            return {'color': int(color), 'pixels': [], 'bbox': (0,0,0,0), 'size': 0}
        
        # Calcular bbox
        min_i = min(p[0] for p in pixels)
        max_i = max(p[0] for p in pixels)
        min_j = min(p[1] for p in pixels)
        max_j = max(p[1] for p in pixels)
        
        return {
            'color': int(color),
            'pixels': pixels,
            'bbox': (min_i, min_j, max_i, max_j),
            'size': len(pixels)
        }
    
    # ==================== SPATIAL PATTERNS ====================
    
    def _analyze_spatial_patterns(self, inp: np.ndarray, out: np.ndarray) -> Dict:
        """
        v5.1: Detecta patrones espaciales
        """
        patterns = {
            'symmetry': self._detect_symmetry(out),
            'tiling': self._detect_tiling(inp, out),
        }
        
        return patterns
    
    def _detect_symmetry(self, grid: np.ndarray) -> Optional[str]:
        """
        v5.1: Detecta simetría
        """
        # Horizontal
        if np.array_equal(grid, np.fliplr(grid)):
            return 'horizontal'
        
        # Vertical
        if np.array_equal(grid, np.flipud(grid)):
            return 'vertical'
        
        # Diagonal
        if grid.shape[0] == grid.shape[1]:
            if np.array_equal(grid, grid.T):
                return 'diagonal'
        
        # Rotacional 180°
        if np.array_equal(grid, np.rot90(grid, 2)):
            return 'rotational_180'
        
        return None
    
    def _detect_tiling(self, inp: np.ndarray, out: np.ndarray) -> Optional[Dict]:
        """
        v5.1: Detecta tiling
        """
        # Caso 1: Output es repetición perfecta del input
        if out.shape[0] % inp.shape[0] == 0 and out.shape[1] % inp.shape[1] == 0:
            factor_h = out.shape[0] // inp.shape[0]
            factor_w = out.shape[1] // inp.shape[1]
            
            # Verificar si es tiling perfecto
            is_tiling = True
            for i in range(factor_h):
                for j in range(factor_w):
                    tile = out[i*inp.shape[0]:(i+1)*inp.shape[0], 
                              j*inp.shape[1]:(j+1)*inp.shape[1]]
                    if not np.array_equal(tile, inp):
                        is_tiling = False
                        break
                if not is_tiling:
                    break
            
            if is_tiling:
                return {
                    'type': 'perfect_tiling',
                    'tile': inp,
                    'repetitions': (factor_h, factor_w)
                }
        
        # Caso 2: Buscar tile interno (limitado para rendimiento)
        for tile_h in range(1, min(5, out.shape[0])):
            for tile_w in range(1, min(5, out.shape[1])):
                if self._is_tiled_with_size(out, tile_h, tile_w):
                    tile = out[:tile_h, :tile_w]
                    return {
                        'type': 'internal_tiling',
                        'tile': tile,
                        'tile_size': (tile_h, tile_w)
                    }
        
        return None
    
    def _is_tiled_with_size(self, grid: np.ndarray, th: int, tw: int) -> bool:
        """Verifica si grid está tileado con tiles de tamaño (th, tw)"""
        if grid.shape[0] % th != 0 or grid.shape[1] % tw != 0:
            return False
        
        tile = grid[:th, :tw]
        for i in range(0, grid.shape[0], th):
            for j in range(0, grid.shape[1], tw):
                if not np.array_equal(grid[i:i+th, j:j+tw], tile):
                    return False
        
        return True
    
    # ==================== STRUCTURAL ANALYSIS ====================
    
    def _analyze_structure(self, inp: np.ndarray, out: np.ndarray) -> Dict:
        """
        v5.1: Análisis estructural
        """
        return {
            'size_change': {
                'input': inp.shape,
                'output': out.shape,
                'scale_h': out.shape[0] / inp.shape[0] if inp.shape[0] > 0 else 1.0,
                'scale_w': out.shape[1] / inp.shape[1] if inp.shape[1] > 0 else 1.0
            },
            'density_change': {
                'input': np.sum(inp != 0) / inp.size if inp.size > 0 else 0.0,
                'output': np.sum(out != 0) / out.size if out.size > 0 else 0.0
            }
        }
    
    # ==================== KEY SYNTHESIS ====================
    
    def _synthesize_key_advanced(self, transformations: List[Dict]) -> CipherKey:
        """
        v5.1: Sintetiza cipher key de análisis avanzados
        """
        key = CipherKey()
        
        if not transformations:
            return key
        
        # Sintetizar cada categoría
        key = self._synthesize_basic(transformations, key)
        key = self._synthesize_objects(transformations, key)
        key = self._synthesize_spatial(transformations, key)
        key = self._synthesize_structural(transformations, key)
        
        # Confidence total (weighted average)
        key.confidence = (
            0.3 * key.confidence_basic +
            0.3 * key.confidence_objects +
            0.2 * key.confidence_spatial +
            0.2 * key.confidence_structural
        )
        
        return key
    
    def _synthesize_basic(self, transformations: List[Dict], key: CipherKey) -> CipherKey:
        """Sintetizar transformaciones básicas"""
        basic_trans = [t['basic'] for t in transformations]
        
        # Vote on rotation
        rotations = [t['rotation'] for t in basic_trans]
        if rotations and len(set(rotations)) == 1 and rotations[0] > 0:
            key.rotation_hint = rotations[0]
            key.confidence_basic += 0.4
        
        # Vote on flips
        flips_h = sum(t['flip_h'] for t in basic_trans)
        if flips_h == len(basic_trans) and flips_h > 0:
            key.flip_horizontal = True
            key.confidence_basic += 0.4
        
        flips_v = sum(t['flip_v'] for t in basic_trans)
        if flips_v == len(basic_trans) and flips_v > 0:
            key.flip_vertical = True
            key.confidence_basic += 0.4
        
        # Merge color mappings
        color_maps = [t['color_map'] for t in basic_trans if t['color_map']]
        if color_maps:
            common_map = {}
            if len(color_maps) > 0:
                for color in color_maps[0].keys():
                    values = [cm.get(color) for cm in color_maps if color in cm]
                    if len(set(values)) == 1:
                        common_map[color] = values[0]
            
            key.color_mappings = common_map
            if common_map and len(common_map) > 0:
                key.confidence_basic += 0.3
        
        # Fill rule
        fill_patterns = [t['fill_pattern'] for t in basic_trans if t['fill_pattern']]
        if fill_patterns and len(set(fill_patterns)) == 1:
            key.fill_rule = fill_patterns[0]
            key.confidence_basic += 0.2
        
        return key
    
    def _synthesize_objects(self, transformations: List[Dict], key: CipherKey) -> CipherKey:
        """Sintetizar análisis de objetos"""
        obj_trans = [t['objects'] for t in transformations]
        
        # Vote on transform type
        types = [t['transform_type'] for t in obj_trans if t['transform_type']]
        if types and len(set(types)) == 1:
            key.object_transform_type = types[0]
            key.confidence_objects += 0.5
            
            # Si todos tienen el mismo número de objetos
            nums_in = [t['num_objects_in'] for t in obj_trans]
            nums_out = [t['num_objects_out'] for t in obj_trans]
            if len(set(nums_in)) == 1 and len(set(nums_out)) == 1:
                key.num_objects_expected = nums_out[0]
                key.confidence_objects += 0.3
        
        return key
    
    def _synthesize_spatial(self, transformations: List[Dict], key: CipherKey) -> CipherKey:
        """Sintetizar patrones espaciales"""
        spatial_trans = [t['spatial'] for t in transformations]
        
        # Vote on symmetry
        symmetries = [t['symmetry'] for t in spatial_trans if t['symmetry']]
        if symmetries and len(set(symmetries)) == 1:
            key.symmetry = symmetries[0]
            key.confidence_spatial += 0.4
        
        # Vote on tiling
        tilings = [t['tiling'] for t in spatial_trans if t['tiling']]
        if tilings:
            # Si todos detectan el mismo tipo de tiling
            types = [t['type'] for t in tilings]
            if len(set(types)) == 1:
                key.tiling_pattern = tilings[0]
                key.confidence_spatial += 0.6
        
        return key
    
    def _synthesize_structural(self, transformations: List[Dict], key: CipherKey) -> CipherKey:
        """Sintetizar análisis estructural"""
        struct_trans = [t['structural'] for t in transformations]
        
        # Check consistent scale changes
        scales_h = [t['size_change']['scale_h'] for t in struct_trans]
        scales_w = [t['size_change']['scale_w'] for t in struct_trans]
        
        if len(set(scales_h)) == 1 and len(set(scales_w)) == 1:
            if scales_h[0] != 1.0 or scales_w[0] != 1.0:
                key.scale_ratio = scales_h[0]
                key.confidence_structural += 0.5
        
        return key


class CHIMERAv51:
    """
    v5.1: Enhanced CHIMERA with advanced pattern detection
    """
    
    def __init__(self, use_gpu: bool = True):
        self.ca_engine = CAEngine(use_gpu=use_gpu)
        self.cipher_extractor = CipherExtractor()
        print("=" * 80)
        print("CHIMERA v5.1 - ENHANCED PATTERN DETECTION")
        print("=" * 80)
    
    def solve_task(self, task: Dict) -> List[List]:
        """
        Solve ARC task with enhanced heuristics
        """
        print(f"\n[TASK] Training: {len(task['train'])}, Test: {len(task['test'])}")
        
        # Step 1: Extract enhanced cipher key
        print("[STEP 1] Extracting enhanced cipher key...")
        cipher_key = self.cipher_extractor.extract_key(task['train'])
        
        print(f"  → Overall confidence: {cipher_key.confidence:.2f}")
        print(f"  → Basic confidence: {cipher_key.confidence_basic:.2f}")
        print(f"  → Objects confidence: {cipher_key.confidence_objects:.2f}")
        print(f"  → Spatial confidence: {cipher_key.confidence_spatial:.2f}")
        
        if cipher_key.object_transform_type:
            print(f"  → Object transform: {cipher_key.object_transform_type}")
        if cipher_key.tiling_pattern:
            print(f"  → Tiling detected: {cipher_key.tiling_pattern['type']}")
        if cipher_key.symmetry:
            print(f"  → Symmetry: {cipher_key.symmetry}")
        
        # Step 2: Apply to test cases
        print("[STEP 2] Decrypting test cases...")
        solutions = []
        
        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])
            print(f"  Test {test_idx}: {test_input.shape} grid")
            
            # Attempt 1: Enhanced CA evolution
            attempt1 = self._decrypt_with_ca(test_input, cipher_key)
            
            # Attempt 2: Variation
            attempt2 = self._decrypt_with_variation(test_input, cipher_key)
            
            solutions.append([attempt1.tolist(), attempt2.tolist()])
        
        return solutions
    
    def _decrypt_with_ca(self, test_input: np.ndarray, key: CipherKey) -> np.ndarray:
        """
        v5.1: Decrypt with enhanced strategies
        """
        # Apply geometric hints first if strong
        if key.confidence_basic > 0.5:
            if key.rotation_hint > 0:
                test_input = np.rot90(test_input, k=key.rotation_hint // 90)
            if key.flip_horizontal:
                test_input = np.fliplr(test_input)
            if key.flip_vertical:
                test_input = np.flipud(test_input)
        
        # Evolve CA
        result = self.ca_engine.evolve(test_input, key, iterations=100)
        
        return result
    
    def _decrypt_with_variation(self, test_input: np.ndarray, key: CipherKey) -> np.ndarray:
        """
        v5.1: Generate variation with enhanced logic
        """
        # Si detectamos tiling perfecto, intentar aplicar directamente
        if key.tiling_pattern and key.confidence_spatial > 0.6:
            if key.tiling_pattern.get('type') == 'perfect_tiling':
                tile = key.tiling_pattern['tile']
                reps = key.tiling_pattern['repetitions']
                return np.tile(tile, reps)
        
        # Variation: Color mapping directo
        if key.color_mappings and len(key.color_mappings) > 0:
            result = test_input.copy()
            for old_color, new_color in key.color_mappings.items():
                result[result == old_color] = new_color
            result = self.ca_engine.evolve(result, key, iterations=50)
            return result
        
        # Fallback: más iteraciones
        return self.ca_engine.evolve(test_input, key, iterations=200)


def solve_arc_task(task: Dict, use_gpu: bool = True) -> List[List]:
    """
    v5.1: Main entry point
    """
    chimera = CHIMERAv51(use_gpu=use_gpu)
    return chimera.solve_task(task)


if __name__ == "__main__":
    import json
    from pathlib import Path
    
    print("\n" + "=" * 80)
    print("CHIMERA v5.1 - STANDALONE TEST")
    print("=" * 80)
    
    # Test simple rotation
    print("\n[TEST 1] Simple rotation task")
    simple_task = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[3, 1], [4, 2]]},
            {'input': [[5, 6], [7, 8]], 'output': [[7, 5], [8, 6]]}
        ],
        'test': [{'input': [[9, 10], [11, 12]]}]
    }
    
    result = solve_arc_task(simple_task, use_gpu=False)
    print(f"\nExpected: [[11, 9], [12, 10]]")
    print(f"Attempt 1: {result[0][0]}")
    print(f"Attempt 2: {result[0][1]}")
    
    print("\n" + "=" * 80)
    print("CHIMERA v5.1 READY")
    print("=" * 80)

