#!/usr/bin/env python3
"""
ARC AGI Evaluation Script - CHIMERA v5
Complete evaluation on ARC Prize 2025 dataset

"We don't need AGI to solve ARC.
 We need cryptography + physics.
 
 Training examples = Enigma key
 Test inputs = Encrypted messages
 CA evolution = Turing's Bombe
 
 The water doesn't think.
 It just flows to the ocean."

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import time
from datetime import datetime

# Import CHIMERA v5.1
from chimera_v5_1 import CHIMERAv51, solve_arc_task


def load_tasks(path: str) -> Dict:
    """Load ARC tasks from JSON"""
    with open(path, 'r') as f:
        return json.load(f)


def load_solutions(path: str) -> Dict:
    """Load ground truth solutions (if available)"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠ No ground truth solutions found")
        return {}


def evaluate_solution(predicted: List[List], actual: List[List]) -> bool:
    """Check if predicted solution matches actual output"""
    try:
        pred_array = np.array(predicted)
        actual_array = np.array(actual)
        return np.array_equal(pred_array, actual_array)
    except:
        return False


def evaluate_task(chimera: CHIMERAv51, task_id: str, task: Dict, 
                 ground_truth: Optional[List] = None) -> Dict:
    """
    Evaluate a single ARC task.
    
    Args:
        chimera: CHIMERA v5.1 instance
        task_id: Task identifier
        task: Task data with train/test
        ground_truth: Ground truth solutions (if available)
        
    Returns:
        Evaluation results dictionary
    """
    result = {
        'task_id': task_id,
        'status': 'pending',
        'test_cases': [],
        'accuracy': None,
        'time': 0.0
    }
    
    start_time = time.time()
    
    try:
        # Solve task using CHIMERA v5
        predictions = chimera.solve_task(task)
        
        # Evaluate each test case
        for test_idx, (test_input, pred_attempts) in enumerate(zip(task['test'], predictions)):
            test_result = {
                'test_idx': test_idx,
                'predictions': pred_attempts,
                'correct': None
            }
            
            # Check against ground truth if available
            if ground_truth and test_idx < len(ground_truth):
                expected = ground_truth[test_idx]
                
                # Check both attempts
                correct_1 = evaluate_solution(pred_attempts[0], expected)
                correct_2 = evaluate_solution(pred_attempts[1], expected)
                
                test_result['correct'] = correct_1 or correct_2
                test_result['which_correct'] = 1 if correct_1 else (2 if correct_2 else None)
            
            result['test_cases'].append(test_result)
        
        # Calculate task accuracy
        correct_count = sum(1 for tc in result['test_cases'] if tc['correct'] is True)
        total_with_gt = sum(1 for tc in result['test_cases'] if tc['correct'] is not None)
        
        if total_with_gt > 0:
            result['accuracy'] = correct_count / total_with_gt
        
        result['status'] = 'completed'
        
    except Exception as e:
        result['status'] = 'failed'
        result['error'] = str(e)
        print(f"  ✗ Error: {str(e)[:60]}")
    
    result['time'] = time.time() - start_time
    
    return result


def generate_kaggle_submission(results: List[Dict], output_path: Path):
    """
    Generate submission.json in Kaggle format.
    
    Format:
    {
        "task_id": [
            {"attempt_1": [[...]], "attempt_2": [[...]]},
            {"attempt_1": [[...]], "attempt_2": [[...]]}
        ]
    }
    """
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
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(submission, f, indent=2)
    
    return submission


def generate_report(results: List[Dict], total_time: float, 
                   dataset_name: str = "ARC AGI") -> str:
    """Generate detailed evaluation report"""
    
    completed = [r for r in results if r['status'] == 'completed']
    failed = [r for r in results if r['status'] == 'failed']
    
    # Calculate statistics
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
    
    # Build report
    report = f"""
{'=' * 80}
CHIMERA v5.1 - ENHANCED PATTERN DETECTION - EVALUATION REPORT
{'=' * 80}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dataset: {dataset_name}
Philosophy: "Training = Cipher Key | CA = Turing's Bombe | Solution = Decryption"
{'=' * 80}

EXECUTION SUMMARY
{'=' * 80}
Total Tasks Evaluated: {len(results)}
Successfully Completed: {len(completed)}
Failed: {len(failed)}
Total Execution Time: {total_time:.2f}s ({total_time/60:.1f} min)
Average Time per Task: {avg_time:.2f}s

{'=' * 80}
ACCURACY METRICS
{'=' * 80}
"""
    
    if tasks_with_accuracy:
        report += f"""Tasks with Ground Truth: {len(tasks_with_accuracy)}
Average Accuracy: {avg_accuracy*100:.2f}%
Perfect Solutions (100%): {perfect_tasks} ({perfect_tasks/len(tasks_with_accuracy)*100:.1f}%)
Partial Solutions (>0%): {partial_correct} ({partial_correct/len(tasks_with_accuracy)*100:.1f}%)

Accuracy Distribution:
  100%: {'█' * perfect_tasks}{' ' * (30-perfect_tasks)} {perfect_tasks} tasks
  >0%:  {'█' * partial_correct}{' ' * (30-partial_correct)} {partial_correct} tasks
  0%:   {'█' * (len(tasks_with_accuracy)-perfect_tasks-partial_correct)} {len(tasks_with_accuracy)-perfect_tasks-partial_correct} tasks
"""
    else:
        report += "No ground truth available - submission generated for Kaggle evaluation\n"
    
    report += f"""
{'=' * 80}
DETAILED TASK RESULTS
{'=' * 80}
"""
    
    # Sort by accuracy (descending)
    sorted_results = sorted(
        [r for r in completed if r['accuracy'] is not None],
        key=lambda x: x['accuracy'],
        reverse=True
    )
    
    for r in sorted_results[:20]:  # Show top 20
        acc_str = f"{r['accuracy']*100:5.1f}%"
        time_str = f"{r['time']:6.2f}s"
        report += f"  {r['task_id']}: {acc_str} | {time_str}\n"
    
    if len(sorted_results) > 20:
        report += f"  ... ({len(sorted_results)-20} more tasks)\n"
    
    if failed:
        report += f"""
{'=' * 80}
FAILED TASKS
{'=' * 80}
"""
        for r in failed:
            report += f"  {r['task_id']}: {r.get('error', 'Unknown error')[:60]}\n"
    
    report += f"""
{'=' * 80}
CRYPTOGRAPHIC APPROACH NOTES
{'=' * 80}
CHIMERA v5 treats ARC as a cryptographic problem:

1. CIPHER KEY EXTRACTION
   - Training examples analyzed to extract "encryption method"
   - Geometric invariants (rotation, flip, scale)
   - Color transformation rules
   - Spatial fill patterns

2. DECRYPTION VIA CA EVOLUTION
   - Test input = encrypted message
   - CA evolution = Turing's Bombe machine
   - Cipher key guides the CA toward solution
   - Like water flowing downhill to minimum energy

3. PHYSICAL APPROACH
   - No symbolic reasoning required
   - No neural networks needed
   - Pure physics + mathematics
   - Cryptanalysis + cellular automata

"The water doesn't think about reaching the ocean.
 Turing didn't think about understanding Nazis.
 CHIMERA doesn't think about reasoning.
 All just find the pattern - and flow."

{'=' * 80}
OUTPUT FILES
{'=' * 80}
✓ submission.json - Kaggle submission format
✓ evaluation_results.json - Detailed metrics
✓ evaluation_report.txt - This report

{'=' * 80}
CHIMERA v5.1 EVALUATION COMPLETE
{'=' * 80}
"""
    
    return report


def run_evaluation(dataset: str = 'evaluation', use_gpu: bool = True):
    """
    Run complete evaluation on ARC dataset.
    
    Args:
        dataset: 'evaluation', 'training', or 'test'
        use_gpu: Whether to use GPU acceleration
    """
    
    print("\n" + "=" * 80)
    print("CHIMERA v5.1 - ENHANCED PATTERN DETECTION")
    print("ARC AGI PRIZE 2025 - EVALUATION SCRIPT")
    print("=" * 80)
    print("\nPhilosophy: We don't solve ARC with AGI - we decrypt it with physics")
    print("Training Examples = Enigma Cipher Key")
    print("CA Evolution = Turing's Bombe Machine")
    print("Solution = Decryption\n")
    
    # Setup paths
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results'
    output_dir.mkdir(exist_ok=True)
    
    # Determine dataset files
    if dataset == 'evaluation':
        tasks_file = 'arc-agi_evaluation_challenges.json'
        solutions_file = 'arc-agi_evaluation_solutions.json'
    elif dataset == 'training':
        tasks_file = 'arc-agi_training_challenges.json'
        solutions_file = 'arc-agi_training_solutions.json'
    else:  # test
        tasks_file = 'arc-agi_test_challenges.json'
        solutions_file = None
    
    tasks_path = data_dir / tasks_file
    solutions_path = data_dir / solutions_file if solutions_file else None
    
    if not tasks_path.exists():
        print(f"✗ ERROR: Tasks file not found: {tasks_path}")
        print(f"\nExpected file structure:")
        print(f"  {base_dir}/")
        print(f"    ├── chimera_v5.py")
        print(f"    ├── arc_evaluation_v5.py")
        print(f"    └── data/")
        print(f"        ├── arc-agi_evaluation_challenges.json")
        print(f"        └── arc-agi_evaluation_solutions.json")
        return
    
    # Load data
    print(f"Loading tasks from: {tasks_path}")
    tasks = load_tasks(str(tasks_path))
    print(f"✓ Loaded {len(tasks)} tasks")
    
    solutions = {}
    if solutions_path and solutions_path.exists():
        print(f"Loading solutions from: {solutions_path}")
        solutions = load_solutions(str(solutions_path))
        print(f"✓ Loaded solutions for {len(solutions)} tasks")
    else:
        print("⚠ No ground truth solutions - will generate submission only")
    
    # Initialize CHIMERA v5.1
    print(f"\nInitializing CHIMERA v5.1 (GPU: {use_gpu})...")
    chimera = CHIMERAv51(use_gpu=use_gpu)
    
    # Run evaluation
    print("\n" + "=" * 80)
    print("STARTING CRYPTANALYSIS")
    print("=" * 80)
    
    start_time = time.time()
    results = []
    
    for idx, (task_id, task) in enumerate(tasks.items(), 1):
        print(f"\n[{idx}/{len(tasks)}] Task: {task_id}")
        print(f"  Training: {len(task['train'])} examples | Test: {len(task['test'])} cases")
        
        # Get ground truth if available
        ground_truth = solutions.get(task_id)
        
        # Evaluate
        result = evaluate_task(chimera, task_id, task, ground_truth)
        
        # Print status
        status = "✓" if result['status'] == 'completed' else "✗"
        time_str = f"{result['time']:.2f}s"
        
        if result['accuracy'] is not None:
            acc_str = f"Acc: {result['accuracy']*100:.1f}%"
            print(f"  {status} {acc_str} | {time_str}")
        else:
            print(f"  {status} Completed | {time_str}")
        
        results.append(result)
        
        # Save checkpoint every 20 tasks
        if idx % 20 == 0:
            checkpoint_path = output_dir / f'checkpoint_{idx}.json'
            with open(checkpoint_path, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  → Checkpoint saved")
    
    total_time = time.time() - start_time
    
    # Generate outputs
    print("\n" + "=" * 80)
    print("GENERATING OUTPUT FILES")
    print("=" * 80)
    
    # 1. Kaggle Submission
    submission_path = output_dir / 'submission.json'
    print(f"\nGenerating Kaggle submission: {submission_path}")
    generate_kaggle_submission(results, submission_path)
    size_kb = submission_path.stat().st_size / 1024
    print(f"✓ Submission saved ({size_kb:.1f} KB)")
    
    # 2. Detailed Results
    results_path = output_dir / 'evaluation_results.json'
    print(f"\nSaving detailed results: {results_path}")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    size_kb = results_path.stat().st_size / 1024
    print(f"✓ Results saved ({size_kb:.1f} KB)")
    
    # 3. Evaluation Report
    report_path = output_dir / 'evaluation_report.txt'
    print(f"\nGenerating report: {report_path}")
    report = generate_report(results, total_time, f"ARC AGI {dataset.title()}")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Report saved")
    
    # Print summary
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
    print(f"\nOutput Files:")
    print(f"  • {submission_path}")
    print(f"  • {results_path}")
    print(f"  • {report_path}")
    
    print("\n" + "=" * 80)
    print("Ready for Kaggle submission!")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='CHIMERA v5.1 - Enhanced Pattern Detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate on official evaluation set (for Kaggle)
  python arc_evaluation_v5.1.py --dataset evaluation
  
  # Test on training set (has ground truth)
  python arc_evaluation_v5.1.py --dataset training
  
  # Force CPU mode
  python arc_evaluation_v5.1.py --no-gpu
  
  # Quick test on 10 tasks
  python arc_evaluation_v5.1.py --limit 10
        """
    )
    
    parser.add_argument(
        '--dataset',
        choices=['evaluation', 'training', 'test'],
        default='evaluation',
        help='Which dataset to evaluate on'
    )
    
    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='Disable GPU acceleration (use CPU only)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of tasks to evaluate (for testing)'
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    results = run_evaluation(
        dataset=args.dataset,
        use_gpu=not args.no_gpu
    )
