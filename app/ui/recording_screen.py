"""
Recording screen for SpeechMaster.
Full practice flow: selection -> playback -> recording -> processing -> score.
"""
import logging
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QScrollArea, QFrame, QProgressBar,
    QListWidget, QListWidgetItem, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, Slot, QObject

from app.models.sentence import Sentence
from app.services.scoring_service import score_recording
from app.utils.config import COLORS, MAX_RECORDING_DURATION, PIPER_VOICES

logger = logging.getLogger(__name__)


# ── Background worker for STT + scoring ──
class _ProcessingWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, stt_service, audio_path: str, target_text: str):
        super().__init__()
        self._stt = stt_service
        self._audio_path = audio_path
        self._target_text = target_text

    @Slot()
    def run(self):
        try:
            result = self._stt.transcribe_audio(self._audio_path)
            if not result['success']:
                self.error.emit(result['message'])
                return
            score = score_recording(result['transcription'], self._target_text)
            score['processing_time'] = result['processing_time']
            self.finished.emit(score)
        except Exception as e:
            logger.error("Processing worker error: %s", e)
            self.error.emit(str(e))


# ── Header bar ──
def _make_header(title_text: str, back_callback) -> tuple:
    header = QFrame()
    header.setFixedHeight(56)
    header.setStyleSheet(f"""
        QFrame {{
            background-color: #FFFFFF;
            border-bottom: 1px solid {COLORS['border']};
        }}
    """)
    h_layout = QHBoxLayout(header)
    h_layout.setContentsMargins(16, 0, 16, 0)

    back_btn = QPushButton("Back")
    back_btn.setObjectName("linkButton")
    back_btn.setCursor(Qt.PointingHandCursor)
    back_btn.clicked.connect(back_callback)
    h_layout.addWidget(back_btn)

    title = QLabel(title_text)
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {COLORS['text_dark']}; border: none;")
    h_layout.addWidget(title, 1)

    spacer = QLabel("")
    spacer.setFixedWidth(50)
    spacer.setStyleSheet("border: none;")
    h_layout.addWidget(spacer)

    return header, title


class RecordingScreen(QWidget):
    """Multi-state recording screen."""

    go_back = Signal()

    # ── Internal signal to safely cross from recording thread → main thread ──
    _recording_finished = Signal(dict)

    STATE_SELECTION = 0
    STATE_PLAYBACK = 1
    STATE_RECORDING = 2
    STATE_PROCESSING = 3
    STATE_SCORE = 4

    def __init__(self, auth_service, db, tts_service, stt_service,
                 audio_service, led_service, parent=None):
        super().__init__(parent)
        self._auth = auth_service
        self._db = db
        self._tts = tts_service
        self._stt = stt_service
        self._audio = audio_service
        self._led = led_service

        self._current_sentence: Sentence = None
        self._current_audio_path: str = ""
        self._recording_timer: QTimer = None
        self._elapsed_seconds: int = 0
        self._level_timer: QTimer = None
        self._worker_thread: QThread = None

        # Connect the thread-safe signal
        self._recording_finished.connect(self._process_recording)

        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("recordingScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header, self._header_title = _make_header("Practice", self._on_back)
        layout.addWidget(header)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_selection_page())
        self._stack.addWidget(self._build_playback_page())
        self._stack.addWidget(self._build_recording_page())
        self._stack.addWidget(self._build_processing_page())
        self._stack.addWidget(self._build_score_page())
        layout.addWidget(self._stack)

    # ==================================================================
    # Page 0 — Sentence Selection
    # ==================================================================
    def _build_selection_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Choose a Sentence")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(title)

        desc = QLabel("Tap a sentence to begin. Difficulty shown in brackets.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        layout.addWidget(desc)

        self._sentence_list = QListWidget()
        self._sentence_list.itemDoubleClicked.connect(self._on_sentence_selected)
        layout.addWidget(self._sentence_list, 1)

        select_btn = QPushButton("Select")
        select_btn.setObjectName("primaryButton")
        select_btn.setMinimumHeight(56)
        select_btn.setCursor(Qt.PointingHandCursor)
        select_btn.clicked.connect(self._on_select_clicked)
        layout.addWidget(select_btn)

        return page

    # Page 1 — TTS Playback
    def _build_playback_page(self) -> QWidget:
        from PySide6.QtWidgets import QComboBox

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 36, 28, 28)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        layout.addStretch()

        listen_label = QLabel("Listen carefully")
        listen_label.setAlignment(Qt.AlignCenter)
        listen_label.setStyleSheet(f"font-size: 18px; color: {COLORS['text_light']}; font-weight: bold;")
        layout.addWidget(listen_label)

        # Voice selector
        voice_row = QHBoxLayout()
        voice_row.setSpacing(8)
        voice_label = QLabel("Voice:")
        voice_label.setStyleSheet(f"font-size: 14px; color: {COLORS['text_light']};")
        voice_row.addStretch()
        voice_row.addWidget(voice_label)

        self._voice_combo = QComboBox()
        for key, cfg in PIPER_VOICES.items():
            self._voice_combo.addItem(cfg['label'], key)
        self._voice_combo.setFixedWidth(200)
        self._voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        voice_row.addWidget(self._voice_combo)
        voice_row.addStretch()
        layout.addLayout(voice_row)

        self._playback_sentence = QLabel("")
        self._playback_sentence.setAlignment(Qt.AlignCenter)
        self._playback_sentence.setWordWrap(True)
        self._playback_sentence.setStyleSheet(f"""
            font-size: 24px; font-weight: bold;
            color: {COLORS['text_dark']};
            padding: 28px 20px;
            background: #FFFFFF;
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
        """)
        layout.addWidget(self._playback_sentence)

        layout.addSpacing(20)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        replay_btn = QPushButton("Replay")
        replay_btn.setObjectName("outlineButton")
        replay_btn.setMinimumHeight(56)
        replay_btn.setCursor(Qt.PointingHandCursor)
        replay_btn.clicked.connect(self._play_tts)
        btn_layout.addWidget(replay_btn)

        record_btn = QPushButton("Start Recording")
        record_btn.setObjectName("primaryButton")
        record_btn.setMinimumHeight(56)
        record_btn.setCursor(Qt.PointingHandCursor)
        record_btn.clicked.connect(self._start_recording)
        btn_layout.addWidget(record_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()
        return page

    # Page 2 — Recording
    def _build_recording_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 36, 28, 28)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignCenter)

        layout.addStretch()

        self._rec_status = QLabel("Recording")
        self._rec_status.setAlignment(Qt.AlignCenter)
        self._rec_status.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {COLORS['error_red']};")
        layout.addWidget(self._rec_status)

        self._rec_sentence_display = QLabel("")
        self._rec_sentence_display.setAlignment(Qt.AlignCenter)
        self._rec_sentence_display.setWordWrap(True)
        self._rec_sentence_display.setStyleSheet(f"""
            font-size: 20px; color: {COLORS['text_dark']};
            padding: 20px; background: #FFFFFF;
            border: 1px solid {COLORS['border']};
            border-radius: 14px;
        """)
        layout.addWidget(self._rec_sentence_display)

        layout.addSpacing(8)

        self._timer_label = QLabel(f"0 / {MAX_RECORDING_DURATION}s")
        self._timer_label.setAlignment(Qt.AlignCenter)
        self._timer_label.setStyleSheet(f"font-size: 16px; color: {COLORS['text_light']}; font-weight: bold;")
        layout.addWidget(self._timer_label)

        self._timer_bar = QProgressBar()
        self._timer_bar.setRange(0, MAX_RECORDING_DURATION)
        self._timer_bar.setValue(0)
        self._timer_bar.setFixedHeight(8)
        self._timer_bar.setTextVisible(False)
        self._timer_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #E8EAED; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {COLORS['error_red']}; border-radius: 4px; }}
        """)
        layout.addWidget(self._timer_bar)

        level_label = QLabel("Input Level")
        level_label.setAlignment(Qt.AlignCenter)
        level_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']};")
        layout.addWidget(level_label)

        self._level_bar = QProgressBar()
        self._level_bar.setRange(0, 100)
        self._level_bar.setValue(0)
        self._level_bar.setFixedHeight(12)
        self._level_bar.setTextVisible(False)
        self._level_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #E8EAED; border-radius: 6px; }}
            QProgressBar::chunk {{ background-color: {COLORS['success_green']}; border-radius: 6px; }}
        """)
        layout.addWidget(self._level_bar)

        layout.addSpacing(16)

        stop_btn = QPushButton("Stop Recording")
        stop_btn.setObjectName("dangerButton")
        stop_btn.setMinimumHeight(60)
        stop_btn.setCursor(Qt.PointingHandCursor)
        stop_btn.clicked.connect(self._stop_recording)
        layout.addWidget(stop_btn)

        layout.addStretch()
        return page

    # Page 3 — Processing
    def _build_processing_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        layout.addStretch()

        label = QLabel("Analysing your speech...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(label)

        sublabel = QLabel("This may take a few seconds")
        sublabel.setAlignment(Qt.AlignCenter)
        sublabel.setStyleSheet(f"font-size: 15px; color: {COLORS['text_light']};")
        layout.addWidget(sublabel)

        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setFixedHeight(4)
        progress.setFixedWidth(260)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{ background-color: #E8EAED; border-radius: 2px; }}
            QProgressBar::chunk {{ background-color: {COLORS['primary_blue']}; border-radius: 2px; }}
        """)
        layout.addWidget(progress, alignment=Qt.AlignCenter)

        layout.addStretch()
        return page

    # Page 4 — Score Display
    def _build_score_page(self) -> QWidget:
        page = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 36, 28, 28)
        layout.setSpacing(16)

        self._score_title = QLabel("Great Job!")
        self._score_title.setAlignment(Qt.AlignCenter)
        self._score_title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(self._score_title)

        layout.addSpacing(4)

        # Score bar — use a fixed base style; color is set dynamically via property
        self._score_bar = QProgressBar()
        self._score_bar.setRange(0, 100)
        self._score_bar.setValue(0)
        self._score_bar.setFixedHeight(32)
        self._score_bar.setFormat("%v%")
        self._score_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._score_bar)

        self._score_category = QLabel("")
        self._score_category.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._score_category)

        layout.addSpacing(8)

        # Comparison card
        compare_frame = QFrame()
        compare_frame.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid {COLORS['border']};
                border-radius: 14px;
            }}
        """)
        compare_layout = QVBoxLayout(compare_frame)
        compare_layout.setContentsMargins(20, 18, 20, 18)
        compare_layout.setSpacing(14)

        your_label = QLabel("What you said")
        your_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; font-weight: bold; border: none;")
        compare_layout.addWidget(your_label)

        self._transcription_label = QLabel("")
        self._transcription_label.setWordWrap(True)
        self._transcription_label.setStyleSheet(f"font-size: 17px; color: {COLORS['text_dark']}; border: none;")
        compare_layout.addWidget(self._transcription_label)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background: {COLORS['border']}; max-height: 1px; border: none;")
        compare_layout.addWidget(div)

        target_label = QLabel("Target sentence")
        target_label.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; font-weight: bold; border: none;")
        compare_layout.addWidget(target_label)

        self._target_label = QLabel("")
        self._target_label.setWordWrap(True)
        self._target_label.setStyleSheet(f"font-size: 17px; color: {COLORS['primary_blue']}; font-weight: bold; border: none;")
        compare_layout.addWidget(self._target_label)

        layout.addWidget(compare_frame)

        layout.addSpacing(12)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        retry_btn = QPushButton("Try Again")
        retry_btn.setObjectName("outlineButton")
        retry_btn.setMinimumHeight(56)
        retry_btn.setCursor(Qt.PointingHandCursor)
        retry_btn.clicked.connect(self._retry_sentence)
        btn_layout.addWidget(retry_btn)

        next_btn = QPushButton("Next Sentence")
        next_btn.setObjectName("primaryButton")
        next_btn.setMinimumHeight(56)
        next_btn.setCursor(Qt.PointingHandCursor)
        next_btn.clicked.connect(self._next_sentence)
        btn_layout.addWidget(next_btn)

        layout.addLayout(btn_layout)

        dashboard_btn = QPushButton("Back to Dashboard")
        dashboard_btn.setObjectName("linkButton")
        dashboard_btn.setCursor(Qt.PointingHandCursor)
        dashboard_btn.clicked.connect(self.go_back.emit)
        layout.addWidget(dashboard_btn, alignment=Qt.AlignCenter)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        return page

    # Public
    def load_sentences(self):
        self._sentence_list.clear()
        sentences = self._db.get_all_sentences()
        for s in sentences:
            sentence = Sentence.from_dict(s)
            item = QListWidgetItem(f"[{sentence.difficulty_label}]  {sentence.text}")
            item.setData(Qt.UserRole, s)
            self._sentence_list.addItem(item)

    def reset(self):
        self._stack.setCurrentIndex(self.STATE_SELECTION)
        self._header_title.setText("Practice")
        self.load_sentences()

    # State transitions
    def _on_select_clicked(self):
        item = self._sentence_list.currentItem()
        if item:
            self._on_sentence_selected(item)

    def _on_sentence_selected(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        self._current_sentence = Sentence.from_dict(data)
        self._header_title.setText("Listen & Record")
        self._playback_sentence.setText(self._current_sentence.text)
        self._stack.setCurrentIndex(self.STATE_PLAYBACK)
        QTimer.singleShot(300, self._play_tts)

    def _on_voice_changed(self, index: int):
        """Switch TTS voice when the combo box changes."""
        voice_key = self._voice_combo.currentData()
        if voice_key:
            ok = self._tts.switch_voice(voice_key)
            if not ok:
                QMessageBox.warning(self, "Voice Error",
                                    f"Could not load voice: {voice_key}")

    def _play_tts(self):
        if not self._current_sentence:
            return
        self._led.set_state('playing_tts')
        result = self._tts.text_to_speech(self._current_sentence.text)
        if result['success']:
            self._audio.play_audio(
                result['audio_path'],
                done_callback=lambda: self._led.set_state('idle'),
            )
        else:
            self._led.set_state('idle')
            QMessageBox.warning(self, "TTS Error", result['message'])

    def _start_recording(self):
        if not self._current_sentence:
            return
        if not self._audio.check_microphone():
            QMessageBox.critical(self, "Microphone Error",
                                 "No microphone detected.\nPlease connect a microphone.")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rec_dir = self._auth.get_user_recording_dir()
        self._current_audio_path = os.path.join(rec_dir, f"rec_{timestamp}.wav")

        self._rec_sentence_display.setText(self._current_sentence.text)
        self._elapsed_seconds = 0
        self._timer_label.setText(f"0 / {MAX_RECORDING_DURATION}s")
        self._timer_bar.setValue(0)
        self._level_bar.setValue(0)
        self._stack.setCurrentIndex(self.STATE_RECORDING)

        self._led.set_state('recording')

        self._recording_timer = QTimer()
        self._recording_timer.timeout.connect(self._tick_timer)
        self._recording_timer.start(1000)

        self._level_timer = QTimer()
        self._level_timer.timeout.connect(self._update_level)
        self._level_timer.start(100)

        # done_callback is called from a background thread.
        # We emit a Qt Signal so the slot runs on the main thread.
        self._audio.start_recording(
            output_path=self._current_audio_path,
            duration=MAX_RECORDING_DURATION,
            done_callback=lambda result: self._recording_finished.emit(result),
        )

    def _tick_timer(self):
        self._elapsed_seconds += 1
        self._timer_label.setText(f"{self._elapsed_seconds} / {MAX_RECORDING_DURATION}s")
        self._timer_bar.setValue(self._elapsed_seconds)
        if self._elapsed_seconds >= MAX_RECORDING_DURATION:
            self._stop_recording()

    def _update_level(self):
        self._level_bar.setValue(int(self._audio.current_level * 100))

    def _stop_recording(self):
        if self._recording_timer:
            self._recording_timer.stop()
        if self._level_timer:
            self._level_timer.stop()
        self._audio.stop_recording()

    # ── This slot runs on the MAIN thread thanks to the Signal ──
    @Slot(dict)
    def _process_recording(self, rec_result: dict):
        logger.info("Processing recording: %s", rec_result.get('audio_path', ''))

        if self._recording_timer:
            self._recording_timer.stop()
        if self._level_timer:
            self._level_timer.stop()

        if not rec_result.get('success'):
            self._led.set_state('error')
            QMessageBox.warning(self, "Recording Error", rec_result.get('message', 'Unknown error'))
            self._stack.setCurrentIndex(self.STATE_PLAYBACK)
            return

        # Validate
        validation = self._audio.validate_recording(self._current_audio_path)
        if not validation['valid']:
            issues = validation['issues']
            if 'too_quiet' in issues:
                reply = QMessageBox.warning(
                    self, "Low Audio",
                    "Your recording seems very quiet.\nTry again or continue?",
                    QMessageBox.Retry | QMessageBox.Ignore,
                )
                if reply == QMessageBox.Retry:
                    self._stack.setCurrentIndex(self.STATE_PLAYBACK)
                    return
            elif 'too_short' in issues:
                QMessageBox.warning(self, "Too Short", "Recording is too short. Please try again.")
                self._stack.setCurrentIndex(self.STATE_PLAYBACK)
                return

        # Switch to processing UI
        self._stack.setCurrentIndex(self.STATE_PROCESSING)
        self._led.set_state('processing')

        # Run STT + scoring in background thread
        self._worker_thread = QThread()
        worker = _ProcessingWorker(self._stt, self._current_audio_path, self._current_sentence.text)
        worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(worker.run)
        worker.finished.connect(self._on_processing_done)
        worker.error.connect(self._on_processing_error)
        worker.finished.connect(self._worker_thread.quit)
        worker.error.connect(self._worker_thread.quit)
        self._worker = worker  # prevent GC
        self._worker_thread.start()

    def _on_processing_done(self, score: dict):
        accuracy = score['accuracy']
        category = score['category']
        transcription = score['transcription']
        target = score['target']

        # LED
        led_map = {'excellent': 'score_excellent', 'good': 'score_good', 'needs_improvement': 'score_poor'}
        self._led.set_state(led_map.get(category, 'idle'))

        # Title
        titles = {'excellent': 'Excellent!', 'good': 'Good Job!', 'needs_improvement': 'Keep Practicing'}
        self._score_title.setText(titles.get(category, 'Result'))

        # Color
        color_map = {'excellent': COLORS['success_green'], 'good': COLORS['warning_orange'],
                     'needs_improvement': COLORS['error_red']}
        color = color_map.get(category, COLORS['text_dark'])

        # Score bar — set complete stylesheet each time (avoids appending / font issues)
        self._score_bar.setValue(accuracy)
        self._score_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {COLORS['border']};
                border-radius: 16px;
                background-color: #F1F3F4;
                font-size: 15px;
                font-weight: bold;
                color: {COLORS['text_dark']};
            }}
            QProgressBar::chunk {{
                border-radius: 14px;
                background-color: {color};
            }}
        """)

        cat_labels = {'excellent': 'Excellent', 'good': 'Good', 'needs_improvement': 'Needs Improvement'}
        self._score_category.setText(cat_labels.get(category, category))
        self._score_category.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")

        self._transcription_label.setText(transcription if transcription else "(no speech detected)")
        self._target_label.setText(target)

        # Save to DB
        if not self._auth.is_guest and self._current_sentence:
            try:
                self._db.save_recording(
                    user_id=self._auth.current_user.id,
                    sentence_id=self._current_sentence.id,
                    audio_file_path=self._current_audio_path,
                    transcription=transcription,
                    target_text=target,
                    wer_score=score['wer'],
                    accuracy_percentage=accuracy,
                    score_category=category,
                    duration_seconds=self._elapsed_seconds,
                )
                logger.info("Recording saved: %d%% (%s)", accuracy, category)
            except Exception as e:
                logger.error("Failed to save recording: %s", e)

        self._stack.setCurrentIndex(self.STATE_SCORE)

    def _on_processing_error(self, msg: str):
        self._led.set_state('error')
        QMessageBox.critical(self, "Processing Error", msg)
        self._stack.setCurrentIndex(self.STATE_PLAYBACK)

    def _retry_sentence(self):
        self._stack.setCurrentIndex(self.STATE_PLAYBACK)
        QTimer.singleShot(300, self._play_tts)

    def _next_sentence(self):
        self.reset()

    def _on_back(self):
        current = self._stack.currentIndex()
        if current == self.STATE_SELECTION:
            self.go_back.emit()
        elif current == self.STATE_RECORDING:
            self._stop_recording()
            self._stack.setCurrentIndex(self.STATE_PLAYBACK)
        elif current == self.STATE_PROCESSING:
            pass
        elif current == self.STATE_SCORE:
            self.reset()
        else:
            self._stack.setCurrentIndex(self.STATE_SELECTION)
