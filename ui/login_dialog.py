from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use a standard window but disable resize and maximize
        self.setWindowTitle("ERP Manager - Secure Login")
        self.setFixedSize(450, 500)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.Dialog)
        
        # Set main dialog background
        self.setStyleSheet("QDialog { background-color: #1e272e; }")
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 50, 40, 40)
        main_layout.setSpacing(25)
        
        # --- Header Section ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        title = QLabel("ERP Manager")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 32px;
                font-weight: 800;
                color: #00a8ff;
                letter-spacing: 1px;
            }
        """)
        header_layout.addWidget(title)
        
        subtitle = QLabel("Please sign in to your account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                color: #7f8fa6;
                font-weight: 500;
            }
        """)
        header_layout.addWidget(subtitle)
        
        main_layout.addLayout(header_layout)
        
        main_layout.addSpacing(15)
        
        # --- Input Section ---
        input_style = """
            QLineEdit {
                background-color: #2f3640;
                border: 2px solid #353b48;
                border-radius: 6px;
                padding: 12px 15px;
                color: #f5f6fa;
                font-size: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLineEdit:focus {
                border: 2px solid #00a8ff;
                background-color: #353b48;
            }
            QLineEdit::placeholder {
                color: #718093;
            }
        """
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setStyleSheet(input_style)
        self.user_input.setMinimumHeight(50)
        main_layout.addWidget(self.user_input)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(input_style)
        self.pass_input.setMinimumHeight(50)
        main_layout.addWidget(self.pass_input)
        
        # --- Error Label ---
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("""
            QLabel {
                color: #e84118;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 5px;
            }
        """)
        self.error_label.setMinimumHeight(30)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)
        
        main_layout.addStretch()
        
        # --- Action Buttons ---
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(15)
        
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
                color: white;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
                border: none;
            }
            QPushButton:hover {
                background-color: #0097e6;
            }
            QPushButton:pressed {
                background-color: #0082c8;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        btn_layout.addWidget(self.login_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8fa6;
                border: 1px solid transparent;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                color: #dcdde1;
                background-color: #2f3640;
                border: 1px solid #353b48;
            }
            QPushButton:pressed {
                background-color: #353b48;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        # Wrap cancel button to center it
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        cancel_layout.addWidget(self.cancel_btn)
        cancel_layout.addStretch()
        
        btn_layout.addLayout(cancel_layout)
        
        main_layout.addLayout(btn_layout)
        
        # Enable Enter key
        self.user_input.returnPressed.connect(self.handle_login)
        self.pass_input.returnPressed.connect(self.handle_login)
        
    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        
        # Reset error styles if previously applied
        base_input_style = """
            QLineEdit {
                background-color: #2f3640;
                border: 2px solid #353b48;
                border-radius: 6px;
                padding: 12px 15px;
                color: #f5f6fa;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #00a8ff;
                background-color: #353b48;
            }
            QLineEdit::placeholder { color: #718093; }
        """
        self.user_input.setStyleSheet(base_input_style)
        self.pass_input.setStyleSheet(base_input_style)
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            self.highlight_errors(not username, not password)
            return
            
        # Hardcoded credentials
        if username == "Kanishk" and password == "1312":
            self.accept()
        else:
            self.show_error("Invalid username or password")
            self.pass_input.clear()
            self.pass_input.setFocus()
            self.highlight_errors(True, True)
            
    def highlight_errors(self, user_err, pass_err):
        error_style = """
            QLineEdit {
                background-color: #2f3640;
                border: 2px solid #e84118;
                border-radius: 6px;
                padding: 12px 15px;
                color: #f5f6fa;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 2px solid #e84118;
                background-color: #353b48;
            }
            QLineEdit::placeholder { color: #718093; }
        """
        if user_err:
            self.user_input.setStyleSheet(error_style)
        if pass_err:
            self.pass_input.setStyleSheet(error_style)

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
        QTimer.singleShot(3000, self.error_label.hide)
