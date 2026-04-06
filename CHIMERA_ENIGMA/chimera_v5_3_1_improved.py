#!/usr/bin/env python3
"""
CHIMERA v5.3.1 - Improved Scoring (Less Strict)
"Fix the regression by using softer scoring, not stricter validation"

The original v5.3.1 regressed from 2% to 1% because the SolutionScorer
was too harsh. This version fixes that by:

1. Removing strict color validation
2. Using softer bonuses/penalties
3. Accepting identity solutions more readily
4. Following inertia principle: when uncertain, allow the solution

Philosophy: The problem isn't that v5.3.1 generates wrong solutions.
The problem is that it REJECTS valid solutions by being too strict.

Solution: Trust v5.3's core logic but score more permissively.
"""

import numpy as np
from typing import List, Dict, Tuple
from chimera_v5_3 import CHIMERAv53, SequenceAnalyzer, SequenceCA, TemporalPattern
import time


class CHIMERAv531Improved:
    """
    CHIMERA v5.3.1 - Improved with Softer Scoring

    Key changes from original v5.3.1:
    - Score function is less penalizing
    - Accept more solutions (remove strict validation)
    - Trust v5.3 core + multiple attempts strategy
    - Use inertia principle: when uncertain, allow solution through
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        print("=" * 80)
        print("CHIMERA v5.3.1 - IMPROVED SCORING (LESS STRICT)")
        print("=" * 80)
        print("Core: v5.3 temporal sequence analyzer")
        print("Improvement: Softer scoring to fix 2%->1% regression")
        print("Philosophy: Don't reject valid solutions by being too strict")
        print("=" * 80)

    def solve_task(self, task: Dict) -> List[List]:
        """Solve using improved scoring."""

        if self.verbose:
            print(f"\n[TASK] Training: {len(task['train'])}, Test: {len(task['test'])}")

        # Step 1: Analyze sequence
        analyzer = SequenceAnalyzer()
        pattern = analyzer.analyze_sequence(task['train'])

        if self.verbose:
            print(f"[PATTERN] Confidence: {pattern.confidence:.2f}")

        # Step 2: Generate multiple solutions
        solutions = []

        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])

            if self.verbose:
                print(f"\n[TEST {test_idx}] Input shape: {test_input.shape}")

            # Generate multiple attempts
            attempts = self._generate_attempts(test_input, task['train'], pattern)

            # Score and pick 2 best
            if len(attempts) >= 2:
                # Score each attempt (softer scoring)
                for attempt in attempts:
                    attempt['improved_score'] = self._score_improved(
                        attempt['output'], task['train']
                    )

                best_2 = sorted(attempts, key=lambda x: x['improved_score'], reverse=True)[:2]
                sol1 = best_2[0]['output'].tolist()
                sol2 = best_2[1]['output'].tolist()

                if self.verbose:
                    print(f"  -> Generated {len(attempts)} attempts")
                    print(f"     Best 1: score={best_2[0]['improved_score']:.2f}, type={best_2[0]['type']}")
                    print(f"     Best 2: score={best_2[1]['improved_score']:.2f}, type={best_2[1]['type']}")
            elif len(attempts) == 1:
                sol1 = attempts[0]['output'].tolist()
                sol2 = sol1
            else:
                sol1 = test_input.tolist()
                sol2 = sol1

            solutions.append([sol1, sol2])

        return solutions

    def _generate_attempts(self, test_input: np.ndarray,
                          training_examples: List[Dict],
                          pattern: TemporalPattern) -> List[Dict]:
        """Generate multiple attempt variations."""

        attempts = []
        ca = SequenceCA(pattern)
        target_size = self._predict_target_size(training_examples, pattern)

        # Attempt 1: Standard v5.3 approach
        try:
            result = ca.apply_pattern(test_input, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'standard'
                })
        except:
            pass

        # Attempt 2: Just color mapping
        try:
            result = test_input.copy().astype(np.int64)
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[test_input == old_color] = new_color
            if self._is_valid(result):
                attempts.append({
                    'output': result,
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
                    'type': 'size_only'
                })
        except:
            pass

        # Attempt 4: Last training output size
        try:
            last_output_size = np.array(training_examples[-1]['output']).shape
            result = ca.apply_pattern(test_input, last_output_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'last_size'
                })
        except:
            pass

        # Attempt 5: First training output size
        try:
            first_output_size = np.array(training_examples[0]['output']).shape
            result = ca.apply_pattern(test_input, first_output_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'first_size'
                })
        except:
            pass

        # Attempt 6-9: Rotations
        for rot_times, rot_deg in [(1, 90), (2, 180), (3, 270)]:
            try:
                result = np.rot90(test_input.copy().astype(np.int64), rot_times)
                if pattern.color_mappings:
                    for old_color, new_color in pattern.color_mappings.items():
                        result[result == old_color] = new_color
                result = ca.evolve_to_target_size(result, target_size)
                if self._is_valid(result):
                    attempts.append({
                        'output': result,
                        'type': f'rotate_{rot_deg}'
                    })
            except:
                pass

        # Attempt 10: Horizontal flip
        try:
            result = np.fliplr(test_input.copy().astype(np.int64))
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'flip_h'
                })
        except:
            pass

        # Attempt 11: Vertical flip
        try:
            result = np.flipud(test_input.copy().astype(np.int64))
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            result = ca.evolve_to_target_size(result, target_size)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'flip_v'
                })
        except:
            pass

        # Attempt 12: Tiling
        try:
            result = np.tile(test_input.copy().astype(np.int64), (2, 2))
            if pattern.color_mappings:
                for old_color, new_color in pattern.color_mappings.items():
                    result[result == old_color] = new_color
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'tile_2x2'
                })
        except:
            pass

        # Attempt 13: Identity (no change)
        try:
            result = test_input.copy().astype(np.int64)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'identity'
                })
        except:
            pass

        return attempts

    def _score_improved(self, solution: np.ndarray, training_examples: List[Dict]) -> float:
        """
        Improved scoring - MUCH softer than original v5.3.1.

        Original was too strict. This version:
        - Starts at 0.0 (no base penalty)
        - Gives bonuses for good properties
        - Never penalizes (only positive feedback)
        """
        score = 0.0

        # Get training properties
        train_shapes = [np.array(ex['output']).shape for ex in training_examples]
        train_colors = set()
        for ex in training_examples:
            train_colors.update(np.unique(ex['output']))

        sol_colors = set(np.unique(solution))

        # Bonus 1: Shape match (strong indicator)
        if solution.shape in train_shapes:
            score += 2.0

        # Bonus 2: Uses training colors
        if sol_colors.issubset(train_colors):
            score += 1.0
        elif len(sol_colors & train_colors) > 0:
            # Partial match
            score += 0.5

        # Bonus 3: Has activity (not monochrome)
        if len(sol_colors) > 1:
            score += 0.5

        # Bonus 4: Spatial coherence
        if solution.size > 1:
            h, w = solution.shape
            changes = 0
            total = 0

            for i in range(h):
                for j in range(w - 1):
                    if solution[i, j] != solution[i, j + 1]:
                        changes += 1
                    total += 1

            if total > 0:
                coherence = 1.0 - (changes / total)
                score += max(0, coherence) * 0.5

        return score

    def _predict_target_size(self, training_examples: List[Dict],
                            pattern: TemporalPattern) -> Tuple[int, int]:
        """Predict target size."""
        output_sizes = [np.array(ex['output']).shape for ex in training_examples]

        if len(output_sizes) < 2:
            return output_sizes[-1] if output_sizes else (10, 10)

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
        """Check if grid is valid per ARC spec."""
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


def solve_arc_task(task: Dict, verbose: bool = False) -> List[List]:
    """Main entry point."""
    chimera = CHIMERAv531Improved(verbose=verbose)
    return chimera.solve_task(task)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHIMERA v5.3.1 IMPROVED - LOCAL TESTS")
    print("=" * 80)

    # Test 1: Simple case
    print("\n[TEST 1] Color Mapping with Improved Scoring")
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
    print("CHIMERA v5.3.1 IMPROVED READY")
    print("=" * 80)
