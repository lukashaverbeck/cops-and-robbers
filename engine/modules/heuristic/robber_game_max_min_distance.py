from networkx import Graph, all_pairs_shortest_path_length

from .base import RobberHeuristic
from .util import CopPositions, RobberPosition, compute_effective_game_graph, calc_graph_size, VertexT
from ..minimax import CNRMinimaxEngine


class MaxMinDistanceRobberHeuristic(RobberHeuristic):
    MAX_BRUTEFORCE_GRAPH_SIZE = 30

    def __init__(self, graph: Graph, n_cops: int):
        super(MaxMinDistanceRobberHeuristic, self).__init__(graph, n_cops)
        self.minimax = CNRMinimaxEngine.factory_default(graph, n_cops)

    def compute_move(self, cop_positions: CopPositions, robber_position: RobberPosition) -> RobberPosition:
        effective_game_graph = compute_effective_game_graph(self.graph, cop_positions, robber_position)
        effective_game_graph_size = calc_graph_size(effective_game_graph)

        if effective_game_graph_size <= self.MAX_BRUTEFORCE_GRAPH_SIZE:
            return self.minimax.best_robber_move(cop_positions, robber_position)

        possible_next_positions = {robber_position}.union(effective_game_graph.neighbors(robber_position))
        cop_distances = dict(all_pairs_shortest_path_length(effective_game_graph))

        def compute_min_cop_distance(position: VertexT) -> int:
            return min(cop_distances[cop_position][position] for cop_position in cop_positions)

        almost_caught = int(compute_min_cop_distance(robber_position) == 1)
        possible_next_positions = filter(
            lambda position: compute_min_cop_distance(position) > 1 - almost_caught,
            possible_next_positions
        )

        return max(
            possible_next_positions,
            key=lambda position: sum(cop_distances[cop_position][position] for cop_position in cop_positions)
        )
