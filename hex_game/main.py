# File: hex_game/main.py
import sys
from PyQt6.QtWidgets import QApplication
from hex_game.ui.qt_main import MainWindow
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(100, 100, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    app.setStyleSheet("""
        QPushButton {
            background-color: #444;
            border: 1px solid #666;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
        }
        QPushButton:hover {
            background-color: #555;
        }
        QLabel {
            color: white;
        }
        QToolBar {
            background-color: #222;
            spacing: 8px;
            padding: 4px;
            border-bottom: 1px solid #333;
        }
        QMainWindow {
            background-color: #1e1e1e;
        }
        QWidget#SidePanel {
            background-color: #1c1c1c;
            border-left: 2px solid #666;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0px 0px 12px rgba(0, 0, 0, 0.6);
        }
        QWidget#SidePanel {
            background-color: #1c1c1c;
            border: 2px solid #777;         /* pełny kontur wokół */
            padding: 12px;
            border-radius: 10px;
        }
        QWidget#SidePanel QLabel {
            color: #ddd;
            font-weight: bold;
            margin-bottom: 6px;
        }
        QComboBox QAbstractItemView {
            background-color: #2a2a2a;
            color: white;
            selection-background-color: #555;
        }
        QListWidget, QTreeWidget, QTableWidget {
            background-color: #2a2a2a;
            color: white;
            border: 1px solid #555;
        }
        QGroupBox {
            color: white;
            border: 1px solid #444;
            margin-top: 6px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
        }
        QLineEdit {
            background-color: #2a2a2a;
            color: white;
            border: 1px solid #555;
            padding: 4px;
        }
        QLineEdit:disabled {
            background-color: #1e1e1e;
            color: #888;
            border: 1px solid #444;
        }
        QLineEdit:disabled::placeholder {
            color: white;
        }

    """)

    window = MainWindow()
    window.resize(1100, 900)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()