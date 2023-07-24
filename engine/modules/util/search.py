from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

from networkx import Graph, astar_path


def multi_target_shortest_path(graph: Graph, source: int, targets: Iterable[int]) -> list[int]:
    targets = set(targets)
    visited = defaultdict(lambda: False)
    predecessors = {}

    def trace_path(target: int) -> list[int]:
        path = [target]

        while target in predecessors:
            target = predecessors[target]
            path.append(target)

        path.reverse()
        return path

    discovered_nodes = deque([source])

    while discovered_nodes:
        node = discovered_nodes.popleft()

        if visited[node]:
            continue

        if node in targets:
            return trace_path(node)

        visited[node] = True
        unvisited_neighbors = filter(lambda v: not visited[v] and v not in predecessors, graph.neighbors(node))

        for neighbor in unvisited_neighbors:
            discovered_nodes.append(neighbor)
            predecessors[neighbor] = node

    raise Exception(f"There is no path from {source} to any of {targets} in {graph}.")


def farthest_node(graph: Graph, sources: list[int]) -> int:
    visited = defaultdict(lambda: False)

    discovered_nodes = deque(sources)
    last_visited_node = sources[0]

    while discovered_nodes:
        node = discovered_nodes.popleft()

        if visited[node]:
            continue

        visited[node] = True
        last_visited_node = node

        unvisited_neighbors = filter(lambda v: not visited[v], graph.neighbors(node))
        discovered_nodes.extend(unvisited_neighbors)

    return last_visited_node


def penalty_astar(graph: Graph, source: int, target: int, penalty: dict[int, int]):
    path = astar_path(graph, source, target, lambda v, _: penalty[v])

    for node in path:
        penalty[node] += 1

    return path


def disjoint_search_steps(graph: Graph, cop_positions: list[int], robber_position: int) -> list[int]:
    move = []
    penalty = defaultdict(lambda: 0)

    for cop_position in cop_positions:
        path = penalty_astar(graph, cop_position, robber_position, penalty)
        step = first_step_on_path(path)
        move.append(step)

    return move


def first_step_on_path(path: list[int]) -> int:
    if len(path) <= 1:
        return path[0]
    return path[1]
