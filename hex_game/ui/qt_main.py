from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QMenuBar, QToolBar, QFileDialog,
    QMessageBox, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QDialog,
    QPushButton
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from hex_game.ui.qt_board_widget import BoardWidget
from hex_game.ui.bot_worker import BotWorker
from hex_game.engine.game import Game
from hex_game.players import registry
from hex_game.paths import AUTOSAVE_PATH
import json
import os

DEFAULT_SETTINGS = {
    "player_x": "X",
    "player_o": "O",
    "with_bot": False,
    "first": "X",
    "board_size": 11,
    "agent": "minimax",
    "difficulty": "normal",
    "swap_rule": True,
}


class SidePanel(QWidget):
    """Live summary of the game plus the two actions that need a visible home."""

    swap_requested = pyqtSignal()
    undo_requested = pyqtSignal()

    def __init__(self, game, settings):
        super().__init__()
        self.game = game
        self.settings = settings

        self.label_x = QLabel()
        self.label_o = QLabel()
        self.label_turn = QLabel()
        self.label_turn.setStyleSheet("font-weight: bold;")
        self.label_setup = QLabel()
        self.label_setup.setWordWrap(True)
        self.label_moves = QLabel()
        self.label_swap = QLabel()
        self.label_swap.setWordWrap(True)

        self.swap_button = QPushButton("Zamień strony (swap)")
        self.swap_button.clicked.connect(self.swap_requested)
        self.undo_button = QPushButton("Cofnij ruch")
        self.undo_button.clicked.connect(self.undo_requested)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("👤 Gracz X (lewa ↔ prawa):"))
        layout.addWidget(self.label_x)
        layout.addWidget(QLabel("👤 Gracz O (góra ↕ dół):"))
        layout.addWidget(self.label_o)
        layout.addWidget(QLabel("🕑 Tura:"))
        layout.addWidget(self.label_turn)
        layout.addSpacing(12)
        layout.addWidget(self.label_setup)
        layout.addWidget(self.label_moves)
        layout.addWidget(self.label_swap)
        layout.addSpacing(12)
        layout.addWidget(self.swap_button)
        layout.addWidget(self.undo_button)
        layout.addStretch()
        self.setLayout(layout)

    def update_info(self, can_swap=False, can_undo=False):
        self.label_x.setText(self.game.player_x)
        self.label_o.setText(self.game.player_o)
        self.label_turn.setText(self.game.get_current_player_name())

        mode = "Gracz vs Bot" if self.game.with_bot else "Gracz vs Gracz"
        setup = f"Tryb: {mode}\nPlansza: {self.game.board.size} × {self.game.board.size}"
        if self.game.with_bot:
            setup += (
                f"\nBot: {registry.agent_label(self.settings['agent'])}"
                f"\nPoziom: {registry.difficulty_label(self.settings['difficulty'])}"
            )
        self.label_setup.setText(setup)
        self.label_moves.setText(f"Ruchy: {len(self.game.get_move_history())}")

        if not self.game.swap_rule:
            self.label_swap.setText("Swap: wyłączony")
        elif self.game.swapped:
            self.label_swap.setText("Swap: wykorzystany")
        elif self.game.can_swap():
            self.label_swap.setText("Swap: dostępny dla drugiego gracza")
        else:
            self.label_swap.setText("Swap: niewykorzystany")

        self.swap_button.setVisible(can_swap)
        self.undo_button.setEnabled(can_undo)


class MainWindow(QMainWindow):
    request_bot_move = pyqtSignal(object, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game")
        self.resize(1100, 800)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.settings = dict(DEFAULT_SETTINGS)
        self.bot = None
        self.bot_token = 0
        self.bot_busy = False
        self._preset_with_bot = None

        self.bot_timer = QTimer()
        self.bot_timer.setSingleShot(True)
        self.bot_timer.timeout.connect(self.start_bot_search)

        self.bot_thread = QThread(self)
        self.bot_worker = BotWorker()
        self.bot_worker.moveToThread(self.bot_thread)
        self.request_bot_move.connect(self.bot_worker.search)
        self.bot_worker.move_ready.connect(self.on_bot_move)
        self.bot_worker.failed.connect(self.on_bot_failed)
        self.bot_thread.start()

        # Quitting through the menu or a signal never reaches closeEvent, and a
        # QThread still running at interpreter shutdown hangs or crashes Qt.
        application = QApplication.instance()
        if application is not None:
            application.aboutToQuit.connect(self.shutdown_bot_thread)

        self.game = self._load_autosave() or Game(
            board_size=self.settings["board_size"],
            swap_rule=self.settings["swap_rule"],
        )
        self.rebuild_bot()

        self.init_menu()
        self.init_toolbar()

        self.board_widget = BoardWidget(self.game, self)
        self.info_panel = SidePanel(self.game, self.settings)
        self.info_panel.swap_requested.connect(self.on_swap_clicked)
        self.info_panel.undo_requested.connect(self.undo_move)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.board_widget, 1)
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setLayout(QVBoxLayout())
        right_panel.layout().addWidget(self.info_panel)
        right_panel.setObjectName("SidePanel")
        right_panel.setMinimumWidth(240)
        main_layout.addWidget(right_panel, 0)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.update_status()
        self.check_bot_move()

    # ------------------------------------------------------------------
    # seats and agents
    # ------------------------------------------------------------------

    @property
    def bot_seat(self):
        """The bot starts on seat O; a swap exchanges the two players' seats."""
        return 'X' if self.game.swapped else 'O'

    @property
    def human_seat(self):
        return 'O' if self.bot_seat == 'X' else 'X'

    def rebuild_bot(self):
        if self.game.with_bot:
            self.bot = registry.create_agent(
                self.settings["agent"], self.bot_seat, self.settings["difficulty"]
            )
        else:
            self.bot = None
        self.bot_worker.bot = self.bot

    def sync_bot_seat(self):
        if self.bot:
            self.bot.set_seat(self.bot_seat)

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------

    def update_status(self, message=None):
        winner = self.game.get_winner()
        self.info_panel.update_info(
            can_swap=self.game.can_swap() and not self.bot_to_move(),
            can_undo=bool(self.game.actions) and not self.bot_busy,
        )
        if message:
            self.status.showMessage(message)
        elif winner:
            self.status.showMessage(
                f"🏆 {self.game.get_winner_name()} wygrał! (seat {winner})"
            )
        else:
            self.status.showMessage(f"Tura gracza: {self.game.get_current_player_name()}")

    def bot_to_move(self):
        return (
            self.game.with_bot
            and self.bot is not None
            and self.game.get_current_player() == self.bot_seat
        )

    # ------------------------------------------------------------------
    # menu and toolbar
    # ------------------------------------------------------------------

    def init_menu(self):
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        game_menu = menu_bar.addMenu("🎮 Gra")

        new_game_action = QAction("Nowa gra", self)
        new_game_action.setShortcut("Ctrl+N")
        new_game_action.triggered.connect(self.new_game)
        game_menu.addAction(new_game_action)

        undo_action = QAction("Cofnij ruch", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_move)
        game_menu.addAction(undo_action)

        toggle_mode_action = QAction("Zmień tryb: Gracz vs Bot", self)
        toggle_mode_action.triggered.connect(self.toggle_mode)
        game_menu.addAction(toggle_mode_action)

        game_menu.addSeparator()

        save_action = QAction("Zapisz grę", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_game)
        game_menu.addAction(save_action)

        load_action = QAction("Wczytaj grę", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_game)
        game_menu.addAction(load_action)

        game_menu.addSeparator()

        exit_action = QAction("Wyjdź", self)
        exit_action.triggered.connect(self.close)
        game_menu.addAction(exit_action)

    def init_toolbar(self):
        toolbar = QToolBar("Główne opcje")
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        new_game = QAction("🆕 Nowa gra", self)
        new_game.triggered.connect(self.new_game)
        toolbar.addAction(new_game)

        undo = QAction("↩ Cofnij", self)
        undo.triggered.connect(self.undo_move)
        toolbar.addAction(undo)

        save = QAction("💾 Zapisz", self)
        save.triggered.connect(self.save_game)
        toolbar.addAction(save)

        load = QAction("📂 Wczytaj", self)
        load.triggered.connect(self.load_game)
        toolbar.addAction(load)

    # ------------------------------------------------------------------
    # game lifecycle
    # ------------------------------------------------------------------

    def new_game(self):
        from hex_game.ui.game_setup_dialog import GameSetupDialog

        proposed = dict(self.settings)
        if self._preset_with_bot is not None:
            proposed["with_bot"] = self._preset_with_bot
            self._preset_with_bot = None

        dialog = GameSetupDialog(self, settings=proposed)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.settings = dialog.get_settings()
        self.abandon_bot_search()
        self.game.reset(
            with_bot=self.settings["with_bot"],
            first=self.settings["first"],
            player_x=self.settings["player_x"],
            player_o=self.settings["player_o"],
            board_size=self.settings["board_size"],
            swap_rule=self.settings["swap_rule"],
        )
        self.rebuild_bot()
        self.board_widget.set_game(self.game)
        self.info_panel.game = self.game
        self.info_panel.settings = self.settings
        self.update_status()
        self.check_bot_move()

    def toggle_mode(self):
        self._preset_with_bot = not self.game.with_bot
        self.new_game()

    def undo_move(self):
        if not self.game.actions:
            return
        self.abandon_bot_search()
        if self.game.with_bot:
            self.game.undo_turn(self.human_seat)
        else:
            self.game.undo_last()
        self.sync_bot_seat()
        self.board_widget.set_game(self.game)
        self.update_status("Cofnięto ruch.")

    def on_swap_clicked(self):
        if not self.game.apply_swap():
            return
        self.sync_bot_seat()
        self.board_widget.update()
        self.update_status(
            f"Swap: {self.game.player_x} przejmuje pierwszy kamień."
        )
        self.check_bot_move()

    # ------------------------------------------------------------------
    # bot turn
    # ------------------------------------------------------------------

    def abandon_bot_search(self):
        """Invalidate any in-flight search; its position no longer exists."""
        self.bot_timer.stop()
        self.bot_token += 1
        self.bot_busy = False

    def check_bot_move(self):
        if not self.bot_to_move() or self.bot_busy or self.game.get_winner():
            return
        if self.game.can_swap():
            self.bot_timer.stop()
            self.consider_bot_swap()
            return
        self.bot_timer.start(150)

    def consider_bot_swap(self):
        """Pie-rule decision is a cheap lookup, so it stays on the GUI thread."""
        if self.bot.should_swap(self.game.board) and self.game.apply_swap():
            self.sync_bot_seat()
            self.update_status(
                f"Bot wykonał swap i gra teraz jako {self.bot_seat}."
            )
            self.board_widget.update()
            self.check_bot_move()
        else:
            self.bot_timer.start(150)

    def start_bot_search(self):
        if not self.bot_to_move() or self.game.get_winner():
            return
        self.bot_busy = True
        self.update_status("Bot analizuje pozycję…")
        self.request_bot_move.emit(self.game.board.copy(), self.bot_token)

    def on_bot_move(self, x, y, token):
        self.bot_busy = False
        if token != self.bot_token:
            return
        if not self.game.make_move(x, y):
            return
        self.board_widget.animate_cell(x, y)
        self.board_widget.update()
        self.update_status()
        if self.game.get_winner():
            self.board_widget.show_winner(self.game.get_winner_name())
        else:
            self.check_bot_move()

    def on_bot_failed(self, message, token):
        self.bot_busy = False
        if token == self.bot_token:
            self.update_status(f"Błąd bota: {message}")

    # ------------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------------

    def _payload(self):
        payload = self.game.serialize()
        payload["settings"] = self.settings
        return payload

    def _restore_settings(self, data):
        saved = data.get("settings")
        if isinstance(saved, dict):
            self.settings.update(
                {key: saved[key] for key in DEFAULT_SETTINGS if key in saved}
            )

    def _load_autosave(self):
        if not os.path.exists(AUTOSAVE_PATH):
            return None
        try:
            with open(AUTOSAVE_PATH, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self._restore_settings(data)
            return Game.load_from_dict(data)
        except Exception as error:
            print(f"[Błąd wczytywania autosave]: {error}")
            return None

    def save_game(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Zapisz grę", "save.json", "Pliki JSON (*.json)"
        )
        if not file_name:
            return
        try:
            with open(file_name, "w", encoding="utf-8") as handle:
                json.dump(self._payload(), handle, indent=2, ensure_ascii=False)
            self.status.showMessage("Grę zapisano pomyślnie.")
        except Exception as error:
            QMessageBox.critical(
                self, "Błąd zapisu", f"Nie udało się zapisać gry: {error}"
            )

    def load_game(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj grę", "", "Pliki JSON (*.json)"
        )
        if not file_name:
            return
        try:
            with open(file_name, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.abandon_bot_search()
            self._restore_settings(data)
            self.game = Game.load_from_dict(data)
            self.rebuild_bot()
            self.board_widget.set_game(self.game)
            self.info_panel.game = self.game
            self.info_panel.settings = self.settings
            self.update_status("Grę wczytano pomyślnie.")
            self.check_bot_move()
        except Exception as error:
            QMessageBox.critical(
                self, "Błąd wczytywania", f"Nie udało się wczytać gry: {error}"
            )

    def shutdown_bot_thread(self):
        self.abandon_bot_search()
        if self.bot_thread.isRunning():
            self.bot_thread.quit()
            self.bot_thread.wait(3000)

    def closeEvent(self, event):
        self.shutdown_bot_thread()
        try:
            with open(AUTOSAVE_PATH, "w", encoding="utf-8") as handle:
                json.dump(self._payload(), handle, indent=2, ensure_ascii=False)
        except Exception as error:
            print(f"[Błąd autosave]: {error}")
        super().closeEvent(event)
