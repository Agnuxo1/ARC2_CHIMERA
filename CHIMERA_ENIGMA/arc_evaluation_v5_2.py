#!/usr/bin/env python3
"""
ARC AGI Evaluation Script - CHIMERA v5.2
Energy Landscape Learning with Chemotaxis-based CA Evolution

"Training examples create an energy landscape.
 CA evolution follows gradients to find solutions.
 Like bacteria following chemical gradients to food.
 No reasoning required - just physics."

Francisco Angulo de Lafuente - CHIMERA Project 2025
"""

import json
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path
import time
from datetime import datetime

# Import CHIMERA v5.2
from chimera_v5_2 import CHIMERAv52, solve_arc_task


def load_tasks(path: str) -> Dict:
    """Load ARC tasks from JSON"""
    with open(path, 'r') as f:
        return json.load(f)


def load_solutions(path: str) -> Dict:
    """Load ground truth solutions"""
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


def evaluate_task(chimera: CHIMERAv52, task_id: str, task: Dict,
                 ground_truth: Optional[List] = None) -> Dict:
    """
    Evaluate a single ARC task.
    
    Args:
        chimera: CHIMERA v5.2 instance
        task_id: Task identifier
        task: Task data
        ground_truth: Ground truth solutions (if available)
        
    Returns:
        Evaluation results
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
        # Solve task using CHIMERA v5.2
        predictions = chimera.solve_task(task)
        
        # Evaluate each test case
        for test_idx, pred_attempts in enumerate(predictions):
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
        print(f"  [FAIL] Error: {str(e)[:60]}")
    
    result['time'] = time.time() - start_time
    
    return result


def generate_kaggle_submission(results: List[Dict], output_path: Path):
    """
    Generate submission.json in Kaggle format.
    
    Format:
    {
        "task_id": [
            {"attempt_1": [[...]], "attempt_2": [[...]]},
            ...
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
CHIMERA v5.2 - ENERGY LANDSCAPE LEARNING - EVALUATION REPORT
{'=' * 80}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dataset: {dataset_name}
Approach: Chemotaxis-based CA evolution with energy landscape learning
{'=' * 80}

PHILOSOPHICAL FOUNDATION
{'=' * 80}
CHIMERA v5.2 treats ARC as a gradient descent problem:

1. ENERGY LANDSCAPE CONSTRUCTION
   - Training examples define "energy valleys" (correct solutions)
   - Each pattern observation lowers energy at that configuration
   - Unseen patterns have high energy (probably incorrect)

2. CHEMOTAXIS-BASED CA EVOLUTION
   - CA cells probe neighborhood like bacteria sensing chemicals
   - Move toward lower energy (like bacteria toward food)
   - No explicit reasoning - just gradient following
   - Convergence at energy minimum = solution found

3. BIOLOGICAL INSPIRATION
   - E. coli bacteria: Follow glucose gradient without "thinking"
   - Water: Flows downhill without "planning"
   - CHIMERA CA: Finds solutions without "reasoning"

This approach embodies the CHIMERA paper philosophy:
"Rendering IS Thinking" - computation emerges from physics

{'=' * 80}
EXECUTION SUMMARY
{'=' * 80}
Total Tasks: {len(results)}
Completed: {len(completed)}
Failed: {len(failed)}
Total Time: {total_time:.2f}s ({total_time/60:.1f} min)
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
  100%: {'#' * perfect_tasks}{' ' * (30-perfect_tasks)} {perfect_tasks} tasks
  >0%:  {'#' * partial_correct}{' ' * (30-partial_correct)} {partial_correct} tasks
  0%:   {'#' * (len(tasks_with_accuracy)-perfect_tasks-partial_correct)} {len(tasks_with_accuracy)-perfect_tasks-partial_correct} tasks

COMPARISON TO v5.1:
  v5.1 accuracy: 0.40% (static cipher keys)
  v5.2 accuracy: {avg_accuracy*100:.2f}% (energy landscape learning)
  Improvement: {avg_accuracy/0.004:.1f}× better
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
KEY INNOVATIONS IN v5.2
{'=' * 80}

1. ENERGY LANDSCAPE LEARNING
   Instead of static rules, v5.2 learns an energy function from training:
   
   Low Energy  = Patterns matching training examples (likely correct)
   High Energy = Patterns never seen in training (likely wrong)
   
   The energy landscape encodes "what good solutions look like"

2. CHEMOTAXIS CA EVOLUTION
   Each CA cell acts like a bacterium:
   
   - Senses local energy gradient
   - Probes neighbor colors (like tasting chemicals)
   - Moves toward lowest energy (like moving toward food)
   - No global plan, just local decisions
   
   Emergent behavior: Entire grid flows to solution

3. BIOLOGICAL REALISM
   This approach mirrors actual biological problem-solving:
   
   - Bacteria finding nutrients: Chemotaxis
   - Neurons firing: Minimum energy states
   - Water flowing: Gradient descent
   - Evolution: Fitness landscape optimization
   
   Intelligence = Physics, not Algorithms

{'=' * 80}
OUTPUT FILES
{'=' * 80}
[OK] submission.json - Kaggle submission format
[OK] evaluation_results.json - Detailed metrics
[OK] evaluation_report_v5_2.txt - This report

{'=' * 80}
NEXT STEPS FOR v5.3
{'=' * 80}
Potential improvements:

1. Multi-scale energy landscapes
   - Coarse patterns for global structure
   - Fine patterns for local details
   
2. Adaptive evolution steps
   - More iterations for complex tasks
   - Early stopping for simple tasks
   
3. Ensemble energy landscapes
   - Train multiple landscapes
   - Combine predictions

4. GPU acceleration
   - OpenGL texture-based energy lookup
   - Parallel CA evolution in shaders

{'=' * 80}
CHIMERA v5.2 EVALUATION COMPLETE
{'=' * 80}
"""
    
    return report


def run_evaluation(dataset: str = 'training', limit: Optional[int] = None):
    """
    Run complete evaluation on ARC dataset.
    
    Args:
        dataset: 'training' or 'evaluation'
        limit: Limit number of tasks (for testing)
    """
    
    print("\n" + "=" * 80)
    print("CHIMERA v5.2 - ENERGY LANDSCAPE LEARNING")
    print("ARC AGI EVALUATION")
    print("=" * 80)
    print("\nApproach: Chemotaxis-based CA with energy landscape learning")
    print("Training examples -> Energy landscape (valleys = solutions)")
    print("CA evolution -> Gradient descent (flow downhill to valleys)")
    print()
    
    # Setup paths
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    output_dir = base_dir / 'results'
    output_dir.mkdir(exist_ok=True)
    
    # Determine dataset files
    if dataset == 'training':
        tasks_file = 'arc-agi_training_challenges.json'
        solutions_file = 'arc-agi_training_solutions.json'
    else:
        tasks_file = 'arc-agi_evaluation_challenges.json'
        solutions_file = 'arc-agi_evaluation_solutions.json'
    
    tasks_path = data_dir / tasks_file
    solutions_path = data_dir / solutions_file if solutions_file else None
    
    if not tasks_path.exists():
        print(f"[FAIL] ERROR: Tasks file not found: {tasks_path}")
        return
    
    # Load data
    print(f"Loading tasks from: {tasks_path}")
    tasks = load_tasks(str(tasks_path))
    print(f"[OK] Loaded {len(tasks)} tasks")
    
    if limit:
        task_items = list(tasks.items())[:limit]
        tasks = dict(task_items)
        print(f"  (Limited to {limit} tasks for testing)")
    
    solutions = {}
    if solutions_path and solutions_path.exists():
        print(f"Loading solutions from: {solutions_path}")
        solutions = load_solutions(str(solutions_path))
        print(f"[OK] Loaded solutions for {len(solutions)} tasks")
    else:
        print("⚠ No ground truth solutions - will generate submission only")
    
    # Initialize CHIMERA v5.2
    print("\nInitializing CHIMERA v5.2...")
    chimera = CHIMERAv52(verbose=False)
    
    # Run evaluation
    print("\n" + "=" * 80)
    print("STARTING EVALUATION")
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
        status = "[OK]" if result['status'] == 'completed' else "[FAIL]"
        time_str = f"{result['time']:.2f}s"
        
        if result['accuracy'] is not None:
            acc_str = f"Acc: {result['accuracy']*100:.1f}%"
            print(f"  {status} {acc_str} | {time_str}")
        else:
            print(f"  {status} Completed | {time_str}")
        
        results.append(result)
    
    total_time = time.time() - start_time
    
    # Generate outputs
    print("\n" + "=" * 80)
    print("GENERATING OUTPUT FILES")
    print("=" * 80)
    
    # 1. Kaggle Submission
    submission_path = output_dir / 'submission_v5_2.json'
    print(f"\nGenerating Kaggle submission: {submission_path}")
    generate_kaggle_submission(results, submission_path)
    size_kb = submission_path.stat().st_size / 1024
    print(f"[OK] Submission saved ({size_kb:.1f} KB)")
    
    # 2. Detailed Results
    results_path = output_dir / 'evaluation_results_v5_2.json'
    print(f"\nSaving detailed results: {results_path}")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    size_kb = results_path.stat().st_size / 1024
    print(f"[OK] Results saved ({size_kb:.1f} KB)")
    
    # 3. Evaluation Report
    report_path = output_dir / 'evaluation_report_v5_2.txt'
    print(f"\nGenerating report: {report_path}")
    report = generate_report(results, total_time, f"ARC AGI {dataset.title()}")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"[OK] Report saved")
    
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
        print(f"\nImprovement over v5.1: {avg_acc/0.004:.1f}× better")
    
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
        description='CHIMERA v5.2 - ARC AGI Evaluation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate on training set (has ground truth)
  python arc_evaluation_v5_2.py --dataset training
  
  # Quick test on 10 tasks
  python arc_evaluation_v5_2.py --dataset training --limit 10
  
  # Generate Kaggle submission
  python arc_evaluation_v5_2.py --dataset evaluation
        """
    )
    
    parser.add_argument(
        '--dataset',
        choices=['training', 'evaluation'],
        default='training',
        help='Which dataset to evaluate on'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of tasks (for testing)'
    )
    
    args = parser.parse_args()
    
    # Run evaluation
    results = run_evaluation(
        dataset=args.dataset,
        limit=args.limit
    )
