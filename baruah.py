from typing import Any, Mapping, Tuple, List, Dict, Set
from random import shuffle

Node = Any
Edge = Tuple[Any, Any]
Graph = Mapping[Node, Mapping[Node, Mapping[str, Any]]]

Entry = Tuple[float, Node | None, float]
Table = List[Entry] 
Tables = Dict[Node, Table]

def baruah(graph: Graph, destination: Node, keep_entries: bool) -> Tables:
    """
    Runs Baruah's routing algorithm.

    'graph' adjacency list of the graph.
    'destination' the destination node.
    'keep_entries' will make sure for the routing tables of each node to keep a routing table entry for each neighboring node.
    """

    # get list of nodes and edges of the graph
    nodes = graph.keys()
    edges = []
    for u, neighbors in graph.items():
        for v, weights in neighbors.items():
            edges.append((u, v, weights["typical_delay"], weights["max_delay"]))
    
    shuffle(edges)

    # initialization
    tab: Tables = {}
    for node in nodes:
        tab[node] = []
    tab[destination] = [(0, None, 0)]

    def relax(edge):
        # u, v are the start and end vertices of the edge
        # c_w is the worst case delay traversing the edge
        # c_t is the estimate of the typical delay when traversing the edge
        u, v, c_t, c_w = edge

        # this function attempts to use the entries in tab[v] to update tab[u]

        if not tab[v]:
            # the tab[v] is empty there is nothing to update the tab[u] with
            return

        # tab[v], = informs us
        # of a path from v to the destinaton with
        # worst-case delay bound d_v and typical delay de_v
        # the next node along this path is p_v

        # d_min is the smallest worst-case delay bound from u to the destination
        d_min = c_w + min([d_v for d_v, p_v, de_v in tab[v]])

        for d_v, p_v, de_v in tab[v]:
            # d is a worst case delay bound
            # it's exact definition is complicated
            d = max(d_min, c_t + d_v)
            de = de_v + c_t

            entry_count = {}
            if keep_entries:
                for neighbor in graph[u].keys():
                    entry_count[neighbor] = 0
                    for d_u, p_u, de_u in tab[u]:
                        if p_u == neighbor:
                            entry_count[neighbor] += 1
            
                # if there are no entries with v as the parent we insert v
                if entry_count[v] == 0:
                    tab[u].append((d, v, de))
                    return
                
            insert = True

            for d_u, p_u, de_u in tab[u]:
                if d_u <= d and de_u <= de:
                    # our new entry is dominated by an existing entry, it should not be inserted
                    # -> there are no entries in the table that this entry dominates
                    insert = False
                    break
                elif d_u >= d and de_u >= de:
                    # existing entry is dominated by our new entry 
                    # -> our new entry is definitely in the table
                    if not keep_entries or entry_count[p_u] > 1 or v == p_u:
                        # we make sure that there is at least one entry with p_u
                        tab[u].remove((d_u, p_u, de_u))

            if insert:
                tab[u].append((d, v, de))

    my_edges = [(1, 3, 10, 12), (1, 2, 5, 12), (2, 3, 5, 12)]
    my_edges2 = [(1, 3, 10, 24), (1, 2, 5, 6),  (2, 3, 5, 6)]


    for i in range(len(nodes) - 1):
        for edge in my_edges:
            relax(edge)

   # since tables are a set of entries having them as a sorted list is convenient
    for table in tab.values():
        table.sort()

    return tab