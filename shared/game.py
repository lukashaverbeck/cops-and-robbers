from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from types import ModuleType
from typing import Type

from networkx import Graph

from .killable_thread import KillableThread
from .player import Player
from .player_id import PlayerID
from .resource_manager import dispose_unmanaged_resources
from .status import Status


class Game(ABC):
    """Abstract base class for various game variations of the Cops'n'Robbers game."""

    logger = getLogger('game')

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

        The constructor initializes both Cops and Robber.

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
        # Initialize basic game attributes.
        self.graph = graph

        self.__robber_class: Type[Player] = robber_engine.Robber
        self.__cops_class: Type[Player] = cops_engine.Cops

        self.cops_count = cops_count
        self.timeout_init = timeout_init
        self.timeout_step = timeout_step
        self.max_rounds = max_rounds

        self.cops: Player | None = None
        self.robber: Player | None = None

        self._robber_position: int | None = None
        self._cop_positions: list[int] | None = None

        self.round_number = 0
        self.next_player: PlayerID | None = None
        self._first_player: PlayerID | None = None
        self.__status = Status.GAME_CONTINUES

        # Initialize both players.
        self.__init_player(PlayerID.COPS)

        if self.status is not Status.GAME_CONTINUES:
            return

        self.__init_player(PlayerID.ROBBER)

    def __init_player(self, player_id: PlayerID) -> None:
        """Initializes a player.

        If an exception is raised during the initialization or the timeout for
        the init phase is exceeded the other player wins.

        :param player_id: The ID of the player to be initialized.
        """
        # Get the current player's class.
        player_class = self.__cops_class if player_id is PlayerID.COPS \
            else self.__robber_class

        # Call the constructor in a new thread.
        thread = KillableThread(target=player_class,
                                kwargs={'graph': self.graph.copy(),
                                        'cops_count': self.cops_count,
                                        'timeout_init': self.timeout_init,
                                        'timeout_step': self.timeout_step,
                                        'max_rounds': self.max_rounds})
        thread.start()

        try:
            # Wait for the result of the thread for the length of the
            # timeout plus extra time compensating for launching the thread.
            player = thread.join(self.__adjust_timeout(self.timeout_init))

        except TimeoutError:
            # Terminate the thread.
            thread.terminate()

            # End the game due to the timeout.
            self.status = player_id.timeout_status

            self.logger.warning("%s timed out & lost. Thread killed.",
                                player_id)
            return

        except RuntimeError as err:
            # Any potential exception caused by the call will be caught here.
            # In that case, end the game due to the exception.
            self.status = player_id.exception_status

            self.logger.warning("%s raised the following exception & lost:",
                                player_id)
            self.logger.exception(err)
            return

        finally:
            # Clean up any unmanaged resources left behind.
            dispose_unmanaged_resources()

        # If the thread finished, save the returned player.
        if player_id is PlayerID.COPS:
            self.cops = player
        elif player_id is PlayerID.ROBBER:
            self.robber = player

    def __step_player(self, player_id: PlayerID, is_init_pos: bool = False) -> None:
        """Computes the next position of a player and updates them.

        If an exception is raised during the calculation or the timeout for
        the the step phase is exceeded during the 'get_init_position(s)' call,
        the other player wins.

        During the 'step' calls, a timeout is permitted and will result in not
        having that player's position updated.

        :param player_id: The ID of the player whose next positions should be
        calculated.
        :param is_init_pos: Indicates if 'get_init_position(s)' should be
        called instead of 'step', defaults to False.
        """
        # TODO: Replace with match-case in Python 3.10+.
        # Get the current target function.
        if is_init_pos:
            if player_id is PlayerID.COPS:
                target = self.cops.get_init_positions
                args = ()
            elif player_id is PlayerID.ROBBER:
                target = self.robber.get_init_position
                args = (self.cop_positions.copy(),)
        else:
            if player_id is PlayerID.COPS:
                target = self.cops.step
                args = (self.robber_position,)
            elif player_id is PlayerID.ROBBER:
                target = self.robber.step
                args = (self.cop_positions.copy(),)

        # Call the function in a new thread.
        thread = KillableThread(target=target, args=args)
        thread.start()

        try:
            # Wait for the result of the thread for the length of the
            # timeout plus extra time compensating for launching the thread.
            new_position = thread.join(self.__adjust_timeout(self.timeout_step))

        except TimeoutError:
            # Terminate the thread.
            thread.terminate()

            # Only end the game due to the timeout during the first round,
            # otherwise only skip updating positions and player.
            if is_init_pos:
                self.status = player_id.timeout_status
                self.logger.warning("%s timed out & lost. Thread killed.",
                                    player_id)
            else:
                self.logger.warning("%s timed out & skipped this turn. "
                                    "Thread killed.", player_id)
            return

        except RuntimeError as err:
            # Any potential exception caused by the call will be caught here.
            # In that case, end the game due to the exception.
            self.status = player_id.exception_status

            self.logger.warning("%s raised the following exception & lost:",
                                player_id)
            self.logger.exception(err)
            return

        finally:
            # Clean up any unmanaged resources left behind.
            dispose_unmanaged_resources()

        # If the thread finished, save the positions.
        if player_id is PlayerID.COPS:
            self.cop_positions = new_position
        elif player_id is PlayerID.ROBBER:
            self.robber_position = new_position

    def run(self) -> None:
        """Computes the entire game.

        Computes steps until one player has won, indicated by the game status.
        """
        if self.max_rounds is None:
            self.logger.warning("The run method was called without setting a "
                                "maximum round number. The game might never "
                                "finish, if the robber is never caught.")

        while self.status is Status.GAME_CONTINUES:
            self.step()

    def next_round(self) -> None:
        """Computes a single round in the game.

        Each round consists of two steps, one for the robber and one for the
        cops. Thus, this method simply computes two steps.
        """
        self.step()
        self.step()

    def step(self) -> None:
        """Computes a single step in the game.

        This method handles the coordination of the game, i.e. modifying the
        round number and the next player, calling the appropriate step methods
        for the current player, and checking for game ending conditions
        independent of the validity of the position (which should be checked in
        the derived player position setters, as that varies depending on the
        game rules).
        """
        # Warn if 'step' is called in an already finished game.
        if self.status is not Status.GAME_CONTINUES:
            self.logger.warning("A game step is being made despite "
                                "the game having already concluded.")
            if self.next_player is None:
                self.logger.error("The game cannot continue, since the player "
                                  "initialization failed.")
                return

        # If it is the first players turn, the round has begun, thus increase
        # the round number.
        if self.next_player is self._first_player:
            self.round_number += 1

        # If the current players position is not initialized yet, set the
        # 'is_init_pos' attribute, so 'get_init_position(s)' is called instead
        # of 'step'.
        is_init_pos = self.next_player is PlayerID.COPS and self.cop_positions == [] \
            or self.next_player is PlayerID.ROBBER and self.robber_position is None

        # Make the actual step.
        self.__step_player(self.next_player, is_init_pos)

        # If it is not the first players turn, the round has ended, thus check
        # if the game ends naturally.
        if self.next_player is not self._first_player:
            if self.robber_position in self.cop_positions:
                self.status = Status.ROBBER_CAUGHT
                self.logger.info("Robber has been caught & lost.")
            elif self.round_number == self.max_rounds:
                self.status = Status.COPS_OUT_OF_STEPS
                self.logger.info("Cops ran out of steps & lost.")

        # Switch to the next player.
        self.next_player = PlayerID(not self.next_player)

    @property
    def cop_positions(self) -> list[int]:
        """The current cop positions.

        If the cop positions have not been set yet, the empty list is returned.
        """
        return self._cop_positions if self._cop_positions is not None else []

    @cop_positions.setter
    @abstractmethod
    def cop_positions(self, positions: list[int]) -> None:
        """The new cop positions.

        This property's setter is marked as abstract and to be overridden in
        inheriting classes based on the rules of the implemented game.

        :raises NotImplementedError: This property's setter raises a
        'NotImplementedError' unless it is overridden.
        """
        raise NotImplementedError

    @property
    def robber_position(self) -> int:
        """The current robber position."""
        return self._robber_position

    @robber_position.setter
    @abstractmethod
    def robber_position(self, position: int) -> None:
        """The new robber position.

        This property's setter is marked as abstract and to be overridden in
        inheriting classes based on the rules of the implemented game.

        :raises NotImplementedError: This property's setter raises a
        'NotImplementedError' unless it is overridden.
        """
        raise NotImplementedError

    @property
    def status(self) -> Status:
        """The current status of the game.

        Possible values are listed in the 'GameStatus' enum.
        """
        return self.__status

    @status.setter
    def status(self, status: Status) -> None:
        """The current status of the game.

        Possible values are listed in the 'GameStatus' enum. The status will
        only be set if the current status is 'GAME_CONTINUES'.

        :param status: The new status of the game.
        :type status: GameStatus
        """
        if self.__status is Status.GAME_CONTINUES:
            self.__status = status

    @property
    def result(self) -> int:
        """The current result of the game.

        This property represents the current result of the game.
        0 represents that the game is currently running,
        1 represents that Cops win, and
        -1 represents that the Robber wins.

        This property is deprecated and will be removed in future revisions.
        Use the 'status' property instead.
        """
        return 0 if self.status == 0 \
            else 1 if self.status >= 1 \
            else -1  # self.status <= -1

    @staticmethod
    def __adjust_timeout(timeout: float | None) -> float | None:
        """Adjusts a given timeout to take processing delays into
        consideration.

        The current adjustment is that the timeout is increased by 5% and a
        flat amount of 10 milliseconds.

        :param timeout: The timeout to be adjusted.
        :return: The adjusted timeout, or 'None' if the input timeout was
        'None'.
        """
        if timeout is None:
            return None

        return timeout * 1.05 + .01
