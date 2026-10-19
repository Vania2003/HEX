import pytest

from hex_game.engine.geometry import AXIAL_DIRECTIONS, BoardGeometry, from_axial, to_axial

SIZES = [3, 5, 11]


@pytest.mark.parametrize("size", SIZES)
def test_adjacency_is_symmetric(size):
    geometry = BoardGeometry.get(size)
    for index in range(geometry.cell_count):
        for neighbour in geometry.neighbours[index]:
            assert index in geometry.neighbours[neighbour]


@pytest.mark.parametrize("size", SIZES)
def test_offset_neighbours_are_the_axial_neighbours(size):
    """The parity rule must be exactly the six fixed axial directions."""
    geometry = BoardGeometry.get(size)
    for index in range(geometry.cell_count):
        col, row = geometry.coords(index)
        q, r = to_axial(col, row)

        expected = set()
        for dq, dr in AXIAL_DIRECTIONS:
            ncol, nrow = from_axial(q + dq, r + dr)
            if 0 <= ncol < size and 0 <= nrow < size:
                expected.add(geometry.index(ncol, nrow))

        assert set(geometry.neighbours[index]) == expected


@pytest.mark.parametrize("size", SIZES)
def test_axial_roundtrip(size):
    for row in range(size):
        for col in range(size):
            assert from_axial(*to_axial(col, row)) == (col, row)


@pytest.mark.parametrize("size", SIZES)
def test_interior_cells_have_six_neighbours(size):
    geometry = BoardGeometry.get(size)
    interior = [
        index
        for index in range(geometry.cell_count)
        if len(geometry.neighbours[index]) == 6
    ]
    assert interior, "every board above size 2 has interior cells"
    for index in interior:
        col, row = geometry.coords(index)
        assert 0 < col < size - 1 and 0 < row < size - 1


def test_geometry_instances_are_shared():
    assert BoardGeometry.get(11) is BoardGeometry.get(11)
