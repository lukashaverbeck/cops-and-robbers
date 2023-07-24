import unittest
import networkx as nx
import numpy as np

from group3.engine.modules.minimax.engine import effective_game_graph


class TestEngine(unittest.TestCase):

    def test_effective_game_graph(self):
        edgelist = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
        graph = nx.Graph(edgelist)
        cop_positions = np.array([3, 6])
        robber_position = 1
        actual = effective_game_graph(graph, cop_positions, robber_position)
        expected = None

        self.assertTrue((actual == expected).all())
