#!/usr/bin/env python3
"""
Visualization Script for Demo Data
Preview processed equine sensor data before demo
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys


def load_demo_session(filename: str = 'demo_session_lameness.json'):
    """Load demo session JSON"""
    demo_data_dir = Path('demo_data')
    session_path = demo_data_dir / filename

    if not session_path.exists():
        print(f"[ERROR] Demo session not found: {session_path}")
        print(f"Run 'python src/data_processor.py' first to generate demo data")
        return None

    with open(session_path, 'r') as f:
        session = json.load(f)

    print(f"[OK] Loaded: {filename}")
    return session


def visualize_gait_data(demo_session: dict):
    """Create comprehensive visualization of gait data"""

    sensor_data = demo_session['sensor_data']
    metadata = demo_session['metadata']

    timestamps_sec = np.array(sensor_data['timestamps']) / 1000.0  # Convert to seconds

    # Create figure with subplots
    fig, axes = plt.subplots(4, 1, figsize=(14, 10))
    fig.suptitle(f'EquineSync Demo Data - Horse: {metadata["horse_id"]}',
                 fontsize=16, fontweight='bold')

    colors = {'FL': '#e74c3c', 'FR': '#3498db', 'BL': '#2ecc71', 'BR': '#f39c12'}
    labels = {'FL': 'Front Left', 'FR': 'Front Right', 'BL': 'Back Left', 'BR': 'Back Right'}

    # Plot 1: All 4 legs overlaid
    ax1 = axes[0]
    for sensor_id in ['FL', 'FR', 'BL', 'BR']:
        ax1.plot(timestamps_sec, sensor_data[sensor_id],
                label=labels[sensor_id], color=colors[sensor_id], alpha=0.7, linewidth=1)

    ax1.set_ylabel('Acceleration (g)', fontsize=11, fontweight='bold')
    ax1.set_title('Raw Sensor Data - All Legs', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', ncol=4, fontsize=9)
    ax1.grid(True, alpha=0.3)

    # Add lameness indicator if present
    if metadata.get('includes_lameness_scenario'):
        lameness_time = metadata['lameness_details']['onset_time_sec']
        ax1.axvline(x=lameness_time, color='red', linestyle='--',
                   linewidth=2, label='Lameness Onset', alpha=0.7)
        ax1.text(lameness_time + 2, ax1.get_ylim()[1] * 0.9,
                'Lameness\nOnset', fontsize=10, color='red', fontweight='bold')

    # Plot 2: Front legs comparison
    ax2 = axes[1]
    ax2.plot(timestamps_sec, sensor_data['FL'], label='Front Left',
            color=colors['FL'], linewidth=1.5)
    ax2.plot(timestamps_sec, sensor_data['FR'], label='Front Right',
            color=colors['FR'], linewidth=1.5)
    ax2.set_ylabel('Acceleration (g)', fontsize=11, fontweight='bold')
    ax2.set_title('Front Legs - Symmetry Comparison', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)

    if metadata.get('includes_lameness_scenario'):
        ax2.axvline(x=lameness_time, color='red', linestyle='--', linewidth=2, alpha=0.7)

    # Plot 3: Hind legs comparison
    ax3 = axes[2]
    ax3.plot(timestamps_sec, sensor_data['BL'], label='Back Left',
            color=colors['BL'], linewidth=1.5)
    ax3.plot(timestamps_sec, sensor_data['BR'], label='Back Right',
            color=colors['BR'], linewidth=1.5)
    ax3.set_ylabel('Acceleration (g)', fontsize=11, fontweight='bold')
    ax3.set_title('Hind Legs - Symmetry Comparison', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)

    if metadata.get('includes_lameness_scenario'):
        ax3.axvline(x=lameness_time, color='red', linestyle='--', linewidth=2, alpha=0.7)

    # Plot 4: Amplitude comparison over time
    ax4 = axes[3]
    window_size = 200  # 2 seconds at 100Hz

    amplitudes_over_time = {sensor_id: [] for sensor_id in ['FL', 'FR', 'BL', 'BR']}
    time_points = []

    for i in range(0, len(timestamps_sec), window_size // 2):  # 50% overlap
        end_idx = min(i + window_size, len(timestamps_sec))
        if end_idx - i < window_size // 2:
            break

        mid_idx = min(i + window_size // 2, len(timestamps_sec) - 1)
        time_points.append(timestamps_sec[mid_idx])

        for sensor_id in ['FL', 'FR', 'BL', 'BR']:
            window = sensor_data[sensor_id][i:end_idx]
            amplitude = np.percentile(np.abs(window), 95)
            amplitudes_over_time[sensor_id].append(amplitude)

    for sensor_id in ['FL', 'FR', 'BL', 'BR']:
        ax4.plot(time_points, amplitudes_over_time[sensor_id],
                label=labels[sensor_id], color=colors[sensor_id],
                linewidth=2, marker='o', markersize=3)

    ax4.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Peak Amplitude (g)', fontsize=11, fontweight='bold')
    ax4.set_title('Gait Amplitude Trends - Lameness Detection', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right', fontsize=9)
    ax4.grid(True, alpha=0.3)

    if metadata.get('includes_lameness_scenario'):
        ax4.axvline(x=lameness_time, color='red', linestyle='--', linewidth=2, alpha=0.7)
        # Highlight affected leg
        affected_leg = metadata['lameness_details']['affected_leg']
        ax4.plot(time_points, amplitudes_over_time[affected_leg],
                color=colors[affected_leg], linewidth=3, alpha=0.8)

    plt.tight_layout()

    # Save figure
    output_path = Path('demo_data') / 'gait_visualization.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Saved visualization: {output_path}")

    return fig


def visualize_hrv_data(demo_session: dict):
    """Visualize HRV data"""

    hrv_data = demo_session['hrv_data']['rr_intervals_ms']
    metadata = demo_session['metadata']

    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 8))
    fig.suptitle(f'Heart Rate Variability Analysis - {metadata["horse_id"]}',
                 fontsize=16, fontweight='bold')

    # Plot 1: RR Intervals over time
    ax1 = axes[0, 0]
    beat_numbers = np.arange(len(hrv_data))
    ax1.plot(beat_numbers, hrv_data, linewidth=1, color='#e74c3c')
    ax1.set_xlabel('Heartbeat Number', fontsize=10, fontweight='bold')
    ax1.set_ylabel('RR Interval (ms)', fontsize=10, fontweight='bold')
    ax1.set_title('RR Interval Tachogram', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Add stress indicator if lameness
    if metadata.get('includes_lameness_scenario'):
        lameness_time = metadata['lameness_details']['onset_time_sec']
        stress_beat = int(lameness_time * 1.2)  # ~72 BPM
        ax1.axvline(x=stress_beat, color='red', linestyle='--',
                   linewidth=2, alpha=0.7)
        ax1.text(stress_beat + 5, ax1.get_ylim()[1] * 0.95,
                'Stress\nIncrease', fontsize=9, color='red', fontweight='bold')

    # Plot 2: RR Interval Distribution
    ax2 = axes[0, 1]
    ax2.hist(hrv_data, bins=30, color='#3498db', alpha=0.7, edgecolor='black')
    ax2.axvline(x=np.mean(hrv_data), color='red', linestyle='--',
               linewidth=2, label=f'Mean: {np.mean(hrv_data):.1f} ms')
    ax2.set_xlabel('RR Interval (ms)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Frequency', fontsize=10, fontweight='bold')
    ax2.set_title('RR Interval Distribution', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Successive Differences (for RMSSD)
    ax3 = axes[1, 0]
    successive_diffs = np.diff(hrv_data)
    ax3.plot(successive_diffs, linewidth=1, color='#2ecc71')
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.5)
    ax3.axhline(y=50, color='orange', linestyle='--', linewidth=1, alpha=0.5, label='50ms threshold')
    ax3.axhline(y=-50, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax3.set_xlabel('Heartbeat Pair', fontsize=10, fontweight='bold')
    ax3.set_ylabel('RR Difference (ms)', fontsize=10, fontweight='bold')
    ax3.set_title('Successive RR Differences (RMSSD Calculation)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)

    # Plot 4: HRV Metrics Summary
    ax4 = axes[1, 1]
    ax4.axis('off')

    # Calculate HRV metrics
    sdnn = np.std(hrv_data, ddof=1)
    rmssd = np.sqrt(np.mean(successive_diffs ** 2))
    pnn50 = (np.sum(np.abs(successive_diffs) > 50) / len(successive_diffs)) * 100
    mean_hr = 60000 / np.mean(hrv_data)  # BPM

    summary_text = f"""
    HRV Metrics Summary
    {'='*40}

    Mean RR Interval: {np.mean(hrv_data):.1f} ms
    Mean Heart Rate: {mean_hr:.1f} BPM

    SDNN: {sdnn:.2f} ms
    Status: {'Good' if sdnn > 50 else 'Warning' if sdnn > 30 else 'Alert'}

    RMSSD: {rmssd:.2f} ms
    Status: {'Good' if rmssd > 40 else 'Warning' if rmssd > 20 else 'Alert'}

    pNN50: {pnn50:.2f} %
    Status: {'Good' if pnn50 > 3 else 'Warning' if pnn50 > 1 else 'Alert'}

    Overall Stress: {'Low' if sdnn > 50 else 'Moderate' if sdnn > 30 else 'High'}
    """

    ax4.text(0.1, 0.9, summary_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save figure
    output_path = Path('demo_data') / 'hrv_visualization.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[OK] Saved visualization: {output_path}")

    return fig


def print_summary(demo_session: dict):
    """Print detailed summary of demo session"""

    metadata = demo_session['metadata']
    sensor_data = demo_session['sensor_data']
    hrv_data = demo_session['hrv_data']

    print("\n" + "="*70)
    print("DEMO SESSION SUMMARY")
    print("="*70)

    print(f"\nHorse ID: {metadata['horse_id']}")
    print(f"Session ID: {metadata['session_id']}")
    print(f"Duration: {metadata['duration_seconds']:.1f} seconds")
    print(f"Sample Rate: {metadata['sample_rate_hz']} Hz")
    print(f"Total Samples: {len(sensor_data['timestamps']):,}")

    print(f"\nData Source: {metadata['data_source']}")
    print(f"License: {metadata['license']}")

    if metadata.get('includes_lameness_scenario'):
        lameness = metadata['lameness_details']
        print(f"\n[!] LAMENESS SCENARIO INCLUDED:")
        print(f"    Affected Leg: {lameness['affected_leg']}")
        print(f"    Onset Time: {lameness['onset_time_sec']}s")
        print(f"    Severity: {lameness['severity']}")
    else:
        print(f"\n[OK] Healthy gait - No lameness scenario")

    print(f"\nSensor Data Statistics:")
    for sensor_id in ['FL', 'FR', 'BL', 'BR']:
        data = np.array(sensor_data[sensor_id])
        print(f"  {sensor_id}: mean={np.mean(data):.3f}g, "
              f"std={np.std(data):.3f}g, "
              f"range=[{np.min(data):.3f}, {np.max(data):.3f}]g")

    rr_intervals = np.array(hrv_data['rr_intervals_ms'])
    print(f"\nHRV Data:")
    print(f"  Total Heartbeats: {len(rr_intervals)}")
    print(f"  Mean RR: {np.mean(rr_intervals):.1f} ms")
    print(f"  Mean HR: {60000 / np.mean(rr_intervals):.1f} BPM")
    print(f"  SDNN: {np.std(rr_intervals, ddof=1):.2f} ms")

    print("\n" + "="*70)


def main():
    """Main visualization script"""
    print("="*70)
    print("EQUINESYNC DEMO DATA VISUALIZATION")
    print("="*70)

    # Allow specifying which session to visualize
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'demo_session_lameness.json'

    # Load demo session
    demo_session = load_demo_session(filename)

    if not demo_session:
        return

    # Print summary
    print_summary(demo_session)

    # Create visualizations
    print(f"\n[*] Generating visualizations...")

    try:
        visualize_gait_data(demo_session)
        visualize_hrv_data(demo_session)

        print(f"\n[OK] Visualizations complete!")
        print(f"\nTo view the plots:")
        print(f"  1. Check demo_data/gait_visualization.png")
        print(f"  2. Check demo_data/hrv_visualization.png")
        print(f"\nOr run again and plots will be displayed on screen.")

        # Optionally show plots
        # plt.show()

    except Exception as e:
        print(f"[ERROR] Visualization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
