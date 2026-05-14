"""Tests for DSP primitives."""

import numpy as np
import pytest
from rubin.dsp import (
    soft_clip_tanh, tube_saturate, wow_flutter, bit_crush,
    vinyl_noise, deesser, ms_width, rms_normalize, db_to_linear
)


SR = 48000
DURATION = 2.0
N = int(SR * DURATION)


def sine(freq=440.0, amp=0.5, sr=SR, n=N) -> np.ndarray:
    t = np.linspace(0, n / sr, n)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def stereo(freq=440.0) -> np.ndarray:
    s = sine(freq)
    return np.stack([s, s * 0.9], axis=1)


class TestSaturation:
    def test_soft_clip_unity_at_zero_drive(self):
        audio = sine()
        out = soft_clip_tanh(audio, 0.0)
        np.testing.assert_array_equal(out, audio)

    def test_soft_clip_reduces_peak(self):
        loud = sine(amp=2.0)
        out = soft_clip_tanh(loud, 1.0)
        assert np.max(np.abs(out)) < np.max(np.abs(loud))

    def test_tube_saturate_preserves_rms(self):
        audio = sine()
        rms_in = np.sqrt(np.mean(audio ** 2))
        out = tube_saturate(audio, 0.5, 1.0)
        rms_out = np.sqrt(np.mean(out ** 2))
        assert abs(rms_in - rms_out) < rms_in * 0.1, "RMS changed by more than 10%"

    def test_tube_saturate_stereo(self):
        audio = stereo()
        out = tube_saturate(audio, 0.3, 0.5)
        assert out.shape == audio.shape


class TestWowFlutter:
    def test_no_flutter_passthrough(self):
        audio = sine()
        out = wow_flutter(audio, SR, 0.0, 0.002)
        np.testing.assert_array_equal(out, audio)

    def test_flutter_changes_audio(self):
        audio = sine()
        out = wow_flutter(audio, SR, 1.0, 0.005)
        assert not np.array_equal(out, audio)

    def test_flutter_stereo(self):
        audio = stereo()
        out = wow_flutter(audio, SR, 1.5, 0.003)
        assert out.shape == audio.shape


class TestBitCrush:
    def test_no_crush_at_32(self):
        audio = sine()
        out = bit_crush(audio, 32)
        np.testing.assert_array_equal(out, audio)

    def test_crush_reduces_resolution(self):
        audio = sine(amp=0.5)
        out = bit_crush(audio, 8)
        unique_values = np.unique(np.round(out, 6))
        assert len(unique_values) <= 256 + 2


class TestVinylNoise:
    def test_shape(self):
        noise = vinyl_noise(N, SR, 0.01, 2)
        assert noise.shape == (N, 2)

    def test_zero_level(self):
        noise = vinyl_noise(N, SR, 0.0, 2)
        assert np.all(noise == 0)

    def test_noise_is_small(self):
        noise = vinyl_noise(N, SR, 0.005, 2)
        rms = np.sqrt(np.mean(noise ** 2))
        assert rms < 0.01


class TestDeesser:
    def test_reduces_sibilance(self):
        # Generate signal with energy at 7.5kHz
        t = np.linspace(0, DURATION, N)
        sib = (0.8 * np.sin(2 * np.pi * 7500 * t)).astype(np.float32)
        audio = np.stack([sib, sib], axis=1)
        out = deesser(audio, SR, 7500.0, -6.0, 6.0, 1.0, 50.0)
        # Output should be smaller than input
        assert np.max(np.abs(out)) <= np.max(np.abs(audio)) + 0.01

    def test_passes_low_freq(self):
        # Low frequency signal should not be affected much by de-esser
        audio = stereo(freq=200.0)
        out = deesser(audio, SR, 7500.0, -10.0, 6.0, 1.0, 50.0)
        diff = np.max(np.abs(out - audio))
        assert diff < 0.05


class TestMSWidth:
    def test_mono_collapse(self):
        audio = stereo()
        mono = ms_width(audio, 0.0)
        # Both channels should be equal (mono)
        np.testing.assert_allclose(mono[:, 0], mono[:, 1], atol=1e-6)

    def test_wider(self):
        audio = stereo()
        wider = ms_width(audio, 1.5)
        # Side energy should increase
        side_before = (audio[:, 0] - audio[:, 1]) * 0.5
        side_after = (wider[:, 0] - wider[:, 1]) * 0.5
        assert np.sum(side_after ** 2) > np.sum(side_before ** 2)

    def test_unity_passthrough(self):
        audio = stereo()
        out = ms_width(audio, 1.0)
        np.testing.assert_allclose(out, audio, atol=1e-6)
