"""
Offline translation module using NLLB (No Language Left Behind) model
Works completely offline without internet connection
"""

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OfflineTranslator:
    """
    Offline translator using NLLB model for multilingual translation
    Supports translation to Urdu and English from Sindhi, Pashto, and other languages
    """
    
    LANGUAGE_CODES = {
        "ur": "urd_Arab",
        "en": "eng_Latn",
        "sd": "snd_Arab",
        "ps": "pus_Arab",
        "pa": "pan_Guru",
        "hi": "hin_Deva",
    }
    
    def __init__(self, device: Optional[str] = None, model_size: str = "600M"):
        """
        Initialize offline translator
        
        Args:
            device: Device to use (cuda, cpu, or None for auto-detect)
            model_size: Model size - "600M" (recommended) or "1.3B" (larger, slower)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_size = model_size
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """
        Load NLLB translation model
        Model is downloaded once and cached locally for offline use
        """
        try:
            model_sizes = {
                "600M": "facebook/nllb-200-distilled-600M",
                "1.3B": "facebook/nllb-200-1.3B",
                "3.3B": "facebook/nllb-200-3.3B"
            }
            model_name = model_sizes.get(self.model_size, model_sizes["600M"])
            logger.info(f"Loading NLLB {self.model_size} model ({model_name}) on {self.device}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            self.model = self.model.to(self.device)
            self.model.eval()
            
            logger.info("NLLB model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load NLLB model: {e}")
            if self.device == "cuda":
                logger.info("Falling back to CPU...")
                try:
                    self.device = "cpu"
                    model_sizes = {
                        "600M": "facebook/nllb-200-distilled-600M",
                        "1.3B": "facebook/nllb-200-1.3B",
                        "3.3B": "facebook/nllb-200-3.3B"
                    }
                    model_name = model_sizes.get(self.model_size, model_sizes["600M"])
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                    self.model = self.model.to(self.device)
                    self.model.eval()
                    logger.info("NLLB model loaded on CPU successfully!")
                except Exception as e2:
                    raise RuntimeError(f"Failed to load NLLB model on CPU: {str(e2)}")
            else:
                raise RuntimeError(f"Failed to load NLLB model: {str(e)}")
    
    def _get_nllb_code(self, lang_code: str) -> str:
        """
        Convert language code to NLLB format
        
        Args:
            lang_code: Standard language code (ur, en, sd, ps, etc.)
            
        Returns:
            NLLB language code
        """
        return self.LANGUAGE_CODES.get(lang_code, "eng_Latn")
    
    def translate(self, text: str, source_lang: str, target_lang: str, max_length: int = 512) -> str:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (sd, ps, ur, en, etc.)
            target_lang: Target language code (ur, en, etc.)
            max_length: Maximum length for translation (default 512)
            
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return ""
        
        if source_lang == target_lang:
            return text
        
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Translation model not loaded")
        
        try:
            source_code = self._get_nllb_code(source_lang)
            target_code = self._get_nllb_code(target_lang)
            
            if target_code not in self.tokenizer.lang_code_to_id:
                logger.warning(f"Target language code {target_code} not supported by NLLB. Returning original text.")
                return text
            
            self.tokenizer.src_lang = source_code
            
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.tokenizer.lang_code_to_id[target_code],
                    max_length=max_length,
                    num_beams=5,
                    early_stopping=True
                )
            
            translated_text = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
            return translated_text.strip()
        
        except KeyError as e:
            logger.error(f"Language code not found in tokenizer: {e}")
            logger.info(f"Available language codes: {list(self.tokenizer.lang_code_to_id.keys())[:10]}...")
            return text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    def translate_segments(self, segments: list, source_lang: str, target_lang: str) -> list:
        """
        Translate a list of segments with timestamps
        
        Args:
            segments: List of segment dictionaries with 'text' field
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated segments with original timestamps
        """
        translated_segments = []
        
        for segment in segments:
            original_text = segment.get("text", "").strip()
            if not original_text:
                translated_segments.append(segment)
                continue
            
            translated_text = self.translate(original_text, source_lang, target_lang)
            
            translated_segment = segment.copy()
            translated_segment["text"] = translated_text
            translated_segments.append(translated_segment)
        
        return translated_segments
    
    def is_available(self) -> bool:
        """
        Check if translation model is loaded and available
        
        Returns:
            True if model is ready
        """
        return self.model is not None and self.tokenizer is not None

