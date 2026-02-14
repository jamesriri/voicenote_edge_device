from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.welcome_screen import WelcomeScreen
from ui.screens.dashboard import DashboardScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Note")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome_screen = WelcomeScreen()
        self.dashboard = DashboardScreen()

        self.stack.addWidget(self.welcome_screen)
        self.stack.addWidget(self.dashboard)


        self.stack.setCurrentWidget(self.welcome_screen)

        self.welcome_screen.start_button.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.dashboard)
        )
