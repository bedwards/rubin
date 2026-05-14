from enum import Enum
from pydantic import BaseModel, Field


class PresetStyle(str, Enum):
    ANALOG_CONSOLE = "analog_console"
    TAPE = "tape"
    LOFI = "lofi"


class VocalPreset(BaseModel):
    # Gain staging
    input_gain_db: float = 0.0

    # High-pass filter
    hpf_hz: float = 80.0

    # De-essing: frequency center and threshold
    deess_freq_hz: float = 7500.0
    deess_threshold_db: float = -18.0
    deess_ratio: float = 6.0
    deess_attack_ms: float = 1.0
    deess_release_ms: float = 50.0

    # Pre-compression EQ (shelves and bells)
    eq_lo_shelf_hz: float = 200.0
    eq_lo_shelf_db: float = 0.0
    eq_lo_mid_hz: float = 400.0
    eq_lo_mid_db: float = 0.0
    eq_lo_mid_q: float = 1.0
    eq_presence_hz: float = 3000.0
    eq_presence_db: float = 0.0
    eq_presence_q: float = 1.0
    eq_air_hz: float = 12000.0
    eq_air_db: float = 0.0

    # Saturation (tube/tape)
    saturation_drive: float = 0.0    # 0-1 normalized
    saturation_mix: float = 0.5

    # Compressor
    comp_threshold_db: float = -18.0
    comp_ratio: float = 3.0
    comp_attack_ms: float = 10.0
    comp_release_ms: float = 80.0
    comp_makeup_db: float = 3.0

    # Reverb
    reverb_room_size: float = 0.4
    reverb_damping: float = 0.6
    reverb_wet: float = 0.15
    reverb_predelay_ms: float = 20.0
    reverb_width: float = 0.8

    # High-frequency shelf rolloff (for tape)
    hf_rolloff_hz: float = 0.0       # 0 = disabled
    hf_rolloff_db: float = -3.0

    # Tape wow/flutter
    flutter_rate_hz: float = 0.0     # 0 = disabled
    flutter_depth: float = 0.002

    # Output gain
    output_gain_db: float = 0.0


class GuitarPreset(BaseModel):
    input_gain_db: float = 0.0

    hpf_hz: float = 60.0

    eq_mud_hz: float = 250.0
    eq_mud_db: float = 0.0
    eq_mud_q: float = 1.5
    eq_presence_hz: float = 2500.0
    eq_presence_db: float = 0.0
    eq_presence_q: float = 1.0
    eq_sparkle_hz: float = 8000.0
    eq_sparkle_db: float = 0.0

    saturation_drive: float = 0.0
    saturation_mix: float = 0.5

    comp_threshold_db: float = -18.0
    comp_ratio: float = 2.0
    comp_attack_ms: float = 20.0
    comp_release_ms: float = 150.0
    comp_makeup_db: float = 2.0

    reverb_room_size: float = 0.3
    reverb_damping: float = 0.7
    reverb_wet: float = 0.12
    reverb_predelay_ms: float = 15.0
    reverb_width: float = 0.6

    hf_rolloff_hz: float = 0.0
    hf_rolloff_db: float = -3.0

    flutter_rate_hz: float = 0.0
    flutter_depth: float = 0.002

    # Lo-fi degradation
    lofi_sample_rate: int = 0       # 0 = disabled
    lofi_bit_depth: int = 0         # 0 = disabled
    lofi_noise_level: float = 0.0   # 0 = disabled

    output_gain_db: float = 0.0


class MasterPreset(BaseModel):
    # Stem mix levels (relative dB)
    vocal_level_db: float = 0.0
    guitar_level_db: float = 0.0

    # Stereo width (mid/side)
    stereo_width: float = 1.0       # 1.0 = no change, >1 = wider, <1 = narrower

    # Global EQ
    master_eq_lo_shelf_hz: float = 80.0
    master_eq_lo_shelf_db: float = 0.0
    master_eq_hi_shelf_hz: float = 10000.0
    master_eq_hi_shelf_db: float = 0.0

    # Glue compression
    glue_comp_threshold_db: float = -12.0
    glue_comp_ratio: float = 1.5
    glue_comp_attack_ms: float = 30.0
    glue_comp_release_ms: float = 200.0
    glue_comp_makeup_db: float = 1.5

    # Master saturation (2nd order harmonics for "life")
    master_saturation_drive: float = 0.0
    master_saturation_mix: float = 0.3

    # Global tape/lofi
    master_hf_rolloff_hz: float = 0.0
    master_hf_rolloff_db: float = -3.0
    master_lofi_sample_rate: int = 0
    master_vinyl_noise_level: float = 0.0

    # Limiter + LUFS targets
    limiter_true_peak_db: float = -2.0
    target_lufs: float = -14.0
    target_lufs_tolerance: float = 0.5

    # Output format
    output_bit_depth: int = 24
    output_sample_rate: int = 44100
