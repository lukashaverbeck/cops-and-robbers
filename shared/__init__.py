"""A package for common modules shared among all strategies.

This package does not contain a strategy by itself, but rather the modules that
are shared by all other strategy packages. The pre-existing modules should not
be changed as they build the game as we expect it to work, but if more modules
are created that are used by multiple strategies, they can be added here.
"""

from .game import Game
from .player import Player
from .player_id import PlayerID
from .status import Status

__all__ = ('Game', 'Player', 'PlayerID', 'Status')
