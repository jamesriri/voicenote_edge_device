import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.theme import app_stylesheet

def main():
    """Application entry"""
    
    app = QApplication(sys.argv)
    app.setStyleSheet(app_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
