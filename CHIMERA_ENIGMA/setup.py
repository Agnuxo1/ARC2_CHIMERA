#!/usr/bin/env python3
"""
Setup Script - CHIMERA v5
Downloads ARC data and verifies installation
"""

import sys
import subprocess
from pathlib import Path
import urllib.request
import json

def print_header(text):
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)

def download_file(url, dest):
    """Download a file with progress"""
    print(f"Downloading {dest.name}...", end=" ", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
        size_mb = dest.stat().st_size / (1024 * 1024)
        print(f"✓ ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def main():
    print_header("CHIMERA v5 - SETUP")
    
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    
    # Step 1: Check Python version
    print("\n[STEP 1] Checking Python version...")
    py_version = sys.version_info
    print(f"Python {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 7):
        print("✗ Python 3.7+ required")
        return 1
    print("✓ Version OK")
    
    # Step 2: Install dependencies
    print("\n[STEP 2] Installing dependencies...")
    try:
        print("Installing numpy...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "numpy"])
        print("✓ numpy installed")
        
        print("Installing moderngl (GPU support)...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "moderngl"],
            capture_output=True
        )
        if result.returncode == 0:
            print("✓ moderngl installed")
        else:
            print("⚠ moderngl failed (GPU disabled - will use CPU)")
    except Exception as e:
        print(f"⚠ Dependency installation warning: {e}")
        print("You can install manually: pip install numpy moderngl")
    
    # Step 3: Create directories
    print("\n[STEP 3] Creating directories...")
    data_dir.mkdir(exist_ok=True)
    print(f"✓ {data_dir}")
    
    results_dir = base_dir / 'results'
    results_dir.mkdir(exist_ok=True)
    print(f"✓ {results_dir}")
    
    # Step 4: Download ARC data
    print("\n[STEP 4] Downloading ARC AGI data...")
    
    base_url = "https://github.com/fchollet/ARC-AGI/raw/master/data"
    
    files_to_download = [
        ("training", "arc-agi_training_challenges.json"),
        ("training", "arc-agi_training_solutions.json"),
        ("evaluation", "arc-agi_evaluation_challenges.json"),
        ("evaluation", "arc-agi_evaluation_solutions.json"),
    ]
    
    success_count = 0
    for category, filename in files_to_download:
        url = f"{base_url}/{category}/{filename}"
        dest = data_dir / filename
        
        if dest.exists():
            print(f"Skipping {filename} (already exists)")
            success_count += 1
        else:
            if download_file(url, dest):
                success_count += 1
    
    print(f"\n✓ Downloaded {success_count}/{len(files_to_download)} files")
    
    # Step 5: Verify installation
    print("\n[STEP 5] Verifying installation...")
    
    # Check files
    print("Checking core files...")
    core_files = [
        'chimera_v5.py',
        'arc_evaluation_v5.py',
        'test_quick.py',
        'README.md'
    ]
    
    all_present = True
    for filename in core_files:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} (missing)")
            all_present = False
    
    if not all_present:
        print("⚠ Some core files are missing")
        return 1
    
    # Step 6: Test import
    print("\n[STEP 6] Testing CHIMERA import...")
    try:
        from chimera_v5 import CHIMERAv5
        print("✓ CHIMERA v5 imports successfully")
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return 1
    
    # Success!
    print_header("SETUP COMPLETE!")
    
    print("\nCHIMERA v5 is ready to use!")
    print("\nNext steps:")
    print("  1. Run quick test:")
    print("     python test_quick.py")
    print()
    print("  2. Evaluate on training set (has ground truth):")
    print("     python arc_evaluation_v5.py --dataset training --limit 10")
    print()
    print("  3. Generate Kaggle submission:")
    print("     python arc_evaluation_v5.py --dataset evaluation")
    print()
    print("  4. Check results:")
    print("     cat results/evaluation_report.txt")
    
    print("\n" + "=" * 80)
    print("🌊 Let the river flow. Let physics solve. Let CHIMERA decrypt. 🌊")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
