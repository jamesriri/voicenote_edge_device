"""
History screen for SpeechMaster.
Clean list of past recordings with filters and detail dialog.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QDialog,
)
from PySide6.QtCore import Qt, Signal

from app.models.recording import Recording
from app.utils.config import COLORS

logger = logging.getLogger(__name__)


class RecordingDetailDialog(QDialog):
    """Modal with full recording details."""

    delete_requested = Signal(int)

    def __init__(self, recording: Recording, audio_service, parent=None):
        super().__init__(parent)
        self._recording = recording
        self._audio = audio_service
        self.setWindowTitle("Recording Details")
        self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 28)

        # Date
        date_lbl = QLabel(self._recording.date_display)
        date_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; font-weight: bold;")
        layout.addWidget(date_lbl)

        # Target
        layout.addWidget(self._card("Target Sentence", self._recording.target_text))

        # Transcription
        layout.addWidget(self._card("Your Speech",
                                    self._recording.transcription or "(no speech detected)"))

        # Score
        color = self._recording.category_color
        score_frame = QFrame()
        score_frame.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                border-left: 4px solid {color};
            }}
        """)
        score_lay = QVBoxLayout(score_frame)
        score_lay.setContentsMargins(16, 14, 16, 14)
        score_lbl = QLabel(f"{self._recording.accuracy_percentage}%  —  {self._recording.category_label}")
        score_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color}; border: none;")
        score_lay.addWidget(score_lbl)
        wer_lbl = QLabel(f"Word Error Rate: {self._recording.wer_score:.2f}")
        wer_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; border: none;")
        score_lay.addWidget(wer_lbl)
        layout.addWidget(score_frame)

        # Play
        play_btn = QPushButton("Play Recording")
        play_btn.setObjectName("primaryButton")
        play_btn.setMinimumHeight(48)
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.clicked.connect(self._play)
        layout.addWidget(play_btn)

        # Delete
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("dangerOutlineButton")
        delete_btn.setMinimumHeight(48)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(self._confirm_delete)
        layout.addWidget(delete_btn)

        # Close
        close_btn = QPushButton("Close")
        close_btn.setObjectName("secondaryButton")
        close_btn.setMinimumHeight(44)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _card(self, title: str, body: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 14, 16, 14)
        t = QLabel(title)
        t.setStyleSheet(f"font-size: 12px; color: {COLORS['text_light']}; font-weight: bold; border: none;")
        lay.addWidget(t)
        c = QLabel(body)
        c.setWordWrap(True)
        c.setStyleSheet(f"font-size: 16px; color: {COLORS['text_dark']}; border: none;")
        lay.addWidget(c)
        return frame

    def _play(self):
        if self._recording.audio_file_path:
            self._audio.play_audio(self._recording.audio_file_path)

    def _confirm_delete(self):
        reply = QMessageBox.question(
            self, "Delete Recording",
            "Are you sure? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.delete_requested.emit(self._recording.id)
            self.accept()


# ======================================================================
class HistoryScreen(QWidget):
    """Browse and manage past recordings."""

    go_back = Signal()

    def __init__(self, auth_service, db, audio_service, parent=None):
        super().__init__(parent)
        self._auth = auth_service
        self._db = db
        self._audio = audio_service
        self._recordings: list[Recording] = []
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("historyScreen")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{ background: #FFFFFF; border-bottom: 1px solid {COLORS['border']}; }}
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        back_btn = QPushButton("Back")
        back_btn.setObjectName("linkButton")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self.go_back.emit)
        h_lay.addWidget(back_btn)

        title = QLabel("Recording History")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {COLORS['text_dark']}; border: none;")
        h_lay.addWidget(title, 1)

        spacer = QLabel("")
        spacer.setFixedWidth(50)
        spacer.setStyleSheet("border: none;")
        h_lay.addWidget(spacer)

        layout.addWidget(header)

        # Filter bar
        filter_bar = QFrame()
        filter_bar.setStyleSheet("QFrame { background: #F1F3F4; }")
        fb_lay = QHBoxLayout(filter_bar)
        fb_lay.setContentsMargins(16, 8, 16, 8)
        fb_lay.setSpacing(8)

        filter_lbl = QLabel("Filter")
        filter_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text_light']}; background: transparent;")
        fb_lay.addWidget(filter_lbl)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Excellent", "Good", "Needs Improvement"])
        self._filter_combo.setMinimumHeight(40)
        self._filter_combo.currentIndexChanged.connect(self._apply_filters)
        fb_lay.addWidget(self._filter_combo)

        sort_lbl = QLabel("Sort")
        sort_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLORS['text_light']}; background: transparent;")
        fb_lay.addWidget(sort_lbl)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(["Recent", "Best", "Worst"])
        self._sort_combo.setMinimumHeight(40)
        self._sort_combo.currentIndexChanged.connect(self._apply_filters)
        fb_lay.addWidget(self._sort_combo)

        layout.addWidget(filter_bar)

        # List
        self._list_widget = QListWidget()
        self._list_widget.itemDoubleClicked.connect(self._show_detail)
        layout.addWidget(self._list_widget, 1)

        # Empty state
        self._empty_label = QLabel("No recordings yet.\nStart a practice session to see results here.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setWordWrap(True)
        self._empty_label.setStyleSheet(f"font-size: 16px; color: {COLORS['text_light']}; padding: 48px;")
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

    def refresh(self):
        user = self._auth.current_user
        if not user or user.is_guest:
            self._recordings = []
            self._populate_list()
            return
        self._apply_filters()

    def _apply_filters(self):
        user = self._auth.current_user
        if not user or user.is_guest:
            self._recordings = []
            self._populate_list()
            return

        category_map = {0: None, 1: 'excellent', 2: 'good', 3: 'needs_improvement'}
        category = category_map.get(self._filter_combo.currentIndex())

        sort_map = {0: 'recorded_at DESC', 1: 'accuracy_percentage DESC', 2: 'accuracy_percentage ASC'}
        order_by = sort_map.get(self._sort_combo.currentIndex(), 'recorded_at DESC')

        rows = self._db.get_recordings_for_user(user.id, category=category, order_by=order_by)
        self._recordings = [Recording.from_dict(r) for r in rows]
        self._populate_list()

    def _populate_list(self):
        self._list_widget.clear()
        if not self._recordings:
            self._empty_label.show()
            self._list_widget.hide()
            return
        self._empty_label.hide()
        self._list_widget.show()
        for rec in self._recordings:
            text = f"{rec.date_display}   {rec.accuracy_percentage}% {rec.category_label}\n{rec.target_preview}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, rec)
            self._list_widget.addItem(item)

    def _show_detail(self, item: QListWidgetItem):
        rec: Recording = item.data(Qt.UserRole)
        dialog = RecordingDetailDialog(rec, self._audio, parent=self)
        dialog.delete_requested.connect(self._delete_recording)
        dialog.exec()

    def _delete_recording(self, recording_id: int):
        self._db.delete_recording(recording_id)
        self.refresh()
