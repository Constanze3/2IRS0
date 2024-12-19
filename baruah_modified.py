from __future__ import annotations

from btypes import Graph, Node, Tables, Edge, Table, Entry, TemporalGraph

updated = []

def original_baruah(graph: Graph, destination: str, keep_entries: bool) -> Tables:
    """
    Runs Baruah's routing algorithm.

    'graph' adjacency list of the graph.
    'destination' the destination node.
    'keep_entries' will make sure for the routing tables of each node to keep a routing table entry for each neighboring node.
    """

    # get list of nodes and edges of the graph
    nodes = graph.nodes()
    edges = graph.edges()

    # shuffle(edges)

    # initialization
    tab: Tables = {}
    for node in nodes:
        tab[node] = Table()
    tab[destination] = Table(entries=[Entry(parent=None, max_time=0, expected_time=0)])

    def relax(edge: Edge):
        # u, v are the start and end vertices of the edge
        # c_w is the worst case delay traversing the edge
        # c_t is the estimate of the typical delay when traversing the edge
        u = edge.from_node
        v = edge.to_node
        c_t = edge.expected_delay
        c_w = edge.worst_case_delay

        # this function attempts to use the entries in tab[v] to update tab[u]

        if len(tab[v].entries) == 0:
            # the tab[v] is empty there is nothing to update the tab[u] with
            return

        # tab[v], = informs us
        # of a path from v to the destinaton with
        # worst-case delay bound d_v and typical delay de_v
        # the next node along this path is p_v

        # d_min is the smallest worst-case delay bound from u to the destination
        d_min = c_w + min([entry.max_time for entry in tab[v].entries])

        for entry in tab[v].entries:
            d_v = entry.max_time
            de_v = entry.expected_time
            p_v = entry.parent
            # d is a worst case delay bound
            # it's exact definition is complicated
            d = max(d_min, c_t + d_v)
            de = de_v + c_t
            
            new_entry = Entry(d, v, de)
            if keep_entries:
                tab[u].insert_ppd(new_entry)
            else:
                tab[u].insert(new_entry)

    for i in range(len(nodes)):
        for edge in edges:
            relax(edge)

    # since tables are a set of entries having them as a sorted list is convenient
    for table in tab.values():
        table.entries.sort()

    # assign the tables to the nodes
    # for node in nodes:
    #     node.table = tab[node]

    return tab

def get_single_edge_change(graphs: TemporalGraph, time: int) -> None | Edge:
    if time == 0:
        return None

    old_graph = graphs.at_time(time - 1)
    new_graph = graphs.at_time(time)

    old_edges = old_graph.edges()
    new_edges = new_graph.edges()
    # assuming there is only 1 edge that changes

    for edge in new_edges:
        if edge not in old_edges:
            return edge

    return None


# def check_dominates_or_dominated(new_entry, table) -> None | List[Entry]:
#     for entry in table.entries:
#         if (
#             new_entry.max_time >= entry.max_time
#             and new_entry.expected_time >= entry.expected_time
#         ):
#             return None
#         elif (
#             new_entry.max_time <= entry.max_time
#             and new_entry.expected_time <= entry.expected_time
#         ):
#             return [entry]
#     return []


# def process_new_entry(node: Node, table: Table, entry: Entry) -> None:
#     status = check_dominates_or_dominated(entry, table)
#     if status == None:
#         return
#     elif len(status) > 0:
#         # remove the dominated entry
#         table.entries.remove(status[0])
#     table.entries.append(entry)
#     return


# def changed_edge_update_table(node: Node, table: Table, new_edge):
#     # create entries that use that edge
#     destination_node = new_edge.to_node

#     # find an entry for every entry in the destination node's table
#     # taking in account the new edge
#     for entry in destination_node.table.entries:
#         new_entry = Entry(
#             node,
#             new_edge.worse_case_delay + entry.max_time,
#             new_edge.expected_delay + entry.expected_time,
#         )  # check this
#         process_new_entry(node, table, new_entry)

#     return


# def update_table(
#     graph: Graph,
#     table: Table,
#     node: Node,
#     relevant_edge: Edge,
#     relevant_deadlines: List[int],
#     relevant_expected_times: List[int],
#     # updated: t.List[str],
# ):
#     global updated
#     # TODO: find a better way to figure out the relevant deadlines and expected times
#     i = 0
#     for deadline in relevant_deadlines:
#         exp_time = relevant_expected_times[i]
#         new_entry = Entry(parent=relevant_edge.to_node, max_time=deadline, expected_time=exp_time)

#         process_new_entry(node, table, new_entry)

#     updated.append(node)
#     for e in graph.outgoing_edges(node):
#         n = e.get_other_side(node)
#         if n not in updated: 
#             relevant_deadlines = [entry.max_time for entry in table.entries]
#             relevant_expected_times = [entry.expected_time for entry in table.entries]
#             update_table(graph, n, e, relevant_deadlines, relevant_expected_times)
#     i += 1


# # what happens when time advances one step?
# # ASSUMPTION: ONLY ONE EDGE CHANGES
# def time_step(graph: TemporalGraph, t: int):

#     # find the edge that changed
#     changed_edge = get_single_edge_change(graph, t)

#     if changed_edge == None:
#         return
#     print(f"Changed edge: {changed_edge.from_node.label} -> {changed_edge.to_node.label}")

#     # node that starts propagation: source of the changed edge
#     node: Node = changed_edge.from_node

#     # update the routing table for the node
#     changed_edge_update_table(node, changed_edge)

#     global updated
#     updated = [node.label]
#     for edge in graph.at_time(t).outgoing_edges(node):
#         if edge != changed_edge:
#             n = edge.get_other_side(node.label)
#             if n.label in updated:
#                 if len(updated) == len(graph.at_time(t).get_nodes()):
#                     break
#                 continue
    
#             update_table(
#                 graph.at_time(t),
#                 n,
#                 edge,
#                 [changed_edge.worst_case_delay],
#                 [changed_edge.expected_delay],
#             )


# def main():

#     g = Graph(
#         adjacency_list={
#             "A": {"B": (10, 15), "C": (12, 18), "D": (14, 20)},
#             "B": {"C": (16, 22), "E": (18, 25)},
#             "C": {"D": (20, 30), "E": (22, 28)},
#             "D": {"E": (24, 35)},
#             "E": {}
#         }
#     )

#     g_copy = deepcopy(g)
#     g_copy.edge("C", "D").expected_delay = 30

#     original_baruah(g, g.get_node("E"), False)
#     original_baruah(g_copy, g_copy.get_node("E"), False)


#     graphs = TemporalGraph([g, g_copy])
#     print(graphs)

#     def print_state(graph: Graph, t: int):
#         print(f"Time {t}")
#         print(graph)
#         for n in graph.get_nodes():
#             print(f"Node {n.label}")
#             for entry in n.table.entries:
#                 print(
#                     entry
#                 )
#         print("\n")

#     for t in range(len(graphs)):
#         time_step(graphs, t)
#         print_state(graphs.at_time(t), t)


# if __name__ == "__main__":
#     main()
