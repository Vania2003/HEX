import random

import pytest

from hex_game.engine.board import Board
from hex_game.engine.geometry import EMPTY, O, X


def brute_force_winner(board):
    """Independent DFS reference for the incremental union-find result."""
    geometry = board.geometry
    cells = board.cells
    size = board.size

    for code, sources, at_goal in (
        (X, geometry.left_cells, lambda i: i % size == size - 1),
        (O, geometry.top_cells, lambda i: i // size == size - 1),
    ):
        seen = set()
        stack = [i for i in sources if cells[i] == code]
        while stack:
            index = stack.pop()
            if index in seen:
                continue
            seen.add(index)
            if at_goal(index):
                return code
            for neighbour in geometry.neighbours[index]:
                if cells[neighbour] == code and neighbour not in seen:
                    stack.append(neighbour)
    return EMPTY


def random_fill(board, rnd):
    order = list(range(board.geometry.cell_count))
    rnd.shuffle(order)
    for step, index in enumerate(order):
        board.play(index, X if step % 2 == 0 else O)


def test_undo_restores_every_field():
    board = Board(7)
    before = bytes(board.cells)
    board.play(board.geometry.index(3, 3), X)
    assert bytes(board.cells) != before
    board.undo()
    assert bytes(board.cells) == before
    assert board.empty_count == board.geometry.cell_count
    assert board.winner_code == EMPTY


def test_undo_clears_a_win():
    board = Board(5)
    for col in range(4):
        board.play(board.geometry.index(col, 2), X)
    assert board.winner_code == EMPTY
    board.play(board.geometry.index(4, 2), X)
    assert board.winner_code == X
    board.undo()
    assert board.winner_code == EMPTY


@pytest.mark.parametrize("seed", range(20))
def test_incremental_winner_matches_brute_force(seed):
    rnd = random.Random(seed)
    board = Board(9)
    order = list(range(board.geometry.cell_count))
    rnd.shuffle(order)
    for step, index in enumerate(order):
        board.play(index, X if step % 2 == 0 else O)
        if board.winner_code != EMPTY:
            break
    assert board.winner_code == brute_force_winner(board)


@pytest.mark.parametrize("seed", range(30))
def test_a_full_board_always_has_exactly_one_winner(seed):
    """The Hex no-draw property; it is what makes the search sound."""
    rnd = random.Random(seed)
    board = Board(9)
    random_fill(board, rnd)
    x_connected = board.has_connection('X')
    o_connected = board.has_connection('O')
    assert x_connected != o_connected


def test_winning_path_is_a_real_chain():
    board = Board(5)
    for col in range(5):
        board.play(board.geometry.index(col, 2), X)
    path = board.get_winning_path()
    assert path[0][0] == 0
    assert path[-1][0] == 4
    geometry = board.geometry
    for (col, row), (next_col, next_row) in zip(path, path[1:]):
        assert geometry.index(next_col, next_row) in geometry.neighbours[
            geometry.index(col, row)
        ]


def test_copy_is_independent():
    board = Board(5)
    board.play(board.geometry.index(2, 2), X)
    clone = board.copy()
    clone.play(clone.geometry.index(1, 1), O)
    assert board.cells[board.geometry.index(1, 1)] == EMPTY
    assert clone.cells[clone.geometry.index(2, 2)] == X
