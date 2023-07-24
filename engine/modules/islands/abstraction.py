from networkx import Graph


def trap_free_subgraph(graph: Graph) -> Graph:
    """ Computes a subgraph that only contains the regions of the input graph where the robber is not trapped.

    We start with the whole graphs. We iteratively remove nodes with degree 0 or 1. This is because the robber cannot
    escape from a nodes with degree 0 or 1 and will sooner or later be unable to escape from any node that was adjacent
    only to other trap nodes in previous iterations.

    The resulting subgraph might not be connected. If the graph only contains trap nodes (e.g., path graphs, trees) the
    resulting subgraph is empty.

    :param graph: The graph to compute the trap free subgraph for.
    :return: The trap free subgraph.
    """
    stop = False  # we stop as soon as we do not remove any nodes anymore

    while not stop:
        nodes = [node for node, degree in graph.degree if degree >= 2]  # filter out nodes with degree 0 or 1
        stop = len(nodes) == graph.number_of_nodes()  # check if the node set became smaller
        graph = graph.subgraph(nodes)  # update graph to remove trap nodes

    return graph
