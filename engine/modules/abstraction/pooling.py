import math
from heapq import heapify, heappop
from statistics import geometric_mean

import numpy as np
from networkx import Graph


def abstract_vertex_pooling(graph: Graph) -> dict[int, int]:
    """ Computes a structure-preserving abstraction of a graph.

    The abstraction is computed as a mapping from nodes to abstract nodes where sets of nodes are contracted into one
    abstract node (i.e., a pool of nodes in the input graph). The size of the abstract graph is (roughly) half the size
    of the input graph. For even |V|, the resulting abstract graph has |V| // 2 nodes. For odd |V|, the resulting
    abstract graph has |V| // 2 + 1 nodes.

    First, we contract pairs of adjacent nodes that have not yet been contracted in order of their geometric mean
    degree. In this sense the abstraction preserves parts of the structure because adjacent nodes with small geometric
    mean degree are "characteristic" neighbors.

    If this does not suffice (i.e., if not enough nodes were contracted), we repeat the same procedure between the
    remaining nodes that have not yet been contracted and nodes that have already been contracted until there are
    sufficiently few abstract nodes.

    As contracting nodes effectively corresponds to joining disjoint sets, we maintain a union-find data structure to
    efficiently contract nodes and look up their respective abstract nodes.

    We require that the input graph be connected. Under this assumption, the abstract graph induced by linking the
    abstract nodes based on the links between the nodes that constitute them is connected again.

    :param graph: The connected graph to be abstracted.
    :return: A mapping from nodes to abstract nodes that cuts the number of nodes in half.
    """
    nodes = [node for node in graph.nodes]
    n_nodes = len(nodes)
    node_indices = {node: i for i, node in enumerate(graph.nodes)}

    uf_parents = np.arange(n_nodes)  # parent pointers of the union-find data structure
    uf_rank = np.ones(n_nodes, dtype=np.int32)  # rank of the union-find data structure

    def union(_u: int, _v: int):
        """ Performs a union operation in the union-find data structure.

        We join the two sets corresponding to the input elements by joining their root set representatives.
        We use rank compression to keep the union-find tree height small.

        :param _u: An element within the data structure (must be in {0, ..., n - 1}).
        :param _v: Another element to join sets with the first one (must be in {0, ..., n - 1} as well).
        """
        # find roots of the input elements
        _u = find(_u)
        _v = find(_v)

        # join the roots by rank
        if uf_rank[_u] > uf_rank[_v]:
            uf_parents[_v] = _u
        elif uf_rank[_u] < uf_rank[_v]:
            uf_parents[_u] = _v
        else:
            uf_parents[_v] = _u
            uf_rank[_u] += 1

    def find(_v: int) -> int:
        """ Performs a find operation in the union-find data structure.

        We find the root representative of the input by traversing up the union-find tree to its root.
        We use path compression to decrease the height of the tree amortizing the complexity of the operation to be
        almost constant on average.

        :param _v: An element within the data structure (must be in {0, ..., n - 1}).
        :return: The root set representative of the element (index in {0, ..., n - 1}).
        """
        while uf_parents[_v] != _v:  # search for root element
            _v = uf_parents[_v] = uf_parents[uf_parents[_v]]  # move up to parent using path compression
        return _v

    n_abstract_nodes = n_nodes  # keeps track of number of abstract nodes present after the pooling
    target_n_abstract_nodes = math.ceil(n_nodes / 2)  # desired number of nodes in the abstract graph
    marked = np.full(n_nodes, False)  # stores whether a node has been already contracted with another node

    def geometric_mean_degree(_u: int, _v: int) -> float:
        """ Computes the geometric mean degree of two nodes.

        A low geometric mean degree between two adjacent nodes indicates a characteristic neighborhood
        between those nodes as they are neighbors, although they have few neighbors. The geometric mean is
        chosen because it is only little affected by outliers.

        :param _u: One node in the input graph.
        :param _v: Another node in the input graph.
        :return: The geometric mean of the degrees of the input nodes.
        """
        return geometric_mean((graph.degree[nodes[_u]], graph.degree[nodes[_v]]))

    def make_mean_degree_edge_tuple(_u: int, _v: int) -> tuple[float, int, int]:
        return geometric_mean_degree(_u, _v), _u, _v

    def perform_vertex_pooling(strict: bool, mean_degree_edge_tuples: list[tuple[float, int, int]]):
        """ Contracts vertices based on their mean degree.

        We iterate over all given edges in non-decreasing order of the geometric mean degree of their incident
        vertices. As long as there are nodes left to contract and too many abstract nodes, we contract the
        adjacent nodes which decreases the number of abstract nodes by one.

        In strict mode, we only contract two adjacent nodes if they both have not yet been contracted (i.e., are not
        marked). Otherwise, we only contract two adjacent nodes if one of them is marked and the other is not.

        :param strict: Boolean indicating whether to contract in strict mode.
        :param mean_degree_edge_tuples: Tuple (metric, u, v) where nodes u and v are contracted in order of the metric.
        """
        nonlocal n_abstract_nodes
        heapify(mean_degree_edge_tuples)

        while mean_degree_edge_tuples and n_abstract_nodes > target_n_abstract_nodes:
            _, u, v = heappop(mean_degree_edge_tuples)  # get edge {u, v} with minimal geometric mean degree of the nodes

            # if in strict mode, we require both nodes to be unmarked
            # if not in strict mode, we require exactly one node to be unmarked
            # if either of the condition is not given, we ignore the edge and move on to the next edge
            if (strict and (marked[u] or marked[v])) or (not strict and not (marked[u] ^ marked[v])):
                continue

            union(u, v)  # contracts u and v by joining their respective node sets in the union-find data structure
            n_abstract_nodes -= 1  # contracting two nodes removes exactly one abstract vertex

            # mark both vertices as having been contracted at least once
            marked[u] = True
            marked[v] = True

    # Phase 1: Contract pairs of adjacent unmarked nodes
    perform_vertex_pooling(True, [
        make_mean_degree_edge_tuple(node_indices[u], node_indices[v])
        for u, v in graph.edges
        if u != v
    ])

    # Phase 2: If there are still too many nodes, contract pairs of adjacent nodes where one is marked and one is not
    # We do this because it might be the case that no pair of adjacent unmarked nodes ist left to contract, but we
    # haven't yet reached the desired small number of abstracted nodes
    if n_abstract_nodes > target_n_abstract_nodes:
        unmarked_nodes, = np.where(~marked)  # indices of nodes that are not marked yet

        # contract unmarked nodes with adjacent marked nodes
        perform_vertex_pooling(False, [
            make_mean_degree_edge_tuple(unmarked_node_index, marked_neighbor_index)
            for unmarked_node_index in unmarked_nodes
            for neighbor in graph.neighbors(nodes[unmarked_node_index])
            if marked[marked_neighbor_index := node_indices[neighbor]]
        ])

    # map each vertex to its contracted abstract node where the abstract nodes
    uf_roots = set(find(node) for node in uf_parents)
    root_indices = {root: i for i, root in enumerate(uf_roots)}
    abstract_node_mapping = {node: root_indices[find(i)] for i, node in enumerate(nodes)}

    return abstract_node_mapping
