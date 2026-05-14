"""Master chain: mix stems, apply glue, LUFS normalize."""

import numpy as np
import pedalboard as pb
from pedalboard import Pedalboard

from ..presets.base import MasterPreset
from .. import dsp
from ..lufs import normalize_to_lufs


class MasterChain:
    def __init__(self, preset: MasterPreset):
        self.preset = preset

    def process(
        self,
        vocal: np.ndarray,
        guitar: np.ndarray,
        sr: int,
    ) -> tuple[np.ndarray, dict]:
        """Mix stems and master. Returns (audio, stats)."""
        p = self.preset

        # Ensure stereo
        vocal = _ensure_stereo(vocal).astype(np.float32)
        guitar = _ensure_stereo(guitar).astype(np.float32)

        # Match lengths
        min_len = min(vocal.shape[0], guitar.shape[0])
        vocal = vocal[:min_len]
        guitar = guitar[:min_len]

        # Apply stem level trims
        vocal = vocal * dsp.db_to_linear(p.vocal_level_db)
        guitar = guitar * dsp.db_to_linear(p.guitar_level_db)

        # Mix
        mix = vocal + guitar

        # Prevent clipping before further processing
        peak = np.max(np.abs(mix))
        if peak > 0.95:
            mix = mix * (0.95 / peak)

        # Stereo width
        if p.stereo_width != 1.0:
            mix = dsp.ms_width(mix, p.stereo_width).astype(np.float32)

        # --- Master EQ ---
        eq_board = Pedalboard([
            pb.LowShelfFilter(
                cutoff_frequency_hz=p.master_eq_lo_shelf_hz,
                gain_db=p.master_eq_lo_shelf_db,
            ),
            pb.HighShelfFilter(
                cutoff_frequency_hz=p.master_eq_hi_shelf_hz,
                gain_db=p.master_eq_hi_shelf_db,
            ),
        ])
        mix = _from_pb(eq_board(_to_pb(mix), sr))

        # --- Glue compression ---
        glue_board = Pedalboard([
            pb.Compressor(
                threshold_db=p.glue_comp_threshold_db,
                ratio=p.glue_comp_ratio,
                attack_ms=p.glue_comp_attack_ms,
                release_ms=p.glue_comp_release_ms,
            ),
            pb.Gain(gain_db=p.glue_comp_makeup_db),
        ])
        mix = _from_pb(glue_board(_to_pb(mix), sr))

        # --- Master saturation ---
        if p.master_saturation_drive > 0:
            mix = dsp.tube_saturate(
                mix, p.master_saturation_drive, p.master_saturation_mix
            ).astype(np.float32)

        # --- Global HF rolloff ---
        if p.master_hf_rolloff_hz > 0:
            rolloff_board = Pedalboard([
                pb.HighShelfFilter(
                    cutoff_frequency_hz=p.master_hf_rolloff_hz,
                    gain_db=p.master_hf_rolloff_db,
                )
            ])
            mix = _from_pb(rolloff_board(_to_pb(mix), sr))

        # --- Lo-fi sample rate reduction ---
        if p.master_lofi_sample_rate > 0 and p.master_lofi_sample_rate < sr:
            resample_board = Pedalboard([
                pb.Resample(target_sample_rate=float(p.master_lofi_sample_rate))
            ])
            mix = _from_pb(resample_board(_to_pb(mix), sr))

        # --- Vinyl noise ---
        if p.master_vinyl_noise_level > 0:
            noise = dsp.vinyl_noise(mix.shape[0], sr, p.master_vinyl_noise_level, 2)
            mix = (mix + noise).astype(np.float32)

        # --- Brick wall limiter (before LUFS norm) ---
        # Catches any peaks from saturation/noise before normalization boost.
        limiter_board = Pedalboard([
            pb.Limiter(
                threshold_db=p.limiter_true_peak_db - 0.5,
                release_ms=50.0,
            )
        ])
        mix = _from_pb(limiter_board(_to_pb(mix), sr))

        # --- LUFS normalize + true peak protection ---
        mix, stats = normalize_to_lufs(
            mix, sr,
            target_lufs=p.target_lufs,
            true_peak_db=p.limiter_true_peak_db,
            tolerance=p.target_lufs_tolerance,
        )

        return mix.astype(np.float32), stats


def _to_pb(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio[np.newaxis, :]
    return audio.T.copy()


def _from_pb(audio_pb: np.ndarray) -> np.ndarray:
    if audio_pb.shape[0] == 1:
        return audio_pb[0]
    return audio_pb.T.copy()


def _ensure_stereo(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return np.stack([audio, audio], axis=1)
    if audio.ndim == 2 and audio.shape[1] == 1:
        return np.repeat(audio, 2, axis=1)
    return audio
