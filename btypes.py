from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Tuple, Mapping, Set

class Table:
    entries: List[Entry]

    def __init__(self, entries=None) -> None:
        self.entries = entries or []

    def __iter__(self):
        return iter(self.entries)

    def __len__(self):
        return len(self.entries)

    def __str__(self) -> str:
        return str(self.entries)

    def insert(self, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with domination checks.
        """

        if entry.parent is None:
            self.entries.append(entry)
            return

        should_insert = True
        remove = []
        for existing_entry in self.entries:
            if existing_entry.max_time <= entry.max_time and existing_entry.expected_time <= entry.max_time:
                # entry is dominated by an existing entry
                should_insert = False
                break

            elif existing_entry.max_time >= entry.max_time and existing_entry.expected_time >= entry.expected_time:
                # entry dominates existing entry
                remove.append(existing_entry)
        
        for entry_to_remove in remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.append(entry)

    def insert_ppd(self, entry: Entry) -> None:
        """
        Inserts the `entry` in the `table` with per parent domination checks.
        
        If `entry` is not dominated by any entries that have the same parent it gets inserted and
        all entries that have the same parent and are dominated by `entry` get removed.
        """

        if entry.parent is None:
            self.entries.append(entry)
            return

        should_insert = True
        remove = []
        for existing_entry in self.entries:
            if existing_entry.parent != entry.parent:
                # only consider domination if existing entry has the same parent as entry
                continue

            if existing_entry.max_time <= entry.max_time and existing_entry.expected_time <= entry.expected_time:
                # entry is dominated by existing entry
                should_insert = False
                break

            if entry.max_time <= existing_entry.max_time and entry.expected_time <= existing_entry.expected_time:
                # entry dominates existing entry
                remove.append(existing_entry)

        for entry_to_remove in remove:
            self.entries.remove(entry_to_remove)
        
        if should_insert:
            self.entries.append(entry)


Node = int | str
Tables = Dict[Node, Table]

@dataclass
class Edge:
    from_node: Node
    to_node: Node
    expected_delay: int
    worst_case_delay: int

    def get_other_side(self, node):
        return self.to_node if self.from_node == node else self.from_node
    
    # equals
    def __eq__(self, other):
        return self.from_node == other.from_node and self.to_node == other.to_node and self.expected_delay == other.expected_delay and self.worst_case_delay == other.worst_case_delay
    
    def __str__(self):
        return f"Edge {self.from_node} -({self.expected_delay}, {self.worst_case_delay})-> {self.to_node}"
    
    def __hash__(self):
        return hash((self.from_node, self.to_node, self.expected_delay, self.worst_case_delay))


@dataclass
class Entry:
    max_time: int
    parent: Node | None
    expected_time: int

    # equals
    def __eq__(self, other):
        return hash(self) == hash(other) 
    
    # less than
    def __lt__(self, other):
        return hash(self) < hash(other)
    
    # hash
    def __hash__(self):
        return hash((self.parent, self.max_time, self.expected_time))
    
    def __str__(self):
        return f"Entry: {self.max_time} {self.parent} {self.expected_time}"
    
    def __repr__(self):
        return self.__str__()

@dataclass
class Graph:
    data: Dict[Node, Dict[Node, Tuple[int, int]]]

    def __init__(self: Graph, adjacency_list: Mapping[Node, Mapping[Node, Tuple[int, int]]]) -> None:
        """
        Constructs a new graph.

        Maps a node to a map of neighboring nodes and (expected delay, worst case delay).
        """
        self.data = {}

        for (node, v) in adjacency_list.items():
            self.data[node] = {}
            for (other_node, edge_weights) in v.items():
                self.data[node][other_node] = edge_weights

    def edge(self, u: Node, v: Node) -> Edge:
        weights = self.data[u][v]
        return Edge(u, v, *weights)

    def modify_edge(self, u:Node, v:Node, data: Tuple[int, int]):
        self.data[u][v] = data
    
    def nodes(self: Graph) -> List[Node]:
        return list(self.data.keys())
    
    def edges(self: Graph) -> Set[Edge]:
        edges: Set[Edge] = set()

        for (node, neighbors) in self.data.items():
            for (neighbor, weights) in neighbors.items():
                edges.add(Edge(node, neighbor, *weights))

        return edges

    def neighbors(self: Graph, node: Node) -> List[Node]:
        neighbors = []
        for neighbor in self.data[node].keys():
            neighbors.append(neighbor)

        return neighbors
    
    def neighbor_of(self: Graph, node: Node) -> List[Node]:
        neighborof = []
        for (n, edges) in self.data.items():
            if node in edges.keys():
                neighborof.append(n)
        return neighborof
        
    
    def outgoing_edges(self: Graph, node: Node) -> List[Edge]:
        edges = []
        for (node, neighbors) in self.data.items():
            for (neighbor, weights) in neighbors.items():
                edges.append(Edge(node, neighbor, *weights))
        return edges
    
    def incoming_edges(self: Graph, node: Node) -> List[Edge]:
        edges = []
        for (n, neighbors) in self.data.items():
            if node in neighbors.keys():
                edges.append(Edge(n, node, *neighbors[node]))
        return edges
    
    def __str__(self):
        result = ""
        for (node, neighbors) in self.data.items():
            result += f"{node}:\n"
            if len(neighbors) == 0:
                result += "    None\n"
            for (neighbor, weights) in neighbors.items():
                result += f"    -({weights[0]}, {weights[1]})-> {neighbor}\n"

        return result 
    
def test():
    G = Graph({
        1: {2: (4, 10), 4: (15, 25)},
        2: {3: (4, 10), 4: (12, 15)},
        3: {4: (4, 10)},
        4: {}
    })

    print(G)

@dataclass
class TemporalGraph:
    time_to_graph: List[Graph]

    def __len__(self):
        return len(self.time_to_graph)

    def __init__(self, graphs: List[Graph]):
        self.time_to_graph = graphs

    def at_time(self, t: int) -> Graph:
        return self.time_to_graph[t]
    
    def __str__(self):
        string = ""
        for i, graph in enumerate(self.time_to_graph):
            string += (f"Time {i}: {graph}\n")
        return string
