# VoiceNote Therapy Edge Device

A collaborative, open-source codebase for the VoiceNote Therapy Edge Device—combining a modern UI with powerful backend services for voice therapy applications.

## Features

- **PySide6 UI**: Intuitive graphical interface for therapy sessions
- **Voice Captioning**: Real-time speech-to-text capabilities
- **Prompt Voices**: Dynamic voice generation and management
- **Edge Processing**: Optimized for edge device deployment

## Project Structure

```
voicenote_edge_device/
├── assets/               # Application assets
├── services/             # Core backend services
│   ├── captioning/       # Voice captioning module
│   ├── voice_prompt/     # Prompt voice management
│   └── ...
├── ui/                   # PySide6 UI components
├── .gitignore
├── README.md
├── requirements.txt
└── venv/                 # Virtual environment
```

## Setup

### Prerequisites
- Python 3.8+
- pip

### Environment Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/jamesriri/voicenote_edge_device.git
    cd voicenote_edge_device
    ```

2. Create a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

From the project root directory:

```bash
python app/main.py
```

## Contributing

We welcome contributions! Please follow our contribution guidelines and submit pull requests.

## License

This project is licensed under the Apache License 2.0. See the LICENSE file for details.
