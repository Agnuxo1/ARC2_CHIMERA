#!/usr/bin/env python3
"""
CHIMERA v5.3 - Temporal Sequence Pattern Recognition
"IQ Test Approach" - Treating ARC as sequence interpolation

Philosophy:
"ARC is not about transformation rules - it's about temporal sequences.
Like an IQ test where you see frames 1, 2, 3... and must predict frame 5.
The pattern is ALWAYS a simple mathematical progression over time/frames.

Examples are sequential snapshots.
Training = frames 1, 2, 3 (positions in sequence)
Test = positions we need to interpolate/extrapolate

Size, color, position, rotation - all follow mathematical progressions.
Just like a clock going 12:00 -> 12:15 -> 12:30 -> 12:45

Pattern Discovery = Finding the sequence law.
No reasoning needed - just mathematical interpolation."

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import time
from collections import Counter


@dataclass
class TemporalPattern:
    """
    Represents a detected temporal pattern in the sequence.

    Examples are frames in a sequence:
    - Frame 0: Input[0], Output[0]
    - Frame 1: Input[1], Output[1]
    - Frame N: We need to find Output[N]
    """
    # Pattern types detected
    size_progression: Optional[Tuple[int, int, int]] = None  # (start, delta, type)
    color_mappings: Optional[Dict[int, int]] = None
    position_deltas: Optional[List[Tuple[int, int]]] = None  # How (row, col) change per frame
    rotation_progression: Optional[int] = None  # Degrees per frame
    fill_progression: Optional[str] = None  # How filling evolves

    # Detected invariants (things that don't change)
    invariant_colors: Optional[Set[int]] = None
    invariant_shapes: Optional[List] = None

    # Pattern strength
    confidence: float = 0.0

    def __post_init__(self):
        if self.color_mappings is None:
            self.color_mappings = {}
        if self.invariant_colors is None:
            self.invariant_colors = set()


class SequenceAnalyzer:
    """
    Analyze training examples as frames in a temporal sequence.

    Key insight: ARC examples aren't independent - they're a sequence.
    Frame 0: transforms one way
    Frame 1: transforms another way
    Frame 2: follows the pattern
    Frame N (test): extrapolate the pattern
    """

    def __init__(self):
        self.patterns = []

    def analyze_sequence(self, training_examples: List[Dict]) -> TemporalPattern:
        """
        Analyze training examples as a sequence.

        Detect:
        1. Size progression (how grid grows/shrinks)
        2. Color evolution (which colors map to which)
        3. Position changes (where things move)
        4. Rotation/flip patterns (geometric changes)
        5. Fill patterns (how areas expand/contract)

        Returns the mathematical law governing the sequence.
        """

        if len(training_examples) < 2:
            # Insufficient data to detect pattern
            return self._fallback_analysis(training_examples)

        # Extract key features from each frame
        frames = []
        for example in training_examples:
            inp = np.array(example['input'])
            out = np.array(example['output'])
            frame = {
                'input': inp,
                'output': out,
                'input_size': inp.shape,
                'output_size': out.shape,
                'input_colors': set(inp.flatten()),
                'output_colors': set(out.flatten()),
            }
            frames.append(frame)

        pattern = TemporalPattern()

        # 1. DETECT SIZE PROGRESSION
        pattern.size_progression = self._detect_size_progression(frames)

        # 2. DETECT COLOR MAPPINGS
        pattern.color_mappings = self._detect_color_evolution(frames)

        # 3. DETECT POSITION CHANGES
        pattern.position_deltas = self._detect_position_progression(frames)

        # 4. DETECT ROTATION/GEOMETRIC
        pattern.rotation_progression = self._detect_rotation_progression(frames)

        # 5. DETECT INVARIANTS
        pattern.invariant_colors = self._detect_invariant_colors(frames)

        # Calculate confidence
        pattern.confidence = self._calculate_confidence(pattern, frames)

        return pattern

    def _detect_size_progression(self, frames: List) -> Optional[Tuple]:
        """
        Detect how grid size changes frame by frame.

        Examples:
        - Frame 0: 2x2, Frame 1: 4x4, Frame 2: 6x6 -> progression = (+2, +2)
        - Frame 0: 5x5, Frame 1: 5x5, Frame 2: 5x5 -> no change
        """
        if len(frames) < 2:
            return None

        output_sizes = [f['output_size'] for f in frames]

        # Check if there's a consistent delta
        deltas_h = []
        deltas_w = []

        for i in range(len(output_sizes) - 1):
            h1, w1 = output_sizes[i]
            h2, w2 = output_sizes[i + 1]
            deltas_h.append(h2 - h1)
            deltas_w.append(w2 - w1)

        # Check for arithmetic progression
        if len(deltas_h) > 0:
            avg_delta_h = np.mean(deltas_h)
            avg_delta_w = np.mean(deltas_w)

            # If consistent deltas, it's arithmetic
            if abs(np.std(deltas_h)) < 0.1 and abs(np.std(deltas_w)) < 0.1:
                return ('arithmetic', int(avg_delta_h), int(avg_delta_w))

            # Check for geometric progression
            if output_sizes[0][0] > 0:
                ratios_h = [output_sizes[i+1][0] / output_sizes[i][0] for i in range(len(output_sizes)-1)]
                if abs(np.std(ratios_h)) < 0.1 and ratios_h[0] > 0:
                    return ('geometric', ratios_h[0], 1.0)

        return None

    def _detect_color_evolution(self, frames: List) -> Dict[int, int]:
        """
        Detect stable color mappings.
        If color X always maps to color Y, it's a rule.
        """
        mapping = {}

        for frame in frames:
            inp = frame['input']
            out = frame['output']

            # Only analyze if same shape
            if inp.shape != out.shape:
                continue

            # For each unique color in input, find what it becomes
            for color in frame['input_colors']:
                mask_inp = (inp == color)

                # Get corresponding output colors
                out_colors = out[mask_inp]

                if len(out_colors) > 0:
                    most_common = Counter(out_colors).most_common(1)[0][0]

                    if color not in mapping:
                        mapping[color] = most_common

        return mapping

    def _detect_position_progression(self, frames: List) -> Optional[List[Tuple[int, int]]]:
        """
        Detect how positions change frame by frame.
        Find objects and track their movement.
        """
        # Simplified: detect center of mass progression
        deltas = []

        for frame in frames:
            out = frame['output']
            # Find center of non-zero elements
            coords = np.argwhere(out != 0)
            if len(coords) > 0:
                center = np.mean(coords, axis=0)
                deltas.append(tuple(center))

        if len(deltas) < 2:
            return None

        # Check for consistent movement
        movements = []
        for i in range(len(deltas) - 1):
            mov = (deltas[i+1][0] - deltas[i][0], deltas[i+1][1] - deltas[i][1])
            movements.append(mov)

        return movements if movements else None

    def _detect_rotation_progression(self, frames: List) -> Optional[int]:
        """
        Detect if there's rotation happening frame by frame.
        Check for 90, 180, 270 degree rotations.
        """
        # Simplified version - check if output[i] is rotation of input[i]
        for i, frame in enumerate(frames):
            inp = frame['input']
            out = frame['output']

            # Only check if same size
            if inp.shape == out.shape:
                for rot in [1, 2, 3]:  # 90, 180, 270 degrees
                    rotated = np.rot90(inp, rot)
                    if np.array_equal(rotated, out):
                        return rot * 90

        return None

    def _detect_invariant_colors(self, frames: List) -> Set[int]:
        """
        Find colors that never change position or role.
        These are usually background or structural elements.
        """
        all_input_colors = set()
        for frame in frames:
            all_input_colors.update(frame['input_colors'])

        # Colors that appear in input and output consistently
        invariant = set()
        for color in all_input_colors:
            appears_in_all = all(color in f['input_colors'] for f in frames)
            if appears_in_all:
                invariant.add(color)

        return invariant

    def _calculate_confidence(self, pattern: TemporalPattern, frames: List) -> float:
        """
        Calculate how confident we are in this pattern.
        """
        confidence = 0.0

        if pattern.size_progression is not None:
            confidence += 0.3
        if pattern.color_mappings:
            confidence += 0.3
        if pattern.rotation_progression is not None:
            confidence += 0.2
        if pattern.invariant_colors:
            confidence += 0.2

        return min(confidence, 1.0)

    def _fallback_analysis(self, training_examples: List[Dict]) -> TemporalPattern:
        """Fallback when insufficient data."""
        pattern = TemporalPattern()

        if training_examples:
            inp = np.array(training_examples[0]['input'])
            out = np.array(training_examples[0]['output'])

            pattern.color_mappings = {}
            for color in set(inp.flatten()):
                mask = (inp == color)
                out_colors = out[mask]
                if len(out_colors) > 0:
                    pattern.color_mappings[color] = Counter(out_colors).most_common(1)[0][0]

        return pattern


class SequenceCA:
    """
    Cellular Automaton guided by detected temporal patterns.

    Instead of generic energy gradients, use the detected sequence law
    to guide grid transformation.
    """

    def __init__(self, pattern: TemporalPattern):
        self.pattern = pattern

    def evolve_to_target_size(self, state: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Transform state to target size following the pattern.
        """
        current_size = state.shape

        if current_size == target_size:
            return state

        # Strategy 1: Simple interpolation
        if target_size[0] > current_size[0] or target_size[1] > current_size[1]:
            return self._expand_grid(state, target_size)
        else:
            return self._contract_grid(state, target_size)

    def _expand_grid(self, state: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Expand grid to target size using pattern."""
        h_curr, w_curr = state.shape
        h_targ, w_targ = target_size

        # Use repeat/tile if ratio is integer
        h_ratio = h_targ / h_curr
        w_ratio = w_targ / w_curr

        if (h_ratio == int(h_ratio) and w_ratio == int(w_ratio) and
            h_ratio > 0 and w_ratio > 0):
            # Tile pattern
            return np.tile(state, (int(h_ratio), int(w_ratio)))

        # Fallback: zoom using nearest neighbor
        from scipy.ndimage import zoom
        return zoom(state, (h_targ / h_curr, w_targ / w_curr), order=0).astype(state.dtype)

    def _contract_grid(self, state: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Contract grid to target size."""
        from scipy.ndimage import zoom
        h_curr, w_curr = state.shape
        h_targ, w_targ = target_size
        return zoom(state, (h_targ / h_curr, w_targ / w_curr), order=0).astype(state.dtype)

    def apply_pattern(self, state: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Apply detected pattern transformations to state."""
        result = state.copy()

        # Apply color mappings
        if self.pattern.color_mappings:
            for old_color, new_color in self.pattern.color_mappings.items():
                result[state == old_color] = new_color

        # Apply rotation if detected
        if self.pattern.rotation_progression is not None:
            times = self.pattern.rotation_progression // 90
            result = np.rot90(result, times)

        # Resize to target
        result = self.evolve_to_target_size(result, target_size)

        return result


class CHIMERAv53:
    """
    CHIMERA v5.3 - Temporal Sequence Pattern Recognition

    "ARC is an IQ test. Treat it as a sequence interpolation problem.

    Each training example is a frame in a temporal sequence.
    Find the mathematical law that governs how frames evolve.
    Apply that law to predict the test frame.

    It's not about AGI reasoning - it's about pattern discovery."
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        print("=" * 80)
        print("CHIMERA v5.3 - TEMPORAL SEQUENCE PATTERN RECOGNITION")
        print("=" * 80)
        print("Approach: IQ Test / Sequence Interpolation")
        print("Each example = frame in temporal sequence")
        print("Task = detect sequence law and extrapolate")
        print("=" * 80)

    def solve_task(self, task: Dict) -> List[List]:
        """
        Solve ARC task by treating examples as temporal sequence.
        """
        if self.verbose:
            print(f"\n[TASK] Training frames: {len(task['train'])}, Test frames: {len(task['test'])}")

        # Step 1: Analyze sequence
        if self.verbose:
            print("[STEP 1] Analyzing temporal sequence...")

        analyzer = SequenceAnalyzer()
        pattern = analyzer.analyze_sequence(task['train'])

        if self.verbose:
            print(f"  -> Pattern confidence: {pattern.confidence:.2f}")
            if pattern.size_progression:
                print(f"  -> Size progression: {pattern.size_progression}")
            if pattern.color_mappings:
                print(f"  -> Color mappings: {pattern.color_mappings}")

        # Step 2: Predict test outputs
        if self.verbose:
            print("[STEP 2] Predicting test outputs...")

        ca = SequenceCA(pattern)
        solutions = []

        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])

            if self.verbose:
                print(f"  Test {test_idx}: {test_input.shape} grid")

            # Predict target size from pattern
            if pattern.size_progression:
                target_size = self._predict_size(task['train'], pattern)
            else:
                # Fallback: assume same size as last training output
                target_size = np.array(task['train'][-1]['output']).shape

            # Apply transformations
            attempt1 = ca.apply_pattern(test_input, target_size)
            attempt2 = ca.apply_pattern(test_input, target_size)  # Could vary with randomness

            solutions.append([attempt1.tolist(), attempt2.tolist()])

        return solutions

    def _predict_size(self, training_examples: List[Dict], pattern: TemporalPattern) -> Tuple[int, int]:
        """Predict target size based on detected progression."""
        output_sizes = [np.array(ex['output']).shape for ex in training_examples]

        if len(output_sizes) < 2:
            return output_sizes[-1]

        if pattern.size_progression[0] == 'arithmetic':
            _, delta_h, delta_w = pattern.size_progression
            last_h, last_w = output_sizes[-1]
            return (last_h + delta_h, last_w + delta_w)

        return output_sizes[-1]


def solve_arc_task(task: Dict, verbose: bool = False) -> List[List]:
    """Main entry point."""
    chimera = CHIMERAv53(verbose=verbose)
    return chimera.solve_task(task)


# ============================================================================
# TESTING & VALIDATION
# ============================================================================

if __name__ == "__main__":
    import json
    from pathlib import Path

    print("\n" + "=" * 80)
    print("CHIMERA v5.3 - SEQUENCE ANALYSIS TESTS")
    print("=" * 80)

    # Test 1: Simple size progression
    print("\n[TEST 1] Size Progression")
    task1 = {
        'train': [
            {'input': [[1, 1], [1, 1]], 'output': [[1, 1, 1], [1, 1, 1]]},
            {'input': [[2, 2], [2, 2]], 'output': [[2, 2, 2], [2, 2, 2]]},
        ],
        'test': [
            {'input': [[3, 3], [3, 3]]}
        ]
    }
    result1 = solve_arc_task(task1, verbose=True)
    print(f"Predicted output shape: {np.array(result1[0][0]).shape}")

    # Test 2: Color mapping
    print("\n[TEST 2] Color Mapping")
    task2 = {
        'train': [
            {'input': [[1, 1], [1, 1]], 'output': [[2, 2], [2, 2]]},
            {'input': [[3, 3], [3, 3]], 'output': [[4, 4], [4, 4]]},
        ],
        'test': [
            {'input': [[5, 5], [5, 5]]}
        ]
    }
    result2 = solve_arc_task(task2, verbose=True)

    # Test 3: Rotation
    print("\n[TEST 3] Rotation Pattern")
    task3 = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[3, 1], [4, 2]]},
        ],
        'test': [
            {'input': [[5, 6], [7, 8]]}
        ]
    }
    result3 = solve_arc_task(task3, verbose=True)

    print("\n" + "=" * 80)
    print("CHIMERA v5.3 READY")
    print("=" * 80)
