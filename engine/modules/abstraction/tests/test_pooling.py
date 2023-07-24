import collections
import math
import random
from unittest import TestCase
from networkx import Graph, gnm_random_graph

from group3.engine.modules.abstraction.pooling import abstract_vertex_pooling


def generate_random_graph() -> Graph:
    average_degree = random.randint(3, 7)
    num_of_nodes = random.randint(5, 40)
    return gnm_random_graph(num_of_nodes, num_of_nodes*average_degree)


class Test(TestCase):

    def test_abstract_vertex_pooling(self):
        for i in range(1):
            graph = generate_random_graph()
            pooling = abstract_vertex_pooling(graph)

            # Test if the correct number of nodes is present in the pooling
            self.assertEqual(math.ceil(graph.number_of_nodes()/2), len(collections.Counter(pooling.values())))
