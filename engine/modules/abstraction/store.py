import math
from abc import ABC, abstractmethod
from typing import final

from networkx import Graph, shortest_path_length

from ..util import timeout_loop


class Store(ABC):
    is_populated: bool

    def __init__(self):
        self.is_populated = False

    @final
    def populate(self, graph: Graph, finish_time: float, *args, **kwargs) -> bool:
        self.is_populated = self._populate(graph, finish_time, *args, **kwargs)
        return self.is_populated

    @abstractmethod
    def _populate(self, graph: Graph, finish_time: float, *args, **kwargs) -> bool:
        raise NotImplementedError


class ShortestPathLengthStore(Store):
    pairwise_distances: dict[int, dict[int, int]]

    def _populate(self, graph: Graph, finish_time: float, *args, **kwargs) -> bool:
        self.pairwise_distances = {}

        @timeout_loop(finish_time)
        def populate_single_source_distances(source: int):
            self.pairwise_distances[source] = shortest_path_length(graph, source)

        for node in graph.nodes:
            if not populate_single_source_distances(node):
                return False

        return True


class UndominatedNeighborhoodEdgeRankStore(Store):
    ranks: dict[tuple[int, int], float]

    def _populate(self, graph: Graph, finish_time: float, *args, **kwargs) -> bool:
        self.ranks = {}
        neighborhoods = {}

        @timeout_loop(finish_time)
        def populate_neighborhoods(vertex: int):
            neighborhoods[vertex] = {vertex}.union(graph.neighbors(vertex))

        @timeout_loop(finish_time)
        def populate_rank(vertex: int):
            neighborhood = neighborhoods[vertex]

            for neighbor in neighborhood:
                hop_neighborhood = set().union(*[
                    neighborhoods[other_neighbor]
                    for other_neighbor in neighborhood
                    if other_neighbor != neighbor
                ])

                dominated_neighborhood = neighborhoods[neighbor] & hop_neighborhood
                self.ranks[vertex, neighbor] = self.ranks[neighbor, vertex] = math.exp(-len(dominated_neighborhood))

        for node in graph.nodes:
            if not populate_neighborhoods(node):
                return False

        for node in graph.nodes:
            if not populate_rank(node):
                return False

        return True
