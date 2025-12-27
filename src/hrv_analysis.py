"""
EquineSync HRV (Heart Rate Variability) Analysis Module
Implements SDNN, RMSSD, pNN50 calculations and stress detection
Based on ESC/NASPE HRV standards adapted for equines
"""

import numpy as np
from typing import List, Dict, Tuple
import json
import os


class HRVAnalyzer:
    """Analyzes heart rate variability for stress and cardiac health assessment"""

    def __init__(self, config_path: str = None):
        """Initialize with HRV thresholds from config"""
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'alert_thresholds.json')

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.thresholds = config['hrv_metrics']

    def filter_rr_intervals(self, rr_intervals: List[float]) -> List[float]:
        """
        Filter R-R intervals to remove artifacts

        From Section 3.2.1:
        300 ms ≤ RR_i ≤ 2000 ms
        |RR_i - median(RR)| ≤ 0.20 × median(RR)

        Args:
            rr_intervals: Raw R-R intervals in milliseconds

        Returns:
            Filtered R-R intervals
        """
        # Convert to numpy array
        rr = np.array(rr_intervals)

        # Physiological bounds filter
        valid = (rr >= 300) & (rr <= 2000)
        rr_filtered = rr[valid]

        if len(rr_filtered) == 0:
            return []

        # Median-based artifact removal
        median_rr = np.median(rr_filtered)
        deviation_threshold = 0.20 * median_rr

        valid_deviation = np.abs(rr_filtered - median_rr) <= deviation_threshold
        rr_final = rr_filtered[valid_deviation]

        return rr_final.tolist()

    def calculate_sdnn(self, rr_intervals: List[float]) -> float:
        """
        Calculate SDNN (Standard Deviation of NN intervals)
        Measures overall HRV

        From Section 3.2.1, Equation 3:
        SDNN = sqrt(1/(N-1) × Σ(RR_i - mean(RR))²)

        Args:
            rr_intervals: Filtered R-R intervals in milliseconds

        Returns:
            SDNN in milliseconds
        """
        if len(rr_intervals) < 2:
            return 0.0

        rr = np.array(rr_intervals)
        mean_rr = np.mean(rr)

        # SDNN calculation
        sdnn = np.sqrt(np.sum((rr - mean_rr) ** 2) / (len(rr) - 1))

        return round(sdnn, 2)

    def calculate_rmssd(self, rr_intervals: List[float]) -> float:
        """
        Calculate RMSSD (Root Mean Square of Successive Differences)
        Measures parasympathetic (vagal) activity

        From Section 3.2.1, Equation 4:
        RMSSD = sqrt(1/(N-1) × Σ(RR_{i+1} - RR_i)²)

        Args:
            rr_intervals: Filtered R-R intervals in milliseconds

        Returns:
            RMSSD in milliseconds
        """
        if len(rr_intervals) < 2:
            return 0.0

        rr = np.array(rr_intervals)

        # Calculate successive differences
        successive_diffs = np.diff(rr)

        # RMSSD calculation
        rmssd = np.sqrt(np.mean(successive_diffs ** 2))

        return round(rmssd, 2)

    def calculate_pnn50(self, rr_intervals: List[float]) -> float:
        """
        Calculate pNN50 (Percentage of successive intervals differing by >50ms)

        From Section 3.2.1, Equation 5:
        pNN50 = count(|RR_{i+1} - RR_i| > 50 ms) / (N-1) × 100%

        Args:
            rr_intervals: Filtered R-R intervals in milliseconds

        Returns:
            pNN50 as percentage
        """
        if len(rr_intervals) < 2:
            return 0.0

        rr = np.array(rr_intervals)

        # Calculate successive differences
        successive_diffs = np.abs(np.diff(rr))

        # Count differences > 50ms
        count_above_50 = np.sum(successive_diffs > 50)

        # Calculate percentage
        pnn50 = (count_above_50 / (len(rr) - 1)) * 100

        return round(pnn50, 2)

    def interpret_hrv_metrics(
        self,
        sdnn: float,
        rmssd: float,
        pnn50: float
    ) -> Dict[str, str]:
        """
        Interpret HRV metrics according to thresholds

        From Table 1:
        SDNN: >50ms (Good), 30-50ms (Warning), <30ms (Alert)
        RMSSD: >40ms (Good), 20-40ms (Warning), <20ms (Alert)
        pNN50: >3% (Good), 1-3% (Warning), <1% (Alert)

        Returns:
            Dict with status for each metric
        """
        # SDNN interpretation
        if sdnn > self.thresholds['sdnn']['good']:
            sdnn_status = 'Good'
        elif sdnn >= self.thresholds['sdnn']['warning']:
            sdnn_status = 'Warning'
        else:
            sdnn_status = 'Alert'

        # RMSSD interpretation
        if rmssd > self.thresholds['rmssd']['good']:
            rmssd_status = 'Good'
        elif rmssd >= self.thresholds['rmssd']['warning']:
            rmssd_status = 'Warning'
        else:
            rmssd_status = 'Alert'

        # pNN50 interpretation
        if pnn50 > self.thresholds['pnn50']['good']:
            pnn50_status = 'Good'
        elif pnn50 >= self.thresholds['pnn50']['warning']:
            pnn50_status = 'Warning'
        else:
            pnn50_status = 'Alert'

        return {
            'sdnn_status': sdnn_status,
            'rmssd_status': rmssd_status,
            'pnn50_status': pnn50_status
        }

    def calculate_stress_level(
        self,
        sdnn: float,
        rmssd: float,
        pnn50: float
    ) -> Tuple[str, int]:
        """
        Calculate overall stress level from HRV metrics

        Returns:
            (stress_level_label, stress_score_0_100)
        """
        # Interpret individual metrics
        statuses = self.interpret_hrv_metrics(sdnn, rmssd, pnn50)

        # Count alert/warning indicators
        alert_count = sum(1 for status in statuses.values() if status == 'Alert')
        warning_count = sum(1 for status in statuses.values() if status == 'Warning')

        # Determine stress level
        if alert_count >= 2:
            stress_level = 'Critical'
            stress_score = 90
        elif alert_count == 1 or warning_count >= 2:
            stress_level = 'High'
            stress_score = 70
        elif warning_count == 1:
            stress_level = 'Moderate'
            stress_score = 50
        else:
            stress_level = 'Low'
            stress_score = 20

        return stress_level, stress_score

    def estimate_emotional_state(
        self,
        stress_score: int,
        hrv_trend: str = 'stable'
    ) -> str:
        """
        Estimate emotional state for horse-rider bond assessment

        Args:
            stress_score: 0-100 stress score
            hrv_trend: 'increasing', 'decreasing', or 'stable'

        Returns:
            Emotional state description
        """
        if stress_score < 30:
            if hrv_trend == 'increasing':
                return 'Relaxed & Bonding'
            else:
                return 'Calm & Content'
        elif stress_score < 60:
            return 'Moderate Arousal'
        elif stress_score < 80:
            if hrv_trend == 'increasing':
                return 'Anxious & Escalating'
            else:
                return 'Stressed'
        else:
            return 'Critical Distress'

    def calculate_rider_bond_score(
        self,
        horse_stress: int,
        rider_stress: int = None,
        interaction_quality: float = None
    ) -> float:
        """
        Calculate horse-rider bond score (0-100)

        Higher score = stronger bond
        Based on synchronized HRV patterns

        Args:
            horse_stress: Horse stress score (0-100)
            rider_stress: Rider stress score (0-100) if available
            interaction_quality: Quality metric (0-1) if available

        Returns:
            Bond score 0-100
        """
        # Base score inversely proportional to stress
        base_score = 100 - horse_stress

        # If rider data available, factor in synchronization
        if rider_stress is not None:
            # Lower stress differential = better bond
            stress_diff = abs(horse_stress - rider_stress)
            sync_bonus = max(0, 20 - (stress_diff * 0.4))
            base_score += sync_bonus

        # Quality adjustment
        if interaction_quality is not None:
            base_score *= interaction_quality

        return round(min(100, max(0, base_score)), 2)

    def analyze_hrv_window(
        self,
        rr_intervals: List[float],
        horse_id: str = 'unknown'
    ) -> Dict:
        """
        Complete HRV analysis for a time window (typically 60 seconds)

        Args:
            rr_intervals: Raw R-R intervals in milliseconds
            horse_id: Horse identifier

        Returns:
            Complete HRV analysis results
        """
        # Filter artifacts
        filtered_rr = self.filter_rr_intervals(rr_intervals)

        if len(filtered_rr) < 5:
            return {
                'error': 'Insufficient valid R-R intervals',
                'raw_count': len(rr_intervals),
                'filtered_count': len(filtered_rr)
            }

        # Calculate HRV metrics
        sdnn = self.calculate_sdnn(filtered_rr)
        rmssd = self.calculate_rmssd(filtered_rr)
        pnn50 = self.calculate_pnn50(filtered_rr)

        # Interpret metrics
        statuses = self.interpret_hrv_metrics(sdnn, rmssd, pnn50)

        # Calculate stress
        stress_level, stress_score = self.calculate_stress_level(sdnn, rmssd, pnn50)

        # Estimate emotional state
        emotional_state = self.estimate_emotional_state(stress_score)

        # Calculate bond score (simplified - no rider data)
        bond_score = self.calculate_rider_bond_score(stress_score)

        return {
            'horse_id': horse_id,
            'timestamp': int(np.mean([0])),  # Would use actual timestamps
            'sdnn': sdnn,
            'rmssd': rmssd,
            'pnn50': pnn50,
            'sdnn_status': statuses['sdnn_status'],
            'rmssd_status': statuses['rmssd_status'],
            'pnn50_status': statuses['pnn50_status'],
            'stress_level': stress_level,
            'stress_score': stress_score,
            'emotional_state': emotional_state,
            'rider_bond_score': bond_score,
            'samples_analyzed': len(filtered_rr),
            'samples_filtered_out': len(rr_intervals) - len(filtered_rr)
        }


# Example usage
if __name__ == "__main__":
    analyzer = HRVAnalyzer()

    # Simulate 60 seconds of R-R intervals (healthy horse, ~100 BPM)
    # Mean RR = 600ms, SDNN ~50ms (healthy variation)
    np.random.seed(42)
    baseline_rr = 600
    healthy_rr = np.random.normal(baseline_rr, 50, 100)  # 100 heartbeats

    print("=== Healthy Horse HRV Analysis ===")
    results_healthy = analyzer.analyze_hrv_window(healthy_rr.tolist(), 'horse-001')
    for key, value in results_healthy.items():
        print(f"  {key}: {value}")

    # Simulate stressed horse (low HRV)
    stressed_rr = np.random.normal(baseline_rr, 15, 100)  # Low SDNN

    print("\n=== Stressed Horse HRV Analysis ===")
    results_stressed = analyzer.analyze_hrv_window(stressed_rr.tolist(), 'horse-002')
    for key, value in results_stressed.items():
        print(f"  {key}: {value}")
