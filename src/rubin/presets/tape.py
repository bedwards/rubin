"""
Tape preset: analog tape machine character.
Warmth, saturation, HF rolloff, subtle compression artifacts.
Targets -14 LUFS / -1.0 dBTP.
"""
from .base import VocalPreset, GuitarPreset, MasterPreset

TAPE_VOCAL = VocalPreset(
    input_gain_db=0.0,
    hpf_hz=100.0,
    deess_freq_hz=6800.0,
    deess_threshold_db=-14.0,
    deess_ratio=4.0,
    deess_attack_ms=2.0,
    deess_release_ms=80.0,
    eq_lo_shelf_hz=180.0,
    eq_lo_shelf_db=2.0,       # Tape warmth
    eq_lo_mid_hz=350.0,
    eq_lo_mid_db=-1.0,
    eq_lo_mid_q=1.0,
    eq_presence_hz=3000.0,
    eq_presence_db=1.5,
    eq_presence_q=1.0,
    eq_air_hz=10000.0,
    eq_air_db=-0.5,           # Slight HF dip before rolloff
    saturation_drive=0.22,    # Tape saturation
    saturation_mix=0.6,
    comp_threshold_db=-18.0,
    comp_ratio=4.0,
    comp_attack_ms=4.0,       # Fast tape-like response
    comp_release_ms=90.0,
    comp_makeup_db=4.5,
    reverb_room_size=0.40,
    reverb_damping=0.70,
    reverb_wet=0.16,
    reverb_predelay_ms=22.0,
    reverb_width=0.75,
    hf_rolloff_hz=14000.0,    # Tape bandwidth limit
    hf_rolloff_db=-4.0,
    flutter_rate_hz=0.8,      # Subtle wow/flutter
    flutter_depth=0.0018,
    output_gain_db=0.0,
)

TAPE_GUITAR = GuitarPreset(
    input_gain_db=0.0,
    hpf_hz=85.0,
    eq_mud_hz=200.0,
    eq_mud_db=-1.5,
    eq_mud_q=1.3,
    eq_presence_hz=2500.0,
    eq_presence_db=2.0,
    eq_presence_q=0.85,
    eq_sparkle_hz=8000.0,
    eq_sparkle_db=0.5,
    saturation_drive=0.28,    # Stronger tape saturation on guitar
    saturation_mix=0.65,
    comp_threshold_db=-20.0,
    comp_ratio=3.0,
    comp_attack_ms=12.0,
    comp_release_ms=130.0,
    comp_makeup_db=3.5,
    reverb_room_size=0.32,
    reverb_damping=0.75,
    reverb_wet=0.13,
    reverb_predelay_ms=16.0,
    reverb_width=0.50,
    hf_rolloff_hz=13000.0,
    hf_rolloff_db=-5.0,
    flutter_rate_hz=0.6,
    flutter_depth=0.0022,
    output_gain_db=0.0,
)

TAPE_MASTER = MasterPreset(
    vocal_level_db=0.0,
    guitar_level_db=-2.0,
    stereo_width=1.0,
    master_eq_lo_shelf_hz=80.0,
    master_eq_lo_shelf_db=1.0,       # Low-end warmth on tape
    master_eq_hi_shelf_hz=8000.0,
    master_eq_hi_shelf_db=-0.5,
    glue_comp_threshold_db=-12.0,
    glue_comp_ratio=2.0,
    glue_comp_attack_ms=40.0,
    glue_comp_release_ms=300.0,
    glue_comp_makeup_db=2.0,
    master_saturation_drive=0.15,    # Global tape saturation
    master_saturation_mix=0.40,
    master_hf_rolloff_hz=16000.0,    # Gentle global tape rolloff
    master_hf_rolloff_db=-2.5,
    limiter_true_peak_db=-2.0,
    target_lufs=-14.0,
    output_bit_depth=24,
    output_sample_rate=44100,
)
