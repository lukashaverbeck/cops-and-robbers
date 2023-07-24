from __future__ import annotations

from networkx import Graph, connected_components


class Component:
    graph: Graph

    @staticmethod
    def mapping(graph: Graph) -> dict[int, Component]:
        component_nodes = connected_components(graph)
        component_mapping = {}

        for nodes in component_nodes:
            component = Component(graph.subgraph(nodes))

            component_mapping.update({
                node: component
                for node in nodes
            })

        return component_mapping

    def __init__(self, graph: Graph):
        self.graph = graph
