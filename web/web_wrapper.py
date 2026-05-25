import io
import json
import numpy as np
from scipy.io import wavfile
import dsp

def process_audio(wav_bytes_js, stretch_factor, effects_json):
    # wav_bytes_js is a memoryview or bytes passed from JS
    wav_bytes = bytes(wav_bytes_js)
    
    # Read WAV from bytes
    sample_rate, audio_data = wavfile.read(io.BytesIO(wav_bytes))
    
    # Ensure it's 2D for consistency, or keep as is. dsp handles both.
    if audio_data.ndim == 1:
        audio_data = audio_data.reshape(-1, 1)
        
    # Normalize if it's integer
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float64) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float64) / 2147483648.0
    elif audio_data.dtype == np.float32:
        audio_data = audio_data.astype(np.float64)
        
    # Paulstretch
    settings = dsp.StretchSettings(window_size=8192) # use a slightly smaller window for web
    stretched = dsp.paulstretch_audio(audio_data, stretch_factor, settings=settings)
    
    # Parse effects
    effects_dict = json.loads(effects_json)
    
    # Handle the Enum for FilterMode
    if "filter_mode" in effects_dict:
        effects_dict["filter_mode"] = dsp.FilterMode(effects_dict["filter_mode"])
        
    effect_settings = dsp.EffectSettings(**effects_dict)
    
    # Apply effects
    processed = dsp.apply_effects(stretched, sample_rate, effect_settings)
    
    # Convert back to 16-bit PCM for web playback to save memory
    processed_int16 = np.clip(processed * 32767.0, -32768.0, 32767.0).astype(np.int16)
    
    # Write to bytes
    out_buffer = io.BytesIO()
    wavfile.write(out_buffer, sample_rate, processed_int16)
    
    return out_buffer.getvalue()
