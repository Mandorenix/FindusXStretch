from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RegionSelection:
    start_seconds: float
    end_seconds: float

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.end_seconds - self.start_seconds)


@dataclass(frozen=True)
class WaveformOverview:
    min_peaks: np.ndarray
    max_peaks: np.ndarray
    duration_seconds: float
    channels: int
    sample_rate: int
    frame_count: int


def build_waveform_overview(
    audio: np.ndarray,
    sample_rate: int,
    bins: int = 1600,
) -> WaveformOverview:
    array = np.asarray(audio, dtype=np.float32)
    if array.ndim == 1:
        array = array[:, None]
    frame_count, channels = array.shape
    if frame_count == 0:
        raise ValueError("Cannot build waveform overview from empty audio.")

    bins = max(32, min(bins, frame_count))
    edges = np.linspace(0, frame_count, bins + 1, dtype=int)
    min_peaks = np.zeros((channels, bins), dtype=np.float32)
    max_peaks = np.zeros((channels, bins), dtype=np.float32)

    for index in range(bins):
        start = edges[index]
        end = max(start + 1, edges[index + 1])
        segment = array[start:end]
        min_peaks[:, index] = np.min(segment, axis=0)
        max_peaks[:, index] = np.max(segment, axis=0)

    return WaveformOverview(
        min_peaks=min_peaks,
        max_peaks=max_peaks,
        duration_seconds=frame_count / sample_rate,
        channels=channels,
        sample_rate=sample_rate,
        frame_count=frame_count,
    )
