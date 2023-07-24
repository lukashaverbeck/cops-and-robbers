from __future__ import annotations

import time
from collections import Counter

from networkx import Graph

from .modules.islands import Component
from .modules.islands.choosing import component_cop_distribution
from .modules.strategy.contour_relaxation import ContourRelaxationRobberStrategy
from .modules.util import remaining_time
from .modules.util.timeout import distribute_remaining_time
from .player import Player


class Robber(Player):
    robber_position: int
    component_mapping: dict[int, Component]
    components: list[Component]
    cop_distribution: dict[Component, float]
    strategies: dict[Component, ContourRelaxationRobberStrategy]

    def __init__(self,
                 graph: Graph,
                 cops_count: int | None = None,
                 timeout_init: float | None = None,
                 timeout_step: float | None = None,
                 max_rounds: int | None = None) -> None:
        """Initializes the robber.

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
        finish_time = time.time() + (timeout_init if timeout_init is not None else 600)
        super().__init__(graph, cops_count, timeout_init, timeout_step, max_rounds)

        self.robber_position = -1

        self.component_mapping = Component.mapping(graph)
        self.components = list(set(self.component_mapping.values()))
        self.cop_distribution = component_cop_distribution(self.components)

        component_finish_times = distribute_remaining_time(
            remaining_time(finish_time, 0.85),
            (component.graph.number_of_nodes() / graph.number_of_nodes() for component in self.components)
        )

        self.strategies = {
            component: ContourRelaxationRobberStrategy(
                component.graph,
                component_finish_time
            )
            for component, component_finish_time in zip(self.components, component_finish_times)
        }

    def get_init_position(self, cop_positions: list[int]) -> int:
        """Computes the initial robber position.

        :param cop_positions: The initial cop positions.
        :return: The initial robber position.
        """
        finish_time = time.time() + (self.timeout_step if self.timeout_step is not None else 60)
        cop_components = [self.component_mapping[cop_position] for cop_position in cop_positions]
        n_cops = Counter(cop_components)

        if any(n_cops[component] == 0 for component in self.components):
            component = next(component for component in self.components if n_cops[component] == 0)
            self.robber_position = list(component.graph.nodes)[0]
        else:
            component = min(self.components, key=lambda c: n_cops[c] / (self.cop_distribution[c] + 1e-9))

            cop_positions = [
                cop_position for cop_position in cop_positions
                if self.component_mapping[cop_position] is component
            ]

            if len(cop_positions) == 0:
                self.robber_position = list(component.graph.nodes)[0]
            else:
                self.robber_position = self.strategies[component].init(
                    cop_positions,
                    remaining_time(finish_time, 0.85)
                )

        return self.robber_position

    def step(self, cop_positions: list[int]) -> int:
        """Computes the next robber position based on the cop positions.

        :param cop_positions: The current cop positions.
        :return: The next robber position.
        """
        finish_time = time.time() + (self.timeout_step if self.timeout_step is not None else 60)
        component = self.component_mapping[self.robber_position]

        cop_positions = [
            cop_position for cop_position in cop_positions
            if self.component_mapping[cop_position] is component
        ]

        if len(cop_positions) > 0:
            self.robber_position = self.strategies[component].step(
                cop_positions,
                self.robber_position,
                remaining_time(finish_time, 0.85)
            )

        return self.robber_position
