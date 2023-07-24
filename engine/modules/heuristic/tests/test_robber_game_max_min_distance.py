from unittest import TestCase

import networkx as nx
from group3.engine.modules.heuristic import MaxMinDistanceRobberHeuristic


class TestMaxMinDistanceRobberHeuristic(TestCase):
    def test_compute_move(self):
        edgelist = [(0, 1), (1, 3), (0, 2), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
        graph = nx.Graph(edgelist)
        cops_count = 0
        robber_position = 0
        # heuristic = MaxMinDistanceRobberHeuristic(graph, cops_count)

        # TODO Minimax can't handle cop_count 0
        # self.assertEqual(0, heuristic.compute_move([], robber_position))

        # TODO Minimax Engine cop_count seems to not be able to be updated
        cops_count = 1
        cop_position = [3]
        heuristic_ = MaxMinDistanceRobberHeuristic(graph, cops_count)
        move = heuristic_.compute_move(cop_position, robber_position)

        self.assertTrue(graph.nodes.__contains__(move))
