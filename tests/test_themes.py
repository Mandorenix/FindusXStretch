from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from paulstretch_light.themes import DEFAULT_THEME_NAME, ThemeManager, available_theme_names


class _WaveformProbe:
    def __init__(self) -> None:
        self.theme = None

    def set_theme(self, theme) -> None:  # noqa: ANN001
        self.theme = theme


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_theme_manager_applies_selected_theme_to_root_and_waveform() -> None:
    app = _app()
    manager = ThemeManager(app)
    root = QWidget()
    waveform = _WaveformProbe()

    applied = manager.apply_theme("8bit", root=root, waveform_widget=waveform, ui_scale_percent=150)

    assert applied.name == "8bit"
    assert manager.current_theme.name == "8bit"
    assert manager.ui_scale_percent == 150
    assert root.property("themeName") == "8bit"
    assert root.property("uiScalePercent") == 150
    assert waveform.theme == applied.waveform


def test_theme_manager_falls_back_to_default_theme() -> None:
    app = _app()
    manager = ThemeManager(app)

    applied = manager.apply_theme("unknown-theme")

    assert applied.name == DEFAULT_THEME_NAME


def test_available_theme_names_include_extended_variants() -> None:
    names = set(available_theme_names())

    assert "studio" in names
    assert "8bit" in names
    assert "16bit" in names
    assert "c64" in names
    assert "amiga" in names
    assert "sega" in names
    assert "arcade" in names
    assert "amber" in names
    assert "ice" in names
    assert "sunset" in names
    assert "dos" in names
    assert "gameboy" in names
    assert "nes" in names
    assert "snes" in names
    assert "playstation" in names
    assert "tracker" in names
    assert "matrix" in names
    assert "crtgreen" in names
