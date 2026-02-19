"""
Speech-to-Text service using HuggingFace Transformers (Whisper) for SpeechMaster.
Optimized for 16kHz mono input from AudioService.
"""
import logging
import time
from pathlib import Path
from typing import Optional

import numpy as np

from app.utils.config import (
    WHISPER_MODEL_ID,
    WHISPER_DEVICE,
    AUDIO_SAMPLE_RATE,
)

logger = logging.getLogger(__name__)

class STTService:
    """Offline speech-to-text using HuggingFace Whisper models."""

    def __init__(self):
        self._model = None
        self._processor = None
        self._initialized = False
        self._model_id = WHISPER_MODEL_ID

    def initialize(self, model_id: str = None) -> bool:
        """Load the Whisper model and processor."""
        model_id = model_id or self._model_id

        try:
            import torch
            from transformers import WhisperProcessor, WhisperForConditionalGeneration

            logger.info("Loading Whisper model '%s' ...", model_id)

            self._processor = WhisperProcessor.from_pretrained(model_id)
            self._model = WhisperForConditionalGeneration.from_pretrained(model_id)
            self._model.to(WHISPER_DEVICE)
            self._model.eval()

            self._initialized = True
            self._model_id = model_id

            params = sum(p.numel() for p in self._model.parameters())
            logger.info(
                "Whisper model loaded: %s (%.1fM params, device=%s)",
                model_id, params / 1e6, WHISPER_DEVICE,
            )
            return True

        except Exception as e:
            logger.error("Failed to initialize Whisper: %s", e)
            self._initialized = False
            return False

    @property
    def is_available(self) -> bool:
        return self._initialized

    def transcribe_audio(self, audio_path: str) -> dict:
        """Transcribe 16kHz WAV file to text."""
        if not self._initialized:
            return {'success': False, 'message': 'STT engine not initialized.'}

        if not Path(audio_path).exists():
            return {'success': False, 'message': f'File not found: {audio_path}'}

        start_time = time.time()

        try:
            import torch
            import soundfile as sf

            # 1. Load audio - soundfile is fast and reliable
            audio_data, sample_rate = sf.read(audio_path, dtype='float32')

            # 2. Safety Check (AudioService should have handled this, but good for stability)
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)
            
            # 3. Prepare features
            # No resampling needed anymore because AudioService records at 16k!
            input_features = self._processor(
                audio_data,
                sampling_rate=AUDIO_SAMPLE_RATE,
                return_tensors="pt",
            ).input_features.to(WHISPER_DEVICE)

            # 4. Generate
            with torch.no_grad():
                predicted_ids = self._model.generate(
                    input_features,
                    max_new_tokens=128,
                    language="en",
                    task="transcribe",
                )

            # 5. Decode
            transcription = self._processor.batch_decode(
                predicted_ids, skip_special_tokens=True
            )[0].strip()

            processing_time = time.time() - start_time
            logger.info("Transcription (%.1fs): %s", processing_time, transcription[:50])

            return {
                'success': True,
                'transcription': transcription,
                'processing_time': round(processing_time, 2),
                'message': 'Transcription successful.',
            }

        except Exception as e:
            logger.error("Transcription failed: %s", e)
            return {
                'success': False,
                'processing_time': round(time.time() - start_time, 2),
                'message': str(e),
            }
