from itertools import product
from typing import Iterable, Callable

from networkx import Graph, max_weight_matching

from .alpha_beta import minimax_alpha_beta
from .zobrist import Move, ZobristTranspositionTable
from ..util import timeout_loop

COP_WIN_VALUE = 1


def restore_possible_move_permutation(graph: Graph, cop_positions: list[int], move: list[int]) -> list[int]:
    """ Computes a permutation of a cop move that is actually possible under the given cop positions.

    It might be the case that a certain move can be reached from a configuration, but in a different oder of the cops.
    This might happen when using minimax with a transposition table that is invariant to some symmetries in the game
    configuration. This function restores a permutation of a cop move such that the resulting cop move is equivalent
    to the given move, but the move is actually possible in the cop order of the given current cop positions.

    We assume that such a permutation exists.

    We first check, if the given move is already possible for the given cop positions. If this is the case, we simply
    return the move as is. Otherwise, we construct a permutation of the move that is possible for the given cop
    positions. We do so by creating a bipartite graph that connects cops with the moves that they could actually make.
    We then compute a maximum matching. Iff a permutation with the desired properties exists, the maximum matching will
    be a perfect matching that induces a permutation of the cop moves which makes the move possible for the given cop
    positions. We then simply apply that permutation to the given cop move.

    :param graph: The graph on which the cops play against the robber.
    :param cop_positions: The current positions of the cops in the graph.
    :param move: Desired target positions for the cops (possibly only reachable in a different oder of the cops).
    :return: A permutation of the given move which is possible for the given cop positions.
    """
    # set of nodes that can be reached by each individual cop in one step from the current position
    possible_next_nodes = [
        {cop_position}.union(graph.neighbors(cop_position))
        for cop_position in cop_positions
    ]

    # check if the move is already possible from the current cop positions
    if all(target_position in possible_next_nodes[cop_id] for cop_id, target_position in enumerate(move)):
        return move

    # construct a graph that matches cops with the moves they could make
    # we represent cops as negative 1-indexed to disambiguate them from the move indices
    move_matching_graph = Graph({
        -(cop_id + 1): [move_id for move_id, move in enumerate(move) if move in possible_next_nodes[cop_id]]
        for cop_id, cop_position in enumerate(cop_positions)
    })

    # compute a maximum matching
    # this should be a perfect matching if the move is possible under some permutation of the cops
    move_permutation_matching = max_weight_matching(move_matching_graph, maxcardinality=True)
    move_permutation = [-1] * len(move)

    # map the matching to a permutation of the move
    for matching in move_permutation_matching:
        cop_id = -min(matching) - 1  # map cop indices from negative 1-indexed to 0-indexed
        move_id = max(matching)
        move_permutation[cop_id] = move[move_id]

    return move_permutation


def iterative_deepening_minimax(
    effective_graph: Graph,
    graph: Graph,
    cop_positions: list[int],
    robber_position: int,
    cop_turn: bool,
    max_depth: int,
    finish_time: float,
    transposition: ZobristTranspositionTable,
    hidden_cops: set[int],
    fixated_steps: Callable[[list[int], int], list[int]]
) -> tuple[Move, bool]:
    """ Performs iterative deepening minimax with alpha beta pruning.

    We perform minimax to increasing levels of depth. We stop early when the search yielded a winning strategy fot the
    cops.

    Some cop positions can be fixated. This means that their next move in a given position will be determined by a
    dedicated function as opposed to considering all possible moves for that cop in that position.

    :param effective_graph: The subgraph on which the cops play against the robber.
    :param graph: The graph underlying the effective graph.
    :param cop_positions: The current positions of the cops in the graph.
    :param hidden_cops: The set of cops that are not inside the effective graph.
    :param robber_position: The current position of the robber in the graph.
    :param cop_turn: Boolean indicating whether it is the cops turn.
    :param max_depth: Maximum depth to which to search in the game tree.
    :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
    :param transposition: Transposition table storing previously computed results on the same graph.
    :param fixated_steps: Function computing steps for hidden cops.
    :return: A tuple containing the best move to be made in the current configuration and a Boolean indicating whether
    the cops have a winning strategy taking that move.
    """
    cop_transition_cache = {}

    def robber_transitions(_, _robber_position: int) -> Iterable[int]:
        yield _robber_position
        yield from effective_graph.neighbors(_robber_position)

    fixated_cops = list(hidden_cops)
    fixated_cop_positions = [cop_positions[cop_id] for cop_id in fixated_cops]
    cop_fixated_steps = {
        cop_id: cop_fixated_step
        for cop_id, cop_fixated_step in zip(fixated_cops, fixated_steps(fixated_cop_positions, robber_position))
    }

    def cop_transitions(_cop_positions: list[int], _robber_position: int) -> Iterable[list[int]]:
        for position in filter(lambda p: p not in cop_transition_cache, _cop_positions):
            cop_transition_cache[position] = list(graph.neighbors(position))
            cop_transition_cache[position].append(position)

        yield from map(list, product(*[
            cop_transition_cache[cop_position]
            if cop_id not in hidden_cops
            else [cop_fixated_steps[cop_id]]
            for cop_id, cop_position in enumerate(_cop_positions)
        ]))

    move = cop_positions if cop_turn else robber_position
    value = 0

    @timeout_loop(finish_time, 2)
    def minimax_iteration():
        nonlocal move, value

        move, value = minimax_alpha_beta(
            transposition,
            cop_transitions,
            robber_transitions,
            cop_positions,
            robber_position,
            cop_turn,
            depth,
            finish_time
        )

    for depth in range(max_depth + 1):
        if not minimax_iteration() or value == 1:
            break

    # it might be the case that the move was encountered through some permutation of the cops
    # in this case it is necessary to find a permutation of that move through which every position in the move can
    # actually be reached by each cop
    if cop_turn:
        move = restore_possible_move_permutation(graph, cop_positions, move)

    return move, bool(value == 1)
