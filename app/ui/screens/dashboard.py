from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from app.ui.theme import PRIMARY_BG, SECONDARY_BG, ACCENT, TEXT_PRIMARY, TEXT_MUTED
# from app.ui.screens.sidebar import Sidebar
from app.ui.screens.analytics import StatCard


class Dashboard(QWidget):
    start_practice = Signal()
    view_history = Signal()
    logout_requested = Signal()

    def __init__(self, auth_service, db_service, stack=None):
        super().__init__()

        self._auth = auth_service
        self._db = db_service
        self._stack = stack

        self._setup_ui()
        # self._connect_sidebar()

    # ======================================================
    # UI SETUP
    # ======================================================
    def _setup_ui(self):
        self.setObjectName("dashboard")

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== SIDEBAR =====
        # self.sidebar = Sidebar()
        # main_layout.addWidget(self.sidebar)

        # ===== RIGHT CONTENT =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #FFFFFF; }")

        content = QWidget()
        content.setStyleSheet("background: #FFFFFF;")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(24)

        # ======================================================
        # HEADER
        # ======================================================
        header_layout = QHBoxLayout()

        self._greeting = QLabel("Welcome!")
        self._greeting.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {TEXT_PRIMARY};
        """)
        header_layout.addWidget(self._greeting)
        header_layout.addStretch()

        history_btn = QPushButton("History")
        history_btn.setObjectName("outlineButton")
        history_btn.setMinimumSize(90, 44)
        history_btn.clicked.connect(self.view_history.emit)
        header_layout.addWidget(history_btn)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("dangerOutlineButton")
        logout_btn.setMinimumSize(90, 44)
        logout_btn.clicked.connect(self.logout_requested.emit)
        header_layout.addWidget(logout_btn)

        layout.addLayout(header_layout)

        # ======================================================
        # STATS CARDS
        # ======================================================
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self._card_total = StatCard("Total Sessions", "0", ACCENT)
        self._card_avg = StatCard("Average Score", "0%", "#22C55E")
        self._card_excellent = StatCard("Excellent", "0", "#10B981")
        self._card_good = StatCard("Good", "0", "#F59E0B")
        self._card_needs = StatCard("Needs Improvement", "0", "#EF4444")

        stats_layout.addWidget(self._card_total)
        stats_layout.addWidget(self._card_avg)
        stats_layout.addWidget(self._card_excellent)
        stats_layout.addWidget(self._card_good)
        stats_layout.addWidget(self._card_needs)

        layout.addLayout(stats_layout)

        # ======================================================
        # PRACTICE CARD
        # ======================================================
        practice_frame = QFrame()
        practice_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {ACCENT}, stop:1 #6EA8FE);
                border-radius: 20px;
            }}
        """)

        practice_layout = QVBoxLayout(practice_frame)
        practice_layout.setContentsMargins(28, 32, 28, 32)

        title = QLabel("Practice Session")
        title.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: white;"
        )
        practice_layout.addWidget(title)

        desc = QLabel(
            "Select a sentence, listen, record, and get your score."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            "font-size: 15px; color: rgba(255,255,255,0.85);"
        )
        practice_layout.addWidget(desc)

        practice_layout.addSpacing(12)

        start_btn = QPushButton("Start Practice")
        start_btn.setObjectName("whiteLargeButton")
        start_btn.setMinimumHeight(60)
        start_btn.clicked.connect(self.start_practice.emit)
        practice_layout.addWidget(start_btn, alignment=Qt.AlignLeft)

        layout.addWidget(practice_frame)

        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    # ======================================================
    # SIDEBAR CONNECTIONS
    # ======================================================
    # def _connect_sidebar(self):
        # self.sidebar.dashboard_btn.clicked.connect(
        #     lambda: self._stack.setCurrentWidget(self)  # switch to dashboard itself
        # )
        # self.sidebar.library_btn.clicked.connect(
        #     lambda: self._stack.setCurrentWidget(self._stack.widget(2))  # library index
        # )
        # self.sidebar.analytics_btn.clicked.connect(
        #     lambda: self._stack.setCurrentWidget(self._stack.widget(3))  # analytics index
        # )
        # self.sidebar.settings_btn.clicked.connect(
        #     lambda: self._stack.setCurrentWidget(self._stack.widget(4))  # settings index
        # )

    # ======================================================
    # REFRESH METHOD (RESTORED)
    # ======================================================
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
                for card in (
                    self._card_total,
                    self._card_avg,
                    self._card_excellent,
                    self._card_good,
                    self._card_needs
                ):
                    card.set_value("—")
