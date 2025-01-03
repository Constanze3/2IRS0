from __future__ import annotations
from typing import List, Tuple, Dict, Mapping, Set

Node = int | str

class Edge:
    from_node: Node
    to_node: Node
    expected_delay: int
    worst_case_delay: int

    def __init__(self: Edge, from_node: Node, to_node: Node, expected_delay: int, worst_case_delay: int):
        self.from_node = from_node
        self.to_node = to_node
        self.expected_delay = expected_delay
        self.worst_case_delay = worst_case_delay

    def other_side(self: Edge, node: Node) -> Node:
        """
        Provided with the from/to node of an edge returns the node at the opposite side of the edge. 
        """
        if self.from_node == node:
            return self.to_node
        elif self.to_node == node:
            return self.from_node
        else:
            raise ValueError("node should be either the from_node or to_node of the edge")
        
    def __eq__(self: Edge, other: object):
        if type(other) == Edge:
            result = True
            result &= self.from_node == other.from_node
            result &= self.to_node == other.to_node
            result &= self.expected_delay == other.expected_delay
            result &= self.worst_case_delay == other.worst_case_delay
            return result
        else:
            return False
    
    def __str__(self: Edge):
        return f"Edge {self.from_node} -({self.expected_delay}, {self.worst_case_delay})-> {self.to_node}"
    
    def __repr__(self: Edge):
        return str(self)
    
    def __hash__(self: Edge):
        return hash((self.from_node, self.to_node, self.expected_delay, self.worst_case_delay))

class Graph:
    data: Dict[Node, Dict[Node, Tuple[int, int]]]

    def __init__(self: Graph, adjacency_list: Mapping[Node, Mapping[Node, Tuple[int, int]]]):
        """
        Constructs a new graph.

        The graph maps a node to its neighboring nodes and their respective
        edge weights (expected delay, worst-case delay).
        """
        self.data = {}

        for (u, edges) in adjacency_list.items():
            self.data[u] = {}
            for (v, edge_weights) in edges.items():
                self.data[u][v] = edge_weights

    def edge(self: Graph, u: Node, v: Node) -> Edge:
        weights = self.data[u][v]
        return Edge(u, v, *weights)

    def modify_edge_weights(
        self: Graph, 
        u: Node, 
        v: Node, 
        new_expected_delay: int | None = None, 
        new_worst_case_delay: int | None = None
    ):
        (current_expected_delay, current_worst_case_delay) = self.data[u][v]

        if new_expected_delay == None:
            new_expected_delay = current_expected_delay
        if new_worst_case_delay == None:
            new_worst_case_delay = current_worst_case_delay

        self.data[u][v] = (new_expected_delay, new_worst_case_delay)
    
    def nodes(self: Graph) -> List[Node]:
        return list(self.data.keys())
    
    def edges(self: Graph) -> Set[Edge]:
        edges: Set[Edge] = set()

        for (node, neighbors) in self.data.items():
            for (neighbor, weights) in neighbors.items():
                edges.add(Edge(node, neighbor, *weights))

        return edges

    def successors(self: Graph, node: Node) -> List[Node]:
        neighbors = []
        for neighbor in self.data[node].keys():
            neighbors.append(neighbor)

        return neighbors
    
    def predecessors(self: Graph, node: Node) -> List[Node]:
        result = []
        for (u, edges) in self.data.items():
            if node in edges.keys():
                result.append(u)
        return result
        
    
    def outgoing_edges(self: Graph, node: Node) -> List[Edge]:
        result = []
        for (node, edges) in self.data.items():
            for (v, weights) in edges.items():
                result.append(Edge(node, v, *weights))
        return result
    
    def incoming_edges(self: Graph, node: Node) -> List[Edge]:
        result = []
        for (u, edges) in self.data.items():
            if node in edges.keys():
                result.append(Edge(u, node, *edges[node]))
        return result
    
    def __str__(self: Graph):
        result = ""
        for (u, edges) in self.data.items():
            result += f"{u}:\n"
            if len(edges) == 0:
                result += "    None\n"
            for (v, weights) in edges.items():
                result += f"    -({weights[0]}, {weights[1]})-> {v}\n"

        return result 

class Entry:
    max_time: int
    parents: List[Node]
    expected_time: int

    def __init__(self: Entry, max_time: int, parents: List[Node], expected_time: int):
        self.max_time = max_time
        self.parents = parents
        self.expected_time = expected_time

    def parent(self: Entry) -> Node | None:
        if 0 < len(self.parents):
            return self.parents[0]
        else:
            return None
        
    def dominates(self: Entry, other: Entry) -> bool:
        return self.max_time <= other.max_time and self.expected_time <= other.expected_time

    def strictly_dominates(self: Entry, other: Entry) -> bool:
        if self.max_time < other.max_time and self.expected_time <= other.expected_time:
            return True
        
        if self.max_time == other.max_time and self.expected_time < other.expected_time:
            return True

        return False
    
    def equivalent(self: Entry, other: Entry) -> bool:
        """
        Checks whether an entry has the same max time and expected time as an `other` entry.
        """
        return self.max_time == other.max_time and self.expected_time == other.expected_time

    def __eq__(self: Entry, other: object):
        if type(other) == Entry:
            result = True
            result &= self.max_time == other.max_time
            result &= self.parents == other.parents
            result &= self.expected_time == other.expected_time
            return result
        else:
            return False
    
    def __hash__(self: Entry):
        return hash((self.max_time, self.parent(), self.expected_time))
    
    def __str__(self: Entry):
        return f"Entry: {self.max_time} {self.parents} {self.expected_time}"
    
    def __repr__(self):
        return str(self)
    
class Table:
    entries: Set[Entry]

    def __init__(self: Table, entries: Set | None = None) -> None:
        self.entries = entries or set()

    def insert_d(self: Table, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with domination checks.
        """
        should_insert = True
        to_remove = []

        for existing_entry in self.entries:
            if existing_entry.dominates(entry):
                should_insert = False
                break
            elif entry.dominates(existing_entry):
                to_remove.append(existing_entry)
                    
        for entry_to_remove in to_remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.add(entry)

    def insert_sd(self: Table, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with strict dominaion checks.
        """
        should_insert = True
        to_remove = []

        for existing_entry in self.entries:
            if existing_entry.strictly_dominates(entry):
                should_insert = False
                break
            elif entry.strictly_dominates(existing_entry):
                to_remove.append(existing_entry)
                    
        for entry_to_remove in to_remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.add(entry)

    def insert_ppd(self: Table, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with per parent domination checks.
        
        If `entry` is not dominated by any entries that have the same parent it gets inserted and
        all entries that have the same parent and are dominated by `entry` get removed.
        """

        should_insert = True
        to_remove = []
        for existing_entry in self.entries:
            if existing_entry.parent() != None and entry.parent() != None and existing_entry.parent() != entry.parent():
                # only consider domination if existing entry has the same parent as entry
                continue
            
            # may be necessary, not sure
            if existing_entry.equivalent(entry):
               break

            if existing_entry.dominates(entry):
                should_insert = False
                break
            elif entry.dominates(existing_entry):
                to_remove.append(existing_entry)

        for entry_to_remove in to_remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.add(entry)

    def remove_all_entries_with_parent(self: Table, parent: Node):
        to_remove = []
        for entry in self.entries:
            if entry.parent() == parent:
                to_remove.append(entry)

        for entry_to_remove in to_remove:
            self.entries.remove(entry_to_remove)

    def __iter__(self: Table):
        return iter(self.entries)

    def __len__(self: Table):
        return len(self.entries)

    def __str__(self: Table):
        return str(self.entries)
    
    def __repr__(self: Table):
        return str(self)
    
    def __eq__(self: Table, other: object):
        if type(other) == Table:
            return self.entries == other.entries
        else:
            return False
    
class TableDiff:
    removed: Set[Entry]
    added: Set[Entry]

    def __init__(self, old_table: Table, new_table: Table) -> None:
        self.removed = old_table.entries - new_table.entries
        self.added = new_table.entries - old_table.entries

    def apply(self: TableDiff, table: Table):
        for removed_entry in self.removed:
            if removed_entry in table.entries:
                table.entries.remove(removed_entry)
        
        for added_entry in self.added:
            table.entries.add(added_entry)

    
    def __len__(self):
        return len(self.removed) + len(self.added)

    def __eq__(self, other: object):
        if type(other) == TableDiff:
            return self.removed == other.removed and self.added == other.added
        else:
            return False
    
    def __str__(self):
        return f"(removed: {self.removed}, added: {self.added})"
    
    def __repr__(self):
        return str(self) 
