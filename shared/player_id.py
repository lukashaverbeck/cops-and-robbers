from __future__ import annotations

from enum import IntEnum, unique

from .status import Status


@unique
class PlayerID(IntEnum):
    """Enum for the players of the game.

    Represents a player.

    Robber is defined as 0 or False.
    Cops is defined as 1 or True.
    """
    COPS = True
    ROBBER = False

    def __str__(self) -> str:
        return {
            PlayerID.COPS: 'Cops',
            PlayerID.ROBBER: 'Robber',
        }[self]

    @property
    def regular_loss_status(self) -> Status:
        """The status representing a natural loss for the current player ID."""
        return Status.COPS_OUT_OF_STEPS if self \
            else Status.ROBBER_CAUGHT

    @property
    def invalid_step_status(self) -> Status:
        """The status representing an invalid step for the current player ID."""
        return Status.COPS_INVALID_STEP if self \
            else Status.ROBBER_INVALID_STEP

    @property
    def timeout_status(self) -> Status:
        """The status representing a timeout for the current player ID."""
        return Status.COPS_TIMEOUT if self \
            else Status.ROBBER_TIMEOUT

    @property
    def exception_status(self) -> Status:
        """The status representing an exception for the current player ID."""
        return Status.COPS_EXCEPTION if self \
            else Status.ROBBER_EXCEPTION
