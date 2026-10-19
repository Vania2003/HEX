import math
import random
import time

from hex_game.engine.geometry import CODES, EMPTY, O, X


def _other(code):
    return O if code == X else X


class Node:
    __slots__ = ("move", "parent", "children", "untried", "visits", "reward",
                 "to_move", "rave_visits", "rave_reward")

    def __init__(self, move, parent, to_move, untried):
        self.move = move
        self.parent = parent
        self.to_move = to_move
        self.untried = untried
        self.children = []
        self.visits = 0
        self.reward = 0
        # AMAF statistics of the candidate moves of this node, keyed by move.
        self.rave_visits = {}
        self.rave_reward = {}


class MCTSBot:
    def __init__(self, symbol, time_limit=1.0, exploration=1.0,
                 max_simulations=None, seed=None, use_bridges=True,
                 use_rave=True, rave_bias=0.3):
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.code = CODES[symbol]
        self.opponent_code = _other(self.code)
        self.time_limit = time_limit
        self.exploration = exploration
        self.max_simulations = max_simulations
        self.use_bridges = use_bridges
        self.use_rave = use_rave
        self.rave_bias = rave_bias
        self.rng = random.Random(seed)

        self.geometry = None
        self.size = 0
        self.union_targets = None
        self.simulations = 0
        self.best_win_rate = 0.0

    def set_seat(self, symbol):
        self.symbol = symbol
        self.opponent = 'O' if symbol == 'X' else 'X'
        self.code = CODES[symbol]
        self.opponent_code = _other(self.code)

    # ------------------------------------------------------------------

    def make_move(self, board):
        self._bind(board)
        empties = board.legal_indices()
        if not empties:
            return None
        if len(empties) == self.geometry.cell_count:
            middle = board.size // 2
            return self.geometry.coords(self.geometry.index(middle, middle))

        root = Node(None, None, self.code, self._shuffled(empties))
        deadline = time.perf_counter() + self.time_limit
        budget = self.max_simulations or float("inf")

        self.simulations = 0
        while self.simulations < budget:
            if self.max_simulations is None and time.perf_counter() > deadline:
                break
            self._run_one(board, root)
            self.simulations += 1

        if not root.children:
            return self.geometry.coords(self.rng.choice(empties))
        best = max(root.children, key=lambda child: child.visits)
        self.best_win_rate = best.reward / best.visits
        return self.geometry.coords(best.move)

    # ------------------------------------------------------------------

    def _bind(self, board):
        if self.geometry is not board.geometry:
            geometry = board.geometry
            self.geometry = geometry
            self.size = board.size
            # Neighbours and own border nodes in one tuple per cell and colour,
            # so a playout can merge a stone into its group in a single pass.
            self.union_targets = {
                code: tuple(
                    geometry.neighbours[index] + geometry.border_nodes[index][slot]
                    for index in range(geometry.cell_count)
                )
                for code, slot in ((X, 0), (O, 1))
            }

    def _shuffled(self, moves):
        order = list(moves)
        self.rng.shuffle(order)
        return order

    def _run_one(self, board, root):
        node = root
        path = [root]
        tree_moves = []
        played = 0

        # Selection: descend through fully expanded nodes by UCT.
        while not node.untried and node.children:
            node = self._best_child(node)
            mover = _other(node.to_move)
            board.play(node.move, mover)
            tree_moves.append((node.move, mover))
            path.append(node)
            played += 1
            if board.winner_code:
                break

        winner = board.winner_code

        # Expansion: add one child for an untried move.
        if not winner and node.untried:
            move = node.untried.pop()
            mover = node.to_move
            board.play(move, mover)
            tree_moves.append((move, mover))
            played += 1
            child = Node(move, node, _other(mover), None)
            node.children.append(child)
            path.append(child)
            node = child
            winner = board.winner_code
            if not winner:
                node.untried = self._shuffled(board.legal_indices())
            else:
                node.untried = []

        # Simulation.
        trace = [] if self.use_rave else None
        if not winner:
            winner = self._playout(board, node.to_move, trace)

        self._backpropagate(path, tree_moves, trace, node.to_move, winner)

        for _ in range(played):
            board.undo()

    def _backpropagate(self, path, tree_moves, trace, playout_first, winner):
        # A move counts for RAVE at a node only if the player to move there is
        # the one who later played it, so the sets grow as we climb the path.
        if trace is None:
            played_by = None
        else:
            played_by = {X: set(), O: set()}
            mover = playout_first
            other = _other(mover)
            for move in trace:
                played_by[mover].add(move)
                mover, other = other, mover

        for depth in range(len(path) - 1, -1, -1):
            node = path[depth]
            node.visits += 1
            if node.parent is not None and winner == _other(node.to_move):
                node.reward += 1

            if played_by is not None:
                own = played_by[node.to_move]
                if own:
                    rave_visits = node.rave_visits
                    rave_reward = node.rave_reward
                    scored = winner == node.to_move
                    for move in own:
                        rave_visits[move] = rave_visits.get(move, 0) + 1
                        if scored:
                            rave_reward[move] = rave_reward.get(move, 0) + 1
                move, mover = tree_moves[depth - 1] if depth else (None, None)
                if move is not None:
                    played_by[mover].add(move)

    def _best_child(self, node):
        exploration = self.exploration
        log_parent = math.log(node.visits)
        rave_visits = node.rave_visits
        rave_reward = node.rave_reward
        squared_bias = 4.0 * self.rave_bias * self.rave_bias
        best = None
        best_value = -1.0
        for child in node.children:
            visits = child.visits
            value = child.reward / visits
            amaf_visits = rave_visits.get(child.move, 0)
            if amaf_visits:
                weight = amaf_visits / (
                    visits + amaf_visits + squared_bias * visits * amaf_visits
                )
                amaf_value = rave_reward.get(child.move, 0) / amaf_visits
                value += weight * (amaf_value - value)
            value += exploration * math.sqrt(log_parent / visits)
            if value > best_value:
                best_value = value
                best = child
        return best

    def _playout(self, board, to_move, trace=None):
        if self.use_bridges:
            return self._playout_with_bridges(board, to_move, trace)
        return self._playout_uniform(board, to_move, trace)

    def _playout_uniform(self, board, to_move, trace=None):
        # Only the final filled board matters: exactly one player is connected
        # on it, and that player is the one who won on the way, so the order in
        # which the remaining cells are filled makes no difference.
        scratch = bytearray(board.cells)
        empties = [index for index, cell in enumerate(scratch) if cell == EMPTY]
        self.rng.shuffle(empties)
        opponent = _other(to_move)
        for index in empties[0::2]:
            scratch[index] = to_move
        for index in empties[1::2]:
            scratch[index] = opponent
        if trace is not None:
            trace.extend(empties)
        return X if self._x_connected(scratch) else O

    def _playout_with_bridges(self, board, to_move, trace=None):
        # Whenever a player steps into a carrier of the opponent's bridge, the
        # opponent answers on the other carrier and so keeps the virtual
        # connection. Connectivity is tracked incrementally on the board's own
        # union-find so the fill can stop the moment somebody connects.
        geometry = self.geometry
        saves = geometry.playout_saves
        x_goals = geometry.goal_nodes(X)
        o_goals = geometry.goal_nodes(O)
        x_targets = self.union_targets[X]
        o_targets = self.union_targets[O]

        # A throwaway copy of the board's union-find: because it is discarded
        # after the playout it may be flattened by path halving, which the
        # rollback structure on the board cannot afford.
        parent = board.dsu.parent[:]

        scratch = bytearray(board.cells) + geometry.virtual_tail
        pool = [index for index, cell in enumerate(board.cells) if cell == EMPTY]
        self.rng.shuffle(pool)

        player = to_move
        opponent = _other(to_move)
        if to_move == X:
            goals, other_goals = x_goals, o_goals
            targets, other_targets = x_targets, o_targets
        else:
            goals, other_goals = o_goals, x_goals
            targets, other_targets = o_targets, x_targets
        player_replies = []
        opponent_replies = []
        cursor = 0

        while True:
            move = -1
            while player_replies:
                candidate = player_replies.pop()
                if scratch[candidate] == EMPTY:
                    move = candidate
                    break
            if move < 0:
                move = pool[cursor]
                while scratch[move] != EMPTY:
                    cursor += 1
                    move = pool[cursor]
                cursor += 1

            scratch[move] = player
            if trace is not None:
                trace.append(move)

            root = move
            while parent[root] != root:
                parent[root] = parent[parent[root]]
                root = parent[root]
            for other in targets[move]:
                if scratch[other] != player:
                    continue
                node = other
                while parent[node] != node:
                    parent[node] = parent[parent[node]]
                    node = parent[node]
                if node != root:
                    parent[node] = root

            start, end = goals
            while parent[start] != start:
                parent[start] = parent[parent[start]]
                start = parent[start]
            while parent[end] != end:
                parent[end] = parent[parent[end]]
                end = parent[end]
            if start == end:
                return player

            for first, second, rescue in saves[move]:
                if (scratch[first] == opponent and scratch[second] == opponent
                        and scratch[rescue] == EMPTY):
                    opponent_replies.append(rescue)

            player, opponent = opponent, player
            goals, other_goals = other_goals, goals
            targets, other_targets = other_targets, targets
            player_replies, opponent_replies = opponent_replies, player_replies

    def _x_connected(self, cells):
        geometry = self.geometry
        size = self.size
        neighbours = geometry.neighbours
        stack = [index for index in geometry.left_cells if cells[index] == X]
        seen = set(stack)
        while stack:
            index = stack.pop()
            if index % size == size - 1:
                return True
            for neighbour in neighbours[index]:
                if cells[neighbour] == X and neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        return False

    # ------------------------------------------------------------------

    def should_swap(self, board, samples=400):
        # Estimate how well the opening stone serves its owner by sampling
        # random completions of the current position.
        self._bind(board)
        opening_seat = self.opponent_code
        wins = 0
        for _ in range(samples):
            if self._playout(board, self.code) == opening_seat:
                wins += 1
        return wins > samples / 2
