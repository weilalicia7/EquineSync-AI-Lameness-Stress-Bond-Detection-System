#!/usr/bin/env python3
"""
Demo Data Loader for EquineSync Dashboard
Loads authentic dataset and serves it via HTTP API
"""

import os
import json
import numpy as np
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import time
from datetime import datetime


app = Flask(__name__)
CORS(app)  # Enable CORS for dashboard access

# Global state
demo_session = None
playback_start_time = None
playback_paused = False
current_sample_index = 0


def load_demo_session(filename: str = 'demo_session_lameness.json'):
    """Load demo session from JSON file"""
    demo_data_dir = Path('demo_data')
    session_path = demo_data_dir / filename

    if not session_path.exists():
        print(f"[ERROR] Demo session not found: {session_path}")
        return None

    with open(session_path, 'r') as f:
        session = json.load(f)

    print(f"[OK] Loaded demo session: {filename}")
    print(f"    Horse: {session['metadata']['horse_id']}")
    print(f"    Duration: {session['metadata']['duration_seconds']:.1f}s")
    print(f"    Samples: {len(session['sensor_data']['timestamps'])}")

    return session


@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'online',
        'timestamp': int(time.time() * 1000),
        'demo_loaded': demo_session is not None,
        'playback_active': playback_start_time is not None
    })


@app.route('/api/metadata')
def get_metadata():
    """Get session metadata"""
    if not demo_session:
        return jsonify({'error': 'No demo session loaded'}), 404

    return jsonify(demo_session['metadata'])


@app.route('/api/sensor/stream')
def get_sensor_stream():
    """
    Get current sensor data (simulated real-time stream)
    Returns data based on elapsed time since playback started
    """
    global current_sample_index, playback_start_time

    if not demo_session:
        return jsonify({'error': 'No demo session loaded'}), 404

    # Initialize playback if not started
    if playback_start_time is None:
        playback_start_time = time.time()
        current_sample_index = 0

    # Calculate current position in playback
    elapsed_time = time.time() - playback_start_time
    sample_rate = demo_session['metadata']['sample_rate_hz']
    target_sample_index = int(elapsed_time * sample_rate)

    # Get sensor data
    sensor_data = demo_session['sensor_data']
    total_samples = len(sensor_data['timestamps'])

    # Loop playback if reached end
    if target_sample_index >= total_samples:
        playback_start_time = time.time()
        target_sample_index = 0

    current_sample_index = target_sample_index

    # Return current window of data (last 2 seconds for gait analysis)
    window_size = sample_rate * 2  # 2 seconds
    start_idx = max(0, target_sample_index - window_size)
    end_idx = target_sample_index

    response = {
        'timestamp': int(sensor_data['timestamps'][target_sample_index]),
        'elapsed_time_sec': elapsed_time,
        'progress_percent': (target_sample_index / total_samples) * 100,
        'sensor_readings': {
            'FL': sensor_data['FL'][start_idx:end_idx],
            'FR': sensor_data['FR'][start_idx:end_idx],
            'BL': sensor_data['BL'][start_idx:end_idx],
            'BR': sensor_data['BR'][start_idx:end_idx]
        },
        'window_timestamps': sensor_data['timestamps'][start_idx:end_idx]
    }

    return jsonify(response)


@app.route('/api/gait/analysis')
def get_gait_analysis():
    """Get real-time gait analysis results"""
    from gait_analysis import GaitAnalyzer

    if not demo_session:
        return jsonify({'error': 'No demo session loaded'}), 404

    # Get current sensor window
    sensor_stream = get_sensor_stream()
    if isinstance(sensor_stream, tuple):  # Error response
        return sensor_stream

    sensor_stream_data = sensor_stream.get_json()

    # Calculate amplitudes from sensor data
    analyzer = GaitAnalyzer()
    amplitudes = {}

    # Use baseline peak from healthy horse data (~7g for walk gait)
    baseline_peak_accel = 7.0

    for sensor_id in ['FL', 'FR', 'BL', 'BR']:
        accel_data = sensor_stream_data['sensor_readings'][sensor_id]
        if len(accel_data) > 0:
            # Use 95th percentile as peak amplitude
            peak_accel = np.percentile(np.abs(accel_data), 95)
            amplitudes[sensor_id] = (peak_accel / baseline_peak_accel) * 100  # Normalize to percentage
        else:
            amplitudes[sensor_id] = 0

    # Calculate symmetry scores
    symmetry = analyzer.calculate_symmetry_scores(amplitudes)

    # Detect alerts
    # Store recent scores for alert detection
    if not hasattr(get_gait_analysis, 'score_history'):
        get_gait_analysis.score_history = []

    get_gait_analysis.score_history.append(symmetry['symmetry_total'])
    if len(get_gait_analysis.score_history) > 5:
        get_gait_analysis.score_history = get_gait_analysis.score_history[-5:]

    alert = analyzer.detect_asymmetry_alert(get_gait_analysis.score_history)

    return jsonify({
        'timestamp': int(time.time() * 1000),
        'symmetry_scores': symmetry,
        'amplitudes': amplitudes,
        'alert_triggered': alert,
        'gait_quality': 'excellent' if symmetry['symmetry_total'] > 85 else
                       'good' if symmetry['symmetry_total'] > 70 else
                       'concerning' if symmetry['symmetry_total'] > 60 else
                       'poor'
    })


@app.route('/api/hrv/analysis')
def get_hrv_analysis():
    """Get HRV analysis results"""
    from hrv_analysis import HRVAnalyzer

    if not demo_session:
        return jsonify({'error': 'No demo session loaded'}), 404

    # Get current position in playback
    elapsed_time = time.time() - playback_start_time if playback_start_time else 0

    # Get HRV data - use last 60 seconds of RR intervals
    hrv_data = demo_session['hrv_data']['rr_intervals_ms']

    # Calculate which heartbeats to analyze (assuming ~1.2 BPM = 72 BPM)
    beats_per_sec = 1.2
    current_beat = int(elapsed_time * beats_per_sec)
    window_beats = 60  # Last 60 heartbeats (~50 seconds)

    start_beat = max(0, current_beat - window_beats)
    end_beat = min(len(hrv_data), current_beat)

    if end_beat - start_beat < 10:
        return jsonify({'error': 'Insufficient HRV data'}), 400

    rr_window = hrv_data[start_beat:end_beat]

    # Analyze HRV
    analyzer = HRVAnalyzer()
    hrv_results = analyzer.analyze_hrv_window(
        rr_window,
        horse_id=demo_session['metadata']['horse_id']
    )

    return jsonify({
        'timestamp': int(time.time() * 1000),
        'hrv_metrics': hrv_results
    })


@app.route('/api/playback/reset')
def reset_playback():
    """Reset playback to beginning"""
    global playback_start_time, current_sample_index
    playback_start_time = None
    current_sample_index = 0
    return jsonify({'status': 'reset', 'message': 'Playback reset to beginning'})


@app.route('/api/sessions/list')
def list_sessions():
    """List available demo sessions"""
    demo_data_dir = Path('demo_data')
    if not demo_data_dir.exists():
        return jsonify({'sessions': []})

    sessions = []
    for json_file in demo_data_dir.glob('*.json'):
        sessions.append({
            'filename': json_file.name,
            'size_mb': json_file.stat().st_size / (1024*1024)
        })

    return jsonify({'sessions': sessions})


@app.route('/api/sessions/load/<filename>')
def load_session(filename):
    """Load a specific demo session"""
    global demo_session, playback_start_time, current_sample_index

    demo_session = load_demo_session(filename)
    playback_start_time = None
    current_sample_index = 0

    if demo_session:
        return jsonify({
            'status': 'loaded',
            'metadata': demo_session['metadata']
        })
    else:
        return jsonify({'error': 'Failed to load session'}), 404


# Serve static dashboard files
@app.route('/')
def serve_index():
    """Serve dashboard index.html"""
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)


def main():
    """Start demo data server"""
    global demo_session

    print("="*70)
    print("EQUINESYNC DEMO DATA SERVER")
    print("="*70)

    # Load default demo session
    demo_session = load_demo_session('demo_session_lameness.json')

    if not demo_session:
        print("\n[WARNING] No demo session loaded. Generate one first:")
        print("  python src/data_processor.py")

    print("\n" + "="*70)
    print("Server starting on http://localhost:8000")
    print("="*70)
    print("\nAPI Endpoints:")
    print("  GET  /api/status              - System status")
    print("  GET  /api/metadata            - Session metadata")
    print("  GET  /api/sensor/stream       - Real-time sensor data")
    print("  GET  /api/gait/analysis       - Gait analysis results")
    print("  GET  /api/hrv/analysis        - HRV analysis results")
    print("  GET  /api/playback/reset      - Reset playback")
    print("  GET  /api/sessions/list       - List available sessions")
    print("  GET  /api/sessions/load/<fn>  - Load specific session")
    print("\nAPI Server: http://localhost:8000")
    print("Dashboard: http://localhost:5180 (serve separately)")
    print("="*70)

    # Start Flask server
    app.run(host='0.0.0.0', port=8000, debug=False)


if __name__ == "__main__":
    main()
