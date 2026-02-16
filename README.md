# SpeechMaster — Speech Learning Tool

Offline speech therapy application that helps users improve speech through sentence repetition, recording, and automated scoring. Designed for Raspberry Pi with a 7-inch touchscreen.

## Features

- **Practice Sessions** — Choose sentences of varying difficulty, listen via TTS, record your speech, and get instant accuracy scores.
- **Automatic Scoring** — Word Error Rate (WER) calculated by comparing your speech (transcribed by Whisper) against target sentences.
- **Recording History** — Browse, filter, replay, and delete past sessions.
- **User Accounts** — Secure login with bcrypt-hashed passwords, or quick Guest mode.
- **LED Feedback** — GPIO-driven LEDs indicate recording state, processing, and score results on Raspberry Pi.
- **Fully Offline** — No internet connection required. Uses Piper TTS and Whisper locally.

## Whisper Model

Custom finetuned Whisper-tiny for Kenyan English non-standard speech:

| HuggingFace ID | Parameters |
|---------------|------------|
| `cdli/whisper-tiny_finetuned_kenyan_english_nonstandard_speech_v0.9` | 37.8M |

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI | PySide6 (Qt 6) |
| TTS | Piper TTS — `en_US-amy-low` (offline, ~63 MB) |
| STT | HuggingFace Transformers — Whisper-tiny finetuned (37.8M params) |
| Audio | sounddevice + soundfile |
| Database | SQLite3 |
| Password Hashing | bcrypt |
| Scoring | Word-level Levenshtein distance |
| LED Control | RPi.GPIO (Raspberry Pi) |

## Quick Start

### 1. Install system dependencies

```bash
# Debian / Raspberry Pi OS
sudo apt-get install -y portaudio19-dev libsndfile1 ffmpeg
```

### 2. Create virtual environment and install

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Download Piper TTS model

```bash
mkdir -p models/piper
cd models/piper
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx.json
```

The Whisper model is auto-downloaded from HuggingFace on first run (requires internet once, then cached locally).

### 4. Run

```bash
python app/main.py
```

## Directory Structure

```
speech_learning_tool/
├── app/
│   ├── main.py                  # Entry point
│   ├── ui/                      # PySide6 screens
│   ├── models/                  # Data models
│   ├── services/                # Business logic
│   ├── utils/                   # Config, DB, validators
│   └── resources/               # QSS theme, sentences JSON, icons
├── data/                        # SQLite DB, user recordings, TTS cache
├── models/                      # ML model weights (Whisper, Piper)
├── requirements.txt
└── README.md
```

## Hardware Wiring (Raspberry Pi)

| LED | GPIO Pin (BCM) | Resistor |
|-----|----------------|----------|
| Green | 17 | 220 Ω |
| Orange | 27 | 220 Ω |
| Red | 22 | 220 Ω |

## Scoring

| Accuracy | Category | LED |
|----------|----------|-----|
| 70–100 % | Excellent | Green |
| 50–69 % | Good | Orange |
| 0–49 % | Needs Improvement | Red |

## License

Internal / educational use.
