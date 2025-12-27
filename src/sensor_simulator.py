"""
EquineSync Sensor Simulator - Kafka Producer
Simulates 4 IMU sensors (one per leg) + heart rate monitor streaming to Confluent Cloud
"""

import os
import time
import json
import random
import math
import argparse
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer

load_dotenv()


class SensorSimulator:
    """Simulates IMU sensors on horse legs + HRV monitor"""

    SENSOR_IDS = ["FL", "FR", "BL", "BR"]  # Front-Left, Front-Right, Back-Left, Back-Right
    SAMPLE_RATE_HZ = 100  # 100 Hz sampling

    def __init__(self):
        self.config = self._load_config()
        self.producer = self._create_producer()
        self.topic = os.getenv("KAFKA_TOPIC_SENSOR_RAW", "sensor-data-raw")

        # Baseline gait parameters (healthy horse, walking)
        self.gait_freq_hz = 0.8  # Walk gait ~0.8 Hz
        self.baseline_accel_g = 1.2
        self.baseline_rr_interval_ms = 600  # 100 BPM

        # Lameness simulation (set to True to simulate injured leg)
        self.simulate_lameness = False
        self.lame_leg = "FL"
        self.lameness_severity = 0.3  # 30% amplitude reduction

    def _load_config(self) -> Dict:
        """Load Confluent Cloud configuration"""
        return {
            'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': os.getenv('CONFLUENT_API_KEY'),
            'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
            'client.id': 'equinesync-sensor-simulator'
        }

    def _create_producer(self) -> Producer:
        """Create Kafka producer"""
        return Producer(self.config)

    def generate_imu_data(self, sensor_id: str, t: float) -> Dict:
        """Generate realistic IMU sensor data with gait patterns"""

        # Gait cycle (sinusoidal pattern)
        phase = 2 * math.pi * self.gait_freq_hz * t

        # Front vs hind legs have different movement patterns
        is_front = sensor_id.startswith('F')
        phase_offset = 0 if sensor_id.endswith('L') else math.pi  # Left/right offset

        # Vertical acceleration (dominant in gait)
        accel_z_base = self.baseline_accel_g * math.sin(phase + phase_offset)
        accel_z = accel_z_base + random.gauss(0, 0.1)

        # Apply lameness (reduced amplitude on affected leg)
        if self.simulate_lameness and sensor_id == self.lame_leg:
            accel_z *= (1 - self.lameness_severity)

        # Lateral and forward acceleration (smaller components)
        accel_x = 0.3 * math.cos(phase + phase_offset) + random.gauss(0, 0.05)
        accel_y = 0.2 * math.sin(2 * phase) + random.gauss(0, 0.05)

        # Gyroscope (rotation during stride)
        gyro_scale = 200 if is_front else 150  # Front legs rotate more
        gyro_x = gyro_scale * math.sin(phase + phase_offset) + random.gauss(0, 10)
        gyro_y = gyro_scale * 0.5 * math.cos(phase) + random.gauss(0, 10)
        gyro_z = gyro_scale * 0.3 * math.sin(phase * 2) + random.gauss(0, 10)

        return {
            'sensor_id': sensor_id,
            'timestamp': int(time.time() * 1000),  # ms
            'accel_x': round(accel_x, 3),
            'accel_y': round(accel_y, 3),
            'accel_z': round(accel_z, 3),
            'gyro_x': round(gyro_x, 2),
            'gyro_y': round(gyro_y, 2),
            'gyro_z': round(gyro_z, 2),
            'hr_rr_interval': None  # Only included in heart rate samples
        }

    def generate_hrv_data(self) -> float:
        """Generate heart rate R-R interval (ms)"""
        # Add HRV (healthy variation ~50ms SDNN)
        rr_interval = self.baseline_rr_interval_ms + random.gauss(0, 50)

        # Simulate stress (reduced HRV)
        if random.random() < 0.05:  # 5% chance of stress event
            rr_interval = self.baseline_rr_interval_ms + random.gauss(0, 15)  # Low HRV

        return round(rr_interval, 2)

    def delivery_report(self, err, msg):
        """Kafka delivery callback"""
        if err:
            print(f'❌ Delivery failed: {err}')
        else:
            pass  # Suppress success messages for cleaner output

    def run(self, duration_sec: int = 60, enable_lameness: bool = False):
        """
        Run sensor simulation

        Args:
            duration_sec: Simulation duration in seconds
            enable_lameness: Simulate lameness on front-left leg
        """
        self.simulate_lameness = enable_lameness

        print(f"🐴 EquineSync Sensor Simulator Started")
        print(f"📡 Streaming to topic: {self.topic}")
        print(f"⏱️  Duration: {duration_sec}s")
        print(f"🦵 Sensors: {', '.join(self.SENSOR_IDS)}")
        print(f"❤️  Heart Rate: {60000/self.baseline_rr_interval_ms:.0f} BPM")
        if enable_lameness:
            print(f"⚠️  SIMULATING LAMENESS: {self.lame_leg} leg ({self.lameness_severity*100:.0f}% severity)")
        print("-" * 60)

        start_time = time.time()
        sample_count = 0
        hr_sample_interval = 1.0  # 1 Hz for HRV
        last_hr_sample = 0

        try:
            while (time.time() - start_time) < duration_sec:
                t = time.time() - start_time

                # Generate IMU data for all 4 legs (100 Hz)
                for sensor_id in self.SENSOR_IDS:
                    data = self.generate_imu_data(sensor_id, t)

                    # Add HRV data at 1 Hz
                    if t - last_hr_sample >= hr_sample_interval:
                        data['hr_rr_interval'] = self.generate_hrv_data()
                        last_hr_sample = t

                    # Send to Kafka
                    self.producer.produce(
                        topic=self.topic,
                        key=sensor_id,
                        value=json.dumps(data),
                        callback=self.delivery_report
                    )

                    sample_count += 1

                # Poll for delivery reports
                self.producer.poll(0)

                # Print status every 10 seconds
                if int(t) % 10 == 0 and t > 0 and t - int(t) < 0.01:
                    msgs_per_sec = sample_count / t
                    print(f"⏱  {int(t)}s | 📊 {sample_count:,} messages | 🚀 {msgs_per_sec:.0f} msgs/sec")

                # Sleep to maintain 100 Hz rate
                time.sleep(1 / self.SAMPLE_RATE_HZ)

        except KeyboardInterrupt:
            print("\n⏸️  Simulation interrupted by user")

        finally:
            # Flush remaining messages
            print("\n🔄 Flushing remaining messages...")
            self.producer.flush()

            elapsed = time.time() - start_time
            print(f"\n✅ Simulation complete!")
            print(f"📊 Total messages sent: {sample_count:,}")
            print(f"⏱️  Elapsed time: {elapsed:.1f}s")
            print(f"🚀 Average throughput: {sample_count/elapsed:.0f} msgs/sec")


def main():
    parser = argparse.ArgumentParser(description='EquineSync Sensor Simulator')
    parser.add_argument('--duration', type=int, default=60, help='Simulation duration in seconds')
    parser.add_argument('--lameness', action='store_true', help='Simulate lameness on FL leg')
    parser.add_argument('--horse-id', type=str, default='horse-001', help='Horse identifier')

    args = parser.parse_args()

    simulator = SensorSimulator()
    simulator.run(duration_sec=args.duration, enable_lameness=args.lameness)


if __name__ == "__main__":
    main()
