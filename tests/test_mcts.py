import random

import pytest

from hex_game.engine.board import Board
from hex_game.engine.geometry import EMPTY, O, X
from hex_game.players.mcts import MCTSBot


def brute_force_winner(board_cells, geometry, size):
    for code, sources, at_goal in (
        (X, geometry.left_cells, lambda i: i % size == size - 1),
        (O, geometry.top_cells, lambda i: i // size == size - 1),
    ):
        seen = set()
        stack = [i for i in sources if board_cells[i] == code]
        while stack:
            index = stack.pop()
            if index in seen:
                continue
            seen.add(index)
            if at_goal(index):
                return code
            for neighbour in geometry.neighbours[index]:
                if board_cells[neighbour] == code and neighbour not in seen:
                    stack.append(neighbour)
    return EMPTY


@pytest.mark.parametrize("seed", range(10))
def test_playout_winner_matches_brute_force(seed):
    board = Board(9)
    bot = MCTSBot('X', seed=seed)
    bot._bind(board)
    rnd = random.Random(seed)
    for _ in range(6):
        index = rnd.choice(board.legal_indices())
        board.play(index, X if board.empty_count % 2 else O)

    scratch = bytearray(board.cells)
    empties = [i for i, cell in enumerate(scratch) if cell == EMPTY]
    bot.rng.shuffle(empties)
    for i in empties[0::2]:
        scratch[i] = X
    for i in empties[1::2]:
        scratch[i] = O
    assert bot._x_connected(scratch) == (
        brute_force_winner(scratch, board.geometry, board.size) == X
    )


def test_playout_always_produces_a_winner():
    board = Board(7)
    bot = MCTSBot('X', seed=1)
    bot._bind(board)
    for _ in range(50):
        assert bot._playout(board, X) in (X, O)


@pytest.mark.parametrize("seed", range(8))
def test_bridge_playout_agrees_with_brute_force(seed):
    board = Board(7)
    bot = MCTSBot('X', seed=seed)
    bot._bind(board)
    rnd = random.Random(seed)
    for turn in range(8):
        board.play(rnd.choice(board.legal_indices()), X if turn % 2 else O)
    if board.winner_code:
        pytest.skip("random opening already decided the game")

    trace = []
    winner = bot._playout_with_bridges(board, X, trace)
    scratch = bytearray(board.cells)
    mover = X
    for move in trace:
        scratch[move] = mover
        mover = O if mover == X else X
    assert brute_force_winner(scratch, board.geometry, board.size) == winner


def test_playout_restores_the_board_union_find():
    board = Board(9)
    board.play(board.geometry.index(4, 4), X)
    bot = MCTSBot('O', seed=11)
    bot._bind(board)
    parent_before = list(board.dsu.parent)
    size_before = list(board.dsu.size)
    for _ in range(20):
        bot._playout(board, O)
    assert board.dsu.parent == parent_before
    assert board.dsu.size == size_before


def test_rave_statistics_are_collected():
    board = Board(7)
    board.play(board.geometry.index(3, 3), X)
    bot = MCTSBot('O', max_simulations=400, seed=12, use_rave=True)
    bot.make_move(board)
    assert bot.simulations == 400


def test_search_leaves_the_board_untouched():
    board = Board(7)
    board.play(board.geometry.index(3, 3), X)
    snapshot = bytes(board.cells)
    empty_before = board.empty_count
    frontier_before = set(board.frontier)

    MCTSBot('O', max_simulations=300, seed=2).make_move(board)

    assert bytes(board.cells) == snapshot
    assert board.empty_count == empty_before
    assert board.frontier == frontier_before
    assert board.winner_code == EMPTY


def test_bot_finds_an_immediate_win():
    board = Board(5)
    for col in range(4):
        board.play(board.geometry.index(col, 2), X)
        if col < 3:
            board.play(board.geometry.index(col, 0), O)
    bot = MCTSBot('X', max_simulations=1500, seed=3)
    assert bot.make_move(board) == (4, 2)


def test_simulation_budget_is_respected():
    board = Board(9)
    board.play(board.geometry.index(4, 4), X)
    bot = MCTSBot('O', max_simulations=250, seed=4)
    bot.make_move(board)
    assert bot.simulations == 250


def test_results_are_reproducible_for_a_fixed_seed():
    board = Board(9)
    board.play(board.geometry.index(4, 4), X)
    first = MCTSBot('O', max_simulations=400, seed=7).make_move(board)
    second = MCTSBot('O', max_simulations=400, seed=7).make_move(board)
    assert first == second


def test_opening_in_the_centre_is_worth_swapping():
    board = Board(9)
    board.play(board.geometry.index(4, 4), X)
    assert MCTSBot('O', seed=5).should_swap(board)
