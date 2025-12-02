"""
Configuration settings for MSTUTS
"""

MODEL_OPTIONS = {
    "base": "base",
    "small": "small",
    "medium": "medium",
    "large-v3": "large-v3",
    "large-v3-turbo": "large-v3-turbo"
}

DEFAULT_MODEL = "base"

SUPPORTED_LANGUAGES = {
    "auto": "Auto-detect",
    "sd": "Sindhi",
    "ps": "Pashto",
    "bal": "Balochi",
    "pa": "Punjabi",
    "ur": "Urdu"
}

SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".mpeg", ".mp4", ".webm"]

OUTPUT_TARGET_LANGUAGE = "ur"

TRANSLATION_TARGETS = {
    "ur": "Urdu",
    "en": "English"
}

DEFAULT_TRANSLATION_TARGET = "ur"

DEVICE = "cuda"

CHUNK_LENGTH_S = 30

