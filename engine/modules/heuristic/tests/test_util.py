from unittest import TestCase

import networkx as nx

from group3.engine.modules.heuristic.util import calc_graph_size, compute_cop_uncontrolled_subgraph, \
    compute_effective_game_graph

EDGELIST = [(0, 1), (1, 3), (0, 2), (2, 3), (3, 4), (4, 5), (4, 6), (5, 6)]


class Test(TestCase):
    def test_compute_cop_uncontrolled_subgraph(self):
        # Empty graph, empty cop pos:
        graph = nx.Graph()
        cop_pos = []

        self.assertEqual(graph.nodes, compute_cop_uncontrolled_subgraph(graph, cop_pos).nodes,
                         "Error with empty inputs")

        graph = nx.Graph(EDGELIST)
        cop_pos = [0]

        self.assertEqual(graph.subgraph([3, 4, 5, 6]).edges, compute_cop_uncontrolled_subgraph(graph, cop_pos).edges,
                         "Wrong edges returned")

        self.assertEqual(graph.subgraph([3, 4, 5, 6]).nodes, compute_cop_uncontrolled_subgraph(graph, cop_pos).nodes,
                         "Wrong node sets returned")

    def test_compute_effective_game_graph(self):
        graph = nx.Graph(EDGELIST)
        cop_pos = [0]
        robber_pos = 3

        # TODO Folgefehler mit Lukas besprechen
        self.assertEqual(graph.subgraph([0, 3, 4, 5, 6]).nodes,
                         compute_effective_game_graph(graph, cop_pos, robber_pos).nodes, "Returned wrong game graph")

    def test_calc_graph_size(self):
        # Test for none graph
        graph = None
        self.assertRaises(AttributeError, calc_graph_size, graph)
        # Test for empty graph
        graph = nx.Graph()
        self.assertEqual(0, calc_graph_size(graph), "Empty graph error")
        # Test for known graph
        graph = nx.Graph(EDGELIST)
        self.assertEqual(15, calc_graph_size(graph), "Wrong size for custom graph")



