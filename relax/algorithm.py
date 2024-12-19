from baruah_modified import original_baruah
from btypes import Graph, Node, Entry, Tables, Table
from typing import List, Mapping, Dict, Tuple, Set
from copy import deepcopy
import random
import math

class TableDiff:
    def __init__(self, removed: Set[Entry] | None = None, added: Set[Entry] | None = None) -> None:
        self.removed = removed or set()
        self.added = added or set()
    
    def __len__(self):
        return len(self.removed) + len(self.added)

    def __eq__(self, other):
        return self.removed == other.removed and self.added == other.added
    
    def __str__(self):
        return f"removed: {self.removed}, added: {self.added}"
    
    def __repr__(self):
        return self.__str__()

    def __ior__(self, other):
        return TableDiff(self.removed | other.removed, self.added | other.added)

    
def difference(old_table: Table, new_table: Table) -> TableDiff:
    """
    Finds for each table the difference between old and new table.

    It returns for a table what are entries that were removed and what are entreis
    that were added to the old table to get to the new table.
    """

    old_entries = sorted(old_table.entries)
    new_entries = sorted(new_table.entries)

    # entries in old table that were removed to get to the new table
    removed: Set[Entry] = set()
    # entries in new table that were an addition to the entries of old table
    added: Set[Entry] = set()

    index_old = 0
    index_new = 0

    while(True):
        if len(old_entries) <= index_old and len(new_entries) <= index_new:
            # no more entries to consider
            break

        if len(old_entries) <= index_old:
            entry_new = new_entries[index_new]
            # entry_new only exists in the new table -> it was added
            added.add(entry_new)
            index_new += 1
            continue

        if len(new_entries) <= index_new:
            entry_old = old_entries[index_old]
            # entry_old only exist in the old table -> it was removed
            removed.add(entry_old)
            index_old += 1
            continue
        
        # at this point: index_old < len(old_table) and index_new < len(new_table) 

        entry_old = old_entries[index_old]
        entry_new = new_entries[index_new]

        if entry_old == entry_new:
            # entry exists in both tables -> not a change
            index_new += 1
            index_old += 1
            continue

        if entry_old < entry_new:
            # entry_old was "skipped over" in new table, the table is sorted -> the new table doesn't contain it -> it was removed
            removed.add(entry_old)
            index_old += 1
            continue
        
        if entry_new < entry_old:
            # entry_new was "skipped over" in old table, the table is sorted -> the old table doesn't contain it -> it was added
            added.add(entry_new)
            index_new += 1
            continue
    
    return TableDiff(removed, added)

    
def algorithm(G: Graph, u: Node, v:Node):
    v_node = G.nodes_obj[v]
    v_node.propogate([v], u, [])

def difference_tables(old_tables: Tables, new_tables: Tables)-> Dict[Node, TableDiff]:
    """
    Return a map, for each node return the difference.
    """
    output_differences = {}
    for (u, old_table) in old_tables.items(): 
        output_differences[u] = difference(old_table, new_tables[u])
    return output_differences

def construct_tables(graph) -> Tables:
    return dict((node, node_obj.routing_table) for node, node_obj in graph.nodes_obj.items())

def test_algorithm(name: str, graph: Graph, destination: Node, edge: Tuple[Node, Node], change: Tuple[int, int]):
    old_tables = original_baruah(graph, destination, True)
    (u, v) = edge
    graph.modify_edge(u, v, change)
    algorithm(graph, u, v)
    new_tables = original_baruah(graph, destination, True)
    expected_changes = difference_tables(old_tables, new_tables)
    actual_tables = construct_tables(graph)
    actual_changes = difference_tables(old_tables, actual_tables)

    print(f"--- {name} ---");
    print()

    show_debug = False

    if actual_changes != expected_changes:
        print("FAIL")
        print(actual_changes)
        print(expected_changes)
    else:
        print("PASS")
    print()


def dense_test():
    g1 = Graph({
        1: {2: (4, 10), 4: (15, 25)},
        2: {3: (4, 10), 4: (12, 15)},
        3: {4: (4, 10)},
        4: {}
    })
    test_algorithm("test1", g1, 4, (1, 2), 9)
    test_algorithm("test2", g1, 4, (1, 4), 1)
    test_algorithm("test3", g1, 4, (2, 3), 5)
    test_algorithm("test4", g1, 4, (3, 4), 10)
    test_algorithm("test5", g1, 4, (3, 4), 1)

    g2 = Graph({
        1: {2: (5, 12), 3: (8, 20)},
        2: {3: (3, 8), 4: (10, 18), 5: (7, 15)},
        3: {4: (6, 10), 5: (9, 20)},
        4: {5: (2, 5), 6: (8, 16)},
        5: {6: (4, 10)},
        6: {}
    })
    test_algorithm("test6", g2, 4, (5, 6), 1)
    test_algorithm("test7", g2, 4, (1, 3), 11)

    g3 = Graph({
        1: {2: (3, 7), 4: (12, 25)},
        2: {3: (4, 10)},
        3: {},
        4: {5: (7, 18)},
        5: {}
    })
    test_algorithm("test8", g3, 4, (4, 5), 17)
    test_algorithm("test9", g3, 4, (4, 5), 1)

    g4 = Graph({
        1: {2: (4, 8), 3: (6, 15)},
        2: {3: (5, 12), 4: (3, 7)},
        3: {4: (4, 10), 1: (8, 20)},
        4: {1: (2, 6), 2: (3, 9)}
    })
    test_algorithm("test10", g4, 4, (1, 3), 14)
    test_algorithm("test11", g4, 4, (2, 4), 4)

    g5 = Graph({
        1: {2: (3, 9), 3: (5, 15), 4: (7, 18)},
        2: {3: (4, 10), 4: (6, 14), 5: (8, 20)},
        3: {4: (3, 7), 5: (5, 12), 6: (9, 18)},
        4: {5: (2, 6), 6: (4, 10), 7: (10, 25)},
        5: {6: (3, 8), 7: (7, 16)},
        6: {7: (6, 12)},
        7: {}
    })
    test_algorithm("test12", g5, 4, (1, 4), 17)
    test_algorithm("test13", g5, 4, (6, 7), 11)
    test_algorithm("test14", g5, 4, (6, 7), 1)
    test_algorithm("test15", g5, 4, (3, 6), 1)
    test_algorithm("test16", g5, 4, (4, 6), 17)

    g6 = Graph({
        1: {2: (3, 7), 3: (4, 8), 4: (5, 10)},
        2: {1: (3, 7), 3: (2, 6), 4: (4, 9)},
        3: {1: (4, 8), 2: (2, 6), 4: (3, 7)},
        4: {1: (5, 10), 2: (4, 9), 3: (3, 7)}
    })
    test_algorithm("test20", g6, 4, (3, 1), 1)


    test_algorithm("test17", g6, 4, (1, 4), 7)
    test_algorithm("test18", g6, 4, (2, 4), 8)
    test_algorithm("test19", g6, 4, (2, 4), 1)
    test_algorithm("test20", g6, 4, (3, 1), 1)
    test_algorithm("test21", g6, 4, (3, 1), 7)
    test_algorithm("test22", g6, 4, (4, 1), 2)
    test_algorithm("test23", g6, 4, (4, 2), 8)
    
def draw_graph(graph: Graph):
    import networkx as nx
    import matplotlib.pyplot as plt

    nx_graph = nx.DiGraph()

    for node in graph.nodes():
        nx_graph.add_node(node)

    for edge in graph.edges():
        nx_graph.add_edge(
            edge.from_node, 
            edge.to_node, 
            expected_delay=edge.expected_delay, 
            worst_case_delay=edge.worst_case_delay
        )

    pos = nx.spring_layout(nx_graph)

    colors = ["b"] * len(nx_graph.edges())
    nx.draw_networkx(nx_graph, pos, with_labels=True, edge_color=colors)
    nx.draw_networkx_edge_labels(nx_graph, pos, edge_labels=nx.get_edge_attributes(nx_graph, "expected_delay"), label_pos=0.3)
    nx.draw_networkx_edge_labels(nx_graph, pos, edge_labels=nx.get_edge_attributes(nx_graph, "worst_case_delay"), font_color="red", label_pos=0.4)

    plt.show()


def single_test():
    g = Graph({
        1: {2: (2, 5)},
        2: {3: (3, 12), 4: (7, 12)},
        3: {4: (4, 12)},
        4: {}
    })
    test_algorithm("single test", g, 4, (3, 4), 3)
    # draw_graph(g)

def random_test(num_tests=1000, min_nodes=5, max_nodes=15, max_delay=20):
    def random_delay():
        typical = random.randint(1, max_delay-1)
        return (typical, random.randint(typical + 1, max_delay))

    for i in range(num_tests):
        nodes = [x for x in range(random.randint(min_nodes, max_nodes))] # create the nodes
        graph = dict((x, {y: random_delay()}) for x, y in zip(nodes, nodes[1:])) # turn the path into a dictionary
        n = len(nodes) # get the number of nodes
        biggest_node = n - 1
        graph[biggest_node] = {} # the last edge does not go anywhere afterwards

        for x in range(random.randint(0, n*(n-1))): # create a random number of edges. n(n-1) is the maximum number of edges
            from_node = random.randint(0, biggest_node)
            to_node = random.randint(0, biggest_node)
            while to_node == from_node: # makes sure that the to node and the from node are not the same
                to_node = random.randint(0, biggest_node)
            graph[from_node][to_node] = random_delay() # currently has an issue of accidentally overriding previous edges. But oh well.

        g = Graph(graph)
        from_node = random.randint(0,biggest_node) # select a random node
        while len(graph[from_node].keys()) == 0: # make sure that the node has out going edges. (might not always be the case that the node has outgoing edges)
            from_node = random.randint(0,biggest_node) # select a random node
        to_node = random.choice(list(graph[from_node].keys())) # select one of its edges
        edge = g.edge(from_node, to_node)
        new_delay = random.randint(1, edge.worst_case_delay)
        test_algorithm(f"test {i}", g, biggest_node, (from_node, to_node), (new_delay, edge.worst_case_delay))

if __name__ == "__main__":
    random_test(num_tests=3, min_nodes=3, max_nodes=3)
    # g = Graph({
    #     0: {1: (6, 20), 4: (5, 19), 2: (13, 18), 5: (11, 17)}, 
    #     1: {2: (15, 16), 3: (6, 7)}, 
    #     2: {3: (16, 19), 0: (11, 17), 5: (10, 19)}, 
    #     3: {4: (19, 20), 2: (3, 18), 5: (14, 15)}, 
    #     4: {5: (13, 14), 1: (19, 20)}, 
    #     5: {0: (4, 12)}
    # })
    # test_algorithm("test", g, 5, (1, 3), (4, 7))
    # dense_test()
    # single_test()
