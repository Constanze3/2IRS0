from __future__ import annotations

from dataclasses import dataclass, field
import typing as t
from enum import Enum


@dataclass
class Table:
    entries: t.List[Entry] = field(default_factory=list)


@dataclass
class Node:
    neighbors: t.List[Node]
    edges: t.List[Edge]
    label: str = "Node"
    table: Table = field(default_factory=Table)

    # equals
    def __eq__(self, other):
        return self.label == other.label
    
    # hash
    def __hash__(self):
        return hash(self.label)
    
    def __str__(self):
        return f"Node: {self.label}"


Tables = t.Dict[Node, Table]


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
    node: Node | None
    max_time: int
    expected_time: int

    # equals
    def __eq__(self, other):
        return self.node == other.node and self.max_time == other.max_time and self.expected_time == other.expected_time
    
    # less than
    def __lt__(self, other):
        return self.expected_time < other.expected_time
    
    # hash
    def __hash__(self):
        return hash((self.node, self.max_time, self.expected_time))
    
    def __str__(self):
        return f"Entry: {self.node.label if self.node else "None"} {self.max_time} {self.expected_time}"


@dataclass
class Graph:
    nodes: t.Mapping[str, Node]
    edges: t.Mapping[t.Tuple[str, str], Edge]

    def __str__(self):
        nodes = [str(node) for node in self.nodes.values()]
        edges = [str(edge) for edge in self.edges.values()]
        
        return f"Graph: {nodes} {edges}"


@dataclass
class TemporalGraph:
    time_to_graph: t.List[Graph]

    def __len__(self):
        return len(self.time_to_graph)

    def __init__(self, graphs: t.List[Graph]):
        self.time_to_graph = graphs

    def at_time(self, t: int) -> Graph:
        return self.time_to_graph[t]
    
    def __str__(self):
        string = ""
        for i, graph in enumerate(self.time_to_graph):
            string += (f"Time {i}: {graph}\n")
        return string
