#!/usr/bin/env python3
"""
CHIMERA v5.3.1 - Inertia-Based Multiple Attempts Strategy
"When there are doubts, use inertia to break ties and prevent 0 output"

Philosophy: v5.3 is proven (2-5% accuracy). We enhance it with:
1. Multiple diverse attempts (like v5.3.1)
2. Inertia-based tie-breaking (from CHIMERA paper)
3. Less strict scoring (avoid rejecting valid solutions)
4. Momentum from previous frame state

When uncertain (scoring tie), favor solutions that:
- Continue the established pattern (inertial momentum)
- Use same colors/shapes as previous frames
- Don't dramatically change structure

This prevents zero outputs and allows model evolution.

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from chimera_v5_3 import CHIMERAv53, SequenceAnalyzer, SequenceCA, TemporalPattern
import time


class InertiaScorer:
    """
    Score solutions with inertia principle from CHIMERA paper.

    Key insight: When uncertain (scores are similar), use "impulso de inercia"
    to favor solutions that continue established patterns, not dramatic changes.
    """

    def __init__(self, training_examples: List[Dict]):
        self.training_examples = training_examples
        self.established_colors = self._extract_established_colors()
        self.established_shapes = self._extract_established_shapes()
        self.established_structure = self._extract_structure_features()

    def _extract_established_colors(self) -> set:
        """Colors that appear consistently in training."""
        all_colors = set()
        for ex in self.training_examples:
            all_colors.update(np.unique(ex['output']))
        return all_colors

    def _extract_established_shapes(self) -> List[Tuple[int, int]]:
        """Shapes that appear in training outputs."""
        return [np.array(ex['output']).shape for ex in self.training_examples]

    def _extract_structure_features(self) -> Dict:
        """Extract structural features from training."""
        features = {
            'avg_density': [],
            'color_distribution': {},
            'has_background': False
        }

        for ex in self.training_examples:
            output = np.array(ex['output'])
            features['avg_density'].append(np.count_nonzero(output) / output.size)

            # Color distribution
            for color in np.unique(output):
                count = np.sum(output == color)
                if color not in features['color_distribution']:
                    features['color_distribution'][color] = []
                features['color_distribution'][color].append(count)

        return features

    def score_with_inertia(self, solution: np.ndarray,
                          all_attempts: List[Dict],
                          test_input: np.ndarray) -> float:
        """
        Score using inertia principle.
        Base score + inertial momentum bonus.
        """
        base_score = self._base_score(solution)

        # Inertial momentum: favor solutions similar to established patterns
        inertia_bonus = self._inertia_momentum(solution, test_input)

        # Prevent zero-like outputs (CHIMERA principle)
        zero_penalty = self._zero_prevention_bonus(solution)

        return base_score + inertia_bonus + zero_penalty

    def _base_score(self, solution: np.ndarray) -> float:
        """Basic score without strict validation."""
        score = 0.5  # Start at 0.5 instead of 1.0 (less harsh baseline)

        # Soft bonus if uses training colors
        sol_colors = set(np.unique(solution))
        if sol_colors.issubset(self.established_colors):
            score += 0.5  # Softer bonus (was 1.5)
        elif len(sol_colors & self.established_colors) > 0:
            # Partial match: some known colors
            overlap_ratio = len(sol_colors & self.established_colors) / len(sol_colors)
            score += 0.2 * overlap_ratio

        # Bonus if has activity (not monochrome)
        if len(sol_colors) > 1:
            score += 0.3

        # Shape match bonus (soft)
        if solution.shape in self.established_shapes:
            score += 0.8  # Softer bonus (was 2.0)

        return score

    def _inertia_momentum(self, solution: np.ndarray, test_input: np.ndarray) -> float:
        """
        Inertial momentum: favor solutions that continue established patterns.
        This is the "impulso de inercia" from CHIMERA paper.
        """
        bonus = 0.0

        # 1. Size continuity (prefer established sizes)
        if solution.shape in self.established_shapes:
            bonus += 0.3

        # 2. Color continuity
        sol_colors = set(np.unique(solution))
        test_colors = set(np.unique(test_input))

        # Prefer solutions that expand test colors gradually
        if sol_colors & test_colors:  # Some overlap
            overlap_ratio = len(sol_colors & test_colors) / len(test_colors)
            bonus += 0.3 * overlap_ratio

        # 3. Structural continuity (density)
        sol_density = np.count_nonzero(solution) / solution.size

        for est_density in self.established_structure['avg_density']:
            if abs(sol_density - est_density) < 0.3:
                bonus += 0.2
                break

        # 4. Color distribution continuity
        for color in sol_colors:
            if color in self.established_structure['color_distribution']:
                bonus += 0.1

        return bonus

    def _zero_prevention_bonus(self, solution: np.ndarray) -> float:
        """
        Prevent zero-like outputs (all same color, or empty).
        CHIMERA principle: use inertia to prevent degenerate solutions.
        """
        unique_colors = len(np.unique(solution))

        # All same color (worst case)
        if unique_colors == 1:
            return -1.0  # Strong penalty

        # Very few colors (better than monochrome)
        if unique_colors < 3:
            return -0.2

        # Sufficient variation (good)
        return 0.2


class CHIMERAv531Inertia:
    """
    CHIMERA v5.3.1 with Inertia Principle

    Fixes the regression from v5.3 (2-5%) to v5.3.1 (1%) by:
    1. Using softer scoring (not too strict)
    2. Implementing inertia-based tie-breaking
    3. Allowing diverse solutions without conflicting
    4. Preventing zero outputs
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        print("=" * 80)
        print("CHIMERA v5.3.1 - INERTIA-BASED MULTIPLE ATTEMPTS")
        print("=" * 80)
        print("Core: v5.3 temporal sequence analyzer")
        print("Enhancement: Inertia-based tie-breaking + soft scoring")
        print("Principle: When uncertain, use impulso de inercia to prevent 0 output")
        print("=" * 80)

    def solve_task(self, task: Dict) -> List[List]:
        """Solve using inertia principle."""

        if self.verbose:
            print(f"\n[TASK] Training: {len(task['train'])}, Test: {len(task['test'])}")

        # Step 1: Analyze sequence
        analyzer = SequenceAnalyzer()
        pattern = analyzer.analyze_sequence(task['train'])

        if self.verbose:
            print(f"[PATTERN] Confidence: {pattern.confidence:.2f}")
            if pattern.color_mappings:
                print(f"  Color mappings: {pattern.color_mappings}")
            if pattern.size_progression:
                print(f"  Size progression: {pattern.size_progression}")

        # Step 2: Initialize inertia scorer
        inertia_scorer = InertiaScorer(task['train'])

        # Step 3: For each test, generate multiple solutions
        solutions = []

        for test_idx, test_case in enumerate(task['test']):
            test_input = np.array(test_case['input'])

            if self.verbose:
                print(f"\n[TEST {test_idx}] Input shape: {test_input.shape}")

            # Generate multiple attempts
            attempts = self._generate_attempts(
                test_input, task['train'], pattern
            )

            # Score with inertia principle
            for attempt in attempts:
                attempt['inertia_score'] = inertia_scorer.score_with_inertia(
                    attempt['output'], attempts, test_input
                )

            # Pick 2 best by inertia score
            if len(attempts) >= 2:
                best_2 = sorted(attempts,
                              key=lambda x: x['inertia_score'],
                              reverse=True)[:2]
                sol1 = best_2[0]['output'].tolist()
                sol2 = best_2[1]['output'].tolist()
                if self.verbose:
                    print(f"  -> Generated {len(attempts)} attempts")
                    print(f"     Best 1: inertia={best_2[0]['inertia_score']:.2f}, type={best_2[0]['type']}")
                    print(f"     Best 2: inertia={best_2[1]['inertia_score']:.2f}, type={best_2[1]['type']}")
            elif len(attempts) == 1:
                sol1 = attempts[0]['output'].tolist()
                sol2 = sol1
                if self.verbose:
                    print(f"  -> Generated 1 attempt")
            else:
                # Fallback
                sol1 = test_input.tolist()
                sol2 = sol1
                if self.verbose:
                    print(f"  -> No valid attempts, using fallback")

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
                    'type': 'standard',
                    'score': 1.0
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
                    'type': 'color_only',
                    'score': 0.8
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
                    'type': 'size_only',
                    'score': 0.7
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
                    'type': 'last_size',
                    'score': 0.6
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
                    'type': 'first_size',
                    'score': 0.5
                })
        except:
            pass

        # Attempt 6-9: Transformations
        for rot_deg, rot_times in [(90, 1), (180, 2), (270, 3)]:
            try:
                result = np.rot90(test_input.copy().astype(np.int64), rot_times)
                if pattern.color_mappings:
                    for old_color, new_color in pattern.color_mappings.items():
                        result[result == old_color] = new_color
                result = ca.evolve_to_target_size(result, target_size)
                if self._is_valid(result):
                    attempts.append({
                        'output': result,
                        'type': f'rotate_{rot_deg}',
                        'score': 0.4
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
                    'type': 'flip_h',
                    'score': 0.35
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
                    'type': 'flip_v',
                    'score': 0.3
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
                    'type': 'tile_2x2',
                    'score': 0.25
                })
        except:
            pass

        # Attempt 13: Identity (always include as fallback)
        try:
            result = test_input.copy().astype(np.int64)
            if self._is_valid(result):
                attempts.append({
                    'output': result,
                    'type': 'identity',
                    'score': 0.1
                })
        except:
            pass

        return attempts

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
    chimera = CHIMERAv531Inertia(verbose=verbose)
    return chimera.solve_task(task)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHIMERA v5.3.1 INERTIA - LOCAL TESTS")
    print("=" * 80)

    # Test 1: Simple case
    print("\n[TEST 1] Color Mapping with Inertia")
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
    print("CHIMERA v5.3.1 INERTIA READY")
    print("=" * 80)
