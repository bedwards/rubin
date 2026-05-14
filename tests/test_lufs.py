"""Tests for LUFS measurement and normalization."""

import numpy as np
import pytest
from rubin.lufs import measure_lufs, normalize_to_lufs

SR = 48000
N = SR * 5  # 5 seconds (pyloudnorm needs ~3s minimum for integrated)


def pink_noise(n=N, sr=SR) -> np.ndarray:
    """Approximate pink noise: better LUFS test signal than sine."""
    white = np.random.default_rng(42).standard_normal((n, 2)).astype(np.float32)
    # Simple 1/f filter approximation
    from scipy import signal as sp
    b, a = sp.butter(1, 200 / (sr / 2), btype="high")
    white[:, 0] = sp.lfilter(b, a, white[:, 0])
    white[:, 1] = sp.lfilter(b, a, white[:, 1])
    return white * 0.1  # moderate level


class TestMeasureLufs:
    def test_returns_dict(self):
        audio = pink_noise()
        result = measure_lufs(audio, SR)
        assert "integrated_lufs" in result
        assert "true_peak_db" in result

    def test_silent_audio(self):
        silence = np.zeros((N, 2), dtype=np.float32)
        result = measure_lufs(silence, SR)
        assert result["integrated_lufs"] < -70 or np.isinf(result["integrated_lufs"])

    def test_loudness_range(self):
        audio = pink_noise()
        result = measure_lufs(audio, SR)
        # Pink noise at 0.1 amplitude should be in reasonable range
        assert -40 < result["integrated_lufs"] < 0


class TestNormalizeLufs:
    @pytest.mark.parametrize("target", [-14.0, -16.0, -23.0])
    def test_hits_target(self, target):
        audio = pink_noise()
        normalized, stats = normalize_to_lufs(audio, SR, target_lufs=target)
        assert abs(stats["integrated_lufs"] - target) < 0.5

    def test_true_peak_protected(self):
        # Loud signal that needs significant reduction
        audio = pink_noise() * 10.0
        normalized, stats = normalize_to_lufs(audio, SR, target_lufs=-14.0, true_peak_db=-1.0)
        assert stats["true_peak_db"] <= -0.9

    def test_output_is_float32(self):
        audio = pink_noise()
        normalized, _ = normalize_to_lufs(audio, SR, -14.0)
        assert normalized.dtype == np.float32
