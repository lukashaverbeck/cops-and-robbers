import time
from typing import Callable, Iterable

from .zobrist import Move, ZobristTranspositionTable


def is_terminal(cop_positions: list[int], robber_position: int) -> bool:
    return robber_position in cop_positions


def minimax_alpha_beta(
    transposition: ZobristTranspositionTable,
    cop_transitions: Callable[[list[int], int], Iterable[list[int]]],
    robber_transitions: Callable[[list[int], int], Iterable[int]],
    cop_positions: list[int],
    robber_position: int,
    cop_turn: bool,
    remaining_depth: int,
    finish_time: float,
    alpha: float = 0,
    beta: float = 1
) -> tuple[Move, float]:
    """ Performs minimax with alpha beta pruning from a given start configuration and up to a given depth.

    :param transposition: Transposition table to use for lookups.
    :param cop_transitions: Function computing possible next positions for the cops.
    :param robber_transitions: Function computing possible next positions for the robber.
    :param cop_positions: The current cop positions in the search tree.
    :param robber_position: The current robber position in the search tree.
    :param cop_turn: Boolean indicating whether the cops move now.
    :param remaining_depth: Remaining depth up to which to search the tree.
    :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
    :param alpha: Lower bound on the evaluation achievable from the start configuration.
    :param beta: Upper bound on the evaluation achievable from the start configuration.
    :return: The best move in the given configuration and a Boolean indicating if the move leads to a cop win for
    optimal play of both parties up to the given depth.
    """
    key = cop_positions, robber_position, cop_turn, remaining_depth

    if key not in transposition:  # only evaluate the state if it is not cached
        best_move = cop_positions if cop_turn else robber_position  # by default, stay in the current position
        evaluation = alpha if cop_turn else beta  # by default, choose the most pessimistic state value

        # case 1: the current state is a leaf node in the search tree
        # then, we do not move and just update the value of the state
        # the value is 1 if it is cop win and 0 otherwise
        if (is_terminal_state := is_terminal(cop_positions, robber_position)) or remaining_depth <= 0:
            evaluation = int(is_terminal_state)
        # case 2: the current state is not a leaf node, but we are running out of time
        # then, we simply return the current position and an evaluation inbetween cop win and robber win
        elif finish_time - time.time() <= 0.001 / (remaining_depth + 1):
            return best_move, 0.5
        # case 3: the current state is not a leaf node, and we have computation time left, and it is a cop turn
        # then, we dynamically compute the value and the best move for the cops based on successor states
        elif cop_turn:
            for successor_positions in cop_transitions(cop_positions, robber_position):
                _, successor_evaluation = minimax_alpha_beta(
                    transposition,
                    cop_transitions,
                    robber_transitions,
                    successor_positions,
                    robber_position,
                    False,
                    remaining_depth - 1,
                    finish_time,
                    alpha,
                    beta
                )

                # always choose the successor state with the highest value
                if successor_evaluation > evaluation:
                    evaluation = successor_evaluation
                    best_move = successor_positions

                alpha = max(alpha, evaluation)  # update lower bound

                # stop evaluating this subtree if the value of this state exceeds the upper bound
                # we can do this because the robber has a strategy that always results in a lower value in this case
                if evaluation >= beta:
                    break
        # case 4: the current state is not a leaf node, and we have computation time left, and it is a robber turn
        # then, we dynamically compute the value and the best move for the robber based on successor states
        else:
            for successor_position in robber_transitions(cop_positions, robber_position):
                _, successor_evaluation = minimax_alpha_beta(
                    transposition,
                    cop_transitions,
                    robber_transitions,
                    cop_positions,
                    successor_position,
                    True,
                    remaining_depth,
                    finish_time,
                    alpha,
                    beta
                )

                # always choose the successor state with the highest value
                if successor_evaluation < evaluation:
                    evaluation = successor_evaluation
                    best_move = successor_position

                beta = min(beta, evaluation)  # update higher bound

                # stop evaluating this subtree if the value of this state exceeds the lower bound
                # we can do this because the cops have a strategy that always results in a higher value in this case
                if evaluation <= alpha:
                    break

        transposition[key] = best_move, evaluation  # save the evaluation in the transposition table

    return transposition[key]
