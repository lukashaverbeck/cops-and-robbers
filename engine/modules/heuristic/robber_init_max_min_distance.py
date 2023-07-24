import sys

from networkx import connected_components, Graph, multi_source_dijkstra_path_length

from .base import RobberInitializationHeuristic
from .util import CopPositions, RobberPosition, compute_cop_uncontrolled_subgraph


class MaxMinDistanceRobberInitHeuristic(RobberInitializationHeuristic):
    def compute_move(self, cop_positions: CopPositions) -> RobberPosition:
        if len(cop_positions) == 0:
            return list(self.graph)[0]

        cop_uncontrolled_subgraph: Graph = compute_cop_uncontrolled_subgraph(self.graph, cop_positions)
        cop_uncontrolled_components: list[set] = list(connected_components(cop_uncontrolled_subgraph))
        biggest_robber_controlled_component: set = max(cop_uncontrolled_components, key=len)
        robber_subgraph: Graph = self.graph.subgraph(biggest_robber_controlled_component | set(cop_positions))
        distances = multi_source_dijkstra_path_length(robber_subgraph, cop_positions)
        # TODO Rethink strategy doesn't work in some small examples we found, also multi_source_dijkstra_path_length
        # TODO ignores nodes that aren't connected to any cop_positions in the subgraph, leading to errors
        # hacked solution that doesn't solve anything except return a valid position in the graph
        for node in robber_subgraph.nodes:
            if node not in distances:
                distances[node] = int(sys.maxsize)
        return max(distances, key=distances.get)
