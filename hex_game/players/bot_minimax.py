import math
import random
from collections import deque

class MinimaxBot:
    def __init__(self, symbol, depth=3):
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.depth = depth

    def make_move(self, board_obj):
        board = board_obj.get_state()
        empty_cells = sum(row.count('.') for row in board)

        # Dynamiczna zmiana głębokości
        if empty_cells > 40:
            self.depth = 2
        elif empty_cells > 20:
            self.depth = 3
        else:
            self.depth = 4

        moves = self.get_reasonable_moves(board_obj)

        # KILLER MOVE CHECK
        for x, y in moves:
            board_obj.apply_move(x, y, self.symbol)
            if board_obj.get_winner_simulation() == self.symbol:
                board_obj.undo_move(x, y)
                return (x, y)
            board_obj.undo_move(x, y)

        best_score = -math.inf
        best_move = None

        for x, y in moves:
            board_obj.apply_move(x, y, self.symbol)
            score = self.minimax(board_obj, self.depth - 1, False, -math.inf, math.inf)
            board_obj.undo_move(x, y)
            if score > best_score:
                best_score = score
                best_move = (x, y)

        return best_move or random.choice(board_obj.get_possible_moves())

    def get_reasonable_moves(self, board_obj):
        board = board_obj.get_state()
        size = len(board)
        neighbors = set()

        for y in range(size):
            for x in range(size):
                if board[y][x] != '.':
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < size and 0 <= ny < size and board[ny][nx] == '.':
                            neighbors.add((nx, ny))

        possible_moves = list(neighbors) if neighbors else board_obj.get_possible_moves()

        # ✨ Funkcja pomocnicza
        def will_opponent_win_if_play_here(x, y):
            board_obj.apply_move(x, y, self.opponent)
            winner = board_obj.get_winner_simulation()
            board_obj.undo_move(x, y)
            return winner == self.opponent

        # ✨ Styl gry dynamiczny
        my_dist = self._bfs_distance(board_obj, self.symbol)
        opp_dist = self._bfs_distance(board_obj, self.opponent)

        if opp_dist <= 2:
            style = "defensive"
        elif my_dist <= 3:
            style = "offensive"
        else:
            style = "balanced"

        # ✨ Priorytetyzacja ruchów
        def move_priority(move):
            x, y = move
            score = 0

            if will_opponent_win_if_play_here(x, y):
                score += 10000

            own_neighbors = 0
            opp_neighbors = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    if board[ny][nx] == self.symbol:
                        own_neighbors += 1
                    elif board[ny][nx] == self.opponent:
                        opp_neighbors += 1

            if style == "offensive":
                score += own_neighbors * 8
                score += opp_neighbors * 2
            elif style == "defensive":
                score += own_neighbors * 3
                score += opp_neighbors * 6
            else:  # balanced
                score += own_neighbors * 6
                score += opp_neighbors * 3

            center_x, center_y = size // 2, size // 2
            score -= (abs(x - center_x) + abs(y - center_y))

            return -score

        possible_moves.sort(key=move_priority)

        return possible_moves

    def minimax(self, board_obj, depth, maximizing, alpha, beta):
        winner = board_obj.get_winner_simulation()
        if winner == self.symbol:
            return 1000 + depth
        elif winner == self.opponent:
            return -1000 - depth
        elif depth == 0:
            return self.evaluate(board_obj)

        if maximizing:
            max_eval = -math.inf
            for x, y in board_obj.get_possible_moves():
                board_obj.apply_move(x, y, self.symbol)
                eval = self.minimax(board_obj, depth - 1, False, alpha, beta)
                board_obj.undo_move(x, y)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for x, y in board_obj.get_possible_moves():
                board_obj.apply_move(x, y, self.opponent)
                eval = self.minimax(board_obj, depth - 1, True, alpha, beta)
                board_obj.undo_move(x, y)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def evaluate(self, board_obj):
        board = board_obj.get_state()
        size = len(board)
        score = 0

        def max_connected_group(player):
            visited = set()
            max_size = 0

            def dfs(x, y):
                if (x, y) in visited:
                    return 0
                visited.add((x, y))
                count = 1
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < size and 0 <= ny < size:
                        if board[ny][nx] == player:
                            count += dfs(nx, ny)
                return count

            for y in range(size):
                for x in range(size):
                    if board[y][x] == player and (x, y) not in visited:
                        group_size = dfs(x, y)
                        max_size = max(max_size, group_size)
            return max_size

        my_dist = self._bfs_distance(board_obj, self.symbol)
        opp_dist = self._bfs_distance(board_obj, self.opponent)

        if my_dist == float('inf'):
            my_dist = size * 2
        if opp_dist == float('inf'):
            opp_dist = size * 2

        if my_dist <= 1:
            score += 10000
        elif my_dist == 2:
            score += 6000
        else:
            score += (size * 2 - my_dist) * 10

        if opp_dist <= 2:
            score -= 20000
        else:
            score -= (size * 2 - opp_dist) * 12

        # bonus za kontrolę środka
        center_x, center_y = size // 2, size // 2
        for y in range(size):
            for x in range(size):
                if board[y][x] == self.symbol:
                    if abs(x - center_x) <= 1 and abs(y - center_y) <= 1:
                        score += 5
                elif board[y][x] == self.opponent:
                    if abs(x - center_x) <= 1 and abs(y - center_y) <= 1:
                        score -= 5

        score += max_connected_group(self.symbol) * 35
        score -= max_connected_group(self.opponent) * 30

        return score

    def _bfs_distance(self, board_obj, player):
        board = board_obj.get_state()
        size = len(board)
        visited = set()
        queue = deque()

        if player == 'X':
            for y in range(size):
                if board[y][0] in ('.', player):
                    queue.append((0, y, 0))
        else:
            for x in range(size):
                if board[0][x] in ('.', player):
                    queue.append((x, 0, 0))

        while queue:
            x, y, dist = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if (player == 'X' and x == size - 1) or (player == 'O' and y == size - 1):
                return dist

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    cell = board[ny][nx]
                    if cell == player:
                        queue.appendleft((nx, ny, dist))
                    elif cell == '.':
                        queue.append((nx, ny, dist + 1))
        return float('inf')
