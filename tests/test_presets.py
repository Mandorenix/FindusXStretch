from __future__ import annotations

import json
from pathlib import Path

from paulstretch_light.dsp import EffectSettings, FilterMode, QualityProfile
from paulstretch_light.preset_library import AppPreset, AppState, CompareSlotState, PresetLibrary, ProjectSession, QueuedRenderJob
from paulstretch_light.recording import RecentTake


def test_preset_library_roundtrip_user_preset(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    preset = AppPreset(
        name="My Drone",
        stretch_factor=12.0,
        quality_profile=QualityProfile.HIGH,
        preview_length=4.0,
        effects=EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            reverb_amount=0.7,
            drive_amount=0.22,
            drive_enabled=False,
            chorus_amount=0.35,
            texture_amount=0.28,
            motion_amount=0.17,
            pitch_drift_amount=0.14,
            bloom_amount=0.3,
            granular_amount=0.28,
            granular_enabled=False,
            autopan_amount=0.18,
            shimmer_amount=0.5,
            freeze_enabled=True,
        ),
        factory=False,
        tags=("dark", "ambient"),
        favorite=True,
    )

    library.save_user_preset(preset)
    loaded = library.get_preset("My Drone")

    assert loaded is not None
    assert not loaded.factory
    assert loaded.effects.freeze_enabled
    assert loaded.effects.filter_mode == FilterMode.BANDPASS
    assert loaded.effects.drive_amount == 0.22
    assert not loaded.effects.drive_enabled
    assert loaded.effects.texture_amount == 0.28
    assert loaded.effects.shimmer_amount == 0.5
    assert not loaded.effects.granular_enabled
    assert loaded.tags == ("dark", "ambient")
    assert loaded.favorite is True


def test_preset_library_state_roundtrip(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    state_path = tmp_path / "state.json"
    take_path = tmp_path / "take.wav"
    take_path.write_bytes(b"ok")
    state = AppState(
        input_path="input.wav",
        output_path="output.wav",
        recent_source_paths=("input.wav", "other.wav"),
        current_project_path="project.findusstretch.json",
        render_output_mode="dry_wet",
        recording_output_path="take.wav",
        audio_backend="portaudio",
        host_api_name="ASIO",
        recording_input_device_id="mic-1",
        preview_output_device_id="out-1",
        recording_sample_rate=44100,
        recording_input_channels=2,
        preview_output_channels=2,
        auto_load_recordings=False,
        active_workspace_tab="Effects",
        recent_takes=[RecentTake(path=str(take_path), duration_seconds=1.25, sample_rate=48000, timestamp="2026-03-12T19:10:00")],
        preview_start=1.5,
        preview_length=3.0,
        stretch_factor=14.0,
        quality_profile=QualityProfile.LOW,
        effects=EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            filter_enabled=False,
            delay_amount=0.4,
            delay_enabled=False,
            drive_amount=0.3,
            chorus_amount=0.25,
            texture_amount=0.31,
            motion_amount=0.22,
            pitch_drift_amount=0.19,
            bloom_amount=0.41,
            granular_amount=0.2,
            autopan_amount=0.45,
            reverse=True,
            input_gain_db=6.0,
            limiter_enabled=True,
        ),
        selected_preset_name="Dark Drone",
        compare_slot_a=CompareSlotState(
            stretch_factor=12.0,
            quality_profile=QualityProfile.HIGH,
            preview_length=3.0,
            effects=EffectSettings(reverb_amount=0.2),
            region_start=0.5,
            region_end=3.5,
            preset_name="Orbit Choir",
        ),
        compare_slot_b=CompareSlotState(
            stretch_factor=9.0,
            quality_profile=QualityProfile.MEDIUM,
            preview_length=2.2,
            effects=EffectSettings(delay_amount=0.3),
            region_start=1.0,
            region_end=3.2,
            preset_name="Custom",
        ),
        render_queue=(
            QueuedRenderJob(
                input_path="input.wav",
                output_path="batch_dark_drone.wav",
                stretch_factor=14.0,
                quality_profile=QualityProfile.HIGH,
                effects=EffectSettings(reverb_amount=0.55),
                region_start=0.5,
                region_end=3.5,
                preset_name="Dark Drone",
                output_mode="wet",
            ),
            QueuedRenderJob(
                input_path="input.wav",
                output_path="batch_orbit_choir.wav",
                stretch_factor=13.0,
                quality_profile=QualityProfile.HIGH,
                effects=EffectSettings(shimmer_amount=0.52),
                region_start=0.5,
                region_end=3.5,
                preset_name="Orbit Choir",
                output_mode="dry_wet",
            ),
        ),
        recent_project_paths=("project.findusstretch.json", "older.findusstretch.json"),
        favorite_factory_presets=("Dark Drone", "Orbit Choir"),
        waveform_region_start=1.5,
        waveform_region_end=4.5,
        loop_enabled=True,
        loop_crossfade_ms=120,
        theme_name="16bit",
        ui_scale_percent=150,
    )

    library.save_state(state, state_path)
    loaded = library.load_state(state_path)

    assert loaded.input_path == "input.wav"
    assert loaded.recording_output_path == "take.wav"
    assert loaded.recent_source_paths == ("input.wav", "other.wav")
    assert loaded.current_project_path == "project.findusstretch.json"
    assert loaded.render_output_mode == "dry_wet"
    assert loaded.audio_backend == "portaudio"
    assert loaded.host_api_name == "ASIO"
    assert loaded.recording_input_device_id == "mic-1"
    assert loaded.preview_output_device_id == "out-1"
    assert loaded.recording_sample_rate == 44100
    assert loaded.recording_input_channels == 2
    assert loaded.preview_output_channels == 2
    assert not loaded.auto_load_recordings
    assert loaded.active_workspace_tab == "Effects"
    assert len(loaded.recent_takes) == 1
    assert loaded.loop_enabled
    assert loaded.effects.reverse
    assert not loaded.effects.filter_enabled
    assert loaded.effects.filter_mode == FilterMode.HIGHPASS
    assert loaded.effects.autopan_amount == 0.45
    assert loaded.effects.bloom_amount == 0.41
    assert loaded.effects.input_gain_db == 6.0
    assert loaded.effects.limiter_enabled is True
    assert not loaded.effects.delay_enabled
    assert loaded.compare_slot_a is not None
    assert loaded.compare_slot_a.preset_name == "Orbit Choir"
    assert loaded.compare_slot_b is not None
    assert loaded.compare_slot_b.effects.delay_amount == 0.3
    assert len(loaded.render_queue) == 2
    assert loaded.render_queue[0].preset_name == "Dark Drone"
    assert loaded.render_queue[1].output_mode == "dry_wet"
    assert loaded.recent_project_paths == ("project.findusstretch.json", "older.findusstretch.json")
    assert loaded.favorite_factory_presets == ("Dark Drone", "Orbit Choir")
    assert loaded.waveform_region_end == 4.5
    assert loaded.loop_crossfade_ms == 120
    assert loaded.theme_name == "16bit"
    assert loaded.ui_scale_percent == 150


def test_preset_library_can_rename_user_preset(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    preset = AppPreset(
        name="Old Name",
        stretch_factor=9.0,
        quality_profile=QualityProfile.MEDIUM,
        preview_length=2.0,
        effects=EffectSettings(delay_amount=0.2),
        factory=False,
    )
    library.save_user_preset(preset)
    library.rename_user_preset("Old Name", "New Name")

    assert library.get_preset("Old Name") is None
    renamed = library.get_preset("New Name")
    assert renamed is not None
    assert renamed.preview_length == 2.0


def test_project_session_roundtrip(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    project_path = tmp_path / "session.findusstretch.json"
    project = ProjectSession(
        input_path="input.wav",
        output_path="output.wav",
        render_output_mode="dry_wet",
        preview_start=1.2,
        preview_length=3.4,
        stretch_factor=12.0,
        quality_profile=QualityProfile.HIGH,
        effects=EffectSettings(reverb_amount=0.4, shimmer_amount=0.25, freeze_enabled=True),
        selected_preset_name="Orbit Choir",
        compare_slot_a=CompareSlotState(
            stretch_factor=10.0,
            quality_profile=QualityProfile.MEDIUM,
            preview_length=2.5,
            effects=EffectSettings(chorus_amount=0.3),
            region_start=0.5,
            region_end=3.0,
            preset_name="Custom",
        ),
        render_queue=(
            QueuedRenderJob(
                input_path="input.wav",
                output_path="batch.wav",
                stretch_factor=12.0,
                quality_profile=QualityProfile.HIGH,
                effects=EffectSettings(reverb_amount=0.4),
                region_start=1.2,
                region_end=4.6,
                preset_name="Orbit Choir",
                output_mode="dry_wet",
            ),
        ),
        waveform_region_start=1.2,
        waveform_region_end=4.6,
        loop_enabled=True,
        loop_crossfade_ms=140,
    )

    library.save_project(project, project_path)
    loaded = library.load_project(project_path)

    assert loaded.input_path == "input.wav"
    assert loaded.output_path == "output.wav"
    assert loaded.render_output_mode == "dry_wet"
    assert loaded.preview_start == 1.2
    assert loaded.preview_length == 3.4
    assert loaded.stretch_factor == 12.0
    assert loaded.quality_profile == QualityProfile.HIGH
    assert loaded.effects.freeze_enabled is True
    assert loaded.selected_preset_name == "Orbit Choir"
    assert loaded.compare_slot_a is not None
    assert loaded.compare_slot_a.effects.chorus_amount == 0.3
    assert len(loaded.render_queue) == 1
    assert loaded.render_queue[0].output_mode == "dry_wet"
    assert loaded.loop_enabled is True
    assert loaded.loop_crossfade_ms == 140


def test_preset_library_ignores_corrupt_user_preset_file(tmp_path: Path) -> None:
    path = tmp_path / "presets.json"
    path.write_text("{ definitely not json", encoding="utf-8")

    library = PresetLibrary(path=path)

    assert library.get_preset("Dark Drone") is not None


def test_preset_library_load_state_falls_back_for_corrupt_json(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    state_path = tmp_path / "state.json"
    state_path.write_text("{ broken", encoding="utf-8")

    loaded = library.load_state(state_path)

    assert loaded == AppState()


def test_preset_library_load_state_normalizes_invalid_numeric_values(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "preview_start": -12,
                "recording_sample_rate": 1000,
                "recording_channels": 99,
                "preview_output_channels": 99,
                "preview_length": 0,
                "stretch_factor": 1,
                "quality_profile": "medium",
                "effects": {
                    "filter_mode": "bad-mode",
                    "reverb_amount": 99,
                    "lowpass_hz": -4,
                    "drive_amount": 3,
                    "chorus_amount": -2,
                    "texture_amount": 5,
                    "motion_amount": -1,
                    "pitch_drift_amount": "nan",
                    "bloom_amount": 7,
                    "granular_amount": "nan",
                    "delay_amount": -3,
                    "autopan_amount": 9,
                    "stereo_width": 99,
                    "shimmer_amount": "nan",
                    "wet_dry": 99,
                },
                "waveform_region_start": -8,
                "waveform_region_end": 0,
                "theme_name": "not-a-theme",
                "ui_scale_percent": 999,
            }
        ),
        encoding="utf-8",
    )

    loaded = library.load_state(state_path)

    assert loaded.preview_start == 0.0
    assert loaded.recording_sample_rate == 8000
    assert loaded.recording_input_channels == 2
    assert loaded.preview_output_channels == 2
    assert loaded.preview_length == 0.05
    assert loaded.stretch_factor == 2.0
    assert loaded.effects.filter_mode == FilterMode.OFF
    assert loaded.effects.reverb_amount == 1.0
    assert loaded.effects.lowpass_hz == 20.0
    assert loaded.effects.drive_amount == 1.0
    assert loaded.effects.chorus_amount == 0.0
    assert loaded.effects.texture_amount == 1.0
    assert loaded.effects.motion_amount == 0.0
    assert loaded.effects.pitch_drift_amount == 0.0
    assert loaded.effects.bloom_amount == 1.0
    assert loaded.effects.granular_amount == 0.0
    assert loaded.effects.delay_amount == 0.0
    assert loaded.effects.autopan_amount == 1.0
    assert loaded.effects.stereo_width == 2.0
    assert loaded.effects.shimmer_amount == 0.0
    assert loaded.effects.wet_dry == 1.0
    assert loaded.waveform_region_start == 0.0
    assert loaded.waveform_region_end == 0.01
    assert loaded.theme_name == "studio"
    assert loaded.ui_scale_percent == 200


def test_preset_library_load_state_filters_missing_recent_takes(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    existing_take = tmp_path / "exists.wav"
    existing_take.write_bytes(b"ok")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "recent_takes": [
                    {
                        "path": str(existing_take),
                        "duration_seconds": 1.0,
                        "sample_rate": 48000,
                        "timestamp": "2026-03-12T19:00:00",
                    },
                    {
                        "path": str(tmp_path / "missing.wav"),
                        "duration_seconds": 2.0,
                        "sample_rate": 48000,
                        "timestamp": "2026-03-12T19:01:00",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    loaded = library.load_state(state_path)

    assert [take.path for take in loaded.recent_takes] == [str(existing_take)]


def test_preset_library_load_state_defaults_recent_sources_when_missing(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"input_path": "demo.wav"}), encoding="utf-8")

    loaded = library.load_state(state_path)

    assert loaded.input_path == "demo.wav"
    assert loaded.recent_source_paths == ()


def test_preset_library_normalizes_invalid_user_preset_entries(tmp_path: Path) -> None:
    path = tmp_path / "presets.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "user_presets": [
                    {
                        "name": "Valid",
                        "stretch_factor": 12,
                        "quality_profile": "high",
                        "preview_length": 4.0,
                        "effects": {
                            "filter_mode": "band-pass",
                            "reverb_amount": 0.7,
                            "drive_amount": 0.25,
                            "texture_amount": 0.4,
                        },
                    },
                    {
                        "name": "Bad",
                        "stretch_factor": 10,
                        "quality_profile": "unknown",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    library = PresetLibrary(path=path)

    assert library.get_preset("Valid") is not None
    valid = library.get_preset("Valid")
    assert valid is not None
    assert valid.effects.filter_mode == FilterMode.BANDPASS
    assert valid.effects.drive_amount == 0.25
    assert valid.effects.texture_amount == 0.4
    invalid = library.get_preset("Bad")
    assert invalid is not None
    assert invalid.quality_profile == QualityProfile.MEDIUM
    assert invalid.preview_length == 2.5


def test_preset_library_load_state_defaults_missing_new_effect_fields(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "effects": {
                    "reverb_amount": 0.4,
                    "delay_amount": 0.1,
                }
            }
        ),
        encoding="utf-8",
    )

    loaded = library.load_state(state_path)

    assert loaded.effects.filter_mode == FilterMode.OFF
    assert loaded.effects.filter_enabled
    assert loaded.effects.drive_amount == 0.0
    assert loaded.effects.drive_enabled
    assert loaded.effects.chorus_amount == 0.0
    assert loaded.effects.texture_amount == 0.0
    assert loaded.effects.motion_amount == 0.0
    assert loaded.effects.pitch_drift_amount == 0.0
    assert loaded.effects.bloom_amount == 0.0
    assert loaded.effects.granular_amount == 0.0
    assert loaded.effects.autopan_amount == 0.0
    assert loaded.effects.reverb_amount == 0.4
    assert loaded.effects.delay_amount == 0.1
    assert loaded.effects.delay_enabled
    assert loaded.effects.wet_dry == 1.0


def test_factory_presets_include_extended_texture_variants(tmp_path: Path) -> None:
    library = PresetLibrary(path=tmp_path / "presets.json")

    names = {preset.name for preset in library.list_presets() if preset.factory}

    assert "Dust Bloom" in names
    assert "Orbit Choir" in names
    assert "Cathedral Bloom" in names
    assert "Neon Canal" in names
    assert "Glass Current" in names
    assert "Basement Fog" in names
    assert "Solar Drift" in names
    assert "Velvet Rotor" in names
    assert "Ice Shelf" in names
    assert "Tape Orbit" in names
    assert "Signal Garden" in names
    assert "Slow Aurora" in names
    assert "Dust Choir" in names
    assert "Broken Orbit" in names
    assert "Magnetic Fog" in names
    assert "Glass Bloom" in names
