# main_window.py
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from ui.screens.welcome_screen import WelcomeScreen
from ui.screens.dashboard import DashboardScreen
from ui.screens.library import LibraryScreen
from ui.screens.analytics import AnalyticsScreen
from ui.screens.settings import SettingsScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Note")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Screens
        self.welcome_screen = WelcomeScreen()
        self.dashboard = DashboardScreen(stack=self.stack)
        self.library = LibraryScreen()
        self.analytics = AnalyticsScreen()
        self.settings = SettingsScreen()

        # Add screens to the stack
        self.stack.addWidget(self.welcome_screen)
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.library)
        self.stack.addWidget(self.analytics)
        self.stack.addWidget(self.settings)

        # Start with welcome screen
        self.stack.setCurrentWidget(self.welcome_screen)

        # Connect welcome button
        self.welcome_screen.start_button.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.dashboard)
        )
