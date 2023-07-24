from collections import defaultdict

from networkx import single_source_shortest_path_length

from .base import CopsInitializationHeuristic
from .util import CopPositions


class DegreeDistributedCopsInitHeuristic(CopsInitializationHeuristic):
    def compute_move(self) -> CopPositions:
        nodes = set(self.graph.nodes)
        max_degree_node = max(nodes, key=self.graph.degree.__getitem__)  # node with the highest degree

        # compute distances of all nodes to the node with the highest degree
        big_sentinel_distance = self.graph.number_of_nodes() + 1
        shortest_distances = defaultdict(
            lambda: big_sentinel_distance,
            single_source_shortest_path_length(self.graph, max_degree_node)
        )

        # sort all other nodes by the product of their degree with their distance to the highest degree node
        n_remaining_cops = self.n_cops - 1
        degree_distributed_nodes = list(nodes - {max_degree_node})
        degree_distributed_nodes.sort(key=lambda node: self.graph.degree[node] * shortest_distances[node])

        # place the cops at the node with the highest degree and at the nodes with the biggest degree-distributedness
        # factors
        return [max_degree_node] + degree_distributed_nodes[-n_remaining_cops:]
