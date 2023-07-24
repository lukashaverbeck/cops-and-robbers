from __future__ import annotations

from networkx import (Graph, closeness_centrality, has_path, shortest_path,
                      shortest_path_length)

from .player import Player


class Cops(Player):
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

        self.centrality = closeness_centrality(graph)

    def get_init_positions(self) -> list[int]:
        """Computes the initial cop positions.

        :return: The initial cop positions.
        """
        if not self.cops_count:
            self.cops_count = 3

        nodes_by_centrality = sorted(self.graph.nodes(),
                                     key=self.centrality.get,
                                     reverse=True)

        self.cop_positions = nodes_by_centrality[:self.cops_count]

        return self.cop_positions

    def step(self, robber_position: int) -> list[int]:
        """Computes the next cop positions based on the robber position.

        :param robber_position: The current robber position.
        :return: The next cop positions.
        """
        self.robber_position = robber_position

        avail_cops = set(filter(lambda node: has_path(self.graph,
                                                      node[1],
                                                      robber_position),
                                enumerate(self.cop_positions)))
        reserve_cops = set()
        working_graph = self.graph.copy()

        while avail_cops:
            idx, pos = sorted(avail_cops, key=lambda n:
                              shortest_path_length(working_graph, n[1], robber_position))[0]
            path: list[int] = shortest_path(working_graph, pos, robber_position)

            if len(path) == 2:
                self.cop_positions[idx] = path[1]
                break
            if len(path) > 2:
                new_pos = path[1]
                self.cop_positions[idx] = new_pos
                working_graph.remove_node(new_pos)

            avail_cops.remove((idx, pos))

            cut_off_cops = {cop for cop in avail_cops
                            if not has_path(working_graph, cop[1], robber_position)}
            avail_cops -= cut_off_cops
            reserve_cops |= cut_off_cops

        for idx, pos in reserve_cops:
            path: list[int] = shortest_path(self.graph, pos, robber_position)
            if len(path) >= 2:
                self.cop_positions[idx] = path[1]

        return self.cop_positions
