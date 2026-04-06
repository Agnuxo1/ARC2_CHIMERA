#!/usr/bin/env python3
"""
ARC Evaluation for CHIMERA v6 GPU

Benchmarks the GPU-accelerated reasoning engine.
Measures accuracy and GPU vs CPU speed comparison.
"""

import json
import time
import numpy as np
from pathlib import Path
from typing import List, Dict
import argparse
from chimera_v6_gpu import solve_arc_task


def load_arc_dataset(dataset_path: str, limit: int = None) -> List[Dict]:
    """Load ARC dataset"""
    tasks = []
    data_dir = Path(dataset_path)

    if not data_dir.exists():
        print(f"[ERROR] Dataset path not found: {data_dir}")
        return []

    task_files = sorted(data_dir.glob("*.json"))[:limit]

    for task_file in task_files:
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
                tasks.append({
                    'id': task_file.stem,
                    'task': task
                })
        except Exception as e:
            print(f"[ERROR] Failed to load {task_file}: {e}")

    return tasks


def evaluate_solution(predicted: List, expected: List) -> bool:
    """Check if prediction matches expected output exactly"""
    if len(predicted) != len(expected):
        return False

    for pred_grid, exp_grid in zip(predicted, expected):
        pred_array = np.array(pred_grid, dtype=np.uint8)
        exp_array = np.array(exp_grid, dtype=np.uint8)

        if not np.array_equal(pred_array, exp_array):
            return False

    return True


def run_benchmark(dataset_path: str, limit: int = 20, verbose: bool = False):
    """Run benchmark on dataset"""

    print("\n" + "=" * 80)
    print("CHIMERA v6 GPU - BENCHMARK")
    print("=" * 80)
    print(f"Dataset: {dataset_path}")
    print(f"Limit: {limit}")
    print("=" * 80)

    # Load dataset
    tasks = load_arc_dataset(dataset_path, limit=limit)

    if not tasks:
        print("[ERROR] No tasks loaded")
        return

    print(f"Loaded {len(tasks)} tasks")

    # Run evaluation
    results = []
    perfect_count = 0
    total_time = 0
    gpu_times = []
    cpu_estimate = 0

    for idx, task_info in enumerate(tasks, 1):
        task_id = task_info['id']
        task = task_info['task']

        # Get expected outputs for test cases (if available)
        expected_outputs = [ex.get('output') for ex in task.get('test', [])]
        has_ground_truth = all(exp is not None for exp in expected_outputs)

        # Run solver
        start_time = time.time()
        try:
            predictions = solve_arc_task(task, verbose=False)
            elapsed = time.time() - start_time
            gpu_times.append(elapsed)

            # Check if perfect (if we have ground truth)
            is_perfect = False
            if has_ground_truth and predictions:
                # Check first attempt of each test
                predicted_outputs = [pred[0] for pred in predictions]
                is_perfect = evaluate_solution(predicted_outputs, expected_outputs)

            if is_perfect:
                perfect_count += 1
                status = "[PERFECT]"
            else:
                status = "[ATTEMPT]"

        except Exception as e:
            elapsed = time.time() - start_time
            gpu_times.append(elapsed)
            status = "[ERROR]"
            print(f"[{idx:3d}/{len(tasks)}] {task_id} {status} {e}")
            continue

        accuracy = (perfect_count / idx) * 100

        print(f"[{idx:3d}/{len(tasks)}] {task_id}... {status} ({elapsed:.3f}s) Acc: {accuracy:.1f}%")

        total_time += elapsed

        results.append({
            'task_id': task_id,
            'perfect': is_perfect,
            'time': elapsed,
        })

    # Calculate statistics
    avg_time = total_time / len(tasks) if tasks else 0
    avg_gpu_time = np.mean(gpu_times) if gpu_times else 0
    perfect_accuracy = (perfect_count / len(tasks)) * 100 if tasks else 0

    # Estimate CPU time (baseline from v5.3 ~0.01s per task)
    cpu_estimate_per_task = 0.01
    estimated_cpu_time = cpu_estimate_per_task * len(tasks)
    speedup = (cpu_estimate_per_task / avg_gpu_time) if avg_gpu_time > 0 else 0

    # Print results
    print("\n" + "=" * 80)
    print("RESULTS - CHIMERA v6 GPU")
    print("=" * 80)
    print(f"Tasks Completed: {len(tasks)}/{len(tasks)}")
    print(f"Average Accuracy: {perfect_accuracy:.2f}%")
    print(f"Perfect Solutions: {perfect_count}/{len(tasks)}")
    print(f"Total Time: {total_time:.2f}s ({total_time/60:.1f} min)")
    print(f"Avg Time per Task: {avg_gpu_time:.4f}s")
    print(f"\nGPU Speedup Estimate:")
    print(f"  CPU estimate: {estimated_cpu_time:.2f}s ({cpu_estimate_per_task:.4f}s per task)")
    print(f"  GPU actual: {total_time:.2f}s ({avg_gpu_time:.4f}s per task)")
    print(f"  Speedup: {speedup:.2f}×")
    print("=" * 80)

    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    results_file = results_dir / "evaluation_v6_gpu.json"
    with open(results_file, 'w') as f:
        json.dump({
            'accuracy': perfect_accuracy,
            'perfect_count': perfect_count,
            'total_tasks': len(tasks),
            'total_time': total_time,
            'avg_time_per_task': avg_gpu_time,
            'speedup_estimate': speedup,
            'detailed_results': results
        }, f, indent=2)

    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CHIMERA v6 GPU Evaluation")
    parser.add_argument("--dataset", type=str, default="D:\\ARC2_CHIMERA\\data\\training",
                        help="Path to ARC dataset")
    parser.add_argument("--limit", type=int, default=20,
                        help="Limit number of tasks to evaluate")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    run_benchmark(args.dataset, limit=args.limit, verbose=args.verbose)
