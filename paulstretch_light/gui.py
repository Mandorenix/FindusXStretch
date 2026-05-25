from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import random
import sys

import numpy as np

from PySide6.QtCore import QBuffer, QByteArray, QElapsedTimer, QIODevice, QObject, QPointF, QRectF, QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QColor, QDesktopServices, QDragEnterEvent, QDropEvent, QFont, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtGui import QKeySequence
from PySide6.QtMultimedia import QAudio, QAudioFormat, QAudioSink, QMediaDevices
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSlider,
    QStatusBar,
    QStyle,
    QSplashScreen,
    QTabBar,
    QTabWidget,
    QTextBrowser,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .dsp import SAFETY_LIMITER_CEILING_DB, EffectSettings, FilterMode, QualityProfile, build_loop_crossfade_audio
from .preset_library import APP_STATE_PATH, AppPreset, AppState, CompareSlotState, PresetLibrary
from .preset_library import ProjectSession, QueuedRenderJob
from .recording import (
    AUDIO_BACKEND_AUTO,
    AUDIO_BACKEND_PORTAUDIO,
    AUDIO_BACKEND_QT,
    RecordingConfig,
    RecordingController,
    RecentTake,
    RecordingResult,
    channel_options,
    device_details,
    find_audio_device,
    filter_existing_recent_takes,
    list_audio_backends,
    list_audio_routing,
    merge_recent_takes,
    next_available_recording_path,
    output_device_details,
    remove_recent_take,
    resolve_audio_backend,
    resolve_qt_output_device,
    recent_take_from_result,
    rename_take_file,
    suggested_recording_path,
)
from .renderer import (
    PreviewConfig,
    PreviewResult,
    RenderConfig,
    RenderOutputMode,
    RenderResult,
    RenderStatus,
    load_waveform_overview,
    render_preview,
    render_output_mode_from_value,
    render_to_wav,
)
from .themes import (
    DEFAULT_THEME_NAME,
    ThemeManager,
    WaveformTheme,
    available_theme_names,
    clamp_ui_scale_percent,
    get_theme_definition,
)
from .waveform import RegionSelection, WaveformOverview

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None

try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    APP_ROOT = Path(sys._MEIPASS)
else:
    APP_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = APP_ROOT / "assets"
DEFAULT_APP_ICON_PATH = ASSETS_DIR / "findus_stretching_icon.png"
STARTUP_SPLASH_VARIANT_PATHS = (
    ASSETS_DIR / "icon_variants" / "findus_cat_classic.png",
    ASSETS_DIR / "icon_variants" / "findus_cat_midnight.png",
    ASSETS_DIR / "icon_variants" / "findus_cat_stamp.png",
    ASSETS_DIR / "icon_variants" / "findus_cat_orbit.png",
)
STARTUP_SPLASH_ACCENTS = {
    "findus_cat_classic": QColor("#7eff6f"),
    "findus_cat_midnight": QColor("#27ebff"),
    "findus_cat_stamp": QColor("#d8b266"),
    "findus_cat_orbit": QColor("#f0b14f"),
}
STARTUP_SPLASH_STYLES = {
    "findus_cat_classic": "spiral",
    "findus_cat_midnight": "neon_ring",
    "findus_cat_stamp": "stamp_pulse",
    "findus_cat_orbit": "orbit_arc",
}


class StartupSplashScreen(QSplashScreen):
    def __init__(self, art_path: Path) -> None:
        super().__init__(QPixmap())
        self.art_path = art_path
        self.message = "Loading startup..."
        self.progress = 0
        self.loader_accent = self._resolve_loader_accent()
        self.loader_style = self._resolve_loader_style()
        self.loader_phase = 0
        self.loader_timer = QTimer(self)
        self.loader_timer.setInterval(90)
        self.loader_timer.timeout.connect(self.advance_loader)
        self.setPixmap(self._render_pixmap())

    def show_stage(self, message: str, progress: int) -> None:
        self.message = message
        self.progress = max(0, min(100, int(progress)))
        self.advance_loader()

    def advance_loader(self) -> None:
        self.loader_phase = (self.loader_phase + 1) % 24
        self.setPixmap(self._render_pixmap())

    def showEvent(self, event) -> None:  # noqa: ANN001
        super().showEvent(event)
        self.loader_timer.start()

    def hideEvent(self, event) -> None:  # noqa: ANN001
        self.loader_timer.stop()
        super().hideEvent(event)

    def _render_pixmap(self) -> QPixmap:
        width = 760
        height = 420
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#0f0f12"))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(QRectF(0, 0, width, height), QColor("#111114"))

        card_rect = QRectF(28, 28, width - 56, height - 56)
        painter.setPen(QPen(QColor(255, 255, 255, 24), 2))
        painter.setBrush(QColor(255, 255, 255, 8))
        painter.drawRoundedRect(card_rect, 28, 28)

        art = QPixmap(str(self.art_path))
        if art.isNull():
            art = QPixmap(str(DEFAULT_APP_ICON_PATH))
        if not art.isNull():
            art = art.scaled(230, 230, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(int((width - art.width()) / 2), 52, art)
        self._draw_forehead_loader(painter)

        title_font = QFont("Segoe UI", 24)
        title_font.setWeight(QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#f6f6f6"))
        painter.drawText(QRectF(80, 278, width - 160, 34), Qt.AlignmentFlag.AlignCenter, "FINDUS>x<STRETCHING")

        body_font = QFont("Segoe UI", 12)
        body_font.setWeight(QFont.Weight.Medium)
        painter.setFont(body_font)
        painter.setPen(QColor(220, 220, 220, 210))
        painter.drawText(QRectF(92, 314, width - 184, 24), Qt.AlignmentFlag.AlignCenter, self.message)

        bar_rect = QRectF(118, 354, width - 236, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 22))
        painter.drawRoundedRect(bar_rect, 8, 8)
        fill_width = max(18.0, (bar_rect.width() * self.progress) / 100.0) if self.progress > 0 else 0.0
        if fill_width:
            fill_rect = QRectF(bar_rect.left(), bar_rect.top(), min(bar_rect.width(), fill_width), bar_rect.height())
            painter.setBrush(self.loader_accent)
            painter.drawRoundedRect(fill_rect, 8, 8)

        painter.setPen(QColor(255, 255, 255, 120))
        painter.drawText(QRectF(118, 376, width - 236, 22), Qt.AlignmentFlag.AlignCenter, f"{self.progress}%")
        painter.end()
        return pixmap

    def _draw_forehead_loader(self, painter: QPainter) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(380, 144)
        if self.loader_style == "neon_ring":
            self._draw_neon_ring_loader(painter, center)
        elif self.loader_style == "stamp_pulse":
            self._draw_stamp_pulse_loader(painter, center)
        elif self.loader_style == "orbit_arc":
            self._draw_orbit_arc_loader(painter, center)
        else:
            self._draw_spiral_loader(painter, center)
        painter.restore()

    def _draw_spiral_loader(self, painter: QPainter, center: QPointF) -> None:
        rings = 3
        segments_per_ring = 11
        total_segments = rings * segments_per_ring
        active_index = self.loader_phase % total_segments
        points: list[QPointF] = []

        for index in range(total_segments):
            ring_index = index // segments_per_ring
            segment_index = index % segments_per_ring
            ring_progress = segment_index / max(1, segments_per_ring - 1)
            radius = 5.0 + (ring_index * 6.8) + (ring_progress * 8.5)
            angle = (ring_progress * np.pi * 1.8) + (ring_index * 0.52) + (self.loader_phase * 0.16)
            x = center.x() + np.cos(angle) * radius
            y = center.y() + np.sin(angle) * radius
            points.append(QPointF(float(x), float(y)))

        base_red = self.loader_accent.red()
        base_green = self.loader_accent.green()
        base_blue = self.loader_accent.blue()

        for index in range(len(points) - 1):
            distance = (active_index - index) % total_segments
            alpha = max(28, 255 - (distance * 15))
            width = max(1.8, 6.2 - (distance * 0.14))
            color = QColor(base_red, base_green, base_blue, alpha)
            painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(points[index], points[index + 1])

        orbit_radius = 22.0
        orbit_angle = (self.loader_phase / max(1, total_segments)) * np.pi * 2.0
        orbit_x = center.x() + np.cos(orbit_angle) * orbit_radius
        orbit_y = center.y() + np.sin(orbit_angle) * (orbit_radius * 0.68)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(base_red, base_green, base_blue, 210))
        painter.drawEllipse(QPointF(float(orbit_x), float(orbit_y)), 4.4, 4.4)

    def _draw_neon_ring_loader(self, painter: QPainter, center: QPointF) -> None:
        phase = self.loader_phase % 36
        halo_rect = QRectF(center.x() - 24, center.y() - 18, 48, 36)
        for index, width in enumerate((9, 6, 3)):
            alpha = max(30, 120 - (index * 28))
            painter.setPen(QPen(QColor(self.loader_accent.red(), self.loader_accent.green(), self.loader_accent.blue(), alpha), width))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawArc(halo_rect, int((phase * 16 + index * 420) * 16), 160 * 16)
        dot_angle = (phase / 36.0) * np.pi * 2.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.loader_accent.red(), self.loader_accent.green(), self.loader_accent.blue(), 230))
        painter.drawEllipse(
            QPointF(float(center.x() + np.cos(dot_angle) * 22), float(center.y() + np.sin(dot_angle) * 15)),
            4.2,
            4.2,
        )

    def _draw_stamp_pulse_loader(self, painter: QPainter, center: QPointF) -> None:
        pulse = (np.sin(self.loader_phase * 0.42) + 1.0) / 2.0
        glow_alpha = int(70 + pulse * 90)
        glow_radius = 10.0 + pulse * 8.0
        for scale, alpha_scale in ((1.45, 0.24), (1.0, 0.55)):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QColor(
                    self.loader_accent.red(),
                    self.loader_accent.green(),
                    self.loader_accent.blue(),
                    int(glow_alpha * alpha_scale),
                )
            )
            painter.drawEllipse(center, glow_radius * scale, glow_radius * scale)
        painter.setPen(QPen(QColor(self.loader_accent.red(), self.loader_accent.green(), self.loader_accent.blue(), 220), 3.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, 11.5 + pulse * 4.2, 11.5 + pulse * 4.2)

    def _draw_orbit_arc_loader(self, painter: QPainter, center: QPointF) -> None:
        phase = self.loader_phase % 48
        arc_rect = QRectF(center.x() - 26, center.y() - 18, 52, 36)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for offset, span, alpha, width in ((0, 112, 225, 5.8), (160, 78, 170, 4.2), (272, 58, 120, 3.2)):
            painter.setPen(QPen(QColor(self.loader_accent.red(), self.loader_accent.green(), self.loader_accent.blue(), alpha), width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawArc(arc_rect, int((phase * 12 + offset) * 16), span * 16)
        orbit_angle = (phase / 48.0) * np.pi * 2.0
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.loader_accent.red(), self.loader_accent.green(), self.loader_accent.blue(), 235))
        painter.drawEllipse(
            QPointF(float(center.x() + np.cos(orbit_angle) * 24), float(center.y() + np.sin(orbit_angle) * 12)),
            4.8,
            4.8,
        )

    def _resolve_loader_accent(self) -> QColor:
        return STARTUP_SPLASH_ACCENTS.get(self.art_path.stem, QColor("#35d7c0"))

    def _resolve_loader_style(self) -> str:
        return STARTUP_SPLASH_STYLES.get(self.art_path.stem, "spiral")


class WaveformWidget(QWidget):
    regionChanged = Signal(float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.overview: WaveformOverview | None = None
        self.theme = get_theme_definition(DEFAULT_THEME_NAME).waveform
        self.region = RegionSelection(0.0, 1.0)
        self.visible_range = RegionSelection(0.0, 1.0)
        self.playhead_seconds: float | None = None
        self._drag_mode: str | None = None
        self._drag_anchor_seconds = 0.0
        self.snap_step_seconds: float | None = None
        self.setMinimumHeight(210)
        self.setMouseTracking(True)

    def set_overview(self, overview: WaveformOverview) -> None:
        self.overview = overview
        full_end = max(0.1, overview.duration_seconds)
        self.visible_range = RegionSelection(0.0, full_end)
        end = min(full_end, max(0.5, min(2.5, full_end)))
        self.set_region(RegionSelection(0.0, end), emit_signal=False)

    def set_region(self, region: RegionSelection, emit_signal: bool = True) -> None:
        if self.overview is None:
            self.region = region
            return
        full_end = max(0.01, self.overview.duration_seconds)
        start = self._snap_seconds(max(0.0, min(region.start_seconds, full_end)))
        end = self._snap_seconds(max(start + 0.01, min(region.end_seconds, full_end)))
        if end <= start:
            end = min(full_end, start + max(0.01, self.snap_step_seconds or 0.01))
        self.region = RegionSelection(start, end)
        self.update()
        if emit_signal:
            self.regionChanged.emit(self.region.start_seconds, self.region.end_seconds)

    def fit_selection(self) -> None:
        if self.overview is None:
            return
        margin = max(0.05, self.region.duration_seconds * 0.25)
        center = (self.region.start_seconds + self.region.end_seconds) / 2.0
        half_width = (self.region.duration_seconds / 2.0) + margin
        self._set_visible_range(center - half_width, center + half_width)
        self.update()

    def zoom_to_selection(self) -> None:
        self.fit_selection()

    def fit_full_range(self) -> None:
        if self.overview is None:
            return
        self.visible_range = RegionSelection(0.0, self.overview.duration_seconds)
        self.update()

    def show_full_range(self) -> None:
        self.fit_full_range()

    def reset_selection(self) -> None:
        if self.overview is None:
            return
        end = min(self.overview.duration_seconds, 2.5)
        self.set_region(RegionSelection(0.0, max(0.5, end)))
        self.fit_full_range()

    def set_snap_step(self, seconds: float | None) -> None:
        self.snap_step_seconds = seconds if seconds and seconds > 0.0 else None

    def wheelEvent(self, event) -> None:  # noqa: ANN001
        if self.overview is None:
            event.ignore()
            return
        angle = event.angleDelta().y()
        if angle == 0:
            event.ignore()
            return
        zoom_factor = 0.85 if angle > 0 else 1.15
        cursor_seconds = self._x_to_seconds(event.position().x())
        new_duration = float(np.clip(self.visible_range.duration_seconds * zoom_factor, 0.1, self.overview.duration_seconds))
        ratio = (cursor_seconds - self.visible_range.start_seconds) / max(0.001, self.visible_range.duration_seconds)
        start = cursor_seconds - (new_duration * ratio)
        end = start + new_duration
        self._set_visible_range(start, end)
        event.accept()

    def set_playhead(self, seconds: float | None) -> None:
        self.playhead_seconds = seconds
        self.update()

    def set_theme(self, theme: WaveformTheme) -> None:
        self.theme = theme
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(self.theme.background))
        painter.setPen(QPen(QColor(self.theme.border), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        if self.overview is None:
            painter.setPen(QColor(self.theme.empty_text))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Load or record audio to see the waveform")
            return

        content = self.rect().adjusted(8, 8, -8, -8)
        painter.fillRect(content, QColor(self.theme.content_background))
        mid_y = content.center().y()
        painter.setPen(QPen(QColor(self.theme.center_line), 1))
        painter.drawLine(content.left(), mid_y, content.right(), mid_y)

        bins = self.overview.min_peaks.shape[1]
        start_bin = int((self.visible_range.start_seconds / self.overview.duration_seconds) * bins)
        end_bin = int((self.visible_range.end_seconds / self.overview.duration_seconds) * bins)
        end_bin = max(start_bin + 1, min(bins, end_bin))
        min_peaks = self.overview.min_peaks[0, start_bin:end_bin]
        max_peaks = self.overview.max_peaks[0, start_bin:end_bin]

        painter.setPen(QPen(QColor(self.theme.waveform_line), 1))
        for index, (min_peak, max_peak) in enumerate(zip(min_peaks, max_peaks)):
            x = content.left() + (index / max(1, min_peaks.size - 1)) * content.width()
            top = mid_y - (max_peak * content.height() * 0.42)
            bottom = mid_y - (min_peak * content.height() * 0.42)
            painter.drawLine(int(x), int(top), int(x), int(bottom))

        sel_left = self._seconds_to_x(self.region.start_seconds, content)
        sel_right = self._seconds_to_x(self.region.end_seconds, content)
        selection_rect = QRectF(sel_left, content.top(), max(4.0, sel_right - sel_left), content.height())
        painter.fillRect(selection_rect, QColor(*self.theme.selection_fill))
        painter.setPen(QPen(QColor(self.theme.selection_border), 2))
        painter.drawLine(int(sel_left), content.top(), int(sel_left), content.bottom())
        painter.drawLine(int(sel_right), content.top(), int(sel_right), content.bottom())

        if self.playhead_seconds is not None:
            playhead_x = self._seconds_to_x(self.playhead_seconds, content)
            painter.setPen(QPen(QColor(self.theme.playhead), 2))
            painter.drawLine(int(playhead_x), content.top(), int(playhead_x), content.bottom())

        painter.setPen(QColor(self.theme.text))
        painter.drawText(
            content.adjusted(8, 8, -8, -8),
            f"Selection {self.region.start_seconds:.2f}s - {self.region.end_seconds:.2f}s ({self.region.duration_seconds:.2f}s)",
        )

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        if self.overview is None:
            return
        seconds = self._x_to_seconds(event.position().x())
        edge_threshold = self._seconds_per_pixel() * 12.0
        if abs(seconds - self.region.start_seconds) <= edge_threshold:
            self._drag_mode = "left"
        elif abs(seconds - self.region.end_seconds) <= edge_threshold:
            self._drag_mode = "right"
        elif self.region.start_seconds < seconds < self.region.end_seconds:
            self._drag_mode = "move"
            self._drag_anchor_seconds = seconds - self.region.start_seconds
        else:
            self._drag_mode = "new"
            self.set_region(RegionSelection(seconds, seconds + 0.01))

    def mouseMoveEvent(self, event) -> None:  # noqa: ANN001
        if self.overview is None or self._drag_mode is None:
            return
        seconds = self._x_to_seconds(event.position().x())
        if self._drag_mode == "left":
            self.set_region(RegionSelection(seconds, self.region.end_seconds))
        elif self._drag_mode == "right":
            self.set_region(RegionSelection(self.region.start_seconds, seconds))
        elif self._drag_mode == "move":
            duration = self.region.duration_seconds
            new_start = seconds - self._drag_anchor_seconds
            self.set_region(RegionSelection(new_start, new_start + duration))
        elif self._drag_mode == "new":
            start = min(self.region.start_seconds, seconds)
            end = max(self.region.start_seconds, seconds)
            self.set_region(RegionSelection(start, max(start + 0.01, end)))

    def mouseReleaseEvent(self, event) -> None:  # noqa: ANN001
        self._drag_mode = None

    def _seconds_to_x(self, seconds: float, rect) -> float:  # noqa: ANN001
        ratio = (seconds - self.visible_range.start_seconds) / max(0.001, self.visible_range.duration_seconds)
        return rect.left() + np.clip(ratio, 0.0, 1.0) * rect.width()

    def _x_to_seconds(self, x: float) -> float:
        rect = self.rect().adjusted(8, 8, -8, -8)
        ratio = (x - rect.left()) / max(1.0, rect.width())
        seconds = self.visible_range.start_seconds + np.clip(ratio, 0.0, 1.0) * self.visible_range.duration_seconds
        return float(np.clip(seconds, 0.0, self.overview.duration_seconds if self.overview else seconds))

    def _seconds_per_pixel(self) -> float:
        return self.visible_range.duration_seconds / max(1.0, self.width())

    def _set_visible_range(self, start: float, end: float) -> None:
        if self.overview is None:
            return
        duration = max(0.1, min(end - start, self.overview.duration_seconds))
        clamped_start = max(0.0, min(start, self.overview.duration_seconds - duration))
        clamped_end = min(self.overview.duration_seconds, clamped_start + duration)
        self.visible_range = RegionSelection(clamped_start, max(clamped_start + 0.1, clamped_end))
        self.update()

    def _snap_seconds(self, seconds: float) -> float:
        if self.snap_step_seconds is None:
            return seconds
        return round(seconds / self.snap_step_seconds) * self.snap_step_seconds


class PyQtGraphWaveformWidget(QWidget):
    regionChanged = Signal(float, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.overview: WaveformOverview | None = None
        self.theme = get_theme_definition(DEFAULT_THEME_NAME).waveform
        self.region = RegionSelection(0.0, 1.0)
        self.visible_range = RegionSelection(0.0, 1.0)
        self.playhead_seconds: float | None = None
        self.snap_step_seconds: float | None = None
        
        self.setMinimumHeight(210)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget(enableMenu=False)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        layout.addWidget(self.plot_widget)

        self.fill_item = None
        self.region_item = pg.LinearRegionItem(values=[0.0, 1.0], brush=pg.mkBrush(0, 0, 255, 50))
        self.region_item.setZValue(10)
        self.plot_widget.addItem(self.region_item)
        
        self.playhead_item = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('y', width=2))
        self.playhead_item.setZValue(20)
        self.plot_widget.addItem(self.playhead_item)
        self.playhead_item.hide()
        
        self.region_item.sigRegionChanged.connect(self._on_region_item_changed)
        
        self.label = QLabel("Load or record audio to see the waveform", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setContentsMargins(10, 10, 0, 0)
        
        self._apply_theme()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.label.setGeometry(self.rect())

    def _apply_theme(self):
        bg = QColor(self.theme.background)
        self.plot_widget.setBackground(bg)
        
        sel_fill = self.theme.selection_fill
        self.region_item.setBrush(pg.mkBrush(*sel_fill))
        self.region_item.setHoverBrush(pg.mkBrush(*sel_fill))
        
        # Region border lines
        border_pen = pg.mkPen(QColor(self.theme.selection_border), width=2)
        for line in self.region_item.lines:
            line.setPen(border_pen)
            line.setHoverPen(border_pen)
            
        self.playhead_item.setPen(pg.mkPen(QColor(self.theme.playhead), width=2))
        self.label.setStyleSheet(f"color: {self.theme.empty_text}; font-weight: bold;")
        
        if self.fill_item is not None:
            self.fill_item.setBrush(pg.mkBrush(QColor(self.theme.waveform_line)))
            
    def set_theme(self, theme: WaveformTheme) -> None:
        self.theme = theme
        self._apply_theme()

    def set_overview(self, overview: WaveformOverview) -> None:
        self.overview = overview
        if self.fill_item is not None:
            self.plot_widget.removeItem(self.fill_item)
            self.fill_item = None
            if getattr(self, 'curve1', None) is not None:
                self.plot_widget.removeItem(self.curve1)
                self.curve1 = None
            if getattr(self, 'curve2', None) is not None:
                self.plot_widget.removeItem(self.curve2)
                self.curve2 = None
            
        if self.overview is None:
            self.label.setText("Load or record audio to see the waveform")
            self.label.setStyleSheet(f"color: {self.theme.empty_text}; font-weight: bold;")
            self.label.show()
            return
            
        self.label.hide()
        
        bins = self.overview.min_peaks.shape[1]
        x_axis = np.linspace(0, self.overview.duration_seconds, bins)
        
        self.curve1 = pg.PlotDataItem(x_axis, self.overview.max_peaks[0], pen=pg.mkPen(QColor(self.theme.waveform_line)))
        self.curve2 = pg.PlotDataItem(x_axis, self.overview.min_peaks[0], pen=pg.mkPen(QColor(self.theme.waveform_line)))
        
        self.plot_widget.addItem(self.curve1)
        self.plot_widget.addItem(self.curve2)
        
        self.fill_item = pg.FillBetweenItem(self.curve1, self.curve2, brush=pg.mkBrush(QColor(self.theme.waveform_line)))
        self.plot_widget.addItem(self.fill_item)
        
        full_end = max(0.1, overview.duration_seconds)
        self.visible_range = RegionSelection(0.0, full_end)
        end = min(full_end, max(0.5, min(2.5, full_end)))
        self.set_region(RegionSelection(0.0, end), emit_signal=False)
        self.fit_full_range()

    def set_region(self, region: RegionSelection, emit_signal: bool = True) -> None:
        if self.overview is None:
            self.region = region
            return
        full_end = max(0.01, self.overview.duration_seconds)
        start = self._snap_seconds(max(0.0, min(region.start_seconds, full_end)))
        end = self._snap_seconds(max(start + 0.01, min(region.end_seconds, full_end)))
        if end <= start:
            end = min(full_end, start + max(0.01, self.snap_step_seconds or 0.01))
            
        self.region = RegionSelection(start, end)
        
        self.region_item.sigRegionChanged.disconnect(self._on_region_item_changed)
        self.region_item.setRegion([start, end])
        self.region_item.sigRegionChanged.connect(self._on_region_item_changed)
        
        self.label.setText(f"Selection {self.region.start_seconds:.2f}s - {self.region.end_seconds:.2f}s ({self.region.duration_seconds:.2f}s)")
        self.label.setStyleSheet(f"color: {self.theme.text};")
        self.label.show()
        
        if emit_signal:
            self.regionChanged.emit(self.region.start_seconds, self.region.end_seconds)

    def _on_region_item_changed(self):
        if self.overview is None:
            return
        rgn = self.region_item.getRegion()
        start = self._snap_seconds(rgn[0])
        end = self._snap_seconds(rgn[1])
        
        self.region = RegionSelection(start, end)
        self.label.setText(f"Selection {self.region.start_seconds:.2f}s - {self.region.end_seconds:.2f}s ({self.region.duration_seconds:.2f}s)")
        self.regionChanged.emit(self.region.start_seconds, self.region.end_seconds)

    def fit_selection(self) -> None:
        if self.overview is None:
            return
        margin = max(0.05, self.region.duration_seconds * 0.25)
        center = (self.region.start_seconds + self.region.end_seconds) / 2.0
        half_width = (self.region.duration_seconds / 2.0) + margin
        self.plot_widget.setXRange(center - half_width, center + half_width, padding=0)

    def zoom_to_selection(self) -> None:
        self.fit_selection()

    def fit_full_range(self) -> None:
        if self.overview is None:
            return
        self.plot_widget.setXRange(0.0, self.overview.duration_seconds, padding=0)

    def show_full_range(self) -> None:
        self.fit_full_range()

    def reset_selection(self) -> None:
        if self.overview is None:
            return
        end = min(self.overview.duration_seconds, 2.5)
        self.set_region(RegionSelection(0.0, max(0.5, end)))
        self.fit_full_range()

    def set_snap_step(self, seconds: float | None) -> None:
        self.snap_step_seconds = seconds if seconds and seconds > 0.0 else None

    def set_playhead(self, seconds: float | None) -> None:
        self.playhead_seconds = seconds
        if seconds is None:
            self.playhead_item.hide()
        else:
            self.playhead_item.setValue(seconds)
            self.playhead_item.show()

    def _snap_seconds(self, seconds: float) -> float:
        if self.snap_step_seconds is None:
            return seconds
        return round(seconds / self.snap_step_seconds) * self.snap_step_seconds


class StaticWheelTabBar(QTabBar):
    def wheelEvent(self, event) -> None:  # noqa: ANN001
        event.ignore()


class RenderWorker(QThread):
    status_changed = Signal(int, str)
    render_completed = Signal(object)
    render_failed = Signal(str)

    def __init__(self, config: RenderConfig) -> None:
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            result = render_to_wav(self.config, status_callback=self._on_status)
        except Exception as exc:
            self.render_failed.emit(str(exc))
        else:
            self.render_completed.emit(result)

    def _on_status(self, status: RenderStatus) -> None:
        self.status_changed.emit(int(status.progress * 100), status.message)


class PreviewWorker(QThread):
    status_changed = Signal(int, str)
    preview_completed = Signal(object)
    preview_failed = Signal(str)

    def __init__(self, config: PreviewConfig) -> None:
        super().__init__()
        self.config = config

    def run(self) -> None:
        try:
            result = render_preview(self.config, status_callback=self._on_status)
        except Exception as exc:
            self.preview_failed.emit(str(exc))
        else:
            self.preview_completed.emit(result)

    def _on_status(self, status: RenderStatus) -> None:
        self.status_changed.emit(int(status.progress * 100), status.message)


@dataclass
class PreviewHistoryEntry:
    input_path: str
    snapshot: CompareSlotState
    preview_result: PreviewResult
    preview_key: tuple | None
    label: str


@dataclass(frozen=True)
class WorkflowStateSnapshot:
    input_path: str = ""
    output_path: str = ""
    render_output_mode: str = "wet"
    preview_start: float = 0.0
    preview_length: float = 2.5
    waveform_region_start: float = 0.0
    waveform_region_end: float = 2.5
    stretch_factor: float = 8.0
    quality_profile: QualityProfile = QualityProfile.MEDIUM
    effects: EffectSettings = EffectSettings()
    selected_preset_name: str = "Custom"
    compare_slot_a: CompareSlotState | None = None
    compare_slot_b: CompareSlotState | None = None
    loop_enabled: bool = False
    loop_crossfade_ms: int = 80


@dataclass(frozen=True)
class WorkflowHistoryEntry:
    snapshot: WorkflowStateSnapshot
    label: str = "workflow change"


class PreviewPlayer(QObject):
    def __init__(self) -> None:
        super().__init__(None)
        self.audio_sink: QAudioSink | None = None
        self.buffer_device: QBuffer | None = None
        self.byte_array: QByteArray | None = None
        self.on_finished = None
        self._manual_stop = False
        self._sd_active = False
        self._sd_finish_timer = QTimer(self)
        self._sd_finish_timer.setSingleShot(True)
        self._sd_finish_timer.timeout.connect(self._finish_sounddevice_playback)

    def play(
        self,
        audio: np.ndarray,
        sample_rate: int,
        on_finished,
        *,
        audio_backend: str = AUDIO_BACKEND_AUTO,
        output_device_id: str = "",
        output_channels: int = 2,
        host_api_name: str = "",
    ) -> None:  # noqa: ANN001
        self.stop()
        self._manual_stop = False
        self.on_finished = on_finished
        actual_backend = resolve_audio_backend(audio_backend)
        if actual_backend == AUDIO_BACKEND_PORTAUDIO and sd is not None:
            device_info = find_audio_device(
                output_device_id,
                direction="output",
                requested_backend=AUDIO_BACKEND_PORTAUDIO,
                host_api_name=host_api_name,
            )
            if device_info is not None:
                prepared_audio = _coerce_audio_channels(audio, min(max(1, output_channels), max(1, device_info.max_output_channels)))
                sd.play(
                    np.asarray(prepared_audio, dtype=np.float32),
                    sample_rate,
                    device=int(device_info.device_id.split(":", 1)[1]),
                    blocking=False,
                )
                self._sd_active = True
                duration_ms = int(round((prepared_audio.shape[0] / max(1, sample_rate)) * 1000.0)) + 25
                self._sd_finish_timer.start(max(1, duration_ms))
                return

        prepared_audio = _coerce_audio_channels(audio, max(1, output_channels))
        self.byte_array = QByteArray(_float_audio_to_pcm16(prepared_audio))
        self.buffer_device = QBuffer()
        self.buffer_device.setData(self.byte_array)
        self.buffer_device.open(QIODevice.OpenModeFlag.ReadOnly)

        fmt = QAudioFormat()
        fmt.setSampleRate(sample_rate)
        fmt.setChannelCount(1 if prepared_audio.ndim == 1 else prepared_audio.shape[1])
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.audio_sink = QAudioSink(resolve_qt_output_device(output_device_id) or QMediaDevices.defaultAudioOutput(), fmt)
        self.audio_sink.stateChanged.connect(self._on_state_changed)
        self.audio_sink.start(self.buffer_device)

    def stop(self) -> None:
        self._manual_stop = True
        if self._sd_active:
            self._sd_finish_timer.stop()
            if sd is not None:
                sd.stop()
            self._sd_active = False
        self._dispose_audio_resources()

    def is_active(self) -> bool:
        return self.audio_sink is not None or self._sd_active

    def _on_state_changed(self, state) -> None:  # noqa: ANN001
        if self.audio_sink is None or state != QAudio.State.IdleState or self._manual_stop:
            return
        on_finished = self.on_finished
        self._dispose_audio_resources()
        if on_finished is not None:
            on_finished()

    def _dispose_audio_resources(self) -> None:
        if self.audio_sink is not None:
            try:
                self.audio_sink.stateChanged.disconnect(self._on_state_changed)
            except (RuntimeError, TypeError):
                pass
            self.audio_sink.stop()
            self.audio_sink.deleteLater()
            self.audio_sink = None
        if self.buffer_device is not None:
            self.buffer_device.close()
            self.buffer_device.deleteLater()
            self.buffer_device = None
        self.byte_array = None

    def _finish_sounddevice_playback(self) -> None:
        if not self._sd_active or self._manual_stop:
            return
        self._sd_active = False
        if self.on_finished is not None:
            self.on_finished()


class MainWindow(QMainWindow):
    def __init__(self, startup_callback: Callable[[str, int], None] | None = None) -> None:
        super().__init__()
        self._startup_callback = startup_callback
        self.preset_library = PresetLibrary()
        self.theme_manager = ThemeManager(QApplication.instance())
        self.current_theme_name = DEFAULT_THEME_NAME
        self.current_ui_scale_percent = 100
        self.recording_controller = RecordingController(self)
        self.render_worker: RenderWorker | None = None
        self.preview_worker: PreviewWorker | None = None
        self.preview_player = PreviewPlayer()
        self.current_preview: PreviewResult | None = None
        self.current_preview_key: tuple | None = None
        self.preview_state = "idle"
        self._current_playback_audio: np.ndarray | None = None
        self.effects_bypass_snapshot: EffectSettings | None = None
        self._suspend_dirty_tracking = False
        self.current_audio_snapshot = None
        self.current_preset_name = "Custom"
        self.favorite_factory_preset_names: set[str] = set()
        self.compare_slots: dict[str, CompareSlotState | None] = {"A": None, "B": None}
        self.preview_history_entries: list[PreviewHistoryEntry] = []
        self.current_project_path = ""
        self.recent_source_paths: list[str] = []
        self.recent_project_paths: list[str] = []
        self.render_queue_items: list[QueuedRenderJob] = []
        self.render_queue_running = False
        self.render_queue_results: list[RenderResult] = []
        self.active_render_job: QueuedRenderJob | None = None
        self.recent_takes: list[RecentTake] = []
        self.undo_stack: list[WorkflowHistoryEntry] = []
        self.redo_stack: list[WorkflowHistoryEntry] = []
        self._workflow_history_baseline_snapshot: WorkflowStateSnapshot | None = None
        self._workflow_history_pending = False
        self._workflow_history_pending_label: str | None = None
        self._suspend_workflow_history_tracking = False
        self._pending_compare_preview_result: PreviewResult | None = None
        self._pending_compare_preview_key: tuple | None = None
        self._pending_compare_render = False
        self.waveform_overview: WaveformOverview | None = None
        self._syncing_region = False
        self.current_playback_duration_seconds = 0.0
        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(40)
        self.playback_timer.timeout.connect(self._update_playhead)
        self.workflow_history_timer = QTimer(self)
        self.workflow_history_timer.setSingleShot(True)
        self.workflow_history_timer.setInterval(250)
        self.workflow_history_timer.timeout.connect(self._commit_workflow_history_baseline)
        self.playback_clock = QElapsedTimer()
        self.recording_clock = QElapsedTimer()
        self.recording_timer = QTimer(self)
        self.recording_timer.setInterval(200)
        self.recording_timer.timeout.connect(self._update_recording_duration)
        self.recording_peak_hold = 0.0
        self.setWindowTitle("FINDUS>x<STRETCHING")
        self._base_window_size = (980, 760)
        self.resize(*self._base_window_size)
        self.setMinimumSize(560, 420)
        self.setAcceptDrops(True)
        self._report_startup("Building workspace...", 14)
        self._build_ui()
        self.main_content.setAcceptDrops(True)
        self.main_scroll_area.viewport().setAcceptDrops(True)
        self._report_startup("Applying theme...", 36)
        self._apply_theme(DEFAULT_THEME_NAME, announce=False)
        self._report_startup("Connecting audio tools...", 52)
        self._connect_recording_signals()
        self._report_startup("Loading presets...", 68)
        self._refresh_presets()
        self._report_startup("Detecting audio devices...", 82)
        self._refresh_audio_routing()
        self._report_startup("Restoring session...", 92)
        self._restore_state()
        self._report_startup("Startup ready.", 100)

    def _report_startup(self, message: str, progress: int) -> None:
        if self._startup_callback is not None:
            self._startup_callback(message, progress)

    def _build_ui(self) -> None:
        self._build_toolbar()

        central = QWidget(self)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.main_scroll_area = scroll_area

        content = QWidget()
        self.main_content = content
        layout = QVBoxLayout(content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.drop_hint_label = QLabel("Drop one audio file or one .findusstretch.json project")
        self.drop_hint_label.setWordWrap(True)
        self.drop_hint_label.setProperty("muted", True)
        self.drop_hint_label.hide()
        layout.addWidget(self.drop_hint_label)

        self.waveform_widget = WaveformWidget()  # PyQtGraphWaveformWidget is currently buggy/incomplete
        self.waveform_widget.regionChanged.connect(self._on_waveform_region_changed)
        layout.addWidget(self.waveform_widget)

        waveform_controls = QHBoxLayout()
        self.loop_checkbox = QCheckBox("Loop")
        self.loop_checkbox.toggled.connect(self._on_loop_toggled)
        self.loop_state_label = QLabel("Loop off")
        self.snap_to_grid_checkbox = QCheckBox("Snap 0.1s")
        self.snap_to_grid_checkbox.toggled.connect(self._on_snap_to_grid_toggled)
        self.zoom_selection_button = QPushButton("Fit Selection")
        self.zoom_selection_button.clicked.connect(self.waveform_widget.fit_selection)
        self.zoom_selection_button.setToolTip("Fit the selection in view (Z)")
        self.show_full_button = QPushButton("Fit Full File")
        self.show_full_button.clicked.connect(self.waveform_widget.fit_full_range)
        self.show_full_button.setToolTip("Show the full waveform (F)")
        self.reset_selection_button = QPushButton("Reset Selection")
        self.reset_selection_button.clicked.connect(self.waveform_widget.reset_selection)
        self.reset_selection_button.setToolTip("Reset selection (R)")
        self.region_status = QLabel("No waveform loaded")
        waveform_controls.addWidget(self.loop_checkbox)
        waveform_controls.addWidget(self.loop_state_label)
        waveform_controls.addWidget(self.snap_to_grid_checkbox)
        waveform_controls.addWidget(self.zoom_selection_button)
        waveform_controls.addWidget(self.show_full_button)
        waveform_controls.addWidget(self.reset_selection_button)
        waveform_controls.addWidget(self.region_status, 1)
        layout.addLayout(waveform_controls)

        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setTabBar(StaticWheelTabBar())
        self.workspace_tabs.currentChanged.connect(self._on_workspace_tab_changed)
        self.workspace_tabs.addTab(self._build_source_tab(), "Source")
        self.workspace_tabs.addTab(self._build_stretch_tab(), "Stretch")
        self.workspace_tabs.addTab(self._build_effects_tab(), "Effects")
        self.workspace_tabs.addTab(self._build_presets_tab(), "Presets")
        self.workspace_tabs.addTab(self._build_help_tab(), "Help")
        layout.addWidget(self.workspace_tabs)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.preview_status_label = QLabel("Preview idle. Load audio to build a cached preview.")
        layout.addWidget(self.preview_status_label)

        transport_row = QHBoxLayout()
        self.preview_button = QPushButton("Play Preview")
        self.preview_button.clicked.connect(self._preview)
        self.replay_preview_button = QPushButton("Replay Last Preview")
        self.replay_preview_button.clicked.connect(self._replay_last_preview)
        self.record_button = QPushButton("Record Input")
        self.record_button.clicked.connect(self._start_recording)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._stop_active)
        self.render_button = QPushButton("Render WAV")
        self.render_button.clicked.connect(self._render)
        transport_row.addWidget(self.preview_button)
        transport_row.addWidget(self.replay_preview_button)
        transport_row.addWidget(self.record_button)
        transport_row.addWidget(self.stop_button)
        transport_row.addStretch(1)

        output_meter_layout = QVBoxLayout()
        output_meter_layout.setSpacing(2)
        self.output_left_level_bar = QProgressBar()
        self.output_left_level_bar.setRange(0, 100)
        self.output_left_level_bar.setValue(0)
        self.output_left_level_bar.setTextVisible(False)
        self.output_left_level_bar.setMaximumHeight(8)
        self.output_right_level_bar = QProgressBar()
        self.output_right_level_bar.setRange(0, 100)
        self.output_right_level_bar.setValue(0)
        self.output_right_level_bar.setTextVisible(False)
        self.output_right_level_bar.setMaximumHeight(8)
        output_meter_label = QLabel("Output")
        output_meter_label.setProperty("muted", True)
        font = output_meter_label.font()
        font.setPointSize(font.pointSize() - 2)
        output_meter_label.setFont(font)
        output_meter_layout.addWidget(self.output_left_level_bar)
        output_meter_layout.addWidget(self.output_right_level_bar)
        output_meter_layout.addWidget(output_meter_label)
        transport_row.addLayout(output_meter_layout)
        transport_row.addSpacing(10)

        transport_row.addWidget(self.render_button)
        layout.addLayout(transport_row)

        scroll_area.setWidget(content)
        outer_layout.addWidget(scroll_area)

        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")
        self._update_command_state()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        self.main_toolbar = toolbar

        self.undo_action = QAction(self._icon("edit-undo", QStyle.StandardPixmap.SP_ArrowBack), "Undo", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.triggered.connect(self._undo_workflow)
        self.undo_action.setToolTip("Undo workflow change (Ctrl+Z)")
        toolbar.addAction(self.undo_action)

        self.redo_action = QAction(self._icon("edit-redo", QStyle.StandardPixmap.SP_ArrowForward), "Redo", self)
        self.redo_action.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.redo_action.triggered.connect(self._redo_workflow)
        self.redo_action.setToolTip("Redo workflow change (Ctrl+Y / Ctrl+Shift+Z)")
        toolbar.addAction(self.redo_action)

        self.open_action = QAction(self._icon("document-open", QStyle.StandardPixmap.SP_DirOpenIcon), "Open", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self._browse_input)
        self.open_action.setToolTip("Open input audio (Ctrl+O)")
        toolbar.addAction(self.open_action)

        self.open_project_action = QAction(
            self._icon("document-open-recent", QStyle.StandardPixmap.SP_DialogOpenButton),
            "Open Project",
            self,
        )
        self.open_project_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.open_project_action.triggered.connect(self._browse_project)
        self.open_project_action.setToolTip("Open project file (Ctrl+Shift+O)")
        toolbar.addAction(self.open_project_action)

        self.save_project_action = QAction(
            self._icon("document-save", QStyle.StandardPixmap.SP_DialogSaveButton),
            "Save Project",
            self,
        )
        self.save_project_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.save_project_action.triggered.connect(self._save_project)
        self.save_project_action.setToolTip("Save project file (Ctrl+Shift+S)")
        toolbar.addAction(self.save_project_action)

        self.record_action = QAction(self._icon("media-record", QStyle.StandardPixmap.SP_DialogApplyButton), "Record", self)
        self.record_action.setShortcut(QKeySequence("Ctrl+R"))
        self.record_action.triggered.connect(self._start_recording)
        self.record_action.setToolTip("Start recording (Ctrl+R)")
        toolbar.addAction(self.record_action)

        self.stop_action = QAction(self._icon("media-playback-stop", QStyle.StandardPixmap.SP_MediaStop), "Stop", self)
        self.stop_action.setShortcut(QKeySequence("Escape"))
        self.stop_action.triggered.connect(self._stop_active)
        self.stop_action.setToolTip("Stop playback or recording (Esc)")
        toolbar.addAction(self.stop_action)

        self.preview_action = QAction(self._icon("media-playback-start", QStyle.StandardPixmap.SP_MediaPlay), "Preview", self)
        self.preview_action.setShortcut(QKeySequence("Space"))
        self.preview_action.triggered.connect(self._preview)
        self.preview_action.setToolTip("Play preview (Space)")
        toolbar.addAction(self.preview_action)

        self.render_action = QAction(self._icon("document-save", QStyle.StandardPixmap.SP_DialogSaveButton), "Render", self)
        self.render_action.setShortcut(QKeySequence("Ctrl+E"))
        self.render_action.triggered.connect(self._render)
        self.render_action.setToolTip("Render WAV (Ctrl+E)")
        toolbar.addAction(self.render_action)

        self.help_action = QAction(self._icon("help-contents", QStyle.StandardPixmap.SP_DialogHelpButton), "Help", self)
        self.help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        self.help_action.triggered.connect(lambda: self._set_active_tab("Help"))
        self.help_action.setToolTip("Open help and workflow guide (F1)")
        toolbar.addAction(self.help_action)

        toolbar.addSeparator()
        theme_picker = QWidget(self)
        theme_picker.setProperty("themePicker", True)
        theme_row = QHBoxLayout(theme_picker)
        theme_row.setContentsMargins(6, 0, 0, 0)
        theme_row.setSpacing(6)
        theme_label = QLabel("Theme")
        theme_label.setProperty("muted", True)
        self.theme_combo = QComboBox()
        for theme_name in available_theme_names():
            theme = get_theme_definition(theme_name)
            self.theme_combo.addItem(theme.label, theme.name)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.ui_scale_combo = QComboBox()
        self.ui_scale_combo.setMinimumContentsLength(6)
        for scale_percent in (50, 75, 100, 125, 150, 175, 200):
            self.ui_scale_combo.addItem(f"{scale_percent}%", scale_percent)
        self.ui_scale_combo.setCurrentIndex(self.ui_scale_combo.findData(100))
        self.ui_scale_combo.currentIndexChanged.connect(self._on_ui_scale_changed)
        scale_label = QLabel("Scale")
        scale_label.setProperty("muted", True)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo)
        theme_row.addWidget(scale_label)
        theme_row.addWidget(self.ui_scale_combo)
        toolbar.addWidget(theme_picker)

        self.zoom_action = QAction("Fit Selection", self)
        self.zoom_action.setShortcut(QKeySequence("Z"))
        self.zoom_action.triggered.connect(self._zoom_to_selection)
        self.addAction(self.zoom_action)

        self.show_full_action = QAction("Fit Full File", self)
        self.show_full_action.setShortcut(QKeySequence("F"))
        self.show_full_action.triggered.connect(self._show_full_waveform)
        self.addAction(self.show_full_action)

        self.reset_selection_action = QAction("Reset Selection", self)
        self.reset_selection_action.setShortcut(QKeySequence("R"))
        self.reset_selection_action.triggered.connect(self._reset_waveform_selection)
        self.addAction(self.reset_selection_action)

        self.source_tab_action = QAction("Source Tab", self)
        self.source_tab_action.setShortcut(QKeySequence("Ctrl+1"))
        self.source_tab_action.triggered.connect(lambda: self._set_active_tab("Source"))
        self.addAction(self.source_tab_action)

        self.stretch_tab_action = QAction("Stretch Tab", self)
        self.stretch_tab_action.setShortcut(QKeySequence("Ctrl+2"))
        self.stretch_tab_action.triggered.connect(lambda: self._set_active_tab("Stretch"))
        self.addAction(self.stretch_tab_action)

        self.effects_tab_action = QAction("Effects Tab", self)
        self.effects_tab_action.setShortcut(QKeySequence("Ctrl+3"))
        self.effects_tab_action.triggered.connect(lambda: self._set_active_tab("Effects"))
        self.addAction(self.effects_tab_action)

        self.presets_tab_action = QAction("Presets Tab", self)
        self.presets_tab_action.setShortcut(QKeySequence("Ctrl+4"))
        self.presets_tab_action.triggered.connect(lambda: self._set_active_tab("Presets"))
        self.addAction(self.presets_tab_action)

        self.help_tab_action = QAction("Help Tab", self)
        self.help_tab_action.setShortcut(QKeySequence("Ctrl+5"))
        self.help_tab_action.triggered.connect(lambda: self._set_active_tab("Help"))
        self.addAction(self.help_tab_action)

        self.toggle_ab_action = QAction("Toggle A/B", self)
        self.toggle_ab_action.setShortcut(QKeySequence("Alt+X"))
        self.toggle_ab_action.triggered.connect(self._toggle_compare_slots)
        self.addAction(self.toggle_ab_action)

    def _new_subtab_widget(self, object_name: str) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName(object_name)
        tabs.setTabBar(StaticWheelTabBar())
        return tabs

    def _new_form_page(self) -> tuple[QWidget, QFormLayout]:
        page = QWidget()
        form = QFormLayout(page)
        return page, form

    def _build_source_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.source_subtabs = self._new_subtab_widget("sourceSubtabs")
        layout.addWidget(self.source_subtabs)

        files_page, files_form = self._new_form_page()

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Choose an input audio file to preview or render")
        self.browse_input_button = QPushButton("Browse...")
        self.browse_input_button.setMinimumWidth(110)
        self.browse_input_button.clicked.connect(self._browse_input)
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_edit)
        input_row.addWidget(self.browse_input_button)
        files_form.addRow("Input audio", _wrap_layout(input_row))

        self.recent_sources_list = QListWidget()
        self.recent_sources_list.setMinimumHeight(90)
        self.recent_sources_list.itemSelectionChanged.connect(self._update_command_state)
        self.recent_sources_list.itemDoubleClicked.connect(lambda _: self._open_selected_recent_source())
        files_form.addRow("Recent sources", self.recent_sources_list)

        recent_source_actions = QHBoxLayout()
        self.open_recent_source_button = QPushButton("Open Selected")
        self.open_recent_source_button.clicked.connect(self._open_selected_recent_source)
        self.open_recent_source_folder_button = QPushButton("Open Folder")
        self.open_recent_source_folder_button.clicked.connect(self._open_selected_recent_source_folder)
        self.forget_recent_sources_button = QPushButton("Forget Missing")
        self.forget_recent_sources_button.clicked.connect(self._forget_missing_recent_sources)
        self.clear_recent_sources_button = QPushButton("Clear List")
        self.clear_recent_sources_button.clicked.connect(self._clear_recent_sources)
        recent_source_actions.addWidget(self.open_recent_source_button)
        recent_source_actions.addWidget(self.open_recent_source_folder_button)
        recent_source_actions.addWidget(self.forget_recent_sources_button)
        recent_source_actions.addWidget(self.clear_recent_sources_button)
        files_form.addRow("Source actions", _wrap_layout(recent_source_actions))

        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Choose where the rendered WAV should be saved")
        self.output_edit.textEdited.connect(self._on_output_path_edited)
        self.browse_output_button = QPushButton("Save as...")
        self.browse_output_button.setMinimumWidth(110)
        self.browse_output_button.clicked.connect(self._browse_output)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_edit)
        output_row.addWidget(self.browse_output_button)
        files_form.addRow("Render WAV", _wrap_layout(output_row))

        self.render_output_mode_combo = QComboBox()
        self.render_output_mode_combo.addItem("Wet only", RenderOutputMode.WET)
        self.render_output_mode_combo.addItem("Dry only", RenderOutputMode.DRY)
        self.render_output_mode_combo.addItem("Dry + Wet", RenderOutputMode.DRY_WET)
        self.render_output_mode_combo.currentIndexChanged.connect(self._on_render_output_mode_changed)
        files_form.addRow("Export mode", self.render_output_mode_combo)

        self.source_subtabs.addTab(files_page, "Files")

        projects_page, projects_form = self._new_form_page()

        project_actions = QHBoxLayout()
        self.open_project_button = QPushButton("Open Project")
        self.open_project_button.clicked.connect(self._browse_project)
        self.save_project_button = QPushButton("Save Project")
        self.save_project_button.clicked.connect(self._save_project)
        self.save_project_as_button = QPushButton("Save Project As")
        self.save_project_as_button.clicked.connect(self._save_project_as)
        project_actions.addWidget(self.open_project_button)
        project_actions.addWidget(self.save_project_button)
        project_actions.addWidget(self.save_project_as_button)
        projects_form.addRow("Project", _wrap_layout(project_actions))

        self.project_path_label = QLabel("No project file loaded")
        self.project_path_label.setWordWrap(True)
        projects_form.addRow("Project file", self.project_path_label)

        self.recent_projects_list = QListWidget()
        self.recent_projects_list.setMinimumHeight(110)
        self.recent_projects_list.itemSelectionChanged.connect(self._update_command_state)
        self.recent_projects_list.itemDoubleClicked.connect(lambda _: self._open_selected_recent_project())
        projects_form.addRow("Recent projects", self.recent_projects_list)

        recent_project_actions = QHBoxLayout()
        self.open_recent_project_button = QPushButton("Open Selected")
        self.open_recent_project_button.clicked.connect(self._open_selected_recent_project)
        self.forget_recent_projects_button = QPushButton("Forget Missing")
        self.forget_recent_projects_button.clicked.connect(self._forget_missing_recent_projects)
        recent_project_actions.addWidget(self.open_recent_project_button)
        recent_project_actions.addWidget(self.forget_recent_projects_button)
        projects_form.addRow("Project actions", _wrap_layout(recent_project_actions))

        self.render_queue_list = QListWidget()
        self.render_queue_list.setMinimumHeight(120)
        self.render_queue_list.itemSelectionChanged.connect(self._update_command_state)
        projects_form.addRow("Render queue", self.render_queue_list)

        queue_actions = QHBoxLayout()
        self.queue_current_button = QPushButton("Queue Current")
        self.queue_current_button.clicked.connect(self._queue_current_render)
        self.start_queue_button = QPushButton("Start Queue")
        self.start_queue_button.clicked.connect(self._start_render_queue)
        self.remove_queue_job_button = QPushButton("Remove Job")
        self.remove_queue_job_button.clicked.connect(self._remove_selected_queue_job)
        self.clear_queue_button = QPushButton("Clear Queue")
        self.clear_queue_button.clicked.connect(self._clear_render_queue)
        queue_actions.addWidget(self.queue_current_button)
        queue_actions.addWidget(self.start_queue_button)
        queue_actions.addWidget(self.remove_queue_job_button)
        queue_actions.addWidget(self.clear_queue_button)
        projects_form.addRow("Queue actions", _wrap_layout(queue_actions))

        self.render_queue_status_label = QLabel("Queue empty")
        self.render_queue_status_label.setWordWrap(True)
        projects_form.addRow("Queue status", self.render_queue_status_label)

        self.source_subtabs.addTab(projects_page, "Projects")

        self.recording_output_edit = QLineEdit()
        self.recording_output_edit.setPlaceholderText("Auto-generate a new WAV path when recording starts")
        self.browse_recording_button = QPushButton("Choose...")
        self.browse_recording_button.setMinimumWidth(110)
        self.browse_recording_button.clicked.connect(self._browse_recording_output)
        recording_output_row = QHBoxLayout()
        recording_output_row.addWidget(self.recording_output_edit)
        recording_output_row.addWidget(self.browse_recording_button)
        audio_page, audio_form = self._new_form_page()

        self.audio_backend_combo = QComboBox()
        self.audio_backend_combo.setMinimumContentsLength(16)
        for backend_id, backend_label in list_audio_backends():
            self.audio_backend_combo.addItem(backend_label, backend_id)
        self.audio_backend_combo.currentIndexChanged.connect(self._on_audio_backend_changed)
        audio_form.addRow("Audio backend", self.audio_backend_combo)

        self.host_api_combo = QComboBox()
        self.host_api_combo.setMinimumContentsLength(18)
        self.host_api_combo.currentIndexChanged.connect(self._on_host_api_changed)
        audio_form.addRow("Host API", self.host_api_combo)

        self.input_device_combo = QComboBox()
        self.input_device_combo.setMinimumContentsLength(28)
        self.input_device_combo.currentIndexChanged.connect(self._on_input_device_changed)
        self.refresh_inputs_button = QPushButton("Refresh")
        self.refresh_inputs_button.setMinimumWidth(110)
        self.refresh_inputs_button.clicked.connect(self._refresh_audio_routing)
        device_row = QHBoxLayout()
        device_row.addWidget(self.input_device_combo)
        device_row.addWidget(self.refresh_inputs_button)
        audio_form.addRow("Input device", _wrap_layout(device_row))

        self.output_device_combo = QComboBox()
        self.output_device_combo.setMinimumContentsLength(28)
        self.output_device_combo.currentIndexChanged.connect(self._on_output_device_changed)
        audio_form.addRow("Output device", self.output_device_combo)

        self.recording_sample_rate_combo = QComboBox()
        self.recording_sample_rate_combo.setMinimumContentsLength(12)
        for sample_rate in [22050, 44100, 48000, 96000]:
            self.recording_sample_rate_combo.addItem(f"{sample_rate} Hz", sample_rate)
        self.recording_sample_rate_combo.setCurrentIndex(2)
        self.recording_sample_rate_combo.currentIndexChanged.connect(lambda _: self._mark_dirty())
        audio_form.addRow("Sample rate", self.recording_sample_rate_combo)

        self.recording_channels_combo = QComboBox()
        self.recording_channels_combo.setMinimumContentsLength(12)
        self.recording_channels_combo.currentIndexChanged.connect(lambda _: self._mark_dirty())
        audio_form.addRow("Input channels", self.recording_channels_combo)

        self.preview_output_channels_combo = QComboBox()
        self.preview_output_channels_combo.setMinimumContentsLength(12)
        self.preview_output_channels_combo.currentIndexChanged.connect(lambda _: self._mark_dirty())
        audio_form.addRow("Output channels", self.preview_output_channels_combo)

        self.input_device_details_label = QLabel("No input device selected")
        self.input_device_details_label.setWordWrap(True)
        audio_form.addRow("Input info", self.input_device_details_label)

        self.output_device_details_label = QLabel("No output device selected")
        self.output_device_details_label.setWordWrap(True)
        audio_form.addRow("Output info", self.output_device_details_label)

        self.detected_host_apis_label = QLabel("No host APIs detected yet")
        self.detected_host_apis_label.setWordWrap(True)
        audio_form.addRow("Detected APIs", self.detected_host_apis_label)

        self.driver_status_label = QLabel("Driver scan not run yet")
        self.driver_status_label.setWordWrap(True)
        audio_form.addRow("Driver status", self.driver_status_label)

        self.source_subtabs.addTab(audio_page, "Audio I/O")

        recording_page, recording_form = self._new_form_page()
        recording_form.addRow("Recording WAV", _wrap_layout(recording_output_row))

        self.auto_load_recordings_checkbox = QCheckBox("Auto-load the recorded file as the current source")
        self.auto_load_recordings_checkbox.setChecked(True)
        self.auto_load_recordings_checkbox.toggled.connect(lambda _: self._mark_dirty())
        recording_form.addRow("After record", self.auto_load_recordings_checkbox)

        self.recording_level_bar = QProgressBar()
        self.recording_level_bar.setRange(0, 100)
        self.recording_level_bar.setValue(0)
        recording_form.addRow("Input level", self.recording_level_bar)

        self.recording_peak_label = QLabel("Peak hold: 0%")
        recording_form.addRow("Peak", self.recording_peak_label)

        stereo_meter_row = QHBoxLayout()
        self.recording_left_level_bar = QProgressBar()
        self.recording_left_level_bar.setRange(0, 100)
        self.recording_left_level_bar.setValue(0)
        self.recording_right_level_bar = QProgressBar()
        self.recording_right_level_bar.setRange(0, 100)
        self.recording_right_level_bar.setValue(0)
        stereo_meter_row.addWidget(QLabel("L"))
        stereo_meter_row.addWidget(self.recording_left_level_bar)
        stereo_meter_row.addWidget(QLabel("R"))
        stereo_meter_row.addWidget(self.recording_right_level_bar)
        recording_form.addRow("Stereo meter", _wrap_layout(stereo_meter_row))

        self.recording_status = QLabel("Ready to record from a microphone or other input device.")
        self.recording_status.setWordWrap(True)
        recording_form.addRow("Recording", self.recording_status)

        self.recording_duration_label = QLabel("00:00.0")
        recording_form.addRow("Duration", self.recording_duration_label)

        self.recent_takes_list = QListWidget()
        self.recent_takes_list.setMinimumHeight(130)
        self.recent_takes_list.itemDoubleClicked.connect(lambda _: self._load_selected_recent_take())
        recording_form.addRow("Recent takes", self.recent_takes_list)

        take_actions = QHBoxLayout()
        self.load_take_button = QPushButton("Load Take")
        self.load_take_button.clicked.connect(self._load_selected_recent_take)
        self.use_take_output_button = QPushButton("Use For Render Name")
        self.use_take_output_button.clicked.connect(self._use_selected_take_for_output)
        self.rename_take_button = QPushButton("Rename Take")
        self.rename_take_button.clicked.connect(self._rename_selected_recent_take)
        self.delete_take_button = QPushButton("Delete Take")
        self.delete_take_button.clicked.connect(self._delete_selected_recent_take)
        self.open_take_folder_button = QPushButton("Open Folder")
        self.open_take_folder_button.clicked.connect(self._open_selected_take_folder)
        take_actions.addWidget(self.load_take_button)
        take_actions.addWidget(self.use_take_output_button)
        take_actions.addWidget(self.rename_take_button)
        take_actions.addWidget(self.delete_take_button)
        take_actions.addWidget(self.open_take_folder_button)
        recording_form.addRow("Take actions", _wrap_layout(take_actions))

        self.source_subtabs.addTab(recording_page, "Recording")

        helper = QLabel(
            "Use the Files, Projects, Audio I/O, and Recording subtabs to keep source work compact. "
            "Double-click a recent source, take, or project to open it, and you can also drag an audio file or project file straight into the app."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)
        layout.addStretch(1)
        return tab

    def _build_stretch_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.stretch_subtabs = self._new_subtab_widget("stretchSubtabs")
        layout.addWidget(self.stretch_subtabs)

        region_page, region_form = self._new_form_page()

        self.stretch_slider = QSlider(Qt.Orientation.Horizontal)
        self.stretch_slider.setRange(2, 64)
        self.stretch_slider.setValue(8)
        self.stretch_slider.valueChanged.connect(self._update_stretch_label)
        self.stretch_slider.valueChanged.connect(lambda _: self._mark_dirty(action_label="stretch change"))
        self.stretch_label = QLabel("8x")
        stretch_row = QHBoxLayout()
        stretch_row.addWidget(self.stretch_slider)
        stretch_row.addWidget(self.stretch_label)
        region_form.addRow("Stretch factor", _wrap_layout(stretch_row))

        self.preview_start = QDoubleSpinBox()
        self.preview_start.setRange(0.0, 36000.0)
        self.preview_start.setDecimals(2)
        self.preview_start.setSuffix(" s")
        self.preview_start.valueChanged.connect(self._on_numeric_region_changed)
        self.preview_start.valueChanged.connect(lambda _: self._mark_dirty(action_label="region change"))
        region_form.addRow("Preview start", self.preview_start)

        self.preview_duration = QDoubleSpinBox()
        self.preview_duration.setRange(0.05, 30.0)
        self.preview_duration.setDecimals(2)
        self.preview_duration.setSuffix(" s")
        self.preview_duration.setValue(2.5)
        self.preview_duration.valueChanged.connect(self._on_numeric_region_changed)
        self.preview_duration.valueChanged.connect(lambda _: self._mark_dirty(action_label="region change"))
        region_form.addRow("Preview length", self.preview_duration)

        self.quality_combo = QComboBox()
        for profile in QualityProfile:
            self.quality_combo.addItem(profile.value, profile)
        self.quality_combo.currentIndexChanged.connect(lambda _: self._mark_dirty(action_label="quality change"))
        region_form.addRow("Quality", self.quality_combo)

        self.loop_crossfade_spin = QDoubleSpinBox()
        self.loop_crossfade_spin.setRange(0.0, 500.0)
        self.loop_crossfade_spin.setDecimals(0)
        self.loop_crossfade_spin.setSuffix(" ms")
        self.loop_crossfade_spin.setSingleStep(10.0)
        self.loop_crossfade_spin.setValue(80.0)
        self.loop_crossfade_spin.valueChanged.connect(self._on_loop_crossfade_changed)
        region_form.addRow("Loop crossfade", self.loop_crossfade_spin)

        self.stretch_subtabs.addTab(region_page, "Region")

        compare_page, compare_form = self._new_form_page()

        compare_grid = QGridLayout()
        self.capture_a_button = QPushButton("Store A")
        self.capture_a_button.clicked.connect(lambda: self._store_compare_slot("A"))
        self.load_a_button = QPushButton("Load A")
        self.load_a_button.clicked.connect(lambda: self._load_compare_slot("A"))
        self.capture_b_button = QPushButton("Store B")
        self.capture_b_button.clicked.connect(lambda: self._store_compare_slot("B"))
        self.load_b_button = QPushButton("Load B")
        self.load_b_button.clicked.connect(lambda: self._load_compare_slot("B"))
        self.toggle_ab_button = QPushButton("Toggle A/B")
        self.toggle_ab_button.clicked.connect(self._toggle_compare_slots)
        self.store_active_compare_button = QPushButton("Store Active")
        self.store_active_compare_button.clicked.connect(self._store_active_compare_slot)
        self.swap_compare_button = QPushButton("Swap A/B")
        self.swap_compare_button.clicked.connect(self._swap_compare_slots)
        self.compare_status_label = QLabel("A/B: A empty | B empty")
        compare_grid.addWidget(self.capture_a_button, 0, 0)
        compare_grid.addWidget(self.load_a_button, 0, 1)
        compare_grid.addWidget(self.capture_b_button, 1, 0)
        compare_grid.addWidget(self.load_b_button, 1, 1)
        compare_grid.addWidget(self.toggle_ab_button, 2, 0, 1, 2)
        compare_grid.addWidget(self.store_active_compare_button, 3, 0)
        compare_grid.addWidget(self.swap_compare_button, 3, 1)
        compare_grid.addWidget(self.compare_status_label, 4, 0, 1, 2)
        compare_form.addRow("A/B Compare", _wrap_layout(compare_grid))

        self.stretch_subtabs.addTab(compare_page, "Compare")

        history_page, history_form = self._new_form_page()

        self.preview_history_list = QListWidget()
        self.preview_history_list.setMinimumHeight(110)
        self.preview_history_list.itemSelectionChanged.connect(self._update_command_state)
        self.preview_history_list.itemDoubleClicked.connect(lambda _: self._load_selected_preview_history())
        history_form.addRow("Preview history", self.preview_history_list)

        history_actions = QHBoxLayout()
        self.load_history_button = QPushButton("Load History")
        self.load_history_button.clicked.connect(self._load_selected_preview_history)
        self.replay_history_button = QPushButton("Replay History")
        self.replay_history_button.clicked.connect(lambda: self._load_selected_preview_history(replay=True))
        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self._clear_preview_history_entries)
        history_actions.addWidget(self.load_history_button)
        history_actions.addWidget(self.replay_history_button)
        history_actions.addWidget(self.clear_history_button)
        history_form.addRow("History actions", _wrap_layout(history_actions))

        self.preview_history_status_label = QLabel("Preview history is empty")
        self.preview_history_status_label.setWordWrap(True)
        history_form.addRow("History status", self.preview_history_status_label)

        self.stretch_subtabs.addTab(history_page, "History")

        helper = QLabel(
            "Use Region for exact preview timing, Compare for A/B slots, and History for recent rendered previews. "
            "Preview and export always use the same selected waveform region."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)
        layout.addStretch(1)
        return tab

    def _build_effects_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        effects_grid = QGridLayout()
        effects_grid.setColumnStretch(1, 1)
        effects_grid.setVerticalSpacing(10)

        self.input_trim_slider, self.input_trim_value = _build_db_slider(0, minimum=-24, maximum=24)
        self.filter_enabled_checkbox = QCheckBox("On")
        self.filter_mode_combo = QComboBox()
        for mode in FilterMode:
            self.filter_mode_combo.addItem(mode.value, mode)
        self.filter_mode_combo.currentIndexChanged.connect(lambda _: self._mark_dirty())
        self.reverb_slider, self.reverb_value = _build_percent_slider(0)
        self.reverb_enabled_checkbox = QCheckBox("On")
        self.lowpass_slider, self.lowpass_value = _build_hz_slider(6000, 500, 18000)
        self.drive_slider, self.drive_value = _build_percent_slider(0)
        self.drive_enabled_checkbox = QCheckBox("On")
        self.chorus_slider, self.chorus_value = _build_percent_slider(0)
        self.chorus_enabled_checkbox = QCheckBox("On")
        self.texture_slider, self.texture_value = _build_percent_slider(0)
        self.texture_enabled_checkbox = QCheckBox("On")
        self.motion_slider, self.motion_value = _build_percent_slider(0)
        self.motion_enabled_checkbox = QCheckBox("On")
        self.pitch_drift_slider, self.pitch_drift_value = _build_percent_slider(0)
        self.pitch_drift_enabled_checkbox = QCheckBox("On")
        self.bloom_slider, self.bloom_value = _build_percent_slider(0)
        self.bloom_enabled_checkbox = QCheckBox("On")
        self.shimmer_slider, self.shimmer_value = _build_percent_slider(0)
        self.shimmer_enabled_checkbox = QCheckBox("On")
        self.granular_slider, self.granular_value = _build_percent_slider(0)
        self.granular_enabled_checkbox = QCheckBox("On")
        self.delay_slider, self.delay_value = _build_percent_slider(0)
        self.delay_enabled_checkbox = QCheckBox("On")
        self.autopan_slider, self.autopan_value = _build_percent_slider(0)
        self.autopan_enabled_checkbox = QCheckBox("On")
        self.width_slider, self.width_value = _build_percent_slider(100, max_value=200)
        self.wetdry_slider, self.wetdry_value = _build_percent_slider(100)
        self.limiter_checkbox = QCheckBox("On")
        self.limiter_checkbox.toggled.connect(lambda _: self._mark_dirty())
        self.limiter_value = QLabel(f"Soft ceiling at {SAFETY_LIMITER_CEILING_DB:.1f} dB")
        self.reverse_checkbox = QCheckBox("Reverse wet signal")
        self.freeze_checkbox = QCheckBox("Freeze selection")
        self.effect_enabled_checkboxes = [
            self.filter_enabled_checkbox,
            self.reverb_enabled_checkbox,
            self.drive_enabled_checkbox,
            self.chorus_enabled_checkbox,
            self.texture_enabled_checkbox,
            self.motion_enabled_checkbox,
            self.pitch_drift_enabled_checkbox,
            self.bloom_enabled_checkbox,
            self.shimmer_enabled_checkbox,
            self.granular_enabled_checkbox,
            self.delay_enabled_checkbox,
            self.autopan_enabled_checkbox,
        ]

        self.filter_mode_combo.setMinimumContentsLength(12)
        for slider in [
            self.input_trim_slider,
            self.reverb_slider,
            self.lowpass_slider,
            self.drive_slider,
            self.chorus_slider,
            self.texture_slider,
            self.motion_slider,
            self.pitch_drift_slider,
            self.bloom_slider,
            self.shimmer_slider,
            self.granular_slider,
            self.delay_slider,
            self.autopan_slider,
            self.width_slider,
            self.wetdry_slider,
        ]:
            slider.valueChanged.connect(lambda _: self._mark_dirty())
        for checkbox in self.effect_enabled_checkboxes:
            checkbox.setChecked(True)
            checkbox.toggled.connect(lambda _: self._mark_dirty())
        self.reverse_checkbox.toggled.connect(lambda _: self._mark_dirty())
        self.freeze_checkbox.toggled.connect(lambda _: self._mark_dirty())

        self.random_effects_button = QPushButton("Random")
        self.random_effects_button.clicked.connect(lambda: self._randomize_effects("random"))
        self.random_dark_button = QPushButton("Dark")
        self.random_dark_button.clicked.connect(lambda: self._randomize_effects("dark"))
        self.random_bright_button = QPushButton("Bright")
        self.random_bright_button.clicked.connect(lambda: self._randomize_effects("bright"))
        self.random_huge_button = QPushButton("Huge")
        self.random_huge_button.clicked.connect(lambda: self._randomize_effects("huge"))
        self.random_weird_button = QPushButton("Weird")
        self.random_weird_button.clicked.connect(lambda: self._randomize_effects("weird"))
        self.harmonize_effects_button = QPushButton("Harmonize")
        self.harmonize_effects_button.clicked.connect(self._apply_harmonize_effects)
        self.bypass_effects_button = QPushButton("Bypass All Effects")
        self.bypass_effects_button.clicked.connect(self._toggle_effects_bypass)
        self.reset_effects_button = QPushButton("Reset Effects")
        self.reset_effects_button.clicked.connect(self._reset_effects)

        row = 0
        effects_grid.addWidget(
            _build_section_header("Tone And Shape", "Core tone, stereo, level, and output behavior."),
            row,
            0,
            1,
            4,
        )
        row += 1
        _add_effect_row(effects_grid, row, "Input trim", self.input_trim_slider, self.input_trim_value)
        row += 1
        effects_grid.addWidget(QLabel("Filter mode"), row, 0)
        effects_grid.addWidget(self.filter_mode_combo, row, 1, 1, 2)
        effects_grid.addWidget(self.filter_enabled_checkbox, row, 3)
        row += 1
        _add_effect_row(effects_grid, row, "Filter freq", self.lowpass_slider, self.lowpass_value)
        row += 1
        _add_effect_row(effects_grid, row, "Drive", self.drive_slider, self.drive_value, self.drive_enabled_checkbox)
        row += 1
        _add_effect_row(effects_grid, row, "Stereo width", self.width_slider, self.width_value)
        row += 1
        _add_effect_row(effects_grid, row, "Wet/Dry", self.wetdry_slider, self.wetdry_value)
        row += 1
        effects_grid.addWidget(QLabel("Safety limiter"), row, 0)
        effects_grid.addWidget(self.limiter_value, row, 1, 1, 2)
        effects_grid.addWidget(self.limiter_checkbox, row, 3)
        row += 1
        effects_grid.addWidget(self.freeze_checkbox, row, 0, 1, 2)
        effects_grid.addWidget(self.reverse_checkbox, row, 2, 1, 2)
        row += 1

        effects_grid.addWidget(
            _build_section_header("Motion And Texture", "Movement, drift, haze, and broken texture in one place."),
            row,
            0,
            1,
            4,
        )
        row += 1
        _add_effect_row(effects_grid, row, "Chorus", self.chorus_slider, self.chorus_value, self.chorus_enabled_checkbox)
        row += 1
        _add_effect_row(effects_grid, row, "Texture", self.texture_slider, self.texture_value, self.texture_enabled_checkbox)
        row += 1
        _add_effect_row(effects_grid, row, "Motion", self.motion_slider, self.motion_value, self.motion_enabled_checkbox)
        row += 1
        _add_effect_row(
            effects_grid, row, "Pitch drift", self.pitch_drift_slider, self.pitch_drift_value, self.pitch_drift_enabled_checkbox
        )
        row += 1
        _add_effect_row(effects_grid, row, "Bloom", self.bloom_slider, self.bloom_value, self.bloom_enabled_checkbox)
        row += 1
        _add_effect_row(
            effects_grid, row, "Granular smear", self.granular_slider, self.granular_value, self.granular_enabled_checkbox
        )
        row += 1
        _add_effect_row(effects_grid, row, "Auto-pan", self.autopan_slider, self.autopan_value, self.autopan_enabled_checkbox)
        row += 1

        effects_grid.addWidget(
            _build_section_header("Space", "Ambience and tail-building effects."),
            row,
            0,
            1,
            4,
        )
        row += 1
        _add_effect_row(effects_grid, row, "Reverb", self.reverb_slider, self.reverb_value, self.reverb_enabled_checkbox)
        row += 1
        _add_effect_row(effects_grid, row, "Shimmer", self.shimmer_slider, self.shimmer_value, self.shimmer_enabled_checkbox)
        row += 1
        _add_effect_row(effects_grid, row, "Delay", self.delay_slider, self.delay_value, self.delay_enabled_checkbox)
        row += 1

        effects_grid.addWidget(
            _build_section_header("Macros", "Quick starting points and fast A/B helpers without leaving the same view."),
            row,
            0,
            1,
            4,
        )
        row += 1
        macro_grid = QGridLayout()
        macro_grid.addWidget(self.random_effects_button, 0, 0)
        macro_grid.addWidget(self.harmonize_effects_button, 0, 1)
        macro_grid.addWidget(self.bypass_effects_button, 0, 2)
        macro_grid.addWidget(self.reset_effects_button, 0, 3)
        macro_grid.addWidget(self.random_dark_button, 1, 0)
        macro_grid.addWidget(self.random_bright_button, 1, 1)
        macro_grid.addWidget(self.random_huge_button, 1, 2)
        macro_grid.addWidget(self.random_weird_button, 1, 3)
        effects_grid.addWidget(_wrap_layout(macro_grid), row, 0, 1, 4)

        helper = QLabel(
            "All effect controls stay in one view now, but they are grouped into clear sections so it still feels compact. "
            "Filter mode Off is neutral, Custom starts dry by default, and the random buttons are starting points rather than fixed outcomes."
        )
        helper.setWordWrap(True)

        layout.addLayout(effects_grid)
        layout.addWidget(helper)
        layout.addStretch(1)
        return tab

    def _build_presets_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.presets_subtabs = self._new_subtab_widget("presetsSubtabs")
        layout.addWidget(self.presets_subtabs)

        library_page, library_form = self._new_form_page()

        self.preset_search_edit = QLineEdit()
        self.preset_search_edit.setPlaceholderText("Search presets or tags")
        self.preset_search_edit.textChanged.connect(self._on_preset_filter_changed)
        self.preset_tag_filter_combo = QComboBox()
        self.preset_tag_filter_combo.currentIndexChanged.connect(self._on_preset_filter_changed)
        self.preset_favorites_only_checkbox = QCheckBox("Favorites only")
        self.preset_favorites_only_checkbox.toggled.connect(self._on_preset_filter_changed)
        filter_row = QHBoxLayout()
        filter_row.addWidget(self.preset_search_edit)
        filter_row.addWidget(self.preset_tag_filter_combo)
        filter_row.addWidget(self.preset_favorites_only_checkbox)
        library_form.addRow("Filter", _wrap_layout(filter_row))

        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_row = QHBoxLayout()
        preset_row.addWidget(self.preset_combo)
        self.preset_dirty_label = QLabel("Preset: clean")
        preset_row.addWidget(self.preset_dirty_label)
        library_form.addRow("Preset", _wrap_layout(preset_row))

        self.presets_subtabs.addTab(library_page, "Library")

        manage_page, manage_form = self._new_form_page()

        self.toggle_favorite_preset_button = QPushButton("Favorite")
        self.toggle_favorite_preset_button.clicked.connect(self._toggle_selected_preset_favorite)
        self.preset_tags_edit = QLineEdit()
        self.preset_tags_edit.setPlaceholderText("comma-separated tags")
        self.apply_preset_tags_button = QPushButton("Apply Tags")
        self.apply_preset_tags_button.clicked.connect(self._apply_selected_preset_tags)
        metadata_row = QHBoxLayout()
        metadata_row.addWidget(self.toggle_favorite_preset_button)
        metadata_row.addWidget(self.preset_tags_edit)
        metadata_row.addWidget(self.apply_preset_tags_button)
        manage_form.addRow("Metadata", _wrap_layout(metadata_row))

        self.save_new_preset_button = QPushButton("Save New")
        self.save_new_preset_button.clicked.connect(self._save_new_preset)
        self.update_preset_button = QPushButton("Update Preset")
        self.update_preset_button.clicked.connect(self._update_selected_preset)
        self.rename_preset_button = QPushButton("Rename")
        self.rename_preset_button.clicked.connect(self._rename_selected_preset)
        self.duplicate_preset_button = QPushButton("Duplicate")
        self.duplicate_preset_button.clicked.connect(self._duplicate_selected_preset)
        self.delete_preset_button = QPushButton("Delete")
        self.delete_preset_button.clicked.connect(self._delete_selected_preset)

        preset_buttons = QGridLayout()
        preset_buttons.addWidget(self.save_new_preset_button, 0, 0)
        preset_buttons.addWidget(self.update_preset_button, 0, 1)
        preset_buttons.addWidget(self.rename_preset_button, 1, 0)
        preset_buttons.addWidget(self.duplicate_preset_button, 1, 1)
        preset_buttons.addWidget(self.delete_preset_button, 2, 0, 1, 2)
        manage_form.addRow("Actions", _wrap_layout(preset_buttons))

        self.presets_subtabs.addTab(manage_page, "Manage")

        batch_page, batch_form = self._new_form_page()

        self.batch_preset_list = QListWidget()
        self.batch_preset_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.batch_preset_list.setMinimumHeight(140)
        self.batch_preset_list.itemSelectionChanged.connect(self._update_command_state)
        batch_form.addRow("Batch presets", self.batch_preset_list)

        batch_actions = QHBoxLayout()
        self.select_filtered_batch_button = QPushButton("Select Filtered")
        self.select_filtered_batch_button.clicked.connect(self._select_all_filtered_batch_presets)
        self.clear_batch_selection_button = QPushButton("Clear Selection")
        self.clear_batch_selection_button.clicked.connect(lambda: self.batch_preset_list.clearSelection())
        self.queue_batch_button = QPushButton("Queue Selected Batch")
        self.queue_batch_button.clicked.connect(self._queue_selected_preset_batch)
        batch_actions.addWidget(self.select_filtered_batch_button)
        batch_actions.addWidget(self.clear_batch_selection_button)
        batch_actions.addWidget(self.queue_batch_button)
        batch_form.addRow("Batch actions", _wrap_layout(batch_actions))

        helper = QLabel(
            "Library keeps searching and selection compact, Manage handles favorites and saving, and Batch collects filtered presets for queued exports."
        )
        helper.setWordWrap(True)
        batch_form.addRow(helper)

        self.presets_subtabs.addTab(batch_page, "Batch")
        layout.addStretch(1)
        return tab

    def _build_help_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        help_browser = QTextBrowser()
        help_browser.setOpenExternalLinks(False)
        help_browser.setReadOnly(True)
        help_browser.setHtml(_help_html())
        layout.addWidget(help_browser)
        return tab

    def _connect_recording_signals(self) -> None:
        self.recording_controller.level_changed.connect(self._on_recording_level_changed)
        self.recording_controller.channel_levels_changed.connect(self._on_recording_channel_levels_changed)
        self.recording_controller.status_changed.connect(self._on_recording_status_changed)
        self.recording_controller.recording_started.connect(self._on_recording_started)
        self.recording_controller.recording_stopped.connect(self._on_recording_complete)
        self.recording_controller.recording_failed.connect(self._on_recording_failed)

    def closeEvent(self, event) -> None:  # noqa: ANN001
        self._persist_state()
        self.recording_controller.cancel_recording()
        self.preview_player.stop()
        super().closeEvent(event)

    def _browse_input(self) -> None:
        if not self._ensure_editable("Choose the input file after the current job has finished."):
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open audio file",
            "",
            "Audio Files (*.wav *.flac *.ogg *.aiff *.aif *.mp3);;All Files (*.*)",
        )
        if not file_path:
            return
        self._load_source_audio_path(
            file_path,
            status_message=f"Loaded input: {Path(file_path).name}",
            create_undo_checkpoint=True,
        )

    def _browse_output(self) -> None:
        if not self._ensure_editable("Choose the output path after the current job has finished."):
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export WAV",
            self.output_edit.text() or "stretched.wav",
            "WAV Files (*.wav)",
        )
        if file_path:
            self.output_edit.setText(_ensure_wav_suffix(file_path))
            self.statusBar().showMessage(f"Output path selected: {Path(self.output_edit.text()).name}")

    def _browse_recording_output(self) -> None:
        if not self._ensure_editable("Choose the recording path after the current job has finished."):
            return
        default_name = self.recording_output_edit.text() or self._default_recording_path()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Recording WAV",
            default_name,
            "WAV Files (*.wav)",
        )
        if file_path:
            self.recording_output_edit.setText(_ensure_wav_suffix(file_path))
            self.statusBar().showMessage(f"Recording path selected: {Path(self.recording_output_edit.text()).name}")

    def _refresh_audio_routing(
        self,
        *,
        backend: str | None = None,
        host_api_name: str | None = None,
        input_device_id: str | None = None,
        output_device_id: str | None = None,
    ) -> None:
        current_backend = backend if backend is not None else self._selected_audio_backend()
        current_host_api = host_api_name if host_api_name is not None else self._selected_host_api_name()
        current_input = input_device_id if input_device_id is not None else self._selected_input_device_id()
        current_output = output_device_id if output_device_id is not None else self._selected_output_device_id()

        backend_index = self.audio_backend_combo.findData(current_backend)
        if backend_index >= 0 and self.audio_backend_combo.currentIndex() != backend_index:
            self.audio_backend_combo.blockSignals(True)
            self.audio_backend_combo.setCurrentIndex(backend_index)
            self.audio_backend_combo.blockSignals(False)

        snapshot = list_audio_routing(requested_backend=current_backend, host_api_name=current_host_api)

        self.host_api_combo.blockSignals(True)
        self.host_api_combo.clear()
        for name in snapshot.host_api_names:
            self.host_api_combo.addItem(name, name)
        if self.host_api_combo.count() == 0:
            self.host_api_combo.addItem("No host APIs", "")
        host_match = 0
        if current_host_api:
            for index in range(self.host_api_combo.count()):
                if self.host_api_combo.itemData(index) == current_host_api:
                    host_match = index
                    break
        self.host_api_combo.setCurrentIndex(host_match)
        self.host_api_combo.setEnabled(snapshot.active_backend == AUDIO_BACKEND_PORTAUDIO)
        self.host_api_combo.blockSignals(False)

        self._populate_device_combo(self.input_device_combo, snapshot.input_devices, current_input, "No audio inputs detected")
        self._populate_device_combo(self.output_device_combo, snapshot.output_devices, current_output, "No audio outputs detected")
        self._refresh_channel_combo(self.recording_channels_combo, self._selected_input_device_id(), "input")
        self._refresh_channel_combo(self.preview_output_channels_combo, self._selected_output_device_id(), "output")
        self.current_audio_snapshot = snapshot
        self._update_audio_device_details()
        self._update_audio_driver_diagnostics(snapshot)
        if snapshot.input_devices:
            self.recording_status.setText(
                f"Ready to record via {snapshot.active_backend.upper()} from the selected input device."
            )
        else:
            self.recording_status.setText("No audio input devices are currently available.")
        self._update_command_state()

    def _populate_device_combo(
        self,
        combo: QComboBox,
        devices,
        selected_id: str,
        empty_text: str,
    ) -> None:  # noqa: ANN001
        combo.blockSignals(True)
        combo.clear()
        if devices:
            for device in devices:
                combo.addItem(device.label, device.device_id)
            match_index = 0
            if selected_id:
                for index in range(combo.count()):
                    if combo.itemData(index) == selected_id:
                        match_index = index
                        break
            combo.setCurrentIndex(match_index)
        else:
            combo.addItem(empty_text, None)
        combo.blockSignals(False)

    def _refresh_channel_combo(self, combo: QComboBox, device_id: str, direction: str) -> None:
        current_value = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for count in channel_options(
            device_id,
            direction,
            requested_backend=self._selected_audio_backend(),
            host_api_name=self._selected_host_api_name(),
        ):
            label = "Mono (1 ch)" if count == 1 else "Stereo (2 ch)"
            combo.addItem(label, count)
        if combo.count() == 0:
            combo.addItem("Mono (1 ch)", 1)
        match_index = 0
        if current_value is not None:
            for index in range(combo.count()):
                if combo.itemData(index) == current_value:
                    match_index = index
                    break
        combo.setCurrentIndex(match_index)
        combo.blockSignals(False)

    def _on_audio_backend_changed(self) -> None:
        self._refresh_audio_routing(backend=self._selected_audio_backend(), host_api_name="")
        self._mark_dirty()

    def _on_host_api_changed(self) -> None:
        self._refresh_audio_routing(
            backend=self._selected_audio_backend(),
            host_api_name=self._selected_host_api_name(),
        )
        self._mark_dirty()

    def _on_input_device_changed(self) -> None:
        self._refresh_channel_combo(self.recording_channels_combo, self._selected_input_device_id(), "input")
        self._update_audio_device_details()
        self._mark_dirty()

    def _on_output_device_changed(self) -> None:
        self._refresh_channel_combo(self.preview_output_channels_combo, self._selected_output_device_id(), "output")
        self._update_audio_device_details()
        self._mark_dirty()

    def _update_audio_device_details(self) -> None:
        backend = self._selected_audio_backend()
        host_api_name = self._selected_host_api_name()
        self.input_device_details_label.setText(
            device_details(
                device_id=self._selected_input_device_id(),
                direction="input",
                requested_backend=backend,
                host_api_name=host_api_name,
            )
        )

    def _update_audio_driver_diagnostics(self, snapshot) -> None:  # noqa: ANN001
        host_names = snapshot.host_api_names if snapshot is not None else []
        if host_names:
            self.detected_host_apis_label.setText(", ".join(host_names))
        else:
            self.detected_host_apis_label.setText("No host APIs detected")

        asio_detected = any(name.strip().lower() == "asio" for name in host_names)
        if snapshot is None:
            self.driver_status_label.setText("No driver information available.")
            return

        active_backend = snapshot.active_backend.upper()
        input_count = len(snapshot.input_devices)
        output_count = len(snapshot.output_devices)
        if asio_detected:
            asio_text = "ASIO available to the app."
        else:
            asio_text = "ASIO not detected by the app right now."
        if snapshot.active_backend == AUDIO_BACKEND_QT:
            fallback_text = "Using Qt fallback device routing."
        else:
            fallback_text = f"Using {active_backend} device routing."
        self.driver_status_label.setText(
            f"{fallback_text} {asio_text} Inputs detected: {input_count}. Outputs detected: {output_count}. "
            "Driver and port visibility depends on what Windows and the installed audio driver expose."
        )

    def _load_waveform(self, input_path: str) -> bool:
        try:
            self.waveform_overview = load_waveform_overview(input_path)
        except Exception as exc:
            self._clear_loaded_input("No waveform loaded")
            self._show_error(str(exc))
            self.statusBar().showMessage("Could not load input audio")
            return False

        self.waveform_widget.set_overview(self.waveform_overview)
        self._apply_region_to_waveform(
            RegionSelection(
                float(self.preview_start.value()),
                float(self.preview_start.value() + self.preview_duration.value()),
            )
        )
        self.region_status.setText(f"{self.waveform_overview.duration_seconds:.2f}s loaded")
        return True

    def _on_waveform_region_changed(self, start_seconds: float, end_seconds: float) -> None:
        self._syncing_region = True
        self.preview_start.setValue(start_seconds)
        self.preview_duration.setValue(max(0.05, end_seconds - start_seconds))
        self._syncing_region = False
        self._update_region_status(RegionSelection(start_seconds, end_seconds))
        self._mark_dirty(action_label="region change")

    def _on_numeric_region_changed(self) -> None:
        if self._syncing_region:
            return
        start = float(self.preview_start.value())
        end = start + float(self.preview_duration.value())
        if self.waveform_overview is None:
            normalized = self._quantized_region(RegionSelection(start, end))
            self._syncing_region = True
            self.preview_start.setValue(normalized.start_seconds)
            self.preview_duration.setValue(max(0.05, normalized.duration_seconds))
            self._syncing_region = False
            self._update_region_status(normalized)
            self._mark_dirty(action_label="region change")
            return
        self.waveform_widget.set_region(RegionSelection(start, end), emit_signal=False)
        normalized = self.waveform_widget.region
        self._syncing_region = True
        self.preview_start.setValue(normalized.start_seconds)
        self.preview_duration.setValue(max(0.05, normalized.duration_seconds))
        self._syncing_region = False
        self._update_region_status(normalized)
        self._mark_dirty(action_label="region change")

    def _on_workspace_tab_changed(self, index: int) -> None:
        del index
        if not hasattr(self, "preview_start"):
            return
        self._persist_state()
        if self.preview_player.is_active() and self.current_preview is not None:
            self._set_preview_state("looping" if self.loop_checkbox.isChecked() else "playing", result=self.current_preview)
        elif self.current_preview is not None:
            self._set_preview_state("ready", result=self.current_preview)

    def _on_snap_to_grid_toggled(self, checked: bool) -> None:
        snap_step = 0.1 if checked else None
        self.waveform_widget.set_snap_step(snap_step)
        self.preview_start.setSingleStep(0.1 if checked else 0.01)
        self.preview_duration.setSingleStep(0.1 if checked else 0.01)
        self._on_numeric_region_changed()
        self.statusBar().showMessage(
            "Snap to 0.1 second grid enabled." if checked else "Snap to 0.1 second grid disabled."
        )

    def _quantized_region(self, region: RegionSelection) -> RegionSelection:
        snap_step = 0.1 if self.snap_to_grid_checkbox.isChecked() else None
        if snap_step is None:
            return region
        start = round(region.start_seconds / snap_step) * snap_step
        end = round(region.end_seconds / snap_step) * snap_step
        end = max(start + snap_step, end)
        return RegionSelection(round(start, 3), round(end, 3))

    def _update_stretch_label(self, value: int) -> None:
        self.stretch_label.setText(f"{value:.0f}x")

    def _preview(self) -> None:
        input_path = self.input_edit.text().strip()
        if not input_path:
            self._show_error("Choose an input audio file before previewing.")
            return
        if not Path(input_path).exists():
            self._show_error(f"Input audio file was not found:\n{input_path}")
            return
        if not self._ensure_idle("Wait for the current render or recording job to finish first."):
            return
        preview_key = self._preview_cache_key()
        if self.current_preview is not None and preview_key == self.current_preview_key:
            self._play_preview_result(self.current_preview, from_cache=True)
            return

        self.preview_player.stop()
        self.current_preview = None
        self.current_preview_key = None
        self.current_playback_duration_seconds = 0.0
        self.playback_timer.stop()
        self.waveform_widget.set_playhead(None)
        self._set_preview_state("rendering")
        self._update_command_state()
        self.progress_bar.setValue(0)

        self.preview_worker = PreviewWorker(self._preview_config())
        self.preview_worker.status_changed.connect(self._on_job_status)
        self.preview_worker.preview_completed.connect(self._on_preview_complete)
        self.preview_worker.preview_failed.connect(self._on_job_failed)
        self.preview_worker.finished.connect(self._on_preview_finished)
        self.preview_worker.start()
        self._update_command_state()

    def _render(self) -> None:
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()
        if not input_path or not output_path:
            self._show_error("Choose both an input file and an output WAV path.")
            return
        if not Path(input_path).exists():
            self._show_error(f"Input audio file was not found:\n{input_path}")
            return
        if not self._ensure_idle("Wait for the current render or recording job to finish first."):
            return
        self.preview_player.stop()
        self.playback_timer.stop()
        self.current_playback_duration_seconds = 0.0
        self.waveform_widget.set_playhead(None)
        current_job = self._current_render_job()
        self.statusBar().showMessage(f"Export rendering: {Path(current_job.output_path).name}")
        self.progress_bar.setValue(0)
        self.render_worker = RenderWorker(self._render_config_for_job(current_job))
        self.render_worker.status_changed.connect(self._on_job_status)
        self.render_worker.render_completed.connect(self._on_render_complete)
        self.render_worker.render_failed.connect(self._on_job_failed)
        self.render_worker.finished.connect(self._on_render_finished)
        self.render_worker.start()
        self._update_command_state()

    def _start_recording(self) -> None:
        if not self._ensure_idle("Wait for the current preview or render job to finish first."):
            return
        if self.preview_player.is_active():
            self._stop_preview()
        if self.recording_controller.is_recording():
            self._show_error("A recording is already in progress.")
            return
        if self.input_device_combo.currentData() is None:
            self._show_error("No audio input device is available for recording.")
            return

        output_path = self.recording_output_edit.text().strip() or self._default_recording_path()
        output_path = _ensure_wav_suffix(output_path)
        self.recording_output_edit.setText(output_path)

        try:
            self.recording_controller.start_recording(self._recording_config())
        except Exception as exc:
            self._show_error(str(exc))
            self.statusBar().showMessage("Recording could not start")
            return
        self.recording_peak_hold = 0.0
        self.recording_level_bar.setValue(0)
        self.recording_left_level_bar.setValue(0)
        self.recording_right_level_bar.setValue(0)
        self.recording_peak_label.setText("Peak hold: 0%")
        self.progress_bar.setValue(0)
        self._update_command_state()

    def _stop_active(self) -> None:
        if self.recording_controller.is_recording():
            self.recording_controller.stop_recording()
            self._update_command_state()
            return
        self._stop_preview()

    def _stop_preview(self) -> None:
        self._clear_deferred_compare_preview()
        self.preview_player.stop()
        self.playback_timer.stop()
        self.current_playback_duration_seconds = 0.0
        self._current_playback_audio = None
        self.output_left_level_bar.setValue(0)
        self.output_right_level_bar.setValue(0)
        self.waveform_widget.set_playhead(None)
        self._set_preview_state("idle", event="stopped")
        self._update_command_state()

    def _play_preview_result(self, result: PreviewResult, *, from_cache: bool = False, loop_restart: bool = False) -> None:
        self.current_preview = result
        playback_audio = result.audio
        if self.loop_checkbox.isChecked():
            playback_audio = build_loop_crossfade_audio(
                result.audio,
                result.sample_rate,
                float(self.loop_crossfade_spin.value()),
            )
        self.current_playback_duration_seconds = playback_audio.shape[0] / max(1, result.sample_rate)
        self._current_playback_audio = playback_audio
        self.playback_clock.restart()
        self.playback_timer.start()
        self.preview_player.play(
            playback_audio,
            result.sample_rate,
            self._on_preview_playback_finished,
            audio_backend=self._selected_audio_backend(),
            output_device_id=self._selected_output_device_id(),
            output_channels=self._selected_output_channels(),
            host_api_name=self._selected_host_api_name(),
        )
        self._set_preview_state("looping" if loop_restart else "playing", result=result, from_cache=from_cache)
        self._update_command_state()

    def _on_preview_playback_finished(self) -> None:
        if self.loop_checkbox.isChecked() and self.current_preview is not None:
            self._play_preview_result(self.current_preview, loop_restart=True)
            return
        self.playback_timer.stop()
        self.current_playback_duration_seconds = 0.0
        self.waveform_widget.set_playhead(None)
        self._set_preview_state("idle", event="finished" if self.current_preview is not None else "selection changed")
        pending_preview = self._pending_compare_preview_result
        pending_key = self._pending_compare_preview_key
        pending_render = self._pending_compare_render
        self._clear_deferred_compare_preview()
        if pending_preview is not None and pending_key is not None:
            self.current_preview = pending_preview
            self.current_preview_key = pending_key
            self._play_preview_result(pending_preview, from_cache=True)
            return
        if pending_render:
            self._preview()
            return
        self._update_command_state()

    def _update_playhead(self) -> None:
        if self.current_preview is None:
            return
        region = self._current_region()
        preview_seconds = self.current_playback_duration_seconds or (
            self.current_preview.preview_frames / self.current_preview.sample_rate
        )
        elapsed = self.playback_clock.elapsed() / 1000.0
        progress = (elapsed % max(0.01, preview_seconds)) / max(0.01, preview_seconds)
        self.waveform_widget.set_playhead(region.start_seconds + (region.duration_seconds * progress))

        audio = getattr(self, "_current_playback_audio", None)
        if audio is not None:
            frame = int(elapsed * self.current_preview.sample_rate)
            chunk_frames = int(0.04 * self.current_preview.sample_rate)
            start = max(0, frame - chunk_frames)
            end = min(audio.shape[0], frame)
            chunk = audio[start:end]
            if chunk.size > 0:
                if chunk.ndim == 1:
                    left = right = float(np.max(np.abs(chunk)))
                else:
                    left = float(np.max(np.abs(chunk[:, 0])))
                    right = float(np.max(np.abs(chunk[:, 1]))) if chunk.shape[1] > 1 else left
                self.output_left_level_bar.setValue(int(np.clip(left, 0.0, 1.0) * 100))
                self.output_right_level_bar.setValue(int(np.clip(right, 0.0, 1.0) * 100))
            else:
                self.output_left_level_bar.setValue(0)
                self.output_right_level_bar.setValue(0)

    def _on_job_status(self, progress: int, message: str) -> None:
        self.progress_bar.setValue(progress)
        self.statusBar().showMessage(message)
        if self.preview_worker is not None:
            self.preview_status_label.setText(f"Preview rendering. {message}")

    def _on_preview_complete(self, result: PreviewResult) -> None:
        self.current_preview = result
        self.current_preview_key = self._preview_cache_key()
        self._remember_preview_history(result)
        self.progress_bar.setValue(100)
        self._set_preview_state("ready", result=result)
        self._play_preview_result(result)

    def _on_render_complete(self, result: RenderResult) -> None:
        duration_ratio = result.output_frames / max(result.input_frames, 1)
        self.progress_bar.setValue(100)
        if self.render_queue_running and self.active_render_job is not None:
            self.render_queue_results.append(result)
            self.statusBar().showMessage(
                f"Queue job complete: {self.active_render_job.preset_name} ({len(result.output_paths)} file(s))"
            )
            return
        output_text = "\n".join(result.output_paths)
        self.statusBar().showMessage(f"Export complete: {Path(result.output_path).name}")
        QMessageBox.information(
            self,
            "Render complete",
            (
                f"Saved WAV to:\n{output_text}\n\n"
                f"Sample rate: {result.sample_rate} Hz\n"
                f"Channels: {result.channels}\n"
                f"Input frames: {result.input_frames}\n"
                f"Output frames: {result.output_frames}\n"
                f"Actual length ratio: {duration_ratio:.2f}x"
            ),
        )

    def _on_job_failed(self, message: str) -> None:
        self._show_error(message)
        if self.render_queue_running:
            failed_name = self.active_render_job.preset_name if self.active_render_job is not None else "queued render"
            self.render_queue_running = False
            self.active_render_job = None
            self._refresh_render_queue_list()
            self.statusBar().showMessage(f"Render queue stopped on {failed_name}")
            return
        self.statusBar().showMessage("Render failed")

    def _on_render_finished(self) -> None:
        if self.render_worker is not None:
            self.render_worker.deleteLater()
            self.render_worker = None
        if self.render_queue_running:
            self._start_next_render_job()
            return
        self._update_command_state()

    def _on_preview_finished(self) -> None:
        if self.preview_worker is not None:
            self.preview_worker.deleteLater()
            self.preview_worker = None
        if self.preview_player.is_active():
            self._set_preview_state("playing", result=self.current_preview)
        elif self.current_preview is not None:
            self._set_preview_state("ready", result=self.current_preview)
        else:
            self._set_preview_state("idle")
        self._update_command_state()

    def _on_recording_level_changed(self, level: float) -> None:
        normalized = float(np.clip(level, 0.0, 1.0))
        self.recording_peak_hold = max(self.recording_peak_hold * 0.96, normalized)
        self.recording_level_bar.setValue(int(normalized * 100))
        self.recording_peak_label.setText(f"Peak hold: {int(self.recording_peak_hold * 100)}%")

    def _on_recording_channel_levels_changed(self, levels) -> None:  # noqa: ANN001
        normalized_levels = [int(float(np.clip(level, 0.0, 1.0)) * 100) for level in levels]
        left = normalized_levels[0] if normalized_levels else 0
        right = normalized_levels[1] if len(normalized_levels) > 1 else left
        self.recording_left_level_bar.setValue(left)
        self.recording_right_level_bar.setValue(right)

    def _on_recording_status_changed(self, message: str) -> None:
        self.recording_status.setText(message)
        self.statusBar().showMessage(message)

    def _on_recording_started(self, device_name: str) -> None:
        self.recording_clock.restart()
        self.recording_timer.start()
        self.recording_duration_label.setText("00:00.0")
        config = self._recording_config()
        self.recording_status.setText(
            f"Recording from {device_name} at {config.sample_rate} Hz / {config.channels} ch"
        )
        self.statusBar().showMessage(f"Recording from {device_name}")
        self._update_command_state()

    def _on_recording_complete(self, result: RecordingResult) -> None:
        self.recording_timer.stop()
        self.recording_level_bar.setValue(0)
        self.recording_left_level_bar.setValue(0)
        self.recording_right_level_bar.setValue(0)
        self.recording_peak_hold = 0.0
        self.recording_peak_label.setText("Peak hold: 0%")
        self.recording_duration_label.setText(_format_seconds(result.duration_seconds))
        self.recording_status.setText(f"Saved recording to {Path(result.output_path).name}")
        self.statusBar().showMessage(f"Recording saved: {Path(result.output_path).name}")
        self.recording_output_edit.setText(str(next_available_recording_path(result.output_path)))
        self._remember_recent_take(result)
        if result.auto_load:
            self.input_edit.setText(result.output_path)
            if not self.output_edit.text():
                self.output_edit.setText(str(Path(result.output_path).with_name(f"{Path(result.output_path).stem}_stretched.wav")))
            self._load_waveform(result.output_path)
            self.statusBar().showMessage(f"Recording saved and loaded: {Path(result.output_path).name}")
        else:
            self.statusBar().showMessage(f"Recording saved: {Path(result.output_path).name}")
        QMessageBox.information(
            self,
            "Recording saved",
            (
                f"Saved WAV to:\n{result.output_path}\n\n"
                f"Sample rate: {result.sample_rate} Hz\n"
                f"Channels: {result.channels}\n"
                f"Frames: {result.frames}\n"
                f"Duration: {result.duration_seconds:.2f}s"
            ),
        )
        self._update_command_state()

    def _on_recording_failed(self, message: str) -> None:
        self.recording_timer.stop()
        self.recording_level_bar.setValue(0)
        self.recording_left_level_bar.setValue(0)
        self.recording_right_level_bar.setValue(0)
        self.recording_peak_hold = 0.0
        self.recording_peak_label.setText("Peak hold: 0%")
        self.recording_status.setText("Recording failed")
        self._show_error(message)
        self.statusBar().showMessage("Recording failed")
        self._update_command_state()

    def _update_recording_duration(self) -> None:
        if not self.recording_controller.is_recording():
            self.recording_timer.stop()
            return
        self.recording_duration_label.setText(_format_seconds(self.recording_clock.elapsed() / 1000.0))

    def _remember_recent_take(self, result: RecordingResult) -> None:
        self.recent_takes = merge_recent_takes(self.recent_takes, recent_take_from_result(result))
        self._refresh_recent_takes_list()

    def _refresh_recent_takes_list(self) -> None:
        self.recent_takes = filter_existing_recent_takes(self.recent_takes)
        self.recent_takes_list.clear()
        for take in self.recent_takes:
            item = QListWidgetItem(
                f"{Path(take.path).name}  |  {_format_seconds(take.duration_seconds)}  |  {take.sample_rate} Hz"
            )
            item.setData(Qt.ItemDataRole.UserRole, take.path)
            item.setToolTip(f"{take.path}\nRecorded: {take.timestamp}")
            self.recent_takes_list.addItem(item)
        if self.recent_takes_list.count() > 0:
            self.recent_takes_list.setCurrentRow(0)
        self._update_recent_take_buttons()

    def _selected_recent_take(self) -> RecentTake | None:
        item = self.recent_takes_list.currentItem()
        if item is None:
            return None
        path = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(path, str):
            return None
        for take in self.recent_takes:
            if take.path == path:
                return take
        return None

    def _load_selected_recent_take(self) -> None:
        if not self._ensure_editable("Load a take after the current job has finished."):
            return
        take = self._selected_recent_take()
        if take is None:
            self._show_error("Select a recent take to load it.")
            return
        if not Path(take.path).exists():
            self.recent_takes = filter_existing_recent_takes(self.recent_takes)
            self._refresh_recent_takes_list()
            self._show_error("The selected take file no longer exists.")
            return
        self._load_source_audio_path(
            take.path,
            status_message=f"Loaded recent take: {Path(take.path).name}",
            create_undo_checkpoint=True,
        )

    def _use_selected_take_for_output(self) -> None:
        if not self._ensure_editable("Update the render name after the current job has finished."):
            return
        take = self._selected_recent_take()
        if take is None:
            self._show_error("Select a recent take to build a render filename from it.")
            return
        render_path = Path(take.path).with_name(f"{Path(take.path).stem}_stretched.wav")
        self.output_edit.setText(str(render_path))
        self.statusBar().showMessage(f"Render name updated from take: {render_path.name}")

    def _rename_selected_recent_take(self) -> None:
        if not self._ensure_editable("Rename a take after the current job has finished."):
            return
        take = self._selected_recent_take()
        if take is None:
            self._show_error("Select a recent take to rename it.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename take", "New take name:", text=Path(take.path).stem)
        if not ok or not new_name.strip():
            return
        try:
            renamed_path = rename_take_file(take.path, new_name.strip())
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.recent_takes = [
            RecentTake(
                path=str(renamed_path) if item.path == take.path else item.path,
                duration_seconds=item.duration_seconds,
                sample_rate=item.sample_rate,
                timestamp=item.timestamp,
            )
            for item in self.recent_takes
        ]
        self._retarget_open_paths(take.path, str(renamed_path))
        self._refresh_recent_takes_list()
        self.statusBar().showMessage(f"Renamed take: {renamed_path.name}")

    def _delete_selected_recent_take(self) -> None:
        if not self._ensure_editable("Delete a take after the current job has finished."):
            return
        take = self._selected_recent_take()
        if take is None:
            self._show_error("Select a recent take to delete it.")
            return
        answer = QMessageBox.question(
            self,
            "Delete take",
            f"Delete this take from disk?\n\n{take.path}",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            Path(take.path).unlink(missing_ok=False)
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.recent_takes = remove_recent_take(self.recent_takes, take.path)
        if self.input_edit.text().strip() == take.path:
            self.input_edit.clear()
            self._clear_loaded_input("Take deleted")
        self._refresh_recent_takes_list()
        self.statusBar().showMessage(f"Deleted take: {Path(take.path).name}")

    def _open_selected_take_folder(self) -> None:
        take = self._selected_recent_take()
        if take is None:
            self._show_error("Select a recent take to open its folder.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(take.path).parent)))

    def _retarget_open_paths(self, old_path: str, new_path: str) -> None:
        if self.input_edit.text().strip() == old_path:
            self.input_edit.setText(new_path)
            self._load_waveform(new_path)
        if self.output_edit.text().strip() == str(Path(old_path).with_name(f"{Path(old_path).stem}_stretched.wav")):
            self.output_edit.setText(str(Path(new_path).with_name(f"{Path(new_path).stem}_stretched.wav")))

    def _update_recent_take_buttons(self) -> None:
        enabled = self.recent_takes_list.count() > 0 and not self._is_processing()
        self.load_take_button.setEnabled(enabled)
        self.use_take_output_button.setEnabled(enabled)
        self.rename_take_button.setEnabled(enabled)
        self.delete_take_button.setEnabled(enabled)
        self.open_take_folder_button.setEnabled(self.recent_takes_list.count() > 0)

    def _workflow_snapshot_ready(self) -> bool:
        return hasattr(self, "preview_start") and hasattr(self, "output_edit") and hasattr(self, "render_output_mode_combo")

    def _current_workflow_snapshot(self) -> WorkflowStateSnapshot:
        region = self._current_region()
        return WorkflowStateSnapshot(
            input_path=self.input_edit.text().strip(),
            output_path=self.output_edit.text().strip(),
            render_output_mode=self._selected_render_output_mode().value,
            preview_start=float(self.preview_start.value()),
            preview_length=float(self.preview_duration.value()),
            waveform_region_start=region.start_seconds,
            waveform_region_end=region.end_seconds,
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            effects=self._effect_settings(),
            selected_preset_name=self.current_preset_name,
            compare_slot_a=self.compare_slots.get("A"),
            compare_slot_b=self.compare_slots.get("B"),
            loop_enabled=self.loop_checkbox.isChecked(),
            loop_crossfade_ms=self._selected_loop_crossfade_ms(),
        )

    def _resolve_workflow_action_label(self, action_label: str | None = None) -> str:
        if action_label:
            return action_label
        sender = self.sender()
        if sender in {getattr(self, "preview_start", None), getattr(self, "preview_duration", None)}:
            return "region change"
        if sender is getattr(self, "stretch_slider", None):
            return "stretch change"
        if sender is getattr(self, "quality_combo", None):
            return "quality change"
        if sender is getattr(self, "output_edit", None):
            return "output path edit"
        if sender is getattr(self, "render_output_mode_combo", None):
            return "export mode change"
        if sender is getattr(self, "loop_checkbox", None):
            return "loop toggle"
        if sender is getattr(self, "loop_crossfade_spin", None):
            return "loop crossfade change"
        effect_controls = {
            getattr(self, "input_trim_slider", None),
            getattr(self, "filter_mode_combo", None),
            getattr(self, "reverb_slider", None),
            getattr(self, "lowpass_slider", None),
            getattr(self, "drive_slider", None),
            getattr(self, "chorus_slider", None),
            getattr(self, "texture_slider", None),
            getattr(self, "motion_slider", None),
            getattr(self, "pitch_drift_slider", None),
            getattr(self, "bloom_slider", None),
            getattr(self, "shimmer_slider", None),
            getattr(self, "granular_slider", None),
            getattr(self, "delay_slider", None),
            getattr(self, "autopan_slider", None),
            getattr(self, "width_slider", None),
            getattr(self, "wetdry_slider", None),
            getattr(self, "limiter_checkbox", None),
            getattr(self, "reverse_checkbox", None),
            getattr(self, "freeze_checkbox", None),
            getattr(self, "filter_enabled_checkbox", None),
            getattr(self, "reverb_enabled_checkbox", None),
            getattr(self, "drive_enabled_checkbox", None),
            getattr(self, "chorus_enabled_checkbox", None),
            getattr(self, "texture_enabled_checkbox", None),
            getattr(self, "motion_enabled_checkbox", None),
            getattr(self, "pitch_drift_enabled_checkbox", None),
            getattr(self, "bloom_enabled_checkbox", None),
            getattr(self, "shimmer_enabled_checkbox", None),
            getattr(self, "granular_enabled_checkbox", None),
            getattr(self, "delay_enabled_checkbox", None),
            getattr(self, "autopan_enabled_checkbox", None),
        }
        if sender in effect_controls:
            return "effects change"
        return "workflow change"

    def _update_workflow_history_action_labels(self) -> None:
        if not hasattr(self, "undo_action") or not hasattr(self, "redo_action"):
            return
        undo_label = self.undo_stack[-1].label if self.undo_stack else "workflow change"
        redo_label = self.redo_stack[-1].label if self.redo_stack else "workflow change"
        self.undo_action.setToolTip(
            f"Undo {undo_label} (Ctrl+Z)" if self.undo_stack else "Undo workflow change (Ctrl+Z)"
        )
        self.redo_action.setToolTip(
            f"Redo {redo_label} (Ctrl+Y / Ctrl+Shift+Z)"
            if self.redo_stack
            else "Redo workflow change (Ctrl+Y / Ctrl+Shift+Z)"
        )

    def _append_undo_snapshot(self, snapshot: WorkflowStateSnapshot, action_label: str | None = None) -> None:
        entry = WorkflowHistoryEntry(snapshot=snapshot, label=self._resolve_workflow_action_label(action_label))
        if self.undo_stack and self.undo_stack[-1] == entry:
            return
        self.undo_stack.append(entry)
        if len(self.undo_stack) > 100:
            self.undo_stack = self.undo_stack[-100:]

    def _append_redo_snapshot(self, snapshot: WorkflowStateSnapshot, action_label: str | None = None) -> None:
        entry = WorkflowHistoryEntry(snapshot=snapshot, label=self._resolve_workflow_action_label(action_label))
        if self.redo_stack and self.redo_stack[-1] == entry:
            return
        self.redo_stack.append(entry)
        if len(self.redo_stack) > 100:
            self.redo_stack = self.redo_stack[-100:]

    def _capture_workflow_undo_snapshot_if_needed(self, action_label: str | None = None) -> None:
        if self._suspend_workflow_history_tracking or not self._workflow_snapshot_ready():
            return
        current = self._current_workflow_snapshot()
        if self._workflow_history_baseline_snapshot is None:
            self._workflow_history_baseline_snapshot = current
            return
        if not self._workflow_history_pending and current != self._workflow_history_baseline_snapshot:
            resolved_label = self._resolve_workflow_action_label(action_label)
            self._append_undo_snapshot(self._workflow_history_baseline_snapshot, resolved_label)
            self.redo_stack.clear()
            self._workflow_history_pending = True
            self._workflow_history_pending_label = resolved_label
        self.workflow_history_timer.start()
        self._update_command_state()

    def _commit_workflow_history_baseline(self) -> None:
        if self._suspend_workflow_history_tracking or not self._workflow_snapshot_ready():
            return
        self._workflow_history_baseline_snapshot = self._current_workflow_snapshot()
        self._workflow_history_pending = False
        self._workflow_history_pending_label = None
        self._update_command_state()

    def _flush_workflow_history(self) -> None:
        if self.workflow_history_timer.isActive():
            self.workflow_history_timer.stop()
        self._commit_workflow_history_baseline()

    def _prepare_immediate_workflow_action(self, action_label: str | None = None) -> None:
        if self._suspend_workflow_history_tracking or not self._workflow_snapshot_ready():
            return
        self._flush_workflow_history()
        resolved_label = self._resolve_workflow_action_label(action_label)
        self._append_undo_snapshot(self._current_workflow_snapshot(), resolved_label)
        self.redo_stack.clear()
        self._workflow_history_pending_label = resolved_label
        self._update_command_state()

    def _finish_immediate_workflow_action(self) -> None:
        if self._workflow_snapshot_ready():
            self._workflow_history_baseline_snapshot = self._current_workflow_snapshot()
        self._workflow_history_pending = False
        self._workflow_history_pending_label = None
        if self.workflow_history_timer.isActive():
            self.workflow_history_timer.stop()
        self._update_command_state()

    def _reset_workflow_history(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._workflow_history_pending = False
        self._workflow_history_pending_label = None
        if self.workflow_history_timer.isActive():
            self.workflow_history_timer.stop()
        self._workflow_history_baseline_snapshot = self._current_workflow_snapshot() if self._workflow_snapshot_ready() else None
        self._clear_deferred_compare_preview()
        self._update_command_state()

    def _apply_dirty_state(
        self,
        *,
        audio_change: bool,
        event: str = "selection changed",
        clear_bypass_snapshot: bool = True,
    ) -> None:
        if clear_bypass_snapshot:
            self.effects_bypass_snapshot = None
            self._update_effect_shortcut_labels()
        if audio_change:
            self._clear_preview_cache(event=event, announce_playing=True)
        self._update_dirty_label()

    def _note_workflow_change(
        self,
        *,
        audio_change: bool,
        event: str = "selection changed",
        clear_bypass_snapshot: bool = True,
        action_label: str | None = None,
    ) -> None:
        if self._suspend_dirty_tracking:
            return
        self._capture_workflow_undo_snapshot_if_needed(action_label)
        self._apply_dirty_state(
            audio_change=audio_change,
            event=event,
            clear_bypass_snapshot=clear_bypass_snapshot,
        )

    def _effective_effect_settings_from(self, effects: EffectSettings) -> EffectSettings:
        return EffectSettings(
            input_gain_db=effects.input_gain_db,
            filter_mode=effects.filter_mode if effects.filter_enabled else FilterMode.OFF,
            filter_enabled=effects.filter_enabled,
            reverb_amount=effects.reverb_amount if effects.reverb_enabled else 0.0,
            reverb_enabled=effects.reverb_enabled,
            lowpass_hz=effects.lowpass_hz,
            drive_amount=effects.drive_amount if effects.drive_enabled else 0.0,
            drive_enabled=effects.drive_enabled,
            chorus_amount=effects.chorus_amount if effects.chorus_enabled else 0.0,
            chorus_enabled=effects.chorus_enabled,
            texture_amount=effects.texture_amount if effects.texture_enabled else 0.0,
            texture_enabled=effects.texture_enabled,
            motion_amount=effects.motion_amount if effects.motion_enabled else 0.0,
            motion_enabled=effects.motion_enabled,
            pitch_drift_amount=effects.pitch_drift_amount if effects.pitch_drift_enabled else 0.0,
            pitch_drift_enabled=effects.pitch_drift_enabled,
            bloom_amount=effects.bloom_amount if effects.bloom_enabled else 0.0,
            bloom_enabled=effects.bloom_enabled,
            granular_amount=effects.granular_amount if effects.granular_enabled else 0.0,
            granular_enabled=effects.granular_enabled,
            delay_amount=effects.delay_amount if effects.delay_enabled else 0.0,
            delay_enabled=effects.delay_enabled,
            autopan_amount=effects.autopan_amount if effects.autopan_enabled else 0.0,
            autopan_enabled=effects.autopan_enabled,
            stereo_width=effects.stereo_width,
            reverse=effects.reverse,
            freeze_enabled=effects.freeze_enabled,
            shimmer_amount=effects.shimmer_amount if effects.shimmer_enabled else 0.0,
            shimmer_enabled=effects.shimmer_enabled,
            wet_dry=effects.wet_dry,
            limiter_enabled=effects.limiter_enabled,
        )

    def _preview_cache_key_from_snapshot(self, snapshot: WorkflowStateSnapshot) -> tuple:
        effects = self._effective_effect_settings_from(snapshot.effects)
        return (
            snapshot.input_path,
            snapshot.stretch_factor,
            snapshot.quality_profile.value,
            round(snapshot.waveform_region_start, 3),
            round(snapshot.waveform_region_end, 3),
            round(effects.input_gain_db, 3),
            effects.filter_mode.value,
            round(effects.reverb_amount, 3),
            round(effects.lowpass_hz, 1),
            round(effects.drive_amount, 3),
            round(effects.chorus_amount, 3),
            round(effects.texture_amount, 3),
            round(effects.motion_amount, 3),
            round(effects.pitch_drift_amount, 3),
            round(effects.bloom_amount, 3),
            round(effects.delay_amount, 3),
            round(effects.granular_amount, 3),
            round(effects.autopan_amount, 3),
            round(effects.stereo_width, 3),
            effects.reverse,
            effects.freeze_enabled,
            round(effects.shimmer_amount, 3),
            round(effects.wet_dry, 3),
            effects.limiter_enabled,
        )

    def _clear_deferred_compare_preview(self) -> None:
        self._pending_compare_preview_result = None
        self._pending_compare_preview_key = None
        self._pending_compare_render = False

    def _remember_recent_source(self, source_path: str) -> None:
        normalized = source_path.strip()
        if not normalized:
            return
        updated = [normalized]
        for existing in self.recent_source_paths:
            if existing != normalized and Path(existing).exists():
                updated.append(existing)
        self.recent_source_paths = updated[:8]
        self._refresh_recent_sources_list()

    def _refresh_recent_sources_list(self) -> None:
        if not hasattr(self, "recent_sources_list"):
            return
        self.recent_source_paths = [path for path in self.recent_source_paths if Path(path).exists()]
        self.recent_sources_list.blockSignals(True)
        self.recent_sources_list.clear()
        for source_path in self.recent_source_paths:
            item = QListWidgetItem(Path(source_path).name)
            item.setData(Qt.ItemDataRole.UserRole, source_path)
            item.setToolTip(source_path)
            self.recent_sources_list.addItem(item)
        if self.recent_sources_list.count() > 0:
            self.recent_sources_list.setCurrentRow(0)
        self.recent_sources_list.blockSignals(False)
        self._update_command_state()

    def _selected_recent_source_path(self) -> str:
        item = self.recent_sources_list.currentItem() if hasattr(self, "recent_sources_list") else None
        if item is None:
            return ""
        value = item.data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) else ""

    def _set_source_audio_fields(self, source_path: str, *, suggest_paths: bool = True) -> None:
        self.input_edit.setText(source_path)
        render_output_path, recording_output_path = self._output_paths_for_source(source_path)
        if suggest_paths and not self.output_edit.text().strip():
            self.output_edit.setText(render_output_path)
        if suggest_paths and not self.recording_output_edit.text().strip():
            self.recording_output_edit.setText(recording_output_path)

    def _load_source_audio_path(
        self,
        source_path: str,
        *,
        status_message: str,
        remember_recent: bool = True,
        create_undo_checkpoint: bool = False,
        invalidate_preview: bool = True,
        suggest_paths: bool = True,
    ) -> bool:
        normalized = source_path.strip()
        if not normalized:
            self._show_error("Choose an input audio file first.")
            return False
        if not Path(normalized).exists():
            self._show_error(f"Input audio file was not found:\n{normalized}")
            return False
        if create_undo_checkpoint:
            self._prepare_immediate_workflow_action("source load")
        previous_dirty_suspend = self._suspend_dirty_tracking
        previous_suspend = self._suspend_workflow_history_tracking
        self._suspend_dirty_tracking = True
        self._suspend_workflow_history_tracking = True
        try:
            self._set_source_audio_fields(normalized, suggest_paths=suggest_paths)
            if not self._load_waveform(normalized):
                return False
            if remember_recent:
                self._remember_recent_source(normalized)
            if invalidate_preview:
                self._apply_dirty_state(audio_change=True, clear_bypass_snapshot=False)
            else:
                self._update_dirty_label()
        finally:
            self._suspend_dirty_tracking = previous_dirty_suspend
            self._suspend_workflow_history_tracking = previous_suspend
        if create_undo_checkpoint:
            self._finish_immediate_workflow_action()
        self._persist_state()
        self._update_command_state()
        self.statusBar().showMessage(status_message)
        return True

    def _output_paths_for_source(self, source_path: str) -> tuple[str, str]:
        source = Path(source_path)
        return (
            str(source.with_name(f"{source.stem}_stretched.wav")),
            str(source.with_name(f"{source.stem}_take.wav")),
        )

    def _on_output_path_edited(self, _: str) -> None:
        self._note_workflow_change(
            audio_change=False,
            clear_bypass_snapshot=False,
            action_label="output path edit",
        )

    def _open_selected_recent_source(self) -> None:
        if not self._ensure_editable("Open a source file after the current job has finished."):
            return
        source_path = self._selected_recent_source_path()
        if not source_path:
            self._show_error("Select a recent source to open it.")
            return
        self._load_source_audio_path(
            source_path,
            status_message=f"Loaded recent source: {Path(source_path).name}",
            create_undo_checkpoint=True,
        )

    def _open_selected_recent_source_folder(self) -> None:
        source_path = self._selected_recent_source_path()
        if not source_path:
            self._show_error("Select a recent source to open its folder.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(source_path).parent)))

    def _forget_missing_recent_sources(self) -> None:
        before = len(self.recent_source_paths)
        self.recent_source_paths = [path for path in self.recent_source_paths if Path(path).exists()]
        self._refresh_recent_sources_list()
        removed = before - len(self.recent_source_paths)
        self._persist_state()
        self.statusBar().showMessage(
            "No missing recent sources to forget." if removed == 0 else f"Forgot {removed} missing source(s)."
        )

    def _clear_recent_sources(self) -> None:
        if not self.recent_source_paths:
            self.statusBar().showMessage("Recent sources list is already empty.")
            return
        removed = len(self.recent_source_paths)
        self.recent_source_paths.clear()
        self._refresh_recent_sources_list()
        self._persist_state()
        self.statusBar().showMessage(f"Cleared {removed} recent source(s).")

    def _current_compare_slot_state(self) -> CompareSlotState:
        region = self._current_region()
        return CompareSlotState(
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            preview_length=float(self.preview_duration.value()),
            effects=self._effect_settings(),
            region_start=region.start_seconds,
            region_end=region.end_seconds,
            preset_name=self.current_preset_name,
        )

    def _compare_slot_signature(self, slot: CompareSlotState | None) -> tuple | None:
        if slot is None:
            return None
        return (
            round(slot.stretch_factor, 3),
            slot.quality_profile.value,
            round(slot.preview_length, 3),
            round(slot.region_start, 3),
            round(slot.region_end, 3),
            slot.effects,
        )

    def _store_compare_slot(self, slot_name: str) -> None:
        self._prepare_immediate_workflow_action(f"store slot {slot_name}")
        self.compare_slots[slot_name] = self._current_compare_slot_state()
        self._finish_immediate_workflow_action()
        self._update_compare_slot_status()
        self._persist_state()
        self.statusBar().showMessage(f"Stored current workflow in slot {slot_name}.")

    def _current_compare_slot_label(self, slot_name: str) -> str:
        slot = self.compare_slots.get(slot_name)
        if slot is None:
            return f"{slot_name} empty"
        return f"{slot_name} {slot.preset_name or 'Custom'}"

    def _default_compare_store_slot_name(self) -> str:
        active_slot = self._active_compare_slot_name()
        return active_slot if active_slot is not None else "A"

    def _active_compare_slot_name(self) -> str | None:
        current = self._current_compare_slot_state()
        if current == self.compare_slots.get("A"):
            return "A"
        if current == self.compare_slots.get("B"):
            return "B"
        return None

    def _cached_preview_result_for_key(self, preview_key: tuple | None) -> PreviewResult | None:
        if preview_key is None:
            return None
        if self.current_preview is not None and self.current_preview_key == preview_key:
            return self.current_preview
        for entry in self.preview_history_entries:
            if entry.preview_key == preview_key:
                return entry.preview_result
        return None

    def _load_compare_slot(
        self,
        slot_name: str,
        *,
        create_undo_checkpoint: bool = True,
        auto_preview: bool = False,
    ) -> None:
        slot = self.compare_slots.get(slot_name)
        if slot is None:
            self._show_error(f"Slot {slot_name} is empty. Store something there first.")
            return
        previous_snapshot = self._current_workflow_snapshot()
        previous_preview = self.current_preview
        previous_preview_key = self.current_preview_key
        changed = self._compare_slot_signature(slot) != self._compare_slot_signature(self._current_compare_slot_state())
        if create_undo_checkpoint:
            self._prepare_immediate_workflow_action(f"load slot {slot_name}")
        self._suspend_dirty_tracking = True
        self.stretch_slider.setValue(int(round(slot.stretch_factor)))
        quality_index = self.quality_combo.findData(slot.quality_profile)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)
        self.preview_start.setValue(slot.region_start)
        self.preview_duration.setValue(max(0.05, slot.preview_length))
        self._apply_effect_settings_to_controls(slot.effects)
        self._suspend_dirty_tracking = False
        if slot.preset_name:
            self.current_preset_name = slot.preset_name
        self._refresh_presets(selected_name=self.current_preset_name)
        self._update_compare_slot_status()
        if create_undo_checkpoint:
            self._finish_immediate_workflow_action()
        if changed:
            self._mark_dirty(action_label=f"load slot {slot_name}")
            if not auto_preview:
                if self.preview_player.is_active():
                    self.statusBar().showMessage(
                        f"Loaded slot {slot_name}. Current playback will finish; next preview will use slot {slot_name}."
                    )
                else:
                    self.statusBar().showMessage(f"Loaded slot {slot_name}. Preview will re-render on next play.")
        else:
            self.statusBar().showMessage(f"Loaded slot {slot_name}. Audio state already matched.")
        if not auto_preview:
            return
        target_snapshot = self._current_workflow_snapshot()
        target_key = self._preview_cache_key_from_snapshot(target_snapshot)
        cached_preview = previous_preview if previous_preview_key == target_key else self._cached_preview_result_for_key(target_key)
        if self.preview_player.is_active():
            self._pending_compare_preview_result = cached_preview
            self._pending_compare_preview_key = target_key
            self._pending_compare_render = cached_preview is None
            self.statusBar().showMessage(
                f"Switched to slot {slot_name}. Current playback will finish, then "
                f"{'cached slot ' + slot_name + ' preview will replay.' if cached_preview is not None else 'slot ' + slot_name + ' preview will render.'}"
            )
            return
        if cached_preview is not None:
            self.current_preview = cached_preview
            self.current_preview_key = target_key
            self._play_preview_result(cached_preview, from_cache=True)
            self.statusBar().showMessage(f"Replaying cached slot {slot_name} preview.")
            return
        if previous_snapshot != target_snapshot:
            self._preview()
            self.statusBar().showMessage(f"Rendering slot {slot_name} preview.")

    def _update_compare_slot_status(self) -> None:
        active_slot = self._active_compare_slot_name()
        if active_slot == "A":
            state_label = "A active"
        elif active_slot == "B":
            state_label = "B active"
        else:
            state_label = "Custom mix"
        self.compare_status_label.setText(
            "A/B: " + " | ".join([state_label, self._current_compare_slot_label("A"), self._current_compare_slot_label("B")])
        )

    def _toggle_compare_slots(self) -> None:
        if self.compare_slots.get("A") is None or self.compare_slots.get("B") is None:
            self._show_error("Store both A and B before toggling between them.")
            return
        active_slot = self._active_compare_slot_name()
        target_slot = "B" if active_slot == "A" else "A"
        self._load_compare_slot(target_slot, create_undo_checkpoint=True, auto_preview=True)

    def _store_active_compare_slot(self) -> None:
        slot_name = self._default_compare_store_slot_name()
        self._store_compare_slot(slot_name)
        self.statusBar().showMessage(f"Stored current workflow in active slot {slot_name}.")

    def _swap_compare_slots(self) -> None:
        if self.compare_slots.get("A") is None and self.compare_slots.get("B") is None:
            self._show_error("Store something in A or B before swapping slots.")
            return
        self._prepare_immediate_workflow_action("swap slots")
        self.compare_slots["A"], self.compare_slots["B"] = self.compare_slots.get("B"), self.compare_slots.get("A")
        self._finish_immediate_workflow_action()
        self._update_compare_slot_status()
        self._persist_state()
        self.statusBar().showMessage("Swapped slot A and slot B.")

    def _current_project_session(self) -> ProjectSession:
        region = self._current_region()
        return ProjectSession(
            input_path=self.input_edit.text().strip(),
            output_path=self.output_edit.text().strip(),
            render_output_mode=self._selected_render_output_mode().value,
            preview_start=float(self.preview_start.value()),
            preview_length=float(self.preview_duration.value()),
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            effects=self._effect_settings(),
            selected_preset_name=self.current_preset_name,
            compare_slot_a=self.compare_slots.get("A"),
            compare_slot_b=self.compare_slots.get("B"),
            render_queue=tuple(self.render_queue_items),
            waveform_region_start=region.start_seconds,
            waveform_region_end=region.end_seconds,
            loop_enabled=self.loop_checkbox.isChecked(),
            loop_crossfade_ms=self._selected_loop_crossfade_ms(),
        )

    def _set_current_project_path(self, path: str) -> None:
        self.current_project_path = path.strip()
        self._update_project_path_label()

    def _update_project_path_label(self) -> None:
        if not hasattr(self, "project_path_label"):
            return
        if not self.current_project_path:
            self.project_path_label.setText("No project file loaded")
            self.setWindowTitle("FINDUS>x<STRETCHING")
            return
        project_path = Path(self.current_project_path)
        self.project_path_label.setText(str(project_path))
        self.setWindowTitle(f"FINDUS>x<STRETCHING - {project_path.name}")

    def _remember_recent_project(self, project_path: str) -> None:
        normalized = project_path.strip()
        if not normalized:
            return
        updated = [normalized]
        for existing in self.recent_project_paths:
            if existing != normalized and Path(existing).exists():
                updated.append(existing)
        self.recent_project_paths = updated[:8]
        self._refresh_recent_projects_list()

    def _refresh_recent_projects_list(self) -> None:
        if not hasattr(self, "recent_projects_list"):
            return
        self.recent_project_paths = [path for path in self.recent_project_paths if Path(path).exists()]
        self.recent_projects_list.blockSignals(True)
        self.recent_projects_list.clear()
        for project_path in self.recent_project_paths:
            item = QListWidgetItem(Path(project_path).name)
            item.setData(Qt.ItemDataRole.UserRole, project_path)
            item.setToolTip(project_path)
            self.recent_projects_list.addItem(item)
        if self.recent_projects_list.count() > 0:
            self.recent_projects_list.setCurrentRow(0)
        self.recent_projects_list.blockSignals(False)
        self._update_command_state()

    def _selected_recent_project_path(self) -> str:
        item = self.recent_projects_list.currentItem() if hasattr(self, "recent_projects_list") else None
        if item is None:
            return ""
        value = item.data(Qt.ItemDataRole.UserRole)
        return value if isinstance(value, str) else ""

    def _forget_missing_recent_projects(self) -> None:
        before = len(self.recent_project_paths)
        self.recent_project_paths = [path for path in self.recent_project_paths if Path(path).exists()]
        self._refresh_recent_projects_list()
        removed = before - len(self.recent_project_paths)
        self._persist_state()
        self.statusBar().showMessage(
            "No missing recent projects to forget." if removed == 0 else f"Forgot {removed} missing project(s)."
        )

    def _browse_project(self) -> None:
        if not self._ensure_editable("Open a project after the current job has finished."):
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open project",
            self.current_project_path or "",
            "FINDUS Project (*.findusstretch.json);;JSON Files (*.json);;All Files (*.*)",
        )
        if file_path:
            self._load_project_from_path(file_path)

    def _open_selected_recent_project(self) -> None:
        if not self._ensure_editable("Open a project after the current job has finished."):
            return
        project_path = self._selected_recent_project_path()
        if not project_path:
            self._show_error("Select a recent project to open it.")
            return
        self._load_project_from_path(project_path)

    def _save_project(self) -> None:
        if not self._ensure_editable("Save the project after the current job has finished."):
            return
        if not self.current_project_path:
            self._save_project_as()
            return
        self._save_project_to_path(self.current_project_path)

    def _save_project_as(self) -> None:
        if not self._ensure_editable("Save the project after the current job has finished."):
            return
        suggested_name = self.current_project_path or self._default_project_path()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save project",
            suggested_name,
            "FINDUS Project (*.findusstretch.json);;JSON Files (*.json)",
        )
        if not file_path:
            return
        self._save_project_to_path(_ensure_project_suffix(file_path))

    def _save_project_to_path(self, project_path: str) -> None:
        try:
            self.preset_library.save_project(self._current_project_session(), Path(project_path))
        except Exception as exc:
            self._show_error(str(exc))
            return
        self._set_current_project_path(project_path)
        self._remember_recent_project(project_path)
        self._persist_state()
        self.statusBar().showMessage(f"Saved project: {Path(project_path).name}")

    def _load_project_from_path(self, project_path: str) -> None:
        try:
            project = self.preset_library.load_project(Path(project_path))
        except Exception as exc:
            self._show_error(str(exc))
            return
        self._prepare_immediate_workflow_action("project load")
        self._apply_project_session(project, project_path, reset_workflow_history=False)
        self._finish_immediate_workflow_action()

    def _apply_project_session(
        self,
        project: ProjectSession,
        project_path: str,
        *,
        reset_workflow_history: bool = True,
    ) -> None:
        self._clear_deferred_compare_preview()
        self._suspend_workflow_history_tracking = True
        self._suspend_dirty_tracking = True
        self.input_edit.setText(project.input_path)
        self.output_edit.setText(project.output_path)
        render_mode_index = self.render_output_mode_combo.findData(render_output_mode_from_value(project.render_output_mode))
        if render_mode_index >= 0:
            self.render_output_mode_combo.setCurrentIndex(render_mode_index)
        self.preview_start.setValue(project.preview_start)
        self.preview_duration.setValue(project.preview_length)
        self.stretch_slider.setValue(int(round(project.stretch_factor)))
        quality_index = self.quality_combo.findData(project.quality_profile)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)
        self.loop_checkbox.setChecked(project.loop_enabled)
        self.loop_crossfade_spin.blockSignals(True)
        self.loop_crossfade_spin.setValue(float(project.loop_crossfade_ms))
        self.loop_crossfade_spin.blockSignals(False)
        self._apply_effect_settings_to_controls(project.effects)
        self.compare_slots = {"A": project.compare_slot_a, "B": project.compare_slot_b}
        self.render_queue_items = list(project.render_queue)
        self.current_preset_name = project.selected_preset_name or "Custom"
        self._refresh_presets(selected_name=self.current_preset_name)
        self._suspend_dirty_tracking = False
        self._suspend_workflow_history_tracking = False
        self._update_compare_slot_status()
        self._refresh_render_queue_list()
        self.effects_bypass_snapshot = None
        self._update_effect_shortcut_labels()
        self.current_preview = None
        self.current_preview_key = None
        if project.input_path and Path(project.input_path).exists():
            if self._load_waveform(project.input_path):
                self._apply_region_to_waveform(
                    RegionSelection(project.waveform_region_start, project.waveform_region_end)
                )
                self.statusBar().showMessage(f"Loaded project: {Path(project_path).name}")
        elif project.input_path:
            self._clear_loaded_input("Project source file is missing")
            self._show_warning(
                "Project source missing",
                f"The project loaded, but the source file was not found:\n{project.input_path}",
            )
        else:
            self._clear_loaded_input("Project loaded without a source file")
        self._set_current_project_path(project_path)
        self._remember_recent_project(project_path)
        self._update_dirty_label()
        if reset_workflow_history:
            self._reset_workflow_history()
        self._update_command_state()
        self._persist_state()

    def _default_project_path(self) -> str:
        if self.input_edit.text().strip():
            source_path = Path(self.input_edit.text().strip())
            return str(source_path.with_suffix(".findusstretch.json"))
        if self.output_edit.text().strip():
            output_path = Path(self.output_edit.text().strip())
            return str(output_path.with_name(f"{output_path.stem}.findusstretch.json"))
        return str((Path(__file__).resolve().parent.parent / "findus_project.findusstretch.json"))

    def _preview_history_signature(self) -> tuple:
        slot = self._current_compare_slot_state()
        return (
            self.input_edit.text().strip(),
            self._compare_slot_signature(slot),
            self._preview_cache_key(),
        )

    def _remember_preview_history(self, result: PreviewResult) -> None:
        if not hasattr(self, "preview_history_list"):
            return
        snapshot = self._current_compare_slot_state()
        region = RegionSelection(snapshot.region_start, snapshot.region_end)
        label = (
            f"{snapshot.preset_name or 'Custom'} | "
            f"{Path(self.input_edit.text().strip()).name or 'No source'} | "
            f"{region.start_seconds:.2f}-{region.end_seconds:.2f}s"
        )
        entry = PreviewHistoryEntry(
            input_path=self.input_edit.text().strip(),
            snapshot=snapshot,
            preview_result=result,
            preview_key=self._preview_cache_key(),
            label=label,
        )
        signature = (
            entry.input_path,
            self._compare_slot_signature(entry.snapshot),
            entry.preview_key,
        )
        if self.preview_history_entries:
            current = self.preview_history_entries[0]
            current_signature = (
                current.input_path,
                self._compare_slot_signature(current.snapshot),
                current.preview_key,
            )
            if signature == current_signature:
                self.preview_history_entries[0] = entry
                self._refresh_preview_history_list(selected_index=0)
                return
        self.preview_history_entries.insert(0, entry)
        self.preview_history_entries = self.preview_history_entries[:8]
        self._refresh_preview_history_list(selected_index=0)

    def _refresh_preview_history_list(self, selected_index: int = 0) -> None:
        if not hasattr(self, "preview_history_list"):
            return
        self.preview_history_list.blockSignals(True)
        self.preview_history_list.clear()
        for entry in self.preview_history_entries:
            item = QListWidgetItem(entry.label)
            item.setToolTip(entry.input_path or "No source")
            self.preview_history_list.addItem(item)
        if self.preview_history_list.count() > 0:
            self.preview_history_list.setCurrentRow(max(0, min(selected_index, self.preview_history_list.count() - 1)))
            self.preview_history_status_label.setText(
                f"{len(self.preview_history_entries)} preview state(s) saved for this session."
            )
        else:
            self.preview_history_status_label.setText("Preview history is empty")
        self.preview_history_list.blockSignals(False)
        self._update_command_state()

    def _selected_preview_history_entry(self) -> PreviewHistoryEntry | None:
        if not hasattr(self, "preview_history_list"):
            return None
        row = self.preview_history_list.currentRow()
        if row < 0 or row >= len(self.preview_history_entries):
            return None
        return self.preview_history_entries[row]

    def _load_selected_preview_history(self, replay: bool = False) -> None:
        entry = self._selected_preview_history_entry()
        if entry is None:
            self._show_error("Select a preview history entry first.")
            return
        if entry.input_path and not Path(entry.input_path).exists():
            self._show_error(f"Preview history source file was not found:\n{entry.input_path}")
            return
        previous_input_path = self.input_edit.text().strip()
        self._prepare_immediate_workflow_action("preview history load")
        self._suspend_dirty_tracking = True
        if entry.input_path:
            if self.waveform_overview is None or previous_input_path != entry.input_path:
                self._load_source_audio_path(
                    entry.input_path,
                    status_message=f"Loaded preview history source: {Path(entry.input_path).name}",
                    remember_recent=True,
                    create_undo_checkpoint=False,
                    invalidate_preview=False,
                    suggest_paths=False,
                )
            else:
                self.input_edit.setText(entry.input_path)
        self.stretch_slider.setValue(int(round(entry.snapshot.stretch_factor)))
        quality_index = self.quality_combo.findData(entry.snapshot.quality_profile)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)
        self.preview_start.setValue(entry.snapshot.region_start)
        self.preview_duration.setValue(entry.snapshot.preview_length)
        self._apply_effect_settings_to_controls(entry.snapshot.effects)
        self._suspend_dirty_tracking = False
        self.current_preset_name = entry.snapshot.preset_name or "Custom"
        self._refresh_presets(selected_name=self.current_preset_name)
        self._apply_region_to_waveform(RegionSelection(entry.snapshot.region_start, entry.snapshot.region_end))
        self.current_preview = entry.preview_result
        self.current_preview_key = entry.preview_key
        if replay:
            self._play_preview_result(entry.preview_result, from_cache=True)
        else:
            self._set_preview_state("ready", result=entry.preview_result)
            self.statusBar().showMessage(f"Loaded preview history: {entry.label}")
        self._finish_immediate_workflow_action()
        self._update_dirty_label()
        self._update_command_state()

    def _clear_preview_history_entries(self) -> None:
        self.preview_history_entries.clear()
        self._refresh_preview_history_list()
        self.statusBar().showMessage("Preview history cleared.")

    def _selected_render_output_mode(self) -> RenderOutputMode:
        value = self.render_output_mode_combo.currentData() if hasattr(self, "render_output_mode_combo") else None
        return render_output_mode_from_value(value)

    def _on_render_output_mode_changed(self, index: int) -> None:
        del index
        self._note_workflow_change(
            audio_change=False,
            clear_bypass_snapshot=False,
            action_label="export mode change",
        )
        mode_text = self.render_output_mode_combo.currentText().lower() if hasattr(self, "render_output_mode_combo") else "wet only"
        self.statusBar().showMessage(f"Export mode set to {mode_text}.")
        if hasattr(self, "render_queue_status_label"):
            self._update_render_queue_status()

    def _current_render_job(self, *, preset: AppPreset | None = None, output_path: str | None = None) -> QueuedRenderJob:
        region = self._current_region()
        target_output_path = output_path or self.output_edit.text().strip()
        if target_output_path:
            target_output_path = _ensure_wav_suffix(target_output_path)
        if preset is None:
            return QueuedRenderJob(
                input_path=self.input_edit.text().strip(),
                output_path=target_output_path,
                stretch_factor=float(self.stretch_slider.value()),
                quality_profile=self._selected_profile(),
                effects=self._effective_effect_settings(),
                region_start=region.start_seconds,
                region_end=region.end_seconds,
                preset_name=self.current_preset_name,
                output_mode=self._selected_render_output_mode().value,
            )
        return QueuedRenderJob(
            input_path=self.input_edit.text().strip(),
            output_path=target_output_path,
            stretch_factor=preset.stretch_factor,
            quality_profile=preset.quality_profile,
            effects=preset.effects,
            region_start=region.start_seconds,
            region_end=region.end_seconds,
            preset_name=preset.name,
            output_mode=self._selected_render_output_mode().value,
        )

    def _render_config_for_job(self, job: QueuedRenderJob) -> RenderConfig:
        return RenderConfig(
            input_path=job.input_path,
            output_path=job.output_path,
            output_mode=render_output_mode_from_value(job.output_mode),
            stretch_factor=job.stretch_factor,
            quality_profile=job.quality_profile,
            effects=job.effects,
            region=RegionSelection(job.region_start, job.region_end),
        )

    def _render_queue_label(self, job: QueuedRenderJob) -> str:
        mode = render_output_mode_from_value(job.output_mode)
        mode_label = {
            RenderOutputMode.WET: "Wet",
            RenderOutputMode.DRY: "Dry",
            RenderOutputMode.DRY_WET: "Dry+Wet",
        }[mode]
        return f"{job.preset_name} | {Path(job.output_path).name} | {mode_label}"

    def _selected_queue_index(self) -> int:
        if not hasattr(self, "render_queue_list"):
            return -1
        row = self.render_queue_list.currentRow()
        return row if row >= 0 else -1

    def _refresh_render_queue_list(self, selected_index: int | None = None) -> None:
        if not hasattr(self, "render_queue_list"):
            return
        current_index = self._selected_queue_index() if selected_index is None else selected_index
        self.render_queue_list.blockSignals(True)
        self.render_queue_list.clear()
        for job in self.render_queue_items:
            item = QListWidgetItem(self._render_queue_label(job))
            item.setData(Qt.ItemDataRole.UserRole, job.output_path)
            self.render_queue_list.addItem(item)
        if self.render_queue_list.count() > 0:
            clamped_index = max(0, min(current_index, self.render_queue_list.count() - 1))
            self.render_queue_list.setCurrentRow(clamped_index)
        self.render_queue_list.blockSignals(False)
        self._update_render_queue_status()

    def _update_render_queue_status(self) -> None:
        if not hasattr(self, "render_queue_status_label"):
            return
        queued_count = len(self.render_queue_items)
        if self.render_queue_running and self.active_render_job is not None:
            self.render_queue_status_label.setText(
                f"Queue running. Rendering {self.active_render_job.preset_name} with {queued_count} job(s) remaining."
            )
            return
        if queued_count == 0:
            self.render_queue_status_label.setText("Queue empty")
            return
        next_job = self.render_queue_items[0]
        self.render_queue_status_label.setText(
            f"{queued_count} job(s) queued. Next: {next_job.preset_name} -> {Path(next_job.output_path).name}"
        )

    def _append_render_jobs(self, jobs: list[QueuedRenderJob], *, message: str) -> None:
        self.render_queue_items.extend(jobs)
        self._refresh_render_queue_list(selected_index=len(self.render_queue_items) - 1)
        self._persist_state()
        self.statusBar().showMessage(message)

    def _queue_current_render(self) -> None:
        if not self._ensure_editable("Queue the render after the current job has finished."):
            return
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()
        if not input_path or not output_path:
            self._show_error("Choose both an input file and an output WAV path before queueing.")
            return
        if not Path(input_path).exists():
            self._show_error(f"Input audio file was not found:\n{input_path}")
            return
        self._append_render_jobs(
            [self._current_render_job()],
            message=f"Queued current render: {Path(output_path).name}",
        )

    def _remove_selected_queue_job(self) -> None:
        if not self._ensure_editable("Edit the render queue after the current job has finished."):
            return
        index = self._selected_queue_index()
        if index < 0 or index >= len(self.render_queue_items):
            self._show_error("Select a queued render job to remove it.")
            return
        removed = self.render_queue_items.pop(index)
        self._refresh_render_queue_list(selected_index=index - 1)
        self._persist_state()
        self.statusBar().showMessage(f"Removed queued render: {removed.preset_name}")

    def _clear_render_queue(self) -> None:
        if not self._ensure_editable("Clear the render queue after the current job has finished."):
            return
        if not self.render_queue_items:
            self.statusBar().showMessage("Render queue already empty.")
            return
        removed_count = len(self.render_queue_items)
        self.render_queue_items.clear()
        self._refresh_render_queue_list()
        self._persist_state()
        self.statusBar().showMessage(f"Cleared {removed_count} queued render job(s).")

    def _start_render_queue(self) -> None:
        if not self.render_queue_items:
            self._show_error("Queue at least one render job before starting the render queue.")
            return
        if not self._ensure_idle("Wait for the current render or recording job to finish first."):
            return
        self.preview_player.stop()
        self.playback_timer.stop()
        self.current_playback_duration_seconds = 0.0
        self.waveform_widget.set_playhead(None)
        self.render_queue_running = True
        self.render_queue_results = []
        self.statusBar().showMessage("Render queue started.")
        self._start_next_render_job()

    def _start_next_render_job(self) -> None:
        if not self.render_queue_running:
            self._refresh_render_queue_list()
            self._update_command_state()
            return
        if not self.render_queue_items:
            self._finish_render_queue()
            return
        self.active_render_job = self.render_queue_items.pop(0)
        self._refresh_render_queue_list()
        self.progress_bar.setValue(0)
        self.render_worker = RenderWorker(self._render_config_for_job(self.active_render_job))
        self.render_worker.status_changed.connect(self._on_job_status)
        self.render_worker.render_completed.connect(self._on_render_complete)
        self.render_worker.render_failed.connect(self._on_job_failed)
        self.render_worker.finished.connect(self._on_render_finished)
        self.render_worker.start()
        self._update_command_state()

    def _finish_render_queue(self) -> None:
        completed_results = list(self.render_queue_results)
        output_paths = [path for result in completed_results for path in result.output_paths]
        completed_jobs = len(completed_results)
        self.render_queue_running = False
        self.render_queue_results = []
        self.active_render_job = None
        self._refresh_render_queue_list()
        self._persist_state()
        self._update_command_state()
        if completed_jobs == 0:
            self.statusBar().showMessage("Render queue finished with no completed jobs.")
            return
        preview_lines = "\n".join(output_paths[:6])
        if len(output_paths) > 6:
            preview_lines += "\n..."
        QMessageBox.information(
            self,
            "Render queue complete",
            (
                f"Finished {completed_jobs} queue job(s).\n\n"
                f"Created {len(output_paths)} file(s):\n{preview_lines}"
            ),
        )
        self.statusBar().showMessage(f"Render queue complete: {completed_jobs} job(s)")

    def _selected_batch_preset_names(self) -> tuple[str, ...]:
        if not hasattr(self, "batch_preset_list"):
            return ()
        names: list[str] = []
        for item in self.batch_preset_list.selectedItems():
            name = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(name, str) and name not in names:
                names.append(name)
        return tuple(names)

    def _refresh_batch_preset_list(
        self,
        presets: list[AppPreset],
        *,
        selected_names: tuple[str, ...] | None = None,
    ) -> None:
        if not hasattr(self, "batch_preset_list"):
            return
        chosen_names = set(selected_names if selected_names is not None else self._selected_batch_preset_names())
        self.batch_preset_list.blockSignals(True)
        self.batch_preset_list.clear()
        for preset in presets:
            item = QListWidgetItem(self._display_preset_label(preset))
            item.setData(Qt.ItemDataRole.UserRole, preset.name)
            self.batch_preset_list.addItem(item)
            if preset.name in chosen_names:
                item.setSelected(True)
        self.batch_preset_list.blockSignals(False)

    def _select_all_filtered_batch_presets(self) -> None:
        for index in range(self.batch_preset_list.count()):
            self.batch_preset_list.item(index).setSelected(True)
        self.statusBar().showMessage(f"Selected {self.batch_preset_list.count()} filtered preset(s) for batch render.")

    def _queue_selected_preset_batch(self) -> None:
        if not self._ensure_editable("Queue the preset batch after the current job has finished."):
            return
        input_path = self.input_edit.text().strip()
        output_path = self.output_edit.text().strip()
        if not input_path or not output_path:
            self._show_error("Choose both an input file and an output WAV path before queueing a preset batch.")
            return
        if not Path(input_path).exists():
            self._show_error(f"Input audio file was not found:\n{input_path}")
            return
        selected_presets: list[AppPreset] = []
        for preset_name in self._selected_batch_preset_names():
            preset = self.preset_library.get_preset(preset_name)
            if preset is not None:
                selected_presets.append(preset)
        if not selected_presets:
            self._show_error("Select one or more presets in the batch list first.")
            return
        jobs = [
            self._current_render_job(
                preset=preset,
                output_path=self._batch_output_path(output_path, preset.name),
            )
            for preset in selected_presets
        ]
        self._append_render_jobs(
            jobs,
            message=f"Queued {len(jobs)} preset render job(s) from the filtered batch list.",
        )

    def _batch_output_path(self, output_path: str, preset_name: str) -> str:
        base_path = Path(_ensure_wav_suffix(output_path))
        suffix = _safe_name_token(preset_name)
        return str(base_path.with_name(f"{base_path.stem}_{suffix}{base_path.suffix}"))

    def _favorite_factory_names_tuple(self) -> tuple[str, ...]:
        return tuple(sorted(self.favorite_factory_preset_names))

    def _preset_auto_tags(self, preset: AppPreset) -> tuple[str, ...]:
        tags: list[str] = []
        effects = preset.effects
        if effects.filter_mode == FilterMode.LOWPASS and (effects.reverb_amount >= 0.3 or effects.wet_dry >= 0.7):
            tags.append("dark")
        if effects.chorus_amount >= 0.3 or effects.shimmer_amount >= 0.35:
            tags.append("choir")
        if effects.stereo_width >= 1.4 or effects.bloom_amount >= 0.4 or effects.reverb_amount >= 0.55:
            tags.append("huge")
        if effects.drive_amount >= 0.25 and effects.filter_mode == FilterMode.LOWPASS:
            tags.append("tape")
        if effects.granular_amount >= 0.2 or effects.texture_amount >= 0.35 or effects.pitch_drift_amount >= 0.18:
            tags.append("weird")
        if effects.reverb_amount >= 0.25 or effects.bloom_amount >= 0.2 or effects.texture_amount >= 0.15:
            tags.append("ambient")
        return tuple(tags)

    def _preset_tags(self, preset: AppPreset) -> tuple[str, ...]:
        tags: list[str] = []
        for tag in list(self._preset_auto_tags(preset)) + list(preset.tags):
            if tag not in tags:
                tags.append(tag)
        return tuple(tags)

    def _is_preset_favorite(self, preset: AppPreset) -> bool:
        if preset.factory:
            return preset.name in self.favorite_factory_preset_names
        return preset.favorite

    def _display_preset_label(self, preset: AppPreset) -> str:
        favorite_prefix = "★ " if self._is_preset_favorite(preset) else ""
        source_prefix = "[Factory]" if preset.factory else "[User]"
        tags = self._preset_tags(preset)
        tag_suffix = f"  ({', '.join(tags[:3])})" if tags else ""
        return f"{favorite_prefix}{source_prefix} {preset.name}{tag_suffix}"

    def _filtered_presets(self) -> list[AppPreset]:
        presets = self.preset_library.list_presets()
        search_text = self.preset_search_edit.text().strip().lower() if hasattr(self, "preset_search_edit") else ""
        selected_tag = self.preset_tag_filter_combo.currentData() if hasattr(self, "preset_tag_filter_combo") else ""
        favorites_only = self.preset_favorites_only_checkbox.isChecked() if hasattr(self, "preset_favorites_only_checkbox") else False
        filtered: list[AppPreset] = []
        for preset in presets:
            tags = self._preset_tags(preset)
            haystack = " ".join([preset.name.lower(), " ".join(tags)])
            if search_text and search_text not in haystack:
                continue
            if selected_tag and selected_tag not in tags:
                continue
            if favorites_only and not self._is_preset_favorite(preset):
                continue
            filtered.append(preset)
        return filtered

    def _refresh_preset_tag_filter(self) -> None:
        if not hasattr(self, "preset_tag_filter_combo"):
            return
        current_tag = self.preset_tag_filter_combo.currentData()
        tags = sorted({tag for preset in self.preset_library.list_presets() for tag in self._preset_tags(preset)})
        self.preset_tag_filter_combo.blockSignals(True)
        self.preset_tag_filter_combo.clear()
        self.preset_tag_filter_combo.addItem("All tags", "")
        for tag in tags:
            self.preset_tag_filter_combo.addItem(tag.title(), tag)
        index = self.preset_tag_filter_combo.findData(current_tag)
        self.preset_tag_filter_combo.setCurrentIndex(index if index >= 0 else 0)
        self.preset_tag_filter_combo.blockSignals(False)

    def _selected_preset_for_management(self) -> AppPreset | None:
        preset = self.preset_combo.currentData()
        if isinstance(preset, AppPreset):
            return preset
        return self.preset_library.get_preset(self.current_preset_name)

    def _on_preset_filter_changed(self, *_args) -> None:
        self._refresh_presets(selected_name=self.current_preset_name)

    def _update_preset_metadata_controls(self) -> None:
        if not hasattr(self, "toggle_favorite_preset_button"):
            return
        preset = self._selected_preset_for_management()
        has_selection = preset is not None
        is_user = preset is not None and not preset.factory
        self.toggle_favorite_preset_button.setEnabled(has_selection and not self._is_processing())
        self.apply_preset_tags_button.setEnabled(is_user and not self._is_processing())
        self.preset_tags_edit.setEnabled(is_user and not self._is_processing())
        if preset is None:
            self.toggle_favorite_preset_button.setText("Favorite")
            self.preset_tags_edit.clear()
            return
        self.toggle_favorite_preset_button.setText("Unfavorite" if self._is_preset_favorite(preset) else "Favorite")
        self.preset_tags_edit.setText(", ".join(preset.tags))

    def _toggle_selected_preset_favorite(self) -> None:
        preset = self._selected_preset_for_management()
        if preset is None:
            self._show_error("Select a preset to favorite it.")
            return
        if preset.factory:
            if preset.name in self.favorite_factory_preset_names:
                self.favorite_factory_preset_names.remove(preset.name)
                message = f"Removed favorite: {preset.name}"
            else:
                self.favorite_factory_preset_names.add(preset.name)
                message = f"Favorited preset: {preset.name}"
            self._refresh_presets(selected_name=preset.name)
            self._persist_state()
            self.statusBar().showMessage(message)
            return
        updated = AppPreset(
            name=preset.name,
            stretch_factor=preset.stretch_factor,
            quality_profile=preset.quality_profile,
            preview_length=preset.preview_length,
            effects=preset.effects,
            factory=False,
            tags=preset.tags,
            favorite=not preset.favorite,
        )
        self.preset_library.save_user_preset(updated)
        self._refresh_presets(selected_name=updated.name)
        self.statusBar().showMessage(
            f"{'Favorited' if updated.favorite else 'Unfavorited'} preset: {updated.name}"
        )

    def _apply_selected_preset_tags(self) -> None:
        preset = self._selected_preset_for_management()
        if preset is None or preset.factory:
            self._show_error("Select a user preset to edit its tags.")
            return
        raw_tags = [part.strip().lower() for part in self.preset_tags_edit.text().split(",")]
        tags: list[str] = []
        for tag in raw_tags:
            if tag and tag not in tags:
                tags.append(tag)
        updated = AppPreset(
            name=preset.name,
            stretch_factor=preset.stretch_factor,
            quality_profile=preset.quality_profile,
            preview_length=preset.preview_length,
            effects=preset.effects,
            factory=False,
            tags=tuple(tags),
            favorite=preset.favorite,
        )
        self.preset_library.save_user_preset(updated)
        self._refresh_preset_tag_filter()
        self._refresh_presets(selected_name=updated.name)
        self.statusBar().showMessage(f"Updated tags for preset: {updated.name}")

    def _on_preset_selected(self, index: int) -> None:
        del index
        preset = self.preset_combo.currentData()
        if not isinstance(preset, AppPreset):
            self._update_preset_metadata_controls()
            return
        previous_signature = self._compare_slot_signature(self._current_compare_slot_state())
        self._prepare_immediate_workflow_action("preset load")
        self.current_preset_name = preset.name
        self._apply_preset(preset)
        self._finish_immediate_workflow_action()
        if previous_signature != self._compare_slot_signature(self._current_compare_slot_state()):
            self._mark_dirty(action_label="preset load")
        self._update_preset_buttons()
        self._update_dirty_label()
        self._update_preset_metadata_controls()

    def _apply_preset(self, preset: AppPreset) -> None:
        self._suspend_dirty_tracking = True
        self.effects_bypass_snapshot = None
        self._update_effect_shortcut_labels()
        self.stretch_slider.setValue(int(round(preset.stretch_factor)))
        self.preview_duration.setValue(preset.preview_length)
        quality_index = self.quality_combo.findData(preset.quality_profile)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)
        self._apply_effect_settings_to_controls(preset.effects)
        self._suspend_dirty_tracking = False

    def _effect_enabled_controls(self) -> dict[str, QCheckBox]:
        return {
            "filter_enabled": self.filter_enabled_checkbox,
            "reverb_enabled": self.reverb_enabled_checkbox,
            "drive_enabled": self.drive_enabled_checkbox,
            "chorus_enabled": self.chorus_enabled_checkbox,
            "texture_enabled": self.texture_enabled_checkbox,
            "motion_enabled": self.motion_enabled_checkbox,
            "pitch_drift_enabled": self.pitch_drift_enabled_checkbox,
            "bloom_enabled": self.bloom_enabled_checkbox,
            "granular_enabled": self.granular_enabled_checkbox,
            "delay_enabled": self.delay_enabled_checkbox,
            "autopan_enabled": self.autopan_enabled_checkbox,
            "shimmer_enabled": self.shimmer_enabled_checkbox,
        }

    def _apply_effect_settings_to_controls(self, effects: EffectSettings) -> None:
        self.input_trim_slider.setValue(int(round(effects.input_gain_db)))
        filter_mode_index = self.filter_mode_combo.findData(effects.filter_mode)
        if filter_mode_index >= 0:
            self.filter_mode_combo.setCurrentIndex(filter_mode_index)
        self.reverb_slider.setValue(int(round(effects.reverb_amount * 100)))
        self.lowpass_slider.setValue(int(round(effects.lowpass_hz)))
        self.drive_slider.setValue(int(round(effects.drive_amount * 100)))
        self.chorus_slider.setValue(int(round(effects.chorus_amount * 100)))
        self.texture_slider.setValue(int(round(effects.texture_amount * 100)))
        self.motion_slider.setValue(int(round(effects.motion_amount * 100)))
        self.pitch_drift_slider.setValue(int(round(effects.pitch_drift_amount * 100)))
        self.bloom_slider.setValue(int(round(effects.bloom_amount * 100)))
        self.shimmer_slider.setValue(int(round(effects.shimmer_amount * 100)))
        self.granular_slider.setValue(int(round(effects.granular_amount * 100)))
        self.delay_slider.setValue(int(round(effects.delay_amount * 100)))
        self.autopan_slider.setValue(int(round(effects.autopan_amount * 100)))
        self.width_slider.setValue(int(round(effects.stereo_width * 100)))
        self.reverse_checkbox.setChecked(effects.reverse)
        self.freeze_checkbox.setChecked(effects.freeze_enabled)
        self.wetdry_slider.setValue(int(round(effects.wet_dry * 100)))
        self.limiter_checkbox.setChecked(effects.limiter_enabled)
        for field_name, checkbox in self._effect_enabled_controls().items():
            checkbox.setChecked(bool(getattr(effects, field_name)))

    def _neutral_effect_settings(self) -> EffectSettings:
        return EffectSettings()

    def _bypassed_effect_settings(self) -> EffectSettings:
        return EffectSettings(
            filter_enabled=False,
            reverb_enabled=False,
            drive_enabled=False,
            chorus_enabled=False,
            texture_enabled=False,
            motion_enabled=False,
            pitch_drift_enabled=False,
            bloom_enabled=False,
            granular_enabled=False,
            delay_enabled=False,
            autopan_enabled=False,
            shimmer_enabled=False,
        )

    def _update_effect_shortcut_labels(self) -> None:
        bypassed = self.effects_bypass_snapshot is not None
        if hasattr(self, "bypass_effects_button"):
            self.bypass_effects_button.setText("Restore Effects" if bypassed else "Bypass All Effects")
        if hasattr(self, "reset_effects_button"):
            self.reset_effects_button.setText("Reset Effects")

    def _apply_effect_shortcut(
        self,
        effects: EffectSettings,
        *,
        status_message: str,
        action_label: str,
    ) -> None:
        self._prepare_immediate_workflow_action(action_label)
        self._suspend_dirty_tracking = True
        self._apply_effect_settings_to_controls(effects)
        self._suspend_dirty_tracking = False
        self._finish_immediate_workflow_action()
        self._mark_dirty(
            event="selection changed",
            clear_bypass_snapshot=False,
            action_label=action_label,
        )
        self._update_effect_shortcut_labels()
        self.statusBar().showMessage(status_message)

    def _toggle_effects_bypass(self) -> None:
        if self.effects_bypass_snapshot is None:
            self.effects_bypass_snapshot = self._effect_settings()
            self._apply_effect_shortcut(
                self._bypassed_effect_settings(),
                status_message="Effects bypassed. Current playback will finish; next preview will use the dry signal.",
                action_label="bypass effects",
            )
            return
        restored = self.effects_bypass_snapshot
        self.effects_bypass_snapshot = None
        self._apply_effect_shortcut(
            restored,
            status_message="Effects restored. Cached preview was invalidated.",
            action_label="restore effects",
        )

    def _reset_effects(self) -> None:
        self.effects_bypass_snapshot = None
        self._apply_effect_shortcut(
            self._neutral_effect_settings(),
            status_message="Effects reset to neutral.",
            action_label="reset effects",
        )

    def _randomize_effects(self, profile: str = "random") -> None:
        rng = np.random.default_rng()
        randomized = self._random_effect_settings(rng, profile)
        self.effects_bypass_snapshot = None
        self._apply_effect_shortcut(
            randomized,
            status_message=f"Applied {profile.title()} starting point. Cached preview was invalidated.",
            action_label=f"effects randomize ({profile})",
        )

    def _apply_harmonize_effects(self) -> None:
        harmonized = EffectSettings(
            filter_mode=FilterMode.HIGHPASS,
            reverb_amount=0.44,
            lowpass_hz=2200.0,
            drive_amount=0.0,
            chorus_amount=0.46,
            texture_amount=0.08,
            motion_amount=0.22,
            pitch_drift_amount=0.12,
            bloom_amount=0.42,
            granular_amount=0.0,
            delay_amount=0.18,
            autopan_amount=0.12,
            stereo_width=1.55,
            reverse=False,
            freeze_enabled=False,
            shimmer_amount=0.48,
            wet_dry=0.78,
        )
        self.effects_bypass_snapshot = None
        self._apply_effect_shortcut(
            harmonized,
            status_message="Applied harmonize effect stack.",
            action_label="effects harmonize",
        )

    def _random_effect_settings(self, rng: np.random.Generator, profile: str) -> EffectSettings:
        if profile == "dark":
            return EffectSettings(
                filter_mode=rng.choice([FilterMode.LOWPASS, FilterMode.BANDPASS]),
                lowpass_hz=float(rng.uniform(900.0, 4200.0)),
                reverb_amount=float(rng.uniform(0.32, 0.82)),
                drive_amount=float(rng.uniform(0.0, 0.28)),
                chorus_amount=float(rng.uniform(0.0, 0.24)),
                texture_amount=float(rng.uniform(0.12, 0.54)),
                motion_amount=float(rng.uniform(0.02, 0.24)),
                pitch_drift_amount=float(rng.uniform(0.0, 0.18)),
                bloom_amount=float(rng.uniform(0.24, 0.72)),
                granular_amount=float(rng.uniform(0.0, 0.24)),
                delay_amount=float(rng.uniform(0.08, 0.36)),
                autopan_amount=float(rng.uniform(0.0, 0.18)),
                shimmer_amount=float(rng.uniform(0.0, 0.18)),
                stereo_width=float(rng.uniform(0.9, 1.4)),
                wet_dry=float(rng.uniform(0.62, 0.9)),
            )
        if profile == "bright":
            return EffectSettings(
                filter_mode=rng.choice([FilterMode.OFF, FilterMode.HIGHPASS]),
                lowpass_hz=float(rng.uniform(1800.0, 9600.0)),
                reverb_amount=float(rng.uniform(0.12, 0.42)),
                drive_amount=float(rng.uniform(0.0, 0.18)),
                chorus_amount=float(rng.uniform(0.18, 0.58)),
                texture_amount=float(rng.uniform(0.0, 0.28)),
                motion_amount=float(rng.uniform(0.04, 0.36)),
                pitch_drift_amount=float(rng.uniform(0.0, 0.16)),
                bloom_amount=float(rng.uniform(0.12, 0.38)),
                granular_amount=float(rng.uniform(0.0, 0.18)),
                delay_amount=float(rng.uniform(0.0, 0.24)),
                autopan_amount=float(rng.uniform(0.0, 0.26)),
                shimmer_amount=float(rng.uniform(0.22, 0.7)),
                stereo_width=float(rng.uniform(1.2, 1.9)),
                wet_dry=float(rng.uniform(0.5, 0.8)),
            )
        if profile == "huge":
            return EffectSettings(
                filter_mode=rng.choice([FilterMode.LOWPASS, FilterMode.BANDPASS, FilterMode.HIGHPASS]),
                lowpass_hz=float(rng.uniform(1200.0, 6200.0)),
                reverb_amount=float(rng.uniform(0.42, 0.88)),
                drive_amount=float(rng.uniform(0.0, 0.2)),
                chorus_amount=float(rng.uniform(0.18, 0.46)),
                texture_amount=float(rng.uniform(0.12, 0.52)),
                motion_amount=float(rng.uniform(0.12, 0.42)),
                pitch_drift_amount=float(rng.uniform(0.04, 0.2)),
                bloom_amount=float(rng.uniform(0.34, 0.84)),
                granular_amount=float(rng.uniform(0.0, 0.24)),
                delay_amount=float(rng.uniform(0.18, 0.48)),
                autopan_amount=float(rng.uniform(0.0, 0.22)),
                shimmer_amount=float(rng.uniform(0.08, 0.42)),
                stereo_width=float(rng.uniform(1.35, 2.0)),
                wet_dry=float(rng.uniform(0.68, 0.94)),
            )
        if profile == "weird":
            return EffectSettings(
                filter_mode=rng.choice([FilterMode.OFF, FilterMode.BANDPASS, FilterMode.HIGHPASS]),
                lowpass_hz=float(rng.uniform(700.0, 8800.0)),
                reverb_amount=float(rng.uniform(0.0, 0.62)),
                drive_amount=float(rng.uniform(0.0, 0.42)),
                chorus_amount=float(rng.uniform(0.0, 0.64)),
                texture_amount=float(rng.uniform(0.12, 0.68)),
                motion_amount=float(rng.uniform(0.12, 0.62)),
                pitch_drift_amount=float(rng.uniform(0.12, 0.38)),
                bloom_amount=float(rng.uniform(0.04, 0.56)),
                granular_amount=float(rng.uniform(0.16, 0.56)),
                delay_amount=float(rng.uniform(0.0, 0.42)),
                autopan_amount=float(rng.uniform(0.12, 0.62)),
                shimmer_amount=float(rng.uniform(0.0, 0.58)),
                stereo_width=float(rng.uniform(0.7, 1.9)),
                reverse=bool(rng.integers(0, 3) == 0),
                freeze_enabled=bool(rng.integers(0, 5) == 0),
                wet_dry=float(rng.uniform(0.42, 0.88)),
            )
        return EffectSettings(
            filter_mode=rng.choice([FilterMode.OFF, FilterMode.LOWPASS, FilterMode.HIGHPASS, FilterMode.BANDPASS]),
            reverb_amount=float(rng.uniform(0.08, 0.78)),
            lowpass_hz=float(rng.uniform(650.0, 9600.0)),
            drive_amount=float(rng.uniform(0.0, 0.42)),
            chorus_amount=float(rng.uniform(0.0, 0.58)),
            texture_amount=float(rng.uniform(0.0, 0.62)),
            motion_amount=float(rng.uniform(0.0, 0.58)),
            pitch_drift_amount=float(rng.uniform(0.0, 0.34)),
            bloom_amount=float(rng.uniform(0.0, 0.7)),
            granular_amount=float(rng.uniform(0.0, 0.48)),
            delay_amount=float(rng.uniform(0.0, 0.52)),
            autopan_amount=float(rng.uniform(0.0, 0.55)),
            stereo_width=float(rng.uniform(0.8, 1.8)),
            reverse=bool(rng.integers(0, 5) == 0),
            freeze_enabled=bool(rng.integers(0, 6) == 0),
            shimmer_amount=float(rng.uniform(0.0, 0.62)),
            wet_dry=float(rng.uniform(0.45, 0.9)),
        )

    def _refresh_presets(self, selected_name: str | None = None) -> None:
        selected = selected_name or self.current_preset_name
        selected_batch_names = self._selected_batch_preset_names() if hasattr(self, "batch_preset_list") else ()
        self._refresh_preset_tag_filter()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        presets = self._filtered_presets()
        self._refresh_batch_preset_list(presets, selected_names=selected_batch_names)
        for preset in presets:
            self.preset_combo.addItem(self._display_preset_label(preset), preset)
        index = -1
        for candidate in range(self.preset_combo.count()):
            preset = self.preset_combo.itemData(candidate)
            if isinstance(preset, AppPreset) and preset.name == selected:
                index = candidate
                break
        self.preset_combo.setCurrentIndex(index)
        self.preset_combo.blockSignals(False)
        preset = self.preset_combo.currentData()
        if isinstance(preset, AppPreset):
            self.current_preset_name = preset.name
            self._update_preset_buttons()
            self._update_dirty_label()
        else:
            self._update_preset_buttons()
            self._update_dirty_label()
        self._update_preset_metadata_controls()

    def _save_new_preset(self) -> None:
        if not self._ensure_editable("Save a preset after the current job has finished."):
            return
        name, ok = QInputDialog.getText(self, "Save preset", "Preset name:")
        if not ok or not name.strip():
            return
        normalized_name = self._validated_preset_name(name, mode="new")
        if normalized_name is None:
            return
        preset = self._current_preset(normalized_name, factory=False)
        self.preset_library.save_user_preset(preset)
        self._refresh_preset_tag_filter()
        self._refresh_presets(selected_name=preset.name)
        self.statusBar().showMessage(f"Saved preset: {preset.name}")

    def _update_selected_preset(self) -> None:
        if not self._ensure_editable("Update a preset after the current job has finished."):
            return
        preset = self.preset_combo.currentData()
        if not isinstance(preset, AppPreset) or preset.factory:
            self._show_error("Select a user preset to update it.")
            return
        updated = AppPreset(
            name=preset.name,
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            preview_length=float(self.preview_duration.value()),
            effects=self._effect_settings(),
            factory=False,
            tags=preset.tags,
            favorite=preset.favorite,
        )
        self.preset_library.save_user_preset(updated)
        self._refresh_presets(selected_name=updated.name)
        self.statusBar().showMessage(f"Updated preset: {updated.name}")

    def _duplicate_selected_preset(self) -> None:
        if not self._ensure_editable("Duplicate a preset after the current job has finished."):
            return
        preset = self.preset_combo.currentData()
        if not isinstance(preset, AppPreset):
            return
        name, ok = QInputDialog.getText(self, "Duplicate preset", "New preset name:", text=f"{preset.name} Copy")
        if not ok or not name.strip():
            return
        normalized_name = self._validated_preset_name(name, mode="new")
        if normalized_name is None:
            return
        duplicated = AppPreset(
            name=normalized_name,
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            preview_length=float(self.preview_duration.value()),
            effects=self._effect_settings(),
            factory=False,
            tags=preset.tags,
            favorite=False,
        )
        self.preset_library.save_user_preset(duplicated)
        self._refresh_preset_tag_filter()
        self._refresh_presets(selected_name=duplicated.name)
        self.statusBar().showMessage(f"Duplicated preset: {duplicated.name}")

    def _rename_selected_preset(self) -> None:
        if not self._ensure_editable("Rename a preset after the current job has finished."):
            return
        preset = self.preset_combo.currentData()
        if not isinstance(preset, AppPreset) or preset.factory:
            self._show_error("Select a user preset to rename it.")
            return
        name, ok = QInputDialog.getText(self, "Rename preset", "New preset name:", text=preset.name)
        if not ok or not name.strip():
            return
        new_name = self._validated_preset_name(name, mode="rename", current_name=preset.name)
        if new_name is None:
            return
        self.preset_library.rename_user_preset(preset.name, new_name)
        self.current_preset_name = new_name
        self._refresh_presets(selected_name=new_name)
        self.statusBar().showMessage(f"Renamed preset: {preset.name} -> {new_name}")

    def _delete_selected_preset(self) -> None:
        if not self._ensure_editable("Delete a preset after the current job has finished."):
            return
        preset = self.preset_combo.currentData()
        if not isinstance(preset, AppPreset) or preset.factory:
            self._show_error("Factory presets cannot be deleted.")
            return
        self.preset_library.delete_user_preset(preset.name)
        self._refresh_presets(selected_name="Custom")
        self.statusBar().showMessage(f"Deleted preset: {preset.name}")

    def _selected_profile(self) -> QualityProfile:
        value = self.quality_combo.currentData()
        if isinstance(value, QualityProfile):
            return value
        if isinstance(value, str):
            try:
                return QualityProfile(value)
            except ValueError:
                pass
        return QualityProfile.MEDIUM

    def _effect_settings(self) -> EffectSettings:
        return EffectSettings(
            input_gain_db=float(self.input_trim_slider.value()),
            filter_mode=self._selected_filter_mode(),
            filter_enabled=self.filter_enabled_checkbox.isChecked(),
            reverb_amount=self.reverb_slider.value() / 100.0,
            reverb_enabled=self.reverb_enabled_checkbox.isChecked(),
            lowpass_hz=float(self.lowpass_slider.value()),
            drive_amount=self.drive_slider.value() / 100.0,
            drive_enabled=self.drive_enabled_checkbox.isChecked(),
            chorus_amount=self.chorus_slider.value() / 100.0,
            chorus_enabled=self.chorus_enabled_checkbox.isChecked(),
            texture_amount=self.texture_slider.value() / 100.0,
            texture_enabled=self.texture_enabled_checkbox.isChecked(),
            motion_amount=self.motion_slider.value() / 100.0,
            motion_enabled=self.motion_enabled_checkbox.isChecked(),
            pitch_drift_amount=self.pitch_drift_slider.value() / 100.0,
            pitch_drift_enabled=self.pitch_drift_enabled_checkbox.isChecked(),
            bloom_amount=self.bloom_slider.value() / 100.0,
            bloom_enabled=self.bloom_enabled_checkbox.isChecked(),
            granular_amount=self.granular_slider.value() / 100.0,
            granular_enabled=self.granular_enabled_checkbox.isChecked(),
            delay_amount=self.delay_slider.value() / 100.0,
            delay_enabled=self.delay_enabled_checkbox.isChecked(),
            autopan_amount=self.autopan_slider.value() / 100.0,
            autopan_enabled=self.autopan_enabled_checkbox.isChecked(),
            stereo_width=self.width_slider.value() / 100.0,
            reverse=self.reverse_checkbox.isChecked(),
            freeze_enabled=self.freeze_checkbox.isChecked(),
            shimmer_amount=self.shimmer_slider.value() / 100.0,
            shimmer_enabled=self.shimmer_enabled_checkbox.isChecked(),
            wet_dry=self.wetdry_slider.value() / 100.0,
            limiter_enabled=self.limiter_checkbox.isChecked(),
        )

    def _effective_effect_settings(self) -> EffectSettings:
        effects = self._effect_settings()
        return EffectSettings(
            input_gain_db=effects.input_gain_db,
            filter_mode=effects.filter_mode if effects.filter_enabled else FilterMode.OFF,
            filter_enabled=effects.filter_enabled,
            reverb_amount=effects.reverb_amount if effects.reverb_enabled else 0.0,
            reverb_enabled=effects.reverb_enabled,
            lowpass_hz=effects.lowpass_hz,
            drive_amount=effects.drive_amount if effects.drive_enabled else 0.0,
            drive_enabled=effects.drive_enabled,
            chorus_amount=effects.chorus_amount if effects.chorus_enabled else 0.0,
            chorus_enabled=effects.chorus_enabled,
            texture_amount=effects.texture_amount if effects.texture_enabled else 0.0,
            texture_enabled=effects.texture_enabled,
            motion_amount=effects.motion_amount if effects.motion_enabled else 0.0,
            motion_enabled=effects.motion_enabled,
            pitch_drift_amount=effects.pitch_drift_amount if effects.pitch_drift_enabled else 0.0,
            pitch_drift_enabled=effects.pitch_drift_enabled,
            bloom_amount=effects.bloom_amount if effects.bloom_enabled else 0.0,
            bloom_enabled=effects.bloom_enabled,
            granular_amount=effects.granular_amount if effects.granular_enabled else 0.0,
            granular_enabled=effects.granular_enabled,
            delay_amount=effects.delay_amount if effects.delay_enabled else 0.0,
            delay_enabled=effects.delay_enabled,
            autopan_amount=effects.autopan_amount if effects.autopan_enabled else 0.0,
            autopan_enabled=effects.autopan_enabled,
            stereo_width=effects.stereo_width,
            reverse=effects.reverse,
            freeze_enabled=effects.freeze_enabled,
            shimmer_amount=effects.shimmer_amount if effects.shimmer_enabled else 0.0,
            shimmer_enabled=effects.shimmer_enabled,
            wet_dry=effects.wet_dry,
            limiter_enabled=effects.limiter_enabled,
        )

    def _preview_config(self) -> PreviewConfig:
        return PreviewConfig(
            input_path=self.input_edit.text().strip(),
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            effects=self._effective_effect_settings(),
            region=self._current_region(),
            preview_source_duration_seconds=float(self.preview_duration.value()),
        )

    def _render_config(self) -> RenderConfig:
        return RenderConfig(
            input_path=self.input_edit.text().strip(),
            output_path=self.output_edit.text().strip(),
            output_mode=self._selected_render_output_mode(),
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            effects=self._effective_effect_settings(),
            region=self._current_region(),
        )

    def _recording_config(self) -> RecordingConfig:
        return RecordingConfig(
            output_path=self.recording_output_edit.text().strip(),
            device_id=self._selected_input_device_id(),
            sample_rate=int(self.recording_sample_rate_combo.currentData()),
            channels=int(self.recording_channels_combo.currentData()),
            auto_load=self.auto_load_recordings_checkbox.isChecked(),
            audio_backend=self._selected_audio_backend(),
            host_api_name=self._selected_host_api_name(),
        )

    def _current_region(self) -> RegionSelection:
        if self.waveform_overview is not None:
            return self.waveform_widget.region
        start = float(self.preview_start.value())
        return RegionSelection(start, start + float(self.preview_duration.value()))

    def _preview_cache_key(self) -> tuple:
        effects = self._effective_effect_settings()
        region = self._current_region()
        return (
            self.input_edit.text().strip(),
            float(self.stretch_slider.value()),
            self._selected_profile().value,
            round(region.start_seconds, 3),
            round(region.end_seconds, 3),
            round(effects.input_gain_db, 3),
            effects.filter_mode.value,
            round(effects.reverb_amount, 3),
            round(effects.lowpass_hz, 1),
            round(effects.drive_amount, 3),
            round(effects.chorus_amount, 3),
            round(effects.texture_amount, 3),
            round(effects.motion_amount, 3),
            round(effects.pitch_drift_amount, 3),
            round(effects.bloom_amount, 3),
            round(effects.delay_amount, 3),
            round(effects.granular_amount, 3),
            round(effects.autopan_amount, 3),
            round(effects.stereo_width, 3),
            effects.reverse,
            effects.freeze_enabled,
            round(effects.shimmer_amount, 3),
            round(effects.wet_dry, 3),
            effects.limiter_enabled,
        )

    def _current_preset(self, name: str, factory: bool) -> AppPreset:
        return AppPreset(
            name=name,
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            preview_length=float(self.preview_duration.value()),
            effects=self._effect_settings(),
            factory=factory,
        )

    def _clear_preview_cache(self, *, event: str, announce_playing: bool) -> None:
        preview_was_playing = hasattr(self, "preview_player") and self.preview_player.is_active()
        self.current_preview = None
        self.current_preview_key = None
        if preview_was_playing:
            self.preview_state = "stale"
            self.preview_status_label.setText(self._preview_status_text("stale", event=event))
            if announce_playing and hasattr(self, "statusBar"):
                self.statusBar().showMessage(self._preview_status_text("stale", event=event))
            return
        self._set_preview_state("idle", event=event)

    def _mark_dirty(
        self,
        *,
        event: str = "selection changed",
        clear_bypass_snapshot: bool = True,
        action_label: str | None = None,
    ) -> None:
        if not hasattr(self, "stretch_slider") or not hasattr(self, "preset_dirty_label"):
            return
        self._note_workflow_change(
            audio_change=True,
            event=event,
            clear_bypass_snapshot=clear_bypass_snapshot,
            action_label=action_label,
        )

    def _apply_workflow_snapshot(
        self,
        snapshot: WorkflowStateSnapshot,
        *,
        action_name: str,
    ) -> None:
        previous_key = self._preview_cache_key() if self.input_edit.text().strip() else None
        previous_dirty_suspend = self._suspend_dirty_tracking
        previous_history_suspend = self._suspend_workflow_history_tracking
        self._clear_deferred_compare_preview()
        self._suspend_dirty_tracking = True
        self._suspend_workflow_history_tracking = True
        try:
            self.compare_slots = {
                "A": snapshot.compare_slot_a,
                "B": snapshot.compare_slot_b,
            }
            self.current_preset_name = snapshot.selected_preset_name or "Custom"
            self.input_edit.setText(snapshot.input_path)
            self.output_edit.setText(snapshot.output_path)
            render_mode_index = self.render_output_mode_combo.findData(
                render_output_mode_from_value(snapshot.render_output_mode)
            )
            if render_mode_index >= 0:
                self.render_output_mode_combo.setCurrentIndex(render_mode_index)
            self.preview_start.setValue(snapshot.preview_start)
            self.preview_duration.setValue(snapshot.preview_length)
            self.stretch_slider.setValue(int(round(snapshot.stretch_factor)))
            quality_index = self.quality_combo.findData(snapshot.quality_profile)
            if quality_index >= 0:
                self.quality_combo.setCurrentIndex(quality_index)
            self.loop_checkbox.setChecked(snapshot.loop_enabled)
            self.loop_crossfade_spin.blockSignals(True)
            self.loop_crossfade_spin.setValue(float(snapshot.loop_crossfade_ms))
            self.loop_crossfade_spin.blockSignals(False)
            self._apply_effect_settings_to_controls(snapshot.effects)
            if snapshot.input_path and Path(snapshot.input_path).exists():
                self._load_waveform(snapshot.input_path)
                self._apply_region_to_waveform(
                    RegionSelection(snapshot.waveform_region_start, snapshot.waveform_region_end)
                )
            elif snapshot.input_path:
                self._clear_loaded_input("Input audio missing")
            else:
                self._clear_loaded_input("No waveform loaded")
            self._refresh_presets(selected_name=self.current_preset_name)
            self.effects_bypass_snapshot = None
            self._update_effect_shortcut_labels()
        finally:
            self._suspend_dirty_tracking = previous_dirty_suspend
            self._suspend_workflow_history_tracking = previous_history_suspend
        self._update_compare_slot_status()
        self._update_region_status()
        target_key = self._preview_cache_key() if snapshot.input_path and Path(snapshot.input_path).exists() else None
        audio_changed = previous_key != target_key
        self._apply_dirty_state(audio_change=audio_changed, clear_bypass_snapshot=False)
        if audio_changed and self.preview_player.is_active():
            self.statusBar().showMessage(
                f"{action_name} Current playback will finish; next preview will use updated settings."
            )
        else:
            self.statusBar().showMessage(action_name)
        self._update_command_state()

    def _undo_workflow(self) -> None:
        if not self.undo_stack:
            return
        self._flush_workflow_history()
        current = self._current_workflow_snapshot()
        target = self.undo_stack.pop()
        if current != target.snapshot:
            self._append_redo_snapshot(current, target.label)
        self._apply_workflow_snapshot(target.snapshot, action_name=f"Undo: {target.label}")

    def _redo_workflow(self) -> None:
        if not self.redo_stack:
            return
        self._flush_workflow_history()
        current = self._current_workflow_snapshot()
        target = self.redo_stack.pop()
        if current != target.snapshot:
            self._append_undo_snapshot(current, target.label)
        self._apply_workflow_snapshot(target.snapshot, action_name=f"Redo: {target.label}")

    def _update_dirty_label(self) -> None:
        if not hasattr(self, "preset_dirty_label") or not hasattr(self, "stretch_slider"):
            return
        preset = self.preset_library.get_preset(self.current_preset_name)
        if preset is None:
            self.preset_dirty_label.setText("Preset: custom working state")
            return
        current = self._current_preset(preset.name, preset.factory)
        clean = (
            round(current.stretch_factor, 3) == round(preset.stretch_factor, 3)
            and current.quality_profile == preset.quality_profile
            and round(current.preview_length, 3) == round(preset.preview_length, 3)
            and current.effects == preset.effects
        )
        if preset.name == "Custom":
            self.preset_dirty_label.setText("Preset: custom working state")
            return
        self.preset_dirty_label.setText(f"Preset: {preset.name}" if clean else f"Preset: modified from {preset.name}")

    def _update_preset_buttons(self) -> None:
        preset = self.preset_combo.currentData() if hasattr(self, "preset_combo") else None
        actions_enabled = not self._is_processing()
        is_user = preset is not None and not preset.factory and actions_enabled
        self.save_new_preset_button.setEnabled(actions_enabled)
        self.duplicate_preset_button.setEnabled(actions_enabled)
        self.update_preset_button.setEnabled(is_user)
        self.rename_preset_button.setEnabled(is_user)
        self.delete_preset_button.setEnabled(is_user)
        if hasattr(self, "recent_takes_list"):
            self._update_recent_take_buttons()

    def _update_command_state(self) -> None:
        processing = self._is_processing()
        recording = self.recording_controller.is_recording()
        preview_playing = self.preview_player.is_active()
        editable = not processing
        can_record = editable and self.input_device_combo.currentData() is not None

        self._update_workflow_history_action_labels()

        self.preview_button.setEnabled(editable)
        self.replay_preview_button.setEnabled(editable and self.current_preview is not None)
        self.render_button.setEnabled(editable)
        self.record_button.setEnabled(can_record)
        self.stop_button.setEnabled(recording or preview_playing)
        self.preview_button.setText("Restart Preview" if preview_playing else "Play Preview")

        self.preview_action.setEnabled(editable)
        self.render_action.setEnabled(editable)
        self.open_project_action.setEnabled(editable)
        self.save_project_action.setEnabled(editable)
        self.record_action.setEnabled(can_record)
        self.stop_action.setEnabled(recording or preview_playing)
        self.open_action.setEnabled(editable)
        self.undo_action.setEnabled(bool(self.undo_stack))
        self.redo_action.setEnabled(bool(self.redo_stack))
        self.preview_action.setText("Restart Preview" if preview_playing else "Play Preview")

        for widget in [
            self.browse_input_button,
            self.browse_output_button,
            self.browse_recording_button,
            self.refresh_inputs_button,
            self.input_edit,
            self.output_edit,
            self.open_project_button,
            self.save_project_button,
            self.save_project_as_button,
            self.recent_sources_list,
            self.open_recent_source_button,
            self.open_recent_source_folder_button,
            self.forget_recent_sources_button,
            self.clear_recent_sources_button,
            self.recent_projects_list,
            self.open_recent_project_button,
            self.forget_recent_projects_button,
            self.render_output_mode_combo,
            self.recording_output_edit,
            self.audio_backend_combo,
            self.host_api_combo,
            self.input_device_combo,
            self.output_device_combo,
            self.recording_sample_rate_combo,
            self.recording_channels_combo,
            self.preview_output_channels_combo,
            self.auto_load_recordings_checkbox,
            self.snap_to_grid_checkbox,
            self.stretch_slider,
            self.preview_start,
            self.preview_duration,
            self.quality_combo,
            self.loop_crossfade_spin,
            self.capture_a_button,
            self.load_a_button,
            self.capture_b_button,
            self.load_b_button,
            self.toggle_ab_button,
            self.store_active_compare_button,
            self.swap_compare_button,
            self.preview_history_list,
            self.load_history_button,
            self.replay_history_button,
            self.clear_history_button,
            self.preset_combo,
            self.preset_search_edit,
            self.preset_tag_filter_combo,
            self.preset_favorites_only_checkbox,
            self.toggle_favorite_preset_button,
            self.preset_tags_edit,
            self.apply_preset_tags_button,
            self.batch_preset_list,
            self.select_filtered_batch_button,
            self.clear_batch_selection_button,
            self.queue_batch_button,
            self.render_queue_list,
            self.queue_current_button,
            self.start_queue_button,
            self.remove_queue_job_button,
            self.clear_queue_button,
            self.loop_checkbox,
            self.filter_mode_combo,
            self.theme_combo,
            self.ui_scale_combo,
            self.zoom_selection_button,
            self.show_full_button,
            self.reset_selection_button,
            self.input_trim_slider,
            self.reverb_slider,
            self.lowpass_slider,
            self.drive_slider,
            self.chorus_slider,
            self.texture_slider,
            self.motion_slider,
            self.pitch_drift_slider,
            self.bloom_slider,
            self.shimmer_slider,
            self.granular_slider,
            self.delay_slider,
            self.autopan_slider,
            self.width_slider,
            self.wetdry_slider,
            self.limiter_checkbox,
            self.reverse_checkbox,
            self.freeze_checkbox,
            self.random_effects_button,
            self.random_dark_button,
            self.random_bright_button,
            self.random_huge_button,
            self.random_weird_button,
            self.harmonize_effects_button,
            self.bypass_effects_button,
            self.reset_effects_button,
            self.filter_enabled_checkbox,
            self.reverb_enabled_checkbox,
            self.drive_enabled_checkbox,
            self.chorus_enabled_checkbox,
            self.texture_enabled_checkbox,
            self.motion_enabled_checkbox,
            self.pitch_drift_enabled_checkbox,
            self.bloom_enabled_checkbox,
            self.shimmer_enabled_checkbox,
            self.granular_enabled_checkbox,
            self.delay_enabled_checkbox,
            self.autopan_enabled_checkbox,
        ]:
            widget.setEnabled(editable)
        queue_has_items = len(self.render_queue_items) > 0
        queue_has_selection = 0 <= self._selected_queue_index() < len(self.render_queue_items)
        batch_has_items = self.batch_preset_list.count() > 0
        batch_has_selection = len(self._selected_batch_preset_names()) > 0
        recent_sources_has_items = self.recent_sources_list.count() > 0
        recent_sources_has_selection = bool(self._selected_recent_source_path())
        recent_projects_has_items = self.recent_projects_list.count() > 0
        preview_history_has_items = len(self.preview_history_entries) > 0
        compare_ready = self.compare_slots.get("A") is not None and self.compare_slots.get("B") is not None
        compare_has_any = self.compare_slots.get("A") is not None or self.compare_slots.get("B") is not None
        self.render_queue_list.setEnabled(editable and queue_has_items)
        self.start_queue_button.setEnabled(editable and queue_has_items)
        self.remove_queue_job_button.setEnabled(editable and queue_has_selection)
        self.clear_queue_button.setEnabled(editable and queue_has_items)
        self.batch_preset_list.setEnabled(editable and batch_has_items)
        self.select_filtered_batch_button.setEnabled(editable and batch_has_items)
        self.clear_batch_selection_button.setEnabled(editable and batch_has_selection)
        self.queue_batch_button.setEnabled(editable and batch_has_selection)
        self.recent_sources_list.setEnabled(editable and recent_sources_has_items)
        self.open_recent_source_button.setEnabled(editable and recent_sources_has_selection)
        self.open_recent_source_folder_button.setEnabled(editable and recent_sources_has_selection)
        self.forget_recent_sources_button.setEnabled(editable and recent_sources_has_items)
        self.clear_recent_sources_button.setEnabled(editable and recent_sources_has_items)
        self.recent_projects_list.setEnabled(editable and recent_projects_has_items)
        self.open_recent_project_button.setEnabled(editable and recent_projects_has_items)
        self.forget_recent_projects_button.setEnabled(editable and recent_projects_has_items)
        self.preview_history_list.setEnabled(editable and preview_history_has_items)
        self.load_history_button.setEnabled(editable and preview_history_has_items)
        self.replay_history_button.setEnabled(editable and preview_history_has_items)
        self.clear_history_button.setEnabled(editable and preview_history_has_items)
        self.toggle_ab_button.setEnabled(editable and compare_ready)
        self.toggle_ab_action.setEnabled(editable and compare_ready)
        self.store_active_compare_button.setEnabled(editable)
        self.swap_compare_button.setEnabled(editable and compare_has_any)
        self._update_preset_buttons()

    def _restore_state(self) -> None:
        state = self.preset_library.load_state(APP_STATE_PATH)
        self._suspend_dirty_tracking = True
        self._suspend_workflow_history_tracking = True
        self.current_ui_scale_percent = clamp_ui_scale_percent(state.ui_scale_percent)
        scale_index = self.ui_scale_combo.findData(self.current_ui_scale_percent)
        if scale_index >= 0:
            self.ui_scale_combo.setCurrentIndex(scale_index)
        self._apply_theme(state.theme_name, announce=False)
        theme_index = self.theme_combo.findData(self.current_theme_name)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        self.input_edit.setText(state.input_path)
        self.output_edit.setText(state.output_path)
        self.current_project_path = state.current_project_path
        render_mode_index = self.render_output_mode_combo.findData(render_output_mode_from_value(state.render_output_mode))
        if render_mode_index >= 0:
            self.render_output_mode_combo.setCurrentIndex(render_mode_index)
        self.recording_output_edit.setText(state.recording_output_path)
        backend_index = self.audio_backend_combo.findData(state.audio_backend)
        if backend_index >= 0:
            self.audio_backend_combo.setCurrentIndex(backend_index)
        self.auto_load_recordings_checkbox.setChecked(state.auto_load_recordings)
        self.recent_takes = state.recent_takes
        self.recent_source_paths = list(state.recent_source_paths)
        self.recent_project_paths = list(state.recent_project_paths)
        self.favorite_factory_preset_names = set(state.favorite_factory_presets)
        self.compare_slots = {"A": state.compare_slot_a, "B": state.compare_slot_b}
        self.render_queue_items = list(state.render_queue)
        sample_rate_index = self.recording_sample_rate_combo.findData(state.recording_sample_rate)
        if sample_rate_index >= 0:
            self.recording_sample_rate_combo.setCurrentIndex(sample_rate_index)
        self.preview_start.setValue(state.preview_start)
        self.preview_duration.setValue(state.preview_length)
        self.stretch_slider.setValue(int(round(state.stretch_factor)))
        self.loop_checkbox.setChecked(state.loop_enabled)
        self.loop_crossfade_spin.blockSignals(True)
        self.loop_crossfade_spin.setValue(float(state.loop_crossfade_ms))
        self.loop_crossfade_spin.blockSignals(False)
        quality_index = self.quality_combo.findData(state.quality_profile)
        if quality_index >= 0:
            self.quality_combo.setCurrentIndex(quality_index)
        self._apply_effect_settings_to_controls(state.effects)
        requested_preset_name = state.selected_preset_name or "Custom"
        self._refresh_presets(selected_name=requested_preset_name)
        self._refresh_audio_routing(
            backend=state.audio_backend,
            host_api_name=state.host_api_name,
            input_device_id=state.recording_input_device_id,
            output_device_id=state.preview_output_device_id,
        )
        channels_index = self.recording_channels_combo.findData(state.recording_input_channels)
        if channels_index >= 0:
            self.recording_channels_combo.setCurrentIndex(channels_index)
        output_channels_index = self.preview_output_channels_combo.findData(state.preview_output_channels)
        if output_channels_index >= 0:
            self.preview_output_channels_combo.setCurrentIndex(output_channels_index)
        self._set_active_tab(state.active_workspace_tab)
        if requested_preset_name != self.current_preset_name:
            self.statusBar().showMessage(
                f"Preset '{requested_preset_name}' was not found. Falling back to {self.current_preset_name}."
            )
        if state.input_path and Path(state.input_path).exists():
            if self._load_waveform(state.input_path):
                self._apply_region_to_waveform(
                    RegionSelection(state.waveform_region_start, state.waveform_region_end)
                )
                self.statusBar().showMessage(f"Restored session from {Path(state.input_path).name}")
        elif state.input_path:
            self.input_edit.clear()
            self._clear_loaded_input("Saved input file is missing")
            self.statusBar().showMessage("Saved input file is missing; restore skipped")
        else:
            self.statusBar().showMessage("Ready")
        if not self.recording_output_edit.text():
            self.recording_output_edit.setText(self._default_recording_path())
        self.recording_duration_label.setText("00:00.0")
        self._suspend_dirty_tracking = False
        self._suspend_workflow_history_tracking = False
        self._refresh_recent_takes_list()
        self._refresh_recent_sources_list()
        self._update_project_path_label()
        self._refresh_recent_projects_list()
        self._update_compare_slot_status()
        self._refresh_render_queue_list()
        self.effects_bypass_snapshot = None
        self._update_effect_shortcut_labels()
        self.current_preview = None
        self.current_preview_key = None
        self.preview_state = "idle"
        self._update_region_status()
        self._update_dirty_label()
        self._reset_workflow_history()
        self._update_command_state()
        self._fit_window_to_screen()

    def _persist_state(self) -> None:
        region = self._current_region()
        state = AppState(
            input_path=self.input_edit.text().strip(),
            output_path=self.output_edit.text().strip(),
            recent_source_paths=tuple(self.recent_source_paths),
            current_project_path=self.current_project_path,
            render_output_mode=self._selected_render_output_mode().value,
            recording_output_path=self.recording_output_edit.text().strip(),
            audio_backend=self._selected_audio_backend(),
            host_api_name=self._selected_host_api_name(),
            recording_input_device_id=self._selected_input_device_id(),
            preview_output_device_id=self._selected_output_device_id(),
            recording_sample_rate=int(self.recording_sample_rate_combo.currentData()),
            recording_input_channels=int(self.recording_channels_combo.currentData()),
            preview_output_channels=int(self.preview_output_channels_combo.currentData()),
            auto_load_recordings=self.auto_load_recordings_checkbox.isChecked(),
            active_workspace_tab=self.workspace_tabs.tabText(self.workspace_tabs.currentIndex()),
            recent_takes=self.recent_takes,
            preview_start=float(self.preview_start.value()),
            preview_length=float(self.preview_duration.value()),
            stretch_factor=float(self.stretch_slider.value()),
            quality_profile=self._selected_profile(),
            effects=self._effect_settings(),
            selected_preset_name=self.current_preset_name,
            compare_slot_a=self.compare_slots.get("A"),
            compare_slot_b=self.compare_slots.get("B"),
            render_queue=tuple(self.render_queue_items),
            recent_project_paths=tuple(self.recent_project_paths),
            favorite_factory_presets=self._favorite_factory_names_tuple(),
            waveform_region_start=region.start_seconds,
            waveform_region_end=region.end_seconds,
            loop_enabled=self.loop_checkbox.isChecked(),
            loop_crossfade_ms=self._selected_loop_crossfade_ms(),
            theme_name=self.current_theme_name,
            ui_scale_percent=self.current_ui_scale_percent,
        )
        self.preset_library.save_state(state, APP_STATE_PATH)

    def _on_theme_changed(self, index: int) -> None:
        if index < 0:
            return
        theme_name = self.theme_combo.itemData(index)
        if isinstance(theme_name, str):
            self._apply_theme(theme_name)

    def _on_ui_scale_changed(self, index: int) -> None:
        if index < 0:
            return
        value = self.ui_scale_combo.itemData(index)
        self._apply_ui_scale(value if value is not None else 100)

    def _apply_theme(self, theme_name: str, *, announce: bool = True) -> None:
        theme = self.theme_manager.apply_theme(
            theme_name,
            root=self,
            waveform_widget=self.waveform_widget,
            ui_scale_percent=self.current_ui_scale_percent,
        )
        self.current_theme_name = theme.name
        if hasattr(self, "theme_combo"):
            combo_index = self.theme_combo.findData(theme.name)
            if combo_index >= 0 and combo_index != self.theme_combo.currentIndex():
                self.theme_combo.blockSignals(True)
                self.theme_combo.setCurrentIndex(combo_index)
                self.theme_combo.blockSignals(False)
        if announce and hasattr(self, "statusBar"):
            self.statusBar().showMessage(f"Theme switched to {theme.label}")

    def _apply_ui_scale(self, scale_percent: object, *, announce: bool = True) -> None:
        self.current_ui_scale_percent = clamp_ui_scale_percent(scale_percent)
        if hasattr(self, "ui_scale_combo"):
            combo_index = self.ui_scale_combo.findData(self.current_ui_scale_percent)
            if combo_index >= 0 and combo_index != self.ui_scale_combo.currentIndex():
                self.ui_scale_combo.blockSignals(True)
                self.ui_scale_combo.setCurrentIndex(combo_index)
                self.ui_scale_combo.blockSignals(False)
        self._apply_theme(self.current_theme_name, announce=False)
        self._fit_window_to_screen()
        if announce and hasattr(self, "statusBar"):
            self.statusBar().showMessage(f"Interface scale set to {self.current_ui_scale_percent}%")

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "FINDUS>x<STRETCHING", message)

    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def _clear_loaded_input(self, region_message: str) -> None:
        self.waveform_overview = None
        self.waveform_widget.overview = None
        self.waveform_widget.set_playhead(None)
        self.waveform_widget.update()
        self.effects_bypass_snapshot = None
        self._update_effect_shortcut_labels()
        self.current_preview = None
        self.current_preview_key = None
        self.region_status.setText(region_message)
        self._set_preview_state("idle")

    def _apply_region_to_waveform(self, region: RegionSelection) -> None:
        if self.waveform_overview is None:
            return
        self.waveform_widget.set_region(region, emit_signal=False)
        normalized = self.waveform_widget.region
        self._syncing_region = True
        self.preview_start.setValue(normalized.start_seconds)
        self.preview_duration.setValue(max(0.05, normalized.duration_seconds))
        self._syncing_region = False
        self._update_region_status(normalized)

    def _selected_loop_crossfade_ms(self) -> int:
        return int(round(float(self.loop_crossfade_spin.value()))) if hasattr(self, "loop_crossfade_spin") else 80

    def _on_loop_toggled(self, checked: bool) -> None:
        self._note_workflow_change(
            audio_change=False,
            clear_bypass_snapshot=False,
            action_label="loop toggle",
        )
        self.loop_state_label.setText("Loop on" if checked else "Loop off")
        self.loop_state_label.setToolTip(
            "Preview will repeat until you stop it." if checked else "Preview will play once."
        )
        if self.preview_player.is_active() and self.current_preview is not None:
            self._set_preview_state("looping" if checked else "playing", result=self.current_preview)
        elif self.current_preview is not None:
            self._set_preview_state("ready", result=self.current_preview)

    def _on_loop_crossfade_changed(self, value: float) -> None:
        self._note_workflow_change(
            audio_change=False,
            clear_bypass_snapshot=False,
            action_label="loop crossfade change",
        )
        ms = int(round(value))
        if self.preview_player.is_active() and self.loop_checkbox.isChecked() and self.current_preview is not None:
            self._set_preview_state("looping", result=self.current_preview)
            self.statusBar().showMessage(
                f"Loop crossfade set to {ms} ms. Current loop will finish; next pass will use the updated crossfade."
            )
            return
        if self.current_preview is not None and self.loop_checkbox.isChecked():
            self._set_preview_state("ready", result=self.current_preview)
        else:
            self.statusBar().showMessage(
                "Loop crossfade disabled." if ms <= 0 else f"Loop crossfade set to {ms} ms."
            )

    def _set_drop_hint_visible(self, visible: bool) -> None:
        if hasattr(self, "drop_hint_label"):
            self.drop_hint_label.setVisible(visible)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if any(self._dropped_path_kind(path) is not None for path in self._dropped_paths_from_event(event)):
            self._set_drop_hint_visible(True)
            self.statusBar().showMessage("Drop one audio file or one .findusstretch.json project.")
            event.acceptProposedAction()
            return
        self._set_drop_hint_visible(False)
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drop_hint_visible(False)
        if self._handle_dropped_paths(self._dropped_paths_from_event(event)):
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: ANN001
        self._set_drop_hint_visible(False)
        super().dragLeaveEvent(event)

    def _dropped_paths_from_event(self, event) -> list[str]:  # noqa: ANN001
        mime = event.mimeData()
        if mime is None or not mime.hasUrls():
            return []
        paths: list[str] = []
        for url in mime.urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        return paths

    def _dropped_path_kind(self, path: str) -> str | None:
        lowered = path.lower()
        if lowered.endswith(".findusstretch.json"):
            return "project"
        if lowered.endswith((".wav", ".flac", ".ogg", ".aiff", ".aif", ".mp3")):
            return "audio"
        return None

    def _handle_dropped_paths(self, paths: list[str]) -> bool:
        supported: list[tuple[str, str]] = []
        for path in paths:
            kind = self._dropped_path_kind(path)
            if kind is not None:
                supported.append((kind, path))
        if not supported:
            if paths:
                self.statusBar().showMessage("Ignored unsupported dropped file.")
            return False
        if not self._ensure_editable("Drop files after the current job has finished."):
            return True
        kind, chosen_path = supported[0]
        if kind == "project":
            self._load_project_from_path(chosen_path)
        else:
            self._load_source_audio_path(
                chosen_path,
                status_message=f"Loaded dropped source: {Path(chosen_path).name}",
                create_undo_checkpoint=True,
            )
        if len(supported) > 1:
            self.statusBar().showMessage(
                f"Loaded {Path(chosen_path).name}. Only the first supported dropped file was used."
            )
        return True

    def _update_region_status(self, region: RegionSelection | None = None) -> None:
        region = region or self._current_region()
        self.region_status.setText(self._region_summary_text(region))
        if hasattr(self, "preview_status_label"):
            self.preview_status_label.setText(self._preview_status_text(self.preview_state, result=self.current_preview))

    def _replay_last_preview(self) -> None:
        if self.current_preview is None:
            self._show_error("No cached preview is ready yet. Press Play Preview first.")
            return
        if not self._ensure_idle("Wait for the current render or recording job to finish first."):
            return
        self._play_preview_result(self.current_preview, from_cache=True)

    def _region_summary_text(self, region: RegionSelection | None = None) -> str:
        region = region or self._current_region()
        return (
            f"Region {region.start_seconds:.2f}s -> {region.end_seconds:.2f}s "
            f"({region.duration_seconds:.2f}s selected)"
        )

    def _set_preview_state(
        self,
        state: str,
        *,
        result: PreviewResult | None = None,
        from_cache: bool = False,
        event: str | None = None,
    ) -> None:
        self.preview_state = state
        text = self._preview_status_text(state, result=result, from_cache=from_cache, event=event)
        self.preview_status_label.setText(text)
        self.statusBar().showMessage(text)

    def _preview_status_text(
        self,
        state: str,
        *,
        result: PreviewResult | None = None,
        from_cache: bool = False,
        event: str | None = None,
    ) -> str:
        region_text = self._region_summary_text()
        if state == "rendering":
            return f"Preview rendering. Preparing processed audio for {region_text}."
        if state == "ready":
            return f"Cached preview ready. Press Replay Last Preview to audition {region_text}."
        if state == "playing":
            cached_text = "cached " if from_cache else ""
            return f"Playing {cached_text}processed preview for {region_text}."
        if state == "looping":
            crossfade_ms = self._selected_loop_crossfade_ms()
            if crossfade_ms > 0:
                return f"Looping processed preview for {region_text} with {crossfade_ms} ms crossfade."
            return f"Looping processed preview for {region_text}."
        if state == "stale":
            return f"Current playback will finish; next preview will use updated settings for {region_text}."
        if event == "stopped":
            return f"Preview stopped. Cached preview ready for {region_text}."
        if event == "finished":
            return f"Preview finished. Cached preview ready for {region_text}."
        if event == "selection changed":
            return f"Preview invalidated. Next preview will re-render for {region_text}."
        return f"Preview idle. {region_text}."

    def _validated_preset_name(
        self,
        raw_name: str,
        *,
        mode: str,
        current_name: str | None = None,
    ) -> str | None:
        name = raw_name.strip()
        if not name:
            self._show_error("Preset name cannot be empty.")
            return None
        existing = self.preset_library.get_preset(name)
        if existing is None:
            return name
        if mode == "rename" and current_name == name:
            return name
        self._show_error(f"A preset named '{name}' already exists.")
        return None

    def _selected_audio_backend(self) -> str:
        value = self.audio_backend_combo.currentData()
        return value if isinstance(value, str) else AUDIO_BACKEND_AUTO

    def _selected_host_api_name(self) -> str:
        value = self.host_api_combo.currentData()
        return value if isinstance(value, str) else ""

    def _selected_input_device_id(self) -> str:
        value = self.input_device_combo.currentData()
        return value if isinstance(value, str) else ""

    def _selected_output_device_id(self) -> str:
        value = self.output_device_combo.currentData()
        return value if isinstance(value, str) else ""

    def _selected_output_channels(self) -> int:
        value = self.preview_output_channels_combo.currentData()
        return int(value) if value is not None else 2

    def _selected_filter_mode(self) -> FilterMode:
        value = self.filter_mode_combo.currentData()
        if isinstance(value, FilterMode):
            return value
        if isinstance(value, str):
            try:
                return FilterMode(value)
            except ValueError:
                pass
        return FilterMode.LOWPASS

    def _is_processing(self) -> bool:
        return self.preview_worker is not None or self.render_worker is not None or self.recording_controller.is_recording()

    def _ensure_idle(self, message: str) -> bool:
        if self._is_processing():
            self._show_error(message)
            return False
        return True

    def _ensure_editable(self, message: str) -> bool:
        return self._ensure_idle(message)

    def _set_active_tab(self, name: str) -> None:
        for index in range(self.workspace_tabs.count()):
            if self.workspace_tabs.tabText(index) == name:
                self.workspace_tabs.setCurrentIndex(index)
                return
        self.workspace_tabs.setCurrentIndex(0)

    def _fit_window_to_screen(self) -> None:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        scale_factor = self.current_ui_scale_percent / 100.0
        desired_width = int(round(self._base_window_size[0] * scale_factor))
        desired_height = int(round(self._base_window_size[1] * scale_factor))
        target_width = max(self.minimumWidth(), min(desired_width, int(available.width() * 0.92)))
        target_height = max(self.minimumHeight(), min(desired_height, int(available.height() * 0.9)))
        if self.width() != target_width or self.height() != target_height:
            self.resize(target_width, target_height)

    def _zoom_to_selection(self) -> None:
        if hasattr(self, "waveform_widget"):
            self.waveform_widget.fit_selection()

    def _show_full_waveform(self) -> None:
        if hasattr(self, "waveform_widget"):
            self.waveform_widget.fit_full_range()

    def _reset_waveform_selection(self) -> None:
        if hasattr(self, "waveform_widget"):
            self.waveform_widget.reset_selection()

    def _default_recording_path(self) -> str:
        if self.input_edit.text().strip():
            base_dir = Path(self.input_edit.text().strip()).resolve().parent
        elif self.output_edit.text().strip():
            base_dir = Path(self.output_edit.text().strip()).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parent.parent
        return suggested_recording_path(base_dir)

    def _icon(self, theme_name: str, fallback: QStyle.StandardPixmap) -> QIcon:
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            return self.style().standardIcon(fallback)
        return icon


def _existing_startup_splash_paths() -> tuple[Path, ...]:
    existing = tuple(path for path in STARTUP_SPLASH_VARIANT_PATHS if path.exists())
    if existing:
        return existing
    if DEFAULT_APP_ICON_PATH.exists():
        return (DEFAULT_APP_ICON_PATH,)
    return ()


def _choose_startup_splash_path(choice_func: Callable[[list[Path]], Path] | None = None) -> Path | None:
    options = list(_existing_startup_splash_paths())
    if not options:
        return None
    chooser = choice_func or random.choice
    return chooser(options)


def run() -> int:
    app = QApplication.instance() or QApplication([])
    splash_path = _choose_startup_splash_path()
    splash = StartupSplashScreen(splash_path) if splash_path is not None else None

    if splash is not None:
        splash.show()
        splash.show_stage("Preparing startup screen...", 6)
        app.processEvents()

    def update_startup(message: str, progress: int) -> None:
        if splash is None:
            return
        splash.show_stage(message, progress)
        app.processEvents()

    window = MainWindow(startup_callback=update_startup)
    if splash is not None:
        splash.show_stage("Opening workspace...", 100)
        app.processEvents()
    window.show()
    if splash is not None:
        splash.finish(window)
    return app.exec()


def _wrap_layout(layout) -> QWidget:  # noqa: ANN001
    widget = QWidget()
    widget.setLayout(layout)
    return widget


def _build_section_header(title: str, description: str) -> QLabel:
    label = QLabel(f"<b>{title}</b><br>{description}")
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setProperty("muted", True)
    return label


def _float_audio_to_pcm16(audio: np.ndarray) -> bytes:
    clipped = np.clip(np.asarray(audio, dtype=np.float32), -1.0, 1.0)
    return (clipped * 32767.0).astype(np.int16).tobytes()


def _coerce_audio_channels(audio: np.ndarray, channels: int) -> np.ndarray:
    data = np.asarray(audio, dtype=np.float32)
    target_channels = max(1, int(channels))
    if data.ndim == 1:
        if target_channels == 1:
            return data
        return np.repeat(data[:, None], target_channels, axis=1)
    if data.shape[1] == target_channels:
        return data
    if target_channels == 1:
        return np.mean(data, axis=1, dtype=np.float32)
    if data.shape[1] == 1:
        return np.repeat(data, target_channels, axis=1)
    return data[:, :target_channels]


def _build_percent_slider(value: int, max_value: int = 100) -> tuple[QSlider, QLabel]:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(0, max_value)
    slider.setValue(value)
    label = QLabel(f"{value}%")
    slider.valueChanged.connect(lambda amount: label.setText(f"{amount}%"))
    return slider, label


def _build_hz_slider(value: int, minimum: int, maximum: int) -> tuple[QSlider, QLabel]:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setValue(value)
    label = QLabel(f"{value} Hz")
    slider.valueChanged.connect(lambda amount: label.setText(f"{amount} Hz"))
    return slider, label


def _build_db_slider(value: int, minimum: int, maximum: int) -> tuple[QSlider, QLabel]:
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(minimum, maximum)
    slider.setValue(value)
    label = QLabel(f"{value:+d} dB")
    slider.valueChanged.connect(lambda amount: label.setText(f"{amount:+d} dB"))
    return slider, label


def _add_effect_row(
    layout: QGridLayout,
    row: int,
    name: str,
    slider: QSlider,
    label: QLabel,
    toggle: QCheckBox | None = None,
) -> None:
    layout.addWidget(QLabel(name), row, 0)
    layout.addWidget(slider, row, 1)
    layout.addWidget(label, row, 2)
    if toggle is not None:
        layout.addWidget(toggle, row, 3)


def _ensure_wav_suffix(path: str) -> str:
    return path if path.lower().endswith(".wav") else f"{path}.wav"


def _ensure_project_suffix(path: str) -> str:
    return path if path.lower().endswith(".findusstretch.json") else f"{path}.findusstretch.json"


def _format_seconds(seconds: float) -> str:
    total_seconds = max(0.0, seconds)
    minutes = int(total_seconds // 60)
    seconds_remainder = total_seconds - (minutes * 60)
    return f"{minutes:02d}:{seconds_remainder:04.1f}"


def _safe_name_token(value: str) -> str:
    cleaned = "".join(character.lower() if character.isascii() and character.isalnum() else "_" for character in value.strip())
    normalized = "_".join(part for part in cleaned.split("_") if part)
    return normalized or "preset"


def _help_html() -> str:
    return """
    <h2>FINDUS&gt;x&lt;STRETCHING Help</h2>
    <p>
      This app turns short sounds, recordings, and found audio into long drones, pads, and ambient textures.
      The typical workflow is: load or record audio, choose a region, shape the stretch, add effects, preview, and render.
    </p>

    <h3>Quick Workflow</h3>
    <ol>
      <li>Open a source file or record a new take from the <b>Source</b> tab.</li>
      <li>Choose the most interesting part of the sound in the waveform or with numeric region controls.</li>
      <li>Set stretch amount and quality in the <b>Stretch</b> tab.</li>
      <li>Shape tone and motion in the <b>Effects</b> tab.</li>
      <li>Pick a preset as a starting point, then preview and render.</li>
    </ol>

    <h3>Toolbar And Main Controls</h3>
    <ul>
      <li><b>Undo / Redo</b>: move backward or forward through recent workflow edits.</li>
      <li>The undo and redo tooltips reflect the latest workflow step, such as stretch change, source load, project load, or slot load.</li>
      <li><b>Open</b>: choose an input audio file.</li>
      <li><b>Open Project</b>: load a saved project file with source, region, effects, compare slots, and queue state.</li>
      <li><b>Save Project</b>: save the current project file without touching the lightweight app-state restore file.</li>
      <li><b>Record</b>: start recording from the selected input device.</li>
      <li><b>Stop</b>: stop playback or recording.</li>
      <li><b>Preview</b>: render a short preview of the selected region with the current settings.</li>
      <li><b>Render</b>: export the current wet, dry, or dry+wet render mode as WAV.</li>
      <li><b>Theme</b>: switch the whole app between Studio, 8-bit, and 16-bit looks.</li>
      <li><b>Scale</b>: resize the interface from 50% to 200% to better fit different screens.</li>
    </ul>

    <h3>Themes</h3>
    <p>
      The app now includes a larger set of visual themes. Available styles include:
      <b>Studio</b>, <b>8-bit</b>, <b>16-bit</b>, <b>C64</b>, <b>Amiga</b>, <b>Sega</b>,
      <b>Arcade</b>, <b>Amber</b>, <b>Ice</b>, <b>Sunset</b>, <b>DOS</b>, <b>Game Boy</b>,
      <b>NES</b>, <b>SNES</b>, <b>PlayStation</b>, <b>Tracker</b>, <b>Matrix</b>, and <b>CRT Green</b>.
      Themes only change the look of the app and waveform, not the audio result.
    </p>

    <h3>Waveform Area</h3>
    <ul>
      <li><b>Waveform</b>: shows the loaded source and the active selection.</li>
      <li><b>Loop</b>: repeats the current processed preview until you stop it.</li>
      <li><b>Loop crossfade</b>: smooths the handoff between loop passes for more seamless ambient previewing.</li>
<li><b>Fit Selection</b>: centers the current region in view.</li>
<li><b>Fit Full File</b>: resets the waveform zoom to the full file.</li>
<li><b>Snap 0.1s</b>: rounds region edits to tenths for cleaner loop points.</li>
      <li><b>Reset Selection</b>: returns to a safe default selection.</li>
    </ul>

    <h3>Source Tab</h3>
    <ul>
      <li><b>Subtabs</b>: use <b>Files</b>, <b>Projects</b>, <b>Audio I/O</b>, and <b>Recording</b> to keep the source workspace compact.</li>
      <li><b>Files</b>: keeps input audio, recent sources, render path, and export mode together.</li>
      <li><b>Projects</b>: keeps project open/save tools, recent projects, and the render queue together.</li>
      <li><b>Audio I/O</b>: keeps backend, host API, devices, channels, and routing diagnostics together.</li>
      <li><b>Recording</b>: keeps recording path, live meters, auto-load, and recent takes together.</li>
      <li><b>Input audio</b>: source file used for preview and render.</li>
      <li><b>Drag and drop</b>: drop one supported audio file or one project file anywhere into the window to open it quickly.</li>
      <li><b>Recent sources</b>: quick list of recently opened source files that still exist on disk.</li>
      <li><b>Source actions</b>: open the selected recent source, jump to its folder, forget missing files, or clear the list.</li>
      <li><b>Render WAV</b>: destination path for the final export.</li>
      <li><b>Project</b>: open, save, or save-as a project file for the current working session.</li>
      <li><b>Project file</b>: shows the active project path, if one is loaded or saved.</li>
      <li><b>Recent projects</b>: launchable list of saved project files that still exist on disk.</li>
      <li><b>Export mode</b>: choose wet only, dry only, or dry+wet export. Dry means stretched audio before effects, not the untouched source file.</li>
      <li><b>Recording WAV</b>: destination path for a recorded take.</li>
      <li><b>Render queue</b>: holds upcoming render jobs and processes them one after another.</li>
      <li><b>Queue Current</b>: adds the current source region, stretch, preset/effects snapshot, and export mode to the queue.</li>
      <li><b>Start Queue</b>: starts the queued jobs sequentially.</li>
      <li><b>Audio backend</b>: choose Auto, PortAudio, or Qt fallback. Auto prefers PortAudio on Windows when available.</li>
      <li><b>Host API</b>: choose a driver family such as MME, WASAPI, WDM-KS, or ASIO when PortAudio exposes it.</li>
      <li><b>Input device</b>: microphone or hardware input used for recording.</li>
      <li><b>Output device</b>: hardware output used for preview playback.</li>
      <li><b>Sample rate</b>: recording sample rate.</li>
      <li><b>Input channels</b>: mono or stereo recording, based on what the selected input device supports.</li>
      <li><b>Output channels</b>: mono or stereo preview output, based on what the selected output device supports.</li>
      <li><b>Input info / Output info</b>: shows backend, host API, max channels, default rate, and whether the device is the default.</li>
      <li><b>Detected APIs</b>: lists the host APIs currently visible to the app, such as MME, WASAPI, WDM-KS, or ASIO.</li>
      <li><b>Driver status</b>: explains which routing backend is active, whether ASIO is visible, and how many input/output devices the app can currently use.</li>
      <li><b>After record</b>: automatically loads the new take into the app after recording.</li>
      <li><b>Input level / Peak / Stereo meter</b>: live recording metering.</li>
      <li><b>Recent takes</b>: quickly reload or manage recordings made in the app.</li>
    </ul>

    <p>
      Project files are separate from the normal app-state restore file. Use them when you want to intentionally save and reopen a named work session,
      including the selected source, region, stretch, effects, A/B slots, and render queue.
    </p>

    <p>
      At startup, the app now shows a rotating splash screen using one of the main FinDus cat icon variants, with a short loading bar and a small animated forehead loader while the workspace is being prepared.
      The loader style also changes with the art variant: <b>Classic</b> uses a spiral, <b>Midnight</b> uses a neon ring,
      <b>Stamp</b> uses a pulsing emblem glow, and <b>Orbit</b> uses a moving orbit arc.
    </p>

    <p>
      ASIO devices only appear if the driver is installed and PortAudio can see it. Tools like ASIO4ALL are not bundled with the app.
      Port and channel visibility depends on what the driver exposes, so some hardware may only appear as one stereo device.
      The app detects what is usable right now, not every driver file installed in Windows.
    </p>

    <p>
      In practice, that means a driver can be installed on the machine but still not show up here if Windows, the driver,
      or PortAudio does not expose it as a usable audio endpoint at runtime. The diagnostics area is meant to show what the
      app can actually route through right now.
    </p>

    <h3>Stretch Tab</h3>
    <ul>
      <li><b>Subtabs</b>: use <b>Region</b> for timing, <b>Compare</b> for A/B slots, and <b>History</b> for recent previews.</li>
      <li><b>Region</b>: keeps stretch factor, preview start, preview length, quality, and loop crossfade together.</li>
      <li><b>Compare</b>: keeps slot A/B capture, load, swap, and toggle actions together.</li>
      <li><b>History</b>: keeps recent preview states, replay, and history cleanup together.</li>
      <li><b>Stretch factor</b>: how much longer the source becomes.</li>
      <li><b>Preview start</b>: where the selected region begins. This stays synced with the waveform selection.</li>
      <li><b>Preview length</b>: how much source audio is stretched. This also stays synced with the waveform selection.</li>
      <li><b>Quality</b>: larger windows sound smoother but take longer.</li>
      <li><b>Loop crossfade</b>: sets how much extra fade-overlap is added at loop restarts. This changes preview playback only and does not force a rerender.</li>
      <li><b>A/B Compare</b>: store the current region, stretch, quality, and effects into slot A or B and jump back to them instantly.</li>
      <li><b>Toggle A/B</b>: switches between slot A and slot B, then immediately auditions the target slot.</li>
      <li><b>Store Active</b>: overwrites whichever compare slot is currently active, or slot A if you are in a custom mix.</li>
      <li><b>Swap A/B</b>: exchanges the contents of slots A and B without changing the current rendered audio until the next preview.</li>
      <li><b>Preview History</b>: keeps a short session-local list of recently rendered preview states so you can load or replay them without rebuilding them manually.</li>
    </ul>

    <h3>Preview Workflow</h3>
    <ul>
      <li><b>Play Preview</b>: auditions the currently selected region with the current stretch and effects.</li>
      <li><b>Replay Last Preview</b>: plays the latest cached preview again without forcing a new render.</li>
      <li><b>Cached preview reuse</b>: if you press preview again without changing region or audio settings, the app reuses the last processed preview instead of rendering it again.</li>
      <li><b>Restart Preview</b>: while preview is playing, the play button changes to show that pressing it will restart the current preview.</li>
      <li><b>Stop</b>: immediately stops playback and clears the moving playhead.</li>
      <li><b>Preview status label</b>: explains whether the app is idle, rendering, cached and ready, playing, looping, stopped, or waiting for a rerender after a real audio change.</li>
      <li><b>Selection changes</b>: changing the region or sound settings invalidates the cache, but non-audio view changes like waveform zoom do not.</li>
    </ul>

    <h3>Effects Tab</h3>
    <ul>
      <li><b>Single view layout</b>: all effects now stay in one continuous panel so you can see the whole chain without changing sub-tabs.</li>
      <li><b>Shape section</b>: keeps input trim, filter, drive, stereo width, wet/dry, limiter, freeze, and reverse together.</li>
      <li><b>Motion section</b>: keeps chorus, texture, motion, pitch drift, bloom, granular smear, and auto-pan together.</li>
      <li><b>Space section</b>: keeps reverb, shimmer, and delay together.</li>
      <li><b>Macros section</b>: keeps Random, Dark, Bright, Huge, Weird, Harmonize, Bypass All Effects, and Reset Effects together.</li>
      <li><b>Input trim</b>: boosts or cuts the source before stretching and effects, which is useful for very weak or very hot material.</li>
      <li><b>Filter mode</b>: turns tonal filtering off or switches between low-pass, high-pass, and band-pass.</li>
      <li><b>Filter freq</b>: cutoff or center frequency for the selected filter mode.</li>
      <li><b>On toggles</b>: each major effect row can be turned on or off without losing its slider position, which makes A/B comparison and troubleshooting much easier.</li>
      <li><b>Drive</b>: soft saturation that adds density and color.</li>
      <li><b>Chorus</b>: subtle detune and modulation for width and movement.</li>
      <li><b>Texture</b>: adds dusty, broken, foggy texture with a more fragmented feel.</li>
      <li><b>Motion</b>: adds slow stereo movement and drifting life to long sounds.</li>
      <li><b>Pitch Drift</b>: adds slight analog-style instability and soft pitch wandering.</li>
      <li><b>Bloom</b>: expands the sound into a larger, softer ambient cloud.</li>
      <li><b>Granular smear</b>: breaks the sound into drifting micro-textures.</li>
      <li><b>Reverb</b>: adds space and tail.</li>
      <li><b>Shimmer</b>: blends in a pitched-up ambient layer.</li>
      <li><b>Delay</b>: adds repeating echoes.</li>
      <li><b>Auto-pan</b>: slowly moves the sound in the stereo field.</li>
      <li><b>Stereo width</b>: narrows or widens the stereo image.</li>
      <li><b>Wet/Dry</b>: blends original source with the effected sound.</li>
      <li><b>Safety limiter</b>: adds a soft output ceiling to catch aggressive peaks from extreme combinations.</li>
      <li><b>Freeze selection</b>: sustains the selected region into a continuous drone source.</li>
      <li><b>Reverse wet signal</b>: reverses the processed result before the final mix.</li>
      <li><b>Bypass All Effects</b>: temporarily forces a dry chain for instant A/B against the processed sound.</li>
      <li><b>Reset Effects</b>: returns the entire effects area to a neutral dry state without changing stretch or source selection.</li>
      <li><b>Random</b>: broad musical randomization across the full effect stack.</li>
      <li><b>Dark / Bright / Huge / Weird</b>: guided random starting points that push the sound in a more specific direction before you fine-tune it.</li>
      <li><b>Harmonize</b>: applies a choir-like stack built around chorus, shimmer, bloom, and width.</li>
    </ul>

    <h3>Presets Tab</h3>
    <ul>
      <li><b>Subtabs</b>: use <b>Library</b> for browsing, <b>Manage</b> for metadata and saving, and <b>Batch</b> for queued preset exports.</li>
      <li><b>Library</b>: keeps preset search, tag filters, favorites-only filtering, and the main preset picker together.</li>
      <li><b>Manage</b>: keeps favorite toggling, tags, and preset save/update/rename/duplicate/delete actions together.</li>
      <li><b>Batch</b>: keeps the filtered batch list and queue actions together for multi-preset exports.</li>
      <li><b>Preset</b>: loads a factory or user preset.</li>
      <li><b>Filter</b>: search by preset name or tags, narrow by one tag, or show favorites only.</li>
      <li><b>Favorite</b>: stars the selected preset so it is easier to find later. Factory presets can be favorited even though they are still read-only.</li>
      <li><b>Tags</b>: user presets can store lightweight comma-separated tags such as dark, choir, huge, tape, weird, or ambient.</li>
      <li><b>Batch presets</b>: shows the filtered preset list again as a multi-select batch render source.</li>
      <li><b>Select Filtered</b>: selects all currently visible filtered presets at once.</li>
      <li><b>Queue Selected Batch</b>: adds one queued render job per selected preset, using safe output filenames based on the preset names.</li>
      <li><b>Save New</b>: saves current settings as a new user preset.</li>
      <li><b>Update Preset</b>: overwrites the selected user preset with current settings.</li>
      <li><b>Rename</b>: renames the selected user preset.</li>
      <li><b>Duplicate</b>: copies a preset to a new user preset.</li>
      <li><b>Delete</b>: removes a user preset from disk.</li>
    </ul>

    <h3>Preset Ideas</h3>
    <p>
      Use bright chorus and shimmer for choir-like pads, granular smear plus band-pass for dusty textures,
      and drive plus low-pass for darker tape-style drones. The guided random buttons are a fast way to find a strong starting point before saving your own preset.
    </p>

    <h3>Shortcuts</h3>
    <ul>
      <li><b>Ctrl+Z</b>: undo</li>
      <li><b>Ctrl+Y / Ctrl+Shift+Z</b>: redo</li>
      <li><b>Ctrl+O</b>: open source audio</li>
      <li><b>Ctrl+Shift+O</b>: open project</li>
      <li><b>Ctrl+R</b>: start recording</li>
      <li><b>Ctrl+E</b>: render WAV</li>
      <li><b>Ctrl+Shift+S</b>: save project</li>
      <li><b>Alt+X</b>: toggle A/B</li>
      <li><b>Space</b>: preview</li>
      <li><b>Esc</b>: stop</li>
<li><b>Z</b>: fit selection in view</li>
<li><b>F</b>: fit the full waveform</li>
      <li><b>R</b>: reset selection</li>
      <li><b>Ctrl+1..5</b>: switch tabs</li>
      <li><b>F1</b>: open this help view</li>
    </ul>

    <h3>Releases And Install Files</h3>
    <p>
      If you use the Windows launcher <b>start.bat</b>, there are a few release options that are helpful to know:
    </p>
    <ul>
      <li><b>Build Windows .exe</b>: creates the portable app folder in <b>dist/findus_stretching</b>.</li>
      <li><b>Build Setup.exe</b>: creates a normal Windows installer in <b>dist/installer</b>.</li>
      <li><b>Full release</b>: makes a normal new release. It raises the last version number, runs tests, builds the app, builds the installer, and creates a zip.</li>
      <li><b>Minor release</b>: use this when the app got a bigger new feature. It raises the middle version number before doing the same full release flow.</li>
      <li><b>Clean build artifacts</b>: removes generated build folders so you can build again from a clean state.</li>
    </ul>

    <h3>Version Numbers In Simple Terms</h3>
    <ul>
      <li><b>Patch release</b>: small fixes or polish. Example: <b>0.1.1</b> becomes <b>0.1.2</b>.</li>
      <li><b>Minor release</b>: bigger feature update. Example: <b>0.1.1</b> becomes <b>0.2.0</b>.</li>
    </ul>

    <h3>Which File Should You Share?</h3>
    <ul>
      <li><b>Setup.exe</b>: best for most people. It installs the app like a normal Windows program.</li>
      <li><b>ZIP</b>: good if someone just wants to unpack and test without installing.</li>
      <li><b>The whole project folder</b>: usually not needed for testers, only for development.</li>
    </ul>

    <!-- CHANGELOG_START -->
    <!-- CHANGELOG_END -->
    """
