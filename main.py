"""
ShoreLine - Personal Photo Culling Application
Fast, keyboard-first workflow for photographers
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.app import MainWindow


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("ShoreLine")
    app.setOrganizationName("ShoreLine")
    
    # Load stylesheet
    try:
        with open("resources/styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass  # Use default style if stylesheet not found
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
