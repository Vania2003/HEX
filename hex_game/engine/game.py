from hex_game.engine.board import Board
from hex_game.engine.geometry import CODES

MOVE = "move"
SWAP = "swap"

class Game:
    def __init__(self, board_size=11, with_bot=False, player_x="X", player_o="O",
                 first="X", swap_rule=True):
        self.board = Board(board_size)
        self.with_bot = with_bot
        self.player_x = player_x
        self.player_o = player_o
        self.first = first
        self.current_player = first
        self.winner = None
        self.swap_rule = swap_rule
        self.swapped = False
        self.actions = []
        self.move_history = []  # list of (seat, x, y)

    def make_move(self, x, y):
        if self.winner is not None:
            return False
        if not self.board.place_piece(x, y, self.current_player):
            return False

        seat = self.current_player
        self.move_history.append((seat, x, y))
        self.actions.append((MOVE, seat, x, y))

        if self.board.winner == seat:
            self.winner = seat
        else:
            self.toggle_player()
        return True

    def can_swap(self):
        return (
            self.swap_rule
            and not self.swapped
            and self.winner is None
            and len(self.move_history) == 1
        )

    def apply_swap(self):
        if not self.can_swap():
            return False
        self.player_x, self.player_o = self.player_o, self.player_x
        self.swapped = True
        self.actions.append((SWAP,))
        return True

    def undo_last(self):
        if not self.actions:
            return None
        action = self.actions.pop()
        if action[0] == SWAP:
            self.player_x, self.player_o = self.player_o, self.player_x
            self.swapped = False
            return SWAP

        _, seat, _, _ = action
        self.board.undo()
        self.move_history.pop()
        self.current_player = seat
        self.winner = self.board.winner
        return MOVE

    def undo_turn(self, seat):
        undone = 0
        while self.actions and (self.current_player != seat or undone == 0):
            if self.undo_last() is None:
                break
            undone += 1
        return undone

    def toggle_player(self):
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def get_current_player(self):
        return self.current_player

    def get_current_player_name(self):
        return self.player_x if self.current_player == 'X' else self.player_o

    def get_player_name(self, seat):
        return self.player_x if seat == 'X' else self.player_o

    def get_winner(self):
        return self.winner

    def get_winner_name(self):
        return self.get_player_name(self.winner) if self.winner else None

    def get_winning_path(self):
        return self.board.get_winning_path()

    def get_move_history(self):
        return self.move_history

    def get_score(self):
        cells = self.board.cells
        return {"X": cells.count(CODES["X"]), "O": cells.count(CODES["O"])}

    def get_board_state(self):
        return self.board.get_state()

    def serialize(self):
        return {
            "version": 2,
            "board_size": self.board.size,
            "with_bot": self.with_bot,
            "player_x": self.player_x,
            "player_o": self.player_o,
            "first": self.first,
            "current": self.current_player,
            "winner": self.winner,
            "swap_rule": self.swap_rule,
            "swapped": self.swapped,
            "history": self.move_history,
            "actions": [list(action) for action in self.actions],
        }

    @classmethod
    def load_from_dict(cls, data):
        game = cls(
            board_size=data.get("board_size", 11),
            with_bot=data.get("with_bot", False),
            player_x=data.get("player_x", "X"),
            player_o=data.get("player_o", "O"),
            first=data.get("first", "X"),
            swap_rule=data.get("swap_rule", True),
        )

        actions = data.get("actions")
        if actions is None:
            # Version 1 saves only stored the move list.
            actions = [[MOVE, seat, x, y] for seat, x, y in data.get("history", [])]

        for action in actions:
            if action[0] == SWAP:
                game.actions.append((SWAP,))
                game.swapped = True
                continue
            _, seat, x, y = action
            game.current_player = seat
            game.make_move(x, y)

        game.current_player = data.get("current", game.current_player)
        game.winner = game.board.winner
        return game

    def reset(self, with_bot=False, first="X", player_x="X", player_o="O",
              board_size=None, swap_rule=None):
        self.__init__(
            board_size=self.board.size if board_size is None else board_size,
            with_bot=with_bot,
            player_x=player_x,
            player_o=player_o,
            first=first,
            swap_rule=self.swap_rule if swap_rule is None else swap_rule,
        )
