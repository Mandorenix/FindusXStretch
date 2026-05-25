from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys

import numpy as np
from PySide6.QtCore import QObject, QIODevice, Signal
from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices

try:
    import soundfile as sf
except ImportError:  # pragma: no cover
    sf = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None


AUDIO_BACKEND_AUTO = "auto"
AUDIO_BACKEND_PORTAUDIO = "portaudio"
AUDIO_BACKEND_QT = "qt"
QT_HOST_API_NAME = "Qt Multimedia"


@dataclass(frozen=True)
class AudioDeviceInfo:
    backend: str
    host_api_name: str
    device_id: str
    label: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: int
    is_default_input: bool = False
    is_default_output: bool = False


@dataclass(frozen=True)
class AudioRoutingSnapshot:
    requested_backend: str
    active_backend: str
    host_api_names: list[str]
    input_devices: list[AudioDeviceInfo]
    output_devices: list[AudioDeviceInfo]


@dataclass(frozen=True)
class RecordingConfig:
    output_path: str
    device_id: str = ""
    sample_rate: int = 48000
    channels: int = 1
    auto_load: bool = True
    audio_backend: str = AUDIO_BACKEND_AUTO
    host_api_name: str = ""


@dataclass(frozen=True)
class RecordingResult:
    output_path: str
    sample_rate: int
    channels: int
    frames: int
    duration_seconds: float
    auto_load: bool


@dataclass(frozen=True)
class RecentTake:
    path: str
    duration_seconds: float
    sample_rate: int
    timestamp: str


def list_input_devices() -> list[tuple[str, str]]:
    return [(device.device_id, device.label) for device in list_audio_routing().input_devices]


def list_output_devices() -> list[tuple[str, str]]:
    return [(device.device_id, device.label) for device in list_audio_routing().output_devices]


def list_audio_backends() -> list[tuple[str, str]]:
    return [
        (AUDIO_BACKEND_AUTO, "Auto"),
        (AUDIO_BACKEND_PORTAUDIO, "PortAudio"),
        (AUDIO_BACKEND_QT, "Qt fallback"),
    ]


def resolve_audio_backend(requested_backend: str) -> str:
    normalized = (requested_backend or AUDIO_BACKEND_AUTO).strip().lower()
    if normalized == AUDIO_BACKEND_PORTAUDIO:
        return AUDIO_BACKEND_PORTAUDIO if portaudio_is_available() else AUDIO_BACKEND_QT
    if normalized == AUDIO_BACKEND_QT:
        return AUDIO_BACKEND_QT
    if sys.platform.startswith("win") and portaudio_is_available():
        return AUDIO_BACKEND_PORTAUDIO
    return AUDIO_BACKEND_QT


def portaudio_is_available() -> bool:
    if sd is None:
        return False
    try:
        sd.query_devices()
    except Exception:
        return False
    return True


def list_audio_routing(requested_backend: str = AUDIO_BACKEND_AUTO, host_api_name: str = "") -> AudioRoutingSnapshot:
    active_backend = resolve_audio_backend(requested_backend)
    if active_backend == AUDIO_BACKEND_PORTAUDIO:
        try:
            return _portaudio_routing_snapshot(requested_backend, host_api_name)
        except Exception:
            if requested_backend == AUDIO_BACKEND_PORTAUDIO:
                return _qt_routing_snapshot(requested_backend)
            return _qt_routing_snapshot(requested_backend)
    return _qt_routing_snapshot(requested_backend)


def input_device_details(device_id: str) -> str:
    return device_details(device_id=device_id, direction="input")


def output_device_details(
    device_id: str,
    requested_backend: str = AUDIO_BACKEND_AUTO,
    host_api_name: str = "",
) -> str:
    return device_details(
        device_id=device_id,
        direction="output",
        requested_backend=requested_backend,
        host_api_name=host_api_name,
    )


def device_details(
    *,
    device_id: str = "",
    direction: str,
    requested_backend: str = AUDIO_BACKEND_AUTO,
    host_api_name: str = "",
) -> str:
    snapshot = list_audio_routing(requested_backend=requested_backend, host_api_name=host_api_name)
    devices = snapshot.input_devices if direction == "input" else snapshot.output_devices
    device = next((item for item in devices if item.device_id == device_id), devices[0] if devices else None)
    if device is None:
        return f"No {direction} device available"
    io_channels = device.max_input_channels if direction == "input" else device.max_output_channels
    direction_defaults = "input" if direction == "input" else "output"
    default_flag = getattr(device, f"is_default_{direction_defaults}", False)
    default_text = " | Default" if default_flag else ""
    return (
        f"{device.label} | Backend: {device.backend} | Host API: {device.host_api_name} | "
        f"Max {direction} channels: {io_channels} | Default rate: {device.default_sample_rate} Hz{default_text}"
    )


def channel_options(device_id: str, direction: str, requested_backend: str = AUDIO_BACKEND_AUTO, host_api_name: str = "") -> list[int]:
    snapshot = list_audio_routing(requested_backend=requested_backend, host_api_name=host_api_name)
    devices = snapshot.input_devices if direction == "input" else snapshot.output_devices
    device = next((item for item in devices if item.device_id == device_id), None)
    if device is None:
        return [1]
    max_channels = device.max_input_channels if direction == "input" else device.max_output_channels
    max_channels = max(1, min(int(max_channels), 2))
    return list(range(1, max_channels + 1))


def find_audio_device(
    device_id: str,
    *,
    direction: str,
    requested_backend: str = AUDIO_BACKEND_AUTO,
    host_api_name: str = "",
) -> AudioDeviceInfo | None:
    snapshot = list_audio_routing(requested_backend=requested_backend, host_api_name=host_api_name)
    devices = snapshot.input_devices if direction == "input" else snapshot.output_devices
    if device_id:
        for device in devices:
            if device.device_id == device_id:
                return device
    default_attr = "is_default_input" if direction == "input" else "is_default_output"
    for device in devices:
        if getattr(device, default_attr):
            return device
    return devices[0] if devices else None


def resolve_qt_output_device(device_id: str):
    return _resolve_output_device(device_id)


def suggested_recording_path(base_dir: str | Path, now: datetime | None = None) -> str:
    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    path = Path(base_dir) / f"findus_recording_{timestamp}.wav"
    return str(next_available_recording_path(path))


def next_available_recording_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix or ".wav"
    parent = candidate.parent
    for index in range(1, 1000):
        numbered = parent / f"{stem}_{index:02d}{suffix}"
        if not numbered.exists():
            return numbered
    raise RuntimeError("Could not find a free recording filename.")


def recording_format(sample_rate: int = 48000, channels: int = 1) -> QAudioFormat:
    fmt = QAudioFormat()
    fmt.setSampleRate(sample_rate)
    fmt.setChannelCount(max(1, channels))
    fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    return fmt


def pcm16_bytes_to_float32(raw_bytes: bytes, channels: int) -> np.ndarray:
    if channels <= 0:
        raise ValueError("Channel count must be positive.")
    sample_count = len(raw_bytes) // 2
    if sample_count == 0:
        return np.zeros((0, channels), dtype=np.float32)
    trimmed = raw_bytes[: sample_count * 2]
    samples = np.frombuffer(trimmed, dtype="<i2").astype(np.float32) / 32768.0
    if channels == 1:
        return samples.reshape(-1, 1)
    frame_count = samples.size // channels
    if frame_count == 0:
        return np.zeros((0, channels), dtype=np.float32)
    return samples[: frame_count * channels].reshape(frame_count, channels)


def peak_level_for_pcm16(raw_bytes: bytes, channels: int) -> float:
    audio = pcm16_bytes_to_float32(raw_bytes, channels=channels)
    if audio.size == 0:
        return 0.0
    return float(np.max(np.abs(audio)))


def peak_levels_for_pcm16(raw_bytes: bytes, channels: int) -> list[float]:
    audio = pcm16_bytes_to_float32(raw_bytes, channels=channels)
    if audio.size == 0:
        return [0.0] * max(1, channels)
    return [float(np.max(np.abs(audio[:, index]))) for index in range(audio.shape[1])]


def write_recording_wav(raw_bytes: bytes, config: RecordingConfig) -> RecordingResult:
    if sf is None:
        raise RuntimeError("Missing dependency: soundfile. Install requirements before recording.")
    if not raw_bytes:
        raise ValueError("No recorded audio was captured.")

    output_path = Path(config.output_path)
    if output_path.suffix.lower() != ".wav":
        raise ValueError("Recording output file must use the .wav extension.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    audio = pcm16_bytes_to_float32(raw_bytes, channels=config.channels)
    if audio.shape[0] == 0:
        raise ValueError("No recorded audio frames were captured.")

    sf.write(
        str(output_path),
        audio,
        config.sample_rate,
        subtype="FLOAT",
        format="WAV",
    )
    return RecordingResult(
        output_path=str(output_path),
        sample_rate=config.sample_rate,
        channels=config.channels,
        frames=audio.shape[0],
        duration_seconds=audio.shape[0] / max(1, config.sample_rate),
        auto_load=config.auto_load,
    )


def write_recording_array_wav(audio: np.ndarray, config: RecordingConfig) -> RecordingResult:
    if sf is None:
        raise RuntimeError("Missing dependency: soundfile. Install requirements before recording.")
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)
    if audio.shape[0] == 0:
        raise ValueError("No recorded audio frames were captured.")
    output_path = Path(config.output_path)
    if output_path.suffix.lower() != ".wav":
        raise ValueError("Recording output file must use the .wav extension.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), audio, config.sample_rate, subtype="FLOAT", format="WAV")
    return RecordingResult(
        output_path=str(output_path),
        sample_rate=config.sample_rate,
        channels=audio.shape[1],
        frames=audio.shape[0],
        duration_seconds=audio.shape[0] / max(1, config.sample_rate),
        auto_load=config.auto_load,
    )


def recent_take_from_result(result: RecordingResult, now: datetime | None = None) -> RecentTake:
    return RecentTake(
        path=result.output_path,
        duration_seconds=result.duration_seconds,
        sample_rate=result.sample_rate,
        timestamp=(now or datetime.now()).isoformat(timespec="seconds"),
    )


def merge_recent_takes(
    recent_takes: list[RecentTake],
    new_take: RecentTake,
    *,
    max_items: int = 8,
) -> list[RecentTake]:
    merged = [new_take]
    for take in recent_takes:
        if Path(take.path) != Path(new_take.path):
            merged.append(take)
    return merged[:max_items]


def filter_existing_recent_takes(recent_takes: list[RecentTake]) -> list[RecentTake]:
    return [take for take in recent_takes if Path(take.path).exists()]


def remove_recent_take(recent_takes: list[RecentTake], path: str | Path) -> list[RecentTake]:
    target = Path(path)
    return [take for take in recent_takes if Path(take.path) != target]


def rename_take_file(path: str | Path, new_stem: str) -> Path:
    source = Path(path)
    normalized_stem = new_stem.strip()
    if not normalized_stem:
        raise ValueError("Take name cannot be empty.")
    destination = source.with_name(f"{normalized_stem}{source.suffix}")
    if destination == source:
        return source
    if destination.exists():
        raise FileExistsError(f"Target file already exists: {destination}")
    source.rename(destination)
    return destination


class RecordingController(QObject):
    level_changed = Signal(float)
    channel_levels_changed = Signal(object)
    status_changed = Signal(str)
    recording_started = Signal(str)
    recording_stopped = Signal(object)
    recording_failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.audio_source: QAudioSource | None = None
        self.input_device: QIODevice | None = None
        self.config: RecordingConfig | None = None
        self._raw_bytes = bytearray()
        self._sd_stream = None
        self._sd_chunks: list[np.ndarray] = []

    def is_recording(self) -> bool:
        return (self.audio_source is not None and self.input_device is not None) or self._sd_stream is not None

    def start_recording(self, config: RecordingConfig) -> None:
        if self.is_recording():
            raise RuntimeError("A recording is already in progress.")
        if sf is None:
            raise RuntimeError("Missing dependency: soundfile. Install requirements before recording.")
        requested_backend = config.audio_backend or AUDIO_BACKEND_AUTO
        if resolve_audio_backend(requested_backend) == AUDIO_BACKEND_PORTAUDIO:
            try:
                self._start_recording_sounddevice(config)
                return
            except Exception:
                if requested_backend == AUDIO_BACKEND_PORTAUDIO:
                    raise
        self._start_recording_qt(config)

    def stop_recording(self) -> None:
        if not self.is_recording():
            return
        if self._sd_stream is not None:
            self._stop_recording_sounddevice()
            return
        assert self.input_device is not None
        assert self.audio_source is not None
        assert self.config is not None

        self._drain_input()
        try:
            self.input_device.readyRead.disconnect(self._drain_input)
        except (RuntimeError, TypeError):
            pass
        self.audio_source.stop()
        self.input_device = None
        self.audio_source.deleteLater()
        self.audio_source = None

        try:
            result = write_recording_wav(bytes(self._raw_bytes), self.config)
        except Exception as exc:
            self.recording_failed.emit(str(exc))
        else:
            self.level_changed.emit(0.0)
            self.status_changed.emit(f"Recording saved: {Path(result.output_path).name}")
            self.recording_stopped.emit(result)
        finally:
            self._raw_bytes = bytearray()
            self.config = None

    def cancel_recording(self) -> None:
        if not self.is_recording():
            return
        if self._sd_stream is not None:
            self._cancel_recording_sounddevice()
            return
        assert self.input_device is not None
        assert self.audio_source is not None
        try:
            self.input_device.readyRead.disconnect(self._drain_input)
        except (RuntimeError, TypeError):
            pass
        self.audio_source.stop()
        self.input_device = None
        self.audio_source.deleteLater()
        self.audio_source = None
        self._raw_bytes = bytearray()
        self.config = None
        self.level_changed.emit(0.0)
        self.status_changed.emit("Recording cancelled")

    def _drain_input(self) -> None:
        if self.input_device is None or self.config is None:
            return
        chunk = bytes(self.input_device.readAll().data())
        if not chunk:
            return
        self._raw_bytes.extend(chunk)
        self.level_changed.emit(peak_level_for_pcm16(chunk, channels=self.config.channels))
        self.channel_levels_changed.emit(peak_levels_for_pcm16(chunk, channels=self.config.channels))

    def _start_recording_qt(self, config: RecordingConfig) -> None:
        device = _resolve_input_device(config.device_id)
        if device is None:
            raise RuntimeError("No audio input devices are available.")
        fmt = _resolve_supported_format(device, config)
        self.audio_source = QAudioSource(device, fmt, self)
        self.input_device = self.audio_source.start()
        if self.input_device is None:
            self.audio_source.deleteLater()
            self.audio_source = None
            raise RuntimeError("Could not start audio capture from the selected input device.")
        self.config = RecordingConfig(
            output_path=config.output_path,
            device_id=_normalize_qt_device_id(_device_id(device)),
            sample_rate=fmt.sampleRate(),
            channels=fmt.channelCount(),
            auto_load=config.auto_load,
            audio_backend=AUDIO_BACKEND_QT,
            host_api_name=QT_HOST_API_NAME,
        )
        self._raw_bytes = bytearray()
        self.input_device.readyRead.connect(self._drain_input)
        self.status_changed.emit(f"Recording from {device.description()} via Qt fallback")
        self.recording_started.emit(device.description())

    def _start_recording_sounddevice(self, config: RecordingConfig) -> None:
        if sd is None:
            raise RuntimeError("sounddevice is not available.")
        device_info = _find_portaudio_device(config.device_id, direction="input", host_api_name=config.host_api_name)
        if device_info is None:
            raise RuntimeError("The selected PortAudio input device is not available.")
        channels = min(max(1, int(config.channels)), max(1, device_info.max_input_channels))
        self.config = RecordingConfig(
            output_path=config.output_path,
            device_id=device_info.device_id,
            sample_rate=int(config.sample_rate),
            channels=channels,
            auto_load=config.auto_load,
            audio_backend=AUDIO_BACKEND_PORTAUDIO,
            host_api_name=device_info.host_api_name,
        )
        self._sd_chunks = []
        self._sd_stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            device=_portaudio_index_from_device_id(device_info.device_id),
            channels=channels,
            dtype="float32",
            callback=self._on_sd_input,
        )
        self._sd_stream.start()
        self.status_changed.emit(f"Recording from {device_info.label} via {device_info.host_api_name}")
        self.recording_started.emit(device_info.label)

    def _stop_recording_sounddevice(self) -> None:
        assert self._sd_stream is not None
        assert self.config is not None
        stream = self._sd_stream
        self._sd_stream = None
        stream.stop()
        stream.close()
        try:
            audio = np.concatenate(self._sd_chunks, axis=0) if self._sd_chunks else np.zeros((0, self.config.channels), dtype=np.float32)
            result = write_recording_array_wav(audio, self.config)
        except Exception as exc:
            self.recording_failed.emit(str(exc))
        else:
            self.level_changed.emit(0.0)
            self.status_changed.emit(f"Recording saved: {Path(result.output_path).name}")
            self.recording_stopped.emit(result)
        finally:
            self._sd_chunks = []
            self.config = None

    def _cancel_recording_sounddevice(self) -> None:
        if self._sd_stream is None:
            return
        stream = self._sd_stream
        self._sd_stream = None
        stream.stop()
        stream.close()
        self._sd_chunks = []
        self.config = None
        self.level_changed.emit(0.0)
        self.status_changed.emit("Recording cancelled")

    def _on_sd_input(self, indata, frames, time, status) -> None:  # noqa: ANN001
        if self.config is None:
            return
        audio = np.asarray(indata, dtype=np.float32).copy()
        self._sd_chunks.append(audio)
        if audio.size == 0:
            return
        peak = float(np.max(np.abs(audio)))
        channel_peaks = [float(np.max(np.abs(audio[:, index]))) for index in range(audio.shape[1])]
        self.level_changed.emit(peak)
        self.channel_levels_changed.emit(channel_peaks)


def _resolve_input_device(device_id: str):
    devices = QMediaDevices.audioInputs()
    if not devices:
        return None
    normalized_id = _strip_device_prefix(device_id, "qt")
    if device_id:
        for device in devices:
            if _device_id(device) == normalized_id or _normalize_qt_device_id(_device_id(device)) == device_id:
                return device
    return QMediaDevices.defaultAudioInput() or devices[0]


def _resolve_output_device(device_id: str):
    devices = QMediaDevices.audioOutputs()
    if not devices:
        return None
    normalized_id = _strip_device_prefix(device_id, "qt")
    if normalized_id:
        for device in devices:
            if _device_id(device) == normalized_id:
                return device
    return QMediaDevices.defaultAudioOutput() or devices[0]


def _resolve_supported_format(device, config: RecordingConfig) -> QAudioFormat:
    desired = recording_format(sample_rate=config.sample_rate, channels=config.channels)
    if device.isFormatSupported(desired):
        return desired
    preferred = device.preferredFormat()
    if preferred.sampleFormat() != QAudioFormat.SampleFormat.Int16:
        raise RuntimeError("The selected input device does not support 16-bit PCM recording.")
    return preferred


def _device_id(device) -> str:
    raw_id = bytes(device.id())
    if not raw_id:
        return device.description()
    return raw_id.decode("utf-8", errors="ignore")


def _normalize_qt_device_id(raw_id: str) -> str:
    return f"qt:{raw_id}"


def _normalize_portaudio_device_id(index: int) -> str:
    return f"pa:{index}"


def _strip_device_prefix(device_id: str, prefix: str) -> str:
    if device_id.startswith(f"{prefix}:"):
        return device_id.split(":", 1)[1]
    return device_id


def _qt_routing_snapshot(requested_backend: str) -> AudioRoutingSnapshot:
    input_devices = []
    output_devices = []
    default_input = QMediaDevices.defaultAudioInput()
    default_output = QMediaDevices.defaultAudioOutput()
    for device in QMediaDevices.audioInputs():
        preferred = device.preferredFormat()
        input_devices.append(
            AudioDeviceInfo(
                backend=AUDIO_BACKEND_QT,
                host_api_name=QT_HOST_API_NAME,
                device_id=_normalize_qt_device_id(_device_id(device)),
                label=device.description(),
                max_input_channels=max(1, preferred.channelCount()),
                max_output_channels=0,
                default_sample_rate=max(8000, preferred.sampleRate()),
                is_default_input=default_input is not None and _device_id(default_input) == _device_id(device),
            )
        )
    for device in QMediaDevices.audioOutputs():
        preferred = device.preferredFormat()
        output_devices.append(
            AudioDeviceInfo(
                backend=AUDIO_BACKEND_QT,
                host_api_name=QT_HOST_API_NAME,
                device_id=_normalize_qt_device_id(_device_id(device)),
                label=device.description(),
                max_input_channels=0,
                max_output_channels=max(1, preferred.channelCount()),
                default_sample_rate=max(8000, preferred.sampleRate()),
                is_default_output=default_output is not None and _device_id(default_output) == _device_id(device),
            )
        )
    return AudioRoutingSnapshot(
        requested_backend=requested_backend,
        active_backend=AUDIO_BACKEND_QT,
        host_api_names=[QT_HOST_API_NAME],
        input_devices=input_devices,
        output_devices=output_devices,
    )


def _portaudio_routing_snapshot(requested_backend: str, host_api_name: str) -> AudioRoutingSnapshot:
    assert sd is not None
    host_apis = sd.query_hostapis()
    devices = sd.query_devices()
    host_names = [str(api["name"]) for api in host_apis]
    selected_host = host_api_name if host_api_name in host_names else ""
    input_devices: list[AudioDeviceInfo] = []
    output_devices: list[AudioDeviceInfo] = []
    for index, device in enumerate(devices):
        api_name = str(host_apis[device["hostapi"]]["name"])
        if selected_host and api_name != selected_host:
            continue
        label = str(device["name"])
        sample_rate = int(round(float(device.get("default_samplerate", 48000) or 48000)))
        info = AudioDeviceInfo(
            backend=AUDIO_BACKEND_PORTAUDIO,
            host_api_name=api_name,
            device_id=_normalize_portaudio_device_id(index),
            label=label,
            max_input_channels=int(device.get("max_input_channels", 0)),
            max_output_channels=int(device.get("max_output_channels", 0)),
            default_sample_rate=sample_rate,
            is_default_input=host_apis[device["hostapi"]].get("default_input_device") == index,
            is_default_output=host_apis[device["hostapi"]].get("default_output_device") == index,
        )
        if info.max_input_channels > 0:
            input_devices.append(info)
        if info.max_output_channels > 0:
            output_devices.append(info)
    return AudioRoutingSnapshot(
        requested_backend=requested_backend,
        active_backend=AUDIO_BACKEND_PORTAUDIO,
        host_api_names=host_names,
        input_devices=input_devices,
        output_devices=output_devices,
    )


def _find_portaudio_device(device_id: str, *, direction: str, host_api_name: str = "") -> AudioDeviceInfo | None:
    snapshot = _portaudio_routing_snapshot(AUDIO_BACKEND_PORTAUDIO, host_api_name)
    devices = snapshot.input_devices if direction == "input" else snapshot.output_devices
    if device_id:
        for device in devices:
            if device.device_id == device_id:
                return device
    for device in devices:
        if (direction == "input" and device.is_default_input) or (direction == "output" and device.is_default_output):
            return device
    return devices[0] if devices else None


def _portaudio_index_from_device_id(device_id: str) -> int:
    return int(_strip_device_prefix(device_id, "pa"))
