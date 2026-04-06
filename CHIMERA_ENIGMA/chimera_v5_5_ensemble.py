#!/usr/bin/env python3
"""
CHIMERA v5.5 - Ensemble Approach
"Multiple strategies, pick the best"

The insight: Different ARC tasks need different strategies.
- Some need color mapping (v5.3 strategy)
- Some need geometric transforms (v5.4 strategy)
- Some need size progression only

Solution: Try BOTH v5.3 and v5.4, return the one with highest "confidence"

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import numpy as np
from typing import List, Dict, Tuple
from chimera_v5_3 import solve_arc_task as solve_v53
from chimera_v5_4 import solve_arc_task as solve_v54


class EnsembleCHIMERA:
    """
    Ensemble of v5.3 (simple) and v5.4 (geometric).

    For each test case, we generate solutions from both and pick
    the one that looks "better" based on heuristics.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        print("=" * 80)
        print("CHIMERA v5.5 - ENSEMBLE APPROACH")
        print("=" * 80)
        print("Strategy: Multiple algorithms + intelligent voting")
        print("Combines v5.3 (simple) and v5.4 (geometric)")
        print("=" * 80)

    def solve_task(self, task: Dict) -> List[List]:
        """Solve task using ensemble approach"""

        if self.verbose:
            print(f"\n[TASK] Training: {len(task['train'])}, Test: {len(task['test'])}")

        solutions = []

        # Get solutions from both strategies
        try:
            sol_v53 = solve_v53(task, verbose=False)
        except Exception as e:
            if self.verbose:
                print(f"  v5.3 failed: {str(e)[:50]}")
            sol_v53 = [[np.zeros_like(np.array(task['train'][0]['output'])).tolist(),
                        np.zeros_like(np.array(task['train'][0]['output'])).tolist()]] * len(task['test'])

        try:
            sol_v54 = solve_v54(task, verbose=False)
        except Exception as e:
            if self.verbose:
                print(f"  v5.4 failed: {str(e)[:50]}")
            sol_v54 = [[np.zeros_like(np.array(task['train'][0]['output'])).tolist(),
                        np.zeros_like(np.array(task['train'][0]['output'])).tolist()]] * len(task['test'])

        # For each test case, pick the better solution
        for test_idx in range(len(task['test'])):
            if test_idx < len(sol_v53) and test_idx < len(sol_v54):
                # Both have solutions - pick the better one
                attempt1, attempt2 = self._pick_better_solution(sol_v53[test_idx], sol_v54[test_idx])
                solutions.append([attempt1, attempt2])
            elif test_idx < len(sol_v53):
                solutions.append(sol_v53[test_idx])
            elif test_idx < len(sol_v54):
                solutions.append(sol_v54[test_idx])

        return solutions

    def _pick_better_solution(self, sol_v53: List, sol_v54: List) -> Tuple[List, List]:
        """
        Pick the better solution set from v5.3 and v5.4.

        Heuristics:
        1. Prefer non-zero solutions (activity)
        2. Prefer solutions with consistent patterns
        3. Prefer solutions that match training distribution
        """

        # Convert to arrays
        v53_arr = [np.array(s) for s in sol_v53]
        v54_arr = [np.array(s) for s in sol_v54]

        # Score based on heuristics
        v53_score = sum(self._score_solution(s) for s in v53_arr)
        v54_score = sum(self._score_solution(s) for s in v54_arr)

        if v53_score >= v54_score:
            return sol_v53[0], sol_v53[1]
        else:
            return sol_v54[0], sol_v54[1]

    def _score_solution(self, solution: np.ndarray) -> float:
        """
        Score a solution based on characteristics.
        Higher = better
        """
        score = 0.0

        # Prefer non-zero solutions
        non_zero_ratio = np.count_nonzero(solution) / solution.size
        score += non_zero_ratio * 10.0

        # Prefer solutions with consistent local patterns
        # (i.e., groups of same color are spatially coherent)
        if solution.size > 1:
            # Count color changes
            h, w = solution.shape
            changes = 0
            for i in range(h):
                for j in range(w-1):
                    if solution[i, j] != solution[i, j+1]:
                        changes += 1
            for i in range(h-1):
                for j in range(w):
                    if solution[i, j] != solution[i+1, j]:
                        changes += 1

            # Prefer fewer changes (more coherent)
            coherence = 1.0 - (changes / (h*w))
            score += coherence * 5.0

        return score


def solve_arc_task(task: Dict, verbose: bool = False) -> List[List]:
    """Main entry point"""
    ensemble = EnsembleCHIMERA(verbose=verbose)
    return ensemble.solve_task(task)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CHIMERA v5.5 - ENSEMBLE TESTS")
    print("=" * 80)

    # Test ensemble on simple example
    task = {
        'train': [
            {'input': [[1, 2], [3, 4]], 'output': [[3, 1], [4, 2]]},
        ],
        'test': [
            {'input': [[5, 6], [7, 8]]}
        ]
    }

    result = solve_arc_task(task, verbose=True)
    print(f"\nEnsemble prediction: {result[0][0]}")

    print("\n" + "=" * 80)
    print("CHIMERA v5.5 READY")
    print("=" * 80)
