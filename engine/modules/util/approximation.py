import random
from heapq import nsmallest

from networkx import Graph

from .search import farthest_node


def gon(graph: Graph, k: int) -> list[int]:
    """ Computes a 2-approximation for the unweighted vertex k-center problem.

    The algorithm is taken from `Clustering to minimize the maximum intercluster distance`
    (https://www.sciencedirect.com/science/article/pii/0304397585902245). We start from an arbitrary node for which we
    choose the highest degree node. From there we add to our list of centers the node that has maximum distance to all
    current center nodes. This gives the theoretical guarantee of a 2-approximation.

    We assume that the graph contains at least one node.

    :param graph: The undirected graph to compute k central nodes for.
    :param k: Number of centers to compute.
    :return: k central vertices in the graph.
    """
    centers = [max(graph.nodes, key=graph.degree.__getitem__)]

    while len(centers) < k:
        max_center_distance_node = farthest_node(graph, centers)
        centers.append(max_center_distance_node)

    return centers


def greedy_weighted_k_center(
    graph: Graph,
    pairwise_distances: dict[int, dict[int, int]],
    weights: dict[int, float],
    d: int,
    upper_bound: float = float("inf")
) -> list[int]:
    """ Computes a greedy solution to the weighted k-vertex solution.

    The algorithm is adapted for undirected graphs taken from `A Heuristic Algorithm for the k-Center Problem with
    Vertex Weight` (https://link.springer.com/chapter/10.1007/3-540-52921-7_88). The fact that we only consider
    undirected graphs simplifies the local neighborhood of a node in d-restricted graphs to the set of nodes that are at
    most 2*d away. This significantly speeds up the computation in each iteration.

    If the solution exceeds an optionally given upper bound, we stop early and return the current solution. In this case
    there is no guarantee of a 2-approximation.

    :param graph: The undirected graph to compute k central nodes for.
    :param pairwise_distances: Map containing the pairwise distances between all vertices.
    :param weights: Map containing the weights for each vertex.
    :param d: Distance to restrict the local neighborhood of each vertex to.
    :param upper_bound: An upper bound on the size of the solution.
    :return: A list of greedily highly-weighted central vertices such that every vertex has distance at most 2*d to any
    of these central vertices.
    """
    centers = []
    nodes = set(graph.nodes)

    while nodes:
        center = max(nodes, key=weights.get)
        centers.append(center)

        if len(centers) > upper_bound:
            break

        nodes.remove(center)
        nodes -= {node for node in nodes if pairwise_distances[center][node] <= 2 * d}

    return centers


def wang_cheng_weighted_k_center(
    graph: Graph,
    pairwise_distances: dict[int, dict[int, int]],
    weights: dict[int, float],
    k: int
) -> list[int]:
    """ Computes a 2-approximation for the weighted vertex k-center problem.

    The algorithm is adapted for undirected graphs taken from `A Heuristic Algorithm for the k-Center Problem with
    Vertex Weight` (https://link.springer.com/chapter/10.1007/3-540-52921-7_88).

    We assume that the graph contains at least one node.

    :param graph: The undirected graph to compute k central nodes for.
    :param pairwise_distances: Map containing the pairwise distances between all vertices.
    :param weights: Map containing the weights for each vertex.
    :param k: Number of centers to compute.
    :return: k central vertices in the graph.
    """
    centers = []
    different_distances = set().union(*[distances.values() for distances in pairwise_distances.values()])

    # for any distance that exists between two vertices in the graph, we greedily compute a 2-approximation using an
    # unfixed number of centers until we find a solution that is small enough
    for distance in sorted(different_distances):
        greedy_d_centers = greedy_weighted_k_center(graph, pairwise_distances, weights, distance, k)

        if len(greedy_d_centers) <= k:
            centers = greedy_d_centers
            break

    # if there are more centers to choose, we pick the ones with the smallest total distance to all nodes
    # if there are not enough different nodes to do that, we pick the remaining nodes randomly from the already chosen
    # centers
    if len(centers) < k and len(graph.nodes) > 0:
        def total_distance(node: int) -> float:
            return sum(pairwise_distances[node].values())

        nodes = [node for node in graph.nodes if node not in centers]
        centers.extend(nsmallest(k - len(centers), nodes, key=total_distance))

        if len(centers) < k:
            centers.extend(random.choices(list(centers), k=k - len(centers)))

    return centers
