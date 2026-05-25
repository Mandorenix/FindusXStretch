from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

import numpy as np

from .dsp import (
    EffectSettings,
    QualityProfile,
    SAFETY_LIMITER_CEILING_DB,
    apply_input_gain,
    freeze_source,
    normalize_audio,
    paulstretch_audio,
    quality_settings,
    apply_effects,
    apply_safety_limiter,
)
from .waveform import RegionSelection, WaveformOverview, build_waveform_overview

try:
    import soundfile as sf
except ImportError:  # pragma: no cover
    sf = None


class RenderOutputMode(str, Enum):
    WET = "wet"
    DRY = "dry"
    DRY_WET = "dry_wet"


@dataclass(frozen=True)
class ProcessConfig:
    input_path: str
    stretch_factor: float
    quality_profile: QualityProfile = QualityProfile.MEDIUM
    effects: EffectSettings = field(default_factory=EffectSettings)
    random_seed: int | None = None
    region: RegionSelection | None = None


@dataclass(frozen=True)
class RenderConfig(ProcessConfig):
    output_path: str = ""
    output_mode: RenderOutputMode = RenderOutputMode.WET


@dataclass(frozen=True)
class PreviewConfig(ProcessConfig):
    preview_source_duration_seconds: float | None = None


@dataclass(frozen=True)
class RenderResult:
    output_path: str
    output_paths: tuple[str, ...]
    output_mode: RenderOutputMode
    sample_rate: int
    channels: int
    input_frames: int
    output_frames: int
    stretch_factor: float


@dataclass(frozen=True)
class PreviewResult:
    audio: np.ndarray
    sample_rate: int
    channels: int
    preview_frames: int
    source_start_seconds: float
    source_duration_seconds: float
    stretch_factor: float


@dataclass(frozen=True)
class RenderStatus:
    progress: float
    message: str


StatusCallback = Callable[[RenderStatus], None]


def load_audio_file(input_path: str) -> tuple[np.ndarray, int]:
    if sf is None:
        raise RuntimeError(
            "Missing dependency: soundfile. Install requirements before rendering."
        )
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    try:
        return sf.read(str(path), always_2d=True, dtype="float32")
    except Exception as exc:
        raise RuntimeError(f"Could not read input audio: {exc}") from exc


def load_waveform_overview(input_path: str, bins: int = 1600) -> WaveformOverview:
    audio, sample_rate = load_audio_file(input_path)
    return build_waveform_overview(audio, sample_rate, bins=bins)


def render_to_wav(
    config: RenderConfig,
    status_callback: StatusCallback | None = None,
) -> RenderResult:
    if sf is None:
        raise RuntimeError(
            "Missing dependency: soundfile. Install requirements before rendering."
        )

    output_path = Path(config.output_path)
    if output_path.suffix.lower() != ".wav":
        raise ValueError("Output file must use the .wav extension.")

    mode = render_output_mode_from_value(config.output_mode)
    dry_processed, wet_processed, sample_rate, input_frames, _ = _render_variants(
        config,
        status_callback=status_callback,
        status_prefix="Export rendering",
    )
    output_targets = _resolve_output_targets(output_path, mode)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    written_paths: list[str] = []
    for index, (target_kind, target_path) in enumerate(output_targets, start=1):
        try:
            label = "dry" if target_kind == "dry" else "wet"
            progress = 0.97 if len(output_targets) == 1 else 0.94 + (0.03 * (index / len(output_targets)))
            _emit_status(status_callback, progress, f"Writing {label} WAV ({index}/{len(output_targets)})")
            sf.write(
                str(target_path),
                np.asarray(dry_processed if target_kind == "dry" else wet_processed, dtype=np.float32),
                sample_rate,
                subtype="FLOAT",
                format="WAV",
            )
            written_paths.append(str(target_path))
        except Exception as exc:
            raise RuntimeError(f"Could not write output WAV: {exc}") from exc

    channels = 1 if wet_processed.ndim == 1 else wet_processed.shape[1]
    _emit_status(status_callback, 1.0, "Export render complete")
    return RenderResult(
        output_path=_primary_output_path(output_targets),
        output_paths=tuple(written_paths),
        output_mode=mode,
        sample_rate=sample_rate,
        channels=channels,
        input_frames=input_frames,
        output_frames=wet_processed.shape[0],
        stretch_factor=config.stretch_factor,
    )


def render_preview(
    config: PreviewConfig,
    status_callback: StatusCallback | None = None,
) -> PreviewResult:
    _, processed, sample_rate, _, segment_info = _render_variants(
        config,
        status_callback=status_callback,
        status_prefix="Preview rendering",
    )
    channels = 1 if processed.ndim == 1 else processed.shape[1]
    _emit_status(status_callback, 1.0, "Preview render complete")
    return PreviewResult(
        audio=np.asarray(processed, dtype=np.float32),
        sample_rate=sample_rate,
        channels=channels,
        preview_frames=processed.shape[0],
        source_start_seconds=segment_info[0],
        source_duration_seconds=segment_info[1],
        stretch_factor=config.stretch_factor,
    )


def process_audio(
    config: ProcessConfig,
    status_callback: StatusCallback | None = None,
    status_prefix: str = "Rendering",
) -> tuple[np.ndarray, int, int, tuple[float, float]]:
    _, processed, sample_rate, input_frames, segment_info = _render_variants(
        config,
        status_callback=status_callback,
        status_prefix=status_prefix,
    )
    return processed, sample_rate, input_frames, segment_info


def _render_variants(
    config: ProcessConfig,
    status_callback: StatusCallback | None = None,
    status_prefix: str = "Rendering",
) -> tuple[np.ndarray, np.ndarray, int, int, tuple[float, float]]:
    input_path = Path(config.input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if config.stretch_factor <= 1.0:
        raise ValueError("Stretch factor must be greater than 1.0.")

    _emit_status(status_callback, 0.02, f"{status_prefix}: loading audio")
    audio, sample_rate = load_audio_file(config.input_path)
    if audio.size == 0:
        raise ValueError("Input audio file contains no samples.")

    profile = quality_settings(config.quality_profile, random_seed=config.random_seed)
    source_audio, start_seconds, duration_seconds = _segment_audio(
        audio, sample_rate, config, profile.preview_source_seconds
    )

    if abs(config.effects.input_gain_db) > 1e-9:
        _emit_status(status_callback, 0.04, f"{status_prefix}: applying input trim")
        source_audio = apply_input_gain(source_audio, config.effects.input_gain_db)

    if config.effects.freeze_enabled:
        _emit_status(status_callback, 0.05, f"{status_prefix}: building freeze source")
        freeze_target = max(
            profile.stretch.window_size * 4,
            int(sample_rate * max(duration_seconds * 3.0, profile.preview_source_seconds * 2.0)),
        )
        source_audio = freeze_source(source_audio, freeze_target, random_seed=config.random_seed)

    _emit_status(status_callback, 0.08, f"{status_prefix}: stretching audio")
    stretched = paulstretch_audio(
        source_audio,
        config.stretch_factor,
        settings=profile.stretch,
        progress_callback=lambda progress, message: _emit_status(
            status_callback,
            0.08 + (0.74 * progress),
            f"{status_prefix}: {message}",
        ),
    )

    dry = np.asarray(stretched, dtype=np.float64)
    _emit_status(status_callback, 0.85, f"{status_prefix}: applying effects")
    wet = apply_effects(
        stretched,
        sample_rate,
        config.effects,
        random_seed=config.random_seed,
        normalize_output=False,
    )
    clip_level = profile.stretch.fade_clip
    if config.effects.limiter_enabled:
        _emit_status(status_callback, 0.91, f"{status_prefix}: applying safety limiter")
        dry = apply_safety_limiter(dry, ceiling_db=SAFETY_LIMITER_CEILING_DB)
        wet = apply_safety_limiter(wet, ceiling_db=SAFETY_LIMITER_CEILING_DB)
        clip_level = min(profile.stretch.fade_clip, 10.0 ** (SAFETY_LIMITER_CEILING_DB / 20.0))
    dry = normalize_audio(dry, clip_level=clip_level)
    wet = normalize_audio(wet, clip_level=clip_level)
    return dry, wet, sample_rate, audio.shape[0], (start_seconds, duration_seconds)


def _segment_audio(
    audio: np.ndarray,
    sample_rate: int,
    config: ProcessConfig,
    default_preview_duration: float,
) -> tuple[np.ndarray, float, float]:
    total_seconds = audio.shape[0] / sample_rate
    if config.region is not None:
        start_seconds = max(0.0, min(config.region.start_seconds, total_seconds))
        end_seconds = max(start_seconds + 0.01, min(config.region.end_seconds, total_seconds))
        start_frame = int(start_seconds * sample_rate)
        end_frame = min(audio.shape[0], int(end_seconds * sample_rate))
        segment = audio[start_frame:end_frame]
        if segment.shape[0] == 0:
            segment = audio[: max(1, int(default_preview_duration * sample_rate))]
            return segment, 0.0, segment.shape[0] / sample_rate
        return segment, start_seconds, segment.shape[0] / sample_rate

    if isinstance(config, PreviewConfig):
        duration_seconds = config.preview_source_duration_seconds or default_preview_duration
        end_frame = min(audio.shape[0], max(1, int(duration_seconds * sample_rate)))
        segment = audio[:end_frame]
        return segment, 0.0, segment.shape[0] / sample_rate

    return audio, 0.0, audio.shape[0] / sample_rate


def _emit_status(
    callback: StatusCallback | None,
    progress: float,
    message: str,
) -> None:
    if callback is None:
        return
    callback(RenderStatus(progress=max(0.0, min(1.0, progress)), message=message))


def render_output_mode_from_value(value: object) -> RenderOutputMode:
    if isinstance(value, RenderOutputMode):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for mode in RenderOutputMode:
            if mode.value == normalized:
                return mode
    return RenderOutputMode.WET


def _resolve_output_targets(
    output_path: Path,
    mode: RenderOutputMode,
) -> tuple[tuple[str, Path], ...]:
    if mode == RenderOutputMode.DRY:
        return (("dry", output_path),)
    if mode == RenderOutputMode.DRY_WET:
        return (
            ("dry", output_path.with_name(f"{output_path.stem}_dry.wav")),
            ("wet", output_path.with_name(f"{output_path.stem}_wet.wav")),
        )
    return (("wet", output_path),)


def _primary_output_path(output_targets: tuple[tuple[str, Path], ...]) -> str:
    for target_kind, target_path in output_targets:
        if target_kind == "wet":
            return str(target_path)
    return str(output_targets[0][1])
