from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QSlider, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
import pyttsx3
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import random
import time


# ------------------- TTS Thread -------------------
class TTSThread(QThread):
    finished = Signal()

    def __init__(self, text, rate=150):
        super().__init__()
        self.text = text
        self.rate = rate
        self.engine = pyttsx3.init()

    def run(self):
        self.engine.setProperty("rate", self.rate)
        self.engine.say(self.text)
        self.engine.runAndWait()
        self.finished.emit()


# ------------------- Recording Thread -------------------
class RecordThread(QThread):
    update_time = Signal(str)
    finished = Signal()

    def __init__(self, duration=3, fs=44100, filename="output.wav"):
        super().__init__()
        self.duration = duration
        self.fs = fs
        self.filename = filename

    def run(self):
        recording = sd.rec(int(self.duration * self.fs),
                           samplerate=self.fs,
                           channels=1)
        start = time.time()
        while True:
            elapsed = int(time.time() - start)
            if elapsed > self.duration:
                break
            self.update_time.emit(f"Recording... {elapsed}s")
            time.sleep(0.2)
        sd.wait()
        write(self.filename, self.fs, recording)
        self.finished.emit()


# ------------------- Sentence Card -------------------
class SentenceCard(QFrame):
    def __init__(self, sentence):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #1E293B; border-radius: 12px;")
        self.setMaximumWidth(700)

        layout = QVBoxLayout()

        # Sentence label
        self.sentence_label = QLabel(sentence)
        self.sentence_label.setWordWrap(True)

        # Controls
        controls = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.record_btn = QPushButton("Record")
        self.submit_btn = QPushButton("Submit")

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(250)
        self.speed_slider.setValue(150)

        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)
        controls.addWidget(QLabel("Speed"))
        controls.addWidget(self.speed_slider)
        controls.addWidget(self.record_btn)
        controls.addWidget(self.submit_btn)

        layout.addWidget(self.sentence_label)
        layout.addLayout(controls)
        self.setLayout(layout)

        # Threads
        self.tts_thread = None
        self.record_thread = None

        # Connections
        self.play_btn.clicked.connect(self.play_sentence)
        self.pause_btn.clicked.connect(self.stop_sentence)
        self.record_btn.clicked.connect(self.record_audio)
        self.submit_btn.clicked.connect(self.submit_audio)

    # ------------------- TTS -------------------
    def play_sentence(self):
        rate = self.speed_slider.value()
        self.tts_thread = TTSThread(self.sentence_label.text(), rate)
        self.tts_thread.start()

    def stop_sentence(self):
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.terminate()

    # ------------------- Recording -------------------
    def record_audio(self):
        # disable play/pause during recording
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.record_btn.setStyleSheet("background-color: red; color: white;")
        self.record_thread = RecordThread(duration=5)
        self.record_thread.update_time.connect(lambda t: self.record_btn.setText(t))
        self.record_thread.finished.connect(self.record_finished)
        self.record_thread.start()

    def record_finished(self):
        self.record_btn.setStyleSheet("")
        self.record_btn.setText("Record")
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        print("Recording finished and saved to output.wav")

    # ------------------- Submit -------------------
    def submit_audio(self):
        score = random.choice(["High", "Moderate", "Low"])
        print(f"Submitted audio. Score: {score}")


# ------------------- Library Screen -------------------
class LibraryScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel("Library")
        title.setObjectName("title")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        sentences = [
            "Good morning, how are you?",
            "The sun rises in the east.",
            "Practice makes perfect.",
            "Speech therapy helps improve clarity."
        ]

        for sentence in sentences:
            card = SentenceCard(sentence)
            layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addStretch()
        self.setLayout(layout)
