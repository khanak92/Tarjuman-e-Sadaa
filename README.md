# Multilingual Speech-to-Urdu Transcription System (MSTUTS)

A lightweight, offline-capable tool that converts Sindhi, Pashto, Balochi, Punjabi, and Urdu speech into Urdu written text using AI-based Automatic Speech Recognition (ASR).

## Features

- **Multilingual Support**: Recognizes Sindhi, Pashto, Balochi, Punjabi, and Urdu speech
- **Urdu Transcription**: Converts all recognized speech (Sindhi, Pashto, Balochi, Punjabi, Urdu) into Urdu script text
- **Offline Capability**: Works completely offline using Whisper models
- **GPU Acceleration**: Optimized for NVIDIA GPUs (CUDA support)
- **Audio Formats**: Supports MP3, WAV, M4A, MPEG, MP4, WEBM files
- **Language Auto-Detection**: Automatically detects input language
- **User-Friendly GUI**: Simple Windows interface for easy operation

## Important Notes

- **Language Support**: Whisper supports Urdu (ur), Pashto (ps), Punjabi (pa), and Sindhi (sd). Balochi (bal) may have limited support and may need to use auto-detection.
- **Script Output**: All transcriptions are output in Urdu script, regardless of input language. The system detects the input language for better accuracy but always produces Urdu script output.
- **Note**: For best results with non-Urdu languages, manually select the input language in the GUI (e.g., "sd" for Sindhi) to help the model recognize the speech correctly, even though output will be in Urdu script.

## System Requirements

- **OS**: Windows 10 (64-bit) or later
- **RAM**: 16 GB recommended
- **GPU**: NVIDIA GPU with CUDA support (optional, CPU mode available)
- **Storage**: SSD recommended for faster processing
- **Python**: 3.8 or higher

## Installation

### Step 1: Install Python
Install Python 3.8 or higher from [python.org](https://www.python.org/)

### Step 2: Install FFmpeg

**Option A: Automatic Installation (Recommended)**
1. Right-click `install_ffmpeg.bat` and select "Run as Administrator"
2. Follow the prompts - it will download and install FFmpeg automatically
3. Restart your terminal/command prompt after installation

**Option B: Manual Installation**
1. Download FFmpeg from [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (Windows builds)
   - Or visit [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg` (or your preferred location)
3. Add to system PATH:
   - Press `Win + X`, select "System"
   - Click "Advanced system settings" → "Environment Variables"
   - Under "System variables", select "Path" → "Edit"
   - Click "New" and add: `C:\ffmpeg\bin` (or your FFmpeg bin path)
   - Click OK on all dialogs
4. Restart your terminal/command prompt

**Verify FFmpeg installation:**
```bash
ffmpeg -version
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Note:** If you have TensorFlow installed and encounter numpy version conflicts, the requirements.txt is configured to use a compatible numpy version (1.22.0-1.23.x).

### Step 4: Verify Setup
Run the setup verification script:
```bash
python setup_check.py
```

### Step 5: Download Whisper Models
Models will be automatically downloaded on first run:
- Medium model: ~1.4 GB (default)
- Large-v3 model: ~3.0 GB (optional, better accuracy - select in GUI)

## Usage

Run the application:
```bash
python main.py
```

### Using the GUI:

1. **Upload Audio**: Click "Select Audio File" and choose your audio file (MP3, WAV, M4A)
2. **Select Language** (optional): Choose input language or leave as "Auto-detect"
3. **Process**: Click "Transcribe" to start transcription
4. **Download**: Once complete, click "Save Transcription" to export Urdu text

## Performance

- **Transcription Speed**: 1.0-1.5× realtime on GPU
- **Accuracy**:
  - Sindhi/Urdu/Punjabi: 80-95%
  - Pashto/Balochi: 65-85%
- **Max File Size**: Up to 2 hours audio

## Model Selection

The application uses Whisper Medium by default. For better accuracy (especially for Pashto/Balochi), you can switch to Large-v3 in the settings, but it requires more VRAM and processing time.

## License

MIT License

