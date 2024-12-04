from btypes import Graph, Node, Edge, Entry, Tables, Table
from typing import List, Mapping
from copy import deepcopy
import math


class TableDiff:
    def __init__(self, removed: List[Entry], added: List[Entry]) -> None:
       self.removed = removed
       self.added = added
    
    def __len__(self):
        return len(self.removed) + len(self.added)

def insert_into_table(table: Table, node: Node, entry: Entry):
    """
    If the provided `entry` is not dominated by entries in the `table` of a `node` it inserts it into `table`
    and removes all entries dominated by `entry`, but keeping at least one entry for each neighbor.
    """

    entry_count = {}
    for neighbor in node.neighbors:
        entry_count[neighbor] = 0
    for existing_entry in table.entries:
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
        table.entries.remove(entry_to_remove)
    
    if insert:
        table.entries.append(entry)


def algorithm(graph: Graph, tab: Tables, e: Edge, value: float) -> Mapping[Node, TableDiff]:
    changes: Mapping[Node, TableDiff] = {}

    for node in graph.nodes:
        changes[node] = TableDiff([], [])

    start = e.from_node
    edge_change = value - e.expected_delay

    # no change
    if edge_change == 0:
        return changes

    increment = edge_change > 0

    # determine changes in the start node's table
    for entry in tab[start].entries:
        if entry.parent == e.to_node:
            new_entry = deepcopy(entry)
            new_entry.expected_time += edge_change

            changes[start] = TableDiff(new_entry, deepcopy(entry))

    queue: List[Node] = []
    queue.append(start)

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
            insert_into_table(new_tab_v, v, added_entry)
        
        for u in graph.nodes:
            edge = graph.edges[(u, v)]

            new_tab_u = Table()

            may_create = [True] * len(changes[v].added)
            dominates_some_feasible = [False] * len(changes[v].added)

            for entry_u in tab[u].entries:
                # consider only entries that lead to v
                if v != entry_u.parent:
                    continue

                # determine feasible entries with minimum typical time
                d_min = entry_u.max_time - edge.worse_case_delay
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
 
                insert_into_table(new_tab_u, u, associated_entry)

            if not increment:
                for (index, added_entry) in enumerate(changes[v].added):
                    if may_create[index] and dominates_some_feasible[index]:
                        d_min = edge.worse_case_delay + min([entry.max_time for entry in new_tab_v.entries])
                        d = max(d_min, edge.expected_delay + added_entry.max_time)
                        de = edge.expected_delay + added_entry.expected_time

                        new_entry = Entry(d, v, de)
                        insert_into_table(new_tab_u, u, new_entry)
            
            diff = difference(tab[u], new_tab_u)
            changes[u] = diff
            
            if len(diff) > 0:
                queue.append(u)

def test_algorithm():
    G = Graph()
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
    

def test_insert_into_table():
    table = Table()

    a = Node(label="a", neighbors=[], edges=[])
    b = Node(label="b", neighbors=[], edges=[])
    c = Node(label="c", neighbors=[], edges=[])
    v = Node(label="v", neighbors=[a, b, c], edges=[])

    e1 = Entry(a, 10, 19)
    e2 = Entry(b, 20, 19)
    e3 = Entry(b, 12, 19)
    e4 = Entry(b, 5, 39)

    insert_into_table(table, v, e1)
    insert_into_table(table, v, e2)
    insert_into_table(table, v, e3)
    insert_into_table(table, v, e4)

    expected = [e1, e3, e4]
    expected.sort()

    actual = table.entries
    actual.sort()

    assert(expected == actual)


if __name__ == "__main__":
    test_insert_into_table()