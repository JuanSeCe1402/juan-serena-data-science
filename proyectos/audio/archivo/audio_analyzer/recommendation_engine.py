from typing import Dict, Any
import numpy as np
from scipy import interpolate
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generates audio recommendations based on analysis."""

    def __init__(self):
        self.harman_target = self._create_harman_target()

    def _create_harman_target(self):
        """Create Harman target curve."""
        freq = np.array([20, 50, 100, 200, 500, 1000, 2000, 3000, 4000, 6000, 10000, 20000])
        response = np.array([5.5, 6.5, 5.5, 4.0, 1.5, 0.0, 2.5, 3.5, 4.0, 1.5, -2.0, -4.0])
        return interpolate.PchipInterpolator(freq, response)

    def generate_recommendations(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on analysis."""
        try:
            eq_settings = self._recommend_eq(analysis_results['spectral'])
            headphones = self._recommend_headphones(analysis_results)

            return {
                'eq_settings': eq_settings,
                'headphones': headphones,
                'volume': self._recommend_volume(analysis_results['temporal'])
            }
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            return {}

    def _recommend_eq(self, spectral_data: Dict[str, Any]) -> Dict[str, float]:
        """Generate EQ recommendations with safety checks."""
        freq_bands = {
            'Sub Bass (20-60Hz)': (20, 60),
            'Bass (60-250Hz)': (60, 250),
            'Low Mids (250-500Hz)': (250, 500),
            'Mids (500-2kHz)': (500, 2000),
            'Upper Mids (2-4kHz)': (2000, 4000),
            'Presence (4-6kHz)': (4000, 6000),
            'Brilliance (6-20kHz)': (6000, 20000)
        }

        eq_settings = {}
        freqs = spectral_data['frequencies']
        mag_spectrum = spectral_data['magnitude_spectrum']

        for band_name, (low, high) in freq_bands.items():
            mask = (freqs >= low) & (freqs <= high)
            if np.any(mask):  # Check if we have frequencies in this band
                band_freqs = freqs[mask]
                band_energy = np.mean(mag_spectrum[mask])
                target_energy = np.mean(self.harman_target(band_freqs))

                difference = target_energy - band_energy
                if abs(difference) > 1:
                    eq_settings[band_name] = float(round(difference, 1))

        return eq_settings
