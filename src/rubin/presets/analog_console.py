"""
Analog console preset: SSL/Neve-inspired warm and clear processing.
Targets -14 LUFS / -1.0 dBTP for streaming.
"""
from .base import VocalPreset, GuitarPreset, MasterPreset

ANALOG_CONSOLE_VOCAL = VocalPreset(
    input_gain_db=0.0,
    hpf_hz=90.0,
    deess_freq_hz=7200.0,
    deess_threshold_db=-10.0,   # Raw signal peaks at -1dBFS; de-ess only loud sibilants
    deess_ratio=5.0,
    deess_attack_ms=1.0,
    deess_release_ms=81.0,
    eq_lo_shelf_hz=200.0,
    eq_lo_shelf_db=1.5,       # Warmth boost
    eq_lo_mid_hz=450.0,
    eq_lo_mid_db=-1.5,        # Cut boxiness
    eq_lo_mid_q=1.2,
    eq_presence_hz=3500.0,
    eq_presence_db=2.5,       # Presence and clarity
    eq_presence_q=0.9,
    eq_air_hz=12000.0,
    eq_air_db=2.0,            # Air/shimmer
    saturation_drive=0.12,    # Light tube warmth
    saturation_mix=0.4,
    # Stage 1: fast FET, catches loud peaks only (raw signal peaks ~-1 dBFS)
    comp_threshold_db=-10.0,
    comp_ratio=4.0,
    comp_attack_ms=5.0,
    comp_release_ms=60.0,
    comp_makeup_db=3.0,
    # Stage 2: optical, transparent gain riding
    comp2_threshold_db=-16.0,
    comp2_ratio=1.8,
    comp2_attack_ms=40.0,
    comp2_release_ms=220.0,
    comp2_makeup_db=1.0,
    reverb_room_size=0.45,    # Plate-like medium room
    reverb_damping=0.65,
    reverb_wet=0.10,          # Reduced: less reverb tail filling quiet spaces
    reverb_predelay_ms=18.0,
    reverb_width=0.85,
    output_gain_db=0.0,
)

ANALOG_CONSOLE_GUITAR = GuitarPreset(
    input_gain_db=0.0,
    hpf_hz=65.0,
    eq_mud_hz=220.0,
    eq_mud_db=-2.0,           # Cut mud
    eq_mud_q=1.4,
    eq_presence_hz=4000.0,    # 4kHz presence per research
    eq_presence_db=2.0,
    eq_presence_q=0.9,
    eq_sparkle_hz=7000.0,     # 7kHz sparkle per research
    eq_sparkle_db=2.5,
    saturation_drive=0.08,    # Very light console coloring
    saturation_mix=0.35,
    comp_threshold_db=-12.0,   # Catches peaks in raw -1dBFS signal
    comp_ratio=4.0,
    comp_attack_ms=12.0,
    comp_release_ms=120.0,
    comp_makeup_db=2.0,
    reverb_room_size=0.07,    # Very short room per research (50ms-ish)
    reverb_damping=0.88,      # Highly damped = darker, shorter
    reverb_wet=0.38,          # 40% wet per research
    reverb_predelay_ms=8.0,
    reverb_width=0.55,
    output_gain_db=0.0,
)

ANALOG_CONSOLE_MASTER = MasterPreset(
    vocal_level_db=0.0,
    guitar_level_db=-1.5,     # Guitar slightly below vocal
    stereo_width=1.05,
    master_eq_lo_shelf_hz=80.0,
    master_eq_lo_shelf_db=0.5,
    master_eq_hi_shelf_hz=10000.0,
    master_eq_hi_shelf_db=0.8,
    glue_comp_threshold_db=-6.0,    # Mixed signal peaks around -6 dBFS
    glue_comp_ratio=1.3,
    glue_comp_attack_ms=50.0,
    glue_comp_release_ms=400.0,
    glue_comp_makeup_db=0.5,
    master_saturation_drive=0.06,
    master_saturation_mix=0.25,
    limiter_true_peak_db=-2.0,
    target_lufs=-14.0,
    output_bit_depth=24,
    output_sample_rate=44100,
)
