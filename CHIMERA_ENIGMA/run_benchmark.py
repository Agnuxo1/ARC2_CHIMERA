#!/usr/bin/env python3
"""
Wrapper script to run CHIMERA v5.2 evaluation with proper encoding handling
"""
import sys
import os

# Force UTF-8 output
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Now import and run the evaluation
from arc_evaluation_v5_2 import run_evaluation

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='CHIMERA v5.2 - ARC AGI Benchmark',
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
