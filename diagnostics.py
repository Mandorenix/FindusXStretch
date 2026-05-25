from __future__ import annotations

import json
import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_PATH = PROJECT_ROOT / "diagnostics_report.txt"


def _line(lines: list[str], text: str = "") -> None:
    lines.append(text)


def _section(lines: list[str], title: str) -> None:
    _line(lines)
    _line(lines, f"=== {title} ===")


def _add_kv(lines: list[str], key: str, value: object) -> None:
    _line(lines, f"{key}: {value}")


def _safe_json(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"unreadable ({exc})"
    return json.dumps(data, indent=2, ensure_ascii=True)


def _run_import_diagnostics(lines: list[str]) -> None:
    _section(lines, "Imports")
    modules = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("soundfile", "soundfile"),
        ("PySide6", "PySide6"),
        ("pytest", "pytest"),
        ("pyqtgraph", "pyqtgraph"),
        ("PyInstaller", "PyInstaller"),
        ("sounddevice", "sounddevice"),
    ]
    for label, module_name in modules:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "unknown")
            _add_kv(lines, label, f"OK ({version})")
        except Exception as exc:
            _add_kv(lines, label, f"FAIL ({exc})")


def _run_audio_diagnostics(lines: list[str]) -> None:
    _section(lines, "Audio")
    try:
        from paulstretch_light.recording import list_audio_routing, portaudio_is_available

        _add_kv(lines, "portaudio_available", portaudio_is_available())
        for requested in ("auto", "portaudio", "qt"):
            try:
                snapshot = list_audio_routing(requested_backend=requested)
                _add_kv(lines, f"{requested}_active_backend", snapshot.active_backend)
                _add_kv(lines, f"{requested}_host_apis", ", ".join(snapshot.host_api_names) or "(none)")
                input_labels = [device.label for device in snapshot.input_devices[:5]]
                output_labels = [device.label for device in snapshot.output_devices[:5]]
                _add_kv(lines, f"{requested}_inputs", " | ".join(input_labels) or "(none)")
                _add_kv(lines, f"{requested}_outputs", " | ".join(output_labels) or "(none)")
            except Exception as exc:
                _add_kv(lines, f"{requested}_snapshot", f"FAIL ({exc})")
    except Exception:
        _line(lines, traceback.format_exc().rstrip())


def _run_gui_diagnostics(lines: list[str]) -> None:
    _section(lines, "GUI")
    previous_platform = os.environ.get("QT_QPA_PLATFORM")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = None
    window = None
    try:
        from PySide6.QtWidgets import QApplication
        from paulstretch_light.gui import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        _add_kv(lines, "mainwindow_init", "OK")
        _add_kv(lines, "workspace_tabs", window.workspace_tabs.count())
        _add_kv(lines, "current_tab", window.workspace_tabs.tabText(window.workspace_tabs.currentIndex()))
        _add_kv(lines, "theme", getattr(window, "current_theme_name", "unknown"))
        _add_kv(lines, "ui_scale_percent", getattr(window, "current_ui_scale_percent", "unknown"))
    except Exception:
        _line(lines, traceback.format_exc().rstrip())
    finally:
        if window is not None:
            window.close()
        if app is not None:
            app.quit()
        if previous_platform is None:
            os.environ.pop("QT_QPA_PLATFORM", None)
        else:
            os.environ["QT_QPA_PLATFORM"] = previous_platform


def _run_state_diagnostics(lines: list[str]) -> None:
    _section(lines, "Project State")
    try:
        from paulstretch_light.preset_library import APP_STATE_PATH, USER_PRESETS_PATH
    except Exception:
        _line(lines, traceback.format_exc().rstrip())
        return

    _add_kv(lines, "project_root", PROJECT_ROOT)
    _add_kv(lines, "state_path", APP_STATE_PATH)
    _add_kv(lines, "presets_path", USER_PRESETS_PATH)
    _add_kv(lines, "dist_exe_exists", (PROJECT_ROOT / "dist" / "findus_stretching" / "findus_stretching.exe").exists())
    _add_kv(lines, "installer_exists", any((PROJECT_ROOT / "dist" / "installer").glob("*.exe")))

    _line(lines)
    _line(lines, "state_file_contents:")
    _line(lines, _safe_json(APP_STATE_PATH))

    _line(lines)
    _line(lines, "preset_file_contents:")
    _line(lines, _safe_json(USER_PRESETS_PATH))


def build_report() -> str:
    lines: list[str] = []
    _line(lines, "FINDUS>x<STRETCHING Diagnostics Report")
    _line(lines, f"Generated: {datetime.now().isoformat(timespec='seconds')}")

    _section(lines, "System")
    _add_kv(lines, "python", sys.version.replace("\n", " "))
    _add_kv(lines, "executable", sys.executable)
    _add_kv(lines, "platform", platform.platform())
    _add_kv(lines, "cwd", Path.cwd())
    _add_kv(lines, "project_root", PROJECT_ROOT)
    _add_kv(lines, "qt_qpa_platform", os.environ.get("QT_QPA_PLATFORM", "(not set)"))

    _run_import_diagnostics(lines)
    _run_state_diagnostics(lines)
    _run_audio_diagnostics(lines)
    _run_gui_diagnostics(lines)

    _section(lines, "Done")
    _line(lines, f"Copy the contents of {REPORT_PATH.name} into the chat when something breaks.")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Diagnostics written to: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
