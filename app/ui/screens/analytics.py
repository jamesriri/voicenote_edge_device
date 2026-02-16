from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from app.ui.theme import PRIMARY_BG, SECONDARY_BG, ACCENT, TEXT_PRIMARY, TEXT_MUTED


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

class StatCard(QFrame):
    """Minimal stat card with left color accent."""

    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid #E8EAED;
                border-radius: 14px;
                border-left: 4px solid {color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 13px; color: {TEXT_PRIMARY}; border: none; font-weight: bold;")
        layout.addWidget(title_lbl)

        self._value_lbl = QLabel(str(value))
        self._value_lbl.setStyleSheet(f"font-size: 30px; font-weight: bold; color: {color}; border: none;")
        layout.addWidget(self._value_lbl)

    def set_value(self, value: str):
        self._value_lbl.setText(str(value))