from collections import Counter
from functools import reduce
from operator import xor

import numpy as np
from networkx import Graph

Move = int | list[int]
TranspositionItem = tuple[list[int], int, bool, int]


class ZobristTranspositionTable:
    table: dict[int, tuple[int, Move, float]]
    cop_keys: dict[int, np.ndarray]
    robber_keys: dict[int, np.ndarray]
    cop_turn_key: dict[bool, int]

    def __init__(self, graph: Graph, n_cops: int):
        self.table = {}

        def generate_random_keys(*shape: int) -> np.ndarray:
            int_info = np.iinfo(np.int64)
            return np.random.randint(int_info.min, int_info.max, shape, dtype=np.int64)

        n_nodes = graph.number_of_nodes()
        self.cop_keys = dict(zip(graph.nodes, generate_random_keys(n_nodes, n_cops)))
        self.robber_keys = dict(zip(graph.nodes, generate_random_keys(n_nodes)))
        self.cop_turn_key = dict(zip([True, False], generate_random_keys(2)))

    def key(self, cop_positions: list[int], robber_position: int, cop_turn: bool) -> int:
        """ Computes the hash keys for a given configuration of the game.

        The hash key is computed as the xor between the cop key, the robber key, and the turn key.
        As there are multiple cops, the cop key is computed as the xor between the keys for the cop positions taking
        into account the number of cops on that position.

        Note that this way of hashing a configuration automatically reduces all symmetries regarding the order in which
        the cops stand on certain nodes to the same hash value because xor is commutative.

        Hash collisions for inherently different configurations are possible but unlikely.

        Note that this way of hashing does not directly take care of the depth at which the configuration is encountered.

        :param cop_positions: The current cop positions.
        :param robber_position: The current robber position.
        :param cop_turn: Boolean indicating whether it is the cops' turn.
        :return: The hash value for the given game configuration.
        """
        # map cop positions to cop keys taking into consideration the number of cops on the same node
        cop_keys = map(
            lambda position: self.cop_keys[position][freq[position] - 1],
            freq := Counter(cop_positions)
        )

        # we retrieve the hash value as the xor of all cop keys, the robber key, and the turn key
        return reduce(xor, cop_keys) ^ self.robber_keys[robber_position] ^ self.cop_turn_key[cop_turn]

    def __getitem__(self, item: TranspositionItem) -> tuple[Move, float]:
        """ Retrieves a hashed entry for a given game configuration.

        Note that there might be stored entries that were hashed for a lower depth than the depth of the given game
        configuration. This function will return a stored entry even if the remaining depth of that entry is lower than
        the depth of the given game configuration.

        :param item: A tuple of the cop positions, the robber position, a Boolean indicating whether the cops are to
        move, and the remaining search depth.
        :return: A tuple of the stored move and the evaluation of that move.
        """
        cop_positions, robber_position, cop_turn, depth = item
        key = self.key(cop_positions, robber_position, cop_turn)
        hash_depth, move, evaluation = self.table[key]

        return move, evaluation

    def __contains__(self, item: TranspositionItem) -> bool:
        """ Checks whether there is an entry for a certain game configuration.

        In particular, for this to be the case, there must be a hash of the given game configuration that has at least
        the remaining depth of the given game state. To check this, we compare the given remaining depth against the
        entry for the given configuration.

        :param item: A tuple of the cop positions, the robber position, a Boolean indicating whether the cops are to
        move, and the remaining search depth.
        :return: Boolean indicating whether there is a stored entry for the given game configuration with a remaining
        depth of at least the given depth.
        """
        cop_positions, robber_position, cop_turn, depth = item
        key = self.key(cop_positions, robber_position, cop_turn)
        return key in self.table and self.table[key][0] >= depth

    def __setitem__(self, item: TranspositionItem, value: tuple[Move, float]) -> None:
        """ Stores an entry in the transposition table.

        Note that the entry will only be stored if there is no prior entry for the given configuration or the entry for
        the given configuration was created for a lower remaining depth in the search.

        :param item: A tuple of the cop positions, the robber position, a Boolean indicating whether the cops are to
        move, and the remaining search depth.
        :param value: A tuple of the move and its evaluation for the give game configuration.
        """
        cop_positions, robber_position, cop_turn, depth = item
        move, evaluation = value
        key = self.key(cop_positions, robber_position, cop_turn)
        entry = depth, move, evaluation

        if key not in self.table:
            self.table[key] = entry
        else:
            self.table[key] = max(self.table[key], entry, key=lambda v: v[0])
