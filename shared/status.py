from __future__ import annotations

from enum import IntEnum, unique


@unique
class Status(IntEnum):
    """Enum for game states.

    Represents all states the game can take.

    Status 0 represents a continuing game.
    Negative states represent a Robber win.
    Positive states represent a Cops win.
    """
    COPS_EXCEPTION = -4
    COPS_TIMEOUT = -3
    COPS_INVALID_STEP = -2
    COPS_OUT_OF_STEPS = -1
    GAME_CONTINUES = 0
    ROBBER_CAUGHT = 1
    ROBBER_INVALID_STEP = 2
    ROBBER_TIMEOUT = 3
    ROBBER_EXCEPTION = 4

    def __str__(self) -> str:
        return {
            Status.GAME_CONTINUES: 'The game continues.',
            Status.ROBBER_CAUGHT: 'The Robber was caught.',
            Status.ROBBER_INVALID_STEP: 'The Robber made an invalid step.',
            Status.ROBBER_TIMEOUT: 'The Robber timed out.',
            Status.ROBBER_EXCEPTION: 'The Robber raised an exception.',
            Status.COPS_OUT_OF_STEPS: 'The Cops could not catch the Robber in time.',
            Status.COPS_INVALID_STEP: 'The Cops made an invalid step.',
            Status.COPS_TIMEOUT: 'The Cops timed out.',
            Status.COPS_EXCEPTION: 'The Cops raised an exception.',
        }[self]
