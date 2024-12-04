from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Mapping, Set

@dataclass
class Table:
    entries: List[Entry] = field(default_factory=list)

    def __len__(self):
        return len(self.entries)


@dataclass
class Node:
    label: str = "Node"
    table: Table = field(default_factory=Table)

    def get_outgoing_edges(self):
        edges = []
        for neighbor in self.neighbors:
            edges.append(Graph.edges[(self.label, neighbor.label)])
        return edges
    
    def get_incoming_edges(self):
        edges = []
        for neighbor in self.neighbors:
            edges.append(Graph.edges[(neighbor.label, self.label)])
        return


    # equals
    def __eq__(self, other):
        return self.label == other.label
    
    # hash
    def __hash__(self):
        return hash(self.label)
    
    def __str__(self):
        return f"Node {self.label}"


Tables = Dict[Node, Table]


@dataclass
class Edge:
    from_node: Node
    to_node: Node
    expected_delay: int
    worst_case_delay: int

    def get_other_side(self, label):
        return self.to_node if self.from_node.label == label else self.from_node
    
    # equals
    def __eq__(self, other):
        return self.from_node == other.from_node and self.to_node == other.to_node and self.expected_delay == other.expected_delay and self.worst_case_delay == other.worst_case_delay
    
    def __str__(self):
        return f"Edge {self.from_node.label} -({self.expected_delay}, {self.worst_case_delay})-> {self.to_node.label}"


@dataclass
class Entry:
    parent: Node | None
    max_time: int
    expected_time: int

    # equals
    def __eq__(self, other: Entry):
        return self.parent == other.parent and self.max_time == other.max_time and self.expected_time == other.expected_time
    
    # less than
    def __lt__(self, other):
        return self.expected_time < other.expected_time
    
    # hash
    def __hash__(self):
        return hash((self.parent, self.max_time, self.expected_time))
    
    def __str__(self):
        return f"Entry: {self.parent.label if self.parent else 'None'} {self.max_time} {self.expected_time}"
    
    def __repr__(self):
        return self.__str__()

@dataclass
class Graph:
    data: Dict[Node, List[Edge]] # Adjacency list with redundancy

    def __init__(self: Graph, adjacency_list: Mapping[Node, Mapping[Node, (int, int)]]) -> None:
        """
        Constructs a new graph.

        Maps a node to a map of neighboring nodes and (expected delay, worst case delay).
        """
        self.data = {}

        for (label, v) in adjacency_list.items():
            node = Node(label=label)
            self.data[node] = []
            for (other_label, (ed, wd)) in v.items():
                other_node = Node(label=other_label)
                self.data[node].append(Edge(node, other_node, ed, wd))

    def get_neighbors_of(self: Graph, node: Node) -> List[Node]:
        neighbors = []
        for edge in self.data[node]:
            neighbors.append(edge.to_node)
        return neighbors
    
    def get_nodes(self: Graph) -> List[Node]:
        return list(self.data.keys())
    
    def get_edges(self: Graph) -> List[Edge]:
        edges: Set[Edge] = set()
        for edge_list in self.data.values():
            for edge in edge_list:
                edges.add(edge)
        return list(edges)
        
    def get_outgoing_edges(self: Graph, node: Node) -> List[Edge]:
        return self.data[node]
    
    def __str__(self):
        result = ""
        for (node, edges) in self.data.items():
            result += f"{node}:\n"
            if len(edges) == 0:
                result += "    None\n"
            for edge in edges:
                result += f"    {edge}\n"

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
