# Offline Translation Feature

This system now includes **offline translation** capabilities for Sindhi, Pashto, and Balochi audio to Urdu and English.

## How It Works

### Transcription + Translation Workflow

1. **Audio Detection**: System detects the language (Sindhi, Pashto, etc.)
2. **Native Transcription**: Audio is transcribed in the **original language** (preserving meaning)
3. **Offline Translation**: Transcribed text is translated to Urdu using NLLB (No Language Left Behind) model
4. **English Translation**: Whisper's built-in translation provides English output

### Languages Supported

- **Sindhi (sd)** → Urdu + English
- **Pashto (ps)** → Urdu + English  
- **Balochi (bal)** → Urdu + English (transcribed as Sindhi, then translated)
- **Urdu (ur)** → Urdu + English (direct transcription)
- **Hindi (hi)** → Urdu + English (converted to Urdu)
- **Punjabi (pa)** → Punjabi + English (direct transcription)

## Technical Details

### Offline Translator

- **Model**: Facebook NLLB-200 (600M parameters)
- **Library**: Transformers (Hugging Face)
- **Device**: Uses GPU (CUDA) if available, falls back to CPU
- **Offline**: Works completely offline after initial model download

### Model Download

The NLLB model (~2.3 GB) is downloaded automatically on first use and cached locally. You need internet connection **only once** for the initial download. After that, the system works completely offline.

**Download location**: `~/.cache/huggingface/hub/` (automatically managed)

## Installation

### New Dependencies

```bash
pip install transformers>=4.30.0 sentencepiece>=0.1.99
```

Or update requirements:

```bash
pip install -r requirements.txt
```

### First Run

1. Run the application normally
2. When you transcribe Sindhi/Pashto audio for the first time, the translator model will download automatically
3. Wait for download to complete (~2-3 GB, ~5-10 minutes depending on internet speed)
4. After first use, the model is cached and works offline

## Usage

### In GUI Application

1. Select audio file (Sindhi/Pashto)
2. Choose language (or use Auto-detect)
3. Click "Transcribe"
4. System will:
   - Transcribe in original language
   - Translate to Urdu
   - Translate to English
5. View results in Urdu/English tabs

### In Web Application

Same workflow - the webapp automatically uses the offline translator when needed.

## Translation Quality

- **NLLB-600M**: Good quality for common phrases and sentences
- **Context-Aware**: Translates whole sentences, preserving meaning
- **Script Conversion**: Converts to Urdu script (Nastaliq) automatically

## Performance

- **Translation Speed**: ~1-2 seconds per sentence (GPU), ~3-5 seconds (CPU)
- **Memory Usage**: Additional ~1.5 GB RAM for translator model
- **GPU Acceleration**: Recommended for faster translation

## Troubleshooting

### Translator Not Loading

If you see: `"Warning: Failed to load offline translator"`

**Solutions:**
1. Install dependencies: `pip install transformers sentencepiece`
2. Check internet connection (first-time download only)
3. Check disk space (need ~3 GB free for model cache)

### Translation Quality Issues

- For better quality, use longer audio segments
- Ensure audio is clear and noise-free
- Some regional dialects may have lower accuracy

### Memory Issues

If you run out of memory:
1. Close other applications
2. Use smaller Whisper model (base/small instead of large)
3. The translator uses additional ~1.5 GB RAM

## Offline Mode

✅ **Fully Offline After Initial Setup**
- No internet required for transcription
- No internet required for translation
- All models stored locally

## Files Modified

- `transcription_engine.py`: Updated to use offline translator
- `offline_translator.py`: New module for NLLB translation
- `requirements.txt`: Added transformers and sentencepiece

## Language Code Mapping

| Language | Code | NLLB Code |
|----------|------|-----------|
| Urdu | ur | urd_Arab |
| English | en | eng_Latn |
| Sindhi | sd | snd_Arab |
| Pashto | ps | pus_Arab |
| Punjabi | pa | pan_Guru |
| Hindi | hi | hin_Deva |

