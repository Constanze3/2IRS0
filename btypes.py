from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

@dataclass
class Table:
    entries: List[Entry] = field(default_factory=list)

    def __len__(self):
        return len(self.entries)


@dataclass
class Node:
    neighbors: List[Node]
    label: str
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
        return f"Node: {self.label}"


Tables = Dict[Node, Table]


@dataclass
class Edge:
    from_node: Node
    to_node: Node
    expected_delay: int
    worse_case_delay: int

    def get_other_side(self, label):
        return self.to_node if self.from_node.label == label else self.from_node
    
    def __str__(self):
        return f"Edge: {self.from_node.label} -> {self.to_node.label} {self.expected_delay} {self.worse_case_delay}"


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
    nodes: Dict[str, Node]
    edges: Dict[Tuple[str, str], Edge]

    def __str__(self):
        nodes = [str(node) for node in self.nodes.values()]
        edges = [str(edge) for edge in self.edges.values()]
        
        return f"Graph: {nodes} {edges}"


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
