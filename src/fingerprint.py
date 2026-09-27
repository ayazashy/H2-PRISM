"""
Candidate Transient Fingerprinting Layer (Person 2: Faisal).
Extracts compact time-frequency and wavelet energy descriptors.
Subject to strict ablation testing (A6/B4 vs B3).
"""

from typing import Dict, Any
import numpy as np

try:
    import pywt
    HAS_PYWT = True
except ImportError:
    HAS_PYWT = False


def extract_transient_fingerprint(
    signal: np.ndarray,
    sampling_rate_hz: float = 1.0,
    scales: np.ndarray = np.arange(1, 16)
) -> Dict[str, float]:
    """
    Extracts compact time-frequency descriptors from transient waveform.
    Returns:
    - transient_energy
    - peak_energy_ratio
    - dominant_scale
    - high_frequency_ratio
    """
    signal = signal - np.mean(signal)
    total_energy = float(np.sum(signal ** 2)) + 1e-9

    if not HAS_PYWT or len(signal) < 8:
        # Fallback to simple FFT energy bands
        fft_vals = np.abs(np.fft.rfft(signal))
        n_half = len(fft_vals)
        low_band = float(np.sum(fft_vals[: n_half // 2] ** 2))
        high_band = float(np.sum(fft_vals[n_half // 2:] ** 2))
        return {
            "transient_energy": total_energy,
            "transient_peak_ratio": float(np.max(np.abs(signal)) ** 2 / total_energy),
            "dominant_scale": 1.0,
            "high_freq_energy_ratio": float(high_band / (low_band + high_band + 1e-9)),
            "wavelet_available": 0.0
        }

    # Continuous Wavelet Transform using Morlet wavelet
    coefficients, frequencies = pywt.cwt(signal, scales, "morl", sampling_period=1.0 / sampling_rate_hz)
    scale_energies = np.sum(np.abs(coefficients) ** 2, axis=1)
    dominant_scale_idx = int(np.argmax(scale_energies))

    return {
        "transient_energy": total_energy,
        "transient_peak_ratio": float(np.max(np.abs(signal)) ** 2 / total_energy),
        "dominant_scale": float(scales[dominant_scale_idx]),
        "high_freq_energy_ratio": float(np.sum(scale_energies[:4]) / (np.sum(scale_energies) + 1e-9)),
        "wavelet_available": 1.0
    }
