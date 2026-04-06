#!/usr/bin/env python3
"""
CHIMERA v5.4 - Geometric Transformation Detection
"Enhanced Temporal Sequence Analysis with Geometric Transforms"

Improvements over v5.3:
- Detect tiling/replication patterns
- Detect progressive rotations
- Detect scaling and expansion
- Detect object movement patterns
- Apply transformations correctly to test inputs

Philosophy: Same as v5.3 (temporal sequences)
But now we understand WHAT KIND of transformation happens frame by frame.

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import time
from collections import Counter
from scipy.ndimage import zoom


@dataclass
class GeometricTransform:
    """Represents a detected geometric transformation"""
    transform_type: str  # 'rotation', 'flip', 'scale', 'tile', 'move', 'fill', 'identity'
    params: Dict = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class TemporalPattern:
    """Enhanced pattern with geometric transforms"""
    size_progression: Optional[Tuple] = None
    color_mappings: Optional[Dict[int, int]] = None
    transforms: List[GeometricTransform] = field(default_factory=list)
    position_deltas: Optional[List[Tuple[int, int]]] = None
    invariant_colors: Optional[Set[int]] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.color_mappings is None:
            self.color_mappings = {}
        if self.invariant_colors is None:
            self.invariant_colors = set()


class GeometricAnalyzer:
    """Detect geometric transformations in training examples"""

    @staticmethod
    def detect_tiling(inp: np.ndarray, out: np.ndarray) -> Optional[GeometricTransform]:
        """
        Detect if output is a tiled/replicated version of input.

        Example: 2x2 → 6x6 (tiled 3x3)
        """
        h_in, w_in = inp.shape
        h_out, w_out = out.shape

        if h_in == 0 or w_in == 0:
            return None

        # Check if output size is integer multiple
        h_ratio = h_out / h_in
        w_ratio = w_out / w_in

        if h_ratio != int(h_ratio) or w_ratio != int(w_ratio):
            return None

        h_ratio, w_ratio = int(h_ratio), int(w_ratio)

        # Try tiling
        if h_ratio > 1 or w_ratio > 1:
            tiled = np.tile(inp, (h_ratio, w_ratio))
            if np.array_equal(tiled, out):
                return GeometricTransform(
                    transform_type='tile',
                    params={'h_ratio': h_ratio, 'w_ratio': w_ratio},
                    confidence=1.0
                )

        return None

    @staticmethod
    def detect_rotation(inp: np.ndarray, out: np.ndarray) -> Optional[GeometricTransform]:
        """Detect if output is a rotated version of input"""
        if inp.shape != out.shape:
            return None

        # Try each rotation
        for times in range(1, 4):  # 90, 180, 270
            rotated = np.rot90(inp, times)
            if np.array_equal(rotated, out):
                return GeometricTransform(
                    transform_type='rotation',
                    params={'degrees': times * 90},
                    confidence=1.0
                )

        return None

    @staticmethod
    def detect_flip(inp: np.ndarray, out: np.ndarray) -> Optional[GeometricTransform]:
        """Detect if output is a flipped version of input"""
        if inp.shape != out.shape:
            return None

        # Horizontal flip
        if np.array_equal(np.fliplr(inp), out):
            return GeometricTransform(
                transform_type='flip',
                params={'axis': 'horizontal'},
                confidence=1.0
            )

        # Vertical flip
        if np.array_equal(np.flipud(inp), out):
            return GeometricTransform(
                transform_type='flip',
                params={'axis': 'vertical'},
                confidence=1.0
            )

        return None

    @staticmethod
    def detect_object_movement(inp: np.ndarray, out: np.ndarray) -> Optional[GeometricTransform]:
        """
        Detect if objects move within the grid.
        Find center of mass of non-zero elements.
        """
        if inp.shape != out.shape:
            return None

        # Get non-zero positions in input
        inp_coords = np.argwhere(inp != 0)
        out_coords = np.argwhere(out != 0)

        if len(inp_coords) == 0 or len(out_coords) == 0:
            return None

        # Calculate center of mass
        inp_center = np.mean(inp_coords, axis=0)
        out_center = np.mean(out_coords, axis=0)

        delta = out_center - inp_center

        if not np.allclose(delta, [0, 0]):
            return GeometricTransform(
                transform_type='move',
                params={'delta_row': float(delta[0]), 'delta_col': float(delta[1])},
                confidence=0.7
            )

        return None

    @staticmethod
    def detect_fill_pattern(inp: np.ndarray, out: np.ndarray) -> Optional[GeometricTransform]:
        """
        Detect if output fills in patterns.
        Example: sparse points → connected lines
        """
        if inp.shape != out.shape:
            return None

        # Count non-zero pixels
        inp_count = np.count_nonzero(inp)
        out_count = np.count_nonzero(out)

        # If output has more non-zero pixels, it's likely a fill
        if out_count > inp_count:
            fill_factor = out_count / inp_count if inp_count > 0 else 1.0
            return GeometricTransform(
                transform_type='fill',
                params={'fill_factor': fill_factor},
                confidence=0.6
            )

        return None

    @staticmethod
    def detect_scaling(inp: np.ndarray, out: np.ndarray) -> Optional[GeometricTransform]:
        """
        Detect if output is a scaled version of input.
        """
        h_in, w_in = inp.shape
        h_out, w_out = out.shape

        if h_in == 0 or w_in == 0:
            return None

        h_ratio = h_out / h_in
        w_ratio = w_out / w_in

        # Try zoom-nearest neighbor
        try:
            scaled = zoom(inp, (h_ratio, w_ratio), order=0).astype(inp.dtype)
            if np.array_equal(scaled, out):
                return GeometricTransform(
                    transform_type='scale',
                    params={'h_ratio': h_ratio, 'w_ratio': w_ratio},
                    confidence=0.8
                )
        except:
            pass

        return None


class EnhancedSequenceAnalyzer:
    """Analyze training examples with geometric understanding"""

    def __init__(self):
        self.geom_analyzer = GeometricAnalyzer()

    def analyze_sequence(self, training_examples: List[Dict]) -> TemporalPattern:
        """Analyze sequence with geometric transforms"""

        pattern = TemporalPattern()

        if len(training_examples) < 1:
            return pattern

        # Extract frames
        frames = []
        for example in training_examples:
            inp = np.array(example['input'])
            out = np.array(example['output'])
            frames.append({'input': inp, 'output': out})

        # Detect size progression
        pattern.size_progression = self._detect_size_progression(frames)

        # Detect color mappings
        pattern.color_mappings = self._detect_color_mappings(frames)

        # Detect geometric transforms in each frame
        pattern.transforms = self._detect_transforms(frames)

        # Detect invariants
        pattern.invariant_colors = self._detect_invariants(frames)

        # Calculate confidence
        pattern.confidence = self._calculate_confidence(pattern, frames)

        return pattern

    def _detect_size_progression(self, frames: List) -> Optional[Tuple]:
        """Detect how size changes"""
        output_sizes = [f['output'].shape for f in frames]

        if len(output_sizes) < 2:
            return None

        deltas_h = []
        deltas_w = []

        for i in range(len(output_sizes) - 1):
            h1, w1 = output_sizes[i]
            h2, w2 = output_sizes[i + 1]
            deltas_h.append(h2 - h1)
            deltas_w.append(w2 - w1)

        # Check arithmetic progression
        if len(deltas_h) > 0:
            avg_delta_h = np.mean(deltas_h)
            avg_delta_w = np.mean(deltas_w)

            if abs(np.std(deltas_h)) < 0.5 and abs(np.std(deltas_w)) < 0.5:
                return ('arithmetic', int(avg_delta_h), int(avg_delta_w))

        return None

    def _detect_color_mappings(self, frames: List) -> Dict[int, int]:
        """Detect stable color mappings"""
        mapping = {}

        for frame in frames:
            inp = frame['input']
            out = frame['output']

            # Skip if shapes don't match
            if inp.shape != out.shape:
                continue

            # Find color mappings
            for color in set(inp.flatten()):
                mask = (inp == color)
                out_colors = out[mask]

                if len(out_colors) > 0:
                    most_common = Counter(out_colors).most_common(1)[0][0]

                    if color not in mapping:
                        mapping[color] = most_common
                    elif mapping[color] != most_common:
                        # Inconsistent mapping - remove it
                        mapping.pop(color, None)

        return mapping

    def _detect_transforms(self, frames: List) -> List[GeometricTransform]:
        """Detect geometric transforms applied"""
        transforms = []

        for frame in frames:
            inp = frame['input']
            out = frame['output']

            # Try each transform type
            candidates = [
                self.geom_analyzer.detect_tiling(inp, out),
                self.geom_analyzer.detect_rotation(inp, out),
                self.geom_analyzer.detect_flip(inp, out),
                self.geom_analyzer.detect_scaling(inp, out),
                self.geom_analyzer.detect_fill_pattern(inp, out),
                self.geom_analyzer.detect_object_movement(inp, out),
            ]

            # Take highest confidence
            best = max(
                [c for c in candidates if c is not None],
                key=lambda x: x.confidence,
                default=None
            )

            if best:
                transforms.append(best)

        return transforms

    def _detect_invariants(self, frames: List) -> Set[int]:
        """Find colors that never change"""
        invariant = set()

        if not frames:
            return invariant

        # Colors in first frame
        first_colors = set(frames[0]['input'].flatten())

        for color in first_colors:
            # Check if this color appears in both input and output of all frames
            appears_in_all = True
            for frame in frames:
                if color not in set(frame['input'].flatten()):
                    appears_in_all = False
                    break

            if appears_in_all:
                invariant.add(color)

        return invariant

    def _calculate_confidence(self, pattern: TemporalPattern, frames: List) -> float:
        """Calculate pattern confidence"""
        confidence = 0.0

        if pattern.size_progression:
            confidence += 0.2
        if pattern.color_mappings:
            confidence += 0.3
        if pattern.transforms:
            confidence += 0.3
        if pattern.invariant_colors:
            confidence += 0.2

        return min(confidence, 1.0)


class GeometricCA:
    """CA guided by detected geometric patterns"""

    def __init__(self, pattern: TemporalPattern):
        self.pattern = pattern

    def apply_transforms(self, state: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Apply detected transforms to state (CONSERVATIVELY)"""
        result = state.copy()

        # 1. Apply color mappings (ALWAYS safe)
        if self.pattern.color_mappings:
            for old_color, new_color in self.pattern.color_mappings.items():
                result[state == old_color] = new_color

        # 2. Apply geometric transforms ONLY if HIGH CONFIDENCE
        if self.pattern.transforms and self.pattern.confidence > 0.4:
            # Only apply the MOST CONFIDENT transform, not all of them
            best_trans = max(self.pattern.transforms, key=lambda t: t.confidence)

            if best_trans.confidence > 0.6:  # High confidence threshold
                if best_trans.transform_type == 'rotation':
                    times = best_trans.params.get('degrees', 90) // 90
                    result = np.rot90(result, times)

                elif best_trans.transform_type == 'flip':
                    axis = best_trans.params.get('axis', 'horizontal')
                    if axis == 'horizontal':
                        result = np.fliplr(result)
                    else:
                        result = np.flipud(result)

                elif best_trans.transform_type == 'tile':
                    h_ratio = best_trans.params.get('h_ratio', 1)
                    w_ratio = best_trans.params.get('w_ratio', 1)
                    if h_ratio > 1 or w_ratio > 1:
                        result = np.tile(result, (h_ratio, w_ratio))

                elif best_trans.transform_type == 'scale':
                    h_ratio = best_trans.params.get('h_ratio', 1.0)
                    w_ratio = best_trans.params.get('w_ratio', 1.0)
                    if h_ratio != 1.0 and w_ratio != 1.0:
                        result = zoom(result, (h_ratio, w_ratio), order=0).astype(result.dtype)

        # 3. Resize to target size if needed
        if result.shape != target_size:
            result = self._resize_to_target(result, target_size)

        return result

    def _resize_to_target(self, state: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Resize to target size"""
        h_curr, w_curr = state.shape
        h_targ, w_targ = target_size

        if h_curr == h_targ and w_curr == w_targ:
            return state

        h_ratio = h_targ / h_curr if h_curr > 0 else 1.0
        w_ratio = w_targ / w_curr if w_curr > 0 else 1.0

        return zoom(state, (h_ratio, w_ratio), order=0).astype(state.dtype)


class CHIMERAv54:
    """
    CHIMERA v5.4 - Geometric Transformation Detection

    "Same temporal sequence thinking, but now we understand the GEOMETRY.
    Not just 'what changes' but 'HOW it changes' (rotation, scale, tile, move, fill).
    This understanding lets us apply transforms correctly to test inputs."
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        print("=" * 80)
        print("CHIMERA v5.4 - GEOMETRIC TRANSFORMATION DETECTION")
        print("=" * 80)
        print("Approach: Temporal sequences + Geometric understanding")
        print("Detects: Rotation, Flip, Scale, Tiling, Movement, Fill")
        print("=" * 80)

    def solve_task(self, task: Dict) -> List[List]:
        """Solve task with geometric awareness"""

        if self.verbose:
            print(f"\n[TASK] Training frames: {len(task['train'])}, Test: {len(task['test'])}")

        # Analyze sequence
        analyzer = EnhancedSequenceAnalyzer()
        pattern = analyzer.analyze_sequence(task['train'])

        if self.verbose:
            print(f"  -> Confidence: {pattern.confidence:.2f}")
            if pattern.transforms:
                print(f"  -> Transforms: {[t.transform_type for t in pattern.transforms]}")
            if pattern.color_mappings:
                print(f"  -> Color maps: {pattern.color_mappings}")

        # Predict and apply
        ca = GeometricCA(pattern)
        solutions = []

        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])

            if self.verbose:
                print(f"  Test {test_idx}: {test_input.shape} grid")

            # Predict target size
            target_size = self._predict_target_size(task['train'], pattern)

            # Apply transforms
            attempt1 = ca.apply_transforms(test_input, target_size)
            attempt2 = ca.apply_transforms(test_input, target_size)

            solutions.append([attempt1.tolist(), attempt2.tolist()])

        return solutions

    def _predict_target_size(self, training_examples: List[Dict], pattern: TemporalPattern) -> Tuple[int, int]:
        """Predict target size from pattern"""
        output_sizes = [np.array(ex['output']).shape for ex in training_examples]

        if not output_sizes:
            return (10, 10)

        if len(output_sizes) < 2:
            return output_sizes[-1]

        # Use size progression if detected
        if pattern.size_progression:
            prog_type, delta_h, delta_w = pattern.size_progression
            last_h, last_w = output_sizes[-1]

            if prog_type == 'arithmetic':
                return (last_h + delta_h, last_w + delta_w)

        # Otherwise use last output size
        return output_sizes[-1]


def solve_arc_task(task: Dict, verbose: bool = False) -> List[List]:
    """Main entry point"""
    chimera = CHIMERAv54(verbose=verbose)
    return chimera.solve_task(task)


if __name__ == "__main__":
    import json
    from pathlib import Path

    print("\n" + "=" * 80)
    print("CHIMERA v5.4 - GEOMETRIC TRANSFORMATION TESTS")
    print("=" * 80)

    # Test 1: Rotation
    print("\n[TEST 1] Rotation Detection")
    task1 = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[3, 1], [4, 2]]},  # 90° rotation
        ],
        'test': [
            {'input': [[5, 6], [7, 8]]}
        ]
    }
    result1 = solve_arc_task(task1, verbose=True)
    print(f"Predicted: {result1[0][0]}")

    # Test 2: Tiling
    print("\n[TEST 2] Tiling Detection")
    task2 = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[1, 2, 1, 2], [3, 4, 3, 4]]},
        ],
        'test': [
            {'input': [[5, 6], [7, 8]]}
        ]
    }
    result2 = solve_arc_task(task2, verbose=True)
    print(f"Predicted shape: {np.array(result2[0][0]).shape}")

    # Test 3: Color mapping + rotation
    print("\n[TEST 3] Combined Transforms")
    task3 = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[8, 5], [9, 6]]},
        ],
        'test': [
            {'input': [[1, 2], [3, 4]]}
        ]
    }
    result3 = solve_arc_task(task3, verbose=True)

    print("\n" + "=" * 80)
    print("CHIMERA v5.4 READY")
    print("=" * 80)
