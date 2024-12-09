from copy import deepcopy
import random
from baruah_modified import original_baruah
from btypes import Graph, Entry, Tables, Table, TemporalGraph, Node, Edge
from typing import List, Dict
from dataclasses import dataclass
import multiprocessing as mp
from time import sleep

NodeLabel = int | str


@dataclass
class NeighborUpdate:
    from_node: Node
    # deadline: int
    difference: int



@dataclass
class NodeData:
    parent_queues: List[mp.Queue]  # THESE ARE NODES WITH EDGES TO THIS NODE
    edges: List[Edge]  # THESE ARE EDGES FROM THIS NODE
    table: Table


def reduce_table(node_data: NodeData, keep_entries: bool = True):
    table = node_data.table
    new_table = deepcopy(table)

    entry_count = {}
    for entry in table.entries:
        if entry.parent in entry_count:
            entry_count[entry.parent] += 1
        else:
            entry_count[entry.parent] = 1

    for entry in table.entries:
        for entry2 in table.entries:
            if entry == entry2:
                continue
            if (
                entry.expected_time <= entry2.expected_time
                and entry.max_time <= entry2.max_time
            ):
                if entry2 in new_table.entries:
                    if not keep_entries or entry_count[entry.parent] > 1: #or v == entry2.parent:
                        new_table.entries.remove(entry2)
                        entry_count[entry.parent] -= 1
    table.entries = new_table.entries

# HYPOTHESIS:
# the only important weight change to consider is how much the expected delay
# of the outgoing edge with the SMALLEST expected delay changes
def process_edge_change(node: Node, edge: Edge, node_data: NodeData):
    old_edge = None
    for e in node_data.edges:
        if e.from_node == edge.from_node and e.to_node == edge.to_node:
            old_edge = deepcopy(e)
            e.expected_delay = edge.expected_delay
            break
    if old_edge is None:
        raise ValueError("Edge not found in node data")
    # iterate over all entries in the table
    new_entries = []
    removed_entries = []
    for entry in sorted(node_data.table.entries, key=lambda x: x.expected_time):
        if entry.parent == edge.to_node:
            removed_entries.append(entry)
            # update the entry
            new_entry = Entry(
                entry.max_time,
                edge.to_node,
                entry.expected_time + (edge.expected_delay - old_edge.expected_delay),
            )
            new_entries.append(new_entry)



    print(f"Node {node} old table {node_data.table}")
    old_smallest_expected_delay = min([x.expected_time for x in node_data.table.entries])
    for entry in removed_entries:
        node_data.table.entries.remove(entry)
    for entry in new_entries:
        node_data.table.entries.append(entry)
    reduce_table(node_data)
    print(f"Node {node} new table {node_data.table}")
    new_smallest_expected_delay = min([x.expected_time for x in node_data.table.entries])
    # already notify parents
    for parent_queue in node_data.parent_queues:
        parent_queue.put(
            NeighborUpdate(
                node, new_smallest_expected_delay - old_smallest_expected_delay
            )
        )

    return


def process_neighbor_update(node: Node, update: NeighborUpdate, node_data: NodeData):
    # find entry with smallest deadline >= update.deadline
    new_entries = []
    removed_entries = []
    old_smallest_expected_delay = min([x.expected_time for x in node_data.table.entries])
    min_expected_time_to_neighbor = 999999999
    first = True
    for entry in sorted(node_data.table.entries, key=lambda x: x.expected_time):
        if entry.parent == update.from_node:
            if first:
                first = False
                min_expected_time_to_neighbor = entry.expected_time + update.difference
                removed_entries.append(entry)
            new_entry = Entry(
                entry.max_time,
                entry.parent,
                max(min_expected_time_to_neighbor, entry.expected_time + update.difference),
            )
            new_entries.append(new_entry)
    print(f"Node {node} old table {node_data.table}")
    for entry in removed_entries:
        node_data.table.entries.remove(entry)
    for entry in new_entries:
        node_data.table.entries.append(entry)
    reduce_table(node_data)
    print(f"Node {node} new table {node_data.table}")
    new_smallest_expected_delay = min([x.expected_time for x in node_data.table.entries])
    # already notify parents
    for parent_queue in node_data.parent_queues:
        parent_queue.put(
            NeighborUpdate(
                node, new_smallest_expected_delay - old_smallest_expected_delay
            )
        )

    return


def node_loop(node: Node, node_data: NodeData, queue: mp.Queue, return_queue: mp.Queue) -> None:
    while True:
        received: Edge | NeighborUpdate | None = queue.get()
        if isinstance(received, NeighborUpdate):
            print(f"Node {node} received neighbor update {received}")
            # process neighbor update
            process_neighbor_update(node, received, node_data)
        elif isinstance(received, Edge):
            old_edge = None
            for e in node_data.edges:
                if e.from_node == received.from_node and e.to_node == received.to_node:
                    old_edge = deepcopy(e)
                    break
            print(f"Node {node} received edge change from {old_edge} to {received}")
            process_edge_change(node, received, node_data)
        elif received is None:
            print(f"Node {node} exiting")
            break
        return_queue.put(node_data)
    return


def randomly_modify_graph(graph: Graph) -> Graph:
    new_graph = deepcopy(graph)
    # pick one edge randomly_modify_graph
    edge = random.choice(list(new_graph.edges()))
    # modify the edge
    # modify expected delay only
    new_graph.modify_edge(
        edge.from_node,
        edge.to_node,
        (random.randint(1, edge.worst_case_delay), edge.worst_case_delay),
    )
    return new_graph

TIME_BETWEEN_UPDATES = 0.1
NUM_TIMES = 100
SEED = 105
def main():
    baruah_paper_graph = Graph(
        {
            1: {2: (4, 10), 4: (15, 25)},
            2: {3: (4, 10), 4: (12, 15)},
            3: {4: (4, 10)},
            4: {},
        }
    )

    initial_tables = original_baruah(baruah_paper_graph, 4, True)

    graph_list: List[Graph] = []
    g2 = deepcopy(baruah_paper_graph)
    g2.modify_edge(2, 3, (9, 10))
    graph_list.append(baruah_paper_graph)
    graph_list.append(g2)

    random.seed(SEED)
    for i in range(NUM_TIMES - 1):
        graph_list.append(randomly_modify_graph(graph_list[-1]))

    temporal_graph = TemporalGraph(graph_list)
    print(temporal_graph)
    print(initial_tables)

    # start loop for all nodes
    # use multiprocessing to parallelize the loop
    queues = {}
    return_queues = {}
    node_tables: Dict[Node, Table] = {}
    processes = {}
    for node in temporal_graph.at_time(0).nodes():
        manager = mp.Manager()
        queues[node] = manager.Queue()
        manager2 = mp.Manager()
        return_queues[node] = manager2.Queue()
    for node in temporal_graph.at_time(0).nodes():
        adjacent_queues = [
            queues[j] for j in temporal_graph.at_time(0).neighbor_of(node)
        ]
        data = NodeData(
            adjacent_queues,
            temporal_graph.at_time(0).outgoing_edges(node),
            initial_tables[node],
        )
        node_tables[node] = initial_tables[node]
        p = mp.Process(target=node_loop, args=(node, data, queues[node], return_queues[node],))
        processes[node] = p
        p.start()

    time = 0
    current_graph = temporal_graph.at_time(0)
    for i in range(len(temporal_graph) - 1):
        old_tables = original_baruah(temporal_graph.at_time(time), 4, True)
        time += 1
        print(f"Time {time}")
        new_tables = original_baruah(temporal_graph.at_time(time), 4, True)
        current_graph = temporal_graph.at_time(time)
        changed_edges = list(current_graph.edges() - temporal_graph.at_time(time - 1).edges())
        for edge in changed_edges:
            # only 1 edge is changed for now
            queues[edge.from_node].put(edge)


        sleep(TIME_BETWEEN_UPDATES)
        for i in current_graph.nodes():
            new_table = Table()

            try:
                new_table: Table = return_queues[i].get_nowait().table
            except:
                # print(f"Node {i} did not change")
                continue
            # check it matches baruah_paper_graph
            if node_tables[i] == old_tables[i]:
                print(f"Node {i} old table matches")
            else:

                print(f"Node {i} old table does not match!!!!!!!!!!!!!!!! {node_tables[i]} =/= {old_tables[i]}")
                print(f"Graph at time {time}\n{temporal_graph.at_time(time - 1)}")
                exit(1)
            node_tables[i] = new_table
            if node_tables[i] == new_tables[i]:
                print(f"Node {i} new table matches")
            else:
                print(f"Node {i} new table does not match!!!!!!!!!!!!!!!! {node_tables[i]} =/= {new_tables[i]}")
                print(f"Graph at time {time}\n{temporal_graph.at_time(time)}")
                exit(1)

        print("----Baruah's Answer----")
        if len(changed_edges) == 0:
            print("No edge changes")
        else:
            print(f"Old table {old_tables[changed_edges[0].from_node]}")
            print(f"New table {new_tables[changed_edges[0].from_node]}")
            print(f"-------Time {time} done-------")

    # join all processes
    for i in temporal_graph.at_time(0).nodes():
        queues[i].put(None)
        processes[i].join()

    print(initial_tables)
    return


if __name__ == "__main__":
    main()
