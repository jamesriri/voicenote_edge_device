from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget

from ui.screens.sidebar import Sidebar
from ui.screens.library import LibraryScreen
from ui.screens.analytics import AnalyticsScreen
from ui.screens.settings import SettingsScreen


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = Sidebar()

        # Content area
        self.content_stack = QStackedWidget()

        # Screens
        self.library_screen = LibraryScreen()
        self.analytics_screen = AnalyticsScreen()
        self.settings_screen = SettingsScreen()

        # Add to stack
        self.content_stack.addWidget(self.library_screen)
        self.content_stack.addWidget(self.analytics_screen)
        self.content_stack.addWidget(self.settings_screen)

        # Default screen
        self.content_stack.setCurrentWidget(self.library_screen)

        # Layout structure
        layout.addWidget(self.sidebar)
        layout.addWidget(self.content_stack)

        self.setLayout(layout)

        # 🔥 Sidebar Navigation Connections
        self.sidebar.library_btn.clicked.connect(
            lambda: self.content_stack.setCurrentWidget(self.library_screen)
        )

        self.sidebar.analytics_btn.clicked.connect(
            lambda: self.content_stack.setCurrentWidget(self.analytics_screen)
        )

        self.sidebar.settings_btn.clicked.connect(
            lambda: self.content_stack.setCurrentWidget(self.settings_screen)
        )
