"""Main mastering engine: orchestrates stem chains and output."""

import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf

from .chains import VocalChain, GuitarChain, MasterChain
from .presets.base import PresetStyle, VocalPreset, GuitarPreset, MasterPreset
from .presets import (
    ANALOG_CONSOLE_VOCAL, ANALOG_CONSOLE_GUITAR, ANALOG_CONSOLE_MASTER,
    TAPE_VOCAL, TAPE_GUITAR, TAPE_MASTER,
    LOFI_VOCAL, LOFI_GUITAR, LOFI_MASTER,
)

PRESETS: dict[PresetStyle, tuple[VocalPreset, GuitarPreset, MasterPreset]] = {
    PresetStyle.ANALOG_CONSOLE: (ANALOG_CONSOLE_VOCAL, ANALOG_CONSOLE_GUITAR, ANALOG_CONSOLE_MASTER),
    PresetStyle.TAPE: (TAPE_VOCAL, TAPE_GUITAR, TAPE_MASTER),
    PresetStyle.LOFI: (LOFI_VOCAL, LOFI_GUITAR, LOFI_MASTER),
}


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load audio file, always return float32."""
    audio, sr = sf.read(str(path), dtype="float32", always_2d=True)
    return audio, sr


def save_audio(audio: np.ndarray, sr: int, path: Path, bit_depth: int = 24) -> None:
    """Save audio with appropriate bit depth and format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subtype_map = {16: "PCM_16", 24: "PCM_24", 32: "PCM_32"}
    subtype = subtype_map.get(bit_depth, "PCM_24")
    audio_clipped = np.clip(audio, -1.0, 1.0)
    sf.write(str(path), audio_clipped, sr, subtype=subtype)


_STYLE_LABELS = {
    "analog_console": "Analog Console",
    "tape": "Tape",
    "lofi": "Lo-Fi",
}


def encode_masters(
    wav_path: Path,
    song_dir: Path,
    style: str,
    song_title: str = "",
    artist: str = "",
) -> list[Path]:
    """Encode WAV master to MP3/M4A/FLAC with metadata tags via ffmpeg."""
    outputs = []
    base = song_dir / "masters" / f"{style}"

    comment = f"Mastered by Rubin | Style: {_STYLE_LABELS.get(style, style)}"
    meta_args = []
    if song_title:
        meta_args += ["-metadata", f"title={song_title}"]
    if artist:
        meta_args += ["-metadata", f"artist={artist}"]
    meta_args += ["-metadata", f"comment={comment}"]
    meta_args += ["-metadata", f"album_artist=Rubin Mastering"]

    # 320k MP3
    mp3_path = base.with_suffix(".mp3")
    mp3_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-codec:a", "libmp3lame", "-b:a", "320k",
        "-id3v2_version", "3",
        *meta_args,
        str(mp3_path)
    ], check=True, capture_output=True)
    outputs.append(mp3_path)

    # AAC/M4A for Apple (256k)
    m4a_path = base.with_suffix(".m4a")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-codec:a", "aac", "-b:a", "256k",
        *meta_args,
        str(m4a_path)
    ], check=True, capture_output=True)
    outputs.append(m4a_path)

    # FLAC lossless
    flac_path = base.with_suffix(".flac")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(wav_path),
        "-codec:a", "flac",
        *meta_args,
        str(flac_path)
    ], check=True, capture_output=True)
    outputs.append(flac_path)

    return outputs


def _process_style(
    style: PresetStyle,
    vocal_path: Path,
    guitar_path: Path,
    song_dir: Path,
    song_title: str,
    artist: str,
    vocal_preset_overrides: Optional[dict],
    guitar_preset_overrides: Optional[dict],
    master_preset_overrides: Optional[dict],
) -> tuple[str, dict]:
    """Process one style. Returns (style_name, result_dict). Runs in worker.

    Each worker loads its own audio to avoid pickling large arrays over IPC.
    """
    vocal_preset, guitar_preset, master_preset = PRESETS[style]

    if vocal_preset_overrides:
        vocal_preset = vocal_preset.model_copy(update=vocal_preset_overrides)
    if guitar_preset_overrides:
        guitar_preset = guitar_preset.model_copy(update=guitar_preset_overrides)
    if master_preset_overrides:
        master_preset = master_preset.model_copy(update=master_preset_overrides)

    style_name = style.value

    vocal_raw, vocal_sr = load_audio(vocal_path)
    guitar_raw, guitar_sr = load_audio(guitar_path)
    sr = vocal_sr
    if vocal_sr != guitar_sr:
        from scipy import signal as sp
        ratio = vocal_sr / guitar_sr
        new_len = int(round(guitar_raw.shape[0] * ratio))
        guitar_raw = sp.resample(guitar_raw, new_len).astype(np.float32)

    vocal_processed = VocalChain(vocal_preset).process(vocal_raw, sr)
    guitar_processed = GuitarChain(guitar_preset).process(guitar_raw, sr)

    stems_dir = song_dir / "stems" / style_name
    vocal_stem_path = stems_dir / "01_vocals_processed.wav"
    guitar_stem_path = stems_dir / "02_guitar_processed.wav"
    save_audio(vocal_processed, sr, vocal_stem_path, bit_depth=32)
    save_audio(guitar_processed, sr, guitar_stem_path, bit_depth=32)

    mix_dir = song_dir / "mixes"
    pre_master_path = mix_dir / f"{style_name}_pre_master.wav"
    premix = np.clip(vocal_processed + guitar_processed, -1, 1)
    save_audio(premix, sr, pre_master_path, bit_depth=32)

    mix, stats = MasterChain(master_preset).process(vocal_processed, guitar_processed, sr)

    if master_preset.output_sample_rate != sr:
        from scipy import signal as sp
        ratio = master_preset.output_sample_rate / sr
        new_len = int(round(mix.shape[0] * ratio))
        mix = sp.resample(mix, new_len).astype(np.float32)
        out_sr = master_preset.output_sample_rate
    else:
        out_sr = sr

    masters_dir = song_dir / "masters"
    master_wav = masters_dir / f"{style_name}_master.wav"
    save_audio(mix, out_sr, master_wav, bit_depth=master_preset.output_bit_depth)

    encoded = encode_masters(master_wav, song_dir, style_name, song_title=song_title, artist=artist)

    return style_name, {
        "stats": stats,
        "stems": {"vocal": vocal_stem_path, "guitar": guitar_stem_path},
        "pre_master": pre_master_path,
        "master_wav": master_wav,
        "encoded": encoded,
    }


def process_song(
    vocal_path: Path,
    guitar_path: Path,
    song_dir: Path,
    styles: Optional[list[PresetStyle]] = None,
    vocal_preset_overrides: Optional[dict] = None,
    guitar_preset_overrides: Optional[dict] = None,
    master_preset_overrides: Optional[dict] = None,
    song_title: str = "",
    artist: str = "",
    parallel: bool = True,
) -> dict:
    """Process a song through all (or selected) mastering chains.

    Returns dict of {style: {paths, stats}}.
    Uses parallel workers (one per style) when parallel=True.
    """
    if styles is None:
        styles = list(PresetStyle)

    # Infer song title from directory name if not provided
    if not song_title:
        song_title = song_dir.name

    results = {}

    shared_kwargs = dict(
        vocal_path=vocal_path,
        guitar_path=guitar_path,
        song_dir=song_dir,
        song_title=song_title,
        artist=artist,
        vocal_preset_overrides=vocal_preset_overrides,
        guitar_preset_overrides=guitar_preset_overrides,
        master_preset_overrides=master_preset_overrides,
    )

    if parallel and len(styles) > 1:
        # Process styles in parallel — pedalboard releases the GIL, so
        # ProcessPoolExecutor gives true parallelism on multi-core hardware.
        with ProcessPoolExecutor(max_workers=len(styles)) as pool:
            futures = {
                pool.submit(_process_style, style, **shared_kwargs): style
                for style in styles
            }
            for fut in as_completed(futures):
                style_name, result = fut.result()
                results[style_name] = result
    else:
        for style in styles:
            style_name, result = _process_style(style, **shared_kwargs)
            results[style_name] = result

    return results
