from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from ui.widgets.primary_button import PrimaryButton

class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(30)

        layout.addStretch()

        self.title = QLabel("VoiceNote Therapy")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel("Your intelligent and personalized companion for speech clarity and confidence.")
        self.subtitle.setObjectName("subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_button = PrimaryButton("Start Session")

        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addSpacing(40)
        layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        self.setLayout(layout)
