"""
Splash screen for SpeechMaster.
Clean loading screen with app identity and progress indicator.
"""
import logging

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer

from app.utils.config import APP_NAME, APP_VERSION, COLORS

logger = logging.getLogger(__name__)


class SplashScreen(QWidget):
    """Splash screen shown at application startup."""

    def __init__(self, on_finished=None, parent=None):
        super().__init__(parent)
        self._on_finished = on_finished
        self._setup_ui()
        QTimer.singleShot(2500, self._finish)

    def _setup_ui(self):
        self.setObjectName("splashScreen")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(48, 80, 48, 60)

        layout.addStretch(3)

        # App name — large, bold, blue
        name_label = QLabel(APP_NAME)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(f"""
            font-size: 44px;
            font-weight: bold;
            color: {COLORS['primary_blue']};
            letter-spacing: 1px;
        """)
        layout.addWidget(name_label)

        # Tagline
        tagline = QLabel("Speech Learning Tool")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(f"""
            font-size: 17px;
            color: {COLORS['text_light']};
            letter-spacing: 0.5px;
        """)
        layout.addWidget(tagline)

        layout.addSpacing(48)

        # Loading bar — thin, indeterminate
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedHeight(3)
        self._progress.setFixedWidth(200)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: {COLORS['surface_gray']};
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['primary_blue']};
                border-radius: 1px;
            }}
        """)
        layout.addWidget(self._progress, alignment=Qt.AlignCenter)

        layout.addStretch(4)

        # Version
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_light']};
        """)
        layout.addWidget(version_label)

    def _finish(self):
        logger.info("Splash screen finished.")
        if self._on_finished:
            self._on_finished()
