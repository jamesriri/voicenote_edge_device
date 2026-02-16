"""
Login / Signup screen for SpeechMaster.
Clean card-based layout with form inputs.
"""
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QMessageBox, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, Signal

from app.utils.config import COLORS, APP_NAME
from app.utils.validators import password_strength

logger = logging.getLogger(__name__)


class AuthScreen(QWidget):
    """Login / Signup / Guest mode screen."""

    login_success = Signal(dict)
    guest_login = Signal()

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self._auth = auth_service
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("authScreen")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f0f2ef; }")

        content = QWidget()
        content.setStyleSheet("background: #f0f2ef;")
        main_layout = QVBoxLayout(content)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(36, 48, 36, 36)
        main_layout.setSpacing(8)

        # Header
        header = QLabel(APP_NAME)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(f"""
            font-size: 34px; font-weight: bold;
            color: #28112b;
        """)
        main_layout.addWidget(header)

        subtitle = QLabel("Improve your speech, one sentence at a time")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 15px; color: {COLORS['text_light']}; margin-bottom: 20px;")
        main_layout.addWidget(subtitle)

        # Stacked widget for Login / Signup
        self._stack = QStackedWidget()
        self._login_page = self._build_login_page()
        self._signup_page = self._build_signup_page()
        self._stack.addWidget(self._login_page)
        self._stack.addWidget(self._signup_page)
        main_layout.addWidget(self._stack)

        main_layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def _build_login_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("authPage")
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        self._login_username = self._make_input("Username", "Enter your username")
        layout.addWidget(self._login_username)

        self._login_password = self._make_input("Password", "Enter your password", password=True)
        layout.addWidget(self._login_password)

        self._login_error = QLabel("")
        self._login_error.setStyleSheet(f"color: {COLORS['error_red']}; font-size: 13px;")
        self._login_error.setWordWrap(True)
        self._login_error.hide()
        layout.addWidget(self._login_error)

        layout.addSpacing(8)

        login_btn = QPushButton("Log In")
        login_btn.setMinimumHeight(56)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #28112b;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #bce7fd;
                color: #28112b;
            }}
            QPushButton:pressed {{
                background-color: #2A56C6;
            }}
        """)
        login_btn.clicked.connect(self._on_login)
        layout.addWidget(login_btn)

        guest_btn = QPushButton("Continue as Guest")
        guest_btn.setMinimumHeight(56)
        guest_btn.setCursor(Qt.PointingHandCursor)
        guest_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #F1F3F4;
                color: #3C4043;
                border: none;
                border-radius: 14px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #bce7fd;
                color: #28112b;
                
            }}
            QPushButton:pressed {{
                background-color: #DADCE0;
            }}
        """)
        guest_btn.clicked.connect(self._on_guest)
        layout.addWidget(guest_btn)

        layout.addSpacing(16)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: #28112b; background: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(divider)

        layout.addSpacing(8)

        create_link = QPushButton("Create a new account")
        create_link.setObjectName("linkButton")
        create_link.setStyleSheet(f"""
            QPushButton {{
                background-color: #28112b;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #bce7fd;
                color: #28112b;
                                
            }}
            QPushButton:pressed {{
                background-color: #DADCE0;
            }}
        """)
        create_link.setCursor(Qt.PointingHandCursor)
        create_link.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        layout.addWidget(create_link, alignment=Qt.AlignCenter)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Signup
    # ------------------------------------------------------------------
    def _build_signup_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("authPage")
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        section_title = QLabel("Create Account")
        section_title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(section_title)

        self._signup_username = self._make_input("Username", "Choose a username")
        layout.addWidget(self._signup_username)

        self._signup_password = self._make_input("Password", "Choose a password", password=True)
        self._signup_password.findChild(QLineEdit).textChanged.connect(self._update_strength)
        layout.addWidget(self._signup_password)

        self._strength_label = QLabel("")
        self._strength_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self._strength_label)

        self._signup_confirm = self._make_input("Confirm Password", "Re-enter password", password=True)
        layout.addWidget(self._signup_confirm)

        self._signup_error = QLabel("")
        self._signup_error.setStyleSheet(f"color: {COLORS['error_red']}; font-size: 13px;")
        self._signup_error.setWordWrap(True)
        self._signup_error.hide()
        layout.addWidget(self._signup_error)

        layout.addSpacing(8)

        create_btn = QPushButton("Create Account")
        create_btn.setMinimumHeight(56)
        create_btn.setCursor(Qt.PointingHandCursor)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary_blue']};
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3B78E7;
            }}
            QPushButton:pressed {{
                background-color: #2A56C6;
            }}
        """)
        create_btn.clicked.connect(self._on_signup)
        layout.addWidget(create_btn)

        layout.addSpacing(16)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"color: {COLORS['border']}; background: {COLORS['border']}; max-height: 1px;")
        layout.addWidget(divider)

        layout.addSpacing(8)

        back_link = QPushButton("Back to login")
        back_link.setObjectName("linkButton")
        back_link.setCursor(Qt.PointingHandCursor)
        back_link.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        layout.addWidget(back_link, alignment=Qt.AlignCenter)

        layout.addStretch()
        return page

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_input(self, label_text: str, placeholder: str, password: bool = False) -> QWidget:
        container = QWidget()
        container.setObjectName("authInputContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(label_text)
        label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLORS['text_dark']};")
        layout.addWidget(label)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setMinimumHeight(52)
        line_edit.setObjectName("authInput")
        if password:
            line_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(line_edit)

        return container

    @staticmethod
    def _get_input(container: QWidget) -> str:
        line_edit = container.findChild(QLineEdit)
        return line_edit.text().strip() if line_edit else ""

    def _clear_fields(self):
        for container in (self._login_username, self._login_password,
                          self._signup_username, self._signup_password, self._signup_confirm):
            le = container.findChild(QLineEdit)
            if le:
                le.clear()
        self._login_error.hide()
        self._signup_error.hide()
        self._strength_label.setText("")

    def _update_strength(self, text: str):
        if not text:
            self._strength_label.setText("")
            return
        strength = password_strength(text)
        colors = {'weak': COLORS['error_red'], 'medium': COLORS['warning_orange'], 'strong': COLORS['success_green']}
        self._strength_label.setText(f"Password strength: {strength}")
        self._strength_label.setStyleSheet(f"font-size: 13px; color: {colors.get(strength, COLORS['text_light'])};")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_login(self):
        username = self._get_input(self._login_username)
        password = self._get_input(self._login_password)
        result = self._auth.login_user(username, password)
        if result['success']:
            self._login_error.hide()
            self._clear_fields()
            self.login_success.emit(result)
        else:
            self._login_error.setText(result['message'])
            self._login_error.show()

    def _on_signup(self):
        username = self._get_input(self._signup_username)
        password = self._get_input(self._signup_password)
        confirm = self._get_input(self._signup_confirm)
        result = self._auth.register_user(username, password, confirm)
        if result['success']:
            self._signup_error.hide()
            login_result = self._auth.login_user(username, password)
            if login_result['success']:
                self._clear_fields()
                self.login_success.emit(login_result)
            else:
                self._clear_fields()
                self._stack.setCurrentIndex(0)
                QMessageBox.information(self, "Success", "Account created! Please log in.")
        else:
            self._signup_error.setText(result['message'])
            self._signup_error.show()

    def _on_guest(self):
        reply = QMessageBox.question(
            self, "Guest Mode",
            "Recordings will not be saved.\nContinue as guest?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._auth.create_guest_session()
            self._clear_fields()
            self.guest_login.emit()

    def reset(self):
        self._clear_fields()
        self._stack.setCurrentIndex(0)
