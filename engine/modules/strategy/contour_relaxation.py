from __future__ import annotations

import random
from collections import defaultdict

from networkx import Graph

from .base import BaseRobberStrategy
from ..abstraction import AbstractionHierarchy
from ..abstraction.store import ShortestPathLengthStore
from ..util import remaining_time, timeout_loop


class ContourRelaxationRobberStrategy(BaseRobberStrategy):
    hierarchy: AbstractionHierarchy
    shortest_path_lengths: ShortestPathLengthStore

    def __init__(self, graph: Graph, finish_time: float):
        self.hierarchy = AbstractionHierarchy(graph)
        self.hierarchy.populate_shortest_path_lengths(remaining_time(finish_time, 0.8))

        self.shortest_path_lengths = ShortestPathLengthStore()
        self.shortest_path_lengths.populate(graph, remaining_time(finish_time, 1))

    def init(self, cop_positions: list[int], finish_time: float) -> int:
        if self.shortest_path_lengths.is_populated:
            return max(
                self.hierarchy.graph.nodes,
                key=lambda node: min(
                    self.shortest_path_lengths.pairwise_distances[node][cop_position]
                    for cop_position in cop_positions
                )
            )
        elif (abstraction := self.hierarchy.lowest_shortest_path_length_abstraction()) is not None:
            abstract_node = max(
                abstraction.graph.nodes,
                key=lambda node: min(
                    abstraction.shortest_path_lengths.pairwise_distances[node][abstract_cop_position]
                    for abstract_cop_position in map(abstraction.abstract_node, cop_positions)
                )
            )

            return random.choice(abstraction.inverse_literal_vertex_mapping[abstract_node])
        else:
            return random.choice(list(self.hierarchy.graph.nodes))

    def step(self, cop_positions: list[int], robber_position: int, finish_time: float) -> int:
        """ Chooses the next robber position.

        The Contour Relaxation Strategy works similar to the Dijkstra algorithm. We iteratively expand the contours around all cop
        and robber vertices. At the end, the robber makes a step on the shortest path towards the node that was last relaxed by a
        cop contour. The heuristic here is that the robber tries to maximize the time to capture and should therefore move in a
        direction where it intersects as late as possible with a shortest path starting from any cop position.

        :param cop_positions: The current positions of the robbers in the graph.
        :param robber_position: The current position of the cop in the graph.
        :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
        :return: The next robber position.
        """
        visited = defaultdict(lambda: False)  # stores which vertices have been visited
        robber_predecessor = {}  # stores the predecessors to get to a vertex relaxed in a robber contour

        # checks if a vertex has been relaxed by any expansion
        def unvisited(_node: int) -> bool:
            return not visited[_node]

        def get_robber_move(_node: int) -> int:
            """ Computes the neighbor to which the robber has to move on the shortest path to a certain vertex.

            :param _node: The node the robber should move towards.
            :return: The neighbor of the current robber position that is on a shortest path to the given node.
            """
            while _node in robber_predecessor and robber_predecessor[_node] != robber_position:
                _node = robber_predecessor[_node]
            return _node

        cop_contour = set(cop_positions)  # initial contour around the cops are the current cop positions
        robber_contour = {robber_position}  # initial contour around the robber is the current robber position
        robber_cover_node = robber_position  # the robber position cannot be reached by any cop in 0 moves

        @timeout_loop(finish_time)
        def relax_and_expand_contour():
            nonlocal cop_contour, robber_contour, robber_cover_node

            next_cop_contour = set()
            next_robber_contour = set()

            # expand unvisited neighbors around the cop contours
            for node in filter(unvisited, cop_contour):
                visited[node] = True
                unvisited_neighbors = filter(unvisited, self.hierarchy.graph.neighbors(node))
                next_cop_contour.update(unvisited_neighbors)

            # expand unvisited neighbors around the robber contour
            for node in filter(unvisited, robber_contour):
                visited[node] = True
                # this vertex was expanded in the last iteration and hasn't been reached by any cop at that point
                robber_cover_node = node

                for neighbor in filter(unvisited, self.hierarchy.graph.neighbors(node)):
                    next_robber_contour.add(neighbor)
                    robber_predecessor[neighbor] = node

            cop_contour = next_cop_contour
            robber_contour = next_robber_contour

        # as long as there are contours to relax, relax the contours
        # if time runs out early, we stop early and use the best solution we got so far
        while cop_contour and robber_contour:
            if not relax_and_expand_contour():
                break

        return get_robber_move(robber_cover_node)
