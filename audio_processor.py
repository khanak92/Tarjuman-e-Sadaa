"""
Audio preprocessing and format conversion module
"""

import os
import numpy as np
from pydub import AudioSegment
import tempfile
from typing import Optional


class AudioProcessor:
    """
    Handles audio file loading, normalization, and preprocessing
    """
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def load_audio(self, file_path: str) -> tuple:
        """
        Load audio file and convert to numpy array
        
        Args:
            file_path: Path to audio file
            
        Returns:
            tuple: (audio_array, sample_rate)
        """
        try:
            import whisper
            audio = whisper.load_audio(file_path)
            return audio, whisper.audio.SAMPLE_RATE
        except Exception as e:
            try:
                audio = AudioSegment.from_file(file_path)
                audio = audio.set_frame_rate(16000)
                audio = audio.set_channels(1)
                
                audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32)
                if audio.sample_width == 2:
                    audio_array = audio_array / 32768.0
                elif audio.sample_width == 4:
                    audio_array = audio_array / 2147483648.0
                
                sample_rate = audio.frame_rate
                return audio_array, sample_rate
            except Exception as e2:
                raise ValueError(f"Error loading audio file: {str(e)} (fallback also failed: {str(e2)})")
    
    def normalize_audio(self, audio_array: np.ndarray) -> np.ndarray:
        """
        Normalize audio to prevent clipping
        
        Args:
            audio_array: Input audio array
            
        Returns:
            Normalized audio array
        """
        max_val = np.max(np.abs(audio_array))
        if max_val > 0:
            audio_array = audio_array / max_val * 0.95
        return audio_array
    
    def split_audio(
        self,
        audio_array: np.ndarray,
        sample_rate: int,
        chunk_length_s: int = 30,
        model_size: Optional[str] = None
    ) -> tuple:
        """
        Split audio into chunks for processing
        
        Args:
            audio_array: Input audio array
            sample_rate: Sample rate of audio
            chunk_length_s: Base chunk length in seconds
            model_size: Optional model name to auto-adjust chunk sizing
            
        Returns:
            Tuple of (list of audio chunks, actual chunk duration in seconds)
        """
        duration = len(audio_array) / sample_rate
        high_memory_models = {"large", "large-v2", "large-v3", "large-v3-turbo", "turbo"}
        
        if duration <= 120:
            if model_size and model_size in high_memory_models and duration > 40:
                chunk_length_s = min(duration, 30)
            else:
                return [audio_array], duration
        elif duration <= 600:
            chunk_length_s = 60
        elif duration <= 1800:
            chunk_length_s = 45
        else:
            chunk_length_s = 30
        
        if model_size and model_size in high_memory_models:
            if duration > 60:
                chunk_length_s = min(chunk_length_s, 30)
            if duration > 1200:
                chunk_length_s = min(chunk_length_s, 25)
        
        chunk_length_samples = int(max(chunk_length_s, 1) * sample_rate)
        chunks = []
        
        for i in range(0, len(audio_array), chunk_length_samples):
            chunk = audio_array[i:i + chunk_length_samples]
            if len(chunk) > 0:
                chunks.append(chunk)
        
        return chunks, chunk_length_s
    
    def get_audio_info(self, file_path: str) -> dict:
        """
        Get audio file information
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio info (duration, sample_rate, channels)
        """
        try:
            audio = AudioSegment.from_file(file_path)
            duration_s = len(audio) / 1000.0
            return {
                "duration": duration_s,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "format": os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            raise ValueError(f"Error reading audio info: {str(e)}")

