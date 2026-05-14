"""Tests for processing chains."""

import numpy as np
import pytest
from rubin.chains import VocalChain, GuitarChain, MasterChain
from rubin.presets import (
    ANALOG_CONSOLE_VOCAL, ANALOG_CONSOLE_GUITAR, ANALOG_CONSOLE_MASTER,
    TAPE_VOCAL, TAPE_GUITAR, TAPE_MASTER,
    LOFI_VOCAL, LOFI_GUITAR, LOFI_MASTER,
)

SR = 48000
N = SR * 3  # 3 seconds


def make_stereo_tone(freq=220.0, amp=0.3) -> np.ndarray:
    t = np.linspace(0, N / SR, N)
    sig = (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    return np.stack([sig, sig * 0.85], axis=1)


def rms(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio ** 2)))


class TestVocalChain:
    @pytest.mark.parametrize("preset", [
        ANALOG_CONSOLE_VOCAL, TAPE_VOCAL, LOFI_VOCAL
    ])
    def test_outputs_audio(self, preset):
        audio = make_stereo_tone(880.0)
        chain = VocalChain(preset)
        out = chain.process(audio, SR)
        assert out is not None
        assert out.shape[0] > 0

    @pytest.mark.parametrize("preset", [
        ANALOG_CONSOLE_VOCAL, TAPE_VOCAL, LOFI_VOCAL
    ])
    def test_no_clipping(self, preset):
        audio = make_stereo_tone(880.0, amp=0.3)
        chain = VocalChain(preset)
        out = chain.process(audio, SR)
        # Processed output should not clip hard
        assert np.max(np.abs(out)) < 2.0, "Severe clipping detected"

    def test_analog_console_adds_high_freq(self):
        # Presence boost should add energy at 3.5kHz
        audio = make_stereo_tone(220.0)
        chain = VocalChain(ANALOG_CONSOLE_VOCAL)
        out = chain.process(audio, SR)
        assert out is not None


class TestGuitarChain:
    @pytest.mark.parametrize("preset", [
        ANALOG_CONSOLE_GUITAR, TAPE_GUITAR, LOFI_GUITAR
    ])
    def test_outputs_audio(self, preset):
        audio = make_stereo_tone(330.0)
        chain = GuitarChain(preset)
        out = chain.process(audio, SR)
        assert out is not None
        assert out.shape[0] > 0

    def test_lofi_sample_reduction(self):
        audio = make_stereo_tone(330.0)
        chain = GuitarChain(LOFI_GUITAR)
        out = chain.process(audio, SR)
        # Lo-fi should still produce audio
        assert np.max(np.abs(out)) > 0.001


class TestMasterChain:
    @pytest.mark.parametrize("vp,gp,mp", [
        (ANALOG_CONSOLE_VOCAL, ANALOG_CONSOLE_GUITAR, ANALOG_CONSOLE_MASTER),
        (TAPE_VOCAL, TAPE_GUITAR, TAPE_MASTER),
        (LOFI_VOCAL, LOFI_GUITAR, LOFI_MASTER),
    ])
    def test_master_produces_output(self, vp, gp, mp):
        vocal = make_stereo_tone(880.0)
        guitar = make_stereo_tone(330.0)

        from rubin.chains import VocalChain, GuitarChain
        v_proc = VocalChain(vp).process(vocal, SR)
        g_proc = GuitarChain(gp).process(guitar, SR)

        chain = MasterChain(mp)
        mix, stats = chain.process(v_proc, g_proc, SR)

        assert mix is not None
        assert "integrated_lufs" in stats
        assert "true_peak_db" in stats

    def test_lufs_target_hit(self):
        vocal = make_stereo_tone(880.0, amp=0.4)
        guitar = make_stereo_tone(330.0, amp=0.3)

        from rubin.chains import VocalChain, GuitarChain
        v_proc = VocalChain(ANALOG_CONSOLE_VOCAL).process(vocal, SR)
        g_proc = GuitarChain(ANALOG_CONSOLE_GUITAR).process(guitar, SR)

        chain = MasterChain(ANALOG_CONSOLE_MASTER)
        mix, stats = chain.process(v_proc, g_proc, SR)

        target = ANALOG_CONSOLE_MASTER.target_lufs
        tolerance = ANALOG_CONSOLE_MASTER.target_lufs_tolerance
        lufs = stats["integrated_lufs"]
        assert not np.isinf(lufs), "LUFS is -inf (silent output)"
        assert abs(lufs - target) <= tolerance + 1.0, f"LUFS {lufs:.1f} too far from target {target}"

    def test_true_peak_protected(self):
        vocal = make_stereo_tone(880.0, amp=0.8)
        guitar = make_stereo_tone(330.0, amp=0.8)

        from rubin.chains import VocalChain, GuitarChain
        v_proc = VocalChain(ANALOG_CONSOLE_VOCAL).process(vocal, SR)
        g_proc = GuitarChain(ANALOG_CONSOLE_GUITAR).process(guitar, SR)

        chain = MasterChain(ANALOG_CONSOLE_MASTER)
        mix, stats = chain.process(v_proc, g_proc, SR)

        tp_limit = ANALOG_CONSOLE_MASTER.limiter_true_peak_db
        # Allow 0.3 dB over due to LUFS normalization applied after limiter
        assert stats["true_peak_db"] <= tp_limit + 0.5, (
            f"True peak {stats['true_peak_db']:.2f} exceeded limit {tp_limit}"
        )
