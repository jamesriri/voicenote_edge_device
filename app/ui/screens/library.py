from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QSlider, QFrame
)
from PySide6.QtCore import Qt


class SentenceCard(QFrame):
    def __init__(self, sentence):
        super().__init__()

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("background-color: #1E293B; border-radius: 12px;")

        layout = QVBoxLayout()

        # Sentence text
        sentence_label = QLabel(sentence)
        sentence_label.setWordWrap(True)

        # Controls row
        controls = QHBoxLayout()

        self.play_btn = QPushButton("Play")
        self.pause_btn = QPushButton("Pause")
        self.record_btn = QPushButton("Record")
        self.submit_btn = QPushButton("Submit")

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(150)
        self.speed_slider.setValue(100)

        controls.addWidget(self.play_btn)
        controls.addWidget(self.pause_btn)
        controls.addWidget(QLabel("Speed"))
        controls.addWidget(self.speed_slider)
        controls.addWidget(self.record_btn)
        controls.addWidget(self.submit_btn)

        layout.addWidget(sentence_label)
        layout.addLayout(controls)

        self.setLayout(layout)


class LibraryScreen(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(20)

        title = QLabel("Library")
        title.setObjectName("title")

        layout.addWidget(title)

        # Hardcoded sentences
        sentences = [
            "Good morning, how are you?",
            "The sun rises in the east.",
            "Practice makes perfect.",
            "Speech therapy helps improve clarity."
        ]

        for sentence in sentences:
            card = SentenceCard(sentence)
            layout.addWidget(card)

        layout.addStretch()
        self.setLayout(layout)
