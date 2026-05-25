from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .dsp import EffectSettings, FilterMode, QualityProfile
from .recording import RecentTake, filter_existing_recent_takes
from .themes import DEFAULT_THEME_NAME, clamp_ui_scale_percent, normalize_theme_name


def _default_root() -> Path:
    return Path(__file__).resolve().parent.parent


PRESET_LIBRARY_VERSION = 1
PROJECT_FILE_VERSION = 1
USER_PRESETS_PATH = _default_root() / "findus_stretching_presets.json"
APP_STATE_PATH = _default_root() / "findus_stretching_state.json"


@dataclass(frozen=True)
class AppPreset:
    name: str
    stretch_factor: float
    quality_profile: QualityProfile
    preview_length: float
    effects: EffectSettings = field(default_factory=EffectSettings)
    factory: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)
    favorite: bool = False


@dataclass(frozen=True)
class CompareSlotState:
    stretch_factor: float = 8.0
    quality_profile: QualityProfile = QualityProfile.MEDIUM
    preview_length: float = 2.5
    effects: EffectSettings = field(default_factory=EffectSettings)
    region_start: float = 0.0
    region_end: float = 2.5
    preset_name: str = "Custom"


@dataclass(frozen=True)
class QueuedRenderJob:
    input_path: str = ""
    output_path: str = ""
    stretch_factor: float = 8.0
    quality_profile: QualityProfile = QualityProfile.MEDIUM
    effects: EffectSettings = field(default_factory=EffectSettings)
    region_start: float = 0.0
    region_end: float = 2.5
    preset_name: str = "Custom"
    output_mode: str = "wet"


@dataclass(frozen=True)
class ProjectSession:
    input_path: str = ""
    output_path: str = ""
    render_output_mode: str = "wet"
    preview_start: float = 0.0
    preview_length: float = 2.5
    stretch_factor: float = 8.0
    quality_profile: QualityProfile = QualityProfile.MEDIUM
    effects: EffectSettings = field(default_factory=EffectSettings)
    selected_preset_name: str = "Custom"
    compare_slot_a: CompareSlotState | None = None
    compare_slot_b: CompareSlotState | None = None
    render_queue: tuple[QueuedRenderJob, ...] = field(default_factory=tuple)
    waveform_region_start: float = 0.0
    waveform_region_end: float = 2.5
    loop_enabled: bool = False
    loop_crossfade_ms: int = 80


FACTORY_PRESETS = [
    AppPreset("Custom", 8.0, QualityProfile.MEDIUM, 2.5, EffectSettings(), True),
    AppPreset(
        "Dark Drone",
        14.0,
        QualityProfile.HIGH,
        4.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.55,
            lowpass_hz=2400.0,
            delay_amount=0.35,
            stereo_width=1.2,
            wet_dry=0.78,
        ),
        True,
    ),
    AppPreset(
        "Air Pad",
        10.0,
        QualityProfile.MEDIUM,
        3.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.28,
            lowpass_hz=9500.0,
            delay_amount=0.18,
            stereo_width=1.3,
            wet_dry=0.55,
        ),
        True,
    ),
    AppPreset(
        "Fast Sketch",
        6.0,
        QualityProfile.LOW,
        1.5,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.20,
            lowpass_hz=7000.0,
            delay_amount=0.10,
            stereo_width=0.9,
            wet_dry=0.45,
        ),
        True,
    ),
    AppPreset(
        "Ghost Reverse",
        12.0,
        QualityProfile.HIGH,
        3.5,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.48,
            lowpass_hz=4200.0,
            delay_amount=0.30,
            stereo_width=1.25,
            reverse=True,
            wet_dry=0.72,
        ),
        True,
    ),
    AppPreset(
        "Wide Haze",
        10.0,
        QualityProfile.HIGH,
        3.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.38,
            lowpass_hz=7600.0,
            delay_amount=0.26,
            stereo_width=1.7,
            wet_dry=0.62,
        ),
        True,
    ),
    AppPreset(
        "Tape Mist",
        9.0,
        QualityProfile.MEDIUM,
        2.5,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.30,
            lowpass_hz=3200.0,
            delay_amount=0.42,
            stereo_width=1.05,
            wet_dry=0.68,
        ),
        True,
    ),
    AppPreset(
        "Frozen Hall",
        16.0,
        QualityProfile.HIGH,
        5.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            reverb_amount=0.65,
            lowpass_hz=1800.0,
            delay_amount=0.22,
            stereo_width=1.4,
            wet_dry=0.82,
            freeze_enabled=True,
        ),
        True,
    ),
    AppPreset(
        "Dust Bloom",
        11.0,
        QualityProfile.HIGH,
        3.5,
        EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            lowpass_hz=2800.0,
            granular_amount=0.42,
            chorus_amount=0.18,
            reverb_amount=0.48,
            shimmer_amount=0.22,
            wet_dry=0.76,
        ),
        True,
    ),
    AppPreset(
        "Orbit Choir",
        13.0,
        QualityProfile.HIGH,
        4.0,
        EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            lowpass_hz=1800.0,
            chorus_amount=0.46,
            autopan_amount=0.38,
            shimmer_amount=0.52,
            reverb_amount=0.44,
            stereo_width=1.55,
            wet_dry=0.74,
        ),
        True,
    ),
    AppPreset(
        "Broken Air",
        9.0,
        QualityProfile.MEDIUM,
        2.8,
        EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            lowpass_hz=3600.0,
            drive_amount=0.28,
            granular_amount=0.36,
            delay_amount=0.18,
            reverb_amount=0.24,
            wet_dry=0.63,
        ),
        True,
    ),
    AppPreset(
        "Rust Halo",
        10.0,
        QualityProfile.MEDIUM,
        3.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            lowpass_hz=2400.0,
            drive_amount=0.34,
            chorus_amount=0.2,
            reverb_amount=0.32,
            delay_amount=0.26,
            shimmer_amount=0.12,
            wet_dry=0.71,
        ),
        True,
    ),
    AppPreset(
        "Cathedral Bloom",
        15.0,
        QualityProfile.HIGH,
        4.8,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            lowpass_hz=2100.0,
            chorus_amount=0.16,
            reverb_amount=0.68,
            shimmer_amount=0.38,
            delay_amount=0.22,
            stereo_width=1.45,
            wet_dry=0.84,
        ),
        True,
    ),
    AppPreset(
        "Neon Canal",
        8.0,
        QualityProfile.MEDIUM,
        2.4,
        EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            lowpass_hz=2200.0,
            chorus_amount=0.42,
            autopan_amount=0.44,
            delay_amount=0.36,
            stereo_width=1.65,
            wet_dry=0.69,
        ),
        True,
    ),
    AppPreset(
        "Glass Current",
        12.0,
        QualityProfile.HIGH,
        3.4,
        EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            lowpass_hz=5200.0,
            chorus_amount=0.28,
            granular_amount=0.22,
            shimmer_amount=0.34,
            reverb_amount=0.31,
            stereo_width=1.5,
            wet_dry=0.72,
        ),
        True,
    ),
    AppPreset(
        "Basement Fog",
        11.0,
        QualityProfile.MEDIUM,
        3.1,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            lowpass_hz=1400.0,
            drive_amount=0.41,
            granular_amount=0.18,
            reverb_amount=0.28,
            delay_amount=0.14,
            wet_dry=0.74,
        ),
        True,
    ),
    AppPreset(
        "Solar Drift",
        14.0,
        QualityProfile.HIGH,
        4.2,
        EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            lowpass_hz=1500.0,
            chorus_amount=0.34,
            autopan_amount=0.48,
            shimmer_amount=0.46,
            reverb_amount=0.4,
            stereo_width=1.7,
            wet_dry=0.77,
        ),
        True,
    ),
    AppPreset(
        "Velvet Rotor",
        9.0,
        QualityProfile.MEDIUM,
        2.7,
        EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            lowpass_hz=2400.0,
            drive_amount=0.22,
            chorus_amount=0.24,
            autopan_amount=0.3,
            delay_amount=0.24,
            stereo_width=1.38,
            wet_dry=0.66,
        ),
        True,
    ),
    AppPreset(
        "Ice Shelf",
        18.0,
        QualityProfile.HIGH,
        5.0,
        EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            lowpass_hz=3200.0,
            freeze_enabled=True,
            granular_amount=0.26,
            shimmer_amount=0.5,
            reverb_amount=0.57,
            stereo_width=1.58,
            wet_dry=0.8,
        ),
        True,
    ),
    AppPreset(
        "Tape Orbit",
        10.0,
        QualityProfile.MEDIUM,
        3.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            lowpass_hz=2600.0,
            drive_amount=0.3,
            chorus_amount=0.14,
            delay_amount=0.31,
            autopan_amount=0.21,
            reverb_amount=0.27,
            wet_dry=0.7,
        ),
        True,
    ),
    AppPreset(
        "Signal Garden",
        10.0,
        QualityProfile.MEDIUM,
        3.0,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            texture_amount=0.34,
            motion_amount=0.26,
            pitch_drift_amount=0.14,
            bloom_amount=0.22,
            chorus_amount=0.12,
            wet_dry=0.7,
        ),
        True,
    ),
    AppPreset(
        "Slow Aurora",
        14.0,
        QualityProfile.HIGH,
        4.2,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            texture_amount=0.16,
            motion_amount=0.42,
            pitch_drift_amount=0.22,
            bloom_amount=0.5,
            shimmer_amount=0.34,
            reverb_amount=0.4,
            stereo_width=1.45,
            wet_dry=0.78,
        ),
        True,
    ),
    AppPreset(
        "Dust Choir",
        12.0,
        QualityProfile.HIGH,
        3.8,
        EffectSettings(
            filter_mode=FilterMode.BANDPASS,
            lowpass_hz=2600.0,
            texture_amount=0.56,
            motion_amount=0.18,
            pitch_drift_amount=0.1,
            bloom_amount=0.44,
            granular_amount=0.18,
            shimmer_amount=0.28,
            wet_dry=0.82,
        ),
        True,
    ),
    AppPreset(
        "Broken Orbit",
        9.0,
        QualityProfile.MEDIUM,
        2.8,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            texture_amount=0.48,
            motion_amount=0.36,
            pitch_drift_amount=0.3,
            bloom_amount=0.18,
            drive_amount=0.22,
            delay_amount=0.22,
            wet_dry=0.67,
        ),
        True,
    ),
    AppPreset(
        "Magnetic Fog",
        11.0,
        QualityProfile.HIGH,
        3.4,
        EffectSettings(
            filter_mode=FilterMode.LOWPASS,
            lowpass_hz=2100.0,
            texture_amount=0.4,
            motion_amount=0.28,
            pitch_drift_amount=0.18,
            bloom_amount=0.36,
            drive_amount=0.2,
            reverb_amount=0.32,
            wet_dry=0.74,
        ),
        True,
    ),
    AppPreset(
        "Glass Bloom",
        15.0,
        QualityProfile.HIGH,
        4.6,
        EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            lowpass_hz=2400.0,
            texture_amount=0.12,
            motion_amount=0.24,
            pitch_drift_amount=0.2,
            bloom_amount=0.64,
            chorus_amount=0.22,
            shimmer_amount=0.38,
            wet_dry=0.8,
        ),
        True,
    ),
]


@dataclass(frozen=True)
class AppState:
    input_path: str = ""
    output_path: str = ""
    recent_source_paths: tuple[str, ...] = field(default_factory=tuple)
    current_project_path: str = ""
    render_output_mode: str = "wet"
    recording_output_path: str = ""
    audio_backend: str = "auto"
    host_api_name: str = ""
    recording_input_device_id: str = ""
    preview_output_device_id: str = ""
    recording_sample_rate: int = 48000
    recording_input_channels: int = 1
    preview_output_channels: int = 2
    auto_load_recordings: bool = True
    active_workspace_tab: str = "Source"
    recent_takes: list[RecentTake] = field(default_factory=list)
    preview_start: float = 0.0
    preview_length: float = 2.5
    stretch_factor: float = 8.0
    quality_profile: QualityProfile = QualityProfile.MEDIUM
    effects: EffectSettings = field(default_factory=EffectSettings)
    selected_preset_name: str = "Custom"
    compare_slot_a: CompareSlotState | None = None
    compare_slot_b: CompareSlotState | None = None
    render_queue: tuple[QueuedRenderJob, ...] = field(default_factory=tuple)
    recent_project_paths: tuple[str, ...] = field(default_factory=tuple)
    favorite_factory_presets: tuple[str, ...] = field(default_factory=tuple)
    waveform_region_start: float = 0.0
    waveform_region_end: float = 2.5
    loop_enabled: bool = False
    loop_crossfade_ms: int = 80
    theme_name: str = DEFAULT_THEME_NAME
    ui_scale_percent: int = 100


class PresetLibrary:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or USER_PRESETS_PATH

    def list_presets(self) -> list[AppPreset]:
        return FACTORY_PRESETS + self._load_user_presets()

    def get_preset(self, name: str) -> AppPreset | None:
        for preset in self.list_presets():
            if preset.name == name:
                return preset
        return None

    def save_user_preset(self, preset: AppPreset) -> None:
        presets = {item.name: item for item in self._load_user_presets()}
        presets[preset.name] = AppPreset(
            name=preset.name,
            stretch_factor=preset.stretch_factor,
            quality_profile=preset.quality_profile,
            preview_length=preset.preview_length,
            effects=preset.effects,
            factory=False,
            tags=preset.tags,
            favorite=preset.favorite,
        )
        self._write_user_presets(list(presets.values()))

    def delete_user_preset(self, name: str) -> None:
        presets = [item for item in self._load_user_presets() if item.name != name]
        self._write_user_presets(presets)

    def rename_user_preset(self, old_name: str, new_name: str) -> None:
        presets = self._load_user_presets()
        updated = []
        for preset in presets:
            if preset.name == old_name:
                updated.append(
                    AppPreset(
                        name=new_name,
                        stretch_factor=preset.stretch_factor,
                        quality_profile=preset.quality_profile,
                        preview_length=preset.preview_length,
                        effects=preset.effects,
                        factory=False,
                        tags=preset.tags,
                        favorite=preset.favorite,
                    )
                )
            else:
                updated.append(preset)
        self._write_user_presets(updated)

    def load_state(self, path: Path | None = None) -> AppState:
        state_path = path or APP_STATE_PATH
        if not state_path.exists():
            return AppState()
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            return AppState()
        try:
            return AppState(
                input_path=str(data.get("input_path", "")),
                output_path=str(data.get("output_path", "")),
                recent_source_paths=_project_path_tuple(data.get("recent_source_paths", [])),
                current_project_path=str(data.get("current_project_path", "")),
                render_output_mode=_render_output_mode_value(data.get("render_output_mode", "wet")),
                recording_output_path=str(data.get("recording_output_path", "")),
                audio_backend=str(data.get("audio_backend", "auto")),
                host_api_name=str(data.get("host_api_name", "")),
                recording_input_device_id=str(data.get("recording_input_device_id", data.get("recording_device_id", ""))),
                preview_output_device_id=str(data.get("preview_output_device_id", "")),
                recording_sample_rate=int(_finite_float(data.get("recording_sample_rate", 48000), 48000, minimum=8000.0)),
                recording_input_channels=int(_finite_float(data.get("recording_input_channels", data.get("recording_channels", 1)), 1, minimum=1.0, maximum=2.0)),
                preview_output_channels=int(_finite_float(data.get("preview_output_channels", 2), 2, minimum=1.0, maximum=2.0)),
                auto_load_recordings=bool(data.get("auto_load_recordings", True)),
                active_workspace_tab=str(data.get("active_workspace_tab", "Source")),
                recent_takes=_recent_takes_from_list(data.get("recent_takes", [])),
                preview_start=_finite_float(data.get("preview_start", 0.0), 0.0, minimum=0.0),
                preview_length=_finite_float(data.get("preview_length", 2.5), 2.5, minimum=0.05),
                stretch_factor=_finite_float(data.get("stretch_factor", 8.0), 8.0, minimum=2.0),
                quality_profile=_quality_profile_from_value(data.get("quality_profile", QualityProfile.MEDIUM.value)),
                effects=_effect_from_dict(data.get("effects", {})),
                selected_preset_name=str(data.get("selected_preset_name", "Custom")),
                compare_slot_a=_compare_slot_from_dict(data.get("compare_slot_a")),
                compare_slot_b=_compare_slot_from_dict(data.get("compare_slot_b")),
                render_queue=_queue_jobs_from_list(data.get("render_queue", [])),
                recent_project_paths=_project_path_tuple(data.get("recent_project_paths", [])),
                favorite_factory_presets=_preset_name_tuple(data.get("favorite_factory_presets", [])),
                waveform_region_start=_finite_float(data.get("waveform_region_start", 0.0), 0.0, minimum=0.0),
                waveform_region_end=_finite_float(data.get("waveform_region_end", 2.5), 2.5, minimum=0.01),
                loop_enabled=bool(data.get("loop_enabled", False)),
                loop_crossfade_ms=int(_finite_float(data.get("loop_crossfade_ms", 80), 80, minimum=0.0, maximum=500.0)),
                theme_name=normalize_theme_name(data.get("theme_name", DEFAULT_THEME_NAME)),
                ui_scale_percent=clamp_ui_scale_percent(data.get("ui_scale_percent", 100)),
            )
        except Exception:
            return AppState()

    def save_state(self, state: AppState, path: Path | None = None) -> None:
        state_path = path or APP_STATE_PATH
        payload = {
            "input_path": state.input_path,
            "output_path": state.output_path,
            "recent_source_paths": list(state.recent_source_paths),
            "current_project_path": state.current_project_path,
            "render_output_mode": _render_output_mode_value(state.render_output_mode),
            "recording_output_path": state.recording_output_path,
            "audio_backend": state.audio_backend,
            "host_api_name": state.host_api_name,
            "recording_input_device_id": state.recording_input_device_id,
            "preview_output_device_id": state.preview_output_device_id,
            "recording_device_id": state.recording_input_device_id,
            "recording_sample_rate": state.recording_sample_rate,
            "recording_input_channels": state.recording_input_channels,
            "preview_output_channels": state.preview_output_channels,
            "recording_channels": state.recording_input_channels,
            "auto_load_recordings": state.auto_load_recordings,
            "active_workspace_tab": state.active_workspace_tab,
            "recent_takes": [_recent_take_to_dict(take) for take in filter_existing_recent_takes(state.recent_takes)],
            "preview_start": state.preview_start,
            "preview_length": state.preview_length,
            "stretch_factor": state.stretch_factor,
            "quality_profile": _quality_profile_value(state.quality_profile),
            "effects": _effect_to_dict(state.effects),
            "selected_preset_name": state.selected_preset_name,
            "compare_slot_a": _compare_slot_to_dict(state.compare_slot_a),
            "compare_slot_b": _compare_slot_to_dict(state.compare_slot_b),
            "render_queue": [_queued_render_job_to_dict(job) for job in state.render_queue],
            "recent_project_paths": list(state.recent_project_paths),
            "favorite_factory_presets": list(state.favorite_factory_presets),
            "waveform_region_start": state.waveform_region_start,
            "waveform_region_end": state.waveform_region_end,
            "loop_enabled": state.loop_enabled,
            "loop_crossfade_ms": state.loop_crossfade_ms,
            "theme_name": normalize_theme_name(state.theme_name),
            "ui_scale_percent": clamp_ui_scale_percent(state.ui_scale_percent),
        }
        state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_project(self, path: Path) -> ProjectSession:
        if not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Could not read project file: {exc}") from exc
        if data.get("version") != PROJECT_FILE_VERSION:
            raise RuntimeError("Unsupported project file version.")
        try:
            return ProjectSession(
                input_path=str(data.get("input_path", "")),
                output_path=str(data.get("output_path", "")),
                render_output_mode=_render_output_mode_value(data.get("render_output_mode", "wet")),
                preview_start=_finite_float(data.get("preview_start", 0.0), 0.0, minimum=0.0),
                preview_length=_finite_float(data.get("preview_length", 2.5), 2.5, minimum=0.05),
                stretch_factor=_finite_float(data.get("stretch_factor", 8.0), 8.0, minimum=2.0),
                quality_profile=_quality_profile_from_value(data.get("quality_profile", QualityProfile.MEDIUM.value)),
                effects=_effect_from_dict(data.get("effects", {})),
                selected_preset_name=str(data.get("selected_preset_name", "Custom")),
                compare_slot_a=_compare_slot_from_dict(data.get("compare_slot_a")),
                compare_slot_b=_compare_slot_from_dict(data.get("compare_slot_b")),
                render_queue=_queue_jobs_from_list(data.get("render_queue", [])),
                waveform_region_start=_finite_float(data.get("waveform_region_start", 0.0), 0.0, minimum=0.0),
                waveform_region_end=_finite_float(data.get("waveform_region_end", 2.5), 2.5, minimum=0.01),
                loop_enabled=bool(data.get("loop_enabled", False)),
                loop_crossfade_ms=int(_finite_float(data.get("loop_crossfade_ms", 80), 80, minimum=0.0, maximum=500.0)),
            )
        except Exception as exc:
            raise RuntimeError(f"Could not parse project file: {exc}") from exc

    def save_project(self, project: ProjectSession, path: Path) -> None:
        payload = {
            "version": PROJECT_FILE_VERSION,
            "input_path": project.input_path,
            "output_path": project.output_path,
            "render_output_mode": _render_output_mode_value(project.render_output_mode),
            "preview_start": project.preview_start,
            "preview_length": project.preview_length,
            "stretch_factor": project.stretch_factor,
            "quality_profile": _quality_profile_value(project.quality_profile),
            "effects": _effect_to_dict(project.effects),
            "selected_preset_name": project.selected_preset_name,
            "compare_slot_a": _compare_slot_to_dict(project.compare_slot_a),
            "compare_slot_b": _compare_slot_to_dict(project.compare_slot_b),
            "render_queue": [_queued_render_job_to_dict(job) for job in project.render_queue],
            "waveform_region_start": project.waveform_region_start,
            "waveform_region_end": project.waveform_region_end,
            "loop_enabled": project.loop_enabled,
            "loop_crossfade_ms": project.loop_crossfade_ms,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load_user_presets(self) -> list[AppPreset]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if raw.get("version") != PRESET_LIBRARY_VERSION:
            return []
        presets = []
        for item in raw.get("user_presets", []):
            try:
                presets.append(
                    AppPreset(
                        name=str(item["name"]),
                        stretch_factor=_finite_float(item["stretch_factor"], 8.0, minimum=2.0),
                        quality_profile=_quality_profile_from_value(item["quality_profile"]),
                        preview_length=_finite_float(item.get("preview_length", 2.5), 2.5, minimum=0.05),
                        effects=_effect_from_dict(item.get("effects", {})),
                        factory=False,
                        tags=_tags_from_value(item.get("tags", [])),
                        favorite=bool(item.get("favorite", False)),
                    )
                )
            except Exception:
                continue
        return presets

    def _write_user_presets(self, presets: list[AppPreset]) -> None:
        payload = {
            "version": PRESET_LIBRARY_VERSION,
            "user_presets": [
                {
                    "name": preset.name,
                    "stretch_factor": preset.stretch_factor,
                    "quality_profile": _quality_profile_value(preset.quality_profile),
                    "preview_length": preset.preview_length,
                    "effects": _effect_to_dict(preset.effects),
                    "tags": list(preset.tags),
                    "favorite": preset.favorite,
                }
                for preset in presets
            ],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _effect_from_dict(data: dict) -> EffectSettings:
    return EffectSettings(
        filter_mode=_filter_mode_from_value(data.get("filter_mode", FilterMode.OFF.value)),
        filter_enabled=bool(data.get("filter_enabled", True)),
        reverb_amount=_finite_float(data.get("reverb_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        reverb_enabled=bool(data.get("reverb_enabled", True)),
        lowpass_hz=_finite_float(data.get("lowpass_hz", 6000.0), 6000.0, minimum=20.0),
        drive_amount=_finite_float(data.get("drive_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        drive_enabled=bool(data.get("drive_enabled", True)),
        chorus_amount=_finite_float(data.get("chorus_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        chorus_enabled=bool(data.get("chorus_enabled", True)),
        texture_amount=_finite_float(data.get("texture_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        texture_enabled=bool(data.get("texture_enabled", True)),
        motion_amount=_finite_float(data.get("motion_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        motion_enabled=bool(data.get("motion_enabled", True)),
        pitch_drift_amount=_finite_float(data.get("pitch_drift_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        pitch_drift_enabled=bool(data.get("pitch_drift_enabled", True)),
        bloom_amount=_finite_float(data.get("bloom_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        bloom_enabled=bool(data.get("bloom_enabled", True)),
        granular_amount=_finite_float(data.get("granular_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        granular_enabled=bool(data.get("granular_enabled", True)),
        delay_amount=_finite_float(data.get("delay_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        delay_enabled=bool(data.get("delay_enabled", True)),
        autopan_amount=_finite_float(data.get("autopan_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        autopan_enabled=bool(data.get("autopan_enabled", True)),
        stereo_width=_finite_float(data.get("stereo_width", 1.0), 1.0, minimum=0.0, maximum=2.0),
        reverse=bool(data.get("reverse", False)),
        freeze_enabled=bool(data.get("freeze_enabled", False)),
        shimmer_amount=_finite_float(data.get("shimmer_amount", 0.0), 0.0, minimum=0.0, maximum=1.0),
        shimmer_enabled=bool(data.get("shimmer_enabled", True)),
        wet_dry=_finite_float(data.get("wet_dry", 1.0), 1.0, minimum=0.0, maximum=1.0),
        input_gain_db=_finite_float(data.get("input_gain_db", 0.0), 0.0, minimum=-24.0, maximum=24.0),
        limiter_enabled=bool(data.get("limiter_enabled", False)),
    )


def _effect_to_dict(effects: EffectSettings) -> dict[str, object]:
    payload = asdict(effects)
    payload["filter_mode"] = effects.filter_mode.value
    return payload


def _compare_slot_from_dict(data: object) -> CompareSlotState | None:
    if not isinstance(data, dict):
        return None
    return CompareSlotState(
        stretch_factor=_finite_float(data.get("stretch_factor", 8.0), 8.0, minimum=2.0),
        quality_profile=_quality_profile_from_value(data.get("quality_profile", QualityProfile.MEDIUM.value)),
        preview_length=_finite_float(data.get("preview_length", 2.5), 2.5, minimum=0.05),
        effects=_effect_from_dict(data.get("effects", {})),
        region_start=_finite_float(data.get("region_start", 0.0), 0.0, minimum=0.0),
        region_end=_finite_float(data.get("region_end", 2.5), 2.5, minimum=0.01),
        preset_name=str(data.get("preset_name", "Custom")),
    )


def _compare_slot_to_dict(slot: CompareSlotState | None) -> dict[str, object] | None:
    if slot is None:
        return None
    return {
        "stretch_factor": slot.stretch_factor,
        "quality_profile": _quality_profile_value(slot.quality_profile),
        "preview_length": slot.preview_length,
        "effects": _effect_to_dict(slot.effects),
        "region_start": slot.region_start,
        "region_end": slot.region_end,
        "preset_name": slot.preset_name,
    }


def _queued_render_job_from_dict(data: object) -> QueuedRenderJob | None:
    if not isinstance(data, dict):
        return None
    return QueuedRenderJob(
        input_path=str(data.get("input_path", "")),
        output_path=str(data.get("output_path", "")),
        stretch_factor=_finite_float(data.get("stretch_factor", 8.0), 8.0, minimum=2.0),
        quality_profile=_quality_profile_from_value(data.get("quality_profile", QualityProfile.MEDIUM.value)),
        effects=_effect_from_dict(data.get("effects", {})),
        region_start=_finite_float(data.get("region_start", 0.0), 0.0, minimum=0.0),
        region_end=_finite_float(data.get("region_end", 2.5), 2.5, minimum=0.01),
        preset_name=str(data.get("preset_name", "Custom")),
        output_mode=_render_output_mode_value(data.get("output_mode", "wet")),
    )


def _queued_render_job_to_dict(job: QueuedRenderJob) -> dict[str, object]:
    return {
        "input_path": job.input_path,
        "output_path": job.output_path,
        "stretch_factor": job.stretch_factor,
        "quality_profile": _quality_profile_value(job.quality_profile),
        "effects": _effect_to_dict(job.effects),
        "region_start": job.region_start,
        "region_end": job.region_end,
        "preset_name": job.preset_name,
        "output_mode": _render_output_mode_value(job.output_mode),
    }


def _queue_jobs_from_list(value: object) -> tuple[QueuedRenderJob, ...]:
    if not isinstance(value, list):
        return ()
    jobs: list[QueuedRenderJob] = []
    for item in value:
        job = _queued_render_job_from_dict(item)
        if job is not None:
            jobs.append(job)
    return tuple(jobs)


def _tags_from_value(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    tags: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        tag = item.strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tuple(tags)


def _preset_name_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    names: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        name = item.strip()
        if name and name not in names:
            names.append(name)
    return tuple(names)


def _project_path_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    paths: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        path = item.strip()
        if path and path not in paths:
            paths.append(path)
    return tuple(paths)


def _render_output_mode_value(value: object) -> str:
    if not isinstance(value, str):
        return "wet"
    normalized = value.strip().lower()
    if normalized in {"wet", "dry", "dry_wet"}:
        return normalized
    return "wet"


def _recent_takes_from_list(data: object) -> list[RecentTake]:
    if not isinstance(data, list):
        return []
    takes: list[RecentTake] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        takes.append(
            RecentTake(
                path=path,
                duration_seconds=_finite_float(item.get("duration_seconds", 0.0), 0.0, minimum=0.0),
                sample_rate=int(_finite_float(item.get("sample_rate", 48000), 48000, minimum=1.0)),
                timestamp=str(item.get("timestamp", "")),
            )
        )
    return filter_existing_recent_takes(takes)


def _recent_take_to_dict(take: RecentTake) -> dict[str, object]:
    return {
        "path": take.path,
        "duration_seconds": take.duration_seconds,
        "sample_rate": take.sample_rate,
        "timestamp": take.timestamp,
    }


def _quality_profile_value(value: QualityProfile | str) -> str:
    if isinstance(value, QualityProfile):
        return value.value
    return QualityProfile(value).value if isinstance(value, str) else QualityProfile.MEDIUM.value


def _quality_profile_from_value(value: object) -> QualityProfile:
    if isinstance(value, QualityProfile):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for profile in QualityProfile:
            if normalized in {profile.value.lower(), profile.name.lower()}:
                return profile
    return QualityProfile.MEDIUM


def _filter_mode_from_value(value: object) -> FilterMode:
    if isinstance(value, FilterMode):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        for mode in FilterMode:
            if normalized in {mode.value.lower(), mode.name.lower()}:
                return mode
    return FilterMode.OFF


def _finite_float(
    value: object,
    default: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default
    if not math.isfinite(result):
        result = default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result
