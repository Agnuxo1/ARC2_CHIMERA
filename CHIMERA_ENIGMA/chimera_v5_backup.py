#!/usr/bin/env python3
"""
CHIMERA v5 - Cryptographic Cellular Automata Engine
The CORRECT approach: Training examples as cipher keys, CA evolution as decryption

Philosophy:
- Training examples = Enigma cipher key
- Test input = Encrypted message
- CA evolution = Turing's Bombe machine
- Output = Decrypted solution

"The water doesn't think - it just flows to the ocean.
 Turing didn't understand Nazi messages - he just found the pattern."
 
Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import time


@dataclass
class CipherKey:
    """
    The cryptographic key extracted from training examples.
    This encodes the transformation pattern as mathematical invariants.
    """
    # Geometric invariants
    scale_ratio: float = 1.0
    rotation_hint: int = 0  # 0, 90, 180, 270
    flip_horizontal: bool = False
    flip_vertical: bool = False
    
    # Color transformation rules
    color_mappings: Dict[int, int] = None
    color_rules: List[Tuple] = None
    
    # Spatial patterns
    fill_rule: Optional[str] = None  # 'expand', 'contract', 'mirror'
    symmetry: Optional[str] = None   # 'vertical', 'horizontal', 'diagonal'
    
    # Energy landscape parameters
    attraction_points: List[Tuple[int, int]] = None
    repulsion_points: List[Tuple[int, int]] = None
    
    # Confidence score
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


class CAEngine:
    """
    Cellular Automata Engine - The physical decryption machine.
    Like water flowing downhill, CA finds minimum energy states.
    """
    
    def __init__(self, use_gpu: bool = True):
        self.use_gpu = use_gpu
        self.gl_context = None
        
        # Try to initialize OpenGL
        if use_gpu:
            try:
                import moderngl
                self.gl_context = moderngl.create_standalone_context()
                print("✓ GPU Mode: OpenGL initialized")
            except:
                print("⚠ GPU unavailable - falling back to NumPy CPU mode")
                self.use_gpu = False
    
    def evolve(self, 
               initial_state: np.ndarray,
               cipher_key: CipherKey,
               iterations: int = 100) -> np.ndarray:
        """
        Evolve CA guided by cipher key.
        
        This is where the "decryption" happens:
        - Initial state = encrypted message (test input)
        - Cipher key = transformation rules from training
        - Evolution = finding minimum energy (correct solution)
        
        Args:
            initial_state: Test input grid
            cipher_key: Extracted from training examples
            iterations: Evolution steps
            
        Returns:
            Decrypted grid (solution)
        """
        if self.use_gpu and self.gl_context:
            return self._evolve_gpu(initial_state, cipher_key, iterations)
        else:
            return self._evolve_cpu(initial_state, cipher_key, iterations)
    
    def _evolve_gpu(self, state: np.ndarray, key: CipherKey, iters: int) -> np.ndarray:
        """GPU-accelerated CA evolution using OpenGL shaders"""
        # TODO: Implement full OpenGL shader pipeline
        # For now, fall back to CPU with note
        print("  [GPU] CA evolution (shader compilation pending)")
        return self._evolve_cpu(state, key, iters)
    
    def _evolve_cpu(self, state: np.ndarray, key: CipherKey, iters: int) -> np.ndarray:
        """
        CPU CA evolution with cipher-guided rules.
        
        The CA evolves by minimizing energy defined by:
        1. Geometric constraints from cipher key
        2. Color transformation rules
        3. Spatial coherence
        """
        current = state.copy().astype(np.int32)
        h, w = current.shape
        
        # Pre-compute energy landscape from cipher key
        energy_field = self._compute_energy_field(state, key)
        
        for iteration in range(iters):
            # Create next generation
            next_state = current.copy()
            
            # Apply CA rules guided by cipher key
            for i in range(h):
                for j in range(w):
                    # Get neighborhood
                    neighbors = self._get_neighbors(current, i, j)
                    
                    # Compute next state based on:
                    # 1. Current cell
                    # 2. Neighbors
                    # 3. Energy field (from cipher key)
                    # 4. Color rules
                    
                    next_state[i, j] = self._ca_rule(
                        current[i, j],
                        neighbors,
                        energy_field[i, j],
                        key
                    )
            
            # Check convergence
            if np.array_equal(current, next_state):
                print(f"  [CA] Converged at iteration {iteration}")
                break
                
            current = next_state
        
        return current
    
    def _compute_energy_field(self, state: np.ndarray, key: CipherKey) -> np.ndarray:
        """
        Compute energy landscape from cipher key.
        Low energy = where solution should flow to.
        """
        h, w = state.shape
        energy = np.zeros((h, w), dtype=np.float32)
        
        # Add attraction/repulsion from key
        for (ai, aj) in key.attraction_points:
            if 0 <= ai < h and 0 <= aj < w:
                # Create gradient toward attraction point
                for i in range(h):
                    for j in range(w):
                        dist = np.sqrt((i - ai)**2 + (j - aj)**2)
                        energy[i, j] -= 1.0 / (dist + 1.0)  # Attraction
        
        for (ri, rj) in key.repulsion_points:
            if 0 <= ri < h and 0 <= rj < w:
                for i in range(h):
                    for j in range(w):
                        dist = np.sqrt((i - ri)**2 + (j - rj)**2)
                        energy[i, j] += 1.0 / (dist + 1.0)  # Repulsion
        
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
    
    def _ca_rule(self, cell: int, neighbors: List[int], 
                 energy: float, key: CipherKey) -> int:
        """
        CA update rule guided by cipher key.
        
        This is the "physical law" that makes the CA flow
        toward the solution, like water flowing downhill.
        """
        # Count neighbor colors
        from collections import Counter
        neighbor_counts = Counter(neighbors)
        
        # Rule 1: Color mapping from cipher key
        if cell in key.color_mappings:
            return key.color_mappings[cell]
        
        # Rule 2: Fill empty cells based on neighbors
        if cell == 0 and len(neighbors) > 0:
            # Check fill rule from key
            if key.fill_rule == 'expand':
                # Expand non-zero colors
                non_zero = [n for n in neighbors if n != 0]
                if len(non_zero) >= 3:
                    return neighbor_counts.most_common(1)[0][0]
            
            elif key.fill_rule == 'majority':
                if len(neighbors) >= 5:
                    return neighbor_counts.most_common(1)[0][0]
        
        # Rule 3: Preserve non-zero cells unless key says otherwise
        if cell != 0:
            # Check if should be transformed
            for rule in key.color_rules:
                if rule[0] == 'preserve':
                    return cell
                elif rule[0] == 'replace' and cell == rule[1]:
                    return rule[2]
        
        # Rule 4: Energy-guided evolution
        # (cells flow toward low energy states)
        if energy < -0.5:  # Strong attraction
            most_common = neighbor_counts.most_common(1)
            if most_common and most_common[0][1] >= 3:
                return most_common[0][0]
        
        # Default: keep current state
        return cell


class CipherExtractor:
    """
    Extracts the cipher key from training examples.
    
    This is the cryptanalysis step: analyzing encrypted/decrypted
    pairs to discover the encryption method.
    """
    
    def extract_key(self, training_examples: List[Dict]) -> CipherKey:
        """
        Extract cipher key from training examples.
        
        Args:
            training_examples: List of {'input': grid, 'output': grid}
            
        Returns:
            CipherKey encoding the transformation
        """
        if not training_examples:
            return CipherKey(confidence=0.0)
        
        key = CipherKey()
        
        # Analyze all training pairs
        transformations = []
        for example in training_examples:
            inp = np.array(example['input'])
            out = np.array(example['output'])
            
            trans = self._analyze_transformation(inp, out)
            transformations.append(trans)
        
        # Extract consistent patterns across all examples
        key = self._synthesize_key(transformations)
        
        return key
    
    def _analyze_transformation(self, inp: np.ndarray, out: np.ndarray) -> Dict:
        """Analyze a single input→output transformation"""
        trans = {
            'scale_change': False,
            'rotation': 0,
            'flip_h': False,
            'flip_v': False,
            'color_map': {},
            'fill_pattern': None,
            'geometric': None
        }
        
        # Check scale change
        if inp.shape != out.shape:
            trans['scale_change'] = True
            trans['scale_ratio'] = out.shape[0] / inp.shape[0]
        
        # Check rotations (if same size)
        if inp.shape == out.shape:
            for k in [0, 1, 2, 3]:  # 0, 90, 180, 270 degrees
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
        
        # Analyze color transformations
        trans['color_map'] = self._extract_color_mapping(inp, out)
        
        # Analyze fill patterns
        trans['fill_pattern'] = self._detect_fill_pattern(inp, out)
        
        return trans
    
    def _extract_color_mapping(self, inp: np.ndarray, out: np.ndarray) -> Dict[int, int]:
        """Extract color transformation rules"""
        mapping = {}
        
        # For same-sized grids, try to find consistent mappings
        if inp.shape == out.shape:
            for i in range(inp.shape[0]):
                for j in range(inp.shape[1]):
                    in_color = inp[i, j]
                    out_color = out[i, j]
                    
                    if in_color in mapping:
                        # Check consistency
                        if mapping[in_color] != out_color:
                            # Inconsistent mapping
                            pass
                    else:
                        mapping[in_color] = out_color
        
        return mapping
    
    def _detect_fill_pattern(self, inp: np.ndarray, out: np.ndarray) -> Optional[str]:
        """Detect if there's a filling pattern"""
        
        # Count zeros (empty cells)
        inp_zeros = np.sum(inp == 0)
        out_zeros = np.sum(out == 0)
        
        if inp_zeros > out_zeros:
            # Output has fewer empty cells -> expansion
            return 'expand'
        elif inp_zeros < out_zeros:
            # Output has more empty cells -> contraction
            return 'contract'
        
        # Check for symmetry filling
        if out.shape == inp.shape:
            if np.array_equal(out, np.fliplr(out)):
                return 'mirror_horizontal'
            if np.array_equal(out, np.flipud(out)):
                return 'mirror_vertical'
        
        return None
    
    def _synthesize_key(self, transformations: List[Dict]) -> CipherKey:
        """
        Synthesize a single cipher key from multiple transformation analyses.
        
        This finds the consistent pattern across all training examples.
        """
        key = CipherKey()
        
        if not transformations:
            return key
        
        # Vote on rotation
        rotations = [t['rotation'] for t in transformations]
        if rotations and len(set(rotations)) == 1:
            key.rotation_hint = rotations[0]
            key.confidence += 0.3
        
        # Vote on flips
        flips_h = sum(t['flip_h'] for t in transformations)
        if flips_h == len(transformations):
            key.flip_horizontal = True
            key.confidence += 0.3
        
        flips_v = sum(t['flip_v'] for t in transformations)
        if flips_v == len(transformations):
            key.flip_vertical = True
            key.confidence += 0.3
        
        # Merge color mappings (take intersection)
        color_maps = [t['color_map'] for t in transformations if t['color_map']]
        if color_maps:
            # Find consistent mappings
            common_map = {}
            for color in color_maps[0].keys():
                values = [cm.get(color) for cm in color_maps if color in cm]
                if len(set(values)) == 1:  # All agree
                    common_map[color] = values[0]
            
            key.color_mappings = common_map
            if common_map:
                key.confidence += 0.3
        
        # Determine fill rule
        fill_patterns = [t['fill_pattern'] for t in transformations if t['fill_pattern']]
        if fill_patterns and len(set(fill_patterns)) == 1:
            key.fill_rule = fill_patterns[0]
            key.confidence += 0.1
        
        return key


class CHIMERAv5:
    """
    CHIMERA v5 - The Complete Cryptographic System
    
    "We don't solve ARC with reasoning.
     We decrypt it with physics.
     
     Training examples are the cipher key.
     CA evolution is the Bombe machine.
     The solution flows like water to the ocean."
    """
    
    def __init__(self, use_gpu: bool = True):
        self.ca_engine = CAEngine(use_gpu=use_gpu)
        self.cipher_extractor = CipherExtractor()
        print("=" * 80)
        print("CHIMERA v5 - CRYPTOGRAPHIC CELLULAR AUTOMATA ENGINE")
        print("=" * 80)
    
    def solve_task(self, task: Dict) -> List[List]:
        """
        Solve an ARC task using cryptographic approach.
        
        Process:
        1. Extract cipher key from training examples (cryptanalysis)
        2. For each test input:
           a. Initialize CA with test input
           b. Evolve CA guided by cipher key
           c. Generate multiple attempts with variations
        
        Args:
            task: {'train': [...], 'test': [...]}
            
        Returns:
            List of solutions, each with [attempt1, attempt2]
        """
        print(f"\n[TASK] Training examples: {len(task['train'])}, Test cases: {len(task['test'])}")
        
        # Step 1: CRYPTANALYSIS - Extract cipher key
        print("[STEP 1] Extracting cipher key from training examples...")
        cipher_key = self.cipher_extractor.extract_key(task['train'])
        print(f"  → Key confidence: {cipher_key.confidence:.2f}")
        print(f"  → Rotation: {cipher_key.rotation_hint}°")
        print(f"  → Color mappings: {len(cipher_key.color_mappings)}")
        print(f"  → Fill rule: {cipher_key.fill_rule}")
        
        # Step 2: DECRYPTION - Apply to test cases
        print("[STEP 2] Decrypting test cases...")
        solutions = []
        
        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])
            print(f"  Test {test_idx}: {test_input.shape} grid")
            
            # Attempt 1: Direct CA evolution
            attempt1 = self._decrypt_with_ca(test_input, cipher_key)
            
            # Attempt 2: Variation (geometric transform first, then CA)
            attempt2 = self._decrypt_with_variation(test_input, cipher_key)
            
            solutions.append([attempt1.tolist(), attempt2.tolist()])
        
        return solutions
    
    def _decrypt_with_ca(self, test_input: np.ndarray, key: CipherKey) -> np.ndarray:
        """
        Decrypt test input using CA evolution.
        
        This is the core "Turing Bombe" operation.
        """
        # Apply geometric hints first if strong
        if key.confidence > 0.5:
            if key.rotation_hint > 0:
                test_input = np.rot90(test_input, k=key.rotation_hint // 90)
            if key.flip_horizontal:
                test_input = np.fliplr(test_input)
            if key.flip_vertical:
                test_input = np.flipud(test_input)
        
        # Evolve CA
        result = self.ca_engine.evolve(
            test_input,
            key,
            iterations=100
        )
        
        return result
    
    def _decrypt_with_variation(self, test_input: np.ndarray, key: CipherKey) -> np.ndarray:
        """
        Generate variation by trying different CA parameters.
        """
        # Try more iterations or different initial conditions
        
        # Variation: Apply color mapping directly if available
        if key.color_mappings and len(key.color_mappings) > 0:
            result = test_input.copy()
            for old_color, new_color in key.color_mappings.items():
                result[result == old_color] = new_color
            
            # Then evolve briefly
            result = self.ca_engine.evolve(result, key, iterations=50)
            return result
        
        # Otherwise, just evolve longer
        return self.ca_engine.evolve(test_input, key, iterations=200)


def solve_arc_task(task: Dict, use_gpu: bool = True) -> List[List]:
    """
    Main entry point for solving ARC tasks.
    
    Args:
        task: ARC task dictionary
        use_gpu: Whether to use GPU acceleration
        
    Returns:
        Solutions for all test cases
    """
    chimera = CHIMERAv5(use_gpu=use_gpu)
    return chimera.solve_task(task)


if __name__ == "__main__":
    import json
    from pathlib import Path
    
    print("\n" + "=" * 80)
    print("CHIMERA v5 - STANDALONE TEST")
    print("=" * 80)
    
    # Test with simple example
    print("\n[TEST 1] Simple rotation task")
    simple_task = {
        'train': [
            {
                'input': [[1, 2], [3, 4]],
                'output': [[3, 1], [4, 2]]  # 90° CCW rotation
            },
            {
                'input': [[5, 6], [7, 8]],
                'output': [[7, 5], [8, 6]]  # 90° CCW rotation
            }
        ],
        'test': [
            {
                'input': [[9, 10], [11, 12]]
            }
        ]
    }
    
    result = solve_arc_task(simple_task, use_gpu=False)
    print(f"\nInput:     [[9, 10], [11, 12]]")
    print(f"Expected:  [[11, 9], [12, 10]]")
    print(f"Attempt 1: {result[0][0]}")
    print(f"Attempt 2: {result[0][1]}")
    
    # Test with actual ARC data if available
    data_path = Path(__file__).parent / 'data' / 'arc-agi_training_challenges.json'
    if data_path.exists():
        print("\n" + "=" * 80)
        print("[TEST 2] Real ARC task")
        print("=" * 80)
        
        with open(data_path, 'r') as f:
            tasks = json.load(f)
        
        # Test first task
        task_id = list(tasks.keys())[0]
        task = tasks[task_id]
        
        print(f"\nTask ID: {task_id}")
        result = solve_arc_task(task, use_gpu=False)
        print(f"Generated {len(result)} solutions")
    else:
        print("\n[INFO] No ARC data found for extended testing")
    
    print("\n" + "=" * 80)
    print("CHIMERA v5 READY")
    print("=" * 80)
