from typing import Any, Tuple, Mapping, List, Dict

Node = Any
Edge = Tuple[Any, Any]
Graph = Mapping[Node, Mapping[Node, Mapping[str, Any]]]

Entry = Tuple[float, Node | None, float]
Table = List[Entry]
Tables = Dict[Node, Table]


def update_table(node: Node, table: Table, old_edge, new_edge) -> Table:
    uo, vo, c_to, c_wo = old_edge
    un, vn, c_tn, c_wn = new_edge

    """
    Update the routing table for a node.
    """
    for i, entry in enumerate(table):
        # check if the entry is for the edge
        if entry[1] == vn:
            # calculate the new entry
            table[i] = (entry[0] - uo + un, vo, entry[2] - c_to + c_tn)
            for j, other_entry in enumerate(table):
                # check if the new entry dominates other entries
                if table[i][0] <= other_entry[0] and table[i][2] <= other_entry[2]:
                    table.pop(j)
                # check if other entries dominate the new entry
                if table[i][0] >= other_entry[0] and table[i][2] >= other_entry[2]:
                    table.pop(i)
                    break

        return table

def notify_update(from_node: Node, to_node: Node, relevant_deadline, difference):
    pass;

def time_step(current_time: int, old_G, new_G, tables: Tables):
    current_time += 1

    old_G_baruah = {node: {key: (list(value.values())[0], list(value.values())[1]) for key, value in edge.items()} for
                    node, edge in old_G.adjacency()}
    new_G_baruah = {node: {key: (list(value.values())[0], list(value.values())[1]) for key, value in edge.items()} for
                    node, edge in new_G.adjacency()}
    for node in new_G_baruah.keys():
        for edge in new_G_baruah[node]:
            if new_G_baruah[node][edge] != old_G_baruah[node][edge]:
                # change detected! update routing table
                tables[node] = update_table(node, tables[node], old_G_baruah[node][edge], new_G_baruah[node][edge])
