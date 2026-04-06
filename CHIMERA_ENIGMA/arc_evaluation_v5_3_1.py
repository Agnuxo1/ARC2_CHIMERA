#!/usr/bin/env python3
"""
ARC AGI Evaluation - CHIMERA v5.3.1
Multiple Hypotheses + ARC-Aware Scoring

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import json
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import time
from datetime import datetime

from chimera_v5_3_1 import solve_arc_task


def load_tasks(path: str) -> Dict:
    with open(path, 'r') as f:
        return json.load(f)


def load_solutions(path: str) -> Dict:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def evaluate_solution(predicted: List[List], actual: List[List]) -> bool:
    try:
        pred_array = np.array(predicted)
        actual_array = np.array(actual)
        return np.array_equal(pred_array, actual_array)
    except:
        return False


def evaluate_task(task_id: str, task: Dict, ground_truth: Optional[List] = None) -> Dict:
    result = {
        'task_id': task_id,
        'status': 'pending',
        'test_cases': [],
        'accuracy': None,
        'time': 0.0
    }

    start_time = time.time()

    try:
        predictions = solve_arc_task(task, verbose=False)

        for test_idx, pred_attempts in enumerate(predictions):
            test_result = {
                'test_idx': test_idx,
                'predictions': pred_attempts,
                'correct': None
            }

            if ground_truth and test_idx < len(ground_truth):
                expected = ground_truth[test_idx]
                correct_1 = evaluate_solution(pred_attempts[0], expected)
                correct_2 = evaluate_solution(pred_attempts[1], expected)
                test_result['correct'] = correct_1 or correct_2

            result['test_cases'].append(test_result)

        correct_count = sum(1 for tc in result['test_cases'] if tc['correct'] is True)
        total_with_gt = sum(1 for tc in result['test_cases'] if tc['correct'] is not None)

        if total_with_gt > 0:
            result['accuracy'] = correct_count / total_with_gt

        result['status'] = 'completed'

    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)

    result['time'] = time.time() - start_time

    return result


def run_evaluation(dataset: str = 'training', limit: Optional[int] = None):
    print("\n" + "=" * 80)
    print("CHIMERA v5.3.1 - MULTIPLE HYPOTHESES + ARC-AWARE SCORING")
    print("ARC AGI EVALUATION")
    print("=" * 80)
    print("\nApproach: Multiple hypotheses + color validation + smart scoring")
    print()

    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results'
    output_dir.mkdir(exist_ok=True)

    if dataset == 'training':
        tasks_file = 'arc-agi_training_challenges.json'
        solutions_file = 'arc-agi_training_solutions.json'
    else:
        tasks_file = 'arc-agi_evaluation_challenges.json'
        solutions_file = 'arc-agi_evaluation_solutions.json'

    tasks_path = data_dir / tasks_file
    solutions_path = data_dir / solutions_file

    if not tasks_path.exists():
        print(f"[ERROR] Tasks file not found: {tasks_path}")
        return

    print(f"Loading tasks from: {tasks_path}")
    tasks = load_tasks(str(tasks_path))
    print(f"[OK] Loaded {len(tasks)} tasks")

    if limit:
        task_items = list(tasks.items())[:limit]
        tasks = dict(task_items)
        print(f"  (Limited to {limit} tasks)")

    solutions = {}
    if solutions_path.exists():
        print(f"Loading solutions from: {solutions_path}")
        solutions = load_solutions(str(solutions_path))
        print(f"[OK] Loaded solutions for {len(solutions)} tasks")

    print("\n" + "=" * 80)
    print("STARTING EVALUATION")
    print("=" * 80)

    start_time = time.time()
    results = []

    for idx, (task_id, task) in enumerate(tasks.items(), 1):
        print(f"[{idx}/{len(tasks)}] {task_id}...", end=" ", flush=True)

        ground_truth = solutions.get(task_id)
        result = evaluate_task(task_id, task, ground_truth)

        if result['accuracy'] is not None:
            print(f"Acc: {result['accuracy']*100:.1f}% ({result['time']:.3f}s)")
        else:
            print(f"OK ({result['time']:.3f}s)")

        results.append(result)

    total_time = time.time() - start_time

    # Statistics
    completed = [r for r in results if r['status'] == 'completed']
    tasks_with_acc = [r for r in completed if r['accuracy'] is not None]

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print(f"Tasks Completed: {len(completed)}/{len(results)}")

    if tasks_with_acc:
        avg_acc = np.mean([r['accuracy'] for r in tasks_with_acc])
        perfect = sum(1 for r in tasks_with_acc if r['accuracy'] == 1.0)

        print(f"Average Accuracy: {avg_acc*100:.2f}%")
        print(f"Perfect Solutions: {perfect}/{len(tasks_with_acc)}")

        # Improvement metrics
        print(f"\nImprovement over v5.3:")
        if avg_acc >= 0.05:
            improvement = avg_acc / 0.025  # v5.3 baseline
            print(f"  {improvement:.1f}× better ({avg_acc*100:.2f}% vs 2.5%)")

    print(f"\nTotal Time: {total_time:.2f}s ({total_time/60:.1f} min)")

    # Save results
    submission_path = output_dir / 'submission_v5_3_1.json'
    with open(submission_path, 'w') as f:
        submission = {}
        for r in completed:
            if r['status'] == 'completed':
                submission[r['task_id']] = [
                    {"attempt_1": tc['predictions'][0], "attempt_2": tc['predictions'][1]}
                    for tc in r['test_cases']
                ]
        json.dump(submission, f, indent=2)

    results_path = output_dir / 'evaluation_results_v5_3_1.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nOutput files saved:")
    print(f"  • {submission_path}")
    print(f"  • {results_path}")

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='CHIMERA v5.3.1 Evaluation')
    parser.add_argument('--dataset', choices=['training', 'evaluation'], default='training')
    parser.add_argument('--limit', type=int, help='Limit tasks')

    args = parser.parse_args()

    results = run_evaluation(dataset=args.dataset, limit=args.limit)
