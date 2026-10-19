AXIAL_DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1))

# A bridge joins two cells that share exactly two empty neighbours (the
# carrier). It is a virtual connection: whichever carrier the opponent takes,
# the other one still joins the pair.
AXIAL_BRIDGE_DIRECTIONS = ((1, 1), (2, -1), (1, -2), (-1, -1), (-2, 1), (-1, 2))

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
    _cache = {}

    def __init__(self, size):
        self.size = size
        self.cell_count = size * size
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

        self.bridges = self._compute_bridges()
        self.edge_bridges = self._compute_edge_bridges()
        self.bridge_saves = self._compute_bridge_saves()
        self.edge_bridge_saves = self._compute_edge_bridge_saves()
        self.playout_saves = tuple(
            cell_entries + edge_entries
            for cell_entries, edge_entries
            in zip(self.bridge_saves, self.edge_bridge_saves)
        )
        # Appended to a playout board so that the four border nodes can be read
        # like ordinary stones, which lets edge bridges share the cell path.
        self.virtual_tail = bytes((X, X, O, O))

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

    def _compute_bridges(self):
        neighbour_sets = [set(group) for group in self.neighbours]
        found = []
        seen = set()
        for first in range(self.cell_count):
            q, r = self.axial(first)
            for dq, dr in AXIAL_BRIDGE_DIRECTIONS:
                col, row = from_axial(q + dq, r + dr)
                if not (0 <= col < self.size and 0 <= row < self.size):
                    continue
                second = self.index(col, row)
                key = (min(first, second), max(first, second))
                if key in seen:
                    continue
                carriers = neighbour_sets[first] & neighbour_sets[second]
                if len(carriers) != 2:
                    continue
                seen.add(key)
                left, right = sorted(carriers)
                found.append((first, second, left, right))
        return tuple(found)

    def _compute_edge_bridges(self):
        """A cell one step from its owner's border bridges to that border."""
        found = []
        for index in range(self.cell_count):
            col, row = self.coords(index)
            for node, on_approach, on_border in (
                (self.left_node, col == 1, lambda c, r: c == 0),
                (self.right_node, col == self.size - 2, lambda c, r: c == self.size - 1),
                (self.top_node, row == 1, lambda c, r: r == 0),
                (self.bottom_node, row == self.size - 2, lambda c, r: r == self.size - 1),
            ):
                if not on_approach:
                    continue
                carriers = sorted(
                    neighbour
                    for neighbour in self.neighbours[index]
                    if on_border(*self.coords(neighbour))
                )
                if len(carriers) == 2:
                    found.append((index, node, carriers[0], carriers[1]))
        return tuple(found)

    def _compute_bridge_saves(self):
        saves = [[] for _ in range(self.cell_count)]
        for first, second, left, right in self.bridges:
            saves[left].append((first, second, right))
            saves[right].append((first, second, left))
        return tuple(tuple(group) for group in saves)

    def _compute_edge_bridge_saves(self):
        saves = [[] for _ in range(self.cell_count)]
        for index, node, left, right in self.edge_bridges:
            saves[left].append((index, node, right))
            saves[right].append((index, node, left))
        return tuple(tuple(group) for group in saves)

    def goal_nodes(self, player):
        if player == X:
            return self.left_node, self.right_node
        return self.top_node, self.bottom_node
