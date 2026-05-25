from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

import numpy as np
from scipy.signal import butter, fftconvolve, resample, sosfiltfilt, windows


class QualityProfile(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class FilterMode(str, Enum):
    OFF = "Off"
    LOWPASS = "Low-pass"
    HIGHPASS = "High-pass"
    BANDPASS = "Band-pass"


SAFETY_LIMITER_CEILING_DB = -1.0


@dataclass(frozen=True)
class StretchSettings:
    window_size: int = 16384
    analysis_hop_ratio: float = 0.25
    fade_clip: float = 0.98
    random_seed: int | None = None


@dataclass(frozen=True)
class EffectSettings:
    filter_mode: FilterMode = FilterMode.OFF
    filter_enabled: bool = True
    reverb_amount: float = 0.0
    reverb_enabled: bool = True
    lowpass_hz: float = 6000.0
    drive_amount: float = 0.0
    drive_enabled: bool = True
    chorus_amount: float = 0.0
    chorus_enabled: bool = True
    texture_amount: float = 0.0
    texture_enabled: bool = True
    motion_amount: float = 0.0
    motion_enabled: bool = True
    pitch_drift_amount: float = 0.0
    pitch_drift_enabled: bool = True
    bloom_amount: float = 0.0
    bloom_enabled: bool = True
    granular_amount: float = 0.0
    granular_enabled: bool = True
    delay_amount: float = 0.0
    delay_enabled: bool = True
    autopan_amount: float = 0.0
    autopan_enabled: bool = True
    stereo_width: float = 1.0
    reverse: bool = False
    freeze_enabled: bool = False
    shimmer_amount: float = 0.0
    shimmer_enabled: bool = True
    wet_dry: float = 1.0
    input_gain_db: float = 0.0
    limiter_enabled: bool = False


@dataclass(frozen=True)
class QualitySettings:
    profile: QualityProfile
    stretch: StretchSettings
    preview_source_seconds: float


ProgressCallback = Callable[[float, str], None]


def quality_settings(
    profile: QualityProfile, random_seed: int | None = None
) -> QualitySettings:
    if profile == QualityProfile.LOW:
        return QualitySettings(
            profile=profile,
            stretch=StretchSettings(window_size=4096, analysis_hop_ratio=0.25, random_seed=random_seed),
            preview_source_seconds=1.5,
        )
    if profile == QualityProfile.HIGH:
        return QualitySettings(
            profile=profile,
            stretch=StretchSettings(window_size=16384, analysis_hop_ratio=0.25, random_seed=random_seed),
            preview_source_seconds=4.0,
        )
    return QualitySettings(
        profile=QualityProfile.MEDIUM,
        stretch=StretchSettings(window_size=8192, analysis_hop_ratio=0.25, random_seed=random_seed),
        preview_source_seconds=2.5,
    )


def paulstretch_channel(
    channel: np.ndarray,
    stretch_factor: float,
    settings: StretchSettings | None = None,
    progress_callback: ProgressCallback | None = None,
    progress_offset: float = 0.0,
    progress_span: float = 1.0,
) -> np.ndarray:
    if settings is None:
        settings = StretchSettings()
    if stretch_factor <= 1.0:
        raise ValueError("stretch_factor must be greater than 1.0.")

    samples = np.asarray(channel, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        raise ValueError("Input audio is empty.")

    synthesis_hop = max(1, int(settings.window_size * settings.analysis_hop_ratio))
    input_hop = synthesis_hop / stretch_factor
    window = windows.hann(settings.window_size, sym=False)
    padded = _pad_audio(samples, settings.window_size)
    max_start = max(0.0, padded.size - settings.window_size)
    frame_count = max(1, int(np.ceil(max_start / input_hop)) + 1)

    output_length = settings.window_size + synthesis_hop * max(frame_count - 1, 0)
    output = np.zeros(output_length, dtype=np.float32)
    window_norm = np.zeros(output_length, dtype=np.float32)
    rng = np.random.default_rng(settings.random_seed)

    for frame_index in range(frame_count):
        start = min(frame_index * input_hop, max_start)
        frame = _fractional_window(padded, start, settings.window_size) * window
        magnitude = np.abs(np.fft.rfft(frame))
        phases = rng.uniform(0.0, 2.0 * np.pi, size=magnitude.shape)
        rebuilt = np.fft.irfft(magnitude * np.exp(1j * phases), n=settings.window_size)
        out_start = frame_index * synthesis_hop
        output[out_start : out_start + settings.window_size] += rebuilt * window
        window_norm[out_start : out_start + settings.window_size] += window * window
        if progress_callback and (
            frame_index == frame_count - 1 or frame_index % max(1, frame_count // 50) == 0
        ):
            progress_callback(
                progress_offset + progress_span * ((frame_index + 1) / frame_count),
                "Resynthesizing spectral frames",
            )

    nonzero = window_norm > 1e-12
    output[nonzero] /= window_norm[nonzero]
    output = _trim_fade(output, settings.window_size)
    return normalize_audio(output, clip_level=settings.fade_clip)


def paulstretch_audio(
    audio: np.ndarray,
    stretch_factor: float,
    settings: StretchSettings | None = None,
    progress_callback: ProgressCallback | None = None,
) -> np.ndarray:
    if settings is None:
        settings = StretchSettings()

    array = np.asarray(audio, dtype=np.float32)
    if array.ndim == 1:
        return paulstretch_channel(
            array,
            stretch_factor,
            settings,
            progress_callback=progress_callback,
        )
    if array.ndim != 2:
        raise ValueError("Audio must be mono or shaped as (samples, channels).")

    if progress_callback:
        progress_callback(0.0, "Preparing channels")

    channels = []
    channel_count = array.shape[1]
    for idx in range(channel_count):
        channels.append(
            paulstretch_channel(
                array[:, idx],
                stretch_factor,
                settings,
                progress_callback=progress_callback,
                progress_offset=idx / channel_count,
                progress_span=1.0 / channel_count,
            )
        )
    min_len = min(channel.shape[0] for channel in channels)
    return np.column_stack([channel[:min_len] for channel in channels])


def apply_effects(
    audio: np.ndarray,
    sample_rate: int,
    effects: EffectSettings,
    random_seed: int | None = None,
    *,
    normalize_output: bool = True,
) -> np.ndarray:
    dry = np.asarray(audio, dtype=np.float32)
    if dry.size == 0:
        return dry.copy()

    # Block processing for large files to save memory and prevent browser crashes
    chunk_size = sample_rate * 15  # 15 seconds
    if dry.shape[0] <= chunk_size * 1.5:
        out = _apply_effects_internal(dry, sample_rate, effects, random_seed)
    else:
        overlap = sample_rate * 3  # 3 seconds crossfade
        step = chunk_size - overlap
        
        out = np.zeros_like(dry, dtype=np.float32)
        window_in = np.linspace(0.0, 1.0, overlap, dtype=np.float32)
        window_out = np.linspace(1.0, 0.0, overlap, dtype=np.float32)
        if dry.ndim == 2:
            window_in = window_in[:, None]
            window_out = window_out[:, None]

        for start in range(0, dry.shape[0], step):
            end = min(start + chunk_size, dry.shape[0])
            chunk = dry[start:end]
            
            processed_chunk = _apply_effects_internal(
                chunk, sample_rate, effects, random_seed
            )
            
            # Apply crossfade windowing
            if start > 0:
                fade_len = min(overlap, processed_chunk.shape[0])
                processed_chunk[:fade_len] *= window_in[:fade_len]
            
            if end < dry.shape[0]:
                fade_len = min(overlap, processed_chunk.shape[0])
                processed_chunk[-fade_len:] *= window_out[-fade_len:]
                
            out[start:end] += processed_chunk

    if effects.reverse:
        out = reverse_audio(out)

    return _normalize_if_needed(out, normalize_output)


def _apply_effects_internal(
    dry: np.ndarray,
    sample_rate: int,
    effects: EffectSettings,
    random_seed: int | None = None,
) -> np.ndarray:
    filter_mode = effects.filter_mode if effects.filter_enabled else FilterMode.OFF
    wet = apply_filter(dry, sample_rate, filter_mode, effects.lowpass_hz)
    wet = apply_drive(wet, effects.drive_amount if effects.drive_enabled else 0.0)
    wet = apply_chorus(wet, sample_rate, effects.chorus_amount if effects.chorus_enabled else 0.0)
    wet = apply_pitch_drift(
        wet,
        sample_rate,
        effects.pitch_drift_amount if effects.pitch_drift_enabled else 0.0,
    )
    wet = apply_texture(
        wet,
        sample_rate,
        effects.texture_amount if effects.texture_enabled else 0.0,
        random_seed=random_seed,
    )
    wet = apply_granular_smear(
        wet,
        sample_rate,
        effects.granular_amount if effects.granular_enabled else 0.0,
        random_seed=random_seed,
    )
    wet = apply_bloom(
        wet,
        sample_rate,
        effects.bloom_amount if effects.bloom_enabled else 0.0,
        random_seed=random_seed,
    )
    wet = apply_reverb(
        wet,
        sample_rate,
        effects.reverb_amount if effects.reverb_enabled else 0.0,
        random_seed=random_seed,
    )
    wet = apply_shimmer(wet, sample_rate, effects.shimmer_amount if effects.shimmer_enabled else 0.0)
    wet = apply_delay(wet, sample_rate, effects.delay_amount if effects.delay_enabled else 0.0)
    wet = apply_motion(wet, sample_rate, effects.motion_amount if effects.motion_enabled else 0.0)
    wet = apply_autopan(wet, sample_rate, effects.autopan_amount if effects.autopan_enabled else 0.0)
    wet = apply_stereo_width(wet, effects.stereo_width)
    
    mix = float(np.clip(effects.wet_dry, 0.0, 1.0))
    if mix <= 0.0:
        return dry.copy()
    if mix >= 1.0:
        return wet
    return (dry * (1.0 - mix)) + (wet * mix)


def freeze_source(
    audio: np.ndarray,
    target_frames: int,
    random_seed: int | None = None,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    if array.ndim == 1:
        array = array[:, None]
    if array.shape[0] == 0:
        raise ValueError("Cannot freeze empty audio.")
    if target_frames <= array.shape[0]:
        frozen = array[:target_frames]
        return frozen[:, 0] if frozen.shape[1] == 1 else frozen

    window = windows.hann(min(max(64, array.shape[0]), 2048), sym=False)
    fade_size = min(window.shape[0] // 2, max(16, array.shape[0] // 4))
    rng = np.random.default_rng(random_seed)
    out = np.zeros((target_frames, array.shape[1]), dtype=np.float32)
    position = 0
    while position < target_frames:
        chunk = array.copy()
        jitter = 0.96 + (0.08 * rng.random())
        chunk *= jitter
        end = min(target_frames, position + chunk.shape[0])
        out[position:end] = chunk[: end - position]
        if end >= target_frames:
            break
        overlap_start = max(0, end - fade_size)
        blend_count = end - overlap_start
        fade_out = np.linspace(1.0, 0.0, blend_count, endpoint=False)[:, None]
        fade_in = np.linspace(0.0, 1.0, blend_count, endpoint=False)[:, None]
        out[overlap_start:end] = (
            out[overlap_start:end] * fade_out
            + chunk[:blend_count] * fade_in
        )
        position = end - fade_size
    out = normalize_audio(out)
    return out[:, 0] if out.shape[1] == 1 else out


def apply_filter(audio: np.ndarray, sample_rate: int, mode: FilterMode | str, cutoff_hz: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    filter_mode = _coerce_filter_mode(mode)
    if filter_mode == FilterMode.OFF:
        return array.copy()
    nyquist = sample_rate * 0.5
    cutoff = float(np.clip(cutoff_hz, 100.0, max(120.0, nyquist * 0.99)))
    if filter_mode == FilterMode.LOWPASS and cutoff >= nyquist * 0.98:
        return array.copy()
    if filter_mode == FilterMode.BANDPASS:
        low = max(40.0, cutoff * 0.55)
        high = min(nyquist * 0.98, max(low + 80.0, cutoff * 1.45))
        if high <= low:
            return array.copy()
        sos = butter(4, [low / nyquist, high / nyquist], btype="bandpass", output="sos")
    elif filter_mode == FilterMode.HIGHPASS:
        sos = butter(4, cutoff / nyquist, btype="highpass", output="sos")
    else:
        sos = butter(4, cutoff / nyquist, btype="lowpass", output="sos")
    if array.ndim == 1:
        return sosfiltfilt(sos, array)
    return np.column_stack([sosfiltfilt(sos, array[:, idx]) for idx in range(array.shape[1])])


def apply_lowpass(audio: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    return apply_filter(audio, sample_rate, FilterMode.LOWPASS, cutoff_hz)


def apply_drive(audio: np.ndarray, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()
    gain = 1.0 + (mix * 5.0)
    driven = np.tanh(array * gain) / np.tanh(gain)
    return normalize_audio((array * (1.0 - 0.45 * mix)) + (driven * (0.55 * mix)))


def apply_chorus(audio: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    delay_a = int(max(4, sample_rate * 0.012))
    delay_b = int(max(6, sample_rate * 0.019))
    depth_a = max(2, int(sample_rate * 0.0018 * mix))
    depth_b = max(3, int(sample_rate * 0.0026 * mix))
    rate_a = 0.08 + (0.18 * mix)
    rate_b = 0.11 + (0.22 * mix)
    phase = np.linspace(0.0, array.shape[0] / sample_rate, array.shape[0], endpoint=False)

    if array.ndim == 1:
        delayed_a = _modulated_delay(array, delay_a, depth_a, rate_a, phase, 0.0)
        delayed_b = _modulated_delay(array, delay_b, depth_b, rate_b, phase, np.pi * 0.5)
        wet = (delayed_a + delayed_b) * 0.5
    else:
        wet_channels = []
        for idx in range(array.shape[1]):
            ch_phase = phase + (idx * 0.37)
            delayed_a = _modulated_delay(array[:, idx], delay_a, depth_a, rate_a, ch_phase, idx * 0.2)
            delayed_b = _modulated_delay(array[:, idx], delay_b, depth_b, rate_b, ch_phase, np.pi * 0.5 + idx * 0.3)
            wet_channels.append((delayed_a + delayed_b) * 0.5)
        wet = np.column_stack(wet_channels)
    return normalize_audio((array * (1.0 - 0.5 * mix)) + (wet * (0.65 * mix)))


def apply_pitch_drift(audio: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0 or array.shape[0] < 16:
        return array.copy()

    phase = np.linspace(0.0, array.shape[0] / sample_rate, array.shape[0], endpoint=False)
    rate_a = 0.018 + (0.035 * mix)
    rate_b = 0.031 + (0.045 * mix)
    max_drift = 1.5 + (10.0 * mix)
    drift_curve = (
        np.sin(2.0 * np.pi * rate_a * phase)
        + (0.55 * np.sin((2.0 * np.pi * rate_b * phase) + np.pi * 0.37))
    ) * max_drift

    if array.ndim == 1:
        drifted = _variable_resample_positions(array, drift_curve)
    else:
        drifted = np.column_stack(
            [_variable_resample_positions(array[:, idx], drift_curve + (idx * 0.3)) for idx in range(array.shape[1])]
        )
    return normalize_audio((array * (1.0 - 0.4 * mix)) + (drifted * (0.55 * mix)))


def apply_texture(
    audio: np.ndarray,
    sample_rate: int,
    amount: float,
    random_seed: int | None = None,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0 or array.shape[0] < 64:
        return array.copy()

    smeared = apply_granular_smear(array, sample_rate, min(1.0, 0.2 + (0.65 * mix)), random_seed=random_seed)
    softened = _moving_average(smeared, max(3, int(7 + (mix * 18))))
    rng = np.random.default_rng(random_seed)
    noise = rng.normal(0.0, 0.0025 + (0.01 * mix), size=array.shape)
    textured = softened + noise
    return normalize_audio((array * (1.0 - 0.35 * mix)) + (textured * (0.65 * mix)))


def apply_granular_smear(
    audio: np.ndarray,
    sample_rate: int,
    amount: float,
    random_seed: int | None = None,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0 or array.shape[0] < 64:
        return array.copy()

    grain_size = max(64, int(sample_rate * (0.025 + (0.05 * mix))))
    hop = max(16, grain_size // 3)
    jitter = max(2, int(grain_size * (0.12 + 0.18 * mix)))
    window = windows.hann(grain_size, sym=False)
    rng = np.random.default_rng(random_seed)
    wet = np.zeros_like(array, dtype=np.float32)
    norm = np.zeros(array.shape[0], dtype=np.float32)

    limit = max(1, array.shape[0] - grain_size)
    if array.ndim == 1:
        for start in range(0, limit, hop):
            source_start = int(np.clip(start + rng.integers(-jitter, jitter + 1), 0, array.shape[0] - grain_size))
            grain = array[source_start : source_start + grain_size] * window
            wet[start : start + grain_size] += grain
            norm[start : start + grain_size] += window
    else:
        for start in range(0, limit, hop):
            source_start = int(np.clip(start + rng.integers(-jitter, jitter + 1), 0, array.shape[0] - grain_size))
            grain = array[source_start : source_start + grain_size] * window[:, None]
            wet[start : start + grain_size] += grain
            norm[start : start + grain_size] += window
    valid = norm > 1e-9
    if array.ndim == 1:
        wet[valid] /= norm[valid]
    else:
        wet[valid] /= norm[valid, None]
    return normalize_audio((array * (1.0 - 0.45 * mix)) + (wet * (0.75 * mix)))


def apply_bloom(
    audio: np.ndarray,
    sample_rate: int,
    amount: float,
    random_seed: int | None = None,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    softened = apply_filter(array, sample_rate, FilterMode.LOWPASS, 2200.0 + (5400.0 * (1.0 - mix)))
    spacious = apply_reverb(softened, sample_rate, min(1.0, 0.15 + (0.75 * mix)), random_seed=random_seed)
    airy = apply_shimmer(spacious, sample_rate, min(1.0, 0.1 + (0.55 * mix)))
    return normalize_audio((array * (1.0 - 0.45 * mix)) + (airy * (0.75 * mix)))


def apply_motion(audio: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    moving = apply_autopan(array, sample_rate, min(1.0, 0.2 + (0.7 * mix)))
    if moving.ndim == 1:
        moving = np.column_stack([moving, moving])
    phase = np.linspace(0.0, moving.shape[0] / sample_rate, moving.shape[0], endpoint=False)
    rate = 0.012 + (0.035 * mix)
    envelope = 0.92 + (0.08 * np.sin(2.0 * np.pi * rate * phase))
    if moving.ndim == 1:
        shaped = moving * envelope
    else:
        shaped = moving * envelope[:, None]
    return normalize_audio((moving * (1.0 - 0.25 * mix)) + (shaped * (0.25 * mix)))


def apply_autopan(audio: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    phase = np.linspace(0.0, array.shape[0] / sample_rate, array.shape[0], endpoint=False)
    rate = 0.025 + (0.09 * mix)
    lfo = np.sin(2.0 * np.pi * rate * phase)
    left_gain = 1.0 - (0.35 * mix) + (0.35 * mix * (0.5 - 0.5 * lfo))
    right_gain = 1.0 - (0.35 * mix) + (0.35 * mix * (0.5 + 0.5 * lfo))

    if array.ndim == 1:
        stereo = np.column_stack([array * left_gain, array * right_gain])
        return normalize_audio(stereo)
    if array.shape[1] == 1:
        stereo = np.column_stack([array[:, 0] * left_gain, array[:, 0] * right_gain])
        return normalize_audio(stereo)

    wet = array.copy()
    wet[:, 0] *= left_gain
    wet[:, 1] *= right_gain
    return normalize_audio(wet)


def apply_reverb(
    audio: np.ndarray,
    sample_rate: int,
    amount: float,
    random_seed: int | None = None,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    ir_seconds = 1.8 + (1.2 * mix)
    ir_length = max(256, int(sample_rate * ir_seconds))
    times = np.linspace(0.0, ir_seconds, ir_length, endpoint=False)
    decay = np.exp(-times * (2.5 - (1.5 * mix)))
    rng = np.random.default_rng(random_seed)
    noise = rng.normal(0.0, 1.0, size=ir_length)
    ir = decay * noise
    ir[0] += 1.0
    ir /= np.max(np.abs(ir))

    if array.ndim == 1:
        wet = fftconvolve(array, ir, mode="full")[: array.shape[0]]
    else:
        wet = np.column_stack(
            [fftconvolve(array[:, idx], ir, mode="full")[: array.shape[0]] for idx in range(array.shape[1])]
        )
    return normalize_audio((array * (1.0 - 0.3 * mix)) + (wet * (0.7 * mix)))


def apply_shimmer(audio: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    if array.ndim == 1:
        shifted = _octave_up(array)
    else:
        shifted = np.column_stack([_octave_up(array[:, idx]) for idx in range(array.shape[1])])

    shimmer_tail = apply_reverb(shifted, sample_rate, 0.45 + (0.35 * mix))
    return normalize_audio((array * (1.0 - 0.4 * mix)) + (shimmer_tail * (0.8 * mix)))


def apply_delay(audio: np.ndarray, sample_rate: int, amount: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    mix = float(np.clip(amount, 0.0, 1.0))
    if mix <= 0.0:
        return array.copy()

    delay_samples = max(1, int(sample_rate * (0.18 + 0.42 * mix)))
    feedback = 0.15 + (0.45 * mix)

    if array.ndim == 1:
        wet = array.copy()
        wet[delay_samples:] += array[:-delay_samples] * feedback
    else:
        wet = array.copy()
        if array.shape[1] == 1:
            wet[delay_samples:, 0] += array[:-delay_samples, 0] * feedback
        else:
            wet[delay_samples:, 0] += array[:-delay_samples, 1] * feedback
            wet[delay_samples:, 1] += array[:-delay_samples, 0] * feedback
    return normalize_audio((array * (1.0 - 0.35 * mix)) + (wet * (0.65 * mix)))


def apply_stereo_width(audio: np.ndarray, width: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    if array.ndim != 2 or array.shape[1] < 2:
        return array.copy()
    amount = float(np.clip(width, 0.0, 2.0))
    mid = (array[:, 0] + array[:, 1]) * 0.5
    side = (array[:, 0] - array[:, 1]) * 0.5 * amount
    widened = np.column_stack([mid + side, mid - side])
    return normalize_audio(widened)


def reverse_audio(audio: np.ndarray) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    return np.flip(array, axis=0).copy()


def apply_input_gain(audio: np.ndarray, gain_db: float) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    gain = float(gain_db)
    if abs(gain) <= 1e-9:
        return array.copy()
    return array * (10.0 ** (gain / 20.0))


def apply_safety_limiter(
    audio: np.ndarray,
    ceiling_db: float = SAFETY_LIMITER_CEILING_DB,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    if array.size == 0:
        return array.copy()
    threshold = float(np.clip(10.0 ** (ceiling_db / 20.0), 1e-4, 1.0))
    peak = np.max(np.abs(array))
    if peak <= threshold + 1e-12:
        return array.copy()
    return np.tanh(array / threshold) * threshold


def build_loop_crossfade_audio(
    audio: np.ndarray,
    sample_rate: int,
    crossfade_ms: float,
) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    if array.size == 0:
        return array.copy()
    crossfade_frames = int(round((max(0.0, float(crossfade_ms)) / 1000.0) * max(1, sample_rate)))
    if crossfade_frames <= 1:
        return array.copy()
    crossfade_frames = min(crossfade_frames, max(1, array.shape[0] // 4))
    if crossfade_frames <= 1:
        return array.copy()

    head = array[:crossfade_frames]
    tail = array[-crossfade_frames:]
    wrapped_head = np.concatenate([head[1:], head[:1]], axis=0)
    fade_out = np.linspace(1.0, 0.0, crossfade_frames, endpoint=True, dtype=np.float32)
    fade_in = 1.0 - fade_out

    if array.ndim == 1:
        transition = (tail * fade_out) + (wrapped_head * fade_in)
        return np.concatenate([array, transition])

    transition = (tail * fade_out[:, None]) + (wrapped_head * fade_in[:, None])
    return np.vstack([array, transition])


def normalize_audio(audio: np.ndarray, clip_level: float = 0.98) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    peak = np.max(np.abs(array)) if array.size else 0.0
    if peak <= 1e-12:
        return array
    return (array / peak) * clip_level


def _normalize_if_needed(audio: np.ndarray, normalize_output: bool) -> np.ndarray:
    array = np.asarray(audio, dtype=np.float32)
    if not normalize_output:
        return array.copy()
    return normalize_audio(array)


def _octave_up(channel: np.ndarray) -> np.ndarray:
    compressed = resample(channel, max(8, channel.shape[0] // 2))
    shifted = resample(compressed, channel.shape[0])
    return shifted


def _pad_audio(audio: np.ndarray, window_size: int) -> np.ndarray:
    total_size = max(audio.size, window_size) + window_size
    padded = np.zeros(total_size, dtype=np.float32)
    padded[: audio.size] = audio
    return padded


def _fractional_window(audio: np.ndarray, start: float, window_size: int) -> np.ndarray:
    base = int(np.floor(start))
    frac = start - base
    frame = audio[base : base + window_size + 1]
    if frame.shape[0] < window_size + 1:
        padded = np.zeros(window_size + 1, dtype=np.float32)
        padded[: frame.shape[0]] = frame
        frame = padded
    if frac <= 1e-12:
        return frame[:window_size]
    return ((1.0 - frac) * frame[:window_size]) + (frac * frame[1 : window_size + 1])


def _trim_fade(audio: np.ndarray, window_size: int) -> np.ndarray:
    trim = min(window_size // 2, audio.size // 10)
    if trim <= 0:
        return audio
    return audio[trim:-trim] if audio.size > 2 * trim else audio


def _coerce_filter_mode(mode: FilterMode | str) -> FilterMode:
    if isinstance(mode, FilterMode):
        return mode
    if isinstance(mode, str):
        normalized = mode.strip().lower()
        for candidate in FilterMode:
            if normalized in {candidate.value.lower(), candidate.name.lower()}:
                return candidate
    return FilterMode.LOWPASS


def _modulated_delay(
    channel: np.ndarray,
    base_delay: int,
    depth: int,
    rate_hz: float,
    phase_seconds: np.ndarray,
    phase_offset: float,
) -> np.ndarray:
    out = np.empty_like(channel)
    block_size = 131072
    for i in range(0, channel.shape[0], block_size):
        end = min(i + block_size, channel.shape[0])
        phase_chunk = phase_seconds[i:end]
        delay_curve = base_delay + (np.sin((2.0 * np.pi * rate_hz * phase_chunk) + phase_offset) * depth)
        source_positions = np.arange(i, end, dtype=np.float32) - delay_curve
        source_positions = np.clip(source_positions, 0.0, channel.shape[0] - 1)
        base = np.floor(source_positions).astype(int)
        frac = source_positions - base
        next_idx = np.clip(base + 1, 0, channel.shape[0] - 1)
        out[i:end] = ((1.0 - frac) * channel[base]) + (frac * channel[next_idx])
    return out


def _variable_resample_positions(channel: np.ndarray, drift_curve: np.ndarray) -> np.ndarray:
    out = np.empty_like(channel)
    block_size = 131072
    for i in range(0, channel.shape[0], block_size):
        end = min(i + block_size, channel.shape[0])
        drift_chunk = drift_curve[i:end]
        source_positions = np.arange(i, end, dtype=np.float32) - drift_chunk
        source_positions = np.clip(source_positions, 0.0, channel.shape[0] - 1)
        base = np.floor(source_positions).astype(int)
        frac = source_positions - base
        next_idx = np.clip(base + 1, 0, channel.shape[0] - 1)
        out[i:end] = ((1.0 - frac) * channel[base]) + (frac * channel[next_idx])
    return out


def _moving_average(audio: np.ndarray, kernel_size: int) -> np.ndarray:
    if kernel_size <= 1:
        return audio.copy()
    kernel = np.ones(kernel_size, dtype=np.float32) / kernel_size
    if audio.ndim == 1:
        return np.convolve(audio, kernel, mode="same")
    return np.column_stack([np.convolve(audio[:, idx], kernel, mode="same") for idx in range(audio.shape[1])])
