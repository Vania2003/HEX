from collections import deque

from hex_game.engine.geometry import CODES, EMPTY, SYMBOLS, X, BoardGeometry
from hex_game.engine.union_find import RollbackUnionFind

class Board:
    def __init__(self, size=11):
        self.size = size
        self.geometry = BoardGeometry.get(size)
        self.cells = bytearray(self.geometry.cell_count)
        self.empty_count = self.geometry.cell_count
        self.winner_code = EMPTY
        self._dsu = RollbackUnionFind(self.geometry.node_count)
        self._undo_stack = []
        self._winning_path = None

        self.frontier = set()
        self._occupied_neighbours = [0] * self.geometry.cell_count

    @property
    def dsu(self):
        """Exposed so a search can union and roll back on the live structure."""
        return self._dsu

    def play(self, index, code):
        geometry = self.geometry
        dsu = self._dsu
        mark = dsu.mark()

        self.cells[index] = code
        self.empty_count -= 1

        self.frontier.discard(index)
        counts = self._occupied_neighbours
        for neighbour in geometry.neighbours[index]:
            counts[neighbour] += 1
            if self.cells[neighbour] == code:
                dsu.union(index, neighbour)
            elif self.cells[neighbour] == EMPTY:
                self.frontier.add(neighbour)
        for border in geometry.border_nodes[index][0 if code == X else 1]:
            dsu.union(index, border)

        self._undo_stack.append((index, mark, self.winner_code))
        if self.winner_code == EMPTY:
            start, end = geometry.goal_nodes(code)
            if dsu.connected(start, end):
                self.winner_code = code
                self._winning_path = None

    def undo(self):
        index, mark, previous_winner = self._undo_stack.pop()
        self.cells[index] = EMPTY
        self.empty_count += 1
        self._dsu.rollback(mark)
        self.winner_code = previous_winner
        self._winning_path = None

        counts = self._occupied_neighbours
        for neighbour in self.geometry.neighbours[index]:
            counts[neighbour] -= 1
            if counts[neighbour] == 0 and self.cells[neighbour] == EMPTY:
                self.frontier.discard(neighbour)
        if counts[index]:
            self.frontier.add(index)
        return index

    def legal_indices(self):
        cells = self.cells
        return [index for index in range(len(cells)) if cells[index] == EMPTY]

    def is_empty(self, index):
        return self.cells[index] == EMPTY

    def copy(self):
        clone = Board.__new__(Board)
        clone.size = self.size
        clone.geometry = self.geometry
        clone.cells = bytearray(self.cells)
        clone.empty_count = self.empty_count
        clone.winner_code = self.winner_code
        clone._dsu = self._dsu.copy()
        clone._undo_stack = self._undo_stack[:]
        clone._winning_path = None
        clone.frontier = set(self.frontier)
        clone._occupied_neighbours = self._occupied_neighbours[:]
        return clone

    def is_valid_move(self, x, y):
        return (
            0 <= x < self.size
            and 0 <= y < self.size
            and self.cells[y * self.size + x] == EMPTY
        )

    def place_piece(self, x, y, player):
        if not self.is_valid_move(x, y):
            return False
        self.play(y * self.size + x, CODES[player])
        return True

    def apply_move(self, x, y, player):
        self.play(y * self.size + x, CODES[player])

    def undo_move(self, x=None, y=None):
        self.undo()

    def get_cell(self, x, y):
        return SYMBOLS[self.cells[y * self.size + x]]

    def get_state(self):
        size = self.size
        cells = self.cells
        return [
            [SYMBOLS[cells[row * size + col]] for col in range(size)]
            for row in range(size)
        ]

    def get_possible_moves(self):
        size = self.size
        return [(index % size, index // size) for index in self.legal_indices()]

    @property
    def winner(self):
        return SYMBOLS[self.winner_code] if self.winner_code else None

    def has_connection(self, player):
        code = CODES[player] if isinstance(player, str) else player
        start, end = self.geometry.goal_nodes(code)
        return self._dsu.connected(start, end)

    def get_winner_simulation(self):
        return self.winner

    def find_winner(self):
        return self.winner

    def get_winning_path(self):
        if self.winner_code == EMPTY:
            return []
        if self._winning_path is None:
            self._winning_path = self._compute_winning_path(self.winner_code)
        return self._winning_path

    def _compute_winning_path(self, code):
        """Shortest chain of own stones joining the player's two borders."""
        geometry = self.geometry
        cells = self.cells
        if code == X:
            sources, is_target = geometry.left_cells, set(geometry.right_cells)
        else:
            sources, is_target = geometry.top_cells, set(geometry.bottom_cells)

        previous = {}
        queue = deque()
        for index in sources:
            if cells[index] == code:
                previous[index] = None
                queue.append(index)

        while queue:
            index = queue.popleft()
            if index in is_target:
                path = []
                while index is not None:
                    path.append(geometry.coords(index))
                    index = previous[index]
                path.reverse()
                return path
            for neighbour in geometry.neighbours[index]:
                if cells[neighbour] == code and neighbour not in previous:
                    previous[neighbour] = index
                    queue.append(neighbour)
        return []
