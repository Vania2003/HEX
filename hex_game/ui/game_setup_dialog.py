from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout
)

from hex_game.players import registry

BOARD_SIZES = (7, 9, 11, 13)


class GameSetupDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Nowa gra – Ustawienia")
        settings = settings or {}

        self.player_x_input = QLineEdit(settings.get("player_x", ""))
        self.player_o_input = QLineEdit(settings.get("player_o", ""))
        self.mode_selector = QComboBox()
        self.size_selector = QComboBox()
        self.first_player_selector = QComboBox()
        self.agent_selector = QComboBox()
        self.difficulty_selector = QComboBox()
        self.swap_checkbox = QCheckBox("Reguła swap (pie rule)")

        self.player_x_input.setPlaceholderText("np. Alicja")
        self.player_o_input.setPlaceholderText("np. Bot lub Bob")

        self.mode_selector.addItems(["Gracz vs Gracz", "Gracz vs Bot"])
        self.mode_selector.setCurrentIndex(1 if settings.get("with_bot") else 0)

        self.size_selector.addItems([f"{size} × {size}" for size in BOARD_SIZES])
        requested_size = settings.get("board_size", 11)
        if requested_size in BOARD_SIZES:
            self.size_selector.setCurrentIndex(BOARD_SIZES.index(requested_size))

        self.first_player_selector.addItems(["X", "O"])
        self.first_player_selector.setCurrentText(settings.get("first", "X"))

        self.agent_selector.addItems(registry.agent_labels())
        self.difficulty_selector.addItems(registry.difficulty_labels())
        self.difficulty_selector.setCurrentText(
            registry.difficulty_label(settings.get("difficulty", "normal"))
        )
        self.swap_checkbox.setChecked(settings.get("swap_rule", True))

        form = QFormLayout()
        form.addRow("Imię gracza X:", self.player_x_input)
        form.addRow("Imię gracza O:", self.player_o_input)
        form.addRow("Rozmiar planszy:", self.size_selector)
        form.addRow("Tryb gry:", self.mode_selector)
        form.addRow("Kto zaczyna:", self.first_player_selector)
        form.addRow("Algorytm bota:", self.agent_selector)
        form.addRow("Poziom trudności:", self.difficulty_selector)

        self.hint = QLabel(
            "X łączy lewą i prawą krawędź, O górną i dolną.\n"
            "Swap pozwala drugiemu graczowi przejąć pierwszy kamień."
        )
        self.hint.setWordWrap(True)

        buttons = QHBoxLayout()
        start_btn = QPushButton("Start")
        start_btn.setDefault(True)
        start_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(start_btn)
        buttons.addWidget(cancel_btn)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.swap_checkbox)
        layout.addWidget(self.hint)
        layout.addLayout(buttons)
        self.setLayout(layout)

        self.mode_selector.currentIndexChanged.connect(self._update_bot_fields)
        self._update_bot_fields()

    def _update_bot_fields(self):
        enabled = self.mode_selector.currentIndex() == 1
        self.agent_selector.setEnabled(enabled)
        self.difficulty_selector.setEnabled(enabled)

    def get_settings(self):
        return {
            "player_x": self.player_x_input.text() or "X",
            "player_o": self.player_o_input.text() or "O",
            "with_bot": self.mode_selector.currentIndex() == 1,
            "first": self.first_player_selector.currentText(),
            "board_size": BOARD_SIZES[self.size_selector.currentIndex()],
            "agent": registry.agent_key(self.agent_selector.currentIndex()),
            "difficulty": registry.difficulty_key(
                self.difficulty_selector.currentIndex()
            ),
            "swap_rule": self.swap_checkbox.isChecked(),
        }
