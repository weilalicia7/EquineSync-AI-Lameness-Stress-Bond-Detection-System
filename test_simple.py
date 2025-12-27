#!/usr/bin/env python3
"""Simple test without unicode for Windows compatibility"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("\n" + "="*70)
print("EQUINESYNC TEST SUITE")
print("="*70)

# Test 1: Imports
print("\n[TEST 1] Checking Python imports...")
try:
    import confluent_kafka
    print("  [OK] Confluent Kafka")
    import numpy
    print("  [OK] NumPy")
    import scipy
    print("  [OK] SciPy")
    import pandas
    print("  [OK] Pandas")
    print("[PASS] All imports successful\n")
except ImportError as e:
    print(f"[FAIL] Import error: {e}\n")
    sys.exit(1)

# Test 2: Gait Analysis
print("[TEST 2] Testing Gait Analysis...")
try:
    from gait_analysis import GaitAnalyzer
    analyzer = GaitAnalyzer()
    result = analyzer.calculate_symmetry_scores({
        'FL': 98.5, 'FR': 100.2, 'BL': 97.8, 'BR': 99.1
    })
    print(f"  Symmetry Total: {result['symmetry_total']:.1f}")
    print(f"  Front: {result['symmetry_front']:.1f}")
    print(f"  Hind: {result['symmetry_hind']:.1f}")
    assert 0 <= result['symmetry_total'] <= 100
    print("[PASS] Gait analysis working\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: HRV Analysis
print("[TEST 3] Testing HRV Analysis...")
try:
    import numpy as np
    from hrv_analysis import HRVAnalyzer
    analyzer = HRVAnalyzer()
    rr_data = np.random.normal(600, 50, 100).tolist()
    result = analyzer.analyze_hrv_window(rr_data, 'test')
    print(f"  SDNN: {result.get('sdnn', 0):.1f}ms")
    print(f"  Stress: {result.get('stress_level', 'Unknown')}")
    assert result.get('sdnn', 0) > 0
    print("[PASS] HRV analysis working\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    sys.exit(1)

# Test 4: Vertex AI Client
print("[TEST 4] Testing Vertex AI Client...")
try:
    from vertex_ai_client import VertexAIClient
    client = VertexAIClient()
    print("[PASS] Vertex AI client initialized\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    sys.exit(1)

# Test 5: Config files
print("[TEST 5] Checking configuration files...")
files_ok = True
for f in ['config/kafka_topics.json', 'config/alert_thresholds.json', 'requirements.txt']:
    if os.path.exists(f):
        print(f"  [OK] {f}")
    else:
        print(f"  [MISSING] {f}")
        files_ok = False

if files_ok:
    print("[PASS] All config files present\n")
else:
    print("[FAIL] Some config files missing\n")
    sys.exit(1)

# Test 6: End-to-end simulation
print("[TEST 6] End-to-end simulation...")
try:
    import numpy as np
    from gait_analysis import GaitAnalyzer
    from hrv_analysis import HRVAnalyzer

    gait_analyzer = GaitAnalyzer()
    hrv_analyzer = HRVAnalyzer()

    # Simulate data
    amplitudes = {'FL': 55.0, 'FR': 100.0, 'BL': 98.0, 'BR': 99.0}
    symmetry = gait_analyzer.calculate_symmetry_scores(amplitudes)

    rr = np.random.normal(600, 50, 100).tolist()
    hrv = hrv_analyzer.analyze_hrv_window(rr, 'test')

    # Test alert
    low_scores = [55, 53, 52]
    alert = gait_analyzer.detect_asymmetry_alert(low_scores)

    print(f"  Symmetry: {symmetry['symmetry_total']:.1f}")
    print(f"  HRV Stress: {hrv['stress_level']}")
    print(f"  Alert Triggered: {alert}")
    print("[PASS] End-to-end flow working\n")
except Exception as e:
    print(f"[FAIL] {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("="*70)
print("ALL TESTS PASSED!")
print("="*70)
print("\nYour EquineSync installation is ready!")
print("\nNext steps:")
print("  1. Configure .env with Confluent Cloud credentials")
print("  2. Run: python src/sensor_simulator.py --duration 30")
print("  3. Run: python src/stream_processor.py (in another terminal)")
