from hex_game.engine.game import Game
from hex_game.engine.geometry import EMPTY


def test_undo_restores_the_previous_turn():
    game = Game(board_size=7)
    game.make_move(3, 3)
    game.make_move(2, 2)
    assert game.get_current_player() == 'X'

    game.undo_last()
    assert game.get_current_player() == 'O'
    assert game.board.cells[2 * 7 + 2] == EMPTY
    assert len(game.get_move_history()) == 1


def test_undo_clears_a_finished_game():
    game = Game(board_size=5, swap_rule=False)
    for col in range(4):
        game.make_move(col, 2)
        game.make_move(col, 4)
    game.make_move(4, 2)
    assert game.get_winner() == 'X'

    game.undo_last()
    assert game.get_winner() is None
    assert game.get_current_player() == 'X'


def test_undo_turn_gives_a_human_their_move_back():
    game = Game(board_size=7, with_bot=True, swap_rule=False)
    game.make_move(3, 3)  # human as X
    game.make_move(1, 1)  # bot as O
    assert game.get_current_player() == 'X'

    undone = game.undo_turn('X')
    assert undone == 2
    assert game.get_current_player() == 'X'
    assert game.get_move_history() == []


def test_swap_exchanges_seats_without_touching_the_board():
    game = Game(board_size=7, player_x="Ala", player_o="Bot")
    game.make_move(3, 3)
    stones = bytes(game.board.cells)

    assert game.can_swap()
    assert game.apply_swap()
    assert bytes(game.board.cells) == stones
    assert game.player_x == "Bot"
    assert game.player_o == "Ala"
    # The opening seat is taken; the other seat still owes a stone.
    assert game.get_current_player() == 'O'
    assert not game.can_swap()


def test_swap_is_only_offered_once_and_only_after_one_stone():
    game = Game(board_size=7)
    assert not game.can_swap()
    game.make_move(3, 3)
    assert game.can_swap()
    game.make_move(1, 1)
    assert not game.can_swap()


def test_swap_can_be_disabled():
    game = Game(board_size=7, swap_rule=False)
    game.make_move(3, 3)
    assert not game.can_swap()
    assert not game.apply_swap()


def test_undoing_a_swap_restores_the_seats():
    game = Game(board_size=7, player_x="Ala", player_o="Bot")
    game.make_move(3, 3)
    game.apply_swap()
    assert game.undo_last() == "swap"
    assert game.player_x == "Ala"
    assert game.player_o == "Bot"
    assert game.swapped is False
    assert game.can_swap()


def test_save_and_load_round_trip_with_a_swap():
    game = Game(board_size=9, player_x="Ala", player_o="Bot", swap_rule=True)
    game.make_move(4, 4)
    game.apply_swap()
    game.make_move(2, 3)
    game.make_move(5, 5)

    restored = Game.load_from_dict(game.serialize())
    assert bytes(restored.board.cells) == bytes(game.board.cells)
    assert restored.player_x == game.player_x
    assert restored.player_o == game.player_o
    assert restored.swapped is True
    assert restored.get_current_player() == game.get_current_player()
    assert restored.get_move_history() == game.get_move_history()


def test_version_one_saves_still_load():
    legacy = {
        "board_size": 7,
        "with_bot": False,
        "player_x": "Ala",
        "player_o": "Bob",
        "first": "X",
        "winner": None,
        "history": [["X", 3, 3], ["O", 1, 1]],
    }
    game = Game.load_from_dict(legacy)
    assert game.get_move_history() == [("X", 3, 3), ("O", 1, 1)]
    assert game.board.cells[3 * 7 + 3] != EMPTY
