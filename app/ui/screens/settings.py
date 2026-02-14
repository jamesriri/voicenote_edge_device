from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class SettingsScreen(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(30)

        title = QLabel("Settings")
        title.setObjectName("title")

        subtitle = QLabel("Adjust playback speed, audio input, and therapy preferences.")
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addStretch()

        self.setLayout(layout)
