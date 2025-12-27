"""
EquineSync Stream Processor - Kafka Consumer
Processes real-time sensor streams with Vertex AI inference
Produces gait analysis, HRV metrics, and alerts
"""

import os
import json
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Deque
from dotenv import load_dotenv
from confluent_kafka import Consumer, Producer, KafkaError
import numpy as np

# Import local modules
from gait_analysis import GaitAnalyzer
from hrv_analysis import HRVAnalyzer
from vertex_ai_client import VertexAIClient
from slack_notifier import SlackNotifier

load_dotenv()


class StreamProcessor:
    """Real-time stream processor for equine health monitoring"""

    def __init__(self):
        """Initialize stream processor"""
        self.consumer = self._create_consumer()
        self.producer = self._create_producer()

        # Topics
        self.topic_sensor = os.getenv('KAFKA_TOPIC_SENSOR_RAW', 'sensor-data-raw')
        self.topic_gait = os.getenv('KAFKA_TOPIC_GAIT_ANALYSIS', 'gait-analysis')
        self.topic_hrv = os.getenv('KAFKA_TOPIC_HRV_METRICS', 'hrv-metrics')
        self.topic_alerts = os.getenv('KAFKA_TOPIC_ALERTS', 'alerts')

        # Analyzers
        self.gait_analyzer = GaitAnalyzer()
        self.hrv_analyzer = HRVAnalyzer()
        self.vertex_ai = VertexAIClient()
        self.slack = SlackNotifier()

        # Windowing buffers (2-second windows for gait, 60-second for HRV)
        self.sensor_windows: Dict[str, Deque[Dict]] = defaultdict(lambda: deque(maxlen=200))  # 2s @ 100Hz
        self.rr_intervals: Deque[float] = deque(maxlen=100)  # ~60s of R-R intervals

        # Recent symmetry scores for alert detection
        self.recent_symmetry: Deque[float] = deque(maxlen=10)

        # Stats
        self.stats = {
            'messages_processed': 0,
            'gait_analyses': 0,
            'hrv_analyses': 0,
            'alerts_sent': 0,
            'errors': 0
        }

        print("🚀 EquineSync Stream Processor Initialized")
        print(f"📥 Consuming from: {self.topic_sensor}")
        print(f"📤 Producing to: {self.topic_gait}, {self.topic_hrv}, {self.topic_alerts}")
        print("-" * 70)

    def _create_consumer(self) -> Consumer:
        """Create Kafka consumer"""
        config = {
            'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': os.getenv('CONFLUENT_API_KEY'),
            'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
            'group.id': 'equinesync-stream-processor',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True
        }
        return Consumer(config)

    def _create_producer(self) -> Producer:
        """Create Kafka producer"""
        config = {
            'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': os.getenv('CONFLUENT_API_KEY'),
            'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
            'client.id': 'equinesync-stream-processor-producer'
        }
        return Producer(config)

    def process_sensor_message(self, message: Dict):
        """Process incoming sensor data message"""
        sensor_id = message['sensor_id']
        timestamp = message['timestamp']

        # Add to windowing buffer
        self.sensor_windows[sensor_id].append(message)

        # Collect R-R intervals for HRV
        if message.get('hr_rr_interval') is not None:
            self.rr_intervals.append(message['hr_rr_interval'])

        # Check if we have full 2-second window for all sensors
        if all(len(self.sensor_windows[sid]) >= 200 for sid in ['FL', 'FR', 'BL', 'BR']):
            self.analyze_gait_window()

        # Check if we have enough R-R intervals for HRV analysis (60 beats)
        if len(self.rr_intervals) >= 60:
            self.analyze_hrv_window()

    def analyze_gait_window(self):
        """Analyze 2-second window of gait data"""
        try:
            # Extract sensor data for all legs
            sensor_data = {
                sensor_id: list(window)
                for sensor_id, window in self.sensor_windows.items()
            }

            # Perform gait analysis
            gait_results = self.gait_analyzer.analyze_gait_window(sensor_data)

            # Add metadata
            gait_results['horse_id'] = 'horse-001'  # Would come from message metadata
            gait_results['timestamp'] = int(time.time() * 1000)

            # Produce to gait-analysis topic
            self.producer.produce(
                topic=self.topic_gait,
                key='horse-001',
                value=json.dumps(gait_results)
            )

            # Check for asymmetry alerts
            self.recent_symmetry.append(gait_results['symmetry_total'])
            if self.gait_analyzer.detect_asymmetry_alert(list(self.recent_symmetry)):
                self.generate_asymmetry_alert(gait_results)

            self.stats['gait_analyses'] += 1

            # Print periodic status
            if self.stats['gait_analyses'] % 10 == 0:
                print(f"📊 Gait: {self.stats['gait_analyses']} | "
                      f"Symmetry: {gait_results['symmetry_total']:.1f} | "
                      f"Gait: {gait_results['gait_type']} ({gait_results['stride_frequency']:.2f} Hz)")

        except Exception as e:
            print(f"❌ Gait analysis error: {e}")
            self.stats['errors'] += 1

    def analyze_hrv_window(self):
        """Analyze 60-second window of HRV data"""
        try:
            # Get R-R intervals
            rr_list = list(self.rr_intervals)

            # Perform HRV analysis
            hrv_results = self.hrv_analyzer.analyze_hrv_window(rr_list, 'horse-001')

            # Add timestamp
            hrv_results['timestamp'] = int(time.time() * 1000)

            # Produce to hrv-metrics topic
            self.producer.produce(
                topic=self.topic_hrv,
                key='horse-001',
                value=json.dumps(hrv_results)
            )

            # Check for HRV critical alerts
            if hrv_results.get('stress_level') == 'Critical':
                self.generate_hrv_alert(hrv_results)

            self.stats['hrv_analyses'] += 1

            # Print status
            print(f"❤️  HRV: {self.stats['hrv_analyses']} | "
                  f"SDNN: {hrv_results.get('sdnn', 0):.1f}ms | "
                  f"Stress: {hrv_results.get('stress_level', 'Unknown')} | "
                  f"Bond: {hrv_results.get('rider_bond_score', 0):.0f}/100")

            # Clear R-R buffer after analysis
            self.rr_intervals.clear()

        except Exception as e:
            print(f"❌ HRV analysis error: {e}")
            self.stats['errors'] += 1

    def generate_asymmetry_alert(self, gait_results: Dict):
        """Generate and send asymmetry alert"""
        # Find most affected leg pair
        scores = {
            'front': gait_results['symmetry_front'],
            'hind': gait_results['symmetry_hind'],
            'diagonal': gait_results['symmetry_diagonal']
        }
        affected_pair = min(scores, key=scores.get)
        lowest_score = scores[affected_pair]

        # Create alert
        alert = {
            'alert_id': str(uuid.uuid4()),
            'horse_id': gait_results['horse_id'],
            'timestamp': gait_results['timestamp'],
            'alert_type': 'ASYMMETRY',
            'severity': 'CRITICAL' if lowest_score < 50 else 'WARNING',
            'affected_leg': affected_pair,
            'metric_value': lowest_score,
            'threshold': 60.0,
            'message': f'{affected_pair} pair showing {lowest_score:.1f}% symmetry',
            'recommendation': 'Reduce training intensity. Schedule veterinary examination within 48 hours.'
        }

        # Send to alerts topic
        self.producer.produce(
            topic=self.topic_alerts,
            key=alert['horse_id'],
            value=json.dumps(alert)
        )

        # Send Slack notification
        self.slack.send_alert(alert)

        self.stats['alerts_sent'] += 1
        print(f"🚨 ALERT: {alert['alert_type']} - {alert['message']}")

    def generate_hrv_alert(self, hrv_results: Dict):
        """Generate and send HRV critical alert"""
        alert = {
            'alert_id': str(uuid.uuid4()),
            'horse_id': hrv_results['horse_id'],
            'timestamp': hrv_results['timestamp'],
            'alert_type': 'HRV_CRITICAL',
            'severity': 'CRITICAL',
            'affected_leg': None,
            'metric_value': hrv_results.get('sdnn', 0),
            'threshold': 30.0,
            'message': f"SDNN={hrv_results.get('sdnn', 0):.1f}ms indicates high stress",
            'recommendation': 'Immediate rest required. Assess for pain, anxiety, or environmental stressors.'
        }

        # Send to alerts topic
        self.producer.produce(
            topic=self.topic_alerts,
            key=alert['horse_id'],
            value=json.dumps(alert)
        )

        # Send Slack notification
        self.slack.send_alert(alert)

        self.stats['alerts_sent'] += 1
        print(f"🚨 ALERT: {alert['alert_type']} - {alert['message']}")

    def run(self):
        """Main processing loop"""
        # Subscribe to sensor data topic
        self.consumer.subscribe([self.topic_sensor])

        print("✅ Stream processor running...")
        print("⏳ Waiting for messages...\n")

        try:
            while True:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"❌ Consumer error: {msg.error()}")
                        break

                # Parse message
                try:
                    message = json.loads(msg.value().decode('utf-8'))
                    self.process_sensor_message(message)
                    self.stats['messages_processed'] += 1

                    # Print stats every 1000 messages
                    if self.stats['messages_processed'] % 1000 == 0:
                        print(f"\n📊 Stats: {self.stats['messages_processed']:,} msgs | "
                              f"{self.stats['gait_analyses']} gait | "
                              f"{self.stats['hrv_analyses']} HRV | "
                              f"{self.stats['alerts_sent']} alerts\n")

                except Exception as e:
                    print(f"❌ Message processing error: {e}")
                    self.stats['errors'] += 1

                # Flush producer periodically
                self.producer.poll(0)

        except KeyboardInterrupt:
            print("\n⏸️  Stream processor interrupted by user")

        finally:
            # Cleanup
            print("\n🔄 Shutting down...")
            self.producer.flush()
            self.consumer.close()

            print(f"\n✅ Stream processor stopped")
            print(f"📊 Final stats:")
            for key, value in self.stats.items():
                print(f"   {key}: {value:,}")


def main():
    processor = StreamProcessor()
    processor.run()


if __name__ == "__main__":
    main()
