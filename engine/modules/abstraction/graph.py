from __future__ import annotations

from collections import defaultdict
from itertools import chain
from typing import Iterable

from networkx import Graph

from .pooling import abstract_vertex_pooling
from .store import ShortestPathLengthStore, UndominatedNeighborhoodEdgeRankStore


class GraphAbstraction:
    graph: Graph
    vertex_mapping: dict[int, int]
    inverse_vertex_mapping: dict[int, list[int]]
    literal_vertex_mapping: dict[int, int]
    inverse_literal_vertex_mapping: dict[int, list[int]]
    n_nodes: int
    n_edges: int

    shortest_path_lengths: ShortestPathLengthStore
    undominated_neighborhood_ranks: UndominatedNeighborhoodEdgeRankStore

    def __init__(self, graph: Graph, prior_literal_vertex_mapping: dict[int, int]):
        self.vertex_mapping = abstract_vertex_pooling(graph)
        self.inverse_vertex_mapping = defaultdict(list)

        for node, abstract_node in self.vertex_mapping.items():
            self.inverse_vertex_mapping[abstract_node].append(node)

        self.literal_vertex_mapping = {
            node: self.vertex_mapping[prior_literal_vertex_mapping[node]]
            for node in prior_literal_vertex_mapping
        }

        self.inverse_literal_vertex_mapping = defaultdict(list)
        for node, abstract_node in self.literal_vertex_mapping.items():
            self.inverse_literal_vertex_mapping[abstract_node].append(node)

        self.graph = Graph()
        self.graph.add_nodes_from(self.vertex_mapping.values())
        self.graph.add_edges_from(
            (abstract_u, abstract_v)
            for u, v in graph.edges
            if (abstract_u := self.vertex_mapping[u]) != (abstract_v := self.vertex_mapping[v])
        )

        self.n_nodes = self.graph.number_of_nodes()
        self.n_edges = self.graph.number_of_edges()

        self.shortest_path_lengths = ShortestPathLengthStore()
        self.undominated_neighborhood_ranks = UndominatedNeighborhoodEdgeRankStore()

    def populate_shortest_path_lengths(self, finish_time: float) -> bool:
        return self.shortest_path_lengths.populate(self.graph, finish_time)

    def populate_undominated_neighborhood_ranks(self, finish_time: float) -> bool:
        return self.undominated_neighborhood_ranks.populate(self.graph, finish_time)

    def invert_node(self, node: int) -> list[int]:
        return self.inverse_literal_vertex_mapping[node]

    def invert_nodes(self, nodes: Iterable[int]) -> list[int]:
        inverted_nodes = chain.from_iterable(map(self.inverse_vertex_mapping.__getitem__, nodes))
        return list(inverted_nodes)

    def abstract_node(self, literal_node: int) -> int:
        return self.literal_vertex_mapping[literal_node]

    def abstract_nodes(self, literal_nodes: Iterable[int]) -> list[int]:
        return [self.abstract_node(literal_node) for literal_node in literal_nodes]

    def __hash__(self):
        return hash(("GraphAbstraction", self.n_nodes, self.n_edges))

    def __lt__(self, other: GraphAbstraction) -> bool:
        return self.n_nodes < other.n_nodes

    def __le__(self, other: GraphAbstraction) -> bool:
        return self.n_nodes <= other.n_nodes

    def __gt__(self, other: GraphAbstraction) -> bool:
        return self.n_nodes > other.n_nodes

    def __ge__(self, other: GraphAbstraction) -> bool:
        return self.n_nodes >= other.n_nodes
