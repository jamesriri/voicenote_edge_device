from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedWidth(120)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.library_btn = QPushButton("Library")
        self.dashboard_btn = QPushButton("Dashboard")
        self.analytics_btn = QPushButton("Analytics")
        self.settings_btn = QPushButton("Settings")

        layout.addWidget(self.library_btn)
        layout.addWidget(self.analytics_btn)
        layout.addWidget(self.settings_btn)

        layout.addStretch()

        self.setLayout(layout)
