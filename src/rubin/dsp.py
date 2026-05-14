"""Low-level DSP primitives not available in pedalboard."""

import numpy as np
from scipy import signal as sp_signal


def soft_clip_tanh(audio: np.ndarray, drive: float) -> np.ndarray:
    """Tape/tube saturation via tanh soft-clipping.

    drive: 0-1, amount of harmonic coloring
    Adds even harmonics for warmth (pre-gain into tanh then normalize).
    """
    if drive <= 0:
        return audio
    gain = 1.0 + drive * 8.0
    clipped = np.tanh(audio * gain) / np.tanh(gain)
    return clipped


def tube_saturate(audio: np.ndarray, drive: float, mix: float) -> np.ndarray:
    """2nd-order harmonic saturation (tube-style, asymmetric).

    Asymmetric waveshaping emphasizes even harmonics.
    drive: 0-1
    mix: 0-1 wet/dry
    """
    if drive <= 0:
        return audio
    gain = 1.0 + drive * 5.0
    driven = audio * gain
    # Asymmetric: different clipping for positive/negative
    pos = np.where(driven > 0, np.tanh(driven * 1.3) / (1.3 * np.tanh(gain)), driven)
    neg = np.where(driven <= 0, np.tanh(driven * 0.8) / (0.8 * np.tanh(gain)), pos)
    saturated = np.where(audio > 0, pos, neg)
    # Normalize to prevent loudness increase
    sat_rms = np.sqrt(np.mean(saturated ** 2)) + 1e-8
    dry_rms = np.sqrt(np.mean(audio ** 2)) + 1e-8
    saturated = saturated * (dry_rms / sat_rms)
    return audio * (1 - mix) + saturated * mix


def wow_flutter(audio: np.ndarray, sr: int, rate_hz: float, depth: float) -> np.ndarray:
    """Tape wow/flutter: time-varying pitch modulation.

    rate_hz: LFO speed (0.5-4 Hz typical)
    depth: pitch deviation in fraction of sample (0.001-0.01 typical)
    """
    if rate_hz <= 0 or depth <= 0:
        return audio
    n_samples = audio.shape[0]
    t = np.arange(n_samples) / sr
    # Use two sine waves at slightly different rates for organic wow
    lfo = (
        depth * np.sin(2 * np.pi * rate_hz * t)
        + depth * 0.4 * np.sin(2 * np.pi * rate_hz * 2.1 * t + 0.7)
    )
    # Convert depth to fractional samples
    delay_samples = lfo * sr * 0.01
    indices = np.arange(n_samples) + delay_samples
    indices = np.clip(indices, 0, n_samples - 1)
    if audio.ndim == 2:
        result = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            result[:, ch] = np.interp(indices, np.arange(n_samples), audio[:, ch])
        return result
    return np.interp(indices, np.arange(n_samples), audio)


def bit_crush(audio: np.ndarray, bit_depth: int) -> np.ndarray:
    """Reduce bit depth for lo-fi character."""
    if bit_depth <= 0 or bit_depth >= 32:
        return audio
    levels = 2 ** (bit_depth - 1)
    return np.round(audio * levels) / levels


def vinyl_noise(n_samples: int, sr: int, level: float, channels: int = 2) -> np.ndarray:
    """Generate vinyl crackle/surface noise.

    Combines white noise (hiss) with occasional pops (crackle).
    """
    if level <= 0:
        return np.zeros((n_samples, channels), dtype=np.float32)

    # White noise hiss (LPF shaped to vinyl frequency response)
    noise = np.random.normal(0, level * 0.4, (n_samples, channels)).astype(np.float32)
    # LPF the hiss
    b, a = sp_signal.butter(2, 8000 / (sr / 2), btype="low")
    for ch in range(channels):
        noise[:, ch] = sp_signal.lfilter(b, a, noise[:, ch])

    # Occasional crackle pops
    pop_rate = 0.5  # pops per second
    n_pops = max(1, int(pop_rate * n_samples / sr))
    pop_positions = np.random.randint(0, n_samples, n_pops)
    for pos in pop_positions:
        pop_len = np.random.randint(20, 80)
        pop_end = min(pos + pop_len, n_samples)
        pop_env = np.exp(-np.linspace(0, 8, pop_end - pos))
        pop_amp = level * np.random.uniform(1.0, 3.0)
        for ch in range(channels):
            noise[pos:pop_end, ch] += pop_env * pop_amp * np.random.choice([-1, 1])

    return noise


def deesser(
    audio: np.ndarray,
    sr: int,
    center_hz: float,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
) -> np.ndarray:
    """Frequency-selective de-esser using sidechain compression on high band."""
    if audio.ndim == 1:
        audio = audio[:, np.newaxis]
        squeeze = True
    else:
        squeeze = False

    # Bandpass the sidechain around sibilance frequency
    bw = center_hz * 0.6
    lo = max(20, center_hz - bw / 2)
    hi = min(sr / 2 - 1, center_hz + bw / 2)
    b, a = sp_signal.butter(2, [lo / (sr / 2), hi / (sr / 2)], btype="band")

    n_samples = audio.shape[0]
    n_ch = audio.shape[1]
    result = np.zeros_like(audio)

    attack_coef = np.exp(-1.0 / (attack_ms * sr / 1000.0))
    release_coef = np.exp(-1.0 / (release_ms * sr / 1000.0))
    threshold = 10 ** (threshold_db / 20.0)

    for ch in range(n_ch):
        sidechain = sp_signal.lfilter(b, a, audio[:, ch])
        gain = np.ones(n_samples, dtype=np.float64)
        env = 0.0
        for i in range(n_samples):
            level = abs(sidechain[i])
            if level > env:
                env = attack_coef * env + (1 - attack_coef) * level
            else:
                env = release_coef * env + (1 - release_coef) * level
            if env > threshold:
                reduction = threshold / env
                gain[i] = 1.0 - (1.0 - reduction) * (1.0 - 1.0 / ratio)
        result[:, ch] = audio[:, ch] * gain

    if squeeze:
        return result[:, 0]
    return result


def ms_width(audio: np.ndarray, width: float) -> np.ndarray:
    """Mid/side stereo width control.

    width > 1: wider, width < 1: narrower, width == 0: mono
    """
    if audio.ndim != 2 or audio.shape[1] != 2:
        return audio
    mid = (audio[:, 0] + audio[:, 1]) * 0.5
    side = (audio[:, 0] - audio[:, 1]) * 0.5
    side_adjusted = side * width
    left = mid + side_adjusted
    right = mid - side_adjusted
    return np.stack([left, right], axis=1)


def rms_normalize(audio: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    """Normalize audio to target RMS level."""
    current_rms = np.sqrt(np.mean(audio ** 2)) + 1e-8
    return audio * (target_rms / current_rms)


def db_to_linear(db: float) -> float:
    return 10 ** (db / 20.0)


def linear_to_db(linear: float) -> float:
    return 20 * np.log10(max(linear, 1e-8))
