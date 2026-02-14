from PySide6.QtWidgets import QMainWindow, QStackedWidget

from ui.screens.welcome_screen import WelcomeScreen

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TheraAI")

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome_screen = WelcomeScreen()

        self.stack.addWidget(self.welcome_screen)
        self.stack.setCurrentWidget(self.welcome_screen)
