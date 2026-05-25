from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from paulstretch_light.dsp import EffectSettings, QualityProfile
from paulstretch_light.renderer import PreviewConfig, RenderConfig, RenderOutputMode, render_preview, render_to_wav
from paulstretch_light.waveform import RegionSelection, build_waveform_overview


def test_render_to_wav_creates_float_wav_and_reports_status(tmp_path: Path) -> None:
    sample_rate = 22050
    t = np.linspace(0.0, 0.5, int(sample_rate * 0.5), endpoint=False)
    stereo = np.column_stack(
        [
            np.sin(2.0 * np.pi * 220.0 * t),
            np.sin(2.0 * np.pi * 440.0 * t),
        ]
    ).astype(np.float32)
    input_path = tmp_path / "input.wav"
    output_path = tmp_path / "output.wav"
    sf.write(str(input_path), stereo, sample_rate, subtype="FLOAT", format="WAV")

    statuses: list[tuple[float, str]] = []
    result = render_to_wav(
        RenderConfig(
            input_path=str(input_path),
            output_path=str(output_path),
            stretch_factor=3.0,
            region=RegionSelection(0.0, 0.5),
            quality_profile=QualityProfile.LOW,
            effects=EffectSettings(reverb_amount=0.25, lowpass_hz=5000.0, wet_dry=0.5),
            random_seed=42,
        ),
        status_callback=lambda status: statuses.append((status.progress, status.message)),
    )

    assert output_path.exists()
    rendered, rendered_sr = sf.read(str(output_path), always_2d=True, dtype="float32")
    assert rendered_sr == sample_rate
    assert rendered.shape[1] == 2
    assert rendered.shape[0] == result.output_frames
    assert result.channels == 2
    assert result.output_frames > result.input_frames
    assert result.output_paths == (str(output_path),)
    assert result.output_mode == RenderOutputMode.WET
    assert statuses
    assert statuses[-1][0] == 1.0


def test_render_to_wav_supports_dry_and_wet_outputs_from_one_render(tmp_path: Path) -> None:
    sample_rate = 22050
    t = np.linspace(0.0, 0.75, int(sample_rate * 0.75), endpoint=False)
    stereo = np.column_stack(
        [
            np.sin(2.0 * np.pi * 180.0 * t),
            np.sin(2.0 * np.pi * 360.0 * t),
        ]
    ).astype(np.float32)
    input_path = tmp_path / "input.wav"
    base_output_path = tmp_path / "stack.wav"
    sf.write(str(input_path), stereo, sample_rate, subtype="FLOAT", format="WAV")

    statuses: list[tuple[float, str]] = []
    result = render_to_wav(
        RenderConfig(
            input_path=str(input_path),
            output_path=str(base_output_path),
            output_mode=RenderOutputMode.DRY_WET,
            stretch_factor=2.5,
            region=RegionSelection(0.0, 0.75),
            quality_profile=QualityProfile.MEDIUM,
            effects=EffectSettings(reverb_amount=0.45, shimmer_amount=0.25, wet_dry=0.8),
            random_seed=7,
        ),
        status_callback=lambda status: statuses.append((status.progress, status.message)),
    )

    dry_path = tmp_path / "stack_dry.wav"
    wet_path = tmp_path / "stack_wet.wav"
    assert dry_path.exists()
    assert wet_path.exists()
    assert result.output_path == str(wet_path)
    assert result.output_paths == (str(dry_path), str(wet_path))
    assert result.output_mode == RenderOutputMode.DRY_WET
    dry_audio, dry_sr = sf.read(str(dry_path), always_2d=True, dtype="float32")
    wet_audio, wet_sr = sf.read(str(wet_path), always_2d=True, dtype="float32")
    assert dry_sr == sample_rate
    assert wet_sr == sample_rate
    assert dry_audio.shape == wet_audio.shape
    assert not np.allclose(dry_audio, wet_audio)
    assert any("Writing dry WAV" in message for _, message in statuses)
    assert any("Writing wet WAV" in message for _, message in statuses)


def test_render_preview_uses_requested_start_and_preserves_channels(tmp_path: Path) -> None:
    sample_rate = 24000
    t = np.linspace(0.0, 2.0, int(sample_rate * 2.0), endpoint=False)
    stereo = np.column_stack(
        [
            np.sin(2.0 * np.pi * 220.0 * t),
            np.sin(2.0 * np.pi * 330.0 * t),
        ]
    ).astype(np.float32)
    input_path = tmp_path / "preview_input.wav"
    sf.write(str(input_path), stereo, sample_rate, subtype="FLOAT", format="WAV")

    preview = render_preview(
        PreviewConfig(
            input_path=str(input_path),
            stretch_factor=2.0,
            region=RegionSelection(1.25, 1.75),
            quality_profile=QualityProfile.MEDIUM,
            effects=EffectSettings(reverb_amount=0.2, lowpass_hz=7000.0, wet_dry=0.6),
            random_seed=9,
        )
    )

    assert preview.channels == 2
    assert preview.audio.ndim == 2
    assert preview.audio.shape[1] == 2
    assert preview.preview_frames > 0
    assert np.max(np.abs(preview.audio)) > 0.05
    assert 1.2 <= preview.source_start_seconds <= 1.26


def test_render_preview_from_near_end_falls_back_to_short_segment(tmp_path: Path) -> None:
    sample_rate = 16000
    t = np.linspace(0.0, 1.0, int(sample_rate * 1.0), endpoint=False)
    mono = np.sin(2.0 * np.pi * 180.0 * t).astype(np.float32)
    input_path = tmp_path / "tail_input.wav"
    sf.write(str(input_path), mono, sample_rate, subtype="FLOAT", format="WAV")

    preview = render_preview(
        PreviewConfig(
            input_path=str(input_path),
            stretch_factor=2.0,
            region=RegionSelection(99.0, 100.0),
            quality_profile=QualityProfile.LOW,
            effects=EffectSettings(),
            random_seed=7,
        )
    )

    assert preview.preview_frames > 0
    assert preview.source_duration_seconds > 0.0


def test_render_preview_respects_requested_preview_source_duration(tmp_path: Path) -> None:
    sample_rate = 22050
    t = np.linspace(0.0, 3.0, int(sample_rate * 3.0), endpoint=False)
    mono = np.sin(2.0 * np.pi * 220.0 * t).astype(np.float32)
    input_path = tmp_path / "duration_input.wav"
    sf.write(str(input_path), mono, sample_rate, subtype="FLOAT", format="WAV")

    preview = render_preview(
        PreviewConfig(
            input_path=str(input_path),
            stretch_factor=2.0,
            region=RegionSelection(0.5, 1.25),
            preview_source_duration_seconds=0.75,
            quality_profile=QualityProfile.HIGH,
            effects=EffectSettings(),
            random_seed=5,
        )
    )

    assert 0.70 <= preview.source_duration_seconds <= 0.76
    assert preview.preview_frames > int(sample_rate * 0.75)


def test_render_preview_freeze_uses_selected_region(tmp_path: Path) -> None:
    sample_rate = 22050
    t = np.linspace(0.0, 1.5, int(sample_rate * 1.5), endpoint=False)
    stereo = np.column_stack([np.sin(2.0 * np.pi * 110.0 * t), np.sin(2.0 * np.pi * 220.0 * t)]).astype(np.float32)
    input_path = tmp_path / "freeze.wav"
    sf.write(str(input_path), stereo, sample_rate, subtype="FLOAT", format="WAV")

    preview = render_preview(
        PreviewConfig(
            input_path=str(input_path),
            stretch_factor=3.0,
            region=RegionSelection(0.25, 0.45),
            quality_profile=QualityProfile.MEDIUM,
            effects=EffectSettings(freeze_enabled=True, shimmer_amount=0.5, wet_dry=0.8),
            random_seed=12,
        )
    )

    assert preview.preview_frames > 0
    assert preview.source_duration_seconds <= 0.21
    assert np.max(np.abs(preview.audio)) > 0.05


def test_render_preview_supports_input_trim_and_safety_limiter(tmp_path: Path) -> None:
    sample_rate = 22050
    t = np.linspace(0.0, 1.0, int(sample_rate * 1.0), endpoint=False)
    mono = (0.08 * np.sin(2.0 * np.pi * 220.0 * t)).astype(np.float32)
    input_path = tmp_path / "trimmed.wav"
    sf.write(str(input_path), mono, sample_rate, subtype="FLOAT", format="WAV")

    plain = render_preview(
        PreviewConfig(
            input_path=str(input_path),
            stretch_factor=2.0,
            region=RegionSelection(0.0, 1.0),
            quality_profile=QualityProfile.LOW,
            effects=EffectSettings(drive_amount=0.45, wet_dry=1.0),
            random_seed=3,
        )
    )
    boosted_and_limited = render_preview(
        PreviewConfig(
            input_path=str(input_path),
            stretch_factor=2.0,
            region=RegionSelection(0.0, 1.0),
            quality_profile=QualityProfile.LOW,
            effects=EffectSettings(
                drive_amount=0.45,
                wet_dry=1.0,
                input_gain_db=12.0,
                limiter_enabled=True,
            ),
            random_seed=3,
        )
    )

    assert not np.allclose(plain.audio, boosted_and_limited.audio)
    assert np.max(np.abs(boosted_and_limited.audio)) <= 0.892


def test_build_waveform_overview_returns_expected_shape() -> None:
    sample_rate = 16000
    t = np.linspace(0.0, 1.0, sample_rate, endpoint=False)
    stereo = np.column_stack([np.sin(2.0 * np.pi * 100.0 * t), np.sin(2.0 * np.pi * 200.0 * t)]).astype(np.float32)
    overview = build_waveform_overview(stereo, sample_rate, bins=256)
    assert overview.min_peaks.shape == (2, 256)
    assert overview.max_peaks.shape == (2, 256)
    assert overview.duration_seconds == 1.0
