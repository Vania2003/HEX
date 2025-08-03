from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QHBoxLayout
)

class GameSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nowa gra – Ustawienia")

        self.player_x_input = QLineEdit()
        self.player_o_input = QLineEdit()
        self.mode_selector = QComboBox()
        self.first_player_selector = QComboBox()

        self.player_x_input.setPlaceholderText("np. Alicja")
        self.player_o_input.setPlaceholderText("np. Bot lub Bob")

        self.mode_selector.addItems(["Gracz vs Gracz", "Gracz vs Bot"])
        self.first_player_selector.addItems(["X", "O"])

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Imię gracza X:"))
        layout.addWidget(self.player_x_input)
        layout.addWidget(QLabel("Imię gracza O:"))
        layout.addWidget(self.player_o_input)
        layout.addWidget(QLabel("Tryb gry:"))
        layout.addWidget(self.mode_selector)
        layout.addWidget(QLabel("Kto zaczyna:"))
        layout.addWidget(self.first_player_selector)

        buttons = QHBoxLayout()
        start_btn = QPushButton("Start")
        start_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(start_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.setLayout(layout)

    def get_settings(self):
        return {
            "player_x": self.player_x_input.text() or "X",
            "player_o": self.player_o_input.text() or "O",
            "with_bot": self.mode_selector.currentIndex() == 1,
            "first": self.first_player_selector.currentText()
        }
