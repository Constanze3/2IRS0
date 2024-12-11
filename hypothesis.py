from baruah import Entry, Tables, Node, Edge, Graph
from typing import Mapping, List, Tuple, Set
import math

Path = List[Node]
Paths = Mapping[Tuple[Node, Entry], Path]

EntryEdgeMap = Mapping[Tuple[Node, Entry], Set[Edge]]
EdgeEntryMap = Mapping[Edge, List[Tuple[Node, Entry]]]

class ChangedEntries:
    def __init__(
            self, 
            on_increment: EdgeEntryMap, 
            on_decrement: EdgeEntryMap
    ) -> None:
        # entries changed on incrementing an edge
        self.on_increment = on_increment
        # entries changed on decrementing an edge
        self.on_decrement = on_decrement

def determine_changed_entries(graph: Graph, destination: Node, tables: Tables) -> ChangedEntries:
    """
    This function determines an increment-set and a decrement-set that contain
    (identifiers of) table entries for each edge in the graph such that if the
    hypothesis is correct then incrementing/decrementing an edge by one the entries
    in the corresponding sets should be removed from their respective tables.
    """

    # edges that change the entry on incrementing by 1
    increment_edges: EntryEdgeMap = dict()

    # edges that change the entry on decrementing by 1
    decrement_edges: EntryEdgeMap = dict()

    for node, table in tables.items():
        for entry in table:
            increment_edges[(node, entry)] = set()
            decrement_edges[(node, entry)] = set()

    queue: List[Node] = []
    queue.append(destination)

    while queue:
        v = queue.pop(0)

        for u in graph.keys():
            for entry_u in tables[u]:
                d_u, p_u, de_u = entry_u

                # consider only entries that lead to v
                if p_u != v:
                    continue

                queue.append(u)

                c_t = graph[u][v]["typical_delay"]
                c_w = graph[u][v]["max_delay"]
                
                d_min = d_u - c_w
                d_max = d_u - c_t
                
                # determine feasible entries with minimum typical time

                min_de_v = math.inf
                feasible_entries = []

                for entry_v in tables[v]:
                    d_v, p_v, de_v = entry_v

                    if d_min <= d_v and d_v <= d_max:
                        if de_v == min_de_v:
                            feasible_entries.append(entry_v)
                        elif de_v < min_de_v:
                            min_de_v = de_v
                            feasible_entries.clear()
                            feasible_entries.append(entry_v)

                if len(feasible_entries) == 1 and v != destination:
                    # there is exactly one feasible entry
                    feasible_entry = feasible_entries[0]
                    
                    # incrementing an edge along the feasible path defined by the entry results in change
                    increment_edges[(u, entry_u)] = {(u, v)} | increment_edges[(v, feasible_entry)]

                    # decrementing an edge along any of the decrement paths of the entry results in change
                    decrement_edges[(u, entry_u)] = {(u, v)} | decrement_edges[(v, feasible_entry)]

                elif 1 < len(feasible_entries) and v != destination:
                    #  there are multiple feasible entries 

                    # incrementing an edge in any feasible increment path has no effect,
                    # because there is/are other feasible increment path(s) with unchanged typical value
                    increment_edges[(u, entry_u)] = {(u, v)}
                    
                    # decrementing any of the feasible decrement paths will result in the entry being changed
                    decrement_edges[(u, entry_u)] = {(u, v)}
                    for feasible_entry in feasible_entries:
                        decrement_edges[(u, entry_u)] |= decrement_edges[(v, feasible_entry)]
                else:
                    # v = destination
                    # the destination has no paths to consider the only edge that changes the entry is (u, v)
                    increment_edges[(u, entry_u)] = {(u, v)}
                    decrement_edges[(u, entry_u)] = {(u, v)}

    # transform result into EdgeEntryMap

    on_increment: EdgeEntryMap = dict()
    on_decrement: EdgeEntryMap = dict()

    for u, neighbors in graph.items():
        for v in neighbors.keys():
            edge = (u, v)

            on_increment[edge] = []
            on_decrement[edge] = []
            
            for entry_id, edges in increment_edges.items():
                if edge in edges:
                    on_increment[edge].append(entry_id)

            for entry_id, edges in decrement_edges.items():
                if edge in edges:
                    on_decrement[edge].append(entry_id)

    return ChangedEntries(on_increment, on_decrement)

if __name__ == "__main__":
    from baruah import baruah
    from difference import difference

    G = {
        1: {2: {'typical_delay': 4, 'max_delay': 10}, 4: {'typical_delay': 15, 'max_delay': 25}},
        2: {3: {'typical_delay': 4, 'max_delay': 10}, 4: {'typical_delay': 12, 'max_delay': 15}},
        3: {4: {'typical_delay': 4, 'max_delay': 10}},
        4: {}
    }

    tables = baruah(G, 4, True)

    changed_entries = determine_changed_entries(G, 4, tables)
    print(changed_entries.on_increment)

    e = (2, 3)
    ew = G[e[0]][e[1]]
    
    ew["typical_delay"] += 1
    new_tables = baruah(G, 4, True)
    
    for node, diff in difference(tables, new_tables).items():
        print(f"from {node} removed {diff.removed}")
    
