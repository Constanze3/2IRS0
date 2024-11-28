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

    # def update(self, updated: t.List[str], update_fun, *args):
    #     # Update current Node's tables here
    #     update_fun(self, *args)  # Pass the function that updates tables here
    #     # Update the rest of the network
    #     for node in self.neighbors:
    #         if node.label not in updated: 
    #             node.update(updated + [self.label], update_fun, *args)


@dataclass
class Edge:
    from_node: Node
    to_node: Node
    expected_delay: int
    worse_case_delay: int
    
    def get_other_side(self, label):
        return self.to_node if self.from_node.label == label else self.from_node

@dataclass
class Entry:
    node: Node
    max_time: int
    expected_time: int

@dataclass
class Graph:
    nodes: t.Mapping[str, Node]
    edges: t.Mapping[t.Tuple[str, str], Edge]

@dataclass
class TemporalGraph:
    time_to_graph: t.List[Graph]

    def __len__(self):
        return len(self.time_to_graph)
    
    def __init__(self, graphs: t.List[Graph]):
        self.time_to_graph = graphs

    def at_time(self, t:int) -> Graph:
        return self.time_to_graph[t]