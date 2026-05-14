"""Vocal processing chain."""

import numpy as np
import pedalboard as pb
from pedalboard import Pedalboard

from ..presets.base import VocalPreset
from .. import dsp


class VocalChain:
    def __init__(self, preset: VocalPreset):
        self.preset = preset

    def process(self, audio: np.ndarray, sr: int) -> np.ndarray:
        p = self.preset

        # Ensure float32
        audio = audio.astype(np.float32)

        # Input gain
        if p.input_gain_db != 0:
            audio = audio * dsp.db_to_linear(p.input_gain_db)

        # --- Phase 1: HPF + Subtractive EQ ---
        # Subtractive (corrective) EQ before compression so problem freqs
        # don't trigger the compressor unevenly.
        eq_board = Pedalboard([
            pb.HighpassFilter(cutoff_frequency_hz=p.hpf_hz),
            pb.LowShelfFilter(
                cutoff_frequency_hz=p.eq_lo_shelf_hz,
                gain_db=p.eq_lo_shelf_db,
            ),
            pb.PeakFilter(
                cutoff_frequency_hz=p.eq_lo_mid_hz,
                gain_db=p.eq_lo_mid_db,
                q=p.eq_lo_mid_q,
            ),
        ])
        audio_pb = _to_pb(audio)
        audio_pb = eq_board(audio_pb, sr)
        audio = _from_pb(audio_pb)

        # --- Phase 2: First compression pass (FET-style peak control) ---
        comp1_board = Pedalboard([
            pb.Compressor(
                threshold_db=p.comp_threshold_db,
                ratio=p.comp_ratio,
                attack_ms=p.comp_attack_ms,
                release_ms=p.comp_release_ms,
            ),
            pb.Gain(gain_db=p.comp_makeup_db),
        ])
        audio_pb = _to_pb(audio)
        audio_pb = comp1_board(audio_pb, sr)
        audio = _from_pb(audio_pb)

        # --- Phase 3: De-esser AFTER compression ---
        # Compression pumps up sibilance relative to vowels; de-ess after.
        if p.deess_threshold_db < 0:
            audio = dsp.deesser(
                audio, sr,
                center_hz=p.deess_freq_hz,
                threshold_db=p.deess_threshold_db,
                ratio=p.deess_ratio,
                attack_ms=p.deess_attack_ms,
                release_ms=p.deess_release_ms,
            ).astype(np.float32)

        # --- Phase 3b: Stage 2 compression (optical, transparent gain riding) ---
        # Placed after de-essing so sibilance doesn't trigger the compressor
        if p.comp2_threshold_db < 0:
            comp2_board = Pedalboard([
                pb.Compressor(
                    threshold_db=p.comp2_threshold_db,
                    ratio=p.comp2_ratio,
                    attack_ms=p.comp2_attack_ms,
                    release_ms=p.comp2_release_ms,
                ),
                pb.Gain(gain_db=p.comp2_makeup_db),
            ])
            audio_pb = _to_pb(audio)
            audio_pb = comp2_board(audio_pb, sr)
            audio = _from_pb(audio_pb)

        # --- Phase 4: Additive/creative EQ (presence + air) ---
        additive_eq_board = Pedalboard([
            pb.PeakFilter(
                cutoff_frequency_hz=p.eq_presence_hz,
                gain_db=p.eq_presence_db,
                q=p.eq_presence_q,
            ),
            pb.HighShelfFilter(
                cutoff_frequency_hz=p.eq_air_hz,
                gain_db=p.eq_air_db,
            ),
        ])
        audio_pb = _to_pb(audio)
        audio_pb = additive_eq_board(audio_pb, sr)
        audio = _from_pb(audio_pb)

        # --- Phase 5: Saturation (tube warmth, after compression so peaks tamed first) ---
        if p.saturation_drive > 0:
            audio = dsp.tube_saturate(audio, p.saturation_drive, p.saturation_mix).astype(np.float32)

        # --- Phase 6: HF rolloff (tape bandwidth) ---
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

        # --- Phase 7: Reverb ---
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

        # --- Phase 7: Wow/flutter (tape time modulation) ---
        if p.flutter_rate_hz > 0:
            audio = dsp.wow_flutter(audio, sr, p.flutter_rate_hz, p.flutter_depth).astype(np.float32)

        # Output gain
        if p.output_gain_db != 0:
            audio = audio * dsp.db_to_linear(p.output_gain_db)

        return audio.astype(np.float32)


def _to_pb(audio: np.ndarray) -> np.ndarray:
    """Convert (samples, channels) to pedalboard's (channels, samples)."""
    if audio.ndim == 1:
        return audio[np.newaxis, :]
    return audio.T.copy()


def _from_pb(audio_pb: np.ndarray) -> np.ndarray:
    """Convert pedalboard's (channels, samples) back to (samples, channels)."""
    if audio_pb.shape[0] == 1:
        return audio_pb[0]
    return audio_pb.T.copy()
