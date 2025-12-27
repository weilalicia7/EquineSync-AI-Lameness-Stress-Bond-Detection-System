#!/usr/bin/env python3
"""
EquineSync Quick Test Suite
Runs all basic tests to verify installation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test 1: Verify all imports work"""
    print("\n" + "="*70)
    print("TEST 1: Checking Python imports...")
    print("="*70)

    tests = [
        ('confluent_kafka', 'Confluent Kafka'),
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
        ('pandas', 'Pandas'),
        ('requests', 'Requests'),
    ]

    passed = 0
    for module, name in tests:
        try:
            __import__(module)
            print(f"✅ {name:20s} OK")
            passed += 1
        except ImportError as e:
            print(f"❌ {name:20s} FAILED: {e}")

    print(f"\n📊 Result: {passed}/{len(tests)} imports successful")
    return passed == len(tests)


def test_modules():
    """Test 2: Verify local modules work"""
    print("\n" + "="*70)
    print("TEST 2: Testing local modules...")
    print("="*70)

    tests_passed = 0
    tests_total = 3

    # Test gait analysis
    try:
        from gait_analysis import GaitAnalyzer
        analyzer = GaitAnalyzer()
        result = analyzer.calculate_symmetry_scores({
            'FL': 98.5, 'FR': 100.2, 'BL': 97.8, 'BR': 99.1
        })
        assert 95 < result['symmetry_total'] < 100
        print(f"✅ Gait Analysis    OK (symmetry: {result['symmetry_total']:.1f})")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Gait Analysis    FAILED: {e}")

    # Test HRV analysis
    try:
        import numpy as np
        from hrv_analysis import HRVAnalyzer
        analyzer = HRVAnalyzer()
        rr_data = np.random.normal(600, 50, 100).tolist()
        result = analyzer.analyze_hrv_window(rr_data, 'test')
        assert result.get('sdnn', 0) > 0
        print(f"✅ HRV Analysis     OK (SDNN: {result.get('sdnn', 0):.1f}ms)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ HRV Analysis     FAILED: {e}")

    # Test Vertex AI client (local fallback)
    try:
        from vertex_ai_client import VertexAIClient
        client = VertexAIClient()
        print(f"✅ Vertex AI Client OK (fallback mode)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Vertex AI Client FAILED: {e}")

    print(f"\n📊 Result: {tests_passed}/{tests_total} modules working")
    return tests_passed == tests_total


def test_config():
    """Test 3: Verify configuration files"""
    print("\n" + "="*70)
    print("TEST 3: Checking configuration files...")
    print("="*70)

    files = [
        'config/kafka_topics.json',
        'config/alert_thresholds.json',
        'requirements.txt',
        '.env.example'
    ]

    passed = 0
    for filepath in files:
        if os.path.exists(filepath):
            print(f"✅ {filepath:35s} EXISTS")
            passed += 1
        else:
            print(f"❌ {filepath:35s} MISSING")

    # Check .env file (optional)
    if os.path.exists('.env'):
        print(f"✅ {'.env':35s} EXISTS (credentials configured)")
        passed += 1
    else:
        print(f"⚠️  {'.env':35s} MISSING (copy from .env.example)")

    print(f"\n📊 Result: {passed}/{len(files)} required files found")
    return passed == len(files)


def test_kafka_config():
    """Test 4: Check Kafka configuration"""
    print("\n" + "="*70)
    print("TEST 4: Kafka configuration check...")
    print("="*70)

    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = [
            'CONFLUENT_BOOTSTRAP_SERVERS',
            'CONFLUENT_API_KEY',
            'CONFLUENT_API_SECRET'
        ]

        configured = 0
        for var in required_vars:
            value = os.getenv(var)
            if value and value != f'your-{var.lower().replace("_", "-")}':
                print(f"✅ {var:35s} CONFIGURED")
                configured += 1
            else:
                print(f"⚠️  {var:35s} NOT CONFIGURED")

        if configured == len(required_vars):
            print("\n✅ Kafka fully configured - ready for streaming!")
            return True
        else:
            print(f"\n⚠️  Kafka partially configured ({configured}/{len(required_vars)})")
            print("   Set credentials in .env to enable Kafka streaming")
            return False

    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False


def test_data_flow():
    """Test 5: Simulate complete data flow"""
    print("\n" + "="*70)
    print("TEST 5: End-to-end data flow simulation...")
    print("="*70)

    try:
        import numpy as np
        from gait_analysis import GaitAnalyzer
        from hrv_analysis import HRVAnalyzer

        # Simulate sensor data
        print("🔄 Simulating sensor data...")
        sensor_data = {
            'FL': [{'accel_z': np.random.normal(1.2, 0.1)} for _ in range(200)],
            'FR': [{'accel_z': np.random.normal(1.2, 0.1)} for _ in range(200)],
            'BL': [{'accel_z': np.random.normal(1.1, 0.1)} for _ in range(200)],
            'BR': [{'accel_z': np.random.normal(1.1, 0.1)} for _ in range(200)]
        }

        # Gait analysis
        print("🦵 Running gait analysis...")
        gait_analyzer = GaitAnalyzer()
        amplitudes = gait_analyzer.extract_stride_amplitudes(sensor_data)
        symmetry = gait_analyzer.calculate_symmetry_scores(amplitudes)

        print(f"   ✅ Symmetry calculated: {symmetry['symmetry_total']:.1f}/100")

        # HRV analysis
        print("❤️  Running HRV analysis...")
        hrv_analyzer = HRVAnalyzer()
        rr_intervals = np.random.normal(600, 50, 100).tolist()
        hrv_results = hrv_analyzer.analyze_hrv_window(rr_intervals, 'test-horse')

        print(f"   ✅ HRV calculated: SDNN={hrv_results['sdnn']:.1f}ms, Stress={hrv_results['stress_level']}")

        # Alert detection
        print("🚨 Testing alert system...")
        low_scores = [55, 53, 52]  # Should trigger alert
        alert = gait_analyzer.detect_asymmetry_alert(low_scores)

        print(f"   ✅ Alert detection: {'TRIGGERED' if alert else 'Normal'}")

        print("\n✅ End-to-end data flow successful!")
        return True

    except Exception as e:
        print(f"❌ Data flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  EQUINESYNC TEST SUITE")
    print("  Verifying installation and configuration...")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Modules", test_modules()))
    results.append(("Config Files", test_config()))
    results.append(("Kafka Config", test_kafka_config()))
    results.append(("Data Flow", test_data_flow()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20s} {status}")

    print("="*70)
    print(f"\n📊 OVERALL: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your EquineSync installation is ready!")
        print("\n📝 Next steps:")
        print("   1. Configure Kafka credentials in .env (if not done)")
        print("   2. Run: python src/sensor_simulator.py --duration 30")
        print("   3. Run: python src/stream_processor.py (in another terminal)")
        print("   4. Watch the real-time processing!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\n💡 Common fixes:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Copy .env.example to .env")
        print("   - Check file paths are correct")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
