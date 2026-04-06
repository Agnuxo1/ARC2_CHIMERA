#!/usr/bin/env python3
"""
ARC AGI Evaluation Script - CHIMERA v5.4
Geometric Transformation Detection

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import json
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import time
from datetime import datetime

from chimera_v5_4 import CHIMERAv54, solve_arc_task


def load_tasks(path: str) -> Dict:
    with open(path, 'r') as f:
        return json.load(f)


def load_solutions(path: str) -> Dict:
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] No ground truth solutions found")
        return {}


def evaluate_solution(predicted: List[List], actual: List[List]) -> bool:
    try:
        pred_array = np.array(predicted)
        actual_array = np.array(actual)
        return np.array_equal(pred_array, actual_array)
    except:
        return False


def evaluate_task(chimera: CHIMERAv54, task_id: str, task: Dict,
                 ground_truth: Optional[List] = None) -> Dict:
    result = {
        'task_id': task_id,
        'status': 'pending',
        'test_cases': [],
        'accuracy': None,
        'time': 0.0
    }

    start_time = time.time()

    try:
        predictions = chimera.solve_task(task)

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
        print(f"  [FAIL] Error: {str(e)[:60]}")

    result['time'] = time.time() - start_time

    return result


def generate_kaggle_submission(results: List[Dict], output_path: Path):
    submission = {}

    for result in results:
        if result['status'] != 'completed':
            continue

        task_id = result['task_id']
        task_predictions = []

        for test_case in result['test_cases']:
            preds = test_case['predictions']
            task_predictions.append({
                "attempt_1": preds[0],
                "attempt_2": preds[1]
            })

        submission[task_id] = task_predictions

    with open(output_path, 'w') as f:
        json.dump(submission, f, indent=2)

    return submission


def generate_report(results: List[Dict], total_time: float, dataset_name: str = "ARC AGI") -> str:
    completed = [r for r in results if r['status'] == 'completed']
    failed = [r for r in results if r['status'] == 'failed']

    tasks_with_accuracy = [r for r in completed if r['accuracy'] is not None]

    if tasks_with_accuracy:
        avg_accuracy = np.mean([r['accuracy'] for r in tasks_with_accuracy])
        perfect_tasks = sum(1 for r in tasks_with_accuracy if r['accuracy'] == 1.0)
        partial_correct = sum(1 for r in tasks_with_accuracy if 0 < r['accuracy'] < 1.0)
    else:
        avg_accuracy = None
        perfect_tasks = 0
        partial_correct = 0

    avg_time = np.mean([r['time'] for r in completed]) if completed else 0.0

    report = f"""
{'='*80}
CHIMERA v5.4 - GEOMETRIC TRANSFORMATION DETECTION - EVALUATION REPORT
{'='*80}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dataset: {dataset_name}
Approach: Temporal sequences + geometric transforms
{'='*80}

PHILOSOPHICAL FOUNDATION
{'='*80}
CHIMERA v5.4 enhances v5.3 with geometric understanding:

1. TEMPORAL SEQUENCE ANALYSIS (v5.3 foundation)
   - Each training example is a frame in temporal sequence
   - Detect size progressions (arithmetic, geometric)
   - Detect color evolution

2. GEOMETRIC TRANSFORMATION DETECTION (NEW in v5.4)
   - Rotation detection (90, 180, 270 degrees)
   - Flip detection (horizontal, vertical)
   - Tiling/replication (factor detection)
   - Scaling (zoom in/out)
   - Object movement (center of mass tracking)
   - Fill patterns (sparse -> connected)

3. COMBINED APPLICATION
   - Detect which transforms happen
   - Apply detected transforms to test input
   - Combine with color mappings
   - Resize to predicted target size

This adds the "HOW" to the "WHAT" detected in v5.3.

{'='*80}
EXECUTION SUMMARY
{'='*80}
Total Tasks: {len(results)}
Completed: {len(completed)}
Failed: {len(failed)}
Total Time: {total_time:.2f}s ({total_time/60:.1f} min)
Average Time per Task: {avg_time:.2f}s

{'='*80}
ACCURACY METRICS
{'='*80}
"""

    if tasks_with_accuracy:
        report += f"""Tasks with Ground Truth: {len(tasks_with_accuracy)}
Average Accuracy: {avg_accuracy*100:.2f}%
Perfect Solutions (100%): {perfect_tasks} ({perfect_tasks/len(tasks_with_accuracy)*100:.1f}%)
Partial Solutions (>0%): {partial_correct} ({partial_correct/len(tasks_with_accuracy)*100:.1f}%)

Improvement Chain:
  v5.2: 0.00% (energy landscapes - FAILED)
  v5.3: 5.00% (temporal sequences - WORKING)
  v5.4: {avg_accuracy*100:.2f}% (+ geometric transforms)
  Improvement v5.3->v5.4: {(avg_accuracy*100/5.0):.1f}x
"""
    else:
        report += "No ground truth available - submission generated for Kaggle\n"

    report += f"""
{'='*80}
DETAILED TASK RESULTS
{'='*80}
"""

    sorted_results = sorted(
        [r for r in completed if r['accuracy'] is not None],
        key=lambda x: x['accuracy'],
        reverse=True
    )

    for r in sorted_results[:30]:
        acc_str = f"{r['accuracy']*100:5.1f}%"
        time_str = f"{r['time']:6.2f}s"
        report += f"  {r['task_id']}: {acc_str} | {time_str}\n"

    if len(sorted_results) > 30:
        report += f"  ... ({len(sorted_results)-30} more tasks)\n"

    report += f"""
{'='*80}
KEY IMPROVEMENTS IN v5.4
{'='*80}

1. ROTATION DETECTION
   Identifies 90/180/270 degree rotations
   Applies correct rotation to test input

2. TILING DETECTION
   Identifies replication patterns (2x2, 3x3, etc)
   Applies tiling to expand test input correctly

3. SCALING DETECTION
   Identifies zoom transformations
   Applies scaling ratios to test input

4. OBJECT TRACKING
   Detects movement of connected components
   Tracks position changes across frames

5. FILL DETECTION
   Identifies sparse -> dense transformations
   Estimates fill factors

{'='*80}
CONCLUSION
{'='*80}

CHIMERA v5.4 adds the missing piece from v5.3:
- v5.3 knew WHAT changed (colors, sizes)
- v5.4 knows HOW it changed (rotation, tile, scale, move)

This should improve accuracy from 5% toward target of 10-15%.

Next steps (v5.5):
- Object-level reasoning (track objects across frames)
- Regional analysis (different rules per region)
- Ensemble approaches (try multiple hypotheses)

{'='*80}
CHIMERA v5.4 EVALUATION COMPLETE
{'='*80}
"""

    return report


def run_evaluation(dataset: str = 'training', limit: Optional[int] = None):
    print("\n" + "=" * 80)
    print("CHIMERA v5.4 - GEOMETRIC TRANSFORMATION DETECTION")
    print("ARC AGI EVALUATION")
    print("=" * 80)
    print("\nApproach: Temporal sequences + geometric transforms")
    print("Detects: Rotation, Flip, Scale, Tiling, Movement, Fill")
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
        print(f"  (Limited to {limit} tasks for testing)")

    solutions = {}
    if solutions_path.exists():
        print(f"Loading solutions from: {solutions_path}")
        solutions = load_solutions(str(solutions_path))
        print(f"[OK] Loaded solutions for {len(solutions)} tasks")
    else:
        print("[!] No ground truth solutions")

    print("\nInitializing CHIMERA v5.4...")
    chimera = CHIMERAv54(verbose=False)

    print("\n" + "=" * 80)
    print("STARTING EVALUATION")
    print("=" * 80)

    start_time = time.time()
    results = []

    for idx, (task_id, task) in enumerate(tasks.items(), 1):
        print(f"\n[{idx}/{len(tasks)}] Task: {task_id}")
        print(f"  Training: {len(task['train'])} frames | Test: {len(task['test'])} frames")

        ground_truth = solutions.get(task_id)
        result = evaluate_task(chimera, task_id, task, ground_truth)

        status = "[OK]" if result['status'] == 'completed' else "[FAIL]"
        time_str = f"{result['time']:.2f}s"

        if result['accuracy'] is not None:
            acc_str = f"Acc: {result['accuracy']*100:.1f}%"
            print(f"  {status} {acc_str} | {time_str}")
        else:
            print(f"  {status} Completed | {time_str}")

        results.append(result)

    total_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("GENERATING OUTPUT FILES")
    print("=" * 80)

    submission_path = output_dir / 'submission_v5_4.json'
    print(f"\nGenerating Kaggle submission: {submission_path}")
    generate_kaggle_submission(results, submission_path)
    size_kb = submission_path.stat().st_size / 1024
    print(f"[OK] Submission saved ({size_kb:.1f} KB)")

    results_path = output_dir / 'evaluation_results_v5_4.json'
    print(f"\nSaving detailed results: {results_path}")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    size_kb = results_path.stat().st_size / 1024
    print(f"[OK] Results saved ({size_kb:.1f} KB)")

    report_path = output_dir / 'evaluation_report_v5_4.txt'
    print(f"\nGenerating report: {report_path}")
    report = generate_report(results, total_time, f"ARC AGI {dataset.title()}")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[OK] Report saved")

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)

    completed = sum(1 for r in results if r['status'] == 'completed')
    tasks_with_acc = [r for r in results if r.get('accuracy') is not None]

    print(f"\nTasks Completed: {completed}/{len(tasks)}")

    if tasks_with_acc:
        avg_acc = np.mean([r['accuracy'] for r in tasks_with_acc])
        perfect = sum(1 for r in tasks_with_acc if r['accuracy'] == 1.0)
        print(f"Average Accuracy: {avg_acc*100:.2f}%")
        print(f"Perfect Solutions: {perfect}/{len(tasks_with_acc)}")

    print(f"Total Time: {total_time:.2f}s ({total_time/60:.1f} minutes)")

    print("\n" + "=" * 80)
    print("Ready for Kaggle submission!")
    print("=" * 80)

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='CHIMERA v5.4 - ARC AGI Evaluation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python arc_evaluation_v5_4.py --dataset training
  python arc_evaluation_v5_4.py --dataset training --limit 50
  python arc_evaluation_v5_4.py --dataset evaluation
        """
    )

    parser.add_argument('--dataset', choices=['training', 'evaluation'], default='training')
    parser.add_argument('--limit', type=int, help='Limit number of tasks')

    args = parser.parse_args()

    results = run_evaluation(dataset=args.dataset, limit=args.limit)
