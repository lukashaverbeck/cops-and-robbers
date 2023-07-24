from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from heapq import nlargest

from networkx import Graph

from .modules.islands import Component
from .modules.islands.choosing import component_cop_distribution
from .modules.strategy.abstract_minimax_disjoint_refinement import AbstractMinimaxDisjointRefinementCopsStrategy
from .modules.util import remaining_time
from .modules.util.timeout import distribute_remaining_time
from .player import Player


class Cops(Player):
    component_mapping: dict[int, Component]
    components: list[Component]
    cop_distribution: dict[Component, float]
    n_cops: dict[Component, int]
    strategies: dict[Component, AbstractMinimaxDisjointRefinementCopsStrategy | None]

    def __init__(self,
                 graph: Graph,
                 cops_count: int | None = None,
                 timeout_init: float | None = None,
                 timeout_step: float | None = None,
                 max_rounds: int | None = None) -> None:
        """Initializes the cops.

        :param graph: The Graph the game should be played on.
        :param cops_count: The number of cops in the game. Defaults to None,
        which means that Cops can choose their own number.
        :param timeout_init: The number of seconds the initialization of Cops
        and Robber is allowed to take. Defaults to None, which means no time
        limit will be imposed.
        :param timeout_step: The number of seconds the 'step' &
        'get_init_position' calls of Cops and Robber is allowed to take.
        Defaults to None, which means no time limit will be imposed.
        :param max_rounds: The maximum number of rounds that may be played
        before the cops run out of steps and lose. Defaults to None, which
        means that the game can continue forever.
        """
        super().__init__(graph, cops_count, timeout_init, timeout_step, max_rounds)
        finish_time = time.time() + (timeout_init if timeout_init is not None else 600)

        self.component_mapping = Component.mapping(graph)
        self.components = list(set(self.component_mapping.values()))
        self.cop_distribution = component_cop_distribution(self.components)

        n_components = len(self.components)

        if cops_count < n_components:
            self.n_cops = {}
            n_remaining_cops = cops_count

            for component in sorted(self.components, key=lambda c: c.graph.number_of_nodes()):
                self.n_cops[component] = int(n_remaining_cops > 0)
                n_remaining_cops -= 1
        else:
            self.n_cops = {component: 1 for component in self.components}
            n_remaining_cops = cops_count - n_components

            for component, proportion in self.cop_distribution.items():
                self.n_cops[component] += math.floor(n_remaining_cops * proportion)

            n_remaining_cops = cops_count - sum(self.n_cops.values())
            fill_up_components = nlargest(n_remaining_cops, self.components, key=self.cop_distribution.get)

            for component in fill_up_components:
                self.n_cops[component] += 1

        component_finish_times = distribute_remaining_time(
            remaining_time(finish_time, 0.85),
            (component.graph.number_of_nodes() / graph.number_of_nodes() for component in self.components)
        )

        # we define strategies for all component for which we reserve at least one cop
        # for other components there is no point in defining a strategy as there is no cop that could follow it
        self.strategies = defaultdict(lambda: None, {
            component: AbstractMinimaxDisjointRefinementCopsStrategy(
                component.graph,
                self.n_cops[component],
                component_finish_time
            )
            for component, component_finish_time in zip(self.components, component_finish_times)
            if self.n_cops[component] > 0
        })

        self.cop_positions = {}

    def chained_cop_positions(self) -> list[int]:
        return [cop_position for component in self.components for cop_position in self.cop_positions[component]]

    def get_init_positions(self) -> list[int]:
        """ Computes the initial cop positions.

        We choose initial positions for each island in the graph.

        If there are no cops reserved for an island, we do not place any cops.
        If there are more cops than nodes reserved for an island, we place the cops to cover all nodes.
        Otherwise, (which should be the most common case), we choose the initial cop positions for that island
        according to the strategy for that component.

        :return: The initial cop positions.
        """
        finish_time = time.time() + (self.timeout_step if self.timeout_step is not None else 60)

        for component in self.components:
            n_cops = self.n_cops[component]

            # case 1: we have more cops reserved for an island than there are nodes in that component
            # we let the cops cover all nodes
            if n_cops >= component.graph.number_of_nodes():
                nodes = list(component.graph.nodes)
                fill_up_nodes = [random.choice(nodes)] * (n_cops - len(nodes))
                self.cop_positions[component] = nodes + fill_up_nodes
            # case 2: we have at least one cop reserved for an island but cannot cover all nodes in that component
            # we choose the initial cop positions according to the strategy for that component
            elif self.n_cops[component] > 0:
                self.cop_positions[component] = self.strategies[component].init(
                    remaining_time(finish_time, 0.75 * self.cop_distribution[component])
                )
            # case 3: we have no cops reserved for an island
            # we choose no initial positions as there are no cops to place
            else:
                self.cop_positions[component] = []

        return self.chained_cop_positions()

    def step(self, robber_position: int) -> list[int]:
        """ Computes the next cop positions based on the robber position.

        If there is no cop in the robber component, we do not move at all as we cannot possibly reach the robber
        anyway. Otherwise, we take a step only in the robber component because only these cops can potentially reach the
        robber. If the robber is already caught, we do not move because we do not have to.

        :param robber_position: The current robber position.
        :return: The next cop positions.
        """
        finish_time = time.time() + (self.timeout_step if self.timeout_step is not None else 60)
        component = self.component_mapping[robber_position]  # island on which the robber is located
        cop_positions = self.cop_positions[component]  # cop positions in the robber island

        if robber_position not in cop_positions:  # only make a move if the robber is not yet caught
            strategy = self.strategies[component]  # strategy for the robber island

            # take a step in the robber island
            # the strategy for the robber island is not defined if there are no cops on that island
            if strategy is not None:
                self.cop_positions[component] = self.strategies[component].step(
                    cop_positions,
                    robber_position,
                    remaining_time(finish_time, 0.75)
                )

        return self.chained_cop_positions()
