"""
EquineSync Gait Analysis Module
Implements symmetry analysis, gait classification, and leg health scoring
Based on mathematical foundation from PROJECT_STORY.pdf
"""

import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from typing import Dict, List, Tuple
import json
import os


class GaitAnalyzer:
    """Analyzes horse gait patterns for symmetry and health metrics"""

    def __init__(self, config_path: str = None):
        """Initialize with alert thresholds from config"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'alert_thresholds.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.thresholds = config['gait_symmetry']
        self.gait_classes = config['gait_classification']
        self.leg_health_config = config['leg_health_scoring']

    def calculate_symmetry_scores(self, amplitudes: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate symmetry scores for leg pairs

        Equations from Section 3.2.3:
        S_front = 100 - |A_FL - A_FR| × k_front
        S_hind = 100 - |A_BL - A_BR| × k_hind
        S_diag = 100 - (|A_FL - A_BR| + |A_FR - A_BL|) / 2 × k_diag
        S_total = w1·S_front + w2·S_hind + w3·S_diag

        Args:
            amplitudes: Dict with keys 'FL', 'FR', 'BL', 'BR' (normalized %)

        Returns:
            Dict with symmetry scores
        """
        A_FL = amplitudes['FL']
        A_FR = amplitudes['FR']
        A_BL = amplitudes['BL']
        A_BR = amplitudes['BR']

        k_front = self.thresholds['scaling_factors']['k_front']
        k_hind = self.thresholds['scaling_factors']['k_hind']
        k_diag = self.thresholds['scaling_factors']['k_diag']

        # Front pair symmetry
        S_front = 100 - abs(A_FL - A_FR) * k_front

        # Hind pair symmetry
        S_hind = 100 - abs(A_BL - A_BR) * k_hind

        # Diagonal symmetry
        S_diag = 100 - ((abs(A_FL - A_BR) + abs(A_FR - A_BL)) / 2) * k_diag

        # Overall symmetry (weighted)
        w1 = self.thresholds['weights']['w_front']
        w2 = self.thresholds['weights']['w_hind']
        w3 = self.thresholds['weights']['w_diag']

        S_total = w1 * S_front + w2 * S_hind + w3 * S_diag

        # Clamp scores to valid range [0, 100]
        return {
            'symmetry_front': round(max(0, min(100, S_front)), 2),
            'symmetry_hind': round(max(0, min(100, S_hind)), 2),
            'symmetry_diagonal': round(max(0, min(100, S_diag)), 2),
            'symmetry_total': round(max(0, min(100, S_total)), 2)
        }

    def extract_stride_amplitudes(self, sensor_data: Dict[str, List[Dict]]) -> Dict[str, float]:
        """
        Extract peak vertical acceleration from each leg's sensor data
        Returns normalized amplitude ratios (% of baseline)

        Args:
            sensor_data: Dict[sensor_id -> List[readings]] for 2-second window

        Returns:
            Dict[sensor_id -> normalized_amplitude_%]
        """
        amplitudes = {}
        baseline_accel = 1.2  # g (typical walk gait)

        for sensor_id, readings in sensor_data.items():
            # Extract vertical acceleration (z-axis)
            accel_z = np.array([r['accel_z'] for r in readings])

            # Find peak acceleration (use 95th percentile to avoid outliers)
            peak_accel = np.percentile(np.abs(accel_z), 95)

            # Normalize to percentage of baseline
            amplitude_ratio = (peak_accel / baseline_accel) * 100

            amplitudes[sensor_id] = round(amplitude_ratio, 2)

        return amplitudes

    def classify_gait(self, accel_data: np.ndarray, sample_rate_hz: int = 100) -> Tuple[str, float]:
        """
        Classify gait type based on stride frequency using FFT

        From Table 2:
        - Stand: <0.3 Hz
        - Walk: 0.3-1.0 Hz
        - Trot: 1.0-1.8 Hz
        - Canter: 1.8-2.5 Hz
        - Gallop: >2.5 Hz

        Args:
            accel_data: Vertical acceleration array
            sample_rate_hz: Sampling rate

        Returns:
            (gait_type, stride_frequency_hz)
        """
        # FFT to find dominant frequency
        N = len(accel_data)
        yf = fft(accel_data)
        xf = fftfreq(N, 1 / sample_rate_hz)

        # Only positive frequencies
        positive_freqs = xf[:N//2]
        magnitude = np.abs(yf[:N//2])

        # Find dominant frequency (ignore DC component)
        dominant_idx = np.argmax(magnitude[1:]) + 1
        stride_freq = positive_freqs[dominant_idx]

        # Classify gait
        for gait_name, freq_range in self.gait_classes.items():
            if freq_range['min_hz'] <= stride_freq < freq_range['max_hz']:
                return gait_name, round(stride_freq, 2)

        return 'unknown', round(stride_freq, 2)

    def calculate_leg_health_score(
        self,
        stride_variability: float,
        baseline_variability: float,
        measured_freq: float,
        expected_freq: float,
        accel_deviation: float
    ) -> Dict[str, float]:
        """
        Calculate leg health score with deductions

        From Section 3.2.5:
        Score_leg = 100 - D_variability - D_frequency - D_deviation

        Where:
        D_variability = 20 × (σ_stride / σ_baseline) [capped at 40]
        D_frequency = 15 × |f_measured - f_expected| / f_expected [capped at 30]
        D_deviation = 10 × Σ|a_i - a_healthy,i| / Σa_healthy,i [capped at 30]

        Returns:
            Dict with score and deductions
        """
        # D_variability
        D_var = min(
            20 * (stride_variability / baseline_variability),
            self.leg_health_config['variability_cap']
        )

        # D_frequency
        D_freq = min(
            15 * abs(measured_freq - expected_freq) / expected_freq,
            self.leg_health_config['frequency_cap']
        )

        # D_deviation
        D_dev = min(
            10 * accel_deviation,
            self.leg_health_config['deviation_cap']
        )

        # Total score
        score = 100 - D_var - D_freq - D_dev

        return {
            'leg_health_score': round(max(0, score), 2),
            'deduction_variability': round(D_var, 2),
            'deduction_frequency': round(D_freq, 2),
            'deduction_deviation': round(D_dev, 2)
        }

    def detect_asymmetry_alert(
        self,
        symmetry_scores: List[float],
        threshold: float = 60
    ) -> bool:
        """
        Check for asymmetry alert condition

        From Section 3.2.6:
        Alert if |S_pair| < 60 for > 3 consecutive readings

        Args:
            symmetry_scores: List of recent symmetry scores
            threshold: Symmetry threshold (default 60)

        Returns:
            True if alert condition met
        """
        consecutive_required = self.thresholds['consecutive_readings_required']

        if len(symmetry_scores) < consecutive_required:
            return False

        # Check last N readings
        recent_scores = symmetry_scores[-consecutive_required:]

        # All must be below threshold
        return all(score < threshold for score in recent_scores)

    def calculate_confidence_score(
        self,
        freq_confidence: float,
        front_hind_confidence: float,
        left_right_confidence: float,
        diag_confidence: float
    ) -> float:
        """
        Calculate overall confidence score

        From Section 3.2.4:
        C_total = 0.40·C_freq + 0.30·C_FH + 0.20·C_LR + 0.10·C_diag

        Weights from logistic regression on n=120 training strides
        """
        C_total = (
            0.40 * freq_confidence +
            0.30 * front_hind_confidence +
            0.20 * left_right_confidence +
            0.10 * diag_confidence
        )

        return round(C_total, 2)

    def analyze_gait_window(self, sensor_data: Dict[str, List[Dict]]) -> Dict:
        """
        Analyze a 2-second window of sensor data

        Args:
            sensor_data: Dict[sensor_id -> List[readings]] (200 readings @ 100Hz)

        Returns:
            Complete gait analysis results
        """
        # Extract amplitudes for symmetry analysis
        amplitudes = self.extract_stride_amplitudes(sensor_data)

        # Calculate symmetry scores
        symmetry = self.calculate_symmetry_scores(amplitudes)

        # Classify gait using front-left sensor as reference
        fl_accel = np.array([r['accel_z'] for r in sensor_data['FL']])
        gait_type, stride_freq = self.classify_gait(fl_accel)

        # Calculate leg health scores (simplified - using dummy baseline values)
        leg_health_scores = {}
        for sensor_id in ['FL', 'FR', 'BL', 'BR']:
            health = self.calculate_leg_health_score(
                stride_variability=0.05,  # Would calculate from actual data
                baseline_variability=0.04,
                measured_freq=stride_freq,
                expected_freq=0.8,  # Expected for walk
                accel_deviation=0.1
            )
            leg_health_scores[sensor_id] = health['leg_health_score']

        # Confidence score (simplified)
        confidence = self.calculate_confidence_score(
            freq_confidence=95.0,
            front_hind_confidence=92.0,
            left_right_confidence=88.0,
            diag_confidence=85.0
        )

        return {
            'symmetry_front': symmetry['symmetry_front'],
            'symmetry_hind': symmetry['symmetry_hind'],
            'symmetry_diagonal': symmetry['symmetry_diagonal'],
            'symmetry_total': symmetry['symmetry_total'],
            'stride_frequency': stride_freq,
            'gait_type': gait_type,
            'leg_health_scores': leg_health_scores,
            'confidence_score': confidence,
            'amplitudes': amplitudes
        }


# Example usage
if __name__ == "__main__":
    analyzer = GaitAnalyzer()

    # Test symmetry calculation
    test_amplitudes = {
        'FL': 98.5,  # Front Left
        'FR': 100.2,  # Front Right
        'BL': 97.8,  # Back Left
        'BR': 99.1   # Back Right
    }

    scores = analyzer.calculate_symmetry_scores(test_amplitudes)
    print("Symmetry Scores:")
    for key, value in scores.items():
        print(f"  {key}: {value}")

    # Test gait classification
    sample_rate = 100
    duration = 2.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    gait_freq = 0.8  # Walk
    test_accel = 1.2 * np.sin(2 * np.pi * gait_freq * t)

    gait_type, freq = analyzer.classify_gait(test_accel)
    print(f"\nGait Classification: {gait_type} ({freq} Hz)")
