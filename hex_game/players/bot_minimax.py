import math
import time
from collections import deque

from hex_game.engine.geometry import CODES, EMPTY, O, X

WIN_SCORE = 1_000_000
UNREACHABLE = 1 << 30


class SearchTimeout(Exception):
    pass

def _other(code):
    return O if code == X else X

class MinimaxBot:
    def __init__(self, symbol, depth=4, time_limit=1.0):
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.code = CODES[symbol]
        self.opponent_code = _other(self.code)
        self.depth = depth
        self.max_depth = depth
        self.time_limit = time_limit
        self.nodes = 0
        self.reached_depth = 0

    def make_move(self, board):
        geometry = board.geometry
        candidates = self._candidates(board)
        if not candidates:
            return None

        immediate = self._decisive_move(board, candidates, self.code)
        if immediate is None:
            immediate = self._decisive_move(board, candidates, self.opponent_code)
        if immediate is not None:
            return geometry.coords(immediate)

        self.nodes = 0
        self.reached_depth = 0
        deadline = time.perf_counter() + self.time_limit
        best = candidates[0]

        for depth in range(1, self.max_depth + 1):
            try:
                best = self._search_root(board, depth, deadline, best)
            except SearchTimeout:
                break
            self.reached_depth = depth

        return geometry.coords(best)

    def set_seat(self, symbol):
        """Re-seat the agent, which the swap rule can do after the first move."""
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.code = CODES[symbol]
        self.opponent_code = _other(self.code)

    def should_swap(self, board):
        stones = [index for index, cell in enumerate(board.cells) if cell]
        if len(stones) != 1:
            return False
        positional = self._evaluate(board, _other(self.code))
        central = board.geometry.centre_distance[stones[0]] <= board.size / 2
        return positional > 0 and central

    def _decisive_move(self, board, candidates, code):
        for index in candidates:
            board.play(index, code)
            decided = board.winner_code == code
            board.undo()
            if decided:
                return index
        return None

    def _search_root(self, board, depth, deadline, preferred):
        candidates = self._ordered(board, self._candidates(board), self.code)
        if preferred in candidates:
            candidates.remove(preferred)
            candidates.insert(0, preferred)

        best_move = candidates[0]
        alpha = -math.inf
        for index in candidates:
            board.play(index, self.code)
            value = -self._negamax(
                board, depth - 1, -math.inf, -alpha, self.opponent_code, deadline
            )
            board.undo()
            if value > alpha:
                alpha = value
                best_move = index
        return best_move

    def _negamax(self, board, depth, alpha, beta, code, deadline):
        self.nodes += 1
        if self.nodes % 128 == 0 and time.perf_counter() > deadline:
            raise SearchTimeout

        if board.winner_code != EMPTY:
            return -(WIN_SCORE + depth)
        if depth == 0:
            return self._evaluate(board, code)

        best = -math.inf
        for index in self._ordered(board, self._candidates(board), code):
            board.play(index, code)
            value = -self._negamax(
                board, depth - 1, -beta, -alpha, _other(code), deadline
            )
            board.undo()
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best if best != -math.inf else self._evaluate(board, code)

    def _candidates(self, board):
        if not board.frontier:
            middle = board.size // 2
            return [board.geometry.index(middle, middle)]
        return list(board.frontier)

    def _ordered(self, board, candidates, code):
        geometry = board.geometry
        cells = board.cells
        opponent = _other(code)
        centre_distance = geometry.centre_distance

        def key(index):
            own = 0
            theirs = 0
            for neighbour in geometry.neighbours[index]:
                cell = cells[neighbour]
                if cell == code:
                    own += 1
                elif cell == opponent:
                    theirs += 1
            return -(own * 6 + theirs * 4) + centre_distance[index]

        candidates.sort(key=key)
        return candidates

    def _evaluate(self, board, code):
        mine = self._connection_distance(board, code)
        theirs = self._connection_distance(board, _other(code))
        if mine >= UNREACHABLE and theirs >= UNREACHABLE:
            return 0
        if mine >= UNREACHABLE:
            return -(WIN_SCORE // 2)
        if theirs >= UNREACHABLE:
            return WIN_SCORE // 2
        return (theirs - mine) * 100

    def _connection_distance(self, board, code):
        geometry = board.geometry
        cells = board.cells
        size = board.size
        opponent = _other(code)

        if code == X:
            sources = geometry.left_cells
            at_goal = lambda index: index % size == size - 1
        else:
            sources = geometry.top_cells
            at_goal = lambda index: index // size == size - 1

        distance = [UNREACHABLE] * geometry.cell_count
        queue = deque()
        for index in sources:
            cell = cells[index]
            if cell == opponent:
                continue
            step = 0 if cell == code else 1
            if step < distance[index]:
                distance[index] = step
                if step:
                    queue.append(index)
                else:
                    queue.appendleft(index)

        while queue:
            index = queue.popleft()
            current = distance[index]
            if at_goal(index):
                return current
            for neighbour in geometry.neighbours[index]:
                cell = cells[neighbour]
                if cell == opponent:
                    continue
                candidate = current + (0 if cell == code else 1)
                if candidate < distance[neighbour]:
                    distance[neighbour] = candidate
                    if candidate == current:
                        queue.appendleft(neighbour)
                    else:
                        queue.append(neighbour)
        return UNREACHABLE
