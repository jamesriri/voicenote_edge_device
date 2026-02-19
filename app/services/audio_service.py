"""
Audio recording and playback service for SpeechMaster.
Optimized for 16kHz Whisper compatibility via ALSA plughw resampling.
"""
import logging
import os
import signal
import subprocess
import threading
import wave
import re
from pathlib import Path
from typing import Optional, Callable

# Importing constants from your config
from app.utils.config import (
    AUDIO_SAMPLE_RATE, # Should be 16000
    AUDIO_CHANNELS,    # Should be 1
    MAX_RECORDING_DURATION,
    MIN_RECORDING_DURATION,
    MAX_AUDIO_FILE_SIZE,
)

logger = logging.getLogger(__name__)

class AudioService:
    """Handles audio recording and playback via system calls (arecord/aplay)."""

    def __init__(self):
        self._is_recording = False
        self._is_playing = False
        self._record_proc: Optional[subprocess.Popen] = None
        self._play_proc: Optional[subprocess.Popen] = None
        
        # Hardware configuration
        self.target_mic_name = "UACDemoV10"
        self._input_device = self._find_mic_device(self.target_mic_name) or "default"
        self._output_device = "default"
        
        logger.info(f"AudioService initialized. Using input device: {self._input_device}")

    def _find_mic_device(self, card_name: str) -> Optional[str]:
        """Auto-detects the 'plughw' address for the specified microphone."""
        try:
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return None
            
            pattern = rf"card (\d+):.*{card_name}.*device (\d+):"
            match = re.search(pattern, result.stdout, re.IGNORECASE)
            
            if match:
                card_no = match.group(1)
                device_no = match.group(2)
                return f"plughw:CARD={card_no},DEV={device_no}"
        except Exception as e:
            logger.error(f"Hardware detection error: {e}")
        return None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def current_level(self) -> float:
        """Real-time levels are disabled for stability; returns 0.0."""
        return 0.0

    def check_microphone(self) -> bool:
        """Verifies if the target microphone is still connected."""
        device = self._find_mic_device(self.target_mic_name)
        return device is not None

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------
    def start_recording(
        self,
        output_path: str,
        duration: int = MAX_RECORDING_DURATION,
        level_callback: Optional[Callable[[float], None]] = None,
        done_callback: Optional[Callable[[dict], None]] = None,
    ):
        """Starts recording to a WAV file in a background thread."""
        if self._is_recording:
            logger.warning("Already recording.")
            return

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        self._is_recording = True

        def _record_thread():
            try:
                # Refresh device location in case of replugging
                device = self._find_mic_device(self.target_mic_name) or "default"
                
                cmd = [
                    'arecord',
                    '-D', device,
                    '-f', 'S16_LE',
                    '-r', str(AUDIO_SAMPLE_RATE),
                    '-c', str(AUDIO_CHANNELS),
                    '-d', str(duration),
                    '-t', 'wav',
                    output_path
                ]
                
                logger.info(f"Starting recording: {' '.join(cmd)}")
                self._record_proc = subprocess.Popen(cmd)
                self._record_proc.wait()

                # Cleanup and result verification
                success = os.path.exists(output_path) and os.path.getsize(output_path) > 44
                actual_duration = 0.0
                
                if success:
                    with wave.open(output_path, 'rb') as wf:
                        actual_duration = wf.getnframes() / float(wf.getframerate())

                result = {
                    'success': success,
                    'audio_path': output_path if success else '',
                    'duration': round(actual_duration, 2),
                    'file_size': os.path.getsize(output_path) if success else 0,
                    'message': 'Recording saved successfully.' if success else 'Recording failed.',
                }

                if done_callback:
                    done_callback(result)

            except Exception as e:
                logger.error(f"Recording process failed: {e}")
                if done_callback:
                    done_callback({'success': False, 'message': str(e)})
            finally:
                self._is_recording = False
                self._record_proc = None

        threading.Thread(target=_record_thread, daemon=True).start()

    def stop_recording(self):
        """Gracefully stops the arecord process."""
        if self._record_proc and self._is_recording:
            # SIGINT (Ctrl+C) allows arecord to finish writing the WAV header
            self._record_proc.send_signal(signal.SIGINT)
            self._is_recording = False
            logger.info("Recording manually stopped.")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_recording(self, audio_path: str) -> dict:
        """Checks if the recording exists and matches Whisper requirements."""
        issues = []
        if not os.path.exists(audio_path):
            return {'valid': False, 'issues': ['file_not_found'], 'message': 'File not found.'}

        try:
            with wave.open(audio_path, 'rb') as wf:
                params = wf.getparams()
                duration = params.nframes / float(params.framerate)

                if duration < MIN_RECORDING_DURATION:
                    issues.append('too_short')
                if params.framerate != 16000:
                    issues.append('wrong_sample_rate')
                if params.nchannels != 1:
                    issues.append('not_mono')
            
            if os.path.getsize(audio_path) > MAX_AUDIO_FILE_SIZE:
                issues.append('too_large')
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            issues.append('corrupted')

        valid = len(issues) == 0
        return {
            'valid': valid,
            'issues': issues,
            'message': "Recording is valid." if valid else f"Issues: {', '.join(issues)}"
        }

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------
    def play_audio(self, file_path: str, done_callback: Optional[Callable] = None):
        """Plays audio using aplay."""
        if self._is_playing:
            self.stop_playback()

        def _play_thread():
            self._is_playing = True
            try:
                # Using 'default' for playback is usually safest on Pi
                self._play_proc = subprocess.Popen(['aplay', '-D', self._output_device, file_path])
                self._play_proc.wait()
            except Exception as e:
                logger.error(f"Playback failed: {e}")
            finally:
                self._is_playing = False
                self._play_proc = None
                if done_callback:
                    done_callback()

        threading.Thread(target=_play_thread, daemon=True).start()

    def stop_playback(self):
        """Stops the aplay process."""
        if self._play_proc:
            self._play_proc.terminate()
            self._is_playing = False
