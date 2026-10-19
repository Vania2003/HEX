"""Single source of truth for the Hex board geometry.

Cells are stored in a flat array of ``size * size`` entries, addressed by
``index = row * size + col``.  Storage coordinates ``(col, row)`` are an even-q
offset projection of axial coordinates ``(q, r)``::

    q = col
    r = row - col // 2

Under that bijection the six fixed axial neighbours ``(q+1, r), (q-1, r),
(q, r+1), (q, r-1), (q+1, r-1), (q-1, r+1)`` turn into the parity-dependent
offsets listed below.  Expressing them once here keeps the engine, the bots and
the renderer on the same graph; the previous code had the axial deltas
hard-coded in the bot and the offset deltas hard-coded in the board, which are
two different graphs that disagree on 27% of the edges.

X owns the LEFT and RIGHT borders, O owns the TOP and BOTTOM borders.  Each
border is exposed as a virtual node placed just past the real cells, so that a
disjoint-set structure can answer "has this player connected its two sides?"
without searching the board.
"""

AXIAL_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))

EVEN_COL_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1))
ODD_COL_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, 1))

EMPTY = 0
X = 1
O = 2

SYMBOLS = {EMPTY: '.', X: 'X', O: 'O'}
CODES = {'.': EMPTY, 'X': X, 'O': O}


def to_axial(col, row):
    return col, row - col // 2


def from_axial(q, r):
    return q, r + q // 2


class BoardGeometry:
    """Pre-computed adjacency and border tables for one board size."""

    _cache = {}

    def __init__(self, size):
        self.size = size
        self.cell_count = size * size

        # Virtual border nodes live right after the real cells.
        self.left_node = self.cell_count
        self.right_node = self.cell_count + 1
        self.top_node = self.cell_count + 2
        self.bottom_node = self.cell_count + 3
        self.node_count = self.cell_count + 4

        self.neighbours = tuple(
            self._compute_neighbours(index) for index in range(self.cell_count)
        )
        self.border_nodes = tuple(
            self._compute_border_nodes(index) for index in range(self.cell_count)
        )

        self.left_cells = tuple(self.index(0, row) for row in range(size))
        self.right_cells = tuple(self.index(size - 1, row) for row in range(size))
        self.top_cells = tuple(self.index(col, 0) for col in range(size))
        self.bottom_cells = tuple(self.index(col, size - 1) for col in range(size))

        centre = (size - 1) / 2.0
        self.centre_distance = tuple(
            abs(index % size - centre) + abs(index // size - centre)
            for index in range(self.cell_count)
        )

    @classmethod
    def get(cls, size):
        geometry = cls._cache.get(size)
        if geometry is None:
            geometry = cls(size)
            cls._cache[size] = geometry
        return geometry

    def index(self, col, row):
        return row * self.size + col

    def coords(self, index):
        return index % self.size, index // self.size

    def axial(self, index):
        col, row = self.coords(index)
        return to_axial(col, row)

    def _compute_neighbours(self, index):
        col, row = self.coords(index)
        deltas = EVEN_COL_DELTAS if col % 2 == 0 else ODD_COL_DELTAS
        result = []
        for dcol, drow in deltas:
            ncol, nrow = col + dcol, row + drow
            if 0 <= ncol < self.size and 0 <= nrow < self.size:
                result.append(self.index(ncol, nrow))
        return tuple(result)

    def _compute_border_nodes(self, index):
        """Virtual nodes a stone on this cell should be merged with, per player."""
        col, row = self.coords(index)
        x_nodes = []
        o_nodes = []
        if col == 0:
            x_nodes.append(self.left_node)
        if col == self.size - 1:
            x_nodes.append(self.right_node)
        if row == 0:
            o_nodes.append(self.top_node)
        if row == self.size - 1:
            o_nodes.append(self.bottom_node)
        return tuple(x_nodes), tuple(o_nodes)

    def goal_nodes(self, player):
        if player == X:
            return self.left_node, self.right_node
        return self.top_node, self.bottom_node
