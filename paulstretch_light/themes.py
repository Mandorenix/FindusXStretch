from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QWidget


DEFAULT_THEME_NAME = "studio"


@dataclass(frozen=True)
class WaveformTheme:
    background: str
    border: str
    empty_text: str
    content_background: str
    center_line: str
    waveform_line: str
    selection_fill: tuple[int, int, int, int]
    selection_border: str
    playhead: str
    text: str


@dataclass(frozen=True)
class ThemeDefinition:
    name: str
    label: str
    font_family: str
    font_size: int
    window: str
    panel: str
    panel_alt: str
    text: str
    muted_text: str
    accent: str
    accent_soft: str
    border: str
    input_bg: str
    button_bg: str
    button_hover: str
    button_pressed: str
    disabled_bg: str
    disabled_text: str
    progress_bg: str
    selection_bg: str
    selection_text: str
    radius: int
    padding: int
    waveform: WaveformTheme


THEMES: dict[str, ThemeDefinition] = {
    "studio": ThemeDefinition(
        name="studio",
        label="Studio",
        font_family="'Segoe UI', 'Trebuchet MS', sans-serif",
        font_size=10,
        window="#1c1d21",
        panel="#25272c",
        panel_alt="#2f3238",
        text="#f2f2f3",
        muted_text="#b8bcc7",
        accent="#f58d3d",
        accent_soft="#6f3d1e",
        border="#3f434b",
        input_bg="#17181c",
        button_bg="#32353b",
        button_hover="#3b3f46",
        button_pressed="#26292e",
        disabled_bg="#2a2c31",
        disabled_text="#7f848d",
        progress_bg="#15161a",
        selection_bg="#f58d3d",
        selection_text="#111215",
        radius=4,
        padding=8,
        waveform=WaveformTheme(
            background="#17181c",
            border="#44484f",
            empty_text="#b6bec9",
            content_background="#111216",
            center_line="#484f5b",
            waveform_line="#ffb067",
            selection_fill=(245, 141, 61, 58),
            selection_border="#f6a45f",
            playhead="#fff27a",
            text="#f0f0f2",
        ),
    ),
    "16bit": ThemeDefinition(
        name="16bit",
        label="16-bit",
        font_family="'Trebuchet MS', 'Verdana', sans-serif",
        font_size=10,
        window="#1e2340",
        panel="#28315a",
        panel_alt="#34407a",
        text="#fef6d8",
        muted_text="#d7d2b8",
        accent="#ff7f50",
        accent_soft="#874957",
        border="#7dc4ff",
        input_bg="#151a31",
        button_bg="#4b5bb4",
        button_hover="#6273d2",
        button_pressed="#38478f",
        disabled_bg="#353d72",
        disabled_text="#b2b0b5",
        progress_bg="#14192d",
        selection_bg="#ff7f50",
        selection_text="#101321",
        radius=6,
        padding=9,
        waveform=WaveformTheme(
            background="#151a31",
            border="#7dc4ff",
            empty_text="#f5f0cd",
            content_background="#0f1330",
            center_line="#5763bb",
            waveform_line="#7ef2ff",
            selection_fill=(255, 127, 80, 64),
            selection_border="#ffd166",
            playhead="#fff8a6",
            text="#fdf8dd",
        ),
    ),
    "8bit": ThemeDefinition(
        name="8bit",
        label="8-bit",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#101b10",
        panel="#152715",
        panel_alt="#1d321d",
        text="#e8f6b0",
        muted_text="#a9c484",
        accent="#7dfb4f",
        accent_soft="#315e27",
        border="#9ee26f",
        input_bg="#0b140b",
        button_bg="#234523",
        button_hover="#2e5d2e",
        button_pressed="#173117",
        disabled_bg="#1b2a1b",
        disabled_text="#6f8967",
        progress_bg="#091009",
        selection_bg="#7dfb4f",
        selection_text="#081008",
        radius=0,
        padding=6,
        waveform=WaveformTheme(
            background="#091109",
            border="#9ee26f",
            empty_text="#d8f69d",
            content_background="#030803",
            center_line="#3f6e3f",
            waveform_line="#7dfb4f",
            selection_fill=(125, 251, 79, 46),
            selection_border="#d9ff7a",
            playhead="#fff29a",
            text="#ecffbf",
        ),
    ),
    "c64": ThemeDefinition(
        name="c64",
        label="C64",
        font_family="'Courier New', 'Consolas', monospace",
        font_size=10,
        window="#2c2c74",
        panel="#3b3b8f",
        panel_alt="#4d4daa",
        text="#8fe38f",
        muted_text="#b8d9a8",
        accent="#72ffff",
        accent_soft="#355f8a",
        border="#7fbfff",
        input_bg="#23235f",
        button_bg="#5050b4",
        button_hover="#6363ca",
        button_pressed="#3d3d92",
        disabled_bg="#2d2d6f",
        disabled_text="#8aa0a8",
        progress_bg="#1c1c48",
        selection_bg="#72ffff",
        selection_text="#111133",
        radius=0,
        padding=6,
        waveform=WaveformTheme(
            background="#1c1c48",
            border="#8cb3ff",
            empty_text="#aee8ae",
            content_background="#14143c",
            center_line="#5760c4",
            waveform_line="#8fe38f",
            selection_fill=(114, 255, 255, 44),
            selection_border="#72ffff",
            playhead="#fff78f",
            text="#d6ffd6",
        ),
    ),
    "amiga": ThemeDefinition(
        name="amiga",
        label="Amiga",
        font_family="'Trebuchet MS', 'Verdana', sans-serif",
        font_size=10,
        window="#0f3a57",
        panel="#14506f",
        panel_alt="#1c668b",
        text="#f1f4ff",
        muted_text="#c1d0e7",
        accent="#ff6f91",
        accent_soft="#8b3b68",
        border="#7fe7ff",
        input_bg="#0c2b41",
        button_bg="#2b7fa1",
        button_hover="#3998bf",
        button_pressed="#1f627e",
        disabled_bg="#26455f",
        disabled_text="#96a6b7",
        progress_bg="#0b2131",
        selection_bg="#ff6f91",
        selection_text="#0f1722",
        radius=4,
        padding=8,
        waveform=WaveformTheme(
            background="#0b2131",
            border="#7fe7ff",
            empty_text="#d6e3ff",
            content_background="#071823",
            center_line="#287194",
            waveform_line="#8fe9ff",
            selection_fill=(255, 111, 145, 54),
            selection_border="#ffd166",
            playhead="#fff7a1",
            text="#f3f7ff",
        ),
    ),
    "sega": ThemeDefinition(
        name="sega",
        label="Sega",
        font_family="'Segoe UI', 'Trebuchet MS', sans-serif",
        font_size=10,
        window="#0b1f4f",
        panel="#12306f",
        panel_alt="#184498",
        text="#f7fbff",
        muted_text="#d6deef",
        accent="#18d8ff",
        accent_soft="#1f5f8e",
        border="#9cc8ff",
        input_bg="#091739",
        button_bg="#204f9d",
        button_hover="#2c65c2",
        button_pressed="#173b78",
        disabled_bg="#233d63",
        disabled_text="#99a8bc",
        progress_bg="#071127",
        selection_bg="#18d8ff",
        selection_text="#07121e",
        radius=3,
        padding=8,
        waveform=WaveformTheme(
            background="#071127",
            border="#9cc8ff",
            empty_text="#dbe9ff",
            content_background="#050d1f",
            center_line="#305aa6",
            waveform_line="#18d8ff",
            selection_fill=(24, 216, 255, 52),
            selection_border="#ffffff",
            playhead="#ffe66d",
            text="#f8fbff",
        ),
    ),
    "arcade": ThemeDefinition(
        name="arcade",
        label="Arcade",
        font_family="'Trebuchet MS', 'Verdana', sans-serif",
        font_size=10,
        window="#1b1026",
        panel="#2a173e",
        panel_alt="#3a2156",
        text="#ffeef8",
        muted_text="#d2b8d7",
        accent="#ff4d6d",
        accent_soft="#6b2948",
        border="#ffd166",
        input_bg="#130b1d",
        button_bg="#4d2f6f",
        button_hover="#633b8e",
        button_pressed="#351f4e",
        disabled_bg="#2a2035",
        disabled_text="#96829a",
        progress_bg="#0d0714",
        selection_bg="#ff4d6d",
        selection_text="#120813",
        radius=6,
        padding=8,
        waveform=WaveformTheme(
            background="#0d0714",
            border="#ffd166",
            empty_text="#ffdff0",
            content_background="#09040d",
            center_line="#6d3b7d",
            waveform_line="#ff8fab",
            selection_fill=(255, 77, 109, 58),
            selection_border="#ffd166",
            playhead="#7df9ff",
            text="#fff2f9",
        ),
    ),
    "amber": ThemeDefinition(
        name="amber",
        label="Amber",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#16110a",
        panel="#20170d",
        panel_alt="#2c1f10",
        text="#ffcc73",
        muted_text="#caa167",
        accent="#ff9f1c",
        accent_soft="#71430f",
        border="#b9781d",
        input_bg="#120d08",
        button_bg="#3a260e",
        button_hover="#533514",
        button_pressed="#261908",
        disabled_bg="#24190f",
        disabled_text="#8a6c4b",
        progress_bg="#0d0905",
        selection_bg="#ff9f1c",
        selection_text="#120b04",
        radius=2,
        padding=7,
        waveform=WaveformTheme(
            background="#0d0905",
            border="#b9781d",
            empty_text="#f3bf67",
            content_background="#070503",
            center_line="#6c4a1d",
            waveform_line="#ffcc73",
            selection_fill=(255, 159, 28, 48),
            selection_border="#ffe0a3",
            playhead="#fff4c2",
            text="#ffd891",
        ),
    ),
    "ice": ThemeDefinition(
        name="ice",
        label="Ice",
        font_family="'Segoe UI', 'Verdana', sans-serif",
        font_size=10,
        window="#dcebf4",
        panel="#edf7fd",
        panel_alt="#cde3f0",
        text="#183245",
        muted_text="#4d6b7f",
        accent="#00a6d6",
        accent_soft="#7fbfd7",
        border="#8bb9cc",
        input_bg="#f7fcff",
        button_bg="#d0e8f3",
        button_hover="#bee0ef",
        button_pressed="#b0d3e3",
        disabled_bg="#d4dee4",
        disabled_text="#7f95a3",
        progress_bg="#c6dce8",
        selection_bg="#00a6d6",
        selection_text="#f8feff",
        radius=8,
        padding=9,
        waveform=WaveformTheme(
            background="#e8f4fb",
            border="#8bb9cc",
            empty_text="#49697a",
            content_background="#f7fcff",
            center_line="#9dc2d3",
            waveform_line="#00a6d6",
            selection_fill=(0, 166, 214, 36),
            selection_border="#0c6f8f",
            playhead="#ff9f1c",
            text="#1f3d50",
        ),
    ),
    "sunset": ThemeDefinition(
        name="sunset",
        label="Sunset",
        font_family="'Trebuchet MS', 'Segoe UI', sans-serif",
        font_size=10,
        window="#2f162f",
        panel="#472048",
        panel_alt="#5f2e5d",
        text="#fff0cf",
        muted_text="#d6b8bf",
        accent="#ff9f1c",
        accent_soft="#8a4a28",
        border="#ffcd70",
        input_bg="#241023",
        button_bg="#6b315d",
        button_hover="#86406f",
        button_pressed="#502344",
        disabled_bg="#3c2438",
        disabled_text="#a0898e",
        progress_bg="#1d0c1d",
        selection_bg="#ff9f1c",
        selection_text="#200d11",
        radius=7,
        padding=8,
        waveform=WaveformTheme(
            background="#1d0c1d",
            border="#ffcd70",
            empty_text="#ffe3c1",
            content_background="#140714",
            center_line="#7a3f6a",
            waveform_line="#ffb347",
            selection_fill=(255, 159, 28, 44),
            selection_border="#ffd166",
            playhead="#7df9ff",
            text="#fff0d4",
        ),
    ),
    "dos": ThemeDefinition(
        name="dos",
        label="DOS",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#050505",
        panel="#0b0b0b",
        panel_alt="#111111",
        text="#b6ff9d",
        muted_text="#7fc76d",
        accent="#4cff4c",
        accent_soft="#1e4f1e",
        border="#2d8f2d",
        input_bg="#030303",
        button_bg="#0f180f",
        button_hover="#132413",
        button_pressed="#081008",
        disabled_bg="#0d0d0d",
        disabled_text="#517051",
        progress_bg="#020202",
        selection_bg="#4cff4c",
        selection_text="#020802",
        radius=0,
        padding=6,
        waveform=WaveformTheme(
            background="#020202",
            border="#2d8f2d",
            empty_text="#93d787",
            content_background="#010101",
            center_line="#184718",
            waveform_line="#7dff7d",
            selection_fill=(76, 255, 76, 42),
            selection_border="#c7ffc7",
            playhead="#fff28c",
            text="#c6ffc6",
        ),
    ),
    "gameboy": ThemeDefinition(
        name="gameboy",
        label="Game Boy",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#889878",
        panel="#9bbc72",
        panel_alt="#7f8f69",
        text="#203018",
        muted_text="#3d5033",
        accent="#0f380f",
        accent_soft="#4e6a43",
        border="#306230",
        input_bg="#b8c49a",
        button_bg="#7c8f57",
        button_hover="#90a565",
        button_pressed="#66784a",
        disabled_bg="#8f9a78",
        disabled_text="#51614e",
        progress_bg="#71835a",
        selection_bg="#0f380f",
        selection_text="#d7e2b8",
        radius=2,
        padding=7,
        waveform=WaveformTheme(
            background="#95a874",
            border="#306230",
            empty_text="#314129",
            content_background="#b8c49a",
            center_line="#68775a",
            waveform_line="#0f380f",
            selection_fill=(15, 56, 15, 36),
            selection_border="#203018",
            playhead="#1f2f17",
            text="#203018",
        ),
    ),
    "nes": ThemeDefinition(
        name="nes",
        label="NES",
        font_family="'Trebuchet MS', 'Verdana', sans-serif",
        font_size=10,
        window="#202028",
        panel="#2f2f37",
        panel_alt="#444450",
        text="#f5f5f0",
        muted_text="#c4c4bc",
        accent="#e84a5f",
        accent_soft="#7a2f3f",
        border="#f7d774",
        input_bg="#16161b",
        button_bg="#575763",
        button_hover="#6b6b79",
        button_pressed="#40404a",
        disabled_bg="#34343b",
        disabled_text="#8f8f93",
        progress_bg="#121216",
        selection_bg="#e84a5f",
        selection_text="#fdf7da",
        radius=2,
        padding=7,
        waveform=WaveformTheme(
            background="#121216",
            border="#f7d774",
            empty_text="#ececdf",
            content_background="#0d0d10",
            center_line="#555560",
            waveform_line="#f7d774",
            selection_fill=(232, 74, 95, 46),
            selection_border="#fff2a6",
            playhead="#7dd3fc",
            text="#f6f6ef",
        ),
    ),
    "snes": ThemeDefinition(
        name="snes",
        label="SNES",
        font_family="'Trebuchet MS', 'Verdana', sans-serif",
        font_size=10,
        window="#2b2b38",
        panel="#39394a",
        panel_alt="#4d4d63",
        text="#f2f2f8",
        muted_text="#cacad8",
        accent="#9b5de5",
        accent_soft="#5c3a88",
        border="#72efdd",
        input_bg="#1f1f2b",
        button_bg="#5c5c78",
        button_hover="#717190",
        button_pressed="#474760",
        disabled_bg="#343447",
        disabled_text="#9292a7",
        progress_bg="#171720",
        selection_bg="#9b5de5",
        selection_text="#f5f1ff",
        radius=6,
        padding=8,
        waveform=WaveformTheme(
            background="#171720",
            border="#72efdd",
            empty_text="#ececfa",
            content_background="#101018",
            center_line="#5d5d79",
            waveform_line="#72efdd",
            selection_fill=(155, 93, 229, 46),
            selection_border="#cdb4ff",
            playhead="#ffd166",
            text="#f5f5fb",
        ),
    ),
    "playstation": ThemeDefinition(
        name="playstation",
        label="PlayStation",
        font_family="'Segoe UI', 'Trebuchet MS', sans-serif",
        font_size=10,
        window="#e7eaee",
        panel="#f4f5f7",
        panel_alt="#d8dde4",
        text="#1a2634",
        muted_text="#596776",
        accent="#d90429",
        accent_soft="#8d3b4a",
        border="#9aa5b1",
        input_bg="#ffffff",
        button_bg="#dfe4ea",
        button_hover="#d1d9e1",
        button_pressed="#c4cdd7",
        disabled_bg="#d8dde2",
        disabled_text="#8a96a1",
        progress_bg="#cfd6de",
        selection_bg="#d90429",
        selection_text="#ffffff",
        radius=8,
        padding=9,
        waveform=WaveformTheme(
            background="#eef1f5",
            border="#9aa5b1",
            empty_text="#5e6c78",
            content_background="#ffffff",
            center_line="#bcc6cf",
            waveform_line="#0070f3",
            selection_fill=(217, 4, 41, 34),
            selection_border="#d90429",
            playhead="#f4c542",
            text="#1f2b38",
        ),
    ),
    "tracker": ThemeDefinition(
        name="tracker",
        label="Tracker",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#10131a",
        panel="#171c26",
        panel_alt="#232b38",
        text="#d7ecff",
        muted_text="#8ba6bf",
        accent="#00e5ff",
        accent_soft="#145261",
        border="#3388aa",
        input_bg="#0b0f15",
        button_bg="#1f2834",
        button_hover="#293443",
        button_pressed="#151d26",
        disabled_bg="#171b22",
        disabled_text="#6c7e8d",
        progress_bg="#07090d",
        selection_bg="#00e5ff",
        selection_text="#041217",
        radius=2,
        padding=6,
        waveform=WaveformTheme(
            background="#07090d",
            border="#3388aa",
            empty_text="#92b9cf",
            content_background="#040608",
            center_line="#24475b",
            waveform_line="#00e5ff",
            selection_fill=(0, 229, 255, 38),
            selection_border="#9bf6ff",
            playhead="#ffd166",
            text="#d7ecff",
        ),
    ),
    "matrix": ThemeDefinition(
        name="matrix",
        label="Matrix",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#030503",
        panel="#071007",
        panel_alt="#0a160a",
        text="#7dff7d",
        muted_text="#53b653",
        accent="#00ff41",
        accent_soft="#124d21",
        border="#1d7a34",
        input_bg="#010301",
        button_bg="#0b190b",
        button_hover="#102510",
        button_pressed="#061006",
        disabled_bg="#081008",
        disabled_text="#3f6e3f",
        progress_bg="#010201",
        selection_bg="#00ff41",
        selection_text="#020402",
        radius=1,
        padding=6,
        waveform=WaveformTheme(
            background="#010201",
            border="#1d7a34",
            empty_text="#67cf67",
            content_background="#000100",
            center_line="#0c3515",
            waveform_line="#00ff41",
            selection_fill=(0, 255, 65, 34),
            selection_border="#b8ffb8",
            playhead="#e3ff73",
            text="#92ff92",
        ),
    ),
    "crtgreen": ThemeDefinition(
        name="crtgreen",
        label="CRT Green",
        font_family="'Consolas', 'Courier New', monospace",
        font_size=10,
        window="#0c120c",
        panel="#121a12",
        panel_alt="#1b261b",
        text="#b9ffb9",
        muted_text="#7db27d",
        accent="#85ff85",
        accent_soft="#426842",
        border="#5f9b5f",
        input_bg="#080d08",
        button_bg="#1a281a",
        button_hover="#243624",
        button_pressed="#121d12",
        disabled_bg="#111711",
        disabled_text="#577457",
        progress_bg="#050805",
        selection_bg="#85ff85",
        selection_text="#071007",
        radius=3,
        padding=6,
        waveform=WaveformTheme(
            background="#050805",
            border="#5f9b5f",
            empty_text="#a6e8a6",
            content_background="#020402",
            center_line="#294529",
            waveform_line="#b9ffb9",
            selection_fill=(133, 255, 133, 30),
            selection_border="#d5ffd5",
            playhead="#fff2a6",
            text="#cbffcb",
        ),
    ),
}


def available_theme_names() -> tuple[str, ...]:
    return tuple(THEMES.keys())


def get_theme_definition(name: str) -> ThemeDefinition:
    return THEMES[normalize_theme_name(name)]


def normalize_theme_name(name: object) -> str:
    if isinstance(name, str):
        normalized = name.strip().lower()
        if normalized in THEMES:
            return normalized
    return DEFAULT_THEME_NAME


def clamp_ui_scale_percent(value: object) -> int:
    try:
        scale = int(round(float(value)))
    except (TypeError, ValueError):
        scale = 100
    return max(50, min(200, scale))


class ThemeManager:
    def __init__(self, application: QApplication | None = None) -> None:
        self.application = application or QApplication.instance()
        self._current_theme = get_theme_definition(DEFAULT_THEME_NAME)
        self._ui_scale_percent = 100

    @property
    def current_theme(self) -> ThemeDefinition:
        return self._current_theme

    @property
    def ui_scale_percent(self) -> int:
        return self._ui_scale_percent

    def apply_theme(
        self,
        name: str,
        *,
        root: QWidget | None = None,
        waveform_widget: QWidget | None = None,
        ui_scale_percent: int = 100,
    ) -> ThemeDefinition:
        theme = get_theme_definition(name)
        self._current_theme = theme
        self._ui_scale_percent = clamp_ui_scale_percent(ui_scale_percent)
        scale_factor = self._ui_scale_percent / 100.0

        if self.application is not None:
            self.application.setPalette(_build_palette(theme))
            font = QFont(_primary_font_family(theme.font_family))
            font.setPointSizeF(theme.font_size * scale_factor)
            self.application.setFont(font)
            self.application.setStyleSheet(_build_stylesheet(theme, self._ui_scale_percent))

        if waveform_widget is not None and hasattr(waveform_widget, "set_theme"):
            waveform_widget.set_theme(theme.waveform)

        if root is not None:
            root.setProperty("themeName", theme.name)
            root.setProperty("uiScalePercent", self._ui_scale_percent)
            root.style().unpolish(root)
            root.style().polish(root)
            root.update()

        return theme


def _build_palette(theme: ThemeDefinition) -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(theme.window))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text))
    palette.setColor(QPalette.ColorRole.Base, QColor(theme.input_bg))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.panel_alt))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme.panel))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.text))
    palette.setColor(QPalette.ColorRole.Text, QColor(theme.text))
    palette.setColor(QPalette.ColorRole.Button, QColor(theme.button_bg))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(theme.selection_text))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.selection_bg))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme.selection_text))
    palette.setColor(QPalette.ColorRole.Light, QColor(theme.button_hover))
    palette.setColor(QPalette.ColorRole.Mid, QColor(theme.border))
    palette.setColor(QPalette.ColorRole.Dark, QColor(theme.progress_bg))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(theme.muted_text))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(theme.disabled_text))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(theme.disabled_text))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(theme.disabled_text))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(theme.disabled_bg))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(theme.disabled_bg))
    return palette


def _build_stylesheet(theme: ThemeDefinition, ui_scale_percent: int = 100) -> str:
    scale_factor = clamp_ui_scale_percent(ui_scale_percent) / 100.0
    radius = _scale(theme.radius, scale_factor)
    padding = _scale(theme.padding, scale_factor)
    toolbar_spacing = _scale(6, scale_factor)
    toolbar_padding = _scale(4, scale_factor)
    groove_height = _scale(8, scale_factor)
    slider_handle = _scale(16, scale_factor)
    min_control_height = _scale(24, scale_factor)
    min_button_width = _scale(88, scale_factor)
    combo_drop_width = _scale(24, scale_factor)
    return f"""
QWidget {{
    background-color: {theme.window};
    color: {theme.text};
    font-size: {theme.font_size * scale_factor:.2f}pt;
}}
QMainWindow, QStatusBar {{
    background-color: {theme.window};
}}
QToolBar {{
    background-color: {theme.panel};
    border: 1px solid {theme.border};
    spacing: {toolbar_spacing}px;
    padding: {toolbar_padding}px;
}}
QToolBar::separator {{
    background: {theme.border};
    width: 1px;
    margin: {toolbar_padding}px {toolbar_spacing}px;
}}
QTabWidget::pane, QListWidget, QLineEdit, QComboBox, QDoubleSpinBox, QProgressBar {{
    background-color: {theme.panel};
    border: 1px solid {theme.border};
    border-radius: {radius}px;
}}
QTabBar::tab {{
    background-color: {theme.panel_alt};
    color: {theme.muted_text};
    border: 1px solid {theme.border};
    border-bottom: 0;
    border-top-left-radius: {radius}px;
    border-top-right-radius: {radius}px;
    padding: {max(_scale(4, scale_factor), padding - _scale(2, scale_factor))}px {padding + _scale(2, scale_factor)}px;
    margin-right: {_scale(2, scale_factor)}px;
}}
QTabBar::tab:selected {{
    background-color: {theme.panel};
    color: {theme.text};
}}
QPushButton {{
    background-color: {theme.button_bg};
    color: {theme.text};
    border: 1px solid {theme.border};
    border-radius: {radius}px;
    padding: {max(_scale(5, scale_factor), padding - _scale(1, scale_factor))}px {padding + _scale(4, scale_factor)}px;
    min-height: {min_control_height}px;
    min-width: {min_button_width}px;
}}
QPushButton:hover {{
    background-color: {theme.button_hover};
}}
QPushButton:pressed {{
    background-color: {theme.button_pressed};
}}
QPushButton:disabled, QLineEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled, QSlider:disabled, QListWidget:disabled {{
    background-color: {theme.disabled_bg};
    color: {theme.disabled_text};
    border-color: {theme.border};
}}
QLineEdit, QComboBox, QDoubleSpinBox, QListWidget {{
    background-color: {theme.input_bg};
    color: {theme.text};
    selection-background-color: {theme.selection_bg};
    selection-color: {theme.selection_text};
    padding: {max(_scale(4, scale_factor), padding - _scale(2, scale_factor))}px {max(_scale(6, scale_factor), padding)}px;
    min-height: {min_control_height}px;
}}
QLineEdit {{
    qproperty-clearButtonEnabled: true;
}}
QComboBox {{
    padding-right: {padding + _scale(20, scale_factor)}px;
}}
QComboBox QAbstractItemView {{
    background-color: {theme.panel};
    color: {theme.text};
    border: 1px solid {theme.border};
    selection-background-color: {theme.selection_bg};
    selection-color: {theme.selection_text};
}}
QComboBox::drop-down {{
    background-color: {theme.button_bg};
    border-left: 1px solid {theme.border};
    border-top-right-radius: {radius}px;
    border-bottom-right-radius: {radius}px;
    border: 0;
    width: {combo_drop_width}px;
}}
QSlider::groove:horizontal {{
    height: {groove_height}px;
    background: {theme.progress_bg};
    border: 1px solid {theme.border};
    border-radius: {max(0, radius - 1)}px;
}}
QSlider::sub-page:horizontal {{
    background: {theme.accent};
    border-radius: {max(0, radius - 1)}px;
}}
QSlider::handle:horizontal {{
    background: {theme.selection_text};
    border: 2px solid {theme.accent};
    width: {slider_handle}px;
    margin: -{_scale(6, scale_factor)}px 0;
    border-radius: {radius}px;
}}
QProgressBar {{
    text-align: center;
    background-color: {theme.progress_bg};
    color: {theme.text};
}}
QProgressBar::chunk {{
    background-color: {theme.accent};
}}
QCheckBox::indicator {{
    width: {slider_handle}px;
    height: {slider_handle}px;
    border: 1px solid {theme.border};
    background: {theme.input_bg};
}}
QCheckBox::indicator:checked {{
    background: {theme.accent};
}}
QLabel[muted="true"] {{
    color: {theme.muted_text};
}}
"""


def _primary_font_family(font_family: str) -> str:
    return font_family.split(",")[0].strip().strip("'\"")


def _scale(value: int, factor: float) -> int:
    return max(0, int(round(value * factor)))
