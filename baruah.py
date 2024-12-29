from structures import Node, Edge, Graph, Entry, Table
from typing import Dict, Callable

def baruah(graph: Graph, destination: Node, relax: Callable) -> Dict[Node, Table]:
    """
    Baruah's algorithm with per parent domination and no cyclic entries.
    """
    nodes = graph.nodes()
    edges = graph.edges()

    tables: Dict[Node, Table] = {}
    for node in nodes:
        tables[node] = Table()
    tables[destination] = Table(entries=set([Entry(0, [], 0)]))

    for i in range(len(nodes) - 1):
        for edge in edges:
            relax(edge, tables[edge.from_node], tables[edge.to_node])

    return tables

def relax_original(edge: Edge, from_node_table: Table, to_node_table: Table):
    """
    The relaxation function from the paper Rapid Routing with Guaranteed Delay Bounds.
    Updates `from_node_table`.
    """
    table_u = from_node_table
    v = edge.to_node
    table_v = to_node_table

    if len(table_v.entries) == 0:
        # the table_v is empty there is nothing to update the table_u with
        return

    # min_max_time (d_min) is the smallest worst-case delay bound from u to the destination
    min_max_time = edge.worst_case_delay + min([entry.max_time for entry in table_v.entries])

    for entry in table_v.entries:
        max_time = max(min_max_time, entry.max_time + edge.expected_delay)
        expected_time = entry.expected_time + edge.expected_delay

        parents = entry.parents.copy()
        parents.insert(0, v)

        new_entry = Entry(max_time, parents, expected_time)
        table_u.insert_d(new_entry)

def relax_ppd_nce(edge: Edge, from_node_table: Table, to_node_table: Table):
    """
    Baruah relaxation with per parent domination and no cyclic entries. 
    Updates `from_node_table`.
    """
    u = edge.from_node
    table_u = from_node_table
    v = edge.to_node
    table_v = to_node_table

    if len(table_v.entries) == 0:
        # the table_v is empty there is nothing to update the table_u with
        return

    # min_max_time (d_min) is the smallest worst-case delay bound from u to the destination
    min_max_time = edge.worst_case_delay + min([entry.max_time for entry in table_v.entries])

    for entry in table_v.entries:
        if u in entry.parents:
            # cyclic enties should not be generated
            continue

        max_time = max(min_max_time, entry.max_time + edge.expected_delay)
        expected_time = entry.expected_time + edge.expected_delay

        parents = entry.parents.copy()
        parents.insert(0, v)

        new_entry = Entry(max_time, parents, expected_time)
        table_u.insert_ppd(new_entry)