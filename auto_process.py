#!/usr/bin/env python3
"""
Automatic Download Monitor and Processor
Monitors dataset download and auto-processes when complete
"""

import os
import sys
import time
from pathlib import Path
import subprocess


def get_file_size_mb(filepath):
    """Get file size in MB"""
    try:
        size = Path(filepath).stat().st_size
        return size / (1024 * 1024)
    except:
        return 0


def monitor_download(filepath, target_size_mb=10960):
    """Monitor download progress"""
    print("="*70)
    print("DOWNLOAD MONITOR - Waiting for completion")
    print("="*70)

    last_size = 0
    stall_count = 0

    while True:
        current_size = get_file_size_mb(filepath)

        if current_size == 0:
            print(f"[ERROR] File not found: {filepath}")
            return False

        # Calculate progress
        progress = (current_size / target_size_mb) * 100

        # Check if download is stalled
        if abs(current_size - last_size) < 1:  # Less than 1MB change
            stall_count += 1
        else:
            stall_count = 0

        # Print progress
        print(f"Progress: {current_size:>7.1f} MB / {target_size_mb:.0f} MB ({progress:>5.1f}%) | ", end="")

        if stall_count > 0:
            print(f"Stalled: {stall_count * 10}s", end="")
        else:
            speed = (current_size - last_size) / 10  # MB/s (checking every 10s)
            if speed > 0:
                eta_sec = (target_size_mb - current_size) / speed
                eta_min = eta_sec / 60
                print(f"Speed: {speed:.1f} MB/s | ETA: {eta_min:.1f} min", end="")

        print()

        # Check if complete (within 1% of target)
        if current_size >= target_size_mb * 0.99:
            print("\n[OK] Download complete!")
            return True

        # Check if download failed (stalled for >5 minutes)
        if stall_count > 30:  # 30 * 10s = 5 minutes
            print("\n[ERROR] Download appears to have stalled")
            return False

        last_size = current_size
        time.sleep(10)


def run_processing_pipeline():
    """Run the complete processing pipeline"""
    print("\n" + "="*70)
    print("AUTOMATIC PROCESSING PIPELINE")
    print("="*70)

    steps = [
        {
            'name': 'Data Processing',
            'command': [sys.executable, 'src/data_processor.py'],
            'description': 'Extract and convert dataset to 4-leg format'
        },
        {
            'name': 'Data Visualization',
            'command': [sys.executable, 'src/visualize_demo_data.py'],
            'description': 'Generate preview charts'
        }
    ]

    for step in steps:
        print(f"\n[*] Step: {step['name']}")
        print(f"    {step['description']}")
        print(f"    Running: {' '.join(step['command'])}")

        try:
            result = subprocess.run(
                step['command'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            print(result.stdout)

            if result.returncode == 0:
                print(f"[OK] {step['name']} completed successfully")
            else:
                print(f"[ERROR] {step['name']} failed:")
                print(result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print(f"[ERROR] {step['name']} timed out")
            return False
        except Exception as e:
            print(f"[ERROR] {step['name']} failed: {e}")
            return False

    return True


def main():
    """Main monitoring and processing"""
    zip_path = "horsing_around_data.zip"

    print("="*70)
    print("EQUINESYNC AUTO-PROCESSOR")
    print("="*70)
    print(f"\nMonitoring: {zip_path}")
    print(f"Target size: 10.96 GB")
    print(f"\nThis script will:")
    print("  1. Monitor download progress")
    print("  2. Auto-extract when complete")
    print("  3. Process data to 4-leg format")
    print("  4. Generate demo sessions")
    print("  5. Create visualizations")
    print("\nPress Ctrl+C to stop monitoring\n")

    try:
        # Monitor download
        if monitor_download(zip_path):
            # Run processing pipeline
            if run_processing_pipeline():
                print("\n" + "="*70)
                print("ALL PROCESSING COMPLETE!")
                print("="*70)
                print("\nYour demo data is ready!")
                print("\nTo run the demo:")
                print("  python run_demo.py")
                print("\nOr for timed recording (3 minutes):")
                print("  python run_demo.py timed 3")
                print("\n" + "="*70)
            else:
                print("\n[ERROR] Processing pipeline failed")
        else:
            print("\n[ERROR] Download did not complete successfully")

    except KeyboardInterrupt:
        print("\n\n[*] Monitoring stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
