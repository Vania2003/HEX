"""Disjoint-set structure that supports undoing unions.

Union by size without path compression keeps every union reversible, which is
what a game-tree search needs: ``mark()`` before a move, ``rollback(mark)`` when
the move is taken back.  Find stays O(log n), which is far cheaper than the
full board DFS the engine used to run after every single move.
"""


class RollbackUnionFind:
    __slots__ = ("parent", "size", "_log")

    def __init__(self, count):
        self.parent = list(range(count))
        self.size = [1] * count
        self._log = []

    def find(self, node):
        parent = self.parent
        while parent[node] != node:
            node = parent[node]
        return node

    def union(self, a, b):
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a == root_b:
            return False
        if self.size[root_a] < self.size[root_b]:
            root_a, root_b = root_b, root_a
        self.parent[root_b] = root_a
        self.size[root_a] += self.size[root_b]
        self._log.append((root_a, root_b))
        return True

    def connected(self, a, b):
        return self.find(a) == self.find(b)

    def mark(self):
        return len(self._log)

    def rollback(self, mark):
        log = self._log
        parent = self.parent
        size = self.size
        while len(log) > mark:
            root_a, root_b = log.pop()
            parent[root_b] = root_b
            size[root_a] -= size[root_b]

    def copy(self):
        clone = RollbackUnionFind.__new__(RollbackUnionFind)
        clone.parent = self.parent[:]
        clone.size = self.size[:]
        clone._log = self._log[:]
        return clone
