"""
Core ASR engine using Whisper for multilingual transcription
"""

import whisper
import torch
import numpy as np
from typing import Optional, Dict, List, Tuple
import os

try:
    from offline_translator import OfflineTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False
    print("Warning: OfflineTranslator not available. Translation to Urdu may be limited.")


class TranscriptionEngine:
    """
    Handles speech recognition and Urdu translation using Whisper
    """
    
    def __init__(self, model_size: str = "medium", device: Optional[str] = None, load_translator: bool = True):
        """
        Initialize transcription engine
        
        Args:
            model_size: Whisper model size (medium, large-v3, large-v3-turbo)
            device: Device to use (cuda, cpu, or None for auto-detect)
            load_translator: Whether to load offline translator (default True)
        """
        self.model_size = model_size
        self.original_device = device
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.translator = None
        self.translator_loaded = False
        self.load_translator_flag = load_translator
        self._cuda_failed = False
        self._load_model()
        
        if load_translator and TRANSLATOR_AVAILABLE:
            self._load_translator()
    
    def _load_translator(self):
        """
        Lazy load the offline translator (only when needed)
        """
        if self.translator_loaded or not TRANSLATOR_AVAILABLE:
            return
        
        if self.translator is None:
            try:
                print("Loading offline translator...")
                self.translator = OfflineTranslator(device=self.device, model_size="600M")
                self.translator_loaded = True
                print("Offline translator loaded successfully!")
            except Exception as e:
                print(f"Warning: Failed to load offline translator: {e}")
                print("Sindhi/Pashto will be transcribed but may not translate to Urdu properly.")
                self.translator = None
                self.translator_loaded = True
    
    def _load_model(self):
        """
        Load Whisper model with CUDA fallback
        """
        try:
            print(f"Loading Whisper {self.model_size} model on {self.device}...")
            self.model = whisper.load_model(self.model_size, device=self.device)
            print("Model loaded successfully!")
        except RuntimeError as e:
            if "cuda" in str(e).lower() and self.device == "cuda":
                print(f"CUDA error: {str(e)}")
                print("Falling back to CPU...")
                self.device = "cpu"
                self._cuda_failed = True
                try:
                    self.model = whisper.load_model(self.model_size, device="cpu")
                    print("Model loaded on CPU successfully!")
                except Exception as e2:
                    raise RuntimeError(f"Failed to load Whisper model on CPU: {str(e2)}")
            else:
                raise RuntimeError(f"Failed to load Whisper model: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model: {str(e)}")
    
    def detect_language(self, audio: np.ndarray) -> Tuple[str, float]:
        """
        Detect language in audio
        
        Args:
            audio: Audio array (numpy array)
            
        Returns:
            Tuple of (language_code, probability)
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        audio = whisper.pad_or_trim(audio)
        model_dims = getattr(self.model, "dims", None)
        n_mels = getattr(model_dims, "n_mels", 80)
        mel = whisper.log_mel_spectrogram(audio, n_mels=n_mels).to(self.model.device)
        
        _, probs = self.model.detect_language(mel)
        detected_lang = max(probs, key=probs.get)
        confidence_value = probs[detected_lang]
        if hasattr(confidence_value, 'item'):
            confidence = confidence_value.item()
        else:
            confidence = float(confidence_value)
        
        return detected_lang, confidence
    
    def transcribe_to_urdu(
        self,
        audio: np.ndarray,
        input_language: Optional[str] = None,
        translation_target: str = "ur"
    ) -> Dict:
        """
        Transcribe audio in source language and translate to target language
        
        Args:
            audio: Audio array (numpy array)
            input_language: Input language code (None for auto-detect)
            translation_target: Target language for translation ("ur" or "en")
            
        Returns:
            Dictionary with original transcription and translation
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        audio = np.asarray(audio, dtype=np.float32)
        if len(audio.shape) > 1:
            audio = audio.flatten()
        if not audio.flags['C_CONTIGUOUS']:
            audio = np.ascontiguousarray(audio)
        audio = whisper.pad_or_trim(audio)
        
        if input_language and input_language != "auto":
            lang_code = input_language
        else:
            detected_lang, confidence = self.detect_language(audio)
            lang_code = detected_lang
            
            if confidence < 0.5:
                lang_code = "sd"
        
        needs_translation = lang_code in ["sd", "ps", "bal"]
        
        if lang_code == "ur":
            source_lang = "ur"
        elif lang_code == "hi":
            source_lang = "ur"
        elif lang_code == "sd":
            source_lang = "sd"
        elif lang_code == "ps":
            source_lang = "ps"
        elif lang_code == "pa":
            source_lang = "pa"
        elif lang_code == "bal":
            source_lang = "sd"
        else:
            source_lang = lang_code
        
        force_urdu_script = (lang_code in ["hi", "ur"] or (input_language and input_language == "ur"))
        
        if force_urdu_script:
            source_lang = "ur"
        
        high_memory_models = {"large", "large-v2", "large-v3", "large-v3-turbo", "turbo"}
        
        if self.model_size in high_memory_models and self.device == "cuda":
            beam_size = 3
            best_of = 3
        else:
            beam_size = 5
            best_of = 5
        
        transcribe_options = {
            "task": "transcribe",
            "language": source_lang,
            "fp16": self.device == "cuda" and not self._cuda_failed,
            "verbose": True,
            "beam_size": beam_size,
            "best_of": best_of,
            "temperature": (0.0, 0.2, 0.4),
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
            "condition_on_previous_text": True,
        }
        
        if force_urdu_script:
            transcribe_options["initial_prompt"] = "یہ اردو میں ہے"
        
        print(f"Starting Whisper transcription with language={source_lang}, device={self.device}, model_size={self.model_size}")
        print(f"Audio length: {len(audio)} samples, duration: ~{len(audio) / 16000:.1f} seconds")
        try:
            print("Calling model.transcribe()...")
            original_result = self.model.transcribe(audio, **transcribe_options)
            print(f"model.transcribe() completed! Got {len(original_result.get('segments', []))} segments")
        except RuntimeError as e:
            if "cuda" in str(e).lower() and ("timeout" in str(e).lower() or "launch" in str(e).lower()) and self.device == "cuda":
                print("CUDA timeout detected. Falling back to CPU...")
                self.device = "cpu"
                self._cuda_failed = True
                transcribe_options["fp16"] = False
                if not self.model or self.model.device.type != "cpu":
                    self.model = whisper.load_model(self.model_size, device="cpu")
                original_result = self.model.transcribe(audio, **transcribe_options)
            else:
                raise
        
        print("Processing transcription segments...")
        all_segments = original_result.get("segments", [])
        print(f"Total segments: {len(all_segments)}")
        
        filtered_segments = self._filter_segments_light(all_segments)
        print(f"Filtered segments: {len(filtered_segments)}")
        
        if not filtered_segments:
            filtered_segments = [seg for seg in all_segments if seg.get("text", "").strip()]
        
        original_text = " ".join([seg.get("text", "").strip() for seg in filtered_segments if seg.get("text", "").strip()])
        print(f"Original text extracted, length: {len(original_text)} characters")
        
        detected_hindi_script = self._contains_hindi_script(original_text)
        if detected_hindi_script and force_urdu_script:
            print("Warning: Detected Hindi script in output, attempting to force Urdu...")
            transcribe_options_retry = transcribe_options.copy()
            transcribe_options_retry["language"] = "ur"
            transcribe_options_retry["initial_prompt"] = "یہ اردو میں ہے"
            transcribe_options_retry["temperature"] = (0.0,)
            try:
                retry_result = self.model.transcribe(audio, **transcribe_options_retry)
                retry_segments = retry_result.get("segments", [])
                retry_filtered = self._filter_segments_light(retry_segments)
                if retry_filtered:
                    original_text = " ".join([seg.get("text", "").strip() for seg in retry_filtered if seg.get("text", "").strip()])
                    if not self._contains_hindi_script(original_text):
                        filtered_segments = retry_filtered
                        print("Successfully obtained Urdu script output")
            except Exception as e:
                print(f"Retry with Urdu forcing failed: {e}")
        
        urdu_text = ""
        english_text = ""
        urdu_segments = []
        english_segments = []
        
        print(f"Checking if English translation needed. source_lang={source_lang}")
        if source_lang != "en":
            print("Starting English translation...")
            if self.model_size in high_memory_models and self.device == "cuda":
                beam_size = 3
                best_of = 3
            else:
                beam_size = 5
                best_of = 5
            
            translate_options_en = {
                "task": "translate",
                "language": source_lang,
                "fp16": self.device == "cuda" and not self._cuda_failed,
                "verbose": True,
                "beam_size": beam_size,
                "best_of": best_of,
                "temperature": (0.0, 0.2, 0.4),
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
                "condition_on_previous_text": True,
            }
            
            try:
                print("Calling model.transcribe() for English translation...")
                translation_result_en = self.model.transcribe(audio, **translate_options_en)
                print("English translation completed!")
            except RuntimeError as e:
                if "cuda" in str(e).lower() and "timeout" in str(e).lower() and self.device == "cuda":
                    print("CUDA timeout during translation. Using CPU...")
                    self.device = "cpu"
                    self._cuda_failed = True
                    translate_options_en["fp16"] = False
                    if not self.model or self.model.device.type != "cpu":
                        self.model = whisper.load_model(self.model_size, device="cpu")
                    translation_result_en = self.model.transcribe(audio, **translate_options_en)
                else:
                    raise
            translation_segments_raw_en = translation_result_en.get("segments", [])
            english_segments = self._filter_segments_light(translation_segments_raw_en)
            
            if not english_segments:
                english_segments = [seg for seg in translation_segments_raw_en if seg.get("text", "").strip()]
            
            english_text = " ".join([seg.get("text", "").strip() for seg in english_segments if seg.get("text", "").strip()])
        
        if source_lang == "en":
            english_text = original_text
            english_segments = filtered_segments
        
        if source_lang == "ur":
            urdu_text = original_text
            urdu_segments = filtered_segments
        elif needs_translation:
            print(f"Translation needed for language: {source_lang}")
            if not self.translator_loaded:
                print("Loading translator...")
                self._load_translator()
                print("Translator loading attempted, status:", self.translator_loaded)
            if self.translator and self.translator.is_available():
                print(f"Translating from {source_lang} to Urdu using offline translator...")
                print(f"Text length to translate: {len(original_text)} characters")
                try:
                    urdu_text = self.translator.translate(original_text, source_lang, "ur")
                    print(f"Translation completed, translated text length: {len(urdu_text)} characters")
                    if filtered_segments:
                        print(f"Translating {len(filtered_segments)} segments...")
                        urdu_segments = self.translator.translate_segments(filtered_segments, source_lang, "ur")
                        print("Segment translation completed!")
                    else:
                        urdu_segments = []
                    print("Translation to Urdu completed!")
                except Exception as e:
                    print(f"Warning: Translation to Urdu failed: {e}")
                    import traceback
                    print(traceback.format_exc())
                    print("Using original transcription as fallback...")
                    urdu_text = original_text
                    urdu_segments = filtered_segments
            else:
                translator_available = self.translator.is_available() if self.translator else False
                print(f"Translator not available. Using original text. Translator loaded: {self.translator_loaded}, Available: {translator_available}")
                urdu_text = original_text
                urdu_segments = filtered_segments
        else:
            urdu_text = original_text
            urdu_segments = filtered_segments
        
        return {
            "original_text": original_text.strip(),
            "urdu_text": urdu_text.strip(),
            "english_text": english_text.strip(),
            "original_language": original_result.get("language", "unknown"),
            "urdu_segments": urdu_segments,
            "english_segments": english_segments,
            "text": urdu_text.strip() if urdu_text else english_text.strip()
        }
    
    def _translate_to_urdu(self, text: str, source_lang: str) -> str:
        """
        Return original text (offline mode - no translation to Urdu)
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Original text (since Urdu translation requires internet)
        """
        return text
    
    def _filter_segments_light(self, segments: List[Dict]) -> List[Dict]:
        """
        Light filtering - only removes obviously bad segments
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Filtered list of segments
        """
        filtered = []
        
        for segment in segments:
            text = segment.get("text", "").strip()
            
            if not text:
                continue
            
            if len(text) < 1:
                continue
            
            if self._is_extremely_repetitive(text):
                continue
            
            if self._is_completely_nonsensical(text):
                continue
            
            filtered.append(segment)
        
        return filtered
    
    def _filter_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Filter out repetitive, nonsensical, or low-quality segments
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Filtered list of segments
        """
        return self._filter_segments_light(segments)
    
    def _is_duplicate(self, text: str, seen_texts: set) -> bool:
        """
        Check if text is a duplicate or very similar to seen texts
        
        Args:
            text: Text to check
            seen_texts: Set of previously seen texts (lowercase)
            
        Returns:
            True if duplicate or very similar
        """
        text_lower = text.lower().strip()
        
        if text_lower in seen_texts:
            return True
        
        words = set(text_lower.split())
        if len(words) < 3:
            return False
        
        for seen in seen_texts:
            seen_words = set(seen.split())
            if len(seen_words) < 3:
                continue
            
            overlap = len(words & seen_words) / len(words | seen_words)
            if overlap > 0.8:
                return True
        
        return False
    
    def _is_repetitive(self, text: str) -> bool:
        """
        Check if text is repetitive (e.g., "ھاہاں ھاہاں ھاہاں")
        
        Args:
            text: Text to check
            
        Returns:
            True if repetitive
        """
        if len(text) < 4:
            return False
        
        words = text.split()
        if len(words) < 2:
            return False
        
        if len(words) >= 3:
            unique_words = set(words)
            if len(unique_words) < len(words) * 0.3:
                return True
        
        for word in words:
            if len(word) > 1:
                if word * 2 in text and text.count(word) >= 3:
                    return True
        
        if len(words) >= 2:
            first_word = words[0]
            if words.count(first_word) >= len(words) * 0.5:
                return True
        
        return False
    
    def _is_completely_nonsensical(self, text: str) -> bool:
        """
        Check if text is completely nonsensical (only periods, single characters repeated, etc.)
        
        Args:
            text: Text to check
            
        Returns:
            True if completely nonsensical
        """
        text_clean = text.replace(" ", "").replace("۔", "").replace(".", "")
        if len(text_clean) == 0:
            return True
        
        if len(set(text_clean)) == 1 and len(text_clean) > 5:
            return True
        
        if text.count("۔") > len(text) * 0.7:
            return True
        
        return False
    
    def _is_nonsensical(self, text: str) -> bool:
        """
        Check if text is nonsensical (only periods, single characters repeated, etc.)
        
        Args:
            text: Text to check
            
        Returns:
            True if nonsensical
        """
        return self._is_completely_nonsensical(text)
    
    def _contains_hindi_script(self, text: str) -> bool:
        """
        Check if text contains Hindi (Devanagari) script characters
        
        Args:
            text: Text to check
            
        Returns:
            True if text contains Hindi script characters
        """
        if not text:
            return False
        
        devanagari_range = range(0x0900, 0x097F + 1)
        for char in text:
            if ord(char) in devanagari_range:
                return True
        return False
    
    def _is_extremely_repetitive(self, text: str) -> bool:
        """
        Check if text is extremely repetitive (e.g., same word 5+ times)
        
        Args:
            text: Text to check
            
        Returns:
            True if extremely repetitive
        """
        if len(text) < 6:
            return False
        
        words = text.split()
        if len(words) < 3:
            return False
        
        for word in words:
            if len(word) > 1 and text.count(word) >= 5:
                return True
        
        if len(words) >= 3:
            unique_words = set(words)
            if len(unique_words) < len(words) * 0.2:
                return True
        
        return False
    
    def _has_low_confidence(self, segment: Dict) -> bool:
        """
        Check if segment has low confidence
        
        Args:
            segment: Segment dictionary
            
        Returns:
            True if low confidence
        """
        if "no_speech_prob" in segment:
            if segment["no_speech_prob"] > 0.5:
                return True
        
        if "compression_ratio" in segment:
            if segment["compression_ratio"] > 2.4:
                return True
        
        return False
    
    def transcribe_chunks(
        self,
        audio_chunks: List[np.ndarray],
        input_language: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        chunk_duration: float = 30.0,
        translation_target: str = "ur"
    ) -> Dict:
        """
        Transcribe multiple audio chunks and combine results with translation
        
        Args:
            audio_chunks: List of audio arrays
            input_language: Input language code
            progress_callback: Optional callback function(current, total)
            chunk_duration: Duration of each chunk in seconds (for timestamp calculation)
            translation_target: Target language for translation ("ur" or "en")
            
        Returns:
            Combined transcription result with translation
        """
        if len(audio_chunks) == 1:
            return self.transcribe_to_urdu(audio_chunks[0], input_language, translation_target)
        
        all_urdu_segments = []
        all_english_segments = []
        urdu_text_parts = []
        english_text_parts = []
        
        total_chunks = len(audio_chunks)
        
        for i, chunk in enumerate(audio_chunks):
            if progress_callback:
                progress_callback(i + 1, total_chunks)
            
            result = self.transcribe_to_urdu(chunk, input_language, translation_target)
            
            if self.device == "cuda":
                torch.cuda.empty_cache()
            
            if result.get("urdu_segments"):
                chunk_offset = i * chunk_duration
                for segment in result["urdu_segments"]:
                    segment["start"] += chunk_offset
                    segment["end"] += chunk_offset
                    all_urdu_segments.append(segment)
            
            if result.get("english_segments"):
                chunk_offset = i * chunk_duration
                for segment in result["english_segments"]:
                    segment["start"] += chunk_offset
                    segment["end"] += chunk_offset
                    all_english_segments.append(segment)
            
            if result.get("urdu_text"):
                urdu_text_parts.append(result["urdu_text"])
            
            if result.get("english_text"):
                english_text_parts.append(result["english_text"])
        
        combined_urdu = " ".join(urdu_text_parts)
        combined_english = " ".join(english_text_parts)
        
        deduplicated_urdu_segments = self._deduplicate_segments_simple(all_urdu_segments)
        deduplicated_english_segments = self._deduplicate_segments_simple(all_english_segments)
        
        return {
            "original_text": result.get("original_text", "").strip(),
            "urdu_text": combined_urdu.strip(),
            "english_text": combined_english.strip(),
            "original_language": result.get("original_language", "unknown"),
            "urdu_segments": deduplicated_urdu_segments,
            "english_segments": deduplicated_english_segments,
            "text": combined_urdu.strip() if combined_urdu else combined_english.strip()
        }
    
    def _deduplicate_text_parts(self, text_parts: List[str]) -> List[str]:
        """
        Remove duplicate or very similar text parts
        
        Args:
            text_parts: List of text strings
            
        Returns:
            Deduplicated list
        """
        if not text_parts:
            return []
        
        seen = set()
        deduplicated = []
        
        for text in text_parts:
            text_clean = text.strip()
            if not text_clean:
                continue
            
            text_lower = text_clean.lower()
            
            if text_lower in seen:
                continue
            
            is_duplicate = False
            for seen_text in seen:
                if self._texts_are_similar(text_clean, seen_text):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen.add(text_lower)
                deduplicated.append(text_clean)
        
        return deduplicated
    
    def _deduplicate_segments_simple(self, segments: List[Dict]) -> List[Dict]:
        """
        Simple deduplication - only remove exact duplicates
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Deduplicated list of segments
        """
        if not segments:
            return []
        
        seen_texts = set()
        deduplicated = []
        
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            text_lower = text.lower()
            
            if text_lower not in seen_texts:
                seen_texts.add(text_lower)
                deduplicated.append(segment)
        
        return deduplicated
    
    def _deduplicate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Remove duplicate segments based on text content
        
        Args:
            segments: List of segment dictionaries
            
        Returns:
            Deduplicated list of segments
        """
        return self._deduplicate_segments_simple(segments)
    
    def _texts_are_similar(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """
        Check if two texts are very similar (likely duplicates)
        
        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if texts are very similar
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return False
        
        similarity = intersection / union
        return similarity >= threshold
    
    def get_model_info(self) -> Dict:
        """
        Get information about loaded model
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_size": self.model_size,
            "device": self.device,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        }

