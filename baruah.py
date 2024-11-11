from typing import Any, Mapping, Tuple, List, Dict, Set

Node = Any
# maps a node to a tuple of (typical delay, max delay)
Edges = Mapping[Node, Tuple[float, float]]
Graph = Mapping[Node, Edges]

Tables = Dict[Node, Set[Tuple[float, Node | None, float]]]

def pretty_print_table(table: Tables) -> None:
    for i in range(len(table)):
        print(f"Node {i}: {table[i]}")

def build_routing_tables(graph: Graph, destination: Node) -> Tables:

    # destination t: last elem of graph
    t = destination

    table: Tables = {}
    # INITIALIZE(G = (V, E))
    for node in graph.keys():
        table[node] = set()
    table[t] = {(0, None, 0)}

    # create list of unique edges
    edges = set()
    for u, uedges in graph.items():
        for v, weights in uedges.items():
            edges.add((u, v, weights))

    for _ in range(len(graph) - 1):
        for u, v, weights in edges:
            # RELAX(u, v)
            if len(table[v]) == 0:
                continue
            # Let dmin denote the minimum worst-case delay guarantee that is currently possible if edge (u, v) is traversed
            # dmin = cw(u, v) + min{d | (d, π, δ) ∈ TAB[v]}
            dmin = weights[1] + min([d for (d, _, _) in table[v]])
            for dv, piv, deltav in table[v]:
                d = max(dmin, weights[0] + dv)
                delta = deltav + weights[0]
                
                contains_v = False
                for value in table[u]:
                    if value[1] == v:
                        contains_v = True

                insert = True # Should tuple (d, v, delta) be inserted into TAB[u]?

                if not contains_v:
                    for du, piu, deltau in table[u].copy():
                        if du >= d and deltau >= delta:
                            # remove (du, piu, deltau) from TAB[u], since (d, v, delta) subsumes it
                            table[u] = table[u] - {(du, piu, deltau)}
                        if du <= d and deltau < delta:
                            insert = False # (d, v, delta) is subsumed by (du, piu, deltau)
                    if insert:
                        table[u] = table[u] | {(d, v, delta)}

    # print(table)
    # pretty_print_table(table)

    return table

def baruah(graph, destination, keep_entries):
    """
    Runs Baruah's routing algorithm.

    'keep_entries' will make sure for the routing tables of each node to keep a routing table entry for each neighboring node.
    """

    # TODO actually find nodes and edges of the graph
    nodes = graph.nodes
    edges = graph.edges
    
    tab = {}

    for node in nodes:
        tab[node] = []
    tab[destination] = [(0, None, 0)]

    def relax(edge):
        global tab
        # u, v are the start and end vertices of the edge
        # c_w is the worst case delay traversing the edge
        # c_t is the estimate of the typical delay when traversing the edge
        u, v, c_w, c_t = edge

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
            # TODO for each neighbor check the count of entries in tab[u]

            if keep_entries:
                # if there are no entries with v as the parent we insert v
                if entry_count[v] == 0:
                    tab[u].append((d, v, de))
                    return

            for d_u, p_u, de_u in tab[u]:
                if d_u <= d and de_u < de:
                    # our new entry is dominated by an existing entry, it should not be inserted
                    # -> there are no entries in the table that this entry dominates
                    return
                elif d_u >= d and de_u >= de:
                    # existing entry is dominated by our new entry 
                    # -> our new entry is definitely in the table
                    if not keep_entries or entry_count[p_u] > 1 or v == p_u:
                        # we make sure that there is at least one entry with p_u
                        tab[u].remove((d_u, p_u, de_u))

            tab[u].append((d, v, de))
        
    for i in range(len(nodes) - 1):
        for edge in edges:
            relax(edge)

    return tab