class Board:
    def __init__(self, size=11):
        self.size = size
        self.grid = [['.' for _ in range(size)] for _ in range(size)]
        self.winner = None
        self.winning_path = []

    def is_valid_move(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size and self.grid[y][x] == '.'

    def place_piece(self, x, y, player):
        if self.is_valid_move(x, y):
            self.grid[y][x] = player
            return True
        return False

    def get_state(self):
        return self.grid

    def has_connection(self, player):
        visited = set()
        size = self.size

        def neighbors(x, y):
            if x % 2 == 0:
                return [
                    (x - 1, y), (x + 1, y),
                    (x, y - 1), (x, y + 1),
                    (x - 1, y - 1), (x + 1, y - 1)
                ]
            else:
                return [
                    (x - 1, y), (x + 1, y),
                    (x, y - 1), (x, y + 1),
                    (x - 1, y + 1), (x + 1, y + 1)
                ]

        def dfs(x, y):
            if (x, y) in visited:
                return False
            visited.add((x, y))

            if player == 'X' and x == size - 1:
                return True
            if player == 'O' and y == size - 1:
                return True

            for nx, ny in neighbors(x, y):
                if 0 <= nx < size and 0 <= ny < size:
                    if self.grid[ny][nx] == player and (nx, ny) not in visited:
                        if dfs(nx, ny):
                            return True
            return False

        if player == 'X':
            for y in range(size):
                if self.grid[y][0] == 'X':
                    if dfs(0, y):
                        return True
        else:
            for x in range(size):
                if self.grid[0][x] == 'O':
                    if dfs(x, 0):
                        return True

        return False

    def find_winner(self):
        """Sprawdza realnie kto wygrał i zapamiętuje ścieżkę."""
        visited = set()
        path = []
        size = self.size

        def neighbors(x, y):
            if x % 2 == 0:
                return [
                    (x - 1, y), (x + 1, y),
                    (x, y - 1), (x, y + 1),
                    (x - 1, y - 1), (x + 1, y - 1)
                ]
            else:
                return [
                    (x - 1, y), (x + 1, y),
                    (x, y - 1), (x, y + 1),
                    (x - 1, y + 1), (x + 1, y + 1)
                ]

        def dfs(x, y, trace):
            if (x, y) in visited:
                return False
            visited.add((x, y))
            trace.append((x, y))

            if player == 'X' and x == size - 1:
                path.extend(trace)
                return True
            if player == 'O' and y == size - 1:
                path.extend(trace)
                return True

            for nx, ny in neighbors(x, y):
                if 0 <= nx < size and 0 <= ny < size:
                    if self.grid[ny][nx] == player and (nx, ny) not in visited:
                        if dfs(nx, ny, trace.copy()):
                            return True
            trace.pop()
            return False

        for player in ['X', 'O']:
            visited.clear()
            if player == 'X':
                for y in range(size):
                    if self.grid[y][0] == 'X':
                        if dfs(0, y, []):
                            self.winner = 'X'
                            self.winning_path = path
                            return 'X'
            else:
                for x in range(size):
                    if self.grid[0][x] == 'O':
                        if dfs(x, 0, []):
                            self.winner = 'O'
                            self.winning_path = path
                            return 'O'
        return None

    def get_possible_moves(self):
        return [(x, y) for y in range(self.size) for x in range(self.size) if self.grid[y][x] == '.']

    def apply_move(self, x, y, player):
        self.grid[y][x] = player

    def undo_move(self, x, y):
        self.grid[y][x] = '.'

    def get_winner_simulation(self):
        for player in ['X', 'O']:
            if self.has_connection(player):
                return player
        return None

    def get_winning_path(self):
        return self.winning_path if hasattr(self, "winning_path") else []
