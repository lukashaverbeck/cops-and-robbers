from __future__ import annotations

from typing import Callable

from networkx import Graph

from .graph import GraphAbstraction

GraphAbstractionMatcher = Callable[[GraphAbstraction], bool]

ABSTRACTION_SIZE_THRESHOLD = 5  # number of nodes at which to stop the abstraction hierarchy


class AbstractionHierarchy:
    graph: Graph
    abstractions: list[GraphAbstraction]
    literal_vertex_mappings: list[dict[int, int]]

    @property
    def highest_abstraction(self) -> GraphAbstraction:
        return self.abstractions[-1]

    @property
    def lowest_abstraction(self) -> GraphAbstraction:
        return self.abstractions[0]

    def __init__(self, graph: Graph):
        self.graph = graph

        literal_vertex_mapping = {node: node for node in graph.nodes}
        self.abstractions = [abstraction := GraphAbstraction(graph, literal_vertex_mapping)]

        while abstraction.n_nodes > ABSTRACTION_SIZE_THRESHOLD:
            abstraction = GraphAbstraction(abstraction.graph, abstraction.literal_vertex_mapping)
            self.abstractions.append(abstraction)

    def populate_shortest_path_lengths(self, finish_time: float):
        for abstraction in reversed(self.abstractions):
            if not abstraction.populate_shortest_path_lengths(finish_time):
                break

    def populate_undominated_neighborhood_ranks(self, finish_time: float):
        for abstraction in reversed(self.abstractions):
            if not abstraction.populate_undominated_neighborhood_ranks(finish_time):
                break

    def __fitting_abstraction(self, match: GraphAbstractionMatcher, highest: bool) -> GraphAbstraction | None:
        abstractions = reversed(self.abstractions) if highest else self.abstractions
        return next((abstraction for abstraction in abstractions if match(abstraction)), None)

    def highest_fitting_abstraction(self, match: GraphAbstractionMatcher) -> GraphAbstraction | None:
        return self.__fitting_abstraction(match, True)

    def lowest_fitting_abstraction(self, match: GraphAbstractionMatcher) -> GraphAbstraction | None:
        return self.__fitting_abstraction(match, False)

    def lowest_shortest_path_length_abstraction(self) -> GraphAbstraction | None:
        def has_shortest_path_lengths(abstraction: GraphAbstraction) -> bool:
            return abstraction.shortest_path_lengths.is_populated

        return self.lowest_fitting_abstraction(has_shortest_path_lengths)

    def highest_undecided_abstraction(self, cop_positions: list[int], robber_position: int) -> GraphAbstraction | None:
        def is_undecided(abstraction: GraphAbstraction) -> bool:
            abstract_robber_position = abstraction.literal_vertex_mapping[robber_position]
            abstract_cop_positions = map(abstraction.literal_vertex_mapping.__getitem__, cop_positions)
            return abstract_robber_position not in abstract_cop_positions

        return self.highest_fitting_abstraction(is_undecided)

    def highest_abstraction_lower_than(self, abstraction: GraphAbstraction) -> GraphAbstraction | None:
        return self.highest_fitting_abstraction(lambda x: x.n_nodes > abstraction.n_nodes)

    def lowest_abstraction_higher_than(self, abstraction: GraphAbstraction) -> GraphAbstraction | None:
        return self.highest_fitting_abstraction(abstraction.__gt__)

    def decreasing_abstractions_from(self, abstraction: GraphAbstraction) -> list[GraphAbstraction]:
        return list(filter(abstraction.__le__, reversed(self.abstractions)))
