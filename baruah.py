from typing import Any, Mapping, Tuple, List, Dict, Set

Node = Any
# maps a node to a tuple of (typical delay, max delay)
Edges = Mapping[Node, Tuple[float, float]]
Graph = Mapping[Node, Edges]

Table = Dict[Node, Set[Tuple[float, Node | None, float]]]

def pretty_print_table(table: Table) -> None:
    for i in range(len(table)):
        print(f"Node {i}: {table[i]}")

def build_routing_tables(graph: Graph, destination: Node) -> Table:

    # destination t: last elem of graph
    t = destination

    table: Table = {}
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
                # insert = True # Should tuple (d, v, delta) be inserted into TAB[u]?
                # for du, piu, deltau in table[u].copy():
                #     if du >= d and deltau >= delta:
                #         # remove (du, piu, deltau) from TAB[u], since (d, v, delta) subsumes it
                #         table[u] = table[u] - {(du, piu, deltau)}
                    # if du <= d and deltau < delta:
                    #     insert = False # (d, v, delta) is subsumed by (du, piu, deltau)
                # if insert:
                table[u] = table[u] | {(d, v, delta)}

    # print(table)
    # pretty_print_table(table)

    return table