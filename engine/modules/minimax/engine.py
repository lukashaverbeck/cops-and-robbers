from typing import Callable, Iterator

from networkx import Graph

from .iterative_deepening import iterative_deepening_minimax
from .zobrist import ZobristTranspositionTable
from ..util import timeout_loop


def effective_game_graph(
    graph: Graph,
    cop_positions: list[int],
    robber_position: int,
    max_radius: float
) -> Iterator[tuple[Graph, set[int]]]:
    """ Generates a sequence of contour sub graphs around the robber with an increasing number of cops in it.

    We perform a BFS starting from the cop position. Every time we reach a new robber, we yield the sub graph covered
    by the BFS so far together with the set of cop indices that are not part of this subgraph yet.

    After a given radius, we stop expanding the contours. This feature can be used to stop expanding early as for a
    fixed search depth, there is no point in expanding the search graph further than the depth of the search.

    :param graph: The graph on which the cops play against the robber.
    :param cop_positions: The current cop positions in the graph.
    :param robber_position: The current robber position in the graph.
    :param max_radius: Radius around the robber after which to stop drawing contours.
    :yields: A sequence of sub graphs of the given graph and a set of cop indices that are not inside this sub graph.
    """
    n_cops = len(cop_positions)  # number of cops

    contour = {robber_position}  # start BFS from the robber node
    hidden_cops = set(range(n_cops)) - contour  # set of cop indices not yet reached by the BFS
    visited_nodes = set()
    radius = 0

    # performs a BFS through the whole graph
    while contour:
        if radius > max_radius:
            break
        visited_nodes.update(contour)  # the current contour was now visited

        # the next contour consist of the unvisited neighbors of the last contour
        next_contour = {
            neighbor for node in contour
            for neighbor in graph.neighbors(node)
            if neighbor not in visited_nodes
        }

        newly_found_cops = hidden_cops & next_contour  # set of cops reached in the last contour

        if newly_found_cops:
            hidden_cops.difference_update(newly_found_cops)
            yield graph.subgraph(visited_nodes | next_contour), hidden_cops

        contour = next_contour
        radius += 1


class MinimaxEngine:
    graph: Graph
    transposition: ZobristTranspositionTable
    failed: dict[tuple[int, ...], bool]

    def __init__(self, graph: Graph, n_cops: int):
        self.graph = graph
        self.transposition = ZobristTranspositionTable(graph, n_cops)

    def best_cop_move(
        self,
        cop_positions: list[int],
        robber_position: int,
        depth: int,
        fixated_step: Callable[[list[int], int], list[int]],
        finish_time: float
    ) -> tuple[list[int], bool]:
        """ Computes optimal cop moves using minimax search.

        We play minimax on increasingly broad contours around the robber and fixate cops outside this radius.
        We return a solution as soon as we find a winning one.
        We share the same transposition table across different calls of this function in order to make use of previously
        computes results.

        :param cop_positions: The current cop positions in the graph.
        :param robber_position: The current robber position in the graph.
        :param depth: Depth up which to search the minimax tree.
        :param fixated_step: Function computing fixated steps for a subset of cops outside the contour radius.
        :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
        :return: A Boolean indicating whether a cop winning step was found and the according cop move.
        """
        move = cop_positions
        is_winning = False

        @timeout_loop(finish_time, 2)
        def contour_minimax():
            nonlocal move, is_winning

            move, is_winning = iterative_deepening_minimax(
                graph,
                self.graph,
                cop_positions,
                robber_position,
                True,
                depth,
                finish_time,
                self.transposition,
                hidden_cops,
                fixated_step
            )

        for graph, hidden_cops in effective_game_graph(self.graph, cop_positions, robber_position, depth):
            if not contour_minimax():
                break

            if is_winning:
                return move, is_winning

        return move, is_winning
