from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class PrimaryButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(220)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                border-radius: 16px;
                padding: 14px;
                border: 1px solid transparent;
                min-height: 50px;
            }
            QPushButton:hover {
                border: 1px solid #38BDF8;
            }
            QPushButton:pressed {
                background-color: #38BDF8;
                color: #0F172A;
            }
        """)
