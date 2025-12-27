#!/usr/bin/env python3
"""
Automated Demo Runner for EquineSync
Orchestrates the complete demo experience for video recording
"""

import os
import sys
import time
import subprocess
import json
from pathlib import Path
import signal


class DemoRunner:
    """Automated demo orchestrator"""

    def __init__(self):
        self.processes = []
        self.demo_session = None

    def check_prerequisites(self):
        """Check if all required files exist"""
        print("\n" + "="*70)
        print("CHECKING PREREQUISITES")
        print("="*70)

        required_files = [
            'src/demo_data_loader.py',
            'src/gait_analysis.py',
            'src/hrv_analysis.py',
            'demo_data/demo_session_lameness.json'
        ]

        all_good = True
        for file_path in required_files:
            exists = Path(file_path).exists()
            status = "[OK]" if exists else "[MISSING]"
            print(f"  {status} {file_path}")

            if not exists:
                all_good = False

        if not all_good:
            print("\n[ERROR] Missing required files!")
            print("Run 'python src/data_processor.py' first to generate demo data.")
            return False

        print("\n[OK] All prerequisites met!")
        return True

    def load_demo_metadata(self):
        """Load demo session metadata"""
        session_path = Path('demo_data/demo_session_lameness.json')

        with open(session_path, 'r') as f:
            self.demo_session = json.load(f)

        metadata = self.demo_session['metadata']
        print(f"\n[*] Loaded demo session:")
        print(f"    Horse: {metadata['horse_id']}")
        print(f"    Duration: {metadata['duration_seconds']:.0f}s")

        if metadata.get('includes_lameness_scenario'):
            lameness = metadata['lameness_details']
            print(f"    Lameness onset: {lameness['onset_time_sec']}s ({lameness['affected_leg']})")

    def start_data_server(self):
        """Start the demo data server"""
        print("\n" + "="*70)
        print("STARTING DEMO DATA SERVER")
        print("="*70)

        # Start Flask server
        cmd = [sys.executable, 'src/demo_data_loader.py']

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )

        self.processes.append(('data_server', process))

        # Wait for server to start
        print("[*] Waiting for server to start...")
        time.sleep(3)

        # Check if server is running
        try:
            import requests
            response = requests.get('http://localhost:5180/api/status', timeout=5)
            if response.status_code == 200:
                print("[OK] Data server is running at http://localhost:5180")
                return True
        except:
            print("[ERROR] Server failed to start")
            return False

    def display_demo_timeline(self):
        """Display demo timeline for reference during recording"""

        if not self.demo_session:
            return

        metadata = self.demo_session['metadata']
        duration = metadata['duration_seconds']

        print("\n" + "="*70)
        print("DEMO TIMELINE")
        print("="*70)

        timeline = [
            (0, "START", "Normal gait, healthy horse"),
            (15, "15s", "Stable gait, good symmetry"),
            (30, "30s", "Continued healthy movement"),
            (45, "45s", "Pre-lameness baseline"),
        ]

        if metadata.get('includes_lameness_scenario'):
            lameness_time = metadata['lameness_details']['onset_time_sec']
            affected_leg = metadata['lameness_details']['affected_leg']

            timeline.extend([
                (lameness_time, "LAMENESS ONSET", f"{affected_leg} begins to show reduced amplitude"),
                (lameness_time + 5, f"{lameness_time + 5:.0f}s", "Asymmetry becomes measurable"),
                (lameness_time + 10, f"{lameness_time + 10:.0f}s", "Alert triggered - symmetry <60"),
                (lameness_time + 20, f"{lameness_time + 20:.0f}s", "Persistent asymmetry, increased stress"),
            ])

        timeline.append((duration, "END", "Demo complete"))

        for time_sec, label, description in timeline:
            print(f"  {time_sec:>3.0f}s | {label:<20s} | {description}")

        print("="*70)

    def show_api_endpoints(self):
        """Display available API endpoints for demo"""
        print("\n" + "="*70)
        print("API ENDPOINTS FOR DEMO")
        print("="*70)

        endpoints = [
            ("GET /api/status", "System status check"),
            ("GET /api/metadata", "Session metadata"),
            ("GET /api/sensor/stream", "Real-time sensor data stream"),
            ("GET /api/gait/analysis", "Gait symmetry analysis"),
            ("GET /api/hrv/analysis", "Heart rate variability analysis"),
            ("GET /api/playback/reset", "Reset playback to start"),
        ]

        for endpoint, description in endpoints:
            print(f"  {endpoint:<30s} - {description}")

        print("\nDashboard: http://localhost:5180")
        print("="*70)

    def run_interactive_demo(self):
        """Run interactive demo with user prompts"""
        print("\n" + "="*70)
        print("INTERACTIVE DEMO MODE")
        print("="*70)

        print("\nThe demo data server is now running.")
        print("You can:")
        print("  1. Open http://localhost:5180 in your browser")
        print("  2. Use the API endpoints to fetch real-time data")
        print("  3. Record your screen while the demo plays")

        print("\nDemo will auto-loop when it reaches the end.")
        print("\nPress Ctrl+C to stop the demo server.")

        try:
            # Keep running until user stops
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[*] Stopping demo...")

    def run_timed_demo(self, duration_minutes: int = 3):
        """Run demo for a specific duration"""
        print("\n" + "="*70)
        print(f"TIMED DEMO MODE - {duration_minutes} minutes")
        print("="*70)

        print(f"\n[*] Demo will run for {duration_minutes} minutes")
        print("[*] Recording should start NOW!")

        duration_seconds = duration_minutes * 60

        try:
            for elapsed in range(duration_seconds):
                remaining = duration_seconds - elapsed
                mins, secs = divmod(remaining, 60)

                # Print progress every 10 seconds
                if elapsed % 10 == 0:
                    print(f"  Time remaining: {mins:02d}:{secs:02d}")

                time.sleep(1)

            print("\n[OK] Demo time complete!")

        except KeyboardInterrupt:
            print("\n\n[*] Demo stopped early")

    def cleanup(self):
        """Stop all processes"""
        print("\n" + "="*70)
        print("CLEANING UP")
        print("="*70)

        for name, process in self.processes:
            print(f"[*] Stopping {name}...")
            process.terminate()

            try:
                process.wait(timeout=5)
                print(f"[OK] {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"[!] Forcing {name} to stop...")
                process.kill()

        print("[OK] Cleanup complete")

    def run(self, mode: str = 'interactive', duration: int = 3):
        """
        Run the complete demo

        Args:
            mode: 'interactive' or 'timed'
            duration: Duration in minutes (for timed mode)
        """
        try:
            # Check prerequisites
            if not self.check_prerequisites():
                return

            # Load metadata
            self.load_demo_metadata()

            # Show timeline
            self.display_demo_timeline()

            # Show API endpoints
            self.show_api_endpoints()

            # Start data server
            if not self.start_data_server():
                return

            # Run demo
            if mode == 'timed':
                self.run_timed_demo(duration)
            else:
                self.run_interactive_demo()

        except Exception as e:
            print(f"\n[ERROR] Demo failed: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.cleanup()


def main():
    """Main entry point"""
    print("="*70)
    print("EQUINESYNC AUTOMATED DEMO RUNNER")
    print("="*70)

    # Parse command line arguments
    mode = 'interactive'
    duration = 3

    if len(sys.argv) > 1:
        if sys.argv[1] == 'timed':
            mode = 'timed'
            if len(sys.argv) > 2:
                duration = int(sys.argv[2])

    # Run demo
    runner = DemoRunner()
    runner.run(mode=mode, duration=duration)


if __name__ == "__main__":
    main()
