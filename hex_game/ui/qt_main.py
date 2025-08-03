from PyQt6.QtWidgets import (
    QMainWindow, QStatusBar, QMenuBar, QToolBar, QFileDialog,
    QMessageBox, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QDialog
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QTimer
from hex_game.ui.qt_board_widget import BoardWidget
from hex_game.engine.game import Game
from hex_game.players.bot_minimax import MinimaxBot
import json
import os


class PlayerInfoWidget(QWidget):
    def __init__(self, game):
        super().__init__()
        self.game = game

        layout = QVBoxLayout()
        self.label_x = QLabel()
        self.label_o = QLabel()
        self.label_turn = QLabel()
        self.label_turn.setStyleSheet("font-weight: bold; margin-top: 20px;")

        layout.addWidget(QLabel("👤 Gracz X:"))
        layout.addWidget(self.label_x)
        layout.addWidget(QLabel("👤 Gracz O:"))
        layout.addWidget(self.label_o)
        layout.addWidget(QLabel("🕑 Tura:"))
        layout.addWidget(self.label_turn)
        layout.addStretch()

        self.setLayout(layout)
        self.update_info()

    def update_info(self):
        self.label_x.setText(self.game.player_x)
        self.label_o.setText(self.game.player_o)
        self.label_turn.setText(self.game.get_current_player_name())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hex Game – Player vs Player")
        self.resize(1100, 800)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.with_bot = False
        self.bot = None
        self.bot_timer = QTimer()
        self.bot_timer.setSingleShot(True)
        self.bot_timer.timeout.connect(self.do_bot_move)

        self.game = None
        if os.path.exists("autosave.json"):
            try:
                with open("autosave.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.game = Game.load_from_dict(data)
                    self.with_bot = self.game.with_bot
            except Exception as e:
                print(f"[Błąd wczytywania autosave]: {e}")

        if not self.game:
            self.game = Game(board_size=11, with_bot=self.with_bot)

        self.init_menu()
        self.init_toolbar()

        self.board_widget = BoardWidget(self.game, self)
        self.info_panel = PlayerInfoWidget(self.game)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.board_widget, 1)
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_panel.setLayout(QVBoxLayout())
        right_panel.layout().addWidget(self.info_panel)
        right_panel.setObjectName("SidePanel")
        main_layout.addWidget(right_panel, 0)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.update_status()
        self.check_bot_move()

    def update_status(self):
        winner = self.game.get_winner()
        self.info_panel.update_info()
        if winner:
            winner_name = self.game.player_x if winner == 'X' else self.game.player_o
            self.status.showMessage(f"🏆 {winner_name} wygrał! ({winner})")
        else:
            current_name = self.game.get_current_player_name()
            self.status.showMessage(f"Tura gracza: {current_name}")

    def init_menu(self):
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        game_menu = menu_bar.addMenu("🎮 Gra")

        new_game_action = QAction("Nowa gra", self)
        new_game_action.triggered.connect(self.new_game)
        game_menu.addAction(new_game_action)

        toggle_mode_action = QAction("Zmień tryb: Gracz vs Bot", self)
        toggle_mode_action.triggered.connect(self.toggle_mode)
        game_menu.addAction(toggle_mode_action)

        game_menu.addSeparator()

        save_action = QAction("Zapisz grę", self)
        save_action.triggered.connect(self.save_game)
        game_menu.addAction(save_action)

        load_action = QAction("Wczytaj grę", self)
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

        save = QAction("💾 Zapisz", self)
        save.triggered.connect(self.save_game)
        toolbar.addAction(save)

        load = QAction("📂 Wczytaj", self)
        load.triggered.connect(self.load_game)
        toolbar.addAction(load)

    def new_game(self):
        from hex_game.ui.game_setup_dialog import GameSetupDialog
        dlg = GameSetupDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            settings = dlg.get_settings()
            self.with_bot = settings["with_bot"]
            self.game.reset(
                with_bot=settings["with_bot"],
                first=settings["first"],
                player_x=settings["player_x"],
                player_o=settings["player_o"]
            )
            if self.with_bot:
                self.bot = MinimaxBot('O')
            self.board_widget.set_game(self.game)
            self.info_panel.game = self.game
            self.update_status()
            self.check_bot_move()

    def toggle_mode(self):
        self.with_bot = not self.with_bot
        mode_text = "Gracz vs Bot" if self.with_bot else "Gracz vs Gracz"
        self.status.showMessage(f"Przełączono tryb: {mode_text}")
        self.new_game()

    def save_game(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Zapisz grę", "save.json", "Pliki JSON (*.json)")
        if not file_name:
            return
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(self.game.serialize(), f, indent=2)
            self.status.showMessage("Grę zapisano pomyślnie.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd zapisu", f"Nie udało się zapisać gry: {str(e)}")

    def load_game(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Wczytaj grę", "", "Pliki JSON (*.json)")
        if not file_name:
            return
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.game = Game.load_from_dict(data)
                self.board_widget.set_game(self.game)
                self.info_panel.game = self.game
                self.update_status()
            self.status.showMessage("Grę wczytano pomyślnie.")
        except Exception as e:
            QMessageBox.critical(self, "Błąd wczytywania", f"Nie udało się wczytać gry: {str(e)}")

    def closeEvent(self, event):
        try:
            with open("autosave.json", "w", encoding="utf-8") as f:
                json.dump(self.game.serialize(), f, indent=2)
        except Exception as e:
            print(f"[Błąd autosave]: {e}")
        super().closeEvent(event)

    def check_bot_move(self):
        if self.with_bot and self.game.get_current_player() == 'O' and not self.game.get_winner():
            self.bot_timer.start(300)

    def do_bot_move(self):
        if self.bot and self.game.get_current_player() == 'O':
            move = self.bot.make_move(self.game.board)
            if move:
                self.game.make_move(*move)
                self.board_widget.animate_cell(*move)
                self.board_widget.update()
                self.update_status()
                self.check_bot_move()

                if self.game.get_winner():
                    self.board_widget.show_winner(self.game.get_winner())
                else:
                    self.check_bot_move()