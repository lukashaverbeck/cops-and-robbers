import unittest
import networkx as nx
import numpy as np

from group3.engine.modules.minimax.iterative_deepening import restore_possible_move_permutation, cops_transitions

class TestIterativeDeepening(unittest.TestCase):

    def test_restore_possible_move_permutation(self):
        edgelist = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]
        graph = nx.Graph(edgelist)
        cop_positions = np.array([3, 6])
        move = [1, 3, 4]
        actual = _restore_possible_move_permutation(graph, cop_positions, move)
        expected = None

        self.assertTrue((actual == expected).all())

    def test_cops_transitions(self):
        _cop_positions = [3, 6]
        _robber_positions = 1
        actual = cops_transitions(_cop_positions, _robber_positions)
        expected = None

        self.assertTrue((actual == expected).all())
