from hex_game.engine.board import Board

class Game:
    def __init__(self, board_size=11, with_bot=False, player_x="X", player_o="O", first="X"):
        self.board = Board(board_size)
        self.with_bot = with_bot
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = first
        self.winner = None
        self.move_history = []  # list of (player, x, y)

    def make_move(self, x, y):
        if self.winner is not None:
            return False
        if not self.board.is_valid_move(x, y):
            return False
        if self.board.place_piece(x, y, self.current_player):
            self.move_history.append((self.current_player, x, y))
            if self.board.find_winner() == self.current_player:
                self.winner = self.current_player
                #self.board.mark_winning_path(self.current_player)
            else:
                self.toggle_player()
            return True
        return False

    def toggle_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def get_current_player(self):
        return self.current_player

    def get_current_player_name(self):
        return self.player_x if self.current_player == 'X' else self.player_o

    def get_winner(self):
        return self.winner

    def get_winning_path(self):
        return self.board.get_winning_path()

    def get_move_history(self):
        return self.move_history

    def serialize(self):
        return {
            "board_size": self.board.size,
            "with_bot": self.with_bot,
            "player_x": self.player_x,
            "player_o": self.player_o,
            "first": self.current_player,
            "winner": self.winner,
            "history": self.move_history,
        }

    def get_score(self):
        """Zlicza liczbę zajętych pól przez każdego gracza."""
        score = {"X": 0, "O": 0}
        for row in self.board.get_state():
            for cell in row:
                if cell == "X":
                    score["X"] += 1
                elif cell == "O":
                    score["O"] += 1
        return score

    def get_board_state(self):
        """Zwraca aktualny stan planszy."""
        return self.board.get_state()

    @classmethod
    def load_from_dict(cls, data):
        game = cls(
            board_size=data.get("board_size", 11),
            with_bot=data.get("with_bot", False),
            player_x=data.get("player_x", "X"),
            player_o=data.get("player_o", "O"),
            first=data.get("first", "X")
        )
        for player, x, y in data.get("history", []):
            game.current_player = player
            game.make_move(x, y)
        return game

    def reset(self, with_bot=False, first="X", player_x="X", player_o="O"):
        self.__init__(
            board_size=self.board.size,
            with_bot=with_bot,
            player_x=player_x,
            player_o=player_o,
            first=first
        )
