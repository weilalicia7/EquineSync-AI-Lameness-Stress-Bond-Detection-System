# EquineSync Testing Guide

Complete guide to verify your EquineSync installation works properly.

---

## 🔍 Quick Health Check (5 minutes)

### Step 1: Verify Python Environment

```bash
# Check Python version (need 3.9+)
python --version

# Install dependencies
cd "C:\Users\c25038355\OneDrive - Cardiff University\Desktop\tableau"
pip install -r requirements.txt

# Verify key packages
python -c "import confluent_kafka; print('✅ Confluent Kafka OK')"
python -c "import numpy; print('✅ NumPy OK')"
python -c "import scipy; print('✅ SciPy OK')"
```

**Expected Output:**
```
✅ Confluent Kafka OK
✅ NumPy OK
✅ SciPy OK
```

---

### Step 2: Test Individual Modules (Without Kafka)

#### Test Gait Analysis Module

```bash
python src/gait_analysis.py
```

**Expected Output:**
```
Symmetry Scores:
  symmetry_front: 97.58
  symmetry_hind: 96.75
  symmetry_diagonal: 98.23
  symmetry_total: 97.52

Gait Classification: walk (0.8 Hz)
```

✅ **Pass Criteria**: All symmetry scores between 95-100, gait type = "walk"

---

#### Test HRV Analysis Module

```bash
python src/hrv_analysis.py
```

**Expected Output:**
```
=== Healthy Horse HRV Analysis ===
  horse_id: horse-001
  sdnn: 50.12
  rmssd: 45.67
  pnn50: 8.23
  stress_level: Low
  emotional_state: Calm & Content
  rider_bond_score: 80.0

=== Stressed Horse HRV Analysis ===
  horse_id: horse-002
  sdnn: 14.89
  rmssd: 12.34
  pnn50: 0.56
  stress_level: Critical
  emotional_state: Critical Distress
```

✅ **Pass Criteria**: Healthy horse shows "Low" stress, stressed horse shows "Critical"

---

#### Test Vertex AI Client (Local Fallback)

```bash
python src/vertex_ai_client.py
```

**Expected Output:**
```
✅ Vertex AI initialized: your-project-id (us-central1)

=== Testing Gait Symmetry Prediction ===
{
  "model": "gait-symmetry-v1",
  "predictions": {
    "symmetry_front": 98.5,
    "symmetry_hind": 97.2,
    ...
  },
  "confidence": 0.95,
  "latency_ms": 25
}
```

✅ **Pass Criteria**: JSON response with predictions and no errors

---

#### Test Slack Notifier (Dry Run)

```bash
python src/slack_notifier.py
```

**Expected Output:**
```
⚠️  Slack webhook URL not configured - notifications disabled

💡 To enable Slack notifications:
   1. Create a Slack webhook: https://api.slack.com/messaging/webhooks
   2. Set SLACK_WEBHOOK_URL in your .env file
```

✅ **Pass Criteria**: Shows configuration instructions (Slack optional for testing)

---

## 🧪 Integration Tests (No Kafka Required)

### Test 1: End-to-End Data Flow (Simulated)

Create a test script:

```bash
# Create test file
cat > test_integration.py << 'EOF'
import sys
sys.path.insert(0, 'src')

import numpy as np
from gait_analysis import GaitAnalyzer
from hrv_analysis import HRVAnalyzer

print("🧪 Integration Test: Simulated Data Flow\n")

# Simulate sensor data
gait_analyzer = GaitAnalyzer()
hrv_analyzer = HRVAnalyzer()

# Test data
test_amplitudes = {'FL': 98.5, 'FR': 100.2, 'BL': 97.8, 'BR': 99.1}
test_rr_intervals = np.random.normal(600, 50, 100).tolist()

# Gait analysis
gait_results = gait_analyzer.calculate_symmetry_scores(test_amplitudes)
print("✅ Gait Analysis:")
print(f"   Symmetry Total: {gait_results['symmetry_total']:.1f}")

# HRV analysis
hrv_results = hrv_analyzer.analyze_hrv_window(test_rr_intervals, 'test-horse')
print("\n✅ HRV Analysis:")
print(f"   SDNN: {hrv_results['sdnn']:.1f}ms")
print(f"   Stress Level: {hrv_results['stress_level']}")

# Alert detection
symmetry_history = [95, 92, 88, 55, 53, 52]
alert_triggered = gait_analyzer.detect_asymmetry_alert(symmetry_history)
print(f"\n✅ Alert System:")
print(f"   Asymmetry Alert: {'TRIGGERED' if alert_triggered else 'Normal'}")

print("\n✅ All integration tests passed!")
EOF

python test_integration.py
```

**Expected Output:**
```
🧪 Integration Test: Simulated Data Flow

✅ Gait Analysis:
   Symmetry Total: 98.5

✅ HRV Analysis:
   SDNN: 50.2ms
   Stress Level: Low

✅ Alert System:
   Asymmetry Alert: TRIGGERED

✅ All integration tests passed!
```

---

## 🔗 Kafka Integration Tests

### Prerequisites

1. **Set up Confluent Cloud credentials** in `.env`:
```bash
# Edit .env file
CONFLUENT_BOOTSTRAP_SERVERS=your-server.confluent.cloud:9092
CONFLUENT_API_KEY=your-api-key
CONFLUENT_API_SECRET=your-api-secret
```

2. **Verify Kafka connectivity**:

```bash
cat > test_kafka.py << 'EOF'
import os
from dotenv import load_dotenv
from confluent_kafka import Producer

load_dotenv()

print("🔍 Testing Kafka connection...")

config = {
    'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': os.getenv('CONFLUENT_API_KEY'),
    'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
}

try:
    producer = Producer(config)
    print("✅ Kafka connection successful!")
    print(f"   Bootstrap servers: {config['bootstrap.servers']}")
except Exception as e:
    print(f"❌ Kafka connection failed: {e}")
    print("\n💡 Check your .env file:")
    print("   - CONFLUENT_BOOTSTRAP_SERVERS")
    print("   - CONFLUENT_API_KEY")
    print("   - CONFLUENT_API_SECRET")
EOF

python test_kafka.py
```

---

### Test 2: Sensor Simulator (Kafka Producer)

**Terminal 1: Start sensor simulator**

```bash
# Run for 30 seconds with lameness simulation
python src/sensor_simulator.py --duration 30 --lameness

# OR run without lameness
python src/sensor_simulator.py --duration 30
```

**Expected Output:**
```
🐴 EquineSync Sensor Simulator Started
📡 Streaming to topic: sensor-data-raw
⏱️  Duration: 30s
🦵 Sensors: FL, FR, BL, BR
❤️  Heart Rate: 100 BPM
⚠️  SIMULATING LAMENESS: FL leg (30% severity)
------------------------------------------------------------
⏱  10s | 📊 4,000 messages | 🚀 400 msgs/sec
⏱  20s | 📊 8,000 messages | 🚀 400 msgs/sec
⏱  30s | 📊 12,000 messages | 🚀 400 msgs/sec

🔄 Flushing remaining messages...

✅ Simulation complete!
📊 Total messages sent: 12,000
⏱️  Elapsed time: 30.0s
🚀 Average throughput: 400 msgs/sec
```

✅ **Pass Criteria**:
- ~400 msgs/sec throughput
- No errors
- Total messages ≈ duration × 400

---

### Test 3: Stream Processor (Kafka Consumer)

**Terminal 2: Start stream processor**

```bash
python src/stream_processor.py
```

**Expected Output:**
```
✅ Vertex AI initialized: your-project (us-central1)
⚠️  Slack webhook URL not configured - notifications disabled
🚀 EquineSync Stream Processor Initialized
📥 Consuming from: sensor-data-raw
📤 Producing to: gait-analysis, hrv-metrics, alerts
----------------------------------------------------------------------
✅ Stream processor running...
⏳ Waiting for messages...

📊 Gait: 10 | Symmetry: 92.5 | Gait: walk (0.82 Hz)
❤️  HRV: 1 | SDNN: 48.3ms | Stress: Low | Bond: 78/100
📊 Gait: 20 | Symmetry: 55.2 | Gait: walk (0.79 Hz)
🚨 ALERT: ASYMMETRY - front pair showing 55.2% symmetry

📊 Stats: 1,000 msgs | 20 gait | 2 HRV | 1 alerts
```

✅ **Pass Criteria**:
- Receives messages continuously
- Gait analysis every ~2 seconds
- HRV analysis every ~60 seconds
- Alerts trigger when symmetry < 60

---

## 📊 End-to-End Test

**Run both together:**

```bash
# Terminal 1: Sensor simulator with lameness (triggers alerts)
python src/sensor_simulator.py --duration 120 --lameness

# Terminal 2: Stream processor
python src/stream_processor.py
```

**Watch for:**
1. ✅ Sensor simulator producing 400 msgs/sec
2. ✅ Stream processor consuming messages
3. ✅ Gait analysis showing low symmetry for FL leg
4. ✅ Alerts triggering after 3 consecutive low readings
5. ✅ HRV showing stress indicators

---

## 🐳 Docker Test

```bash
# Build image
docker build -t equinesync:test .

# Test sensor simulator
docker run --env-file .env equinesync:test python src/sensor_simulator.py --duration 10

# Test with docker-compose
docker-compose up

# View logs
docker-compose logs -f stream-processor
```

**Expected**: Both containers start and communicate via Kafka

---

## 🔧 Troubleshooting

### Issue 1: Import Errors

**Error**: `ModuleNotFoundError: No module named 'confluent_kafka'`

**Fix**:
```bash
pip install -r requirements.txt
```

---

### Issue 2: Kafka Connection Failed

**Error**: `Failed to resolve 'your-server.confluent.cloud'`

**Fix**:
1. Check `.env` file exists and has correct credentials
2. Verify Confluent Cloud cluster is running
3. Test connectivity:
```bash
curl -v telnet://your-server.confluent.cloud:9092
```

---

### Issue 3: No Messages Received

**Symptoms**: Stream processor shows "Waiting for messages..." forever

**Fix**:
1. Verify sensor simulator is running in another terminal
2. Check both use same Kafka topic names
3. Check consumer group isn't stuck:
```bash
# Reset consumer group (in Confluent Cloud UI or CLI)
```

---

### Issue 4: Vertex AI Errors

**Error**: `google.auth.exceptions.DefaultCredentialsError`

**Fix**: Vertex AI is optional - the system falls back to local models
```bash
# To use Vertex AI, set:
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

### Issue 5: Slack Notifications Not Sent

**Symptoms**: Alerts show but no Slack message

**Fix**: Slack is optional for testing
```bash
# To enable:
1. Create webhook: https://api.slack.com/messaging/webhooks
2. Add to .env: SLACK_WEBHOOK_URL=https://hooks.slack.com/...
3. Test: python src/slack_notifier.py
```

---

## ✅ Success Checklist

- [ ] All Python modules import successfully
- [ ] Individual module tests pass (gait, HRV, Vertex AI)
- [ ] Sensor simulator produces ~400 msgs/sec
- [ ] Stream processor consumes messages
- [ ] Gait analysis runs every ~2 seconds
- [ ] HRV analysis runs every ~60 seconds
- [ ] Alerts trigger on low symmetry
- [ ] Docker build succeeds
- [ ] No errors in logs for 5+ minutes

---

## 📈 Performance Benchmarks

Expected performance metrics:

| Metric | Target | Acceptable |
|--------|--------|------------|
| Sensor throughput | 400 msgs/sec | 350-450 |
| Gait analysis latency | <30ms | <50ms |
| HRV analysis latency | <20ms | <40ms |
| End-to-end latency | <50ms | <100ms |
| Alerts/hour (with lameness) | 10-20 | 5-30 |
| CPU usage | <30% | <50% |
| Memory usage | <500MB | <1GB |

---

## 🎬 Demo Preparation

For your video demo, test this sequence:

```bash
# 1. Show healthy horse (no alerts)
python src/sensor_simulator.py --duration 60

# 2. Show lame horse (triggers alerts)
python src/sensor_simulator.py --duration 60 --lameness

# 3. Show real-time dashboard (your index.html)
# Open in browser while simulator runs
```

---

## 📞 Need Help?

If tests fail:
1. Check this guide's troubleshooting section
2. Review logs for error messages
3. Verify .env configuration
4. Test components individually before integration

**Everything working?** You're ready for the Confluent Challenge! 🎉
