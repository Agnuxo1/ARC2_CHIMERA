#!/usr/bin/env python3
"""
CHIMERA v5.3.1 - Multiple Attempts Strategy
"Why choose one solution when Kaggle allows 2 attempts?"

Philosophy: v5.3 is proven (2-5% accuracy). Instead of reinventing,
generate multiple diverse attempts using v5.3's core engine with
different parameter variations.

Each test case generates 5-10 solutions (via v5.3 variations),
then returns the 2 with highest confidence.

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple
from chimera_v5_3 import CHIMERAv53, SequenceAnalyzer, SequenceCA, TemporalPattern
import time


class CHIMERAv531:
    """
    CHIMERA v5.3.1 - Multiple Attempts Strategy

    "v5.3 is good but commits to ONE solution per test case.
    Why not generate multiple and pick the 2 best?"

    Strategy:
    1. Use v5.3's proven SequenceAnalyzer to find the pattern
    2. Generate multiple variations of how to apply the pattern
    3. Score each variation
    4. Return top 2
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        print("=" * 80)
        print("CHIMERA v5.3.1 - MULTIPLE ATTEMPTS STRATEGY")
        print("=" * 80)
        print("Core: v5.3 temporal sequence analyzer")
        print("Enhancement: Generate 5-10 variations per test, pick 2 best")
        print("=" * 80)

    def solve_task(self, task: Dict) -> List[List]:
        """Solve using multiple attempt strategy"""

        if self.verbose:
            print(f"\n[TASK] Training: {len(task['train'])}, Test: {len(task['test'])}")

        # Step 1: Analyze sequence (standard v5.3)
        analyzer = SequenceAnalyzer()
        pattern = analyzer.analyze_sequence(task['train'])

        if self.verbose:
            print(f"[PATTERN] Confidence: {pattern.confidence:.2f}")
            if pattern.color_mappings:
                print(f"  Color mappings: {pattern.color_mappings}")
            if pattern.size_progression:
                print(f"  Size progression: {pattern.size_progression}")

        # Step 2: For each test, generate multiple solutions
        solutions = []

        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])

            if self.verbose:
                print(f"\n[TEST {test_idx}] Input shape: {test_input.shape}")

            # Generate multiple attempts
            attempts = self._generate_attempts(
                test_input, task['train'], pattern
            )

            # Pick 2 best
            if len(attempts) >= 2:
                best_2 = sorted(attempts, key=lambda x: x['score'], reverse=True)[:2]
                sol1 = best_2[0]['output'].tolist()
                sol2 = best_2[1]['output'].tolist()
                if self.verbose:
                    print(f"  -> Generated {len(attempts)} attempts")
                    print(f"     Best 1: score={best_2[0]['score']:.2f}, type={best_2[0]['type']}")
                    print(f"     Best 2: score={best_2[1]['score']:.2f}, type={best_2[1]['type']}")
            elif len(attempts) == 1:
                sol1 = attempts[0]['output'].tolist()
                sol2 = sol1  # Repeat if only one
                if self.verbose:
                    print(f"  -> Generated 1 attempt")
            else:
                # Fallback: return test input as-is
                sol1 = test_input.tolist()
                sol2 = sol1
                if self.verbose:
                    print(f"  -> No valid attempts generated, using fallback")

            solutions.append([sol1, sol2])

        return solutions

    def _generate_attempts(self, test_input: np.ndarray, training_examples: List[Dict],
                          pattern: TemporalPattern) -> List[Dict]:
        """Generate multiple attempt variations"""

        attempts = []
        ca = SequenceCA(pattern)

        # Predict target size
        target_size = self._predict_target_size(training_examples, pattern)

        # Attempt 1: Standard v5.3 approach
        try:
            result = ca.apply_pattern(test_input, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'standard'
                })
        except:
            pass

        # Attempt 2: Just color mapping, no resize
        try:
            result = test_input.copy().astype(np.int64)
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[test_input == old_color] = new_color
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'color_only'
                })
        except:
            pass

        # Attempt 3: Size progression only
        try:
            result = test_input.copy().astype(np.int64)
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'size_only'
                })
        except:
            pass

        # Attempt 4: Try with last training output size
        try:
            last_output_size = np.array(training_examples[-1]['output']).shape
            result = ca.apply_pattern(test_input, last_output_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'last_size'
                })
        except:
            pass

        # Attempt 5: Try with first training output size
        try:
            first_output_size = np.array(training_examples[0]['output']).shape
            result = ca.apply_pattern(test_input, first_output_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'first_size'
                })
        except:
            pass

        # Attempt 6: Try rotation 90 degrees
        try:
            result = np.rot90(test_input.copy().astype(np.int64), 1)
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'rotate_90'
                })
        except:
            pass

        # Attempt 7: Try rotation 180 degrees
        try:
            result = np.rot90(test_input.copy().astype(np.int64), 2)
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'rotate_180'
                })
        except:
            pass

        # Attempt 8: Try horizontal flip
        try:
            result = np.fliplr(test_input.copy().astype(np.int64))
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'flip_h'
                })
        except:
            pass

        # Attempt 9: Try vertical flip
        try:
            result = np.flipud(test_input.copy().astype(np.int64))
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'flip_v'
                })
        except:
            pass

        # Attempt 10: Try tiling/replication
        try:
            # Try 2x2 tiling
            result = np.tile(test_input.copy().astype(np.int64), (2, 2))
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples),
                    'type': 'tile_2x2'
                })
        except:
            pass

        # Attempt 11: Identity (no change) - always last resort
        try:
            result = test_input.copy().astype(np.int64)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'score': self._score_solution(result, training_examples) - 0.5,  # Penalize identity
                    'type': 'identity'
                })
        except:
            pass

        return attempts

    def _predict_target_size(self, training_examples: List[Dict],
                            pattern: TemporalPattern) -> Tuple[int, int]:
        """Predict target size"""
        output_sizes = [np.array(ex['output']).shape for ex in training_examples]

        if len(output_sizes) < 2:
            return output_sizes[-1] if output_sizes else (10, 10)

        # Check for progression
        deltas_h = []
        deltas_w = []

        for i in range(len(output_sizes) - 1):
            h1, w1 = output_sizes[i]
            h2, w2 = output_sizes[i + 1]
            deltas_h.append(h2 - h1)
            deltas_w.append(w2 - w1)

        if deltas_h and deltas_w:
            avg_dh = int(np.mean(deltas_h))
            avg_dw = int(np.mean(deltas_w))

            if abs(np.std(deltas_h)) < 0.5:
                last_h, last_w = output_sizes[-1]
                next_h = max(1, min(30, last_h + avg_dh))
                next_w = max(1, min(30, last_w + avg_dw))
                return (next_h, next_w)

        return output_sizes[-1]

    def _is_valid(self, grid: np.ndarray) -> bool:
        """Check if grid is valid per ARC spec"""
        try:
            if grid.ndim != 2:
                return False
            h, w = grid.shape
            if not (1 <= h <= 30 and 1 <= w <= 30):
                return False
            unique_vals = np.unique(grid)
            return all(0 <= int(v) <= 9 for v in unique_vals)
        except:
            return False

    def _score_solution(self, solution: np.ndarray, training_examples: List[Dict]) -> float:
        """Score how good this solution is"""
        score = 1.0  # Base score

        # Collect training properties
        train_colors = set()
        train_outputs = []
        train_shapes = []

        for ex in training_examples:
            output = np.array(ex['output'])
            train_colors.update(np.unique(output))
            train_outputs.append(output)
            train_shapes.append(output.shape)

        # Bonus if uses training colors
        sol_colors = set(np.unique(solution))
        if sol_colors.issubset(train_colors):
            score += 1.5  # Strong bonus for using only known colors

        # Bonus if has activity (not all same color)
        if len(sol_colors) > 1:
            score += 0.5

        # Check if shape matches any training shape (strong indicator of quality)
        if solution.shape in train_shapes:
            score += 2.0

        # Bonus for spatial coherence
        if solution.size > 1:
            h, w = solution.shape
            changes = 0
            total = 0

            for i in range(h):
                for j in range(w - 1):
                    if solution[i, j] != solution[i, j + 1]:
                        changes += 1
                    total += 1

            for i in range(h - 1):
                for j in range(w):
                    if solution[i, j] != solution[i + 1, j]:
                        changes += 1
                    total += 1

            if total > 0:
                coherence = 1.0 - (changes / total)
                score += max(0, coherence) * 0.5

        # Penalty for unusual sizes
        if solution.shape not in train_shapes:
            # Penalize differently sized outputs
            score -= 0.2

        return score


def solve_arc_task(task: Dict, verbose: bool = False) -> List[List]:
    """Main entry point"""
    chimera = CHIMERAv531(verbose=verbose)
    return chimera.solve_task(task)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHIMERA v5.3.1 - LOCAL TESTS")
    print("=" * 80)

    # Test 1: Simple case
    print("\n[TEST 1] Color Mapping")
    task1 = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[2, 3], [4, 5]]},
            {'input': [[5, 6]], 'output': [[6, 7]]},
        ],
        'test': [
            {'input': [[1, 2], [3, 4]]}
        ]
    }
    result1 = solve_arc_task(task1, verbose=True)
    print(f"Result: {result1[0][0]}")

    print("\n" + "=" * 80)
    print("CHIMERA v5.3.1 READY")
    print("=" * 80)
