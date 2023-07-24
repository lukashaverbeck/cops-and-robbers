from typing import Hashable, TypeVar

from networkx import Graph, node_connected_component

VertexT = TypeVar("VertexT", bound=Hashable)
CopPositions = list[VertexT]
RobberPosition = VertexT


def compute_cop_uncontrolled_subgraph(graph: Graph, cop_positions: CopPositions) -> Graph:
    cop_neighbor_nodes = set()
    for cop_position in cop_positions:
        for pos in graph.neighbors(cop_position):
            cop_neighbor_nodes.add(pos)
    cop_controlled_nodes = set(cop_positions) | cop_neighbor_nodes

    robber_controlled_nodes = set(graph.nodes) - cop_controlled_nodes
    return graph.subgraph(robber_controlled_nodes)


def compute_effective_game_graph(graph: Graph, cop_positions: CopPositions, robber_position: RobberPosition) -> Graph:
    cop_uncontrolled_subgraph = compute_cop_uncontrolled_subgraph(graph, cop_positions)
    # node_connected_component raises errors if robber_position isn't in it
    if cop_uncontrolled_subgraph.nodes.__contains__(robber_position):
        robber_connected_nodes = node_connected_component(cop_uncontrolled_subgraph, robber_position)
    else:
        # TODO think about this case that seems to happen a lot
        robber_connected_nodes = set(graph.nodes)
    return graph.subgraph(robber_connected_nodes | set(cop_positions))


def calc_graph_size(graph: Graph) -> int:
    return graph.number_of_nodes() + graph.number_of_edges()
