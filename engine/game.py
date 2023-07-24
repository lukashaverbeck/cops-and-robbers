from __future__ import annotations

from types import ModuleType

from networkx import Graph

from ..shared import Game as GenericGame
from ..shared import PlayerID, Status


class Game(GenericGame):
    """Game class for the standard variant of the Cops'n'Robbers game."""

    def __init__(self,
                 graph: Graph,
                 robber_engine: ModuleType,
                 cops_engine: ModuleType,
                 cops_count: int | None = None,
                 timeout_init: float | None = None,
                 timeout_step: float | None = None,
                 max_rounds: int | None = None) -> None:
        """Constructor for a new game.

        The Cops class must be made available via cops_engine.Cops, and the
        Robber class must be made available via robber_engine.Robber.

        The constructor initializes both Cops and Robber and additionally
        makes the step for initializing cop positions.

        :param graph: The Graph the game should be played on.
        :param robber_engine: The engine used for the robber.
        :param cops_engine: The engine used for the cops.
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
        super().__init__(graph,
                         robber_engine,
                         cops_engine,
                         cops_count,
                         timeout_init,
                         timeout_step,
                         max_rounds)

        if self.status is not Status.GAME_CONTINUES:
            return

        self.__step_player(PlayerID.COPS, is_init_pos=True)

        if self.status is not Status.GAME_CONTINUES:
            return

        self.next_player = self._first_player = PlayerID.ROBBER

    @GenericGame.cop_positions.setter
    def cop_positions(self, positions: list[int]) -> None:
        """The new cop positions.

        Updates the current cop positions if the given ones are valid.

        If the given positions are an invalid type, have not the right amount
        of cops, are outside the graph or contain an illegal move, Cops loses
        and the status is set to 'COPS_INVALID_STEP'.

        In any of those cases, except for an illegal type, the result is stored
        before the game ends.
        """
        # Check if type of new positions is 'list[int]'.
        if not isinstance(positions, list) \
                or not all(isinstance(pos, int) for pos in positions):
            self.status = Status.COPS_INVALID_STEP
            self.logger.warning("Cops returned an invalid type & lost. "
                                "Returned type: %s.", type(positions)
                                if not isinstance(positions, list)
                                else list(map(type, positions)))
            return

        # Set cops count if it was free choice.
        if self.cops_count is None:
            self.cops_count = len(positions)
            self.logger.info("Cops count locked to: %d.", self.cops_count)

        # Check if amount of cops matches.
        if len(positions) != self.cops_count:
            self.status = Status.COPS_INVALID_STEP
            self.logger.warning("Cops returned an invalid amount of cops & lost. "
                                "Required amount: %d. Returned amount: %d.",
                                self.cops_count, len(positions))

        # Check if all positions are inside the graph.
        elif not all(pos in self.graph for pos in positions):
            self.status = Status.COPS_INVALID_STEP
            self.logger.warning("Cops returned a position outside the graph & lost. "
                                "Illegal positions: %s.",
                                [pos for pos in positions if pos not in self.graph])

        # Check if every position is a legal move.
        elif self._cop_positions is not None \
                and not all(old_pos == new_pos
                            or self.graph.has_edge(old_pos, new_pos)
                            for old_pos, new_pos in zip(self._cop_positions, positions)):
            self.status = Status.COPS_INVALID_STEP
            self.logger.warning("Cops made an illegal move & lost. Illegal moves: %s.",
                                [f'{old_pos} -> {new_pos}' for old_pos, new_pos
                                 in zip(self._cop_positions, positions)
                                 if old_pos != new_pos
                                 and not self.graph.has_edge(old_pos, new_pos)])

        self._cop_positions = positions.copy()
        self.logger.info("Cop positions set to: %s.", positions)

    @GenericGame.robber_position.setter
    def robber_position(self, position: int) -> None:
        """The new robber position.

        Updates the current robber position if the given one is valid.

        If the given position is an invalid type, is outside the graph or is an
        illegal move, Robber loses and the status is set to
        'ROBBER_INVALID_STEP'.

        In any of those cases, except for an illegal type, the result is stored
        before the game ends.
        """
        # Check if type of the new positions is 'int'.
        if not isinstance(position, int):
            self.status = Status.ROBBER_INVALID_STEP
            self.logger.warning("Robber returned an invalid type & lost. "
                                "Returned type: %s.", type(position))
            return

        # Check if the position is inside the graph.
        if position not in self.graph:
            self.status = Status.ROBBER_INVALID_STEP
            self.logger.warning("Robber returned a position outside the graph & lost. "
                                "Illegal position: %s.", position)

        # Check if the position is a legal move.
        elif self._robber_position is not None \
                and self._robber_position != position \
                and not self.graph.has_edge(self._robber_position, position):
            self.status = Status.ROBBER_INVALID_STEP
            self.logger.warning("Robber made an illegal move & lost. "
                                "Illegal move: %s -> %s.",
                                self._robber_position, position)

        self._robber_position = position
        self.logger.info("Robber position set to: %s.", position)
