# EquineSync: Early Detection for Healthier Horses

## Inspiration

This project was born from personal heartbreak. I purchased a horse that appeared healthy during the sale, but within weeks, I discovered he was lame. The lameness wasn't visible to the untrained eye during a brief viewing—it only became apparent through careful observation over time.

**I couldn't return him. I couldn't resell him. But I couldn't abandon him either.**

Caring for a lame horse is expensive and emotionally draining. Veterinary bills, special shoeing, supplements, and rehabilitation add up quickly. But more than the cost, I felt deceived—and I knew I wasn't alone. Thousands of horses are sold each year with undetected lameness, leading to:

- Financial hardship for unsuspecting buyers
- Horses being abandoned or sent to slaughter when owners can't cope
- Preventable suffering that early detection could have avoided

**I decided to build a solution.** If I win any prize money from this hackathon, every penny will go toward giving my lame horse a better life—and developing this technology to help other horses get diagnosed early, before it's too late.

---

## What It Does

**EquineSync** is an AI-powered analytics platform that monitors four-legged animals (primarily horses) for early signs of lameness and health issues through:

1. **Gait Symmetry Analysis** - Detecting subtle asymmetries across all four legs with real-time visualization
2. **Heart Rate Variability (HRV) Monitoring** - Assessing stress and cardiac health using ESC/NASPE standards
3. **Individual Leg Health Scoring** - 0-100 health scores for each leg with predictive deductions
4. **Horse-Rider Emotional Bond Tracking** - Monitoring emotional synchronization and stress impact on partnership
5. **Real-Time Leg Detection** - Auto-identifying which sensor is on which leg
6. **Session Result Reports** - Period-by-period behavioral analysis with downloadable comprehensive reports
7. **Alert System** - Flagging potential issues before they become serious
8. **Live Event Logging** - Session progress tracking with timestamped milestone events

### Advanced Dashboard Features

The EquineSync real-time monitoring dashboard provides:

- **Live Visualization**: Real-time charts using Chart.js displaying:
  - Symmetry evolution (overall, front, hind) over session duration
  - 4-leg amplitude tracking with color-coded lines
  - HRV trend analysis (SDNN over time)
  - Horse-rider bond score evolution

- **Session Progress Log**: Live event feed showing:
  - System initialization and milestone events
  - Alert triggers with timestamps
  - Health score changes and degradation warnings
  - Critical events (e.g., lameness onset detection)

- **Period-by-Period Analysis**: Automatic breakdown into 30-second periods showing:
  - Average symmetry and bond scores per period
  - Behavioral observations (baseline, onset, compensation)
  - Color-coded status indicators (green/orange/red)
  - Comparative analysis across time periods

- **Downloadable Reports**: Comprehensive text-based clinical reports including:
  - Minute-by-minute behavioral analysis
  - Statistical summaries (min/max/average metrics)
  - Alert history and timeline
  - Clinical recommendations with urgency levels
  - Veterinary action items and follow-up protocols

---

## How I Built It

### Architecture

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│ IMU Sensors  │───▶│ Confluent Cloud │───▶│  Vertex AI   │───▶│   Tableau   │
│  (4 legs)    │    │  Kafka Streams  │    │  ML Models   │    │  Dashboard  │
│ 100Hz stream │    │                 │    │              │    │             │
├──────────────┤    │  Topics:        │    ├──────────────┤    ├─────────────┤
│ Heart Rate   │───▶│  - sensor-raw   │───▶│ Gait Analysis│───▶│   Slack     │
│   Monitor    │    │  - gait-data    │    │ HRV Analysis │    │   Alerts    │
│              │    │  - hrv-metrics  │    │ Anomaly Det. │    │             │
└──────────────┘    │  - alerts       │    └──────────────┘    └─────────────┘
                    └─────────────────┘

Real-time streaming pipeline: Sensors → Kafka → AI → Insights
```

**Key Components:**
- **Confluent Cloud**: Apache Kafka for real-time data streaming (4 sensors × 100Hz = 400 data points/sec)
- **Vertex AI**: Google Cloud ML for streaming inference on gait symmetry and HRV patterns
- **Tableau Cloud**: Real-time visualization of health metrics and trends
- **Slack Integration**: Instant alerts when lameness or stress detected

---

### Real-Time Streaming with Confluent

**Why Confluent + Google Cloud?**

Traditional batch processing would miss critical moments—lameness develops over seconds, not hours. By streaming sensor data through Confluent Kafka and processing with Vertex AI in real-time, we detect abnormalities **within milliseconds** of occurrence.

**Kafka Topics Architecture:**

1. **`sensor-data-raw`** (400 msgs/sec)
   - Raw IMU readings from 4 legs (accelerometer + gyroscope)
   - Heart rate monitor R-R intervals
   - Timestamped, partitioned by sensor ID

2. **`gait-analysis`** (processed stream)
   - Stride frequency, symmetry scores, leg health metrics
   - Computed in real-time via Vertex AI inference
   - Triggers alerts when thresholds breached

3. **`hrv-metrics`** (1 msg/sec)
   - SDNN, RMSSD, pNN50 calculations
   - Stress level indicators
   - Emotional state tracking (horse-rider bond)

4. **`alerts`** (event-driven)
   - Asymmetry alerts (symmetry < 60 for >3 readings)
   - Impact alerts (peak acceleration > 2.5× baseline)
   - HRV alerts (stress indicators in danger zone)

**Stream Processing Flow:**
```python
# Pseudo-code for Confluent + Vertex AI integration
kafka_consumer = ConfluentConsumer(['sensor-data-raw'])
vertex_ai_model = VertexAIModel('gait-analysis-v1')

for message in kafka_consumer:
    sensor_data = parse_imu_data(message)
    prediction = vertex_ai_model.predict(sensor_data)  # Real-time inference

    if prediction['symmetry_score'] < 60:
        kafka_producer.send('alerts', create_alert(prediction))
        slack.notify(f"⚠️ Lameness detected: {prediction['affected_leg']}")
```

**Performance Benefits:**
- **Latency**: <50ms from sensor reading to alert
- **Throughput**: Handles 400 data points/sec with room to scale
- **Reliability**: Kafka replication ensures no data loss
- **Scalability**: Can monitor entire stables (100+ horses) simultaneously

---

### Mathematical Foundation

#### 1. Heart Rate Variability (HRV) Analysis

Raw R-R intervals are filtered to remove artifacts:

$$300\text{ms} \leq RR_i \leq 2000\text{ms}$$

$$|RR_i - \text{median}(RR)| \leq 0.20 \times \text{median}(RR)$$

**Key HRV Metrics:**

**SDNN** (Standard Deviation of NN intervals) - Overall HRV:
$$SDNN = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N}(RR_i - \overline{RR})^2}$$

**RMSSD** (Root Mean Square of Successive Differences) - Parasympathetic activity:
$$RMSSD = \sqrt{\frac{1}{N-1}\sum_{i=1}^{N-1}(RR_{i+1} - RR_i)^2}$$

**pNN50** (Percentage of successive intervals differing by >50ms):
$$pNN50 = \frac{\text{count}(|RR_{i+1} - RR_i| > 50\text{ms})}{N-1} \times 100\%$$

| Metric | Good | Warning | Alert |
|--------|------|---------|-------|
| SDNN | >50ms | 30-50ms | <30ms |
| RMSSD | >40ms | 20-40ms | <20ms |
| pNN50 | >3% | 1-3% | <1% |

#### 2. Gait Classification

IMU sensors scaled at $\pm16g$ acceleration and $\pm2000°/s$ gyroscope measure stride patterns:

| Gait | Stride Frequency | Acceleration Pattern |
|------|------------------|---------------------|
| Stand | <0.3 Hz | Minimal |
| Walk | 0.3-1.0 Hz | Regular, low amplitude |
| Trot | 1.0-1.8 Hz | Two-beat diagonal |
| Canter | 1.8-2.5 Hz | Three-beat asymmetric |
| Gallop | >2.5 Hz | Four-beat high amplitude |

#### 3. Symmetry Analysis

For each leg pair, symmetry is calculated:

**Front Pair Symmetry:**
$$S_{front} = 100 - |A_{FL} - A_{FR}| \times k_{front}$$

**Hind Pair Symmetry:**
$$S_{hind} = 100 - |A_{BL} - A_{BR}| \times k_{hind}$$

**Diagonal Symmetry:**
$$S_{diag} = 100 - \frac{|A_{FL} - A_{BR}| + |A_{FR} - A_{BL}|}{2} \times k_{diag}$$

**Overall Symmetry Score:**
$$S_{total} = w_1 \cdot S_{front} + w_2 \cdot S_{hind} + w_3 \cdot S_{diag}$$

Where $w_1 = 0.35$, $w_2 = 0.35$, $w_3 = 0.30$

| Score | Status | Action |
|-------|--------|--------|
| $\geq 80$ | Good | Continue monitoring |
| $60-79$ | Warning | Increase observation |
| $< 60$ | Alert | Veterinary consultation recommended |

#### 4. Automatic Leg Detection

The system auto-identifies which sensor is on which leg using a calibration walk:

**Motion Activation Threshold:**
$$E_{motion} = \int_{t}^{t+2s} (a_x^2 + a_y^2 + a_z^2) \, dt > 5.0 \, g^2 \cdot s$$

**Front/Hind Classification** (via acceleration axis ratio):
$$R_{FH} = \frac{\sigma(a_{vertical})}{\sigma(a_{horizontal})}$$

Front legs: $R_{FH} > 1.2$ | Hind legs: $R_{FH} < 0.8$

**Left/Right Classification** (via cross-correlation):
$$\rho_{LR} = \frac{\text{cov}(a_{lateral,1}, a_{lateral,2})}{\sigma_1 \cdot \sigma_2}$$

**Confidence Score:**
$$C_{total} = 0.40 \cdot C_{freq} + 0.30 \cdot C_{FH} + 0.20 \cdot C_{LR} + 0.10 \cdot C_{diag}$$

#### 5. Leg Health Scoring

Each leg receives a health score based on:

$$Score_{leg} = 100 - D_{variability} - D_{frequency} - D_{deviation}$$

Where deductions are calculated from:
- Stride variability compared to baseline
- Frequency anomalies
- Deviation from healthy movement patterns

#### 6. Horse-Rider Emotional Bond Analysis

The horse-rider bond score quantifies the emotional connection and partnership quality:

$$Bond_{score} = Bond_{base} + \alpha \cdot (SDNN - SDNN_{ref}) - \beta \cdot t_{stress}$$

Where:
- $Bond_{base}$: Initial bond score (typically 85-95 for established partnerships)
- $\alpha = 0.3$: HRV adjustment factor
- $SDNN_{ref} = 40$ ms: Reference SDNN value
- $\beta = 0.4$: Stress duration penalty factor (points per second)
- $t_{stress}$: Time elapsed since stress onset (e.g., lameness detection)

The bond score is clamped to $[0, 100]$ and interpreted as:

| Score Range | Interpretation |
|-------------|----------------|
| 80-100 | Excellent Partnership |
| 65-79 | Strong Connection |
| 50-64 | Moderate Bond |
| < 50 | Stress Affecting Bond |

**Clinical Significance:** Bond degradation indicates that pain or discomfort is affecting the horse's responsiveness to rider cues, impacting training effectiveness and partnership quality.

#### 7. Alert Generation

Alerts trigger when:

**Asymmetry Alert:**
$$|S_{pair}| < 60 \text{ for } > 3 \text{ consecutive readings}$$

**Impact Alert:**
$$a_{peak} > 2.5 \times a_{baseline}$$

**Irregularity Alert:**
$$\sigma_{stride} > 1.5 \times \sigma_{normal}$$

---

## Challenges I Faced

### 1. Signal Noise
Real-world sensor data is messy. Horse movement creates vibrations, and sensors can shift during exercise. I implemented Kalman filtering for label stability:
$$\hat{x}_k = \hat{x}_{k-1} + K_k(z_k - \hat{x}_{k-1})$$

### 2. Individual Variation
Every horse moves differently. A thoroughbred's gait differs from a draft horse's. The system needed adaptive baselines that learn each horse's "normal" over time.

### 3. Balancing Sensitivity
Too sensitive = false alarms that cause unnecessary worry
Too lenient = missed detections that defeat the purpose

I tuned thresholds based on veterinary literature and the ESC/NASPE HRV standards.

### 4. Making It Accessible
Complex biomechanical data needs to be understandable for trainers without medical degrees. Tableau's visualization capabilities were essential for translating raw numbers into actionable insights.

---

## What I Learned

- **Real-time data streaming** - Building scalable event-driven architectures with Confluent Kafka
- **Google Cloud AI** - Deploying Vertex AI models for streaming ML inference at scale
- **Equine biomechanics** - How horses distribute weight, compensate for pain, and how subtle lameness manifests
- **Signal processing** - FFT for frequency analysis, cross-correlation for leg pairing, Kalman filtering for stability
- **HRV science** - The parasympathetic nervous system's role in stress detection and emotional bond assessment
- **Stream processing patterns** - Handling 400+ messages/sec with low latency and high reliability
- **Tableau Developer Platform** - APIs, embedding, and real-time data integration
- **Data visualization** - Implementing real-time Chart.js visualizations for biomechanical data
- **Authentic research data integration** - Processing and streaming the "Horsing Around" dataset (4TU ResearchData, CC0 license) containing genuine equine IMU data
- **Clinical report generation** - Creating actionable, veterinary-grade reports with period-by-period analysis

---

## What's Next

If given more time, I would:

1. **Add computer vision** - Camera-based gait analysis to complement IMU sensors
2. **Build mobile app** - On-field assessments during horse sales
3. **Create marketplace integration** - Verified health certificates for horse sales
4. **Expand to other animals** - Dogs, livestock, zoo animals

---

## My Promise

**If this project wins any prize money, 100% will be dedicated to:**

1. Providing the best possible care for my lame horse
2. Developing this technology further to help other horses
3. Working with rescue organizations to screen horses before adoption

No horse should suffer because their lameness wasn't caught early. No buyer should face the heartbreak I experienced. Technology can help—and that's what EquineSync is all about.

---

## References

- Task Force of ESC and NASPE. "Heart rate variability: standards of measurement, physiological interpretation, and clinical use." *Circulation* 93.5 (1996): 1043-1065.
- Equine heart rate research literature
- Gait biomechanics studies

---

## Built With

**Data Streaming & Processing:**
- Confluent Cloud (Apache Kafka)
- Stream processing at 400 msgs/sec
- Flask API server for real-time data endpoints

**AI & Machine Learning:**
- Google Vertex AI / Gemini
- Python (NumPy, SciPy, Scikit-learn, Pandas)
- Real-time ML inference

**Cloud Platform:**
- Google Cloud Platform
- Tableau Cloud
- Cloud Run, Cloud Storage, BigQuery

**Frontend & Visualization:**
- React.js (Main dashboard UI)
- Chart.js (Real-time data visualization)
- HTML5/CSS3 (Advanced monitoring interface)
- Vite (Build tooling and optimization)

**Data Sources:**
- Horsing Around Dataset (4TU ResearchData, CC0 License)
- 10.96 GB authentic equine IMU data
- 148 CSV files with 100Hz sampling rate

**Hardware:**
- IMU Sensors (±16g accelerometer, ±2000°/s gyroscope)
- Heart Rate Monitors (R-R interval detection)

**Integration:**
- Slack API (alerts)
- Confluent Connectors (GCP integration)
- REST APIs

---

*Built with Confluent Kafka, Vertex AI, Tableau Cloud, React, Chart.js, Python, authentic research data, and a deep love for horses.*
