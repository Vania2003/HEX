import sys
from importlib import resources

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from hex_game.ui.qt_main import MainWindow


def build_palette():
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 100, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    return palette


def load_stylesheet():
    try:
        return resources.files("hex_game.ui").joinpath("qt_styles.qss").read_text(
            encoding="utf-8"
        )
    except (OSError, ModuleNotFoundError):
        return ""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setPalette(build_palette())
    app.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.resize(1100, 900)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
