"""LUFS measurement and normalization using pyloudnorm."""

import numpy as np
import pyloudnorm as pyln


def measure_lufs(audio: np.ndarray, sr: int) -> dict:
    """Measure integrated LUFS and true peak."""
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(audio)
    true_peak_db = _true_peak_db(audio)
    return {
        "integrated_lufs": loudness,
        "true_peak_db": true_peak_db,
    }


def normalize_to_lufs(
    audio: np.ndarray,
    sr: int,
    target_lufs: float,
    true_peak_db: float = -1.0,
    tolerance: float = 0.5,
) -> tuple[np.ndarray, dict]:
    """Normalize audio to target LUFS with true peak protection.

    Returns (normalized_audio, stats_dict).
    """
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(audio)

    if np.isinf(loudness):
        # Silent audio - just return as is
        return audio, {"integrated_lufs": float("-inf"), "true_peak_db": -120.0, "gain_applied_db": 0.0}

    # Loudness normalize
    normalized = pyln.normalize.loudness(audio, loudness, target_lufs)

    # True peak limiting
    peak = _true_peak_db(normalized)
    if peak > true_peak_db:
        reduction = peak - true_peak_db
        normalized = normalized * (10 ** (-reduction / 20.0))

    stats = measure_lufs(normalized, sr)
    gain_applied_db = 20 * np.log10(np.max(np.abs(normalized)) / (np.max(np.abs(audio)) + 1e-8))
    stats["gain_applied_db"] = gain_applied_db

    return normalized.astype(np.float32), stats


def _true_peak_db(audio: np.ndarray) -> float:
    """Calculate true peak in dBTP using 4x oversampling."""
    from scipy import signal as sp
    # 4x oversample for accurate intersample peak detection
    os_factor = 4
    if audio.ndim == 2:
        peaks = []
        for ch in range(audio.shape[1]):
            upsampled = sp.resample_poly(audio[:, ch], os_factor, 1)
            peaks.append(np.max(np.abs(upsampled)))
        peak = max(peaks)
    else:
        upsampled = sp.resample_poly(audio, os_factor, 1)
        peak = np.max(np.abs(upsampled))
    return 20 * np.log10(max(peak, 1e-8))
