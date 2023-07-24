from itertools import chain

from networkx import Graph, astar_path, floyd_warshall

from .base import CopsHeuristic
from .util import CopPositions, RobberPosition, compute_effective_game_graph, calc_graph_size
from ..minimax import CNRMinimaxEngine


class DisjointPathsCopsHeuristic(CopsHeuristic):
    MAX_BRUTEFORCE_GRAPH_SIZE = 30
    INTERSECTING_PATH_PENALTY = 10

    def __init__(self, graph: Graph, n_cops: int):
        super(DisjointPathsCopsHeuristic, self).__init__(graph, n_cops)
        self.minimax = CNRMinimaxEngine.factory_default(graph, n_cops)

    def compute_move(self, cop_positions: CopPositions, robber_position: RobberPosition) -> CopPositions:
        effective_game_graph = compute_effective_game_graph(self.graph, cop_positions, robber_position)
        effective_game_graph_size = calc_graph_size(effective_game_graph)

        if effective_game_graph_size <= self.MAX_BRUTEFORCE_GRAPH_SIZE:
            return self.minimax.best_cops_move(cop_positions, robber_position)

        who = {node: i for i, node in enumerate(self.graph.nodes)}
        distances = floyd_warshall(self.graph)
        move = []

        for cop_position in cop_positions:
            path = astar_path(self.graph, cop_position, robber_position, heuristic=lambda u, v: distances[u][v])
            assert len(path) >= 2, f"Path must have at least length 2. Otherwise the robber is already caught."
            move.append(path[1])

            path_neighbors = chain(*[list(self.graph.neighbors(node)) for node in path])
            path_neighbor_indices = [who[neighbor] for neighbor in path_neighbors]
            path_indices = [who[node] for node in path]

            distances[path_neighbor_indices] *= self.INTERSECTING_PATH_PENALTY
            distances[path_indices] *= self.INTERSECTING_PATH_PENALTY ** 2

        return move
