import math
from statistics import mean

from .abstraction import trap_free_subgraph
from .component import Component


def component_cop_distribution(components: list[Component]) -> dict[Component, float]:
    cop_numbers = {}
    total_cop_number = 0

    for component in components:
        trap_free_component = trap_free_subgraph(component.graph)

        if trap_free_component.number_of_nodes() == 0:
            cop_number = 0
        else:
            mean_degree = mean(trap_free_component.degree[node] for node in trap_free_component.nodes)
            n_nodes = trap_free_component.number_of_nodes()
            sqrt_nodes = math.sqrt(n_nodes)

            if mean_degree <= sqrt_nodes:
                cop_number = mean_degree
            else:
                cop_number = sqrt_nodes * (1 - (mean_degree - sqrt_nodes) / (n_nodes - sqrt_nodes))

        cop_numbers[component] = cop_number
        total_cop_number += cop_number

    if total_cop_number == 0:
        n_nodes = sum(component.graph.number_of_nodes() for component in components)
        assert n_nodes > 0
        return {component: component.graph.number_of_nodes() / n_nodes for component in components}

    return {
        component: cop_number / total_cop_number
        for component, cop_number in cop_numbers.items()
    }
