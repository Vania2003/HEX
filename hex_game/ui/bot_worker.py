"""Runs an agent's search off the GUI thread.

The search takes anywhere from milliseconds to seconds; calling it directly
from a timer slot froze the whole window for that long.  The worker receives a
private copy of the board, so the user may keep interacting while it thinks.

Every request carries a token.  A result whose token no longer matches the
current game belongs to a position that has since been abandoned (new game,
loaded save) and is dropped.
"""

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class BotWorker(QObject):
    move_ready = pyqtSignal(int, int, int)
    failed = pyqtSignal(str, int)

    def __init__(self, bot=None):
        super().__init__()
        self.bot = bot

    @pyqtSlot(object, int)
    def search(self, board, token):
        if self.bot is None:
            return
        try:
            move = self.bot.make_move(board)
        except Exception as error:  # a crash here must not kill the thread
            self.failed.emit(str(error), token)
            return
        if move is not None:
            self.move_ready.emit(move[0], move[1], token)
