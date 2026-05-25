from __future__ import annotations

import numpy as np

from paulstretch_light.dsp import (
    EffectSettings,
    FilterMode,
    QualityProfile,
    SAFETY_LIMITER_CEILING_DB,
    StretchSettings,
    apply_autopan,
    apply_bloom,
    apply_chorus,
    apply_drive,
    apply_effects,
    apply_filter,
    apply_granular_smear,
    apply_input_gain,
    apply_motion,
    apply_pitch_drift,
    apply_safety_limiter,
    apply_shimmer,
    apply_stereo_width,
    apply_texture,
    build_loop_crossfade_audio,
    freeze_source,
    normalize_audio,
    paulstretch_audio,
    quality_settings,
    reverse_audio,
)


def test_normalize_audio_preserves_silence() -> None:
    silent = np.zeros(128, dtype=np.float64)
    normalized = normalize_audio(silent)
    assert np.array_equal(normalized, silent)


def test_paulstretch_audio_makes_output_longer_and_finite() -> None:
    sr = 48000
    duration = 0.6
    t = np.linspace(0.0, duration, int(sr * duration), endpoint=False)
    mono = np.sin(2.0 * np.pi * 220.0 * t)

    stretched = paulstretch_audio(
        mono,
        stretch_factor=4.0,
        settings=StretchSettings(window_size=2048, random_seed=1234),
    )

    assert stretched.shape[0] > mono.shape[0]
    assert np.isfinite(stretched).all()
    assert np.max(np.abs(stretched)) <= 0.981


def test_paulstretch_audio_preserves_stereo_channels() -> None:
    sr = 32000
    duration = 0.8
    t = np.linspace(0.0, duration, int(sr * duration), endpoint=False)
    stereo = np.column_stack(
        [
            np.sin(2.0 * np.pi * 110.0 * t),
            np.sin(2.0 * np.pi * 330.0 * t),
        ]
    )

    stretched = paulstretch_audio(
        stereo,
        stretch_factor=3.0,
        settings=StretchSettings(window_size=2048, random_seed=99),
    )

    assert stretched.ndim == 2
    assert stretched.shape[1] == 2
    assert stretched.shape[0] > stereo.shape[0]


def test_paulstretch_audio_reports_progress() -> None:
    sr = 24000
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    mono = np.sin(2.0 * np.pi * 180.0 * t)
    events: list[tuple[float, str]] = []

    stretched = paulstretch_audio(
        mono,
        stretch_factor=2.0,
        settings=StretchSettings(window_size=1024, random_seed=7),
        progress_callback=lambda progress, message: events.append((progress, message)),
    )

    assert stretched.shape[0] > mono.shape[0]
    assert events
    assert events[-1][0] >= 0.99
    assert any(message for _, message in events)


def test_quality_profiles_map_to_different_window_sizes() -> None:
    low = quality_settings(QualityProfile.LOW)
    medium = quality_settings(QualityProfile.MEDIUM)
    high = quality_settings(QualityProfile.HIGH)

    assert low.stretch.window_size < medium.stretch.window_size < high.stretch.window_size
    assert low.preview_source_seconds < medium.preview_source_seconds < high.preview_source_seconds


def test_apply_effects_wetdry_zero_keeps_dry_shape() -> None:
    sr = 22050
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 220.0 * t), np.sin(2.0 * np.pi * 440.0 * t)]
    )

    effected = apply_effects(
        stereo,
        sr,
        EffectSettings(reverb_amount=1.0, lowpass_hz=1000.0, wet_dry=0.0),
        random_seed=4,
    )

    expected = normalize_audio(stereo)
    assert effected.shape == stereo.shape
    assert np.allclose(effected, expected)


def test_default_effect_settings_are_neutral() -> None:
    sr = 22050
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 220.0 * t), np.sin(2.0 * np.pi * 440.0 * t)]
    )

    effected = apply_effects(stereo, sr, EffectSettings(), random_seed=4)

    expected = normalize_audio(stereo)
    assert effected.shape == stereo.shape
    assert np.allclose(effected, expected)


def test_apply_input_gain_uses_db_scaling() -> None:
    mono = np.array([0.1, -0.2, 0.3], dtype=np.float64)

    boosted = apply_input_gain(mono, 6.0)
    cut = apply_input_gain(mono, -6.0)

    assert np.allclose(boosted, mono * (10.0 ** (6.0 / 20.0)))
    assert np.allclose(cut, mono * (10.0 ** (-6.0 / 20.0)))


def test_apply_safety_limiter_softens_hot_peaks() -> None:
    mono = np.array([0.25, -0.5, 1.8, -2.2, 0.9], dtype=np.float64)

    limited = apply_safety_limiter(mono, ceiling_db=SAFETY_LIMITER_CEILING_DB)
    threshold = 10.0 ** (SAFETY_LIMITER_CEILING_DB / 20.0)

    assert limited.shape == mono.shape
    assert np.max(np.abs(limited)) <= threshold + 1e-6
    assert np.max(np.abs(limited)) < np.max(np.abs(mono))


def test_build_loop_crossfade_audio_adds_loop_tail_that_lands_near_start() -> None:
    sample_rate = 1000
    mono = np.linspace(-0.6, 0.8, 400, dtype=np.float64)

    looped = build_loop_crossfade_audio(mono, sample_rate, 80.0)

    assert looped.shape[0] > mono.shape[0]
    assert np.isclose(looped[-1], mono[0], atol=1e-6)


def test_disabled_effect_flags_are_ignored_in_processing() -> None:
    sr = 22050
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 220.0 * t), np.sin(2.0 * np.pi * 440.0 * t)]
    )

    effected = apply_effects(
        stereo,
        sr,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            filter_enabled=False,
            reverb_amount=0.6,
            reverb_enabled=False,
            drive_amount=0.5,
            drive_enabled=False,
            chorus_amount=0.4,
            chorus_enabled=False,
            wet_dry=1.0,
        ),
        random_seed=4,
    )

    expected = normalize_audio(stereo)
    assert np.allclose(effected, expected)


def test_reverse_audio_flips_time_axis() -> None:
    stereo = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])
    reversed_audio = reverse_audio(stereo)
    assert np.array_equal(reversed_audio, np.array([[3.0, 30.0], [2.0, 20.0], [1.0, 10.0]]))


def test_apply_stereo_width_zero_collapses_to_mid() -> None:
    stereo = np.array([[1.0, -1.0], [0.5, -0.5], [0.25, -0.25]])
    narrowed = apply_stereo_width(stereo, 0.0)
    assert narrowed.shape == stereo.shape
    assert np.allclose(narrowed[:, 0], narrowed[:, 1])


def test_apply_effects_reverse_and_delay_remain_finite() -> None:
    sr = 24000
    t = np.linspace(0.0, 0.75, int(sr * 0.75), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 180.0 * t), np.sin(2.0 * np.pi * 270.0 * t)]
    )

    effected = apply_effects(
        stereo,
        sr,
        EffectSettings(
            reverb_amount=0.5,
            lowpass_hz=3500.0,
            delay_amount=0.6,
            stereo_width=1.7,
            reverse=True,
            shimmer_amount=0.4,
            wet_dry=1.0,
        ),
        random_seed=11,
    )

    assert effected.shape == stereo.shape
    assert np.isfinite(effected).all()
    assert np.max(np.abs(effected)) <= 0.981


def test_freeze_source_extends_short_region() -> None:
    mono = np.linspace(-0.5, 0.5, 128)
    frozen = freeze_source(mono, 1024, random_seed=3)
    assert frozen.shape[0] == 1024
    assert np.isfinite(frozen).all()
    assert np.max(np.abs(frozen)) <= 0.981


def test_apply_shimmer_returns_finite_audio() -> None:
    sr = 22050
    t = np.linspace(0.0, 0.75, int(sr * 0.75), endpoint=False)
    mono = np.sin(2.0 * np.pi * 220.0 * t)
    shimmered = apply_shimmer(mono, sr, 0.8)
    assert shimmered.shape == mono.shape
    assert np.isfinite(shimmered).all()


def test_apply_filter_supports_highpass_and_bandpass() -> None:
    sr = 32000
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    mono = np.sin(2.0 * np.pi * 180.0 * t) + (0.35 * np.sin(2.0 * np.pi * 2600.0 * t))

    highpassed = apply_filter(mono, sr, FilterMode.HIGHPASS, 1000.0)
    bandpassed = apply_filter(mono, sr, FilterMode.BANDPASS, 1800.0)

    assert highpassed.shape == mono.shape
    assert bandpassed.shape == mono.shape
    assert np.isfinite(highpassed).all()
    assert np.isfinite(bandpassed).all()
    assert not np.allclose(highpassed, mono)
    assert not np.allclose(bandpassed, mono)


def test_new_effect_primitives_return_input_at_zero_amount() -> None:
    sr = 24000
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 220.0 * t), np.sin(2.0 * np.pi * 330.0 * t)]
    )

    assert np.allclose(apply_drive(stereo, 0.0), stereo)
    assert np.allclose(apply_chorus(stereo, sr, 0.0), stereo)
    assert np.allclose(apply_pitch_drift(stereo, sr, 0.0), stereo)
    assert np.allclose(apply_texture(stereo, sr, 0.0, random_seed=5), stereo)
    assert np.allclose(apply_granular_smear(stereo, sr, 0.0, random_seed=5), stereo)
    assert np.allclose(apply_bloom(stereo, sr, 0.0, random_seed=5), stereo)
    assert np.allclose(apply_motion(stereo, sr, 0.0), stereo)
    assert np.allclose(apply_autopan(stereo, sr, 0.0), stereo)


def test_new_effect_primitives_change_audio_when_enabled() -> None:
    sr = 24000
    t = np.linspace(0.0, 0.75, int(sr * 0.75), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 180.0 * t), np.sin(2.0 * np.pi * 270.0 * t)]
    )

    driven = apply_drive(stereo, 0.45)
    chorused = apply_chorus(stereo, sr, 0.5)
    drifted = apply_pitch_drift(stereo, sr, 0.35)
    textured = apply_texture(stereo, sr, 0.5, random_seed=9)
    granular = apply_granular_smear(stereo, sr, 0.55, random_seed=9)
    bloomed = apply_bloom(stereo, sr, 0.45, random_seed=9)
    moved = apply_motion(stereo, sr, 0.5)
    autopanned = apply_autopan(stereo, sr, 0.5)

    for effected in (driven, chorused, drifted, textured, granular, bloomed, moved, autopanned):
        assert effected.shape == stereo.shape
        assert np.isfinite(effected).all()
        assert np.max(np.abs(effected)) <= 0.981
        assert not np.allclose(effected, stereo)


def test_apply_autopan_promotes_mono_to_stereo() -> None:
    sr = 22050
    t = np.linspace(0.0, 0.5, int(sr * 0.5), endpoint=False)
    mono = np.sin(2.0 * np.pi * 220.0 * t)

    autopanned = apply_autopan(mono, sr, 0.65)

    assert autopanned.ndim == 2
    assert autopanned.shape == (mono.shape[0], 2)
    assert np.isfinite(autopanned).all()


def test_apply_effects_creative_chain_remains_finite() -> None:
    sr = 32000
    t = np.linspace(0.0, 0.8, int(sr * 0.8), endpoint=False)
    stereo = np.column_stack(
        [np.sin(2.0 * np.pi * 140.0 * t), np.sin(2.0 * np.pi * 280.0 * t)]
    )

    effected = apply_effects(
        stereo,
        sr,
        EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            lowpass_hz=2600.0,
            drive_amount=0.25,
            chorus_amount=0.35,
            texture_amount=0.32,
            motion_amount=0.28,
            pitch_drift_amount=0.2,
            bloom_amount=0.4,
            granular_amount=0.4,
            reverb_amount=0.3,
            shimmer_amount=0.2,
            delay_amount=0.2,
            autopan_amount=0.45,
            stereo_width=1.4,
            wet_dry=1.0,
        ),
        random_seed=17,
    )

    assert effected.shape == stereo.shape
    assert np.isfinite(effected).all()
    assert np.max(np.abs(effected)) <= 0.981
