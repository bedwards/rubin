"""Acoustic guitar processing chain."""

import numpy as np
import pedalboard as pb
from pedalboard import Pedalboard

from ..presets.base import GuitarPreset
from .. import dsp


class GuitarChain:
    def __init__(self, preset: GuitarPreset):
        self.preset = preset

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        p = self.preset

        audio = audio.astype(np.float32)

        if p.input_gain_db != 0:
            audio = audio * dsp.db_to_linear(p.input_gain_db)

        # --- Phase 1: EQ ---
        board = Pedalboard([
            pb.HighpassFilter(cutoff_frequency_hz=p.hpf_hz),
            pb.PeakFilter(
                cutoff_frequency_hz=p.eq_mud_hz,
                gain_db=p.eq_mud_db,
                q=p.eq_mud_q,
            ),
            pb.PeakFilter(
                cutoff_frequency_hz=p.eq_presence_hz,
                gain_db=p.eq_presence_db,
                q=p.eq_presence_q,
            ),
            pb.HighShelfFilter(
                cutoff_frequency_hz=p.eq_sparkle_hz,
                gain_db=p.eq_sparkle_db,
            ),
        ])
        audio_pb = _to_pb(audio)
        audio_pb = board(audio_pb, sr)
        audio = _from_pb(audio_pb)

        # --- Phase 2: Saturation ---
        if p.saturation_drive > 0:
            audio = dsp.tube_saturate(audio, p.saturation_drive, p.saturation_mix).astype(np.float32)

        # --- Phase 3: Compression ---
        comp_board = Pedalboard([
            pb.Compressor(
                threshold_db=p.comp_threshold_db,
                ratio=p.comp_ratio,
                attack_ms=p.comp_attack_ms,
                release_ms=p.comp_release_ms,
            ),
            pb.Gain(gain_db=p.comp_makeup_db),
        ])
        audio_pb = _to_pb(audio)
        audio_pb = comp_board(audio_pb, sr)
        audio = _from_pb(audio_pb)

        # --- Phase 4: HF rolloff ---
        if p.hf_rolloff_hz > 0:
            shelf_board = Pedalboard([
                pb.HighShelfFilter(
                    cutoff_frequency_hz=p.hf_rolloff_hz,
                    gain_db=p.hf_rolloff_db,
                )
            ])
            audio_pb = _to_pb(audio)
            audio_pb = shelf_board(audio_pb, sr)
            audio = _from_pb(audio_pb)

        # --- Phase 5: Reverb ---
        reverb_board = Pedalboard([
            pb.Reverb(
                room_size=p.reverb_room_size,
                damping=p.reverb_damping,
                wet_level=p.reverb_wet,
                dry_level=1.0 - p.reverb_wet * 0.1,
                width=p.reverb_width,
            )
        ])
        audio_pb = _to_pb(audio)
        audio_pb = reverb_board(audio_pb, sr)
        audio = _from_pb(audio_pb)

        # --- Phase 6: Wow/flutter ---
        if p.flutter_rate_hz > 0:
            audio = dsp.wow_flutter(audio, sr, p.flutter_rate_hz, p.flutter_depth).astype(np.float32)

        # --- Phase 7: Lo-fi degradation ---
        if p.lofi_sample_rate > 0 and p.lofi_sample_rate < sr:
            # Resample down then back up
            resample_board = Pedalboard([
                pb.Resample(target_sample_rate=float(p.lofi_sample_rate))
            ])
            audio_pb = _to_pb(audio)
            audio_pb = resample_board(audio_pb, sr)
            audio = _from_pb(audio_pb)

        if p.lofi_bit_depth > 0:
            audio = dsp.bit_crush(audio, p.lofi_bit_depth).astype(np.float32)

        if p.lofi_noise_level > 0:
            n_samples = audio.shape[0] if audio.ndim > 1 else len(audio)
            n_ch = audio.shape[1] if audio.ndim == 2 else 1
            noise = dsp.vinyl_noise(n_samples, sr, p.lofi_noise_level, n_ch)
            if audio.ndim == 1:
                noise = noise[:, 0]
            audio = (audio + noise).astype(np.float32)

        if p.output_gain_db != 0:
            audio = audio * dsp.db_to_linear(p.output_gain_db)

        return audio.astype(np.float32)


def _to_pb(audio: np.ndarray) -> np.ndarray:
    if audio.ndim == 1:
        return audio[np.newaxis, :]
    return audio.T.copy()


def _from_pb(audio_pb: np.ndarray) -> np.ndarray:
    if audio_pb.shape[0] == 1:
        return audio_pb[0]
    return audio_pb.T.copy()
