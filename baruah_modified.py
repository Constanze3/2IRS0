from __future__ import annotations

from btypes import *

updated = []

def get_single_edge_change(graphs: TemporalGraph, time: int) -> None | Edge:
    if time == 0:
        return None

    old_graph = graphs.at_time(time - 1)
    new_graph = graphs.at_time(time)
    # assuming there is only 1 edge that changes

    for edge in new_graph.edges:
        if old_graph.edges[edge].expected_delay != new_graph.edges[edge].expected_delay:
            return new_graph.edges[edge]

    return None


def check_dominates_or_dominated(new_entry, table) -> None | t.List[Entry]:
    for entry in table.entries:
        if (
            new_entry.max_time >= entry.max_time
            and new_entry.expected_time >= entry.expected_time
        ):
            return None
        elif (
            new_entry.max_time <= entry.max_time
            and new_entry.expected_time <= entry.expected_time
        ):
            return [entry]
    return []


def process_new_entry(node: Node, entry: Entry):
    status = check_dominates_or_dominated(entry, node.table)
    if status == None:
        return
    elif len(status) > 0:
        # remove the dominated entry
        node.table.entries.remove(status[0])
    node.table.entries.append(entry)
    return


def changed_edge_update_table(node: Node, new_edge):
    # create entries that use that edge
    destination_node = new_edge.to_node

    # find an entry for every entry in the destination node's table
    # taking in account the new edge
    for entry in destination_node.table.entries:
        new_entry = Entry(
            node,
            new_edge.worse_case_delay + entry.max_time,
            new_edge.expected_delay + entry.expected_time,
        )  # check this
        process_new_entry(node, new_entry)

    return


def update_table(
    node: Node,
    relevant_edge: Edge,
    relevant_deadlines: t.List[int],
    relevant_expected_times: t.List[int],
    # updated: t.List[str],
):
    global updated
    # TODO: find a better way to figure out the relevant deadlines and expected times
    i = 0
    for deadline in relevant_deadlines:
        exp_time = relevant_expected_times[i]
        new_entry = Entry(relevant_edge.to_node, deadline, exp_time)

        process_new_entry(node, new_entry)

    updated.append(node.label)
    for e in node.edges:
        n = e.get_other_side(node.label)
        if n.label not in updated: 
            relevant_deadlines = [entry.max_time for entry in node.table.entries]
            relevant_expected_times = [entry.expected_time for entry in node.table.entries]
            update_table(n, e, relevant_deadlines, relevant_expected_times)
    i += 1


# what happens when time advances one step?
# ASSUMPTION: ONLY ONE EDGE CHANGES
def time_step(graph: TemporalGraph, t: int):

    # find the edge that changed
    changed_edge = get_single_edge_change(graph, t)

    if changed_edge == None:
        return
    print(f"Changed edge: {changed_edge.from_node.label} -> {changed_edge.to_node.label}")

    # node that starts propagation: source of the changed edge
    node: Node = changed_edge.from_node

    # update the routing table for the node
    changed_edge_update_table(node, changed_edge)

    global updated
    updated = [node.label]
    for edge in node.edges:
        if edge != changed_edge:
            n = edge.get_other_side(node.label)
            if n.label in updated:
                if len(updated) == len(graph.at_time(t).nodes):
                    break
                continue
    
            update_table(
                n,
                edge,
                [changed_edge.worse_case_delay],
                [changed_edge.expected_delay],
                # [node.label],
            )


def main():
    nodes = {
        "A": Node(neighbors=[], edges=[], label="A", table=Table(entries=[])),
        "B": Node(neighbors=[], edges=[], label="B", table=Table(entries=[])),
        "C": Node(neighbors=[], edges=[], label="C", table=Table(entries=[])),
        "D": Node(neighbors=[], edges=[], label="D", table=Table(entries=[])),
        "E": Node(neighbors=[], edges=[], label="E", table=Table(entries=[])),
    }

    edges = {
        ("A", "B"): Edge(nodes["A"], nodes["B"], 10, 15),
        ("A", "C"): Edge(nodes["A"], nodes["C"], 12, 18),
        ("A", "D"): Edge(nodes["A"], nodes["D"], 14, 20),
        ("B", "C"): Edge(nodes["B"], nodes["C"], 16, 22),
        ("B", "E"): Edge(nodes["B"], nodes["E"], 18, 25),
        ("C", "D"): Edge(nodes["C"], nodes["D"], 20, 30),
        ("C", "E"): Edge(nodes["C"], nodes["E"], 22, 28),
        ("D", "E"): Edge(nodes["D"], nodes["E"], 24, 35),
    }

    # Assign edges to nodes
    nodes["A"].edges = [edges[("A", "B")], edges[("A", "C")], edges[("A", "D")]]
    nodes["B"].edges = [edges[("A", "B")], edges[("B", "C")], edges[("B", "E")]]
    nodes["C"].edges = [edges[("A", "C")], edges[("B", "C")], edges[("C", "D")], edges[("C", "E")]]
    nodes["D"].edges = [edges[("A", "D")], edges[("C", "D")], edges[("D", "E")]]
    nodes["E"].edges = [edges[("B", "E")], edges[("C", "E")], edges[("D", "E")]]

    # Assign neighbors to nodes
    nodes["A"].neighbors = [nodes["B"], nodes["C"], nodes["D"]]
    nodes["B"].neighbors = [nodes["A"], nodes["C"], nodes["E"]]
    nodes["C"].neighbors = [nodes["A"], nodes["B"], nodes["D"], nodes["E"]]
    nodes["D"].neighbors = [nodes["A"], nodes["C"], nodes["E"]]
    nodes["E"].neighbors = [nodes["B"], nodes["C"], nodes["D"]]

    g = Graph(nodes=nodes, edges=edges)

    # Create a copy of the graph with one edge changed
    nodes_copy = {
        "A": Node(neighbors=[], edges=[], label="A", table=Table(entries=[])),
        "B": Node(neighbors=[], edges=[], label="B", table=Table(entries=[])),
        "C": Node(neighbors=[], edges=[], label="C", table=Table(entries=[])),
        "D": Node(neighbors=[], edges=[], label="D", table=Table(entries=[])),
        "E": Node(neighbors=[], edges=[], label="E", table=Table(entries=[])),
    }

    edges_copy = {
        ("A", "B"): Edge(nodes_copy["A"], nodes_copy["B"], 10, 15),
        ("A", "C"): Edge(nodes_copy["A"], nodes_copy["C"], 12, 18),
        ("A", "D"): Edge(nodes_copy["A"], nodes_copy["D"], 14, 20),
        ("B", "C"): Edge(nodes_copy["B"], nodes_copy["C"], 16, 22),
        ("B", "E"): Edge(nodes_copy["B"], nodes_copy["E"], 18, 25),
        ("C", "D"): Edge(nodes_copy["C"], nodes_copy["D"], 21, 33),  # Changed edge
        ("C", "E"): Edge(nodes_copy["C"], nodes_copy["E"], 22, 28),
        ("D", "E"): Edge(nodes_copy["D"], nodes_copy["E"], 24, 35),
    }

    # Assign edges to copied nodes
    nodes_copy["A"].edges = [edges_copy[("A", "B")], edges_copy[("A", "C")], edges_copy[("A", "D")]]
    nodes_copy["B"].edges = [edges_copy[("A", "B")], edges_copy[("B", "C")], edges_copy[("B", "E")]]
    nodes_copy["C"].edges = [edges_copy[("A", "C")], edges_copy[("B", "C")], edges_copy[("C", "D")], edges_copy[("C", "E")]]
    nodes_copy["D"].edges = [edges_copy[("A", "D")], edges_copy[("C", "D")], edges_copy[("D", "E")]]
    nodes_copy["E"].edges = [edges_copy[("B", "E")], edges_copy[("C", "E")], edges_copy[("D", "E")]]

    # Assign neighbors to copied nodes
    nodes_copy["A"].neighbors = [nodes_copy["B"], nodes_copy["C"], nodes_copy["D"]]
    nodes_copy["B"].neighbors = [nodes_copy["A"], nodes_copy["C"], nodes_copy["E"]]
    nodes_copy["C"].neighbors = [nodes_copy["A"], nodes_copy["B"], nodes_copy["D"], nodes_copy["E"]]
    nodes_copy["D"].neighbors = [nodes_copy["A"], nodes_copy["C"], nodes_copy["E"]]
    nodes_copy["E"].neighbors = [nodes_copy["B"], nodes_copy["C"], nodes_copy["D"]]

    g_copy = Graph(nodes=nodes_copy, edges=edges_copy)



    graphs = TemporalGraph([g, g_copy])
    for t in range(0, 2):
        time_step(graphs, t)
        print(f"Time {t}")
        for node in graphs.at_time(t).nodes:
            n = graphs.at_time(t).nodes[node]
            print(f"Node {n.label}")
            for entry in n.table.entries:
                print(
                    f"Entry: {entry.node.label}, {entry.max_time}, {entry.expected_time}"
                )
        print("\n")


if __name__ == "__main__":
    main()
