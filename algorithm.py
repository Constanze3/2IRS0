from baruah_modified import original_baruah
from btypes import Graph, Node, Edge, Entry, Tables, Table
from typing import List, Mapping, Dict
from copy import deepcopy
import math

class TableDiff:
    def __init__(self, removed: List[Entry], added: List[Entry]) -> None:
       self.removed = removed
       self.added = added
    
    def __len__(self):
        return len(self.removed) + len(self.added)

    def __eq__(self, other):
        return self.removed == other.removed and self.added == other.added
    
    def __str__(self):
        return f"removed: {self.removed}, added: {self.added}"
    
    def __repr__(self):
        return self.__str__()
    
def difference(old_table: Table, new_table: Table) -> TableDiff:
    """
    Finds for each table the difference between old and new table.

    It returns for a table what are entries that were removed and what are entreis
    that were added to the old table to get to the new table.
    """

    old_entries = sorted(old_table.entries)
    new_entries = sorted(new_table.entries)

    # entries in old table that were removed to get to the new table
    removed = []
    # entries in new table that were an addition to the entries of old table
    added = []

    index_old = 0
    index_new = 0

    while(True):
        if len(old_entries) <= index_old and len(new_entries) <= index_new:
            # no more entries to consider
            break

        if len(old_entries) <= index_old:
            entry_new = new_entries[index_new]
            # entry_new only exists in the new table -> it was added
            added.append(entry_new)
            index_new += 1
            continue

        if len(new_entries) <= index_new:
            entry_old = old_entries[index_old]
            # entry_old only exist in the old table -> it was removed
            removed.append(entry_old)
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
            removed.append(entry_old)
            index_old += 1
            continue
        
        if entry_new < entry_old:
            # entry_new was "skipped over" in old table, the table is sorted -> the old table doesn't contain it -> it was added
            added.append(entry_new)
            index_new += 1
            continue
    
    return TableDiff(removed, added)

def insert_into_table(table: Table, graph: Graph, node: Node, entry: Entry):
    """
    If the provided `entry` is not dominated by entries in the `table` of a `node` it inserts it into `table`
    and removes all entries dominated by `entry`, but keeping at least one entry for each neighbor.
    """

    if entry.parent is None:
        table.entries.append(entry)
        return

    entry_count = {}
    for neighbor in graph.neighbors(node):
        entry_count[neighbor] = 0
    for existing_entry in table.entries:
        if existing_entry.parent != None:
            entry_count[existing_entry.parent] += 1

    # if there is no entry for such neighbor it is definitely inserted
    if entry_count[entry.parent] == 0:
        table.entries.append(entry)
        return
    
    insert = True
    remove = []
    for existing_entry in table.entries:
        if existing_entry.max_time <= entry.max_time and existing_entry.expected_time <= entry.max_time:
            # entry is dominated by an existing entry
            insert = False
            break

        if entry.max_time <= existing_entry.max_time and entry.expected_time <= existing_entry.expected_time:
            # entry dominates existing entry
            if 1 < entry_count[existing_entry.parent] or entry.parent == existing_entry.parent:
                remove.append(existing_entry)
    
    for entry_to_remove in remove:
        print(entry_count[entry_to_remove.parent])
        print(entry_to_remove)
        table.entries.remove(entry_to_remove)
    
    if insert:
        table.entries.append(entry)


def algorithm(graph: Graph, tab: Tables, e: Edge, value: int) -> Dict[Node, TableDiff]:
    changes: Mapping[Node, TableDiff] = {}

    for node in graph.nodes():
        changes[node] = TableDiff([], [])

    start_node = e.from_node
    edge_change = value - e.expected_delay

    # no change
    if edge_change == 0:
        return changes

    increment = edge_change > 0

    # determine changes in the start node's table
    new_start_node_table = Table()

    for entry in tab[start_node].entries:
        if entry.parent == e.to_node:
            new_entry: Entry = deepcopy(entry)
            new_entry.expected_time += edge_change
            insert_into_table(new_start_node_table, graph, start_node, new_entry)
        else:
            insert_into_table(new_start_node_table, graph, start_node, entry)

    changes[start_node] = difference(tab[start_node], new_start_node_table)

    print(changes)
    print()

    queue: List[Node] = []
    queue.append(start_node)

    explored = []
    explored.append(start_node)

    # nodes have access to their neighbor's:
    # tab[neighbor]
    # changes[neighbor]

    while queue:
        v = queue.pop(0)

        # reconstruct the new table of v from the changes
        new_tab_v = deepcopy(tab[v])
        for removed_entry in changes[v].removed:
            new_tab_v.entries.remove(removed_entry)
        for added_entry in changes[v].added:
            insert_into_table(new_tab_v, graph, v, added_entry)
        
        for u in graph.neighbor_of(v):
            if u in explored:
                continue

            explored.append(u)
            new_tab_u = Table()

            edge = graph.edge(u, v)

            may_create = [True] * len(changes[v].added)
            dominates_some_feasible = [False] * len(changes[v].added)

            for entry_u in tab[u].entries:
                # consider only entries that lead to v
                if v != entry_u.parent:
                    insert_into_table(new_tab_u, graph, u, entry_u)
                    continue

                # determine feasible entries with minimum typical time
                d_min = entry_u.max_time - edge.worst_case_delay
                d_max = entry_u.max_time - edge.expected_delay
                
                min_de_v = math.inf
                min_feasible_entries: List[Entry] = []

                max_de_v = -math.inf

                for entry_v in new_tab_v.entries:
                    d_v = entry_v.max_time
                    de_v = entry_v.expected_time

                    if d_min <= d_v and d_v <= d_max:
                        # entry is feasible

                        if entry_v in changes[v].added:
                            index = changes[v].added.index(entry_v)
                            may_create[index] = False

                        if de_v == min_de_v:
                            min_feasible_entries.append(entry_v)
                        elif de_v < min_de_v:
                            min_de_v = de_v
                            min_feasible_entries.clear()
                            min_feasible_entries.append(entry_v)

                        if max_de_v < de_v:
                            max_de_v = de_v

                for (index, added_entry) in enumerate(changes[v].added):
                    if added_entry.expected_time < max_de_v:
                        dominates_some_feasible[index] = True
                    
                # define associated entry in u
                associated_entry = deepcopy(entry_u)
                associated_entry.expected_time = min_feasible_entries[0].expected_time + edge.expected_delay
 
                insert_into_table(new_tab_u, graph, u, associated_entry)

            if not increment:
                for (index, added_entry) in enumerate(changes[v].added):
                    if may_create[index] and dominates_some_feasible[index]:
                        d_min = edge.worst_case_delay + min([entry.max_time for entry in new_tab_v.entries])
                        d = max(d_min, edge.expected_delay + added_entry.max_time)
                        de = edge.expected_delay + added_entry.expected_time

                        new_entry = Entry(d, v, de)
                        insert_into_table(new_tab_u, graph, u, new_entry)
            
            diff = difference(tab[u], new_tab_u)
            changes[u] = diff

            print(changes)
            print()
            
            if len(diff) > 0:
                queue.append(u)

    return changes

def difference_tables(old_tables: Tables, new_tables: Tables)-> Dict[Node, TableDiff]:
    # return a map, for each node return the difference
    output_differences = {}
    for (u, old_table) in old_tables.items(): 
        output_differences[u] = difference(old_table, new_tables[u])
    return output_differences

def test_on_graph(G, edge, new_delay):
    tables = original_baruah(G, 4, True)

    #note that algorithm takes the old graph, not the graph after it has
    changes = algorithm(G, tables, G.edge(*edge), new_delay)
    G.modify_edge(*edge, (new_delay, G.edge(*edge).worst_case_delay))
    print("old tables: ")
    for node, table in tables.items():
        print(f"{node}: {table}")

    # changed_entries = determine_changed_entries(G, 4, tables)
    # print(changed_entries.on_increment)
    new_tables = original_baruah(G, 4, True)
    print("\nnew tables: ")
    for node, table in new_tables.items():
        print(f"{node}: {table}")

    print("\n---running test case---")
    baruah_differences = difference_tables(tables, new_tables)
    for node, changes in changes.items():
        b_changes = baruah_differences[node]
        # assert(changes == b_changes)
        print(f"Entry for node: {node}")
        # if changes != b_changes:
        #     print(f"added too much {[x for x in changes.added if x not in b_changes.added]}")
        #     print(f"did not add {[x for x in b_changes.added if x not in changes.added]}")
        #     print(f"removed too much {[x for x in b_changes.added if x not in changes.added]}")
        #     print(f"did not remove {[x for x in b_changes.removed if x not in changes.removed]}")
        print(f"algo changes: {changes}")
        print(f"baruah changes: {b_changes}")
        print(f"------PASS: {changes == b_changes}------\n")

def test_algorithm():
    G = Graph({
        1: {2: (4, 10), 4: (15, 25)},
        2: {3: (4, 10), 4: (12, 15)},
        3: {4: (4, 10)},
        4: {}
    })
    test_on_graph(G, (2, 3), 5)


def dense_test():
    test_counter = 1
    G = Graph({
        1: {2: (4, 10), 4: (15, 25)},
        2: {3: (4, 10), 4: (12, 15)},
        3: {4: (4, 10)},
        4: {}
    })
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G, (1, 2), 9)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G, (1, 4), 1)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G, (2, 3), 5)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G, (3, 4), 10)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G, (3, 4), 1)

    G1 = Graph({
        1: {2: (5, 12), 3: (8, 20)},
        2: {3: (3, 8), 4: (10, 18), 5: (7, 15)},
        3: {4: (6, 10), 5: (9, 20)},
        4: {5: (2, 5), 6: (8, 16)},
        5: {6: (4, 10)},
        6: {}
    })
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G1, (5, 6), 1)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G1, (1, 3), 11)

    G2 = Graph({
        1: {2: (3, 7), 4: (12, 25)},
        2: {3: (4, 10)},
        3: {},
        4: {5: (7, 18)},
        5: {}
    })
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G2, (4, 5), 17)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G2, (4, 5), 1)

    G3 = Graph({
        1: {2: (4, 8), 3: (6, 15)},
        2: {3: (5, 12), 4: (3, 7)},
        3: {4: (4, 10), 1: (8, 20)},
        4: {1: (2, 6), 2: (3, 9)}
    })
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G3, (1, 3), 14)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G3, (2, 4), 4)
    

    G4 = Graph({
        1: {2: (3, 9), 3: (5, 15), 4: (7, 18)},
        2: {3: (4, 10), 4: (6, 14), 5: (8, 20)},
        3: {4: (3, 7), 5: (5, 12), 6: (9, 18)},
        4: {5: (2, 6), 6: (4, 10), 7: (10, 25)},
        5: {6: (3, 8), 7: (7, 16)},
        6: {7: (6, 12)},
        7: {}
    })
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G4, (1, 4), 17)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G4, (6, 7), 11)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G4, (6, 7), 1)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G4, (3, 6), 1)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G4, (3, 6), 17)

    G5 = Graph({
        1: {2: (3, 7), 3: (4, 8), 4: (5, 10)},
        2: {1: (3, 7), 3: (2, 6), 4: (4, 9)},
        3: {1: (4, 8), 2: (2, 6), 4: (3, 7)},
        4: {1: (5, 10), 2: (4, 9), 3: (3, 7)}
    })

    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (1, 4), 7)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (2, 4), 8)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (2, 4), 1)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (3, 1), 1)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (3, 1), 7)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (4, 1), 2)
    print(f"--- Test {test_counter} ---"); test_counter += 1
    test_on_graph(G5, (4, 2), 8)

    # for node, diff in difference(tables, new_tables).items():
    #     print(f"from {node} removed {diff.removed}")

def test_insert_into_table():
    table = Table()
    
    graph = Graph({
        1: { 2: (4, 20), 3: (5, 20) },
        2: {},
        3: {}
    })

    e1 = Entry(10, 2, 19)
    e2 = Entry(20, 2, 19)
    e3 = Entry(12, 3, 19)
    e4 = Entry(5, 3,  39)

    insert_into_table(table, graph, 1, e1)
    insert_into_table(table, graph, 1, e2)
    insert_into_table(table, graph, 1, e3)
    insert_into_table(table, graph, 1, e4)

    expected = [e1, e3, e4]
    expected.sort()

    actual = table.entries
    actual.sort()

    print(expected)
    print(actual)

    assert(expected == actual)


if __name__ == "__main__":
    # test_algorithm()
    dense_test()
