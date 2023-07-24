from unittest import TestCase

import networkx as nx

from group3.engine.modules.heuristic import DegreeDistributedCopsInitHeuristic

EDGELIST = [(0, 1), (1, 3), (0, 2), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]


class TestDegreeDistributedCopsInitHeuristic(TestCase):
    def test_compute_move(self):
        graph = nx.Graph(EDGELIST)
        cops_count = 2
        heuristic = DegreeDistributedCopsInitHeuristic(graph, cops_count)
        cops_init_pos = heuristic.compute_move()

        self.assertCountEqual([3, 6], cops_init_pos)
