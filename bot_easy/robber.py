from __future__ import annotations

from math import inf

from networkx import Graph, single_source_shortest_path_length

from .player import Player


class Robber(Player):
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
        super().__init__(graph, cops_count, timeout_init, timeout_step, max_rounds)
        self.graph = graph

    def get_init_position(self, cop_positions: list[int]) -> int:
        """Computes the initial robber position.

        :param cop_positions: The initial cop positions.
        :return: The initial robber position.
        """
        self.cop_positions = cop_positions

        global_cop_dists = dict.fromkeys(self.graph, inf)

        for cop_pos in cop_positions:
            single_cop_dists = single_source_shortest_path_length(self.graph, cop_pos)
            global_cop_dists = {k: min(v, single_cop_dists[k]) for k, v in global_cop_dists.items()}

        self.robber_position = sorted(global_cop_dists.keys(), key=global_cop_dists.get, reverse=True)[0]

        return self.robber_position

    def step(self, cop_positions: list[int]) -> int:
        """Computes the next robber position based on the cop positions.

        :param cop_positions: The current cop positions.
        :return: The next robber position.
        """
        self.cop_positions = cop_positions

        global_cop_dists = dict.fromkeys(set(self.graph[self.robber_position]) | {self.robber_position}, inf)

        for cop_pos in cop_positions:
            single_cop_dists = single_source_shortest_path_length(self.graph, cop_pos)
            global_cop_dists = {k: min(v, single_cop_dists[k]) for k, v in global_cop_dists.items()}

        self.robber_position = sorted(global_cop_dists.keys(), key=global_cop_dists.get, reverse=True)[0]

        return self.robber_position
