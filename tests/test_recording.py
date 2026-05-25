from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import soundfile as sf
import paulstretch_light.recording as recording_module

from paulstretch_light.recording import (
    AUDIO_BACKEND_AUTO,
    AUDIO_BACKEND_PORTAUDIO,
    AudioRoutingSnapshot,
    RecordingConfig,
    RecentTake,
    filter_existing_recent_takes,
    list_audio_routing,
    merge_recent_takes,
    next_available_recording_path,
    pcm16_bytes_to_float32,
    peak_level_for_pcm16,
    peak_levels_for_pcm16,
    recent_take_from_result,
    remove_recent_take,
    rename_take_file,
    suggested_recording_path,
    write_recording_wav,
)


def test_suggested_recording_path_uses_timestamp_and_wav_suffix(tmp_path: Path) -> None:
    path = suggested_recording_path(tmp_path, now=datetime(2026, 3, 12, 18, 30, 45))

    assert path.endswith("findus_recording_20260312_183045.wav")
    assert str(tmp_path) in path


def test_pcm16_bytes_to_float32_preserves_channel_shape() -> None:
    raw = np.array([0, 16384, -16384, 32767], dtype="<i2").tobytes()

    audio = pcm16_bytes_to_float32(raw, channels=2)

    assert audio.shape == (2, 2)
    assert np.isclose(audio[0, 1], 0.5, atol=1e-3)
    assert np.isclose(audio[1, 0], -0.5, atol=1e-3)


def test_peak_level_for_pcm16_returns_zero_for_empty_bytes() -> None:
    assert peak_level_for_pcm16(b"", channels=1) == 0.0


def test_peak_levels_for_pcm16_returns_per_channel_levels() -> None:
    raw = np.array([0, 2000, -10000, 4000], dtype="<i2").tobytes()

    peaks = peak_levels_for_pcm16(raw, channels=2)

    assert len(peaks) == 2
    assert peaks[0] > peaks[1]


def test_write_recording_wav_creates_float_wav_file(tmp_path: Path) -> None:
    samples = np.array([0, 12000, -12000, 3000], dtype="<i2").tobytes()
    output_path = tmp_path / "recording.wav"

    result = write_recording_wav(
        samples,
        RecordingConfig(output_path=str(output_path), sample_rate=24000, channels=1, auto_load=False),
    )

    rendered, sample_rate = sf.read(str(output_path), always_2d=True, dtype="float32")
    assert sample_rate == 24000
    assert rendered.shape == (4, 1)
    assert result.frames == 4
    assert not result.auto_load


def test_write_recording_wav_rejects_empty_audio(tmp_path: Path) -> None:
    output_path = tmp_path / "empty.wav"

    try:
        write_recording_wav(
            b"",
            RecordingConfig(output_path=str(output_path), sample_rate=24000, channels=1),
        )
    except ValueError as exc:
        assert "No recorded audio" in str(exc)
    else:
        raise AssertionError("Expected empty recording to fail.")


def test_next_available_recording_path_adds_number_when_file_exists(tmp_path: Path) -> None:
    first = tmp_path / "take.wav"
    first.write_bytes(b"existing")

    next_path = next_available_recording_path(first)

    assert next_path == tmp_path / "take_01.wav"


def test_recent_take_from_result_captures_metadata() -> None:
    take = recent_take_from_result(
        type("Result", (), {
            "output_path": "take.wav",
            "duration_seconds": 1.25,
            "sample_rate": 48000,
        })(),
        now=datetime(2026, 3, 12, 19, 10, 0),
    )

    assert take.path == "take.wav"
    assert take.duration_seconds == 1.25
    assert take.sample_rate == 48000
    assert take.timestamp == "2026-03-12T19:10:00"


def test_merge_recent_takes_puts_new_take_first_and_deduplicates() -> None:
    existing = [
        RecentTake(path="a.wav", duration_seconds=1.0, sample_rate=48000, timestamp="2026-03-12T19:00:00"),
        RecentTake(path="b.wav", duration_seconds=2.0, sample_rate=48000, timestamp="2026-03-12T19:01:00"),
    ]
    updated = merge_recent_takes(
        existing,
        RecentTake(path="a.wav", duration_seconds=1.5, sample_rate=44100, timestamp="2026-03-12T19:02:00"),
        max_items=8,
    )

    assert [take.path for take in updated] == ["a.wav", "b.wav"]
    assert updated[0].duration_seconds == 1.5
    assert updated[0].sample_rate == 44100


def test_filter_existing_recent_takes_removes_missing_files(tmp_path: Path) -> None:
    existing_path = tmp_path / "exists.wav"
    existing_path.write_bytes(b"ok")
    recent_takes = [
        RecentTake(path=str(existing_path), duration_seconds=1.0, sample_rate=48000, timestamp="2026-03-12T19:00:00"),
        RecentTake(path=str(tmp_path / "missing.wav"), duration_seconds=2.0, sample_rate=48000, timestamp="2026-03-12T19:01:00"),
    ]

    filtered = filter_existing_recent_takes(recent_takes)

    assert [take.path for take in filtered] == [str(existing_path)]


def test_remove_recent_take_drops_matching_path() -> None:
    recent_takes = [
        RecentTake(path="a.wav", duration_seconds=1.0, sample_rate=48000, timestamp="2026-03-12T19:00:00"),
        RecentTake(path="b.wav", duration_seconds=2.0, sample_rate=48000, timestamp="2026-03-12T19:01:00"),
    ]

    remaining = remove_recent_take(recent_takes, "a.wav")

    assert [take.path for take in remaining] == ["b.wav"]


def test_rename_take_file_renames_on_disk(tmp_path: Path) -> None:
    source = tmp_path / "take.wav"
    source.write_bytes(b"audio")

    renamed = rename_take_file(source, "renamed_take")

    assert renamed == tmp_path / "renamed_take.wav"
    assert renamed.exists()
    assert not source.exists()


def test_list_audio_routing_maps_portaudio_host_api_devices(monkeypatch) -> None:
    class _FakeSD:
        @staticmethod
        def query_hostapis():
            return [
                {"name": "MME", "default_input_device": 0, "default_output_device": 1},
                {"name": "ASIO", "default_input_device": 2, "default_output_device": 3},
            ]

        @staticmethod
        def query_devices():
            return [
                {"name": "Mic One", "hostapi": 0, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 48000},
                {"name": "Speakers One", "hostapi": 0, "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 48000},
                {"name": "Lexicon In", "hostapi": 1, "max_input_channels": 2, "max_output_channels": 0, "default_samplerate": 44100},
                {"name": "Lexicon Out", "hostapi": 1, "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100},
            ]

    monkeypatch.setattr(recording_module, "sd", _FakeSD())

    snapshot = list_audio_routing(AUDIO_BACKEND_PORTAUDIO, "ASIO")

    assert isinstance(snapshot, AudioRoutingSnapshot)
    assert snapshot.active_backend == AUDIO_BACKEND_PORTAUDIO
    assert snapshot.host_api_names == ["MME", "ASIO"]
    assert [device.label for device in snapshot.input_devices] == ["Lexicon In"]
    assert [device.label for device in snapshot.output_devices] == ["Lexicon Out"]
    assert snapshot.input_devices[0].device_id == "pa:2"


def test_auto_backend_falls_back_when_sounddevice_missing(monkeypatch) -> None:
    monkeypatch.setattr(recording_module, "sd", None)

    snapshot = list_audio_routing(AUDIO_BACKEND_AUTO)

    assert snapshot.active_backend == "qt"
