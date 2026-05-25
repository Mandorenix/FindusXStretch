import io
import json
import numpy as np
from scipy.io import wavfile
import dsp

def process_audio(wav_bytes_js, stretch_factor, effects_json, window_size=8192, region_start=0.0, region_end=-1.0, infinite_mode=False, progress_cb=None):
    # wav_bytes_js is a memoryview or bytes passed from JS
    wav_bytes = bytes(wav_bytes_js)
    
    # Read WAV from bytes
    sample_rate, audio_data = wavfile.read(io.BytesIO(wav_bytes))
    
    # Ensure it's 2D for consistency, or keep as is. dsp handles both.
    if audio_data.ndim == 1:
        audio_data = audio_data.reshape(-1, 1)
        
    # Normalize if it's integer
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0
    elif audio_data.dtype == np.float64:
        audio_data = audio_data.astype(np.float32)
        
    # Crop audio
    start_idx = int(region_start * sample_rate)
    end_idx = int(region_end * sample_rate) if region_end > 0 else len(audio_data)
    
    # Ensure indices are valid
    start_idx = max(0, min(start_idx, len(audio_data) - 1))
    end_idx = max(start_idx + 1, min(end_idx, len(audio_data)))
    
    audio_data = audio_data[start_idx:end_idx]
        
    # Paulstretch
    settings = dsp.StretchSettings(window_size=window_size)
    stretched = dsp.paulstretch_audio(audio_data, stretch_factor, settings=settings, progress_callback=progress_cb)
    
    # Parse effects
    effects_dict = json.loads(effects_json)
    
    # Handle the Enum for FilterMode
    if "filter_mode" in effects_dict:
        effects_dict["filter_mode"] = dsp.FilterMode(effects_dict["filter_mode"])
        
    effect_settings = dsp.EffectSettings(**effects_dict)
    
    # Apply effects
    processed = dsp.apply_effects(stretched, sample_rate, effect_settings)
    
    # Apply Infinite Mode loop crossfade
    if infinite_mode:
        processed = dsp.build_loop_crossfade_audio(processed, sample_rate, crossfade_ms=3000.0)
    
    # Convert back to 16-bit PCM for web playback to save memory
    processed_int16 = np.clip(processed * 32767.0, -32768.0, 32767.0).astype(np.int16)
    
    # Write to bytes
    out_buffer = io.BytesIO()
    wavfile.write(out_buffer, sample_rate, processed_int16)
    
    return out_buffer.getvalue()
