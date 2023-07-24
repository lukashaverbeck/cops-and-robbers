from __future__ import annotations

from networkx import Graph


class Player:
    def __init__(self,
                 graph: Graph,
                 cops_count: int | None = None,
                 timeout_init: float | None = None,
                 timeout_step: float | None = None,
                 max_rounds: int | None = None) -> None:
        """Initializes the player.

        This method writes the parameters to instance variables. It also
        initializes the variables cop_positions and robber_position that
        players can use to remember the current positions in the game.

        :param graph: The Graph the game should be played on.
        :param cops_count: The number of cops in the game. Defaults to None,
        which means that Cops can choose their own number.
        :param timeout_init: The number of seconds the initialization of Cops
        and Robber is allowed to take. Defaults to None, which means no time
        limit will be imposed.
        :param timeout_step: The number of seconds the 'step' &
        'get_init_position' calls of Cops and Robber is allowed to take.
        Defaults to None, which means no time limit will be imposed.
        """
        self.graph = graph
        self.cops_count = cops_count
        self.timeout_init = timeout_init
        self.timeout_step = timeout_step
        self.max_rounds = max_rounds

        self.cop_positions: list[int] | None = None
        self.robber_position: int | None = None
