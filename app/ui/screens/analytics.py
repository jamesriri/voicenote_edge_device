from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class AnalyticsScreen(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setSpacing(30)

        title = QLabel("Analytics")
        title.setObjectName("title")

        subtitle = QLabel("Track your pronunciation progress and performance trends.")
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addStretch()

        self.setLayout(layout)
