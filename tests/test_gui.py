from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import soundfile as sf

from PySide6.QtCore import QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QWheelEvent
from PySide6.QtMultimedia import QAudio
from PySide6.QtWidgets import QApplication, QMessageBox, QTextBrowser

from paulstretch_light.gui import (
    STARTUP_SPLASH_VARIANT_PATHS,
    MainWindow,
    PreviewPlayer,
    StartupSplashScreen,
    _choose_startup_splash_path,
    _existing_startup_splash_paths,
)
from paulstretch_light.preset_library import ProjectSession
from paulstretch_light.renderer import PreviewResult, RenderOutputMode
from paulstretch_light.waveform import RegionSelection, build_waveform_overview


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _write_test_audio(path: Path) -> None:
    sample_rate = 22050
    t = np.linspace(0.0, 0.75, int(sample_rate * 0.75), endpoint=False)
    stereo = np.column_stack(
        [
            np.sin(2.0 * np.pi * 220.0 * t),
            np.sin(2.0 * np.pi * 330.0 * t),
        ]
    ).astype(np.float32)
    sf.write(str(path), stereo, sample_rate, subtype="FLOAT", format="WAV")


def test_main_window_exposes_help_tab_and_shortcut_action() -> None:
    app = _app()
    window = MainWindow()

    tab_names = [window.workspace_tabs.tabText(index) for index in range(window.workspace_tabs.count())]
    assert "Help" in tab_names

    help_browser = window.findChild(QTextBrowser)
    assert help_browser is not None
    assert "FINDUS&gt;x&lt;STRETCHING Help" in help_browser.toHtml()
    assert "Render queue" in help_browser.toPlainText()
    assert "dry+wet" in help_browser.toPlainText().lower()
    assert "project" in help_browser.toPlainText().lower()
    assert "preview history" in help_browser.toPlainText().lower()
    assert "loop crossfade" in help_browser.toPlainText().lower()
    assert "input trim" in help_browser.toPlainText().lower()
    assert "safety limiter" in help_browser.toPlainText().lower()
    assert "undo / redo" in help_browser.toPlainText().lower()
    assert "toggle a/b" in help_browser.toPlainText().lower()
    assert "recent sources" in help_browser.toPlainText().lower()
    assert "drag and drop" in help_browser.toPlainText().lower()
    assert "audio i/o" in help_browser.toPlainText().lower()
    assert "macros" in help_browser.toPlainText().lower()
    assert "rotating splash screen" in help_browser.toPlainText().lower()

    window.help_action.trigger()
    assert window.workspace_tabs.tabText(window.workspace_tabs.currentIndex()) == "Help"

    window.close()


def test_startup_splash_uses_existing_fin_dus_variants() -> None:
    options = _existing_startup_splash_paths()

    assert options
    assert all(path.exists() for path in options)
    assert all(path in STARTUP_SPLASH_VARIANT_PATHS or path.name == "findus_stretching_icon.png" for path in options)


def test_startup_splash_can_choose_and_render_variant() -> None:
    app = _app()
    chosen = _choose_startup_splash_path(lambda options: options[0])

    assert chosen is not None
    splash = StartupSplashScreen(chosen)
    splash.show_stage("Loading workspace...", 42)

    assert splash.pixmap() is not None
    assert not splash.pixmap().isNull()
    assert splash.progress == 42
    current_phase = splash.loader_phase
    splash.advance_loader()
    assert splash.loader_phase != current_phase


def test_startup_splash_loader_style_varies_by_variant() -> None:
    classic = StartupSplashScreen(Path("assets/icon_variants/findus_cat_classic.png"))
    midnight = StartupSplashScreen(Path("assets/icon_variants/findus_cat_midnight.png"))
    stamp = StartupSplashScreen(Path("assets/icon_variants/findus_cat_stamp.png"))
    orbit = StartupSplashScreen(Path("assets/icon_variants/findus_cat_orbit.png"))

    assert classic.loader_style == "spiral"
    assert midnight.loader_style == "neon_ring"
    assert stamp.loader_style == "stamp_pulse"
    assert orbit.loader_style == "orbit_arc"


def test_main_window_restores_ui_scale_controls() -> None:
    app = _app()
    window = MainWindow()

    assert window.ui_scale_combo.currentData() == window.current_ui_scale_percent
    window._apply_ui_scale(150, announce=False)

    assert window.current_ui_scale_percent == 150
    assert window.ui_scale_combo.currentData() == 150
    assert window.property("uiScalePercent") == 150

    window.close()


def test_mousewheel_over_tab_bar_does_not_switch_tabs() -> None:
    app = _app()
    window = MainWindow()

    window.workspace_tabs.setCurrentIndex(0)
    event = QWheelEvent(
        QPointF(10.0, 10.0),
        QPointF(10.0, 10.0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )

    window.workspace_tabs.tabBar().wheelEvent(event)

    assert window.workspace_tabs.currentIndex() == 0

    window.close()


def test_nested_subtabs_group_controls_and_ignore_mousewheel() -> None:
    app = _app()
    window = MainWindow()

    assert [window.source_subtabs.tabText(index) for index in range(window.source_subtabs.count())] == [
        "Files",
        "Projects",
        "Audio I/O",
        "Recording",
    ]
    assert [window.stretch_subtabs.tabText(index) for index in range(window.stretch_subtabs.count())] == [
        "Region",
        "Compare",
        "History",
    ]
    assert [window.presets_subtabs.tabText(index) for index in range(window.presets_subtabs.count())] == [
        "Library",
        "Manage",
        "Batch",
    ]
    assert not hasattr(window, "effects_subtabs")

    window.stretch_subtabs.setCurrentIndex(0)
    event = QWheelEvent(
        QPointF(10.0, 10.0),
        QPointF(10.0, 10.0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )

    window.stretch_subtabs.tabBar().wheelEvent(event)

    assert window.stretch_subtabs.currentIndex() == 0

    window.close()


def test_main_window_exposes_new_macro_effect_controls() -> None:
    app = _app()
    window = MainWindow()

    assert window.texture_slider.value() >= 0
    assert window.motion_slider.value() >= 0
    assert window.pitch_drift_slider.value() >= 0
    assert window.bloom_slider.value() >= 0

    window.texture_slider.setValue(33)
    window.motion_slider.setValue(44)
    window.pitch_drift_slider.setValue(22)
    window.bloom_slider.setValue(55)

    effects = window._effect_settings()

    assert effects.texture_amount == 0.33
    assert effects.motion_amount == 0.44
    assert effects.pitch_drift_amount == 0.22
    assert effects.bloom_amount == 0.55

    window.close()


def test_input_trim_and_limiter_controls_roundtrip_into_effect_settings() -> None:
    app = _app()
    window = MainWindow()

    window.input_trim_slider.setValue(9)
    window.limiter_checkbox.setChecked(True)

    effects = window._effect_settings()

    assert effects.input_gain_db == 9.0
    assert effects.limiter_enabled is True
    assert window._effective_effect_settings().input_gain_db == 9.0

    window.close()


def test_effects_default_to_audible_bypass_state() -> None:
    app = _app()
    window = MainWindow()
    custom = window.preset_library.get_preset("Custom")
    assert custom is not None
    window._apply_preset(custom)

    effects = window._effect_settings()

    assert effects.filter_mode.value == "Off"
    assert effects.reverb_amount == 0.0
    assert effects.delay_amount == 0.0
    assert effects.wet_dry == 1.0

    window.close()


def test_harmonize_button_applies_choir_like_effect_stack() -> None:
    app = _app()
    window = MainWindow()

    window._apply_harmonize_effects()
    effects = window._effect_settings()

    assert effects.filter_mode.value == "High-pass"
    assert effects.chorus_amount == 0.46
    assert effects.shimmer_amount == 0.48
    assert effects.bloom_amount == 0.42
    assert effects.stereo_width == 1.55
    assert effects.wet_dry == 0.78

    window.close()


def test_bypass_all_effects_toggles_to_neutral_and_can_restore() -> None:
    app = _app()
    window = MainWindow()

    window._apply_harmonize_effects()
    colored = window._effect_settings()

    window._toggle_effects_bypass()
    bypassed = window._effect_settings()

    assert bypassed.filter_mode.value == "Off"
    assert bypassed.filter_enabled is False
    assert bypassed.reverb_amount == 0.0
    assert bypassed.delay_amount == 0.0
    assert bypassed.wet_dry == 1.0
    assert window.bypass_effects_button.text() == "Restore Effects"

    window._toggle_effects_bypass()

    assert window._effect_settings() == colored
    assert window.bypass_effects_button.text() == "Bypass All Effects"

    window.close()


def test_reset_effects_restores_neutral_without_touching_stretch_settings() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")

    window.stretch_slider.setValue(23)
    window.preview_start.setValue(1.5)
    window.preview_duration.setValue(4.5)
    window._apply_harmonize_effects()

    window._reset_effects()
    effects = window._effect_settings()

    assert effects == window._neutral_effect_settings()
    assert window.stretch_slider.value() == 23
    assert window.preview_start.value() == 1.5
    assert window.preview_duration.value() == 4.5

    window.close()


def test_effect_toggle_removes_effect_from_effective_settings_but_keeps_slider_value() -> None:
    app = _app()
    window = MainWindow()

    window.reverb_slider.setValue(48)
    window.reverb_enabled_checkbox.setChecked(False)

    raw = window._effect_settings()
    effective = window._effective_effect_settings()

    assert raw.reverb_amount == 0.48
    assert raw.reverb_enabled is False
    assert effective.reverb_amount == 0.0
    assert window.reverb_slider.value() == 48

    window.reverb_enabled_checkbox.setChecked(True)

    assert window._effective_effect_settings().reverb_amount == 0.48

    window.close()


def test_random_button_changes_effect_values() -> None:
    app = _app()
    window = MainWindow()

    before = window._effect_settings()

    window._randomize_effects()

    after = window._effect_settings()

    assert after != before

    window.close()


def test_random_variants_apply_distinct_starting_points() -> None:
    app = _app()
    window = MainWindow()

    window._randomize_effects("dark")
    dark = window._effect_settings()
    assert dark.reverb_amount >= 0.32

    window._randomize_effects("bright")
    bright = window._effect_settings()
    assert bright.shimmer_amount >= 0.22

    window._randomize_effects("huge")
    huge = window._effect_settings()
    assert huge.stereo_width >= 1.35

    window._randomize_effects("weird")
    weird = window._effect_settings()
    assert weird.granular_amount >= 0.16

    window.close()


def test_ab_compare_slots_store_and_restore_workflow() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")

    window.stretch_slider.setValue(21)
    window.preview_start.setValue(1.4)
    window.preview_duration.setValue(3.2)
    window._apply_harmonize_effects()
    window._store_compare_slot("A")

    window.stretch_slider.setValue(9)
    window.preview_start.setValue(0.4)
    window.preview_duration.setValue(1.6)
    window.reverb_slider.setValue(12)

    window._load_compare_slot("A")

    assert window.stretch_slider.value() == 21
    assert window.preview_start.value() == 1.4
    assert window.preview_duration.value() == 3.2
    assert window._effect_settings().chorus_amount == 0.46
    assert "A" in window.compare_status_label.text()

    window.close()


def test_undo_and_redo_restore_workflow_snapshot() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window.stretch_slider.setValue(8)
    window.preview_start.setValue(0.0)
    window.reverb_slider.setValue(0)
    window._reset_workflow_history()

    baseline = window._current_workflow_snapshot()

    window.stretch_slider.setValue(21)
    window.preview_start.setValue(1.4)
    window.reverb_slider.setValue(28)
    window._flush_workflow_history()

    assert window.undo_stack

    window._undo_workflow()

    assert window.stretch_slider.value() == int(round(baseline.stretch_factor))
    assert window.preview_start.value() == baseline.preview_start
    assert window.reverb_slider.value() == int(round(baseline.effects.reverb_amount * 100))

    window._redo_workflow()

    assert window.stretch_slider.value() == 21
    assert window.preview_start.value() == 1.4
    assert window.reverb_slider.value() == 28

    window.close()


def test_consecutive_slider_moves_coalesce_into_one_undo_step() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window.stretch_slider.setValue(8)
    window._reset_workflow_history()

    window.stretch_slider.setValue(10)
    window.stretch_slider.setValue(14)
    window.stretch_slider.setValue(18)

    assert len(window.undo_stack) == 1

    window._flush_workflow_history()
    window._undo_workflow()

    assert window.stretch_slider.value() == 8

    window.close()


def test_undo_restores_state_after_effect_shortcuts() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window._apply_effect_settings_to_controls(window._neutral_effect_settings())
    window._reset_workflow_history()

    baseline = window._effect_settings()
    window._apply_harmonize_effects()
    window._undo_workflow()

    assert window._effect_settings() == baseline

    window._randomize_effects("dark")
    randomized = window._effect_settings()
    assert randomized != baseline
    window._undo_workflow()
    assert window._effect_settings() == baseline

    window.close()


def test_undo_after_loading_compare_slot_restores_previous_state() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window.compare_slots = {"A": None, "B": None}
    window._reset_workflow_history()

    window.stretch_slider.setValue(18)
    window.reverb_slider.setValue(30)
    window._store_compare_slot("A")

    window.stretch_slider.setValue(7)
    window.reverb_slider.setValue(5)

    window._load_compare_slot("A")
    assert window.stretch_slider.value() == 18

    window._undo_workflow()

    assert window.stretch_slider.value() == 7
    assert window.reverb_slider.value() == 5

    window.close()


def test_toggle_ab_chooses_expected_target_and_updates_active_label() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window.compare_slots = {"A": None, "B": None}
    window._reset_workflow_history()

    window.stretch_slider.setValue(12)
    window._store_compare_slot("A")
    window.stretch_slider.setValue(24)
    window._store_compare_slot("B")

    preview_calls: list[str] = []
    window._preview = lambda: preview_calls.append("preview")

    window.stretch_slider.setValue(15)
    window._toggle_compare_slots()
    assert window.stretch_slider.value() == 12
    assert "A active" in window.compare_status_label.text()

    window._toggle_compare_slots()
    assert window.stretch_slider.value() == 24
    assert "B active" in window.compare_status_label.text()
    assert preview_calls == ["preview", "preview"]

    window.close()


def test_toggle_ab_replays_cached_preview_when_target_preview_exists(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "source.wav"
    _write_test_audio(source_path)
    window.compare_slots = {"A": None, "B": None}
    window.preview_history_entries.clear()
    window._reset_workflow_history()
    window._load_source_audio_path(str(source_path), status_message="loaded")

    window.stretch_slider.setValue(12)
    window._store_compare_slot("A")

    window.stretch_slider.setValue(24)
    window._store_compare_slot("B")

    preview = PreviewResult(
        audio=np.zeros((22050, 2), dtype=np.float32),
        sample_rate=22050,
        channels=2,
        preview_frames=22050,
        source_start_seconds=float(window.preview_start.value()),
        source_duration_seconds=float(window.preview_duration.value()),
        stretch_factor=24.0,
    )
    window.current_preview = preview
    window.current_preview_key = window._preview_cache_key()
    window._remember_preview_history(preview)

    window._load_compare_slot("A")

    play_calls: list[tuple[PreviewResult, bool]] = []
    window._play_preview_result = lambda result, from_cache=False, loop_restart=False: play_calls.append((result, from_cache))

    window._toggle_compare_slots()

    assert play_calls == [(preview, True)]
    assert window.current_preview is preview
    assert "B active" in window.compare_status_label.text()

    window.close()


def test_undo_and_redo_tooltips_show_last_action_label() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window._reset_workflow_history()

    window.stretch_slider.setValue(13)

    assert "stretch change" in window.undo_action.toolTip().lower()

    window._undo_workflow()

    assert "stretch change" in window.redo_action.toolTip().lower()

    window.close()


def test_store_active_compare_slot_defaults_to_a_when_current_state_is_custom_mix() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window.compare_slots = {"A": None, "B": None}
    window.current_preset_name = "Custom"
    window._apply_effect_settings_to_controls(window._neutral_effect_settings())
    window._reset_workflow_history()

    window.stretch_slider.setValue(11)
    window._store_compare_slot("A")
    window.stretch_slider.setValue(22)
    window._store_compare_slot("B")
    window._load_compare_slot("B")
    window.reverb_slider.setValue(37)

    window._store_active_compare_slot()

    assert window.compare_slots["A"] is not None
    assert window.compare_slots["A"].effects.reverb_amount == 0.37

    window.close()


def test_swap_ab_exchanges_slots_and_updates_active_status() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")
    window.compare_slots = {"A": None, "B": None}
    window._reset_workflow_history()

    window.stretch_slider.setValue(12)
    window._store_compare_slot("A")
    slot_a = window.compare_slots["A"]
    window.stretch_slider.setValue(24)
    window._store_compare_slot("B")
    slot_b = window.compare_slots["B"]
    window._load_compare_slot("A")

    window._swap_compare_slots()

    assert window.compare_slots["A"] == slot_b
    assert window.compare_slots["B"] == slot_a
    assert "B active" in window.compare_status_label.text()

    window.close()


def test_preset_favorite_and_filter_controls_work_together() -> None:
    app = _app()
    window = MainWindow()
    window.favorite_factory_preset_names = set()
    window._refresh_presets(selected_name="Dark Drone")

    index = next(
        idx
        for idx in range(window.preset_combo.count())
        if isinstance(window.preset_combo.itemData(idx), object)
        and getattr(window.preset_combo.itemData(idx), "name", "") == "Dark Drone"
    )
    window.preset_combo.setCurrentIndex(index)
    window._toggle_selected_preset_favorite()

    assert "Dark Drone" in window.favorite_factory_preset_names

    window.preset_favorites_only_checkbox.setChecked(True)
    visible_names = [
        window.preset_combo.itemData(idx).name
        for idx in range(window.preset_combo.count())
        if window.preset_combo.itemData(idx) is not None
    ]
    assert visible_names == ["Dark Drone"]

    window.preset_search_edit.setText("dark")
    visible_names = [
        window.preset_combo.itemData(idx).name
        for idx in range(window.preset_combo.count())
        if window.preset_combo.itemData(idx) is not None
    ]
    assert visible_names == ["Dark Drone"]

    window.close()


def test_user_preset_tags_can_be_applied_and_filtered() -> None:
    app = _app()
    window = MainWindow()

    preset = window._current_preset("Tagged User", factory=False)
    window.preset_library.save_user_preset(preset)
    window._refresh_presets(selected_name=preset.name)
    index = next(
        idx
        for idx in range(window.preset_combo.count())
        if getattr(window.preset_combo.itemData(idx), "name", "") == "Tagged User"
    )
    window.preset_combo.setCurrentIndex(index)
    window.preset_tags_edit.setText("weird, choir")
    window._apply_selected_preset_tags()

    reloaded = window.preset_library.get_preset("Tagged User")
    assert reloaded is not None
    assert reloaded.tags == ("weird", "choir")

    tag_index = window.preset_tag_filter_combo.findData("weird")
    window.preset_tag_filter_combo.setCurrentIndex(tag_index)
    visible_names = [
        window.preset_combo.itemData(idx).name
        for idx in range(window.preset_combo.count())
        if window.preset_combo.itemData(idx) is not None
    ]
    assert "Tagged User" in visible_names

    window.close()


def test_queue_current_render_captures_effective_snapshot_and_export_mode(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    window._persist_state = lambda: None
    source_path = tmp_path / "source.wav"
    _write_test_audio(source_path)
    window._clear_loaded_input("No waveform loaded")

    window.input_edit.setText(str(source_path))
    window.output_edit.setText(str(tmp_path / "render.wav"))
    window.stretch_slider.setValue(17)
    window.preview_start.setValue(0.4)
    window.preview_duration.setValue(1.3)
    window.reverb_slider.setValue(42)
    window.reverb_enabled_checkbox.setChecked(False)
    render_mode_index = window.render_output_mode_combo.findData(RenderOutputMode.DRY_WET)
    window.render_output_mode_combo.setCurrentIndex(render_mode_index)

    window._queue_current_render()

    assert len(window.render_queue_items) == 1
    job = window.render_queue_items[0]
    assert job.output_mode == "dry_wet"
    assert job.stretch_factor == 17.0
    assert job.region_start == 0.4
    assert round(job.region_end, 3) == 1.7
    assert job.effects.reverb_amount == 0.0
    assert "1 job(s) queued" in window.render_queue_status_label.text()

    window.close()


def test_filtered_batch_queue_uses_selected_presets_and_safe_output_names(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    window._persist_state = lambda: None
    window.render_queue_items.clear()
    window._refresh_render_queue_list()
    source_path = tmp_path / "source.wav"
    _write_test_audio(source_path)

    window.input_edit.setText(str(source_path))
    window.output_edit.setText(str(tmp_path / "render.wav"))
    render_mode_index = window.render_output_mode_combo.findData(RenderOutputMode.DRY_WET)
    window.render_output_mode_combo.setCurrentIndex(render_mode_index)
    window.preset_search_edit.setText("orbit")
    window._select_all_filtered_batch_presets()

    window._queue_selected_preset_batch()

    queued_names = [job.preset_name for job in window.render_queue_items]
    assert queued_names == ["Orbit Choir", "Tape Orbit", "Broken Orbit"]
    assert all(job.output_mode == "dry_wet" for job in window.render_queue_items)
    assert window.render_queue_items[0].output_path.endswith("render_orbit_choir.wav")
    assert window.render_queue_items[1].output_path.endswith("render_tape_orbit.wav")
    assert window.render_queue_items[2].output_path.endswith("render_broken_orbit.wav")

    window.close()


def test_start_render_queue_marks_queue_running_and_requests_next_job(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    window._persist_state = lambda: None
    source_path = tmp_path / "source.wav"
    _write_test_audio(source_path)

    window.input_edit.setText(str(source_path))
    window.output_edit.setText(str(tmp_path / "queued.wav"))
    window.render_queue_items = [window._current_render_job()]
    starts: list[str] = []
    window._start_next_render_job = lambda: starts.append("started")

    window._start_render_queue()

    assert window.render_queue_running is True
    assert starts == ["started"]

    window.close()


def test_save_and_load_project_roundtrip_restores_queue_and_recent_projects(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "source.wav"
    project_path = tmp_path / "session.findusstretch.json"
    _write_test_audio(source_path)
    window.recent_project_paths = []
    window._refresh_recent_projects_list()

    window.input_edit.setText(str(source_path))
    window.output_edit.setText(str(tmp_path / "render.wav"))
    window._load_waveform(str(source_path))
    window.stretch_slider.setValue(19)
    window.preview_start.setValue(0.2)
    window.preview_duration.setValue(0.4)
    window.loop_crossfade_spin.setValue(140.0)
    window.input_trim_slider.setValue(6)
    window.limiter_checkbox.setChecked(True)
    window.reverb_slider.setValue(35)
    window._store_compare_slot("A")
    window._queue_current_render()

    window._save_project_to_path(str(project_path))

    window.stretch_slider.setValue(7)
    window.preview_start.setValue(0.0)
    window.preview_duration.setValue(0.5)
    window.render_queue_items.clear()
    window._refresh_render_queue_list()

    window._load_project_from_path(str(project_path))

    assert window.current_project_path == str(project_path)
    assert window.recent_project_paths[0] == str(project_path)
    assert window.recent_projects_list.count() == 1
    assert window.stretch_slider.value() == 19
    assert window.preview_start.value() == 0.2
    assert window.preview_duration.value() == 0.4
    assert window.loop_crossfade_spin.value() == 140.0
    assert window.input_trim_slider.value() == 6
    assert window.limiter_checkbox.isChecked() is True
    assert window.compare_slots["A"] is not None
    assert len(window.render_queue_items) == 1

    window.close()


def test_project_load_creates_clean_undo_step(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "source.wav"
    project_path = tmp_path / "session.findusstretch.json"
    _write_test_audio(source_path)

    window.input_edit.setText(str(source_path))
    window._load_waveform(str(source_path))
    window.stretch_slider.setValue(19)
    window._save_project_to_path(str(project_path))

    window.stretch_slider.setValue(7)
    window._reset_workflow_history()

    window._load_project_from_path(str(project_path))

    assert "project load" in window.undo_action.toolTip().lower()

    window._undo_workflow()

    assert window.stretch_slider.value() == 7

    window.close()


def test_dropped_audio_loads_source_and_updates_recent_sources(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "drop_source.wav"
    _write_test_audio(source_path)
    window.recent_source_paths = []
    window._refresh_recent_sources_list()

    handled = window._handle_dropped_paths([str(source_path)])

    assert handled is True
    assert window.input_edit.text() == str(source_path)
    assert window.recent_source_paths[0] == str(source_path)
    assert window.recent_sources_list.count() == 1

    window.close()


def test_dropped_project_uses_project_loader_without_adding_recent_source(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    project_path = tmp_path / "session.findusstretch.json"
    window.recent_source_paths = []
    window._refresh_recent_sources_list()
    loaded_projects: list[str] = []
    window._load_project_from_path = lambda path: loaded_projects.append(path)

    handled = window._handle_dropped_paths([str(project_path)])

    assert handled is True
    assert loaded_projects == [str(project_path)]
    assert window.recent_source_paths == []

    window.close()


def test_unsupported_drop_sets_clear_status_message(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()

    handled = window._handle_dropped_paths([str(tmp_path / "notes.txt")])

    assert handled is False
    assert "ignored unsupported dropped file" in window.statusBar().currentMessage().lower()

    window.close()


def test_multi_file_drop_uses_first_supported_file(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_a = tmp_path / "a.wav"
    source_b = tmp_path / "b.wav"
    _write_test_audio(source_a)
    _write_test_audio(source_b)
    window.recent_source_paths = []
    window._refresh_recent_sources_list()

    handled = window._handle_dropped_paths(
        [str(tmp_path / "ignore.txt"), str(source_a), str(source_b)]
    )

    assert handled is True
    assert window.input_edit.text() == str(source_a)
    assert window.recent_source_paths[0] == str(source_a)
    assert "only the first supported dropped file was used" in window.statusBar().currentMessage().lower()

    window.close()


def test_drag_enter_shows_drop_hint_for_supported_file(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "drag.wav"
    _write_test_audio(source_path)

    class _FakeEvent:
        def __init__(self, paths: list[str]) -> None:
            self._paths = [QUrl.fromLocalFile(path) for path in paths]
            self.accepted = False
            self.ignored = False

        def mimeData(self):  # noqa: ANN001
            class _Mime:
                def __init__(self, urls) -> None:  # noqa: ANN001
                    self._urls = urls

                def hasUrls(self) -> bool:
                    return True

                def urls(self):  # noqa: ANN001
                    return self._urls

            return _Mime(self._paths)

        def acceptProposedAction(self) -> None:
            self.accepted = True

        def ignore(self) -> None:
            self.ignored = True

    event = _FakeEvent([str(source_path)])
    window.dragEnterEvent(event)

    assert event.accepted is True
    assert window.drop_hint_label.isHidden() is False
    assert "drop one audio file" in window.statusBar().currentMessage().lower()

    window.close()


def test_recent_sources_list_filters_missing_entries_on_refresh(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    existing = tmp_path / "exists.wav"
    missing = tmp_path / "missing.wav"
    _write_test_audio(existing)
    window.recent_source_paths = [str(existing), str(missing)]

    window._refresh_recent_sources_list()

    assert window.recent_source_paths == [str(existing)]
    assert window.recent_sources_list.count() == 1

    window.close()


def test_recent_source_actions_open_folder_and_clear_list(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    existing = tmp_path / "exists.wav"
    _write_test_audio(existing)
    window.recent_source_paths = [str(existing)]
    window._refresh_recent_sources_list()

    opened: list[str] = []
    original_open_url = QDesktopServices.openUrl
    QDesktopServices.openUrl = lambda url: opened.append(url.toLocalFile())  # type: ignore[assignment]
    try:
        window._open_selected_recent_source_folder()
    finally:
        QDesktopServices.openUrl = original_open_url  # type: ignore[assignment]

    assert [Path(path) for path in opened] == [existing.parent]

    window._clear_recent_sources()

    assert window.recent_source_paths == []
    assert window.recent_sources_list.count() == 0

    window.close()


def test_loading_project_with_missing_source_warns_without_crashing(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    project_path = tmp_path / "missing.findusstretch.json"
    missing_source = tmp_path / "missing_source.wav"

    window.preset_library.save_project(
        ProjectSession(
            input_path=str(missing_source),
            output_path=str(tmp_path / "render.wav"),
            render_output_mode="wet",
            preview_start=0.0,
            preview_length=2.5,
            stretch_factor=8.0,
            quality_profile=window._selected_profile(),
            effects=window._effect_settings(),
            selected_preset_name="Custom",
            compare_slot_a=None,
            compare_slot_b=None,
            render_queue=(),
            waveform_region_start=0.0,
            waveform_region_end=2.5,
            loop_enabled=False,
        ),
        project_path,
    )
    warnings: list[tuple[str, str]] = []
    window._show_warning = lambda title, message: warnings.append((title, message))

    window._load_project_from_path(str(project_path))

    assert warnings
    assert "missing" in warnings[0][0].lower()
    assert window.current_project_path == str(project_path)
    assert window.input_edit.text() == str(missing_source)
    assert window.waveform_overview is None

    window.close()


def test_preview_history_restores_and_replays_cached_preview_state(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "source.wav"
    _write_test_audio(source_path)
    window.input_edit.setText(str(source_path))
    window._load_waveform(str(source_path))
    window.stretch_slider.setValue(18)
    window.preview_start.setValue(0.3)
    window.preview_duration.setValue(1.4)
    preview = PreviewResult(
        audio=np.zeros((22050, 2), dtype=np.float32),
        sample_rate=22050,
        channels=2,
        preview_frames=22050,
        source_start_seconds=0.3,
        source_duration_seconds=1.4,
        stretch_factor=18.0,
    )
    play_calls: list[tuple[PreviewResult, bool]] = []
    window._play_preview_result = lambda result, from_cache=False, loop_restart=False: play_calls.append((result, from_cache))

    window._on_preview_complete(preview)
    window.stretch_slider.setValue(7)

    assert len(window.preview_history_entries) == 1

    window.preview_history_list.setCurrentRow(0)
    window._load_selected_preview_history(replay=True)

    assert window.stretch_slider.value() == 18
    assert window.current_preview is preview
    assert play_calls == [(preview, False), (preview, True)]

    window.close()


def test_preview_history_load_creates_clean_undo_step(tmp_path: Path) -> None:
    app = _app()
    window = MainWindow()
    source_path = tmp_path / "source.wav"
    _write_test_audio(source_path)
    window.input_edit.setText(str(source_path))
    window._load_waveform(str(source_path))
    preview = PreviewResult(
        audio=np.zeros((22050, 2), dtype=np.float32),
        sample_rate=22050,
        channels=2,
        preview_frames=22050,
        source_start_seconds=0.0,
        source_duration_seconds=2.5,
        stretch_factor=8.0,
    )
    window._on_preview_complete(preview)
    window._reset_workflow_history()

    window.stretch_slider.setValue(17)
    window.preview_history_list.setCurrentRow(0)
    window._load_selected_preview_history()

    assert "preview history load" in window.undo_action.toolTip().lower()

    window._undo_workflow()

    assert window.stretch_slider.value() == 17

    window.close()


def test_loop_crossfade_extends_loop_playback_without_invalidating_cached_preview() -> None:
    app = _app()
    window = MainWindow()
    preview = PreviewResult(
        audio=np.zeros((1000, 2), dtype=np.float32),
        sample_rate=1000,
        channels=2,
        preview_frames=1000,
        source_start_seconds=0.0,
        source_duration_seconds=1.0,
        stretch_factor=8.0,
    )
    played_shapes: list[int] = []
    window.preview_player.play = lambda audio, sample_rate, on_finished, **kwargs: played_shapes.append(audio.shape[0])
    window.current_preview = preview
    window.current_preview_key = ("cached",)
    window.loop_checkbox.setChecked(True)

    window.loop_crossfade_spin.setValue(120.0)

    assert window.current_preview is preview
    assert window.current_preview_key == ("cached",)

    window._play_preview_result(preview, from_cache=True)

    assert played_shapes == [1120]
    assert abs(window.current_playback_duration_seconds - 1.12) < 1e-9

    window.close()


def test_preview_player_releases_finished_playback_before_loop_restart() -> None:
    player = PreviewPlayer()
    callbacks: list[str] = []

    class _FakeSignal:
        def disconnect(self, callback) -> None:  # noqa: ANN001
            callbacks.append("disconnected")

    class _FakeSink:
        def __init__(self) -> None:
            self.stateChanged = _FakeSignal()
            self.stopped = False
            self.deleted = False

        def stop(self) -> None:
            self.stopped = True

        def deleteLater(self) -> None:
            self.deleted = True

    class _FakeBuffer:
        def __init__(self) -> None:
            self.closed = False
            self.deleted = False

        def close(self) -> None:
            self.closed = True

        def deleteLater(self) -> None:
            self.deleted = True

    finished_called: list[bool] = []
    sink = _FakeSink()
    buffer_device = _FakeBuffer()
    player.audio_sink = sink
    player.buffer_device = buffer_device
    player.byte_array = object()
    player._manual_stop = False
    player.on_finished = lambda: finished_called.append(player.audio_sink is None)

    player._on_state_changed(QAudio.State.IdleState)

    assert finished_called == [True]
    assert sink.stopped is True
    assert sink.deleted is True
    assert buffer_device.closed is True
    assert buffer_device.deleted is True
    assert callbacks == ["disconnected"]
    assert player.audio_sink is None
    assert player.buffer_device is None


def test_preview_transport_status_and_loop_indicator_are_clear() -> None:
    app = _app()
    window = MainWindow()

    window.waveform_overview = None
    window.waveform_widget.overview = None
    window.preview_start.setValue(1.25)
    window.preview_duration.setValue(2.5)
    window.loop_checkbox.setChecked(False)
    region = RegionSelection(1.25, 3.75)
    window._update_region_status(region)
    window._set_preview_state("idle")

    assert "Region 1.25s -> 3.75s" in window.region_status.text()
    assert "Preview idle." in window.preview_status_label.text()
    assert "2.50s selected" in window.preview_status_label.text()

    window.loop_checkbox.setChecked(True)

    assert window.loop_state_label.text() == "Loop on"
    assert "repeat until you stop it" in window.loop_state_label.toolTip()

    window.close()


def test_mark_dirty_clears_cached_preview_and_updates_status() -> None:
    app = _app()
    window = MainWindow()

    window.waveform_overview = None
    window.waveform_widget.overview = None
    window.preview_start.setValue(1.25)
    window.preview_duration.setValue(2.5)
    window.current_preview = PreviewResult(
        audio=[],
        sample_rate=48000,
        channels=2,
        preview_frames=48000,
        source_start_seconds=0.0,
        source_duration_seconds=2.5,
        stretch_factor=8.0,
    )
    window.current_preview_key = ("demo",)
    window._set_preview_state("ready", result=window.current_preview)

    window._mark_dirty()

    assert window.current_preview is None
    assert window.current_preview_key is None
    assert "Preview invalidated." in window.preview_status_label.text()

    window.close()


def test_mark_dirty_does_not_stop_active_preview_playback() -> None:
    app = _app()
    window = MainWindow()

    stop_calls: list[str] = []
    window.preview_player.is_active = lambda: True
    window.preview_player.stop = lambda: stop_calls.append("stop")
    window.current_preview = PreviewResult(
        audio=[],
        sample_rate=48000,
        channels=2,
        preview_frames=48000,
        source_start_seconds=0.0,
        source_duration_seconds=2.5,
        stretch_factor=8.0,
    )
    window.current_preview_key = ("demo",)

    window._mark_dirty()

    assert stop_calls == []
    assert window.current_preview is None
    assert window.current_preview_key is None
    assert "current playback will finish" in window.statusBar().currentMessage().lower()

    window.close()


def test_switching_tabs_preserves_cached_preview() -> None:
    app = _app()
    window = MainWindow()

    persist_calls: list[str] = []
    window._persist_state = lambda: persist_calls.append("persist")
    preview = PreviewResult(
        audio=[],
        sample_rate=48000,
        channels=2,
        preview_frames=48000,
        source_start_seconds=0.0,
        source_duration_seconds=2.5,
        stretch_factor=8.0,
    )
    window.current_preview = preview
    window.current_preview_key = ("demo",)
    window._set_preview_state("ready", result=preview)

    current_index = window.workspace_tabs.currentIndex()
    target_index = next(
        index
        for index in range(window.workspace_tabs.count())
        if index != current_index
    )
    window.workspace_tabs.setCurrentIndex(target_index)

    assert persist_calls == ["persist"]
    assert window.current_preview is preview
    assert window.current_preview_key == ("demo",)
    assert "Cached preview ready." in window.preview_status_label.text()

    window.close()


def test_waveform_zoom_and_fit_do_not_invalidate_cached_preview() -> None:
    app = _app()
    window = MainWindow()

    audio = np.sin(np.linspace(0.0, 4.0 * np.pi, 4000, endpoint=False))
    overview = build_waveform_overview(audio, 1000)
    window.waveform_widget.set_overview(overview)
    window.waveform_overview = overview
    window.waveform_widget.set_region(RegionSelection(0.8, 1.4), emit_signal=False)
    preview = PreviewResult(
        audio=[],
        sample_rate=48000,
        channels=2,
        preview_frames=48000,
        source_start_seconds=0.8,
        source_duration_seconds=0.6,
        stretch_factor=8.0,
    )
    window.current_preview = preview
    window.current_preview_key = ("demo",)
    original_region = window.waveform_widget.region
    original_key = window.current_preview_key

    initial_visible = window.waveform_widget.visible_range
    wheel_event = QWheelEvent(
        QPointF(40.0, 20.0),
        QPointF(40.0, 20.0),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )
    window.waveform_widget.wheelEvent(wheel_event)
    assert window.waveform_widget.visible_range.duration_seconds < initial_visible.duration_seconds
    assert window.waveform_widget.region == original_region
    assert window.current_preview is preview
    assert window.current_preview_key == original_key

    window.waveform_widget.fit_selection()
    assert window.waveform_widget.region == original_region
    assert window.current_preview is preview

    window.waveform_widget.fit_full_range()
    assert window.waveform_widget.region == original_region
    assert window.current_preview_key == original_key

    window.close()


def test_snap_to_grid_rounds_numeric_region_to_tenths() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")

    window.snap_to_grid_checkbox.setChecked(True)
    window.preview_start.setValue(1.23)
    window.preview_duration.setValue(2.17)

    assert window.preview_start.value() == 1.2
    assert window.preview_duration.value() == 2.2

    window.close()


def test_replay_last_preview_uses_cached_preview_without_rerender() -> None:
    app = _app()
    window = MainWindow()

    preview = PreviewResult(
        audio=[],
        sample_rate=48000,
        channels=2,
        preview_frames=48000,
        source_start_seconds=0.0,
        source_duration_seconds=2.5,
        stretch_factor=8.0,
    )
    play_calls: list[tuple[PreviewResult, bool]] = []
    window.current_preview = preview
    window.current_preview_key = ("demo",)
    window._play_preview_result = lambda result, from_cache=False, loop_restart=False: play_calls.append((result, from_cache))

    window._replay_last_preview()

    assert play_calls == [(preview, True)]

    window.close()


def test_preview_status_text_covers_cached_ready_and_stale_states() -> None:
    app = _app()
    window = MainWindow()

    preview = PreviewResult(
        audio=[],
        sample_rate=48000,
        channels=2,
        preview_frames=48000,
        source_start_seconds=0.0,
        source_duration_seconds=2.5,
        stretch_factor=8.0,
    )
    window.current_preview = preview
    window.current_preview_key = ("demo",)

    window._set_preview_state("ready", result=preview)
    assert "Cached preview ready." in window.preview_status_label.text()

    window.preview_player.is_active = lambda: True
    window._mark_dirty()
    assert "Current playback will finish" in window.preview_status_label.text()

    window.close()


def test_dirty_label_is_explicit_about_modified_preset_source() -> None:
    app = _app()
    window = MainWindow()
    window.input_edit.clear()
    window._clear_loaded_input("No waveform loaded")

    preset = window.preset_library.get_preset("Orbit Choir")
    assert preset is not None

    window.current_preset_name = preset.name
    window._apply_preset(preset)
    window._update_dirty_label()
    assert window.preset_dirty_label.text() == f"Preset: {preset.name}"

    window.reverb_slider.setValue(window.reverb_slider.value() + 5)

    assert window.preset_dirty_label.text() == f"Preset: modified from {preset.name}"

    window.close()


def test_update_command_state_shows_restart_preview_while_playing() -> None:
    app = _app()
    window = MainWindow()

    original_is_active = window.preview_player.is_active
    window.preview_player.is_active = lambda: True

    window._update_command_state()

    assert window.preview_button.text() == "Restart Preview"
    assert window.stop_button.isEnabled() is True

    window.preview_player.is_active = original_is_active
    window.close()


def test_main_window_exposes_audio_routing_controls() -> None:
    app = _app()
    window = MainWindow()

    backend_labels = [window.audio_backend_combo.itemText(index) for index in range(window.audio_backend_combo.count())]

    assert "Auto" in backend_labels
    assert "PortAudio" in backend_labels
    assert "Qt fallback" in backend_labels
    assert window.output_device_combo.count() >= 1
    assert window.preview_output_channels_combo.count() >= 1
    assert window.detected_host_apis_label.text() != ""
    assert "detected" in window.driver_status_label.text().lower() or "using" in window.driver_status_label.text().lower()

    window.close()
