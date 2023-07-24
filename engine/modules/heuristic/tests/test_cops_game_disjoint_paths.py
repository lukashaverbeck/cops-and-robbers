from unittest import TestCase

import networkx as nx

from group3.engine.modules.heuristic import DisjointPathsCopsHeuristic


class TestDisjointPathsCopsHeuristic(TestCase):
    def test_compute_move(self):
        edgelist = [(0, 1), (1, 3), (0, 2), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
        graph = nx.Graph(edgelist)
        cops_count = 1
        cop_position = [3]
        robber_position = 2
        heuristic_ = DisjointPathsCopsHeuristic(graph, cops_count)
        moves = heuristic_.compute_move(cop_position, robber_position)

        self.assertTrue(graph.nodes.__contains__(move) for move in moves)

