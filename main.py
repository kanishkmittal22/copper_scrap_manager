import sys
import os
from PyQt5.QtWidgets import QApplication
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow
from database.db_manager import DatabaseManager

def main():
    app = QApplication(sys.argv)
    
    # Load stylesheet
    try:
        style_path = os.path.join(os.path.dirname(__file__), "ui", "styles.qss")
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Could not load stylesheet: {e}")

    # Initialize DB
    db = DatabaseManager()

    # Show Login
    login = LoginDialog()
    if login.exec_() == LoginDialog.Accepted:
        # If login successful, show main window
        window = MainWindow(db)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
