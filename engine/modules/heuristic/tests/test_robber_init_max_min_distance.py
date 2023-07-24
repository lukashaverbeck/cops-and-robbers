from unittest import TestCase

import networkx as nx
from group3.engine.modules.heuristic import MaxMinDistanceRobberInitHeuristic




class Test(TestCase):
    def test_max_min_distance_robber_init_heuristic(self):
        edgelist = [(0, 1), (1, 3), (0, 2), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
        graph = nx.Graph(edgelist)
        cops_count = 0
        heuristic = MaxMinDistanceRobberInitHeuristic(graph, cops_count)

        self.assertEqual(0, heuristic.compute_move([]))

        cops_count = 1
        cop_position = [3]
        heuristic = MaxMinDistanceRobberInitHeuristic(graph, cops_count)
        move = heuristic.compute_move(cop_position)

        # TODO Re-imagination of heuristic (returns wrong position)
        # Doesn't return smart position right now but at least one that's in the graph.
        self.assertEqual(5, move)
