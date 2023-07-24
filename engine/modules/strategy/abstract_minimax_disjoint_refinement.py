import random
import time
from collections import defaultdict
from typing import Iterable

import numpy as np
from networkx import Graph, pagerank, set_edge_attributes, PowerIterationFailedConvergence

from .base import BaseCopsStrategy
from ..abstraction import AbstractionHierarchy, GraphAbstraction, ShortestPathLengthStore, UndominatedNeighborhoodEdgeRankStore
from ..minimax import MinimaxEngine
from ..util import gon, remaining_time, multi_target_shortest_path, first_step_on_path, disjoint_search_steps, wang_cheng_weighted_k_center, timeout_loop

MINIMAX_DEPTH = 6


class AbstractMinimaxDisjointRefinementCopsStrategy(BaseCopsStrategy):
    graph: Graph
    n_cops: int
    minimax_timeout_probability: dict[tuple, float]
    minimax_probability: dict[tuple, float]

    hierarchy: AbstractionHierarchy
    literal_minimax_engine: MinimaxEngine
    minimax_engine: dict[GraphAbstraction, MinimaxEngine]

    init_positions: list[int]
    shortest_path_lengths: ShortestPathLengthStore
    undominated_neighborhood_ranks: UndominatedNeighborhoodEdgeRankStore

    def __init__(self, graph: Graph, n_cops: int, finish_time: float):
        self.graph = graph
        self.n_cops = n_cops
        self.minimax_timeout_probability = defaultdict(lambda: 0)
        self.minimax_probability = defaultdict(lambda: 1)

        # set up a hierarchy of abstractions and populate shortest path lengths and edge ranks for each abstraction
        self.hierarchy = AbstractionHierarchy(graph)
        self.hierarchy.populate_shortest_path_lengths(remaining_time(finish_time, 0.75))
        self.hierarchy.populate_undominated_neighborhood_ranks(remaining_time(finish_time, 0.75))

        # set up minimax engines for the literal graph and each level of abstraction
        self.literal_minimax_engine = MinimaxEngine(graph, n_cops)
        self.minimax_engine = {
            abstraction: MinimaxEngine(abstraction.graph, n_cops)
            for abstraction in self.hierarchy.abstractions
        }

        # set up stores for shortest path lengths and edge ranks for the literal graph
        self.shortest_path_lengths = ShortestPathLengthStore()
        self.undominated_neighborhood_ranks = UndominatedNeighborhoodEdgeRankStore()

        # compute starting positions and populate shortest path lengths and edge ranks for the literal graph
        self.init_positions = self.compute_init_positions()
        self.shortest_path_lengths.populate(graph, remaining_time(finish_time, 0.75))
        self.undominated_neighborhood_ranks.populate(graph, remaining_time(finish_time, 0.75))

        # if we were able to populate both stores, we update our starting positions because be now have more precise
        # information to use for that
        if self.shortest_path_lengths.is_populated and self.undominated_neighborhood_ranks.is_populated:
            self.init_positions = self.compute_init_positions()

        self.warmup(remaining_time(finish_time, 0.25))

    def compute_init_positions(self) -> list[int]:
        """ Chooses the starting positions for the cops.

        We choose the level of abstraction - or even the actual graph - that has both shortest path lengths and edge
        ranks available. We then compute ranks for each vertex using the Page Rank algorithm. This is to reflect the
        stationary distribution a randomly walking robber would converge to if they followed probabilistic transitions
        proportional to the edge weights. We want cops close to areas in the graph where the robber would likely move
        towards. Therefore, we compute a 2-approximation to the weighted vertex k center problem where k is the number
        of cops. If we were only able to compute this approximation for some level of abstraction, we refine the
        abstract centers by choosing the highest degree node in the actual graph that maps to the center in the
        corresponding abstraction.

        In case that we fail to compute the page rank algorithm, we fall back to weighing the nodes by their degrees.

        If there is no abstraction for which we have pairwise distances and edge ranks available, we fall back to
        computing a 2-approximation to the unweighted vertex k center problem using the Gon algorithm.

        :return: The initial cop positions.
        """

        def compute_centers(
            graph: Graph,
            edge_weights: dict[tuple[int, int], float],
            distances: dict[int, dict[int, int]]
        ) -> list[int]:
            set_edge_attributes(graph, edge_weights, "rank-edge-weight")

            try:
                vertex_ranks = pagerank(graph, weight="rank-edge-weight")
            except PowerIterationFailedConvergence:
                vertex_ranks = dict(graph.degree)

            return wang_cheng_weighted_k_center(
                graph,
                distances,
                vertex_ranks,
                self.n_cops
            )

        if self.shortest_path_lengths.is_populated and self.undominated_neighborhood_ranks.is_populated:
            return compute_centers(
                self.graph,
                self.undominated_neighborhood_ranks.ranks,
                self.shortest_path_lengths.pairwise_distances
            )

        def suited_abstraction(abstraction: GraphAbstraction) -> bool:
            return (abstraction.shortest_path_lengths.is_populated
                    and abstraction.undominated_neighborhood_ranks.is_populated)

        lowest_suited_abstraction = self.hierarchy.lowest_fitting_abstraction(suited_abstraction)

        if lowest_suited_abstraction is None:
            return gon(self.graph, self.n_cops)

        abstract_starting_positions = compute_centers(
            lowest_suited_abstraction.graph,
            lowest_suited_abstraction.undominated_neighborhood_ranks.ranks,
            lowest_suited_abstraction.shortest_path_lengths.pairwise_distances
        )

        return [
            max(lowest_suited_abstraction.invert_node(position), key=self.graph.degree.__getitem__)
            for position in abstract_starting_positions
        ]

    def init(self, finish_time: float) -> list[int]:
        return self.init_positions

    def step(self, cop_positions: list[int], robber_position: int, finish_time: float) -> list[int]:
        """ Chooses the next cop positions.

        If the game is undecided at some level of abstraction, that is if there is some level of abstraction at which
        there is no cop on the abstract vertex the robber stands on, we play minimax on abstractions of the actual graph
        and refine that solution.

        If there is no level of abstraction at which the cops have not already won, we plan preferably disjoint paths
        from the cop positions to the robber position in the actual graph.

        We skip the minimax and directly compute short disjoint paths with a probability that exponentially increases
        with the number of times we performed minimax for the given game configuration. This is to avoid repeating
        positions caused by abstract minimax.

        :param cop_positions: Current cop positions.
        :param robber_position: Current robber position.
        :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
        :return: The next cop positions.
        """
        minimax_abstraction = self.hierarchy.highest_undecided_abstraction(cop_positions, robber_position)
        position_key = robber_position, *cop_positions

        if minimax_abstraction is not None and random.random() < self.minimax_probability[position_key]:
            self.minimax_probability[position_key] /= 2
            return self.minimax_refinement(cop_positions, robber_position, minimax_abstraction, finish_time)

        return disjoint_search_steps(self.graph, cop_positions, robber_position)

    def minimax_refinement(
        self,
        cop_positions: list[int],
        robber_position: int,
        abstraction: GraphAbstraction,
        finish_time: float,
    ) -> list[int]:
        """ Performs minimax search on a graph abstraction and refines the solution.

        We first perform a minimax search at the given level of abstraction. If a winning solution for the cops is found
        on this level of abstraction, we refine the solution through abstract minimax descend. I.e., we perform minimax
        on decreasing levels of abstraction until the cops cannot win anymore at some level of abstraction and let the
        cops take steps on paths in the actual graph towards the abstract target nodes which were obtained through the
        lowest abstraction minimax search which was still winning for the cops.

        If we cannot even brute-force a solution at the initial level of abstraction, we fall back to letting the cops
        take steps on preferably disjoint paths towards the cop in the actual graph.

        Although we try to account to finish in time, we cannot guarantee this. This might lead to repeating timeouts.
        To handle those, we set the probability for a timeout occurring for a certain game configuration at a certain
        level of abstraction to 1 before each minimax computation. We reset them to 0 only after the computation has
        finished without a timeout interrupting the process early. We stop early with the same probability of a timeout
        and cut the probability in half each time we stop early to ensure that we try the computation again at some
        point.

        :param cop_positions: The current cop positions in the actual graph.
        :param robber_position: The current robber position in the actual graph.
        :param abstraction: The graph abstraction at which to perform the first iteration of minimax.
        :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
        :return: The next cop positions.
        """
        minimax_finish_time = remaining_time(finish_time, 0.75)  # use 75% of the time for minimax search

        # perform minimax search on the initial level of abstraction
        target_positions, is_winning = self.abstract_minimax(abstraction, cop_positions, robber_position, finish_time)

        # if the cops can't even win at the initial level of abstraction, we plan preferably disjoint paths from the cop
        # positions to the robber position in the actual graph.
        if not is_winning:
            return disjoint_search_steps(self.graph, cop_positions, robber_position)

        lower_abstraction = abstraction

        # descend in the abstraction hierarchy until the cops don't find a winning strategy anymore
        while is_winning and lower_abstraction is not None:
            # compute the next lower level of abstraction
            lower_abstraction = self.hierarchy.highest_abstraction_lower_than(lower_abstraction)
            timeout_key = lower_abstraction, *cop_positions, robber_position

            # stop at the current level of abstraction with the probability of a timeout occurring
            # we cut the timeout probability in half to make sure we try again at some point
            if random.random() < self.minimax_timeout_probability[timeout_key]:
                self.minimax_timeout_probability[timeout_key] /= 2
                break

            # pessimistically set timeout probability to 1 before the computation
            # this will be reset to 0 if the computation for this level of abstraction finished without interruption
            self.minimax_timeout_probability[timeout_key] = 1

            # case 1: there is no lower abstraction anymore
            # then, we perform minimax on the actual graph
            if lower_abstraction is None:
                # perform minimax on the actual graph
                move, is_winning = self.literal_minimax_engine.best_cop_move(
                    cop_positions,
                    robber_position,
                    MINIMAX_DEPTH,
                    self.get_fixated_steps_function(None),
                    minimax_finish_time
                )

                # if we find a solution in the winning graph, we immediately return that solution
                # because it gives a guaranteed way of winning the game for the cops in the actual graph
                # reset timeout probability to 0 if code until here was executed without interruption caused by timeout
                if is_winning:
                    self.minimax_timeout_probability[timeout_key] = 0
                    return move
            # case 2: there is a lower level of abstraction
            # then, we perform minimax search on that level of abstraction
            else:
                # perform minimax search on the next lower level of abstraction
                new_target_positions, is_winning = self.abstract_minimax(
                    lower_abstraction,
                    cop_positions,
                    robber_position,
                    minimax_finish_time
                )

                # if we find a solution on that level of abstraction, we update the target positions and the level of
                # abstraction to capture the solution at the highest level of abstraction possible
                if is_winning:
                    target_positions = new_target_positions
                    abstraction = lower_abstraction

            # reset timeout probability to 0 if code until here was executed without interruption caused by timeout
            # and the finish time was not exceeded
            if time.time() <= finish_time:
                self.minimax_timeout_probability[timeout_key] = 0

        # in the end, if we did not find a solution in the actual graph but on some level of abstraction, we obtain
        # a move for the cops as steps on a path towards the abstract nodes suggested by the highest resolution winning
        # minimax solution

        return self.abstract_refinement_search(abstraction, cop_positions, target_positions)

    def abstract_minimax(
        self,
        abstraction: GraphAbstraction,
        cop_positions: list[int],
        robber_position: int,
        finish_time: float
    ) -> tuple[list[int], bool]:
        """ Performs minimax search at a given level of graph abstraction.

        We map the positions of cops and robbers to the nodes in the given abstraction and then perform minimax search
        on that same level of abstraction. We use a dedicated engine for each level of abstraction.

        :param abstraction: The level of abstraction at which to perform the minimax search.
        :param cop_positions: The current cop positions in the actual graph.
        :param robber_position: The current robber position in the actual graph.
        :param finish_time: Time stamp indicating when the solution must have been returned at the latest.
        :return: A tuple containing the cop move suggested by the minimax search and a Boolean indicating whether the
        move is part of a winning cop strategy.
        """
        # map cop and robber positions to positions in the abstract graph
        abstract_cop_positions = abstraction.abstract_nodes(cop_positions)
        abstract_robber_position = abstraction.abstract_node(robber_position)

        # perform minimax search using the dedicated minimax engine for the given level of abstraction
        return self.minimax_engine[abstraction].best_cop_move(
            abstract_cop_positions,
            abstract_robber_position,
            MINIMAX_DEPTH,
            self.get_fixated_steps_function(abstraction),
            finish_time
        )

    def get_fixated_steps_function(self, abstraction: GraphAbstraction | None):
        """ Produces a function that computes disjoint short paths for a subset of cops.

        The function produced by this methods should be used to fixate distal cop positions in the minimax search.

        :param abstraction: Level of abstraction at which to plan paths.
        :return: A function that computes short disjoint paths from a subset of cops to the current robber position.
        """
        if abstraction is None:
            graph = self.graph
        else:
            graph = abstraction.graph

        def fixated_steps(cop_positions: list[int], robber_position) -> list[int]:
            return disjoint_search_steps(graph, cop_positions, robber_position)

        return fixated_steps

    def abstract_refinement_search(
        self,
        abstraction: GraphAbstraction,
        cop_positions: list[int],
        abstract_targets: list[int]
    ) -> list[int]:
        """ Computes steps for all cops by searching through the graph abstraction hierarchy.

        We start and the given level of abstraction and search from the abstract cop positions to the given abstract
        target positions. We then refine that search iteratively through decreasing levels of abstraction using only
        parts of the graph used in the path obtained by the search before.

        We then let the cops move a step on the final path obtained in the actual graph using the same procedure as for
        any abstraction. Fixated cop positions are taken as is.

        :param abstraction: The initial level of abstraction at which to start the search.
        :param cop_positions: The current cop positions in the actual graph.
        :param abstract_targets: The target positions for each cop at the given level of abstraction.
        :return: The next steps for each cop obtained through the abstract refinement search.
        """
        move = []

        def reduced_search(graph: Graph, source: int, targets: Iterable[int], nodes: Iterable[int]) -> list[int]:
            """ Finds a shortest path from a source to some of the multiple possible targets on a subset of the nodes.

            The search will be performed on the subgraph induced by the given set of nodes.

            :param graph: The graph through which to search.
            :param source: The node from which to start the search.
            :param targets: The targets to which to search.
            :param nodes: The subset of nodes through which to search.
            :return: A shortest path to any of the given targets in the subgraph induced by the given nodes.
            """
            search_graph = graph.subgraph(nodes)
            return multi_target_shortest_path(search_graph, source, targets)

        for cop_id, (cop_position, abstract_target) in enumerate(zip(cop_positions, abstract_targets)):
            cop_abstract_targets = [abstract_target]  # possible targets to search a path to
            refinement_nodes = abstraction.graph.nodes  # nodes which to use for the search

            # search through decreasing levels of abstraction
            for lower_abstraction in self.hierarchy.decreasing_abstractions_from(abstraction):
                # map cop position in the actual graph to position in the abstract graph
                cop_abstract_position = lower_abstraction.abstract_node(cop_position)

                # search for a path in the abstraction from the abstract cop position to any of the abstract targets
                path = reduced_search(
                    lower_abstraction.graph,
                    cop_abstract_position,
                    cop_abstract_targets,
                    refinement_nodes
                )

                actual_search_target = path[-1]  # abstract target which the search found

                # update the targets and the nodes through which to search for the next lower level of abstraction
                cop_abstract_targets = lower_abstraction.inverse_vertex_mapping[actual_search_target]
                refinement_nodes = lower_abstraction.invert_nodes(path)

            # finally, we search for a path in the actual graph and let the cop move a step on that path
            path = reduced_search(self.graph, cop_position, cop_abstract_targets, refinement_nodes)
            step = first_step_on_path(path)
            move.append(step)

        return move

    def warmup(self, finish_time: float):
        if not self.shortest_path_lengths.is_populated:
            return

        nodes = list(self.graph.nodes)
        distance = self.shortest_path_lengths.pairwise_distances

        cop_start_distances = np.array([
            min(distance[node][cop_position] for cop_position in self.init_positions)
            for node in nodes
        ])

        def softmax(x: np.ndarray) -> np.ndarray:
            exp = np.exp(x - np.max(x))
            return exp / exp.sum()

        cop_start_probabilities = softmax(cop_start_distances)

        @timeout_loop(finish_time)
        def iteration():
            robber_position = np.random.choice(nodes, p=cop_start_probabilities)

            self.warmup_minimax_refinement(
                self.init_positions,
                robber_position,
                finish_time
            )

        while True:
            if not iteration():
                break

    def warmup_minimax_refinement(self, cop_positions: list[int], robber_position: int, finish_time: float):
        abstraction = self.hierarchy.highest_abstraction
        is_winning = True

        @timeout_loop(finish_time, 2)
        def iteration():
            nonlocal is_winning, abstraction, cop_positions
            next_cop_positions = cop_positions

            while is_winning and abstraction is not None:
                abstract_robber_position = abstraction.abstract_node(robber_position)
                abstract_cop_positions = abstraction.abstract_nodes(cop_positions)
                minimax_engine = self.minimax_engine[abstraction]

                move, is_winning = minimax_engine.best_cop_move(
                    abstract_cop_positions,
                    abstract_robber_position,
                    MINIMAX_DEPTH,
                    self.get_fixated_steps_function(abstraction),
                    finish_time
                )

                if is_winning:
                    next_cop_positions = [
                        min(
                            abstraction.invert_node(abstract_cop_position),
                            key=lambda v: self.shortest_path_lengths.pairwise_distances[v][cop_position]
                        ) for cop_position, abstract_cop_position in zip(cop_positions, abstract_cop_positions)
                    ]

                abstraction = self.hierarchy.highest_abstraction_lower_than(abstraction)

            cop_positions = next_cop_positions

        while robber_position not in cop_positions:
            initial_cop_positions = cop_positions.copy()

            if not iteration():
                break

            if initial_cop_positions == cop_positions:
                break
