import time

from hex_game.engine.board import Board
from hex_game.engine.geometry import O, X
from hex_game.players.bot_minimax import UNREACHABLE, MinimaxBot


def test_connection_distance_agrees_with_win_detection():
    """Distance 0 must mean connected, and connected must mean distance 0."""
    board = Board(7)
    bot = MinimaxBot('X')
    for col in range(7):
        assert board.has_connection('X') is (
            bot._connection_distance(board, X) == 0
        )
        board.play(board.geometry.index(col, 3), X)
    assert board.has_connection('X')
    assert bot._connection_distance(board, X) == 0


def test_distance_is_unreachable_when_blocked():
    board = Board(5)
    for row in range(5):
        board.play(board.geometry.index(2, row), O)
    bot = MinimaxBot('X')
    assert bot._connection_distance(board, X) >= UNREACHABLE


def test_bot_takes_an_immediate_win():
    board = Board(5)
    for col in range(4):
        board.play(board.geometry.index(col, 2), X)
    bot = MinimaxBot('X', time_limit=0.5)
    assert bot.make_move(board) == (4, 2)


def test_bot_blocks_an_immediate_loss():
    board = Board(5)
    for col in range(4):
        board.play(board.geometry.index(col, 2), X)
    board.play(board.geometry.index(0, 0), O)
    bot = MinimaxBot('O', time_limit=0.5)
    assert bot.make_move(board) == (4, 2)


def test_search_respects_its_time_budget():
    board = Board(11)
    board.play(board.geometry.index(5, 5), X)
    bot = MinimaxBot('O', depth=12, time_limit=0.5)
    start = time.perf_counter()
    move = bot.make_move(board)
    elapsed = time.perf_counter() - start
    assert move is not None
    assert elapsed < 2.0


def test_search_leaves_the_board_untouched():
    board = Board(9)
    board.play(board.geometry.index(4, 4), X)
    snapshot = bytes(board.cells)
    MinimaxBot('O', time_limit=0.3).make_move(board)
    assert bytes(board.cells) == snapshot
