"""
SpeechMaster — Main Application Entry Point
Speech Learning Tool for ASR Non-Standard Speech
"""
import logging
import sys
import os
from pathlib import Path

# Ensure the project root is on the path so "app.*" imports work ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.utils.config import (
    APP_NAME, APP_VERSION, SCREEN_WIDTH, SCREEN_HEIGHT,
    COLORS, LOG_FILE, LOG_FORMAT, RESOURCES_DIR,
)

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding='utf-8'),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── PySide6 ──
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase

# ── App modules ──
from app.utils.database import Database, init_database
from app.services.auth_service import AuthService
from app.services.tts_service import TTSService
from app.services.stt_service import STTService
from app.services.audio_service import AudioService
from app.services.led_service import LEDService

from app.ui.splash_screen import SplashScreen
from app.ui.auth_screen import AuthScreen
from app.ui.dashboard import Dashboard
from app.ui.recording_screen import RecordingScreen
from app.ui.history_screen import HistoryScreen


# Main Window
class MainWindow(QMainWindow):
    """Application main window that hosts a QStackedWidget of screens."""

    # Screen indices
    SCREEN_SPLASH = 0
    SCREEN_AUTH = 1
    SCREEN_DASHBOARD = 2
    SCREEN_RECORDING = 3
    SCREEN_HISTORY = 4

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ── Initialise services ──
        self._init_services()

        # ── Load stylesheet ──
        self._load_stylesheet()

        # ── Build UI ──
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._build_screens()
        self._connect_signals()

        # Start on splash
        self._stack.setCurrentIndex(self.SCREEN_SPLASH)

        logger.info("Application started.")

    # Service init
    def _init_services(self):
        # Database
        self._db = init_database()

        # Auth
        self._auth = AuthService(self._db)

        # TTS
        self._tts = TTSService()
        if not self._tts.initialize():
            logger.warning("TTS service unavailable — some features will be limited.")

        # STT
        self._stt = STTService()
        if not self._stt.initialize():
            logger.warning("STT service unavailable — some features will be limited.")

        # Audio
        self._audio = AudioService()

        # if self._audio.auto_select_usb_microphone():
        #     print("USB Microphone auto-selected successfully")
        # else:
        #     print("No USB Mic detected")

        # LED
        self._led = LEDService()
        self._led.initialize()

    # Stylesheet
    def _load_stylesheet(self):
        qss_path = RESOURCES_DIR / "styles" / "theme.qss"
        if qss_path.exists():
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
            logger.info("Loaded stylesheet: %s", qss_path)
        else:
            logger.warning("Stylesheet not found: %s", qss_path)

    # Screen construction
    def _build_screens(self):
        # 0 — Splash
        self._splash = SplashScreen(on_finished=self._on_splash_done)
        self._stack.addWidget(self._splash)

        # 1 — Auth
        self._auth_screen = AuthScreen(self._auth)
        self._stack.addWidget(self._auth_screen)

        # 2 — Dashboard
        self._dashboard = Dashboard(self._auth, self._db)
        self._stack.addWidget(self._dashboard)

        # 3 — Recording
        self._recording = RecordingScreen(
            self._auth, self._db, self._tts,
            self._stt, self._audio, self._led,
        )
        self._stack.addWidget(self._recording)

        # 4 — History
        self._history = HistoryScreen(self._auth, self._db, self._audio)
        self._stack.addWidget(self._history)

    def _connect_signals(self):
        # Auth screen
        self._auth_screen.login_success.connect(self._on_login)
        self._auth_screen.guest_login.connect(self._on_guest_login)

        # Dashboard
        self._dashboard.start_practice.connect(self._go_to_recording)
        self._dashboard.view_history.connect(self._go_to_history)
        self._dashboard.logout_requested.connect(self._on_logout)

        # Recording screen
        self._recording.go_back.connect(self._go_to_dashboard)

        # History screen
        self._history.go_back.connect(self._go_to_dashboard)

    # Navigation
    def _on_splash_done(self):
        self._stack.setCurrentIndex(self.SCREEN_AUTH)

    def _on_login(self, user_info: dict):
        logger.info("Login: %s", user_info.get('username'))
        self._go_to_dashboard()

    def _on_guest_login(self):
        logger.info("Guest login.")
        self._go_to_dashboard()

    def _go_to_dashboard(self):
        self._dashboard.refresh()
        self._stack.setCurrentIndex(self.SCREEN_DASHBOARD)

    def _go_to_recording(self):
        # Check services
        if not self._tts.is_available:
            QMessageBox.warning(
                self, "TTS Unavailable",
                "Text-to-speech is not available.\nPlease check the Piper model files.",
            )
            return
        if not self._stt.is_available:
            QMessageBox.warning(
                self, "STT Unavailable",
                "Speech recognition is not available.\nPlease check the Whisper model.",
            )
            return

        self._recording.reset()
        self._stack.setCurrentIndex(self.SCREEN_RECORDING)

    def _go_to_history(self):
        if self._auth.is_guest:
            QMessageBox.information(
                self, "Guest Mode",
                "Recording history is not available in guest mode.",
            )
            return
        self._history.refresh()
        self._stack.setCurrentIndex(self.SCREEN_HISTORY)

    def _on_logout(self):
        self._auth.logout()
        self._led.all_off()
        self._auth_screen.reset()
        self._stack.setCurrentIndex(self.SCREEN_AUTH)
        logger.info("User logged out.")

    # Cleanup
    def closeEvent(self, event):
        """Clean up on window close."""
        self._audio.stop_playback()
        self._audio.stop_recording()
        self._led.cleanup()
        self._db.close()
        logger.info("Application closed.")
        event.accept()


# Entry Point
def _load_bundled_fonts():
    """Load bundled Roboto font from resources."""
    fonts_dir = RESOURCES_DIR / "fonts"
    loaded = []
    if fonts_dir.exists():
        for font_file in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id >= 0:
                families = QFontDatabase.applicationFontFamilies(font_id)
                loaded.extend(families)
                logger.info("Loaded font: %s → %s", font_file.name, families)
            else:
                logger.warning("Failed to load font: %s", font_file)
    return loaded


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Load bundled Roboto font
    families = _load_bundled_fonts()
    if "Roboto" in families:
        app.setFont(QFont("Roboto", 11))
        logger.info("Using bundled Roboto font.")
    else:
        app.setFont(QFont("Roboto", 11))  # Fall back to system Roboto or default
        logger.info("Roboto not bundled — using system fallback.")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
