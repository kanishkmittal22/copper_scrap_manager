from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ERP Manager - Login")
        self.setFixedSize(450, 400)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        
    def init_ui(self):
        # Main layout for the translucent dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Container frame acting as the visible window
        self.container = QFrame(self)
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: #1e272e;
                border-radius: 15px;
                border: 1px solid #353b48;
            }
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 50, 40, 40)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("ERP Manager")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px; 
            font-weight: 800; 
            color: #00a8ff; 
            margin-bottom: 5px;
            font-family: 'Segoe UI', Arial, sans-serif;
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("Please sign in to continue")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px; 
            color: #7f8fa6; 
            margin-bottom: 20px;
        """)
        layout.addWidget(subtitle)
        
        # Input styling
        input_style = """
            QLineEdit {
                background-color: #2f3640;
                border: 2px solid #353b48;
                border-radius: 8px;
                padding: 12px 15px;
                color: #f5f6fa;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00a8ff;
                background-color: #353b48;
            }
            QLineEdit::placeholder {
                color: #7f8fa6;
            }
        """
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("👤 Username")
        self.user_input.setStyleSheet(input_style)
        layout.addWidget(self.user_input)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("🔒 Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(input_style)
        layout.addWidget(self.pass_input)
        
        # Error Label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("""
            color: #e84118;
            font-size: 13px;
            font-weight: bold;
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        layout.addSpacing(10)
        
        # Login Button
        self.login_btn = QPushButton("Log In")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
                color: white;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0097e6;
            }
            QPushButton:pressed {
                background-color: #0082c8;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        # Cancel Button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8fa6;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #dcdde1;
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        main_layout.addWidget(self.container)
        
        # Enable Enter key to trigger login
        self.user_input.returnPressed.connect(self.handle_login)
        self.pass_input.returnPressed.connect(self.handle_login)
        
    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()
        
        # Reset styles
        self.user_input.setStyleSheet(self.user_input.styleSheet().replace("border: 2px solid #e84118;", "border: 2px solid #353b48;"))
        self.pass_input.setStyleSheet(self.pass_input.styleSheet().replace("border: 2px solid #e84118;", "border: 2px solid #353b48;"))
        
        if not username or not password:
            self.show_error("Please enter both username and password.")
            return
            
        # Hardcoded credentials
        if username == "Kanishk" and password == "1312":
            self.accept()
        else:
            self.show_error("Invalid username or password.")
            self.pass_input.clear()
            self.pass_input.setFocus()
            
            # Highlight error fields
            error_style = """
                QLineEdit {
                    background-color: #2f3640;
                    border: 2px solid #e84118;
                    border-radius: 8px;
                    padding: 12px 15px;
                    color: #f5f6fa;
                    font-size: 14px;
                }
                QLineEdit:focus {
                    border: 2px solid #e84118;
                    background-color: #353b48;
                }
                QLineEdit::placeholder {
                    color: #7f8fa6;
                }
            """
            self.user_input.setStyleSheet(error_style)
            self.pass_input.setStyleSheet(error_style)

    def show_error(self, message):
        self.error_label.setText(message)
        self.error_label.show()
        # Auto-hide error after 3 seconds
        QTimer.singleShot(3000, self.error_label.hide)

    # --- Allow dragging the frameless window ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
