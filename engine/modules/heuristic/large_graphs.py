import networkx as nx
from networkx import Graph
from .util import CopPositions, RobberPosition


def minimax_check(steps: int, graph: Graph):
    return steps, graph


def take_second(elem):
    return elem[1]


def take_third(elem):
    return elem[2]


def get_cop_controlled_area(graph: Graph):
    """This function returns the nodes, on which cops are positioned,
    as well as all of their neighbours"""
    cop_controlled_area = set()
    for cop_pos in CopPositions:
        cop_controlled_area.add(cop_pos)
        if cop_pos in graph:
            for n in graph.neighbors(cop_pos):
                cop_controlled_area.add(n)
    return cop_controlled_area


def get_cop_controlled_component(graph: Graph, only_robber_component):
    """This function tests, if the cops have 'control' of a complete area of the graph.
    That is to say if the cops don't move, the robber can't get out of this graph component
    , without passing a cop"""

    temp_graph = graph
    cop_controlled_area = get_cop_controlled_area(graph)
    for n in cop_controlled_area:
        graph.remove_node(n)

    if nx.number_connected_components(graph) > 1:
        if only_robber_component:
            component = nx.node_connected_component(graph, RobberPosition)
            for node in temp_graph:
                if node not in component & node not in cop_controlled_area:
                    temp_graph.remove_node(n)
            return True, temp_graph
        else:
            return True, graph
    return False, temp_graph


def cop_init(graph: Graph, n_cops: int):

    """First we sort a list of all nodes in the Graph, by the number of each node's outgoing edges"""
    all_nodes = list(graph.nodes)
    node_edges = list()
    for node in all_nodes:
        node_edges.append((node, len(graph.edges(node), 0)))

    node_edges.sort(key=take_second, reverse=True)

    """We then take (one of) the node with the most edges as our first Cops starting position"""
    CopPositions.append(node_edges[0][0])
    n_cops = n_cops - 1
    node_edges.remove(node_edges[0])

    """Now we sort the remaining nodes by their distance to our starting Cops position, multiplied
    by the number of outgoing edges, to find a set of nodes that is both widespread, but also well connected"""
    for n in node_edges:
        n[2] = n[1] * len(nx.shortest_path(graph, CopPositions[0], n[0]))

    node_edges.sort(key=take_third, reverse=True)

    """Finally we take the 'best' of these nodes and set our remaining Cops onto them"""
    for i in range(0, n_cops - 1):
        CopPositions.append(node_edges[i][0])


def cop_game(graph: Graph):
    """We first want to check if the cops have 'cordoned of' a component of the graph and
    if so, we check if we can Bruteforce this area"""
    temp = get_cop_controlled_component(graph, True)
    has_cop_controlled_components = temp[0]
    g_new = temp[1]
    if has_cop_controlled_components:
        """This still needs to be correctly implemented"""
        if minimax_check(20, g_new):
            return minimax_check(20, g_new)

    """We now know, that the graph cant be feasibly Brute-Forced, so we try to find a best possible solution,
    by trying to find shortest paths, that have a widespread area of effect"""
    shortest_paths = list()
    for cop_pos in CopPositions:
        temp = nx.shortest_path(graph, cop_pos, RobberPosition)
        shortest_paths.append((cop_pos, temp, len(temp)))
    shortest_paths.sort(key=take_third)

    final_paths = list()
    final_paths.append((shortest_paths[0][0], shortest_paths[0][1]))
    shortest_paths.remove(shortest_paths[0])

    colored = set()
    depth = 2

    """We color every node that is on one of our shortest paths, as well as a certain number of neighbors. 
    This ensures, that the shortest paths are spread apart from each other. As two cops can control up to two 
    nodes between them this is our initial path distance"""
    while depth > 0:
        new_path = True
        for path in final_paths:
            for n in path[1]:
                colored.add(n)
                if depth >= 1:
                    for n1 in graph.neighbors(n):
                        colored.add(n1)
                        if depth == 2:
                            for n2 in graph.neighbors(n1):
                                colored.add(n2)

        g_new = graph
        for x in colored:
            g_new.remove_node(x)

        """If a shortest path goes through a colored section, we try to compute a new shortest path around
        the colored nodes"""
        for path in shortest_paths:
            if path not in final_paths & new_path:
                for c in colored:
                    if c in path[1]:
                        try:
                            path[1] = nx.shortest_path(g_new, path[0], RobberPosition)
                            path[2] = len(path[1])
                        finally:
                            depth = depth - 1
                            new_path = False
                            break

        if new_path:
            shortest_paths.sort(key=take_third)
            final_paths.append((shortest_paths[0][0], shortest_paths[0][1]))
            shortest_paths.remove(shortest_paths[0])

    for path in shortest_paths:
        final_paths.append(path[0], path[1])

    for cop_pos in CopPositions:
        for path in final_paths:
            if cop_pos == path[0]:
                cop_pos == path[1][1]
                final_paths.remove(path)
                break


def robber_init(graph: Graph, n_cops: int):
    """First, we check if the cops have 'cordoned of' a component of the graph and if so,
    we look for the largest component"""
    temp = get_cop_controlled_component(graph, False)
    has_cop_controlled_components = temp[0]
    g_new = temp[1]
    if has_cop_controlled_components:
        largest_component = nx.connected_components(g_new)[0]
        temp = get_cop_controlled_area(graph)
        for n in graph:
            if n not in largest_component & n not in temp:
                graph.remove_node(n)

    """Then we compute the longest shortest distance between two cops, under the assumption, that the cops have
    positioned themselves to be widespread"""
    longest_distance = 0
    checked_cops = list()
    for cop in CopPositions:
        for cop2 in CopPositions:
            if cop2 not in checked_cops & cop != cop2:
                distance = nx.shortest_path_length(graph, cop, cop2)
                if distance > longest_distance:
                    longest_distance = distance
        checked_cops.append(cop)

    """Now we sort a list of all nodes in the Graph (except cop nodes), 
    by the number of each node's outgoing edges"""
    all_nodes = list(graph.nodes)
    node_edges = list()
    for node in all_nodes:
        if node not in CopPositions:
            node_edges.append((node, len(graph.edges(node), 0)))

    node_edges.sort(key=take_second, reverse=True)

    """Finally we look for the node with the most outgoing edges, that is at least as far from a cop, as 
    the two thirds of longest shortest distance between two cops. (If there is none, we decrease the distance from cops, 
    until we find a fitting node)"""
    factor = 2/3
    for i in range(factor*longest_distance, 0):
        for n in node_edges:
            check_area = nx.single_target_shortest_path(graph, n[0], cutoff=i)
            for path in check_area:
                if path[0] in CopPositions:
                    break
                else:
                    return n[0]


def robber_game(graph: Graph):
    """We first want to check if the cops have 'cordoned of' a component of the graph and
    if so, we check if we can Bruteforce this area"""
    temp = get_cop_controlled_component(graph, True)
    has_cop_controlled_components = temp[0]
    g_new = temp[1]
    if has_cop_controlled_components:
        """This still needs to be correctly implemented, the robber wants to find the longest possible game"""
        if minimax_check(20, g_new):
            return minimax_check(20, g_new)

    """Now we compute the shortest path to every cop for our robber node and every neighbouring node. 
    We also check if we are at least 2 steps away from a cop, otherwise we are almost caught."""
    distances_to_cops = list()
    almost_caught = False
    for cop in CopPositions:
        distances_to_cops.append(nx.shortest_path_length(g_new, cop, RobberPosition))
    distances_to_cops.sort()
    if distances_to_cops[0] == 1:
        almost_caught = True
    robber_options = list()
    robber_options.append((RobberPosition, distances_to_cops))
    for n in g_new.neighbors(RobberPosition):
        distances_to_cops = list()
        for cop in CopPositions:
            distances_to_cops.append(nx.shortest_path_length(g_new, cop, n))
        distances_to_cops.sort()
        if distances_to_cops[0] > robber_options[0][1][0] & almost_caught:
            robber_options.append((n, distances_to_cops))
        elif distances_to_cops[0] >= robber_options[0][1][0]:
            robber_options.append((n, distances_to_cops))

    """Finally we compute the robber option with the highest total distance to every cop that is also 
    at least as far away from a cop, as the robber currently is (or further if we are almost caught)"""
    best_option = (RobberPosition, 0)
    for option in robber_options:
        sum_distances_to_cops = 0
        for path in option[1]:
            sum_distances_to_cops += path
        if sum_distances_to_cops > best_option[1]:
            best_option = (option[0], sum_distances_to_cops)

    return best_option[0]
