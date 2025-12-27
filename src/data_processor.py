#!/usr/bin/env python3
"""
Data Processor for Horsing Around Dataset
Converts authentic equine IMU data into EquineSync format
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from pathlib import Path
import zipfile


class HorsingAroundProcessor:
    """Process the Horsing Around dataset for EquineSync demo"""

    def __init__(self, data_dir: str):
        """
        Initialize processor

        Args:
            data_dir: Directory containing extracted dataset
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path('demo_data')
        self.output_dir.mkdir(exist_ok=True)

    def extract_dataset(self, zip_path: str):
        """Extract the downloaded ZIP file"""
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.data_dir)
        print(f"[OK] Extracted to {self.data_dir}")

    def explore_structure(self):
        """Explore and document the dataset structure"""
        print("\n=== Dataset Structure ===")

        # Find all CSV files in csv directory
        csv_dir = self.data_dir / 'csv'
        if not csv_dir.exists():
            print(f"[ERROR] CSV directory not found: {csv_dir}")
            return []

        all_files = list(csv_dir.glob('subject_*.csv'))

        print(f"Found {len(all_files)} horse data files:")
        for f in sorted(all_files)[:10]:  # Show first 10
            rel_path = f.relative_to(self.data_dir)
            size_mb = f.stat().st_size / (1024*1024)
            print(f"  {rel_path} ({size_mb:.2f} MB)")

        if len(all_files) > 10:
            print(f"  ... and {len(all_files) - 10} more files")

        return all_files

    def load_csv_sample(self, csv_file: Path, nrows: int = 1000) -> pd.DataFrame:
        """Load a sample from CSV file to understand structure"""
        try:
            df = pd.read_csv(csv_file, nrows=nrows)
            print(f"\n[OK] Loaded {csv_file.name}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Shape: {df.shape}")
            print(f"  First few rows:")
            print(df.head())
            return df
        except Exception as e:
            print(f"[ERROR] Could not load {csv_file.name}: {e}")
            return None

    def convert_to_four_leg_format(
        self,
        neck_imu_data: pd.DataFrame,
        duration_seconds: int = 180
    ) -> Dict:
        """
        Convert single-neck IMU data to 4-leg sensor format

        The original dataset has IMU on horse neck. We'll simulate
        4 leg sensors by applying biomechanically realistic transformations.

        Args:
            neck_imu_data: DataFrame with neck IMU readings
            duration_seconds: Duration of demo session

        Returns:
            Dict with 4-leg sensor data in EquineSync format
        """
        print(f"\n=== Converting to 4-Leg Format ===")

        # Expected columns: accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
        # Sample at 100Hz to match dataset

        sample_rate = 100  # Hz
        total_samples = duration_seconds * sample_rate

        # Ensure we have enough data
        if len(neck_imu_data) < total_samples:
            # Repeat data if needed
            repetitions = (total_samples // len(neck_imu_data)) + 1
            neck_imu_data = pd.concat([neck_imu_data] * repetitions).reset_index(drop=True)

        neck_imu_data = neck_imu_data.iloc[:total_samples]

        # Extract neck accelerometer data (vertical axis)
        try:
            # Try standard column name from Horsing Around dataset
            neck_accel_z = neck_imu_data['Az'].values
        except KeyError:
            # Try alternative column names
            possible_names = ['accel_z', 'AccZ', 'acc_z', 'acceleration_z', 'az']
            for name in possible_names:
                if name in neck_imu_data.columns:
                    neck_accel_z = neck_imu_data[name].values
                    break
            else:
                # Use first numeric column
                print(f"[WARNING] No Az column found. Using first numeric column.")
                print(f"[WARNING] Available columns: {list(neck_imu_data.columns)}")
                neck_accel_z = neck_imu_data.iloc[:, 0].values

        print(f"  Neck accel_z range: [{neck_accel_z.min():.2f}, {neck_accel_z.max():.2f}]")

        # Simulate 4-leg sensors from neck data
        # Apply phase shifts and amplitude adjustments based on gait biomechanics

        timestamps = np.arange(total_samples) * (1000.0 / sample_rate)  # milliseconds

        # Detect gait frequency from neck motion
        from scipy import signal
        freqs = np.fft.fftfreq(len(neck_accel_z), 1/sample_rate)
        fft = np.fft.fft(neck_accel_z)
        dominant_freq_idx = np.argmax(np.abs(fft[1:len(fft)//2])) + 1
        gait_freq = abs(freqs[dominant_freq_idx])

        print(f"  Detected gait frequency: {gait_freq:.2f} Hz")

        # Generate 4-leg data with realistic phase relationships
        # Front-left (FL) - reference
        # Front-right (FR) - 180° out of phase with FL
        # Back-left (BL) - 180° out of phase with FL
        # Back-right (BR) - in phase with FL

        sensor_data = {
            'FL': [],
            'FR': [],
            'BL': [],
            'BR': [],
            'timestamps': timestamps.tolist()
        }

        # Phase offsets for trot gait (diagonal pairs move together)
        phase_offsets = {
            'FL': 0,
            'FR': np.pi,
            'BL': np.pi,
            'BR': 0
        }

        # Amplitude variations (legs have different impact forces)
        amplitude_factors = {
            'FL': 1.0,
            'FR': 0.98,  # Slightly less (common asymmetry)
            'BL': 0.95,
            'BR': 0.97
        }

        for sensor_id, phase_offset in phase_offsets.items():
            # Shift neck data to leg motion with phase adjustment
            t = np.arange(len(neck_accel_z)) / sample_rate
            phase_shift_samples = int((phase_offset / (2 * np.pi * gait_freq)) * sample_rate)

            # Circular shift
            leg_accel = np.roll(neck_accel_z, phase_shift_samples)

            # Apply amplitude factor
            leg_accel = leg_accel * amplitude_factors[sensor_id]

            # Add slight noise for realism
            noise = np.random.normal(0, 0.05, len(leg_accel))
            leg_accel = leg_accel + noise

            sensor_data[sensor_id] = leg_accel.tolist()

        return sensor_data

    def generate_demo_session(
        self,
        sensor_data: Dict,
        include_lameness: bool = True,
        lameness_start_time: float = 60.0,
        lame_leg: str = 'FL'
    ) -> Dict:
        """
        Generate a complete demo session with realistic scenarios

        Args:
            sensor_data: 4-leg sensor data
            include_lameness: Whether to inject lameness scenario
            lameness_start_time: When lameness begins (seconds)
            lame_leg: Which leg develops lameness

        Returns:
            Complete demo session with metadata
        """
        print(f"\n=== Generating Demo Session ===")

        if include_lameness:
            # Inject lameness by reducing amplitude after start time
            sample_rate = 100
            start_sample = int(lameness_start_time * sample_rate)

            original_amplitude = np.std(sensor_data[lame_leg][:start_sample])

            for i in range(start_sample, len(sensor_data[lame_leg])):
                # Gradually reduce amplitude by 45% (severe lameness)
                progress = min(1.0, (i - start_sample) / (sample_rate * 5))  # 5s transition
                reduction = 0.45 * progress
                sensor_data[lame_leg][i] *= (1 - reduction)

            reduced_amplitude = np.std(sensor_data[lame_leg][start_sample:])
            print(f"  Injected lameness in {lame_leg}")
            print(f"    Original amplitude: {original_amplitude:.2f}")
            print(f"    Reduced amplitude: {reduced_amplitude:.2f}")
            print(f"    Reduction: {((original_amplitude - reduced_amplitude) / original_amplitude * 100):.1f}%")

        # Generate HRV data (simulated for now - could extract from dataset if available)
        duration_sec = len(sensor_data['timestamps']) / 100
        num_heartbeats = int(duration_sec * 1.2)  # ~72 BPM resting

        # Healthy HRV with some variation
        mean_rr = 600  # ms
        sdnn = 50  # healthy variation
        rr_intervals = np.random.normal(mean_rr, sdnn, num_heartbeats).tolist()

        # If lameness occurs, increase stress (reduce HRV)
        if include_lameness:
            stress_start_beat = int(lameness_start_time * 1.2)
            for i in range(stress_start_beat, len(rr_intervals)):
                rr_intervals[i] = np.random.normal(mean_rr, 25, 1)[0]  # Reduced HRV

        demo_session = {
            'metadata': {
                'horse_id': 'Thunder',
                'session_id': 'demo_session_001',
                'duration_seconds': duration_sec,
                'sample_rate_hz': 100,
                'data_source': 'Horsing Around Dataset (4TU ResearchData)',
                'license': 'CC0',
                'includes_lameness_scenario': include_lameness,
                'lameness_details': {
                    'affected_leg': lame_leg,
                    'onset_time_sec': lameness_start_time,
                    'severity': 'moderate_to_severe'
                } if include_lameness else None
            },
            'sensor_data': sensor_data,
            'hrv_data': {
                'rr_intervals_ms': rr_intervals
            }
        }

        return demo_session

    def save_demo_session(self, demo_session: Dict, filename: str = 'demo_session.json'):
        """Save demo session to JSON file"""
        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            json.dump(demo_session, f, indent=2)

        size_mb = output_path.stat().st_size / (1024*1024)
        print(f"\n[OK] Saved demo session: {output_path}")
        print(f"    Size: {size_mb:.2f} MB")
        print(f"    Duration: {demo_session['metadata']['duration_seconds']:.1f} seconds")

        return output_path


def main():
    """Main processing pipeline"""
    print("="*70)
    print("HORSING AROUND DATASET PROCESSOR")
    print("="*70)

    # Initialize processor
    processor = HorsingAroundProcessor('horsing_around_data')

    # Extract ZIP if needed
    zip_path = 'horsing_around_data.zip'
    if os.path.exists(zip_path) and not processor.data_dir.exists():
        processor.extract_dataset(zip_path)

    # Explore structure
    files = processor.explore_structure()

    if not files:
        print("[ERROR] No data files found. Ensure dataset is extracted.")
        return

    # Load a sample CSV to understand structure
    csv_files = [f for f in files if f.suffix == '.csv']
    if csv_files:
        sample_df = processor.load_csv_sample(csv_files[0], nrows=5000)

        if sample_df is not None:
            # Convert to 4-leg format
            sensor_data = processor.convert_to_four_leg_format(sample_df, duration_seconds=180)

            # Generate demo session with lameness
            demo_session = processor.generate_demo_session(
                sensor_data,
                include_lameness=True,
                lameness_start_time=60.0,
                lame_leg='FL'
            )

            # Save
            processor.save_demo_session(demo_session, 'demo_session_lameness.json')

            # Generate healthy session
            demo_session_healthy = processor.generate_demo_session(
                sensor_data,
                include_lameness=False
            )

            processor.save_demo_session(demo_session_healthy, 'demo_session_healthy.json')

    print("\n" + "="*70)
    print("PROCESSING COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    main()
