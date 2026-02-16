"""
Dashboard screen for SpeechMaster.
Clean card layout with stats and navigation.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGridLayout,
)
from PySide6.QtCore import Qt, Signal

from app.utils.config import COLORS

logger = logging.getLogger(__name__)


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
        title_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_light']}; border: none; font-weight: bold;")
        layout.addWidget(title_lbl)

        self._value_lbl = QLabel(str(value))
        self._value_lbl.setStyleSheet(f"font-size: 30px; font-weight: bold; color: {color}; border: none;")
        layout.addWidget(self._value_lbl)

    def set_value(self, value: str):
        self._value_lbl.setText(str(value))


class Dashboard(QWidget):
    """Main dashboard after login."""

    start_practice = Signal()
    view_history = Signal()
    logout_requested = Signal()

    def __init__(self, auth_service, db, parent=None):
        super().__init__(parent)
        self._auth = auth_service
        self._db = db
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("dashboard")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FAFAFA; }")

        content = QWidget()
        content.setStyleSheet("background: #FAFAFA;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)

        # ── Header ──
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self._greeting = QLabel("Welcome!")
        self._greeting.setStyleSheet(f"""
            font-size: 24px; font-weight: bold;
            color: {COLORS['text_dark']};
        """)
        header_layout.addWidget(self._greeting)
        header_layout.addStretch()

        history_btn = QPushButton("History")
        history_btn.setObjectName("outlineButton")
        history_btn.setMinimumSize(90, 44)
        history_btn.setCursor(Qt.PointingHandCursor)
        history_btn.clicked.connect(self.view_history.emit)
        header_layout.addWidget(history_btn)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("dangerOutlineButton")
        logout_btn.setMinimumSize(90, 44)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(logout_btn)

        layout.addLayout(header_layout)

        # ── Practice Card ──
        practice_frame = QFrame()
        practice_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['primary_blue']}, stop:1 #6EA8FE);
                border-radius: 20px;
            }}
        """)
        practice_layout = QVBoxLayout(practice_frame)
        practice_layout.setContentsMargins(28, 32, 28, 32)
        practice_layout.setSpacing(10)

        practice_title = QLabel("Practice Session")
        practice_title.setStyleSheet("font-size: 28px; font-weight: bold; color: white; background: transparent;")
        practice_layout.addWidget(practice_title)

        practice_desc = QLabel("Select a sentence, listen, record, and get your score.")
        practice_desc.setWordWrap(True)
        practice_desc.setStyleSheet("font-size: 15px; color: rgba(255,255,255,0.85); background: transparent;")
        practice_layout.addWidget(practice_desc)

        practice_layout.addSpacing(12)

        start_btn = QPushButton("Start Practice")
        start_btn.setObjectName("whiteLargeButton")
        start_btn.setMinimumHeight(60)
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.clicked.connect(self.start_practice.emit)
        practice_layout.addWidget(start_btn, alignment=Qt.AlignLeft)

        layout.addWidget(practice_frame)

        # ── Progress Section ──
        section_progress = QLabel("Your Progress")
        section_progress.setStyleSheet(f"font-size: 19px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(section_progress)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(12)

        self._card_total = StatCard("Total Sessions", "0", COLORS['primary_blue'])
        self._card_avg = StatCard("Average Score", "0%", COLORS['primary_blue'])
        stats_grid.addWidget(self._card_total, 0, 0)
        stats_grid.addWidget(self._card_avg, 0, 1)
        layout.addLayout(stats_grid)

        # ── Breakdown Section ──
        section_stats = QLabel("Score Breakdown")
        section_stats.setStyleSheet(f"font-size: 19px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(section_stats)

        cat_grid = QGridLayout()
        cat_grid.setSpacing(12)

        self._card_excellent = StatCard("Excellent", "0", COLORS['success_green'])
        self._card_good = StatCard("Good", "0", COLORS['warning_orange'])
        self._card_needs = StatCard("Needs Work", "0", COLORS['error_red'])

        cat_grid.addWidget(self._card_excellent, 0, 0)
        cat_grid.addWidget(self._card_good, 0, 1)
        cat_grid.addWidget(self._card_needs, 1, 0)
        layout.addLayout(cat_grid)

        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        user = self._auth.current_user
        if user:
            self._greeting.setText(f"Welcome, {user.username}")

            if not user.is_guest:
                stats = self._db.get_user_stats(user.id)
                self._card_total.set_value(str(stats['total_sessions']))
                self._card_avg.set_value(f"{stats['average_score']}%")
                self._card_excellent.set_value(str(stats['excellent']))
                self._card_good.set_value(str(stats['good']))
                self._card_needs.set_value(str(stats['needs_improvement']))
            else:
                for card in (self._card_total, self._card_avg, self._card_excellent,
                             self._card_good, self._card_needs):
                    card.set_value("—")
