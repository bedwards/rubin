"""
Lo-fi preset: degraded, nostalgic, cassette/vinyl character.
Heavy saturation, noise, bandwidth limiting, wow/flutter.
Targets -16 LUFS / -2.0 dBTP (lo-fi sounds better less maximized).
"""
from .base import VocalPreset, GuitarPreset, MasterPreset

LOFI_VOCAL = VocalPreset(
    input_gain_db=0.0,
    hpf_hz=150.0,             # Narrower, telephone-adjacent
    deess_freq_hz=6000.0,
    deess_threshold_db=-8.0,    # Lo-fi: slightly more aggressive de-essing
    deess_ratio=3.0,
    deess_attack_ms=3.0,
    deess_release_ms=100.0,
    eq_lo_shelf_hz=300.0,
    eq_lo_shelf_db=3.0,       # Heavy low-mid push
    eq_lo_mid_hz=500.0,
    eq_lo_mid_db=2.0,         # Mid presence
    eq_lo_mid_q=0.8,
    eq_presence_hz=2500.0,
    eq_presence_db=1.0,
    eq_presence_q=1.2,
    eq_air_hz=8000.0,
    eq_air_db=-3.0,           # Roll off the air
    saturation_drive=0.40,    # Heavy saturation
    saturation_mix=0.75,
    comp_threshold_db=-10.0,   # Lo-fi: squash loud peaks hard
    comp_ratio=5.0,           # More aggressive = lo-fi squashed character
    comp_attack_ms=3.0,
    comp_release_ms=60.0,
    comp_makeup_db=3.5,
    reverb_room_size=0.25,    # Intimate, lo-fi room
    reverb_damping=0.80,
    reverb_wet=0.20,
    reverb_predelay_ms=8.0,
    reverb_width=0.60,
    hf_rolloff_hz=10000.0,    # Heavy HF rolloff
    hf_rolloff_db=-8.0,
    flutter_rate_hz=2.0,      # Audible wow/flutter
    flutter_depth=0.004,
    output_gain_db=0.0,
)

LOFI_GUITAR = GuitarPreset(
    input_gain_db=0.0,
    hpf_hz=200.0,             # Heavy HPF
    eq_mud_hz=300.0,
    eq_mud_db=2.0,            # Lo-fi: accentuate the mud slightly
    eq_mud_q=1.0,
    eq_presence_hz=2000.0,
    eq_presence_db=1.5,
    eq_presence_q=1.0,
    eq_sparkle_hz=6000.0,
    eq_sparkle_db=-2.0,       # Roll off sparkle
    saturation_drive=0.45,
    saturation_mix=0.80,
    comp_threshold_db=-12.0,   # Lo-fi guitar: squash the peaks
    comp_ratio=4.0,
    comp_attack_ms=6.0,
    comp_release_ms=80.0,
    comp_makeup_db=2.5,
    reverb_room_size=0.20,
    reverb_damping=0.85,
    reverb_wet=0.18,
    reverb_predelay_ms=6.0,
    reverb_width=0.45,
    hf_rolloff_hz=9000.0,
    hf_rolloff_db=-10.0,
    flutter_rate_hz=1.5,
    flutter_depth=0.005,
    lofi_sample_rate=22050,   # Sample rate reduction
    lofi_bit_depth=12,        # Bit crush
    lofi_noise_level=0.008,   # Noise floor
    output_gain_db=0.0,
)

LOFI_MASTER = MasterPreset(
    vocal_level_db=1.0,       # Vocal forward in lo-fi
    guitar_level_db=-2.5,
    stereo_width=0.85,        # Slightly narrower = more mono = lo-fi
    master_eq_lo_shelf_hz=80.0,
    master_eq_lo_shelf_db=2.0,
    master_eq_hi_shelf_hz=7000.0,
    master_eq_hi_shelf_db=-2.0,
    glue_comp_threshold_db=-12.0,
    glue_comp_ratio=2.5,
    glue_comp_attack_ms=25.0,
    glue_comp_release_ms=180.0,
    glue_comp_makeup_db=2.5,
    master_saturation_drive=0.25,
    master_saturation_mix=0.55,
    master_hf_rolloff_hz=12000.0,
    master_hf_rolloff_db=-4.0,
    master_lofi_sample_rate=32000,   # Slight global sample rate reduction
    master_vinyl_noise_level=0.004,  # Vinyl crackle/hiss
    limiter_true_peak_db=-3.0,    # Extra headroom for lo-fi encoder artifacts
    target_lufs=-16.0,            # Less maximized = more lo-fi dynamics
    output_bit_depth=16,      # 16-bit output for extra lo-fi character
    output_sample_rate=44100,
)
