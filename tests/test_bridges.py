import pytest

from hex_game.engine.geometry import O, X, BoardGeometry

SIZES = [5, 7, 11]


@pytest.mark.parametrize("size", SIZES)
def test_a_bridge_pair_is_not_adjacent_but_shares_two_neighbours(size):
    geometry = BoardGeometry.get(size)
    assert geometry.bridges
    for first, second, left, right in geometry.bridges:
        assert second not in geometry.neighbours[first]
        shared = set(geometry.neighbours[first]) & set(geometry.neighbours[second])
        assert shared == {left, right}


@pytest.mark.parametrize("size", SIZES)
def test_carriers_touch_both_ends_of_the_bridge(size):
    geometry = BoardGeometry.get(size)
    for first, second, left, right in geometry.bridges:
        for carrier in (left, right):
            assert first in geometry.neighbours[carrier]
            assert second in geometry.neighbours[carrier]


@pytest.mark.parametrize("size", SIZES)
def test_every_bridge_is_listed_once(size):
    geometry = BoardGeometry.get(size)
    pairs = [frozenset((first, second)) for first, second, _, _ in geometry.bridges]
    assert len(pairs) == len(set(pairs))


@pytest.mark.parametrize("size", SIZES)
def test_save_table_points_at_the_opposite_carrier(size):
    geometry = BoardGeometry.get(size)
    for carrier, entries in enumerate(geometry.bridge_saves):
        for first, second, rescue in entries:
            shared = set(geometry.neighbours[first]) & set(geometry.neighbours[second])
            assert shared == {carrier, rescue}


@pytest.mark.parametrize("size", SIZES)
def test_edge_bridges_sit_one_step_from_their_owner_border(size):
    geometry = BoardGeometry.get(size)
    assert geometry.edge_bridges
    for index, node, left, right in geometry.edge_bridges:
        col, row = geometry.coords(index)
        for carrier in (left, right):
            carrier_col, carrier_row = geometry.coords(carrier)
            assert index in geometry.neighbours[carrier]
            x_nodes, o_nodes = geometry.border_nodes[carrier]
            assert node in x_nodes + o_nodes
            if node in (geometry.left_node, geometry.right_node):
                assert col in (1, size - 2)
                assert carrier_col in (0, size - 1)
            else:
                assert row in (1, size - 2)
                assert carrier_row in (0, size - 1)


@pytest.mark.parametrize("size", SIZES)
def test_virtual_tail_colours_match_the_goal_borders(size):
    geometry = BoardGeometry.get(size)
    tail = geometry.virtual_tail
    assert len(tail) == geometry.node_count - geometry.cell_count
    for node in geometry.goal_nodes(X):
        assert tail[node - geometry.cell_count] == X
    for node in geometry.goal_nodes(O):
        assert tail[node - geometry.cell_count] == O


def test_known_bridge_on_an_11_board():
    # Axial (0, 0) and (1, 1) are a bridge; their carriers are (1, 0) and (0, 1).
    geometry = BoardGeometry.get(11)
    first = geometry.index(*_from_axial(0, 0))
    second = geometry.index(*_from_axial(1, 1))
    carriers = {geometry.index(*_from_axial(1, 0)), geometry.index(*_from_axial(0, 1))}
    for a, b, left, right in geometry.bridges:
        if {a, b} == {first, second}:
            assert {left, right} == carriers
            break
    else:
        pytest.fail("expected bridge between axial (0,0) and (1,1)")


def _from_axial(q, r):
    from hex_game.engine.geometry import from_axial
    return from_axial(q, r)
