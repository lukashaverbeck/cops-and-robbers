from __future__ import annotations

from json import load
from os.path import dirname, exists, join

from networkx import Graph, node_link_graph


def get_graph(graph_id: str) -> Graph:
    path = join(dirname(__file__), f'{graph_id}.json')
    if not exists(path):
        raise FileNotFoundError(path)

    with open(path, 'r', encoding='utf-8') as file:
        graph_json = load(file)

    graph: Graph = node_link_graph(graph_json)
    return graph


__all__ = ('get_graph',)
